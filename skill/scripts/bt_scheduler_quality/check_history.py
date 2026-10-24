"""Persistence for reusable check outcomes and command duration history."""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Callable
from contextlib import AbstractContextManager

CHECK_HISTORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS check_pass_cache (
    key TEXT PRIMARY KEY,
    exit_code INTEGER,
    duration_ms INTEGER NOT NULL,
    stdout BLOB NOT NULL,
    stderr BLOB NOT NULL,
    created_at REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'pass' CHECK(status IN ('pass','fail','flaky'))
);
CREATE TABLE IF NOT EXISTS check_stats (
    command_key TEXT PRIMARY KEY,
    last_ms INTEGER NOT NULL,
    updated_at REAL NOT NULL
);
"""


class CheckHistory:
    """Own cache/history SQL while sharing the store's connection and transaction boundary."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        lock: threading.RLock,
        transaction: Callable[[], AbstractContextManager[sqlite3.Connection]],
    ):
        self.connection = connection
        self.lock = lock
        self.transaction = transaction

    def migrate(self) -> None:
        columns = {
            row[1] for row in self.connection.execute("PRAGMA table_info(check_pass_cache)")
        }
        if "status" not in columns:
            self.connection.execute(
                "ALTER TABLE check_pass_cache ADD COLUMN status TEXT NOT NULL DEFAULT 'pass'"
            )

    def cached_pass(self, key: str, max_age: float, now: float) -> sqlite3.Row | None:
        if max_age <= 0:
            return None
        with self.lock:
            row = self.connection.execute(
                "SELECT exit_code, duration_ms, stdout, stderr, created_at FROM check_pass_cache "
                "WHERE key = ? AND status='pass'",
                (key,),
            ).fetchone()
        return row if row is not None and now - row["created_at"] <= max_age else None

    def remember_pass(
        self, key: str, exit_code: int | None, duration_ms: int,
        stdout: bytes, stderr: bytes, now: float,
    ) -> None:
        with self.lock, self.transaction() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO check_pass_cache "
                "(key,exit_code,duration_ms,stdout,stderr,created_at,status) "
                "VALUES (?, ?, ?, ?, ?, ?, 'pass')",
                (key, exit_code, duration_ms, stdout, stderr, now),
            )
            connection.execute(
                "DELETE FROM check_pass_cache WHERE created_at < ?", (now - 7 * 86_400,)
            )

    def record_outcome(self, key: str, status: str, now: float) -> bool:
        if status not in {"pass", "fail"}:
            return False
        with self.lock, self.transaction() as connection:
            row = connection.execute(
                "SELECT status FROM check_pass_cache WHERE key=?", (key,)
            ).fetchone()
            flaky = status == "pass" and row is not None and row["status"] in {"fail", "flaky"}
            recorded = "flaky" if flaky else status
            if status == "fail" or flaky or row is None:
                connection.execute(
                    "INSERT OR REPLACE INTO check_pass_cache "
                    "(key,exit_code,duration_ms,stdout,stderr,created_at,status) "
                    "VALUES (?,NULL,0,X'',X'',?,?)",
                    (key, now, recorded),
                )
        return flaky

    def last_ms(self, command_key: str) -> int | None:
        with self.lock:
            row = self.connection.execute(
                "SELECT last_ms FROM check_stats WHERE command_key = ?", (command_key,)
            ).fetchone()
        return int(row["last_ms"]) if row else None

    def record_ms(self, command_key: str, duration_ms: int, now: float) -> None:
        with self.lock, self.transaction() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO check_stats VALUES (?, ?, ?)",
                (command_key, int(duration_ms), now),
            )
