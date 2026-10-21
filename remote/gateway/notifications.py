"""Deterministic event rules and a durable Telegram outbox."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen


MAX_MESSAGE_AGE_SECONDS = 60 * 60
MAX_DELIVERY_ATTEMPTS = 10
INITIAL_RETRY_SECONDS = 5


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
            last_error TEXT,
            created_at REAL NOT NULL DEFAULT 0
        )""")
        columns = {row[1] for row in self._db.execute("PRAGMA table_info(telegram_outbox)")}
        if "created_at" not in columns:
            self._db.execute("ALTER TABLE telegram_outbox ADD COLUMN created_at REAL NOT NULL DEFAULT 0")
        self._db.execute("""CREATE TABLE IF NOT EXISTS telegram_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dedupe_key TEXT NOT NULL,
            outcome TEXT NOT NULL,
            attempt INTEGER NOT NULL,
            at REAL NOT NULL,
            error TEXT
        )""")
        self._db.execute("CREATE TABLE IF NOT EXISTS gateway_state (key TEXT PRIMARY KEY, value INTEGER NOT NULL)")
        self._db.commit()

    def enqueue(self, dedupe_key: str, message: str, created_at: float | None = None) -> bool:
        with self._lock:
            cursor = self._db.execute(
                "INSERT OR IGNORE INTO telegram_outbox(dedupe_key, message, created_at) VALUES (?, ?, ?)",
                (dedupe_key, message, time.time() if created_at is None else created_at),
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

    def history(self) -> list[dict[str, Any]]:
        """Return every delivery attempt and terminal drop, in occurrence order."""
        with self._lock:
            rows = self._db.execute(
                "SELECT dedupe_key, outcome, attempt, at, error FROM telegram_history ORDER BY id"
            ).fetchall()
        return [
            {"dedupeKey": key, "outcome": outcome, "attempt": attempt, "at": at, "error": error}
            for key, outcome, attempt, at, error in rows
        ]

    def _record(self, key: str, outcome: str, attempt: int, at: float, error: str | None,
                *, status: str, next_attempt: float | None = None) -> None:
        with self._lock:
            self._db.execute(
                "INSERT INTO telegram_history(dedupe_key, outcome, attempt, at, error) VALUES (?, ?, ?, ?, ?)",
                (key, outcome, attempt, at, error),
            )
            self._db.execute(
                "UPDATE telegram_outbox SET attempts = ?, status = ?, last_error = ?, "
                "next_attempt = COALESCE(?, next_attempt) WHERE dedupe_key = ? AND status = 'pending'",
                (attempt, status, error, next_attempt, key),
            )
            self._db.commit()

    def deliver_due(self, send: Callable[[str], None], now: float | None = None) -> int:
        current = time.time() if now is None else now
        with self._lock:
            rows = self._db.execute(
                "SELECT dedupe_key, message, attempts, created_at FROM telegram_outbox "
                "WHERE status = 'pending' AND next_attempt <= ? ORDER BY rowid LIMIT 20", (current,)
            ).fetchall()
        delivered = 0
        for key, message, attempts, created_at in rows:
            if current - created_at > MAX_MESSAGE_AGE_SECONDS:
                self._record(key, "dropped", attempts, current, "expired", status="dropped")
                continue
            try:
                send(message)
            except Exception as exc:  # Delivery errors are persisted for retry; do not expose response data.
                code = exc.code if isinstance(exc, HTTPError) else None
                if isinstance(exc, HTTPError):
                    exc.close()
                permanent = code is not None and 400 <= code < 500 and code != 429
                attempt = attempts + 1
                error = f"{type(exc).__name__}:{code}" if code is not None else type(exc).__name__
                if permanent or attempt >= MAX_DELIVERY_ATTEMPTS:
                    self._record(key, "dropped", attempt, current, error, status="dropped")
                else:
                    delay = min(3600, INITIAL_RETRY_SECONDS * (2 ** min(attempt - 1, 10)))
                    self._record(key, "retry", attempt, current, error, status="pending",
                                 next_attempt=current + delay)
            else:
                self._record(key, "sent", attempts + 1, current, None, status="sent")
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
    attempt_id = target.get("attemptId") if isinstance(target, dict) else None
    project = target.get("project") if isinstance(target, dict) else None
    if event_type == "attempt.failed" and all(isinstance(value, str) and value for value in
                                               (project, req, attempt_id)):
        dedupe_key = f"attempt.failed:{project}/{req}:{attempt_id}"
    message = _EVENT_MESSAGES[event_type] + details
    task_id = target.get("taskId") if isinstance(target, dict) else None
    if (event_type == "attempt.failed" and all(isinstance(value, str) and value for value in
            (project, req, task_id, attempt_id))):
        query = urlencode({"project": project, "req": req, "taskId": task_id})
        message += f"\n/review?{query}#attempt-{attempt_id}"
    return f"event:{dedupe_key}", message


def event_timestamp(event: Mapping[str, Any]) -> float | None:
    """Parse the event's ISO-8601 occurrence time for outbox expiry."""
    value = event.get("occurredAt")
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()
