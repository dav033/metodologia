"""Authenticated, versioned HTTP surface for the laptop's remote gateway."""
from __future__ import annotations

import datetime as dt
import hmac
import json
import os
import re
from urllib.parse import parse_qs, urlparse

PREFIX = "/api/remote/v1"
MAX_BODY = 256 * 1024
_ATTEMPT_ID = re.compile(r"^[A-Za-z0-9._:-]{1,120}$")


def _json(handler, payload: dict, status: int = 200, content_type: str = "application/json; charset=utf-8") -> None:
    handler.send(json.dumps(payload, ensure_ascii=False), status, content_type)


def _problem(handler, status: int, code: str, message: str) -> None:
    _json(handler, {"code": code, "message": message}, status, "application/problem+json; charset=utf-8")


def _authorized(handler) -> bool:
    expected = os.environ.get("FLOW_GATEWAY_KEY", "")
    supplied = handler.headers.get("Authorization", "")
    scheme, _, value = supplied.partition(" ")
    if not expected or scheme.lower() != "bearer" or not value:
        return False
    return hmac.compare_digest(value.encode("utf-8"), expected.encode("utf-8"))


def _path(handler) -> tuple[str, dict[str, str]]:
    parsed = urlparse(handler.path)
    query = {key: values[0] for key, values in parse_qs(parsed.query).items()}
    return parsed.path, query


def _runs() -> list[dict]:
    import bt_live_api as live
    return live.run_summaries(None, "global")


def _shared_now_items() -> list[dict]:
    """Read live attempts from the same cached now frame used by the local SSE clients."""
    import bt_live_api as live
    frame = live._now_frame(None).decode("utf-8")
    for line in frame.splitlines():
        if line.startswith("data: "):
            payload = json.loads(line[6:])
            return payload.get("items", [])
    return []


def _snapshot_runs() -> list[dict]:
    """Add live task and liveness data to run summaries using the shared now read model."""
    runs = _runs()
    now_by_run = {}
    for item in _shared_now_items():
        key = f'{item.get("project", "")}/{item.get("req_id", "")}'
        now_by_run.setdefault(key, []).append(item)

    for run in runs:
        live_items = now_by_run.get(run.get("run"), [])
        active = live_items[0] if live_items else None
        task_by_id = {task.get("id"): task for task in run.get("tasks", [])}
        active_task = task_by_id.get(active.get("task")) if active else None
        attempts = [attempt for task in run.get("tasks", [])
                    for attempt in [task.get("attempt"), *(task.get("history") or [])]]
        last_activity = [attempt.get("last_activity_at") for attempt in attempts
                         if attempt and attempt.get("last_activity_at")]
        run["active_task"] = ({"id": active_task.get("id"), "title": active_task.get("title")}
                              if active_task else None)
        run["last_sign_of_life"] = max(last_activity, default=run.get("updated_at"))
    return runs


def _plans() -> list[dict]:
    import bt_plans_api as plans
    from bt_core import ROOT
    return plans.plans_payload(ROOT)


