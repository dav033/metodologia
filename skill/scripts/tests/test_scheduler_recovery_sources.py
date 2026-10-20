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

    def test_a_cancelled_attempt_left_nothing_so_the_retry_starts_fresh_instead_of_being_refused(self):
        source = self._source("REQ-1:r2:T1:att-0001")
        self.assertIsNone(source._previous("T1"))
        self.assertEqual(source.base_ref("T1"), "HEAD")

    def _history(self, *old):
        """Attempts att-0001.. (oldest first) of one task in revision 2, then a reserved current one."""
        attempts = {f"att-{i:04d}": SimpleNamespace(id=f"att-{i:04d}", key=f"REQ-1:r2:T1:att-{i:04d}", state=state,
                                                    token=1, failure=failure)
                    for i, (state, failure) in enumerate(old, 1)}
        current = f"att-{len(old) + 1:04d}"
        attempts[current] = SimpleNamespace(id=current, key=f"REQ-1:r2:T1:{current}", state="reserved", token=1)
        state = SimpleNamespace(plan_id="REQ-1", revision=2, plan_sha256="b" * 64, cancel_requested=False,
                                tasks={"T1": SimpleNamespace(state="active", attempts=list(attempts))}, attempts=attempts)
        scheduler = SimpleNamespace(read=lambda fn: fn(SimpleNamespace(state=state)))
        return RetryContinuation(scheduler, None, lambda _repo: None, "HEAD")

    def test_a_retry_looks_past_cancellations_and_refused_starts_to_the_last_attempt_that_left_work(self):
        source = self._history(("accepted", ""), ("cancelled", "paused by the owner"),
                               ("failed", "start rejected: INTEGRATION_CONFLICT"))
        self.assertEqual(source._previous("T1")["attempt_id"], "att-0001")
        self.assertTrue(source._reworked("T1"))
        failed_first = self._history(("failed", "agent_error"), ("cancelled", "operator cancelled"))
        self.assertEqual(failed_first._previous("T1")["attempt_id"], "att-0001")
        self.assertFalse(failed_first._reworked("T1"))

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

    def test_sent_back_work_continues_only_on_an_unchanged_base(self):
        """A redone prerequisite changes the base: continuing from the old snapshot would conflict when combined."""
        source = self._source("REQ-1:r2:T1:att-0001", old_state="accepted")
        source._handoff = lambda _task: "oldsnap"
        source._previous_base = lambda _task: "basesha"
        source.fallback = lambda _task: "basesha"
        self.assertEqual(source.base_ref("T1"), "oldsnap")               # same base: build on the previous result
        source.fallback = lambda _task: "newbase"
        self.assertEqual(source.base_ref("T1"), "newbase")               # prerequisites changed: start on the new base
        note = source.notes(SimpleNamespace(task_id="T1", base_ref="newbase"))
        self.assertIn("oldsnap", note)
        self.assertIn("start from their new result", note)

    def test_sent_back_work_is_carried_onto_a_changed_base_when_it_can_be_and_only_referenced_when_it_cannot(self):
        source = self._source("REQ-1:r2:T1:att-0001", old_state="accepted")
        source._handoff = lambda _task: "oldsnap"
        source._previous_base = lambda _task: "basesha"
        source.fallback = lambda _task: "newbase"
        source.integrator = SimpleNamespace(rebase=lambda task, snap, base=None: "carriedcommit")
        self.assertEqual(source.base_ref("T1"), "carriedcommit")
        note = source.notes(SimpleNamespace(task_id="T1", base_ref="carriedcommit"))
        self.assertIn("oldsnap", note)
        self.assertIn("add only the changes the audit notes", note)
        source.integrator = SimpleNamespace(rebase=lambda task, snap, base=None: None)       # overlap: start on the new base
        self.assertEqual(source.base_ref("T1"), "newbase")
        self.assertIn("overlaps", source.notes(SimpleNamespace(task_id="T1", base_ref="newbase")))

    def test_a_failed_retry_continues_whatever_the_base(self):
        source = self._source("REQ-1:r2:T1:att-0001", old_state="failed")
        source._handoff = lambda _task: "oldsnap"
        source.fallback = lambda _task: "newbase"
        self.assertEqual(source.base_ref("T1"), "oldsnap")

    def test_a_failed_attempt_is_not_a_rework_and_an_operator_cancel_leaves_nothing_to_continue(self):
        from bt_scheduler_integrator import IntegrationError

        self.assertFalse(self._source("REQ-1:r2:T1:att-0001", old_state="failed")._reworked("T1"))
        self.assertIsNone(
            self._source("REQ-1:r2:T1:att-0001", old_state="cancelled", failure="operator cancelled")._previous("T1"))
        with self.assertRaises(IntegrationError):                       # a running predecessor is still not authorised
            self._source("REQ-1:r2:T1:att-0001", old_state="running")._previous("T1")

    def test_a_start_the_executor_never_accepted_leaves_nothing_to_continue(self):
        source = self._source("REQ-1:r2:T1:att-0001", old_state="failed")
        source.executor = SimpleNamespace(ledger=SimpleNamespace(get=lambda _aid: None))
        self.assertIsNone(source._handoff("T1"))
        self.assertEqual(source.base_ref("T1"), "HEAD")


