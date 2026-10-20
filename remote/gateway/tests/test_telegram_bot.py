from __future__ import annotations

import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from app import GatewayRuntime
from config import GatewayConfig
from telegram_bot import TelegramBot

OWNER = "424242"


class FakeApi:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []
        self.updates: list[dict] = []

    def call(self, method, payload, timeout=None):
        self.calls.append((method, payload))
        if method == "getUpdates":
            pending, self.updates = self.updates, []
            return pending
        return True


class FakeLaptop:
    def __init__(self) -> None:
        self.command_calls: list[dict] = []
        self.feed: list[dict] = []

    def health(self):
        return {"status": "ok"}

    def snapshot(self):
        return {"runs": []}

    def events(self, after):
        return {"events": self.feed, "nextCursor": "c1"}

    def command(self, command):
        self.command_calls.append(command)
        return 200, {"status": "OK"}


class TelegramBotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config = GatewayConfig(
            laptop_origin="http://127.0.0.1:18765", gateway_key="test-key", telegram_bot_token="test-token",
            telegram_chat_id=OWNER, database_path=Path(self.temp.name) / "gateway.sqlite",
            frontend_origin="https://flow.example.test")
        self.laptop = FakeLaptop()
        self.sent: list = []
        self.runtime = GatewayRuntime(self.config, laptop=self.laptop, sender=lambda *args: self.sent.append(args))
        self.addCleanup(self.runtime.outbox._db.close)
        self.runtime.stream.update_snapshot({"runs": [
            {"project": "demo", "req": "REQ-027", "state": "running", "activeAttempt": {"id": "att-1"}}]}, "2026-10-20T12:00:00Z")
        self.api = FakeApi()
        self.bot = TelegramBot(self.api, OWNER, self.runtime, poll_timeout=0)

    @staticmethod
    def callback(data: str, chat: str = OWNER, ident: str = "99887766554433") -> dict:
        return {"update_id": 1, "callback_query": {"id": ident, "data": data, "message": {"chat": {"id": int(chat)}}}}

    def test_alert_message_carries_inline_buttons_for_safe_actions_only(self) -> None:
        payloads = []

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b'{"ok": true, "result": true}'

        def fake_urlopen(request, timeout=None):
            payloads.append(json.loads(request.data))
            return Response()

        self.laptop.feed = [{"schemaVersion": 1, "id": "evt-1", "cursor": "1", "type": "attempt.failed",
                             "occurredAt": "2026-10-20T12:00:00Z", "dedupeKey": "evt-1",
                             "target": {"project": "demo", "req": "REQ-027", "taskId": "T3", "attemptId": "att-1"},
                             "data": {"failure": "verification_rejected",
                                      "retries": {"attempts": 3, "maxAttempts": 3, "remaining": 0}}}]
        runtime = GatewayRuntime(self.config, laptop=self.laptop)
        self.addCleanup(runtime.outbox._db.close)
        with patch("notifications.urlopen", fake_urlopen):
            runtime.poll_once()
        self.assertEqual(len(payloads), 1)
        payload = payloads[0]
        self.assertEqual(payload["chat_id"], OWNER)
        for fragment in ("REQ-027", "T3", "verification_rejected", "3/3"):
            self.assertIn(fragment, payload["text"])
        row = payload["reply_markup"]["inline_keyboard"][0]
        self.assertEqual([button["text"] for button in row], ["Ver", "Reintentar", "Pausar"])
        self.assertTrue(row[0]["url"].startswith("https://flow.example.test/"))
        self.assertEqual({button["callback_data"] for button in row[1:]}, {"retry|demo/REQ-027|T3", "pause|demo/REQ-027|"})
        self.assertFalse(any(word in json.dumps(payload) for word in ("approve", "launch", "delete")))

    def test_other_chats_are_ignored_completely(self) -> None:
        self.bot.handle_update({"update_id": 2, "message": {"chat": {"id": 7}, "text": "/estado"}})
        self.bot.handle_update(self.callback("pause|demo/REQ-027|", chat="7"))
        self.assertEqual(self.api.calls, [])
        self.assertEqual(self.laptop.command_calls, [])

    def test_estado_replies_to_owner_with_cached_state(self) -> None:
        self.bot.handle_update({"update_id": 3, "message": {"chat": {"id": int(OWNER)}, "text": "/estado@flow_bot"}})
        method, payload = self.api.calls[0]
        self.assertEqual((method, payload["chat_id"]), ("sendMessage", OWNER))
        self.assertIn("demo/REQ-027: running", payload["text"])

    def test_safe_callback_relays_a_telegram_origin_command_once_per_press(self) -> None:
        update = self.callback("retry|demo/REQ-027|T3")
        self.bot.handle_update(update)
        self.bot.handle_update(update)
        self.assertEqual(len(self.laptop.command_calls), 2)
        first = self.laptop.command_calls[0]
        self.assertEqual((first["command"], first["origin"], first["target"]), ("retry", "telegram", "demo/REQ-027"))
        self.assertEqual(first["precondition"], {"state": "running"})
        self.assertEqual(first["params"]["task"], "T3")
        self.assertEqual(first["idempotency_key"], self.laptop.command_calls[1]["idempotency_key"])
        self.assertEqual(self.api.calls[0][0], "answerCallbackQuery")

    def test_unsafe_or_malformed_callbacks_never_reach_the_laptop(self) -> None:
        for data in ("approve|demo/REQ-027|", "launch|demo/REQ-027|", "delete-plan|demo/REQ-027|", "pause|../x|",
                     "retry|demo/REQ-027|", "pause"):
            self.bot.handle_update(self.callback(data))
        self.assertEqual(self.laptop.command_calls, [])
        self.assertTrue(all(call[0] == "answerCallbackQuery" for call in self.api.calls))
        self.assertEqual(len(self.api.calls), 6)

    def test_polling_persists_the_offset_across_restarts(self) -> None:
        self.api.updates = [{"update_id": 41, "message": {"chat": {"id": int(OWNER)}, "text": "/estado"}}]
        self.assertEqual(self.bot.poll_once(), 1)
        self.bot.poll_once()
        self.assertEqual(self.api.calls[-1][1]["offset"], 42)

    def test_production_entrypoint_starts_the_bot(self) -> None:
        from main import main
        started = []

        class FakeServer:
            def serve_forever(self): return None
            def shutdown(self): return None
            def server_close(self): return None

        class FakeBot:
            def __init__(self, api, chat_id, runtime):
                started.append(chat_id)

            def run_forever(self):
                started.append("running")

        environment = {
            "LAPTOP_ORIGIN": self.config.laptop_origin, "FLOW_GATEWAY_KEY": "test-key",
            "TELEGRAM_BOT_TOKEN": "test-token", "TELEGRAM_CHAT_ID": OWNER,
            "GATEWAY_DATABASE": str(Path(self.temp.name) / "main.sqlite"), "GITHUB_CLIENT_ID": "id",
            "GITHUB_CLIENT_SECRET": "secret", "SESSION_SECRET": "test-session-secret-with-more-than-32-bytes",
            "FLOW_FRONTEND_ORIGIN": "https://flow.example.test",
        }
        with patch.dict(os.environ, environment, clear=True), patch("main.create_server", return_value=FakeServer()), \
                patch("main.TelegramBot", FakeBot), patch.object(GatewayRuntime, "run_forever", lambda self: time.sleep(0.2)):
            self.assertEqual(main(), 0)
        self.assertEqual(started[0], OWNER)
        self.assertIn("running", started)


if __name__ == "__main__":
    unittest.main()
