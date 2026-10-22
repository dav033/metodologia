"""Implementation helpers passed the M1 symbols by the sole core adapter."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def revision_identity(core: Any, database: Path) -> dict[str, Any]:
    repository = core.SqliteRepository(database, create=False)
    with repository.read_transaction() as tx:
        if tx.state is None:
            raise core.SchedulerError("STATE_MISSING", "Scheduler run has no state")
        state = tx.state
        live_states = {core.AttemptState.RESERVED, core.AttemptState.DISPATCHED, core.AttemptState.RUNNING,
                       core.AttemptState.VERIFYING, core.AttemptState.UNCERTAIN}
        return {"plan_id": state.plan_id, "revision": state.revision, "source_sha256": state.plan_sha256,
                "accepted_map_digest": core.accepted_map_digest(state), "stop_generation": core.stop_generation(state),
                "paused": state.paused, "cancelled": state.cancel_requested,
                "live_attempts": sorted(a.id for a in state.attempts.values()
                                         if core.AttemptState(a.state) in live_states)}


def apply_plan_revision(core: Any, database: Path, owner_lock, rdir: Path, old: Any, new: Any,
                        guard: dict[str, Any]) -> dict[str, Any]:
    parsed = core.RevisionGuard(
        operation_key=guard["operation_key"], source_sha256=guard["source_sha256"],
        target_sha256=guard["target_sha256"], accepted_map_digest=guard["accepted_map_digest"],
        base_digest=guard["base_digest"], stop_generation=guard["stop_generation"],
        scope=tuple(guard["scope"]), barrier_deadline=guard["barrier_deadline"],
        current_base=guard.get("current_base"),
    )
    with owner_lock(rdir):
        repository = core.SqliteRepository(database, create=False)
        result = core.apply_plan_revision(repository, old, new, parsed)
    identity = revision_identity(core, database)
    status = {"applied": "applied", "adopted": "adopted", "waiting": "waiting"}.get(result.outcome, "blocked")
    reason = result.reason or ("live_attempts" if result.outcome == "waiting" else "")
    report = result.report
    if hasattr(report, "__dict__"):
        report = report.__dict__
    return {"status": status, "reason": reason, "report": report,
            "live_attempts": list(result.live_attempt_ids), "stop_generation": identity["stop_generation"]}


def abort_revision_barrier(core: Any, database: Path, operation_key: str, reason: str) -> bool:
    repository = core.SqliteRepository(database, create=False)
    return core.abort_revision_barrier(repository, operation_key, reason)