class ContinuationBases(unittest.TestCase):
    """A task with no prerequisites starts from the repository head, which only moves forward."""

    def setUp(self):
        import json
        import subprocess
        import tempfile
        from pathlib import Path

        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()

        def git(*args):
            return subprocess.run(["git", "-c", "user.name=T", "-c", "user.email=t@t", *args], cwd=self.repo,
                                  capture_output=True, text=True, check=True).stdout.strip()
        self.git = git
        git("init", "-q")
        (self.repo / "a").write_text("1")
        git("add", "a")
        git("commit", "-q", "-m", "one")
        self.old = git("rev-parse", "HEAD")
        (self.repo / "a").write_text("2")
        git("commit", "-qam", "two")
        self.new = git("rev-parse", "HEAD")
        self.json, self.run_dir = json, Path(self.tmp.name)

    def source(self, fallback="HEAD", attempts=2, after=(), snapshots=None):
        attempts_state = {f"att-{i:04d}": SimpleNamespace(id=f"att-{i:04d}", key=f"REQ-1:r2:T1:att-{i:04d}",
                                                          state="accepted", token=1, failure="") for i in range(1, attempts)}
        attempts_state[f"att-{attempts:04d}"] = SimpleNamespace(id=f"att-{attempts:04d}", key="REQ-1:r2:T1:x",
                                                                state="reserved", token=1)
        state = SimpleNamespace(plan_id="REQ-1", revision=2, plan_sha256="b" * 64, cancel_requested=False,
                                tasks={"T1": SimpleNamespace(state="active", attempts=list(attempts_state))},
                                attempts=attempts_state)
        plan = SimpleNamespace(task=lambda _t: SimpleNamespace(repository="app", after=tuple(after)))
        scheduler = SimpleNamespace(read=lambda fn: fn(SimpleNamespace(state=state)), plan=plan)
        return RetryContinuation(scheduler, None, lambda role: self.repo, fallback, default_repository="app",
                                 snapshot_of=lambda attempt: (snapshots or {}).get(attempt), run_dir=self.run_dir)

    def test_a_root_task_continues_when_its_old_base_is_still_part_of_the_head(self):
        source = self.source()
        self.assertTrue(source._same_base("T1", self.old))             # head moved forward: the old base is an ancestor
        self.assertTrue(source._same_base("T1", self.new))
        self.assertFalse(source._same_base("T1", "0" * 40))
        self.assertFalse(source._same_base("T1", None))

    def test_an_integration_commit_or_pin_must_match_exactly(self):
        pinned = self.source(fallback=self.new)
        self.assertTrue(pinned._same_base("T1", self.new))
        self.assertFalse(pinned._same_base("T1", self.old))             # an ancestor is not enough for a merged base

    def test_the_owner_can_direct_the_next_start_only(self):
        source = self.source(attempts=3, snapshots={"att-0001": self.old})
        (self.run_dir / "RUN.continue.json").write_text(self.json.dumps({"T1": {"attempt": "att-0001", "attempts": 2}}))
        self.assertEqual(source._directed("T1"), self.old)
        self.assertEqual(source._continue_from("T1"), self.old)
        later = self.source(attempts=4, snapshots={"att-0001": self.old})   # one more attempt started since
        self.assertIsNone(later._directed("T1"))

    def test_a_result_of_an_earlier_revision_is_continued_for_a_root_task_but_not_for_one_with_prerequisites(self):
        attempts = {"att-0001": SimpleNamespace(id="att-0001", key="REQ-1:r1:T1:att-0001", state="accepted", token=1,
                                                failure=""),
                    "att-0002": SimpleNamespace(id="att-0002", key="REQ-1:r2:T1:att-0002", state="reserved", token=1)}
        state = SimpleNamespace(plan_id="REQ-1", revision=2, plan_sha256="b" * 64, cancel_requested=False,
                                tasks={"T1": SimpleNamespace(state="active", attempts=list(attempts))}, attempts=attempts)

        def make(after):
            plan = SimpleNamespace(task=lambda _t: SimpleNamespace(repository="app", after=after))
            scheduler = SimpleNamespace(read=lambda fn: fn(SimpleNamespace(state=state)), plan=plan)
            return RetryContinuation(scheduler, None, lambda role: self.repo, "HEAD", default_repository="app",
                                     snapshot_of=lambda attempt: self.old)
        self.assertEqual(make(())._earlier_revision_result("T1"), self.old)
        self.assertIsNone(make(("T0",))._earlier_revision_result("T1"))


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
