"""Behavioral fixtures for stable remote notifications and cursor paging."""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import quote

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import bt_remote_api
import bt_remote_events as feed
import bt_plans_api
import bt_rounds

AT = "2026-10-19T12:00:00Z"
OLD = "2026-10-19T08:00:00Z"
KINDS = set(feed.NOTIFICATION_KINDS)


def attempt(attempt_id: str, **values):
    return {"id": attempt_id, "last_activity_at": AT, **values}


def run(tasks, **values):
    return {"project": "demo", "req_id": "REQ-001", "title": "Demo", "updated_at": AT,
            "active": False, "status": "running", "tasks": tasks, **values}


def events_for(state, now=None):
    return {event["type"]: event for event in feed.build_events(state, now)}


class FixtureTests(unittest.TestCase):
    def test_each_notification_kind_has_a_fixture(self):
        fixtures = {
            "attempt.failed": {"runs": [run([{"id": "T1", "title": "Build",
                                               "state": "blocked", "reason": "attempts_exhausted",
                                               "attempts_used": 3, "max_attempts": 3,
                                               "attempt": attempt("a1", state="rejected", failure="tests")}])]},
            "attempt.blocked": {"runs": [run([{"id": "T1", "attempt": attempt("a2", state="blocked")}])]},
            "run.finished": {"runs": [run([], status="done")]},
            "round.waiting": {"rounds": [{"project": "demo", "req": "REQ-001", "round": 2, "at": AT}]},
            "plan.waiting": {"plans": [{"project": "demo", "req_id": "REQ-001", "plan_status": "proposed",
                                          "updated_at": AT}]},
            "quota.exhausted": {"quotas": [{"profile": "codex", "exhausted_until": AT}]},
            "attempt.stalled": {"runs": [run([{"id": "T1", "attempt": attempt(
                "a3", state="running", live=True, last_activity_at=OLD)}])]},
            "laptop.offline": {"offline": [{"since": AT}]},
            "command.updated": {"commands": [{"idempotency_key": "a" * 24, "command": "retry",
                                                "target": "demo/REQ-001",
                                                "origin": "web", "outcome": "done", "created_at": AT}]},
        }
        produced = set()
        for kind, fixture in fixtures.items():
            with self.subTest(kind=kind):
                event = events_for(fixture, now=1792400000.0).get(kind)
                self.assertIsNotNone(event)
                self.assertEqual(event["type"], kind)
                self.assertEqual(event["id"], event["dedupeKey"])
                produced.add(event["type"])
        self.assertEqual(produced, KINDS)

    def test_open_decision_request_is_a_stable_plan_waiting_event(self):
        request = {"id": "decision-7", "task": "T4", "attempt": "a9", "title": "T4 bloqueada",
                   "what": "Se agotaron los intentos.", "options": [{"id": "retry"}, {"id": "stop"}],
                   "recommended": "retry"}
        event = events_for({"decisions": [{"project": "demo", "req": "REQ-001",
                                            "request": request, "at": AT}]})["plan.waiting"]
        self.assertEqual(event["type"], "plan.waiting")
        self.assertEqual(event["target"], {"kind": "task", "project": "demo", "req": "REQ-001",
                                            "taskId": "T4", "attemptId": "a9"})
        self.assertEqual(event["data"]["decisionRequest"]["options"], ["retry", "stop"])
        replay = events_for({"decisions": [{"project": "demo", "req": "REQ-001",
                                             "request": request, "at": AT}]})["plan.waiting"]
        self.assertEqual(event["id"], replay["id"])

    def test_cursor_pages_replay_the_same_ids(self):
        state = {"rounds": [{"project": "demo", "req": "REQ-001", "round": n,
                             "at": f"2026-10-19T12:00:0{n}Z"} for n in range(1, 6)]}
        events = feed.build_events(state)
        first = feed.page(events, limit=2)
        replay = feed.page(feed.build_events(state), limit=2)
        self.assertEqual([item["id"] for item in first["events"]], [item["id"] for item in replay["events"]])
        next_a = feed.page(feed.build_events(state), first["nextCursor"], 2)
        next_b = feed.page(feed.build_events(state), first["nextCursor"], 2)
        self.assertEqual([item["id"] for item in next_a["events"]], [item["id"] for item in next_b["events"]])
        self.assertEqual(len(next_a["events"]), 2)
        self.assertTrue(next_a["hasMore"])

    def test_malformed_cursor_is_rejected(self):
        with self.assertRaises(feed.CursorError):
            feed.page([], "not-a-cursor")


