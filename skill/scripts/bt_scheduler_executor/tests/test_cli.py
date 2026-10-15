"""The command line, end to end, in an isolated interpreter started from an unrelated directory."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]
import support  # noqa: F401

PARENT = str(Path(__file__).resolve().parents[2])
ENTRY = f"import sys; sys.path.insert(0, {PARENT!r}); from bt_scheduler_executor.cli import main; sys.exit(main(sys.argv[1:]))"


def cli(*args, cwd):
    return subprocess.run([sys.executable, "-I", "-c", ENTRY, *args], capture_output=True, text=True, cwd=cwd, timeout=120,
                          check=False)


class Cli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cwd = Path(self.tmp.name) / "unrelated"
        self.cwd.mkdir()

    def test_selftest_runs_two_attempts_end_to_end_with_no_provider(self):
        done = cli("selftest", "--json", "--keep", str(Path(self.tmp.name) / "work"), cwd=self.cwd)
        self.assertEqual(done.returncode, 0, done.stderr)
        data = json.loads(done.stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["attempts"]["att-1"], {"state": "finished", "cause": "clean", "handoff": "captured"})
        self.assertEqual(data["attempts"]["att-2"], {"state": "failed", "cause": "agent_error", "handoff": "captured"})
        self.assertEqual(sorted(data["events"]), ["att-1:finished", "att-1:started", "att-2:failed", "att-2:started"])
        self.root = data["root"]

    def test_status_show_and_events_read_what_the_selftest_left(self):
        work = str(Path(self.tmp.name) / "work")
        root = json.loads(cli("selftest", "--json", "--keep", work, cwd=self.cwd).stdout)["root"]
        status = cli("status", "--root", root, "--json", cwd=self.cwd)
        self.assertEqual(status.returncode, 0, status.stderr)
        data = json.loads(status.stdout)
        self.assertEqual((data["live"], data["terminal"], data["undelivered_events"]), (0, 2, 0))
        self.assertEqual([a["state"] for a in data["attempts"]], ["finished", "failed"])
        shown = json.loads(cli("show", "--root", root, "att-2", cwd=self.cwd).stdout)
        self.assertEqual(shown["outcome"]["cause"], "agent_error")
        self.assertEqual(shown["handoff"]["status"], "captured")
        events = cli("events", "--root", root, "--json", cwd=self.cwd)
        self.assertEqual(len(json.loads(events.stdout)), 4)
        self.assertEqual(json.loads(cli("events", "--root", root, "--undelivered", "--json", cwd=self.cwd).stdout), [])
        plain = cli("status", "--root", root, cwd=self.cwd)
        self.assertIn("att-1", plain.stdout)

    def test_unknown_attempt_or_root_is_exit_two(self):
        self.assertEqual(cli("status", "--root", str(Path(self.tmp.name) / "none"), cwd=self.cwd).returncode, 2)
        work = str(Path(self.tmp.name) / "work")
        root = json.loads(cli("selftest", "--json", "--keep", work, cwd=self.cwd).stdout)["root"]
        done = cli("show", "--root", root, "att-404", cwd=self.cwd)
        self.assertEqual(done.returncode, 2)
        self.assertIn("no such attempt", done.stderr)

    def test_read_commands_do_not_change_the_ledger(self):
        work = str(Path(self.tmp.name) / "work")
        root = Path(json.loads(cli("selftest", "--json", "--keep", work, cwd=self.cwd).stdout)["root"])
        before = {p.name: p.stat().st_mtime_ns for p in root.iterdir() if p.is_file() and p.suffix == ".db"}
        cli("status", "--root", str(root), cwd=self.cwd)
        cli("events", "--root", str(root), cwd=self.cwd)
        self.assertEqual({p.name: p.stat().st_mtime_ns for p in root.iterdir() if p.is_file() and p.suffix == ".db"}, before)


if __name__ == "__main__":
    unittest.main()
