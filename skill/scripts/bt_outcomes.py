"""Task outcomes: what each task of a session was worth, separated from what the session cost.

A *session attempt* is one provider run (`bt_events` row): it owns the time, the tokens and the aggregate result. A
*task outcome* is the verified verdict of one task that ran in it. Learning and quality read outcomes; consumption reads
sessions, so a session of three tasks costs once and yields three verdicts (never three costs, never one failure
standing in for three).

Verdicts: `verified` (the supervisor's verification passed), `failed` (the agent or its verification failed),
`provider_loss` (quota, credits or sign-in: not the model's quality), `skipped` (never reached) and `unjudged`
(claimed, blocked, escalated, stopped or without verdict: neither a success nor a failure). Rows written before
per-task data existed stay readable: `task_results` gives one outcome per task, a bare row one outcome per session
(`granularity: session`), and a legacy aggregate `partial` is unjudged instead of a failure.

Identity: an outcome is (project, run_id, task, attempt number); a recovered or replayed row of the SAME run repeats it
and is dropped, one task is verified at most once per run (whatever model repeats it after a restart), and a new run of
the same REQ has another run_id so it never collides. Legacy rows without `run_id` are not merged at all: they cannot
prove they belong to one run, so each counts as recorded (a documented limit of the old history).
"""
from __future__ import annotations

import hashlib

VERIFIED_RESULTS = ("done", "verified")
FAILED_RESULTS = ("failed", "verify_failed", "timeout")
SKIPPED_RESULTS = ("skipped",)


def verdict_of(result: object, loss: object = None) -> str:
    if result in VERIFIED_RESULTS:
        return "verified"
    if result in SKIPPED_RESULTS:
        return "skipped"
    if result in FAILED_RESULTS:
        return "provider_loss" if loss else "failed"
    return "unjudged"


def _identity(row: dict, task: str | None, attempt: object) -> str:
    """Stable id of one task outcome: (project, run_id, task, attempt). Rows written before `run_id` existed cannot
    tell two runs of the same REQ apart, so they are never merged: each legacy session is its own outcome source."""
    project, run_id = row.get("project"), row.get("run_id")
    if run_id and project and task and attempt is not None:
        return hashlib.sha1(f"{project}|{run_id}|{row.get('attempt_epoch') or 0}|{task}|{attempt}".encode()).hexdigest()[:16]
    return f"{row.get('event_id') or id(row)}:{task}"  # no run/attempt identity: only ever itself


def _tasks_of(row: dict) -> list[dict]:
    """[{id, kind, result, attempt, granularity}] of one session row, whatever generation it is."""
    kind = row.get("kind") or "implement"
    declared = row.get("task_outcomes")
    if isinstance(declared, list) and declared:
        # `kind` is the SESSION's: the route (model, effort) was chosen for that kind, and reports group the same way
        return [{"id": t.get("id"), "kind": kind, "result": t.get("result"),
                 "attempt": t.get("attempt"), "granularity": "task"} for t in declared if isinstance(t, dict)]
    results = row.get("task_results")
    if isinstance(results, dict) and results:
        return [{"id": tid, "kind": kind, "result": res, "attempt": row.get("attempt"), "granularity": "task"}
                for tid, res in results.items()]
    result = row.get("result")
    if result == "partial":  # legacy aggregate with no per-task detail: it says neither which tasks passed nor failed
        result = "unjudged_partial"
    if row.get("outcome") == "claimed_unverified" and result in VERIFIED_RESULTS:
        result = "claimed"  # the row's finer outcome class says the claim was never verified
    return [{"id": row.get("task"), "kind": kind, "result": result, "attempt": row.get("attempt"),
             "granularity": "session"}]


def outcomes(rows: list[dict]) -> list[dict]:
    """Deduplicated task outcomes of the real (non-synthetic) session rows, in row order."""
    seen: set[str] = set()
    verified_tasks: set[tuple] = set()
    out = []
    for row in rows:
        if not isinstance(row, dict) or row.get("origin") == "synthetic" or not isinstance(row.get("result"), str):
            continue
        tasks = _tasks_of(row)
        for t in tasks:
            oid = _identity(row, t["id"], t["attempt"])
            verdict = verdict_of(t["result"], row.get("loss"))
            unique = (row.get("project"), row.get("run_id"), t["id"])
            if oid in seen:
                continue
            if verdict == "verified" and all(unique):
                if unique in verified_tasks:
                    continue  # the same task verified again after a restart or a replay: one completed task
                verified_tasks.add(unique)
            seen.add(oid)
            out.append({"outcome_id": oid, "event_id": row.get("event_id"), "task": t["id"], "verdict": verdict,
                        "result": t["result"], "kind": t["kind"], "granularity": t["granularity"],
                        "retry": isinstance(t["attempt"], int) and t["attempt"] > 1,
                        "session_tasks": len(tasks), "ts": row.get("ts"), "row": row})
    return out


def counts(rows: list[dict], by: tuple = ("agent", "model", "effort", "kind")) -> dict[tuple, dict]:
    """Verdict counts per group of `by` fields (`kind` is the session's). `judged` = verified + failed:
    provider losses, skips and unjudged results never enter a success rate."""
    groups: dict[tuple, dict] = {}
    for o in outcomes(rows):
        key = tuple((o["row"].get(k) or "implement") if k == "kind" else o["row"].get(k) for k in by)
        g = groups.setdefault(key, {"verified": 0, "failed": 0, "provider_loss": 0, "skipped": 0, "unjudged": 0,
                                    "retries": 0})
        g[o["verdict"]] += 1
        g["retries"] += o["retry"]
    for g in groups.values():
        g["judged"] = g["verified"] + g["failed"]
    return groups
