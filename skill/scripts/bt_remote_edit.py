"""Owner-confirmed brief edits dispatched from the remote command ledger."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


def _replace_bytes(path: Path, content: bytes) -> None:
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def dispatch_edit_brief(target: str, params: dict) -> dict:
    """Create an owner-approved revision from the run's exact base and rebase the run onto it."""
    import bt_core
    import bt_planner.contract as contract
    import bt_planner.revisions as revisions
    import bt_planner.sync as planner_sync
    import bt_plans_api
    import bt_scheduler_adapter as adapter
    import bt_scheduler_ops as ops
    from bt_planner._lock import exclusive

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
        value = value.strip()
    elif (not isinstance(value, list) or not value
          or any(not isinstance(item, str) or not item.strip() for item in value)):
        raise ValueError("criteria debe ser una lista de criterios no vacíos.")
    elif sum(map(len, value)) > 20_000:
        raise ValueError("criteria excede 20000 caracteres.")

    rdir = bt_plans_api.req_dir(bt_core.ROOT, project, req)
    path = rdir / "PLAN.json"
    if path.is_symlink() or not path.is_file():
        raise ValueError("PLAN.json debe ser un archivo regular editable.")
    with exclusive(rdir / ".remote-edit.lock"):
        before = path.read_bytes()
        working = json.loads(before)
        if not isinstance(working, dict) or not isinstance(working.get("tasks"), list):
            raise ValueError("PLAN.json no contiene una lista de tareas editable.")
        task = next((item for item in working["tasks"]
                     if isinstance(item, dict) and item.get("id") == task_id), None)
        if task is None:
            raise ValueError(f"No existe la tarea {task_id} en PLAN.json.")

        bound = ops.bound_plan(rdir)
        latest = revisions.latest(rdir)
        if latest is None:
            raise ValueError("PLAN_NOT_FROZEN: no existe una revisión aprobada base.")
        if latest["revision"] != bound.revision:
            raise ValueError("PLAN_BASE_STALE: el run no está ligado a la última revisión aprobada.")
        base = revisions.load_revision(rdir, latest["revision"])
        if working != base:
            raise ValueError("PLAN_DRIFT: PLAN.json contiene cambios no aprobados; restaure la revisión aprobada.")
        if planner_sync.plan_status(rdir) not in planner_sync.APPROVED_STATES:
            raise ValueError("PLAN_NOT_APPROVED: PLAN.md debe conservar un estado aprobado.")

        document = json.loads(json.dumps(base))
        task = next(item for item in document["tasks"] if item.get("id") == task_id)
        document["revision"] = latest["revision"] + 1
        task["objective" if field == "brief" else "acceptance_criteria"] = value
        compatibility = adapter.plan_compatibility_report(rdir, plan_path=path)
        if problem := adapter.plan_consumer_problem(rdir, plan_path=path):
            raise ValueError(problem)

        published = False
        try:
            _replace_bytes(path, contract.dumps(document).encode("utf-8"))
            import bt_plan_adapter as plan_adapter
            if problem := plan_adapter.publishable_problem(rdir, compatibility_report=compatibility):
                raise ValueError(problem)
            report = revisions.freeze(rdir, document, source="remote-owner")
            published = True
        except BaseException:
            if not published:
                _replace_bytes(path, before)
            raise

        messages = ops.apply(project, req, rdir, "revise", reason=f"remote edit of {task_id}")
        messages.append(ops.resume(project, req, rdir))
        return {"revision": report["revision"], "messages": messages}
