"""The module's own lock: busy, stale recovery, cross-process mutual exclusion."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

PACKAGE_PARENT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACKAGE_PARENT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bt_planner import _lock  # noqa: E402
from bt_planner import contract as pc  # noqa: E402
from bt_planner import sync  # noqa: E402
from support import classify  # noqa: E402


class Lock(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="planner-lock-")
        self.addCleanup(self._tmp.cleanup)
        self.folder = Path(self._tmp.name) / "plan-revisions"
        self.lock = self.folder / ".freeze.lock"

    def test_acquire_release_leaves_no_lock_file(self):
        with _lock.exclusive(self.lock):
            self.assertTrue(self.lock.exists())
        self.assertFalse(self.lock.exists())

    def test_a_fresh_lock_held_elsewhere_times_out_with_a_diagnostic(self):
        self.folder.mkdir()
        self.lock.write_text("held", encoding="utf-8")  # another process, still fresh
        with self.assertRaises(pc.PlanContractError) as ctx:
            with _lock.exclusive(self.lock, timeout=0.3):
                self.fail("must not be acquired")
        self.assertEqual(ctx.exception.code, "REVISION_STORE_BUSY")
        self.assertTrue(self.lock.exists())  # a lock we do not own is never removed

    def test_a_stale_lock_from_a_crashed_holder_is_broken(self):
        self.folder.mkdir()
        self.lock.write_text("crashed", encoding="utf-8")
        old = time.time() - _lock.STALE_SECONDS - 5
        os.utime(self.lock, (old, old))
        with _lock.exclusive(self.lock, timeout=2):
            pass
        self.assertFalse(self.lock.exists())

    def test_the_lock_is_released_when_the_critical_section_raises(self):
        with self.assertRaises(RuntimeError):
            with _lock.exclusive(self.lock):
                raise RuntimeError("boom")
        self.assertFalse(self.lock.exists())
        with _lock.exclusive(self.lock, timeout=1):
            pass

    def test_unwritable_location_is_a_diagnostic(self):
        blocker = Path(self._tmp.name) / "file"
        blocker.write_text("x", encoding="utf-8")
        with self.assertRaises(pc.PlanContractError) as ctx:
            with _lock.exclusive(blocker / "plan-revisions" / ".freeze.lock"):
                pass
        self.assertEqual(ctx.exception.code, "REVISION_STORE_UNWRITABLE")


class AcrossProcesses(unittest.TestCase):
    def test_concurrent_freezes_from_separate_processes_agree(self):
        with tempfile.TemporaryDirectory(prefix="planner-procs-") as tmp:
            plan_dir = Path(tmp) / "REQ-300-race"
            plan_dir.mkdir()
            (plan_dir / "SPEC.md").write_text("# s\n", encoding="utf-8")
            (plan_dir / "PLAN.md").write_text("---\nstatus: approved\n---\n### M1 — A\n- [ ] T1 — One · repo: app · "
                                              "verify: `python3 -m unittest -q`\n", encoding="utf-8")
            (plan_dir / "PLAN.json").write_text(pc.dumps(classify(sync.skeleton(plan_dir))), encoding="utf-8")
            code = ("import sys; sys.path.insert(0, sys.argv[1]); import bt_planner as p; from pathlib import Path; "
                    "print(p.approve_freeze(Path(sys.argv[2]))['revision'])")
            procs = [subprocess.Popen([sys.executable, "-I", "-c", code, str(PACKAGE_PARENT), str(plan_dir)],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(5)]
            results = [(p.communicate(timeout=60), p.returncode) for p in procs]
            for (out, err), rc in results:
                self.assertEqual(rc, 0, err)
                self.assertEqual(out.strip(), "1")
            from bt_planner import revisions as rev
            self.assertEqual([r["revision"] for r in rev.list_revisions(plan_dir)], [1])
            self.assertEqual(rev.verify_store(plan_dir), [])
            self.assertEqual([p.name for p in (plan_dir / "plan-revisions").iterdir() if p.name.startswith(".") or
                              p.name.endswith(".tmp")], [])


if __name__ == "__main__":
    unittest.main()
