"""Generated status block inside PLAN.md, the SessionStart "Planes" section and the `plan-status` text table.

The block lives between two HTML-comment markers, holds no checkbox and no heading (so the PLAN.md grammar and the
checkbox ticker never see it) and is ignored by the planner's narrative digest (any `<owner>:status:begin|end` block).
PLAN.json is never touched. Rendering is derived from `bt_planstatus.plan_status`; refreshing rewrites only the region
between the markers, atomically, under the central "plan" lock, and only when something other than the timestamp
changed. Every entry point is best-effort: a failure is logged at debug level and reported as False.
"""
from __future__ import annotations

import datetime as dt
import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Any

import bt_planstatus as planstatus
STATUS_BEGIN = "<!-- bitacora:status:begin -->"   # the marker shape is `<owner>:status:begin|end` (bt_planner ignores it)
STATUS_END = "<!-- bitacora:status:end -->"

LOGGER = logging.getLogger(__name__)
ACTIVE_LINES = 6
_REGION = re.compile(re.escape(STATUS_BEGIN) + r".*?" + re.escape(STATUS_END), re.S)
_STAMP = re.compile(r"generado: \S+")
_TITLE = re.compile(r"^# .*$", re.M)
_LEVEL = {"low": "baja", "medium": "media", "high": "alta", "extreme": "extrema"}
_STATE = {"pending": "pendiente", "ready": "lista", "running": "en curso", "verifying": "verificando",
          "completed": "completada", "rejected": "rechazada", "blocked": "bloqueada", "cancelled": "cancelada"}


def _cell(value: Any) -> str:
    return "—" if value in (None, "") else str(value).replace("|", "/").replace("\n", " ")


def _task_groups(tasks: list[dict[str, Any]]) -> list[tuple[str | None, str | None, list[dict[str, Any]]]]:
    """Preserve legacy flat rendering; group 1.3 tasks and leave composition tasks visible."""
    if not any(task.get("subplan_id") for task in tasks):
        return [(None, None, tasks)]
    groups: dict[str, list[dict[str, Any]]] = {}
    titles: dict[str, str | None] = {}
    unassigned = []
    for task in tasks:
        sid = task.get("subplan_id")
        if not isinstance(sid, str) or not sid:
            unassigned.append(task)
            continue
        groups.setdefault(sid, []).append(task)
        titles.setdefault(sid, task.get("subplan_title"))
    result = [(sid, titles[sid], grouped) for sid, grouped in groups.items()]
    if unassigned:
        result.append(("Sin subplan", None, unassigned))
    return result


def _level(value: str | None) -> str:
    return _LEVEL.get(value or "", "—")


def _now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def render_block(status: dict[str, Any], generated_at: str | None = None) -> str:
    """The marker-delimited block, in Spanish, ending with a newline."""
    plan, run, summary = status["plan"], status["run"], status["summary"]
    lines = [STATUS_BEGIN,
             "> Bloque generado, no editar a mano. "
             f"Plan: {_cell(plan.get('status'))} · ejecución: {_cell(run.get('status'))} · "
             f"hitos {summary['milestones_done']}/{summary['milestones_total']} · "
             f"tareas {summary['tasks_done']}/{summary['tasks_total']} · "
             f"generado: {generated_at or _now()}"]
    for milestone in status["milestones"]:
        progress = milestone["progress"]
        title = f" — {_cell(milestone.get('title'))}" if milestone.get("title") else ""
        lines += ["", f"**{_cell(milestone['id'])}{title}** · dificultad {_level(milestone.get('difficulty'))} · "
                      f"{progress['done']}/{progress['total']}"]
        for subplan, subplan_title, tasks in _task_groups(milestone["tasks"]):
            if subplan is not None:
                label = f"**{_cell(subplan)}"
                if subplan_title:
                    label += f" — {_cell(subplan_title)}"
                lines += ["", label + "**"]
            lines += ["", "| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |",
                      "|---|---|---|---|---|---|---|"]
            for task in tasks:
                attempt = task.get("attempt") or {}
                lines.append("| " + " | ".join((
                    _cell(task["id"]), _cell(task.get("title")), _level(task.get("complexity")),
                    _STATE.get(task["state"], task["state"]), _cell(attempt.get("model_requested")),
                    _cell(attempt.get("account") or attempt.get("account_ref")), str(task.get("attempts") or 0))) + " |")
    lines.append(STATUS_END)
    return "\n".join(lines) + "\n"


def _comparable(block: str) -> str:
    return _STAMP.sub("generado: -", block)


def _insert_at(text: str) -> int:
    front = re.match(r"---\n.*?\n---\n", text, re.S)
    start = front.end() if front else 0
    title = _TITLE.search(text, start)
    if title:
        return min(len(text), title.end() + 1)
    return start


