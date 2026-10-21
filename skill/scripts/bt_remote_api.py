"""Authenticated v1 health endpoint for the remote gateway listener."""
from __future__ import annotations

import datetime as dt
import hmac
import json
import os
from urllib.parse import parse_qs, urlparse

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


def _query(handler) -> dict[str, str]:
    parsed = urlparse(handler.path)
    return {key: values[0] for key, values in parse_qs(parsed.query).items()}


def route_get(handler) -> None:
    if not _authorized(handler):
        return _problem(handler, 401, "UNAUTHORIZED", "Se requiere la clave del gateway.")

    path = _path(handler)
    if path == f"{PREFIX}/snapshot":
        return _snapshot(handler)
    if path == f"{PREFIX}/events":
        import bt_remote_events as feed
        try:
            limit = int(_query(handler).get("limit", "200"))
        except ValueError:
            return _problem(handler, 400, "INVALID_LIMIT", "El límite debe estar entre 1 y 1000.")
        if limit < 1:
            return _problem(handler, 400, "INVALID_LIMIT", "El límite debe estar entre 1 y 1000.")
        query = _query(handler)
        try:
            feed.page([], query.get("after", ""), min(limit, 1000))
        except feed.CursorError as exc:
            return _problem(handler, 400, "INVALID_CURSOR", str(exc))
        import bt_core
        import bt_live_api as live
        import bt_plans_api
        import bt_subscriptions
        import bt_remote_commands as commands

        try:
            runs = live.run_summaries(bt_core.ROOT, "global")
            plans = bt_plans_api.plans_payload(bt_core.ROOT)
            quotas = bt_subscriptions.summary()
            ledger = commands.Ledger()
            rows = ledger.rows()
            events = feed.collect(bt_core.ROOT, runs, plans, quotas, rows)
            return _send_json(handler, feed.page(events, query.get("after", ""), min(limit, 1000)), 200)
        except feed.CursorError as exc:
            return _problem(handler, 400, "INVALID_CURSOR", str(exc))
        except (OSError, ValueError, bt_plans_api.PlanError):
            return _problem(handler, 503, "EVENTS_UNAVAILABLE", "El feed remoto aún no está disponible.")
    if path != f"{PREFIX}/health":
        return _problem(handler, 404, "NOT_FOUND", "Ruta remota no encontrada.")

    from bt_server import code_version

    checked_at = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    return _send_json(handler, {"schemaVersion": 1, "status": "ok", "version": code_version(),
                                "checkedAt": checked_at}, 200)


def _snapshot(handler) -> None:
    """Compact run read model, with live task signals taken from the panel's shared now frame."""
    import bt_core
    import bt_live_api as live

    root = bt_core.ROOT
    try:
        summaries = live.run_summaries(root, "global")
        now = live.now_frame_data(root)
    except Exception:
        return _problem(handler, 503, "SNAPSHOT_UNAVAILABLE", "La vista remota aún no está disponible.")

    active_by_run: dict[str, dict] = {}
    for item in now["items"]:
        active_by_run.setdefault(f'{item["project"]}/{item["req_id"]}', item)

    runs = []
    for run in summaries:
        active = active_by_run.get(run["run"])
        attempts = [attempt for task in run["tasks"] for attempt in task["history"]]
        last_activity = max((a.get("last_activity_at") for a in attempts if a.get("last_activity_at")), default=None)
        if last_activity is None:
            last_activity = run.get("updated_at")
        tasks = []
        for task in run["tasks"]:
            review = next((a for a in reversed(task["history"]) if a.get("state") == "rejected"), None)
            current = task.get("attempt")
            tasks.append({"id": task["id"], "title": task["title"], "state": task["state"],
                          "activeAttempt": live._attempt(current) if current and current.get("live") else None,
                          "reviewAttempt": live._attempt(review),
                          "history": [live._attempt(a) for a in task["history"]]})
        runs.append({"id": run["run"], "project": run["project"], "reqId": run["req_id"],
                     "title": run["title"], "status": run["status"], "active": run["active"],
                     "activeTask": ({"id": active["task"], "title": active["task_title"],
                                     "state": active["state"], "attempt": live._attempt(active["attempt"])}
                                    if active else None),
                     "lastActivityAt": last_activity, "tasks": tasks})
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    return _send_json(handler, {"schemaVersion": 1, "generatedAt": generated_at, "cursor": generated_at,
                                "runs": runs}, 200)


