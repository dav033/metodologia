"""Detect durable Solucionador triggers independently of session launching and supervision.

Triggers (`Trigger`), each launched at most once per key:
- `decision`: healing left an open decision for the owner (limit reached, diagnosis failed, low confidence, an option
  the diagnosis chose that is not offered, the plan blamed, no retry offered at all) — `healing.heal(escalate=...)`;
- `repeat`: the failure signature healing already answered came back in a later round;
- `stuck`: a PENDING task whose state did not move for `solver.stuck_minutes` beyond its known waits (a running agent
  gets `scheduler.attempt_timeout_minutes` more, a quota wait counts from its `until`, a pause or a decision never);
- `error`: the run workflow ended in ERROR;
- `stalled`: the run workflow is PENDING and not paused, but no task workflow is live (nothing runs, waits for quota or
  recovers) and no decision is open, unchanged for `solver.stuck_minutes`: pictures REQ-021 r25 sat like that while gate
  CG-7's composition failed every turn (a GitCommandError), and no other trigger saw it (2026-10-29);
- `ended`: the run workflow ended (SUCCESS) with a rejected composition gate, or `blocked` with a blocked task the owner
  did not stop himself (`decision_answered … stop by owner` in the telemetry, or `by: owner` in RUN.decisions.jsonl):
  r25 then ended at 23:19 with CG-7 rejected («COMPOSE_FAILED 3 turns»), no decision open and no ERROR. Fired at once,
  once per run workflow and rejected-gate/blocked-task set;
- `blocked`: the run, still PENDING and not paused, holds a task `blocked` with no decision behind it (an audit whose
  blocking findings no round could clear, `workflows._audit_stuck`) for `solver.blocked_after_seconds`: pictures REQ-021
  r27's T2.7 sat like that from 14:49 while other tasks kept running, so neither `stalled` nor `ended` saw it and no
  decision was open (2026-10-30). Once per block (the task's round workflow and the run's reason); a block already given
  to the Solucionador is not given again by `stalled` or `ended`;
- `resolution`: a composition conflict waits in `<state>/composition/resolutions/<key>.json` without `<key>.resolved`
  for `solver.resolution_after_seconds` (`bt_durable.resolutions`): no retry can settle it.
"""
from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Iterable
from pathlib import Path

ERRORED = frozenset({"ERROR", "MAX_RECOVERY_ATTEMPTS_EXCEEDED"})
QUIET = frozenset({"paused", "needs_decision"})


def _iso(epoch: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(epoch))


def trigger(kind: str, key: str, run_id: str, *, task_id: str = "", request_id: str = "", round_no: int | None = None,
            reason: str = "") -> dict:
    return {"kind": kind, "key": key, "run_id": run_id, "task_id": task_id, "request_id": request_id,
            "round": round_no, "reason": reason[:400]}


def error_triggers(run, status: dict) -> list[dict]:
    if status.get("workflow_status") in ERRORED:
        workflow = status.get("workflow_id") or f"bt:{run.run_id}"
        return [trigger("error", f"{run.run_id}:error:{workflow}", run.run_id,
                        reason=f"the run workflow {workflow} ended in {status['workflow_status']}")]
    return []


def _live_tasks(status: dict) -> list[str]:
    """Task workflows that still run (each is watched by `stuck_triggers`, or waits for the owner's decision)."""
    return [t for t, item in (status.get("tasks") or {}).items()
            if (item or {}).get("workflow_status") in ("PENDING", "ENQUEUED")]


