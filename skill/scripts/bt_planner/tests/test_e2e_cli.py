"""End to end through the real command line, in a fresh isolated interpreter (`python -I`), from an unrelated cwd."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PACKAGE_PARENT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from support import classify  # noqa: E402

LAUNCHER = ("import sys; sys.path.insert(0, sys.argv[1]); from bt_planner.cli import main; "
            "sys.exit(main(sys.argv[2:]))")

PLAN_MD = """---
status: {status}
---
# Plan

### M1 — Build
- [ ] T1 — First · repo: app · files: src/a.py · verify: `python -m unittest`
- [ ] T2 — Second · repo: app · after: T1

### M2 — Ship
- [ ] T3 — Third · repo: app · after: T2 · verify: `python3 -m unittest discover -q`
"""


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="planner-e2e-")
        self.addCleanup(self._tmp.cleanup)
        self.base = Path(self._tmp.name)
        self.work = self.base / "REQ-200-shipping"
        self.work.mkdir()
        (self.work / "SPEC.md").write_text("# Spec\n## Requirements\n- R1. Demo requirement\n", encoding="utf-8")
        self.set_status("in-progress")
        self.elsewhere = self.base / "unrelated-cwd"
        self.elsewhere.mkdir()

    def set_status(self, status: str) -> None:
        (self.work / "PLAN.md").write_text(PLAN_MD.format(status=status), encoding="utf-8")

    def cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-I", "-c", LAUNCHER, str(PACKAGE_PARENT), *args], capture_output=True,
                              text=True, cwd=self.elsewhere, env={"PATH": "/usr/bin:/bin"}, timeout=60)

    def test_the_whole_session(self):
        # 1. a skeleton is derived and is honestly incomplete
        out = self.cli("init", str(self.work))
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("complexity x3", out.stdout)
        self.assertEqual(self.cli("init", str(self.work)).returncode, 2)  # refuses to overwrite
        out = self.cli("check", str(self.work))
        self.assertEqual(out.returncode, 2)
        self.assertIn("ERROR T1.complexity", out.stdout)
        # 2. the planner classifies; the gate passes
        plan = classify(json.loads((self.work / "PLAN.json").read_text(encoding="utf-8")))
        plan["tasks"][1]["kind"] = "docs"
        (self.work / "PLAN.json").write_text(json.dumps(plan), encoding="utf-8")
        out = self.cli("check", str(self.work), "--json")
        self.assertEqual((out.returncode, json.loads(out.stdout)["ok"]), (0, True), out.stdout)
        # 3. freeze needs approval, then freezes once and is idempotent
        self.assertIn("PLAN_NOT_APPROVED", self.cli("freeze", str(self.work)).stdout)
        self.set_status("approved")
        first = self.cli("freeze", str(self.work))
        self.assertEqual(first.returncode, 0, first.stdout)
        self.assertEqual(self.cli("freeze", str(self.work)).stdout, first.stdout)
        self.assertIn("r1@", self.cli("show", str(self.work)).stdout)
        # 4. an edit is a draft: binding refuses it until its approval freezes revision 2
        plan["tasks"][0]["estimated_minutes"] = 99
        (self.work / "PLAN.json").write_text(json.dumps(plan), encoding="utf-8")
        self.assertEqual(self.cli("check", str(self.work)).returncode, 0)
        self.assertIn("PLAN_DRIFT", self.cli("bind", str(self.work)).stdout)
        self.assertEqual(self.cli("freeze", str(self.work)).returncode, 0)
        self.assertIn("r2@", self.cli("show", str(self.work)).stdout)
        # 5. PLAN.md drifting from PLAN.json is caught
        text = (self.work / "PLAN.md").read_text(encoding="utf-8").replace("after: T2", "after: T1")
        (self.work / "PLAN.md").write_text(text, encoding="utf-8")
        out = self.cli("check", str(self.work))
        self.assertEqual(out.returncode, 2)
        self.assertIn("T3.after", out.stdout)
        # 6. read-only compat and standalone validation of the bundled example
        compat = json.loads(self.cli("compat", str(self.work)).stdout)
        self.assertEqual((compat["plan_id"], compat["task_count"], compat["has_plan_json"]), ("REQ-200", 3, True))
        example = self.base / "example.json"
        example.write_text(self.cli("example").stdout, encoding="utf-8")
        self.assertEqual(self.cli("validate", str(example)).returncode, 0)
        self.assertIn('"$schema"', self.cli("schema").stdout)
        # 7. only the documented places were written
        self.assertEqual(sorted(p.name for p in self.work.iterdir()),
                         ["PLAN.json", "PLAN.md", "SPEC.md", "plan-revisions"])
        self.assertEqual(sorted(p.name for p in (self.work / "plan-revisions").iterdir()),
                         ["MANIFEST.json", "PLAN.r1.json", "PLAN.r2.json"])

    def test_bad_usage_exits_2_without_a_traceback(self):
        for args in (("check",), ("check", str(self.base / "nope")), ("validate", str(self.base / "nope.json"))):
            with self.subTest(args=args):
                out = self.cli(*args)
                self.assertEqual(out.returncode, 2)
                self.assertNotIn("Traceback", out.stderr + out.stdout)
        self.assertEqual(self.cli("frobnicate").returncode, 2)  # argparse refusal

    def test_help_documents_the_actions(self):
        out = self.cli("--help")
        self.assertEqual(out.returncode, 0)
        for action in ("init", "check", "freeze", "show", "compat", "validate", "schema", "example"):
            self.assertIn(action, out.stdout)


if __name__ == "__main__":
    unittest.main()
