"""Deterministic event rules and a durable Telegram outbox."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.request import Request, urlopen


_EVENT_MESSAGES = {
    "attempt.failed": "Una tarea falló sin reintentos pendientes.",
    "attempt.blocked": "Una tarea quedó bloqueada.",
    "run.finished": "La ejecución terminó.",
    "round.waiting": "Hay una ronda de preguntas esperando respuesta.",
    "plan.waiting": "Hay un plan esperando aprobación.",
    "decision.requested": "Hay una decisión esperando respuesta.",
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
            last_error TEXT
        )""")
        self._db.execute("CREATE TABLE IF NOT EXISTS gateway_state (key TEXT PRIMARY KEY, value INTEGER NOT NULL)")
        self._db.commit()

    def enqueue(self, dedupe_key: str, message: str) -> bool:
        with self._lock:
            cursor = self._db.execute(
                "INSERT OR IGNORE INTO telegram_outbox(dedupe_key, message) VALUES (?, ?)",
                (dedupe_key, message),
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
                "SELECT dedupe_key, message, attempts FROM telegram_outbox "
                "WHERE status = 'pending' AND next_attempt <= ? ORDER BY rowid LIMIT 20", (current,)
            ).fetchall()
        delivered = 0
        for key, message, attempts in rows:
            try:
                send(message)
            except Exception as exc:  # Delivery errors are persisted for retry; do not expose response data.
                next_attempt = current + min(3600, 5 * (2 ** min(attempts, 10)))
                status = "dropped" if attempts >= 10 else "pending"
                with self._lock:
                    self._db.execute(
                        "UPDATE telegram_outbox SET attempts = attempts + 1, next_attempt = ?, status = ?, "
                        "last_error = ? WHERE dedupe_key = ? AND status = 'pending'",
                        (next_attempt, status, type(exc).__name__, key),
                    )
                    self._db.commit()
            else:
                with self._lock:
                    self._db.execute(
                        "UPDATE telegram_outbox SET status = 'sent', attempts = attempts + 1 "
                        "WHERE dedupe_key = ? AND status = 'pending'", (key,)
                    )
                    self._db.commit()
                delivered += 1
        return delivered


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
    return f"event:{dedupe_key}", _EVENT_MESSAGES[event_type] + details
