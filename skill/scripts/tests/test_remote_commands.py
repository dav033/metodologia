"""Command ledger: idempotency, preconditions, audit rows; exercised also through bt_remote_api.route_post."""
from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "bt_scheduler_core" / "tests"))
import bt_remote_api
import bt_remote_commands as rc
import bt_scheduler_adapter as scheduler_adapter
import bt_scheduler_core as scheduler_core
import bt_scheduler_ops
from support import Harness, indep

KEY = "test-gateway-key-0123456789"


def req(**over):
    base = {"idempotency_key": "key-00000001", "command": "pause", "target": "demo/REQ-001", "origin": "web",
            "params": {}, "precondition": {"state": "running", "revision": 3}}
    return {**base, **over}


class FakeHandler:
    def __init__(self, body: bytes):
        self.path = "/api/remote/v1/commands"
        self.headers = {"Authorization": f"Bearer {KEY}", "Content-Length": str(len(body))}
        self.rfile = io.BytesIO(body)
        self.sent = None

    def send(self, payload, status=200, content_type=""):
        self.sent = (status, json.loads(payload))


class LedgerBase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ledger = rc.Ledger(Path(self.temp.name) / "c.db")
        self.calls = []
        self.state = {"state": "running", "revision": 3, "updatedAt": "t1"}
        self.handlers = {"pause": self._pause, "launch": self._pause}

    def _pause(self, target, params):
        self.calls.append((target, params))
        return {"done": True}

    def submit(self, r):
        return self.ledger.submit(r, self.handlers, lambda target: self.state)


class LedgerTests(LedgerBase):
    def test_same_key_twice_stores_one_row_and_runs_once(self):
        first, second = self.submit(req()), self.submit(req())
        self.assertEqual((first["status"], second["status"], second["replayed"]), ("OK", "OK", True))
        self.assertEqual(len(self.ledger.rows()), 1)
        self.assertEqual(len(self.calls), 1)

    def test_stale_state_revision_and_updated_at_are_rejected(self):
        for pre in ({"state": "paused"}, {"revision": 2}, {"updatedAt": "t0"}):
            r = self.submit(req(idempotency_key=f"key-{json.dumps(pre)}-xx", precondition=pre))
            self.assertEqual(r["code"], "STALE_PRECONDITION", pre)
        self.assertEqual(self.calls, [])
        self.assertEqual(self.submit(req(idempotency_key="key-fresh-001", precondition={"updatedAt": "t1"}))["status"], "OK")

    def test_missing_target_is_stale(self):
        self.state = None
        self.assertEqual(self.submit(req())["code"], "STALE_PRECONDITION")

    def test_concurrent_commands_recheck_state_under_the_effect_lock(self):
        start = threading.Barrier(3)
        entered_states = []
        results = []

        def effect(target, params):
            entered_states.append(self.state["state"])
            self.state["state"] = "paused"
            return {"done": True}

        handlers = {"pause": effect}

        def submit(key):
            start.wait()
            results.append(self.ledger.submit(req(idempotency_key=key), handlers,
                                              lambda target: dict(self.state)))

        threads = [threading.Thread(target=submit, args=(f"key-concurrent-00{i}",)) for i in (1, 2)]
        for thread in threads:
            thread.start()
        start.wait()
        for thread in threads:
            thread.join(timeout=5)

        self.assertTrue(all(not thread.is_alive() for thread in threads), "concurrent submissions did not finish")
        self.assertCountEqual([result.get("code") or result["status"] for result in results],
                              ["STALE_PRECONDITION", "OK"])
        self.assertEqual(entered_states, ["running"])
        self.assertEqual(len(self.ledger.rows()), 2)

    def test_rows_keep_command_target_origin_outcome(self):
        self.submit(req(origin="telegram"))
        row = self.ledger.rows()[0]
        self.assertEqual((row["command"], row["target"], row["origin"], row["status"]),
                         ("pause", "demo/REQ-001", "telegram", "OK"))
        self.assertEqual(json.loads(row["outcome"]), {"done": True})

    def test_f5_same_key_different_content_conflicts(self):
        self.submit(req())
        for changed in (req(params={"x": 1}), req(target="demo/REQ-002"), req(command="launch"),
                        req(precondition={"state": "running", "revision": 4})):
            self.assertEqual(self.submit(changed)["code"], "IDEMPOTENCY_CONFLICT")
        self.assertEqual((len(self.ledger.rows()), len(self.calls)), (1, 1))

    def test_f4_invalid_commands_are_never_stored_as_ok(self):
        for bad in (req(command="rm-rf"), req(origin="fax"), req(precondition={}), req(precondition={"foo": 1}),
                    req(idempotency_key="x"), "pause", None):
            self.assertEqual(self.submit(bad)["code"], "INVALID_COMMAND")
        self.assertEqual(self.ledger.rows(), [])

    def test_f4_failed_effect_is_recorded_failed_and_not_replayed_as_ok(self):
        def boom(target, params):
            raise RuntimeError("disk full")
        self.handlers["pause"] = boom
        first, second = self.submit(req()), self.submit(req())
        self.assertEqual((first["status"], second["status"], second["replayed"]), ("FAILED", "FAILED", True))

    def test_f4_interrupted_command_replays_as_unknown_not_ok(self):
        class Crash(BaseException):
            pass
        def crash(target, params):
            raise Crash()
        self.handlers["pause"] = crash
        with self.assertRaises(Crash):
            self.submit(req())
        self.assertEqual(self.ledger.rows()[0]["status"], "PENDING")
        self.handlers["pause"] = self._pause
        again = self.submit(req())
        self.assertEqual(again["code"], "UNKNOWN_OUTCOME")
        self.assertEqual(self.calls, [])

    def test_state_reader_receives_command_and_effect_params(self):
        seen = []
        request = req(command="cancel-attempt", params={"attempt": "att-7"})
        self.ledger.submit(request, {"cancel-attempt": self._pause},
                           lambda target, command, params: seen.append((target, command, params)) or self.state)
        self.assertEqual(seen, [(request["target"], "cancel-attempt", {"attempt": "att-7"})])


