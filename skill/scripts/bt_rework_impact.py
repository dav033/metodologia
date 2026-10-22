"""What throwing away accepted work costs, and the owner's confirmation past a ceiling (REQ-030 step 3).

Rework is the biggest hidden cost of a run: REQ-029 spent 140 task-redos (~870 minutes of accepted work) on 22 rework
requests, one of them sending back 23 tasks at once. Past `gates.rework_confirm_over` accepted tasks (default 3) no action
that invalidates accepted work runs without the owner confirming it, and the refusal says what it would cost.

The cost is the mean minutes of the accepted attempts of each task as the run recorded them (reservation -> verdict), or
half of the plan's `estimated_minutes` for a task with no recorded accepted attempt. It is an estimate for a human to
weigh, never a limit by itself.
"""
from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from contextlib import closing
from pathlib import Path

DEFAULT_CEILING = 3


def ceiling() -> int:
    """`gates.rework_confirm_over`: accepted tasks one action may invalidate without confirmation (0 = no ceiling)."""
    import bt_config

    try:
        value = bt_config.get("gates.rework_confirm_over", DEFAULT_CEILING)
    except (KeyError, TypeError):                       # a configuration that cannot be read never stops a run
        return DEFAULT_CEILING
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else DEFAULT_CEILING


def recorded_minutes(db_path: Path | str) -> dict[str, float]:
    """task -> mean minutes of its accepted attempts, from the run's audit trail (read-only; {} when unreadable)."""
    try:
        with closing(sqlite3.connect(f"file:{Path(db_path).resolve()}?mode=ro", uri=True, timeout=2)) as db:
            rows = db.execute("SELECT at, kind, task_id, attempt_id, detail FROM audit ORDER BY rowid").fetchall()
    except sqlite3.Error:
        return {}
    start: dict[str, float] = {}
    spans: dict[str, list[float]] = defaultdict(list)
    for at, kind, task_id, attempt_id, raw in rows:
        if kind == "reserved":
            start[attempt_id] = at
        elif kind == "attempt_transition" and attempt_id in start:
            try:
                target = json.loads(raw).get("to")
            except ValueError:
                continue
            if target == "accepted":
                spans[task_id].append((at - start[attempt_id]) / 60)
    return {task: sum(values) / len(values) for task, values in spans.items()}


def estimate(db_path: Path | str, tasks, plan=None) -> dict:
    """{"tasks": [...], "minutes": float, "recorded": n} for the accepted `tasks` an action would throw away."""
    tasks = list(tasks)
    known = recorded_minutes(db_path)
    minutes, recorded = 0.0, 0
    for task_id in tasks:
        if task_id in known:
            minutes += known[task_id]
            recorded += 1
        elif plan is not None:
            try:
                minutes += float(plan.task(task_id).meta.get("estimated_minutes") or 0) / 2
            except Exception:  # noqa: BLE001 - no estimate for an unknown task
                pass
    return {"tasks": tasks, "minutes": round(minutes), "recorded": recorded}


def describe(action: str, cost: dict, limit: int) -> str:
    listed = ", ".join(cost["tasks"][:10]) + (", …" if len(cost["tasks"]) > 10 else "")
    return (f"{action} would throw away {len(cost['tasks'])} accepted tasks ({listed}), about {cost['minutes']} minutes of "
            f"work (limit without confirmation: {limit}). Name fewer tasks, let the audit findings become remediation tasks "
            "instead, or repeat it with --confirm if the cost is worth it.")
