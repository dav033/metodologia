"""Authenticated v1 health endpoint for the remote gateway listener."""
from __future__ import annotations

import datetime as dt
import hmac
import json
import os
import sqlite3
from urllib.parse import parse_qs, urlparse

import bt_remote_commands as _commands

PREFIX = "/api/remote/v1"
MAX_BODY = 256 * 1024


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

    path = _path(handler)
    if path == f"{PREFIX}/snapshot":
        return _snapshot(handler)
    if path in (f"{PREFIX}/commands", f"{PREFIX}/history"):
        return _command_history(handler)
    if path == f"{PREFIX}/quotas":
        return _quotas(handler)
    if path == f"{PREFIX}/routes":
        return _routes(handler)
    if path != f"{PREFIX}/health":
        return _problem(handler, 404, "NOT_FOUND", "Ruta remota no encontrada.")

    from bt_server import code_version

    checked_at = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    return _send_json(handler, {"schemaVersion": 1, "status": "ok", "version": code_version(),
                                "checkedAt": checked_at}, 200)


def _snapshot(handler) -> None:
    """Compact run read model, with live task signals taken from the panel's shared now frame."""
    try:
        import bt_core
        import bt_live_api as live
        import bt_remote_snapshot

        payload = bt_remote_snapshot.build(bt_core.ROOT, live)
    except Exception:
        return _problem(handler, 503, "SNAPSHOT_UNAVAILABLE", "La vista remota aún no está disponible.")
    return _send_json(handler, payload, 200)


def _query(handler) -> dict[str, str]:
    return {key: values[0] for key, values in parse_qs(urlparse(handler.path).query).items()}


def _command_history(handler) -> None:
    query = _query(handler)
    try:
        limit = int(query.get("limit", "200"))
    except ValueError:
        limit = 0
    if not 1 <= limit <= 1000:
        return _problem(handler, 400, "INVALID_LIMIT", "El límite debe estar entre 1 y 1000.")
    try:
        import bt_remote_commands as commands
        items, cursor = commands.Ledger().history(query.get("after", ""), limit)
    except ValueError:
        return _problem(handler, 400, "INVALID_CURSOR", "El cursor no es válido.")
    return _send_json(handler, {"commands": items, "nextCursor": cursor}, 200)


def _quotas(handler) -> None:
    import bt_quota_live

    try:
        rows = bt_quota_live.read_all_live()
    except Exception:
        rows = []
    accounts = []
    for row in rows:
        windows = []
        for name, window in sorted((row.get("windows") or {}).items()):
            if not isinstance(window, dict) or window.get("used_percent") is None:
                continue
            reset = window.get("resets_at")
            windows.append({"window": name, "usedPercent": window["used_percent"],
                            "resetsAt": dt.datetime.fromtimestamp(reset, dt.UTC).isoformat()
                            if isinstance(reset, (int, float)) else None})
        observed = row.get("observed_at")
        accounts.append({"account": row.get("profile"), "provider": row.get("provider"),
                         "status": row.get("status"),
                         "observedAt": dt.datetime.fromtimestamp(observed, dt.UTC).isoformat()
                         if isinstance(observed, (int, float)) else None, "windows": windows})
    if not accounts:
        return _problem(handler, 503, "QUOTAS_UNAVAILABLE", "Las cuotas aún no están disponibles.")
    checked_at = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    return _send_json(handler, {"accounts": accounts, "checkedAt": checked_at}, 200)


def _routes(handler) -> None:
    query = _query(handler)
    target, task = query.get("target", ""), query.get("task", "")
    import re
    if not re.fullmatch(r"[A-Za-z0-9_-]+/REQ-[0-9]+", target) or \
            not re.fullmatch(r"T[0-9A-Za-z_-]{1,79}", task):
        return _problem(handler, 400, "INVALID_ROUTE_QUERY", "Se requieren target y task válidos.")
    try:
        import bt_plans_api
        import bt_remote_commands as commands
        import bt_remote_recovery as recovery
        project, _, rdir = commands._run_target(target)
        routes = recovery.route_options(project, rdir, task)
    except (ValueError, OSError, sqlite3.Error, bt_plans_api.PlanError):
        return _problem(handler, 404, "ROUTES_UNAVAILABLE", "Las rutas no están disponibles para esta ejecución.")
    return _send_json(handler, {"routes": routes}, 200)


HANDLERS: dict[str, _commands.Handler] = _commands.dispatch_handlers()
_COMMAND_STATUS = {"OK": 200, "INVALID_COMMAND": 400, "CONFIRMATION_REQUIRED": 400,
                   "COMMAND_NOT_IMPLEMENTED": 501, "STALE_PRECONDITION": 409,
                   "IDEMPOTENCY_CONFLICT": 409, "UNKNOWN_OUTCOME": 409,
                   "EFFECT_FAILED": 500, "ROUTE_UNAVAILABLE": 409, "STATE_UNAVAILABLE": 503}


def _target_state(target: str, command: str | None = None, params: dict | None = None) -> dict | None:
    """Resolve the live target state used to validate remote command preconditions."""
    return _commands.target_state(target, command, params)


def _submit_command(handler, length: int) -> None:
    try:
        request = json.loads(handler.rfile.read(length) or b"null")
    except (ValueError, OSError):
        return _problem(handler, 400, "INVALID_COMMAND", "El cuerpo debe ser JSON válido.")
    result = _commands.Ledger().submit(request, HANDLERS, _target_state)
    status = _COMMAND_STATUS.get(result.get("code") or result["status"], 200)
    _send_json(handler, result, status)


def _issue_challenge(handler, length: int) -> None:
    try:
        request = json.loads(handler.rfile.read(length) or b"null")
    except (ValueError, OSError):
        return _problem(handler, 400, "INVALID_CHALLENGE", "El cuerpo debe ser JSON válido.")
    if not isinstance(request, dict):
        return _problem(handler, 400, "INVALID_CHALLENGE", "El cuerpo debe ser un objeto JSON.")
    typed_req = request.get("typedReq", request.get("typed_req"))
    if (set(request) not in ({"target", "typedReq"}, {"target", "typed_req"})
            or not isinstance(request.get("target"), str) or not isinstance(typed_req, str)):
        return _problem(handler, 400, "INVALID_CHALLENGE", "La solicitud de confirmación no es válida.")
    try:
        challenge = _commands.Ledger().issue_challenge(request["target"], typed_req)
    except ValueError as exc:
        return _problem(handler, 400, "INVALID_CHALLENGE", str(exc))
    return _send_json(handler, challenge, 201)


def route_post(handler) -> None:
    if not _authorized(handler):
        return _problem(handler, 401, "UNAUTHORIZED", "Se requiere la clave del gateway.")
    path = _path(handler)
    if path not in {f"{PREFIX}/commands", f"{PREFIX}/challenges"}:
        return _problem(handler, 404, "NOT_FOUND", "Ruta remota no encontrada.")
    is_challenge = path == f"{PREFIX}/challenges"
    invalid_code = "INVALID_CHALLENGE" if is_challenge else "INVALID_COMMAND"
    try:
        length = int(handler.headers.get("Content-Length", "0"))
    except (AttributeError, ValueError):
        length = -1
    if length < 0 or (is_challenge and length == 0):
        return _problem(handler, 400, invalid_code, "Longitud de solicitud no válida.")
    if length > MAX_BODY:
        return _problem(handler, 413, "BODY_TOO_LARGE", "La solicitud excede el tamaño permitido.")
    if is_challenge:
        return _issue_challenge(handler, length)
    return _submit_command(handler, length)
