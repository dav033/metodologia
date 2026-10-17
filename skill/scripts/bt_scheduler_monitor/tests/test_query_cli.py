from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from bt_scheduler_monitor.cli import main
from bt_scheduler_monitor.contracts import MetricSample, NormalizedEvent, ProcessIdentity
from bt_scheduler_monitor.queries import status
from bt_scheduler_monitor.retention import AGGREGATE_DAYS, MAX_STORE_BYTES, apply_retention, record_metric_sample
from bt_scheduler_monitor.store import MonitorStore, SourceCursor, StoreError

NOW = datetime(2026, 10, 15, tzinfo=timezone.utc)
IDENTITY = ProcessIdentity("linux", "boot-a", 23, 100)


def event(sequence: int, received_at: str) -> NormalizedEvent:
    return NormalizedEvent("1.0.0", f"sha256:{sequence:064x}", "fixture/1", "1.0.0", "run-1", 1,
                           "task-1", "attempt-1", "exec-1", IDENTITY, "codex", "profile-1", "model-1",
                           "heartbeat", "heartbeat", received_at, "stdout", sequence, sequence * 8,
                           (("status", "started"),), "reported", host_boot_id="boot-a")


def metric(metric_id: str, observed_at: str, *, key: str = "codex/model-a/tokens", value: int = 4) -> MetricSample:
    return MetricSample("1.0.0", metric_id, "codex", "tokens_used", value, "token", "provider_reported",
                        observed_at, "reported", 1, key, profile_id="profile-a", model="model-a")


class QueryAndRetentionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "monitor.sqlite3"
        self.store = MonitorStore(self.path)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_retention_prunes_events_and_resolved_incidents_but_keeps_open_and_aggregates(self) -> None:
        old = (NOW - timedelta(days=91)).isoformat().replace("+00:00", "Z")
        self.store.append_event(event(1, old), SourceCursor("exec-1", "stdout", "boot-a", 1, 8))
        apply_retention(self.path, now=NOW)
        self.assertIsNone(self.store.get_event("sha256:" + f"{1:064x}"))
        self.assertEqual(self.store.get_cursor("exec-1", "stdout").sequence, 1)

    def test_event_retention_uses_instants_for_fractional_and_equivalent_utc_timestamps(self) -> None:
        before_cutoff = "2026-07-17T11:59:59.999999Z"
        at_cutoff = "2026-07-17T12:00:00.000000+00:00"
        self.store.append_event(event(1, before_cutoff), SourceCursor("exec-1", "stdout", "boot-a", 1, 8))
        self.store.append_event(event(2, at_cutoff), SourceCursor("exec-1", "stdout", "boot-a", 2, 16))
        apply_retention(self.path, now=NOW + timedelta(hours=12))
        self.assertIsNone(self.store.get_event("sha256:" + f"{1:064x}"))
        self.assertIsNotNone(self.store.get_event("sha256:" + f"{2:064x}"))

    def test_old_resolved_incident_is_pruned_but_open_incident_is_never_evicted(self) -> None:
        from bt_scheduler_monitor.contracts import Incident
        old = (NOW - timedelta(days=366)).isoformat().replace("+00:00", "Z")
        resolved = Incident("1.0.0", "resolved-old", "run-1", "task-1", "attempt-1", "exec-1",
                            "missed_heartbeat", "missed_heartbeat", "medium", "low", old, old, 1, (), (),
                            "resolved", resolved_at=old)
        open_incident = Incident("1.0.0", "open-old", "run-1", "task-1", "attempt-1", "exec-1",
                                 "missed_heartbeat", "missed_heartbeat", "medium", "low", old, old, 1, (), (), "open")
        self.store.put_incident(resolved)
        self.store.put_incident(open_incident)
        result = apply_retention(self.path, now=NOW)
        self.assertEqual(result.deleted_incidents, 1)
        self.assertIsNone(self.store.get_incident("resolved-old"))
        self.assertEqual(self.store.get_incident("open-old"), open_incident)

    def test_retention_preserves_incidents_with_live_outbox_and_prunes_acked_outbox(self) -> None:
        from bt_scheduler_monitor.contracts import Incident
        import sqlite3

        old = (NOW - timedelta(days=366)).isoformat().replace("+00:00", "Z")
        incidents = {
            name: Incident("1.0.0", name, "run-1", "task-1", "attempt-1", "exec-1",
                           "missed_heartbeat", "missed_heartbeat", "medium", "low", old, old, 1, (), (),
                           "resolved", resolved_at=old)
            for name in ("pending-old", "claimed-old", "acked-old")
        }
        for incident in incidents.values():
            self.store.put_incident(incident)
        connection = sqlite3.connect(self.path)
        try:
            connection.executemany("INSERT INTO m1_outbox(idempotency_key,incident_id,body,state) VALUES(?,?,?,?)",
                                   [(f"key-{name}", name, "{}", state) for name, state in
                                    (("pending-old", "pending"), ("claimed-old", "claimed"),
                                     ("acked-old", "acked"))])
            connection.commit()
        finally:
            connection.close()

        result = apply_retention(self.path, now=NOW)

        self.assertEqual(result.deleted_incidents, 1)
        self.assertIsNone(self.store.get_incident("acked-old"))
        self.assertEqual(self.store.get_incident("pending-old"), incidents["pending-old"])
        self.assertEqual(self.store.get_incident("claimed-old"), incidents["claimed-old"])
        connection = sqlite3.connect(self.path)
        try:
            outbox = dict(connection.execute("SELECT incident_id,state FROM m1_outbox"))
            self.assertEqual(outbox, {"pending-old": "pending", "claimed-old": "claimed"})
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
        finally:
            connection.close()

    def test_retention_deletes_evidence_references_in_bounded_batches_before_incident(self) -> None:
        import sqlite3
        from bt_scheduler_monitor.contracts import Incident
        from bt_scheduler_monitor.validation import MAX_EVIDENCE_REFS

        old = (NOW - timedelta(days=366)).isoformat().replace("+00:00", "Z")
        expired = Incident("1.0.0", "many-evidence-old", "run-1", "task-1", "attempt-1", "exec-1",
                           "missed_heartbeat", "missed_heartbeat", "medium", "low", old, old, 1, (),
                           tuple(f"ref-{index:04d}" for index in range(MAX_EVIDENCE_REFS)), "resolved",
                           resolved_at=old)
        self.store.put_incident(expired)
        result = apply_retention(self.path, now=NOW)

        self.assertEqual(result.deleted_incidents, 1)
        self.assertIsNone(self.store.get_incident(expired.incident_id))
        connection = sqlite3.connect(self.path)
        try:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM incident_evidence_refs").fetchone(), (0,))
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
        finally:
            connection.close()

    def test_retention_reports_over_cap_without_mutating_store_or_evicting_live_records(self) -> None:
        import sqlite3
        from bt_scheduler_monitor.contracts import Incident

        old = (NOW - timedelta(days=91)).isoformat().replace("+00:00", "Z")
        connection = sqlite3.connect(self.path)
        try:
            connection.executemany("INSERT INTO normalized_events VALUES(?,?,?,?,?,?)",
                                   [(f"old-{index}", "exec-1", "stdout", index, index,
                                     json.dumps({"received_at": old, "detail": "x" * 7000}))
                                    for index in range(300)])
            connection.commit()
        finally:
            connection.close()
        before_bytes = self.path.stat().st_size
        cap = before_bytes // 2
        incident_old = (NOW - timedelta(days=366)).isoformat().replace("+00:00", "Z")
        open_incident = Incident("1.0.0", "open-under-pressure", "run-1", "task-1", "attempt-1", "exec-1",
                                 "missed_heartbeat", "missed_heartbeat", "medium", "low", incident_old,
                                 incident_old, 1, (), (), "open")
        pending_incident = Incident("1.0.0", "pending-under-pressure", "run-1", "task-1", "attempt-1", "exec-1",
                                    "missed_heartbeat", "missed_heartbeat", "medium", "low", incident_old,
                                    incident_old, 1, (), (), "resolved", resolved_at=incident_old)
        self.store.put_incident(open_incident)
        self.store.put_incident(pending_incident)
        connection = sqlite3.connect(self.path)
        try:
            connection.execute("INSERT INTO m1_outbox(idempotency_key,incident_id,body,state) VALUES(?,?,?,?)",
                               ("pending-live", "pending-under-pressure", "{}", "pending"))
            connection.commit()
            connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        finally:
            connection.close()

        over_cap_bytes = sum(candidate.stat().st_size for candidate in
                             (self.path, Path(str(self.path) + "-wal")) if candidate.exists())
        cap = min(cap, over_cap_bytes - 1)
        result = apply_retention(self.path, now=NOW, max_store_bytes=cap)

        self.assertTrue(result.storage_pressure)
        self.assertEqual(result.measured_bytes, over_cap_bytes)
        self.assertGreater(result.measured_bytes, cap)
        self.assertEqual(self.store.get_incident("open-under-pressure"), open_incident)
        self.assertEqual(self.store.get_incident("pending-under-pressure"), pending_incident)
        connection = sqlite3.connect(self.path)
        try:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM normalized_events").fetchone(), (300,))
            self.assertEqual(connection.execute("SELECT state FROM m1_outbox WHERE idempotency_key='pending-live'").fetchone(),
                             ("pending",))
        finally:
            connection.close()

    def test_metric_compaction_separates_unknown_and_distinct_comparability(self) -> None:
        old = (NOW - timedelta(days=91)).isoformat().replace("+00:00", "Z")
        first = metric("metric-1", old, key="unknown-a")
        second = metric("metric-2", old, key="unknown-b")
        comparable_a = metric("metric-3", old, key="codex/model-a/tokens")
        comparable_b = metric("metric-4", old, key="codex/model-a/tokens")
        record_metric_sample(self.path, first)
        record_metric_sample(self.path, second)
        record_metric_sample(self.path, comparable_a)
        record_metric_sample(self.path, comparable_b)
        result = apply_retention(self.path, now=NOW)
        self.assertEqual(result.compacted_samples, 4)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["metrics", "--store", str(self.path)])
        self.assertEqual(code, 0)
        rows = json.loads(output.getvalue())["items"]
        self.assertTrue({"unknown-a", "unknown-b"}.issubset({row["comparability_key"] for row in rows}))
        comparable = next(row for row in rows if row["comparability_key"] == "codex/model-a/tokens")
        self.assertEqual((comparable["value"], comparable["sample_count"]), (8.0, 2))

    def test_metric_retention_compares_instants_and_tracks_chronological_bounds(self) -> None:
        before_cutoff = metric("metric-old", "2026-07-17T11:59:59.999999Z", key="unknown-old")
        at_cutoff = metric("metric-boundary", "2026-07-17T12:00:00.000000+00:00")
        later = metric("metric-a", "2026-07-16T23:00:00.000002+00:00")
        earlier = metric("metric-z", "2026-07-16T23:00:00.000001Z")
        for sample in (before_cutoff, at_cutoff, later, earlier):
            record_metric_sample(self.path, sample)
        result = apply_retention(self.path, now=NOW + timedelta(hours=12))
        self.assertEqual(result.compacted_samples, 3)
        import sqlite3
        connection = sqlite3.connect(self.path)
        try:
            aggregate = connection.execute("""SELECT first_observed_at,last_observed_at
                FROM daily_metric_aggregates WHERE day='2026-07-16'
                AND comparability_key='codex/model-a/tokens'""").fetchone()
            retained = connection.execute("SELECT metric_id FROM metric_samples WHERE metric_id='metric-boundary'").fetchone()
        finally:
            connection.close()
        self.assertEqual(aggregate, ("2026-07-16T23:00:00.000001Z", "2026-07-16T23:00:00.000002+00:00"))
        self.assertEqual(retained, ("metric-boundary",))

    def test_metric_aggregate_merge_handles_late_earlier_and_equivalent_utc_timestamps(self) -> None:
        later = metric("metric-later", "2026-07-16T23:00:00.000002+00:00")
        record_metric_sample(self.path, later)
        apply_retention(self.path, now=NOW)
        earlier_z = metric("metric-earlier-z", "2026-07-16T23:00:00.000001Z")
        earlier_offset = metric("metric-earlier-offset", "2026-07-16T23:00:00.000001+00:00")
        record_metric_sample(self.path, earlier_z)
        record_metric_sample(self.path, earlier_offset)
        apply_retention(self.path, now=NOW)
        import sqlite3
        connection = sqlite3.connect(self.path)
        try:
            first, last = connection.execute("""SELECT first_observed_at,last_observed_at
                FROM daily_metric_aggregates WHERE day='2026-07-16'
                AND comparability_key='codex/model-a/tokens'""").fetchone()
        finally:
            connection.close()
        self.assertEqual(datetime.fromisoformat(first.replace("Z", "+00:00")),
                         datetime.fromisoformat("2026-07-16T23:00:00.000001+00:00"))
        self.assertEqual(datetime.fromisoformat(last.replace("Z", "+00:00")),
                         datetime.fromisoformat("2026-07-16T23:00:00.000002+00:00"))

    def test_unknown_metric_aggregate_keeps_value_null_not_zero(self) -> None:
        old = (NOW - timedelta(days=91)).isoformat().replace("+00:00", "Z")
        unavailable = MetricSample("1.0.0", "metric-unknown", "codex", "tokens_used", None, "token",
                                    "provider_reported", old, "unknown", 0, "codex/model-a/tokens",
                                    profile_id="profile-a", model="model-a")
        record_metric_sample(self.path, unavailable)
        apply_retention(self.path, now=NOW)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["metrics", "--store", str(self.path)])
        self.assertEqual(code, 0)
        aggregate, = json.loads(output.getvalue())["items"]
        self.assertIsNone(aggregate["value"])
        self.assertEqual(aggregate["sample_count"], 0)

    def test_metric_extension_v1_migrates_transactionally_to_nullable_aggregate_value(self) -> None:
        import sqlite3
        connection = sqlite3.connect(self.path)
        try:
            connection.executescript("""CREATE TABLE m4_extension_meta(name TEXT PRIMARY KEY,version INTEGER NOT NULL);
                INSERT INTO m4_extension_meta VALUES('metrics',1);
                CREATE TABLE metric_samples(metric_id TEXT PRIMARY KEY,observed_at TEXT NOT NULL,body TEXT NOT NULL);
                CREATE TABLE daily_metric_aggregates(
                  day TEXT NOT NULL,group_key TEXT NOT NULL,provider TEXT NOT NULL,name TEXT NOT NULL,
                  unit TEXT NOT NULL,source TEXT NOT NULL,quality TEXT NOT NULL,comparability_key TEXT NOT NULL,
                  profile_id TEXT,model TEXT,value_sum REAL NOT NULL,sample_count INTEGER NOT NULL,
                  first_observed_at TEXT NOT NULL,last_observed_at TEXT NOT NULL,PRIMARY KEY(day,group_key));""")
        finally:
            connection.close()
        sample = metric("metric-migration", (NOW - timedelta(days=91)).isoformat().replace("+00:00", "Z"))
        record_metric_sample(self.path, sample)
        connection = sqlite3.connect(self.path)
        try:
            version, = connection.execute("SELECT version FROM m4_extension_meta WHERE name='metrics'").fetchone()
            value_sum = next(row for row in connection.execute("PRAGMA table_info(daily_metric_aggregates)")
                             if row[1] == "value_sum")
        finally:
            connection.close()
        self.assertEqual(version, 2)
        self.assertEqual(value_sum[3], 0)

    def test_metric_extension_migration_refuses_duplicate_table_without_headroom(self) -> None:
        import sqlite3

        connection = sqlite3.connect(self.path)
        try:
            connection.executescript("""CREATE TABLE m4_extension_meta(name TEXT PRIMARY KEY,version INTEGER NOT NULL);
                INSERT INTO m4_extension_meta VALUES('metrics',1);
                CREATE TABLE metric_samples(metric_id TEXT PRIMARY KEY,observed_at TEXT NOT NULL,body TEXT NOT NULL);
                CREATE TABLE daily_metric_aggregates(
                  day TEXT NOT NULL,group_key TEXT NOT NULL,provider TEXT NOT NULL,name TEXT NOT NULL,
                  unit TEXT NOT NULL,source TEXT NOT NULL,quality TEXT NOT NULL,comparability_key TEXT NOT NULL,
                  profile_id TEXT,model TEXT,value_sum REAL NOT NULL,sample_count INTEGER NOT NULL,
                  first_observed_at TEXT NOT NULL,last_observed_at TEXT NOT NULL,PRIMARY KEY(day,group_key));""")
            connection.execute("INSERT INTO daily_metric_aggregates VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                               ("2025-01-01", "group-1", "codex", "x" * 400_000, "token", "fixture",
                                "reported", "codex/model-a/tokens", "profile-a", "model-a", 1.0, 1,
                                "2025-01-01T00:00:00Z", "2025-01-01T00:00:00Z"))
            connection.commit()
        finally:
            connection.close()

        with self.assertRaisesRegex(StoreError, "M4 metric extension migration requires bounded duplicate-table headroom"):
            record_metric_sample(self.path, metric("metric-migration", NOW.isoformat().replace("+00:00", "Z")),
                                 max_store_bytes=800_000)

        connection = sqlite3.connect(self.path)
        try:
            self.assertEqual(connection.execute(
                "SELECT version FROM m4_extension_meta WHERE name='metrics'"
            ).fetchone(), (1,))
            self.assertIsNone(connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='daily_metric_aggregates_v2'"
            ).fetchone())
            self.assertIsNone(connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='index' AND name='metric_samples_observed'"
            ).fetchone())
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM metric_samples").fetchone(), (0,))
        finally:
            connection.close()

    def test_metric_older_than_instant_cutoff_on_same_utc_day_is_compacted(self) -> None:
        sample = metric("metric-same-day", "2026-07-17T11:00:00.000000Z")
        record_metric_sample(self.path, sample)
        result = apply_retention(self.path, now=NOW + timedelta(hours=12))
        self.assertEqual(result.compacted_samples, 1)

    def test_daily_aggregate_expiry_retains_the_730_day_boundary(self) -> None:
        cutoff_day = (NOW - timedelta(days=AGGREGATE_DAYS)).date()
        expired_day = cutoff_day - timedelta(days=1)
        record_metric_sample(self.path, metric("metric-expired", f"{expired_day.isoformat()}T12:00:00Z",
                                               key="expired-key"))
        record_metric_sample(self.path, metric("metric-boundary", f"{cutoff_day.isoformat()}T12:00:00Z",
                                               key="boundary-key"))
        apply_retention(self.path, now=NOW)
        import sqlite3
        connection = sqlite3.connect(self.path)
        try:
            days = {row[0] for row in connection.execute("SELECT day FROM daily_metric_aggregates")}
        finally:
            connection.close()
        self.assertNotIn(expired_day.isoformat(), days)
        self.assertIn(cutoff_day.isoformat(), days)

    def test_storage_pressure_is_reported_as_degraded_status_with_measured_bytes(self) -> None:
        import sqlite3

        self.store.append_event(event(1, NOW.isoformat().replace("+00:00", "Z")),
                                SourceCursor("exec-1", "stdout", "boot-a", 1, 8))
        connection = sqlite3.connect(self.path)
        try:
            connection.execute("UPDATE store_limits SET max_store_bytes=1 WHERE singleton=1")
            connection.commit()
        finally:
            connection.close()
        result = apply_retention(self.path, now=NOW, max_store_bytes=1)
        self.assertTrue(result.storage_pressure)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["status", "--store", str(self.path)])
        self.assertEqual(code, 0)
        data = json.loads(output.getvalue())
        self.assertEqual(data["status"], "degraded")
        self.assertEqual(data["storage"]["state"], "storage_pressure")
        self.assertEqual(data["storage"]["measured_bytes"], result.measured_bytes)

    def test_status_marks_stream_completeness_unknown_or_degraded_from_durable_gaps(self) -> None:
        self.assertEqual(status(self.path)["stream_status"], "unknown")
        self.store.record_stream_gap(gap_id="status-gap", execution_id="exec-1", stream="stdout",
                                     first_sequence=2, last_sequence=2, first_offset=16, last_offset=24,
                                     dropped_bytes=8, dropped_frames=1, reason="queue_overflow",
                                     recorded_at=NOW.isoformat().replace("+00:00", "Z"))
        data = status(self.path)
        self.assertEqual((data["stream_status"], data["stream_gaps"]), ("degraded", 1))

    def test_equal_to_measured_store_size_uses_strict_pressure_cap_and_reports_real_bytes(self) -> None:
        import sqlite3

        connection = sqlite3.connect(self.path)
        try:
            connection.execute("CREATE TABLE size_fixture(payload BLOB)")
            connection.execute("INSERT INTO size_fixture VALUES(zeroblob(300000))")
            connection.commit()
            connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        finally:
            connection.close()
        first = apply_retention(self.path, now=NOW, max_store_bytes=MAX_STORE_BYTES)
        limit = first.measured_bytes
        result = apply_retention(self.path, now=NOW, max_store_bytes=limit)
        actual = sum(candidate.stat().st_size for candidate in (self.path, Path(str(self.path) + "-wal"))
                     if candidate.exists())
        self.assertEqual(result.measured_bytes, actual)
        self.assertEqual(result.storage_pressure, actual + 256 * 1024 > limit)
        data = status(self.path, max_store_bytes=limit)
        self.assertEqual(data["storage"]["measured_bytes"], actual)
        self.assertEqual(data["status"] == "degraded", actual + 256 * 1024 > limit)

    def test_metric_cli_orders_fractional_utc_instants_newest_first(self) -> None:
        older = metric("metric-older", "2026-10-15T00:00:00Z")
        newest = metric("metric-newest", "2026-10-15T00:00:00.100000+00:00")
        record_metric_sample(self.path, older)
        record_metric_sample(self.path, newest)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["metrics", "--store", str(self.path), "--limit", "2"])
        self.assertEqual(code, 0)
        items = json.loads(output.getvalue())["items"]
        self.assertEqual([item["metric_id"] for item in items], ["metric-newest", "metric-older"])

    def test_status_and_incident_query_are_bounded_json_without_raw_provider_text(self) -> None:
        self.store.append_event(event(1, NOW.isoformat().replace("+00:00", "Z")),
                                SourceCursor("exec-1", "stdout", "boot-a", 1, 8))
        for args in (["status", "--store", str(self.path)], ["events", "--store", str(self.path), "--limit", "1"]):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(args)
            self.assertEqual(code, 0)
            self.assertLess(len(output.getvalue()), 16_384)
            self.assertNotIn("raw", output.getvalue().lower())
            self.assertIsInstance(json.loads(output.getvalue()), dict)

    def test_activity_cli_projects_tool_pending_and_identity_without_event_payload(self) -> None:
        started = replace(event(1, "2026-10-15T16:00:00Z"), event_type="tool_started",
                          source_event_type="tool_started", source_occurred_at="2026-10-15T16:00:00Z",
                          received_monotonic_ns=1_000_000_000,
                          payload=(("tool_label", "shell"), ("argument_digest", "sha256:" + "a" * 64)))
        usage = replace(event(2, "2026-10-15T16:00:01Z"), event_type="usage_reported",
                        source_event_type="usage_reported", source_occurred_at="2026-10-15T16:00:01Z",
                        received_monotonic_ns=2_000_000_000,
                        payload=(("metric_name", "tokens_used"), ("value", 42), ("unit", "token"),
                                 ("source", "provider_reported"), ("sample_count", 1)))
        self.store.append_event(started, SourceCursor("exec-1", "stdout", "boot-a", 1, 8))
        self.store.append_event(usage, SourceCursor("exec-1", "stdout", "boot-a", 2, 16))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["activity", "--store", str(self.path), "--limit", "1", "--execution-id", "exec-1"])
        self.assertEqual(code, 0)
        encoded = output.getvalue()
        data = json.loads(encoded)
        item, = data["items"]
        self.assertEqual(item["display_state"], "tool_pending")
        self.assertEqual(item["pending_tools"], ["shell"])
        self.assertEqual((item["provider"], item["process_identity"]["pid"]), ("codex", 23))
        self.assertEqual(item["metrics"][0]["source"], "provider_reported")
        self.assertNotIn("payload", item)
        self.assertNotIn("argument_digest", encoded)

    def test_activity_cli_marks_projection_unknown_when_event_window_truncates(self) -> None:
        for sequence in range(1, 1_002):
            self.store.append_event(event(sequence, f"2026-10-15T16:00:{sequence % 60:02d}Z"),
                                    SourceCursor("exec-1", "stdout", "boot-a", sequence, sequence * 8))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["activity", "--store", str(self.path)])
        self.assertEqual(code, 0)
        data = json.loads(output.getvalue())
        item, = data["items"]
        self.assertTrue(data["truncated"])
        self.assertTrue(item["projection_truncated"])
        self.assertEqual(item["display_state"], "unknown")

    def test_cli_store_failure_uses_stable_error_code(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            code = main(["status", "--store", str(self.path / "missing" / ".." / "nonexistent")])
        self.assertEqual(code, 3)
        self.assertEqual(json.loads(output.getvalue())["code"], "M4_STORE_ERROR")

    def test_cli_invalid_arguments_use_stable_error_code(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            code = main(["events", "--store", str(self.path), "--limit", "0"])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output.getvalue())["code"], "M4_INVALID_ARGUMENT")


if __name__ == "__main__":
    unittest.main()
