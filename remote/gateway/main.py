"""Command-line entry point for the gateway background runtime."""

from __future__ import annotations

import logging
import sys
from threading import Thread

from app import create_runtime
from auth import AuthenticationError, OAuthConfig
from config import ConfigurationError, GatewayConfig
from server import create_server
from telegram_bot import TelegramBot


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        config = GatewayConfig.from_env()
        auth_config = OAuthConfig.from_env()
    except (ConfigurationError, AuthenticationError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    runtime = create_runtime(config)
<<<<<<< f6a71b3b51a4b68b89be455c0487c4f924d8702e
    auth_server = create_server(auth_config, (config.bind_host, config.bind_port), hub=runtime.hub)
||||||| c99af4e0b5d867d05e655e275feeded1932aeb3e
    auth_server = create_server(auth_config, (config.bind_host, config.bind_port), runtime)
=======
    bot = TelegramBot(runtime, config.telegram_bot_token, config.telegram_chat_id)
    auth_server = create_server(auth_config, (config.bind_host, config.bind_port), runtime)
>>>>>>> 5fc76a4af1662ae7ec9c49b5404f5ab4fcf9dcfd
    auth_thread = Thread(target=auth_server.serve_forever, name="gateway-http", daemon=True)
    telegram_thread = Thread(target=bot.run_forever, name="gateway-telegram", daemon=True)
    auth_thread.start()
    telegram_thread.start()
    try:
        runtime.run_forever()
    finally:
        runtime.hub.close()
        auth_server.shutdown()
        auth_server.server_close()
        auth_thread.join(timeout=5)
        telegram_thread.join(timeout=5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
