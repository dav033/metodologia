"""Owner-confirmed brief edits dispatched from the remote command ledger."""
from __future__ import annotations

import json


def dispatch_edit_brief(target: str, params: dict) -> dict:
    """Create and freeze a new approved plan revision, then rebase its Scheduler run."""
    import bt_core
    import bt_planner.contract as contract
    import bt_planner.revisions as revisions
    import bt_plans_api
    import bt_scheduler_adapter as adapter
    import bt_scheduler_ops as ops

    project, separator, req = target.partition("/")
    if not separator:
        raise ValueError("target debe tener el formato project/REQ-NNN.")
    confirmed = params.get("typed_req")
    if not isinstance(confirmed, str) or confirmed.strip().upper() != req.upper():
        raise ValueError("edit-brief requiere confirmar el id REQ del objetivo.")
    task_id, brief = params.get("task"), params.get("brief")
    if not isinstance(task_id, str) or not task_id or not isinstance(brief, str) or not brief.strip():
        raise ValueError("edit-brief requiere task y brief no vacíos.")
    if len(brief) > 20_000:
        raise ValueError("brief excede 20000 caracteres.")

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
    task["objective"] = brief.strip()
    path.write_text(contract.dumps(document), encoding="utf-8")
    report = revisions.freeze(rdir, document, source="remote-owner")
    # The latest revision must also pass the same approved-plan publication gate as local edits.
    import bt_plan_adapter as plan_adapter
    if problem := plan_adapter.plan_consumer_problem(rdir):
        raise ValueError(problem)
    messages = ops.apply(project, req, rdir, "revise", reason=f"remote edit of {task_id}")
    messages.append(ops.resume(project, req, rdir))
    return {"revision": report["revision"], "messages": messages}
