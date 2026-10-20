"""Stable, redacted event projection for the remote laptop API."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from typing import Any

_SECRET_NAMES = r"(?:FLOW_GATEWAY_KEY|TELEGRAM_BOT_TOKEN|GITHUB_CLIENT_SECRET)"
_ASSIGNMENT = re.compile(
    rf"(?i)\b({_SECRET_NAMES})\s*(?:=|:)\s*(?:\"[^\"\r\n]*\"|'[^'\r\n]*'|[^\s,;]+)"
)
_REDACTED = "[REDACTED]"


def redact(value: Any) -> Any:
    """Redact known credential assignments from all remotely exposed text."""
    if isinstance(value, str):
        return _ASSIGNMENT.sub(lambda match: f"{match.group(1)}={_REDACTED}", value)
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        return {key: (_REDACTED if isinstance(key, str) and re.fullmatch(_SECRET_NAMES, key, re.I)
                      else redact(item)) for key, item in value.items()}
    return value


def _stable_id(kind: str, identity: str) -> str:
    digest = hashlib.sha256(f"{kind}\0{identity}".encode()).hexdigest()
    return f"evt_{digest}"


def project_event(kind: str, identity: str, occurred_at: str, target: dict[str, str],
                  data: dict[str, Any]) -> dict[str, Any]:
    event_id = _stable_id(kind, identity)
    return {"schemaVersion": 1, "id": event_id, "cursor": event_id, "type": kind,
            "occurredAt": occurred_at, "target": target, "data": redact(data),
            "dedupeKey": event_id}


def retry_context(runs: list[dict[str, Any]], max_attempts: int) -> dict[tuple[str, str], dict[str, Any]]:
    """Per (run, task): the task's current state and how many attempts it has used of the budget."""
    return {(run.get("run", ""), task.get("id")): {"state": task.get("state"), "attempts": task.get("attempts") or 0,
                                                  "maxAttempts": max_attempts}
            for run in runs for task in run.get("tasks") or []}


def from_flow(row: dict[str, Any], context: dict[tuple[str, str], dict[str, Any]] | None = None) -> dict[str, Any] | None:
    """Map actionable flow-bus records to the versioned remote notification contract.

    With `context` (see `retry_context`), a failed attempt notifies only once the task has no retries left, and the
    event carries those retry facts; a failure the scheduler will still retry produces no event.
    """
    retries = None
    kind = row.get("remote_type")
    if kind is None:
        # Production rows come from bt_flow_bus and carry its `kind`/`data` contract.
        data = row.get("data") if isinstance(row.get("data"), dict) else {}
        state = data.get("state") or data.get("status") or data.get("to")
        kind = row.get("kind")
        if kind in {"state_change", "task_state"}:
            kind = {
                "failed": "attempt.failed", "rejected": "attempt.failed", "blocked": "attempt.blocked",
                "completed": "task.completed", "accepted": "task.completed",
            }.get(state, "task.progress")
        elif kind == "verdict":
            kind = "attempt.failed" if state in {"failed", "rejected"} else "task.completed"
        if kind == "attempt.failed" and context is not None:
            info = context.get((str(row.get("run", "")), str(row.get("task", ""))))
            if info is None:
                return None
            remaining = max(0, info["maxAttempts"] - int(info["attempts"]))
            if info["state"] == "blocked":
                kind = "attempt.blocked"
            elif info["state"] in {"running", "verifying", "completed", "pending", "ready"} or \
                    (remaining > 0 and info["state"] != "failed"):
                return None
            retries = {"attempts": info["attempts"], "maxAttempts": info["maxAttempts"], "remaining": remaining}
    if kind not in {"attempt.failed", "attempt.blocked", "run.finished", "round.waiting", "plan.waiting",
                    "quota.exhausted", "attempt.stalled", "laptop.offline", "command.updated",
                    "task.progress", "task.completed"}:
        return None
    run = str(row.get("run", ""))
    project, separator, req = run.partition("/")
    target = {"project": project, "req": req} if separator else {"run": run}
    if row.get("task"):
        target["taskId"] = str(row["task"])
    if row.get("attempt"):
        target["attemptId"] = str(row["attempt"])
    identity = str(row.get("id") or row.get("ord") or row.get("seq") or "")
    data = row.get("data") if isinstance(row.get("data"), dict) else {}
    if not data:
        data = {key: row.get(key) for key in ("failure", "summary") if row.get(key) is not None}
    elif row.get("summary") is not None and "summary" not in data:
        data = {**data, "summary": row["summary"]}
    if retries is not None:
        data = {**data, "retries": retries}
    return project_event(kind, identity, str(row.get("at") or row.get("occurredAt") or ""), target, data)