class Handler:
    path = "/api/remote/v1/events"
    headers = {"Authorization": "Bearer test-key"}

    def send(self, body, status, content_type):
        self.body, self.status, self.content_type = body, status, content_type


class RouteTests(unittest.TestCase):
    def test_collect_keeps_blocked_attempt_ids_distinct_across_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base_run = run([{"id": "T1", "attempt": attempt("att-0001", state="blocked")}])
            runs = [base_run,
                    {**base_run, "req_id": "REQ-002"},
                    {**base_run, "tasks": [{"id": "T2", "attempt": attempt("att-0001", state="blocked")} ]},
                    {**base_run, "project": "other"}]

            first = feed.collect(root, runs, [], [], [])
            replay = feed.collect(root, runs, [], [], [])

            self.assertEqual(len(first), 4)
            self.assertEqual(len({event["id"] for event in first}), 4)
            self.assertEqual([event["id"] for event in first], [event["id"] for event in replay])
            self.assertEqual([event["dedupeKey"] for event in first], [event["id"] for event in first])

    def test_collect_uses_actual_open_round_creation_time_on_old_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            req_dir = root / "demo" / "requirements" / "REQ-001-old-plan"
            req_dir.mkdir(parents=True)
            plan = req_dir / "PLAN.md"
            plan.write_text("---\nstatus: proposed\n---\n# Plan — REQ-001 — Old plan\n", encoding="utf-8")
            old_time = time.time() - 7200
            os.utime(plan, (old_time, old_time))
            round_path = bt_rounds.new_round(req_dir, {
                "title": "New question",
                "questions": [{"id": "q1", "text": "Choose", "type": "open"}],
            })
            created_at = bt_rounds.load(round_path)["created_at"]

            plans = bt_plans_api.plans_payload(root)
            self.assertEqual(len(plans), 1)
            plan_updated = dt.datetime.fromisoformat(plans[0]["updated_at"]).timestamp()
            round_created = dt.datetime.fromisoformat(created_at).astimezone().timestamp()
            self.assertLess(plan_updated, round_created)
            events = feed.collect(root, [], plans, [], [])

            round_event = next(event for event in events if event["type"] == "round.waiting")
            self.assertEqual(round_event["occurredAt"], created_at)

    def test_get_events_route_uses_cursor_and_projects_open_decisions(self):
        handler = Handler()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._assert_decision_route(handler, root)

    def _assert_decision_route(self, handler, root):
        plan = {"project": "demo", "req_id": "REQ-001", "updated_at": AT, "plan_status": "approved"}
        request = {"id": "decision-1", "task": "T1", "title": "Waiting", "options": [{"id": "stop"}]}
        ledger = type("LedgerStub", (), {"rows": lambda self: []})
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key"}), \
                patch("bt_core.ROOT", root), \
                patch("bt_live_api.run_summaries", return_value=[]), \
                patch("bt_plans_api.plans_payload", return_value=[plan]), \
                patch("bt_plans_api.req_dir", return_value=Path("/tmp/REQ-001")), \
                patch("bt_plans_api.open_decisions", return_value=[request]), \
                patch("bt_plans_api.open_rounds", return_value=[]), \
                patch("bt_live_api.flow_events", return_value=([], [], {})), \
                patch("bt_subscriptions.summary", return_value=[]), \
                patch("bt_remote_commands.Ledger", ledger):
            bt_remote_api.route_get(handler)
        payload = json.loads(handler.body)
        self.assertEqual(handler.status, 200)
        self.assertEqual(payload["events"][0]["type"], "plan.waiting")
        self.assertIn("decisionRequest", payload["events"][0]["data"])

    def test_events_route_rejects_bad_cursor_and_limit(self):
        for path, code in (("/api/remote/v1/events?after=junk", "INVALID_CURSOR"),
                           ("/api/remote/v1/events?limit=0", "INVALID_LIMIT")):
            handler = Handler()
            handler.path = path
            with self.subTest(path=path), patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key"}):
                bt_remote_api.route_get(handler)
            self.assertEqual(handler.status, 400)
            self.assertEqual(json.loads(handler.body)["code"], code)

    def test_events_route_requires_retry_exhaustion_before_failed_notification(self):
        handler = Handler()
        source = run([{"id": "T1", "state": "recovering", "attempts_used": 1, "max_attempts": 3,
                       "attempt": attempt("a1", state="failed", failure="agent exited") }])
        transition = {"kind": "state_change", "project": "demo", "req": "REQ-001", "task": "T1",
                      "id": "transition-1", "at": AT, "data": {"state": "failed", "failure": "agent exited"}}
        class LedgerStub:
            def rows(self):
                return []

        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key"}), \
                patch("bt_core.ROOT", Path(directory)), \
                patch("bt_live_api.run_summaries", return_value=[source]), \
                patch("bt_plans_api.plans_payload", return_value=[]), \
                patch("bt_live_api.flow_events", return_value=([transition], [], {})), \
                patch("bt_subscriptions.summary", return_value=[]), \
                patch("bt_remote_commands.Ledger", LedgerStub):
            bt_remote_api.route_get(handler)
            self.assertEqual(handler.status, 200)
            self.assertFalse(any(event["type"] == "attempt.failed" for event in json.loads(handler.body)["events"]))

            handler = Handler()
            source["tasks"][0].update(state="blocked", reason="attempts_exhausted", attempts_used=3, max_attempts=3)
            bt_remote_api.route_get(handler)
            failed = next(event for event in json.loads(handler.body)["events"] if event["type"] == "attempt.failed")
            self.assertTrue(failed["data"]["retryExhausted"])
            self.assertEqual((failed["data"]["attemptsUsed"], failed["data"]["maxAttempts"]), (3, 3))

    def test_gateway_poll_returns_late_stall_and_round_after_saved_cursor(self):
        # Exercise the route's real feed.collect -> build_events -> page path across polls.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            finished = run([], status="done", updated_at="2026-10-19T12:10:00Z")
            active = run([{"id": "T1", "title": "Build", "attempt": attempt(
                "a1", state="running", live=True, last_activity_at="2026-10-19T12:00:00Z")}],
                status="running", active=True, updated_at="2026-10-19T12:10:00Z")
            plan = {"project": "demo", "req_id": "REQ-001", "updated_at": "2026-10-19T12:00:00Z",
                    "plan_status": "approved"}
            request = {"id": "decision-9", "task": "T1", "attempt": "a1", "title": "Choose",
                       "options": [{"id": "retry"}, {"id": "stop"}]}
            class LedgerStub:
                def rows(self):
                    return []

            def poll(after=""):
                handler = Handler()
                handler.path += "?after=" + quote(after, safe="") if after else ""
                bt_remote_api.route_get(handler)
                self.assertEqual(handler.status, 200)
                return json.loads(handler.body)

            with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key"}), \
                    patch("bt_core.ROOT", root), \
                    patch("bt_live_api.run_summaries", side_effect=[[finished], [active], [active]]), \
                    patch("bt_plans_api.plans_payload", return_value=[plan]), \
                    patch("bt_plans_api.req_dir", return_value=root), \
                    patch("bt_plans_api.open_decisions", side_effect=[[], [request], [request]]), \
                    patch("bt_plans_api.open_rounds", side_effect=[[], [2], [2]]), \
                    patch("bt_live_api.flow_events", return_value=([], [], {})), \
                    patch("bt_subscriptions.summary", return_value=[]), \
                    patch("bt_remote_commands.Ledger", LedgerStub):
                first = poll()
                self.assertEqual([event["type"] for event in first["events"]], ["run.finished"])
                cursor = first["nextCursor"]
                second = poll(cursor)
                self.assertEqual({event["type"] for event in second["events"]},
                                 {"attempt.stalled", "plan.waiting", "round.waiting"})
                self.assertEqual(len({event["id"] for event in second["events"]}), 3)
                replay = poll(cursor)
                self.assertEqual([event["id"] for event in second["events"]],
                                 [event["id"] for event in replay["events"]])
                self.assertEqual(len(replay["events"][1]["data"]["decisionRequest"]["options"]), 2)


if __name__ == "__main__":
    unittest.main()