def _splice(text: str, block: str) -> str:
    found = _REGION.search(text)
    if found:
        return text[:found.start()] + block.rstrip("\n") + text[found.end():]
    at = _insert_at(text)
    head = text[:at] if text[:at].endswith("\n") or not text[:at] else text[:at] + "\n"
    rest = text[at:]
    return head + "\n" + block + (rest if rest.startswith("\n") else "\n" + rest)  # removing "\n<block>\n" gives the original back


def _write_atomic(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".PLAN.md.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, path.stat().st_mode & 0o777)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def refresh_plan_block(project: str, req_dir: Path, *, write: bool = True) -> bool:
    """Bring the block in PLAN.md up to date; True only when the file was (or, with write=False, would be) changed."""
    try:
        from bt_lock import central_lock
        plan = Path(req_dir) / "PLAN.md"
        if not plan.is_file():
            return False
        status = planstatus.plan_status(project, Path(req_dir))
        if not status["milestones"]:
            return False
        block = render_block(status)
        with central_lock("plan"):
            text = plan.read_text(encoding="utf-8")
            found = _REGION.search(text)
            if found and _comparable(found.group(0)) == _comparable(block.rstrip("\n")):
                return False
            if not write:
                return True
            _write_atomic(plan, _splice(text, block))
        return True
    except Exception as exc:  # a status refresh must never break a run, a launch or a hook
        LOGGER.debug("plan status block not refreshed for %s: %s", req_dir, exc)
        return False


def status_table(status: dict[str, Any]) -> str:
    """Compact text for the terminal: one line per milestone, one per task."""
    summary, run = status["summary"], status["run"]
    out = [f"{status['req_id']} · {status.get('title') or '-'} · plan {_cell(status['plan'].get('status'))} · "
           f"ejecución {_cell(run.get('status'))} · hitos {summary['milestones_done']}/{summary['milestones_total']} · "
           f"tareas {summary['tasks_done']}/{summary['tasks_total']} · dificultad {_level(summary.get('difficulty'))}"]
    for milestone in status["milestones"]:
        progress = milestone["progress"]
        out.append(f"  {_cell(milestone['id'])} {_cell(milestone.get('title'))} · "
                   f"{_level(milestone.get('difficulty'))} · {progress['done']}/{progress['total']}")
        for subplan, subplan_title, tasks in _task_groups(milestone["tasks"]):
            if subplan is not None:
                out.append(f"    {subplan}" + (f" {_cell(subplan_title)}" if subplan_title else ""))
            for task in tasks:
                attempt = task.get("attempt") or {}
                indent = "      " if subplan is not None else "    "
                out.append(f"{indent}{task['id']} {_STATE.get(task['state'], task['state'])} · {_level(task.get('complexity'))}"
                           f" · {_cell(attempt.get('model_requested'))} · {_cell(attempt.get('account') or attempt.get('account_ref'))}"
                           f" · intentos {task.get('attempts') or 0} · {_cell(task.get('title'))}")
    return "\n".join(out)


def _active_line(status: dict[str, Any]) -> str:
    summary = status["summary"]
    line = (f"- {status['req_id']} · {status.get('title') or '-'} · hitos {summary['milestones_done']}/"
            f"{summary['milestones_total']} · tareas {summary['tasks_done']}/{summary['tasks_total']} · "
            f"dificultad {_level(summary.get('difficulty'))}")
    running = next((t for m in status["milestones"] for t in m["tasks"] if t["state"] in ("running", "verifying")), None)
    if running:
        attempt = running.get("attempt") or {}
        route = ", ".join(part for part in (attempt.get("model_requested"),
                                            f"cuenta {attempt['account']}" if attempt.get("account") else None) if part)
        line += f" · en curso: {running['id']}" + (f" ({route})" if route else "")
    return line


def planes_context(project: str, root: Path | None = None) -> list[str]:
    """Lines of the SessionStart "Planes" section for the project's active runs; [] when none (or on any failure)."""
    try:
        rows = [r for r in planstatus.list_plans(root, include_inactive=False)
                if r["project"] == project and r["active"]]
        if not rows:
            return []
        base = planstatus._root(root)
        lines = []
        for row in rows:
            rdir = next(iter(sorted((base / project / "requirements").glob(f"{row['req_id']}-*"))), None)
            if rdir is not None:
                lines.append(_active_line(planstatus.plan_status(project, rdir)))
        if not lines:
            return []
        shown = lines[:ACTIVE_LINES]
        if len(lines) > ACTIVE_LINES:
            shown.append(f"- +{len(lines) - ACTIVE_LINES} más")
        return ["### Planes en ejecución", *shown]
    except Exception as exc:
        LOGGER.debug("planes context unavailable for %s: %s", project, exc)
        return []
