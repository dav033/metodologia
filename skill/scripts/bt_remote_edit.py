"""Owner-confirmed brief edits dispatched from the remote command ledger."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


def dispatch_edit_brief(target: str, params: dict) -> dict:
    """Create and freeze a new approved plan revision, then rebase its Scheduler run."""
    import bt_core
    import bt_planner.contract as contract
    import bt_planner.sync as planner_sync
    import bt_plans_api
    import bt_scheduler_adapter as adapter
    import bt_scheduler_ops as ops

    project, separator, req = target.partition("/")
    if not separator:
        raise ValueError("target debe tener el formato project/REQ-NNN.")
    confirmed = params.get("typed_req")
    if not isinstance(confirmed, str) or confirmed.strip().upper() != req.upper():
        raise ValueError("edit-brief requiere confirmar el id REQ del objetivo.")
    task_id = params.get("task")
    field = params.get("field", "brief")
    field = {"objective": "brief", "acceptance_criteria": "criteria"}.get(field, field)
    value = params.get("value", params.get("brief"))
    if not isinstance(task_id, str) or not task_id or field not in {"brief", "criteria"}:
        raise ValueError("edit-brief requiere task y field brief o criteria.")
    if field == "brief":
        if not isinstance(value, str) or not value.strip():
            raise ValueError("edit-brief requiere un brief no vacío.")
        if len(value) > 20_000:
            raise ValueError("brief excede 20000 caracteres.")
    else:
        if (not isinstance(value, list) or not value or
                any(not isinstance(item, str) or not item.strip() for item in value)):
            raise ValueError("criteria debe ser una lista de criterios no vacíos.")
        if sum(map(len, value)) > 20_000:
            raise ValueError("criteria excede 20000 caracteres.")

    rdir = bt_plans_api.req_dir(bt_core.ROOT, project, req)
    path = rdir / "PLAN.json"
    if path.is_symlink() or not path.is_file():
        raise ValueError("PLAN.json debe ser un archivo regular editable.")
    # Serialize edit transactions separately from the revision store lock, which freeze() acquires itself.
    from bt_planner._lock import exclusive
    with exclusive(rdir / ".remote-edit.lock"):
        return _edit_locked(project, req, rdir, path, task_id, field, value,
                            bt_core, contract, planner_sync, ops, adapter)


def _edit_locked(project, req, rdir, path, task_id, field, value, bt_core, contract, planner_sync, ops, adapter):
    import bt_planner.revisions as revisions

    before = path.read_bytes()
    document = json.loads(before)
    if not isinstance(document, dict) or not isinstance(document.get("tasks"), list):
        raise ValueError("PLAN.json no contiene una lista de tareas editable.")
    task = next((item for item in document["tasks"] if isinstance(item, dict) and item.get("id") == task_id), None)
    if task is None:
        raise ValueError(f"No existe la tarea {task_id} en PLAN.json.")
    ops.bound_plan(rdir)  # fail closed when the active run's pinned revision is unreadable
    approved = revisions.latest(rdir)
    if approved is None:
        raise ValueError("PLAN_NOT_FROZEN: no existe una revisión aprobada base.")
    base = revisions.load_revision(rdir, approved["revision"])
    if document != base:
        raise ValueError("PLAN_DRIFT: PLAN.json contiene cambios no aprobados; restaure la revisión aprobada.")
    document["revision"] = approved["revision"] + 1
    task["objective" if field == "brief" else "acceptance_criteria"] = value.strip() if field == "brief" else value
    # Freeze only an owner-approved plan. Keep the working file intact if the publication gate refuses it.
    text = contract.dumps(document)
    fd, temporary_name = tempfile.mkstemp(prefix="PLAN.json.", suffix=".tmp", dir=rdir)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        if problem := adapter.plan_consumer_problem(rdir):
            raise ValueError(problem)
        report = planner_sync.approve_freeze(rdir, req)
    except BaseException:
        rollback_fd, rollback_name = tempfile.mkstemp(prefix="PLAN.json.rollback.", suffix=".tmp", dir=rdir)
        rollback = Path(rollback_name)
        try:
            with os.fdopen(rollback_fd, "wb") as handle:
                handle.write(before)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(rollback, path)
        finally:
            rollback.unlink(missing_ok=True)
            temporary.unlink(missing_ok=True)
        raise
    finally:
        temporary.unlink(missing_ok=True)
    messages = ops.apply(project, req, rdir, "revise", reason=f"remote edit of {task_id}")
    messages.append(ops.resume(project, req, rdir))
    return {"revision": report["revision"], "messages": messages}
