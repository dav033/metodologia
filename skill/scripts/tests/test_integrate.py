"""The repo-owned integration (REQ-031 T1): what operators did by hand on 2026-10-29, in order, under one lock, and never
anything but a fast-forward in the live checkout (a no-ff merge there once reset the staged live bitácora, D-160).

Real git repositories in a temporary directory; the regression, the backup, the push and the units are a recording fake."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_integrate as integ
import bt_integrate_post as post
import bt_regress
import bt_regress_select

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
    def __init__(self, case, *, red: bool = False, smoke=None, during_regression=None, selection=None,
                 stopped: str = ""):
        self.case, self.red, self.calls = case, red, []
        self.smokes = list(smoke or [])
        self.during_regression = during_regression
        self.selection = selection or bt_regress_select.Selection(changed=["skill/scripts/bt_x.py"], total=3,
                                                                   suites={"test_a": ["imports bt_x"]})
        self.stopped, self.modes, self.spawned, self.notes = stopped, [], [], []

    def regress(self, worktree, scratch, out, selection=None, mode="full"):
        self.calls.append(("regress", Path(worktree).name))
        self.modes.append((mode, selection))
        if self.during_regression:
            self.during_regression()
        lines = ["test_a 0 1 python3", "test_known_red 1 1 python3"] + (["test_b 1 1 python3"] if self.red else [])
        result = bt_regress.judge(lines, ALLOWED, rerun=lambda name: False)
        result.stopped = self.stopped
        return result

    def select(self, worktree):
        return self.selection

    def spawn(self, argv, name, log):
        self.spawned.append(argv)
        return f"unit {name}"

    def notify(self, title, message):
        self.notes.append((title, message))

    def backup(self):
        self.calls.append(("backup",))
        return "/backups/bt_durable-1.dump 10 abc"

    def push(self, live):
        self.calls.append(("push", sh(live, "rev-parse", "HEAD")))
        return ""

    def drain(self, timeout):
        self.calls.append(("drain",))
        return getattr(self, "drained", (0.0, []))

    def restart(self, unit):
        self.calls.append(("restart", unit))

    def smoke(self, units, since):
        self.calls.append(("smoke", tuple(units)))
        return self.smokes.pop(0) if self.smokes else []

    def refresh_venv(self, live):
        self.calls.append(("refresh_venv",))
        return getattr(self, "venv_error", "")

    def install_problems(self, live):
        self.calls.append(("install_problems",))
        problems = getattr(self, "venv_problems", [])
        return problems.pop(0) if problems and isinstance(problems[0], list) else problems


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
        self.assertEqual([c[0] for c in fake.calls], ["regress", "backup", "push", "drain", "restart", "restart", "smoke"])
        self.assertEqual(fake.calls[2], ("push", head))
        self.assertEqual([c[1] for c in fake.calls if c[0] == "restart"], [integ.ENGINE_UNIT, integ.WEB_UNIT])
        self.live_bitacora_intact()
        self.assertFalse(self.wt.exists())                                       # clean and merged: cleaned up
        self.assertEqual(sh(self.live, "branch", "--list", "fix"), "")
        self.assertEqual(sh(self.live, "branch", "--list", "deploy-fix"), "")                # D-220
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

    def other_on_main(self, path="skill/scripts/bt_y.py", text="y = 1\n", name="other"):
        other = self.base / f"wt-{name}"
        sh(self.live, "worktree", "add", "-q", "-b", name, str(other), "main")
        commit(other, path, text, name)
        sh(self.live, "merge", "-q", "--ff-only", name)

    def test_disjoint_code_landing_during_the_regression_is_merged_without_another_regression(self):
        """D-260: main's new code in other files is merged and integrated in the same turn; the full regression of the
        merge runs in the background after the smoke instead of a second one before it."""
        landed = []
        def code_commit():
            if not landed:
                landed.append(1)
                self.other_on_main()
        fake = Fake(self, during_regression=code_commit)
        outcome = self.run_it(fake)
        self.assertEqual(outcome.code, 0, outcome.lines)
        self.assertEqual([c for c in fake.calls if c[0] == "regress"], [("regress", "wt-fix")])
        self.assertTrue(any("full regression of the merge runs after the smoke" in line for line in outcome.lines))
        self.assertTrue(fake.spawned)                                         # the post-merge regression started
        self.assertEqual(sh(self.live, "show", "main:skill/scripts/bt_y.py"), "y = 1")

    def shared_file(self) -> list[str]:
        """bt_m.py on main and in the branch, which then changes its first line: main can change its last one cleanly."""
        lines = [f"m{i} = {i}" for i in range(10)]
        self.other_on_main(path="skill/scripts/bt_m.py", text="\n".join(lines) + "\n", name="base-m")
        sh(self.wt, "merge", "-q", "--no-edit", "main")
        commit(self.wt, "skill/scripts/bt_m.py", "\n".join(["m0 = 'branch'", *lines[1:]]) + "\n", "branch m0")
        return lines

    def main_changes_last_line(self, lines: list[str], value: str, name: str) -> None:
        current = sh(self.live, "show", "main:skill/scripts/bt_m.py").splitlines()
        self.other_on_main(path="skill/scripts/bt_m.py", text="\n".join([*current[:-1], f"m9 = {value!r}"]) + "\n",
                           name=name)

    def test_overlapping_code_landing_during_the_regression_is_merged_and_tested_again(self):
        """Main's new code in one of the branch's files (a clean merge): the merged tree is tested before it lands."""
        lines, landed = self.shared_file(), []
        def code_commit():
            if not landed:
                landed.append(1)
                self.main_changes_last_line(lines, "main", "other")
        fake = Fake(self, during_regression=code_commit)
        outcome = self.run_it(fake)
        self.assertEqual(outcome.code, 0, outcome.lines)
        self.assertEqual([c for c in fake.calls if c[0] == "regress"], [("regress", "wt-fix")] * 2)
        self.assertTrue(any("merging it and running again" in line for line in outcome.lines))
        self.assertFalse(fake.spawned)                                        # tested before, nothing after

    def test_main_that_keeps_moving_in_the_branchs_files_gives_the_turn_up(self):
        lines, count = self.shared_file(), []
        def code_commit():
            count.append(1)
            self.main_changes_last_line(lines, f"main {len(count)}", f"other{len(count)}")
        outcome = self.run_it(Fake(self, during_regression=code_commit))
        self.assertEqual(outcome.code, 1)
        self.assertIn("main moved with code", outcome.lines[-1])
        self.assertEqual(len(count), integ.CATCH_UP_RUNS + 1)

    def test_without_regression_it_integrates_on_the_smoke_and_lists_it_in_the_ledger(self):
        """D-261 (owner 2026-10-31): `none` runs no regression and writes the integration to the ledger."""
        ledger = self.base / "REGRESSION-OFF.md"
        fake = Fake(self)
        outcome = self.run_it(fake, regression="none", ledger=ledger)
        self.assertEqual(outcome.code, 0, outcome.lines)
        self.assertFalse([c for c in fake.calls if c[0] == "regress"])
        self.assertFalse(fake.spawned)                                        # no post-merge regression either
        text = ledger.read_text(encoding="utf-8")
        self.assertIn("## Integrated without regression\n", text)
        self.assertIn("x is two (D-900)", text.split("## Escaped defects")[0])
        self.assertIn("regression: skipped (D-261", self.log.read_text(encoding="utf-8"))
        integ.record_escape("T9 broke the panel; test_page_x would have failed", outcome.merge, ledger)
        escaped = ledger.read_text(encoding="utf-8").split("## Escaped defects")[1]
        self.assertIn(f"`{outcome.merge[:12]}` · T9 broke the panel", escaped)

    def test_without_regression_a_failed_smoke_is_an_escaped_defect(self):
        ledger = self.base / "REGRESSION-OFF.md"
        outcome = self.run_it(Fake(self, smoke=[["web answers 500"], []]), regression="none", ledger=ledger)
        self.assertEqual(outcome.code, 3, outcome.lines)
        self.assertIn("the smoke failed after an integration without regression",
                      ledger.read_text(encoding="utf-8").split("## Escaped defects")[1])

    def test_main_code_the_branch_lacks_is_merged_into_it_before_the_regression(self):
        """D-260: 13 of 33 integrations on 2026-10-31 went back to the end of the queue for this."""
        self.other_on_main()
        outcome = self.run_it(Fake(self))
        self.assertEqual(outcome.code, 0, outcome.lines)
        self.assertTrue(any("merged main into fix" in line for line in outcome.lines))
        self.assertEqual(sh(self.live, "show", "main:skill/scripts/bt_x.py"), "x = 2")

    def test_a_conflicting_main_is_aborted_in_the_worktree_and_refused_with_its_files(self):
        self.other_on_main(path="skill/scripts/bt_x.py", text="x = 3\n")
        outcome = self.run_it(Fake(self))
        self.assertEqual(outcome.code, 1)
        self.assertIn("merging it conflicts (skill/scripts/bt_x.py)", outcome.lines[-1])
        self.assertEqual(sh(self.wt, "status", "--porcelain", "--untracked-files=no"), "")    # the merge was aborted
        self.assertEqual(sh(self.wt, "rev-parse", "HEAD"), self.tip)

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
        sh(self.wt, "merge", "-q", "--no-edit", "main")                     # D-260 would merge it anyway
        (self.wt / "skill" / "scripts" / "bt_x.py").write_text("dirty\n", encoding="utf-8")
        self.assertIn("uncommitted changes", self.run_it(Fake(self)).lines[-1])

    def test_which_units_restart_for_which_paths(self):
        self.assertEqual(integ.units_for(["skill/scripts/bt_durable/healing.py"]), [integ.ENGINE_UNIT, integ.WEB_UNIT])
        self.assertEqual(integ.units_for(["skill/scripts/bt_page_plans.py"]), [integ.ENGINE_UNIT, integ.WEB_UNIT])
        self.assertEqual(integ.units_for(["uv.lock"]), [integ.ENGINE_UNIT, integ.WEB_UNIT])
        self.assertEqual(integ.units_for(["skill/assets/plans.css"]), [integ.WEB_UNIT])
        self.assertEqual(integ.units_for(["skill/scripts/tests/test_x.py", "skill/references/modules.md",
                                          "skill/agents/solver.md"]), [])

    def test_the_selected_suites_run_first_by_default_and_a_red_there_refuses_at_once(self):
        fake = Fake(self)
        self.assertEqual(self.run_it(fake).code, 0)
        self.assertEqual(fake.modes, [("staged", fake.selection)])
        self.assertEqual(fake.spawned, [])                                         # staged: nothing runs afterwards
        self.setUp()
        fake = Fake(self, red=True, stopped="selected")
        outcome = self.run_it(fake)
        self.assertEqual(outcome.code, 1)
        self.assertIn("the selected suites are red (test_b)", outcome.lines[-1])
        self.assertEqual(sh(self.live, "rev-parse", "HEAD"), self.previous)
        fake = Fake(self)
        self.assertEqual(self.run_it(fake, regression="full").code, 0)            # the branch stayed: it integrates
        self.assertEqual(fake.modes, [("full", None)])

    def test_selective_integrates_on_the_selection_and_starts_the_full_regression_after_the_smoke(self):
        fake = Fake(self)
        outcome = self.run_it(fake, regression="selective")
        self.assertEqual(outcome.code, 0, outcome.lines)
        self.assertEqual(fake.modes, [("selective", fake.selection)])
        [argv] = fake.spawned
        self.assertEqual(argv[argv.index("--post-merge") + 1], outcome.merge)
        self.assertEqual(argv[argv.index("--release-log") + 1], str(self.log))
        entry = self.log.read_text()
        self.assertIn("the full regression of the merge runs in the background", entry)
        self.assertIn(f"post-merge: full regression of {outcome.merge[:12]} started (unit bt-post-regress-fix-", entry)
        self.assertLess(entry.index("smoke ok"), entry.index("post-merge:"))

    def test_selective_with_an_untrusted_selection_runs_everything_and_nothing_after(self):
        untrusted = bt_regress_select.Selection(changed=["uv.lock"], total=3, full="uv.lock changed (dependencies)")
        fake = Fake(self, selection=untrusted)
        outcome = self.run_it(fake, regression="selective")
        self.assertEqual(outcome.code, 0, outcome.lines)
        self.assertEqual(fake.spawned, [])
        self.assertIn("not trusted: full regression first", "\n".join(outcome.lines))
        self.assertNotIn("background", self.log.read_text())

    def test_dry_run_prints_the_selection(self):
        fake = Fake(self)
        outcome = self.run_it(fake, dry_run=True)
        self.assertEqual(outcome.code, 0)
        self.assertIn("  test_a: imports bt_x", outcome.lines)
        self.assertEqual(fake.calls, [])

    def test_a_red_post_merge_regression_is_loud_and_reverts_nothing(self):
        merged = self.run_it(Fake(self), regression="selective", keep_worktree=True)
        fake = Fake(self, red=True)
        code = post.post_merge(self.request(), merged.merge, fake, say=lambda text: None)
        self.assertEqual(code, 1)
        self.assertEqual(sh(self.live, "rev-parse", "HEAD"), merged.merge)          # main keeps the merge
        text = self.log.read_text()
        self.assertIn(f"POST-MERGE FULL REGRESSION RED for {merged.merge[:12]} (fix)", text)
        self.assertIn(f"--revert {merged.merge} --branch fix", text)
        [(title, message)] = fake.notes
        self.assertIn("RED", title)
        self.assertIn("test_b", message)
        self.assertEqual(list((self.base / "post").iterdir()) if (self.base / "post").exists() else [], [])
        self.assertNotIn("post", sh(self.live, "worktree", "list"))
        green = post.post_merge(self.request(), merged.merge, Fake(self), say=lambda text: None)
        self.assertEqual(green, 0)
        self.assertIn(f"post-merge full regression of {merged.merge[:12]} (fix)", self.log.read_text())

    def test_the_proposed_revert_reverts_the_merge_through_the_deploy_worktree(self):
        merged = self.run_it(Fake(self), regression="selective", keep_worktree=True)
        fake = Fake(self)
        self.assertEqual(post.revert(self.request(), self.previous, fake, say=lambda text: None), 1)   # not a merge
        self.assertEqual(post.revert(self.request(), merged.merge, fake, say=lambda text: None), 0)
        self.assertEqual(sh(self.live, "show", "HEAD:skill/scripts/bt_x.py"), "x = 1")
        self.assertEqual(sh(self.live, "rev-parse", "HEAD^"), merged.merge)
        self.assertEqual([c[0] for c in fake.calls], ["push", "drain", "restart", "restart", "smoke"])
        self.assertIn("reverted by", self.log.read_text())
        self.live_bitacora_intact()

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


class Staged(unittest.TestCase):
    """bt_regress.staged over a fake suite runner: what runs, in which phase, and what the results file says."""

    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="bt-staged-"))
        tests = self.base / "skill" / "scripts" / "tests"
        tests.mkdir(parents=True)
        for name in ("test_a", "test_b", "test_c", "test_durable_d"):
            (tests / f"{name}.py").write_text("", encoding="utf-8")
        self.ran: list[str] = []

    def suite(self, red=(), flaky=()):
        def run(worktree, scratch, path, tag=""):
            self.ran.append(path.stem + tag)
            return f"{path.stem} {1 if path.stem in red or (path.stem in flaky and not tag) else 0} 2 python3"
        return run

    def staged(self, mode, selection, red=(), flaky=()):
        out = self.base / "results.txt"
        result = bt_regress.staged(self.base, self.base / "scratch", out, selection=selection, mode=mode, allowed=(),
                                   suite=self.suite(red, flaky))
        return result, out.read_text()

    def selection(self, **extra):
        return bt_regress_select.Selection(changed=["skill/scripts/bt_b.py"], total=4,
                                           suites={"test_b": ["imports bt_b"], "test_durable_d": ["always"]}, **extra)

    def test_staged_runs_the_selection_first_then_the_rest(self):
        result, text = self.staged("staged", self.selection())
        self.assertEqual(self.ran[:2], ["test_b", "test_durable_d"])
        self.assertEqual(sorted(self.ran[2:]), ["test_a", "test_c"])
        self.assertTrue(result.ok)
        self.assertEqual(len(result.lines), 4)
        self.assertIn("[staged: selected 2 in 0m00s, then the rest 2 in 0m00s]", result.summary())
        self.assertIn("#   test_b: imports bt_b", text)

    def test_a_red_selection_stops_at_its_first_failure(self):
        result, text = self.staged("staged", self.selection(), red=("test_b",))
        self.assertEqual(self.ran, ["test_b", "test_b.rerun"])                      # test_durable_d never started
        self.assertEqual((result.real, result.stopped), (["test_b"], "selected"))
        self.assertIn("stopped at the selected suites", text)

    def test_a_flake_that_stopped_the_selection_early_runs_what_was_left_with_the_rest(self):
        result, _ = self.staged("staged", self.selection(), flaky=("test_b",))
        self.assertTrue(result.ok)
        self.assertEqual(result.flaky, ["test_b"])
        self.assertEqual(sorted(line.split()[0] for line in result.lines),
                         ["test_a", "test_b", "test_c", "test_durable_d"])

    def test_selective_runs_the_selection_alone_and_an_untrusted_one_runs_everything(self):
        result, _ = self.staged("selective", self.selection())
        self.assertEqual(self.ran, ["test_b", "test_durable_d"])
        self.assertIn("[selective: selected 2 in", result.summary())
        self.ran.clear()
        result, text = self.staged("selective", self.selection(full="uv.lock changed (dependencies)"))
        self.assertEqual(self.ran[:2], ["test_b", "test_durable_d"])               # its first phase, then everything
        self.assertEqual(sorted(self.ran[2:]), ["test_a", "test_c"])
        self.assertEqual(result.mode, "staged")
        self.assertIn("[staged: first 2 in 0m00s, then the rest 2 in 0m00s]", result.summary())
        self.assertIn("NOT trusted, full regression: uv.lock changed", text)

    def test_the_estimate_follows_the_schedule(self):
        seconds = {"test_a": 10, "test_b": 10, "test_c": 30, "test_durable_d": 100}
        self.assertEqual(bt_regress.estimate(seconds, seconds, workers=2), 10 + 30 + 100)   # a, c | b
        self.assertEqual(bt_regress.estimate(seconds, ["test_a", "test_b"], workers=2), 10)



class Hygiene(unittest.TestCase):
    """D-220: merged deploy-* branches piled up, and full regressions ran three at a time."""

    def test_two_full_regressions_never_run_at_once(self):
        import threading
        with tempfile.TemporaryDirectory() as tmp:
            inside, overlap = [], []

            def staged(*args, **kwargs):
                inside.append(1)
                if len(inside) > 1:
                    overlap.append(1)
                time.sleep(0.2)
                inside.pop()
                return "ok"
            with mock.patch.object(integ, "lock_file", return_value=Path(tmp) / "integrate.lock"), \
                    mock.patch("bt_regress.staged", side_effect=staged):
                threads = [threading.Thread(target=integ.Services().regress, args=(Path(tmp), Path(tmp), Path(tmp) / "o"))
                           for _ in range(3)]
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join()
            self.assertEqual(overlap, [])


class Detached(unittest.TestCase):
    """D-225: an integration re-runs itself in its own unit; the caller follows its log and returns its exit code."""

    def run_detached(self, unit_states, write_rc=True):
        import io
        with tempfile.TemporaryDirectory() as tmp:
            deploy = Path(tmp) / "deploy"
            calls = []

            def fake_run(argv, **kwargs):
                calls.append(argv)
                if argv[0] == "systemd-run":
                    log = Path(next(a for a in argv if a.startswith("--property=StandardOutput=append:")).split(":", 1)[1])
                    rc = Path(next(a for a in argv if a.startswith("--setenv=BT_INTEGRATE_RC=")).split("=", 2)[2])
                    log.write_text("preflight ok\nmain is now abc\n")
                    if write_rc:
                        rc.write_text("0\n")
                    return subprocess.CompletedProcess(argv, 0, "", "")
                return subprocess.CompletedProcess(argv, 0, unit_states.pop(0) if unit_states else "inactive", "")
            out = io.StringIO()
            with mock.patch.object(integ, "DEPLOY", deploy), mock.patch.object(integ.subprocess, "run", side_effect=fake_run):
                code = integ.detached(["--branch", "x", "--title", "t"], "x", poll=0.0, out=out)
            return code, out.getvalue(), calls

    def test_the_caller_prints_the_units_log_and_returns_its_code(self):
        code, shown, calls = self.run_detached([])
        self.assertEqual(code, 0)
        self.assertIn("main is now abc", shown)
        start = calls[0]
        self.assertEqual(start[:2], ["systemd-run", "--user"])
        self.assertIn("--setenv=BT_INTEGRATE_DETACHED=1", start)
        self.assertEqual(start[-4:], ["--branch", "x", "--title", "t"])

    def test_a_unit_that_ends_without_an_exit_code_is_reported(self):
        code, shown, _ = self.run_detached(["inactive", "inactive"], write_rc=False)
        self.assertEqual(code, 4)
        self.assertIn("without an exit code", shown)


class Cli(unittest.TestCase):
    """D-264: `--escaped TEXT --merge SHA` (the D-261 command) needs no --branch/--title; every other path still does."""

    def main(self, argv):
        import contextlib
        import io
        err = io.StringIO()
        with mock.patch.object(integ, "detached", return_value=0) as detached, \
                mock.patch.object(integ, "integrate") as integrate, \
                mock.patch.object(integ, "_which", return_value="/usr/bin/systemd-run"), \
                mock.patch.dict(integ.os.environ, {}, clear=False), contextlib.redirect_stderr(err), \
                contextlib.redirect_stdout(io.StringIO()):
            integ.os.environ.pop(integ.DETACHED, None)
            try:
                code = integ.main(argv)
            except SystemExit as exit_:
                code = exit_.code
        return code, err.getvalue(), detached, integrate

    def test_escaped_without_branch_or_title_records_in_the_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "REGRESSION-OFF.md"
            with mock.patch.object(integ, "ledger", return_value=ledger):
                code, err, detached, integrate = self.main(
                    ["--escaped", "T9 broke the panel; test_page_x would have failed", "--merge", "abcdef1234567890"])
            self.assertEqual(code, 0, err)
            escaped = ledger.read_text(encoding="utf-8").split("## Escaped defects")[1]
            self.assertIn("merge `abcdef123456` · T9 broke the panel", escaped)
            detached.assert_not_called()
            integrate.assert_not_called()

    def test_an_integration_without_branch_or_title_is_refused_before_anything_runs(self):
        for argv, flag in ((["--title", "t", "--worktree", "."], "--branch"),
                           (["--branch", "x", "--worktree", "."], "--title"),
                           (["--post-merge", "abc", "--branch", "x"], "--title"),
                           (["--revert", "abc", "--title", "t"], "--branch")):
            code, err, detached, integrate = self.main(argv)
            self.assertEqual(code, 2, argv)
            self.assertIn(f"required: {flag}", err)
            detached.assert_not_called()
            integrate.assert_not_called()

    def test_an_integration_with_branch_and_title_still_detaches_with_its_argv(self):
        argv = ["--branch", "x", "--title", "t", "--worktree", "."]
        code, err, detached, _ = self.main(argv)
        self.assertEqual(code, 0, err)
        detached.assert_called_once_with(argv, "x")


class FairLock(unittest.TestCase):
    """D-230: waiters get the machine lock in arrival order; a dead waiter's ticket never blocks the queue."""

    def test_waiters_are_served_in_arrival_order(self):
        import threading
        with tempfile.TemporaryDirectory() as tmp:
            lock, order = Path(tmp) / "integrate.lock", []
            holding = threading.Event()

            def holder():
                with integ.machine_lock(lock, 5, poll=0.01):
                    holding.set()
                    time.sleep(0.3)

            def waiter(name):
                with integ.machine_lock(lock, 10, poll=0.01):
                    order.append(name)
                    time.sleep(0.05)
            first = threading.Thread(target=holder)
            first.start()
            holding.wait()
            threads = []
            for name in ("a", "b", "c"):
                threads.append(threading.Thread(target=waiter, args=(name,)))
                threads[-1].start()
                time.sleep(0.05)                          # arrival order a, b, c
            for thread in [first, *threads]:
                thread.join()
            self.assertEqual(order, ["a", "b", "c"])

    def test_a_dead_waiters_ticket_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / "integrate.lock"
            queue = lock.with_name("integrate.lock.queue")
            queue.mkdir()
            (queue / f"{0:020d}-999999999").touch()       # a waiter that died long ago
            with integ.machine_lock(lock, 2, poll=0.01):
                pass
            self.assertEqual(list(queue.iterdir()), [])


