"""Scheduler attempts in the attempt log: the projection that lets `metrics`, the advice and the router learn from them.

The attempt log (`bt_events`) was written only by the legacy marathon, so a Scheduler run (dozens of attempts, every one
verified) taught the router nothing. This module reads the run's own records (`bt_attempt_facts`: who ran, how long,
how many tokens, how it ended) and appends one row per judged attempt, idempotently, in the same schema.

What an attempt is worth is decided here, from the plan:
  - rejected by its verifier ................ `verify_failed`
  - accepted and named by an audit's finding  `verify_failed`, outcome `audit_rejected` (the independent audit proved
                                               the accepted result wrong: the strongest quality signal there is)
  - ... but the audit named more tasks than .. `stopped`, outcome `systemic_audit_finding`: a defect that wide belongs to
    `gates.attribute_max_tasks` at once         the plan or the integration, and charging every builder for it would
                                               teach the router that a sound model is a bad one
  - accepted and reset with no finding on it . `stopped` (redone because something upstream was, or by the owner)
  - accepted and every audit over it passed .. `verified` (survived the audit; with no audit over it, at once)
  - accepted, an audit over it still pending . not written yet (it is not judged until the audit speaks)
  - an audit attempt rejected by the gate .... `stopped` (unjudged: it did its job by finding problems in OTHER tasks)
  - start refused, killed, cancelled ......... `stopped` (infrastructure, nobody's quality)

Nothing here writes to a run or to M1; recording never raises.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Any

import bt_attempt_facts as facts_
import bt_events
import bt_profiles
import bt_run_stores

SIZE = {"low": "S", "medium": "M", "high": "L", "extreme": "L"}
AUDIT_GATE = "audit gate:"


def _ancestors(tasks: dict[str, dict]) -> dict[str, set[str]]:
    memo: dict[str, set[str]] = {}

    def of(task_id: str, trail: tuple = ()) -> set[str]:
        if task_id in memo:
            return memo[task_id]
        found: set[str] = set()
        for parent in (tasks.get(task_id) or {}).get("after") or []:
            if parent in tasks and parent not in trail:
                found |= {parent} | of(parent, (*trail, task_id))
        memo[task_id] = found
        return found

    return {task_id: of(task_id) for task_id in tasks}


def audits_over(tasks: dict[str, dict]) -> dict[str, set[str]]:
    """{task id: the audit tasks that stand downstream of it}. An audit is the independent check of what precedes it."""
    ancestors = _ancestors(tasks)
    audits = [tid for tid, spec in tasks.items() if spec.get("kind") == "audit"]
    return {tid: {audit for audit in audits if tid in ancestors[audit]} for tid in tasks}


DEFAULT_ATTRIBUTE_MAX = 3


def overturn_of(task_id: str, ended_at: float | None, reworks: list[dict], max_named: int = DEFAULT_ATTRIBUTE_MAX
                ) -> str | None:
    """How a later rework treated an accepted result: `audit` (a finding of the audit gate named this task), `systemic`
    (it named it, but together with more than `max_named` tasks) or `reset` (sent back with no finding on it); None when
    no rework followed it. `reworks`: M1's `rework_requested` rows."""
    for event in reworks:
        if ended_at is not None and event["at"] <= ended_at:
            continue
        if task_id in event["tasks"]:
            if event["by"] != "audit-gate" or task_id not in event["named"]:
                return "reset"
            return "audit" if len(event["named"]) <= max_named else "systemic"
    return None


def judge(attempt: dict, overturn: str | None, task_done: bool, audits_passed: bool, kind: str) -> tuple[str, str] | None:
    """(result, outcome) of one attempt, or None while it is not judged yet."""
    state, failure = attempt.get("state"), attempt.get("failure") or ""
    if state == "accepted":
        if overturn:
            return {"audit": ("verify_failed", "audit_rejected"), "systemic": ("stopped", "systemic_audit_finding"),
                    "reset": ("stopped", "reset_by_rework")}[overturn]
        return ("verified", "verified") if task_done and audits_passed else None
    if state == "rejected":
        if kind == "audit" and failure.startswith(AUDIT_GATE):
            return "stopped", "gate_found_problems"
        return "verify_failed", "verify_failed"
    if state == "failed":
        infrastructure = failure.startswith(("start rejected", "killed"))
        return ("stopped", "infrastructure") if infrastructure else ("failed", "failed")
    if state == "cancelled":
        return "stopped", "cancelled"
    return None


def _usage(tokens: dict | None) -> dict[str, Any]:
    reported = tokens or {}
    fields = {"input_tokens": reported.get("input"), "output_tokens": reported.get("output"),
              "total_tokens": reported.get("total")}
    known = any(value is not None for value in fields.values())
    return {"source": "provider_reported" if known else None, "quality": "reported" if known else "unknown",
            **fields, "cache_read_tokens": None, "cache_write_tokens": None, "reasoning_tokens": None,
            "cost_usd_reported": None}


def _serial(attempt_id: str, fallback: int) -> int:
    """`att-0109` -> 109: the run-wide serial of an attempt, which the log's `session` field carries."""
    tail = str(attempt_id).rsplit("-", 1)[-1]
    return int(tail) if tail.isdigit() else fallback


