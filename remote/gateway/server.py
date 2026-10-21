"""HTTP entry point for the gateway's frontend-proxied GitHub OAuth routes."""

from __future__ import annotations

import hmac
import json
import logging
import re
from typing import Any, Protocol
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from auth import (
    SESSION_COOKIE,
    STATE_COOKIE,
    AuthenticationError,
    OAuthConfig,
    OAuthService,
    SessionStore,
    cookie_values,
)
from app import CommandRelayError
from commands import CommandValidationError
from security import RateLimiter, origin_matches
from stream import SnapshotEventStream, encode_sse
from upstream import UpstreamError

logger = logging.getLogger(__name__)
RATE_WINDOW_SECONDS = 60
LOGIN_FAILURE_LIMIT = 5
COMMAND_REQUEST_LIMIT = 30


class StreamRuntime(Protocol):
    stream: SnapshotEventStream

    def submit_command(self, value: object) -> tuple[int, dict[str, Any]]: ...

    def issue_challenge(self, target: str, typed_req: str) -> dict[str, Any]: ...

    def read_model(self, path: str) -> dict[str, Any]: ...


def make_handler(service: OAuthService, runtime: StreamRuntime | None = None) -> type[BaseHTTPRequestHandler]:
    rate_limiter = RateLimiter()

    class GatewayHandler(BaseHTTPRequestHandler):
        server_version = "FlowGateway"

        def log_message(self, format: str, *args: object) -> None:
            status = str(args[0]) if args else "-"
            logger.info("gateway http client=%s method=%s path=%s status=%s",
                        self.client_address[0], self.command, urlsplit(self.path).path, status)

        def _send(self, status: int, body: bytes = b"", *, content_type: str = "text/plain; charset=utf-8",
                  headers: tuple[tuple[str, str], ...] = ()) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            for name, value in headers:
                self.send_header(name, value)
            self.end_headers()
            if body:
                self.wfile.write(body)

        def _json(self, status: int, value: dict[str, object], headers: tuple[tuple[str, str], ...] = ()) -> None:
            self._send(status, json.dumps(value).encode("utf-8"), content_type="application/json; charset=utf-8", headers=headers)

        def do_GET(self) -> None:
            route = urlsplit(self.path)
            if route.path in {"/api/auth/login", "/api/auth/github"}:
                state = service.store.create_state()
                # GitHub returns by a cross-site top-level GET, so the one-time state cookie must be Lax.
                self._send(302, headers=(
                    ("Location", service.authorization_url(state)),
                    ("Set-Cookie", f"{STATE_COOKIE}={state}; Path=/api/auth/callback; Max-Age=600; HttpOnly; Secure; SameSite=Lax"),
                ))
                return
            if route.path == "/api/auth/logout":
                self._send(302, headers=(
                    ("Location", service.config.frontend_origin + "/"),
                    ("Set-Cookie", f"{SESSION_COOKIE}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Strict"),
                ))
                return
            if route.path == "/api/auth/callback":
                client_key = self.client_address[0]
                if not rate_limiter.acquire("login", client_key, LOGIN_FAILURE_LIMIT, RATE_WINDOW_SECONDS):
                    self._rate_limited()
                    return
                if self._callback(parse_qs(route.query, keep_blank_values=True)):
                    rate_limiter.reset("login", client_key)
                return
            if route.path == "/api/auth/session":
                token = cookie_values(self.headers.get("Cookie")).get(SESSION_COOKIE, "")
                login = service.store.get_session(token) if token else None
                if login is None:
                    self._json(401, {"error": "unauthorized"})
                    return
                self._json(200, {"login": login})
                return
            read_routes = {"/api/remote/v1/snapshot", "/api/remote/v1/events", "/api/remote/v1/commands",
                           "/api/remote/v1/quotas", "/api/remote/v1/routes"}
            is_review = re.fullmatch(r"/api/remote/v1/attempts/[A-Za-z0-9._:-]{1,120}/review", route.path) is not None
            if (route.path in read_routes or is_review) and runtime is not None:
                token = cookie_values(self.headers.get("Cookie")).get(SESSION_COOKIE, "")
                if not token or service.store.get_session(token) is None:
                    self._json(401, {"error": "unauthorized"})
                    return
                if route.path == "/api/remote/v1/snapshot":
                    snapshot = runtime.stream.snapshot()
                    if snapshot is None:
                        self._json(503, {"error": "snapshot unavailable"})
                    else:
                        self._json(200, snapshot)
                    return
                if route.path == "/api/remote/v1/events":
                    self._stream_events()
                    return
                try:
                    model = runtime.read_model(route.path + ("?" + route.query if route.query else ""))
                except UpstreamError:
                    self._json(503, {"error": "read model unavailable"})
                    return
                self._json(200, model)
                return
            self._json(404, {"error": "not found"})

        def _stream_events(self) -> None:
            if runtime is None:
                self._json(404, {"error": "not found"})
                return
            try:
                last_id = runtime.stream.parse_last_event_id(self.headers.get("Last-Event-ID"))
            except ValueError:
                self._json(400, {"error": "invalid Last-Event-ID"})
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-transform")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()
            try:
                while True:
                    events = runtime.stream.wait_after(last_id, timeout=15)
                    if not events:
                        self.wfile.write(b": keep-alive\n\n")
                        self.wfile.flush()
                        continue
                    for event_id, event in events:
                        self.wfile.write(encode_sse(event_id, event))
                        self.wfile.flush()
                        last_id = event_id
            except (BrokenPipeError, ConnectionResetError, OSError):
                return

        def do_POST(self) -> None:
            if not self._valid_state_changing_request():
                self._json(403, {"error": "forbidden"})
                return
            route = urlsplit(self.path)
            if route.path == "/api/remote/v1/challenges":
                client_key = self.client_address[0]
                if not rate_limiter.acquire("commands", client_key, COMMAND_REQUEST_LIMIT, RATE_WINDOW_SECONDS):
                    self._rate_limited()
                    return
                if runtime is None:
                    self._json(404, {"error": "not found"})
                    return
                token = cookie_values(self.headers.get("Cookie")).get(SESSION_COOKIE, "")
                if not token or service.store.get_session(token) is None:
                    self._json(401, {"error": "unauthorized"})
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    self._problem(400, "INVALID_CHALLENGE", "Content-Length is invalid")
                    return
                if length <= 0:
                    self._problem(400, "INVALID_CHALLENGE", "Challenge body is required")
                    return
                if length > 65536:
                    self._problem(413, "BODY_TOO_LARGE", "Challenge body is too large")
                    return
                try:
                    value = json.loads(self.rfile.read(length).decode("utf-8"))
                except (UnicodeError, json.JSONDecodeError):
                    self._problem(400, "INVALID_CHALLENGE", "Challenge body must be valid JSON")
                    return
                if (not isinstance(value, dict) or set(value) not in ({"target", "typedReq"}, {"target", "typed_req"})
                        or not isinstance(value.get("target"), str)
                        or not isinstance(value.get("typedReq", value.get("typed_req")), str)):
                    self._problem(400, "INVALID_CHALLENGE", "Target and typedReq are required")
                    return
                try:
                    result = runtime.issue_challenge(value["target"], value.get("typedReq", value.get("typed_req")))
                except CommandValidationError as exc:
                    self._problem(exc.status, exc.code, str(exc))
                    return
                except CommandRelayError as exc:
                    self._problem(exc.status, exc.code, str(exc))
                    return
                self._json(201, result)
                return
            if route.path == "/api/remote/v1/commands":
                client_key = self.client_address[0]
                if not rate_limiter.acquire("commands", client_key, COMMAND_REQUEST_LIMIT, RATE_WINDOW_SECONDS):
                    self._rate_limited()
                    return
                if runtime is None:
                    self._json(404, {"error": "not found"})
                    return
                token = cookie_values(self.headers.get("Cookie")).get(SESSION_COOKIE, "")
                if not token or service.store.get_session(token) is None:
                    self._json(401, {"error": "unauthorized"})
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    self._problem(400, "INVALID_COMMAND", "Content-Length is invalid")
                    return
                if length <= 0:
                    self._problem(400, "INVALID_COMMAND", "Command body is required")
                    return
                if length > 65536:
                    self._problem(413, "BODY_TOO_LARGE", "Command body is too large")
                    return
                try:
                    value = json.loads(self.rfile.read(length).decode("utf-8"))
                except (UnicodeError, json.JSONDecodeError):
                    self._problem(400, "INVALID_COMMAND", "Command body must be valid JSON")
                    return
                try:
                    status, result = runtime.submit_command(value)
                except CommandValidationError as exc:
                    self._problem(exc.status, exc.code, str(exc))
                    return
                except CommandRelayError as exc:
                    self._problem(exc.status, exc.code, str(exc), idempotency_key=exc.idempotency_key)
                    return
                self._json(status, result)
                return
            self._json(404, {"error": "not found"})

        def _problem(self, status: int, code: str, message: str, *, idempotency_key: str | None = None) -> None:
            body: dict[str, object] = {"code": code, "message": message}
            if idempotency_key is not None:
                body["idempotencyKey"] = idempotency_key
            self._send(status, json.dumps(body).encode("utf-8"), content_type="application/problem+json; charset=utf-8")

        def _valid_state_changing_request(self) -> bool:
            request_marker = self.headers.get("X-Flow-Request", "").strip()
            origins = self.headers.get_all("Origin", [])
            return bool(request_marker) and len(origins) == 1 and origin_matches(origins[0], service.config.frontend_origin)

        def _rate_limited(self) -> None:
            self._json(429, {"error": "too many requests"}, headers=(("Retry-After", str(RATE_WINDOW_SECONDS)),))

        def _callback(self, query: dict[str, list[str]]) -> bool:
            values = cookie_values(self.headers.get("Cookie"))
            cookie_state = values.get(STATE_COOKIE, "")
            query_states = query.get("state", [])
            codes = query.get("code", [])
            valid_shape = len(query_states) == 1 and len(codes) == 1 and bool(codes[0])
            matches = valid_shape and bool(cookie_state) and hmac.compare_digest(cookie_state, query_states[0])
            consumed = service.store.consume_state(cookie_state) if matches else False
            if not matches or not consumed:
                self._json(400, {"error": "invalid OAuth state"}, headers=(
                    ("Set-Cookie", f"{STATE_COOKIE}=; Path=/api/auth/callback; Max-Age=0; HttpOnly; Secure; SameSite=Lax"),
                ))
                return False
            try:
                token = service.finish(codes[0])
            except AuthenticationError as exc:
                logger.info("GitHub sign-in refused: %s", str(exc))
                self._json(403, {"error": "GitHub sign-in refused"}, headers=(
                    ("Set-Cookie", f"{STATE_COOKIE}=; Path=/api/auth/callback; Max-Age=0; HttpOnly; Secure; SameSite=Lax"),
                ))
                return False
            self._send(302, headers=(
                ("Location", service.config.frontend_origin + "/"),
                ("Set-Cookie", f"{SESSION_COOKIE}={token}; Path=/; Max-Age=1209600; HttpOnly; Secure; SameSite=Strict"),
                ("Set-Cookie", f"{STATE_COOKIE}=; Path=/api/auth/callback; Max-Age=0; HttpOnly; Secure; SameSite=Lax"),
            ))
            return True

    return GatewayHandler


def create_server(config: OAuthConfig, bind_address: tuple[str, int] | None = None,
                  runtime: StreamRuntime | None = None) -> ThreadingHTTPServer:
    service = OAuthService(config, store=SessionStore(config.database_path, config.session_secret))
    return ThreadingHTTPServer(bind_address or (config.bind_host, config.bind_port), make_handler(service, runtime))


