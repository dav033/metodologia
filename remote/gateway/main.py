"""Command-line entry point for the gateway background runtime."""

from __future__ import annotations

import logging
import sys

from app import create_runtime
from config import ConfigurationError, GatewayConfig


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        config = GatewayConfig.from_env()
    except ConfigurationError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    create_runtime(config).run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
