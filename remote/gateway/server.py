"""HTTP entry point for the gateway's frontend-proxied GitHub OAuth routes."""

from __future__ import annotations

import hmac
import json
import logging
import time
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
from security import RateLimiter, origin_matches

logger = logging.getLogger(__name__)
RATE_WINDOW_SECONDS = 60
LOGIN_FAILURE_LIMIT = 5
COMMAND_REQUEST_LIMIT = 30


def make_handler(service: OAuthService, runtime=None) -> type[BaseHTTPRequestHandler]:
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
            if route.path == "/api/auth/login":
                state = service.store.create_state()
                # GitHub returns by a cross-site top-level GET, so the one-time state cookie must be Lax.
                self._send(302, headers=(
                    ("Location", service.authorization_url(state)),
                    ("Set-Cookie", f"{STATE_COOKIE}={state}; Path=/api/auth/callback; Max-Age=600; HttpOnly; Secure; SameSite=Lax"),
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
                login = self._session_login()
                if login is None:
                    self._json(401, {"error": "unauthorized"})
                    return
                self._json(200, {"login": login})
                return
            if route.path in {"/api/remote/v1/snapshot", "/api/remote/v1/runs", "/api/remote/v1/plans"}:
                if self._session_login() is None:
                    self._json(401, {"error": "unauthorized"})
                    return
                snapshot = runtime.cached_snapshot() if runtime is not None else None
                if snapshot is None:
                    self._json(503, {"error": "snapshot unavailable"})
                    return
                if route.path.endswith("/runs"):
                    self._json(200, {"runs": snapshot.get("runs", []), "generatedAt": snapshot.get("generatedAt"),
                                    "cachedAt": snapshot.get("cachedAt"), "laptopStatus": snapshot.get("laptopStatus")})
                    return
                if route.path.endswith("/plans"):
                    self._json(200, {"plans": snapshot.get("plans", []), "generatedAt": snapshot.get("generatedAt"),
                                    "cachedAt": snapshot.get("cachedAt"), "laptopStatus": snapshot.get("laptopStatus")})
                    return
                self._json(200, snapshot)
                return
            if route.path in {"/api/remote/v1/events", "/api/remote/v1/stream"}:
                if self._session_login() is None:
                    self._json(401, {"error": "unauthorized"})
                    return
                if runtime is None:
                    self._json(503, {"error": "event stream unavailable"})
                    return
                self._stream(runtime)
                return
            self._json(404, {"error": "not found"})

        def do_POST(self) -> None:
            if not self._valid_state_changing_request():
                self._json(403, {"error": "forbidden"})
                return
            route = urlsplit(self.path)
            if route.path in {"/api/remote/v1/commands", "/api/remote/v1/challenges"}:
                client_key = self.client_address[0]
                if not rate_limiter.acquire("commands", client_key, COMMAND_REQUEST_LIMIT, RATE_WINDOW_SECONDS):
                    self._rate_limited()
                    return
                if self._session_login() is None:
                    self._json(401, {"error": "unauthorized"})
                    return
                if runtime is None:
                    self._json(503, {"code": "UNKNOWN_OUTCOME", "message": "Command relay unavailable"})
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    length = -1
                if length < 0:
                    self._json(400, {"error": "invalid request body"})
                    return
                if length > 256 * 1024:
                    self._json(413, {"error": "request body too large"})
                    return
                try:
                    command = json.loads(self.rfile.read(length))
                except (UnicodeError, json.JSONDecodeError):
                    self._json(400, {"error": "invalid request body"})
                    return
                if not isinstance(command, dict):
                    self._json(400, {"error": "invalid request body"})
                    return
                if route.path.endswith("/challenges"):
                    status, result = runtime.relay_challenge(command)
                else:
                    status, result = runtime.relay_command(command)
                self._json(status, result)
                return
            self._json(404, {"error": "not found"})

        def _valid_state_changing_request(self) -> bool:
            request_marker = self.headers.get("X-Flow-Request", "").strip()
            origins = self.headers.get_all("Origin", [])
            return request_marker == "1" and len(origins) == 1 and origin_matches(origins[0], service.config.frontend_origin)

        def _session_login(self) -> str | None:
            token = cookie_values(self.headers.get("Cookie")).get(SESSION_COOKIE, "")
            return service.store.get_session(token) if token else None

        def _stream(self, runtime) -> None:
            last_event_id = self.headers.get("Last-Event-ID", "").strip()
            if last_event_id and (not last_event_id.isdigit() or len(last_event_id) > 18):
                self._json(400, {"error": "invalid Last-Event-ID"})
                return
            cursor = int(last_event_id) if last_event_id else runtime.stream_position()
            replay, current, expired = runtime.events_after(cursor)
            if expired or cursor > current:
                self._json(409, {"error": "event cursor expired"})
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Accel-Buffering", "no")
            self.send_header("Connection", "close")
            self.end_headers()
            self.close_connection = True
            try:
                self.wfile.write(b"retry: 2000\n: connected\n\n")
                for sequence, event in replay:
                    self._write_event(sequence, event)
                    cursor = sequence
                self.wfile.flush()
                last_beat = time.monotonic()
                while True:
                    runtime.wait_for_events(cursor, 15.0)
                    events, current, expired = runtime.events_after(cursor)
                    if expired:
                        self.wfile.write(f"id: {current}\nevent: reset\ndata: {{}}\n\n".encode("ascii"))
                        self.wfile.flush()
                        return
                    for sequence, event in events:
                        self._write_event(sequence, event)
                        cursor = sequence
                    if events:
                        self.wfile.flush()
                        last_beat = time.monotonic()
                    elif time.monotonic() - last_beat >= 15:
                        self.wfile.write(b": keepalive\n\n")
                        self.wfile.flush()
                        last_beat = time.monotonic()
            except (BrokenPipeError, ConnectionResetError, OSError, ValueError):
                return

        def _write_event(self, sequence: int, event: dict[str, object]) -> None:
            payload = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
            self.wfile.write(f"id: {sequence}\nevent: flow\ndata: {payload}\n\n".encode("utf-8"))

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


def create_server(config: OAuthConfig, bind_address: tuple[str, int] | None = None, runtime=None) -> ThreadingHTTPServer:
    service = OAuthService(config, store=SessionStore(config.database_path, config.session_secret))
    return ThreadingHTTPServer(bind_address or (config.bind_host, config.bind_port), make_handler(service, runtime))


