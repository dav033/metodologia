from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bt_scheduler_quality.contracts import QualityError, VerifyRequest
from bt_scheduler_quality.evidence import canonical_json
from bt_scheduler_quality.store import QualityStore

FIXTURE = Path(__file__).parent / "fixtures" / "verify-order-pass.json"


class QualityStoreTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.order = VerifyRequest.from_mapping(self.raw)

    def test_version_one_store_opens_with_additive_flaky_history_table(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "quality.sqlite3"
            connection = sqlite3.connect(database)
            connection.execute("CREATE TABLE check_pass_cache (key TEXT PRIMARY KEY, exit_code INTEGER, "
                               "duration_ms INTEGER NOT NULL, stdout BLOB NOT NULL, stderr BLOB NOT NULL, created_at REAL NOT NULL)")
            connection.execute("PRAGMA user_version=1")
            connection.close()
            with QualityStore(database) as store:
                key = "a" * 64
                self.assertFalse(store.record_check_outcome(key, "fail", 1))
                self.assertTrue(store.record_check_outcome(key, "pass", 2))

    def test_permission_refresh_preserves_sqlite_lock_against_another_process(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "quality.sqlite3"
            with QualityStore(database) as store:
                store._connection.execute("BEGIN IMMEDIATE")
                try:
                    store._secure_database_files()
                    contender = subprocess.run(
                        [sys.executable, "-c", ("import sqlite3,sys; "
                         "c=sqlite3.connect(sys.argv[1], timeout=0); "
                         "c.execute('BEGIN IMMEDIATE')"), str(database)],
                        capture_output=True, text=True, timeout=10, check=False,
                    )
                    self.assertNotEqual(contender.returncode, 0, contender.stdout)
                    self.assertIn("database is locked", contender.stderr)
                finally:
                    store._connection.execute("ROLLBACK")

    def test_permission_refresh_does_not_open_sqlite_managed_files(self):
        # Closing another fd for the database or shm inode releases SQLite's
        # process-scoped POSIX locks, even though SQLite still owns its fd.
        with tempfile.TemporaryDirectory() as temporary, QualityStore(
            Path(temporary) / "quality.sqlite3"
        ) as store:
            with patch("bt_scheduler_quality.store.os.open") as opened:
                store.reserve(self.order)
            opened.assert_not_called()

    def test_reserves_idempotently_and_rejects_reused_key_with_new_content(self):
        with QualityStore(":memory:") as store:
            self.assertEqual(store.reserve(self.order), ("new", None))
            self.assertEqual(store.reserve(self.order), ("queued", None))
            changed = dict(self.raw)
            changed["verification"] = [
                dict(self.raw["verification"][0], value="python3 changed.py")
            ]

            with self.assertRaises(QualityError) as raised:
                store.reserve(VerifyRequest.from_mapping(changed))

        self.assertEqual(raised.exception.code, "IDEMPOTENCY_CONFLICT")

    def test_persists_result_artifacts_and_pending_outbox_across_restart(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "quality.sqlite3"
            store = QualityStore(database)
            store.reserve(self.order)
            self.assertTrue(store.claim_work(self.order.idempotency_key))
            result, result_bytes, manifest, artifacts = _result("PASS")
            store.finish(self.order, result, result_bytes, manifest, artifacts)
            store.close()

            reopened = QualityStore(database)
            deliveries = reopened.pending_deliveries()
            payload = reopened.begin_delivery(self.order.idempotency_key)
            loaded = reopened.get_result(self.order.idempotency_key)
            self.assertEqual(loaded["status"], result["status"])
            self.assertEqual(loaded["reason_code"], "UNCLASSIFIED")
            self.assertEqual(loaded["checks"][0]["reason_code"], "UNCLASSIFIED")
            self.assertEqual(
                reopened.get_artifact(result["stdout_ref"]), b"captured evidence\n"
            )
            self.assertEqual(len(deliveries), 1)
            self.assertEqual(payload["attempts"], 0)
            self.assertEqual(reopened.pending_deliveries()[0]["attempts"], 1)
            reopened.close()

            self.assertEqual(os.stat(database).st_mode & 0o777, 0o600)

    def test_review_resolution_is_explicit_and_creates_delivery_atomically(self):
        with QualityStore(":memory:") as store:
            store.reserve(self.order)
            self.assertTrue(store.claim_work(self.order.idempotency_key))
            result, result_bytes, manifest, artifacts = _result("NEEDS_REVIEW")
            store.finish(self.order, result, result_bytes, manifest, artifacts)
            self.assertEqual(len(store.list_reviews()), 1)
            evidence = store.resolve_review(
                self.order.idempotency_key,
                "david",
                "PASS",
                "Reviewed the visual proof.",
            )

            delivery = store.pending_deliveries()[0]
            review = store.list_reviews(include_resolved=True)[0]
            self.assertEqual(delivery["decision"], "PASS")
            self.assertEqual(delivery["evidence_ref"], evidence)
            self.assertEqual(review["state"], "resolved")
            self.assertEqual(review["resolved_by"], "david")

            with self.assertRaises(QualityError) as raised:
                store.resolve_review(
                    self.order.idempotency_key, "david", "FAIL", "changed mind"
                )

        self.assertEqual(raised.exception.code, "REVIEW_ALREADY_RESOLVED")

    def test_m5_resume_requeues_only_one_timeout_review_without_creating_a_verdict(self):
        with QualityStore(":memory:") as store:
            store.reserve(self.order)
            self.assertTrue(store.claim_work(self.order.idempotency_key))
            result, _result_bytes, manifest, artifacts = _result("NEEDS_REVIEW")
            result["reason_code"] = "TIMEOUT"
            store.finish(self.order, result, canonical_json(result), manifest, artifacts)
            store.retry_m5_transient(self.order.idempotency_key)
            self.assertEqual(store.reserve(self.order)[0], "queued")
            self.assertEqual(store.list_reviews(), ())
            with self.assertRaises(QualityError):
                store.retry_m5_transient(self.order.idempotency_key)

    def test_review_requires_operator_identity_rationale_and_binary_decision(self):
        with QualityStore(":memory:") as store:
            store.reserve(self.order)
            self.assertTrue(store.claim_work(self.order.idempotency_key))
            result, result_bytes, manifest, artifacts = _result("NEEDS_REVIEW")
            store.finish(self.order, result, result_bytes, manifest, artifacts)

            with self.assertRaises(QualityError):
                store.resolve_review(
                    self.order.idempotency_key, "", "PASS", "rationale"
                )
            with self.assertRaises(QualityError):
                store.resolve_review(self.order.idempotency_key, "operator", "PASS", "")
            with self.assertRaises(QualityError):
                store.resolve_review(
                    self.order.idempotency_key, "operator", "MAYBE", "rationale"
                )
            with self.assertRaises(QualityError):
                store.resolve_review(
                    self.order.idempotency_key, "\ud800", "PASS", "rationale"
                )
            with self.assertRaises(QualityError):
                store.resolve_review(
                    self.order.idempotency_key, "operator", ["PASS"], "rationale"
                )

    def test_metrics_do_not_claim_unmeasured_defects_are_zero(self):
        with QualityStore(":memory:") as store:
            store.reserve(self.order)
            self.assertTrue(store.claim_work(self.order.idempotency_key))
            result, result_bytes, manifest, artifacts = _result(
                "NEEDS_REVIEW", check_status="unknown"
            )
            store.finish(self.order, result, result_bytes, manifest, artifacts)

            metrics = store.metrics()

        self.assertEqual(metrics["checks"]["unknown"], 1)
        self.assertEqual(metrics["defect_count"], None)
        self.assertFalse(metrics["defect_count_measured"])
        self.assertIn("defect_count", metrics["unmeasured"])

    def test_metrics_count_only_the_check_that_was_not_run(self):
        with QualityStore(":memory:") as store:
            store.reserve(self.order)
            self.assertTrue(store.claim_work(self.order.idempotency_key))
            result, _, manifest, artifacts = _result(
                "NEEDS_REVIEW", check_status="unknown"
            )
            result["checks"] = [
                {"status": "unknown", "issue_code": "CHECK_NOT_RUN"},
                {"status": "unknown", "issue_code": "CHECK_TIMEOUT"},
            ]
            result["issues"] = [
                {"code": "CHECK_NOT_RUN", "detail": "a later check was not run"}
            ]
            result_bytes = canonical_json(result)
            store.finish(self.order, result, result_bytes, manifest, artifacts)

            metrics = store.metrics()

        self.assertEqual(metrics["checks"]["not_run"], 1)
        self.assertEqual(metrics["checks"]["unknown"], 1)

    def test_stale_delivery_persists_stale_result_and_removes_it_from_outbox(self):
        with QualityStore(":memory:") as store:
            store.reserve(self.order)
            self.assertTrue(store.claim_work(self.order.idempotency_key))
            result, result_bytes, manifest, artifacts = _result("PASS")
            store.finish(self.order, result, result_bytes, manifest, artifacts)
            old_manifest_ref = result["evidence_manifest"]

            store.finish_delivery(
                self.order.idempotency_key, "stale", "attempt_not_verifying"
            )

            persisted = store.get_result(self.order.idempotency_key)
            self.assertEqual(persisted["status"], "STALE")
            self.assertNotEqual(persisted["evidence_manifest"], old_manifest_ref)
            stale_manifest = json.loads(
                store.get_result_manifest(persisted["evidence_manifest"])
            )
            self.assertEqual(stale_manifest["delivery"]["state"], "stale")
            self.assertIsNotNone(store.get_result_manifest(old_manifest_ref))
            self.assertEqual(store.pending_deliveries(), ())

    def test_database_directory_must_be_private(self):
        with tempfile.TemporaryDirectory() as temporary:
            public = Path(temporary) / "public"
            public.mkdir(mode=0o755)
            public.chmod(0o755)

            with self.assertRaises(QualityError) as raised:
                QualityStore(public / "quality.sqlite3")

        self.assertEqual(raised.exception.code, "STORE_PERMISSIONS")

    def test_unsupported_schema_closes_the_connection_without_reconfiguring_the_database(
        self,
    ):
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "quality.sqlite3"
            connection = sqlite3.connect(database)
            connection.execute("PRAGMA user_version=77")
            connection.close()

            for _ in range(2):
                with self.assertRaises(QualityError) as raised:
                    QualityStore(database)
                self.assertEqual(raised.exception.code, "STORE_SCHEMA_UNSUPPORTED")

            connection = sqlite3.connect(database)
            self.assertEqual(
                connection.execute("PRAGMA journal_mode").fetchone()[0], "delete"
            )
            connection.close()

    def test_artifact_write_failure_rolls_back_result_and_can_be_retried(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "quality.sqlite3"
            store = QualityStore(database)
            store.reserve(self.order)
            self.assertTrue(store.claim_work(self.order.idempotency_key))
            result, result_bytes, manifest, artifacts = _result("PASS")
            connection = sqlite3.connect(database)
            connection.execute(
                "CREATE TRIGGER fail_artifact_insert BEFORE INSERT ON artifacts "
                "BEGIN SELECT RAISE(ABORT, 'simulated disk full'); END"
            )
            connection.commit()
            connection.close()

            with self.assertRaises(sqlite3.IntegrityError):
                store.finish(self.order, result, result_bytes, manifest, artifacts)

            self.assertIsNone(store.get_result(self.order.idempotency_key))
            self.assertEqual(store.pending_deliveries(), ())
            connection = sqlite3.connect(database)
            connection.execute("DROP TRIGGER fail_artifact_insert")
            connection.commit()
            connection.close()

            store.finish(self.order, result, result_bytes, manifest, artifacts)
            self.assertEqual(
                store.get_result(self.order.idempotency_key)["status"], "PASS"
            )
            store.close()


def _result(status: str, *, check_status: str = "pass"):
    stdout = b"captured evidence\n"
    stderr = b""
    stdout_digest = hashlib.sha256(stdout).hexdigest()
    stderr_digest = hashlib.sha256(stderr).hexdigest()
    manifest = b'{"schema_version":"m6.evidence-manifest/1"}'
    manifest_digest = hashlib.sha256(manifest).hexdigest()
    result = {
        "status": status,
        "finished_at": "2026-10-15T00:00:00Z",
        "evidence_manifest": f"m6://result/{manifest_digest}",
        "stdout_ref": f"m6://artifact/{stdout_digest}",
        "stderr_ref": f"m6://artifact/{stderr_digest}",
        "checks": [{"status": check_status}],
    }
    return (
        result,
        canonical_json(result),
        manifest,
        {stdout_digest: stdout, stderr_digest: stderr},
    )


if __name__ == "__main__":
    unittest.main()
