"""Stable, redacted event projection for the remote laptop API."""
from __future__ import annotations

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


def from_flow(row: dict[str, Any]) -> dict[str, Any] | None:
    """Map actionable flow-bus records to the versioned remote notification contract."""
    kind = row.get("remote_type")
    if kind is None:
        # Production rows come from bt_flow_bus and carry its `kind`/`data` contract;
        # `remote_type` is reserved for explicitly projected external notifications.
        data = row.get("data") if isinstance(row.get("data"), dict) else {}
        state = data.get("state")
        kind = {
            ("state_change", "failed"): "attempt.failed",
            ("state_change", "rejected"): "attempt.failed",
            ("task_state", "blocked"): "attempt.blocked",
            ("verdict", "failed"): "attempt.failed",
            ("verdict", "rejected"): "attempt.failed",
        }.get((row.get("kind"), state))
    if kind not in {"attempt.failed", "attempt.blocked", "run.finished", "round.waiting", "plan.waiting",
                    "quota.exhausted", "attempt.stalled", "laptop.offline", "command.updated"}:
        return None
    target = {"run": str(row.get("run", ""))}
    if row.get("task"):
        target["task"] = str(row["task"])
    identity = str(row.get("id") or row.get("ord") or row.get("seq") or "")
    data = row.get("data") if isinstance(row.get("data"), dict) else {}
    if not data:
        data = {key: row.get(key) for key in ("failure", "summary") if row.get(key) is not None}
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