class EntryPointTests(LedgerBase):
    def route_ledger(self):
        return rc.Ledger(Path(self.temp.name) / ".state" / "remote" / "commands.db")

    def post(self, body):
        h = FakeHandler(json.dumps(body).encode() if not isinstance(body, bytes) else body)
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": KEY, "BITACORA_ROOT": self.temp.name}), \
                patch.dict(bt_remote_api.HANDLERS, self.handlers, clear=True), \
                patch.object(bt_remote_api, "_target_state", lambda t: self.state):
            bt_remote_api.route_post(h)
        return h.sent

    def test_route_post_stores_once_and_replays(self):
        a, b = self.post(req()), self.post(req())
        self.assertEqual((a[0], a[1]["status"], b[0], b[1]["replayed"]), (200, "OK", 200, True))
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(len(self.route_ledger().rows()), 1)

    def test_route_post_stale_changed_and_invalid(self):
        self.assertEqual(self.post(req(precondition={"revision": 1}))[0], 409)
        self.assertEqual(self.post(req(idempotency_key="key-00000002", precondition={"revision": 1}))[1]["code"],
                         "STALE_PRECONDITION")
        self.post(req(idempotency_key="key-00000003"))
        self.assertEqual(self.post(req(idempotency_key="key-00000003", params={"a": 1}))[1]["code"], "IDEMPOTENCY_CONFLICT")
        self.assertEqual(self.post(req(command="nope"))[0], 400)
        self.assertEqual(self.post(b"{not json")[0], 400)

    def test_route_post_reopens_rejected_work_through_real_scheduler_operations(self):
        rdir = Path(self.temp.name) / "REQ-001-demo"
        rdir.mkdir()
        plan_folder = rdir / scheduler_adapter.REVISIONS
        plan_folder.mkdir()
        harness = Harness(
            [indep("T1")], repository=scheduler_core.SqliteRepository(rdir / scheduler_adapter.RUN_DB),
            plan_id="REQ-001",
        )
        digest = hashlib.sha256(harness.text.encode()).hexdigest()
        (plan_folder / "PLAN.r1.json").write_text(harness.text, encoding="utf-8")
        manifest = {"schema": 1, "revisions": [
            {"revision": 1, "sha256": digest, "frozen_at": "2026-10-20T00:00:00+00:00"}
        ]}
        (plan_folder / "MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
        harness.core.step()
        harness.send("T1", "execution_finished")
        harness.verdict("T1", accepted=False)
        self.assertEqual(harness.state("T1"), "recovering")

        def reopen(target, params):
            project, req_id = target.split("/", 1)
            return bt_scheduler_ops.apply(
                project, req_id, rdir, "reopen", params["task_id"], params["reason"]
            )

        def current_state(_target):
            return {"state": harness.state("T1"), "revision": 1}

        body = req(command="reopen", target="demo/REQ-001", params={"task_id": "T1", "reason": "fixed"},
                   precondition={"state": "rejected", "revision": 1})
        handler = FakeHandler(json.dumps(body).encode())
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": KEY, "BITACORA_ROOT": self.temp.name}), \
                patch.dict(bt_remote_api.HANDLERS, {"reopen": reopen}, clear=True), \
                patch.object(bt_remote_api, "_target_state", current_state), \
                patch.object(bt_scheduler_ops, "stop_owner", return_value=0):
            bt_remote_api.route_post(handler)

        status, response = handler.sent
        self.assertEqual((status, response["status"]), (200, "OK"))
        self.assertEqual(harness.state("T1"), "ready")
        transitions = [event for event in harness.core.audit_log() if event.kind == "task_transition"]
        self.assertTrue(any(
            event.detail.get("from") == "recovering" and event.detail.get("to") == "ready"
            for event in transitions
        ))
        row = self.route_ledger().rows()[0]
        self.assertEqual(json.loads(row["precondition"]), {"state": "rejected", "revision": 1})
        self.assertEqual(json.loads(row["outcome"]), ["owner stopped: 0 process(es)", "T1: reopened"])

    def test_route_post_without_executor_is_not_ok(self):
        self.handlers.clear()
        status, body = self.post(req(command="launch"))
        self.assertEqual((status, body["code"]), (501, "COMMAND_NOT_IMPLEMENTED"))
        self.assertEqual(self.route_ledger().rows(), [])

    def test_route_post_cancel_attempt_uses_scheduler_operator_apply(self):
        import bt_scheduler_ops as ops

        command = req(command="cancel-attempt", params={"attempt": "att-7"})
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": KEY, "BITACORA_ROOT": self.temp.name}), \
                patch.dict(bt_remote_api.HANDLERS, {}, clear=True), \
                patch.object(bt_remote_api, "_target_state", lambda target: self.state), \
                patch.object(rc, "_run_target", return_value=("demo", "REQ-001", Path(self.temp.name))), \
                patch.object(ops, "apply", return_value=["att-7: cancelled"]) as apply, \
                patch.object(ops, "resume", return_value="watchdog started"):
            status, body = self.post(command)
        self.assertEqual((status, body["status"]), (200, "OK"))
        apply.assert_called_once_with("demo", "REQ-001", Path(self.temp.name), "cancel-attempt", "att-7", "")

    def test_route_post_answer_decision_uses_scheduler_decisions_api(self):
        import bt_scheduler_decisions as decisions

        command = req(command="answer-decision", params={"request_id": "T2:1", "option": "retry"})
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": KEY, "BITACORA_ROOT": self.temp.name}), \
                patch.dict(bt_remote_api.HANDLERS, {}, clear=True), \
                patch.object(bt_remote_api, "_target_state", lambda target: self.state), \
                patch.object(rc, "_run_target", return_value=("demo", "REQ-001", Path(self.temp.name))), \
                patch.object(decisions, "answer", return_value=["T2: reopened"]) as answer:
            status, body = self.post(command)
        self.assertEqual((status, body["status"]), (200, "OK"))
        answer.assert_called_once_with("demo", "REQ-001", Path(self.temp.name), "T2:1", "retry", "", by="remote")

    def test_route_post_refuses_unknown_command_before_dispatch(self):
        command = req(command="erase-run")
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": KEY, "BITACORA_ROOT": self.temp.name}), \
                patch.dict(bt_remote_api.HANDLERS, {}, clear=True), \
                patch.object(bt_remote_api, "_target_state", lambda target: self.state), \
                patch.object(rc, "dispatch_run_command") as dispatch:
            status, body = self.post(command)
        self.assertEqual((status, body["code"]), (400, "INVALID_COMMAND"))
        dispatch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
