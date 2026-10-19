"""Scheduler attempts as `bt_events` schema-2 rows, derived on demand and never written.

The marathon driver appended attempt rows to `.state/events`; Scheduler attempts never did, so `/metrics` and the
per-model pages went stale as runs moved to the Scheduler. Instead of making a second writer (and tying the module
runtime to the marathon's telemetry, which P-001 is retiring), the rows are rebuilt read-only from the per-attempt
read model (`bt_attempt_facts`). Only finished attempts become rows; a live attempt is not an outcome yet.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import bt_attempt_facts as facts
import bt_planstatus as planstatus
import bt_scheduler_adapter as scheduler_

# attempt state -> `result` in the marathon vocabulary (bt_events.OUTCOMES knows these)
RESULT = {"accepted": "done", "rejected": "verify_failed", "failed": "failed", "cancelled": "stopped"}
_LEVEL_LETTER = {"low": "S", "medium": "M", "high": "L", "extreme": "L"}


def _usage(tokens: dict | None, model_reported: str | None) -> dict[str, Any]:
    out = {"source": None, "quality": "unknown", "input_tokens": None, "output_tokens": None,
           "cache_read_tokens": None, "cache_write_tokens": None, "reasoning_tokens": None, "total_tokens": None,
           "cost_usd_reported": None}
    if not tokens:
        return out
    # Only the provider's own total is a final measurement (bt_usage `total_only`); the parts M4 saw alone are a lower
    # bound (`partial`, never summed): a provider's total convention (cache in or out of input) is not M4's to guess.
    if tokens.get("total") is not None:
        out.update(source="m4-provider-reported", total_tokens=tokens["total"], quality="total_only")
    else:
        out.update(source="m4-provider-reported", input_tokens=tokens.get("input"),
                   output_tokens=tokens.get("output"), quality="partial")
    return out


def row_of(project: str, req: str, task: dict[str, Any], attempt: dict[str, Any]) -> dict[str, Any] | None:
    result = RESULT.get(attempt.get("state"))
    if result is None:
        return None
    route = attempt["route"]
    level = task.get("complexity")
    return {
        "schema": 2, "event_id": f"scheduler:{project}:{req}:{attempt['attempt']}", "run_id": None,
        "ts": attempt.get("ended_at") or attempt.get("started_at"), "project": project, "work": False, "req": req,
        "task": attempt["task"], "session": attempt.get("number"), "agent": route["provider"],
        "profile": route["profile"], "model": route["model"], "requested_model": route["model"],
        "reported_model": attempt.get("model_reported"), "identity_source": route.get("source") if route["model"] else None,
        "effort": route["effort"], "kind": task.get("kind") or "implement", "tier": None,
        "tasks": [attempt["task"]], "seconds": attempt.get("duration_s"), "rc": None, "timed_out": False,
        "stopped": result == "stopped", "early_exit": False, "recovered": False, "result": result,
        "usage": _usage(attempt.get("tokens"), attempt.get("model_reported")),
        "route_why": None, "loss": None, "error_excerpt": attempt.get("failure") or None, "change_size": None,
        "origin": "scheduler", "decision": None, "complexity": _LEVEL_LETTER.get(level), "complexity_source": "declared",
        "attempt": attempt.get("number"), "milestone": task.get("milestone_id"), "task_results": None,
        "task_outcomes": None, "titles": [task.get("title") or attempt["task"]],
        "outcome": {"done": "verified", "verify_failed": "verify_failed", "failed": "failed",
                    "stopped": "stopped_by_user"}[result], "why": attempt.get("failure") or None}


def rows(root: Path | None = None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for project, rdir in planstatus._requirement_dirs(planstatus._root(root)):
        if scheduler_.authority(rdir) != "scheduler":
            continue
        status = planstatus.plan_status(project, rdir)
        tasks = {t["id"]: t for m in status["milestones"] for t in m["tasks"]}
        for tid, attempts in facts.attempt_facts(rdir).items():
            for attempt in attempts:
                row = row_of(project, status["req_id"], tasks.get(tid, {}), attempt)
                if row:
                    out.append(row)
    out.sort(key=lambda r: r.get("ts") or "")
    return out
