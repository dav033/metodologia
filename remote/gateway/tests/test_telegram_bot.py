import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from app import GatewayRuntime, create_runtime
from config import GatewayConfig
from main import main
from telegram_bot import TelegramBot
from test_notify import FakeResponse, free_port

OWNER = 4242


class Laptop:
    def __init__(self):
        self.commands = []

    def health(self):
        return {"status": "ok"}

    def snapshot(self):
        return {"runs": [{"run": "demo/REQ-027", "status": "running"},
                         {"run": "demo/REQ-001", "status": "done"},
                         {"run": "demo/REQ-002", "status": "paused"}], "plans": []}

    def events(self, after):
        return {"events": [], "nextCursor": after}

    def command(self, payload):
        self.commands.append(payload)
        return 202, {"status": "OK", "idempotency_key": payload["idempotency_key"]}


def message(chat_id, text, update_id=1):
    return {"update_id": update_id, "message": {"chat": {"id": chat_id}, "text": text}}


def press(chat_id, data, update_id=2):
    return {"update_id": update_id, "callback_query": {"id": f"cb{update_id}", "data": data,
                                                       "message": {"chat": {"id": chat_id}}}}


def env(directory):
    return {"LAPTOP_ORIGIN": "http://127.0.0.1:18765", "FLOW_GATEWAY_KEY": "k", "TELEGRAM_BOT_TOKEN": "tok",
            "TELEGRAM_CHAT_ID": str(OWNER), "GATEWAY_DATABASE": str(Path(directory) / "g.sqlite"),
            "GITHUB_CLIENT_ID": "id", "GITHUB_CLIENT_SECRET": "secret",
            "SESSION_SECRET": "test-session-secret-with-more-than-32-bytes",
            "FLOW_FRONTEND_ORIGIN": "https://flow.example.test",
            "GATEWAY_BIND": "127.0.0.1", "GATEWAY_PORT": str(free_port())}


class BotUnitTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.laptop = Laptop()
        self.runtime = create_runtime(GatewayConfig.from_env(env(self.dir.name)), laptop=self.laptop,
                                      sender=lambda m, url=None: None)
        self.runtime.poll_once()
        self.calls = []
        self.bot = TelegramBot(str(OWNER), self.runtime, lambda m, p, t: self.calls.append((m, p)))

    def test_unknown_chat_gets_no_answer_and_no_command(self):
        self.bot.handle_update(message(999, "/estado"))
        self.bot.handle_update(press(999, "pause:demo/REQ-027"))
        self.bot.handle_update({"update_id": 3, "message": {"text": "/estado"}})
        self.assertEqual(self.calls, [])
        self.assertEqual(self.laptop.commands, [])

    def test_estado_lists_only_active_runs(self):
        self.bot.handle_update(message(OWNER, "/estado"))
        (method, body), = self.calls
        self.assertEqual(method, "sendMessage")
        self.assertIn("demo/REQ-027", body["text"])
        self.assertIn("demo/REQ-002", body["text"])
        self.assertNotIn("REQ-001", body["text"])
        buttons = [b["callback_data"] for row in body["reply_markup"]["inline_keyboard"] for b in row]
        self.assertEqual(buttons, ["pause:demo/REQ-027", "resume:demo/REQ-002"])

    def test_button_creates_ledger_command_with_telegram_origin(self):
        self.bot.handle_update(press(OWNER, "pause:demo/REQ-027"))
        (command,) = self.laptop.commands
        self.assertEqual((command["command"], command["target"], command["origin"]),
                         ("pause", "demo/REQ-027", "telegram"))
        self.assertEqual(command["idempotency_key"], "telegram:cb2")
        self.assertEqual(command["precondition"], {"state": "running"})

    def test_unsafe_button_is_refused(self):
        for data in ("cancel-plan:demo/REQ-027", "approve:demo/REQ-027", "pause:demo", "junk"):
            self.bot.handle_update(press(OWNER, data))
        self.assertEqual(self.laptop.commands, [])

    def test_offset_persists_across_polls(self):
        updates = [[message(OWNER, "/estado", 7)], []]
        bot = TelegramBot(str(OWNER), self.runtime,
                          lambda m, p, t: updates.pop(0) if m == "getUpdates" else None)
        self.assertEqual(bot.poll_once(0), 1)
        self.assertEqual(self.runtime.outbox.state_value("telegram_update_offset"), 8)


class BotThroughMainTests(unittest.TestCase):
    def test_main_starts_bot_that_answers_owner_only_and_creates_command(self):
        laptop = Laptop()
        sent = []
        queue = [[message(111, "/estado", 1), press(111, "pause:demo/REQ-027", 2),
                  message(OWNER, "/estado", 3), press(OWNER, "pause:demo/REQ-027", 4)]]

        def fake_urlopen(request, timeout=None):
            method = request.full_url.rsplit("/", 1)[1]
            body = json.loads(request.data.decode("utf-8"))
            if method == "getUpdates":
                if queue:
                    return FakeResponse(json.dumps({"ok": True, "result": queue.pop(0)}).encode())
                time.sleep(0.02)
                return FakeResponse(b'{"ok": true, "result": []}')
            sent.append((method, body))
            return FakeResponse(b'{"ok": true, "result": true}')

        def cycle(runtime):
            runtime.poll_once()
            deadline = time.time() + 5
            while time.time() < deadline and not (laptop.commands and len(sent) >= 2):
                time.sleep(0.02)

        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, env(directory), clear=True), \
                patch("app.LaptopClient", return_value=laptop), patch("telegram_bot.urlopen", fake_urlopen), \
                patch("notifications.urlopen", lambda *a, **k: FakeResponse()), \
                patch.object(GatewayRuntime, "run_forever", cycle):
            self.assertEqual(main(), 0)
        self.assertTrue(all(body.get("chat_id", OWNER) == str(OWNER) or "callback_query_id" in body
                            for _, body in sent))
        self.assertEqual([m for m, _ in sent], ["sendMessage", "answerCallbackQuery"])
        self.assertIn("demo/REQ-027", sent[0][1]["text"])
        self.assertEqual([(c["command"], c["origin"]) for c in laptop.commands], [("pause", "telegram")])


if __name__ == "__main__":
    unittest.main()
