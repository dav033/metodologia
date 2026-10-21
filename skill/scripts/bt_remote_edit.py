"""Owner-approved task brief edits from remote control."""
from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path
from typing import Any


def _write_plan_atomically(path: Path, content: str) -> None:
    mode = stat.S_IMODE(path.stat().st_mode)
    fd, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def dispatch_edit_brief(target: str, params: dict) -> Any:
    """Edit an approved task brief, freeze the owner's new revision, then rebase the active run."""
    import bt_remote_commands as commands
    _, req, rdir = commands._run_target(target)
    typed_req = params.get("typed_req")
    if not isinstance(typed_req, str) or typed_req.strip().upper() != req.upper():
        raise ValueError("edit-brief requiere confirmar el id REQ del objetivo.")

    task_id = params.get("task")
    field = params.get("field", "objective")
    value = params.get("value", params.get("brief"))
    if not isinstance(task_id, str) or not task_id.strip():
        raise ValueError("edit-brief requiere params.task.")
    if not isinstance(field, str):
        raise ValueError("edit-brief requiere un campo válido.")
    field = {"brief": "objective", "criteria": "acceptance_criteria"}.get(field, field)
    if field == "objective":
        if not isinstance(value, str) or not value.strip():
            raise ValueError("edit-brief requiere un brief de tarea no vacío.")
    elif field == "acceptance_criteria":
        if (not isinstance(value, list) or not value
                or any(not isinstance(item, str) or not item.strip() for item in value)):
            raise ValueError("edit-brief requiere una lista no vacía de criterios.")
    else:
        raise ValueError("edit-brief solo puede cambiar objective o acceptance_criteria.")

    reason = params.get("reason", "Owner edited task brief")
    if not isinstance(reason, str):
        raise ValueError("reason debe ser texto.")

    from bt_planner import contract as plan_contract
    from bt_planner import revisions, sync
    import bt_lock

    plan_path = rdir / "PLAN.json"
    if plan_path.is_symlink() or not plan_path.is_file():
        raise ValueError("PLAN.json debe ser un archivo regular para editarlo desde remoto.")

    try:
        with bt_lock.central_lock("plans"):
            original = plan_path.read_bytes()
            current = plan_contract.load(plan_path)
            latest = revisions.latest(rdir)
            if latest is None:
                raise ValueError("edit-brief requiere una revisión congelada para crear N+1.")
            if (current.get("revision") != latest["revision"]
                    or revisions.sha256(plan_contract.dumps(current)) != latest["sha256"]):
                raise ValueError("PLAN.json cambió desde la última revisión aprobada; no se aplicó el cambio.")

            edited = revisions.load_revision(rdir, latest["revision"])
            task = next((item for item in edited.get("tasks", [])
                         if isinstance(item, dict) and item.get("id") == task_id), None)
            if task is None:
                raise ValueError(f"Tarea desconocida en la revisión {latest['revision']}: {task_id}.")
            task[field] = value
            edited["revision"] = latest["revision"] + 1
            _write_plan_atomically(plan_path, plan_contract.dumps(edited))
            try:
                entry = sync.approve_freeze(rdir, req)
            except BaseException:
                _write_plan_atomically(plan_path, original.decode("utf-8"))
                raise
    except (OSError, UnicodeError) as exc:
        raise ValueError("No se pudo leer o guardar PLAN.json para editarlo desde remoto.") from exc

    result = commands.dispatch_run_command("revise", target, {"typed_req": typed_req, "reason": reason})
    messages = result["messages"]
    return {"revision": entry["revision"], "sha256": entry["sha256"], "messages": messages}
