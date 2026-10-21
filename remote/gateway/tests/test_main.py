from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import main


class MainBotThreadTests(unittest.TestCase):
    def run_main(self, flow_run_bot: str | None) -> list[str]:
        runtime = SimpleNamespace(
            hub=SimpleNamespace(close=lambda: None),
            run_forever=lambda: None,
        )
        auth_server = SimpleNamespace(
            serve_forever=lambda: None,
            shutdown=lambda: None,
            server_close=lambda: None,
        )
        started: list[str] = []

        class FakeThread:
            def __init__(self, *, target, name, daemon):
                self.name = name

            def start(self):
                started.append(self.name)

            def join(self, timeout):
                pass

        env = {} if flow_run_bot is None else {"FLOW_RUN_BOT": flow_run_bot}
        with (
            patch.dict(os.environ, env, clear=True),
            patch.object(main.GatewayConfig, "from_env", return_value=SimpleNamespace(
                bind_host="127.0.0.1", bind_port=8790, telegram_bot_token="", telegram_chat_id=""
            )),
            patch.object(main.OAuthConfig, "from_env", return_value=object()),
            patch.object(main, "create_runtime", return_value=runtime),
            patch.object(main, "create_server", return_value=auth_server),
            patch.object(main, "TelegramBot"),
            patch.object(main, "Thread", FakeThread),
        ):
            self.assertEqual(main.main(), 0)
        return started

    def test_bot_thread_is_skipped_when_disabled(self):
        for value in ("0", "false", "FALSE"):
            with self.subTest(value=value):
                self.assertEqual(self.run_main(value), ["gateway-http"])

    def test_bot_thread_starts_by_default(self):
        self.assertEqual(self.run_main(None), ["gateway-http", "gateway-telegram"])


if __name__ == "__main__":
    unittest.main()