def stalled_triggers(run, status: dict, state: dict, now: float, cfg: dict, handed: Iterable[str] = ()) -> list[dict]:
    """A PENDING, unpaused run workflow with no live task workflow, unchanged (summary and gates) for `stuck_minutes`.
    The `since` mark starts when the picture last changed, so an engine restart or a deploy never fires it at once.
    A stall whose only stops are blocks already given to the Solucionador (`handed`, `blocked_triggers`) is not a new
    block. Updates `state["stall"]`."""
    summary = status.get("summary") if isinstance(status.get("summary"), dict) else None
    # no summary: the run workflow has not set its first one (it sets one before anything else), nothing to judge yet
    if status.get("workflow_status") != "PENDING" or not summary or summary.get("status") == "paused" \
            or _live_tasks(status):
        state.pop("stall", None)
        return []
    basis = json.dumps([status.get("workflow_id"), summary.get("status"), summary.get("tasks"), summary.get("gates")],
                       sort_keys=True, default=str)
    fingerprint = hashlib.sha256(basis.encode()).hexdigest()[:16]
    mark = state.get("stall") or {}
    if mark.get("fp") != fingerprint:
        state["stall"] = mark = {"fp": fingerprint, "since": now}
    since = float(mark.get("since", now))
    if now < since + cfg["stuck_minutes"] * 60:
        return []
    stopped = {t for t, value in (summary.get("tasks") or {}).items() if value in ("blocked", "cancelled")}
    if stopped and stopped <= set(handed) and not (summary.get("gates") or {}).get("rejected"):
        return []
    rejected = ", ".join(sorted((summary.get("gates") or {}).get("rejected") or {}))
    return [trigger("stalled", f"{run.run_id}:stalled:{fingerprint}", run.run_id,
                    reason=f"the run workflow {status.get('workflow_id')} is PENDING with no live task and no open "
                           f"decision since {_iso(since)}" + (f"; rejected gates: {rejected}" if rejected else ""))]


def owner_stops(rdir: Path, telemetry: Path | None, run_id: str) -> set[str]:
    """Tasks the owner himself stopped: a durable `decision_answered` with action `stop` by `owner` (telemetry), or a
    `stop` answered `by: owner` in the legacy answers file (RUN.decisions.jsonl)."""
    out: set[str] = set()
    sources = [(Path(rdir) / "RUN.decisions.jsonl", None)] + ([(Path(telemetry), run_id)] if telemetry else [])
    for path, run_filter in sources:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            if "stop" not in line or "owner" not in line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if run_filter is None and row.get("option") == "stop" and row.get("by") == "owner" and row.get("task"):
                out.add(str(row["task"]))
            elif run_filter is not None and row.get("run_id") == run_filter and row.get("event") == "decision_answered" \
                    and row.get("action") == "stop" and row.get("by") == "owner" and row.get("task_id"):
                out.add(str(row["task_id"]))
    return out


def ended_triggers(run, status: dict, stopped_by_owner: set[str], handed: Iterable[str] = ()) -> list[dict]:
    """A run workflow that ended (SUCCESS) blocked: a rejected composition gate (never the owner's stop), or a blocked
    task the owner did not stop and whose block was not already given to the Solucionador while the run went on
    (`handed`). Nothing waits in it any more, so no other trigger can see it."""
    summary = status.get("summary") if isinstance(status.get("summary"), dict) else {}
    if status.get("workflow_status") != "SUCCESS" or not summary:
        return []
    rejected = dict((summary.get("gates") or {}).get("rejected") or {})
    blocked = sorted(t for t, state in (summary.get("tasks") or {}).items() if state == "blocked")
    unexplained = [t for t in blocked if t not in stopped_by_owner and t not in set(handed)]
    if not rejected and not (summary.get("status") == "blocked" and unexplained):
        return []
    workflow = status.get("workflow_id") or f"bt:{run.run_id}"
    basis = json.dumps([workflow, sorted(rejected), unexplained], sort_keys=True)
    parts = [f"gate {gate} rejected: {str(reason)[:300]}" for gate, reason in sorted(rejected.items())]
    if unexplained:
        parts.append("blocked, not stopped by the owner: " + ", ".join(unexplained))
    item = trigger("ended", f"{run.run_id}:ended:{hashlib.sha256(basis.encode()).hexdigest()[:16]}", run.run_id,
                   reason=f"the run workflow {workflow} ended {summary.get('status')}: " + "; ".join(parts))
    item.update(workflow=workflow, gates=sorted(rejected), blocked=unexplained)
    return [item]


def run_holds(status: dict) -> dict[str, tuple[str, str]]:
    """Tasks the run itself holds `blocked` with no decision behind them -> (block fingerprint, reason). Today that is an
    audit whose blocking findings no remediation round cleared (`workflows._audit_stuck` records `results[task].audit`);
    a task whose own workflow ended blocked was stopped by an answered decision and is not one. The fingerprint is the
    task's latest round workflow and the reason: a `retry-task` (a new round) or a new reason is a new block."""
    summary = status.get("summary") if isinstance(status.get("summary"), dict) else {}
    results = summary.get("results") if isinstance(summary.get("results"), dict) else {}
    out = {}
    for task_id, value in sorted((summary.get("tasks") or {}).items()):
        result = results.get(task_id) if isinstance(results.get(task_id), dict) else {}
        reason = str(result.get("audit") or "")
        if value != "blocked" or not reason:
            continue
        workflow = ((status.get("tasks") or {}).get(task_id) or {}).get("workflow_id") or ""
        basis = json.dumps([task_id, workflow, reason], ensure_ascii=False)
        out[task_id] = (hashlib.sha256(basis.encode()).hexdigest()[:16], reason)
    return out


