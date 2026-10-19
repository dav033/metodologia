import io
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import bt_cli_go as go


def done(rc=0, out="", err=""):
    return subprocess.CompletedProcess([], rc, out, err)


class Go(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.rdir = self.root / "p" / "requirements" / "REQ-001-x"
        self.rdir.mkdir(parents=True)
        (self.rdir / "SPEC.md").write_text("s")
        (self.rdir / "PLAN.md").write_text("p")
        (self.rdir / "PLAN.json").write_text("{}")
        self.calls = []

    def run_go(self, checks, handoff="launched", **kw):
        checks = list(checks)

        def cli(project, *args, **extra):
            self.calls.append(args[:2] if args[0] == "plan-json" else args[:1])
            if args[:2] == ("plan-json", "check"):
                return checks.pop(0) if len(checks) > 1 else checks[0]
            return done()
        out = io.StringIO()
        with patch.object(go, "_cli", cli), patch("bt_handoff.handoff", return_value={"decision": handoff}) as h, \
                redirect_stdout(out):
            rc = go.run(self.root, "p", "REQ-001", **kw)
        return rc, h, out.getvalue()

    def test_an_already_valid_plan_goes_straight_to_the_handoff(self):
        rc, handoff, _ = self.run_go([done(0)])
        self.assertEqual(rc, 0)
        handoff.assert_called_once()
        self.assertNotIn(("planner",), self.calls)

    def test_an_incomplete_plan_is_classified_by_the_planner_then_launched(self):
        rc, handoff, _ = self.run_go([done(2, "gaps"), done(0)])
        self.assertEqual(rc, 0)
        self.assertIn(("planner",), self.calls)
        handoff.assert_called_once()

    def test_a_plan_the_planner_cannot_fix_is_not_launched(self):
        rc, handoff, out = self.run_go([done(2, "still bad")])
        self.assertEqual(rc, 2)
        handoff.assert_not_called()
        self.assertEqual(self.calls.count(("planner",)), go.ATTEMPTS)
        self.assertIn("still bad", out)

    def test_no_ai_never_calls_the_planner(self):
        rc, handoff, _ = self.run_go([done(2, "gaps")], no_ai=True)
        self.assertEqual(rc, 2)
        self.assertNotIn(("planner",), self.calls)
        handoff.assert_not_called()

    def test_risk_reasons_stop_at_the_owner_approval(self):
        rc, _, out = self.run_go([done(0)], handoff="needs_approval")
        self.assertEqual(rc, 3)
        self.assertIn("plan approve", out)

    def test_missing_spec_is_refused(self):
        (self.rdir / "SPEC.md").unlink()
        rc, handoff, _ = self.run_go([done(0)])
        self.assertEqual(rc, 2)
        handoff.assert_not_called()

    def test_missing_plan_json_is_initialised_first(self):
        (self.rdir / "PLAN.json").unlink()
        rc, _, _ = self.run_go([done(0)])
        self.assertEqual(self.calls[0], ("plan-json", "init"))


if __name__ == "__main__":
    unittest.main()
