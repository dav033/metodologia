"""A missing supervised task must never be reinterpreted as the final review."""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bt_runprompt


class MarathonContextIntegrityTests(unittest.TestCase):
    def test_unknown_task_does_not_grant_final_session_duties(self):
        for task in ("missing", "T1,missing"):
            with self.subTest(task=task), patch.dict(os.environ, {
                    "BITACORA_PROJECT": "alpha", "BITACORA_RUN": "REQ-001", "BITACORA_TASK": task}), \
                    patch.object(bt_runprompt, "find_req", return_value=Path("/tmp/requirement")), \
                    patch.object(bt_runprompt.rs, "load", return_value={"tasks": [{"id": "T1"}]}):
                context = bt_runprompt.marathon_block()
            self.assertIn("WARNING", context)
            self.assertNotIn("FINAL session:", context)
