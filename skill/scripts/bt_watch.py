"""`bitacora.py watch REQ`: block until the run has something worth telling, print it, exit.

Made for the conversation that handed the plan off (often followed from a phone through Remote Control): it leaves
this command running in the background, is woken when it exits, relays the news and arms it again until the run is
over. News = a settled session (a milestone, an audit, a task), a blocked task, a wait for usage limits, a pause, a
supervisor that stopped beating, or the end of the run. What was already reported is remembered per run in
<root>/.state/watch/, so nothing is told twice and nothing that happened between two watches is missed.
"""
from __future__ import annotations

import time

import bt_runstate as rs
import bt_scheduler_adapter as scheduler_
from bt_core import *  # noqa: F403

TERMINAL = ("done", "blocked", "stopped")
STALE_MIN = 12  # a running supervisor beats every minute


def _cursor_path(project: str, req: str) -> Path:
    return STATE / "watch" / f"{project}-{req}.json"


def _load_cursor(project: str, req: str) -> dict:
    try:
        data = json.loads(_cursor_path(project, req).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_cursor(project: str, req: str, cursor: dict) -> None:
    path = _cursor_path(project, req)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cursor), encoding="utf-8")
    tmp.replace(path)


def _sessions(entries: list[dict]) -> list[str]:
    """One line per settled session: who ran it, what each task ended as, how long it took."""
    by_session: dict[int, list[dict]] = {}
    for e in entries:
        by_session.setdefault(e.get("session"), []).append(e)
    lines = []
    for n, rows in by_session.items():
        first = rows[0]
        who = " ".join(str(x) for x in (first.get("profile") or first.get("agent"), first.get("model"),
                                        first.get("effort")) if x)
        results = " ".join(f"{r.get('task')}:{r.get('result')}" for r in rows)
        note = next((r.get("summary") for r in rows if r.get("result") not in ("done", "skipped")), None) \
            or first.get("summary") or ""
        lines.append(f"- S{n} [{who or 'agent'}] {results} ({max(1, int(first.get('seconds') or 0) // 60)} min)"
                     + (f" — {' '.join(str(note).split())[:160]}" if note else ""))
    return lines


def snapshot(state: dict) -> dict:
    hb = state.get("heartbeat") or {}
    done, total = rs.progress(state)
    return {"status": state.get("status"), "log": len(state.get("log") or []), "sessions": state.get("sessions"),
            "blocked": sorted(t["id"] for t in state["tasks"] if t["status"] == "blocked"),
            "waiting_until": state.get("waiting_until"), "done": done, "total": total,
            "stale": state.get("status") == "running" and rs.is_stale(state, STALE_MIN), "current": hb.get("task")}


def news(project: str, req: str, state: dict, cursor: dict) -> tuple[list[str], dict]:
    """(lines to tell, new cursor). Empty lines = nothing new since the cursor."""
    snap = snapshot(state)
    log = state.get("log") or []
    seen = cursor.get("at")  # timestamp of the last log entry already told (the log is capped, an index would drift)
    fresh = [e for e in log if seen is None or str(e.get("at")) > seen] if cursor else list(log)
    lines = _sessions(fresh)
    for key, label in (("status", "status"), ("waiting_until", "waiting for usage limits until"),
                       ("blocked", "blocked tasks")):
        if cursor and cursor.get(key) != snap[key] and snap[key]:
            value = ", ".join(snap[key]) if isinstance(snap[key], list) else snap[key]
            lines.append(f"- {label}: {value}")
    if snap["stale"] and not cursor.get("stale"):
        lines.append(f"- the supervisor has not reported for {STALE_MIN}+ min: it may have died. Resume with: "
                     f"bitacora.py --project {project} run {req} --resume")
    new = {**snap, "at": str(log[-1].get("at")) if log else seen}
    return lines, new


def report(project: str, req: str, state: dict, lines: list[str]) -> str:
    snap = snapshot(state)
    terminal = snap["status"] in TERMINAL
    head = f"{project} {req} · {snap['status']} · {snap['done']}/{snap['total']} tasks done"
    out = [head, *lines]
    if terminal:
        tail = {"done": "finished: read REPORT.md next to the plan",
                "blocked": "blocked: see PENDING.md, fix, then run --resume --retry-blocked",
                "stopped": "stopped"}[snap["status"]]
        out.append(f"terminal: true ({tail})")
    else:
        running = [t["id"] for t in state["tasks"] if t["status"] == "in_progress"]
        nxt = rs.next_unit(state)
        if running:  # the session after the one just told has usually started already
            out.append(f"now running: {snap['current'] or ', '.join(running)}")
        elif nxt:
            out.append(f"next: {rs.unit_label(nxt)}")
        elif snap["done"] == snap["total"] and snap["total"]:
            out.append("now running: final review + REPORT.md")
        out.append("terminal: false (run this watch again to hear the next event)")
    return "\n".join(out)


