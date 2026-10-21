"""Stable, cursor-based notifications for the remote gateway."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import sqlite3
from typing import Any

STALL_SECONDS = 15 * 60
RUN_DONE = {"done", "completed", "finished", "complete"}
NOTIFICATION_KINDS = (
    "attempt.failed", "attempt.blocked", "run.finished", "round.waiting", "plan.waiting",
    "quota.exhausted", "attempt.stalled", "laptop.offline", "command.updated",
)
_SECRET_NAMES = (r"(?:FLOW_GATEWAY_KEY|TELEGRAM_BOT_TOKEN|GITHUB_CLIENT_SECRET|SESSION_SECRET"
                 r"|[A-Z0-9_]*(?:API_?KEY|ACCESS_?KEY|SECRET|TOKEN|PASSWORD|PASSWD))")
_ASSIGNMENT = re.compile(rf"(?i)\b({_SECRET_NAMES})\s*(?:=|:)\s*(?:\"[^\"\r\n]*\"|'[^'\r\n]*'|[^\s,;]+)")
_TOKEN_SHAPES = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?(?:-----END [A-Z ]*PRIVATE KEY-----|\Z)"
    r"|\bgh[pousr]_[A-Za-z0-9]{20,}|\bgithub_pat_[A-Za-z0-9_]{20,}|\bsk-[A-Za-z0-9_-]{20,}"
    r"|\bAKIA[0-9A-Z]{16}\b|\bxox[abprs]-[A-Za-z0-9-]{10,}"
    r"|\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"
    r"|\b\d{8,10}:[A-Za-z0-9_-]{35}\b|(?i:\bBearer)\s+[A-Za-z0-9._~+/=-]{16,}"
)
_SECRET_KEY = re.compile(rf"(?i)(?:authorization|{_SECRET_NAMES})")
_REDACTED = "[REDACTED]"


class CursorError(ValueError):
    """The supplied cursor is malformed."""


def redact(value: Any) -> Any:
    """Remove credential assignments and recognizable credential shapes from remote data."""
    if isinstance(value, str):
        return _TOKEN_SHAPES.sub(_REDACTED, _ASSIGNMENT.sub(lambda match: f"{match.group(1)}={_REDACTED}", value))
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        return {key: (_REDACTED if isinstance(key, str) and _SECRET_KEY.fullmatch(key) else redact(item))
                for key, item in value.items()}
    return value


def _event(kind: str, identity: str, occurred_at: str, target: dict[str, str], data: dict[str, Any]) -> dict[str, Any]:
    event_id = "evt_" + hashlib.sha256(f"{kind}\0{identity}".encode()).hexdigest()
    return {"schemaVersion": 1, "id": event_id, "cursor": "", "type": kind,
            "occurredAt": _utc_timestamp(occurred_at), "target": target,
            "data": redact(data), "dedupeKey": event_id}


def _utc_timestamp(stamp: str | None) -> str:
    """Normalize timestamps to RFC 3339 UTC; legacy naive values mean laptop-local time."""
    try:
        parsed = dt.datetime.fromisoformat(stamp.replace("Z", "+00:00")) if stamp else None
    except (ValueError, AttributeError):
        parsed = None
    if parsed is None:
        return "1970-01-01T00:00:00Z"
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    return parsed.astimezone(dt.UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _seconds(stamp: str | None) -> float | None:
    try:
        parsed = dt.datetime.fromisoformat(stamp.replace("Z", "+00:00")) if stamp else None
        return parsed.astimezone(dt.UTC).timestamp() if parsed else None
    except (ValueError, AttributeError):
        return None


def _run_target(project: str, req: str, **extra: str) -> dict[str, str]:
    return {"kind": "run", "project": project, "req": req, **{key: value for key, value in extra.items() if value}}


def _task_target(project: str, req: str, task: str | None = None, attempt: str | None = None) -> dict[str, str]:
    return {"kind": "task", "project": project, "req": req,
            **({"taskId": task} if task else {}), **({"attemptId": attempt} if attempt else {})}


def _retry_exhausted(value: dict[str, Any]) -> bool:
    used = value.get("attempts_used", value.get("attemptsUsed"))
    maximum = value.get("max_attempts", value.get("maxAttempts"))
    remaining = value.get("retries_remaining", value.get("retriesRemaining"))
    if (not isinstance(used, int) or isinstance(used, bool) or used < 1
            or not isinstance(maximum, int) or isinstance(maximum, bool) or maximum < 1 or used < maximum):
        return False
    return (value.get("retry_exhausted") is True or value.get("retryExhausted") is True
            or (isinstance(remaining, int) and not isinstance(remaining, bool) and remaining == 0)
            or (value.get("state") == "blocked" and value.get("reason") == "attempts_exhausted"))


def build_events(state: dict[str, Any], now: float | None = None) -> list[dict[str, Any]]:
    """Derive stable events from current run state and explicit notification fixtures."""
    out: list[dict[str, Any]] = []
    state_failure_targets: set[tuple[str, str, str]] = set()
    for run in state.get("runs", []):
        project, req = run.get("project", ""), run.get("req_id", "")
        for task in run.get("tasks", []):
            exhausted = _retry_exhausted(task)
            terminal_attempt = task.get("attempt")
            terminal_attempt_id = terminal_attempt.get("id") if isinstance(terminal_attempt, dict) else None
            attempts = [attempt for attempt in [task.get("attempt"), *(task.get("history") or [])]
                        if isinstance(attempt, dict) and attempt.get("id")]
            for attempt in {item["id"]: item for item in attempts}.values():
                if exhausted and terminal_attempt_id and attempt["id"] != terminal_attempt_id:
                    continue
                target = _task_target(project, req, task.get("id"), attempt["id"])
                identity = f"{project}/{req}:{task.get('id', '')}:{attempt['id']}"
                occurred_at = attempt.get("ended_at") or attempt.get("last_activity_at") or run.get("updated_at") or ""
                data = {"title": task.get("title"), "failure": attempt.get("failure"),
                        "verdict": attempt.get("verdict")}
                if attempt.get("state") in {"rejected", "failed"} or attempt.get("failure"):
                    if exhausted:
                        data.update({"retryExhausted": True,
                                     "attemptsUsed": task.get("attempts_used", task.get("attemptsUsed",
                                                                  task.get("attempts"))),
                                     "maxAttempts": task.get("max_attempts", task.get("maxAttempts")),
                                     "retriesRemaining": task.get("retries_remaining",
                                                                   task.get("retriesRemaining", 0))})
                        out.append(_event("attempt.failed", identity, occurred_at, target, data))
                        state_failure_targets.add((project, req, str(task.get("id", ""))))
                elif attempt.get("state") == "blocked":
                    out.append(_event("attempt.blocked", identity, occurred_at, target, data))
                elif attempt.get("live") and now is not None:
                    last = _seconds(attempt.get("last_activity_at"))
                    if last is not None and now - last > STALL_SECONDS:
                        out.append(_event("attempt.stalled", f'{identity}:{attempt["last_activity_at"]}',
                                          attempt["last_activity_at"], target, data))
        if run.get("status") in RUN_DONE and not run.get("active"):
            updated_at = run.get("updated_at") or ""
            out.append(_event("run.finished", f"{project}/{req}:{updated_at}", updated_at,
                              _run_target(project, req), {"title": run.get("title"), "status": run["status"]}))

    for decision in state.get("decisions", []):
        request = decision["request"]
        project, req = decision["project"], decision["req"]
        identity = f"{project}/{req}:{request['id']}"
        out.append(_event("plan.waiting", identity, decision.get("at", ""),
                          _task_target(project, req, request.get("task"), request.get("attempt")),
                          {"decisionRequest": {"id": request["id"], "title": request.get("title"),
                                                "what": request.get("what"), "reason": request.get("reason"),
                                                "options": [option.get("id") for option in request.get("options", [])],
                                                "recommended": request.get("recommended")}}))
    for round_ in state.get("rounds", []):
        project, req, number = round_["project"], round_["req"], str(round_["round"])
        out.append(_event("round.waiting", f"{project}/{req}:{number}", round_.get("at", ""),
                          {"kind": "round", "project": project, "req": req, "roundId": number}, {"round": number}))
    for plan in state.get("plans", []):
        if plan.get("plan_status") in {"proposed", "awaiting_approval", "review"}:
            project, req = plan.get("project", ""), plan.get("req_id", "")
            updated_at = plan.get("updated_at") or ""
            out.append(_event("plan.waiting", f"{project}/{req}:{updated_at}", updated_at,
                              {"kind": "plan", "project": project, "req": req}, {"title": plan.get("title")}))
    for quota in state.get("quotas", []):
        until = quota.get("exhausted_until")
        if until:
            out.append(_event("quota.exhausted", f'{quota.get("profile")}:{until}', quota.get("observed_at", ""),
                              {"kind": "system"}, {"profile": quota.get("profile"), "until": until}))
    for command in state.get("commands", []):
        try:
            raw_target = command.get("target") or "{}"
            target = json.loads(raw_target) if isinstance(raw_target, str) else raw_target
        except ValueError:
            target = raw_target
        except TypeError:
            continue
        if isinstance(target, str):
            project, separator, req = target.partition("/")
            target = _run_target(project, req) if separator and project and req else {}
        if not isinstance(target, dict) or target.get("kind") not in {"run", "attempt", "task", "plan", "round"}:
            continue
        identity = f'{command.get("idempotency_key", "")}:{command.get("outcome", "")} '
        out.append(_event("command.updated", identity.strip(), command.get("created_at", ""), target,
                          {"command": command.get("command"), "outcome": command.get("outcome"),
                           "origin": command.get("origin")}))
    for offline in state.get("offline", []):
        since = offline.get("since")
        if since:
            out.append(_event("laptop.offline", since, since, {"kind": "system"}, {"since": since}))
    for row in state.get("flow", []):
        event = from_flow(row)
        if event is not None and not (
            event["type"] in {"attempt.failed", "attempt.blocked"}
            and (event["target"].get("project", ""), event["target"].get("req", ""),
                 event["target"].get("taskId", "")) in state_failure_targets
        ):
            out.append(event)

    out.sort(key=lambda event: (event["occurredAt"], event["id"]))
    for ordinal, event in enumerate(out, 1):
        event["cursor"] = json.dumps(["v2", str(ordinal), event["id"]], ensure_ascii=False)
    return out


def from_flow(row: dict[str, Any]) -> dict[str, Any] | None:
    """Map actionable flow bus transitions to notification events."""
    data = row.get("data") if isinstance(row.get("data"), dict) else {}
    kind = row.get("remote_type")
    if kind is None:
        state = data.get("state", row.get("state"))
        kind = {("state_change", "failed"): "attempt.failed", ("state_change", "rejected"): "attempt.failed",
                ("attempt_transition", "failed"): "attempt.failed",
                ("attempt_transition", "rejected"): "attempt.failed",
                ("task_state", "blocked"): "attempt.blocked", ("verdict", "failed"): "attempt.failed",
                ("verdict", "rejected"): "attempt.failed"}.get((row.get("kind"), state))
    if kind not in NOTIFICATION_KINDS:
        return None
    target = _run_target(str(row.get("project", "unknown")), str(row.get("req", "REQ-000")))
    if row.get("run"):
        project, _, req = str(row["run"]).partition("/")
        target = _run_target(project, req or "REQ-000")
    if row.get("task"):
        target = _task_target(target["project"], target["req"], str(row["task"]),
                              str(row.get("attempt") or ""))
    source_id = str(row.get("id") or row.get("ord") or row.get("seq") or "")
    identity = f'{target["project"]}/{target["req"]}:{source_id}'
    payload = data or {key: row[key] for key in ("failure", "summary") if row.get(key) is not None}
    if kind == "attempt.failed":
        retry_facts = {**row, **payload}
        if not _retry_exhausted(retry_facts):
            return None
        payload = {**payload, "retryExhausted": True,
                   "attemptsUsed": retry_facts.get("attempts_used", retry_facts.get("attemptsUsed")),
                   "maxAttempts": retry_facts.get("max_attempts", retry_facts.get("maxAttempts")),
                   "retriesRemaining": retry_facts.get("retries_remaining", retry_facts.get("retriesRemaining", 0))}
    return _event(kind, identity, str(row.get("at") or row.get("occurredAt") or ""), target, payload)


def page(events: list[dict[str, Any]], after: str = "", limit: int = 200) -> dict[str, Any]:
    """Return a deterministic page strictly after the opaque cursor."""
    if after:
        try:
            key = json.loads(after)
            if not isinstance(key, list) or not all(isinstance(item, str) for item in key):
                raise ValueError
            if len(key) == 3 and key[0] == "v2":
                sequence = int(key[1])
                events = [event for event in events
                          if _cursor_sequence(event["cursor"]) > (sequence, key[2])]
            elif len(key) == 2:  # accept cursors issued before the observation-order format
                events = [event for event in events if [event["occurredAt"], event["id"]] > key]
            else:
                raise ValueError
        except (ValueError, TypeError):
            raise CursorError("El cursor no es válido.") from None
    selected = events[:limit]
    return {"events": selected, "nextCursor": selected[-1]["cursor"] if selected else after,
            "hasMore": len(events) > limit}


def _cursor_sequence(cursor: str) -> tuple[int, str]:
    """Decode an event's persisted observation cursor."""
    try:
        version, sequence, event_id = json.loads(cursor)
        if version != "v2":
            return 0, event_id
        return int(sequence), event_id
    except (ValueError, TypeError):
        return 0, ""


