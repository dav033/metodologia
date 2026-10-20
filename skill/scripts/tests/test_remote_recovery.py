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
import bt_planner as planner
import bt_planner.revisions
import bt_plans_api
import bt_scheduler_adapter as adapter
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


class EditBriefTests(unittest.TestCase):
    """edit-brief through POST /commands: revision N+1, frozen as owner-approved, run rebased onto it."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.rdir = Path(self.temp.name) / "req"
        self.rdir.mkdir()
        plan = planner.loads(planner.example_text())
        planner.revisions.freeze(self.rdir, plan)
        (self.rdir / planner.PLAN_JSON).write_text(planner.dumps(plan), encoding="utf-8")
        self.calls = []

    def status_of(self, *_):
        return {"run": {"authority": "legacy"}, "plan": {"status": "approved",
                                                         "revision": planner.latest(self.rdir)["revision"]}}

    def post(self, params, key="brief-key-0001", revision=1, authority="scheduler"):
        body = {"idempotency_key": key, "command": "edit-brief", "target": "demo/REQ-001", "origin": "web",
                "params": params, "precondition": {"revision": revision}}
        handler = Handler(body)
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": KEY, "BITACORA_ROOT": self.temp.name}), \
                patch.object(commands, "_run_target", return_value=("demo", "REQ-001", self.rdir)), \
                patch.object(bt_plans_api, "status_of", self.status_of), \
                patch.object(adapter, "authority", return_value=authority), \
                patch.object(ops, "apply", side_effect=lambda *a: self.calls.append(a) or ["rebased"]), \
                patch.object(ops, "resume", return_value="watchdog started"):
            bt_remote_api.route_post(handler)
        return handler.sent

    def test_brief_edit_creates_next_revision_frozen_as_owner_approved_and_rebases(self):
        status, body = self.post({"task": "T1", "objective": "Rewritten brief with enough words",
                                  "acceptance_criteria": ["Observable new criterion"]})
        self.assertEqual((status, body["status"]), (200, "OK"))
        self.assertEqual((body["outcome"]["revision"], body["outcome"]["source"]), (2, "owner-approved"))
        last = planner.latest(self.rdir)
        self.assertEqual((last["revision"], last["source"]), (2, "owner-approved"))
        frozen = planner.load_revision(self.rdir, 2)
        task = next(t for t in frozen["tasks"] if t["id"] == "T1")
        self.assertEqual((task["objective"], task["acceptance_criteria"]),
                         ("Rewritten brief with enough words", ["Observable new criterion"]))
        self.assertEqual(planner.load_revision(self.rdir, 1)["tasks"][0]["objective"] != "Rewritten brief with enough words", True)
        self.assertEqual(planner.load(self.rdir / planner.PLAN_JSON)["revision"], 2)
        self.assertEqual([(c[3], c[4]) for c in self.calls], [("revise", "")])

    def test_stale_plan_revision_and_changed_content_under_same_key_are_refused(self):
        self.assertEqual(self.post({"task": "T1", "objective": "First rewritten brief text"})[0], 200)
        status, body = self.post({"task": "T1", "objective": "Second rewritten brief text"}, key="brief-key-0002", revision=1)
        self.assertEqual((status, body["code"]), (409, "STALE_PRECONDITION"))
        status, body = self.post({"task": "T1", "objective": "Other rewritten brief text"}, revision=1)
        self.assertEqual((status, body["code"]), (409, "IDEMPOTENCY_CONFLICT"))
        status, body = self.post({"task": "T1", "objective": "First rewritten brief text"}, revision=1)
        self.assertEqual((status, body["replayed"]), (200, True))
        self.assertEqual(planner.latest(self.rdir)["revision"], 2)
        self.assertEqual(len(self.calls), 1)

    def test_precondition_must_pin_revision_and_invalid_edit_creates_nothing(self):
        body = {"idempotency_key": "brief-key-0003", "command": "edit-brief", "target": "demo/REQ-001",
                "origin": "web", "params": {"task": "T1", "objective": "x"}, "precondition": {"state": "approved"}}
        self.assertIsNotNone(commands.validate(body))
        status, out = self.post({"task": "T9", "objective": "x"}, key="brief-key-0004")
        self.assertEqual((status, out["code"]), (500, "EFFECT_FAILED"))
        self.assertEqual(planner.latest(self.rdir)["revision"], 1)
        self.assertEqual(self.calls, [])

    def test_plan_without_run_only_freezes(self):
        status, _ = self.post({"task": "T2", "acceptance_criteria": ["Another observable criterion"]},
                              authority="none")
        self.assertEqual(status, 200)
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
