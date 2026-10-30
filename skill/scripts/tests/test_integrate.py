"""The repo-owned integration (REQ-031 T1): what operators did by hand on 2026-10-29, in order, under one lock, and never
anything but a fast-forward in the live checkout (a no-ff merge there once reset the staged live bitácora, D-160).

Real git repositories in a temporary directory; the regression, the backup, the push and the units are a recording fake."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_integrate as integ
import bt_regress

ALLOWED = ("test_known_red",)      # a baseline the owner accepted; the default list is empty since 2026-10-29


def sh(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True).stdout.strip()


def commit(cwd: Path, path: str, text: str, message: str) -> str:
    target = Path(cwd) / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    sh(cwd, "add", path)
    sh(cwd, "commit", "-q", "-m", message)
    return sh(cwd, "rev-parse", "HEAD")


class Fake(integ.Services):
    def __init__(self, case, *, red: bool = False, smoke=None, during_regression=None):
        self.case, self.red, self.calls = case, red, []
        self.smokes = list(smoke or [])
        self.during_regression = during_regression

    def regress(self, worktree, scratch, out):
        self.calls.append(("regress", Path(worktree).name))
        if self.during_regression:
            self.during_regression()
        lines = ["test_a 0 1 python3", "test_known_red 1 1 python3"] + (["test_b 1 1 python3"] if self.red else [])
        return bt_regress.judge(lines, ALLOWED, rerun=lambda name: False)

    def backup(self):
        self.calls.append(("backup",))
        return "/backups/bt_durable-1.dump 10 abc"

    def push(self, live):
        self.calls.append(("push", sh(live, "rev-parse", "HEAD")))
        return ""

    def restart(self, unit):
        self.calls.append(("restart", unit))

    def smoke(self, units, since):
        self.calls.append(("smoke", tuple(units)))
        return self.smokes.pop(0) if self.smokes else []


class Integrate(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="bt-integrate-"))
        self.live = self.base / "metodologia"
        self.live.mkdir()
        sh(self.live, "init", "-q", "-b", "main")
        sh(self.live, "config", "user.name", "Test")
        sh(self.live, "config", "user.email", "test@example.invalid")
        commit(self.live, "skill/scripts/bt_x.py", "x = 1\n", "x")
        commit(self.live, "bitacora/log.md", "day 1\n", "log")
        self.previous = sh(self.live, "rev-parse", "HEAD")
        self.wt = self.base / "wt-fix"
        sh(self.live, "worktree", "add", "-q", "-b", "fix", str(self.wt), "main")
        self.tip = commit(self.wt, "skill/scripts/bt_x.py", "x = 2\n", "fix x")
        (self.live / "bitacora" / "log.md").write_text("day 1\nlive, uncommitted\n", encoding="utf-8")
        self.log = self.base / "pre-deploy.txt"
        self.lock = self.base / "state" / "integrate.lock"

    def request(self, **extra) -> integ.Request:
        fields = dict(branch="fix", worktree=self.wt, title="x is two (D-900)", session="s1", live=self.live,
                      deploy=self.base / "deploy", scratch=self.base / "scratch", log=self.log, lock=self.lock,
                      wait_seconds=0, trailers=["Co-Authored-By: Test <t@example.invalid>"])
        return integ.Request(**{**fields, **extra})

    def run_it(self, services, **extra) -> integ.Outcome:
        return integ.integrate(self.request(**extra), services, say=lambda text: None)

    def live_bitacora_intact(self):
        self.assertEqual((self.live / "bitacora" / "log.md").read_text(), "day 1\nlive, uncommitted\n")

    def test_the_steps_run_in_order_and_the_live_checkout_only_fast_forwards(self):
        fake = Fake(self)
        outcome = self.run_it(fake)
        self.assertEqual(outcome.code, 0, outcome.lines)
        head = sh(self.live, "rev-parse", "HEAD")
        self.assertEqual(sh(self.live, "rev-parse", "HEAD^1"), self.previous)
        self.assertEqual(sh(self.live, "rev-parse", "HEAD^2"), self.tip)        # a --no-ff merge, fast-forwarded here
        self.assertIn("Co-Authored-By: Test", sh(self.live, "log", "-1", "--format=%B"))
        self.assertEqual(sh(self.live, "symbolic-ref", "--short", "HEAD"), "main")
        self.assertEqual([c[0] for c in fake.calls], ["regress", "backup", "push", "restart", "restart", "smoke"])
        self.assertEqual(fake.calls[2], ("push", head))
        self.assertEqual([c[1] for c in fake.calls if c[0] == "restart"], [integ.ENGINE_UNIT, integ.WEB_UNIT])
        self.live_bitacora_intact()
        self.assertFalse(self.wt.exists())                                       # clean and merged: cleaned up
        self.assertEqual(sh(self.live, "branch", "--list", "fix"), "")
        entry = self.log.read_text()
        for text in (f"previous main: {self.previous}", "/backups/bt_durable-1.dump 10 abc",
                     "regression: 2 files, only baseline failures (test_known_red)", "rollback: git revert the "
                     "merge of fix on main, restart bt-durable.service and bitacora-web.service", "session s1",
                     "smoke ok"):
            self.assertIn(text, entry)

    def test_a_red_regression_integrates_nothing(self):
        fake = Fake(self, red=True)
        outcome = self.run_it(fake)
        self.assertEqual(outcome.code, 1)
        self.assertEqual(sh(self.live, "rev-parse", "HEAD"), self.previous)
        self.assertEqual([c[0] for c in fake.calls], ["regress"])
        self.assertEqual(sh(self.live, "rev-parse", "fix"), self.tip)               # the branch stays
        self.assertFalse(self.log.exists())
        self.assertIn("test_b", outcome.lines[-1])

    def test_one_integration_at_a_time(self):
        fake = Fake(self)
        with integ.machine_lock(self.lock):
            outcome = self.run_it(fake)
        self.assertEqual(outcome.code, integ.BUSY)
        self.assertEqual(fake.calls, [])
        self.assertEqual(self.run_it(fake).code, 0)                                  # released: the next one runs

    def test_a_refused_fast_forward_leaves_the_live_checkout_as_it_was(self):
        (self.live / "skill" / "scripts" / "bt_x.py").write_text("x = 'live edit'\n", encoding="utf-8")
        fake = Fake(self)
        outcome = self.run_it(fake)
        self.assertEqual(outcome.code, 2, outcome.lines)
        self.assertEqual(sh(self.live, "rev-parse", "HEAD"), self.previous)
        self.assertEqual((self.live / "skill" / "scripts" / "bt_x.py").read_text(), "x = 'live edit'\n")
        self.assertNotIn("restart", [c[0] for c in fake.calls])
        self.assertIn("result: not integrated", self.log.read_text())
        self.live_bitacora_intact()

    def test_cleanup_keeps_what_it_must(self):
        outcome = self.run_it(Fake(self), keep_worktree=True)
        self.assertEqual(outcome.code, 0, outcome.lines)
        self.assertTrue(self.wt.is_dir())
        self.assertEqual(sh(self.live, "rev-parse", "fix"), self.tip)
        self.assertIn("--keep-worktree", outcome.lines[-1])

    def test_cleanup_skips_a_worktree_the_caller_stands_in_or_with_untracked_files(self):
        outcome = self.run_it(Fake(self), cwd=self.wt / "skill")
        self.assertTrue(self.wt.is_dir())
        self.assertIn(f"worktree remove {self.wt.resolve()} && git -C {self.live.resolve()} branch -d fix",
                      outcome.lines[-1])
        self.setUp()
        (self.wt / "notes.txt").write_text("not committed\n", encoding="utf-8")
        outcome = self.run_it(Fake(self))
        self.assertEqual(outcome.code, 0, outcome.lines)
        self.assertTrue((self.wt / "notes.txt").is_file())
        self.assertEqual(sh(self.live, "rev-parse", "fix"), self.tip)
        self.assertIn("untracked", outcome.lines[-1])

    def test_cleanup_never_removes_the_deploy_worktree_nor_force_deletes_a_branch(self):
        lines: list[str] = []
        integ._clean_up(self.request(deploy=self.wt), lines.append)
        self.assertTrue(self.wt.is_dir())
        self.assertIn("never removed", lines[-1])
        integ._clean_up(self.request(), lines.append)                              # fix is not merged into main here
        self.assertFalse(self.wt.exists())
        self.assertEqual(sh(self.live, "rev-parse", "fix"), self.tip)             # -d refused it; nothing forces it
        self.assertIn("branch fix kept", lines[-1])

    def test_a_failed_smoke_reverts_the_merge(self):
        fake = Fake(self, smoke=[["bt-durable.service is failed"], []])
        outcome = self.run_it(fake)
        self.assertEqual(outcome.code, 3, outcome.lines)
        self.assertEqual(sh(self.live, "show", "HEAD:skill/scripts/bt_x.py"), "x = 1")
        self.assertEqual(sh(self.live, "rev-parse", "HEAD^"), outcome.merge)
        self.assertEqual([c[0] for c in fake.calls].count("restart"), 4)
        self.assertIn("reverted by", self.log.read_text())
        self.live_bitacora_intact()
        self.assertTrue(self.wt.is_dir())                                         # a reverted branch keeps its worktree

    def test_bitacora_commits_on_main_are_fine_but_code_is_not(self):
        def bitacora_commit():
            subprocess.run(["git", "-C", str(self.live), "commit", "-q", "-m", "bitácora", "--allow-empty"], check=True)
        self.assertEqual(self.run_it(Fake(self, during_regression=bitacora_commit)).code, 0)

    def test_code_landing_on_main_during_the_regression_stops_it(self):
        def code_commit():
            other = self.base / "wt-other"
            sh(self.live, "worktree", "add", "-q", "-b", "other", str(other), "main")
            commit(other, "skill/scripts/bt_y.py", "y = 1\n", "y")
            sh(self.live, "merge", "-q", "--ff-only", "other")
        outcome = self.run_it(Fake(self, during_regression=code_commit))
        self.assertEqual(outcome.code, 1)
        self.assertIn("main moved with code", outcome.lines[-1])

    def test_preflight_refusals(self):
        commit(self.wt, "bitacora/metodologia/DECISIONS.md", "D-900\n", "decision in the branch")
        outcome = self.run_it(Fake(self))
        self.assertEqual(outcome.code, 1)
        self.assertIn("changes the live bitácora", outcome.lines[-1])
        sh(self.wt, "reset", "-q", "--hard", self.tip)
        other = self.base / "wt-other"
        sh(self.live, "worktree", "add", "-q", "-b", "other", str(other), "main")
        commit(other, "skill/scripts/bt_y.py", "y = 1\n", "y")
        sh(self.live, "merge", "-q", "--ff-only", "other")
        outcome = self.run_it(Fake(self))
        self.assertIn("merge main into the branch", outcome.lines[-1])
        (self.wt / "skill" / "scripts" / "bt_x.py").write_text("dirty\n", encoding="utf-8")
        self.assertIn("uncommitted changes", self.run_it(Fake(self)).lines[-1])

    def test_which_units_restart_for_which_paths(self):
        self.assertEqual(integ.units_for(["skill/scripts/bt_durable/healing.py"]), [integ.ENGINE_UNIT, integ.WEB_UNIT])
        self.assertEqual(integ.units_for(["skill/scripts/bt_page_plans.py"]), [integ.ENGINE_UNIT, integ.WEB_UNIT])
        self.assertEqual(integ.units_for(["uv.lock"]), [integ.ENGINE_UNIT, integ.WEB_UNIT])
        self.assertEqual(integ.units_for(["skill/assets/plans.css"]), [integ.WEB_UNIT])
        self.assertEqual(integ.units_for(["skill/scripts/tests/test_x.py", "skill/references/modules.md",
                                          "skill/agents/solver.md"]), [])

    def test_a_docs_only_change_restarts_and_backs_up_nothing(self):
        sh(self.wt, "reset", "-q", "--hard", "main")
        commit(self.wt, "skill/references/modules.md", "# docs\n", "docs")
        fake = Fake(self)
        self.assertEqual(self.run_it(fake).code, 0)
        self.assertEqual([c[0] for c in fake.calls], ["regress", "push"])
        self.assertIn("backup: not needed", self.log.read_text())


class Regression(unittest.TestCase):
    def test_baseline_allowed_flake_rerun_and_real_failure(self):
        reruns = []
        result = bt_regress.judge(["test_a 0 3 venv", "test_known_red 1 2 python3", "test_platform 1 9 python3",
                                   "test_new 1 4 python3"], ALLOWED,
                                  rerun=lambda name: reruns.append(name) or name == "test_platform")
        self.assertEqual(reruns, ["test_new", "test_platform"])                     # the baseline is never rerun
        self.assertEqual((result.allowed, result.flaky, result.real),
                         (["test_known_red"], ["test_platform"], ["test_new"]))
        self.assertFalse(result.ok)
        self.assertIn("1 real failure(s): test_new", result.summary())


if __name__ == "__main__":
    unittest.main()
