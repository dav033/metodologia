"""Behavioral fixtures for stable remote notifications and cursor paging."""
from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import bt_remote_api
import bt_remote_events as feed

AT = "2026-10-19T12:00:00Z"
OLD = "2026-10-19T08:00:00Z"
KINDS = set(feed.NOTIFICATION_KINDS)


def attempt(attempt_id: str, **values):
    return {"id": attempt_id, "last_activity_at": AT, **values}


def run(tasks, **values):
    return {"project": "demo", "req_id": "REQ-001", "title": "Demo", "updated_at": AT, "max_attempts": 3,
            "active": False, "status": "running", "tasks": tasks, **values}


def events_for(state, now=None):
    return {event["type"]: event for event in feed.build_events(state, now)}


class FixtureTests(unittest.TestCase):
    def test_each_notification_kind_has_a_fixture(self):
        fixtures = {
            "attempt.failed": {"runs": [run([{"id": "T1", "title": "Build", "attempts": 3,
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
    def test_get_events_route_uses_cursor_and_projects_open_decisions(self):
        handler = Handler()
        plan = {"project": "demo", "req_id": "REQ-001", "updated_at": AT, "plan_status": "approved"}
        request = {"id": "decision-1", "task": "T1", "title": "Waiting", "options": [{"id": "stop"}]}
        ledger = type("LedgerStub", (), {"rows": lambda self: []})
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key"}), \
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

    def test_production_events_route_waits_for_retry_budget_exhaustion(self):
        import bt_live_api as live

        flow_row = {"id": "transition-1", "kind": "attempt_transition", "remote_type": "attempt.failed",
                    "project": "demo", "req": "REQ-001", "task": "T1", "attempt": "a1", "at": AT,
                    "data": {"state": "failed"}}
        run_row = run([{"id": "T1", "attempts": 1,
                        "attempt": attempt("a1", state="failed", failure="transient")}])
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key"}), \
                patch("bt_live_api.run_summaries", return_value=[run_row]), \
                patch("bt_plans_api.plans_payload", return_value=[]), \
                patch("bt_subscriptions.summary", return_value=[]), \
                patch("bt_remote_commands.Ledger", return_value=type("LedgerStub", (), {"rows": lambda self: []})()), \
                patch("bt_live_api.flow_events", return_value=([flow_row], [], {})):
            handler = Handler()
            bt_remote_api.route_get(handler)
            payload = json.loads(handler.body)
            self.assertEqual(handler.status, 200)
            self.assertFalse(any(event["type"] == "attempt.failed" for event in payload["events"]))

            run_row["tasks"][0]["attempts"] = 3
            flow_row["data"].update({"attempts_used": 3, "max_attempts": 3})
            handler = Handler()
            bt_remote_api.route_get(handler)
            payload = json.loads(handler.body)
            failed = [event for event in payload["events"] if event["type"] == "attempt.failed"]
            self.assertTrue(failed)
            self.assertEqual(failed[0]["target"]["attemptId"], "a1")


if __name__ == "__main__":
    unittest.main()
