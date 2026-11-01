"""An integration packages every skill/scripts module and leaves the live venv able to import them (D-277).

2026-10-31: five modules were added without a line in `py-modules`; the live venv's editable install maps only listed
modules, so the engine and the CLI died on `No module named 'bt_stage_confirmations'`. `test_package_modules` would
have caught it, but the regression was off (D-261). Now `preflight` refuses the drift whatever the regression setting,
and a merge that changes pyproject.toml or uv.lock refreshes the live venv and checks its imports before restarting.
Real git repositories; the units, uv and the venv are fakes."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bt_integrate as integ
import bt_package_modules as pm
import test_integrate as base
from test_integrate import commit, sh


def pyproject(*modules: str) -> str:
    listed = ", ".join(f'"{m}"' for m in modules)
    return f'[project]\nname = "bitacora"\n\n[tool.setuptools]\npy-modules = [{listed}]\npackages = ["bt_pkg"]\n'


class Venv(base.Fake):
    """`venv_errors` / `venv_problems`: one answer per refresh, in order (then "" / [])."""
    def __init__(self, case, *, venv_errors=(), venv_problems=(), **extra):
        super().__init__(case, **extra)
        self.venv_errors, self.venv_answers = list(venv_errors), list(venv_problems)

    def refresh_venv(self, live):
        self.calls.append(("refresh_venv",))
        return self.venv_errors.pop(0) if self.venv_errors else ""

    def install_problems(self, live):
        self.calls.append(("install_problems",))
        return self.venv_answers.pop(0) if self.venv_answers else []


class Fixture(unittest.TestCase):
    setUp_base, request, run_it = base.Integrate.setUp, base.Integrate.request, base.Integrate.run_it

    def setUp(self):
        self.setUp_base()
        commit(self.live, "pyproject.toml", pyproject("bt_x"), "package bt_x")
        self.previous = sh(self.live, "rev-parse", "HEAD")
        sh(self.wt, "merge", "-q", "--no-edit", "main")

    def kinds(self, fake) -> list[str]:
        return [c[0] for c in fake.calls]


class PreflightRefusesUnlistedModules(Fixture):
    def test_a_branch_adding_an_unlisted_module_is_refused_before_any_change(self):
        commit(self.wt, "skill/scripts/bt_new.py", "y = 1\n", "add bt_new")
        for regression in ("none", "staged"):
            with self.subTest(regression=regression):
                fake = Venv(self)
                outcome = self.run_it(fake, regression=regression)
                self.assertEqual(outcome.code, 1, outcome.lines)
                self.assertIn("bt_new", outcome.lines[-1])
                self.assertIn("D-277", outcome.lines[-1])
                self.assertEqual(fake.calls, [])
                self.assertEqual(sh(self.live, "rev-parse", "main"), self.previous)

    def test_the_dry_run_refuses_it_too(self):
        commit(self.wt, "skill/scripts/bt_new.py", "y = 1\n", "add bt_new")
        self.assertEqual(self.run_it(Venv(self), dry_run=True, regression="none").code, 1)

    def test_listing_it_lets_the_branch_through(self):
        commit(self.wt, "skill/scripts/bt_new.py", "y = 1\n", "add bt_new")
        commit(self.wt, "pyproject.toml", pyproject("bt_x", "bt_new"), "package bt_new")
        outcome = self.run_it(Venv(self), regression="none")
        self.assertEqual(outcome.code, 0, outcome.lines)

    def test_an_unlisted_module_already_on_main_is_refused_in_any_branch(self):
        commit(self.live, "skill/scripts/bt_left.py", "z = 1\n", "left out")
        outcome = self.run_it(Venv(self), regression="none")                   # the branch changes only bt_x
        self.assertEqual(outcome.code, 1, outcome.lines)
        self.assertIn("bt_left", outcome.lines[-1])

    def test_a_listed_module_that_is_gone_is_refused(self):
        commit(self.wt, "pyproject.toml", pyproject("bt_x", "bt_gone"), "list a ghost")
        outcome = self.run_it(Venv(self), regression="none")
        self.assertEqual(outcome.code, 1, outcome.lines)
        self.assertIn("gone: bt_gone", outcome.lines[-1])

    def test_a_pyproject_that_does_not_parse_is_refused(self):
        commit(self.wt, "pyproject.toml", "[tool.setuptools\n", "break it")
        outcome = self.run_it(Venv(self), regression="none")
        self.assertEqual(outcome.code, 1, outcome.lines)
        self.assertIn("does not parse", outcome.lines[-1])


class Drift(unittest.TestCase):
    def test_scripts_tests_subfolders_and_the_named_scripts_are_not_modules(self):
        files = ["bt_a.py", "bt_b.py", "README.md", "tests", "bt_pkg", *[f"{name}.py" for name in pm.NOT_MODULES]]
        self.assertEqual(pm.drift(files, pyproject("bt_a")), (["bt_b"], []))
        self.assertEqual(pm.drift(["bt_a.py"], pyproject("bt_a", "bt_c")), ([], ["bt_c"]))
        self.assertEqual(pm.drift_message([], []), "")

    def test_the_distribution_names_are_the_modules_and_the_top_level_packages(self):
        text = pyproject("bt_a").replace('["bt_pkg"]', '["bt_pkg", "bt_pkg.sub"]')
        self.assertEqual(pm.distribution_names(text), ["bt_a", "bt_pkg"])


class LiveVenvRefresh(Fixture):
    def test_a_pyproject_change_refreshes_and_checks_the_venv_before_the_restart(self):
        for path, text in (("pyproject.toml", pyproject("bt_x") + "# touched\n"), ("uv.lock", "version = 1\n")):
            with self.subTest(path=path):
                self.setUp()
                commit(self.wt, path, text, f"change {path}")
                fake = Venv(self)
                outcome = self.run_it(fake, regression="none")
                self.assertEqual(outcome.code, 0, outcome.lines)
                self.assertEqual(self.kinds(fake), ["backup", "push", "refresh_venv", "install_problems", "drain",
                                                    "restart", "restart", "smoke"])
                self.assertIn("live venv refreshed", "\n".join(outcome.lines))

    def test_code_only_changes_leave_the_venv_alone(self):
        fake = Venv(self)
        self.assertEqual(self.run_it(fake, regression="none").code, 0)
        self.assertNotIn("refresh_venv", self.kinds(fake))

    def test_a_failed_refresh_is_a_failed_smoke_the_units_are_not_restarted_on_it_and_the_merge_is_reverted(self):
        commit(self.wt, "pyproject.toml", pyproject("bt_x") + "# touched\n", "touch")
        fake = Venv(self, venv_errors=["uv sync failed: no lock"])
        outcome = self.run_it(fake, regression="none", ledger=self.base / "ledger.md")
        self.assertEqual(outcome.code, 3, outcome.lines)
        self.assertEqual(self.kinds(fake), ["backup", "push", "refresh_venv", "push", "refresh_venv",
                                            "install_problems", "drain", "restart", "restart", "smoke"])
        self.assertEqual(sh(self.live, "show", "HEAD:pyproject.toml"), pyproject("bt_x").strip())   # reverted
        self.assertIn("not refreshed (uv sync failed: no lock)", "\n".join(outcome.lines))

    def test_a_module_the_venv_cannot_import_is_a_failed_smoke(self):
        commit(self.wt, "pyproject.toml", pyproject("bt_x") + "# touched\n", "touch")
        fake = Venv(self, venv_problems=[["not importable: bt_x"], []])
        outcome = self.run_it(fake, regression="none", ledger=self.base / "ledger.md")
        self.assertEqual(outcome.code, 3, outcome.lines)
        self.assertIn("SMOKE FAILED: the live venv: not importable: bt_x", "\n".join(outcome.lines))
        self.assertEqual(self.kinds(fake).count("restart"), 2)                    # only the revert's restart

    def test_when_the_previous_release_fails_the_venv_check_too_the_owner_must_look(self):
        commit(self.wt, "pyproject.toml", pyproject("bt_x") + "# touched\n", "touch")
        fake = Venv(self, venv_problems=[["not importable: bt_x"], ["not importable: bt_x"]])
        outcome = self.run_it(fake, regression="none", ledger=self.base / "ledger.md")
        self.assertEqual(outcome.code, 4, outcome.lines)
        self.assertNotIn("restart", self.kinds(fake))


class RealServices(unittest.TestCase):
    def test_refresh_venv_syncs_from_the_lock_without_removing_anything_and_reinstalls_the_project(self):
        live = Path(tempfile.mkdtemp(prefix="bt-venv-"))
        (live / "pyproject.toml").write_text(pyproject("bt_x"), encoding="utf-8")
        done = subprocess.CompletedProcess([], 0, "", "")
        with mock.patch.object(integ.subprocess, "run", return_value=done) as run, \
                mock.patch.dict(os.environ, {"VIRTUAL_ENV": "/elsewhere", "UV_PROJECT_ENVIRONMENT": "/x"}):
            self.assertEqual(integ.Services().refresh_venv(live), "")
        argv, kwargs = run.call_args.args[0], run.call_args.kwargs
        self.assertEqual(argv[1:], ["sync", "--frozen", "--inexact", "--quiet", "--reinstall-package", "bitacora"])
        self.assertEqual(kwargs["cwd"], str(live))
        self.assertNotIn("VIRTUAL_ENV", kwargs["env"])
        self.assertNotIn("UV_PROJECT_ENVIRONMENT", kwargs["env"])
        failed = subprocess.CompletedProcess([], 2, "", "error: the lockfile needs to be updated")
        with mock.patch.object(integ.subprocess, "run", return_value=failed):
            self.assertIn("lockfile needs to be updated", integ.Services().refresh_venv(live))

    def test_install_problems_names_what_is_missing_and_what_resolves_outside_the_checkout(self):
        root = Path(tempfile.mkdtemp(prefix="bt-dist-"))
        (root / "pyproject.toml").write_text(pyproject("json", "bt_zz_not_installed"), encoding="utf-8")
        problems = pm.install_problems(Path(sys.executable), root)              # a real interpreter, isolated mode
        self.assertEqual(len(problems), 2, problems)
        self.assertIn("not importable: bt_zz_not_installed, bt_pkg", problems[0])
        self.assertIn("imported from outside", problems[1])
        self.assertIn("json (", problems[1])

    def test_install_problems_is_empty_when_everything_resolves_under_the_checkout(self):
        root = Path(tempfile.mkdtemp(prefix="bt-dist-"))
        (root / "pyproject.toml").write_text(pyproject("bt_a"), encoding="utf-8")
        answer = json.dumps({"bt_a": f"{root}/skill/scripts/bt_a.py", "bt_pkg": f"{root}/skill/scripts/bt_pkg"})
        runner = mock.Mock(return_value=subprocess.CompletedProcess([], 0, answer + "\n", ""))
        self.assertEqual(pm.install_problems(Path("/venv/bin/python"), root, runner=runner), [])
        self.assertEqual(runner.call_args.args[0][:3], ["/venv/bin/python", "-I", "-B"])
        runner.return_value = subprocess.CompletedProcess([], 1, "", "Traceback: boom")
        self.assertIn("boom", pm.install_problems(Path("/venv/bin/python"), root, runner=runner)[0])


if __name__ == "__main__":
    unittest.main()
