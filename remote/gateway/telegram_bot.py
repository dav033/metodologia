"""Owner-only Telegram long-polling controls for the remote gateway."""

from __future__ import annotations

import json
import logging
import secrets
import time
from typing import Any, Callable, Mapping
from urllib.request import Request, urlopen

from app import ACTIVE_RUN_STATES, TELEGRAM_REQ_ID, run_state
from upstream import UpstreamError

logger = logging.getLogger(__name__)
POLL_TIMEOUT_SECONDS = 20
HTTP_TIMEOUT_SECONDS = 25
MAX_TELEGRAM_RESPONSE_BYTES = 1_000_000


def telegram_api(token: str, method: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    """Call the Telegram Bot API without logging credentials or response bodies."""
    request = Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        raw = response.read(MAX_TELEGRAM_RESPONSE_BYTES + 1)
    if len(raw) > MAX_TELEGRAM_RESPONSE_BYTES:
        raise RuntimeError("Telegram response exceeded the configured limit")
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict) or value.get("ok") is not True:
        raise RuntimeError("Telegram API request failed")
    return value


class TelegramBot:
    """Poll Telegram updates and expose a narrow set of owner-only run controls."""

    def __init__(self, runtime: Any, token: str, owner_chat_id: str,
                 api_call: Callable[[str, Mapping[str, Any]], dict[str, Any]] | None = None):
        self.runtime = runtime
        self.owner_chat_id = str(owner_chat_id)
        self._api_call = api_call or (lambda method, payload: telegram_api(token, method, payload))
        self._offset = 0
        self._callbacks: dict[str, dict[str, Any]] = {}

    def poll_once(self) -> int:
        result = self._api_call("getUpdates", {
            "offset": self._offset,
            "timeout": POLL_TIMEOUT_SECONDS,
            "allowed_updates": ["message", "callback_query"],
        })
        updates = result.get("result")
        if not isinstance(updates, list):
            raise RuntimeError("Telegram updates response was invalid")
        handled = 0
        for update in updates:
            if not isinstance(update, dict):
                continue
            update_id = update.get("update_id")
            if isinstance(update_id, int) and not isinstance(update_id, bool):
                self._offset = max(self._offset, update_id + 1)
            self._handle_update(update)
            handled += 1
        return handled

    def _handle_update(self, update: Mapping[str, Any]) -> None:
        message = update.get("message")
        if isinstance(message, dict):
            chat = message.get("chat")
            if not self._is_owner_chat(chat):
                return
            text = message.get("text")
            if isinstance(text, str) and text.startswith("/"):
                command = text.split(maxsplit=1)[0].split("@", 1)[0]
                if command == "/estado":
                    self._send_status(str(chat["id"]))
            return

        callback = update.get("callback_query")
        if not isinstance(callback, dict):
            return
        callback_message = callback.get("message")
        chat = callback_message.get("chat") if isinstance(callback_message, dict) else None
        if not self._is_owner_chat(chat):
            return
        callback_id = callback.get("id")
        token = callback.get("data")
        if not isinstance(token, str) or not isinstance(callback_id, str):
            return
        command = self._callbacks.pop(token, None)
        if command is None:
            self._api_call("answerCallbackQuery", {
                "callback_query_id": callback_id, "text": "Acción vencida",
            })
            return
        try:
            result = self.runtime.submit_telegram_command(command)
        except UpstreamError:
            response = "No fue posible enviar el comando al portátil."
        else:
            status = result.get("status", "aceptado")
            code = result.get("code")
            response = (f"Comando registrado: {status}" if status not in {"REJECTED", "FAILED", "UNKNOWN"}
                        else f"Comando no aplicado: {code or status}")
        self._api_call("answerCallbackQuery", {
            "callback_query_id": callback_id,
            "text": response[:180],
            "show_alert": False,
        })

    def _send_status(self, chat_id: str) -> None:
        try:
            snapshot = self.runtime.laptop.snapshot()
        except UpstreamError:
            self._api_call("sendMessage", {
                "chat_id": chat_id, "text": "Estado no disponible: portátil desconectado.",
            })
            return
        if not isinstance(snapshot, Mapping):
            self._send_message(chat_id, "Estado no disponible.")
            return
        runs = snapshot.get("runs")
        if not isinstance(runs, list):
            self._send_message(chat_id, "Estado no disponible.")
            return
        active = [run for run in runs if self._is_active_run(run)]
        if not active:
            self._send_message(chat_id, "No hay ejecuciones activas.")
            return

        lines = ["Ejecuciones activas:"]
        keyboard: list[list[dict[str, str]]] = []
        self._callbacks.clear()
        for run in active[:20]:
            # The snapshot contract (remote/contract/snapshot.schema.json): `req` and `state` (F11).
            project = run.get("project")
            req = run.get("req")
            status = run_state(run)
            if (not isinstance(project, str) or not 1 <= len(project) <= 80
                    or not isinstance(req, str) or not TELEGRAM_REQ_ID.fullmatch(req)
                    or not isinstance(status, str)):
                continue
            lines.append(f"• {project}/{req} — {status}")
            if status not in {"running", "paused"}:
                continue
            action = "pause" if status == "running" else "resume"
            label = "Pausar" if action == "pause" else "Reanudar"
            callback_token = secrets.token_urlsafe(12)
            self._callbacks[callback_token] = {
                "schemaVersion": 1,
                "idempotencyKey": secrets.token_hex(16),
                "type": action,
                "target": {"kind": "run", "project": project, "req": req},
                "precondition": {"state": status},
            }
            keyboard.append([{"text": f"{label}: {project}/{req}", "callback_data": callback_token}])

        payload: dict[str, Any] = {"chat_id": chat_id, "text": "\n".join(lines)}
        if keyboard:
            payload["reply_markup"] = {"inline_keyboard": keyboard}
        self._api_call("sendMessage", payload)

    @staticmethod
    def _is_active_run(run: object) -> bool:
        return isinstance(run, Mapping) and (
            run.get("active") is True or run_state(run) in ACTIVE_RUN_STATES
        )

    def _is_owner_chat(self, chat: object) -> bool:
        return isinstance(chat, Mapping) and str(chat.get("id", "")) == self.owner_chat_id

    def _send_message(self, chat_id: str, text: str) -> None:
        self._api_call("sendMessage", {"chat_id": chat_id, "text": text})

    def run_forever(self) -> None:
        delay = 1.0
        while True:
            try:
                self.poll_once()
                delay = 1.0
            except Exception as exc:
                # HTTP errors may include the token-bearing request URL; log only the exception type.
                logger.warning("Telegram polling failed (%s); retrying", type(exc).__name__)
                time.sleep(delay)
                delay = min(30.0, delay * 2)
