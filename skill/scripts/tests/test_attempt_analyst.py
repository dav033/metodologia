"""P-138: a task that failed more than twice is analysed by a model that reads and advises; the next attempt's prompt carries it."""
from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bt_attempt_analyst as analyst  # noqa: E402
import bt_attempt_history as history  # noqa: E402


def doc_with(failed: int, accepted: bool = False) -> dict:
    attempts = {f"att-{n}": {"state": "failed", "failure": f"npm test failed: cannot find module x{n}"} for n in range(1, failed + 1)}
    names = list(attempts)
    if accepted:
        attempts["att-ok"] = {"state": "accepted"}
        names.append("att-ok")
    return {"tasks": {"T1": {"state": "ready", "attempts": names}}, "attempts": attempts}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name)


class Due(Base):
    def test_only_a_third_failure_asks_for_an_analysis(self):
        self.assertEqual(analyst.due(self.rdir, "T1", doc_with(2)), 0)
        self.assertEqual(analyst.due(self.rdir, "T1", doc_with(3)), 3)

    def test_an_analysis_is_not_repeated_until_two_more_failures_and_never_while_one_runs(self):
        analyst._save(self.rdir, "T1", {"state": "done", "failures": 3, "cause": "c", "solution": "s"})
        self.assertEqual(analyst.due(self.rdir, "T1", doc_with(4)), 0)
        self.assertEqual(analyst.due(self.rdir, "T1", doc_with(5)), 5)
        analyst._save(self.rdir, "T1", {"state": "running", "failures": 3, "started": time.time()})
        self.assertEqual(analyst.due(self.rdir, "T1", doc_with(9)), 0)
        analyst._save(self.rdir, "T1", {"state": "running", "failures": 3, "started": time.time() - 4000})   # a crashed analysis does not block for ever
        self.assertEqual(analyst.due(self.rdir, "T1", doc_with(9)), 9)


class Answer(Base):
    def test_parse_requires_cause_and_solution_and_keeps_the_flag(self):
        got = analyst.parse('text {"cause": "the mock is wrong", "solution": "1. fix it", "not_the_task": true, "confidence": "alta"} end')
        self.assertEqual((got["cause"], got["not_the_task"], got["confidence"]), ("the mock is wrong", True, "alta"))
        with self.assertRaises(ValueError):
            analyst.parse('{"cause": "x"}')
        with self.assertRaises(ValueError):
            analyst.parse("no json")

    def run_analysis(self, stdout: str, returncode: int = 0) -> dict:
        profile = {"provider": "claude", "bin": "claude"}
        config = {"profile": "p", "model": "m", "effort": "", "timeout_seconds": 5}
        with patch("bt_profiles.get", return_value=profile), patch("bt_profiles.authorize"), patch("bt_profiles.session_env", return_value={}), \
                patch("bt_scheduler_decisions.verify_notes", return_value="last failure"), patch("bt_scheduler_decisions.audit_notes", return_value=""), \
                patch("bt_scheduler_decisions.operator_notes", return_value=""):
            return analyst.analyze("p", self.rdir, "T1", config=config, doc=doc_with(3), plan={"tasks": [{"id": "T1", "title": "t"}]},
                                   runner=lambda *a, **k: SimpleNamespace(returncode=returncode, stdout=stdout, stderr="boom"))

    def test_a_good_answer_is_stored_and_reaches_the_next_prompt_as_an_opinion(self):
        done = self.run_analysis('{"cause": "module x is not installed", "solution": "1. add it", "confidence": "media"}')
        self.assertEqual(done["state"], "done")
        text = analyst.prompt(self.rdir, "T1")
        self.assertIn("module x is not installed", text)
        self.assertIn("check it against the code", text)
        self.assertIn("after 3 failed attempts", text)

    def test_a_failed_call_is_stored_and_adds_nothing_to_the_prompt(self):
        self.assertEqual(self.run_analysis("", returncode=2)["state"], "failed")
        self.assertEqual(analyst.prompt(self.rdir, "T1"), "")
        self.assertEqual(analyst.prompt(self.rdir, "T-none"), "")

    def test_the_outside_the_task_flag_is_said_in_the_prompt(self):
        self.run_analysis('{"cause": "no credential", "solution": "the owner adds it", "not_the_task": true}')
        self.assertIn("OUTSIDE what this task may change", analyst.prompt(self.rdir, "T1"))


class Bundle(Base):
    def test_the_task_text_comes_from_a_scheduler_plan_object_and_from_a_dict(self):
        spec = SimpleNamespace(id="T1", meta={"title": "Title", "objective": "Do it"}, acceptance_criteria=["works"], expected_paths=["a.py"],
                               verification=[{"type": "command", "value": "npm test"}], after=[])
        plan = SimpleNamespace(task=lambda tid: spec)
        with patch("bt_scheduler_decisions.verify_notes", return_value=""), patch("bt_scheduler_decisions.audit_notes", return_value=""), \
                patch("bt_scheduler_decisions.operator_notes", return_value=""):
            text = analyst.bundle(self.rdir, "T1", doc_with(3), plan)
            self.assertIn('"objective": "Do it"', text)
            self.assertIn("npm test", text)
            self.assertIn('"title": "t"', analyst.bundle(self.rdir, "T1", doc_with(3), {"tasks": [{"id": "T1", "title": "t"}]}))
            self.assertNotIn("THE TASK", analyst.bundle(self.rdir, "T1", doc_with(3), SimpleNamespace(task=lambda tid: 1 / 0)))


class Cycle(Base):
    def test_one_start_per_due_task_marked_before_it_starts_and_nothing_when_off(self):
        started = []
        doc = {**doc_with(3), "tasks": {"T1": {"state": "ready", "attempts": ["att-1", "att-2", "att-3"]},
                                        "T2": {"state": "completed", "attempts": []}}}
        with patch("bt_scheduler_decisions._state", return_value=doc):
            self.assertEqual(analyst.cycle("p", "REQ-1", self.rdir, starter=lambda *a: started.append(a) or True), 1)
            self.assertEqual(started, [("p", "REQ-1", "T1")])
            self.assertEqual(analyst.cycle("p", "REQ-1", self.rdir, starter=lambda *a: started.append(a) or True), 0)    # marked running
            with patch.object(analyst, "enabled", return_value=False):
                self.assertEqual(analyst.cycle("p", "REQ-1", self.rdir, starter=lambda *a: started.append(a) or True), 0)
        self.assertEqual(len(started), 1)


if __name__ == "__main__":
    unittest.main()
