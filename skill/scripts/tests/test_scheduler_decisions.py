"""Decision requests: derived from the run, closed options, unskippable ones flagged, answers carried out and recorded."""
from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import bt_run_stores
import bt_scheduler_adapter as adapter
import bt_scheduler_decisions as decisions
import bt_scheduler_ops as ops
import bt_scheduler_watch as watch


def doc(reason="m5:attempts_exhausted", attempts=("att-1", "att-2"), revision=1, state="blocked"):
    return {"revision": revision, "tasks": {"T1": {"state": state, "reason": reason, "attempts": list(attempts)},
                                            "T2": {"state": "pending", "reason": "", "attempts": []}},
            "attempts": {a: {"id": a, "state": "failed", "failure": "verification_rejected", "evidence": "m6://x"}
                         for a in attempts}}


class Base(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.rdir = Path(self.temp.name) / "REQ-001-x"
        self.rdir.mkdir()
        self.doc = doc()
        for target, value in (("_state", lambda rdir: self.doc), ("_newer_revision", lambda rdir, current: False)):
            patcher = patch.object(decisions, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(bt_run_stores, "paths", return_value={})
        patcher.start()
        self.addCleanup(patcher.stop)


class Requests(Base):
    def test_a_known_reason_is_a_request_with_options_a_recommendation_and_no_lock(self):
        [request] = decisions.open_requests(self.rdir)
        self.assertEqual(request["id"], "T1:2")
        self.assertFalse(request["unskippable"])
        self.assertEqual(request["recommended"], "retry")
        self.assertEqual([o["id"] for o in request["options"]], ["retry", "retry_with_note", "stop"])
        self.assertIn("intentos", request["what"])

    def test_an_unknown_reason_fails_closed(self):
        self.doc = doc(reason="somebody wrote this")
        [request] = decisions.open_requests(self.rdir)
        self.assertTrue(request["unskippable"])
        self.assertIn("no reconoce", request["what"])

    def test_integrity_anomalies_are_unskippable(self):
        for code in ("identity_unverified", "execution_unsettled", "evidence_insufficient"):
            self.doc = doc(reason=f"m5:{code}")
            self.assertTrue(decisions.open_requests(self.rdir)[0]["unskippable"], code)

    def test_revise_is_offered_only_when_a_newer_frozen_revision_exists(self):
        with patch.object(decisions, "_newer_revision", return_value=True):
            [request] = decisions.open_requests(self.rdir)
        self.assertIn("revise", [o["id"] for o in request["options"]])

    def test_only_blocked_tasks_ask(self):
        self.doc = doc(state="running")
        self.assertEqual(decisions.open_requests(self.rdir), [])

    def test_a_new_attempt_makes_a_new_request_and_an_answered_one_disappears(self):
        decisions.answers_path(self.rdir).write_text(json.dumps({"request": "T1:2"}) + "\n")
        self.assertEqual(decisions.open_requests(self.rdir), [])
        self.doc = doc(attempts=("att-1", "att-2", "att-3"))
        self.assertEqual(decisions.open_requests(self.rdir)[0]["id"], "T1:3")

    def test_render_names_every_option_and_how_to_answer(self):
        text = decisions.render(decisions.open_requests(self.rdir), "REQ-001")
        for needle in ("retry (recomendada)", "retry_with_note", "stop", "decide T1:2"):
            self.assertIn(needle, text)
        self.assertEqual(decisions.render([], "REQ-001"), "Ninguna decisión pendiente.")


class WhatTheOwnerSees(Base):
    """A stop says what it needs from the owner, what the owner can do and the error itself."""

    def test_a_blocked_task_shows_its_error_what_it_needs_and_what_can_be_done(self):
        decisions.write_verify_notes(self.rdir, "T1", "check `npm test` failed (exit 1): Cannot find module 'x'")
        [request] = decisions.open_requests(self.rdir)
        self.assertIn("Cannot find module", request["error"])
        self.assertIn("verification_rejected", request["error"])
        self.assertTrue(request["needs"])
        self.assertTrue(any("entorno" in item for item in request["you_can"]))
        text = decisions.render([request], "REQ-001")
        for needle in ("Qué necesita de ti:", "Error:", "Cannot find module", "Diagnóstico (reglas): [Dependencias]",
                       "Falta la dependencia x", "1. Reintenta con la indicación"):
            self.assertIn(needle, text)
        self.assertEqual(request["recommended"], "retry_with_note")        # the rule knows the cause: it picks the note

    def test_every_known_reason_has_guidance_and_an_unknown_one_says_to_look(self):
        self.assertEqual(set(decisions.REASONS) - set(decisions.GUIDE), set())
        self.doc = doc(reason="somebody wrote this")
        [request] = decisions.open_requests(self.rdir)
        self.assertIn("somebody wrote this", request["error"])
        self.assertIn("no reconoce", request["needs"] + request["what"])

    def test_a_known_cause_replaces_the_generic_need_of_the_reason_code(self):
        self.doc = doc(reason="m5:identity_unverified")
        self.doc["attempts"]["att-2"]["failure"] = "start rejected: INTEGRATION_CONFLICT: T3 vs T4 for T1: a.py, b.py"
        [request] = decisions.open_requests(self.rdir)
        if request.get("diagnosis") and request["diagnosis"]["confidence"] == "alta":
            self.assertNotIn("no es fiable", request["needs"])
            self.assertIn(request["diagnosis"]["option"], request["needs"])

    def test_a_quota_stop_is_not_presented_as_a_code_defect(self):
        self.doc = doc(reason="m5:quota_reset_unknown")
        [request] = decisions.open_requests(self.rdir)
        self.assertIn("No es un fallo del código", request["needs"])


class AgainstARealRun(unittest.TestCase):
    """The request is read from the state document a real core wrote, not from a hand-made dictionary."""

    def test_a_task_the_core_blocked_becomes_a_request_and_a_reopen_answers_it(self):
        sys.path.insert(0, str(Path(adapter.core.__file__).parent / "tests"))
        sc = adapter.core
        from support import Harness, indep

        with tempfile.TemporaryDirectory() as temp:
            db = Path(temp) / "SCHEDULER.db"
            h = Harness([indep("T1"), indep("T2", ["T1"])], repository=sc.SqliteRepository(db), max_attempts=1)
            h.core.step()
            h.send("T1", "execution_failed", reason="boom")
            h.core.step()
            self.assertEqual(h.state("T1"), "blocked")
            rdir = Path(temp) / "REQ-001-x"
            rdir.mkdir()
            with patch.object(adapter, "run_db_path", return_value=db), \
                    patch.object(bt_run_stores, "paths", return_value={}), \
                    patch.object(decisions, "_newer_revision", return_value=False):
                [request] = decisions.open_requests(rdir)
                self.assertEqual((request["task"], request["id"]), ("T1", "T1:1"))
                self.assertTrue(request["options"])
                h.core.reopen("T1", "owner", "retry")
                h.core.step()
                self.assertEqual(decisions.open_requests(rdir), [])


class Reviews(Base):
    def make_store(self, attempt_state):
        path = Path(self.temp.name) / "m6.sqlite3"
        conn = sqlite3.connect(path)
        conn.execute("CREATE TABLE requests (idempotency_key TEXT, request_json TEXT, result_json TEXT)")
        conn.execute("CREATE TABLE reviews (request_key TEXT, state TEXT)")
        conn.execute("INSERT INTO requests VALUES ('k1', ?, ?)",
                     (json.dumps({"task_id": "T9", "attempt_id": "att-9"}),
                      json.dumps({"issues": [{"code": "SNAPSHOT_INVALID", "detail": "bad"}],
                                  "checks": [{"command": "git diff --quiet", "status": "unknown", "issue_code": "SNAPSHOT_INVALID"}]})))
        conn.execute("INSERT INTO reviews VALUES ('k1', 'open')")
        conn.commit()
        conn.close()
        self.doc = {"revision": 1, "tasks": {}, "attempts": {"att-9": {"id": "att-9", "state": attempt_state}}}
        return path

    def test_an_open_review_of_a_live_attempt_is_an_unskippable_request(self):
        path = self.make_store("verifying")
        with patch.object(bt_run_stores, "paths", return_value={"m6": path}):
            [request] = decisions.open_requests(self.rdir)
        self.assertTrue(request["unskippable"])
        self.assertEqual([o["id"] for o in request["options"]], ["review_fail", "review_pass", "stop"])
        self.assertEqual(request["recommended"], "review_fail")
        self.assertTrue(any("SNAPSHOT_INVALID" in line for line in request["evidence"]))

    def test_a_review_says_whether_the_verifier_broke_or_a_person_must_check_by_hand(self):
        def ask(checks, issues):
            path = Path(self.temp.name) / "m6.sqlite3"
            path.unlink(missing_ok=True)
            conn = sqlite3.connect(path)
            conn.execute("CREATE TABLE requests (idempotency_key TEXT, request_json TEXT, result_json TEXT)")
            conn.execute("CREATE TABLE reviews (request_key TEXT, state TEXT)")
            conn.execute("INSERT INTO requests VALUES ('k1', ?, ?)", (json.dumps({"task_id": "T9", "attempt_id": "att-9"}),
                                                                      json.dumps({"checks": checks, "issues": issues})))
            conn.execute("INSERT INTO reviews VALUES ('k1', 'open')")
            conn.commit()
            conn.close()
            self.doc = {"revision": 1, "tasks": {}, "attempts": {"att-9": {"id": "att-9", "state": "verifying"}}}
            with patch.object(bt_run_stores, "paths", return_value={"m6": path}):
                return decisions.open_requests(self.rdir)[0]

        infra = ask([{"command": "npm test", "status": "unknown", "issue_code": "SANDBOX_UNAVAILABLE"}],
                    [{"code": "SANDBOX_UNAVAILABLE", "detail": "no sandbox"}])
        self.assertIn("no es un fallo de la tarea", infra["needs"])
        self.assertIn("No apruebes a mano", " ".join(infra["you_can"]))
        manual = ask([{"command": "Use the advisor on a phone", "status": "unknown", "issue_code": "CHECK_MANUAL"}], [])
        self.assertIn("a mano", manual["needs"])
        self.assertTrue(any(line.startswith("Comprobar a mano: Use the advisor on a phone") for line in manual["evidence"]))

    def test_a_review_of_an_attempt_that_moved_on_asks_nobody(self):
        path = self.make_store("cancelled")
        with patch.object(bt_run_stores, "paths", return_value={"m6": path}):
            self.assertEqual(decisions.open_requests(self.rdir), [])


class Answers(Base):
    def test_retry_reopens_the_task_through_the_operator_move_and_records_the_answer(self):
        with patch.object(ops, "apply", return_value=["T1: reopened"]) as apply, \
                patch.object(ops, "resume", return_value="watchdog started"):
            result = decisions.answer("p", "REQ-001", self.rdir, "T1:2", "retry", by="david")
        apply.assert_called_once()
        self.assertEqual(apply.call_args.args[3:5], ("reopen", "T1"))
        self.assertIn("T1: reopened", result)
        line = json.loads(decisions.answers_path(self.rdir).read_text().splitlines()[0])
        self.assertEqual((line["request"], line["option"], line["by"]), ("T1:2", "retry", "david"))
        self.doc = doc(state="ready")
        self.assertEqual(decisions.open_requests(self.rdir), [])

    def test_an_option_that_is_not_offered_or_a_missing_reason_is_refused_before_anything_runs(self):
        with patch.object(ops, "apply") as apply:
            with self.assertRaisesRegex(ValueError, "not offered"):
                decisions.answer("p", "REQ-001", self.rdir, "T1:2", "review_pass", "because")
            with self.assertRaisesRegex(ValueError, "needs --reason"):
                decisions.answer("p", "REQ-001", self.rdir, "T1:2", "retry_with_note", " ")
            with self.assertRaisesRegex(ValueError, "no open request"):
                decisions.answer("p", "REQ-001", self.rdir, "T9:1", "retry")
        apply.assert_not_called()
        self.assertFalse(decisions.answers_path(self.rdir).exists())

    def test_retry_with_note_saves_the_owner_text_for_the_next_prompt(self):
        with patch.object(ops, "apply", return_value=["T1: reopened"]), patch.object(ops, "resume", return_value=""):
            decisions.answer("p", "REQ-001", self.rdir, "T1:2", "retry_with_note", "use the fixture, not the network")
        self.assertIn("use the fixture", decisions.operator_notes(self.rdir, "T1"))
        self.assertEqual(decisions.operator_notes(self.rdir, "T2"), "")

    def test_a_review_decision_is_written_to_the_quality_store_with_the_owner_stopped(self):
        calls = []

        class Store:
            def __init__(self, path):
                calls.append(("open", str(path)))

            def resolve_review(self, key, operator, verdict, reason):
                calls.append(("resolve", key, operator, verdict, reason))

        path = Path(self.temp.name) / "m6.sqlite3"
        request = {"id": "k1", "task": "T9", "options": [decisions.PASS], "source": "review"}
        with patch.object(decisions, "open_requests", return_value=[request]), \
                patch.object(bt_run_stores, "paths", return_value={"m6": path}), \
                patch.object(ops, "stop_owner", return_value=1), patch.object(ops, "resume", return_value=""), \
                patch("bt_scheduler_quality.store.QualityStore", Store):
            decisions.answer("p", "REQ-001", self.rdir, "k1", "review_pass", "checked by hand", by="david")
        self.assertEqual(calls[1], ("resolve", "k1", "david", "PASS", "checked by hand"))


class OwnerNotes(Base):
    def test_the_owner_note_leads_the_retry_notes_of_the_prompt(self):
        import bt_scheduler_executor_wiring as wiring
        from types import SimpleNamespace

        path = decisions.notes_path(self.rdir, "T1")
        path.parent.mkdir(parents=True)
        path.write_text("use the fixture\n")
        kinds = {"T1": "implement", "T9": "audit"}

        class Plan:
            def task(self, task_id):
                if task_id not in kinds and task_id != "T2":
                    raise wiring.api.core.SchedulerError("UNKNOWN_TASK", task_id)
                return SimpleNamespace(meta={"kind": kinds.get(task_id, "implement")}, expected_paths=("docs/a.findings.json",))

        notes = wiring._with_owner_notes(self.rdir, Plan(), lambda request: "Continue from snapshot abc.")
        text = notes(SimpleNamespace(task_id="T1"))
        self.assertLess(text.index("use the fixture"), text.index("Continue from snapshot"))
        self.assertEqual(notes(SimpleNamespace(task_id="T2")), "Continue from snapshot abc.")

        decisions.write_audit_notes(self.rdir, "T2", "F1 (critical): the gateway never listens")
        text = notes(SimpleNamespace(task_id="T2"))
        self.assertLess(text.index("F1 (critical)"), text.index("Continue from snapshot"))
        self.assertIn("independent audit", text)

        audit_text = notes(SimpleNamespace(task_id="T9"))
        self.assertIn("findings ledger", audit_text)
        self.assertIn("`docs/a.findings.json`", audit_text)
        self.assertNotIn("findings ledger", text)
        self.assertEqual(wiring._with_owner_notes(self.rdir, Plan(), None)(SimpleNamespace(task_id="T404")), "")


class Announce(Base):
    def test_each_request_is_announced_once(self):
        sent = []
        first = decisions.announce("p", "REQ-001", self.rdir, notify=lambda title, text: sent.append(text))
        second = decisions.announce("p", "REQ-001", self.rdir, notify=lambda title, text: sent.append(text))
        self.assertEqual((first, second), (["T1:2"], []))
        self.assertEqual(len(sent), 1)
        self.assertIn("decisions", sent[0])

    def test_a_run_without_readable_state_announces_nothing(self):
        with patch.object(decisions, "_state", side_effect=sqlite3.OperationalError("no db")):
            self.assertEqual(decisions.announce("p", "REQ-001", self.rdir, notify=lambda *a: 1 / 0), [])


class WatchWaits(unittest.TestCase):
    def test_a_stalled_run_that_asks_is_not_finished_and_runs_again_once_answered(self):
        pending = iter([1, 1, 0])
        spawned, announced, sleeps = [], [], []

        class Owner:
            pid = 1

            def poll(self):
                return 0

        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        rdir = Path(temp.name)
        codes = iter([Owner(), Owner()])
        with patch.object(adapter, "authority", return_value=adapter.AUTHORITY), \
                patch.object(ops, "owner_pids", return_value=[]), \
                patch.object(adapter, "run_db_path", return_value=rdir / "SCHEDULER.db"):
            watcher = watch.Watch("p", "REQ-001", rdir, spawn=lambda resume: spawned.append(resume) or next(codes),
                                  free_bytes=lambda: 10 << 30, sleep=sleeps.append, log=lambda t: None,
                                  announce=lambda: announced.append(1), notify=lambda *a: None,
                                  pending=lambda: next(pending, 0))
            self.assertEqual(watcher.run(), 0)
        self.assertEqual(len(spawned), 2)          # it waited, then started the owner again
        self.assertTrue(announced)
        self.assertIn(watch.POLL_SECONDS * 4, sleeps)


if __name__ == "__main__":
    unittest.main()
