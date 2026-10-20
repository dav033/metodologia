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


class RetryAcrossRevisions(unittest.TestCase):
    def _source(self, old_key, old_state="cancelled", revision=2, failure=""):
        old = SimpleNamespace(id="att-0001", key=old_key, state=old_state, token=1, failure=failure)
        current = SimpleNamespace(id="att-0002", key=f"REQ-1:r{revision}:T1:att-0002", state="reserved", token=1)
        state = SimpleNamespace(
            plan_id="REQ-1", revision=revision, plan_sha256="b" * 64, cancel_requested=False,
            tasks={"T1": SimpleNamespace(state="active", attempts=["att-0001", "att-0002"])},
            attempts={"att-0001": old, "att-0002": current})
        scheduler = SimpleNamespace(read=lambda fn: fn(SimpleNamespace(state=state)))
        return RetryContinuation(scheduler, None, lambda _repo: None, "HEAD")

    def test_an_attempt_of_an_earlier_revision_is_not_a_predecessor_after_a_rebase(self):
        source = self._source("REQ-1:r1:T1:att-0001")
        self.assertIsNone(source._previous("T1"))
        self.assertEqual(source.base_ref("T1"), "HEAD")
        self.assertEqual(source.notes(SimpleNamespace(task_id="T1", base_ref="HEAD")), "")

    def test_a_cancelled_attempt_of_the_same_revision_still_blocks_a_retry(self):
        from bt_scheduler_integrator import IntegrationError

        source = self._source("REQ-1:r2:T1:att-0001")
        with self.assertRaises(IntegrationError):
            source._previous("T1")

    def test_a_failed_attempt_of_the_same_revision_is_the_predecessor(self):
        source = self._source("REQ-1:r2:T1:att-0001", old_state="failed")
        self.assertEqual(source._previous("T1")["attempt_id"], "att-0001")

    def test_work_an_audit_sent_back_is_continued_not_refused(self):
        """After a rework the previous attempt was ACCEPTED (or superseded while verifying): the redo builds on it."""
        for state, failure in (("accepted", ""), ("cancelled", "superseded_by_rework: reworked by audit-gate")):
            with self.subTest(state=state):
                source = self._source("REQ-1:r2:T1:att-0001", old_state=state, failure=failure)
                self.assertEqual(source._previous("T1")["attempt_id"], "att-0001")
                self.assertTrue(source._reworked("T1"))

    def test_a_failed_attempt_is_not_a_rework_and_an_operator_cancel_still_blocks(self):
        from bt_scheduler_integrator import IntegrationError

        self.assertFalse(self._source("REQ-1:r2:T1:att-0001", old_state="failed")._reworked("T1"))
        with self.assertRaises(IntegrationError):
            self._source("REQ-1:r2:T1:att-0001", old_state="cancelled", failure="operator cancelled")._previous("T1")

    def test_a_start_the_executor_never_accepted_leaves_nothing_to_continue(self):
        source = self._source("REQ-1:r2:T1:att-0001", old_state="failed")
        source.executor = SimpleNamespace(ledger=SimpleNamespace(get=lambda _aid: None))
        self.assertIsNone(source._handoff("T1"))
        self.assertEqual(source.base_ref("T1"), "HEAD")


class SnapshotAcrossRevisions(unittest.TestCase):
    def _ledger(self, root, attempt_id, handoff):
        import json
        import sqlite3

        root.mkdir(parents=True)
        with sqlite3.connect(root / "ledger.db") as db:
            db.execute("CREATE TABLE attempts (attempt_id TEXT, handoff TEXT)")
            db.execute("INSERT INTO attempts VALUES (?, ?)", (attempt_id, json.dumps(handoff)))

    def test_a_kept_task_snapshot_is_found_in_the_root_of_an_earlier_revision(self):
        import tempfile
        from pathlib import Path

        from bt_scheduler_executor_adapter import _snapshot_sha

        sha = "a" * 40
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            self._ledger(base / "pictures-REQ-1-r2-aaaa1111-1792409909290", "att-0003",
                         {"status": "captured", "snapshot_sha": sha})
            self._ledger(base / "pictures-REQ-1-r1-bbbb2222-1792409909290", "att-0001",
                         {"status": "failed", "snapshot_sha": sha})
            self._ledger(base / "pictures-REQ-1-r2-cccc3333-1111111111111", "att-0003",
                         {"status": "captured", "snapshot_sha": "b" * 40})
            current = base / "pictures-REQ-1-r3-dddd4444-1792409909290"
            current.mkdir()
            executor = SimpleNamespace(root=current, describe=lambda _aid: None)
            self.assertEqual(_snapshot_sha(executor, "att-0003"), sha)          # same core run only
            self.assertIsNone(_snapshot_sha(executor, "att-0001"))              # not captured
            self.assertIsNone(_snapshot_sha(executor, "att-0099"))              # unknown anywhere
