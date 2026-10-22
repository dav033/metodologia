"""Serve the browser panel's pages and actions through the remote listener (gateway key + allow-list).

The remote listener is the only thing the gateway can reach. This module lets it run the panel's own route
handlers in process for an explicit inventory of GET pages and POST actions, so the production site shows and does
what the local panel shows and does, without forwarding the panel port itself. Everything else is a 404.
"""
from __future__ import annotations

import json
import re
import time
from urllib.parse import urlparse

PANEL_PREFIX = "/api/remote/v1/panel"
_ID = r"[^/]+"

# Inventory of the panel's GET routes (bt_server.route_get). tests/test_remote_panel.py fails when a top-level
# route of the panel is missing here, so a new page cannot ship without its production counterpart.
GET_ROUTES = (
    r"/", r"/metrics", r"/metrics/model/.+", r"/live", r"/learnings", r"/flow", r"/flow/review", r"/now",
    r"/plans", rf"/plans/{_ID}/{_ID}", r"/events",
    r"/api/now", r"/api/simulate", r"/api/flow", r"/api/flow/agent", r"/api/flow/runs",
    r"/api/plans", rf"/api/plans/{_ID}/{_ID}",
    r"/static/.+", r"/go/.+",
    rf"/p/{_ID}", rf"/p/{_ID}/doc/.+\.md", rf"/p/{_ID}/artifacts/.+", rf"/p/{_ID}/view/.+",
    rf"/p/{_ID}/graph", rf"/p/{_ID}/req/{_ID}",
)
# Inventory of the panel's POST actions (bt_server.route_post, plans_post).
POST_ROUTES = (
    r"/api/flow/decision", r"/api/flow/diagnose",
    rf"/plans/{_ID}/restore", rf"/plans/{_ID}/{_ID}/[A-Za-z_-]+",
    rf"/p/{_ID}/req/{_ID}/(?:answer|review|run|plan)",
)
_GET = [re.compile(pattern + r"\Z") for pattern in GET_ROUTES]
_POST = [re.compile(pattern + r"\Z") for pattern in POST_ROUTES]
_FORBIDDEN_RAW = re.compile(r"%2f|%5c|%00|%2e%2e|\\|\x00", re.IGNORECASE)
MAX_POST_BODY = 1024 * 1024


def inner_path(path: str) -> str | None:
    """The panel path carried by a remote path, or None when it is not under the panel prefix."""
    if path == PANEL_PREFIX:
        return "/"
    if path.startswith(PANEL_PREFIX + "/"):
        return path[len(PANEL_PREFIX):]
    return None


def allowed(method: str, path: str) -> bool:
    if _FORBIDDEN_RAW.search(path) or any(seg in ("..", ".") for seg in path.split("/")):
        return False
    routes = _GET if method == "GET" else _POST if method == "POST" else []
    return any(route.match(path) for route in routes)


def _audit(handler, path: str) -> None:
    """Append one line per panel action (never the body) so every remote write leaves a trace on the laptop."""
    try:
        import bt_server

        bt_server.STATE.mkdir(parents=True, exist_ok=True)
        row = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "method": "POST", "path": path,
               "via": "remote-panel"}
        with (bt_server.STATE / "remote-panel-audit.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass


def serve(handler, method: str) -> None:
    """Run the panel handler for an allow-listed panel route; the caller already checked the gateway key."""
    from bt_server import Handler

    parsed = urlparse(handler.path)
    path = inner_path(parsed.path)
    if path is None or not allowed(method, path):
        return handler.send("Not found", 404, "text/plain")
    target = path + ("?" + parsed.query if parsed.query else "")
    if method == "POST":
        try:
            length = int(handler.headers.get("Content-Length") or 0)
        except ValueError:
            length = -1
        if length < 0 or length > MAX_POST_BODY:
            return handler.send("Request too large", 413, "text/plain")
        _audit(handler, path)
    original = handler.path
    handler.path = target
    try:
        return Handler.do_POST(handler) if method == "POST" else Handler.do_GET(handler)
    finally:
        handler.path = original
