"""GitHub OAuth authentication and server-side sessions for the remote gateway."""

from __future__ import annotations

import hmac
import json
import secrets
import sqlite3
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from http.cookies import CookieError, SimpleCookie
from typing import Any
from urllib.error import URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

STATE_COOKIE = "flow_oauth_state"
SESSION_COOKIE = "flow_session"
STATE_TTL_SECONDS = 600
SESSION_TTL_SECONDS = 60 * 60 * 24 * 14


class AuthenticationError(ValueError):
    """Raised when OAuth configuration or credentials are invalid."""


@dataclass(frozen=True)
class OAuthConfig:
    client_id: str
    client_secret: str
    session_secret: str
    frontend_origin: str
    database_path: str
    authorize_url: str = "https://github.com/login/oauth/authorize"
    token_url: str = "https://github.com/login/oauth/access_token"
    user_url: str = "https://api.github.com/user"
    bind_host: str = "127.0.0.1"
    bind_port: int = 8790

    def __post_init__(self) -> None:
        parsed = urlsplit(self.frontend_origin)
        hostname = parsed.hostname or ""
        test_http = parsed.scheme == "http" and (
            hostname in {"localhost", "127.0.0.1"} or hostname.endswith(".test")
        )
        if ((parsed.scheme != "https" and not test_http) or not parsed.netloc or parsed.path not in ("", "/")
                or parsed.query or parsed.fragment or parsed.username or parsed.password):
            raise AuthenticationError("FRONTEND_ORIGIN must be an https origin (http is allowed only for local test hosts)")
        for endpoint in (self.authorize_url, self.token_url, self.user_url):
            provider = urlsplit(endpoint)
            local_test_endpoint = provider.scheme == "http" and (
                (provider.hostname or "") in {"localhost", "127.0.0.1"} or (provider.hostname or "").endswith(".test")
            )
            if provider.scheme != "https" and not local_test_endpoint:
                raise AuthenticationError("GitHub OAuth endpoints must use https")
        if not self.client_id or not self.client_secret or len(self.session_secret) < 32:
            raise AuthenticationError("GitHub OAuth credentials and a 32-character session secret are required")
        if not 1 <= self.bind_port <= 65535:
            raise AuthenticationError("GATEWAY_PORT must be between 1 and 65535")

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> OAuthConfig:
        import os

        values = os.environ if env is None else env
        names = ("GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET", "SESSION_SECRET", "FLOW_FRONTEND_ORIGIN", "GATEWAY_DATABASE")
        missing = [name for name in names if not values.get(name, "").strip()]
        if missing:
            raise AuthenticationError("Missing required gateway authentication configuration: " + ", ".join(missing))
        try:
            bind_port = int(values.get("GATEWAY_PORT", "8790"))
        except ValueError as exc:
            raise AuthenticationError("GATEWAY_PORT must be numeric") from exc
        return cls(
            client_id=values["GITHUB_CLIENT_ID"],
            client_secret=values["GITHUB_CLIENT_SECRET"],
            session_secret=values["SESSION_SECRET"],
            frontend_origin=values["FLOW_FRONTEND_ORIGIN"].rstrip("/"),
            database_path=values["GATEWAY_DATABASE"],
            authorize_url=values.get("GITHUB_AUTHORIZE_URL", "https://github.com/login/oauth/authorize"),
            token_url=values.get("GITHUB_TOKEN_URL", "https://github.com/login/oauth/access_token"),
            user_url=values.get("GITHUB_USER_URL", "https://api.github.com/user"),
            bind_host=values.get("GATEWAY_BIND", "127.0.0.1"),
            bind_port=bind_port,
        )


def _digest(value: str, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), value.encode("utf-8"), "sha256").hexdigest()


