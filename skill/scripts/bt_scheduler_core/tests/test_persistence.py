"""Both repositories honour the same contract: atomic transactions, one authority, an auditable trail (SC-AC19)."""
from __future__ import annotations

import json
import sqlite3
import sys
import threading
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]

from support import Harness, indep, sqlite_path

import bt_scheduler_core as sc
from bt_scheduler_core.model import RunState
from bt_scheduler_core.states import TASK_TRANSITIONS, TaskState


class Contract:
    """Mixed into one TestCase per repository kind."""

    def make(self) -> sc.StateRepository:
        raise NotImplementedError

    def harness(self, tasks=None, **kw):
        return Harness(tasks or [indep("T1"), indep("T2", ["T1"])], repository=self.make(), **kw)

    def test_state_round_trips_exactly(self):
        h = self.harness()
        h.core.step()
        h.send("T1", "execution_finished")
        doc = h.core.read(lambda c: c.state.to_dict())
        self.assertEqual(RunState.from_dict(json.loads(json.dumps(doc))).to_dict(), doc)

    def test_schema_three_upgrades_in_memory_and_preserves_schema_five_facts(self):
        h = self.harness()
        document = h.core.read(lambda ctx: ctx.state.to_dict())
        document["schema"] = 3
        document.pop("subplan_versions")
        document.pop("compositions")
        upgraded = RunState.from_dict(document)
        self.assertEqual(upgraded.schema, 6)
        self.assertEqual((upgraded.subplan_versions, upgraded.compositions), ({}, {}))
        upgraded.subplan_versions["SP-1"] = {"plan_id": upgraded.plan_id, "revision": upgraded.revision,
                                               "version": 1, "commit": "a" * 40,
                                               "manifest_sha256": "b" * 64}
        upgraded.compositions["C1"] = {"plan_id": upgraded.plan_id, "revision": upgraded.revision,
                                         "state": "candidate", "members": {"SP-1": 1},
                                         "manifest_sha256": "c" * 64, "reason": ""}
        self.assertEqual(RunState.from_dict(upgraded.to_dict()).to_dict(), upgraded.to_dict())

    def test_an_exception_inside_a_transaction_changes_nothing(self):
        h = self.harness()
        h.core.step()
        before = (h.core.read(lambda c: c.state.to_dict()), len(h.core.audit_log()))

        def boom(ctx):
            ctx.state.paused = True
            ctx.state.tasks["T1"].state = "completed"
            ctx.audit("should_not_exist")
            raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            h.core.write(boom)
        self.assertEqual((h.core.read(lambda c: c.state.to_dict()), len(h.core.audit_log())), before)

    def test_state_and_audit_move_together(self):
        h = self.harness()
        h.core.step()
        state_seq = h.core.read(lambda c: c.state.counters["audit"])
        self.assertEqual(state_seq, h.core.audit_log()[-1].seq)

    def test_every_audit_entry_is_identifiable(self):                       # SC-AC19
        h = self.harness()
        h.core.step()
        h.send("T1", "execution_finished")
        h.core.step()
        h.verdict("T1")
        rows = h.core.audit_log()
        self.assertTrue(rows)
        for row in rows:
            self.assertEqual(row.plan_id, "REQ-T")
            self.assertTrue(row.kind and row.at > 0)
        for kind in ("reserved", "dispatch_intent", "dispatch_delivered", "task_transition", "attempt_transition"):
            self.assertIn(kind, {r.kind for r in rows})
        reserved = next(r for r in rows if r.kind == "reserved")
        self.assertEqual((reserved.task_id, reserved.attempt_id), ("T1", "att-0001"))

    def test_every_task_transition_in_the_audit_trail_is_legal_and_chained(self):
        h = self.harness([indep("T1"), indep("T2", ["T1"]), indep("T3")], parallel=2, max_attempts=2)
        h.core.step()
        h.send("T1", "execution_failed")
        h.core.step()
        h.core.step()
        h.finish_and_accept("T1")
        h.core.step()
        last: dict[str, str] = {}
        for row in h.core.audit_log():
            if row.kind != "task_transition":
                continue
            old, new = row.detail["from"], row.detail["to"]
            self.assertIn(TaskState(new), TASK_TRANSITIONS[TaskState(old)])
            self.assertEqual(last.get(row.task_id, "pending"), old, f"{row.task_id}: chain broken")
            last[row.task_id] = new
        self.assertEqual(last, {k: v for k, v in h.states().items() if k in last})

    def test_audit_since_pages_the_log(self):
        h = self.harness()
        h.core.step()
        rows = h.core.audit_log()
        self.assertEqual(h.core.audit_log(since=rows[2].seq), rows[3:])
        self.assertEqual(h.core.audit_log(since=rows[-1].seq), [])

    def test_empty_store_has_no_state(self):
        repo = self.make()
        with repo.transaction() as tx:
            self.assertIsNone(tx.state)
        self.assertEqual(repo.audit_log(), [])

    def test_threads_hammering_one_store_never_lose_or_duplicate_audit_rows(self):
        h = self.harness([indep(f"T{i}") for i in range(12)], parallel=12)
        errors = []

        def go(i):
            try:
                core = h.build()
                core.claim(sc.Assignment(f"T{i}", f"w{i}"))
                core.ingest(sc.Event(f"hb-{i}", "REQ-T", 1, f"T{i}", f"att-{i + 1:04d}", "x", "heartbeat"))
            except Exception as exc:  # noqa: BLE001 - collected and asserted empty below
                errors.append(repr(exc))

        threads = [threading.Thread(target=go, args=(i,)) for i in range(12)]
        [t.start() for t in threads]
        [t.join(60) for t in threads]
        self.assertEqual(errors, [])
        seqs = [e.seq for e in h.core.audit_log()]
        self.assertEqual(seqs, list(range(1, len(seqs) + 1)))
        self.assertEqual(h.core.read(lambda c: len(c.state.attempts)), 12)


