"""Durable quiet-point joining of approved stages into an existing Scheduler run."""
from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable
from pathlib import Path

import bt_scheduler_adapter as adapter
import bt_scheduler_m4_wiring as m4_runtime

JOIN_MARKER = ".join.json"


def _join_marker(rdir: Path) -> Path:
    return adapter.run_db_path(rdir).with_name(adapter.run_db_path(rdir).stem + JOIN_MARKER)


def _join_ready(rdir: Path, wiring, scheduler, snap) -> bool:
    """D-134: a newer approved revision (a stage, the whole plan, a scheduler revision) joins the run at a quiet point.
    While it waits, new dispatch is paused (M1 pause; released after the join unless an operator had paused the run);
    True when no attempt is alive and the owner may stop so `dispatch` rebases. A join that would redo more accepted
    tasks than `gates.rework_confirm_over` waits for `scheduler-op REQ revise --confirm` instead."""
    target = adapter.join_target(rdir, snap.revision)
    if target is None:
        return False
    marker = _join_marker(rdir)
    try:
        existing = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        existing = None
    if not isinstance(existing, dict) or existing.get("target") != target or not snap.paused:
        if (refused := _join_refusal(rdir, target, scheduler)):
            if target not in _JOIN_NOTED:
                _JOIN_NOTED.add(target)
                print(refused, file=sys.stderr)
            return False
        paused_here = not snap.paused or (isinstance(existing, dict) and existing.get("paused_by_join") is True)
        tmp = marker.with_suffix(".tmp")
        tmp.write_text(json.dumps({"target": target, "paused_by_join": paused_here}) + "\n", encoding="utf-8")
        os.replace(tmp, marker)
        if not snap.paused:
            scheduler.pause("stage-join", f"approved revision r{target} joins when nothing is running")
    return not m4_runtime.has_live_attempts(wiring) and not m4_runtime.has_pending_streams(wiring)


_JOIN_NOTED: set[int] = set()


def _join_refusal(rdir: Path, target: int, scheduler=None) -> str:
    """Why the run must not join `target` by itself ('' when it may): its cost cannot be measured, or it would redo
    more accepted tasks than `gates.rework_confirm_over` (the operator confirms with `scheduler-op REQ revise --confirm`)."""
    import bt_plan_adapter
    import bt_rework_impact
    if problem := bt_plan_adapter.launch_problem(
            rdir, forced=True, compatibility_report=adapter.plan_compatibility_report(rdir)):
        return problem
    try:
        lost = adapter.join_cost(rdir, scheduler)
    except Exception as exc:  # noqa: BLE001 - a join that cannot be measured is not attempted
        return f"JOIN_UNAVAILABLE: r{target}: {type(exc).__name__}: {exc}"
    limit = bt_rework_impact.ceiling()
    if limit and len(lost) > limit:
        return (f"JOIN_NEEDS_CONFIRM: joining r{target} would redo {len(lost)} accepted task(s) "
                f"({', '.join(lost[:6])}); confirm with `scheduler-op REQ revise --confirm`")
    return ""


def join(rdir: Path, rebind_runtime: Callable[[Path], None]) -> str:
    """Move a run without an owner onto the newest approved revision (rebase, keeping accepted work) and release the
    dispatch pause the join put; '' when there is nothing to join. Raises SchedulerError when the core refuses
    (a live attempt, a cancellation)."""
    identity = adapter.run_identity(rdir)
    target = adapter.join_target(rdir, identity["revision"]) if identity else None
    marker = _join_marker(rdir)
    try:
        pending = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError, AttributeError):
        pending = None
    if target is None and not (identity and isinstance(pending, dict)
                               and type(pending.get("target")) is int
                               and pending["target"] <= identity["revision"]):
        return ""
    report = None
    if target is not None:
        if (refused := _join_refusal(rdir, target)):
            raise adapter.core.SchedulerError(refused.split(":", 1)[0], refused.split(":", 1)[1].strip())
        paused = isinstance(pending, dict) and pending.get("paused_by_join") is True
        tmp = marker.with_suffix(".tmp")
        tmp.write_text(json.dumps({"target": target, "paused_by_join": paused}) + "\n", encoding="utf-8")
        os.replace(tmp, marker)
        report = adapter.rebase_to_latest(rdir)
    else:
        paused = pending.get("paused_by_join") is True
    # The marker survives every crash between M1's rebase and runtime/pause reconciliation.
    rebind_runtime(rdir)
    if paused:
        adapter.apply_control(rdir, "resume", by="stage-join")
    marker.unlink(missing_ok=True)
    return (f"r{report.from_revision} → r{report.to_revision}: kept {len(report.kept)}, redo {len(report.reset)}, "
            f"new {len(report.added)}, removed {len(report.removed)}") if report else f"r{identity['revision']}: join recovered"


