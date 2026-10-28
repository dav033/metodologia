"""The standing gate: the readiness of every next stage is cached by the plan files and reaches the owner as a reason to wait."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_stage_readiness as gate  # noqa: E402


def row(sub, ok, problem="", tasks=3, depends=""):
    return {"subplan": sub, "tasks": tasks, "ok": ok, "problem": problem, "depends_on_unfinished": depends}


class Gate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name)
        (self.rdir / "PLAN.json").write_text('{"schema_version": "1.3.0", "subplans": [{"id": "SP-3"}]}', encoding="utf-8")
        self.walk = patch("bt_plan_adapter.stage_readiness")
        self.compat = patch("bt_scheduler_adapter.plan_compatibility_report", return_value={})
        self.mock = self.walk.start()
        self.compat.start()
        self.addCleanup(self.walk.stop)
        self.addCleanup(self.compat.stop)

    def test_an_error_is_reported_once_on_the_subplan_that_introduces_it(self):
        self.mock.return_value = [row("SP-3", False, "PLAN_INVALID: COMPOSITION_MISSING: no gate; T3.3 cites T4.2"),
                                  row("SP-4", False, "PLAN_INVALID: COMPOSITION_MISSING: no gate; T3.3 cites T4.2"),
                                  row("SP-5", False, "PLAN_INVALID: COMPOSITION_MISSING: no gate; T3.3 cites T4.2; SP-5 lacks a gate with SP-1")]
        self.assertIn("COMPOSITION_MISSING", gate.problem_for(self.rdir, "SP-3"))
        self.assertIn("arrastra", gate.problem_for(self.rdir, "SP-4"))                 # inherited, not repeated
        self.assertIn("SP-5 lacks a gate", gate.problem_for(self.rdir, "SP-5"))
        self.assertNotIn("COMPOSITION_MISSING", gate.problem_for(self.rdir, "SP-5"))

    def test_an_approvable_stage_an_undefined_subplan_and_an_unknown_one_give_no_reason(self):
        self.mock.return_value = [row("SP-3", True), row("SP-7", False, "sin tareas", tasks=0),
                                  row("SP-8", False, "no se puede comprobar", depends="SP-7")]
        for sub in ("SP-3", "SP-7", "SP-8", "SP-99"):
            self.assertEqual(gate.problem_for(self.rdir, sub), "")

    def test_the_walk_runs_once_per_plan_content(self):
        self.mock.return_value = [row("SP-3", True)]
        gate.rows(self.rdir)
        gate.rows(self.rdir)
        self.assertEqual(self.mock.call_count, 1)
        (self.rdir / "PLAN.json").write_text('{"schema_version": "1.3.0", "subplans": [{"id": "SP-3"}], "changed": true}', encoding="utf-8")
        gate.rows(self.rdir)
        self.assertEqual(self.mock.call_count, 2)

    def test_a_plan_without_subplans_or_before_schema_13_is_not_judged(self):
        self.mock.return_value = [row("SP-3", False, "PLAN_INVALID: boom")]
        for text in ('{"tasks": []}', '{"schema_version": "1.2.0", "subplans": [{"id": "SP-3"}]}', "not json"):
            (self.rdir / "PLAN.json").write_text(text, encoding="utf-8")
            self.assertEqual((gate.rows(self.rdir), gate.problem_for(self.rdir, "SP-3")), ([], ""))

    def test_header_and_environment_errors_are_not_structure_errors(self):
        text = ("PLAN_INVALID: the stage cannot be approved: plan.plan_id: missing; classification_evidence: file references could not "
                "be verified against a repository (no repository roots available; register and clone the project's repositories); "
                "T3.3.coupling.evidence[4]: task 'T4.2' is not in this plan")
        self.assertEqual(gate._errors(text), ["T3.3.coupling.evidence[4]: task 'T4.2' is not in this plan"])

    def test_a_plan_that_cannot_be_walked_never_breaks_the_caller(self):
        self.mock.side_effect = RuntimeError("boom")
        self.assertEqual(gate.rows(self.rdir), [])
        self.assertEqual(gate.problem_for(self.rdir, "SP-3"), "")


if __name__ == "__main__":
    unittest.main()
