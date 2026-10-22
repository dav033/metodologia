"""Replica of a real night: replay a recorded run's plan and attempt times through the REAL scheduler core (REQ-030).

`extract()` turns the audit table of a run database plus its plan into a small frozen fixture: the task graph with the
surface each task declares, and for every task the attempts it needed (minutes of execution, minutes of verification,
outcome). `replay()` runs that fixture through `bt_scheduler_core` (its claims, its reservation, its retry budget) under
a Config and a virtual clock, with no provider, no git and no sleeping, and measures:

- `wall_minutes`: clock time from start to the last verdict;
- `attempt_minutes`: sum of the minutes every attempt held a slot (execution + verification);
- `ratio` = attempt_minutes / wall_minutes: ~1 is serial, >1 is real parallelism;
- `max_width`: most tasks live at once; `attempts`: attempts taken.

Only the scheduling policy is under test: the minutes are the recorded ones. The replay stops each task at its first
accepted attempt (`first_pass`), so a config that changes what runs side by side is compared on the same work. How much
rework a night would have avoided is measured by `rework_cost()` over the recorded `rework_requested` events instead.
"""
from __future__ import annotations

import hashlib
import heapq
import json
import sqlite3
from collections import defaultdict
from contextlib import closing
from pathlib import Path
from typing import Any

import bt_scheduler_adapter as adapter

sc = adapter.core
ManualClock = sc.simulators.ManualClock

FIXTURE_VERSION = 1
KEEP = ("id", "after", "repository", "milestone_id", "shared_resources", "expected_paths", "scope", "kind")


def extract(db_path: Path | str, plan_path: Path | str, name: str = "") -> dict[str, Any]:
    """The frozen fixture of one run: `db_path` is `<project>-<REQ>.db` (table `audit`), `plan_path` its PLAN.json."""
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    tasks = [{key: task[key] for key in KEEP if key in task} for task in plan["tasks"]]
    known = {task["id"] for task in tasks}
    with closing(sqlite3.connect(f"file:{Path(db_path).resolve()}?mode=ro", uri=True)) as db:
        rows = db.execute("SELECT at, kind, task_id, attempt_id, detail FROM audit ORDER BY rowid").fetchall()
    first = rows[0][0] if rows else 0.0
    marks: dict[str, dict[str, Any]] = defaultdict(dict)
    reworks = []
    for at, kind, task_id, attempt_id, raw in rows:
        detail = json.loads(raw) if raw else {}
        if kind == "reserved":
            marks[attempt_id].update(task=task_id, start=at)
        elif kind == "attempt_transition" and attempt_id in marks:
            target = detail.get("to")
            if target == "verifying":
                marks[attempt_id]["executed"] = at
            elif target in ("accepted", "rejected", "failed", "cancelled"):
                marks[attempt_id].update(end=at, outcome=target)
        elif kind == "rework_requested":
            reworks.append({"at_min": round((at - first) / 60, 2), "by": detail.get("by", ""),
                            "named": list(detail.get("named") or ()), "tasks": list(detail.get("tasks") or ()),
                            "cascade": bool(detail.get("cascade")), "reason": str(detail.get("reason", ""))[:160]})
    attempts: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for attempt_id in sorted(marks):
        mark = marks[attempt_id]
        if mark.get("task") not in known or "end" not in mark:
            continue
        executed = mark.get("executed", mark["end"])
        attempts[mark["task"]].append({"exec_min": round((executed - mark["start"]) / 60, 2),
                                       "verify_min": round((mark["end"] - executed) / 60, 2), "outcome": mark["outcome"]})
    live = [m for m in marks.values() if "end" in m]
    return {"version": FIXTURE_VERSION, "name": name or Path(db_path).stem,
            "plan": {"plan_id": plan.get("plan_id", "REPLICA"), "tasks": tasks},
            "attempts": dict(attempts), "reworks": reworks,
            "recorded": {"attempts": len(live), "accepted": sum(1 for m in live if m["outcome"] == "accepted"),
                         "rejected": sum(1 for m in live if m["outcome"] == "rejected"),
                         "rework_requests": len(reworks),
                         "attempt_minutes": round(sum(m["end"] - m["start"] for m in live) / 60, 1),
                         "wall_minutes": round((max((m["end"] for m in live), default=first) - first) / 60, 1)}}


def load(path: Path | str) -> dict[str, Any]:
    fixture = json.loads(Path(path).read_text(encoding="utf-8"))
    if fixture.get("version") != FIXTURE_VERSION:
        raise ValueError(f"replica fixture version {fixture.get('version')!r} is not {FIXTURE_VERSION}")
    return fixture


def _plan(fixture: dict[str, Any]) -> sc.Plan:
    tasks = []
    for task in fixture["plan"]["tasks"]:
        tasks.append({"id": task["id"], "milestone_id": task.get("milestone_id", "M1"), "after": task.get("after", []),
                      "repository": task.get("repository", ""), "shared_resources": task.get("shared_resources", []),
                      "expected_paths": task.get("expected_paths", []), "scope": task.get("scope", ""),
                      "acceptance_criteria": [f"{task['id']} works"], "verification": [{"type": "command", "value": "true"}]})
    text = json.dumps({"schema_version": "1.0.0", "plan_id": fixture["plan"]["plan_id"], "revision": 1, "tasks": tasks})
    return sc.load_plan(text, approved_sha256=hashlib.sha256(text.encode()).hexdigest())