HANDLERS: dict = {}  # Filled by the dispatch layer in T5a/T5b.
_COMMAND_STATUS = {"OK": 200, "INVALID_COMMAND": 400, "COMMAND_NOT_IMPLEMENTED": 501,
                   "STALE_PRECONDITION": 409, "IDEMPOTENCY_CONFLICT": 409, "UNKNOWN_OUTCOME": 409,
                   "EFFECT_FAILED": 500, "STATE_UNAVAILABLE": 503, "CONFIRMATION_REQUIRED": 409}


def _target_state(target: str, command: str | None = None, params: dict | None = None) -> dict | None:
    """Resolve the target's current precondition state once the dispatch layer is available."""
    import bt_remote_commands as commands
    return commands.target_state(target, command, params)


def _submit_command(handler, length: int) -> None:
    import bt_remote_commands as commands

    try:
        request = json.loads(handler.rfile.read(length) or b"null")
    except (ValueError, OSError):
        return _problem(handler, 400, "INVALID_COMMAND", "El cuerpo debe ser JSON válido.")
    ledger = commands.Ledger()
    handlers = commands.dispatch_handlers()
    handlers.update(HANDLERS)
    result = ledger.submit(request, handlers, _target_state)
    status = _COMMAND_STATUS.get(result.get("code") or result["status"], 200)
    _send_json(handler, result, status)


def route_post(handler) -> None:
    if not _authorized(handler):
        return _problem(handler, 401, "UNAUTHORIZED", "Se requiere la clave del gateway.")
    if _path(handler) == f"{PREFIX}/commands":
        try:
            length = int(handler.headers.get("Content-Length", "0"))
        except (AttributeError, ValueError):
            length = -1
        if length < 0:
            return _problem(handler, 400, "INVALID_COMMAND", "Longitud de solicitud no válida.")
        if length > MAX_BODY:
            return _problem(handler, 413, "BODY_TOO_LARGE", "La solicitud excede el tamaño permitido.")
        return _submit_command(handler, length)
    if _path(handler) == f"{PREFIX}/challenges":
        try:
            length = int(handler.headers.get("Content-Length", "0"))
        except (AttributeError, ValueError):
            length = -1
        if length < 0:
            return _problem(handler, 400, "INVALID_CHALLENGE", "Longitud de solicitud no válida.")
        if length > MAX_BODY:
            return _problem(handler, 413, "BODY_TOO_LARGE", "La solicitud excede el tamaño permitido.")
        try:
            body = json.loads(handler.rfile.read(length) or b"null")
        except (ValueError, OSError):
            return _problem(handler, 400, "INVALID_CHALLENGE", "El cuerpo debe ser JSON válido.")
        if not isinstance(body, dict) or set(body) not in ({"target", "typedReq"}, {"target", "typed_req"}) \
                or not isinstance(body.get("target"), str):
            return _problem(handler, 400, "INVALID_CHALLENGE", "Se requieren target y typedReq.")
        import bt_remote_commands as commands
        try:
            challenge = commands.Ledger().issue_challenge(
                body["target"], body.get("typedReq", body.get("typed_req")))
        except ValueError as exc:
            return _problem(handler, 400, "INVALID_CHALLENGE", str(exc))
        return _send_json(handler, challenge, 201)
    return _problem(handler, 404, "NOT_FOUND", "Ruta remota no encontrada.")
