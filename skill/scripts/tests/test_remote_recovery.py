"""Remote recovery commands must reach the scheduler, persist pins, and reject unavailable routes first."""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import bt_remote_api
import bt_remote_commands as commands
import bt_remote_recovery as recovery
import bt_scheduler_decisions as decisions
import bt_scheduler_ops as ops

KEY = "test-gateway-key-0123456789"


class Handler:
    def __init__(self, body, path="/api/remote/v1/commands"):
        self.path = path
        raw = json.dumps(body).encode() if not isinstance(body, bytes) else body
        self.headers = {"Authorization": f"Bearer {KEY}", "Content-Length": str(len(raw))}
        self.rfile = io.BytesIO(raw)
        self.sent = None

    def send(self, payload, status=200, content_type=""):
        self.sent = (status, json.loads(payload))


class RemoteRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.rdir = Path(self.temp.name)
        self.retries = []

    def request(self, params, key="key-00000001"):
        body = {"idempotency_key": key, "command": "retry", "target": "demo/REQ-001", "origin": "web",
                "params": params, "precondition": {"state": "running", "revision": 3}}
        handler = Handler(body)
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": KEY, "BITACORA_ROOT": self.temp.name}), \
                patch.object(commands, "_run_target", return_value=("demo", "REQ-001", self.rdir)), \
                patch.object(ops, "bound_plan", return_value=SimpleNamespace(
                    task=lambda task_id: SimpleNamespace(id=task_id))), \
                patch.object(bt_remote_api, "_target_state", return_value={"state": "running", "revision": 3,
                                                                             "updatedAt": "t1"}), \
                patch.object(recovery, "validate_available", return_value=SimpleNamespace()), \
                patch.object(ops, "retry", side_effect=lambda *args: self.retries.append(args) or ["T1 reopened"]), \
                patch.object(ops, "resume", return_value="watchdog started"):
            bt_remote_api.route_post(handler)
        return handler.sent

    def test_real_command_pins_next_m2_candidates_and_records_pin_and_prompt_note(self):
        status, body = self.request({"task": "T1", "route": {"provider": "codex", "model": "gpt-5",
                                                                   "account": "work"},
                                    "reason": "Continue from the failing test"})
        self.assertEqual((status, body["status"]), (200, "OK"))
        pin = recovery.read_pins(self.rdir)["T1"]
        rows = recovery.filter_candidates(pin, [
            SimpleNamespace(provider="claude", model="sonnet", profile="work"),
            SimpleNamespace(provider="codex", model="gpt-5", profile="work"),
            SimpleNamespace(provider="codex", model="gpt-5", profile="personal"),
        ])
        self.assertEqual([(row.provider, row.model, row.profile) for row in rows], [("codex", "gpt-5", "work")])
        ledger = commands.Ledger(self.rdir / ".state" / "remote" / "commands.db")
        self.assertEqual(json.loads(ledger.rows()[0]["params"])["route"],
                         {"account": "work", "model": "gpt-5", "provider": "codex"})
        self.assertIn("Continue from the failing test", decisions.operator_notes(self.rdir, "T1"))
        self.assertEqual(len(self.retries), 1)

    def test_unavailable_pin_is_refused_before_reopen_and_ledger_marks_failure(self):
        body = {"idempotency_key": "key-00000002", "command": "retry", "target": "demo/REQ-001",
                "origin": "web", "params": {"task": "T1", "route": {"profile": "offline"}},
                "precondition": {"state": "running", "revision": 3}}
        handler = Handler(body)
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": KEY, "BITACORA_ROOT": self.temp.name}), \
                patch.object(commands, "_run_target", return_value=("demo", "REQ-001", self.rdir)), \
                patch.object(ops, "bound_plan", return_value=SimpleNamespace(
                    task=lambda task_id: SimpleNamespace(id=task_id))), \
                patch.object(bt_remote_api, "_target_state", return_value={"state": "running", "revision": 3}), \
                patch.object(recovery, "validate_available", side_effect=ValueError("route unavailable")), \
                patch.object(ops, "retry") as retry:
            bt_remote_api.route_post(handler)
        self.assertEqual((handler.sent[0], handler.sent[1]["code"]), (500, "EFFECT_FAILED"))
        retry.assert_not_called()
        self.assertFalse(recovery.pin_path(self.rdir).exists())
        ledger = commands.Ledger(self.rdir / ".state" / "remote" / "commands.db")
        self.assertEqual(ledger.rows()[0]["status"], "FAILED")

    def test_routes_endpoint_uses_run_target_and_task(self):
        handler = Handler({}, "/api/remote/v1/routes?target=demo%2FREQ-001&task=T1")
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": KEY}), \
                patch.object(commands, "_run_target", return_value=("demo", "REQ-001", self.rdir)), \
                patch.object(recovery, "route_options", return_value=[{"provider": "codex", "model": "gpt-5",
                                                                        "profile": "work", "available": True}]) as options:
            bt_remote_api.route_get(handler)
        self.assertEqual(handler.sent, (200, {"routes": [{"provider": "codex", "model": "gpt-5",
                                                          "profile": "work", "available": True}]}))
        options.assert_called_once_with("demo", self.rdir, "T1")

    def test_edit_brief_requires_owner_challenge_before_freeze_or_revise(self):
        effects = []
        request = {"idempotency_key": "key-edit-brief-01", "command": "edit-brief",
                   "target": "demo/REQ-001", "origin": "telegram",
                   "params": {"task": "T1", "field": "objective", "value": "Updated objective"},
                   "precondition": {"state": "running", "revision": 3}}

        def edit_brief(target, params):
            effects.append((target, params["typed_req"]))
            return {"revision": 4, "rebased": True}

        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": KEY, "BITACORA_ROOT": self.temp.name}), \
                patch.dict(bt_remote_api.HANDLERS, {"edit-brief": edit_brief}, clear=True), \
                patch.object(bt_remote_api, "_target_state", return_value={"state": "running", "revision": 3}):
            missing = Handler(request)
            bt_remote_api.route_post(missing)
            self.assertEqual((missing.sent[0], missing.sent[1]["code"]), (409, "CONFIRMATION_REQUIRED"))
            self.assertEqual(effects, [])
            ledger = commands.Ledger(Path(self.temp.name) / ".state" / "remote" / "commands.db")
            self.assertEqual(ledger.rows(), [])

            challenge = ledger.issue_challenge("demo/REQ-001", "REQ-001")
            mismatched = Handler({**request, "idempotency_key": "key-edit-brief-bad",
                                  "confirmation": {"challengeId": challenge["challengeId"],
                                                   "typedReq": "REQ-002"}})
            bt_remote_api.route_post(mismatched)
            self.assertEqual((mismatched.sent[0], mismatched.sent[1]["code"]),
                             (409, "CONFIRMATION_REQUIRED"))
            self.assertEqual(effects, [])
            self.assertEqual(ledger.rows(), [])

            confirmed = {**request, "idempotency_key": "key-edit-brief-02",
                         "confirmation": {"challengeId": challenge["challengeId"], "typedReq": "REQ-001"}}
            accepted = Handler(confirmed)
            bt_remote_api.route_post(accepted)

        self.assertEqual((accepted.sent[0], accepted.sent[1]["status"], accepted.sent[1]["outcome"]["revision"]),
                         (200, "OK", 4))
        self.assertEqual(effects, [("demo/REQ-001", "REQ-001")])

    def test_owner_edit_freezes_next_revision_before_rebasing_run(self):
        from bt_planner import contract as plan_contract, revisions, sync
        from bt_planner.tests.support import PLAN_MD, classify

        rdir = Path(self.temp.name) / "demo" / "requirements" / "REQ-001-demo"
        rdir.mkdir(parents=True)
        (rdir / "SPEC.md").write_text("# Spec\n## Requirements\n- R1. Demo\n", encoding="utf-8")
        (rdir / "PLAN.md").write_text(PLAN_MD.format(status="approved"), encoding="utf-8")
        plan = classify(sync.skeleton(rdir, plan_id="REQ-001"))
        (rdir / "PLAN.json").write_text(plan_contract.dumps(plan), encoding="utf-8")
        sync.approve_freeze(rdir, "REQ-001", ("approved",))
        original_objective = plan["tasks"][0]["objective"]

        challenge_handler = Handler({"target": "demo/REQ-001", "typedReq": "REQ-001"},
                                    "/api/remote/v1/challenges")
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": KEY, "BITACORA_ROOT": self.temp.name}), \
                patch.object(commands, "_run_target", return_value=("demo", "REQ-001", rdir)), \
                patch.object(bt_remote_api, "_target_state", return_value={"state": "running", "revision": 1}), \
                patch.object(ops, "apply", side_effect=lambda project, req, path, action, target, reason: [
                    self.assertEqual((project, req, path, action), ("demo", "REQ-001", rdir, "revise")),
                    self.assertEqual(revisions.latest(rdir)["revision"], 2), "rebased"]), \
                patch.object(ops, "resume", return_value="watchdog started"):
            bt_remote_api.route_post(challenge_handler)
            request = {"idempotency_key": "key-edit-brief-real", "command": "edit-brief",
                       "target": "demo/REQ-001", "origin": "telegram",
                       "params": {"task": "T1", "field": "objective", "value": "A revised task brief"},
                       "precondition": {"state": "running", "revision": 1},
                       "confirmation": {"challengeId": challenge_handler.sent[1]["challengeId"],
                                        "typedReq": "REQ-001"}}
            command_handler = Handler(request)
            bt_remote_api.route_post(command_handler)

        frozen = revisions.load_revision(rdir, 2)
        manifest_entry = revisions.latest(rdir)
        self.assertEqual((command_handler.sent[0], command_handler.sent[1]["status"],
                          command_handler.sent[1]["outcome"]["revision"]), (200, "OK", 2))
        self.assertEqual(frozen["tasks"][0]["objective"], "A revised task brief")
        self.assertNotEqual(frozen["tasks"][0]["objective"], original_objective)
        self.assertEqual(manifest_entry["source"], "approval")


if __name__ == "__main__":
    unittest.main()