class SessionStore:
    """Persist only hashes of opaque session and OAuth state tokens."""

    def __init__(self, database_path: str, secret: str):
        self.database_path = database_path
        self.secret = secret
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS oauth_states (token_hash TEXT PRIMARY KEY, expires_at INTEGER NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, login TEXT NOT NULL, expires_at INTEGER NOT NULL)")

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.database_path, timeout=5)
        try:
            db.execute("PRAGMA journal_mode=WAL")
            yield db
            db.commit()
        finally:
            db.close()

    def create_state(self, now: int | None = None) -> str:
        token = secrets.token_urlsafe(32)
        timestamp = int(time.time()) if now is None else now
        with self._connect() as db:
            db.execute("DELETE FROM oauth_states WHERE expires_at <= ?", (timestamp,))
            db.execute("INSERT INTO oauth_states(token_hash, expires_at) VALUES (?, ?)", (_digest(token, self.secret), timestamp + STATE_TTL_SECONDS))
        return token

    def consume_state(self, token: str, now: int | None = None) -> bool:
        timestamp = int(time.time()) if now is None else now
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT expires_at FROM oauth_states WHERE token_hash = ?", (_digest(token, self.secret),)).fetchone()
            db.execute("DELETE FROM oauth_states WHERE token_hash = ?", (_digest(token, self.secret),))
            return bool(row and row[0] > timestamp)

    def create_session(self, login: str, now: int | None = None) -> str:
        token = secrets.token_urlsafe(32)
        timestamp = int(time.time()) if now is None else now
        with self._connect() as db:
            db.execute("INSERT INTO sessions(token_hash, login, expires_at) VALUES (?, ?, ?)",
                       (_digest(token, self.secret), login, timestamp + SESSION_TTL_SECONDS))
        return token

    def delete_session(self, token: str) -> None:
        with self._connect() as db:
            db.execute("DELETE FROM sessions WHERE token_hash = ?", (_digest(token, self.secret),))

    def get_session(self, token: str, now: int | None = None) -> str | None:
        timestamp = int(time.time()) if now is None else now
        with self._connect() as db:
            row = db.execute("SELECT login, expires_at FROM sessions WHERE token_hash = ?", (_digest(token, self.secret),)).fetchone()
            if row is None or row[1] <= timestamp:
                db.execute("DELETE FROM sessions WHERE token_hash = ?", (_digest(token, self.secret),))
                return None
            return str(row[0])


def _request_json(url: str, *, method: str = "GET", data: dict[str, str] | None = None,
                  headers: dict[str, str] | None = None) -> dict[str, Any]:
    body = urlencode(data).encode("ascii") if data is not None else None
    request = Request(url, data=body, method=method, headers={
        "Accept": "application/json",
        "User-Agent": "flow-remote-gateway",
        **(headers or {}),
        **({"Content-Type": "application/x-www-form-urlencoded"} if body else {}),
    })
    try:
        with urlopen(request, timeout=10) as response:
            payload: object = json.loads(response.read(65536))
    except (URLError, TimeoutError, ValueError) as exc:
        raise AuthenticationError("GitHub authentication provider is unavailable") from exc
    if not isinstance(payload, dict):
        raise AuthenticationError("GitHub returned an invalid response")
    return payload


class OAuthService:
    def __init__(self, config: OAuthConfig, store: SessionStore | None = None,
                 provider_request: Callable[..., dict[str, Any]] = _request_json):
        self.config = config
        self.store = store or SessionStore(config.database_path, config.session_secret)
        self.provider_request = provider_request
        self.callback_url = config.frontend_origin + "/api/auth/callback"

    def authorization_url(self, state: str) -> str:
        query = urlencode({"client_id": self.config.client_id, "redirect_uri": self.callback_url,
                           "state": state, "scope": "read:user"})
        return self.config.authorize_url + ("&" if "?" in self.config.authorize_url else "?") + query

    def finish(self, code: str) -> str:
        token_response = self.provider_request(self.config.token_url, method="POST", data={
            "client_id": self.config.client_id, "client_secret": self.config.client_secret, "code": code,
            "redirect_uri": self.callback_url,
        })
        access_token = token_response.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise AuthenticationError("GitHub did not authorize this sign-in")
        user_response = self.provider_request(self.config.user_url, headers={"Authorization": f"Bearer {access_token}"})
        login = user_response.get("login")
        if not isinstance(login, str) or login.casefold() != "dav033":
            raise AuthenticationError("This GitHub account is not allowed")
        return self.store.create_session("dav033")


def cookie_values(header: str | None) -> dict[str, str]:
    cookie = SimpleCookie()
    if header:
        try:
            cookie.load(header)
        except CookieError:
            return {}
    return {name: morsel.value for name, morsel in cookie.items()}
