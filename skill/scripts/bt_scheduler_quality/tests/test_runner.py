from __future__ import annotations

import tempfile
import time
import unittest
import uuid
from pathlib import Path

from bt_scheduler_quality.policy import CheckSpec, QualityPolicy
from bt_scheduler_quality.runner import SandboxRunner


class SandboxRunnerTests(unittest.TestCase):
    def test_runs_in_a_real_sandbox_without_host_home_or_network(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "probe.py").write_text(
                "import os, socket, sys\n"
                "if os.path.exists('/home/david'): sys.exit(2)\n"
                "if 'M6_HOST_ONLY_PROBE' in os.environ: sys.exit(3)\n"
                "if os.environ.get('M6_APPROVED') != 'yes': sys.exit(4)\n"
                "sock = socket.socket(); sock.settimeout(0.2)\n"
                "if sock.connect_ex(('1.1.1.1', 443)) not in (101, 113): sys.exit(5)\n"
                "print('isolated')\n",
                encoding="utf-8",
            )
            check = _check("probe.py")
            policy = QualityPolicy(environment=(("M6_APPROVED", "yes"),))

            result = SandboxRunner(policy).run(check, root)

        self.assertEqual(result.status, "pass")
        self.assertEqual(result.exit_code, 0)
        self.assertIn(b"isolated", result.stdout)
        self.assertTrue(result.sandboxed)
        self.assertEqual(
            {name for name, _ in result.namespace_ids},
            {"mnt", "net", "pid", "ipc", "uts"},
        )

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
        self.assertEqual(limited.issue_code, "OUTPUT_LIMIT")
        self.assertLessEqual(len(limited.stdout), 1024)

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
