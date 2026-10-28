"""Behavioral fixtures for stable remote notifications and cursor paging."""
from __future__ import annotations

import datetime as dt
import http.client
import json
import os
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.parse import quote

SCRIPTS = Path(__file__).resolve().parents[1]
GATEWAY = Path(__file__).resolve().parents[3] / "remote" / "gateway"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(GATEWAY))

import bt_remote_api
import bt_remote_events as feed
import bt_plans_api
import bt_rounds
import bt_core
import bt_live_api
import bt_plan_adapter
import bt_scheduler_adapter
from bt_planner import revisions as plan_revisions
import bt_server


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
                                               "attemptsUsed": 3, "maxAttempts": 3,
                                               "retriesRemaining": 0,
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
                                                "target": "demo/REQ-001", "origin": "web", "status": "OK",
                                                "code": None, "outcome": '{"messages": []}',
                                                "received_at": AT, "finished_at": AT}]},
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

    def test_f39_command_events_use_the_ledger_row_times(self):
        import bt_remote_commands as commands

        with tempfile.TemporaryDirectory() as root:
            ledger = commands.Ledger(Path(root) / "commands.db")
            ledger.submit({"idempotency_key": "f" * 20, "command": "pause", "target": "demo/REQ-001",
                           "origin": "web", "params": {}, "precondition": {"state": "running"}},
                          {"pause": lambda _target, _params: {"messages": ["paused"]}},
                          lambda _target: {"state": "running"})
            row = ledger.rows()[0]
        event = events_for({"commands": [row]})["command.updated"]
        self.assertNotEqual(event["occurredAt"], "1970-01-01T00:00:00Z")
        self.assertEqual(event["occurredAt"], row["finished_at"])
        self.assertEqual(event["target"], {"kind": "run", "project": "demo", "req": "REQ-001"})
        pending = {**row, "finished_at": None}
        self.assertEqual(events_for({"commands": [pending]})["command.updated"]["occurredAt"], row["received_at"])


class Handler:
    path = "/api/remote/v1/events"
    headers = {"Authorization": "Bearer test-key"}

    def send(self, body, status, content_type):
        self.body, self.status, self.content_type = body, status, content_type


