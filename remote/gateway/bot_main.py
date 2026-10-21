"""Command-line entry point for the separately supervised Telegram bot."""

from __future__ import annotations

import logging
import sys

from app import create_runtime
from config import ConfigurationError, GatewayConfig
from telegram_bot import TelegramBot


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        config = GatewayConfig.from_env()
    except ConfigurationError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    runtime = create_runtime(config)
    bot = TelegramBot(runtime, config.telegram_bot_token, config.telegram_chat_id)
    bot.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
