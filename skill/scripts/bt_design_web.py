"""Requirement-page operations for UI contract approval and its local preview."""
from __future__ import annotations

import json
from pathlib import Path

import bt_config
import bt_design_approval as approval


def preview_file(root: Path, project: str, rdir: Path, ref: str = "") -> Path | None:
    if not (bt_config.get("design.preview", False) is True or
            project in bt_config.get("design.preview_projects", [])):
        return None
    try:
        plan = json.loads((Path(rdir) / "PLAN.json").read_text(encoding="utf-8"))
        subplan = next((item for item in plan.get("subplans", []) if isinstance(item, dict) and
                        isinstance(item.get("ui"), dict) and
                        (not ref or f"{item['ui'].get('contract')}@v{item['ui'].get('version')}" == ref)), None)
        if subplan is None:
            return None
        ui = subplan["ui"]
        repo = approval.repository_for_contract(root, project, rdir, f"{ui['contract']}@v{ui['version']}")
        file = repo / "design/preview/index.html" if repo else None
        if file is None or not file.is_file():
            return None
        try:
            file.resolve().relative_to(repo.resolve())
        except ValueError:
            return None
        return file
    except (OSError, ValueError, KeyError, TypeError):
        return None


def decide(root: Path, project: str, rid: str, rdir: Path, form: dict, commit) -> str:
    ref, decision = form.get("contract", ""), form.get("decision")
    comments = form.get("comments", "").strip()
    if decision not in ("approve", "changes"):
        return "Decisión de contrato inválida."
    if decision == "changes" and not comments:
        return "Para pedir cambios escribe qué debe cambiar."
    repo = approval.repository_for_contract(root, project, rdir, ref)
    if repo is None:
        raise SystemExit(f"No se pudo resolver el repositorio para {ref}.")
    record = approval.decide(rdir, repo, ref, decision == "approve", comments, "owner", "web")
    commit(root, f"{project}: {rid} design contract {ref} {record['status']} (web)")
    if decision == "approve":
        released = _release_ui_holds(project, rid, rdir)
        return (f"Contrato {ref} aprobado con SHA256 {record['sha256']}. "
                f"Tareas de interfaz reabiertas: {', '.join(released) or 'ninguna' }.")
    try:
        rows = approval.ui_contracts(rdir, project)
        task = next(row["design_task"] for row in rows if row["contract"] == ref)
        import bt_scheduler_ops
        moved = bt_scheduler_ops.apply(project, rid, rdir, "rework", task, comments, only=True, confirm=True)
    except Exception as exc:  # noqa: BLE001 - the approval record remains durable and the gate stays closed
        return f"Cambios registrados para {ref}; no se pudo reabrir la tarea de diseño: {type(exc).__name__}: {exc}"
    return f"Cambios registrados para {ref}; tarea de diseño devuelta para rework: {', '.join(moved)}."


def _release_ui_holds(project: str, rid: str, rdir: Path) -> list[str]:
    """Release only M1 tasks held specifically for this environment gate."""
    plan = json.loads((Path(rdir) / "PLAN.json").read_text(encoding="utf-8"))
    status = __import__("bt_planstatus").plan_status(project, Path(rdir))
    states = {task["id"]: task for milestone in status["milestones"] for task in milestone["tasks"]}
    released = []
    import bt_scheduler_ops
    for task in plan.get("tasks", []):
        if not isinstance(task, dict) or task.get("ui") is not True:
            continue
        current = states.get(task.get("id"), {})
        if current.get("state") == "blocked" and current.get("reason") == "blocked_environment":
            bt_scheduler_ops.apply(project, rid, Path(rdir), "reopen", task["id"],
                                   "design contract approval is now available", only=True, confirm=True)
            released.append(task["id"])
    return released
