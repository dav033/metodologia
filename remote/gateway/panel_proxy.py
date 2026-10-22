"""Authenticated relay of the laptop panel's pages and actions through the gateway.

The Vercel frontend rewrites the panel's own URLs (`/p/...`, `/flow`, `/metrics`, ...) to this gateway, so the panel
keeps working with root-relative links. Every request needs the `dav033` session; every write also needs the
`X-Flow-Request` header, the frontend Origin, and a typed confirmation bound to that exact request. The laptop
decides what is reachable (allow-list in `bt_remote_panel`); this module only forwards, redacts and relays.
"""

from __future__ import annotations

import hashlib
import re
import secrets
import threading
import time
from typing import Any
from urllib.parse import urlsplit

from auth import SESSION_COOKIE, cookie_values
from upstream import UpstreamError

PANEL_ROOT_ALIAS = "/__panel_root"
SHIM_PATH = "/__panel/shim.js"
_TOP = {"p", "plans", "events", "now", "flow", "metrics", "learnings", "static", "live", "go"}
_API = {"now", "simulate", "flow", "plans"}
CONFIRM_TEXT = "CONFIRMAR"
CHALLENGE_SECONDS = 120
MAX_REQUEST_BODY = 1024 * 1024
MAX_RESPONSE_BODY = 20 * 1024 * 1024
GET_LIMIT = 1200
POST_LIMIT = 30
RATE_WINDOW = 60
_RELAY_HEADERS = ("Content-Type", "Content-Disposition", "Location", "Content-Security-Policy", "Last-Modified")
_REDACTABLE = ("text/html", "text/plain", "text/markdown", "application/json", "text/x-markdown")
_REDACTIONS = (
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S), "[redacted private key]"),
    (re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{30,}\b"), "[redacted token]"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"), "[redacted token]"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{50,}\b"), "[redacted token]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"), "[redacted token]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[redacted key]"),
    (re.compile(r"\b([A-Z][A-Z0-9_]*(?:SECRET|TOKEN|PASSWORD|API_KEY|PRIVATE_KEY)[A-Z0-9_]*)=([^\s\"'<>&]+)"),
     r"\1=[redacted]"),
)

SHIM = r"""(function () {
  'use strict';
  var nativeFetch = window.fetch.bind(window);
  function confirmText(action) {
    return window.prompt('Acción: ' + action + '\nEscribe ' + '%(confirm)s' + ' para ejecutarla.') || '';
  }
  async function send(url, init) {
    init = Object.assign({}, init);
    init.headers = new Headers(init.headers || {});
    init.headers.set('X-Flow-Request', '1');
    init.credentials = 'same-origin';
    var response = await nativeFetch(url, init);
    if (response.status !== 428) return response;
    var info = await response.json();
    var typed = confirmText(info.action || '');
    if (typed !== '%(confirm)s') return new Response('{"error":"cancelled"}', { status: 499 });
    init.headers.set('X-Flow-Challenge', info.challenge);
    init.headers.set('X-Flow-Typed', typed);
    return nativeFetch(url, init);
  }
  window.fetch = function (input, init) {
    init = init || {};
    var method = String(init.method || (input && input.method) || 'GET').toUpperCase();
    return method === 'POST' ? send(input, init) : nativeFetch(input, init);
  };
  document.addEventListener('submit', function (event) {
    var form = event.target;
    if (String(form.method || 'get').toLowerCase() !== 'post') return;
    event.preventDefault();
    var data = new URLSearchParams(new FormData(form, event.submitter || undefined));
    send(form.action || location.href, {
      method: 'POST', body: data, headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }).then(function (response) {
      if (response.status === 499) return;
      if (response.ok || response.redirected) { location.assign(response.url); return; }
      response.text().then(function (html) { document.open(); document.write(html); document.close(); });
    });
  }, true);
  document.addEventListener('DOMContentLoaded', function () {
    var link = document.createElement('a');
    link.href = '/remote'; link.textContent = 'Remoto'; link.setAttribute('aria-label', 'Control remoto');
    link.style.cssText = 'position:fixed;right:12px;bottom:12px;z-index:99999;min-height:44px;display:flex;' +
      'align-items:center;padding:0 16px;border-radius:999px;background:#cba6f7;color:#11111b;' +
      'font:600 14px system-ui,sans-serif;text-decoration:none';
    document.body.appendChild(link);
  });
})();
""" % {"confirm": CONFIRM_TEXT}


def redact(text: str) -> str:
    for pattern, replacement in _REDACTIONS:
        text = pattern.sub(replacement, text)
    return text


def upstream_path(path: str) -> str | None:
    """The laptop panel path for a gateway path, or None when it is not part of the panel."""
    if path == "/" or path == PANEL_ROOT_ALIAS:
        return "/"
    parts = [part for part in path.split("/") if part]
    if not parts:
        return None
    if parts[0] in _TOP or (parts[0] == "api" and len(parts) >= 2 and parts[1] in _API):
        return path
    return None


