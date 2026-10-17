from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from bt_scheduler_monitor import retention as retention_module
from bt_scheduler_monitor.contracts import MetricSample
from bt_scheduler_monitor.retention import apply_retention, record_metric_sample
from bt_scheduler_monitor.store import MonitorStore


class RetentionPressureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "monitor.sqlite3"
        MonitorStore(self.path)
        self.now = datetime(2026, 10, 15, tzinfo=timezone.utc)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _add_expired_events(self, count: int = 200) -> int:
        apply_retention(self.path, now=self.now)
        old = (self.now - timedelta(days=91)).isoformat().replace("+00:00", "Z")
        connection = sqlite3.connect(self.path)
        try:
            connection.executemany("INSERT INTO normalized_events VALUES(?,?,?,?,?,?)",
                                   [(f"near-cap-{index}", "exec-1", "stdout", index, index,
                                     json.dumps({"received_at": old, "detail": "x" * 7000}))
                                    for index in range(count)])
            connection.commit()
            connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        finally:
            connection.close()
        return self.path.stat().st_size

    def test_retention_reports_pressure_at_zero_headroom_without_crossing_hard_cap(self) -> None:
        before_bytes = self._add_expired_events()

        result = apply_retention(self.path, now=self.now, max_store_bytes=before_bytes)

        self.assertEqual(result.deleted_events, 0)
        self.assertEqual(result.measured_bytes, before_bytes)
        self.assertTrue(result.storage_pressure)
        connection = sqlite3.connect(self.path)
        try:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM normalized_events").fetchone()[0], 200)
            self.assertEqual(connection.execute("PRAGMA journal_mode").fetchone()[0], "wal")
        finally:
            connection.close()

    def test_metric_compaction_near_cap_keeps_database_and_wal_within_limit(self) -> None:
        old = (self.now - timedelta(days=91)).isoformat().replace("+00:00", "Z")
        for index in range(8):
            sample = MetricSample("1.0.0", f"near-cap-metric-{index}", "codex", "tokens_used", index + 1,
                                  "token", "provider_reported", old, "reported", 1,
                                  "codex/model-a/tokens", profile_id="profile-a", model="model-a")
            record_metric_sample(self.path, sample)

        connection = sqlite3.connect(self.path)
        try:
            connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        finally:
            connection.close()
        before_bytes = self.path.stat().st_size
        max_store_bytes = before_bytes + retention_module.WRITE_RESERVE_BYTES // 2
        projected_sizes: list[int] = []
        finish_batch = retention_module._finish_retention_batch

        def measure_batch(connection, path, limit, baseline, *, maintenance):
            projected_sizes.append(retention_module._store_size(path))
            return finish_batch(connection, path, limit, baseline, maintenance=maintenance)

        with patch.object(retention_module, "_finish_retention_batch", side_effect=measure_batch):
            result = apply_retention(self.path, now=self.now, max_store_bytes=max_store_bytes)

        self.assertEqual(result.compacted_samples, 8)
        self.assertTrue(projected_sizes)
        self.assertLessEqual(max(projected_sizes), max_store_bytes)
        self.assertLessEqual(result.measured_bytes, max_store_bytes)
        connection = sqlite3.connect(self.path)
        try:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM metric_samples").fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT sample_count FROM daily_metric_aggregates").fetchone()[0], 8)
        finally:
            connection.close()

    def test_retention_retries_vacuum_from_free_pages_after_a_failed_attempt(self) -> None:
        before_bytes = self._add_expired_events()
        max_store_bytes = before_bytes + retention_module.WRITE_RESERVE_BYTES // 2

        with patch.object(retention_module, "_vacuum_store", side_effect=sqlite3.OperationalError("disk busy")):
            with self.assertRaisesRegex(sqlite3.OperationalError, "disk busy"):
                apply_retention(self.path, now=self.now, max_store_bytes=max_store_bytes,
                                sqlite_temp_dirs=(self.temp.name,))

        connection = sqlite3.connect(self.path)
        try:
            self.assertGreater(connection.execute("PRAGMA freelist_count").fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM normalized_events").fetchone()[0], 0)
        finally:
            connection.close()

        result = apply_retention(self.path, now=self.now, max_store_bytes=max_store_bytes,
                                 sqlite_temp_dirs=(self.temp.name,))
        self.assertLess(result.measured_bytes, before_bytes)
        self.assertFalse(result.storage_pressure)

    def test_vacuum_preflight_requires_room_in_every_declared_sqlite_temp_directory(self) -> None:
        first_temp_dir = Path(self.temp.name) / "first-temp"
        second_temp_dir = Path(self.temp.name) / "second-temp"
        first_temp_dir.mkdir()
        second_temp_dir.mkdir()
        database_bytes = self.path.stat().st_size
        base_usage = retention_module.shutil.disk_usage(self.temp.name)
        free_by_path = {
            self.path.parent: database_bytes * 2 + retention_module.RETENTION_BATCH_RESERVE_BYTES,
            first_temp_dir: database_bytes + retention_module.RETENTION_BATCH_RESERVE_BYTES,
            second_temp_dir: database_bytes + retention_module.RETENTION_BATCH_RESERVE_BYTES - 1,
        }

        def usage(directory: str | Path):
            return base_usage._replace(free=free_by_path[Path(directory)])

        with patch.object(retention_module.shutil, "disk_usage", side_effect=usage):
            self.assertFalse(retention_module._vacuum_has_temporary_space(
                self.path, (first_temp_dir, second_temp_dir)))

    def test_retention_defers_vacuum_without_explicit_sqlite_temp_directories(self) -> None:
        before_bytes = self._add_expired_events()
        max_store_bytes = before_bytes + retention_module.WRITE_RESERVE_BYTES // 2

        with patch.object(retention_module, "_vacuum_store") as vacuum:
            result = apply_retention(self.path, now=self.now, max_store_bytes=max_store_bytes)

        vacuum.assert_not_called()
        self.assertEqual(result.deleted_events, 200)
        self.assertTrue(result.storage_pressure)

    def test_retention_defers_vacuum_when_temporary_filesystem_lacks_room(self) -> None:
        before_bytes = self._add_expired_events()
        max_store_bytes = before_bytes + retention_module.WRITE_RESERVE_BYTES // 2
        temp_dir = Path(self.temp.name) / "sqlite-temp"
        temp_dir.mkdir()
        base_usage = retention_module.shutil.disk_usage(self.temp.name)

        def usage(directory: str | Path):
            free = base_usage.free if Path(directory) == self.path.parent else 0
            return base_usage._replace(free=free)

        with patch.object(retention_module.shutil, "disk_usage", side_effect=usage), \
                patch.object(retention_module, "_vacuum_store") as vacuum:
            result = apply_retention(self.path, now=self.now, max_store_bytes=max_store_bytes,
                                     sqlite_temp_dirs=(temp_dir,))

        vacuum.assert_not_called()
        self.assertEqual(result.deleted_events, 200)
        self.assertLessEqual(result.measured_bytes, max_store_bytes)
        self.assertTrue(result.storage_pressure)
        connection = sqlite3.connect(self.path)
        try:
            self.assertGreater(connection.execute("PRAGMA freelist_count").fetchone()[0], 0)
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