def route_get(handler) -> None:
    if not _authorized(handler):
        return _problem(handler, 401, "UNAUTHORIZED", "Se requiere la clave del gateway.")
    path, query = _path(handler)
    if path == f"{PREFIX}/health":
        from bt_server import code_version
        return _json(handler, {"schemaVersion": 1, "status": "ok",
                               "version": code_version(),
                               "checkedAt": dt.datetime.now(dt.UTC).isoformat()})
    try:
        if path == f"{PREFIX}/snapshot":
            return _json(handler, {"schemaVersion": 1, "runs": _snapshot_runs(), "plans": _plans(),
                                   "generatedAt": dt.datetime.now(dt.UTC).isoformat(), "cursor": ""})
        if path == f"{PREFIX}/runs":
            return _json(handler, {"runs": _runs()})
        if path == f"{PREFIX}/plans":
            return _json(handler, {"plans": _plans()})
        if path == f"{PREFIX}/history":
            return _problem(handler, 503, "HISTORY_UNAVAILABLE", "El registro de comandos aún no está disponible.")
        if path == f"{PREFIX}/challenges":
            return _problem(handler, 503, "CHALLENGES_UNAVAILABLE", "Los desafíos aún no están disponibles.")
        if path == f"{PREFIX}/quotas":
            return _problem(handler, 503, "QUOTAS_UNAVAILABLE", "Las cuotas aún no están disponibles.")
        if path == f"{PREFIX}/events":
            import bt_live_api as live
            try:
                limit = int(query.get("limit", "200"))
            except ValueError:
                return _problem(handler, 400, "INVALID_LIMIT", "El límite debe estar entre 1 y 1000.")
            if limit < 1:
                return _problem(handler, 400, "INVALID_LIMIT", "El límite debe estar entre 1 y 1000.")
            limit = min(limit, 1000)
            after = query.get("after", "")
            if after and not after.isdigit():
                return _problem(handler, 400, "INVALID_CURSOR", "El cursor no es válido.")
            events, _, cursors = live.flow_events(None, "global", after_ord=after, limit=limit)
            cursor = str(max((int(row.get("ord", 0)) for row in events), default=int(after or 0)))
            return _json(handler, {"events": events, "nextCursor": cursor,
                                   "hasMore": len(events) == limit, "cursors": cursors})
        if path == f"{PREFIX}/commands":
            return _problem(handler, 503, "COMMANDS_UNAVAILABLE", "El registro de comandos aún no está disponible.")
        match = re.fullmatch(re.escape(PREFIX) + r"/attempts/([^/]+)/review", path)
        if match:
            if not _ATTEMPT_ID.fullmatch(match.group(1)):
                return _problem(handler, 400, "INVALID_ID", "El identificador del intento no es válido.")
            return _problem(handler, 503, "REVIEW_UNAVAILABLE", "La revisión remota aún no está disponible.")
    except (ValueError, OSError):
        return _problem(handler, 503, "STARTING", "La API remota aún no está disponible.")
    return _problem(handler, 404, "NOT_FOUND", "Ruta remota no encontrada.")


HANDLERS: dict = {}     # additional command handlers supplied by later dispatch layers
_COMMAND_STATUS = {"OK": 200, "INVALID_COMMAND": 400, "COMMAND_NOT_IMPLEMENTED": 501, "STALE_PRECONDITION": 409,
                   "IDEMPOTENCY_CONFLICT": 409, "UNKNOWN_OUTCOME": 409, "EFFECT_FAILED": 500, "STATE_UNAVAILABLE": 503}


def _target_state(target: str) -> dict | None:
    import bt_remote_commands as commands
    return commands.target_state(target)


def _submit_command(handler, length: int) -> None:
    import bt_remote_commands as commands
    try:
        request = json.loads(handler.rfile.read(length) or b"null")
    except (ValueError, OSError):
        return _problem(handler, 400, "INVALID_COMMAND", "El cuerpo debe ser JSON válido.")
    handlers = commands.dispatch_handlers()
    handlers.update(HANDLERS)
    result = commands.Ledger().submit(request, handlers, _target_state)
    _json(handler, result, _COMMAND_STATUS.get(result.get("code") or result["status"], 200))


def route_post(handler) -> None:
    if not _authorized(handler):
        return _problem(handler, 401, "UNAUTHORIZED", "Se requiere la clave del gateway.")
    path, _ = _path(handler)
    if path == f"{PREFIX}/commands":
        try:
            length = int(handler.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1
        if length < 0:
            return _problem(handler, 400, "INVALID_COMMAND", "Longitud de solicitud no válida.")
        if length > MAX_BODY:
            return _problem(handler, 413, "BODY_TOO_LARGE", "La solicitud excede el tamaño permitido.")
        return _submit_command(handler, length)
    if path == f"{PREFIX}/challenges":
        return _problem(handler, 503, "CHALLENGES_UNAVAILABLE", "Los desafíos aún no están disponibles.")
    return _problem(handler, 404, "NOT_FOUND", "Ruta remota no encontrada.")
