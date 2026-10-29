"""The engine's INFO lines reach its journal (D-170): «healing: …» was invisible on 2026-10-29."""
import io
import logging
import unittest
from contextlib import redirect_stderr
from unittest import mock


class EngineLog(unittest.TestCase):
    def tearDown(self):
        log = logging.getLogger("bt_durable")
        log.handlers = [h for h in log.handlers if not getattr(h, "_bt_journal", False)]
        log.propagate = True
        log.setLevel(logging.NOTSET)

    def test_info_lines_of_the_engine_reach_stderr_once(self):
        from bt_durable import cli
        err = io.StringIO()
        with redirect_stderr(err), mock.patch("sys.stderr", err):
            cli.log_to_journal()
            cli.log_to_journal()
            logging.getLogger("bt_durable.service").info("healing: %s", "T93: retry_with_note")
        self.assertEqual(err.getvalue().count("healing: T93: retry_with_note"), 1)
        self.assertIn("(bt_durable.service)", err.getvalue())


if __name__ == "__main__":
    unittest.main()