def blocked_key(run_id: str, task_id: str, fingerprint: str) -> str:
    return f"{run_id}:{task_id}:blocked:{fingerprint}"


def handed_blocks(run, status: dict, state: dict) -> set[str]:
    """Tasks whose current block already has a `blocked` trigger (whatever became of it)."""
    triggers = state.get("triggers") or {}
    return {task_id for task_id, (fingerprint, _) in run_holds(status).items()
            if blocked_key(run.run_id, task_id, fingerprint) in triggers}


def blocked_triggers(run, status: dict, state: dict, now: float, cfg: dict) -> list[dict]:
    """Tasks the run holds blocked (`run_holds`) while its workflow is PENDING and not paused, unchanged for
    `blocked_after_seconds` (a short grace for the owner's own `retry-task`). A run that ended is `ended`'s. Once per
    block: the key is the block's fingerprint. Updates `state["held"]`."""
    summary = status.get("summary") if isinstance(status.get("summary"), dict) else {}
    held = state.setdefault("held", {})
    holds = run_holds(status) if status.get("workflow_status") == "PENDING" and summary.get("status") != "paused" else {}
    for task_id in [t for t in held if t not in holds]:
        del held[task_id]
    found = []
    for task_id, (fingerprint, reason) in holds.items():
        live = ((status.get("tasks") or {}).get(task_id) or {}).get("workflow_status") in ("PENDING", "ENQUEUED")
        mark = held.get(task_id) or {}
        if mark.get("fp") != fingerprint:
            held[task_id] = mark = {"fp": fingerprint, "since": now}
        if live or now < float(mark.get("since", now)) + cfg["blocked_after_seconds"]:
            continue
        item = trigger("blocked", blocked_key(run.run_id, task_id, fingerprint), run.run_id, task_id=task_id,
                       reason=f"the run holds {task_id} blocked since {_iso(float(mark['since']))} while it goes on, "
                              f"with no decision to answer: {reason}")
        item["block"] = fingerprint
        found.append(item)
    if not held:
        state.pop("held", None)
    return found


def stuck_triggers(run, status: dict, state: dict, now: float, cfg: dict) -> list[dict]:
    """PENDING tasks whose state did not move for `stuck_minutes` beyond their known waits. Updates `state["watch"]`."""
    watch = state.setdefault("watch", {})
    seen, found = set(), []
    for task_id, item in sorted((status.get("tasks") or {}).items()):
        item = item or {}
        if item.get("workflow_status") != "PENDING":
            continue
        seen.add(task_id)
        event = item.get("state") if isinstance(item.get("state"), dict) else {}
        decision = item.get("decision") if isinstance(item.get("decision"), dict) else None
        basis = json.dumps([item.get("workflow_id"), event, (decision or {}).get("request_id")], sort_keys=True,
                           default=str)
        fingerprint = hashlib.sha256(basis.encode()).hexdigest()[:16]
        mark = watch.get(task_id) or {}
        if mark.get("fp") != fingerprint:
            watch[task_id] = mark = {"fp": fingerprint, "since": now}
        name = event.get("state")
        if decision or name in QUIET:
            continue
        since = float(mark.get("since", now))
        limit = cfg["stuck_minutes"] * 60
        if name in ("waiting_quota", "recovering") and isinstance(event.get("until"), (int, float)):
            deadline = max(since, float(event["until"])) + limit
        elif name == "running":
            deadline = since + cfg["attempt_minutes"] * 60 + limit
        else:
            deadline = since + limit
        if now >= deadline:
            found.append(trigger("stuck", f"{run.run_id}:{task_id}:stuck:{fingerprint}", run.run_id, task_id=task_id,
                                 reason=f"state {name or 'none'} unchanged since {_iso(since)} while its workflow is "
                                        "PENDING"))
    for task_id in list(watch):
        if task_id not in seen:
            del watch[task_id]
    return found
