"""Deterministic event rules and a durable Telegram outbox."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from urllib.parse import quote
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.error import HTTPError
from urllib.request import Request, urlopen


_EVENT_MESSAGES = {
    "attempt.failed": "Una tarea falló sin reintentos pendientes.",
    "attempt.blocked": "Una tarea quedó bloqueada.",
    "run.finished": "La ejecución terminó.",
    "round.waiting": "Hay una ronda de preguntas esperando respuesta.",
    "plan.waiting": "Hay un plan esperando aprobación.",
    "quota.exhausted": "Se agotó la cuota de una cuenta.",
    "attempt.stalled": "Una tarea no muestra actividad desde hace más de 10 minutos.",
}


class NotificationOutbox:
    """SQLite-backed, deduplicated delivery queue that survives process restarts."""

    def __init__(self, database_path: str):
        self._lock = threading.Lock()
        if database_path != ":memory:":
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(database_path, check_same_thread=False)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("""CREATE TABLE IF NOT EXISTS telegram_outbox (
            dedupe_key TEXT PRIMARY KEY,
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            attempts INTEGER NOT NULL DEFAULT 0,
            next_attempt REAL NOT NULL DEFAULT 0,
            last_error TEXT,
            created_at REAL NOT NULL DEFAULT 0
        )""")
        columns = {row[1] for row in self._db.execute("PRAGMA table_info(telegram_outbox)")}
        if "created_at" not in columns:
            self._db.execute("ALTER TABLE telegram_outbox ADD COLUMN created_at REAL NOT NULL DEFAULT 0")
            # Existing queued rows predate age tracking; start their one-hour window at migration.
            self._db.execute("UPDATE telegram_outbox SET created_at = ? WHERE created_at = 0", (time.time(),))
        self._db.execute("""CREATE TABLE IF NOT EXISTS telegram_delivery_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dedupe_key TEXT NOT NULL,
            recorded_at REAL NOT NULL,
            outcome TEXT NOT NULL,
            error TEXT
        )""")
        self._db.execute("CREATE TABLE IF NOT EXISTS gateway_state (key TEXT PRIMARY KEY, value INTEGER NOT NULL)")
        self._db.commit()

    def enqueue(self, dedupe_key: str, message: str) -> bool:
        with self._lock:
            cursor = self._db.execute(
                "INSERT OR IGNORE INTO telegram_outbox(dedupe_key, message, created_at) VALUES (?, ?, ?)",
                (dedupe_key, message, time.time()),
            )
            self._db.commit()
            return cursor.rowcount == 1

    def next_sequence(self, key: str) -> int:
        with self._lock:
            self._db.execute(
                "INSERT INTO gateway_state(key, value) VALUES (?, 1) "
                "ON CONFLICT(key) DO UPDATE SET value = value + 1", (key,)
            )
            value = self._db.execute("SELECT value FROM gateway_state WHERE key = ?", (key,)).fetchone()[0]
            self._db.commit()
            return int(value)

    def state_value(self, key: str, default: int = 0) -> int:
        with self._lock:
            row = self._db.execute("SELECT value FROM gateway_state WHERE key = ?", (key,)).fetchone()
            return default if row is None else int(row[0])

    def set_state_value(self, key: str, value: int) -> None:
        with self._lock:
            self._db.execute(
                "INSERT INTO gateway_state(key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value)
            )
            self._db.commit()

    def deliver_due(self, send: Callable[[str], None], now: float | None = None) -> int:
        current = time.time() if now is None else now
        with self._lock:
            rows = self._db.execute(
                "SELECT dedupe_key, message, attempts, created_at FROM telegram_outbox "
                "WHERE status = 'pending' AND (next_attempt <= ? OR created_at < ?) "
                "ORDER BY rowid LIMIT 20", (current, current - 3600)
            ).fetchall()
        delivered = 0
        for key, message, attempts, created_at in rows:
            if current - created_at > 3600:
                with self._lock:
                    self._db.execute(
                        "UPDATE telegram_outbox SET status = 'dropped', last_error = 'MessageExpired' "
                        "WHERE dedupe_key = ? AND status = 'pending'", (key,),
                    )
                    self._record_history(key, current, "dropped", "MessageExpired")
                    self._db.commit()
                continue
            try:
                send(message)
            except Exception as exc:  # Delivery errors are persisted for retry; do not expose response data.
                next_attempt = current + min(3600, 5 * (2 ** min(attempts, 10)))
                retryable = not isinstance(exc, HTTPError) or 500 <= exc.code <= 599
                status = "pending" if retryable and attempts < 10 else "dropped"
                outcome = "retry" if status == "pending" else "dropped"
                safe_error = f"HTTP{exc.code}" if isinstance(exc, HTTPError) else type(exc).__name__
                if isinstance(exc, HTTPError):
                    exc.close()
                with self._lock:
                    self._db.execute(
                        "UPDATE telegram_outbox SET attempts = attempts + 1, next_attempt = ?, status = ?, "
                        "last_error = ? WHERE dedupe_key = ? AND status = 'pending'",
                        (next_attempt, status, safe_error, key),
                    )
                    self._record_history(key, current, outcome, safe_error)
                    self._db.commit()
            else:
                with self._lock:
                    self._db.execute(
                        "UPDATE telegram_outbox SET status = 'sent', attempts = attempts + 1, last_error = NULL "
                        "WHERE dedupe_key = ? AND status = 'pending'", (key,)
                    )
                    self._record_history(key, current, "sent", None)
                    self._db.commit()
                delivered += 1
        return delivered

    def _record_history(self, key: str, recorded_at: float, outcome: str, error: str | None) -> None:
        self._db.execute(
            "INSERT INTO telegram_delivery_history(dedupe_key, recorded_at, outcome, error) VALUES (?, ?, ?, ?)",
            (key, recorded_at, outcome, error),
        )

    def history(self, dedupe_key: str | None = None) -> list[dict[str, Any]]:
        """Return delivery attempts in recording order, optionally for one queued message."""
        with self._lock:
            if dedupe_key is None:
                rows = self._db.execute(
                    "SELECT dedupe_key, recorded_at, outcome, error FROM telegram_delivery_history ORDER BY id"
                ).fetchall()
            else:
                rows = self._db.execute(
                    "SELECT dedupe_key, recorded_at, outcome, error FROM telegram_delivery_history "
                    "WHERE dedupe_key = ? ORDER BY id", (dedupe_key,),
                ).fetchall()
        return [
            {"dedupe_key": key, "recorded_at": recorded_at, "outcome": outcome, "error": error}
            for key, recorded_at, outcome, error in rows
        ]


class TelegramSender:
    def __init__(self, token: str, chat_id: str, timeout: float = 5.0):
        self._url = f"https://api.telegram.org/bot{token}/sendMessage"
        self._chat_id = chat_id
        self._timeout = timeout

    def __call__(self, message: str) -> None:
        payload = json.dumps({"chat_id": self._chat_id, "text": message}).encode("utf-8")
        request = Request(self._url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=self._timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
        if not isinstance(result, dict) or result.get("ok") is not True:
            raise RuntimeError("Telegram rejected the message")


def notification_for_event(event: Mapping[str, Any]) -> tuple[str, str] | None:
    """Return the stable dedupe key and rendered message for a notifying feed event."""
    event_type = event.get("type")
    dedupe_key = event.get("dedupeKey")
    event_id = event.get("id")
    if (event_type not in _EVENT_MESSAGES or not isinstance(event_id, str) or not event_id
            or not isinstance(dedupe_key, str) or not dedupe_key):
        return None
    target = event.get("target")
    req = target.get("req") if isinstance(target, dict) else None
    details = f"\n{req}" if isinstance(req, str) and req else ""
    attempt = target.get("attemptId") if isinstance(target, dict) else None
    review = f"\n#attempt-{quote(attempt, safe='')}" if event_type == "attempt.failed" and isinstance(attempt, str) and attempt else ""
    return f"event:{dedupe_key}", _EVENT_MESSAGES[event_type] + details + review