def _observe(root, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Persist first-observation order so late-derived events follow existing cursors."""
    path = root / ".state" / "remote-events.sqlite3"
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    try:
        with connection:
            connection.execute("CREATE TABLE IF NOT EXISTS observed_events ("
                               "id TEXT PRIMARY KEY, sequence INTEGER NOT NULL UNIQUE)")
            connection.execute("BEGIN IMMEDIATE")
            sequence = connection.execute("SELECT COALESCE(MAX(sequence), 0) FROM observed_events").fetchone()[0]
            for event in events:
                sequence += 1
                connection.execute("INSERT OR IGNORE INTO observed_events(id, sequence) VALUES (?, ?)",
                                   (event["id"], sequence))
            rows = dict(connection.execute("SELECT id, sequence FROM observed_events"))
    finally:
        connection.close()
    for event in events:
        event["cursor"] = json.dumps(["v2", str(rows[event["id"]]), event["id"]], ensure_ascii=False)
    return sorted(events, key=lambda event: _cursor_sequence(event["cursor"]))


def collect(root, runs: list[dict[str, Any]], plans: list[dict[str, Any]], quotas: list[dict[str, Any]],
            commands: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collect live flow events and open decisions/rounds, then project notification events."""
    import bt_plans_api
    import bt_live_api
    import bt_rounds
    import time

    decisions, rounds = [], []
    for plan in plans:
        rdir = bt_plans_api.req_dir(root, plan["project"], plan["req_id"])
        at = plan.get("updated_at") or ""
        decisions.extend({"project": plan["project"], "req": plan["req_id"], "request": request, "at": at}
                         for request in bt_plans_api.open_decisions(rdir))
        for number in bt_plans_api.open_rounds(rdir):
            round_path = bt_rounds.rounds_dir(rdir) / f"round-{number:02d}.json"
            try:
                round_data = bt_rounds.load(round_path)
            except (OSError, ValueError):
                round_data = {}
            round_at = round_data.get("created_at") if isinstance(round_data, dict) else None
            if not isinstance(round_at, str) or not round_at:
                round_at = at
            rounds.append({"project": plan["project"], "req": plan["req_id"], "round": number,
                           "at": round_at})
    flow, _, _ = bt_live_api.flow_events(root, "global")
    offline = []
    events = build_events({"runs": runs, "plans": plans, "quotas": quotas, "commands": commands,
                           "decisions": decisions, "rounds": rounds, "offline": offline, "flow": flow},
                          now=time.time())
    return _observe(root, events)
