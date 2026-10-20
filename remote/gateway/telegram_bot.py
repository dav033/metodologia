"""Owner-only Telegram bot: `/estado`, and safe inline-button actions relayed as telegram-origin commands."""

from __future__ import annotations

import logging
import re
import time
from typing import Any

from commands import CommandValidationError
from notifications import SAFE_ACTIONS
from liveness import LaptopStatus

logger = logging.getLogger(__name__)
OFFSET_KEY = "telegram_update_offset"
_TARGET = re.compile(r"^[A-Za-z0-9_-]+/REQ-[0-9]+$")
_TASK = re.compile(r"^T[0-9A-Za-z_-]{1,79}$")
_RESULT_TEXT = {
    "STALE_PRECONDITION": "El estado cambió; revisa y vuelve a intentarlo.",
    "LAPTOP_OFFLINE": "El portátil está desconectado; la acción no se encola.",
    "UNKNOWN_OUTCOME": "Resultado desconocido; no repitas la acción sin revisar.",
}


class TelegramBot:
    def __init__(self, api: Any, owner_chat_id: str, runtime: Any, poll_timeout: int = 20):
        self._api = api
        self._owner = str(owner_chat_id)
        self._runtime = runtime
        self._poll_timeout = poll_timeout

    def poll_once(self) -> int:
        """Fetch and handle pending updates; the next offset is persisted so a restart never replays them."""
        offset = self._runtime.outbox.state_value(OFFSET_KEY)
        updates = self._api.call("getUpdates", {"offset": offset + 1 if offset else 0, "timeout": self._poll_timeout,
                                                "allowed_updates": ["message", "callback_query"]},
                                 timeout=self._poll_timeout + 10)
        handled = 0
        for update in updates if isinstance(updates, list) else []:
            if not isinstance(update, dict) or not isinstance(update.get("update_id"), int):
                continue
            try:
                self.handle_update(update)
            except Exception:  # noqa: BLE001 - one bad update must not stop the bot or leak details
                logger.exception("telegram update failed")
            self._runtime.outbox.set_state_value(OFFSET_KEY, update["update_id"])
            handled += 1
        return handled

    def run_forever(self) -> None:
        while True:
            try:
                self.poll_once()
            except Exception:  # noqa: BLE001
                logger.warning("telegram polling failed; retrying")
                time.sleep(5)

    def _from_owner(self, chat: Any) -> bool:
        return isinstance(chat, dict) and str(chat.get("id")) == self._owner

    def handle_update(self, update: dict[str, Any]) -> None:
        message, callback = update.get("message"), update.get("callback_query")
        if isinstance(callback, dict):
            if self._from_owner((callback.get("message") or {}).get("chat")):
                self._handle_callback(callback)
            return
        if isinstance(message, dict) and self._from_owner(message.get("chat")):
            command = str(message.get("text") or "").split(maxsplit=1)
            name = command[0].split("@", 1)[0].lower() if command else ""
            if name == "/estado":
                self._reply(self.status_text())
            elif name == "/start":
                self._reply("Comandos: /estado. Los botones de las alertas permiten ver, pausar, reanudar y reintentar.")

    def _reply(self, text: str) -> None:
        self._api.call("sendMessage", {"chat_id": self._owner, "text": text})

    def status_text(self) -> str:
        snapshot = self._runtime.stream.snapshot()
        online = self._runtime.liveness.status is not LaptopStatus.OFFLINE
        if snapshot is None:
            return "Sin estado disponible todavía." + ("" if online else " Portátil desconectado.")
        runs = [run for run in snapshot.get("runs", []) if isinstance(run, dict)]
        lines = [("Portátil en línea." if online else "Portátil desconectado (último estado en caché).")
                 + f" Ejecuciones: {len(runs)}."]
        for run in runs[:10]:
            active = run.get("activeAttempt") or run.get("active_task")
            task = f" · {active.get('id')}" if isinstance(active, dict) and active.get("id") else ""
            lines.append(f"{run.get('project')}/{run.get('req')}: {run.get('state')}{task}")
        return "\n".join(lines)

    def _answer(self, callback: dict[str, Any], text: str) -> None:
        self._api.call("answerCallbackQuery", {"callback_query_id": callback.get("id"), "text": text[:180]})

    def _handle_callback(self, callback: dict[str, Any]) -> None:
        parts = str(callback.get("data") or "").split("|")
        if len(parts) != 3 or parts[0] not in SAFE_ACTIONS or not _TARGET.fullmatch(parts[1]) or \
                (parts[0] == "retry" and not _TASK.fullmatch(parts[2])):
            return self._answer(callback, "Acción no permitida desde Telegram.")
        action, target, task = parts
        project, req = target.split("/")
        run = next((item for item in (self._runtime.stream.snapshot() or {}).get("runs", [])
                    if isinstance(item, dict) and item.get("project") == project and item.get("req") == req), None)
        if run is None or not isinstance(run.get("state"), str):
            return self._answer(callback, "No encuentro esa ejecución en el estado actual.")
        command = {"schemaVersion": 1, "idempotencyKey": f"telegram-{callback.get('id')}", "type": action,
                   "target": {"kind": "task" if action == "retry" else "run", "project": project, "req": req,
                              **({"taskId": task} if action == "retry" else {})},
                   "precondition": {"state": run["state"]}}
        if action == "retry":
            command["reason"] = "Reintento solicitado desde Telegram"
        try:
            self._runtime.submit_command(command, origin="telegram")
        except CommandValidationError:
            return self._answer(callback, "Acción no permitida desde Telegram.")
        except Exception as exc:  # noqa: BLE001 - map to a fixed, safe sentence
            code = getattr(exc, "code", "")
            return self._answer(callback, _RESULT_TEXT.get(code, "El portátil no aceptó la acción."))
        self._answer(callback, f"{SAFE_ACTIONS[action]}: enviado.")
