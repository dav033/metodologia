"""Pinned Scheduler retries validate route availability before reopening."""
from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bt_remote_commands as commands
import bt_remote_api as api
import bt_route_pins as pins
import bt_scheduler_adapter as scheduler
import bt_scheduler_core as scheduler_core
import bt_scheduler_ops as ops
from bt_scheduler_core import AssignmentRequest, TaskView
from bt_scheduler_decision import TaskFacts

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bt_scheduler_core" / "tests"))
from support import Harness, indep


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

    def real_blocked_run(self):
        import bt_core

        rdir = self.root / "demo" / "requirements" / "REQ-001-demo"
        rdir.mkdir(parents=True)
        (rdir / "PLAN.md").write_text("---\nstatus: approved\n---\n# Plan\n", encoding="utf-8")
        revisions = rdir / scheduler.REVISIONS
        revisions.mkdir()
        db_path = scheduler.run_db_path(rdir)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        harness = Harness([indep("T1")], repository=scheduler_core.SqliteRepository(db_path), plan_id="REQ-001")
        digest = hashlib.sha256(harness.text.encode()).hexdigest()
        (revisions / "PLAN.r1.json").write_text(harness.text, encoding="utf-8")
        (revisions / "MANIFEST.json").write_text(json.dumps({"schema": 1, "revisions": [
            {"revision": 1, "sha256": digest, "frozen_at": "2026-10-20T00:00:00+00:00"}
        ]}), encoding="utf-8")
        harness.core.step()
        harness.send("T1", "execution_failed", reason="boom")
        harness.core.step()
        scheduler.write_projection(rdir, harness.core)
        return bt_core, rdir, harness

    def real_approved_edit_run(self):
        import bt_core
        import bt_planner
        import bt_scheduler_run
        import bt_scheduler_adapter as adapter
        from test_plan_integration import PLAN_MD, classified

        project_dir = self.root / "demo"
        rdir = project_dir / "requirements" / "REQ-001-demo"
        rdir.mkdir(parents=True)
        (rdir / "SPEC.md").write_text("# Spec\n## Requirements\n- R1. Demo requirement\n", encoding="utf-8")
        (rdir / "PLAN.md").write_text(PLAN_MD.format(status="approved"), encoding="utf-8")
        document = classified(rdir)
        plan_path = rdir / "PLAN.json"
        plan_path.write_text(bt_planner.dumps(document), encoding="utf-8")
        bt_planner.approve_freeze(rdir, "REQ-001", bt_planner.APPROVED_STATES)
        scheduler = adapter.open_scheduler(rdir, config=scheduler_core.Config(max_parallel_tasks=1))
        adapter.write_projection(rdir, scheduler)
        bt_scheduler_run._runtime_binding(rdir, resume=False)
        return bt_core, rdir, document

    def post_real(self, body, bt_core):
        class Handler:
            path = f"{api.PREFIX}/commands"

            def __init__(self):
                raw = json.dumps(body).encode()
                self.rfile = io.BytesIO(raw)
                self.headers = {"Authorization": "Bearer test-key", "Content-Length": str(len(raw))}
                self.sent = None

            def send(self, payload, status=200, content_type=""):
                self.sent = (status, json.loads(payload))

        handler = Handler()
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key", "BITACORA_ROOT": str(self.root)}), \
                patch.object(bt_core, "ROOT", self.root), \
                patch.object(ops, "stop_owner", return_value=0), \
                patch.object(ops, "resume", return_value="watchdog started"):
            api.route_post(handler)
        return handler.sent

    def edit_body(self, bt_core, params, key):
        target = "demo/REQ-001"
        ledger = commands.Ledger(self.root / ".state" / "remote" / "commands.db")
        challenge = ledger.issue_challenge(target, "REQ-001")
        with patch.object(bt_core, "ROOT", self.root):
            precondition = commands.target_state(target, "edit-brief", params)
        return {"idempotency_key": key, "command": "edit-brief", "target": target, "origin": "web",
                "params": params, "confirmation": {"challengeId": challenge["challengeId"],
                                                       "typedReq": "REQ-001"},
                "precondition": precondition}

    def test_http_edit_accepts_phone_objective_and_criteria_aliases_and_rebases_real_run(self):
        import bt_planner

        bt_core, rdir, _document = self.real_approved_edit_run()
        objective = self.edit_body(bt_core, {"task": "T1", "field": "objective",
                                             "value": "Handle expired sessions safely"}, "edit-objective-0001")
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key", "BITACORA_ROOT": str(self.root)}), \
                patch.object(bt_core, "ROOT", self.root), patch.object(ops, "stop_owner", return_value=0), \
                patch.object(ops, "resume", return_value="watchdog started"):
            status, response = self.post_real(objective, bt_core)
        self.assertEqual((status, response["status"]), (200, "OK"), response)
        self.assertEqual(response["outcome"]["revision"], 2)
        self.assertEqual(ops.bound_plan(rdir).revision, 2)
        self.assertEqual(bt_planner.latest(rdir)["source"], "remote-owner")
        saved = json.loads((rdir / "plan-revisions" / "PLAN.r2.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["tasks"][0]["objective"], "Handle expired sessions safely")

        criteria = self.edit_body(bt_core, {"task": "T1", "field": "acceptance_criteria",
                                            "value": ["Expired sessions are rejected"]}, "edit-criteria-0001")
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key", "BITACORA_ROOT": str(self.root)}), \
                patch.object(bt_core, "ROOT", self.root), patch.object(ops, "stop_owner", return_value=0), \
                patch.object(ops, "resume", return_value="watchdog started"):
            status, response = self.post_real(criteria, bt_core)
        self.assertEqual((status, response["status"]), (200, "OK"), response)
        self.assertEqual(response["outcome"]["revision"], 3)
        self.assertEqual(ops.bound_plan(rdir).revision, 3)
        saved = json.loads((rdir / "plan-revisions" / "PLAN.r3.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["tasks"][0]["acceptance_criteria"], ["Expired sessions are rejected"])

    def test_http_edit_rejects_unapproved_drift_and_review_without_publishing_or_mutating(self):
        import bt_planner

        bt_core, rdir, document = self.real_approved_edit_run()
        path = rdir / "PLAN.json"
        drifted = json.loads(path.read_text(encoding="utf-8"))
        drifted["tasks"][1]["objective"] = "Unapproved change to another task"
        path.write_text(json.dumps(drifted), encoding="utf-8")
        drifted_bytes = path.read_bytes()
        body = self.edit_body(bt_core, {"task": "T1", "field": "brief", "value": "New objective"},
                              "edit-drift-0001")
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key", "BITACORA_ROOT": str(self.root)}), \
                patch.object(bt_core, "ROOT", self.root), patch.object(ops, "stop_owner", return_value=0), \
                patch.object(ops, "resume", return_value="watchdog started"):
            status, response = self.post_real(body, bt_core)
        self.assertEqual((status, response["code"]), (500, "EFFECT_FAILED"), response)
        self.assertIn("PLAN_DRIFT", response["outcome"]["error"])
        self.assertEqual(path.read_bytes(), drifted_bytes)
        self.assertEqual(bt_planner.latest(rdir)["revision"], 1)

        path.write_text(bt_planner.dumps(document), encoding="utf-8")
        (rdir / "PLAN.md").write_text((rdir / "PLAN.md").read_text(encoding="utf-8").replace(
            "status: approved", "status: review"), encoding="utf-8")
        before = path.read_bytes()
        body = self.edit_body(bt_core, {"task": "T1", "field": "brief", "value": "New objective"},
                              "edit-review-0001")
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": "test-key", "BITACORA_ROOT": str(self.root)}), \
                patch.object(bt_core, "ROOT", self.root), patch.object(ops, "stop_owner", return_value=0), \
                patch.object(ops, "resume", return_value="watchdog started"):
            status, response = self.post_real(body, bt_core)
        self.assertEqual((status, response["code"]), (500, "EFFECT_FAILED"), response)
        self.assertIn("PLAN_NOT_APPROVED", response["outcome"]["error"])
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(bt_planner.latest(rdir)["revision"], 1)

    def test_http_retry_reopens_real_blocked_task_and_records_the_pin(self):
        bt_core, rdir, harness = self.real_blocked_run()
        selected = candidate(route_id="route-b", model="opus", account_ref="acct:stable-b")
        body = {"idempotency_key": "real-retry-route-01", "command": "retry", "target": "demo/REQ-001",
                "origin": "web", "params": {"task": "T1", "route": "route-b", "reason": "use selected"},
                "precondition": {"state": "blocked", "revision": 1}}
        with patch("bt_route_pins.candidates_for", return_value=(candidate(), selected)):
            status, response = self.post_real(body, bt_core)
        self.assertEqual((status, response["status"]), (200, "OK"), response)
        self.assertEqual(harness.state("T1"), "ready")
        self.assertEqual(pins.get(rdir, "T1"), {"route": "route-b"})
        ledger_row = commands.Ledger(self.root / ".state" / "remote" / "commands.db").rows()[-1]
        self.assertEqual(json.loads(ledger_row["params"])["route"], "route-b")

    def test_http_retry_refuses_unavailable_route_before_real_reopen(self):
        bt_core, _rdir, harness = self.real_blocked_run()
        body = {"idempotency_key": "real-retry-route-02", "command": "retry", "target": "demo/REQ-001",
                "origin": "web", "params": {"task": "T1", "route": "route-missing"},
                "precondition": {"state": "blocked", "revision": 1}}
        with patch("bt_route_pins.candidates_for", return_value=(candidate(),)):
            status, response = self.post_real(body, bt_core)
        self.assertEqual((status, response["code"]), (422, "ROUTE_UNAVAILABLE"), response)
        self.assertEqual(harness.state("T1"), "blocked")
        self.assertEqual(commands.Ledger(self.root / ".state" / "remote" / "commands.db").rows()[-1]["status"],
                         "FAILED")

    def test_web_route_object_normalizes_to_the_chosen_route_id(self):
        self.assertEqual(pins.normalize({"route": {"route_id": "route-b", "provider": "claude",
                                                      "model": "opus", "account": "work"}}),
                         {"route": "route-b"})

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
        self.assertEqual(result["code"], "ROUTE_UNAVAILABLE")
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

    def test_replayed_pinned_retry_does_not_repeat_the_effect(self):
        request = self.request("retry-once-0001", route="route-a")
        result, retry = self.dispatch(request, (candidate(),))
        self.assertEqual(result["status"], "OK")
        retry.assert_called_once()

        replay, retry = self.dispatch(request, (candidate(),))
        self.assertEqual(replay["status"], "OK")
        self.assertTrue(replay["replayed"])
        retry.assert_not_called()
        self.assertEqual(pins.get(self.rdir, "T1"), {"route": "route-a"})

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