def decision_events(plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events = []
    for plan in plans:
        target = {"run": f"{plan.get('project', '')}/{plan.get('req_id', '')}"}
        for request in plan.get("decisions") or []:
            identity = f"{target['run']}:{request.get('id', '')}"
            events.append(project_event("plan.waiting", identity, str(request.get("created_at") or plan.get("updated_at") or ""),
                                        target, {"decision": request}))
    return events


def page(events: list[dict[str, Any]], after: str, limit: int) -> tuple[list[dict[str, Any]], str, bool]:
    events.sort(key=lambda event: (event["occurredAt"], event["id"]))
    start = 0
    if after:
        positions = [index for index, event in enumerate(events) if event["cursor"] == after]
        if positions:
            start = positions[-1] + 1
    selected = events[start:start + limit]
    cursor = selected[-1]["cursor"] if selected else after
    return selected, cursor, start + len(selected) < len(events)


_TERMINAL_RUN = frozenset({"completed", "finished", "done", "failed", "cancelled", "stopped"})
STALL_SECONDS = 600
_first_seen: dict[str, str] = {}


def _parse(value: Any) -> dt.datetime | None:
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.UTC)


def derived_events(runs: list[dict[str, Any]], rounds: list[dict[str, Any]], quotas: list[dict[str, Any]],
                   now: dt.datetime) -> list[dict[str, Any]]:
    """Events computed from state rather than the flow bus: finished runs, open rounds, exhausted quotas, stalls.

    Each has an id derived from its identity and a stable `occurredAt`, so a re-read never reorders or repeats it.
    """
    events = []
    for run in runs:
        name, state = str(run.get("run", "")), run.get("state") or run.get("status")
        target = {"run": name}
        if state in _TERMINAL_RUN:
            events.append(project_event("run.finished", f"{name}:{run.get('updated_at')}", str(run.get("updated_at") or ""),
                                        target, {"state": state}))
        if not run.get("active"):
            continue
        for task in run.get("tasks") or []:
            attempt = task.get("attempt") or {}
            beat = _parse(attempt.get("last_activity_at"))
            if attempt.get("live") and beat and (now - beat).total_seconds() > STALL_SECONDS and attempt.get("id"):
                due = (beat + dt.timedelta(seconds=STALL_SECONDS)).isoformat()
                events.append(project_event("attempt.stalled", f"{name}:{attempt['id']}", due,
                                            {**target, "taskId": str(task.get("id")), "attemptId": str(attempt["id"])},
                                            {"lastActivityAt": attempt.get("last_activity_at")}))
    for item in rounds:
        name = f"{item.get('project')}/{item.get('req')}"
        events.append(project_event("round.waiting", f"{name}:{item.get('id')}", str(item.get("created_at") or ""),
                                    {"run": name}, {"round": item.get("round"), "title": item.get("title")}))
    usable = [account for account in quotas if account.get("windows")]
    if usable and all(any(w.get("remaining") is not None and w["remaining"] <= 0 for w in account["windows"])
                      for account in usable):
        resets = sorted(str(w.get("resetsAt")) for account in usable for w in account["windows"]
                        if w.get("remaining") is not None and w["remaining"] <= 0)
        identity = "quota:" + ",".join(resets)
        events.append(project_event("quota.exhausted", identity, _first_seen.setdefault(identity, now.isoformat()),
                                    {"run": "global"}, {"accounts": [a.get("id") for a in usable]}))
    return events
