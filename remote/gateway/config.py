"""Environment-backed settings for the remote gateway."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Mapping


class ConfigurationError(ValueError):
    """Raised when required gateway settings are missing or invalid."""


@dataclass(frozen=True)
class GatewayConfig:
    laptop_origin: str
    gateway_key: str
    telegram_bot_token: str
    telegram_chat_id: str
    database_path: Path
    bind_host: str = "127.0.0.1"
    bind_port: int = 8790
    request_timeout: float = 5.0
    probe_interval: float = 5.0

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "GatewayConfig":
        values = os.environ if env is None else env
        names = (
            "LAPTOP_ORIGIN",
            "FLOW_GATEWAY_KEY",
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_CHAT_ID",
            "GATEWAY_DATABASE",
        )
        missing = [name for name in names if not values.get(name, "").strip()]
        if missing:
            raise ConfigurationError("Missing required gateway configuration: " + ", ".join(missing))

        origin = values["LAPTOP_ORIGIN"].rstrip("/")
        if not origin.startswith(("http://", "https://")):
            raise ConfigurationError("LAPTOP_ORIGIN must be an http or https URL")
        try:
            port = int(values.get("GATEWAY_PORT", "8790"))
            timeout = float(values.get("UPSTREAM_TIMEOUT", "5"))
            interval = float(values.get("PROBE_INTERVAL", "5"))
        except ValueError as exc:
            raise ConfigurationError("Gateway port and timeouts must be numeric") from exc
        if not 1 <= port <= 65535 or timeout <= 0 or interval <= 0:
            raise ConfigurationError("Gateway port and timeouts must be positive and in range")
        return cls(
            laptop_origin=origin,
            gateway_key=values["FLOW_GATEWAY_KEY"],
            telegram_bot_token=values["TELEGRAM_BOT_TOKEN"],
            telegram_chat_id=values["TELEGRAM_CHAT_ID"],
            database_path=Path(values["GATEWAY_DATABASE"]),
            bind_host=values.get("GATEWAY_BIND", "127.0.0.1"),
            bind_port=port,
            request_timeout=timeout,
            probe_interval=interval,
        )
