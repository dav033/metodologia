"""Pinned Scheduler retries validate route availability before reopening."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bt_remote_commands as commands
import bt_route_pins as pins
import bt_scheduler_adapter as scheduler
from bt_scheduler_core import AssignmentRequest, TaskView
from bt_scheduler_decision import TaskFacts


def candidate(route_id="route-a", provider="claude", model="sonnet", profile="claude-work",
              account_ref="acct:stable-a", **overrides):
    values = {
        "route_id": route_id, "provider": provider, "model": model, "profile": profile,
        "account_ref": account_ref, "effort": "medium", "source_status": "available",
        "source_reason_codes": (), "profile_authorized": True, "auth_status": "valid",
        "runtime_status": "available", "quota_status": "available", "quota_observed_at": 100.0,
        "quota_valid_until": 200.0, "quota_used_percent": 20.0, "baseline_rank": 0,
        "history": SimpleNamespace(),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class RemoteRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.rdir = self.root / "req"
        self.rdir.mkdir()
        self.ledger = commands.Ledger(self.root / "commands.db")

    def tearDown(self):
        self.temp.cleanup()

    def request(self, key="retry-route-0001", **params):
        return {
            "idempotency_key": key,
            "command": "retry",
            "target": "demo/REQ-001",
            "origin": "web",
            "params": {"task": "T1", **params},
            "precondition": {"state": "blocked"},
        }

    def dispatch(self, request, candidate_rows):
        with (
            patch("bt_remote_commands._run_target", return_value=("demo", "REQ-001", self.rdir)),
            patch("bt_route_pins.candidates_for", return_value=tuple(candidate_rows)),
            patch("bt_scheduler_ops.retry", return_value=["T1: reopened"]) as retry,
            patch("bt_scheduler_ops.resume", return_value="watchdog started"),
        ):
            result = self.ledger.submit(request, commands.dispatch_handlers(),
                                        lambda _target, _command, _params: {"state": "blocked"})
        return result, retry

    def test_pinned_retry_routes_only_to_the_chosen_candidate(self):
        rows = (candidate(), candidate("route-b", model="opus", profile="claude-work"))
        result, retry = self.dispatch(self.request(route="route-b", model="opus"), rows)

        self.assertEqual(result["status"], "OK")
        retry.assert_called_once()
        self.assertEqual(pins.get(self.rdir, "T1"), {"route": "route-b", "model": "opus"})

        assignment_port = scheduler.DecisionAssignmentPort.__new__(scheduler.DecisionAssignmentPort)
        assignment_port.project = "demo"
        assignment_port.run_dir = self.rdir
        assignment_port.classification_overlay = None
        assignment_port.checkpoint = "typed-decisions"
        assignment_port.ledger = object()
        captured = {}

        def persist(_ledger, requests, **_kwargs):
            captured["requests"] = requests
            return SimpleNamespace(assignments=())

        request = AssignmentRequest(
            "REQ-001", 1,
            (TaskView("T1", "M1", "skill", (), (), 1),),
            1, 150.0, "a" * 64,
        )
        with (
            patch.object(scheduler, "refresh_quota_preflight", return_value={"claude-work": {"status": "available"}}),
            patch("bt_scheduler_decision_adapter.task_facts",
                  return_value=(TaskFacts("T1", "brief", {}, {}), "implement", {})),
            patch("bt_scheduler_decision_adapter._candidate_rows", return_value=rows),
            patch("bt_scheduler_plan_routing._quota_evidence", return_value={}),
            patch("bt_scheduler_plan_routing.persist_dispatch_batch", side_effect=persist),
        ):
            assignment_port.propose(request)

        selected = captured["requests"][0].candidates
        self.assertEqual([item.route_id for item in selected], ["route-b"])

    def test_unavailable_route_is_refused_before_reopening(self):
        result, retry = self.dispatch(self.request(model="sonnet"),
                                      (candidate(quota_status="unknown"),))

        self.assertEqual(result["status"], "FAILED")
        self.assertIn("no se reabrió", result["outcome"]["error"])
        retry.assert_not_called()
        self.assertEqual(pins.load(self.rdir), {})

    def test_pin_is_recorded_in_ledger_for_success_and_refusal(self):
        self.dispatch(self.request("retry-ok-0001", account="acct:stable-a"), (candidate(),))
        self.dispatch(self.request("retry-no-0001", route="missing-route"), (candidate(),))

        rows = {row["idempotency_key"]: row for row in self.ledger.rows()}
        self.assertEqual(json.loads(rows["retry-ok-0001"]["params"])["account"], "acct:stable-a")
        self.assertEqual(json.loads(rows["retry-no-0001"]["params"])["route"], "missing-route")
        self.assertEqual(rows["retry-ok-0001"]["status"], "OK")
        self.assertEqual(rows["retry-no-0001"]["status"], "FAILED")

    def test_route_pin_matches_provider_model_and_account_selectors(self):
        selected = pins.narrow(self.rdir, "T1", (candidate(), candidate("route-b", provider="codex")))
        self.assertEqual([item.route_id for item in pins.narrow(
            self.rdir, "T1", selected,
        )], [item.route_id for item in selected])
        self.assertTrue(pins.matches({"route": "claude", "model": "sonnet", "account": "claude-work"},
                                     candidate()))
        self.assertFalse(pins.matches({"model": "opus"}, candidate()))

    def test_malformed_pin_is_rejected_without_ledger_or_retry_effect(self):
        request = self.request(model=" ")
        self.assertIsNotNone(commands.validate(request))
        self.assertEqual(self.ledger.submit(request, commands.dispatch_handlers(),
                                             lambda *_args: {"state": "blocked"})["status"], "REJECTED")
        self.assertEqual(self.ledger.rows(), [])

    def test_pin_parameters_are_retry_only(self):
        request = {**self.request(), "command": "resume", "params": {"route": "claude"}}
        self.assertIn("solo se admiten en retry", commands.validate(request))


if __name__ == "__main__":
    unittest.main()
