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
                                                    "run": "demo/REQ-001", "task": "T1", "failure": "failed",
                                                    "retry_exhausted": True})
                self.assertIsNotNone(event)
                self.assertEqual(event["type"], kind)
                self.assertEqual(event["id"], event["cursor"])
                self.assertEqual(event["id"], bt_remote_events.from_flow(
                     {"remote_type": kind, "id": "source-1", "at": "2026-10-19T12:00:00Z",
                     "run": "demo/REQ-001", "task": "T1", "retry_exhausted": True})["id"])

    def test_decision_requests_are_stable_plan_waiting_events(self):
        plans = [{"project": "demo", "req_id": "REQ-001", "decisions": [
            {"id": "decision-7", "title": "Choose", "options": [{"id": "retry"}]}]}]
        first = bt_remote_events.decision_events(plans)
        second = bt_remote_events.decision_events(plans)
        self.assertEqual(first, second)
        self.assertEqual(first[0]["type"], "plan.waiting")
        self.assertEqual(first[0]["target"], {"run": "demo/REQ-001"})

    def test_attempt_failure_notification_requires_durable_retry_exhaustion_decision(self):
        base = {"project": "demo", "req_id": "REQ-001", "decisions": [
            {"id": "d1", "reason": "attempts_exhausted", "task": "T2", "attempt": "a2"}]}
        events = bt_remote_events.decision_events([base])
        failure = next(event for event in events if event["type"] == "attempt.failed")
        self.assertEqual(failure["target"], {"run": "demo/REQ-001", "task": "T2"})
        self.assertTrue(failure["data"]["retry_exhausted"])

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
               "run": "demo/REQ-001", "failure": "FLOW_GATEWAY_KEY=hidden GITHUB_CLIENT_SECRET=alsohidden",
               "data": {"retry_exhausted": True}}
        handler = Handler()
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key"}), \
                patch("bt_live_api.flow_events", return_value=([row], [], {})), \
                patch.object(bt_remote_api, "_plans", return_value=[{"project": "demo", "req_id": "REQ-001",
                                                                       "decisions": [decision]}]), \
                patch.object(bt_remote_api, "_snapshot_runs", return_value=[]), \
                patch.object(bt_remote_api, "_planning_detail", return_value=([], [])), \
                patch("bt_quota_live.read_all_live", return_value=[]), \
                patch("bt_remote_commands.Ledger.rows", return_value=[]):
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

    def test_real_get_route_projects_flow_bus_attempt_events_without_remote_type(self):
        row = {"v": 1, "seq": "m1:17", "ord": "0000000000000001.000000:m1:0000000017",
               "at": "2026-10-19T12:00:00.000+00:00", "run": "demo/REQ-001", "task": "T1",
               "attempt": "attempt-1", "from": "M3", "to": "M1", "kind": "state_change",
               "summary": "attempt-1: running → failed", "data": {"state": "failed", "audit": "attempt_transition"}}

        def get_events():
            handler = Handler()
            with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key"}), \
                    patch("bt_live_api.flow_events", return_value=([row], [], {})), \
                    patch.object(bt_remote_api, "_plans", return_value=[]), \
                    patch.object(bt_remote_api, "_snapshot_runs", return_value=[]), \
                    patch.object(bt_remote_api, "_planning_detail", return_value=([], [])), \
                    patch("bt_quota_live.read_all_live", return_value=[]), \
                    patch("bt_remote_commands.Ledger.rows", return_value=[]):
                bt_remote_api.route_get(handler)
            self.assertEqual(handler.status, 200)
            return json.loads(handler.body)["events"]

        first = get_events()
        self.assertEqual(first, [])  # a failed attempt is not proof that recovery is exhausted
        row["data"]["retry_exhausted"] = True
        first = get_events()
        replay = get_events()
        self.assertEqual(len(first), 1)
        self.assertEqual(first[0]["type"], "attempt.failed")
        self.assertEqual(first[0]["target"], {"run": "demo/REQ-001", "task": "T1"})
        self.assertEqual(first[0]["data"], row["data"])
        self.assertEqual([event["id"] for event in first], [event["id"] for event in replay])

    def test_snapshot_producers_cover_completion_quota_stall_and_open_rounds(self):
        runs = [{"run": "demo/REQ-001", "state": "finished", "updatedAt": "2026-10-20T12:00:00Z",
                 "tasks": [{"id": "T1", "state": "blocked", "reason": "quota_exhausted", "retries_remaining": 0,
                            "attempt": {"id": "a1", "live": True, "last_activity_at": "2026-10-20T11:40:00Z"}}]}]
        rounds = [{"project": "demo", "req": "REQ-001", "round": 2, "status": "open"}]
        events = bt_remote_events.from_snapshot(runs, rounds, quotas=[{"profile": "codex", "status": "exhausted"}],
                                                commands=[{"idempotency_key": "k1", "target": "demo/REQ-001",
                                                           "status": "OK"}], now=1792497600)
        self.assertEqual({event["type"] for event in events},
                         {"run.finished", "attempt.blocked", "quota.exhausted", "attempt.stalled", "round.waiting",
                          "attempt.failed", "command.updated"})


if __name__ == "__main__":
    unittest.main()
