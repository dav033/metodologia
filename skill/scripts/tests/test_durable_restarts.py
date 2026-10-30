"""bt_durable.restarts (D-210): how the previous engine stopped, and the recovery credit of a deliberate stop."""
from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from bt_durable import restarts


class PreviousStop(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        restarts._reset_for_tests()
        self.addCleanup(restarts._reset_for_tests)

    def next_engine(self) -> str:
        restarts._reset_for_tests()                        # a new process
        return restarts.previous_stop(self.dir)

    def test_first_clean_and_unexplained(self):
        self.assertEqual(restarts.previous_stop(self.dir), restarts.FIRST)
        restarts.begin(self.dir)
        restarts.record_clean_stop(self.dir)
        self.assertEqual(self.next_engine(), restarts.CLEAN)
        restarts.begin(self.dir)                           # this engine is killed: no stop record for its session
        self.assertEqual(self.next_engine(), restarts.UNEXPLAINED)
        restarts.begin(self.dir)
        restarts.record_clean_stop(self.dir)
        restarts._reset_for_tests()
        self.assertEqual(restarts.previous_stop(self.dir), restarts.CLEAN)
        restarts.begin(self.dir)                           # a stop record of an EARLIER session proves nothing
        (self.dir / restarts.STOPPED).write_text('{"session": "earlier"}')
        self.assertEqual(self.next_engine(), restarts.UNEXPLAINED)

    def test_the_answer_is_read_once_per_process(self):
        restarts.begin(self.dir)
        restarts.record_clean_stop(self.dir)
        restarts._reset_for_tests()
        self.assertEqual(restarts.previous_stop(self.dir), restarts.CLEAN)
        restarts.begin(self.dir)                           # replaces the session the answer was read from
        self.assertEqual(restarts.previous_stop(self.dir), restarts.CLEAN)


class RecoveryCredit(unittest.TestCase):
    def test_pending_workflows_of_the_executor_get_one_dispatch_back(self):
        db = Path(tempfile.mkdtemp()) / "dbos.sqlite3"
        with sqlite3.connect(db) as conn:
            conn.execute("CREATE TABLE workflow_status (workflow_uuid TEXT, status TEXT, executor_id TEXT, "
                         "recovery_attempts INTEGER)")
            conn.executemany("INSERT INTO workflow_status VALUES (?,?,?,?)", [
                ("a", "PENDING", "local", 3), ("b", "PENDING", "local", 0), ("c", "SUCCESS", "local", 5),
                ("d", "PENDING", "other", 4), ("e", "ENQUEUED", "local", 2)])
        self.assertEqual(restarts.credit_recoveries(f"sqlite:///{db}", "local"), 1)
        with sqlite3.connect(db) as conn:
            rows = dict(conn.execute("SELECT workflow_uuid, recovery_attempts FROM workflow_status"))
        self.assertEqual(rows, {"a": 2, "b": 0, "c": 5, "d": 4, "e": 2})

    def test_a_database_without_dbos_tables_credits_nothing(self):
        db = Path(tempfile.mkdtemp()) / "empty.sqlite3"
        self.assertEqual(restarts.credit_recoveries(f"sqlite:///{db}", "local"), 0)


if __name__ == "__main__":
    unittest.main()
