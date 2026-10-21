"""Command ledger: idempotency, preconditions, audit rows; exercised also through bt_remote_api.route_post."""
from __future__ import annotations

import hashlib
import io
import json
import os
import sqlite3
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


class EntryPointTests(LedgerBase):
    def route_ledger(self):
        return rc.Ledger(Path(self.temp.name) / ".state" / "remote" / "commands.db")

    def challenge(self):
        return 201, self.route_ledger().issue_challenge("demo/REQ-001", "REQ-001")

    def _create_scheduler_state(self, tasks, attempts=None):
        import bt_plans_api

        rdir = Path(self.temp.name) / "demo" / "requirements" / "REQ-001-demo"
        rdir.mkdir(parents=True, exist_ok=True)
        db_path = scheduler_adapter.run_db_path(rdir)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        doc = {"tasks": {key: {"state": state} for key, state in tasks.items()},
               "attempts": {key: {"state": state} for key, state in (attempts or {}).items()}}
        with sqlite3.connect(db_path) as db:
            db.execute("CREATE TABLE state (id INTEGER PRIMARY KEY, version INTEGER NOT NULL, doc TEXT NOT NULL)")
            db.execute("INSERT INTO state VALUES (1, 1, ?)", (json.dumps(doc),))
        model = {"run": {"authority": "scheduler", "status": "running", "updated_at": "t1",
                         "plan_ref": {"revision": 3}}, "plan": {"revision": 3, "status": "approved"}}
        return rdir, [patch.object(rc, "_run_target", return_value=("demo", "REQ-001", rdir)),
                      patch.object(bt_plans_api, "status_of", return_value=model)]

    def post_with_scheduler_state(self, body, patches):
        handler = FakeHandler(json.dumps(body).encode())
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": KEY, "BITACORA_ROOT": self.temp.name}), \
                patch.dict(bt_remote_api.HANDLERS, self.handlers, clear=True):
            with patches[0], patches[1]:
                bt_remote_api.route_post(handler)
        return handler.sent

    def real_run(self, *, blocked=False):
        import bt_core

        rdir = Path(self.temp.name) / "demo" / "requirements" / "REQ-001-demo"
        rdir.mkdir(parents=True)
        (rdir / "PLAN.md").write_text("---\nstatus: approved\n---\n# Plan\n", encoding="utf-8")
        plan_folder = rdir / scheduler_adapter.REVISIONS
        plan_folder.mkdir()
        scheduler_adapter.run_db_path(rdir).parent.mkdir(parents=True)
        harness = Harness(
            [indep("T1")], repository=scheduler_core.SqliteRepository(scheduler_adapter.run_db_path(rdir)),
            plan_id="REQ-001",
        )
        digest = hashlib.sha256(harness.text.encode()).hexdigest()
        (plan_folder / "PLAN.r1.json").write_text(harness.text, encoding="utf-8")
        (plan_folder / "MANIFEST.json").write_text(json.dumps({"schema": 1, "revisions": [
            {"revision": 1, "sha256": digest, "frozen_at": "2026-10-20T00:00:00+00:00"}
        ]}), encoding="utf-8")
        if blocked:
            harness.core.step()
            harness.send("T1", "execution_failed", reason="boom")
            harness.core.step()
        else:
            harness.core.step()
        scheduler_adapter.write_projection(rdir, harness.core)
        return bt_core, rdir, harness

    def post_real(self, body):
        import bt_core

        handler = FakeHandler(json.dumps(body).encode())
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": KEY, "BITACORA_ROOT": self.temp.name}), \
                patch.object(bt_core, "ROOT", Path(self.temp.name)), \
                patch.object(bt_remote_api, "_target_state", rc.target_state):
            bt_remote_api.route_post(handler)
        return handler.sent

    def real_target_state(self, target, command, params):
        import bt_core
        with patch.object(bt_core, "ROOT", Path(self.temp.name)):
            return rc.target_state(target, command, params)

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

    def test_f19_retry_precondition_uses_failed_task_while_run_is_running(self):
        _, patches = self._create_scheduler_state({"T1": "failed"})
        self.handlers["retry"] = self._pause

        status, body = self.post_with_scheduler_state(
            req(command="retry", params={"task": "T1"},
                precondition={"state": "failed", "revision": 3}), patches)

        self.assertEqual((status, body["status"]), (200, "OK"))
        self.assertEqual(self.calls, [("demo/REQ-001", {"task": "T1"})])

    def test_f19_retry_rejects_task_state_change_before_handler(self):
        _, patches = self._create_scheduler_state({"T1": "done"})
        self.handlers["retry"] = self._pause

        status, body = self.post_with_scheduler_state(
            req(command="retry", idempotency_key="key-00000002", params={"task": "T1"},
                precondition={"state": "failed", "revision": 3}), patches)

        self.assertEqual((status, body["code"]), (409, "STALE_PRECONDITION"))
        self.assertEqual(self.calls, [])

    def test_f19_retry_does_not_fall_back_to_running_run_for_missing_task(self):
        _, patches = self._create_scheduler_state({})
        self.handlers["retry"] = self._pause

        status, body = self.post_with_scheduler_state(
            req(command="retry", params={"task": "T-missing"},
                precondition={"state": "running", "revision": 3}), patches)

        self.assertEqual((status, body["code"]), (409, "STALE_PRECONDITION"))
        self.assertEqual(self.calls, [])

    def test_f19_reopen_precondition_uses_task_state_while_run_is_running(self):
        _, patches = self._create_scheduler_state({"T1": "recovering"})
        self.handlers["reopen"] = self._pause

        status, body = self.post_with_scheduler_state(
            req(command="reopen", params={"task": "T1"},
                precondition={"state": "rejected", "revision": 3}), patches)

        self.assertEqual((status, body["status"]), (200, "OK"))
        self.assertEqual(self.calls, [("demo/REQ-001", {"task": "T1"})])

    def test_f19_cancel_attempt_precondition_uses_attempt_state(self):
        _, patches = self._create_scheduler_state({"T1": "done"}, {"att-7": "running"})
        self.handlers["cancel-attempt"] = self._pause

        status, body = self.post_with_scheduler_state(
            req(command="cancel-attempt", idempotency_key="key-00000003", params={"attempt": "att-7"},
                precondition={"state": "running", "revision": 3}), patches)

        self.assertEqual((status, body["status"]), (200, "OK"))
        self.assertEqual(self.calls, [("demo/REQ-001", {"attempt": "att-7"})])

    def test_f19_cancel_attempt_does_not_fall_back_to_running_run_for_missing_attempt(self):
        _, patches = self._create_scheduler_state({"T1": "done"})
        self.handlers["cancel-attempt"] = self._pause

        status, body = self.post_with_scheduler_state(
            req(command="cancel-attempt", params={"attempt": "att-missing"},
                precondition={"state": "running", "revision": 3}), patches)

        self.assertEqual((status, body["code"]), (409, "STALE_PRECONDITION"))
        self.assertEqual(self.calls, [])

    def test_route_post_stale_changed_and_invalid(self):
        self.assertEqual(self.post(req(precondition={"revision": 1}))[0], 409)
        self.assertEqual(self.post(req(idempotency_key="key-00000002", precondition={"revision": 1}))[1]["code"],
                         "STALE_PRECONDITION")
        self.post(req(idempotency_key="key-00000003"))
        self.assertEqual(self.post(req(idempotency_key="key-00000003", params={"a": 1}))[1]["code"], "IDEMPOTENCY_CONFLICT")
        self.assertEqual(self.post(req(command="nope"))[0], 400)
        self.assertEqual(self.post(b"{not json")[0], 400)

    def test_route_post_reopens_rejected_work_through_real_scheduler_operations(self):
        bt_core, rdir, harness = self.real_run()
        harness.core.step()
        harness.send("T1", "execution_finished")
        harness.verdict("T1", accepted=False)
        self.assertEqual(harness.state("T1"), "recovering")
        scheduler_adapter.write_projection(rdir, harness.core)

        body = req(command="reopen", target="demo/REQ-001", params={"task": "T1", "reason": "fixed"},
                   precondition={"state": "rejected", "revision": 1})
        actual = self.real_target_state(body["target"], body["command"], body["params"])
        self.assertEqual(actual["state"], "recovering")
        self.assertTrue(rc._matches_precondition(body, actual), actual)
        handler = FakeHandler(json.dumps(body).encode())
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": KEY, "BITACORA_ROOT": self.temp.name}), \
                patch.object(bt_core, "ROOT", Path(self.temp.name)), \
                patch.object(bt_scheduler_ops, "stop_owner", return_value=0), \
                patch.object(bt_scheduler_ops, "kill_agent", return_value=0), \
                patch.object(bt_scheduler_ops, "resume", return_value="watchdog started"):
            bt_remote_api.route_post(handler)

        status, response = handler.sent
        self.assertEqual((status, response["status"]), (200, "OK"), response)
        self.assertEqual(harness.state("T1"), "ready")
        transitions = [event for event in harness.core.audit_log() if event.kind == "task_transition"]
        self.assertTrue(any(
            event.detail.get("from") == "recovering" and event.detail.get("to") == "ready"
            for event in transitions
        ))
        row = self.route_ledger().rows()[0]
        self.assertEqual(json.loads(row["precondition"]), {"state": "rejected", "revision": 1})
        self.assertEqual(json.loads(row["outcome"]),
                         {"messages": ["owner stopped: 0 process(es)", "T1: reopened", "watchdog started"]})

    def test_route_post_cancels_attempt_through_real_scheduler_operations(self):
        bt_core, rdir, harness = self.real_run()
        with sqlite3.connect(scheduler_adapter.run_db_path(rdir)) as db:
            doc = json.loads(db.execute("SELECT doc FROM state WHERE id = 1").fetchone()[0])
        attempt_id = next(iter(doc["attempts"]))
        state = self.real_target_state("demo/REQ-001", "cancel-attempt", {"attempt": attempt_id})
        body = req(command="cancel-attempt", target="demo/REQ-001", params={"attempt": attempt_id, "reason": "stuck"},
                   precondition={"state": state["state"], "revision": 1})
        with patch.object(bt_core, "ROOT", Path(self.temp.name)), \
                patch.object(bt_scheduler_ops, "stop_owner", return_value=0), \
                patch.object(bt_scheduler_ops, "kill_agent", return_value=0), \
                patch.object(bt_scheduler_ops, "resume", return_value="watchdog started"):
            status, response = self.post_real(body)
        self.assertEqual((status, response["status"]), (200, "OK"), response)
        with sqlite3.connect(scheduler_adapter.run_db_path(rdir)) as db:
            saved = json.loads(db.execute("SELECT doc FROM state WHERE id = 1").fetchone()[0])
        self.assertEqual(saved["attempts"][attempt_id]["state"], "cancelled")
        self.assertEqual(json.loads(self.route_ledger().rows()[0]["outcome"]),
                         {"messages": ["owner stopped: 0 process(es)", f"{attempt_id}: cancelled", "watchdog started"]})

    def test_route_post_answers_decision_through_real_scheduler_decisions_api(self):
        import bt_scheduler_decisions as decisions

        bt_core, rdir, harness = self.real_run(blocked=True)
        self.assertEqual(harness.state("T1"), "blocked")
        scheduler_adapter.write_projection(rdir, harness.core)
        [request] = decisions.open_requests(rdir)
        params = {"request_id": request["id"], "option": "retry", "reason": "fixed"}
        state = self.real_target_state("demo/REQ-001", "answer-decision", params)
        body = req(command="answer-decision", target="demo/REQ-001", params=params,
                   precondition={key: state[key] for key in ("state", "revision") if key in state})
        with patch.object(bt_core, "ROOT", Path(self.temp.name)), \
                patch.object(bt_scheduler_ops, "stop_owner", return_value=0), \
                patch.object(bt_scheduler_ops, "resume", return_value="watchdog started"):
            status, response = self.post_real(body)
        self.assertEqual((status, response["status"]), (200, "OK"), response)
        self.assertEqual(harness.state("T1"), "ready")
        saved = json.loads(decisions.answers_path(rdir).read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual((saved["request"], saved["option"], saved["by"]), (request["id"], "retry", "remote"))

    def test_route_post_answers_open_round_while_scheduler_is_waiting(self):
        import bt_plans_api
        import bt_rounds

        _bt_core, rdir, _harness = self.real_run()
        round_path = bt_rounds.new_round(rdir, {
            "title": "Scope choice",
            "questions": [{"id": "q1", "text": "Keep scope?", "type": "choice",
                           "options": [{"key": "yes", "label": "Yes"}]}],
        })
        round_data = bt_rounds.load(round_path)
        original_status_of = bt_plans_api.status_of

        def waiting_scheduler_status(*args, **kwargs):
            status = original_status_of(*args, **kwargs)
            status["run"]["status"] = "waiting"
            return status

        with patch.object(bt_plans_api, "status_of", side_effect=waiting_scheduler_status):
            actual = self.real_target_state("demo/REQ-001", "answer-round", {"round": round_data["round"]})
        self.assertEqual(actual, {"state": "open", "revision": None})
        body = req(command="answer-round", params={"round": round_data["round"],
                                                    "answers": {"q1": {"text": "yes"}}},
                   precondition={"state": actual["state"]})

        status, response = self.post_real(body)

        self.assertEqual((status, response["status"]), (200, "OK"), response)
        saved = bt_rounds.load(round_path)
        self.assertEqual(saved["status"], "answered")
        self.assertEqual(saved["answers"], {"q1": {"text": "yes"}})

    def test_route_post_without_executor_is_not_ok(self):
        self.handlers.clear()
        status, body = self.post(req())
        self.assertEqual((status, body["code"]), (501, "COMMAND_NOT_IMPLEMENTED"))
        self.assertEqual(self.route_ledger().rows(), [])

    def test_route_post_refuses_unknown_command(self):
        status, response = self.post(req(command="delete-everything"))
        self.assertEqual((status, response["code"]), (400, "INVALID_COMMAND"))
        self.assertEqual(self.route_ledger().rows(), [])


if __name__ == "__main__":
    unittest.main()
