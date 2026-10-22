"""Bounded HTTP client for the laptop's versioned remote API."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen


class UpstreamError(RuntimeError):
    """A laptop API request failed or returned an invalid response."""


class UpstreamResponseError(UpstreamError):
    """The laptop returned an HTTP error with a structured response body."""

    def __init__(self, status: int, payload: dict[str, Any]):
        super().__init__(f"laptop API returned HTTP {status}")
        self.status = status
        self.payload = payload


class UpstreamTimeout(UpstreamError):
    """The laptop did not answer before the request deadline."""


class _NoRedirect(HTTPRedirectHandler):
    """Hand 3xx answers to the browser instead of following them (the panel redirects after every action)."""

    def redirect_request(self, *args, **kwargs):
        return None


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
        except HTTPError as exc:
            try:
                error_body = exc.read()
            except (OSError, UnicodeError):
                raise UpstreamError("laptop API returned an invalid error response") from exc
            finally:
                exc.close()
            try:
                error_payload = json.loads(error_body.decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError):
                raise UpstreamError("laptop API returned an invalid error response") from exc
            if not isinstance(error_payload, dict):
                raise UpstreamError("laptop API returned an invalid error response") from exc
            raise UpstreamResponseError(exc.code, error_payload) from exc
        except (URLError, TimeoutError, OSError, UnicodeError, json.JSONDecodeError) as exc:
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
        if path not in {"/api/remote/v1/commands", "/api/remote/v1/challenges"}:
            raise ValueError("unsupported laptop POST path")
        request = Request(self._origin + path, data=json.dumps(payload).encode("utf-8"), headers={
            "Authorization": f"Bearer {self._key}", "Accept": "application/json",
            "Content-Type": "application/json",
        }, method="POST")
        try:
            with urlopen(request, timeout=self._timeout) as response:
                status, raw = response.status, response.read().decode("utf-8")
        except HTTPError as exc:
            status = exc.code
            try:
                raw = exc.read().decode("utf-8")
            except (OSError, UnicodeError):
                raw = ""
        except TimeoutError as exc:
            raise UpstreamTimeout("laptop command timed out") from exc
        except (URLError, OSError) as exc:
            if isinstance(exc, URLError) and isinstance(exc.reason, TimeoutError):
                raise UpstreamTimeout("laptop command timed out") from exc
            raise UpstreamError("laptop command request failed") from exc
        try:
            result = json.loads(raw)
        except (json.JSONDecodeError, UnicodeError) as exc:
            raise UpstreamError("laptop command response was invalid") from exc
        if not isinstance(result, dict):
            raise UpstreamError("laptop command response was not an object")
        return status, result

    def open_panel(self, method: str, path: str, body: bytes | None = None, content_type: str | None = None,
                   timeout: float = 30.0):
        """Open a laptop panel page or action and return the live response (an HTTPError is also a response)."""
        if not path.startswith("/") or method not in {"GET", "POST"}:
            raise ValueError("unsupported panel request")
        headers = {"Authorization": f"Bearer {self._key}", "Accept": "*/*", "Accept-Encoding": "identity"}
        if content_type and body is not None:
            headers["Content-Type"] = content_type
        request = Request(self._origin + "/api/remote/v1/panel" + path, data=body, headers=headers, method=method)
        try:
            return build_opener(_NoRedirect).open(request, timeout=timeout)
        except HTTPError as exc:
            return exc
        except (URLError, TimeoutError, OSError) as exc:
            raise UpstreamError("laptop panel request failed") from exc

    def read_model(self, path: str) -> dict[str, Any]:
        from urllib.parse import urlsplit

        route = urlsplit(path)
        allowed = {"/api/remote/v1/commands", "/api/remote/v1/history", "/api/remote/v1/quotas",
                   "/api/remote/v1/routes"}
        if route.path not in allowed and not re.fullmatch(
                r"/api/remote/v1/attempts/[A-Za-z0-9._:-]{1,120}/review", route.path):
            raise ValueError("unsupported read model")
        if route.scheme or route.netloc or route.fragment:
            raise ValueError("unsupported read model")
        return self.get_json(path)
