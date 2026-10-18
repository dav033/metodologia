import os
import sqlite3
import tempfile
import unittest
from unittest import mock

from app import store
from app.store import migrate, read_items


class FaultRecorder:
    """Records hook calls and raises at the checkpoint named by ``fail_at``."""

    def __init__(self, fail_at=None):
        self.calls = []
        self.fail_at = fail_at

    def __call__(self, checkpoint):
        self.calls.append(checkpoint)
        if checkpoint == self.fail_at:
            raise RuntimeError(f"injected failure at {checkpoint}")


class TrackingConnection:
    """Proxies a sqlite3 connection and records whether close() was called."""

    def __init__(self, conn):
        self._conn = conn
        self.closed = False

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def close(self):
        self.closed = True
        self._conn.close()


class StoreTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self._tmp.name, "db")

    def tearDown(self):
        self._tmp.cleanup()

    def make_legacy(self, rows):
        conn = sqlite3.connect(self.path)
        conn.execute("CREATE TABLE items(id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
        conn.executemany("INSERT INTO items(id, value) VALUES (?, ?)", rows)
        conn.commit()
        conn.close()

    def state(self):
        """Return version, table names, column names and rows of the database."""
        conn = sqlite3.connect(self.path)
        try:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            tables = [
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
                )
            ]
            columns = {
                table: [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]
                for table in tables
            }
            rows = {
                table: conn.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
                for table in tables
            }
            return version, tables, columns, rows
        finally:
            conn.close()


class MigrateTests(StoreTestCase):
    def test_empty_database_gets_current_schema_without_hooks(self):
        fault = FaultRecorder()
        migrate(self.path, fault)
        version, tables, columns, rows = self.state()
        self.assertEqual(version, 1)
        self.assertEqual(tables, ["items"])
        self.assertEqual(columns["items"], ["id", "value", "normalized"])
        self.assertEqual(rows["items"], [])
        self.assertEqual(fault.calls, [])

    def test_legacy_rows_keep_id_and_value_and_gain_normalized(self):
        self.make_legacy([(10, "  Hello World  "), (3, "ÀbC\t"), (7, "plain"), (5, "\n Mixed \r\n")])
        migrate(self.path)
        self.assertEqual(
            read_items(self.path),
            [(3, "àbc"), (5, "mixed"), (7, "plain"), (10, "hello world")],
        )
        _, _, _, rows = self.state()
        self.assertEqual(
            rows["items"],
            [(3, "ÀbC\t", "àbc"), (5, "\n Mixed \r\n", "mixed"), (7, "plain", "plain"),
             (10, "  Hello World  ", "hello world")],
        )

    def test_legacy_conversion_calls_hooks_in_order_and_leaves_no_temp_table(self):
        self.make_legacy([(1, "A")])
        fault = FaultRecorder()
        migrate(self.path, fault)
        self.assertEqual(fault.calls, ["after_copy", "before_commit"])
        version, tables, _, _ = self.state()
        self.assertEqual((version, tables), (1, ["items"]))

    def test_reopening_migrated_database_is_noop_without_hook_calls(self):
        self.make_legacy([(1, " X ")])
        migrate(self.path)
        before = self.state()
        fault = FaultRecorder()
        migrate(self.path, fault)
        self.assertEqual(fault.calls, [])
        self.assertEqual(self.state(), before)
        self.assertEqual(read_items(self.path), [(1, "x")])

    def test_newer_version_is_rejected_without_mutation(self):
        conn = sqlite3.connect(self.path)
        conn.execute("CREATE TABLE items(id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("INSERT INTO items(id, value) VALUES (1, 'keep')")
        conn.execute("PRAGMA user_version = 2")
        conn.commit()
        conn.close()
        before = self.state()
        fault = FaultRecorder()
        with self.assertRaises(ValueError):
            migrate(self.path, fault)
        self.assertEqual(self.state(), before)
        self.assertEqual(fault.calls, [])

    def test_fault_after_copy_rolls_back_and_retry_succeeds(self):
        self.make_legacy([(2, " B "), (1, "A")])
        before = self.state()
        with self.assertRaises(RuntimeError):
            migrate(self.path, FaultRecorder(fail_at="after_copy"))
        self.assertEqual(self.state(), before)

        migrate(self.path)
        version, tables, _, _ = self.state()
        self.assertEqual((version, tables), (1, ["items"]))
        self.assertEqual(read_items(self.path), [(1, "a"), (2, "b")])

    def test_fault_before_commit_rolls_back_and_retry_succeeds(self):
        self.make_legacy([(4, "Z")])
        before = self.state()
        fault = FaultRecorder(fail_at="before_commit")
        with self.assertRaises(RuntimeError):
            migrate(self.path, fault)
        self.assertEqual(fault.calls, ["after_copy", "before_commit"])
        self.assertEqual(self.state(), before)

        migrate(self.path)
        self.assertEqual(read_items(self.path), [(4, "z")])
        version, tables, _, _ = self.state()
        self.assertEqual((version, tables), (1, ["items"]))

    def test_non_text_legacy_value_is_rejected_without_mutation(self):
        self.make_legacy([(1, "ok")])
        conn = sqlite3.connect(self.path)
        conn.execute("INSERT INTO items(id, value) VALUES (2, ?)", (b"\x00\x01",))
        conn.commit()
        conn.close()
        before = self.state()
        with self.assertRaises(ValueError):
            migrate(self.path)
        self.assertEqual(self.state(), before)

    def test_unexpected_legacy_columns_are_rejected_without_mutation(self):
        conn = sqlite3.connect(self.path)
        conn.execute("CREATE TABLE items(id INTEGER PRIMARY KEY, value TEXT NOT NULL, extra TEXT)")
        conn.commit()
        conn.close()
        before = self.state()
        with self.assertRaises(ValueError):
            migrate(self.path)
        self.assertEqual(self.state(), before)

    def test_connection_is_closed_on_success_and_failure(self):
        real_connect = sqlite3.connect
        tracked = []

        def connect(*args, **kwargs):
            conn = TrackingConnection(real_connect(*args, **kwargs))
            tracked.append(conn)
            return conn

        self.make_legacy([(1, "A")])
        with mock.patch.object(store.sqlite3, "connect", side_effect=connect):
            with self.assertRaises(RuntimeError):
                migrate(self.path, FaultRecorder(fail_at="after_copy"))
            migrate(self.path)
        self.assertEqual(len(tracked), 2)
        self.assertTrue(all(conn.closed for conn in tracked))


class ReadItemsTests(StoreTestCase):
    def test_missing_file_raises_and_is_not_created(self):
        with self.assertRaises(FileNotFoundError):
            read_items(self.path)
        self.assertFalse(os.path.exists(self.path))

    def test_legacy_database_is_rejected_and_unchanged(self):
        self.make_legacy([(1, "A")])
        before = self.state()
        with self.assertRaises(ValueError):
            read_items(self.path)
        self.assertEqual(self.state(), before)

    def test_read_items_closes_connection(self):
        migrate(self.path)
        real_connect = sqlite3.connect
        tracked = []

        def connect(*args, **kwargs):
            conn = TrackingConnection(real_connect(*args, **kwargs))
            tracked.append(conn)
            return conn

        with mock.patch.object(store.sqlite3, "connect", side_effect=connect):
            self.assertEqual(read_items(self.path), [])
        self.assertEqual(len(tracked), 1)
        self.assertTrue(tracked[0].closed)


if __name__ == "__main__":
    unittest.main()
