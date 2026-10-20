"""Bounded HTTP client for the laptop's versioned remote API."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class UpstreamError(RuntimeError):
    """A laptop API request failed or returned an invalid response."""


class LaptopClient:
    def __init__(self, origin: str, gateway_key: str, timeout: float = 5.0):
        self._origin = origin.rstrip("/")
        self._key = gateway_key
        self._timeout = timeout

    def get_json(self, path: str) -> dict[str, Any]:
        if not path.startswith("/"):
            raise ValueError("upstream path must be absolute")
        request = Request(
            self._origin + path,
            headers={"Authorization": f"Bearer {self._key}", "Accept": "application/json"},
            method="GET",
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise UpstreamError("laptop API request failed") from exc
        if not isinstance(payload, dict):
            raise UpstreamError("laptop API returned a non-object response")
        return payload

    def health(self) -> dict[str, Any]:
        return self.get_json("/api/remote/v1/health")

    def snapshot(self) -> dict[str, Any]:
        return self.get_json("/api/remote/v1/snapshot")

    def events(self, after: str, limit: int = 200) -> dict[str, Any]:
        from urllib.parse import urlencode

        return self.get_json("/api/remote/v1/events?" + urlencode({"after": after, "limit": limit}))

    def command(self, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        return self.post_json("/api/remote/v1/commands", payload)

    def challenge(self, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        return self.post_json("/api/remote/v1/challenges", payload)

    def post_json(self, path: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = Request(self._origin + path, data=body, headers={
            "Authorization": f"Bearer {self._key}", "Accept": "application/json",
            "Content-Type": "application/json",
        }, method="POST")
        try:
            with urlopen(request, timeout=self._timeout) as response:
                status = response.status
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            status = exc.code
            try:
                raw = exc.read().decode("utf-8")
            except (OSError, UnicodeError):
                raw = ""
        except (URLError, TimeoutError, OSError) as exc:
            raise UpstreamError("laptop command request failed") from exc
        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise UpstreamError("laptop command response was invalid") from exc
        if not isinstance(result, dict):
            raise UpstreamError("laptop command response was not an object")
        return status, result
