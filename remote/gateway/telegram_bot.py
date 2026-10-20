"""Long-polling Telegram bot: owner-only chat, safe buttons and /estado."""

from __future__ import annotations

import json
import logging
import threading
import time
from typing import Any, Callable
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)
POLL_TIMEOUT_SECONDS = 25
OFFSET_KEY = "telegram_update_offset"
SAFE_COMMANDS = {"pause": "Pausar", "resume": "Reanudar"}  # no destructive or challenged commands
ACTIVE_STATES = frozenset({"running", "waiting", "paused"})
MAX_CALLBACK_BYTES = 64


class TelegramApi:
    def __init__(self, token: str):
        self._base = f"https://api.telegram.org/bot{token}/"

    def __call__(self, method: str, payload: dict[str, Any], timeout: float) -> Any:
        request = Request(self._base + method, data=json.dumps(payload).encode("utf-8"),
                          headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
        if not isinstance(result, dict) or result.get("ok") is not True:
            raise RuntimeError("Telegram rejected the request")
        return result.get("result")


def _active_runs(snapshot: dict[str, Any] | None) -> list[dict[str, Any]]:
    runs = snapshot.get("runs") if isinstance(snapshot, dict) else None
    if not isinstance(runs, list):
        return []
    return [run for run in runs if isinstance(run, dict) and isinstance(run.get("run"), str) and "/" in run["run"]
            and (run.get("active") is True or run.get("status") in ACTIVE_STATES)]


class TelegramBot:
    def __init__(self, chat_id: str, runtime: Any, api: Callable[[str, dict[str, Any], float], Any]):
        self._chat_id = str(chat_id).strip()
        self._runtime = runtime
        self._api = api
        self._stop = threading.Event()

    # -- update handling -------------------------------------------------
    def handle_update(self, update: dict[str, Any]) -> None:
        callback = update.get("callback_query")
        if isinstance(callback, dict):
            message = callback.get("message")
            chat = message.get("chat") if isinstance(message, dict) else None
            if self._allowed(chat):
                self._handle_callback(callback)
            return
        message = update.get("message")
        if isinstance(message, dict) and self._allowed(message.get("chat")):
            text = message.get("text")
            command = text.split()[0].split("@")[0].lower() if isinstance(text, str) and text.split() else ""
            if command in {"/estado", "/start"}:
                self._send_status()

    def _allowed(self, chat: Any) -> bool:
        return isinstance(chat, dict) and bool(self._chat_id) and str(chat.get("id")) == self._chat_id

    def _send_status(self) -> None:
        runs = _active_runs(self._runtime.cached_snapshot())
        if not runs:
            self._say("No hay ejecuciones activas.")
            return
        lines = ["Ejecuciones activas:"]
        rows = []
        for run in runs:
            name, status = run["run"], run.get("status") or "activa"
            lines.append(f"• {name} — {status}")
            command = "resume" if status == "paused" else "pause"
            data = f"{command}:{name}"
            if len(data.encode("utf-8")) <= MAX_CALLBACK_BYTES:
                rows.append([{"text": f"{SAFE_COMMANDS[command]} {name}", "callback_data": data}])
        self._say("\n".join(lines), rows)

    def _handle_callback(self, callback: dict[str, Any]) -> None:
        data = callback.get("data")
        command, _, target = data.partition(":") if isinstance(data, str) else ("", "", "")
        project, _, req = target.partition("/")
        if command not in SAFE_COMMANDS or not project or not req or "/" in req:
            self._answer(callback, "Acción no permitida.")
            return
        run = next((r for r in _active_runs(self._runtime.cached_snapshot()) if r["run"] == target), None)
        payload = {"idempotency_key": f"telegram:{callback.get('id')}", "command": command, "target": target,
                   "origin": "telegram", "params": {},
                   "precondition": {"state": run.get("status")} if run and run.get("status") else None}
        status, result = self._runtime.relay_ledger_command(payload)
        ok = status in (200, 202) and result.get("status") != "REJECTED"
        self._answer(callback, f"{SAFE_COMMANDS[command]}: {'enviado' if ok else 'no se pudo (' + str(result.get('code', status)) + ')'}")

    def _say(self, text: str, rows: list | None = None) -> None:
        body: dict[str, Any] = {"chat_id": self._chat_id, "text": text}
        if rows:
            body["reply_markup"] = {"inline_keyboard": rows}
        self._api("sendMessage", body, 10)

    def _answer(self, callback: dict[str, Any], text: str) -> None:
        self._api("answerCallbackQuery", {"callback_query_id": callback.get("id"), "text": text}, 10)

    # -- polling loop ----------------------------------------------------
    def poll_once(self, timeout: int = POLL_TIMEOUT_SECONDS) -> int:
        offset = self._runtime.outbox.state_value(OFFSET_KEY, 0)
        updates = self._api("getUpdates", {"offset": offset, "timeout": timeout,
                                            "allowed_updates": ["message", "callback_query"]}, timeout + 5)
        handled = 0
        for update in updates if isinstance(updates, list) else []:
            if not isinstance(update, dict) or not isinstance(update.get("update_id"), int):
                continue
            try:
                self.handle_update(update)
            except Exception:  # One bad update must not stall the queue.
                logger.exception("Telegram update failed")
            self._runtime.outbox.set_state_value(OFFSET_KEY, update["update_id"] + 1)
            handled += 1
        return handled

    def run_forever(self) -> None:
        delay = 1.0
        while not self._stop.is_set():
            try:
                self.poll_once()
                delay = 1.0
            except Exception:
                logger.warning("Telegram polling failed; retrying in %.0fs", delay)
                self._stop.wait(delay)
                delay = min(delay * 2, 60.0)

    def stop(self) -> None:
        self._stop.set()
