import os
import sqlite3
import tempfile
import unittest

from app.store import migrate, read_items


def _make_legacy(path, rows):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE items(id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
    conn.executemany("INSERT INTO items(id, value) VALUES (?, ?)", rows)
    conn.commit()
    conn.close()


def _version(path):
    conn = sqlite3.connect(path)
    try:
        return conn.execute("PRAGMA user_version").fetchone()[0]
    finally:
        conn.close()


def _tables(path):
    conn = sqlite3.connect(path)
    try:
        return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    finally:
        conn.close()


def _columns(path, table):
    conn = sqlite3.connect(path)
    try:
        return [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
    finally:
        conn.close()


class _Recorder:
    def __init__(self, fail_at=None):
        self.calls = []
        self.fail_at = fail_at

    def __call__(self, point):
        self.calls.append(point)
        if point == self.fail_at:
            raise RuntimeError(f"injected failure at {point}")


class StoreTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name
        self.path = os.path.join(self.dir, "db")

    def tearDown(self):
        self._tmp.cleanup()

    def test_empty_db_gets_new_schema(self):
        migrate(self.path)
        self.assertEqual(_version(self.path), 1)
        self.assertEqual(_columns(self.path, "items"), ["id", "value", "normalized"])
        self.assertEqual(read_items(self.path), [])

    def test_legacy_conversion_preserves_ids_and_values(self):
        _make_legacy(self.path, [(7, "  Hello World "), (2, "ÀBC\t"), (10, "x")])
        migrate(self.path)
        self.assertEqual(_version(self.path), 1)
        self.assertEqual(read_items(self.path), [(2, "àbc"), (7, "hello world"), (10, "x")])
        conn = sqlite3.connect(self.path)
        try:
            rows = conn.execute("SELECT id, value FROM items ORDER BY id").fetchall()
        finally:
            conn.close()
        self.assertEqual(rows, [(2, "ÀBC\t"), (7, "  Hello World "), (10, "x")])
        self.assertEqual(_tables(self.path), {"items"})

    def test_reopen_migrated_is_noop_without_hook_calls(self):
        _make_legacy(self.path, [(1, "A")])
        migrate(self.path)
        rec = _Recorder()
        migrate(self.path, fault=rec)
        self.assertEqual(rec.calls, [])
        self.assertEqual(read_items(self.path), [(1, "a")])

    def test_newer_version_rejected_without_mutation(self):
        conn = sqlite3.connect(self.path)
        conn.execute("CREATE TABLE other(x INTEGER)")
        conn.execute("PRAGMA user_version = 2")
        conn.commit()
        conn.close()
        rec = _Recorder()
        with self.assertRaises(ValueError):
            migrate(self.path, fault=rec)
        self.assertEqual(rec.calls, [])
        self.assertEqual(_version(self.path), 2)
        self.assertEqual(_tables(self.path), {"other"})

    def test_failure_after_copy_rolls_back_and_retry_succeeds(self):
        _make_legacy(self.path, [(1, " A "), (3, "b")])
        rec = _Recorder(fail_at="after_copy")
        with self.assertRaises(RuntimeError):
            migrate(self.path, fault=rec)
        self.assertEqual(rec.calls, ["after_copy"])
        self.assertEqual(_version(self.path), 0)
        self.assertEqual(_tables(self.path), {"items"})
        self.assertEqual(_columns(self.path, "items"), ["id", "value"])

        migrate(self.path)
        self.assertEqual(read_items(self.path), [(1, "a"), (3, "b")])
        self.assertEqual(_tables(self.path), {"items"})

    def test_failure_before_commit_rolls_back_and_retry_succeeds(self):
        _make_legacy(self.path, [(4, "Z")])
        rec = _Recorder(fail_at="before_commit")
        with self.assertRaises(RuntimeError):
            migrate(self.path, fault=rec)
        self.assertEqual(rec.calls, ["after_copy", "before_commit"])
        self.assertEqual(_version(self.path), 0)
        self.assertEqual(_tables(self.path), {"items"})

        migrate(self.path)
        self.assertEqual(_version(self.path), 1)
        self.assertEqual(read_items(self.path), [(4, "z")])
        self.assertEqual(_tables(self.path), {"items"})

    def test_read_items_rejects_unmigrated_db_and_closes(self):
        _make_legacy(self.path, [(1, "A")])
        with self.assertRaises(ValueError):
            read_items(self.path)
        self.assertEqual(_version(self.path), 0)

    def test_read_items_missing_file_does_not_create_it(self):
        with self.assertRaises(sqlite3.OperationalError):
            read_items(self.path)
        self.assertFalse(os.path.exists(self.path))


if __name__ == "__main__":
    unittest.main()
