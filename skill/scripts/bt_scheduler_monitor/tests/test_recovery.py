from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import stat
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from bt_scheduler_monitor.contracts import Incident
from bt_scheduler_monitor.recovery import (
    RecoveryError,
    export_archive,
    prepare_candidate,
    verify_archive,
    verify_candidate,
)
from bt_scheduler_monitor.storage_limits import StoreError, measured_store_bytes
from bt_scheduler_monitor.store import MonitorStore

NOW = datetime(2026, 10, 15, tzinfo=UTC)
CAP = 3_000_000


def _incident() -> Incident:
    stamp = "2026-10-15T00:00:00Z"
    return Incident("1.0.0", "incident-open", "run-1", "task-1", "attempt-1", "exec-1",
                    "missed_heartbeat", "missed_heartbeat", "medium", "low", stamp, stamp, 1,
                    (), ("sha256:" + "a" * 64,), "open")


def _signature(path: Path) -> dict[str, tuple[int, str] | None]:
    result: dict[str, tuple[int, str] | None] = {}
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(str(path) + suffix)
        result[suffix or "database"] = ((candidate.stat().st_size,
            hashlib.sha256(candidate.read_bytes()).hexdigest()) if candidate.exists() else None)
    return result


class RecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "monitor.sqlite3"
        store = MonitorStore(self.source, max_store_bytes=CAP)
        incident = _incident()
        store.enqueue_incident(incident, "pending-open-incident")
        connection = sqlite3.connect(self.source)
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            old = "2026-07-01T00:00:00Z"
            connection.executemany(
                "INSERT INTO normalized_events VALUES(?,?,?,?,?,?)",
                [(f"expired-{index}", "exec-1", "stdout", index, index,
                  json.dumps({"received_at": old, "detail": "x" * 12_000})) for index in range(160)],
            )
            connection.commit()
        finally:
            connection.close()
        self.archive = self.root / "archive.sqlite3"
        self.archive_manifest = self.root / "archive.manifest.json"
        self.candidate = self.root / "candidate.sqlite3"
        self.candidate_manifest = self.root / "candidate.manifest.json"
        self.sqlite_temp = self.root / "sqlite-temp"
        self.sqlite_temp.mkdir()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _export(self) -> dict[str, object]:
        return export_archive(self.source, self.archive, self.archive_manifest, max_store_bytes=CAP)

    def test_archive_is_complete_verifiable_no_overwrite_and_source_byte_identical(self) -> None:
        before = _signature(self.source)

        result = self._export()
        verified = verify_archive(self.archive, self.archive_manifest)

        self.assertEqual(_signature(self.source), before)
        self.assertEqual(result["sha256"], verified["sha256"])
        self.assertEqual(verified["evidence"]["schema_version"], 2)
        self.assertEqual(verified["evidence"]["table_counts"]["normalized_events"], 160)
        self.assertEqual(verified["evidence"]["protected"]["open_incidents"]["count"], 1)
        self.assertEqual(verified["evidence"]["protected"]["undelivered_outbox"]["count"], 1)
        manifest_text = self.archive_manifest.read_text(encoding="utf-8")
        self.assertNotIn("x" * 80, manifest_text)
        with self.assertRaisesRegex(RecoveryError, "already exists"):
            self._export()

    def test_candidate_reclaims_expired_rows_preserves_protected_records_and_caps_writes(self) -> None:
        self._export()
        source_before = _signature(self.source)
        archive_before = hashlib.sha256(self.archive.read_bytes()).hexdigest()

        result = prepare_candidate(self.archive, self.archive_manifest, self.candidate, self.candidate_manifest,
                                   sqlite_temp_dirs=(self.sqlite_temp,), max_store_bytes=CAP, now=NOW)
        verified = verify_candidate(self.candidate, self.candidate_manifest)

        self.assertEqual(_signature(self.source), source_before)
        self.assertEqual(hashlib.sha256(self.archive.read_bytes()).hexdigest(), archive_before)
        self.assertLess(measured_store_bytes(self.candidate) + 256 * 1024, CAP)
        self.assertEqual(verified["sha256"], result["sha256"])
        recovery = verified["recovery"]
        self.assertEqual(recovery["source_archive_sha256"], archive_before)
        self.assertGreater(recovery["retention"]["deleted_events"], 0)
        self.assertEqual(verified["evidence"]["table_counts"]["normalized_events"], 0)
        self.assertEqual(verified["evidence"]["protected"]["open_incidents"]["count"], 1)
        self.assertEqual(verified["evidence"]["protected"]["undelivered_outbox"]["count"], 1)
        candidate_store = MonitorStore(self.candidate, max_store_bytes=CAP)
        self.assertEqual(candidate_store.get_incident("incident-open"), _incident())
        self.assertEqual(candidate_store.claim_outbox("recovery-check", now=0, lease_seconds=60)[0].idempotency_key,
                         "pending-open-incident")

    def test_candidate_refuses_missing_or_insufficient_temp_directories_without_publishing(self) -> None:
        self._export()
        missing = self.root / "missing-temp-dir"

        with self.assertRaisesRegex(StoreError, "recovery_vacuum_space_unavailable"):
            prepare_candidate(self.archive, self.archive_manifest, self.candidate, self.candidate_manifest,
                              sqlite_temp_dirs=(self.sqlite_temp, missing), max_store_bytes=CAP, now=NOW)

        self.assertFalse(self.candidate.exists())
        self.assertFalse(self.candidate_manifest.exists())

    def test_candidate_refuses_insufficient_filesystem_headroom(self) -> None:
        self._export()

        with (patch("bt_scheduler_monitor.retention.shutil.disk_usage", return_value=SimpleNamespace(free=0)),
              self.assertRaisesRegex(StoreError, "recovery_vacuum_space_unavailable")):
            prepare_candidate(self.archive, self.archive_manifest, self.candidate, self.candidate_manifest,
                              sqlite_temp_dirs=(self.sqlite_temp,), max_store_bytes=CAP, now=NOW)

        self.assertFalse(self.candidate.exists())
        self.assertFalse(self.candidate_manifest.exists())

    def test_archive_verification_rejects_changed_database_bytes(self) -> None:
        self._export()
        with self.archive.open("ab") as stream:
            stream.write(b"tampered")

        with self.assertRaisesRegex(RecoveryError, "SHA-256"):
            verify_archive(self.archive, self.archive_manifest)

    def test_archive_verification_rejects_database_or_manifest_tampering(self) -> None:
        self._export()
        body = json.loads(self.archive_manifest.read_text(encoding="utf-8"))
        body["evidence"]["table_counts"]["normalized_events"] += 1
        self.archive_manifest.write_text(json.dumps(body), encoding="utf-8")

        with self.assertRaisesRegex(RecoveryError, "manifest evidence"):
            verify_archive(self.archive, self.archive_manifest)

    def test_candidate_destinations_are_no_overwrite(self) -> None:
        self._export()
        self.candidate.write_bytes(b"operator data")

        with self.assertRaisesRegex(RecoveryError, "already exists"):
            prepare_candidate(self.archive, self.archive_manifest, self.candidate, self.candidate_manifest,
                              sqlite_temp_dirs=(self.sqlite_temp,), max_store_bytes=CAP, now=NOW)

        self.assertEqual(self.candidate.read_bytes(), b"operator data")
        self.assertFalse(self.candidate_manifest.exists())

    def test_archive_candidate_and_manifests_are_private_with_permissive_umask(self) -> None:
        previous_umask = os.umask(0o022)
        try:
            self._export()
            prepare_candidate(self.archive, self.archive_manifest, self.candidate, self.candidate_manifest,
                              sqlite_temp_dirs=(self.sqlite_temp,), max_store_bytes=CAP, now=NOW)
        finally:
            os.umask(previous_umask)

        for path in (self.archive, self.archive_manifest, self.candidate, self.candidate_manifest):
            with self.subTest(path=path.name):
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)


if __name__ == "__main__":
    unittest.main()
