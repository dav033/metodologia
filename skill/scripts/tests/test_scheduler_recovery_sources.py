"""The recovery evidence boundary must treat missing process identity as uncertainty."""
from __future__ import annotations

import unittest
from types import SimpleNamespace

from bt_scheduler_retry import RetryContinuation


class RecoverySources(unittest.TestCase):
    def test_terminal_record_without_process_identity_is_not_exclusive_writer_evidence(self):
        for stream in ({}, {"process_identity": {"pid": None}}, {"process_identity": {"pid": 42}}):
            with self.subTest(stream=stream):
                row = {"state": "failed", "request": {}, "outcome": {}, "handoff": {}}
                executor = SimpleNamespace(ledger=SimpleNamespace(get=lambda _aid: row),
                                           describe=lambda _aid: {"stream": stream})
                source = RetryContinuation(None, executor, lambda _repo: None, "HEAD")
                facts = source.describe("attempt-1")
                self.assertEqual(facts["state"], "running")
                self.assertFalse(facts["snapshot_verified"])
