"""A retry knows what earlier attempts tried and how they failed, and is told plainly when they keep failing the same way."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bt_attempt_history as history
import bt_block_diagnosis as rules

ESLINT = ("$ npm run verify\nexit code 2\nError [ERR_MODULE_NOT_FOUND]: Cannot find package '@eslint/eslintrc' "
          "imported from /workspace/{run}/remote/web/eslint.config.mjs\n    at node:internal/{n}")


def doc(*attempts, task="T15"):
    return {"tasks": {task: {"attempts": [a for a, _, _ in attempts]}},
            "attempts": {a: {"id": a, "state": state, "failure": failure} for a, state, failure in attempts}}


class History(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.rdir = Path(self.temp.name)

    def test_the_same_failure_has_the_same_signature_across_attempts(self):
        one, two = ESLINT.format(run="att-0019", n=471), ESLINT.format(run="att-0027", n=12)
        self.assertEqual(history.signature(one), history.signature(two))
        self.assertNotEqual(history.signature(one), history.signature("$ npm test\nexit code 1\nAssertionError: 3 != 4"))

    def test_a_retry_sees_every_earlier_attempt_and_a_warning_when_they_repeat(self):
        for n, attempt in enumerate(("att-1", "att-2", "att-3")):
            history.record(self.rdir, "T15", attempt, ESLINT.format(run=attempt, n=n))
        run = doc(("att-0", "failed", "start rejected: INTEGRATION_CONFLICT: T8a vs T15b for T15: a.py"),
                  ("att-1", "rejected", "m6://result/a"), ("att-2", "rejected", "m6://result/b"),
                  ("att-3", "rejected", "m6://result/c"), ("att-4", "running", ""))
        text = history.prompt(self.rdir, "T15", run)
        self.assertIn("#1 att-0: failed: start rejected: INTEGRATION_CONFLICT", text)
        self.assertIn("#2 att-1: verification failed: $ npm run verify", text)
        self.assertIn("ERR_MODULE_NOT_FOUND", text)
        self.assertIn("#4 att-3: verification failed: the same failure as attempt #2", text)
        self.assertIn("WARNING: the last 3 attempts failed in exactly the same way", text)
        self.assertNotIn("att-4", text)                                  # the live attempt is the one being prompted
        self.assertEqual(history.repeats(history.entries(self.rdir, "T15", run)), 3)

    def test_a_first_attempt_gets_no_section_and_different_failures_no_warning(self):
        self.assertEqual(history.prompt(self.rdir, "T15", doc(("att-1", "running", ""))), "")
        history.record(self.rdir, "T15", "att-1", ESLINT.format(run="x", n=1))
        history.record(self.rdir, "T15", "att-2", "$ npm test\nexit code 1\nAssertionError: 3 != 4")
        text = history.prompt(self.rdir, "T15", doc(("att-1", "rejected", "m6://a"), ("att-2", "rejected", "m6://b")))
        self.assertNotIn("WARNING", text)

    def test_an_accepted_result_later_sent_back_and_old_attempts_are_summarised(self):
        rows = [(f"att-{n}", "cancelled", "cancelled by operator: wrong base") for n in range(8)]
        rows.append(("att-8", "accepted", ""))
        text = history.prompt(self.rdir, "T15", doc(*rows))
        self.assertIn("(3 older attempt(s) not shown)", text)
        self.assertIn("accepted, later sent back", text)
        self.assertIn("cancelled: cancelled by operator: wrong base", text.splitlines()[2])

    def test_the_card_says_a_known_cause_keeps_coming_back(self):
        request = {"id": "T15:4", "source": "task", "task": "T15", "options": [{"id": "retry"}, {"id": "retry_with_note"}],
                   "reason": "m5:attempts_exhausted", "error": "", "project": "demo"}
        diagnosis, _ = rules.explain(request, {}, verify=ESLINT.format(run="x", n=1), repeats=3)
        self.assertEqual(diagnosis["kind"], "dependency")
        self.assertIn("Ya van 3 intentos seguidos", diagnosis["origin"])
        diagnosis, _ = rules.explain(request, {}, verify="AssertionError: 3 != 4", repeats=2)
        self.assertEqual(diagnosis["headline"], "Los últimos 2 intentos fallaron exactamente igual")


class Wiring(unittest.TestCase):
    def test_m6_rejections_are_recorded_with_their_attempt(self):
        from bt_scheduler_quality_adapter import QualityVerificationPort
        seen, notes = [], []
        port = QualityVerificationPort.__new__(QualityVerificationPort)
        port.verify_notes, port.verify_history = (lambda task, text: notes.append(text)), (lambda *a: seen.append(a))
        port._failure_digest = lambda result: "$ npm test\nexit code 1"
        port._write_verify_note(SimpleNamespace(task_id="T1", attempt_id="att-7"), {"status": "FAIL"})
        self.assertEqual(seen, [("T1", "att-7", "$ npm test\nexit code 1")])
        port._write_verify_note(SimpleNamespace(task_id="T1", attempt_id="att-8"), {"status": "PASS"})
        self.assertEqual(len(seen), 1)

    def test_the_retry_prompt_carries_the_history_before_the_last_failure(self):
        import bt_scheduler_decisions
        import bt_scheduler_executor_wiring as wiring
        with tempfile.TemporaryDirectory() as temp:
            rdir = Path(temp)
            history.record(rdir, "T1", "att-1", "$ npm test\nexit code 1\nAssertionError")
            bt_scheduler_decisions.write_verify_notes(rdir, "T1", "LAST FAILURE")
            plan = SimpleNamespace(task=lambda task_id: SimpleNamespace(meta={}, expected_paths=()))
            original = bt_scheduler_decisions._state
            bt_scheduler_decisions._state = lambda r: doc(("att-1", "rejected", "m6://x"), task="T1")
            try:
                text = wiring._with_owner_notes(rdir, plan, None)(SimpleNamespace(task_id="T1"))
            finally:
                bt_scheduler_decisions._state = original
        self.assertIn("Earlier attempts of this task", text)
        self.assertLess(text.index("Earlier attempts"), text.index("LAST FAILURE"))


if __name__ == "__main__":
    unittest.main()
