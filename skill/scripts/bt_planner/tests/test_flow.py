"""The planner cycle end to end through the API: skeleton -> classify -> gate -> approve -> freeze -> reread elsewhere."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bt_planner as planner  # noqa: E402
from bt_planner import contract as pc  # noqa: E402
from bt_planner import revisions as rev  # noqa: E402
from bt_planner import sync  # noqa: E402
from support import classify  # noqa: E402

PLAN_MD = """---
status: {status}
---
# Plan

### M1 — Auth fix
- [ ] T1 — Reject expired sessions · repo: app · files: src/auth/** · verify: `python -m unittest`
- [ ] T2 — Document it · repo: app · after: T1
"""


class PlannerCycle(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="planner-flow-")
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name) / "REQ-001-demo"
        self.dir.mkdir()
        (self.dir / "SPEC.md").write_text("# Spec\n## Requirements\n- R1. Demo requirement\n", encoding="utf-8")
        self.set_status("draft")

    def set_status(self, status: str) -> None:
        (self.dir / "PLAN.md").write_text(PLAN_MD.format(status=status), encoding="utf-8")

    def test_full_cycle_is_reproducible_and_starts_nothing(self):
        with patch.object(subprocess, "Popen", side_effect=AssertionError("the planner must not start processes")), \
                patch.object(subprocess, "run", side_effect=AssertionError("the planner must not start processes")):
            sync.write_skeleton(self.dir)
            self.assertFalse(sync.check(self.dir).ok)
            plan = classify(sync.skeleton(self.dir))
            plan["tasks"][0].update({"complexity": "low", "risk": "high", "scope": "isolated_fix",
                                     "shared_resources": ["auth-session-contract"], "coupling": "medium",
                                     "estimate_rationale": "Localised, sensitive because it touches auth"})
            (self.dir / "PLAN.json").write_text(pc.dumps(plan), encoding="utf-8")
            report = sync.check(self.dir)
            self.assertTrue(report.ok, report.errors)
            self.set_status("approved")
            entry = sync.approve_freeze(self.dir)
        first = (self.dir / "PLAN.json").read_text(encoding="utf-8")
        again = pc.dumps(json.loads(first))
        self.assertEqual(first, again)  # canonical, so reproducible
        self.assertEqual(entry["sha256"], rev.sha256(again))
        self.assertEqual(rev.load_revision(self.dir, 1), json.loads(first))
        self.assertEqual(sorted(p.name for p in self.dir.iterdir()),
                         ["PLAN.json", "PLAN.md", "SPEC.md", "plan-revisions"])

    def test_a_fresh_process_can_read_the_plan_without_the_planner(self):
        plan = classify(sync.skeleton(self.dir))
        (self.dir / "PLAN.json").write_text(pc.dumps(plan), encoding="utf-8")
        self.set_status("approved")
        sync.approve_freeze(self.dir)
        code = ("import sys; sys.path.insert(0, sys.argv[1]); import bt_planner as p; from pathlib import Path; "
                "d = Path(sys.argv[2]); print(p.load(d / 'PLAN.json')['plan_id'], p.load_revision(d, 1)['revision'], "
                "p.run_reference(d)['plan_ref']['revision'])")
        done = subprocess.run([sys.executable, "-I", "-c", code, str(Path(__file__).resolve().parents[2]),
                               str(self.dir)], capture_output=True, text=True, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stdout.split(), ["REQ-001", "1", "1"])

    def test_output_never_assigns_models_or_workers(self):  # scheduling is somebody else's decision
        text = pc.dumps(classify(sync.skeleton(self.dir)))
        for word in ('"model"', '"account"', '"workers"', '"agent"'):
            self.assertNotIn(word, text)

    def test_public_api_is_complete_and_importable(self):
        for name in planner.__all__:
            self.assertTrue(hasattr(planner, name), name)
        self.assertEqual(planner.SCHEMA_VERSION, "1.2.0")
        self.assertIn("plan_id", planner.example_text())


if __name__ == "__main__":
    unittest.main()
