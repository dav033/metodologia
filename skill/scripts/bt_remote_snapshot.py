"""Authenticated remote snapshot read model."""
from __future__ import annotations

import datetime as dt


def snapshot(handler, problem, send_json) -> None:
    """Compact run read model, with live task signals taken from the panel's shared now frame."""
    import bt_core
    import bt_live_api as live
    import bt_plans_api
    import bt_rounds
    import bt_remote_events

    root = bt_core.ROOT
    try:
        summaries = live.run_summaries(root, "global")
        now = live.now_frame_data(root)
    except Exception:
        return problem(handler, 503, "SNAPSHOT_UNAVAILABLE", "La vista remota aún no está disponible.")

    active_by_run: dict[str, dict] = {}
    for item in now["items"]:
        active_by_run.setdefault(f'{item["project"]}/{item["req_id"]}', item)

    runs = []
    for run in summaries:
        active = active_by_run.get(run["run"])
        attempts = [attempt for task in run["tasks"] for attempt in task["history"]]
        last_activity = max((a.get("last_activity_at") for a in attempts if a.get("last_activity_at")), default=None)
        if last_activity is None:
            last_activity = run.get("updated_at")
        tasks = []
        for task in run["tasks"]:
            review = next((a for a in reversed(task["history"]) if a.get("state") == "rejected"), None)
            current = task.get("attempt")
            tasks.append({"id": task["id"], "title": task["title"], "state": task["state"],
                          "activeAttempt": live._attempt(current) if current and current.get("live") else None,
                          "reviewAttempt": live._attempt(review),
                          "history": [live._attempt(a) for a in task["history"]]})
        runs.append({"id": run["run"], "project": run["project"], "req": run["req_id"],
                     "reqId": run["req_id"],
                     "state": run.get("status") or ("running" if run.get("active") else "idle"),
                     "title": run["title"], "status": run["status"], "active": run["active"],
                     "activeTask": ({"id": active["task"], "title": active["task_title"],
                                     "state": active["state"], "attempt": live._attempt(active["attempt"])}
                                    if active else None),
                     "activeAttempt": live._attempt(active["attempt"]) if active else None,
                     "lastActivityAt": last_activity, "tasks": tasks})
    plans, rounds, decisions = [], [], []
    try:
        for summary in bt_plans_api.plans_payload(root):
            project, req = summary["project"], summary["req_id"]
            try:
                status = bt_plans_api.status_of(root, project, req)
            except (OSError, ValueError, bt_plans_api.PlanError):
                continue
            plan = status.get("plan") if isinstance(status.get("plan"), dict) else {}
            plan_tasks = []
            for milestone in status.get("milestones", []):
                for task in milestone.get("tasks", []):
                    current = task.get("attempt")
                    plan_tasks.append({"id": task["id"], "title": task.get("title"),
                                       "state": task.get("state", "pending"),
                                       "acceptanceCriteria": task.get("acceptance_criteria", []),
                                       "activeAttempt": live._attempt(current) if current and current.get("live") else None,
                                       "history": [live._attempt(attempt) for attempt in task.get("history", [])]})
            plans.append({"id": plan.get("plan_id") or f"{project}/{req}", "project": project, "req": req,
                          "title": summary.get("title"),
                          "state": plan.get("status") or summary.get("run_status") or "unknown",
                          "revision": plan.get("revision"), "updatedAt": summary.get("updated_at"),
                          "tasks": plan_tasks})
            decisions.extend({"id": item["id"], "project": project, "req": req,
                              "task": item.get("task"), "title": item.get("title"),
                              "what": item.get("what"), "evidence": item.get("evidence", []),
                              "options": item.get("options", []), "recommended": item.get("recommended"),
                              "unskippable": item.get("unskippable"), "state": item.get("state", "open"),
                              "revision": item.get("revision")}
                             for item in status.get("decisions", []) if isinstance(item, dict))
            rdir = bt_plans_api.req_dir(root, project, req)
            for round_path in bt_rounds.list_rounds(rdir):
                try:
                    item = bt_rounds.load(round_path)
                except (OSError, ValueError):
                    continue
                rounds.append({"project": project, "req": req, "round": item.get("round"),
                               "id": item.get("id") or round_path.stem,
                               "title": item.get("title"), "intro": item.get("intro"),
                               "coverage": item.get("coverage"), "status": item.get("status"),
                               "revision": item.get("revision"), "questions": item.get("questions", [])})
    except (OSError, ValueError, bt_plans_api.PlanError):
        # A malformed plan must not make the independent run list unavailable.
        pass
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    snapshot = {"schemaVersion": 1, "generatedAt": generated_at, "cursor": generated_at,
                "runs": runs, "plans": plans, "rounds": rounds,
                "decisionRequests": decisions}
    return send_json(handler, bt_remote_events.redact(snapshot), 200)


