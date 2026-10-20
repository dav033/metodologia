"""Remote event contract and API-boundary redaction coverage."""
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
import bt_remote_events

KINDS = ("attempt.failed", "attempt.blocked", "run.finished", "round.waiting", "plan.waiting",
         "quota.exhausted", "attempt.stalled", "laptop.offline", "command.updated")


class Handler:
    path = "/api/remote/v1/events"
    headers = {"Authorization": "Bearer test-key"}

    def send(self, body, status, content_type):
        self.body, self.status, self.content_type = body, status, content_type


class RemoteEventsTests(unittest.TestCase):
    def test_each_notification_kind_has_a_fixture_and_contract_shape(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                event = bt_remote_events.from_flow({"remote_type": kind, "id": "source-1", "at": "2026-10-19T12:00:00Z",
                                                    "run": "demo/REQ-001", "task": "T1", "failure": "failed"})
                self.assertIsNotNone(event)
                self.assertEqual(event["type"], kind)
                self.assertEqual(event["id"], event["cursor"])
                self.assertEqual(event["id"], bt_remote_events.from_flow(
                    {"remote_type": kind, "id": "source-1", "at": "2026-10-19T12:00:00Z",
                     "run": "demo/REQ-001", "task": "T1"})["id"])

    def test_decision_requests_are_stable_plan_waiting_events(self):
        plans = [{"project": "demo", "req_id": "REQ-001", "decisions": [
            {"id": "decision-7", "title": "Choose", "options": [{"id": "retry"}]}]}]
        first = bt_remote_events.decision_events(plans)
        second = bt_remote_events.decision_events(plans)
        self.assertEqual(first, second)
        self.assertEqual(first[0]["type"], "plan.waiting")
        self.assertEqual(first[0]["target"], {"run": "demo/REQ-001"})

    def test_cursor_page_replay_has_identical_event_ids(self):
        events = [bt_remote_events.project_event("run.finished", str(n), f"2026-10-19T12:00:0{n}Z",
                                                  {"run": "demo/REQ-001"}, {}) for n in range(3)]
        first, cursor, more = bt_remote_events.page(events, "", 2)
        replay, _, _ = bt_remote_events.page(events, "", 2)
        next_page, _, _ = bt_remote_events.page(events, cursor, 2)
        self.assertEqual([event["id"] for event in first], [event["id"] for event in replay])
        self.assertTrue(more)
        self.assertEqual(len(next_page), 1)

    def test_real_get_route_includes_decisions_and_redacts_snapshot_and_event_text(self):
        decision = {"id": "d1", "title": "review", "failure": "TELEGRAM_BOT_TOKEN=abc"}
        row = {"remote_type": "attempt.failed", "id": "a1", "at": "2026-10-19T12:00:00Z",
               "run": "demo/REQ-001", "failure": "FLOW_GATEWAY_KEY=hidden GITHUB_CLIENT_SECRET=alsohidden"}
        handler = Handler()
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key"}), \
                patch("bt_live_api.flow_events", return_value=([row], [], {})), \
                patch.object(bt_remote_api, "_runs", return_value=[]), \
                patch.object(bt_remote_api, "_plans", return_value=[{"project": "demo", "req_id": "REQ-001",
                                                                       "decisions": [decision]}]):
            bt_remote_api.route_get(handler)
        payload = json.loads(handler.body)
        self.assertEqual(handler.status, 200)
        self.assertEqual({event["type"] for event in payload["events"]}, {"attempt.failed", "plan.waiting"})
        self.assertNotIn("hidden", handler.body)
        self.assertNotIn("alsohidden", handler.body)
        self.assertNotIn("abc", handler.body)

        handler.path = "/api/remote/v1/snapshot"
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key"}), \
                patch.object(bt_remote_api, "_snapshot_runs", return_value=[{"failure": "GITHUB_CLIENT_SECRET=secret"}]), \
                patch.object(bt_remote_api, "_plans", return_value=[]):
            bt_remote_api.route_get(handler)
        self.assertNotIn("secret", handler.body)

    def test_session_secret_is_redacted_from_snapshot_and_events(self):
        handler = Handler()
        row = {"remote_type": "attempt.failed", "id": "a1", "at": "2026-10-19T12:00:00Z",
               "run": "demo/REQ-001", "failure": "SESSION_SECRET=zz9plural"}
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key"}), \
                patch("bt_live_api.flow_events", return_value=([row], [], {})), \
                patch.object(bt_remote_api, "_runs", return_value=[]), \
                patch.object(bt_remote_api, "_plans", return_value=[]):
            bt_remote_api.route_get(handler)
        self.assertNotIn("zz9plural", handler.body)
        handler.path = "/api/remote/v1/snapshot"
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key"}), \
                patch.object(bt_remote_api, "_snapshot_runs",
                             return_value=[{"failure": "SESSION_SECRET: zz9plural", "SESSION_SECRET": "zz9plural"}]), \
                patch.object(bt_remote_api, "_plans", return_value=[]):
            bt_remote_api.route_get(handler)
        self.assertNotIn("zz9plural", handler.body)

    def test_real_get_route_projects_flow_bus_attempt_events_without_remote_type(self):
        row = {"v": 1, "seq": "m1:17", "ord": "0000000000000001.000000:m1:0000000017",
               "at": "2026-10-19T12:00:00.000+00:00", "run": "demo/REQ-001", "task": "T1",
               "attempt": "attempt-1", "from": "M3", "to": "M1", "kind": "state_change",
               "summary": "attempt-1: running → failed", "data": {"state": "failed", "audit": "attempt_transition"}}

        RUNS = [{"run": "demo/REQ-001", "tasks": [{"id": "T1", "state": "rejected", "attempts": 3}]}]

        def get_events():
            handler = Handler()
            with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key"}), \
                    patch("bt_live_api.flow_events", return_value=([row], [], {})), \
                    patch.object(bt_remote_api, "_runs", return_value=RUNS), \
                    patch.object(bt_remote_api, "_plans", return_value=[]):
                bt_remote_api.route_get(handler)
            self.assertEqual(handler.status, 200)
            return json.loads(handler.body)["events"]

        first = get_events()
        replay = get_events()
        self.assertEqual(len(first), 1)
        self.assertEqual(first[0]["type"], "attempt.failed")
        self.assertEqual(first[0]["target"], {"project": "demo", "req": "REQ-001", "taskId": "T1", "attemptId": "attempt-1"})
        self.assertEqual(first[0]["data"]["state"], row["data"]["state"])
        self.assertEqual(first[0]["data"]["summary"], row["summary"])
        self.assertEqual([event["id"] for event in first], [event["id"] for event in replay])

    def get_events(self, runs, plans=(), rows=(), quotas=()):
        handler = Handler()
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key"}), \
                patch("bt_live_api.flow_events", return_value=(list(rows), [], {})), \
                patch("bt_remote_views.max_attempts", return_value=3), \
                patch("bt_remote_views.cached_quota_rows", return_value=list(quotas)), \
                patch.object(bt_remote_api, "_runs", return_value=runs), \
                patch.object(bt_remote_api, "_plans", return_value=list(plans)):
            bt_remote_api.route_get(handler)
        self.assertEqual(handler.status, 200, handler.body)
        return json.loads(handler.body)["events"]

    def failed_row(self):
        return {"seq": "m1:9", "ord": "0000000000000009.000000:m1:0000000009", "at": "2026-10-19T12:00:00.000+00:00",
                "run": "demo/REQ-001", "task": "T1", "attempt": "attempt-1", "kind": "state_change",
                "summary": "attempt-1: running → failed", "data": {"state": "failed", "audit": "attempt_transition"}}

    def test_failed_attempt_notifies_only_after_retries_are_exhausted_with_retry_facts(self):
        def runs(state, attempts):
            return [{"run": "demo/REQ-001", "active": True, "status": "running",
                     "tasks": [{"id": "T1", "state": state, "attempts": attempts}]}]

        self.assertEqual(self.get_events(runs("rejected", 1), rows=[self.failed_row()]), [])
        self.assertEqual(self.get_events(runs("running", 2), rows=[self.failed_row()]), [])
        events = self.get_events(runs("rejected", 3), rows=[self.failed_row()])
        self.assertEqual([event["type"] for event in events], ["attempt.failed"])
        self.assertEqual(events[0]["data"]["retries"], {"attempts": 3, "maxAttempts": 3, "remaining": 0})
        blocked = self.get_events(runs("blocked", 1), rows=[self.failed_row()])
        self.assertEqual([event["type"] for event in blocked], ["attempt.blocked"])

    def test_state_derived_producers_emit_stable_events_for_every_specified_condition(self):
        runs = [
            {"run": "demo/REQ-001", "active": False, "status": "completed", "updated_at": "2026-10-19T12:00:00Z", "tasks": []},
            {"run": "demo/REQ-002", "active": True, "status": "running", "updated_at": "2026-10-19T12:00:00Z", "tasks": [
                {"id": "T1", "state": "running", "attempts": 1,
                 "attempt": {"id": "att-stuck", "live": True, "last_activity_at": "2000-01-01T00:00:00Z"}},
                {"id": "T2", "state": "running", "attempts": 1,
                 "attempt": {"id": "att-fresh", "live": True,
                             "last_activity_at": "2999-01-01T00:00:00Z"}}]},
        ]
        rounds_plan = [{"project": "demo", "req_id": "REQ-003", "decisions": [], "rounds": [
            {"project": "demo", "req": "REQ-003", "id": "round-01", "round": 1, "title": "Scope",
             "created_at": "2026-10-19T11:00:00Z"}]}]
        quotas = [{"profile": "claude", "provider": "claude", "status": "ok", "observed_at": 1.0,
                   "windows": {"five_hour": {"used_percent": 100, "resets_at": 4102444800}}},
                  {"profile": "codex", "provider": "codex", "status": "ok", "observed_at": 1.0,
                   "windows": {"seven_day": {"used_percent": 100, "resets_at": 4102444800}}}]
        first = self.get_events(runs, plans=rounds_plan, quotas=quotas)
        replay = self.get_events(runs, plans=rounds_plan, quotas=quotas)
        self.assertEqual({event["type"] for event in first},
                         {"run.finished", "attempt.stalled", "round.waiting", "quota.exhausted"})
        self.assertEqual([event["id"] for event in first], [event["id"] for event in replay])
        stalled = next(event for event in first if event["type"] == "attempt.stalled")
        self.assertEqual(stalled["target"]["attemptId"], "att-stuck")
        partial = [{**quotas[0]}, {**quotas[1], "windows": {"seven_day": {"used_percent": 10, "resets_at": 4102444800}}}]
        self.assertNotIn("quota.exhausted", {event["type"] for event in self.get_events([], quotas=partial)})

    def test_production_plan_rows_carry_decisions_that_become_plan_waiting_events(self):
        import tempfile
        from pathlib import Path
        import bt_remote_views
        with tempfile.TemporaryDirectory() as temp:
            rdir = Path(temp) / "demo" / "requirements" / "REQ-001-thing"
            rdir.mkdir(parents=True)
            (rdir / "PLAN.md").write_text("---\nstatus: approved\n---\n# Thing\n\n## M1 — First\n- [ ] **T1** Build\n",
                                          encoding="utf-8")
            request = {"id": "T1:1", "task": "T1", "title": "T1 bloqueada", "what": "x", "evidence": [],
                       "options": [{"id": "retry", "label": "Reintentar", "consequence": "Gasta un intento."}]}
            with patch("bt_scheduler_decisions.open_requests", return_value=[request]):
                plans = bt_remote_views.plans_view(Path(temp))
        self.assertEqual([d["id"] for d in plans[0]["decisions"]], ["T1:1"])
        events = self.get_events([], plans=plans)
        self.assertEqual([event["type"] for event in events], ["plan.waiting"])


if __name__ == "__main__":
    unittest.main()
