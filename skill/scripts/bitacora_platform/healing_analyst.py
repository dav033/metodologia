"""Turn a finished external-cause analysis into an ordinary task stop, once per analysis."""
from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path

import bt_attempt_analyst as analyst
import bt_scheduler_decisions as decisions
import bt_scheduler_ops as ops

REASON = "analyst_not_the_task"
LIVE = frozenset({"reserved", "dispatched", "running", "verifying", "uncertain"})


def stop_tasks(project: str, req: str, rdir: Path, doc: dict, found: list[dict], state: dict,
               *, enabled: Callable[[], bool], save: Callable[[], None], log: Callable[[str], None]) -> tuple[dict, list[dict]]:
    stopped = False
    seen = state.get("analyst_stops")
    if not isinstance(seen, dict):
        seen = state["analyst_stops"] = {}
    for task, record in doc.get("tasks", {}).items():
        reason = str(record.get("reason", ""))
        if record.get("state") == "blocked" and reason.startswith(REASON + ":"):
            # The operator move committed before the watcher recorded it (a crash between those writes).
            key = f"{task}:{reason.split(':', 1)[1]}"
            if key not in seen:
                seen[key] = {"task": task, "attempt": ""}
                save()
        if record.get("state") not in ("ready", "active"):
            continue
        data = analyst.load(rdir, task)
        if data.get("state") != "done" or data.get("not_the_task") is not True or data.get("confidence") == "baja":
            continue
        if data.get("source_available") is not True:
            continue
        fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        key = f"{task}:{fingerprint}"
        if key in seen:
            continue
        live = [(aid, att) for aid, att in doc.get("attempts", {}).items()
                if att.get("task_id") == task and att.get("state") in LIVE]
        if len(live) > 1 or (record.get("state") == "active" and not live):
            continue
        if not enabled() or ops.on_hold(rdir):
            break
        aid, attempt = live[0] if live else ("", {})
        try:
            ops.apply(project, req, rdir, "cancel-attempt", aid, f"{REASON}:{fingerprint}", block_task=True,
                      expected_task=task, expected_task_state=record["state"],
                      expected_attempt_state=attempt.get("state"))
        except ops.core.SchedulerError as error:
            if error.code != "STALE_PRECONDITION":
                raise
            log(f"healing {task}: analysis stop waits for a fresh task snapshot")
            continue
        seen[key] = {"task": task, "attempt": aid}
        save()
        stopped = True
        log(f"healing {task}: confident external-cause analysis stopped further attempts")
    if stopped:
        return decisions._state(rdir), decisions.open_requests(rdir)
    return doc, found
