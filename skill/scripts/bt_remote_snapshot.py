"""Build the compact remote run read model from the panel's live caches."""
from __future__ import annotations

import datetime as dt


def build(root, live) -> dict:
    """Return runs, active task signals, and last activity using the shared now frame."""
    summaries = live.run_summaries(root, "global")
    now = live.now_frame_data(root)

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
                     "lastActivityAt": last_activity, "tasks": tasks})
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    return {"schemaVersion": 1, "generatedAt": generated_at, "cursor": generated_at, "runs": runs}