class RouteTests(unittest.TestCase):


    def test_snapshot_route_redacts_session_secret_assignments(self):
        handler = Handler()
        handler.path = "/api/remote/v1/snapshot"
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key"}), \
                patch("bt_remote_snapshot.build_snapshot", return_value={
                    "runs": [{"failure": "SESSION_SECRET=synthetic-not-a-credential"}],
                }):
            bt_remote_api.route_get(handler)
        self.assertEqual(handler.status, 200)
        self.assertNotIn("synthetic-not-a-credential", handler.body)
        self.assertIn("SESSION_SECRET=[REDACTED]", handler.body)

    def test_review_route_redacts_session_secret_from_diagnostic_payload(self):
        handler = Handler()
        handler.path = "/api/remote/v1/attempts/a1/review?target=demo%2FREQ-001"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output.tail"
            output.write_text("SESSION_SECRET=synthetic-not-a-credential\n", encoding="utf-8")
            with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key"}), \
                    patch("bt_remote_api._commands._run_target", return_value=("demo", "REQ-001", Path(directory))), \
                    patch("bt_attempt_facts.attempt_facts", return_value={
                        "T1": [{"attempt": "a1", "state": "failed", "failure": "verification failed"}],
                    }), \
                    patch("bt_remote_api._review_executor_attempt", return_value=Path(directory)), \
                    patch("bt_remote_api._review_quality_result", return_value=(None, {})), \
                    patch("bt_remote_api._review_diff", return_value={"stat": None}):
                bt_remote_api.route_get(handler)
        self.assertEqual(handler.status, 200)
        self.assertNotIn("synthetic-not-a-credential", handler.body)
        self.assertIn("SESSION_SECRET=[REDACTED]", handler.body)

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

    def test_new_round_and_event_use_utc_when_laptop_timezone_is_bogota(self):
        if not hasattr(time, "tzset"):
            self.skipTest("tzset is unavailable on this platform")
        original_tz = os.environ.get("TZ")
        try:
            os.environ["TZ"] = "America/Bogota"
            time.tzset()
            with tempfile.TemporaryDirectory() as directory:
                rdir = Path(directory) / "REQ-001"
                rdir.mkdir()
                round_path = bt_rounds.new_round(rdir, {
                    "title": "Fresh question",
                    "questions": [{"id": "q1", "text": "Choose", "type": "open"}],
                })
                created_at = bt_rounds.load(round_path)["created_at"]
                self.assertTrue(created_at.endswith("Z"))
                event = events_for({"rounds": [{"project": "demo", "req": "REQ-001", "round": 1,
                                                  "at": created_at}]})["round.waiting"]
                self.assertEqual(event["occurredAt"], created_at)
                created_epoch = dt.datetime.fromisoformat(created_at.replace("Z", "+00:00")).timestamp()
                self.assertLess(abs(created_epoch - time.time()), 5)
                legacy = events_for({"rounds": [{"project": "demo", "req": "REQ-001", "round": 2,
                                                  "at": "2026-10-21T12:00:00"}]})["round.waiting"]
                self.assertEqual(legacy["occurredAt"], "2026-10-21T17:00:00Z")
        finally:
            if original_tz is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = original_tz
            time.tzset()

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
        transition = {"kind": "attempt_transition", "project": "demo", "req": "REQ-001", "task": "T1",
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
            self.assertEqual(failed["data"]["retriesRemaining"], 0)

    def test_attempt_transition_requires_and_reports_retry_exhaustion(self):
        transition = {"kind": "attempt_transition", "project": "demo", "req": "REQ-001", "task": "T1",
                      "attempt": "a1", "id": "transition-1", "at": AT,
                      "data": {"state": "failed", "failure": "agent exited"}}
        exhausted = {**transition, "data": {"state": "failed", "failure": "agent exited",
                                              "attempts_used": 3, "max_attempts": 3,
                                              "retries_remaining": 0}}

        self.assertIsNone(feed.from_flow(transition))
        event = feed.from_flow(exhausted)
        self.assertIsNotNone(event)
        self.assertEqual(event["type"], "attempt.failed")
        self.assertTrue(event["data"]["retryExhausted"])
        self.assertEqual((event["data"]["attemptsUsed"], event["data"]["maxAttempts"],
                          event["data"]["retriesRemaining"]), (3, 3, 0))

    def test_real_scheduler_projection_emits_exhausted_failure_through_remote_route(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            req_dir = root / "demo" / "requirements" / "REQ-001-budget"
            req_dir.mkdir(parents=True)
            plan = {
                "schema_version": "1.0.0", "plan_id": "REQ-001", "revision": 1,
                "spec_ref": "SPEC.md",
                "milestones": [{"id": "M1", "title": "Build", "acceptance_criteria": ["Build is checked"]}],
                "tasks": [{"id": "T1", "milestone_id": "M1", "title": "Fail three times",
                           "objective": "Exercise the retry limit", "estimate_rationale": "Fixture test",
                           "complexity": "low", "scope": "small_change", "estimated_minutes": 10,
                           "risk": "low", "coupling": "low", "confidence": "high",
                           "repository": "demo", "expected_paths": ["src/**"], "shared_resources": [], "after": [],
                           "verification": [{"type": "command", "value": "true", "purpose": "fixture check"}],
                           "acceptance_criteria": ["A failure is recorded"]}],
            }
            (req_dir / "PLAN.json").write_text(json.dumps(plan), encoding="utf-8")
            (req_dir / "PLAN.md").write_text("---\nstatus: approved\n---\n# Plan — REQ-001 — Budget\n",
                                             encoding="utf-8")
            plan_revisions.freeze(req_dir, plan, source="approval")
            scheduler = bt_scheduler_adapter.open_scheduler(
                req_dir, config=bt_scheduler_adapter.core.Config(max_parallel_tasks=1, max_attempts=3))
            for number in range(1, 4):
                scheduler.step()
                attempt_id = scheduler.snapshot().tasks["T1"]["attempt"]
                token = scheduler.read(lambda ctx: ctx.state.attempts[attempt_id].token)
                scheduler.ingest(bt_scheduler_adapter.core.Event(
                    f"failure-{number}", "REQ-001", 1, "T1", attempt_id, "fixture", "execution_failed",
                    payload={"reason": "fixture failure"}, token=token,
                ))
                scheduler.step()

            projection = json.loads(bt_scheduler_adapter.write_projection(req_dir, scheduler).read_text())
            projected = projection["tasks"][0]
            self.assertEqual((projected["attempts_used"], projected["max_attempts"],
                              projected["retries_remaining"], projected["retry_exhausted"]), (3, 3, 0, True))
            self.assertEqual(projected["attempts"], 3)

            handler = Handler()
            handler.path += "?limit=100"
            with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key", "BITACORA_ROOT": str(root)}), \
                    patch("bt_core.ROOT", root):
                bt_live_api._runs_seen.pop(root.resolve(), None)
                bt_remote_api.route_get(handler)
            self.assertEqual(handler.status, 200)
            payload = json.loads(handler.body)
            failed = [event for event in payload["events"] if event["type"] == "attempt.failed"]
            self.assertEqual(len(failed), 3)
            self.assertEqual(len({event["id"] for event in failed}), 3)
            self.assertEqual({event["data"]["attemptsUsed"] for event in failed}, {3})
            self.assertEqual({event["data"]["maxAttempts"] for event in failed}, {3})

    def test_events_route_requires_exhaustion_for_failed_attempt_transition(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            transition = {"id": "transition-1", "kind": "attempt_transition", "state": "failed",
                          "project": "demo", "req": "REQ-001", "task": "T1", "attempt": "a1",
                          "at": AT, "data": {"state": "failed", "failure": "tests"}}
            exhausted = {**transition, "data": {"state": "failed", "failure": "tests", "attemptsUsed": 3,
                                                 "maxAttempts": 3, "retriesRemaining": 0}}

            class LedgerStub:
                def rows(self):
                    return []

            def poll():
                handler = Handler()
                with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key"}):
                    bt_remote_api.route_get(handler)
                self.assertEqual(handler.status, 200)
                return json.loads(handler.body)

            with patch("bt_core.ROOT", root), \
                    patch("bt_live_api.run_summaries", return_value=[]), \
                    patch("bt_plans_api.plans_payload", return_value=[]), \
                    patch("bt_live_api.flow_events", side_effect=[([transition], [], {}), ([exhausted], [], {})]), \
                    patch("bt_subscriptions.summary", return_value=[]), \
                    patch("bt_remote_commands.Ledger", LedgerStub):
                self.assertEqual(poll()["events"], [])
                events = poll()["events"]
                self.assertEqual(len(events), 1)
                self.assertEqual(events[0]["type"], "attempt.failed")
                self.assertTrue(events[0]["data"]["retryExhausted"])
                self.assertEqual(events[0]["data"]["attemptsUsed"], 3)

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
