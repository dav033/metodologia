from __future__ import annotations

import sys
import json
import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]

from support import Harness, indep
import bt_scheduler_core as sc


def incident_event(h: Harness, *, event_id: str = "sha256:" + "a" * 64, attempt_id: str | None = None,
                   token: int | None = None, **payload_overrides):
    att = attempt_id or h.attempt("T1")
    payload = {"schema_version": "1.0.0", "incident_id": "sha256:" + "b" * 64, "run_id": "runtime-run-1",
               "task_id": "T1", "attempt_id": att, "execution_id": "exec-1", "detector_id": "missed_heartbeat",
               "type": "missed_heartbeat", "severity": "medium", "confidence": "high",
               "observed_at": "2026-10-15T16:00:00Z", "idempotency_key": event_id}
    payload.update(payload_overrides)
    return {"event_id": event_id, "plan_id": h.plan.plan_id, "revision": h.plan.revision, "task_id": "T1",
            "attempt_id": att, "source": "m4", "kind": "incident_observed", "token": token, "payload": payload,
            "contract_version": "1.2.0"}


class IncidentContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.h = Harness([indep("T1")], max_attempts=1)
        self.h.core.step()

    def test_incident_reference_audits_without_changing_task_attempt_or_lease(self):
        before = self.h.core.read(lambda ctx: (ctx.state.to_dict(), ctx.state.attempts[self.h.attempt("T1")].lease_expires_at))
        result = self.h.core.ingest(incident_event(self.h))
        after = self.h.core.read(lambda ctx: (ctx.state.to_dict(), ctx.state.attempts[self.h.attempt("T1")].lease_expires_at))
        self.assertEqual(result.status, "applied")
        self.assertEqual(after[0]["tasks"], before[0]["tasks"])
        self.assertEqual(after[0]["attempts"], before[0]["attempts"])
        self.assertEqual(after[1], before[1])
        audit = self.h.core.audit_log()[-1]
        self.assertEqual(audit.kind, "incident_observed")
        self.assertEqual(audit.detail["incident_id"], "sha256:" + "b" * 64)

    def test_incident_for_matching_terminal_attempt_is_audited(self):
        self.h.finish_and_accept("T1")
        before = self.h.core.read(lambda ctx: (ctx.state.to_dict(), ctx.state.attempts[self.h.attempt("T1")].lease_expires_at))
        self.assertEqual(self.h.core.ingest(incident_event(self.h)).status, "applied")
        after = self.h.core.read(lambda ctx: (ctx.state.to_dict(), ctx.state.attempts[self.h.attempt("T1")].lease_expires_at))
        self.assertEqual(after[0]["tasks"], before[0]["tasks"])
        self.assertEqual(after[0]["attempts"], before[0]["attempts"])
        self.assertEqual(after[1], before[1])

    def test_incident_for_known_superseded_attempt_is_audited_without_state_or_lease_changes(self):
        h = Harness([indep("T1")], max_attempts=3)
        h.core.step()
        first = h.attempt("T1")
        first_token = h.token(first)
        h.send("T1", "execution_failed")
        h.core.step()
        h.core.step()
        self.assertNotEqual(h.attempt("T1"), first)
        before = h.core.read(lambda ctx: (ctx.state.to_dict(),
                                          {key: value.lease_expires_at for key, value in ctx.state.attempts.items()}))
        result = h.core.ingest(incident_event(h, event_id="sha256:" + "c" * 64, attempt_id=first, token=first_token))
        after = h.core.read(lambda ctx: (ctx.state.to_dict(),
                                         {key: value.lease_expires_at for key, value in ctx.state.attempts.items()}))
        self.assertEqual(result.status, "applied")
        self.assertEqual(after[0]["tasks"], before[0]["tasks"])
        self.assertEqual(after[0]["attempts"], before[0]["attempts"])
        self.assertEqual(after[1], before[1])
        self.assertEqual(h.core.audit_log()[-1].kind, "incident_observed")

    def test_idempotency_is_durable_and_does_not_duplicate_audit(self):
        from bt_scheduler_core.sqlite_repository import SqliteRepository

        with tempfile.TemporaryDirectory() as temp:
            repo = SqliteRepository(Path(temp) / "scheduler.db")
            h = Harness([indep("T1")], repository=repo)
            h.core.step()
            event = incident_event(h)
            self.assertEqual(h.core.ingest(event).status, "applied")
            h.crash()
            first_count = len(h.core.audit_log())
            self.assertEqual(h.core.ingest(event).status, "duplicate")
            self.assertEqual(len(h.core.audit_log()), first_count)

    def test_incident_idempotency_survives_seen_event_eviction_and_restart(self):
        from bt_scheduler_core.model import SEEN_LIMIT
        from bt_scheduler_core.sqlite_repository import SqliteRepository

        with tempfile.TemporaryDirectory() as temp:
            repo = SqliteRepository(Path(temp) / "scheduler.db")
            h = Harness([indep("T1")], repository=repo)
            h.core.step()
            event = incident_event(h)
            self.assertEqual(h.core.ingest(event).status, "applied")
            h.core.write(lambda ctx: [ctx.state.remember(f"ordinary:{number}")
                                      for number in range(SEEN_LIMIT + 1)])
            self.assertNotIn(event["event_id"], h.core.read(lambda ctx: ctx.state.seen_events))
            h.crash()
            self.assertEqual(h.core.ingest(event).status, "duplicate")
            matching_rows = [entry for entry in h.core.audit_log() if entry.kind == "incident_observed" and
                             entry.detail["idempotency_key"] == event["event_id"]]
            self.assertEqual(len(matching_rows), 1)

    def test_existing_audit_schema_is_migrated_and_incident_keys_are_backfilled(self):
        from bt_scheduler_core.sqlite_repository import SqliteRepository

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "scheduler.db"
            connection = sqlite3.connect(path)
            connection.executescript("""
                CREATE TABLE state (id INTEGER PRIMARY KEY CHECK (id = 1), version INTEGER NOT NULL, doc TEXT NOT NULL);
                CREATE TABLE audit (seq INTEGER PRIMARY KEY, at REAL NOT NULL, kind TEXT NOT NULL, plan_id TEXT NOT NULL,
                                    task_id TEXT NOT NULL, attempt_id TEXT NOT NULL, detail TEXT NOT NULL);
            """)
            key = "sha256:" + "d" * 64
            connection.execute("INSERT INTO audit VALUES(1, 1, 'incident_observed', 'REQ-T', 'T1', 'attempt-1', ?)",
                               (json.dumps({"idempotency_key": key}),))
            connection.commit()
            connection.close()

            repo = SqliteRepository(path)
            with repo.transaction() as tx:
                self.assertTrue(tx.has_incident_event(key))

    def test_incident_key_backfill_resumes_when_the_column_already_exists(self):
        from bt_scheduler_core.sqlite_repository import SqliteRepository

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "scheduler.db"
            connection = sqlite3.connect(path)
            connection.executescript("""
                CREATE TABLE state (id INTEGER PRIMARY KEY CHECK (id = 1), version INTEGER NOT NULL, doc TEXT NOT NULL);
                CREATE TABLE audit (seq INTEGER PRIMARY KEY, at REAL NOT NULL, kind TEXT NOT NULL, plan_id TEXT NOT NULL,
                                    task_id TEXT NOT NULL, attempt_id TEXT NOT NULL, detail TEXT NOT NULL,
                                    incident_event_id TEXT);
            """)
            completed_key = "sha256:" + "e" * 64
            pending_key = "sha256:" + "f" * 64
            connection.executemany("INSERT INTO audit VALUES(?, 1, 'incident_observed', 'REQ-T', 'T1', 'attempt-1', ?, ?)",
                                   ((1, json.dumps({"idempotency_key": completed_key}), completed_key),
                                    (2, json.dumps({"idempotency_key": pending_key}), None)))
            connection.commit()
            connection.close()

            repo = SqliteRepository(path)
            with repo.transaction() as tx:
                self.assertTrue(tx.has_incident_event(completed_key))
                self.assertTrue(tx.has_incident_event(pending_key))

    def test_concurrent_initializers_serialize_legacy_audit_migration(self):
        from bt_scheduler_core.sqlite_repository import SqliteRepository

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "scheduler.db"
            connection = sqlite3.connect(path)
            connection.executescript("""
                CREATE TABLE state (id INTEGER PRIMARY KEY CHECK (id = 1), version INTEGER NOT NULL, doc TEXT NOT NULL);
                CREATE TABLE audit (seq INTEGER PRIMARY KEY, at REAL NOT NULL, kind TEXT NOT NULL, plan_id TEXT NOT NULL,
                                    task_id TEXT NOT NULL, attempt_id TEXT NOT NULL, detail TEXT NOT NULL);
            """)
            key = "sha256:" + "9" * 64
            connection.execute("INSERT INTO audit VALUES(1, 1, 'incident_observed', 'REQ-T', 'T1', 'attempt-1', ?)",
                               (json.dumps({"idempotency_key": key}),))
            connection.commit()
            connection.close()

            start_together = threading.Barrier(2)

            def initialize_and_check() -> bool:
                start_together.wait()
                repo = SqliteRepository(path)
                with repo.transaction() as tx:
                    return tx.has_incident_event(key)

            with ThreadPoolExecutor(max_workers=2) as executor:
                self.assertEqual(tuple(executor.map(lambda _index: initialize_and_check(), range(2))), (True, True))

    def test_incident_payload_rejects_wrong_source_key_fields_and_unlisted_fields(self):
        valid = incident_event(self.h)
        for change in (
            {"source": "monitor"},
            {"payload": {**valid["payload"], "idempotency_key": "other"}},
            {"payload": {**valid["payload"], "unexpected": "private"}},
            {"payload": {**valid["payload"], "observed_at": "tomorrow"}},
        ):
            bad = {**valid, **change}
            self.assertEqual(self.h.core.ingest(bad).status, "invalid")


if __name__ == "__main__":
    unittest.main()