class InMemory(Contract, unittest.TestCase):
    def make(self):
        return sc.InMemoryRepository()

    def test_a_failure_at_the_commit_point_loses_the_whole_transaction(self):
        h = self.harness()
        before = (h.core.read(lambda c: c.state.to_dict()), len(h.core.audit_log()))
        h.repo.before_commit = lambda: (_ for _ in ()).throw(RuntimeError("disk full"))
        with self.assertRaises(RuntimeError):
            h.core.step()
        h.repo.before_commit = None
        self.assertEqual((h.core.read(lambda c: c.state.to_dict()), len(h.core.audit_log())), before)


class Sqlite(Contract, unittest.TestCase):
    def setUp(self):
        self.tmp, self.path = sqlite_path()
        self.addCleanup(self.tmp.cleanup)

    def make(self):
        return sc.SqliteRepository(self.path)

    def test_the_database_is_in_wal_mode(self):
        self.make()
        conn = sqlite3.connect(self.path)
        try:
            self.assertEqual(conn.execute("PRAGMA journal_mode").fetchone()[0], "wal")
        finally:
            conn.close()

    def test_a_second_repository_object_sees_committed_state(self):
        h = self.harness()
        h.core.step()
        other = sc.SqliteRepository(self.path)
        with other.transaction() as tx:
            self.assertEqual(sorted(tx.state.attempts), ["att-0001"])

    def test_untouched_state_is_not_rewritten(self):
        h = self.harness()
        h.core.inspect()

        def version():
            conn = sqlite3.connect(self.path)
            try:
                return conn.execute("SELECT version FROM state").fetchone()[0]
            finally:
                conn.close()

        before = version()
        for _ in range(3):
            h.core.inspect()
        self.assertEqual(version(), before)

    def test_a_corrupted_document_is_reported_not_guessed(self):
        h = self.harness()
        conn = sqlite3.connect(self.path)
        conn.execute("UPDATE state SET doc = '{\"schema\": 99}'")
        conn.commit()
        conn.close()
        with self.assertRaises(sc.SchedulerError) as cm:
            h.core.snapshot()
        self.assertEqual(cm.exception.code, "STATE_UNREADABLE")
        conn = sqlite3.connect(self.path)
        conn.execute("UPDATE state SET doc = 'not json'")
        conn.commit()
        conn.close()
        with self.assertRaises(sc.SchedulerError) as cm:
            h.core.snapshot()
        self.assertEqual(cm.exception.code, "STATE_UNREADABLE")

    def test_a_crash_midway_through_a_transaction_leaves_the_file_consistent(self):
        h = self.harness()
        h.core.step()
        before = h.core.read(lambda c: c.state.to_dict())

        def die(ctx):
            ctx.state.tasks["T1"].state = "completed"
            raise sc.FakeExecutor.Crash()          # a BaseException: the process "dies" inside the transaction

        with self.assertRaises(sc.FakeExecutor.Crash):
            h.core.write(die)
        self.assertEqual(h.build().inspect().tasks["T1"]["state"], "active")
        self.assertEqual(h.core.read(lambda c: c.state.to_dict()), before)


if __name__ == "__main__":
    unittest.main()
