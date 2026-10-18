import os
import sqlite3
import tempfile
import unittest
from unittest import mock

from app import store
from app.store import migrate, read_items


def make_legacy(path, rows):
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE items(id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
        conn.executemany("INSERT INTO items(id, value) VALUES (?, ?)", rows)
        conn.commit()
    finally:
        conn.close()


def query(path, sql, params=()):
    conn = sqlite3.connect(path)
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def user_version(path):
    return query(path, "PRAGMA user_version")[0][0]


def table_names(path):
    return [r[0] for r in query(path, "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")]


def columns(path):
    return [(r[1], r[2], r[3]) for r in query(path, "PRAGMA table_info(items)")]


class Recorder:
    def __init__(self, fail_at=None):
        self.calls = []
        self.fail_at = fail_at

    def __call__(self, point):
        self.calls.append(point)
        if point == self.fail_at:
            raise RuntimeError(f"injected failure at {point}")


class MigrateTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self._tmp.name, "db")

    def tearDown(self):
        self._tmp.cleanup()

    def test_empty_db_gets_schema_and_version(self):
        migrate(self.path)
        self.assertEqual(user_version(self.path), 1)
        self.assertEqual(
            columns(self.path),
            [("id", "INTEGER", 0), ("value", "TEXT", 1), ("normalized", "TEXT", 1)],
        )
        self.assertEqual(read_items(self.path), [])

    def test_legacy_rows_keep_id_and_value_and_get_normalized(self):
        make_legacy(self.path, [(5, " Foo "), (2, "BAR"), (9, "\tbaz\n")])
        migrate(self.path)
        self.assertEqual(read_items(self.path), [(2, "bar"), (5, "foo"), (9, "baz")])
        self.assertEqual(
            query(self.path, "SELECT id, value FROM items ORDER BY id"),
            [(2, "BAR"), (5, " Foo "), (9, "\tbaz\n")],
        )
        self.assertEqual(table_names(self.path), ["items"])

    def test_reopen_migrated_is_noop_without_fault_calls(self):
        make_legacy(self.path, [(1, "A")])
        migrate(self.path)
        recorder = Recorder()
        migrate(self.path, fault=recorder)
        self.assertEqual(recorder.calls, [])
        self.assertEqual(read_items(self.path), [(1, "a")])

    def test_legacy_conversion_calls_fault_hooks_in_order(self):
        make_legacy(self.path, [(1, "A")])
        recorder = Recorder()
        migrate(self.path, fault=recorder)
        self.assertEqual(recorder.calls, ["after_copy", "before_commit"])

    def test_future_version_rejected_without_mutation(self):
        make_legacy(self.path, [(1, "A")])
        conn = sqlite3.connect(self.path)
        conn.execute("PRAGMA user_version = 2")
        conn.commit()
        conn.close()
        recorder = Recorder()
        with self.assertRaises(ValueError):
            migrate(self.path, fault=recorder)
        self.assertEqual(recorder.calls, [])
        self.assertEqual(user_version(self.path), 2)
        self.assertEqual(table_names(self.path), ["items"])
        self.assertEqual(columns(self.path), [("id", "INTEGER", 0), ("value", "TEXT", 1)])

    def test_failure_after_copy_rolls_back_and_retry_succeeds(self):
        make_legacy(self.path, [(3, " X "), (4, "y")])
        with self.assertRaises(RuntimeError):
            migrate(self.path, fault=Recorder(fail_at="after_copy"))
        self.assertEqual(user_version(self.path), 0)
        self.assertEqual(table_names(self.path), ["items"])
        self.assertEqual(columns(self.path), [("id", "INTEGER", 0), ("value", "TEXT", 1)])

        migrate(self.path)
        self.assertEqual(read_items(self.path), [(3, "x"), (4, "y")])
        self.assertEqual(table_names(self.path), ["items"])

    def test_failure_before_commit_rolls_back_and_retry_succeeds(self):
        make_legacy(self.path, [(7, "Q")])
        recorder = Recorder(fail_at="before_commit")
        with self.assertRaises(RuntimeError):
            migrate(self.path, fault=recorder)
        self.assertEqual(recorder.calls, ["after_copy", "before_commit"])
        self.assertEqual(user_version(self.path), 0)
        self.assertEqual(table_names(self.path), ["items"])

        migrate(self.path)
        self.assertEqual(read_items(self.path), [(7, "q")])
        self.assertEqual(table_names(self.path), ["items"])

    def test_normalization_error_rolls_back(self):
        conn = sqlite3.connect(self.path)
        conn.execute("CREATE TABLE items(id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("INSERT INTO items(id, value) VALUES (1, 'ok')")
        conn.execute("INSERT INTO items(id, value) VALUES (2, ?)", (b"\xff",))
        conn.commit()
        conn.close()
        with self.assertRaises(ValueError):
            migrate(self.path)
        self.assertEqual(user_version(self.path), 0)
        self.assertEqual(table_names(self.path), ["items"])

    def test_connection_is_closed_after_success_and_failure(self):
        opened = []
        real_connect = sqlite3.connect

        def tracking_connect(*args, **kwargs):
            conn = real_connect(*args, **kwargs)
            opened.append(conn)
            return conn

        legacy_path = self.path + ".legacy"
        make_legacy(self.path, [(1, "A")])
        make_legacy(legacy_path, [(2, "B")])
        with mock.patch.object(store.sqlite3, "connect", side_effect=tracking_connect):
            migrate(self.path)
            with self.assertRaises(RuntimeError):
                migrate(legacy_path, fault=Recorder(fail_at="before_commit"))
        self.assertTrue(opened)
        for conn in opened:
            with self.assertRaises(sqlite3.ProgrammingError):
                conn.execute("SELECT 1")


class ReadItemsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self._tmp.name, "db")

    def tearDown(self):
        self._tmp.cleanup()

    def test_unmigrated_db_is_rejected(self):
        make_legacy(self.path, [(1, "A")])
        with self.assertRaises(ValueError):
            read_items(self.path)

    def test_missing_file_is_not_created(self):
        with self.assertRaises(sqlite3.OperationalError):
            read_items(self.path)
        self.assertFalse(os.path.exists(self.path))

    def test_connection_is_closed(self):
        migrate(self.path)
        opened = []
        real_connect = sqlite3.connect

        def tracking_connect(*args, **kwargs):
            conn = real_connect(*args, **kwargs)
            opened.append(conn)
            return conn

        with mock.patch.object(store.sqlite3, "connect", side_effect=tracking_connect):
            read_items(self.path)
        self.assertEqual(len(opened), 1)
        with self.assertRaises(sqlite3.ProgrammingError):
            opened[0].execute("SELECT 1")


if __name__ == "__main__":
    unittest.main()
