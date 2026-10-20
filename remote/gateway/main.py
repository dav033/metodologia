"""Command-line entry point for the gateway background runtime."""

from __future__ import annotations

import logging
import sys
from threading import Thread

from app import create_runtime
from auth import AuthenticationError, OAuthConfig
from config import ConfigurationError, GatewayConfig
from server import create_server


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        config = GatewayConfig.from_env()
        auth_config = OAuthConfig.from_env()
    except (ConfigurationError, AuthenticationError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    auth_server = create_server(auth_config, (config.bind_host, config.bind_port))
    auth_thread = Thread(target=auth_server.serve_forever, name="gateway-http", daemon=True)
    auth_thread.start()
    try:
        create_runtime(config).run_forever()
    finally:
        auth_server.shutdown()
        auth_server.server_close()
        auth_thread.join(timeout=5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
