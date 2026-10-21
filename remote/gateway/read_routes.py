"""Authenticated, allow-listed read routes from the phone gateway to the laptop API."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlencode

from auth import SESSION_COOKIE, cookie_values
from upstream import UpstreamError

_PREFIX = "/api/remote/v1"
_REVIEW = re.compile(r"attempts/([A-Za-z0-9._:-]{1,120})/review\Z")
_TARGET = re.compile(r"[A-Za-z0-9_-]+/REQ-[0-9]+\Z")
_READ_PATHS = {"snapshot", "events", "commands", "history", "quotas", "routes"}


def handle_remote_get(handler, service, runtime, route) -> bool:
    """Serve an authenticated read route, returning False for unrelated URLs."""
    if not route.path.startswith(_PREFIX + "/"):
        return False
    suffix = route.path[len(_PREFIX) + 1:]
    query = parse_qs(route.query, keep_blank_values=True)
    if suffix not in _READ_PATHS and _REVIEW.fullmatch(suffix) is None:
        return False

    token = cookie_values(handler.headers.get("Cookie")).get(SESSION_COOKIE, "")
    if not token or service.store.get_session(token) is None:
        handler._json(401, {"error": "unauthorized"})
        return True
    if runtime is None:
        handler._json(503, {"code": "LAPTOP_UNAVAILABLE"})
        return True

    if suffix == "routes":
        target, task = query.get("target", []), query.get("task", [])
        if (len(target) != 1 or len(task) != 1 or not _TARGET.fullmatch(target[0])
                or not re.fullmatch(r"T[0-9A-Za-z_-]{1,79}", task[0])):
            handler._json(400, {"code": "INVALID_ROUTE_QUERY"})
            return True
    elif _REVIEW.fullmatch(suffix):
        target = query.get("target", [])
        if len(target) != 1 or not _TARGET.fullmatch(target[0]):
            handler._json(400, {"code": "INVALID_TARGET"})
            return True
    elif suffix in {"commands", "history", "events"}:
        for name in ("after", "limit"):
            if len(query.get(name, [])) > 1:
                handler._json(400, {"code": "INVALID_QUERY"})
                return True

    path = route.path
    if route.query:
        path += "?" + urlencode([(key, value) for key, values in query.items() for value in values])
    try:
        payload = runtime.read_remote(path)
    except UpstreamError:
        handler._json(503, {"code": "LAPTOP_UNAVAILABLE"})
        return True
    handler._json(200, payload)
    return True
