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
            ("state_change", "failed"): "attempt.failed" if data.get("retry_exhausted") else None,
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
    if kind == "attempt.failed" and not (data.get("retry_exhausted") or row.get("retry_exhausted")):
        # A failed transition says only that one attempt ended; it does not prove that recovery is over.
        return None
    if not data:
        data = {key: row.get(key) for key in ("failure", "summary") if row.get(key) is not None}
    return project_event(kind, identity, str(row.get("at") or row.get("occurredAt") or ""), target, data)


def from_snapshot(runs: list[dict[str, Any]], rounds: list[dict[str, Any]], *, quotas: list[dict[str, Any]] | None = None,
                  commands: list[dict[str, Any]] | None = None, now: float | None = None
                  ) -> list[dict[str, Any]]:
    """Derive notifications from durable snapshot facts absent from the flow bus."""
    import datetime as dt
    import time

    current = time.time() if now is None else now
    events = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        target = {"run": str(run.get("run", ""))}
        status = run.get("state", run.get("status"))
        stamp = str(run.get("updatedAt", run.get("updated_at", "")) or "")
        identity = str(run.get("run", "")) + ":" + stamp
        if status in {"finished", "completed", "done"}:
            events.append(project_event("run.finished", identity, stamp, target, {"state": status}))
        if run.get("decisions"):
            for decision in run["decisions"]:
                if isinstance(decision, dict):
                    events.append(project_event("plan.waiting", identity + ":" + str(decision.get("id", "")), stamp,
                                                target, {"decision": decision}))
        for task in run.get("tasks", []):
            if not isinstance(task, dict):
                continue
            task_target = {**target, "task": str(task.get("id", ""))}
            attempt = task.get("attempt") if isinstance(task.get("attempt"), dict) else {}
            at = str(attempt.get("ended_at") or attempt.get("last_activity_at") or stamp)
            event_id = str(attempt.get("id") or task.get("id") or identity)
            if task.get("state") == "blocked":
                events.append(project_event("attempt.blocked", event_id, at, task_target,
                                            {"state": "blocked", "reason": task.get("reason")}))
            if task.get("retry_exhausted") is True or task.get("retries_remaining") == 0:
                events.append(project_event("attempt.failed", event_id + ":exhausted", at, task_target,
                                            {"retry_exhausted": True, "attempts": task.get("attempts"),
                                             "retries_remaining": task.get("retries_remaining")}))
            if task.get("state") == "blocked" and "quota" in str(task.get("reason", "")).lower():
                events.append(project_event("quota.exhausted", event_id + ":quota", at, task_target,
                                            {"reason": task.get("reason")}))
            activity = attempt.get("last_activity_at")
            if activity:
                try:
                    age = current - dt.datetime.fromisoformat(str(activity).replace("Z", "+00:00")).timestamp()
                except (ValueError, OverflowError):
                    age = 0
                if age > 600 and attempt.get("live"):
                    events.append(project_event("attempt.stalled", event_id + ":stalled", str(activity), task_target,
                                                {"lastActivityAt": activity, "ageSeconds": int(age)}))
    for round_data in rounds:
        if isinstance(round_data, dict) and round_data.get("status") == "open":
            target = {"run": f"{round_data.get('project', '')}/{round_data.get('req', '')}"}
            events.append(project_event("round.waiting", target["run"] + ":round:" + str(round_data.get("round", "")),
                                        str(round_data.get("created_at", "")), target,
                                        {"round": round_data.get("round"), "title": round_data.get("title")}))
    for account in quotas or []:
        if not isinstance(account, dict):
            continue
        exhausted = account.get("status") == "exhausted" or any(
            isinstance(window, dict) and window.get("used_percent") == 100
            for window in (account.get("windows") or {}).values()
        ) if isinstance(account.get("windows", {}), dict) else account.get("status") == "exhausted"
        if exhausted:
            identity = str(account.get("profile", "")) + ":" + str(account.get("observed_at", ""))
            events.append(project_event("quota.exhausted", identity, str(account.get("observed_at", "")),
                                        {"run": "quota"}, {"profile": account.get("profile"),
                                        "provider": account.get("provider"), "status": account.get("status")}))
    for command in commands or []:
        if isinstance(command, dict):
            identity = str(command.get("idempotency_key", ""))
            events.append(project_event("command.updated", identity, str(command.get("finished_at") or command.get("received_at") or ""),
                                        {"run": str(command.get("target", ""))},
                                        {"command": command.get("command"), "status": command.get("status"),
                                         "origin": command.get("origin")}))
    return events


def decision_events(plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events = []
    for plan in plans:
        target = {"run": f"{plan.get('project', '')}/{plan.get('req_id', '')}"}
        for request in plan.get("decisions") or []:
            identity = f"{target['run']}:{request.get('id', '')}"
            events.append(project_event("plan.waiting", identity, str(request.get("created_at") or plan.get("updated_at") or ""),
                                        target, {"decision": request}))
            reason = str(request.get("reason", ""))
            if reason.removeprefix("m5:").removeprefix("m5_") == "attempts_exhausted":
                events.append(project_event("attempt.failed", identity + ":exhausted",
                                            str(request.get("created_at") or plan.get("updated_at") or ""),
                                            {**target, **({"task": str(request["task"])} if request.get("task") else {})},
                                            {"retry_exhausted": True, "reason": "attempts_exhausted",
                                             "attempt": request.get("attempt")}))
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
