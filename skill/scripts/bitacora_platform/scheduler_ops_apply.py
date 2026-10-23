"""Apply an operator move under a hold, with state preconditions checked before mutation."""
from __future__ import annotations

import json
from pathlib import Path

import bt_scheduler_ops as ops


def apply(project: str, req: str, rdir: Path, action: str, target: str = "", reason: str = "",
          keep_held: bool = False, only: bool = False, option: str = "", *, expected_task: str = "",
          expected_task_state: str | None = None, expected_attempt_state: str | None = None,
          confirm: bool = False) -> list[str]:
    """Run one operator move; the owner is stopped first and the watchdog restarts it afterwards."""
    lines: list[str] = []
    why = reason or f"operator {action}"
    hold_path_before = ops.hold_path(rdir)
    try:
        existing_hold = json.loads(hold_path_before.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        existing_hold = None
    nested_recovery_stop = (action == "stop" and isinstance(existing_hold, dict)
                            and existing_hold.get("why") == "recovery revision")
    if action == "remediate" and (existing_hold is not None or ops.on_hold(rdir)):
        # an operator's stop is already in force: freezing a revision now would consume the correction under it (REQ-029 F15)
        return ["remediation waits: the run is held by an operator move (`scheduler-op REQ resume` releases it)"]
    with ops.hold(rdir, why, keep=keep_held) as hold_token:
        lines.append(f"owner stopped: {ops.stop_owner(project, req)} process(es)")
        if action == "stop":
            if not nested_recovery_stop:
                ops.adapter.apply_control(rdir, "stop", by=ops.OPERATOR)
            return lines
        if action == "remediate":
            import bt_remediation
            built = bt_remediation.apply(rdir, hold_token=hold_token)
            if built is None:
                return [*lines, "nothing to remediate (no request, or its tasks cannot be built: the named tasks are "
                                "sent back by the next rejection)"]
            lines.append(f"remediation of {built['audit']} round {built['round']}: plan r{built['revision']} adds "
                         f"{', '.join(built['tasks'])}")
            action = "revise"
            why = f"{why}: {built['audit']} findings remediated by {', '.join(built['tasks'])}"
        with ops._opened(rdir) as sch:
            if expected_task_state is not None:
                actual_state = sch.read(lambda ctx: ctx.state.tasks.get(expected_task).state
                                        if expected_task in ctx.state.tasks else None)
                if actual_state != expected_task_state:
                    raise ops.core.SchedulerError(
                        "STALE_PRECONDITION",
                        f"task {expected_task} changed from {expected_task_state} to {actual_state}",
                    )
            if expected_attempt_state is not None:
                actual_state = sch.read(lambda ctx: ctx.state.attempts[target].state
                                        if target in ctx.state.attempts else None)
                if actual_state != expected_attempt_state:
                    raise ops.core.SchedulerError(
                        "STALE_PRECONDITION",
                        f"attempt {target} changed from {expected_attempt_state} to {actual_state}",
                    )
            if action == "cancel-attempt":
                lines += ops.cancel_attempts(project, req, rdir, sch, [target], why)
            elif action == "reopen":
                sch.reopen(target, ops.OPERATOR, why)
                lines.append(f"{target}: reopened")
            elif action == "rework":
                tasks = tuple(item.strip() for item in target.split(",") if item.strip())
                ops._impact_guard(rdir, sch, "rework", sch.rework_impact(tasks, (), not only), confirm)
                moved = sch.rework(tasks, ops.OPERATOR, why, cascade=not only, confirmed=True)
                lines.append(f"sent back for rework: {', '.join(moved) or 'nothing (already pending)'}")
            elif action == "continue-from":
                lines.append(ops.direct_continuation(rdir, sch, target, option))
            elif action == "withdraw-rework":
                tasks = tuple(item.strip() for item in target.split(",") if item.strip())
                restored = sch.withdraw_rework(tasks, ops.OPERATOR, why)
                lines.append(f"rework taken back (completed again on their accepted result): {', '.join(restored)}")
            elif action == "revise":
                if not confirm:
                    plan, done = ops._revise_impact(rdir, sch)
                    ops._impact_guard(rdir, sch, f"revise r{plan} -> latest", done, confirm)
                live = [a for a, _, _ in ops._live_attempts(sch)]
                lines += ops.cancel_attempts(project, req, rdir, sch, live, f"{why}: superseded by a plan revision")
            else:
                raise ops.core.SchedulerError("NOT_ALLOWED", f"unknown action {action}")
        if action == "revise":
            report = ops.adapter.rebase_to_latest(rdir)
            import bt_scheduler_run
            bt_scheduler_run.rebind_runtime(rdir)
            lines.append(f"rebase r{report.from_revision} → r{report.to_revision}: kept {len(report.kept)}, "
                         f"redo {len(report.reset)}, new {len(report.added)}, removed {len(report.removed)}")
        ops._refresh_projection(rdir)
    return lines
