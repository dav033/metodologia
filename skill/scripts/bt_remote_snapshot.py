"""Build the mobile snapshot from the live run and plan projections."""

from __future__ import annotations

import datetime as dt


def build_snapshot(root) -> dict:
    """Return the versioned mobile snapshot, including plan, round and decision details."""
    import bt_live_api as live
    import bt_plans_api
    import bt_rounds

    summaries = live.run_summaries(root, "global")
    now = live.now_frame_data(root)
    plan_summaries = bt_plans_api.plans_payload(root)
    active_by_run: dict[str, dict] = {}
    for item in now["items"]:
        active_by_run.setdefault(f'{item["project"]}/{item["req_id"]}', item)

    runs = []
    for run in summaries:
        active = active_by_run.get(run["run"])
        attempts = [attempt for task in run["tasks"] for attempt in task["history"]]
        last_activity = max((item.get("last_activity_at") for item in attempts
                             if item.get("last_activity_at")), default=None) or run.get("updated_at")
        tasks = []
        for task in run["tasks"]:
            history = task["history"]
            review = next((item for item in reversed(history) if item.get("state") in {"failed", "rejected"}), None)
            current = task.get("attempt")
            tasks.append({"id": task["id"], "title": task["title"], "state": task["state"],
                          "activeAttempt": live._attempt(current) if current and current.get("live") else None,
                          "reviewAttempt": live._attempt(review),
                          "history": [live._attempt(item) for item in history]})
        runs.append({"id": run["run"], "project": run["project"], "req": run["req_id"],
                     "reqId": run["req_id"],
                     "state": run.get("status") or ("running" if run.get("active") else "idle"),
                     "title": run["title"], "status": run["status"], "active": run["active"],
                     "revision": run.get("revision"), "updatedAt": run.get("updated_at"),
                     "activeAttempt": live._attempt(active["attempt"]) if active else None,
                     "activeTask": ({"id": active["task"], "title": active["task_title"],
                                     "state": active["state"], "attempt": live._attempt(active["attempt"])}
                                    if active else None),
                     "lastActivityAt": last_activity, "tasks": tasks})

    plans, rounds, decisions = [], [], []
    for plan in plan_summaries:
        project, req = plan["project"], plan["req_id"]
        req_dir = bt_plans_api.req_dir(root, project, req)
        status = bt_plans_api.status_of(root, project, req)
        plan_tasks = []
        for milestone in status.get("milestones", []):
            for task in milestone.get("tasks", []):
                detail = task.get("detail") if isinstance(task.get("detail"), dict) else {}
                plan_tasks.append({"id": task.get("id"), "title": task.get("title"),
                                   "state": task.get("state", "pending"),
                                   "revision": task.get("revision"), "updatedAt": task.get("updated_at"),
                                   "acceptanceCriteria": detail.get("acceptance_criteria", [])})
        plans.append({"id": status.get("plan", {}).get("plan_id") or f"{project}/{req}",
                      "project": project, "req": req,
                      "state": status.get("plan", {}).get("status") or plan.get("plan_status") or "unknown",
                      "revision": status.get("plan", {}).get("revision") or plan.get("revision"),
                      "updatedAt": plan.get("updated_at"), "tasks": plan_tasks,
                      "acceptanceCriteria": [criterion for task in plan_tasks
                                             for criterion in task.get("acceptanceCriteria", [])]})
        for request in bt_plans_api.open_decisions(req_dir):
            options = []
            for option in request.get("options", []):
                if isinstance(option, str):
                    options.append({"id": option, "label": option.replace("_", " "),
                                    "consequence": option.replace("_", " ")})
                elif isinstance(option, dict) and isinstance(option.get("id"), str):
                    options.append(option)
            decisions.append({**request, "project": project, "req": req, "options": options})
        for number in bt_plans_api.open_rounds(req_dir):
            try:
                data = bt_rounds.load(bt_rounds.rounds_dir(req_dir) / f"round-{number:02d}.json")
            except (OSError, ValueError):
                continue
            rounds.append({"project": project, "req": req, "round": number,
                           **{key: data[key] for key in ("id", "title", "intro", "coverage", "status", "questions")
                              if key in data}})

    generated_at = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    return {"schemaVersion": 1, "generatedAt": generated_at, "cursor": generated_at,
            "runs": runs, "plans": plans, "rounds": rounds, "decisionRequests": decisions}
