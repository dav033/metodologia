"""Authenticated v1 health endpoint for the remote gateway listener."""
from __future__ import annotations

import datetime as dt
import hmac
import json
import os
from urllib.parse import urlparse

PREFIX = "/api/remote/v1"


def _send_json(handler, payload: dict, status: int, content_type: str = "application/json; charset=utf-8") -> None:
    handler.send(json.dumps(payload, ensure_ascii=False), status, content_type)


def _problem(handler, status: int, code: str, message: str) -> None:
    _send_json(handler, {"code": code, "message": message}, status,
               "application/problem+json; charset=utf-8")


def _authorized(handler) -> bool:
    expected = os.environ.get("FLOW_GATEWAY_KEY", "")
    authorization = handler.headers.get("Authorization", "")
    scheme, separator, supplied = authorization.partition(" ")
    if not expected or not separator or scheme.lower() != "bearer" or not supplied:
        return False
    return hmac.compare_digest(supplied.encode("utf-8"), expected.encode("utf-8"))


def _path(handler) -> str:
    return urlparse(handler.path).path


def route_get(handler) -> None:
    if not _authorized(handler):
        return _problem(handler, 401, "UNAUTHORIZED", "Se requiere la clave del gateway.")

    if _path(handler) != f"{PREFIX}/health":
        return _problem(handler, 404, "NOT_FOUND", "Ruta remota no encontrada.")

    from bt_server import code_version

    checked_at = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    return _send_json(handler, {"schemaVersion": 1, "status": "ok", "version": code_version(),
                                "checkedAt": checked_at}, 200)


def route_post(handler) -> None:
    if not _authorized(handler):
        return _problem(handler, 401, "UNAUTHORIZED", "Se requiere la clave del gateway.")
    return _problem(handler, 404, "NOT_FOUND", "Ruta remota no encontrada.")
