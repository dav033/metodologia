"""End to end through the real command line in a fresh isolated interpreter (`python -I`) from an unrelated cwd,
plus the in-process simulation of the integration plan the module's own plan asks for (>= 6 tasks, 3 independent,
external verification, a local failure, a restart) (SC-AC06, SC-AC14, SC-AC20)."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]

from support import approved, indep, plan_text, sqlite_path, task

import bt_scheduler_core as sc
from bt_scheduler_core.simulation import Script, simulate

PACKAGE_PARENT = Path(__file__).resolve().parents[2]
LAUNCHER = ("import sys; sys.path.insert(0, sys.argv[1]); from bt_scheduler_core.cli import main; "
            "sys.exit(main(sys.argv[2:]))")

BIG = [indep("T1"), indep("T2", ["T1"]), indep("T3"), indep("T4", ["T3"]), indep("T5"), indep("T6", ["T2", "T4", "T5"]),
       task("T7", ["T6"], repo="docs", paths=["docs/**"], resources=["site"])]


class SimulatedWorld(unittest.TestCase):
    def test_six_plus_tasks_three_independent_branches_run_in_parallel_and_complete(self):
        plan, _ = approved(plan_text(BIG))
        snap, core = simulate(plan, sc.InMemoryRepository(), sc.Config(max_parallel_tasks=3))
        self.assertEqual(snap.status, "completed")
        starts = [e for e in core.audit_log() if e.kind == "reserved"]
        self.assertEqual(len(starts), 7)
        # the three independent roots were reserved before anything they unblock
        self.assertEqual({e.task_id for e in starts[:3]}, {"T1", "T3", "T5"})

    def test_one_local_failure_blocks_only_its_own_descendants(self):
        plan, _ = approved(plan_text(BIG))
        snap, _core = simulate(plan, sc.InMemoryRepository(), sc.Config(max_parallel_tasks=3), Script(fail={"T3": 1}))
        states = {k: v["state"] for k, v in snap.tasks.items()}
        self.assertEqual(states["T3"], "blocked")
        self.assertEqual({k for k, v in snap.tasks.items() if v["unreachable"]}, {"T4", "T6", "T7"})
        self.assertEqual((states["T1"], states["T2"], states["T5"]), ("completed",) * 3)
        self.assertEqual(snap.status, "blocked")

    def test_retries_and_rejections_follow_the_attempt_budget(self):
        plan, _ = approved(plan_text(BIG))
        snap, _core = simulate(plan, sc.InMemoryRepository(), sc.Config(max_parallel_tasks=3, max_attempts=3),
                               Script(fail={"T1": 1}, reject={"T2": 1}))
        self.assertEqual(snap.status, "completed")
        self.assertEqual((snap.tasks["T1"]["attempts"], snap.tasks["T2"]["attempts"]), (2, 2))

    def test_the_simulation_survives_a_restart_on_sqlite(self):
        tmp, path = sqlite_path()
        self.addCleanup(tmp.cleanup)
        plan, _ = approved(plan_text(BIG))
        simulate(plan, sc.SqliteRepository(path), sc.Config(max_parallel_tasks=3))
        reopened = sc.SchedulerCore(plan, sc.SqliteRepository(path)).inspect()
        self.assertEqual(reopened.status, "completed")

    def test_same_inputs_give_the_same_audit_trail(self):
        plan, _ = approved(plan_text(BIG))
        runs = []
        for _ in range(2):
            _snap, core = simulate(plan, sc.InMemoryRepository(), sc.Config(max_parallel_tasks=3), Script(fail={"T3": 1}),
                                   )
            runs.append([(e.kind, e.task_id, e.attempt_id, json.dumps(e.detail, sort_keys=True)) for e in core.audit_log()])
        self.assertEqual(runs[0], runs[1])


class CommandLine(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="sched-e2e-")
        self.addCleanup(self._tmp.cleanup)
        self.base = Path(self._tmp.name)
        self.elsewhere = self.base / "unrelated-cwd"
        self.elsewhere.mkdir()
        self.text = plan_text(BIG)
        self.plan_path = self.base / "PLAN.r1.json"
        self.plan_path.write_text(self.text, encoding="utf-8")
        self.sha = hashlib.sha256(self.text.encode()).hexdigest()

    def cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-I", "-c", LAUNCHER, str(PACKAGE_PARENT), *args], capture_output=True,
                              text=True, check=False, cwd=self.elsewhere, env={"PATH": "/usr/bin:/bin"}, timeout=120)

    def test_the_whole_session(self):
        out = self.cli("validate", str(self.plan_path), "--sha256", self.sha, "--json")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(json.loads(out.stdout)["tasks"], 7)
        bad = self.cli("validate", str(self.plan_path), "--sha256", "0" * 64)
        self.assertEqual(bad.returncode, 2)
        self.assertIn("PLAN_NOT_APPROVED", bad.stderr)
        db = self.base / "run.db"
        out = self.cli("simulate", str(self.plan_path), "--sha256", self.sha, "--db", str(db), "--parallel", "3", "--json")
        self.assertEqual(out.returncode, 0, out.stderr)
        data = json.loads(out.stdout)
        self.assertEqual(data["status"], "completed")
        self.assertGreater(data["audit_entries"], 50)
        status = self.cli("status", str(self.plan_path), "--sha256", self.sha, "--db", str(db), "--json")
        self.assertEqual(json.loads(status.stdout)["status"], "completed")
        audit = self.cli("audit", "--db", str(db), "--json")
        rows = json.loads(audit.stdout)
        self.assertEqual(rows[0]["kind"], "run_created")
        self.assertEqual(self.cli("audit", "--db", str(db), "--since", str(rows[-1]["seq"]), "--json").stdout.strip(), "[]")

    def test_status_is_read_only_and_refuses_another_plan(self):
        db = self.base / "run.db"
        self.cli("simulate", str(self.plan_path), "--sha256", self.sha, "--db", str(db))
        before = json.loads(self.cli("audit", "--db", str(db), "--json").stdout)
        self.cli("status", str(self.plan_path), "--sha256", self.sha, "--db", str(db))
        self.assertEqual(json.loads(self.cli("audit", "--db", str(db), "--json").stdout), before)
        other = self.base / "OTHER.json"
        other.write_text(plan_text(BIG[:3]), encoding="utf-8")
        refused = self.cli("status", str(other), "--sha256", hashlib.sha256(other.read_bytes()).hexdigest(), "--db", str(db))
        self.assertEqual(refused.returncode, 2)
        self.assertIn("PLAN_MISMATCH", refused.stderr)

    def test_failures_and_budget_via_flags(self):
        out = self.cli("simulate", str(self.plan_path), "--sha256", self.sha, "--parallel", "3", "--fail", "T3", "--json")
        self.assertEqual(json.loads(out.stdout)["status"], "blocked")
        out = self.cli("simulate", str(self.plan_path), "--sha256", self.sha, "--parallel", "3", "--fail", "T3:2",
                       "--max-attempts", "3", "--json")
        self.assertEqual(json.loads(out.stdout)["status"], "completed")

    def test_bad_input_is_a_clean_exit_code_not_a_traceback(self):
        for args in (["validate", str(self.base / "missing.json"), "--sha256", self.sha],
                     ["validate", str(self.plan_path)], ["audit", "--db", str(self.base / "nope" / "x.db")]):
            out = self.cli(*args)
            self.assertIn(out.returncode, (2,), (args, out.stderr))
            self.assertNotIn("Traceback", out.stderr)

    def test_the_plan_file_is_not_modified_by_any_command(self):
        before = self.plan_path.read_bytes()
        self.cli("simulate", str(self.plan_path), "--sha256", self.sha)
        self.assertEqual(self.plan_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
