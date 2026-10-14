"""Quota failures stay observable without escaping the background reader thread."""
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bt_relay


class RelayIntegrityTests(unittest.TestCase):
    def test_reader_failure_is_cached_without_unhandled_thread_exception(self):
        def fail():
            raise RuntimeError("private network detail")

        with tempfile.TemporaryDirectory() as scratch, patch.object(bt_relay, "STATE", Path(scratch)), \
                patch.object(threading, "excepthook") as unhandled:
            self.assertIsNone(bt_relay.quota_for("account", reader=fail))
            unhandled.assert_not_called()
            cache = json.loads((Path(scratch) / "relay" / "quota-cache.json").read_text())
            self.assertEqual(cache["account"]["error"], "READER_FAILED")
            self.assertNotIn("private network detail", json.dumps(cache))
