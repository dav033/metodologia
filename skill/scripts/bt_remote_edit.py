"""Owner-confirmed brief edits dispatched from the remote command ledger."""
from __future__ import annotations

import json


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
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or not isinstance(document.get("tasks"), list):
        raise ValueError("PLAN.json no contiene una lista de tareas editable.")
    task = next((item for item in document["tasks"] if isinstance(item, dict) and item.get("id") == task_id), None)
    if task is None:
        raise ValueError(f"No existe la tarea {task_id} en PLAN.json.")
    current = ops.bound_plan(rdir)
    document["revision"] = max(int(document.get("revision", 0)), current.revision) + 1
    task["objective" if field == "brief" else "acceptance_criteria"] = value.strip() if field == "brief" else value
    path.write_text(contract.dumps(document), encoding="utf-8")
    # The latest revision must also pass the same approved-plan publication gate as local edits.
    if problem := adapter.plan_consumer_problem(rdir):
        raise ValueError(problem)
    report = planner_sync.approve_freeze(rdir, req)
    messages = ops.apply(project, req, rdir, "revise", reason=f"remote edit of {task_id}")
    messages.append(ops.resume(project, req, rdir))
    return {"revision": report["revision"], "messages": messages}
