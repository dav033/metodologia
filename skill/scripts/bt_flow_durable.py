"""Flow events of a run the durable runtime owns (D-150): its telemetry (`<state>/durable/telemetry.jsonl`), read-only.

The legacy stores the flow bus tails stop at a migration (pictures REQ-021 showed «en pausa, último mensaje hace 15 h»
while the durable runtime worked). Each telemetry record of the run becomes a message between the same parties: M1 is
the run and task workflows, M2 the router, M3 the agent attempt, M5 the recovery policy, M6 verification and the audit
gate, `owner` the owner's decisions. The cursor is the record's line number; a record this file does not know is shown
as `unknown`, never dropped.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

STORE = "dbos"
_KEY = re.compile(r"^(?P<project>.+?)-(?P<req>REQ-\d+)-r(?P<rev>\d+)-(?P<task>.+)-a(?P<number>\d+)-[0-9a-f]{8}$")
STATUS_ES = {"completed": "aceptada", "blocked": "bloqueada", "failed": "falló", "cancelled": "cancelada",
             "needs_decision": "espera tu decisión"}


def telemetry_path() -> Path:
    import bt_core
    return Path(bt_core.STATE) / "durable" / "telemetry.jsonl"


def _of_run(record: dict[str, Any], project: str, req: str) -> tuple[str, str] | None:
    """(task, attempt key) when the record belongs to `project`/`req`, else None."""
    run_id = str(record.get("run_id") or "")
    key = str(record.get("attempt_key") or "")
    match = _KEY.match(key) if key else None
    if run_id.startswith(f"{project}:{req}:"):
        return str(record.get("task_id") or (match["task"] if match else "")), key
    if match and match["project"] == re.sub(r"[^A-Za-z0-9._-]+", "-", project) and match["req"] == req:
        return str(record.get("task_id") or match["task"]), key
    return None


def _message(r: dict[str, Any], task: str) -> tuple[str, str, str, str, dict[str, Any]]:
    """(from, to, kind, summary, data) of one telemetry record."""
    name = r.get("event")
    if name == "route_decision":
        route = r.get("route") or "sin ruta"
        return "M2", "M1", "assignment", f"{task} → {route}" + (f" ({r['basis']})" if r.get("basis") else ""), \
            {"route": r.get("route"), "basis": r.get("basis")}
    if name == "attempt_started":
        return "M1", "M3", "execution_started", f"{task} arranca · {r.get('provider')}/{r.get('model')}", {}
    if name == "file_guard":
        count = int(r.get("count") or 0)
        return "M3", "M1", "executor_event", f"{task} entrega su trabajo" + (f" · {count} archivo(s) >500 líneas" if count
                                                                             else ""), {}
    if name == "task_settled":
        status = str(r.get("status") or "")
        return "M1", "M1", "task_state", f"{task} {STATUS_ES.get(status, status)} · {r.get('attempts')} intento(s)", \
            {"state": status}
    if name == "recovery_decision":
        return "M5", "M1", "recovery", f"{task}: {r.get('action')} · {r.get('code')} ({r.get('reason') or ''})", \
            {"action": r.get("action"), "code": r.get("code")}
    if name == "decision_requested":
        return "M1", "owner", "recommendation", f"{task} necesita tu decisión: {r.get('reason') or ''}", \
            {"action": "block"}
    if name == "decision_answered":
        return "owner", "M1", "manual_resolution", f"{task}: respondiste {r.get('action')}", {}
    if name == "owner_reverify":
        return "owner", "M6", "verify_order", f"{task}: verificar otra vez el mismo trabajo", {}
    if name in ("audit_passed", "audit_blocked"):
        ok = name == "audit_passed"
        return "M6", "M1", "verdict", f"{task}: auditoría " + ("aprobada" if ok else
                                                                f"bloqueada · {len(r.get('findings') or [])} hallazgo(s)"), \
            {"status": "pass" if ok else "fail"}
    if name == "legacy_reconciled":
        return "M6", "M1", "verdict", f"{task}: trabajo heredado verificado · {r.get('status')}", \
            {"status": "pass" if r.get("status") == "completed" else "fail"}
    if name in ("gate_composed", "gate_recompose"):
        what = (f"compuesta ({r.get('candidate_id')})" if r.get("state") == "candidate" else f"rechazada: {r.get('reason')}") \
            if name == "gate_composed" else "se compone otra vez"
        return "M1", "M1", "start_order", f"puerta {r.get('gate')} {what}", {}
    if name == "run_line_conflict":
        return "M1", "M1", "incident", f"{task} choca en la línea del run (queda en la de su subplan)", {}
    if name == "run_reopened":
        return "owner", "M1", "run_resumed", "la ejecución se reabre", {}
    if name == "run_settled":
        return "M1", "M1", "task_state", f"la ejecución termina: {r.get('status')}", {"state": r.get("status")}
    if name == "subplans_enabled":
        return "M1", "M1", "start_order", "líneas por subplan: " + ", ".join(r.get("subplans") or []), {}
    if name in ("stage_joined", "stage_join_waiting"):
        return "owner", "M1", "run_rebased", f"etapa nueva: {r.get('to')}" + (" (espera a los intentos vivos)"
                                                                            if name == "stage_join_waiting" else ""), {}
    return "M1", "M1", "unknown", str(name), {}


def events(run: str, project: str, req: str, after: int, path: Path | None = None) -> list[dict[str, Any]]:
    """Flow events (bt_flow_bus.event) of `project`/`req` in the durable telemetry after line `after`."""
    from bt_flow_bus import event
    try:
        lines = (path or telemetry_path()).read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out = []
    for number, line in enumerate(lines, 1):
        if number <= after:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        found = _of_run(record, project, req) if isinstance(record, dict) else None
        if found is None:
            continue
        task, key = found
        frm, to, kind, summary, data = _message(record, task)
        out.append(event(run, STORE, number, float(record.get("ts") or 0), frm, to, kind, summary, task=task,
                         attempt=key, data={**data, "durable": record.get("event")}))
    return out


def source(rdir: Path) -> tuple[str, int]:
    """The cursor's file for `bt_flow_bus.sources` (empty for a run the durable runtime never owned)."""
    if not (Path(rdir) / "RUN.owner.json").is_file():
        return "", 0
    path = telemetry_path()
    try:
        return str(path), path.stat().st_ino
    except OSError:
        return str(path), 0


def for_run(run: str, rdir: Path, after: int) -> list[dict[str, Any]]:
    """`events` of the run in `rdir` (`run` = project/REQ-NNN), only when the durable runtime owns or owned it."""
    if not (Path(rdir) / "RUN.owner.json").is_file():
        return []
    project, _, req = run.partition("/")
    return events(run, project, req, after)