def event_id(project: str, req: str, run_id: str, attempt_id: str, result: str) -> str:
    return hashlib.sha1(f"scheduler|{project}|{req}|{run_id}|{attempt_id}|{result}".encode()).hexdigest()[:16]


def rows(project: str, req: str, plan_tasks: dict[str, dict], doc: dict, facts: dict[str, list[dict]],
         now: str, reworks: list[dict] | None = None, max_named: int = DEFAULT_ATTRIBUTE_MAX) -> list[dict]:
    """Every judged attempt of a run as an attempt-log row. Pure: the caller supplies the plan, M1's document, the
    attempt facts and the timestamp."""
    run_id = hashlib.sha1(f"{doc.get('plan_id')}|{doc.get('created_at')}".encode()).hexdigest()[:12]
    over = audits_over(plan_tasks)
    task_states = {tid: (rec or {}).get("state") for tid, rec in (doc.get("tasks") or {}).items()}
    out = []
    for task_id, attempts in facts.items():
        spec = plan_tasks.get(task_id) or {}
        kind = spec.get("kind") or "implement"
        audits_passed = all(task_states.get(audit) == "completed" for audit in over.get(task_id, ()))
        for index, attempt in enumerate(attempts):
            ended = facts_._epoch(attempt.get("ended_at"))
            verdict = judge(attempt, overturn_of(task_id, ended, reworks or [], max_named),
                            task_states.get(task_id) == "completed", audits_passed, kind)
            if verdict is None:
                continue
            result, outcome = verdict
            route = attempt.get("route") or {}
            number = attempt.get("number") if isinstance(attempt.get("number"), int) else index + 1
            out.append({
                "schema": bt_events.SCHEMA, "event_id": event_id(project, req, run_id, attempt["attempt"], result),
                "run_id": run_id, "attempt_epoch": 0, "ts": now, "project": project,
                "work": bt_profiles.is_work_project(project), "req": req, "task": task_id,
                "session": _serial(attempt["attempt"], number),
                "agent": route.get("provider"), "profile": route.get("profile"),
                "model": route.get("model"), "requested_model": route.get("model"),
                "reported_model": attempt.get("model_reported"), "identity_source": "m2-ledger" if route.get("source") else "unknown",
                "effort": route.get("effort"), "kind": kind, "tier": None, "tasks": [task_id],
                "seconds": attempt.get("duration_s"), "rc": None, "timed_out": False, "stopped": result == "stopped",
                "early_exit": False, "recovered": False, "result": result, "usage": _usage(attempt.get("tokens")),
                "route_why": None, "loss": None,
                "error_excerpt": None if result == "verified" else (attempt.get("failure") or "")[:300] or None,
                "change_size": None, "origin": "real", "source": "scheduler", "decision": None,
                "complexity": SIZE.get(spec.get("complexity")), "complexity_source": "declared", "attempt": number,
                "milestone": spec.get("milestone_id"), "task_results": None, "task_outcomes": None,
                "titles": [str(spec.get("title") or "")[:90]], "outcome": outcome, "why": None,
            })
    return out


def rework_events(db: Path) -> list[dict]:
    """M1's `rework_requested` audit rows, oldest first: {at, by, named, tasks}. [] when the log cannot be read."""
    import json
    import sqlite3

    try:
        conn = sqlite3.connect(f"{Path(db).resolve().as_uri()}?mode=ro", uri=True, timeout=0.2)
        try:
            found = conn.execute("SELECT at, detail FROM audit WHERE kind = 'rework_requested' ORDER BY seq").fetchall()
        finally:
            conn.close()
    except (sqlite3.Error, OSError):
        return []
    out = []
    for at, detail in found:
        try:
            body = json.loads(detail)
        except ValueError:
            continue
        out.append({"at": float(at), "by": str(body.get("by") or ""), "named": set(body.get("named") or ()),
                    "tasks": set(body.get("tasks") or ())})
    return out


def _max_named() -> int:
    import bt_config

    value = bt_config.get("gates.attribute_max_tasks", DEFAULT_ATTRIBUTE_MAX)
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 1 else DEFAULT_ATTRIBUTE_MAX


def sync(project: str, req: str, rdir: Path, now: str | None = None) -> int:
    """Append the judged attempts of the run in `rdir` that the log does not hold yet; how many were written."""
    import datetime as dt
    import json

    try:
        rdir = Path(rdir)
        plan = json.loads((rdir / "PLAN.json").read_text(encoding="utf-8"))
        plan_tasks = {task["id"]: task for task in plan.get("tasks", []) if isinstance(task, dict) and "id" in task}
        m1 = bt_run_stores.paths(rdir)["m1"]
        doc = facts_.core_document(m1)
        stamp = now or dt.datetime.now().astimezone().isoformat(timespec="seconds")
        written, known = 0, bt_events.known_event_ids()
        import bt_remediation

        reworks = sorted([*rework_events(m1), *bt_remediation.events(rdir)], key=lambda event: event["at"])
        for row in rows(project, req, plan_tasks, doc, facts_.attempt_facts(rdir), stamp, reworks, _max_named()):
            if bt_events.append_row(row, known) is not None:
                written += 1
        return written
    except Exception as exc:  # noqa: BLE001 - telemetry never stops a run
        print(f"[attempt-log] not synced: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 0
