import concurrent.futures
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from dataclasses import replace
from pathlib import Path

from bt_scheduler_recovery import DecisionStore, Policy, RecoveryError
from bt_scheduler_recovery.history import inspect_store
from helpers import case


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "private" / "decisions.db"
        self.addCleanup(self.temp.cleanup)

    def test_restart_and_wall_clock_idempotency(self):
        source = case(now=100)
        with DecisionStore(self.path) as store:
            first = store.decide(source)
        with DecisionStore(self.path) as store:
            self.assertEqual(first, store.decide(replace(source, now=101)))
            self.assertEqual(store.metrics()["decisions"], 1)
            self.assertEqual(store.latest(), first.to_dict())
            self.assertEqual(store.latest("unrelated"), None)
            self.assertEqual(store.decide(replace(source, now=101, recovery_round=1)).action, "retry")

    def test_immutable_conflict_never_overwrites(self):
        with DecisionStore(self.path) as store:
            first = store.decide(case())
            for changes in ({"manual_cancel": True}, {"handoff_sha": None}, {"max_attempts": 7},
                            {"execution_state": "live"}, {"failure_at": 99}):
                with self.subTest(changes=changes), self.assertRaisesRegex(RecoveryError, "CASE_CONFLICT"):
                    store.decide(case(**changes))
            self.assertEqual(store.latest(), first.to_dict())
            self.assertEqual(store.metrics()["decisions"], 1)

    def test_storage_bound_preserves_deduplication(self):
        with DecisionStore(self.path, max_decisions=2) as store:
            first = store.decide(case())
            store.decide(case(attempt_id="A-002", token=2))
            with self.assertRaisesRegex(RecoveryError, "STORE_FULL"):
                store.decide(case(attempt_id="A-003", token=3))
            self.assertEqual(store.decide(case()), first)
            self.assertEqual(store.metrics()["decisions"], 2)

    def test_policy_bound_uses_stricter_cap(self):
        with DecisionStore(self.path) as store:
            policy = Policy(max_decisions=1)
            store.decide(case(), policy)
            with self.assertRaisesRegex(RecoveryError, "STORE_FULL"):
                store.decide(case(attempt_id="A-002"), policy)

    def test_distinct_attempt_history_not_wait_rounds(self):
        with DecisionStore(self.path) as store:
            for index in range(3):
                store.decide(case(recovery_round=index))
            result = store.decide(case(attempt_id="A-002", token=2))
            self.assertEqual(result.action, "wait")  # second attempt gets 2s backoff, not a repeated-round block
            third = store.decide(case(attempt_id="A-003", token=3))
            self.assertEqual(third.reason_code, "same_cause_limit")
            independent = store.decide(case(task_id="T-002", attempt_id="A-004", token=4))
            self.assertEqual(independent.action, "retry")

    def test_repeated_missing_environment_does_not_consume_code_retry_history(self):
        with DecisionStore(self.path) as store:
            for index, reason in enumerate(("BLOCKED_EXTERNAL", "BLOCKED_ENV", "BLOCKED_EXTERNAL"), start=1):
                result = store.decide(case(attempt_id=f"A-{index:03d}", token=index, reason_code=reason),
                                      Policy(max_same_cause=1))
                self.assertEqual(result.action, "block")
                self.assertEqual(result.retry_budget_remaining, 2)
            code_failure = store.decide(case(attempt_id="A-004", token=4, reason_code="FAIL_CODE"),
                                        Policy(max_same_cause=1))
            self.assertNotEqual(code_failure.reason_code, "same_cause_limit")

    def test_m6_timeout_allows_only_one_distinct_attempt_retry(self):
        with DecisionStore(self.path) as store:
            verification = {"core_cause": "verification_rejected", "technical_cause": "verification_rejected",
                            "execution_state": "finished", "verification_ref": "verdict:" + "d" * 64}
            first = store.decide(case(reason_code="TIMEOUT", **verification))
            second = store.decide(case(attempt_id="A-002", token=2, reason_code="TIMEOUT", **verification))
            self.assertEqual(first.action, "retry")
            self.assertEqual((second.action, second.reason_code), ("block", "timeout_repeated"))

    def test_verification_timeout_history_is_independent_of_technical_cause(self):
        with DecisionStore(self.path) as store:
            verification = {"core_cause": "verification_rejected", "execution_state": "finished",
                            "verification_ref": "verdict:" + "d" * 64}
            first = store.decide(case(reason_code="TIMEOUT", technical_cause="verification_rejected",
                                      **verification))
            second = store.decide(case(attempt_id="A-002", token=2, reason_code="TIMEOUT",
                                       technical_cause="agent_error", **verification))
            self.assertEqual(first.action, "retry")
            self.assertEqual((second.action, second.reason_code), ("block", "timeout_repeated"))

    def test_legacy_serialized_case_and_decision_database_remains_idempotent(self):
        with DecisionStore(self.path) as store:
            previous = store.decide(case())
        with closing(sqlite3.connect(self.path)) as connection:
            row = connection.execute("SELECT decision_id,case_json FROM decisions").fetchone()
            legacy_case = json.loads(row[1])
            legacy_case["schema_version"] = "m5.recovery-case/1"
            legacy_case.pop("reason_code")
            connection.execute("UPDATE decisions SET case_json=?", (json.dumps(legacy_case, sort_keys=True,
                                                                                separators=(",", ":")),))
            connection.commit()
        with DecisionStore(self.path) as store:
            self.assertEqual(store.decide(case()), previous)

    def test_twenty_duplicate_writers_record_one_decision(self):
        def worker(_):
            with DecisionStore(self.path, timeout_seconds=10) as store:
                return store.decide(case()).decision_id
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
            results = list(pool.map(worker, range(20)))
        self.assertEqual(len(set(results)), 1)
        with DecisionStore(self.path) as store:
            self.assertEqual(store.metrics()["decisions"], 1)

    def test_concurrent_distinct_attempts_observe_atomic_cause_limit(self):
        def worker(index):
            with DecisionStore(self.path, timeout_seconds=10) as store:
                return store.decide(case(attempt_id=f"A-{index:03d}", token=index + 1)).action
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            results = list(pool.map(worker, range(10)))
        self.assertEqual(results.count("block"), 8)

    def test_busy_lock_deadline_and_closed_store(self):
        store = DecisionStore(self.path, timeout_seconds=0.01)
        lock = sqlite3.connect(self.path)
        lock.execute("BEGIN IMMEDIATE")
        try:
            with self.assertRaisesRegex(RecoveryError, "STORE_BUSY"):
                store.decide(case())
        finally:
            lock.rollback()
            lock.close()
        store.close()
        with self.assertRaisesRegex(RecoveryError, "STORE_CLOSED"):
            store.metrics()

    def test_permissions_and_secret_free_storage(self):
        with DecisionStore(self.path) as store:
            store.decide(case())
        if os.name == "posix":
            self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(self.path.parent.stat().st_mode & 0o777, 0o700)
        with closing(sqlite3.connect(self.path)) as connection:
            facts, payload = connection.execute("SELECT facts,case_json FROM decisions").fetchone()
            self.assertNotIn("detail", payload)
            self.assertNotIn("/", json.loads(payload)["evidence_refs"][0])
            self.assertLess(len(payload), 8000)
            self.assertNotIn('"now"', facts)

    def test_readonly_inspection_and_missing_store(self):
        missing = Path(self.temp.name) / "absent" / "db"
        with self.assertRaisesRegex(RecoveryError, "STORE_MISSING"):
            inspect_store(missing)
        self.assertFalse(missing.parent.exists())
        with DecisionStore(self.path) as store:
            result = store.decide(case())
        before = self.path.read_bytes()
        self.assertEqual(inspect_store(self.path), result.to_dict())
        self.assertEqual(inspect_store(self.path, metrics=True)["decisions"], 1)
        self.assertEqual(self.path.read_bytes(), before)

    def test_foreign_database_and_symlink_are_rejected(self):
        self.path.parent.mkdir()
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute("CREATE TABLE unrelated(x)")
        self.path.chmod(0o600)
        before = self.path.read_bytes()
        with self.assertRaisesRegex(RecoveryError, "STORE_SCHEMA"):
            DecisionStore(self.path)
        self.assertEqual(self.path.read_bytes(), before)
        link = self.path.parent / "link.db"
        link.symlink_to(self.path)
        with self.assertRaisesRegex(RecoveryError, "STORE_PATH"):
            DecisionStore(link)

    def run_child(self, body):
        scripts = Path(__file__).resolve().parents[2]
        script = "import sys, os, json, sqlite3; sys.path.insert(0, " + repr(str(scripts)) + "); " + body
        return subprocess.run([sys.executable, "-I", "-c", script], cwd=self.temp.name, capture_output=True, text=True,
                              check=False, timeout=10)

    def test_crash_after_commit_before_return_remains_idempotent(self):
        body = ("from bt_scheduler_recovery import DecisionStore, RecoveryCase; "
                f"store=DecisionStore({str(self.path)!r}); "
                f"source=RecoveryCase.from_dict(json.loads({json.dumps(case().to_dict())!r})); "
                "store.decide(source); os._exit(27)")
        result = self.run_child(body)
        self.assertEqual(result.returncode, 27, result.stderr)
        with DecisionStore(self.path) as store:
            decision = store.decide(case())
            self.assertEqual(store.metrics()["decisions"], 1)
            self.assertEqual(store.latest()["decision_id"], decision.decision_id)

    def test_crash_inside_write_transaction_rolls_back(self):
        with DecisionStore(self.path) as store:
            store.decide(case())
        body = (f"connection=sqlite3.connect({str(self.path)!r}); connection.execute('BEGIN IMMEDIATE'); "
                "connection.execute('DELETE FROM decisions'); os._exit(28)")
        result = self.run_child(body)
        self.assertEqual(result.returncode, 28, result.stderr)
        with DecisionStore(self.path) as store:
            self.assertEqual(store.metrics()["decisions"], 1)
            self.assertEqual(store.decide(case()).action, "retry")


if __name__ == "__main__":
    unittest.main()
