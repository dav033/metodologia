"""Read-only operator views; never acquire an owner or modify a run."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import bt_scheduler_adapter as adapter
import bt_run_stores
from . import quality_progress

core = adapter.core


def status(rdir: Path, owners: list[int], watchers: list[int], held: bool) -> dict:
    out = {"owner_pids": owners, "watcher_pids": watchers, "hold": held}
    conn = sqlite3.connect(f"{adapter.run_db_path(rdir).resolve().as_uri()}?mode=ro", uri=True, timeout=5)
    try:
        doc = json.loads(conn.execute("SELECT doc FROM state WHERE id = 1").fetchone()[0])
    finally:
        conn.close()
    live = {s.value for s in core.states.ATTEMPT_LIVE}
    out["revision"] = doc.get("revision")
    out["live_attempts"] = [{"attempt": a["id"], "task": a["task_id"], "state": a["state"]}
                            for a in doc.get("attempts", {}).values() if a.get("state") in live]
    quality_progress.enrich(bt_run_stores.paths(rdir)["m6"], out["live_attempts"], owners)
    try:
        import bt_scheduler_decisions
        out["open_decisions"] = [r["id"] for r in bt_scheduler_decisions.open_requests(rdir)]
    except Exception:  # noqa: BLE001 - status must answer even when the run has no readable state
        out["open_decisions"] = []
    out["blocked_tasks"] = [t for t, r in doc.get("tasks", {}).items() if r.get("state") == "blocked"]
    out["task_states"] = {task: record.get("state") for task, record in doc.get("tasks", {}).items()
                          if isinstance(record, dict) and isinstance(record.get("state"), str)}
    return out


def recovery_status(rdir: Path) -> dict:
    """Read the M5 adapter's diagnostic ledger without opening the owner or mutating stores."""
    import bt_run_stores
    import bt_scheduler_recovery_adapter as recovery

    try:
        marker = json.loads(bt_run_stores.runtime_marker(adapter.run_db_path(rdir)).read_text(encoding="utf-8"))
        run_id = marker.get("runtime_id") if isinstance(marker, dict) else None
        if not isinstance(run_id, str) or not run_id:
            raise ValueError("runtime identity missing")
        path = bt_run_stores.module_stores(adapter.run_db_path(rdir), run_id)["m5"]
        return recovery.read_cycle_status(path, run_id=run_id)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        return {"schema_version": "recovery-status/1", "blocker": f"recovery_status_unavailable:{type(error).__name__}",
                "cycles": []}
