from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from bt_cli_scheduler_monitor import main
from bt_scheduler_monitor_adapter import MonitorStore


class SchedulerMonitorCliTests(unittest.TestCase):
    def test_status_reads_fixture_store_without_mutating_it(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fixture.sqlite3"
            MonitorStore(path)
            before = path.read_bytes()
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                result = main(["status", "--store", str(path)])

            self.assertEqual(result, 0)
            self.assertEqual(json.loads(output.getvalue())["status"], "available")
            self.assertEqual(path.read_bytes(), before)

    def test_missing_fixture_store_is_an_error_and_is_not_created(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "missing.sqlite3"
            error = io.StringIO()

            with contextlib.redirect_stderr(error):
                result = main(["status", "--store", str(path)])

            self.assertEqual(result, 3)
            self.assertEqual(json.loads(error.getvalue())["code"], "M4_STORE_ERROR")
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