class Challenges:
    """Single-use typed confirmations bound to the session, the method, the URL and the exact body."""

    def __init__(self, clock=time.monotonic, limit: int = 256) -> None:
        self._clock, self._limit = clock, limit
        self._items: dict[str, tuple[str, str, str, str, float]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _bind(token: str, method: str, target: str, body: bytes) -> tuple[str, str, str, str]:
        return (hashlib.sha256(token.encode()).hexdigest(), method, target, hashlib.sha256(body).hexdigest())

    def issue(self, token: str, method: str, target: str, body: bytes) -> str:
        now = self._clock()
        with self._lock:
            for key in [k for k, v in self._items.items() if v[4] <= now]:
                del self._items[key]
            if len(self._items) >= self._limit:
                del self._items[min(self._items, key=lambda k: self._items[k][4])]
            ident = secrets.token_urlsafe(18)
            self._items[ident] = (*self._bind(token, method, target, body), now + CHALLENGE_SECONDS)
            return ident

    def consume(self, ident: str, token: str, method: str, target: str, body: bytes) -> bool:
        with self._lock:
            item = self._items.pop(ident, None)
        return (item is not None and item[4] > self._clock()
                and item[:4] == self._bind(token, method, target, body))


def _owner(handler, service) -> tuple[str, str] | None:
    token = cookie_values(handler.headers.get("Cookie")).get(SESSION_COOKIE, "")
    login = service.store.get_session(token) if token else None
    return (token, login) if login else None


def _unauthorized(handler) -> None:
    if "text/html" in handler.headers.get("Accept", ""):
        handler._send(302, headers=(("Location", "/api/auth/login"),))
    else:
        handler._json(401, {"error": "unauthorized"})


def handle(handler, service, runtime, rate_limiter, challenges: Challenges, method: str, route) -> bool:
    """Serve a panel route and return True, or return False when the URL is not a panel URL."""
    if route.path == SHIM_PATH and method == "GET":
        handler._send(200, SHIM.encode("utf-8"), content_type="application/javascript; charset=utf-8")
        return True
    target_path = upstream_path(route.path)
    if target_path is None:
        return False
    owner = _owner(handler, service)
    if owner is None:
        _unauthorized(handler)
        return True
    token, login = owner
    if runtime is None:
        handler._json(503, {"code": "LAPTOP_UNAVAILABLE"})
        return True
    scope, limit = ("panel-get", GET_LIMIT) if method == "GET" else ("panel-post", POST_LIMIT)
    if not rate_limiter.acquire(scope, login, limit, RATE_WINDOW):
        handler._rate_limited()
        return True
    target = target_path + ("?" + route.query if route.query else "")
    body = b""
    if method == "POST":
        try:
            length = int(handler.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1
        if length < 0 or length > MAX_REQUEST_BODY:
            handler._json(413 if length > 0 else 400, {"code": "INVALID_BODY"})
            return True
        body = handler.rfile.read(length) if length else b""
        ident, typed = handler.headers.get("X-Flow-Challenge", ""), handler.headers.get("X-Flow-Typed", "")
        if not ident or typed != CONFIRM_TEXT or not challenges.consume(ident, token, method, target, body):
            handler._json(428, {"code": "CONFIRMATION_REQUIRED", "action": route.path,
                                "challenge": challenges.issue(token, method, target, body)})
            return True
    try:
        response = runtime.laptop.open_panel(method, target, body or None, handler.headers.get("Content-Type"))
    except UpstreamError:
        handler._json(503, {"code": "LAPTOP_OFFLINE"})
        return True
    try:
        _relay(handler, response, route.path)
    finally:
        response.close()
    return True


def _relay(handler, response: Any, path: str) -> None:
    status = getattr(response, "status", None) or response.code
    headers = response.headers
    content_type = headers.get("Content-Type", "application/octet-stream")
    out = [(name, headers[name]) for name in _RELAY_HEADERS if headers.get(name)]
    out += [("X-Content-Type-Options", "nosniff"), ("Referrer-Policy", "no-referrer")]
    if "text/event-stream" in content_type:
        handler.send_response(status)
        for name, value in out:
            handler.send_header(name, value)
        handler.send_header("Cache-Control", "no-store")
        handler.send_header("Connection", "close")
        handler.end_headers()
        handler.close_connection = True
        try:
            while True:
                chunk = response.readline()
                if not chunk:
                    break
                handler.wfile.write(chunk)
                if chunk in (b"\n", b"\r\n"):
                    handler.wfile.flush()
        except OSError:
            pass
        return
    body = response.read(MAX_RESPONSE_BODY + 1)
    if len(body) > MAX_RESPONSE_BODY:
        handler._json(502, {"code": "RESPONSE_TOO_LARGE"})
        return
    kind = content_type.split(";")[0].strip().lower()
    if kind in _REDACTABLE:
        text = redact(body.decode("utf-8", errors="replace"))
        if kind == "text/html" and not headers.get("Content-Security-Policy") and "<head" in text.lower():
            tag = f'<script src="{SHIM_PATH}"></script>'
            text = re.sub(r"(?i)</head>", tag + "</head>", text, count=1) if re.search(r"(?i)</head>", text) \
                else re.sub(r"(?i)(<head[^>]*>)", r"\1" + tag, text, count=1)
            out.append(("X-Frame-Options", "SAMEORIGIN"))
        body = text.encode("utf-8")
    handler._send(status, body, content_type=content_type,
                  headers=tuple((n, v) for n, v in out if n.lower() != "content-type"))
