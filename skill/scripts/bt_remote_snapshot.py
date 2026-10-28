"""Build the mobile snapshot from the live run and plan projections.

The shape is the canonical RemoteSnapshot contract (skill/scripts/bt_contracts/remote.py, published as
remote/contract/snapshot.schema.json): camelCase only, and every nested record projected to its contract fields, so
page-only data (rendered diagnosis HTML, form prefills, free-form round keys) never reaches the phone. Stdlib only.
"""

from __future__ import annotations

import datetime as dt

# live._attempt (snake_case) -> contract Attempt (camelCase)
_ATTEMPT_FIELDS = (("id", "id"), ("number", "number"), ("state", "state"), ("provider", "provider"),
                   ("model", "model"), ("effort", "effort"), ("account", "account"), ("started_at", "startedAt"),
                   ("ended_at", "endedAt"), ("duration_s", "durationS"), ("live", "live"), ("verdict", "verdict"),
                   ("failure", "failure"), ("last_activity_at", "lastActivityAt"))
_QUESTION_FIELDS = ("recommended", "why", "suggested")
_ROUND_FIELDS = ("id", "title", "intro", "coverage", "revision")


def _attempt(item: dict | None) -> dict | None:
    import bt_live_api as live

    shown = live._attempt(item)
    return None if shown is None else {camel: shown.get(snake) for snake, camel in _ATTEMPT_FIELDS}


def _text(value) -> str | None:
    return value if isinstance(value, str) else None


def _option(option) -> dict | None:
    if isinstance(option, str):
        return {"id": option, "label": option.replace("_", " "), "consequence": option.replace("_", " ")}
    if isinstance(option, dict) and isinstance(option.get("id"), str) and option["id"]:
        label = _text(option.get("label")) or option["id"].replace("_", " ")
        return {"id": option["id"], "label": label, "consequence": _text(option.get("consequence")) or label}
    return None


def _decision(request: dict, project: str, req: str) -> dict:
    """An open decision as plain contract fields; the plan page's `diagnosis_html`/`note_prefill` stay local."""
    options = [shown for shown in map(_option, request.get("options") or []) if shown]
    return {"id": str(request.get("id")), "project": project, "req": req, "task": _text(request.get("task")),
            "attempt": _text(request.get("attempt")), "source": _text(request.get("source")),
            "title": str(request.get("title") or ""), "what": str(request.get("what") or ""),
            "needs": _text(request.get("needs")), "reason": _text(request.get("reason")),
            "evidence": [item for item in request.get("evidence") or [] if isinstance(item, str)],
            "options": options, "recommended": _text(request.get("recommended")),
            "unskippable": request.get("unskippable") is True}


def _question(question: dict) -> dict:
    options = [{"key": str(item.get("key")), "label": str(item.get("label") or item.get("key"))}
               for item in question.get("options") or [] if isinstance(item, dict) and item.get("key") is not None]
    shown = {"id": str(question.get("id")), "text": str(question.get("text") or ""),
             "type": "choice" if question.get("type") == "choice" or options else "open"}
    if options:
        shown["options"] = options
    return {**shown, **{key: question[key] for key in _QUESTION_FIELDS if isinstance(question.get(key), str)}}


def _round(data: dict, project: str, req: str, number: int) -> dict:
    shown = {"project": project, "req": req, "round": number, "status": str(data.get("status") or "open"),
             **{key: data[key] for key in _ROUND_FIELDS if key in data and data[key] is not None}}
    shown["questions"] = [_question(item) for item in data.get("questions") or [] if isinstance(item, dict)]
    return shown


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
                          "activeAttempt": _attempt(current) if current and current.get("live") else None,
                          "reviewAttempt": _attempt(review),
                          "history": [_attempt(item) for item in history]})
        state = run.get("status") or ("running" if run.get("active") else "idle")
        # `status` is the deprecated alias window of `state` for gateways deployed before the contract (v2 drops it).
        runs.append({"id": run["run"], "project": run["project"], "req": run["req_id"], "state": state,
                     "status": run.get("status"), "title": run["title"], "active": run["active"],
                     "revision": run.get("revision"), "updatedAt": run.get("updated_at"),
                     "activeAttempt": _attempt(active["attempt"]) if active else None,
                     "activeTask": ({"id": active["task"], "title": active["task_title"],
                                     "state": active["state"], "attempt": _attempt(active["attempt"])}
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
        decisions.extend(_decision(request, project, req) for request in bt_plans_api.open_decisions(req_dir))
        for number in bt_plans_api.open_rounds(req_dir):
            try:
                data = bt_rounds.load(bt_rounds.rounds_dir(req_dir) / f"round-{number:02d}.json")
            except (OSError, ValueError):
                continue
            rounds.append(_round(data, project, req, number))

    generated_at = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    return {"schemaVersion": 1, "generatedAt": generated_at, "cursor": generated_at,
            "runs": runs, "plans": plans, "rounds": rounds, "decisionRequests": decisions}
