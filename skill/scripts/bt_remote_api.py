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

    path = _path(handler)
    if path == f"{PREFIX}/snapshot":
        return _snapshot(handler)
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


def route_post(handler) -> None:
    if not _authorized(handler):
        return _problem(handler, 401, "UNAUTHORIZED", "Se requiere la clave del gateway.")
    return _problem(handler, 404, "NOT_FOUND", "Ruta remota no encontrada.")
