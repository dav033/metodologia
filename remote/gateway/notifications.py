"""Deterministic event rules and a durable Telegram outbox."""

from __future__ import annotations

import inspect
import json
import sqlite3
import threading
import time
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


def _accepts_markup(send: Callable[..., None]) -> bool:
    """Plain one-argument senders (tests, simple sinks) get the text only; Telegram's sender also takes buttons."""
    try:
        parameters = list(inspect.signature(send).parameters.values())
    except (TypeError, ValueError):
        return False
    return any(p.kind is p.VAR_POSITIONAL for p in parameters) or \
        sum(p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD) for p in parameters) >= 2


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
            created_at REAL NOT NULL DEFAULT 0,
            markup TEXT
        )""")
        columns = {row[1] for row in self._db.execute("PRAGMA table_info(telegram_outbox)")}
        if "markup" not in columns:
            self._db.execute("ALTER TABLE telegram_outbox ADD COLUMN markup TEXT")
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

    def enqueue(self, dedupe_key: str, message: str, markup: dict[str, Any] | None = None) -> bool:
        with self._lock:
            cursor = self._db.execute(
                "INSERT OR IGNORE INTO telegram_outbox(dedupe_key, message, created_at, markup) VALUES (?, ?, ?, ?)",
                (dedupe_key, message, time.time(), json.dumps(markup) if markup else None),
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
                "SELECT dedupe_key, message, attempts, created_at, markup FROM telegram_outbox "
                "WHERE status = 'pending' AND (next_attempt <= ? OR created_at < ?) "
                "ORDER BY rowid LIMIT 20", (current, current - 3600)
            ).fetchall()
        delivered = 0
        for key, message, attempts, created_at, markup in rows:
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
                send(message, json.loads(markup)) if markup and _accepts_markup(send) else send(message)
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


class TelegramApi:
    """Minimal Bot API client; every call is bounded and returns the decoded `result`."""

    def __init__(self, token: str, timeout: float = 5.0):
        self._base = f"https://api.telegram.org/bot{token}/"
        self._timeout = timeout

    def call(self, method: str, payload: dict[str, Any], timeout: float | None = None) -> Any:
        request = Request(self._base + method, data=json.dumps(payload).encode("utf-8"),
                          headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=timeout or self._timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
        if not isinstance(result, dict) or result.get("ok") is not True:
            raise RuntimeError("Telegram rejected the request")
        return result.get("result")


class TelegramSender:
    def __init__(self, token: str, chat_id: str, timeout: float = 5.0):
        self._api = TelegramApi(token, timeout)
        self._chat_id = chat_id

    def __call__(self, message: str, markup: dict[str, Any] | None = None) -> None:
        payload: dict[str, Any] = {"chat_id": self._chat_id, "text": message}
        if markup:
            payload["reply_markup"] = markup
        self._api.call("sendMessage", payload)


# Callback data is `<action>|<project>/<REQ>|<task>`; only these actions may ever be built or accepted.
SAFE_ACTIONS = {"pause": "Pausar", "resume": "Reanudar", "retry": "Reintentar"}
_BUTTON_EVENTS = {
    "attempt.failed": ("ver", "retry", "pause"), "attempt.blocked": ("ver", "retry", "pause"),
    "attempt.stalled": ("ver", "pause"), "round.waiting": ("ver",), "plan.waiting": ("ver",),
    "run.finished": ("ver",), "quota.exhausted": ("ver", "resume"),
}


def _buttons(event_type: str, target: dict[str, Any], frontend_origin: str) -> dict[str, Any] | None:
    project, req, task = target.get("project"), target.get("req"), target.get("taskId")
    if not isinstance(project, str) or not isinstance(req, str):
        run = target.get("run")
        project, _, req = run.partition("/") if isinstance(run, str) else ("", "", "")
    if not project or not req:
        return None
    row = []
    for action in _BUTTON_EVENTS.get(event_type, ()):
        if action == "ver":
            attempt = target.get("attemptId")
            if frontend_origin:
                anchor = f"#attempt-{attempt}" if isinstance(attempt, str) and attempt else ""
                row.append({"text": "Ver", "url": f"{frontend_origin}/{anchor}"})
            continue
        data = f"{action}|{project}/{req}|{task if isinstance(task, str) and action == 'retry' else ''}"
        if action == "retry" and not isinstance(task, str):
            continue
        if len(data.encode("utf-8")) <= 64:
            row.append({"text": SAFE_ACTIONS[action], "callback_data": data})
    return {"inline_keyboard": [row]} if row else None


def notification_for_event(event: Mapping[str, Any], frontend_origin: str = "") -> tuple[str, str, dict[str, Any] | None] | None:
    """Return the stable dedupe key, rendered message and inline buttons for a notifying feed event."""
    event_type = event.get("type")
    dedupe_key = event.get("dedupeKey")
    event_id = event.get("id")
    if (event_type not in _EVENT_MESSAGES or not isinstance(event_id, str) or not event_id
            or not isinstance(dedupe_key, str) or not dedupe_key):
        return None
    target = event.get("target") if isinstance(event.get("target"), dict) else {}
    data = event.get("data") if isinstance(event.get("data"), dict) else {}
    req = target.get("req")
    lines = [_EVENT_MESSAGES[event_type]]
    if isinstance(req, str) and req:
        lines.append(req)
    elif isinstance(target.get("run"), str):
        lines.append(target["run"])
    if isinstance(target.get("taskId"), str):
        lines.append(f"Tarea {target['taskId']}")
    cause = data.get("failure") or data.get("summary")
    if isinstance(cause, str) and cause:
        lines.append(f"Causa: {cause[:300]}")
    retries = data.get("retries")
    if isinstance(retries, dict):
        lines.append(f"Intentos: {retries.get('attempts')}/{retries.get('maxAttempts')}")
    markup = _buttons(event_type, target, frontend_origin.rstrip("/"))
    if markup and frontend_origin:
        lines.append(f"{frontend_origin.rstrip('/')}/")
    return f"event:{dedupe_key}", "\n".join(lines), markup