class Drain(unittest.TestCase):
    """D-204: the 09:31 and 10:06 deploys of 2026-10-30 cut pictures REQ-021 T10.45's verification twice; the second
    cut left it for the owner as BLOCKED_ENV. An engine restart now waits for running verifications first."""

    def test_the_engine_restart_waits_for_running_verifications(self):
        notes = []
        fake = integ.Services()
        seen = [["v1", "v2"], ["v2"], []]
        fake.verifying = lambda: seen.pop(0) if seen else []
        fake.restart = lambda unit: notes.append(("restart", unit, len(seen)))
        fake.smoke = lambda units, since: []
        with mock.patch.object(integ, "DRAIN_POLL", 0.0):
            integ._restart(fake, [integ.ENGINE_UNIT], notes.append)
        self.assertEqual([n for n in notes if isinstance(n, tuple)], [("restart", integ.ENGINE_UNIT, 0)])

    def test_a_web_only_restart_does_not_wait_and_a_timeout_restarts_anyway(self):
        fake = integ.Services()
        fake.verifying = lambda: ["stuck"]
        calls = []
        fake.restart = lambda unit: calls.append(unit)
        fake.smoke = lambda units, since: []
        integ._restart(fake, [integ.WEB_UNIT], calls.append)
        self.assertEqual(calls[0], integ.WEB_UNIT)
        with mock.patch.object(integ, "DRAIN_POLL", 0.0), mock.patch("bt_config.get", return_value=0):
            notes = []
            integ._restart(fake, [integ.ENGINE_UNIT], notes.append)
        self.assertTrue(any("1 still running" in n for n in notes if isinstance(n, str)))

if __name__ == "__main__":
    unittest.main()
