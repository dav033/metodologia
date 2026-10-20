"""Command ledger: idempotency, preconditions, audit rows; exercised also through bt_remote_api.route_post."""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import bt_remote_api
import bt_remote_commands as rc
import bt_scheduler_ops

KEY = "test-gateway-key-0123456789"


def req(**over):
    base = {"idempotency_key": "key-00000001", "command": "pause", "target": "demo/REQ-001", "origin": "web",
            "params": {}, "precondition": {"state": "running", "revision": 3}}
    return {**base, **over}


class FakeHandler:
    def __init__(self, body: bytes, path="/api/remote/v1/commands"):
        self.path = path
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

    def post(self, body, path="/api/remote/v1/commands"):
        h = FakeHandler(json.dumps(body).encode() if not isinstance(body, bytes) else body, path)
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": KEY, "BITACORA_ROOT": self.temp.name}), \
                patch.dict(bt_remote_api.HANDLERS, self.handlers, clear=True), \
                patch.object(bt_remote_api, "_target_state", lambda t: self.state):
            bt_remote_api.route_post(h)
        return h.sent

    def challenge(self, target="demo/REQ-001", typed_req="REQ-001"):
        return self.post({"target": target, "typedReq": typed_req}, "/api/remote/v1/challenges")

    def test_route_post_stores_once_and_replays(self):
        a, b = self.post(req()), self.post(req())
        self.assertEqual((a[0], a[1]["status"], b[0], b[1]["replayed"]), (200, "OK", 200, True))
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(len(self.route_ledger().rows()), 1)

    def test_route_post_stale_changed_and_invalid(self):
        self.assertEqual(self.post(req(precondition={"revision": 1}))[0], 409)
        self.assertEqual(self.post(req(idempotency_key="key-00000002", precondition={"revision": 1}))[1]["code"],
                         "STALE_PRECONDITION")
        self.assertEqual(self.post(req(idempotency_key="key-00000004", precondition={"revision": 4}))[1]["code"],
                         "STALE_PRECONDITION")
        self.assertEqual(self.post(req(idempotency_key="key-00000005", precondition={"updatedAt": "t0"}))[1]["code"],
                         "STALE_PRECONDITION")
        self.post(req(idempotency_key="key-00000003"))
        self.assertEqual(self.post(req(idempotency_key="key-00000003", params={"a": 1}))[1]["code"], "IDEMPOTENCY_CONFLICT")
        self.assertEqual(self.post(req(command="nope"))[0], 400)
        self.assertEqual(self.post(b"{not json")[0], 400)

    def test_route_post_requires_confirmation_for_edit_brief(self):
        status, body = self.post(req(command="edit-brief"))
        self.assertEqual((status, body["code"]), (409, "CONFIRMATION_REQUIRED"))
        self.assertEqual(self.route_ledger().rows(), [])

    def test_real_entrypoint_refuses_launch_without_valid_challenge(self):
        status, body = self.post(req(command="launch"))
        self.assertEqual((status, body["code"]), (409, "CONFIRMATION_REQUIRED"))
        self.assertEqual(self.calls, [])
        self.assertEqual(self.route_ledger().rows(), [])

    def test_approve_launches_once_and_replay_does_not_launch_again(self):
        import bt_plans_api

        issued_status, issued = self.challenge()
        self.assertEqual(issued_status, 201)
        self.assertEqual(issued["expiresIn"], 120)
        request = req(command="approve", confirmation={"challengeId": issued["challengeId"],
                                                        "typedReq": "REQ-001"})
        calls = []
        with patch.object(rc, "_run_target", return_value=("demo", "REQ-001", Path(self.temp.name))), \
                patch.object(bt_plans_api, "run_plan", side_effect=lambda *a, **kw: calls.append((a, kw)) or "launched"):
            first, replay = self.post(request), self.post(request)
        self.assertEqual((first[0], first[1]["status"], replay[0], replay[1]["replayed"]),
                         (200, "OK", 200, True))
        self.assertEqual((len(calls), len(self.route_ledger().rows())), (1, 1))

    def test_challenge_cannot_be_reused_with_another_idempotency_key(self):
        _, issued = self.challenge()
        self.handlers["approve"] = self._pause
        request = req(command="approve", confirmation={"challengeId": issued["challengeId"],
                                                        "typedReq": "REQ-001"})
        self.assertEqual(self.post(request)[1]["status"], "OK")
        status, body = self.post({**request, "idempotency_key": "key-00000002"})
        self.assertEqual((status, body["code"]), (409, "CONFIRMATION_REQUIRED"))
        self.assertEqual(len(self.calls), 1)

    def test_f4_interrupted_effect_through_real_entrypoint_replays_unknown(self):
        class Crash(BaseException):
            pass
        self.handlers["pause"] = lambda *_: (_ for _ in ()).throw(Crash())
        with self.assertRaises(Crash):
            self.post(req())
        status, body = self.post(req())
        self.assertEqual((status, body["code"]), (409, "UNKNOWN_OUTCOME"))
        self.assertEqual(self.route_ledger().rows()[0]["status"], "PENDING")

    def test_answer_round_reaches_round_file_through_real_entrypoint(self):
        import bt_rounds

        rdir = Path(self.temp.name) / "requirements" / "REQ-001-demo"
        round_file = rdir / "rounds" / "round-02.json"
        round_file.parent.mkdir(parents=True)
        round_file.write_text(json.dumps({"round": 2, "status": "open", "questions": [{"id": "q1"}],
                                          "answers": {}}), encoding="utf-8")
        request = req(command="answer-round", params={"round": 2, "answers": {"q1": {"text": "Keep scope"}}})
        with patch.object(rc, "_run_target", return_value=("demo", "REQ-001", rdir)):
            status, body = self.post(request)
        saved = bt_rounds.load(round_file)
        self.assertEqual((status, body["status"], saved["status"], saved["answers"], saved["answered_via"]),
                         (200, "OK", "answered", {"q1": {"text": "Keep scope"}}, "remote"))

    def test_round_and_decision_answers_read_the_open_item_not_the_run_state(self):
        import bt_plans_api

        def post(body):  # real `_target_state`: only the handlers table is isolated
            h = FakeHandler(json.dumps(body).encode())
            with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": KEY, "BITACORA_ROOT": self.temp.name}), \
                    patch.dict(bt_remote_api.HANDLERS, {}, clear=True):
                bt_remote_api.route_post(h)
            return h.sent

        rdir = Path(self.temp.name) / "requirements" / "REQ-001-demo"
        round_file = rdir / "rounds" / "round-01.json"
        round_file.parent.mkdir(parents=True)
        round_file.write_text(json.dumps({"round": 1, "status": "open", "questions": [{"id": "q1"}], "answers": {}}),
                              encoding="utf-8")
        waiting = {"run": {"authority": "scheduler", "status": "waiting", "updated_at": "t1",
                           "plan_ref": {"revision": 3}}, "plan": {"revision": 3, "status": "approved"}}
        request = req(command="answer-round", params={"round": 1, "answers": {"q1": {"text": "x"}}},
                      precondition={"state": "open"})
        with patch.object(bt_plans_api, "status_of", return_value=waiting), \
                patch.object(rc, "_run_target", return_value=("demo", "REQ-001", rdir)):
            status, body = post(request)
        self.assertEqual((status, body["status"]), (200, "OK"))

        decision = {"id": "T1:1", "task": "T1", "options": [{"id": "retry"}]}
        calls = []
        request = req(idempotency_key="key-00000002", command="answer-decision",
                      params={"request_id": "T1:1", "option": "retry"}, precondition={"state": "open"})
        with patch.object(bt_plans_api, "status_of", return_value=waiting), \
                patch("bt_scheduler_decisions.open_requests", return_value=[decision]), \
                patch("bt_scheduler_decisions.answer", side_effect=lambda *a, **kw: calls.append(a) or ["ok"]), \
                patch.object(rc, "_run_target", return_value=("demo", "REQ-001", rdir)):
            status, body = post(request)
            self.assertEqual((status, body["status"], calls[0][3:5]), (200, "OK", ("T1:1", "retry")))
        stale = {**request, "idempotency_key": "key-00000003"}
        with patch("bt_scheduler_decisions.open_requests", return_value=[]), \
                patch.object(rc, "_run_target", return_value=("demo", "REQ-001", rdir)):
            status, body = post(stale)
        self.assertEqual((status, body["code"]), (409, "STALE_PRECONDITION"))

    def test_route_post_cancel_attempt_dispatches_through_scheduler_operator(self):
        request = req(command="cancel-attempt", params={"attempt": "att-001", "reason": "owner request"})
        calls = []
        with patch.object(rc, "_run_target", return_value=("demo", "REQ-001", Path(self.temp.name))), \
                patch.object(bt_scheduler_ops, "apply", side_effect=lambda *a, **kw: calls.append((a, kw)) or ["cancelled"]), \
                patch.object(bt_scheduler_ops, "resume", return_value="watchdog started"):
            status, body = self.post(request)
        self.assertEqual((status, body["status"]), (200, "OK"))
        self.assertEqual(calls[0][0][0:5], ("demo", "REQ-001", Path(self.temp.name), "cancel-attempt", "att-001"))
        self.assertEqual(calls[0][0][5], "owner request")

    def test_route_post_reads_public_state_and_live_revision_for_precondition(self):
        import bt_plans_api

        status_model = {"run": {"authority": "scheduler", "status": "running", "updated_at": "t1",
                                "plan_ref": {"revision": 3}}, "plan": {"revision": 4}}
        request = req(command="cancel-attempt", params={"attempt": "att-001"})
        calls = []
        h = FakeHandler(json.dumps(request).encode())
        with patch.object(bt_plans_api, "status_of", return_value=status_model) as status_reader, \
                patch.object(bt_scheduler_ops, "apply", side_effect=lambda *a, **kw: calls.append(a) or ["cancelled"]), \
                patch.object(bt_scheduler_ops, "resume", return_value="watchdog started"), \
                patch.object(rc, "_run_target", return_value=("demo", "REQ-001", Path(self.temp.name))), \
                patch.dict(os.environ, {"FLOW_GATEWAY_KEY": KEY, "BITACORA_ROOT": self.temp.name}), \
                patch.dict(bt_remote_api.HANDLERS, {}, clear=True):
            bt_remote_api.route_post(h)
        status, body = h.sent
        self.assertEqual((status, body["status"]), (200, "OK"))
        self.assertEqual(calls[0][4], "att-001")
        status_reader.assert_called_once()

    def _task_run(self, tasks, attempts=None):
        import sqlite3
        import bt_plans_api

        db = Path(self.temp.name) / "run.db"
        db.unlink(missing_ok=True)
        conn = sqlite3.connect(db)
        conn.execute("CREATE TABLE state (id INTEGER PRIMARY KEY, doc TEXT)")
        conn.execute("INSERT INTO state VALUES (1, ?)", (json.dumps(
            {"tasks": {k: {"state": v} for k, v in tasks.items()},
             "attempts": {k: {"state": v} for k, v in (attempts or {}).items()}}),))
        conn.commit()
        conn.close()
        model = {"run": {"authority": "scheduler", "status": "running", "updated_at": "t1",
                         "plan_ref": {"revision": 3}}, "plan": {"revision": 3, "status": "approved"}}
        return db, [patch.object(bt_plans_api, "status_of", return_value=model),
                    patch.object(rc, "_run_target", return_value=("demo", "REQ-001", Path(self.temp.name))),
                    patch("bt_scheduler_adapter.run_db_path", return_value=db)]

    def _post_real_state(self, request, patches):
        h = FakeHandler(json.dumps(request).encode())
        with patch.dict(os.environ, {"FLOW_GATEWAY_KEY": KEY, "BITACORA_ROOT": self.temp.name}), \
                patch.dict(bt_remote_api.HANDLERS, self.handlers, clear=True):
            for p in patches:
                p.start()
            try:
                bt_remote_api.route_post(h)
            finally:
                patch.stopall()
        return h.sent

    def test_f19_retry_precondition_pins_the_task_state_not_the_run_state(self):
        _, patches = self._task_run({"T1": "failed"})
        self.handlers["retry"] = self._pause
        status, body = self._post_real_state(
            req(command="retry", params={"task": "T1"}, precondition={"state": "failed", "revision": 3}), patches)
        self.assertEqual((status, body["status"]), (200, "OK"))
        self.assertEqual(len(self.calls), 1)

    def test_f19_retry_is_stale_when_the_task_is_no_longer_failed(self):
        _, patches = self._task_run({"T1": "done"})
        self.handlers["retry"] = self._pause
        status, body = self._post_real_state(
            req(command="retry", params={"task": "T1"}, precondition={"state": "failed", "revision": 3}), patches)
        self.assertEqual((status, body["code"]), (409, "STALE_PRECONDITION"))
        self.assertEqual(self.calls, [])

    def test_f19_cancel_attempt_precondition_pins_the_attempt_state(self):
        _, patches = self._task_run({"T1": "running"}, {"att-001": "running"})
        self.handlers["cancel-attempt"] = self._pause
        status, body = self._post_real_state(
            req(command="cancel-attempt", params={"attempt": "att-001"},
                precondition={"state": "running", "revision": 3}), patches)
        self.assertEqual((status, body["status"]), (200, "OK"))
        _, patches = self._task_run({"T1": "running"}, {"att-001": "cancelled"})
        status, body = self._post_real_state(
            req(command="cancel-attempt", idempotency_key="key-00000002", params={"attempt": "att-001"},
                precondition={"state": "running", "revision": 3}), patches)
        self.assertEqual((status, body["code"]), (409, "STALE_PRECONDITION"))

    def test_route_post_rejects_stale_plan_revision(self):
        import bt_plans_api

        status_model = {"run": {"authority": "scheduler", "status": "running", "updated_at": "t1",
                                "plan_ref": {"revision": 3}},
                        "plan": {"revision": 4, "status": "review"}}
        challenge = self.route_ledger().issue_challenge("demo/REQ-001", "REQ-001")
        request = req(command="approve", precondition={"state": "review", "revision": 3},
                      confirmation={"challengeId": challenge["challengeId"], "typedReq": "REQ-001"})
        h = FakeHandler(json.dumps(request).encode())
        with patch.object(bt_plans_api, "status_of", return_value=status_model), \
                patch.object(rc, "_run_target", return_value=("demo", "REQ-001", Path(self.temp.name))), \
                patch.dict(os.environ, {"FLOW_GATEWAY_KEY": KEY, "BITACORA_ROOT": self.temp.name}), \
                patch.dict(bt_remote_api.HANDLERS, {}, clear=True):
            bt_remote_api.route_post(h)
        self.assertEqual((h.sent[0], h.sent[1]["code"]), (409, "STALE_PRECONDITION"))
        self.assertEqual(self.route_ledger().rows(), [])

    def test_route_post_decision_answer_uses_scheduler_decisions_api(self):
        import bt_scheduler_decisions as decisions

        request = req(command="answer-decision", params={"request_id": "T1:2", "option": "retry",
                                                            "reason": "please retry"})
        calls = []
        with patch.object(rc, "_run_target", return_value=("demo", "REQ-001", Path(self.temp.name))), \
                patch.object(decisions, "answer", side_effect=lambda *a, **kw: calls.append((a, kw)) or ["answered"]):
            status, body = self.post(request)
        self.assertEqual((status, body["status"]), (200, "OK"))
        self.assertEqual(calls[0][0], ("demo", "REQ-001", Path(self.temp.name), "T1:2", "retry", "please retry"))
        self.assertEqual(calls[0][1], {"by": "remote"})

    def test_route_post_decision_note_is_read_by_next_attempt_prompt(self):
        import bt_scheduler_decisions as decisions
        import bt_scheduler_executor_wiring as wiring

        request = req(command="answer-decision", params={"request_id": "T1:2", "option": "retry_with_note",
                                                            "reason": "use the fixture"})
        open_request = {"id": "T1:2", "task": "T1", "options": [{"id": "retry_with_note"}]}
        with patch.object(rc, "_run_target", return_value=("demo", "REQ-001", Path(self.temp.name))), \
                patch.object(decisions, "open_requests", return_value=[open_request]), \
                patch.object(bt_scheduler_ops, "apply", return_value=["T1: reopened"]), \
                patch.object(bt_scheduler_ops, "resume", return_value="watchdog started"):
            status, body = self.post(request)
        self.assertEqual((status, body["status"]), (200, "OK"))
        prompt = wiring._with_owner_notes(Path(self.temp.name), lambda _request: "base prompt")(
            type("PromptRequest", (), {"task_id": "T1"})())
        self.assertIn("use the fixture", prompt)
        self.assertIn("base prompt", prompt)

    def test_route_post_refuses_unknown_command_without_ledger_row(self):
        status, body = self.post(req(command="erase-everything"))
        self.assertEqual((status, body["code"]), (400, "INVALID_COMMAND"))
        self.assertEqual(self.route_ledger().rows(), [])


if __name__ == "__main__":
    unittest.main()
