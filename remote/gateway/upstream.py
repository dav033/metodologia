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
        except (HTTPError, URLError, TimeoutError, OSError, UnicodeError, json.JSONDecodeError) as exc:
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
<<<<<<< 0c2b75045d1c088b366d290e1236f82a6204b982
||||||| dc60481f471192cacb7e098604adb9e83f6ca85a
<<<<<<< b21af576095cc9c033b3326647f1e1a84fb3152f
||||||| d59402f2311e71a7d7b249554f3f9507983622f2
<<<<<<< 725ff33443950b7b5e0842d1366bc81f05c1a57c
||||||| 788d3dd30328bfccc7880c00baf691d188b0b6ed
<<<<<<< c0a5e47ed090adf0bb7ad5ad7bdf2c67e37ce775
||||||| 03ca13926945e4dcf4ecdc4e34dddc55b76da7e1

    def challenge(self, challenge: dict[str, Any]) -> dict[str, Any]:
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
                payload = json.loads(response.read(65536).decode("utf-8"))
        except HTTPError as exc:
            try:
                payload = json.loads(exc.read(65536).decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError) as parse_error:
                raise UpstreamError("laptop API returned an invalid challenge response") from parse_error
            if not isinstance(payload, dict):
                raise UpstreamError("laptop API returned an invalid challenge response") from exc
            raise UpstreamResponseError(exc.code, payload) from exc
        except (URLError, TimeoutError, OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise UpstreamError("laptop challenge request failed") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("challengeId"), str):
            raise UpstreamError("laptop API returned an invalid challenge response")
        return payload

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
=======

    def read_model(self, path: str) -> dict[str, Any]:
        from urllib.parse import urlsplit

        route = urlsplit(path)
        allowed = {"/api/remote/v1/commands", "/api/remote/v1/quotas", "/api/remote/v1/routes"}
        if route.path not in allowed and not re.fullmatch(
                r"/api/remote/v1/attempts/[A-Za-z0-9._:-]{1,120}/review", route.path):
            raise ValueError("unsupported read model")
        if route.scheme or route.netloc or route.fragment:
            raise ValueError("unsupported read model")
        return self.get_json(path)

    def challenge(self, challenge: dict[str, Any]) -> dict[str, Any]:
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
                payload = json.loads(response.read(65536).decode("utf-8"))
        except HTTPError as exc:
            try:
                payload = json.loads(exc.read(65536).decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError) as parse_error:
                raise UpstreamError("laptop API returned an invalid challenge response") from parse_error
            if not isinstance(payload, dict):
                raise UpstreamError("laptop API returned an invalid challenge response") from exc
            raise UpstreamResponseError(exc.code, payload) from exc
        except (URLError, TimeoutError, OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise UpstreamError("laptop challenge request failed") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("challengeId"), str):
            raise UpstreamError("laptop API returned an invalid challenge response")
        return payload

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
>>>>>>> ede87253b5f40c74d13b25da89f0c8ea70ac0e63
=======

    def read_model(self, path: str) -> dict[str, Any]:
        from urllib.parse import urlsplit

        route = urlsplit(path)
        allowed = {"/api/remote/v1/commands", "/api/remote/v1/quotas", "/api/remote/v1/routes"}
        if route.path not in allowed and not re.fullmatch(
                r"/api/remote/v1/attempts/[A-Za-z0-9._:-]{1,120}/review", route.path):
            raise ValueError("unsupported read model")
        if route.scheme or route.netloc or route.fragment:
            raise ValueError("unsupported read model")
        return self.get_json(path)

    def challenge(self, challenge: dict[str, Any]) -> dict[str, Any]:
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
                payload = json.loads(response.read(65536).decode("utf-8"))
        except HTTPError as exc:
            try:
                payload = json.loads(exc.read(65536).decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError) as parse_error:
                raise UpstreamError("laptop API returned an invalid challenge response") from parse_error
            if not isinstance(payload, dict):
                raise UpstreamError("laptop API returned an invalid challenge response") from exc
            raise UpstreamResponseError(exc.code, payload) from exc
        except (URLError, TimeoutError, OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise UpstreamError("laptop challenge request failed") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("challengeId"), str):
            raise UpstreamError("laptop API returned an invalid challenge response")
        return payload

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
>>>>>>> 7bab8d3fc65eb4681168829156ff0d7510a656a6
=======

    def read_model(self, path: str) -> dict[str, Any]:
        from urllib.parse import urlsplit

        route = urlsplit(path)
        allowed = {"/api/remote/v1/commands", "/api/remote/v1/quotas", "/api/remote/v1/routes"}
        if route.path not in allowed and not re.fullmatch(
                r"/api/remote/v1/attempts/[A-Za-z0-9._:-]{1,120}/review", route.path):
            raise ValueError("unsupported read model")
        if route.scheme or route.netloc or route.fragment:
            raise ValueError("unsupported read model")
        return self.get_json(path)
>>>>>>> ff6d46bc29f4b6a862628af4bad381b77e5a9d7a
=======

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
>>>>>>> 4714cf64fe4c866730eb7ff2dc4f69bf7c4a5603