def scheduler_news(project: str, req: str, state: dict, cursor: dict) -> tuple[list[str], dict]:
    tasks = [[str(t.get("id", "")), str(t.get("scheduler_state", t.get("status", "?")))]
             for t in state.get("tasks", []) if isinstance(t, dict)]
    tasks.sort()
    done = sum(task.get("status") == "done" for task in state.get("tasks", []) if isinstance(task, dict))
    total = len(state.get("tasks", []))
    snap = {"authority": "scheduler", "status": state.get("status"), "tasks": tasks,
            "done": done, "total": total, "stale": scheduler_.projection_is_stale(state)}
    lines = []
    if not cursor:
        lines.append(f"- ejecución Scheduler: {snap['status']} · {done}/{total} tareas completadas")
    else:
        if cursor.get("status") != snap["status"]:
            lines.append(f"- estado Scheduler: {snap['status']}")
        if cursor.get("tasks") != tasks:
            lines.append(f"- progreso Scheduler: {done}/{total} tareas completadas")
    if snap["stale"] and not cursor.get("stale"):
        command = f"bitacora.py --project {project} scheduler-run {req} --resume"
        lines.append(f"- el heartbeat está vencido; puede reanudarse con: {command}")
    attention = state.get("attention")
    if attention and (not cursor or cursor.get("attention") != attention):
        lines.append(f"- atención M1: {', '.join(str(item) for item in attention)}")
    new = {**snap, "attention": attention or []}
    return lines, new


def scheduler_report(project: str, req: str, state: dict, lines: list[str]) -> str:
    tasks = state.get("tasks", [])
    done = sum(task.get("status") == "done" for task in tasks if isinstance(task, dict))
    total = len(tasks)
    status = str(state.get("status", "desconocido"))
    terminal = status in ("done", "blocked", "stopped")
    out = [f"{project} {req} · Scheduler · {status} · {done}/{total} tareas completadas", *lines]
    out.append("terminal: true" if terminal else "terminal: false (vuelve a ejecutar watch para el próximo cambio)")
    return "\n".join(out)


def watch(project: str, req: str, timeout_min: float = 360, poll_sec: float = 15) -> str:
    """Wait for news on the run (or `timeout_min`), tell it once, remember it was told."""
    rdir = find_req(ROOT / project, req)
    rid = req_id(rdir)
    deadline = time.time() + timeout_min * 60
    state = None
    while True:
        if scheduler_.scheduler_authority(rdir):
            state = scheduler_.read_projection(rdir)
            if state is None:
                command = f"bitacora.py --project {project} scheduler-run {rid} --resume"
                return (f"{project} {rid} · Scheduler · proyección no disponible\n"
                        f"La base M1 se conserva. Recupera la vista con: {command}\nterminal: false")
            cursor = _load_cursor(project, rid)
            lines, new = scheduler_news(project, rid, state, cursor)
            if lines or state.get("status") in TERMINAL:
                _save_cursor(project, rid, new)
                return scheduler_report(project, rid, state, lines or ["- sin cambios nuevos"])
            if time.time() >= deadline:
                return scheduler_report(project, rid, state, [f"- sin cambios en {int(timeout_min)} min"])
            time.sleep(poll_sec)
            continue
        try:
            state = rs.load(rdir)
        except rs.RunStateError:
            state = None
        if state is not None:
            cursor = _load_cursor(project, rid)
            lines, new = news(project, rid, state, cursor)
            if lines or not cursor or state.get("status") in TERMINAL:
                _save_cursor(project, rid, new)
                if not lines and cursor and cursor.get("status") == state.get("status"):
                    lines = ["- nothing new since the last report"]
                return report(project, rid, state, lines or ["- the run has started"])
        if time.time() >= deadline:
            if state is None:
                return f"{project} {rid} · no RUN.json yet (was it launched?)\nterminal: false"
            return report(project, rid, state, [f"- no news in {int(timeout_min)} min"])
        time.sleep(poll_sec)
