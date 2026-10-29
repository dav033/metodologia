"""The panel as the door to the test versions it started: `http://p<port>.localhost:<panel port>/<path>`.

The owner reaches the panel through one SSH tunnel to its port (pictures REQ-021, 2026-10-29: the links to a version on
`http://localhost:3000` led nowhere from his computer, whose tunnel carried only 8765). Browsers resolve every
`*.localhost` name to the machine they run on, so such a link comes back through the same tunnel; the panel sees the
`p<port>` host and relays the request, any method, to that port on loopback. Only ports of test servers the panel itself
started and still runs (`bt_verify_servers` state files) are relayed: the panel never becomes a door to other local
services. The Host header is kept, so the version sees one consistent origin (its same-origin and CSRF checks hold).
WebSocket upgrades (a dev server's live reload) are not relayed. Standard library only.
"""
from __future__ import annotations

import http.client
import json
import os
import re
from pathlib import Path

HOST = re.compile(r"^p(\d{2,5})\.localhost(?::\d{1,5})?$", re.I)
HOP = frozenset({"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers",
                 "transfer-encoding", "upgrade", "content-length"})
MAX_BODY = 64 << 20


def target_port(host: str | None) -> int | None:
    found = HOST.match((host or "").strip())
    return int(found.group(1)) if found else None


def running_ports() -> set[int]:
    """Ports of the test servers `bt_verify_servers` started whose tmux session still runs."""
    import bt_agent_terminal as terminal
    base = Path(os.environ.get("BITACORA_VERIFY_DIR") or Path.home() / ".local" / "share" / "bitacora-verify")
    ports: set[int] = set()
    for state in base.glob("*/*/*.servers.json"):
        try:
            data = json.loads(state.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError):
            continue
        if isinstance(data, dict) and isinstance(data.get("session"), str) and terminal.exists(data["session"]):
            ports.update(p for p in (data.get("ports") or {}).values() if isinstance(p, int))
    return ports


def serve(handler) -> bool:
    """Relay the request when its host names a running test version; False when it is a request for the panel."""
    port = target_port(handler.headers.get("Host"))
    if port is None:
        return False
    if port not in running_ports():
        handler.send("Esa versión no está en marcha: vuelve a «Probar» y pulsa «Probar esta versión».", 404,
                     "text/plain; charset=utf-8")
        return True
    if (handler.headers.get("Upgrade") or "").strip():
        handler.send("Not relayed", 501, "text/plain")
        return True
    try:
        length = int(handler.headers.get("Content-Length") or 0)
    except ValueError:
        length = -1
    if not 0 <= length <= MAX_BODY:
        handler.send("Bad request", 400, "text/plain")
        return True
    body = handler.rfile.read(length) if length else None
    headers = {k: v for k, v in handler.headers.items() if k.lower() not in HOP}
    headers["X-Forwarded-Host"] = handler.headers.get("Host") or ""
    headers["X-Forwarded-Proto"] = "http"
    upstream = http.client.HTTPConnection("127.0.0.1", port, timeout=300)
    try:
        upstream.request(handler.command, handler.path, body=body, headers=headers)
        reply = upstream.getresponse()
    except OSError:
        upstream.close()
        handler.send("La versión todavía no responde; espera unos segundos.", 502, "text/plain; charset=utf-8")
        return True
    try:
        handler.send_response(reply.status, reply.reason)
        for key, value in reply.getheaders():
            if key.lower() not in HOP:
                handler.send_header(key, value)
        handler.send_header("Connection", "close")
        handler.end_headers()
        handler.close_connection = True
        if handler.command != "HEAD":
            while chunk := reply.read1(65536):          # streamed as it comes: a page renders, an event stream flows
                handler.wfile.write(chunk)
                handler.wfile.flush()
    except (BrokenPipeError, ConnectionResetError):
        pass
    finally:
        upstream.close()
    return True
