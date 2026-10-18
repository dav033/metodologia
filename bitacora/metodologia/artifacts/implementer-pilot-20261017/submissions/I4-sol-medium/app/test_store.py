import os
import sqlite3
import tempfile
import unittest
from contextlib import closing

from app.store import migrate, read_items


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = os.path.join(self.directory.name, "items.db")
        self.rows = [(-5, "  ÄBC\u2003"), (42, " İ "), (0, ""), (9, "MiXeD")]

    def legacy(self):
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute(
                "CREATE TABLE items(id INTEGER PRIMARY KEY, value TEXT NOT NULL)"
            )
            connection.executemany("INSERT INTO items VALUES (?, ?)", self.rows)

    def snapshot(self):
        connection = sqlite3.connect(self.path)
        try:
            return (
                connection.execute("PRAGMA user_version").fetchone()[0],
                connection.execute("SELECT name, sql FROM sqlite_master ORDER BY name").fetchall(),
                connection.execute("SELECT * FROM items ORDER BY id").fetchall(),
            )
        finally:
            connection.close()

    def test_conversion_and_reopening(self):
        self.legacy()
        events = []
        migrate(self.path, events.append)
        self.assertEqual(events, ["after_copy", "before_commit"])
        self.assertEqual(
            read_items(self.path),
            sorted((key, value.strip().lower()) for key, value in self.rows),
        )
        before = self.snapshot()
        self.assertEqual(before[0], 1)
        self.assertEqual([row[:2] for row in before[2]], sorted(self.rows))
        self.assertEqual([row[0] for row in before[1]], ["items"])
        migrate(self.path, lambda stage: self.fail(stage))
        self.assertEqual(self.snapshot(), before)

    def test_rollback_and_retry_at_each_hook(self):
        for stage in ("after_copy", "before_commit"):
            with self.subTest(stage=stage):
                if os.path.exists(self.path):
                    os.unlink(self.path)
                self.legacy()
                before = self.snapshot()
                error = RuntimeError(stage)

                def fail(current):
                    if current == stage:
                        raise error

                with self.assertRaises(RuntimeError) as caught:
                    migrate(self.path, fail)
                self.assertIs(caught.exception, error)
                self.assertEqual(self.snapshot(), before)
                migrate(self.path)
                self.assertEqual([row[0] for row in self.snapshot()[1]], ["items"])

    def test_future_version_unchanged(self):
        self.legacy()
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute("PRAGMA user_version = 2")
        before = self.snapshot()
        with self.assertRaises(ValueError):
            migrate(self.path, lambda stage: self.fail(stage))
        self.assertEqual(self.snapshot(), before)

    def test_empty_database_rollback_and_retry(self):
        events = []

        def fail(stage):
            events.append(stage)
            raise RuntimeError(stage)

        with self.assertRaises(RuntimeError):
            migrate(self.path, fail)
        self.assertEqual(events, ["before_commit"])
        with closing(sqlite3.connect(self.path)) as connection, connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT name FROM sqlite_master").fetchall(), [])
        migrate(self.path)
        self.assertEqual(read_items(self.path), [])

    def test_read_requires_migrated_database(self):
        with self.assertRaises(sqlite3.OperationalError):
            read_items(self.path)
        self.assertFalse(os.path.exists(self.path))
        self.legacy()
        before = self.snapshot()
        with self.assertRaises(ValueError):
            read_items(self.path)
        self.assertEqual(self.snapshot(), before)