def _script(fixture: dict[str, Any]) -> dict[str, list[tuple[float, float, bool]]]:
    """task -> [(execution minutes, verification minutes, accepted)] up to and including the first accepted attempt. A
    task never accepted in the record gets one accepted attempt with the mean duration of its recorded ones."""
    script: dict[str, list[tuple[float, float, bool]]] = {}
    for task in fixture["plan"]["tasks"]:
        recorded = fixture["attempts"].get(task["id"], [])
        steps: list[tuple[float, float, bool]] = []
        for attempt in recorded:
            ok = attempt["outcome"] == "accepted"
            steps.append((attempt["exec_min"], attempt["verify_min"], ok))
            if ok:
                break
        if not steps or not steps[-1][2]:
            mean = sum(a["exec_min"] + a["verify_min"] for a in recorded) / len(recorded) if recorded else 30.0
            steps.append((mean * 0.8, mean * 0.2, True))
        script[task["id"]] = steps
    return script


def replay(fixture: dict[str, Any], *, max_parallel_tasks: int = 3, exclusive_scopes: tuple[str, ...] = (),
           max_attempts: int = 50, unknown_surface: str = "serialize") -> dict[str, Any]:
    """Run the fixture to completion through the real core and report how parallel it was."""
    plan, clock = _plan(fixture), ManualClock()
    executor, verifier = sc.FakeExecutor(), sc.FakeVerifier()
    config = sc.Config(max_parallel_tasks=max_parallel_tasks, max_attempts=max_attempts, exclusive_scopes=exclusive_scopes, unknown_surface=unknown_surface,
                       lease_seconds=1e9, reconcile_seconds=1e9)
    core = sc.SchedulerCore(plan, sc.InMemoryRepository(), ports=sc.Ports(execution=executor, verification=verifier),
                            config=config, clock=clock)
    script, taken = _script(fixture), defaultdict(int)
    start = clock.now
    events: list[tuple[float, int, str, str]] = []             # (when, order, what, attempt id)
    queued: set[str] = set()
    live: dict[str, float] = {}                                # attempt -> start time (a slot is held)
    held_minutes, width, order = 0.0, 0, 0
    core.start()
    for _ in range(100_000):
        core.step()
        for attempt_id, started in list(executor.started.items()):
            if attempt_id in queued:
                continue
            queued.add(attempt_id)
            task_id = started.task_id
            step = script[task_id][min(taken[task_id], len(script[task_id]) - 1)]
            taken[task_id] += 1
            live[attempt_id] = clock.now
            width = max(width, len(live))
            order += 1
            heapq.heappush(events, (clock.now + step[0] * 60, order, "executed", attempt_id))
            heapq.heappush(events, (clock.now + (step[0] + step[1]) * 60, order + 100_000, "verdict" + ("+" if step[2] else "-"),
                                    attempt_id))
        if not events:
            break
        when, _o, what, attempt_id = heapq.heappop(events)
        clock.now = max(clock.now, when)
        if what == "executed":
            started = executor.started[attempt_id]
            core.ingest(sc.Event(f"ev-{attempt_id}", plan.plan_id, 1, started.task_id, attempt_id, "replica",
                                 sc.EventKind.EXECUTION_FINISHED.value, "", {}, started.token))
            core.step()
            continue
        request = verifier.requests.get(attempt_id)
        if request is None:
            events and heapq.heappush(events, (clock.now + 1, order + 1, what, attempt_id))
            core.step()
            continue
        held_minutes += (clock.now - live.pop(attempt_id)) / 60
        core.submit_verdict(sc.Verdict(f"vd-{attempt_id}", plan.plan_id, 1, request.task_id, attempt_id, what.endswith("+"),
                                       "replica-validator", "replayed", request.token))
    snap = core.snapshot()
    stuck = {tid: view.get("reason", "") or view.get("state") for tid, view in snap.tasks.items()
             if view.get("state") not in ("completed", "pending", "ready")}
    wall = (clock.now - start) / 60
    return {"status": snap.status, "wall_minutes": round(wall, 1), "attempt_minutes": round(held_minutes, 1),
            "ratio": round(held_minutes / wall, 2) if wall else 0.0, "max_width": width, "attempts": sum(taken.values()),
            "stuck": stuck}


def rework_cost(fixture: dict[str, Any], minutes_per_task: dict[str, float] | None = None) -> dict[str, Any]:
    """What the recorded rework requests cost: tasks sent back (with the tasks that depend on them when `cascade`) and
    the minutes their accepted work took. This is the 'before' number of the minimal-rework policy."""
    plan = _plan(fixture)
    mean: dict[str, float] = {}
    for task in fixture["plan"]["tasks"]:
        accepted = [a for a in fixture["attempts"].get(task["id"], []) if a["outcome"] == "accepted"]
        mean[task["id"]] = (sum(a["exec_min"] + a["verify_min"] for a in accepted) / len(accepted)) if accepted else 0.0
    mean.update(minutes_per_task or {})
    invalidated, minutes = 0, 0.0
    for request in fixture["reworks"]:
        named = [t for t in request["named"] or request["tasks"] if t in mean]
        scope = set(named)
        if request["cascade"]:
            for task_id in named:
                scope |= set(plan.descendants(task_id))
        invalidated += len(scope)
        minutes += sum(mean.get(t, 0.0) for t in scope)
    return {"requests": len(fixture["reworks"]), "tasks_invalidated": invalidated, "minutes": round(minutes, 1)}
