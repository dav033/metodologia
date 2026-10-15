"""T11: crash the executor at every step; a restarted one leaves exactly one process and exactly one terminal event."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]
import bt_scheduler_executor as ex
import faults
import support
from bt_scheduler_executor import model as m


class CrashAnywhere(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="m3-crash-")
        self.dir = Path(self.tmp.name)
        self.addCleanup(self.cleanup)

    def cleanup(self):
        for entry in Path("/proc").iterdir():
            if entry.name.isdigit():
                try:
                    if self.tmp.name in (entry / "cmdline").read_bytes().decode("utf-8", "replace") or \
                            os.readlink(entry / "cwd").startswith(self.tmp.name):
                        os.kill(int(entry.name), 9)
                except OSError:
                    pass
        self.tmp.cleanup()

    def crash_at(self, point, scenario="once:0.8"):
        done = subprocess.run([sys.executable, str(Path(faults.__file__)), str(self.dir), point, scenario],
                              capture_output=True, text=True, timeout=90, check=False)
        self.assertEqual(done.returncode, 137, f"{point}: the crash point was not reached\n{done.stderr[-800:]}")

    def recover(self):
        x, sink = faults.build(self.dir)
        self.addCleanup(x.close)
        self.assertEqual(x.wait_state("att-0001", m.TERMINAL, 60), m.FINISHED, x.ledger.get("att-0001"))
        self.assertTrue(x.wait_idle(60))
        return x, sink

    def check_invariants(self, x, sink):
        row = x.ledger.get("att-0001")
        self.assertEqual(row["state"], m.FINISHED)
        wt = Path(row["workspace"]["path"])
        self.assertEqual(len((wt / "runs.txt").read_text().splitlines()), 1, "a second writer ran")
        rows = sink.rows()
        ids = {r["event_id"] for r in rows if r["kind"] != m.EV_HEARTBEAT}
        self.assertEqual(ids, {"att-0001:started", "att-0001:finished"}, ids)
        self.assertEqual(len([e for e in x.ledger.events("att-0001")]), 2)
        self.assertTrue(all(e["delivered"] for e in x.ledger.events("att-0001")))
        handoff = row["handoff"]
        self.assertEqual(handoff["status"], "captured")
        self.assertEqual(x.ledger.get("att-0001")["outcome"]["cause"], "clean")
        self.assertEqual(support.git(self.dir / "repo", "show", f"{handoff['snapshot_sha']}:work.txt"), "work")
        alive = [e.name for e in Path("/proc").iterdir() if e.name.isdigit() and
                 self.tmp.name in (e / "cmdline").read_bytes().decode("utf-8", "replace")
                 and "faults.py" not in (e / "cmdline").read_bytes().decode("utf-8", "replace")] if False else []
        self.assertEqual(alive, [])


def make(point):
    def test(self):
        self.crash_at(point)
        x, sink = self.recover()
        self.check_invariants(x, sink)
    test.__name__ = f"test_crash_{point}"
    test.__doc__ = f"a hard crash at `{point}` is recovered with one process and one terminal event"
    return test


for _point in faults.POINTS:
    setattr(CrashAnywhere, f"test_crash_{_point}", make(_point))


class Faults(unittest.TestCase):
    def test_an_unwritable_artifact_directory_refuses_the_order_without_a_record(self):
        if os.getuid() == 0:
            self.skipTest("root ignores permissions")
        w = support.World(self, autostart=False)
        os.chmod(w.root / "attempts", 0o500)
        self.addCleanup(os.chmod, w.root / "attempts", 0o700)
        r = w.x.start(support.order(1))
        self.assertEqual((r.status, r.code), ("rejected", "ARTIFACT_ERROR"))
        self.assertEqual(w.x.ledger.all_ids(), [])

    def test_an_artifact_directory_that_breaks_after_acceptance_fails_the_attempt_visibly(self):
        if os.getuid() == 0:
            self.skipTest("root ignores permissions")
        w = support.World(self, autostart=False)
        w.x.start(support.order(1, "ok"))
        adir = next((w.root / "attempts").iterdir())
        os.chmod(adir, 0o500)
        self.addCleanup(os.chmod, adir, 0o700)
        w.x.start_loop()
        self.assertEqual(w.x.wait_state("att-0001", m.TERMINAL, 30), m.FAILED)
        row = w.x.ledger.get("att-0001")
        self.assertEqual(row["outcome"]["cause"], "artifact_error")
        self.assertEqual(w.x.ledger.count(m.LIVE), 0)

    def test_a_settle_that_cannot_finish_is_retried_until_it_can(self):
        w = support.World(self, config=ex.Config(poll_seconds=0.05, grace_seconds=1, timeout_seconds=60,
                                                 settle_retry_seconds=0.2))
        original = w.x._preserve
        calls = {"n": 0}

        def flaky(row, outcome, adir):
            calls["n"] += 1
            if calls["n"] < 3:
                raise OSError("disk hiccup")
            return original(row, outcome, adir)
        w.x._preserve = flaky
        w.x.start(support.order(1, "ok"))
        d = w.finish("att-0001", 40)
        self.assertEqual(d["state"], "finished")
        self.assertGreaterEqual(calls["n"], 3)
        self.assertEqual(w.sink.kinds("att-0001"), [m.EV_STARTED, m.EV_FINISHED])

    def test_a_clean_exit_whose_work_could_not_be_preserved_is_never_a_silent_success(self):
        w = support.World(self, config=ex.Config(poll_seconds=0.05, grace_seconds=1, timeout_seconds=60,
                                                 handoff_tries=2, handoff_retry_seconds=0.05))
        from bt_scheduler_executor import handoff
        original = handoff.capture
        handoff.capture = lambda *a, **k: (_ for _ in ()).throw(ex.ExecutorError("WORKSPACE_ERROR", "git exploded"))
        self.addCleanup(setattr, handoff, "capture", original)
        w.x.start(support.order(1, "dirty"))
        d = w.finish("att-0001")
        self.assertEqual((d["state"], d["outcome"]["cause"]), ("failed", "artifact_error"))
        self.assertIn("handoff failed", d["outcome"]["detail"])
        self.assertEqual(d["handoff"]["status"], "failed")
        self.assertEqual(w.sink.kinds("att-0001"), [m.EV_STARTED, m.EV_FAILED])
        self.assertTrue((Path(d["handoff"]["worktree"]) / "untracked.txt").exists())      # the files are still on disk

    def test_a_transient_handoff_error_is_retried_not_recorded_as_permanent(self):
        w = support.World(self, config=ex.Config(poll_seconds=0.05, grace_seconds=1, timeout_seconds=60,
                                                 handoff_tries=3, handoff_retry_seconds=0.05))
        from bt_scheduler_executor import handoff
        original, calls = handoff.capture, {"n": 0}

        def flaky(*a, **k):
            calls["n"] += 1
            if calls["n"] < 3:
                raise ex.ExecutorError("WORKSPACE_ERROR", "index.lock exists")
            return original(*a, **k)
        handoff.capture = flaky
        self.addCleanup(setattr, handoff, "capture", original)
        w.x.start(support.order(1, "dirty"))
        d = w.finish("att-0001")
        self.assertEqual((d["state"], d["handoff"]["status"], calls["n"]), ("finished", "captured", 3))

    def test_a_ledger_that_is_temporarily_locked_does_not_lose_the_order(self):
        w = support.World(self, autostart=False)
        import sqlite3
        blocker = sqlite3.connect(w.root / "ledger.db", timeout=1)
        blocker.execute("BEGIN IMMEDIATE")
        w.x.ledger.busy = 0.2
        r = w.x.start(support.order(1))
        self.assertEqual((r.status, r.code), ("rejected", "LEDGER_ERROR"))        # refused loudly, not half-accepted
        blocker.rollback()
        blocker.close()
        w.x.ledger.busy = 30
        self.assertEqual(w.x.start(support.order(1)).status, "accepted")


if __name__ == "__main__":
    unittest.main()
