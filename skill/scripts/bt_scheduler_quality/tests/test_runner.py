from __future__ import annotations

import tempfile
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from bt_scheduler_quality.policy import CheckSpec, QualityPolicy
from bt_scheduler_quality.runner import SandboxRunner
from bt_scheduler_quality.sandbox_mounts import attempt_mounts


class SandboxRunnerTests(unittest.TestCase):
    def test_a_check_shares_the_host_network_when_the_policy_allows_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "probe.py").write_text(
                "import os, socket, sys\n"
                "names = {name for _, name in socket.if_nameindex()}\n"
                "sys.exit(0 if names - {'lo'} and os.path.exists('/etc/resolv.conf') else 6)\n",
                encoding="utf-8",
            )
            shared = SandboxRunner(QualityPolicy()).run(_check("probe.py"), root)
            offline = SandboxRunner(QualityPolicy(network=False)).run(_check("probe.py"), root)

        self.assertEqual((shared.status, shared.exit_code), ("pass", 0))
        self.assertNotIn("net", {name for name, _ in shared.namespace_ids})
        self.assertEqual((offline.status, offline.exit_code), ("fail", 6))        # only the loopback inside

    def test_runs_in_a_real_sandbox_without_host_home_or_network(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "probe.py").write_text(
                "import os, socket, sys\n"
                "private = ('.ssh', '.gnupg', '.config', '.claude', '.bashrc', 'dev')\n"
                "if any(os.path.exists('/home/david/' + name) for name in private): sys.exit(2)\n"
                "if 'M6_HOST_ONLY_PROBE' in os.environ: sys.exit(3)\n"
                "if os.environ.get('M6_APPROVED') != 'yes': sys.exit(4)\n"
                "sock = socket.socket(); sock.settimeout(0.2)\n"
                "if sock.connect_ex(('1.1.1.1', 443)) not in (101, 113): sys.exit(5)\n"
                "print('isolated')\n",
                encoding="utf-8",
            )
            check = _check("probe.py")
            policy = QualityPolicy(environment=(("M6_APPROVED", "yes"),), network=False)

            result = SandboxRunner(policy).run(check, root)

        self.assertEqual(result.status, "pass")
        self.assertEqual(result.exit_code, 0)
        self.assertIn(b"isolated", result.stdout)
        self.assertTrue(result.sandboxed)
        self.assertEqual(
            {name for name, _ in result.namespace_ids},
            {"mnt", "net", "pid", "ipc", "uts"},
        )

    def test_toolchain_mounts_are_read_only_and_leave_the_rest_of_home_hidden(self):
        from bt_scheduler_quality import sandbox_mounts

        with tempfile.TemporaryDirectory() as directory:
            tools = Path(directory) / "tools"
            (tools / "bin").mkdir(parents=True)
            (tools / "bin" / "marker").write_text("#!/bin/sh\n", encoding="utf-8")
            root = Path(directory) / "snap"
            root.mkdir()
            (root / "probe.py").write_text(
                "import os, sys\n"
                f"if not os.path.exists({str(tools / 'bin' / 'marker')!r}): sys.exit(2)\n"
                f"try:\n    open({str(tools / 'bin' / 'new')!r}, 'w')\n    sys.exit(3)\n"
                "except OSError:\n    pass\n"
                "if os.path.exists('/home/david/.ssh'): sys.exit(4)\n",
                encoding="utf-8",
            )
            fake = sandbox_mounts.Toolchain((sandbox_mounts.Mount(str(tools), str(tools)),))
            with patch.object(sandbox_mounts, "toolchain", return_value=fake), \
                    patch("bt_scheduler_quality.runner_sandbox_process.toolchain", return_value=fake):
                result = SandboxRunner(QualityPolicy()).run(_check("probe.py"), root)

        self.assertEqual((result.status, result.exit_code), ("pass", 0))

    def test_an_explicit_policy_variable_replaces_the_toolchain_default(self):
        """REQ-030: a NODE_OPTIONS set by the policy (the bounded heap repair) used to collide with the toolchain's own
        default and made the sandbox unavailable; the explicit value wins and the check sees only it."""
        from bt_scheduler_quality import sandbox_mounts

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "snap"
            root.mkdir()
            (root / "probe.py").write_text(
                "import os, sys\nsys.exit(0 if os.environ.get('NODE_OPTIONS') == '--max-old-space-size=12288' else 5)\n",
                encoding="utf-8")
            fake = sandbox_mounts.Toolchain((), (), (("NODE_OPTIONS", sandbox_mounts.NODE_OPTIONS),))
            policy = QualityPolicy(environment=(("NODE_OPTIONS", "--max-old-space-size=12288"),))
            with patch.object(sandbox_mounts, "toolchain", return_value=fake), \
                    patch("bt_scheduler_quality.runner_sandbox_process.toolchain", return_value=fake):
                result = SandboxRunner(policy).run(_check("probe.py"), root)

        self.assertEqual((result.status, result.exit_code), ("pass", 0))

    def test_attempt_dependencies_are_shown_inside_the_workspace_and_writes_stay_in_the_sandbox(self):
        with tempfile.TemporaryDirectory() as directory:
            worktree = Path(directory) / "worktree"
            (worktree / "node_modules" / "dep").mkdir(parents=True)
            (worktree / "node_modules" / "dep" / "index.js").write_text("x\n", encoding="utf-8")
            root = Path(directory) / "snap"
            root.mkdir()
            (root / "probe.py").write_text(
                "import os, sys\n"
                "if not os.path.exists('node_modules/dep/index.js'): sys.exit(2)\n"
                "open('node_modules/dep/new', 'w').write('x')\n",
                encoding="utf-8",
            )
            policy = QualityPolicy()
            mounts = attempt_mounts(policy, worktree)
            result = SandboxRunner(policy).run(_check("probe.py"), root, mounts=mounts)

            self.assertFalse((worktree / "node_modules" / "dep" / "new").exists())      # the host's dependencies are never written

        self.assertEqual(len(mounts), 1)
        self.assertEqual((result.status, result.exit_code), ("pass", 0))

    def test_linked_worktree_git_metadata_is_visible_read_only(self):
        import subprocess

        def git(*args, cwd):
            subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                           env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@x", "GIT_COMMITTER_NAME": "t",
                                "GIT_COMMITTER_EMAIL": "t@x", "PATH": "/usr/bin:/bin", "HOME": "/nonexistent"})

        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            repo.mkdir()
            git("init", "-q", "-b", "main", cwd=repo)
            (repo / "a.txt").write_text("a\n", encoding="utf-8")
            git("add", "a.txt", cwd=repo)
            git("commit", "-q", "-m", "one", cwd=repo)
            git("update-ref", "refs/remotes/origin/main", "HEAD", cwd=repo)
            worktree = Path(directory) / "worktree"
            git("worktree", "add", "-q", "-b", "feature", str(worktree), cwd=repo)
            snapshot = Path(directory) / "snap"
            snapshot.mkdir()
            (snapshot / "a.txt").write_text("a\n", encoding="utf-8")
            policy = QualityPolicy()
            mounts = attempt_mounts(policy, worktree, repo)
            ancestor = CheckSpec("C1", "command", "git merge-base --is-ancestor HEAD origin/main",
                                 ("git", "merge-base", "--is-ancestor", "HEAD", "origin/main"), ".", "p")
            write = _check("probe.py")
            (snapshot / "probe.py").write_text(
                "import subprocess, sys\n"
                "r = subprocess.run(['git', 'update-ref', 'refs/heads/x', 'HEAD'], capture_output=True)\n"
                "sys.exit(0 if r.returncode != 0 else 3)\n",
                encoding="utf-8",
            )
            visible = SandboxRunner(policy).run(ancestor, snapshot, mounts=mounts)
            read_only = SandboxRunner(policy).run(write, snapshot, mounts=mounts)
            hidden = SandboxRunner(policy).run(ancestor, snapshot)

        self.assertEqual(len(mounts), 2)
        self.assertEqual((visible.status, visible.exit_code), ("pass", 0))
        self.assertEqual((read_only.status, read_only.exit_code), ("pass", 0))
        self.assertEqual(hidden.status, "fail")

    def test_workspace_packages_are_built_inside_the_sandbox_before_the_check(self):
        import json

        from bt_scheduler_quality import sandbox_mounts, sandbox_prepare

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "package.json").write_text(json.dumps({"workspaces": ["packages/*"]}), encoding="utf-8")
            (root / "packages" / "lib").mkdir(parents=True)
            (root / "packages" / "lib" / "package.json").write_text(
                json.dumps({"name": "lib", "scripts": {"build": "x"}}), encoding="utf-8")
            (root / "probe.py").write_text(
                "import sys\nsys.exit(0 if open('packages/lib/dist/out.txt').read() == 'built' else 2)\n",
                encoding="utf-8",
            )
            build = ("python3", "-c", "import os; os.makedirs('packages/lib/dist'); "
                     "open('packages/lib/dist/out.txt', 'w').write('built')")
            with patch.object(sandbox_prepare, "BUILD_WORKSPACES", build):
                dep = (sandbox_mounts.Mount(str(root), "/workspace/node_modules"),)
                detected = sandbox_prepare.prepare_steps(QualityPolicy(), root, dep)
                built = SandboxRunner(QualityPolicy()).run(_check("probe.py"), root, mounts=dep)
            plain = SandboxRunner(QualityPolicy()).run(_check("probe.py"), root)
            self.assertEqual(detected, (build,))
            self.assertEqual((built.status, built.exit_code), ("pass", 0))
            self.assertEqual(plain.status, "fail")
            self.assertEqual(sandbox_prepare.prepare_steps(QualityPolicy(toolchain=False), root), ())

    def test_a_failing_prepare_step_is_reported_as_a_failed_check_with_its_output(self):
        import json

        from bt_scheduler_quality import sandbox_mounts, sandbox_prepare

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "package.json").write_text(json.dumps({"workspaces": ["packages/*"]}), encoding="utf-8")
            (root / "packages" / "lib").mkdir(parents=True)
            (root / "packages" / "lib" / "package.json").write_text(
                json.dumps({"scripts": {"build": "x"}}), encoding="utf-8")
            (root / "probe.py").write_text("print('never')\n", encoding="utf-8")
            broken = ("python3", "-c", "import sys; sys.stderr.write('tsc exploded\\n'); sys.exit(2)")
            dep = (sandbox_mounts.Mount(str(root), "/workspace/node_modules"),)
            with patch.object(sandbox_prepare, "BUILD_WORKSPACES", broken):
                result = SandboxRunner(QualityPolicy()).run(_check("probe.py"), root, mounts=dep)

        self.assertEqual((result.status, result.exit_code), ("fail", 1))
        self.assertIn(b"tsc exploded", result.stderr)
        self.assertNotIn(b"never", result.stdout)

    def test_repository_dependencies_stand_in_only_for_an_identical_lockfile(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            repo, worktree, snap = base / "repo", base / "worktree", base / "snap"
            for path in (repo / "node_modules" / "dep", worktree, snap):
                path.mkdir(parents=True)
            (repo / "package-lock.json").write_text('{"v":1}', encoding="utf-8")
            (snap / "package-lock.json").write_text('{"v":1}', encoding="utf-8")
            policy = QualityPolicy()
            shared = attempt_mounts(policy, worktree, repo, snap)
            (snap / "package-lock.json").write_text('{"v":2}', encoding="utf-8")
            changed = attempt_mounts(policy, worktree, repo, snap)
            (worktree / "node_modules").mkdir()
            (worktree / "node_modules" / ".package-lock.json").write_text("{}", encoding="utf-8")   # a finished install
            own = attempt_mounts(policy, worktree, repo, snap)

        self.assertEqual([m.source for m in shared], [str((repo / "node_modules").resolve())])
        self.assertEqual(changed, ())
        self.assertEqual([m.source for m in own], [str((worktree / "node_modules").resolve())])

    def test_workspace_packages_are_not_built_when_no_dependencies_are_mounted(self):
        import json

        from bt_scheduler_quality import sandbox_prepare
        from bt_scheduler_quality.sandbox_mounts import Mount

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "package.json").write_text(json.dumps({"workspaces": ["packages/*"]}), encoding="utf-8")
            (root / "packages" / "lib").mkdir(parents=True)
            (root / "packages" / "lib" / "package.json").write_text(
                json.dumps({"scripts": {"build": "x"}}), encoding="utf-8")
            policy = QualityPolicy()
            self.assertEqual(sandbox_prepare.prepare_steps(policy, root), ())
            with_deps = sandbox_prepare.prepare_steps(policy, root, (Mount("/a", "/workspace/node_modules"),))
        self.assertEqual(with_deps, (sandbox_prepare.BUILD_WORKSPACES,))

    def test_next_projects_generate_their_route_types_before_a_check(self):
        import json

        from bt_scheduler_quality import sandbox_prepare
        from bt_scheduler_quality.sandbox_mounts import Mount

        dep = (Mount("/a", "/workspace/node_modules"),)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "package.json").write_text(json.dumps({"dependencies": {"next": "^16"}}), encoding="utf-8")
            plain = Path(directory) / "plain"
            plain.mkdir()
            (plain / "package.json").write_text(json.dumps({"dependencies": {"react": "^19"}}), encoding="utf-8")
            policy = QualityPolicy()
            self.assertEqual(sandbox_prepare.prepare_steps(policy, root, dep), (sandbox_prepare.NEXT_TYPEGEN,))
            self.assertEqual(sandbox_prepare.prepare_steps(policy, plain, dep), ())
            self.assertEqual(sandbox_prepare.prepare_steps(policy, root), ())
        self.assertNotIn("network", " ".join(sandbox_prepare.NEXT_TYPEGEN))
        self.assertIn("--no-install", sandbox_prepare.NEXT_TYPEGEN)

    def test_times_out_and_kills_sandbox_children(self):
        marker = f"m6-child-{uuid.uuid4().hex}"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "parent.py").write_text(
                "import subprocess, sys, time\n"
                f"subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)', '{marker}'])\n"
                "time.sleep(30)\n",
                encoding="utf-8",
            )
            policy = QualityPolicy(
                max_command_seconds=1, max_total_seconds=1, max_cpu_seconds=2
            )

            result = SandboxRunner(policy).run(_check("parent.py"), root)
            time.sleep(0.1)

        self.assertEqual(result.issue_code, "CHECK_TIMEOUT")
        self.assertEqual(result.status, "unknown")
        self.assertFalse(_process_has_argument(marker))

    def test_a_silent_idle_command_is_a_hang_that_fails_the_code_not_the_infrastructure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "hang.py").write_text("import time\ntime.sleep(60)\n", encoding="utf-8")
            policy = QualityPolicy(max_idle_seconds=3)
            started = time.monotonic()

            result = SandboxRunner(policy).run(_check("hang.py"), root)

        self.assertLess(time.monotonic() - started, 30)
        self.assertEqual(result.status, "fail")
        self.assertIsNone(result.issue_code)
        self.assertIn(b"CHECK_HUNG", result.stderr)

    def test_a_silent_command_that_uses_cpu_is_never_mistaken_for_a_hang(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "busy.py").write_text(
                "import time\nend = time.time() + 7\nwhile time.time() < end:\n    pass\n", encoding="utf-8")
            policy = QualityPolicy(max_idle_seconds=3)

            result = SandboxRunner(policy).run(_check("busy.py"), root)

        self.assertEqual(result.status, "pass")
        self.assertNotIn(b"CHECK_HUNG", result.stderr)

    def test_the_idle_limit_can_be_switched_off(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "quiet.py").write_text("import time\ntime.sleep(5)\n", encoding="utf-8")

            result = SandboxRunner(QualityPolicy(max_idle_seconds=0)).run(_check("quiet.py"), root)

        self.assertEqual(result.status, "pass")

    def test_nonzero_exit_is_a_real_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "fail.py").write_text("raise SystemExit(17)\n", encoding="utf-8")

            result = SandboxRunner(QualityPolicy()).run(_check("fail.py"), root)

        self.assertEqual(result.status, "fail")
        self.assertEqual(result.exit_code, 17)
        self.assertEqual(result.issue_code, None)
        self.assertNotIn(b"M6_COMMAND_STARTED", result.stderr)

    def test_manual_check_is_left_for_an_operator(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            check = CheckSpec(
                "CHECK-001", "manual", "inspect output", (), ".", "visual review"
            )

            result = SandboxRunner(QualityPolicy()).run(check, root)

        self.assertEqual(result.status, "unknown")
        self.assertEqual(result.issue_code, "CHECK_MANUAL")
        self.assertFalse(result.sandboxed)

    def test_caps_and_redacts_untrusted_output(self):
        secret = "m6-dummy-secret-value"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "print_secret.py").write_text(
                "import os\nprint(os.environ['M6_TEST_SECRET'])\n", encoding="utf-8"
            )
            (root / "flood.py").write_text("print('x' * 20000)\n", encoding="utf-8")
            policy = QualityPolicy(
                max_output_bytes=1024,
                environment=(("M6_TEST_SECRET", secret),),
                secret_values=(secret,),
            )
            runner = SandboxRunner(policy)

            redacted = runner.run(_check("print_secret.py"), root)
            limited = runner.run(_check("flood.py"), root)

        self.assertNotIn(secret.encode(), redacted.stdout)
        self.assertIn(b"[REDACTED]", redacted.stdout)
        # a long output is CUT (head and tail kept, flagged), not a failure: the command's own exit code decides
        self.assertEqual((limited.status, limited.exit_code, limited.issue_code), ("pass", 0, None))
        self.assertTrue(limited.output_truncated)
        self.assertLessEqual(len(limited.stdout), 1024)
        self.assertIn(b"output cut", limited.stdout)

    def test_tmp_holds_a_scratch_install_not_only_a_few_megabytes(self):
        """david-ui REQ-001 T5: `registry-smoke.mjs` installs a Next app under /tmp; at 128 MiB npm died with ENOSPC (exit 228)."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "fill.py").write_text(
                "import os, tempfile\nd = tempfile.mkdtemp()\nwith open(os.path.join(d, 'big'), 'wb') as f:\n    f.write(b'0' * (300 * 1024 * 1024))\n",
                encoding="utf-8")
            result = SandboxRunner(QualityPolicy()).run(_check("fill.py"), root)
        self.assertEqual((result.status, result.exit_code), ("pass", 0))

    def test_a_runaway_output_is_killed_as_output_limit(self):
        import bt_scheduler_quality.runner_execution as execution

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "flood.py").write_text("import sys\nwhile True:\n    sys.stdout.write('x' * 65536)\n", encoding="utf-8")
            with patch.object(execution, "HARD_OUTPUT_BYTES", 2_000_000):
                limited = SandboxRunner(QualityPolicy(max_output_bytes=1024)).run(_check("flood.py"), root)
        self.assertEqual(limited.issue_code, "OUTPUT_LIMIT")

    def test_refuses_to_run_when_bubblewrap_is_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "probe.py").write_text("raise SystemExit(71)\n", encoding="utf-8")
            policy = QualityPolicy(bubblewrap_binary="/m6/no-such-bwrap")

            result = SandboxRunner(policy).run(_check("probe.py"), root)

        self.assertEqual(result.status, "unknown")
        self.assertEqual(result.issue_code, "SANDBOX_UNAVAILABLE")
        self.assertIsNone(result.exit_code)


def _check(script: str) -> CheckSpec:
    return CheckSpec(
        "CHECK-001",
        "command",
        f"python3 {script}",
        ("python3", script),
        ".",
        "test behavior",
    )


def _process_has_argument(value: str) -> bool:
    for entry in Path("/proc").iterdir():
        if not entry.name.isdecimal():
            continue
        try:
            command = (entry / "cmdline").read_bytes()
        except OSError:
            continue
        if value.encode() in command.split(b"\0"):
            return True
    return False


if __name__ == "__main__":
    unittest.main()
