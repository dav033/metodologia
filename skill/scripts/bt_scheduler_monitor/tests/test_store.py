from __future__ import annotations

import sqlite3
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from bt_scheduler_monitor.contracts import Incident, NormalizedEvent, ProcessIdentity
from bt_scheduler_monitor.store import (MAX_OUTBOX_CLAIM_BATCH, MAX_OUTBOX_CLAIM_TOKEN_BYTES,
                                       MAX_OUTBOX_ITEMS, MAX_OUTBOX_KEY_BYTES, MonitorStore, SourceCursor,
                                       StoreError)
from bt_scheduler_monitor.storage_limits import measured_store_bytes
from bt_scheduler_monitor.store_migrations import ensure_duplicate_table_headroom

NOW = "2026-10-15T16:00:00Z"
IDENTITY = ProcessIdentity("linux", "boot-a", 23, 100)


def event(sequence: int, *, event_id: str | None = None, offset: int | None = None) -> NormalizedEvent:
    return NormalizedEvent("1.0.0", event_id or f"sha256:{sequence:064x}", "fixture/1", "1.0.0", "run-1", 1,
                           "task-1", "attempt-1", "exec-1", IDENTITY, "codex", "profile-1", "model-1",
                           "heartbeat", "heartbeat", NOW, "stdout", sequence,
                           sequence * 8 if offset is None else offset, (("status", "started"),), "reported",
                           host_boot_id="boot-a")


def incident(*, state: str = "open") -> Incident:
    return Incident("1.0.0", "incident-1", "run-1", "task-1", "attempt-1", "exec-1", "missed_heartbeat",
                    "missed_heartbeat", "medium", "low", NOW, NOW, 1, (), ("sha256:" + "a" * 64,), state,
                    resolved_at=NOW if state == "resolved" else None)


class MonitorStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "monitor.sqlite3"
        self.store = MonitorStore(self.path)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _add_database_padding(self, size: int) -> None:
        connection = sqlite3.connect(self.path)
        try:
            connection.execute("CREATE TABLE IF NOT EXISTS capacity_padding(payload BLOB NOT NULL)")
            connection.execute("INSERT INTO capacity_padding(payload) VALUES(zeroblob(?))", (size,))
            connection.commit()
        finally:
            connection.close()

    def test_event_and_cursor_commit_atomically_and_invalid_advance_rolls_back(self) -> None:
        first = event(1)
        cursor = SourceCursor("exec-1", "stdout", "boot-a", 1, 8)
        self.assertTrue(self.store.append_event(first, cursor))
        connection = sqlite3.connect(self.path)
        try:
            connection.execute("""CREATE TRIGGER reject_cursor BEFORE UPDATE ON source_cursors
                BEGIN SELECT RAISE(ABORT, 'cursor write fault'); END""")
        finally:
            connection.close()
        with self.assertRaises(StoreError):
            # The injected cursor write failure follows the event insert in the transaction.
            self.store.append_event(event(2), SourceCursor("exec-1", "stdout", "boot-a", 2, 16))
        self.assertEqual(self.store.get_cursor("exec-1", "stdout"), cursor)
        self.assertIsNone(self.store.get_event(event(2).event_id))

    def test_replay_is_durable_after_close_and_reopen(self) -> None:
        first = event(1)
        cursor = SourceCursor("exec-1", "stdout", "boot-a", 1, 8)
        self.assertTrue(self.store.append_event(first, cursor))
        self.store = MonitorStore(self.path)
        self.assertFalse(self.store.append_event(first, cursor))
        self.assertEqual(self.store.get_event(first.event_id), first)
        self.assertEqual(self.store.get_cursor("exec-1", "stdout"), cursor)

    def test_stream_gap_is_durable_idempotent_and_does_not_ack_cursor(self) -> None:
        values = dict(gap_id="gap-1", execution_id="exec-1", stream="stdout", first_sequence=4,
                      last_sequence=6, first_offset=32, last_offset=56, dropped_bytes=24,
                      dropped_frames=3, reason="queue_overflow", recorded_at=NOW)
        self.assertTrue(self.store.record_stream_gap(**values))
        self.assertFalse(self.store.record_stream_gap(**values))
        self.assertFalse(self.store.record_stream_gap(**{**values, "recorded_at": "2026-10-15T16:05:00Z"}))
        self.assertIsNone(self.store.get_cursor("exec-1", "stdout"))
        self.store = MonitorStore(self.path)
        self.assertEqual(self.store.list_stream_gaps(execution_id="exec-1"),
                         ({"gap_id": "gap-1", **values},))
        self.assertFalse(self.store.record_stream_gap(**{**values, "dropped_bytes": 25}))
        self.assertEqual(self.store.list_stream_gaps()[0]["dropped_bytes"], 25)
        self.assertEqual(self.store.list_stream_gaps()[0]["recorded_at"], NOW)
        with self.assertRaisesRegex(ValueError, "regressing content"):
            self.store.record_stream_gap(**{**values, "dropped_bytes": 24})

    def test_stream_gap_store_failure_is_visible_and_not_acknowledged(self) -> None:
        connection = sqlite3.connect(self.path)
        try:
            connection.execute("CREATE TRIGGER reject_gap BEFORE INSERT ON stream_gaps "
                               "BEGIN SELECT RAISE(ABORT, 'gap write fault'); END")
        finally:
            connection.close()
        with self.assertRaises(StoreError):
            self.store.record_stream_gap(gap_id="gap-fail", execution_id="exec-1", stream="stdout",
                                         first_sequence=1, last_sequence=1, first_offset=8, last_offset=8,
                                         dropped_bytes=0, dropped_frames=1, reason="decoder_error", recorded_at=NOW)
        self.assertEqual(self.store.list_stream_gaps(), ())

    def test_storage_cap_rejects_new_event_without_cursor_advance_and_reopens_after_capacity_recovers(self) -> None:
        limited = MonitorStore(self.path, max_store_bytes=400_000)
        self._add_database_padding(200_000)
        with self.assertRaisesRegex(StoreError, "storage_pressure: measured_bytes="):
            limited.append_event(event(1), SourceCursor("exec-1", "stdout", "boot-a", 1, 8))
        self.assertIsNone(limited.get_cursor("exec-1", "stdout"))
        larger = MonitorStore(self.path, max_store_bytes=2_000_000)
        self.assertTrue(larger.append_event(event(1), SourceCursor("exec-1", "stdout", "boot-a", 1, 8)))
        self.assertEqual(larger.get_cursor("exec-1", "stdout"), SourceCursor("exec-1", "stdout", "boot-a", 1, 8))

    def test_storage_cap_preserves_open_incident_and_pending_outbox(self) -> None:
        initial = MonitorStore(self.path, max_store_bytes=2_000_000)
        current = incident()
        initial.enqueue_incident(current, "pending-incident")
        limited = MonitorStore(self.path, max_store_bytes=400_000)
        self._add_database_padding(200_000)
        with self.assertRaises(StoreError):
            limited.append_event(event(1), SourceCursor("exec-1", "stdout", "boot-a", 1, 8))
        self.assertEqual(limited.get_incident(current.incident_id), current)
        connection = sqlite3.connect(self.path)
        try:
            self.assertEqual(connection.execute("SELECT state FROM m1_outbox").fetchone()[0], "pending")
        finally:
            connection.close()

    def test_storage_cap_refuses_existing_store_initialization_before_mutation(self) -> None:
        MonitorStore(self.path, max_store_bytes=2_000_000)
        self._add_database_padding(400_000)
        measured_before = measured_store_bytes(self.path)

        with self.assertRaisesRegex(StoreError, "storage_pressure: measured_bytes="):
            MonitorStore(self.path, max_store_bytes=600_000)

        measured_after = measured_store_bytes(self.path)
        self.assertEqual(measured_after, measured_before)
        connection = sqlite3.connect(self.path)
        try:
            self.assertEqual(connection.execute(
                "SELECT max_store_bytes FROM store_limits WHERE singleton=1").fetchone(), (2_000_000,))
            self.assertEqual(connection.execute(
                "SELECT COUNT(*) FROM capacity_padding").fetchone(), (1,))
        finally:
            connection.close()

    def test_migration_headroom_accounts_for_full_measured_database_and_wal_copy(self) -> None:
        with patch("bt_scheduler_monitor.store_migrations.measured_store_bytes", return_value=400_000):
            with self.assertRaisesRegex(StoreError, "estimated_bytes=1062144"):
                ensure_duplicate_table_headroom(self.path, 900_000, "WAL fixture migration")

    def test_distinct_events_from_one_frame_share_source_coordinates(self) -> None:
        cursor = SourceCursor("exec-1", "stdout", "boot-a", 1, 8)
        first = event(1, event_id="sha256:" + "a" * 64)
        second = event(1, event_id="sha256:" + "b" * 64)
        self.assertTrue(self.store.append_event(first, cursor))
        self.assertTrue(self.store.append_event(second, cursor))
        self.assertFalse(self.store.append_event(first, cursor))
        self.assertEqual(self.store.get_cursor("exec-1", "stdout"), cursor)
        self.assertEqual(self.store.get_event(first.event_id), first)
        self.assertEqual(self.store.get_event(second.event_id), second)

    def test_same_sequence_can_advance_across_jsonl_lines(self) -> None:
        first = event(1, event_id="sha256:" + "e" * 64, offset=8)
        second = event(1, event_id="sha256:" + "f" * 64, offset=16)
        self.assertTrue(self.store.append_event(first, SourceCursor("exec-1", "stdout", "boot-a", 1, 8)))
        self.assertTrue(self.store.append_event(second, SourceCursor("exec-1", "stdout", "boot-a", 1, 16)))
        self.assertEqual(self.store.get_cursor("exec-1", "stdout"), SourceCursor("exec-1", "stdout", "boot-a", 1, 16))
        regressed = event(1, event_id="sha256:" + "9" * 64, offset=12)
        with self.assertRaises(ValueError):
            self.store.append_event(regressed, SourceCursor("exec-1", "stdout", "boot-a", 1, 12))
        self.assertIsNone(self.store.get_event(regressed.event_id))

    def test_migrates_previous_sequence_unique_schema(self) -> None:
        legacy_path = Path(self.temp.name) / "legacy.sqlite3"
        connection = sqlite3.connect(legacy_path)
        try:
            connection.executescript("""CREATE TABLE schema_meta(version INTEGER NOT NULL);
                INSERT INTO schema_meta VALUES(1);
                CREATE TABLE normalized_events(event_id TEXT PRIMARY KEY, execution_id TEXT NOT NULL,
                    stream TEXT NOT NULL, sequence INTEGER NOT NULL, offset_bytes INTEGER NOT NULL, body TEXT NOT NULL,
                    UNIQUE(execution_id, stream, sequence));
                INSERT INTO normalized_events VALUES('old-event','exec-1','stdout',1,8,'{}');""")
        finally:
            connection.close()
        migrated = MonitorStore(legacy_path)
        source_event = event(1, event_id="sha256:" + "c" * 64)
        cursor = SourceCursor("exec-1", "stdout", "boot-a", 1, 8)
        self.assertTrue(migrated.append_event(source_event, cursor))
        self.assertEqual(migrated.get_cursor("exec-1", "stdout"), cursor)

    def test_refuses_v1_table_rebuild_without_duplicate_table_headroom(self) -> None:
        legacy_path = Path(self.temp.name) / "large-legacy.sqlite3"
        connection = sqlite3.connect(legacy_path)
        try:
            connection.executescript("""CREATE TABLE schema_meta(version INTEGER NOT NULL);
                INSERT INTO schema_meta VALUES(1);
                CREATE TABLE normalized_events(event_id TEXT PRIMARY KEY, execution_id TEXT NOT NULL,
                    stream TEXT NOT NULL, sequence INTEGER NOT NULL, offset_bytes INTEGER NOT NULL, body TEXT NOT NULL,
                    UNIQUE(execution_id, stream, sequence));""")
            connection.execute("INSERT INTO normalized_events VALUES(?,?,?,?,?,?)",
                               ("large-event", "exec-1", "stdout", 1, 8, "x" * 400_000))
            connection.commit()
        finally:
            connection.close()
        before_bytes = legacy_path.stat().st_size

        with self.assertRaisesRegex(StoreError, "schema migration requires bounded duplicate-table headroom"):
            MonitorStore(legacy_path, max_store_bytes=600_000)

        self.assertEqual(legacy_path.stat().st_size, before_bytes)
        connection = sqlite3.connect(legacy_path)
        try:
            self.assertEqual(connection.execute("SELECT version FROM schema_meta").fetchone(), (1,))
            self.assertTrue(any(index[2] for index in connection.execute(
                "PRAGMA index_list(normalized_events)")))
            self.assertIsNone(connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='store_limits'"
            ).fetchone())
        finally:
            connection.close()

    def test_rejects_inconsistent_same_sequence_coordinates_and_regressions(self) -> None:
        self.store.append_event(event(2), SourceCursor("exec-1", "stdout", "boot-a", 2, 16))
        invalid = (
            (event(2, event_id="sha256:" + "b" * 64, offset=8), SourceCursor("exec-1", "stdout", "boot-a", 2, 8)),
            (event(1, event_id="sha256:" + "c" * 64, offset=24), SourceCursor("exec-1", "stdout", "boot-a", 1, 24)),
            (event(3, event_id="sha256:" + "d" * 64, offset=8), SourceCursor("exec-1", "stdout", "boot-a", 3, 8)),
        )
        for source_event, cursor in invalid:
            with self.subTest(sequence=cursor.sequence, offset=cursor.offset_bytes):
                with self.assertRaises(ValueError):
                    self.store.append_event(source_event, cursor)
                self.assertIsNone(self.store.get_event(source_event.event_id))
        self.assertEqual(self.store.get_cursor("exec-1", "stdout"), SourceCursor("exec-1", "stdout", "boot-a", 2, 16))

    def test_incident_and_outbox_persist_with_claim_retry_and_stable_key(self) -> None:
        current = incident()
        self.assertTrue(self.store.enqueue_incident(current, "incident:incident-1:v1"))
        self.assertFalse(self.store.enqueue_incident(current, "incident:incident-1:v1"))
        claim, = self.store.claim_outbox("worker-a", now=100, lease_seconds=10)
        self.assertEqual(claim.idempotency_key, "incident:incident-1:v1")
        self.assertTrue(self.store.retry_outbox(claim.idempotency_key, "worker-a", "temporary_failure"))
        self.store = MonitorStore(self.path)
        retried, = self.store.claim_outbox("worker-b", now=101, lease_seconds=10)
        self.assertEqual((retried.attempts, retried.idempotency_key), (2, claim.idempotency_key))
        self.assertTrue(self.store.ack_outbox(retried.idempotency_key, "worker-b"))
        self.assertEqual(self.store.claim_outbox("worker-c", now=102, lease_seconds=10), ())
        self.assertEqual(self.store.get_incident(current.incident_id), current)

    def test_claim_lease_expires_after_restart_without_creating_another_item(self) -> None:
        self.store.enqueue_incident(incident(), "stable-key")
        self.store.claim_outbox("worker-a", now=1, lease_seconds=2)
        self.store = MonitorStore(self.path)
        claimed, = self.store.claim_outbox("worker-b", now=3, lease_seconds=2)
        self.assertEqual((claimed.idempotency_key, claimed.attempts), ("stable-key", 2))
        with self.assertRaises(ValueError):
            self.store.enqueue_incident(incident(), "stable-key", {"incident_id": "different"})

    def test_outbox_reference_rejects_every_field_that_disagrees_with_incident(self) -> None:
        current = incident()
        reference = {
            "schema_version": current.schema_version,
            "incident_id": current.incident_id,
            "run_id": current.run_id,
            "task_id": current.task_id,
            "attempt_id": current.attempt_id,
            "execution_id": current.execution_id,
            "detector_id": current.detector_id,
            "type": current.type,
            "severity": current.severity,
        }
        for field in reference:
            with self.subTest(field=field):
                mismatched = {**reference, field: f"different-{field}"}
                with self.assertRaises(ValueError):
                    self.store.enqueue_incident(current, f"key-{field}", mismatched)
                connection = sqlite3.connect(self.path)
                try:
                    count = connection.execute("SELECT COUNT(*) FROM m1_outbox").fetchone()[0]
                finally:
                    connection.close()
                self.assertEqual(count, 0)

        self.assertTrue(self.store.enqueue_incident(current, "default-reference"))
        claim, = self.store.claim_outbox("worker", now=1, lease_seconds=1, limit=1)
        self.assertEqual(dict(claim.payload), reference)

    def test_outbox_reference_must_match_the_persisted_incident_identity(self) -> None:
        persisted = incident()
        self.store.put_incident(persisted)
        mutations = {
            "schema_version": "1.0.1",
            "run_id": "other-run",
            "task_id": "other-task",
            "attempt_id": "other-attempt",
            "execution_id": "other-execution",
            "detector_id": "other_detector",
            "type": "timeout",
            "severity": "high",
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, "persisted incident"):
                    self.store.enqueue_incident(replace(persisted, **{field: value}), f"collision-{field}")
                self.assertEqual(self.store.get_incident(persisted.incident_id), persisted)
        connection = sqlite3.connect(self.path)
        try:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM m1_outbox").fetchone()[0], 0)
        finally:
            connection.close()

    def test_outbox_metadata_is_bounded_and_retry_errors_are_allowlisted(self) -> None:
        current = incident()
        with self.assertRaisesRegex(ValueError, "idempotency_key"):
            self.store.enqueue_incident(current, "k" * (MAX_OUTBOX_KEY_BYTES + 1))
        self.store.enqueue_incident(current, "stable-key")
        for claim_token, limit in (("w" * (MAX_OUTBOX_CLAIM_TOKEN_BYTES + 1), 1),
                                   ("worker", MAX_OUTBOX_CLAIM_BATCH + 1)):
            with self.subTest(claim_token_length=len(claim_token), limit=limit):
                with self.assertRaises(ValueError):
                    self.store.claim_outbox(claim_token, now=1, lease_seconds=1, limit=limit)
        claim, = self.store.claim_outbox("worker", now=1, lease_seconds=1)
        with self.assertRaisesRegex(ValueError, "allowlisted code"):
            self.store.retry_outbox(claim.idempotency_key, "worker", "provider token=private-secret")
        connection = sqlite3.connect(self.path)
        try:
            self.assertIsNone(connection.execute(
                "SELECT last_error FROM m1_outbox WHERE idempotency_key='stable-key'"
            ).fetchone()[0])
        finally:
            connection.close()
        self.assertTrue(self.store.retry_outbox(claim.idempotency_key, "worker", "temporary_failure"))

    def test_outbox_capacity_counts_only_undelivered_items(self) -> None:
        limited_store = MonitorStore(self.path, max_outbox_items=1)
        first = incident()
        second = replace(first, incident_id="incident-2")
        self.assertTrue(limited_store.enqueue_incident(first, "first"))

        with self.assertRaises(StoreError):
            limited_store.enqueue_incident(second, "second")
        self.assertIsNone(limited_store.get_incident(second.incident_id))
        connection = sqlite3.connect(self.path)
        try:
            outbox_count = connection.execute(
                "SELECT COUNT(*) FROM m1_outbox WHERE state IN ('pending', 'claimed')"
            ).fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(outbox_count, 1)

        claim, = limited_store.claim_outbox("worker", now=1, lease_seconds=1)
        self.assertTrue(limited_store.ack_outbox(claim.idempotency_key, "worker"))
        self.assertTrue(limited_store.enqueue_incident(second, "second"))

    def test_outbox_capacity_cannot_exceed_storage_derived_maximum(self) -> None:
        with self.assertRaises(ValueError):
            MonitorStore(self.path, max_outbox_items=MAX_OUTBOX_ITEMS + 1)

    def test_claim_outbox_rejects_nonfinite_clock_and_expiry(self) -> None:
        self.store.enqueue_incident(incident(), "stable-key")
        for now, lease in ((float("nan"), 1), (float("inf"), 1), (1, float("nan")),
                           (1, float("inf")), (1e308, 1e308)):
            with self.subTest(now=now, lease=lease):
                with self.assertRaises(ValueError):
                    self.store.claim_outbox("worker", now=now, lease_seconds=lease)
        claim, = self.store.claim_outbox("worker", now=1, lease_seconds=1)
        self.assertEqual(claim.idempotency_key, "stable-key")

    def test_incident_order_compares_utc_instants_not_timestamp_spellings(self) -> None:
        current = incident()
        self.store.put_incident(current)
        same_instant = replace(current, last_seen_at="2026-10-15T16:00:00+00:00")
        self.assertFalse(self.store.put_incident(same_instant))
        earlier = replace(same_instant, first_seen_at="2026-10-15T15:59:59Z",
                          last_seen_at="2026-10-15T15:59:59+00:00")
        with self.assertRaises(ValueError):
            self.store.put_incident(earlier)

    def test_incident_reference_identity_is_immutable_after_persistence(self) -> None:
        current = incident()
        self.store.put_incident(current)
        for field, value in (("schema_version", "1.0.1"), ("severity", "high")):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, "reference identity"):
                    self.store.put_incident(replace(current, **{field: value}))
                self.assertEqual(self.store.get_incident(current.incident_id), current)

    def test_rejects_inconsistent_cursor_and_invalid_external_records(self) -> None:
        with self.assertRaises(ValueError):
            self.store.append_event(event(1), SourceCursor("other-exec", "stdout", "boot-a", 1, 8))
        with self.assertRaises(ValueError):
            SourceCursor("exec-1", "stdout", "boot-a", True, 8)
        with self.assertRaises(ValueError):
            self.store.append_event(event(1), SourceCursor("exec-1", "stdout", "different-boot", 1, 8))
        with self.assertRaises(ValueError):
            self.store.enqueue_incident(incident(), "key", {"stderr": "private source text"})

    def test_database_persists_normalized_contracts_without_raw_stream_content(self) -> None:
        sentinel = "private-provider-stream-content"
        self.store.append_event(event(1), SourceCursor("exec-1", "stdout", "boot-a", 1, 8))
        self.store.enqueue_incident(incident(), "key")
        connection = sqlite3.connect(self.path)
        try:
            persisted = " ".join(row[0] for row in connection.execute(
                "SELECT body FROM normalized_events UNION ALL SELECT body FROM incidents UNION ALL SELECT body FROM m1_outbox"))
        finally:
            connection.close()
        self.assertNotIn(sentinel, persisted)
        self.assertNotIn("data", persisted)
        self.assertNotIn("raw", persisted)


if __name__ == "__main__":
    unittest.main()
