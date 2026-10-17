from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bt_scheduler_monitor import MetricSample
from bt_scheduler_monitor.retention import record_metric_sample
from bt_scheduler_monitor.store import MonitorStore
from bt_scheduler_monitor_adapter import read_metric_snapshots


class MonitorM2AdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "monitor.sqlite3"
        self.store = MonitorStore(self.path)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_reads_validated_provenance_snapshots_without_mutating_m4_store(self):
        sample = MetricSample("1.0.0", "sha256:" + "a" * 64, "codex", "output_tokens", 128, "tokens",
                              "provider_reported", "2026-10-15T16:00:00Z", "reported", 1,
                              "codex/profile-a/model-a/output_tokens", profile_id="profile-a", model="model-a")
        record_metric_sample(self.path, sample)
        before = self.path.read_bytes()

        snapshots = read_metric_snapshots(self.path, limit=10)

        self.assertEqual(snapshots, (sample,))
        self.assertEqual(self.path.read_bytes(), before)

    def test_missing_metric_extension_is_an_empty_optional_source(self):
        self.assertEqual(read_metric_snapshots(self.path), ())

    def test_missing_database_is_an_empty_optional_source_without_creating_it(self):
        missing = self.path.parent / "not-created.sqlite3"
        self.assertEqual(read_metric_snapshots(missing), ())
        self.assertFalse(missing.exists())

    def test_limit_is_bounded_and_requires_positive_integer(self):
        self.assertEqual(read_metric_snapshots(self.path, limit=10_000), ())
        with self.assertRaisesRegex(ValueError, "positive integer"):
            read_metric_snapshots(self.path, limit=0)

    def test_invalid_persisted_sample_is_rejected(self):
        connection = sqlite3.connect(self.path)
        try:
            connection.execute("CREATE TABLE metric_samples(metric_id TEXT PRIMARY KEY,observed_at TEXT NOT NULL,body TEXT NOT NULL)")
            connection.execute("INSERT INTO metric_samples VALUES(?,?,?)", ("bad", "2026-10-15T16:00:00Z",
                               json.dumps({"schema_version": "1.0.0", "provider": "bogus"})))
            connection.commit()
        finally:
            connection.close()
        with self.assertRaises(ValueError):
            read_metric_snapshots(self.path)

    def test_column_timestamp_must_match_validated_metric_timestamp(self):
        connection = sqlite3.connect(self.path)
        try:
            connection.execute("CREATE TABLE metric_samples(metric_id TEXT PRIMARY KEY,observed_at TEXT NOT NULL,body TEXT NOT NULL)")
            sample = MetricSample("1.0.0", "mismatch", "codex", "output_tokens", 1, "tokens",
                                  "provider_reported", "2026-10-15T16:00:00Z", "reported", 1, "key",
                                  profile_id="profile-a", model="model-a")
            connection.execute("INSERT INTO metric_samples VALUES(?,?,?)",
                               (sample.metric_id, "2026-10-14T16:00:00Z", json.dumps(sample.to_dict())))
            connection.commit()
        finally:
            connection.close()
        with self.assertRaisesRegex(ValueError, "metric_observed_at_mismatch"):
            read_metric_snapshots(self.path)


if __name__ == "__main__":
    unittest.main()
