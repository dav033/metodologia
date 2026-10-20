"""Mobile-contract read models for the remote API: runs, plans, rounds, decisions, quotas and command history.

The production projections (`bt_live_api.run_summaries`, `bt_planstatus`) use the laptop's own vocabulary
(`req_id`, `status`, `attempt`). The mobile parser requires `req`, `state` and `activeAttempt`, so every row is
projected here and keeps its original keys alongside the contract ones.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

DEFAULT_MAX_ATTEMPTS = 3
_WINDOWS = (("five_hour", "5 h"), ("seven_day", "7 d"))


def max_attempts() -> int:
    try:
        import bt_config
        value = bt_config.get("scheduler.max_attempts", DEFAULT_MAX_ATTEMPTS)
        return value if isinstance(value, int) and value >= 1 else DEFAULT_MAX_ATTEMPTS
    except Exception:  # noqa: BLE001 - an unreadable config must not blank the snapshot
        return DEFAULT_MAX_ATTEMPTS


def _active_attempt(attempt: dict | None) -> dict | None:
    if not attempt or not attempt.get("id"):
        return None
    return {"id": attempt["id"], "state": attempt.get("state"),
            "updatedAt": attempt.get("last_activity_at") or attempt.get("ended_at") or attempt.get("started_at")}


def task_view(task: dict) -> dict:
    attempt = task.get("attempt") if isinstance(task.get("attempt"), dict) else None
    live = attempt if attempt and (attempt.get("live") or task.get("state") in {"running", "verifying"}) else None
    state = task.get("state") or "pending"
    # A failed/rejected task keeps its last attempt addressable for the failure review, without making it "active".
    review = _active_attempt(attempt) if live is None and state in {"failed", "rejected"} else None
    return {**task, "state": state, "activeAttempt": _active_attempt(live), "reviewAttempt": review,
            "updatedAt": (attempt or {}).get("last_activity_at") or (attempt or {}).get("ended_at"),
            "acceptanceCriteria": task.get("acceptanceCriteria") or task.get("acceptance_criteria") or []}


def run_view(run: dict) -> dict:
    """Add the mobile contract keys (`req`, `state`, `activeAttempt`, `updatedAt`) to one run summary."""
    project, _, req = str(run.get("run", "")).partition("/")
    tasks = [task_view(task) for task in run.get("tasks") or []]
    active = next((task["activeAttempt"] for task in tasks if task["activeAttempt"]), None)
    return {**run, "project": run.get("project") or project, "req": run.get("req") or run.get("req_id") or req,
            "state": run.get("state") or run.get("status") or "unknown", "updatedAt": run.get("updated_at"),
            "activeAttempt": active, "tasks": tasks}


def _decision_view(project: str, req: str, request: dict) -> dict:
    return {**request, "project": project, "req": req, "state": "open",
            "options": [{"id": o.get("id"), "label": o.get("label"), "consequence": o.get("consequence")}
                        for o in request.get("options") or []]}


def _open_rounds(project: str, req: str, rdir: Path) -> list[dict]:
    out = []
    for path in sorted((rdir / "rounds").glob("round-*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict) or data.get("status") != "open" or not isinstance(data.get("round"), int):
            continue
        try:
            created = dt.datetime.fromtimestamp(path.stat().st_mtime, dt.UTC).isoformat()
        except OSError:
            created = None
        out.append({**data, "project": project, "req": req, "id": f"round-{data['round']:02d}",
                    "created_at": data.get("created_at") or created})
    return out


def _decisions(rdir: Path) -> list[dict]:
    try:
        import bt_scheduler_decisions as decisions
        return decisions.open_requests(rdir)
    except Exception:  # noqa: BLE001 - a run whose state cannot be read asks nothing here
        return []


def plans_view(root: Path) -> list[dict]:
    """Plan rows with the contract keys, their tasks, and the open decisions and rounds each one waits on."""
    import bt_planstatus as ps
    rows = []
    for project, rdir in ps._requirement_dirs(Path(root).resolve()):
        try:
            status = ps.plan_status(project, rdir)
        except Exception:  # noqa: BLE001 - one unreadable plan must not blank the list
            continue
        req = status["req_id"]
        summary = status["summary"]
        tasks = [task_view(task) for milestone in status["milestones"] for task in milestone["tasks"]]
        rows.append({
            "project": project, "req_id": req, "req": req, "title": status["title"],
            "plan_status": status["plan"]["status"], "run_status": status["run"]["status"],
            "state": status["plan"]["status"] or status["run"]["status"] or "unknown",
            "active": status["run"]["active"], "id": status["plan"].get("plan_id"),
            "revision": status["plan"].get("revision"),
            "progress": {"done": summary["tasks_done"], "total": summary["tasks_total"]},
            "difficulty": summary["difficulty"], "updated_at": status["run"]["updated_at"],
            "updatedAt": status["run"]["updated_at"], "tasks": tasks,
            "decisions": [_decision_view(project, req, d) for d in _decisions(rdir)],
            "rounds": _open_rounds(project, req, rdir),
            "asks": 0,
        })
        rows[-1]["asks"] = len(rows[-1]["decisions"]) + len(rows[-1]["rounds"])
    return rows


def rounds_of(plans: list[dict]) -> list[dict]:
    return [round_ for plan in plans for round_ in plan.get("rounds") or []]


def decisions_of(plans: list[dict]) -> list[dict]:
    return [decision for plan in plans for decision in plan.get("decisions") or []]


def _iso(epoch: Any) -> str | None:
    if isinstance(epoch, bool) or not isinstance(epoch, (int, float)) or epoch <= 0:
        return None
    return dt.datetime.fromtimestamp(epoch, dt.UTC).isoformat()


def quota_accounts(rows: list[dict]) -> list[dict]:
    """Subscription readings (`bt_quota_live`) as `{id, windows[{name, remaining, limit, resetsAt}]}` accounts."""
    accounts = []
    for row in rows:
        windows = []
        for key, name in _WINDOWS:
            window = (row.get("windows") or {}).get(key)
            used = (window or {}).get("used_percent")
            if isinstance(used, (int, float)) and not isinstance(used, bool):
                windows.append({"name": name, "remaining": max(0.0, 100.0 - used), "limit": 100,
                                "resetsAt": _iso(window.get("resets_at"))})
        accounts.append({"id": row.get("profile"), "provider": row.get("provider"), "status": row.get("status"),
                         "windows": windows, "checkedAt": _iso(row.get("observed_at")), "source": "subscription-usage"})
    return accounts


def quotas_payload() -> dict:
    import bt_quota_live
    return {"accounts": quota_accounts(bt_quota_live.read_all_live()),
            "checkedAt": dt.datetime.now(dt.UTC).isoformat()}


def cached_quota_rows(max_age: float = 900.0) -> list[dict]:
    """The last quota reading on disk, never a fresh network read, so the event poll stays fast."""
    import time
    import bt_quota_live
    try:
        saved = json.loads(bt_quota_live.cache_path().read_text(encoding="utf-8"))
        return saved["rows"] if time.time() - saved["at"] < max_age else []
    except (OSError, ValueError, KeyError, TypeError):
        return []


def history_payload(rows: list[dict], limit: int = 200) -> dict:
    """The command ledger as `{commands: [...]}`, newest first, each with its origin and result."""
    items = [{"id": row["idempotency_key"], "at": row["finished_at"] or row["received_at"],
              "command": row["command"], "target": row["target"], "origin": row["origin"],
              "result": row["code"] or row["status"]} for row in rows]
    items.reverse()
    return {"commands": items[:limit], "nextCursor": ""}


def available_routes(runs: list[dict]) -> list[dict]:
    """Routes a failed or blocked task could be retried on, deduplicated by route id."""
    import bt_remote_commands as commands
    import bt_remote_recovery as recovery
    found: dict[str, dict] = {}
    for run in runs:
        for task in run.get("tasks") or []:
            if task.get("state") not in {"failed", "blocked", "rejected"}:
                continue
            try:
                project, _, rdir = commands._run_target(run["run"])
                for option in recovery.route_options(project, rdir, task["id"]):
                    if option.get("available") and option.get("route_id"):
                        label = f'{option.get("provider")}/{option.get("model")} · {option.get("account")}'
                        found.setdefault(option["route_id"], {"id": option["route_id"], "label": label})
            except Exception:  # noqa: BLE001 - routes are advisory; the snapshot must still load
                continue
    return list(found.values())
