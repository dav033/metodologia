"""Bounded HTTP client for the laptop's versioned remote API."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class UpstreamError(RuntimeError):
    """A laptop API request failed or returned an invalid response."""


class UpstreamTimeout(UpstreamError):
    """The request timed out, so the laptop may already have applied it."""


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
<<<<<<< a82720ecf6dc19a4b38cdab385315351a90c5c52
        except (HTTPError, URLError, TimeoutError, OSError, UnicodeError, json.JSONDecodeError) as exc:
||||||| 7bbf41f3848b323c12af604ffeb9255ba1e71e8e
<<<<<<< fdc224e41c20baaf18251239055e505699e9db6a
        except (HTTPError, URLError, TimeoutError, OSError, UnicodeError, json.JSONDecodeError) as exc:
||||||| abc942f14b9a0fa0d84e36f8efa479328584534c
<<<<<<< f05f8fd659ac343b89d326952a27e078aab647c1
        except (HTTPError, URLError, TimeoutError, OSError, UnicodeError, json.JSONDecodeError) as exc:
||||||| bb8d45c1c426152ebc0ce48c79c6b29d739fa631
        except HTTPError as exc:
            try:
                error_payload = json.loads(exc.read().decode("utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                raise UpstreamError("laptop API returned an invalid error response") from exc
            if not isinstance(error_payload, dict):
                raise UpstreamError("laptop API returned an invalid error response") from exc
            raise UpstreamResponseError(exc.code, error_payload) from exc
        except (URLError, TimeoutError, OSError, UnicodeError, json.JSONDecodeError) as exc:
=======
        except HTTPError as exc:
            try:
                error_body = exc.read()
            except (OSError, UnicodeError, json.JSONDecodeError):
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
>>>>>>> 7d0156fc3acf8afdbcdf78e19160f8fd15f17368
=======
        except HTTPError as exc:
            try:
                error_body = exc.read()
            except (OSError, UnicodeError, json.JSONDecodeError):
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
>>>>>>> d58d5211dfbc3de3567c96dfad21cbe074ff5303
=======
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
>>>>>>> 2aa3a1885b93515f6a7eaa307a9fb85ab1f1392a
            raise UpstreamError("laptop API request failed") from exc
        if not isinstance(payload, dict):
            raise UpstreamError("laptop API returned a non-object response")
        return payload

    def post_json(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        if path not in {"/api/remote/v1/commands", "/api/remote/v1/challenges"}:
            raise ValueError("unsupported upstream command path")
        request = Request(
            self._origin + path,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"Authorization": f"Bearer {self._key}", "Accept": "application/json",
                     "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            try:
                payload = json.loads(exc.read().decode("utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                raise UpstreamError("laptop API returned an invalid error response") from exc
        except (TimeoutError, OSError) as exc:
            raise UpstreamTimeout("laptop command outcome is unknown") from exc
        except (URLError, UnicodeError, json.JSONDecodeError) as exc:
            if isinstance(exc, URLError) and isinstance(exc.reason, TimeoutError):
                raise UpstreamTimeout("laptop command outcome is unknown") from exc
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
