"""Bounded HTTP client for the laptop's versioned remote API."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class UpstreamError(RuntimeError):
    """A laptop API request failed or returned an invalid response."""


class UpstreamTimeout(UpstreamError):
    """The command request timed out after it may have reached the laptop."""


class UpstreamResponseError(UpstreamError):
    def __init__(self, status: int, payload: dict[str, Any]):
        super().__init__("laptop API rejected the command")
        self.status = status
        self.payload = payload


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

    def read_model(self, path: str) -> dict[str, Any]:
        from urllib.parse import urlsplit

        route = urlsplit(path)
        allowed = {"/api/remote/v1/history", "/api/remote/v1/commands", "/api/remote/v1/quotas"}
        if route.path not in allowed and not route.path.startswith("/api/remote/v1/attempts/") \
                and route.path != "/api/remote/v1/routes":
            raise ValueError("unsupported read model")
        return self.get_json(path)

    def command(self, command: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        body = json.dumps(command).encode("utf-8")
        request = Request(
            self._origin + "/api/remote/v1/commands",
            data=body,
            headers={
                "Authorization": f"Bearer {self._key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:
                status = response.status
                payload = json.loads(response.read(65536).decode("utf-8"))
        except HTTPError as exc:
            try:
                payload = json.loads(exc.read(65536).decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError):
                raise UpstreamError("laptop API returned an invalid command response") from exc
            status = exc.code
        except TimeoutError as exc:
            raise UpstreamTimeout("laptop command outcome is unknown") from exc
        except (URLError, OSError, UnicodeError, json.JSONDecodeError) as exc:
            if isinstance(exc, URLError) and isinstance(exc.reason, TimeoutError):
                raise UpstreamTimeout("laptop command outcome is unknown") from exc
            raise UpstreamError("laptop API request failed") from exc
        if not isinstance(payload, dict):
            raise UpstreamError("laptop API returned a non-object command response")
        if status >= 400:
            raise UpstreamResponseError(status, payload)
        return status, payload

    def issue_challenge(self, challenge: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        body = json.dumps(challenge).encode("utf-8")
        request = Request(
            self._origin + "/api/remote/v1/challenges",
            data=body,
            headers={
                "Authorization": f"Bearer {self._key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:
                status = response.status
                payload = json.loads(response.read(65536).decode("utf-8"))
        except HTTPError as exc:
            try:
                payload = json.loads(exc.read(65536).decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError) as parse_exc:
                raise UpstreamError("laptop API returned an invalid challenge response") from parse_exc
            status = exc.code
        except TimeoutError as exc:
            raise UpstreamTimeout("laptop challenge outcome is unknown") from exc
        except (URLError, OSError, UnicodeError, json.JSONDecodeError) as exc:
            if isinstance(exc, URLError) and isinstance(exc.reason, TimeoutError):
                raise UpstreamTimeout("laptop challenge outcome is unknown") from exc
            raise UpstreamError("laptop API request failed") from exc
        if not isinstance(payload, dict):
            raise UpstreamError("laptop API returned a non-object challenge response")
        if status >= 400:
            raise UpstreamResponseError(status, payload)
        return status, payload
