"""Concurrent sessions: the scheduler's safety rules, the shared-file lock, and a real two-repo parallel run."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

from test_marathon import TMP, MarathonCase  # noqa: E402,F401  (sets BITACORA_ROOT before bt_* imports)
import bt_lock  # noqa: E402
import bt_runstate as rs  # noqa: E402


def task(tid, repo=None, after=(), status="todo"):
    return {"id": tid, "repo": repo, "after": list(after), "status": status}


class SchedulerRules(unittest.TestCase):
    def ids(self, tasks, workers=2):
        return [t["id"] for t in rs.ready_batch({"tasks": tasks}, workers)]

    def test_different_repos_run_together_in_plan_order(self):
        self.assertEqual(self.ids([task("T1", "frontend"), task("T2", "backend")]), ["T1", "T2"])

    def test_same_repo_never_runs_twice_at_once(self):
        self.assertEqual(self.ids([task("T1", "backend"), task("T2", "backend"), task("T3", "frontend")]),
                         ["T1", "T3"])

    def test_a_task_without_a_repo_role_runs_alone_and_blocks_others(self):
        self.assertEqual(self.ids([task("T1"), task("T2", "backend")]), ["T1"])
        self.assertEqual(self.ids([task("T1", "backend"), task("T2")]), ["T1"])

    def test_dependencies_are_respected(self):
        tasks = [task("T1", "frontend"), task("T2", "backend", after=["T1"]), task("T3", "infra")]
        self.assertEqual(self.ids(tasks), ["T1", "T3"])

    def test_a_repo_already_in_progress_is_not_joined(self):
        tasks = [task("T1", "frontend", status="in_progress"), task("T2", "frontend"), task("T3", "backend")]
        self.assertEqual(self.ids(tasks), ["T3"])
        self.assertEqual(self.ids([task("T1", "frontend", status="in_progress"), task("T2")]), [])  # unscoped waits

    def test_default_is_sequential_and_the_cap_is_two(self):
        three = [task("T1", "a"), task("T2", "b"), task("T3", "c")]
        self.assertEqual(self.ids(three, workers=1), ["T1"])
        self.assertEqual(self.ids(three, workers=9), ["T1", "T2"])
        self.assertEqual(rs.ready_batch({"tasks": []}, 2), [])


class CentralLock(unittest.TestCase):
    def test_threads_do_not_interleave_read_modify_write(self):
        counter = TMP / "counter.txt"
        counter.write_text("0")

        def bump():
            for _ in range(40):
                with bt_lock.central_lock("test-counter"):
                    value = int(counter.read_text())
                    counter.write_text(str(value + 1))

        threads = [threading.Thread(target=bump) for _ in range(4)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual(int(counter.read_text()), 160)

    def test_lock_is_reentrant_and_released(self):
        with bt_lock.central_lock("test-reentrant"):
            with bt_lock.central_lock("test-reentrant"):
                pass
        lock = Path(os.environ["BITACORA_ROOT"]) / ".state" / "locks" / "central-test-reentrant.lock"
        self.assertFalse(lock.exists())

    def test_two_processes_serialize(self):
        counter = TMP / "proc-counter.txt"
        counter.write_text("0")
        code = (f"import sys; sys.path.insert(0, {str(SCRIPTS)!r})\nimport bt_lock, pathlib\n"
                f"p = pathlib.Path({str(counter)!r})\nfor _ in range(30):\n"
                f"    with bt_lock.central_lock('test-proc'):\n        p.write_text(str(int(p.read_text()) + 1))\n")
        procs = [subprocess.Popen([sys.executable, "-c", code], env=os.environ.copy()) for _ in range(3)]
        [p.wait(timeout=60) for p in procs]
        self.assertEqual(int(counter.read_text()), 90)


STUB = '''
import os, pathlib, subprocess, sys, time
d = pathlib.Path(os.environ["STUB_DIR"]); tid = os.environ["BITACORA_TASK"]
(d / ("start-" + tid)).write_text(str(time.time()))
time.sleep(float(os.environ.get("STUB_SLEEP", "1.2")))
(d / ("end-" + tid)).write_text(str(time.time()))
if tid == "FINAL":
    pathlib.Path(os.environ["STUB_RDIR"], "REPORT.md").write_text("# report\\n"); sys.exit(0)
subprocess.run([sys.executable, os.environ["STUB_SCRIPT"], "--project", os.environ["BITACORA_PROJECT"], "task",
                "done", os.environ["BITACORA_RUN"], tid, "--evidence", "stub " + tid], check=True)
'''


class ParallelRun(MarathonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pstub = TMP / "pstub.py"
        cls.pstub.write_text(STUB, encoding="utf-8")

    def go(self, tasks, workers):
        self.make_req(tasks)
        os.environ["STUB_DIR"] = str(self.work)
        self.cmd = f'"{sys.executable}" "{self.pstub.as_posix()}"'
        return self.run_sup(workers=workers)

    def stamp(self, kind, tid):
        return float((self.work / f"{kind}-{tid}").read_text())

    def overlapped(self, a, b):
        return self.stamp("start", a) < self.stamp("end", b) and self.stamp("start", b) < self.stamp("end", a)

    def test_two_repos_overlap_and_the_join_task_waits_for_both(self):
        code = self.go(["- [ ] T1 — front · repo: frontend", "- [ ] T2 — back · repo: backend",
                        "- [ ] T3 — join · after: T1, T2"], workers=2)
        self.assertEqual(code, 0)
        self.assertTrue(self.overlapped("T1", "T2"))
        self.assertGreaterEqual(self.stamp("start", "T3"), max(self.stamp("end", "T1"), self.stamp("end", "T2")))
        state = self.state()
        self.assertEqual(state["status"], "done")
        self.assertTrue(all(t["status"] == "done" for t in state["tasks"]))
        sessions = [e["session"] for e in state["log"]]
        self.assertEqual(len(sessions), len(set(sessions)))  # reserved numbers never collide
        self.assertEqual(state["sessions"], 4)
        plan = (self.rdir / "PLAN.md").read_text(encoding="utf-8")
        self.assertIn("[x] T1", plan)
        self.assertIn("[x] T2", plan)
        self.assertEqual(state["heartbeat"].get("session_pids"), {})  # nothing left tracked

    def test_default_run_stays_sequential(self):
        self.assertEqual(self.go(["- [ ] T1 — front · repo: frontend", "- [ ] T2 — back · repo: backend"],
                                 workers=None), 0)
        self.assertFalse(self.overlapped("T1", "T2"))

    def test_same_repo_tasks_never_overlap_even_with_two_workers(self):
        self.assertEqual(self.go(["- [ ] T1 — a · repo: backend", "- [ ] T2 — b · repo: backend"], workers=2), 0)
        self.assertFalse(self.overlapped("T1", "T2"))


if __name__ == "__main__":
    unittest.main()
