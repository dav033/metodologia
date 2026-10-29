"""The verifier's sandbox runs a repository's Python checks (`uv run … pytest`), and a Codex attempt's cache reads count a
tenth of its token budget (pictures REQ-021 T6.3, 2026-10-29: «uv: command not found», exit 127, then the task's whole
budget «used» by 23.54 M cached input tokens)."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bt_scheduler_quality import sandbox_mounts
from bt_scheduler_quality.policy import CheckSpec, QualityPolicy
from bt_scheduler_quality.runner import SandboxRunner
from bt_scheduler_quality.runner_sandbox_process import _mount_arguments
from bt_scheduler_quality.sandbox_mounts import WORKSPACE, attempt_mounts


class PythonToolchain(unittest.TestCase):
    def test_uv_and_its_pythons_are_shown_with_a_throwaway_cache(self):
        with tempfile.TemporaryDirectory() as home:
            bin_dir = Path(home) / ".local" / "bin"
            bin_dir.mkdir(parents=True)
            uv = bin_dir / "uv"
            uv.write_text("#!/bin/sh\n")
            uv.chmod(0o755)
            pythons = Path(home) / ".local" / "share" / "uv" / "python"
            pythons.mkdir(parents=True)
            tools = sandbox_mounts._discover.__wrapped__(str(bin_dir), "", home)
        pairs = [(m.source, m.target) for m in tools.mounts]
        self.assertIn((str(uv.resolve()), str(uv.resolve())), pairs)
        self.assertIn((str(pythons.resolve()), str(pythons.resolve())), pairs)
        self.assertIn(str(bin_dir.resolve()), tools.path)
        env = dict(tools.environment)
        self.assertEqual(env["UV_CACHE_DIR"], sandbox_mounts.UV_CACHE)
        self.assertEqual(env["UV_PYTHON_INSTALL_DIR"], str(pythons.resolve()))
        self.assertEqual(env["UV_PYTHON_DOWNLOADS"], "never")

    def test_the_repository_venv_stands_in_only_with_the_same_lock_and_also_at_its_own_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot, worktree, repo = root / "snapshot", root / "worktree", root / "repo"
            worktree.mkdir()
            for base in (snapshot, repo):
                service = base / "services/ai-api"
                service.mkdir(parents=True)
                (service / "pyproject.toml").write_text("[project]\nname='x'\n")
                (service / "uv.lock").write_text("same")
            venv = repo / "services/ai-api/.venv"
            venv.mkdir()
            (venv / "pyvenv.cfg").write_text("home = /x\n")
            pairs = [(m.source, m.target) for m in attempt_mounts(QualityPolicy(), worktree, repo, snapshot)]
            self.assertIn((str(venv.resolve()), f"{WORKSPACE}/services/ai-api/.venv"), pairs)
            self.assertIn((str(venv.resolve()), str(venv.resolve())), pairs)
            (snapshot / "services/ai-api/uv.lock").write_text("changed")
            self.assertEqual(attempt_mounts(QualityPolicy(), worktree, repo, snapshot), ())

    def test_a_venv_without_its_marker_is_an_unfinished_install_and_is_not_shown(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot, worktree = root / "snapshot", root / "worktree"
            for base in (snapshot, worktree):
                (base / "svc").mkdir(parents=True)
                (base / "svc" / "pyproject.toml").write_text("")
                (base / "svc" / "uv.lock").write_text("lock")
            (worktree / "svc" / ".venv").mkdir()
            self.assertEqual(attempt_mounts(QualityPolicy(), worktree, snapshot_root=snapshot), ())
            (worktree / "svc" / ".venv" / "pyvenv.cfg").write_text("")
            self.assertEqual(len(attempt_mounts(QualityPolicy(), worktree, snapshot_root=snapshot)), 2)

    def test_the_workspace_venv_is_a_throwaway_overlay_and_its_own_path_read_only(self):
        mounts = (sandbox_mounts.Mount("/h/repo/svc/.venv", f"{WORKSPACE}/svc/.venv"),
                  sandbox_mounts.Mount("/h/repo/svc/.venv", "/h/repo/svc/.venv"))
        arguments = _mount_arguments(QualityPolicy(toolchain=False), mounts)
        self.assertEqual(arguments, ["--overlay-src", "/h/repo/svc/.venv", "--tmp-overlay", f"{WORKSPACE}/svc/.venv",
                                     "--ro-bind", "/h/repo/svc/.venv", "/h/repo/svc/.venv"])

    def test_a_venv_is_writable_inside_the_real_sandbox_and_untouched_on_the_host(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot, worktree = root / "snapshot", root / "worktree"
            for base in (snapshot, worktree):
                (base / "svc").mkdir(parents=True)
                (base / "svc" / "pyproject.toml").write_text("")
            venv = worktree / "svc" / ".venv"
            venv.mkdir()
            (venv / "pyvenv.cfg").write_text("installed")
            (snapshot / "svc" / "probe.py").write_text(
                "from pathlib import Path\n"
                "assert Path('.venv/pyvenv.cfg').read_text() == 'installed'\n"
                "Path('.venv/pyvenv.cfg').write_text('changed')\n")
            policy = QualityPolicy()
            mounts = attempt_mounts(policy, worktree, snapshot_root=snapshot)
            check = CheckSpec("C1", "command", "cd svc && python3 probe.py", ("python3", "probe.py"), "svc", "venv isolation")
            result = SandboxRunner(policy).run(check, snapshot, mounts=mounts)
            self.assertEqual((result.status, result.exit_code), ("pass", 0), result)
            self.assertEqual((venv / "pyvenv.cfg").read_text(), "installed")


@unittest.skipUnless(os.environ.get("BT_DURABLE_TESTS", "1") != "0", "durable package")
class BudgetTokens(unittest.TestCase):
    def setUp(self):
        try:
            from bt_durable.adapters.m3 import budget_tokens
        except ImportError as exc:            # the durable package needs the uv environment
            self.skipTest(str(exc))
        self.budget = budget_tokens

    def test_codex_input_includes_its_cache_reads_as_the_driver_reports_them(self):
        usage = {"input_tokens": 23_864_945, "output_tokens": 79_680, "cache_read_tokens": 23_541_120,
                 "total_tokens": 23_944_625}
        self.assertEqual(self.budget(usage, "codex"), 323_825 + 2_354_112 + 79_680)
        self.assertLess(self.budget(usage, "codex"), 8_000_000)

    def test_claude_reports_its_cache_reads_apart(self):
        usage = {"input_tokens": 1_000, "output_tokens": 200, "cache_read_tokens": 50_000, "total_tokens": 1_200}
        self.assertEqual(self.budget(usage, "claude"), 1_000 + 5_000 + 200)

    def test_only_a_total_or_nothing(self):
        self.assertEqual(self.budget({"total_tokens": 5_000}, "codex"), 5_000)
        self.assertIsNone(self.budget({}, "codex"))


if __name__ == "__main__":
    unittest.main()
