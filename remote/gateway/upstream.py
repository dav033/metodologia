"""Bounded HTTP client for the laptop's versioned remote API."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class UpstreamError(RuntimeError):
    """A laptop API request failed or returned an invalid response."""


class UpstreamTimeout(UpstreamError):
    """The laptop did not answer before the request deadline."""


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
<<<<<<< 14d58bc9524f2bf106fdced44f4911eaa5c56677
        except (HTTPError, URLError, TimeoutError, OSError, UnicodeError, json.JSONDecodeError) as exc:
||||||| 7bba8ac713838352e950bd4df154258000ccecdb
<<<<<<< bfa41a71c3071e38a990cad13eb732a5ba9e52a5
        except (HTTPError, URLError, TimeoutError, OSError, UnicodeError, json.JSONDecodeError) as exc:
||||||| 2bedcb11d2d5783266fb3a9f9602d8bf82e99a3f
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
>>>>>>> 3023898c06ce29d14d9ab50f11757fe675920e9d
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
>>>>>>> fbac3dfc2e7826e15e9d91fb2d7f58b33d3b5c1f
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
<<<<<<< 14d58bc9524f2bf106fdced44f4911eaa5c56677
||||||| 7bba8ac713838352e950bd4df154258000ccecdb
||||||| 2bedcb11d2d5783266fb3a9f9602d8bf82e99a3f
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
>>>>>>> 3023898c06ce29d14d9ab50f11757fe675920e9d
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
>>>>>>> fbac3dfc2e7826e15e9d91fb2d7f58b33d3b5c1f
