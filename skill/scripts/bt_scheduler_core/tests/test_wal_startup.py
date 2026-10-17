"""WAL mode changes can return BUSY immediately despite SQLite's configured busy timeout."""
from __future__ import annotations

import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from bt_scheduler_core import SchedulerError, SqliteRepository


class WALStartup(unittest.TestCase):
    def connection_factory(self, code, *, forever=False):
        real_connect = sqlite3.connect
        attempts = []

        class Connection:
            def __init__(self, *args, **kwargs):
                self.delegate = real_connect(*args, **kwargs)

            def execute(self, sql, *args):
                if sql == "PRAGMA journal_mode=WAL":
                    attempts.append(sql)
                    if forever or len(attempts) == 1:
                        error = sqlite3.OperationalError("controlled WAL lock")
                        error.sqlite_errorcode = code
                        raise error
                return self.delegate.execute(sql, *args)

            def __getattr__(self, name):
                return getattr(self.delegate, name)

        return Connection, attempts

    def test_transient_wal_busy_is_retried_without_repeating_migration(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.db"
            connection, attempts = self.connection_factory(sqlite3.SQLITE_BUSY)
            with patch("sqlite3.connect", connection):
                SqliteRepository(path, busy_timeout=1)
            self.assertEqual(len(attempts), 2)
            SqliteRepository(path)
            with sqlite3.connect(path) as check:
                self.assertEqual(check.execute("PRAGMA journal_mode").fetchone()[0], "wal")

    def test_permanent_error_and_exhausted_deadline_remain_visible(self):
        for code, timeout in ((sqlite3.SQLITE_BUSY, 0.025), (sqlite3.SQLITE_IOERR, 1)):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as temporary:
                connection, attempts = self.connection_factory(code, forever=True)
                started = time.monotonic()
                with patch("sqlite3.connect", connection), self.assertRaisesRegex(SchedulerError, "STATE_UNAVAILABLE"):
                    SqliteRepository(Path(temporary) / "state.db", busy_timeout=timeout)
                self.assertLess(time.monotonic() - started, 1)
                self.assertEqual(len(attempts), 1) if code == sqlite3.SQLITE_IOERR else self.assertGreater(len(attempts), 1)
