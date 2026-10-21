from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any, Mapping

from app import create_runtime
from config import GatewayConfig
from telegram_bot import TelegramBot


class FakeLaptop:
    def __init__(self) -> None:
        self.commands: list[dict[str, Any]] = []

    def snapshot(self) -> dict[str, Any]:
        return {"runs": [{
            "project": "demo",
            "req_id": "REQ-027",
            "status": "running",
            "active": True,
        }]}

    def post_json(self, path: str, command: dict[str, Any]) -> dict[str, Any]:
        if path != "/api/remote/v1/commands":
            raise AssertionError("unexpected laptop API path")
        self.commands.append(command)
        return {"commandId": "ledger-1", "status": "accepted"}


class FakeTelegramApi:
    def __init__(self) -> None:
        self.updates: list[dict[str, Any]] = []
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def __call__(self, method: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        self.calls.append((method, dict(payload)))
        if method == "getUpdates":
            updates, self.updates = self.updates, []
            return {"ok": True, "result": updates}
        return {"ok": True, "result": {}}


class TelegramBotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.laptop = FakeLaptop()
        config = GatewayConfig(
            laptop_origin="http://127.0.0.1:18765",
            gateway_key="test-key",
            telegram_bot_token="test-token",
            telegram_chat_id="owner-chat",
            database_path=Path(self.directory.name) / "gateway.sqlite",
        )
        self.runtime = create_runtime(config, laptop=self.laptop, sender=lambda _message: None)
        self.addCleanup(self.runtime.outbox._db.close)
        self.api = FakeTelegramApi()
        self.bot = TelegramBot(self.runtime, "test-token", "owner-chat", api_call=self.api)

    def test_unknown_chat_id_gets_no_answer(self) -> None:
        self.api.updates = [
            {"update_id": 1, "message": {"chat": {"id": 123}, "text": "/estado"}},
            {"update_id": 2, "callback_query": {
                "id": "callback-1", "data": "forged", "message": {"chat": {"id": 123}},
            }},
        ]

        self.bot.poll_once()

        self.assertEqual([method for method, _payload in self.api.calls], ["getUpdates"])
        self.assertEqual(self.laptop.commands, [])
        self.assertEqual(self.api.calls[0][1]["offset"], 0)
        self.assertEqual(self.bot._offset, 3)

    def test_button_press_creates_a_telegram_ledger_command(self) -> None:
        self.api.updates = [{"update_id": 1, "message": {"chat": {"id": "owner-chat"}, "text": "/estado"}}]
        self.bot.poll_once()
        message = next(payload for method, payload in self.api.calls if method == "sendMessage")
        self.assertIn("demo/REQ-027 — running", message["text"])
        callback_data = message["reply_markup"]["inline_keyboard"][0][0]["callback_data"]
        self.api.updates = [{"update_id": 2, "callback_query": {
            "id": "callback-2",
            "data": callback_data,
            "message": {"chat": {"id": "owner-chat"}},
        }}]

        self.bot.poll_once()

        self.assertEqual(len(self.laptop.commands), 1)
        command = self.laptop.commands[0]
        self.assertEqual(command["command"], "pause")
        self.assertEqual(command["origin"], "telegram")
        self.assertEqual(command["target"], "demo/REQ-027")
        self.assertEqual(command["precondition"], {"state": "running"})
        self.assertEqual(len(command["idempotency_key"]), 32)
        self.assertTrue(any(method == "answerCallbackQuery" for method, _payload in self.api.calls))

        self.api.updates = [{"update_id": 3, "callback_query": {
            "id": "callback-replay",
            "data": callback_data,
            "message": {"chat": {"id": "owner-chat"}},
        }}]
        self.bot.poll_once()
        self.assertEqual(len(self.laptop.commands), 1)

    def test_estado_lists_active_runs_and_offers_only_safe_action(self) -> None:
        self.api.updates = [{"update_id": 1, "message": {
            "chat": {"id": "owner-chat"}, "text": "/estado@flow_bot",
        }}]

        self.bot.poll_once()

        message = next(payload for method, payload in self.api.calls if method == "sendMessage")
        self.assertIn("Ejecuciones activas:", message["text"])
        button = message["reply_markup"]["inline_keyboard"][0][0]
        self.assertEqual(button["text"], "Pausar: demo/REQ-027")
        self.assertLessEqual(len(button["callback_data"].encode("utf-8")), 64)

    def test_estado_uses_inline_buttons_only_for_live_owner_runs(self) -> None:
        self.laptop.snapshot = lambda: {"runs": [
            {"project": "demo", "req_id": "REQ-027", "status": "running", "active": True},
            {"project": "demo", "req_id": "REQ-028", "status": "done", "active": False},
        ]}
        self.api.updates = [{"update_id": 1, "message": {"chat": {"id": "owner-chat"}, "text": "/estado"}}]

        self.bot.poll_once()

        message = next(payload for method, payload in self.api.calls if method == "sendMessage")
        buttons = message["reply_markup"]["inline_keyboard"]
        self.assertEqual(len(buttons), 1)
        self.assertEqual(buttons[0][0]["text"], "Pausar: demo/REQ-027")
        self.assertNotIn("REQ-028", [self.bot._callbacks[token]["target"]["req"] for token in self.bot._callbacks])

    def test_telegram_relay_rejects_commands_outside_safe_run_controls(self) -> None:
        command = {
            "schemaVersion": 1,
            "idempotencyKey": "0123456789abcdef0123456789abcdef",
            "type": "cancel-plan",
            "target": {"kind": "plan", "project": "demo", "req": "REQ-027"},
            "precondition": {"state": "review"},
        }

        result = self.runtime.submit_telegram_command(command)

        self.assertEqual(result["code"], "INVALID_COMMAND")
        command.update(type="pause", target={"kind": "run", "project": "demo", "req": "REQ-027"})
        result = self.runtime.submit_telegram_command(command)
        self.assertEqual(result["code"], "INVALID_COMMAND")
        self.assertEqual(self.laptop.commands, [])


if __name__ == "__main__":
    unittest.main()
