"""Read-only plan status: one data layer for "what is the plan, how hard, who is running it, how far along".

Pure functions returning JSON-serialisable dicts; they never write, lock or create files and open the scheduler
database only through a `mode=ro` URI. Cheap enough to call every second (`fingerprint` first, `plan_status` on change).

    plan_status(project, req_dir) -> {
      project, req_id, title,
      plan:    {plan_id, revision, sha256, status, schema_version, has_contract},
      run:     {authority: scheduler|legacy|none, status, active, updated_at},
      summary: {tasks_total, tasks_done, milestones_total, milestones_done, difficulty},
      milestones: [{id, title, difficulty, difficulty_counts, state, progress: {done, total}, tasks: [
        {id, title, milestone_id, complexity, scope, risk, kind, after, state, attempts, attempt, history, evidence}]}]}
    list_plans(root=None, include_inactive=True) -> [{project, req_id, title, plan_status, run_status, active,
        progress: {done, total}, difficulty, updated_at}]
    fingerprint(root=None) -> str

Vocabularies. Task state: pending|ready|running|verifying|completed|rejected|blocked|cancelled. Milestone state:
pending|running|completed|blocked|cancelled. Difficulty (PLAN.json `complexity`): low < medium < high < extreme; a
milestone has no difficulty of its own in the frozen contract, so it is DERIVED as the highest task complexity (with
per-level counts). Legacy S|M|L declarations map to low|medium|high. An attempt is {id, number, state, provider,
model_requested, model_reported, effort, account, account_ref, started_at, ended_at, cost_usd}; `history` holds up to
10 attempts, oldest first. Anything not recorded is None, never guessed. Scheduler attempts carry their own route
(M2 ledger), duration, last activity, `tokens` ({input, output, total, source}) and `model_reported` (M4) from
`bt_attempt_facts`; a task also carries `route` = the assigned route and its status. `cost_usd` is None unless the
legacy RUN.json log recorded it. Active plans (run status running|waiting|paused) are unlimited.
"""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import bt_attempt_facts as attempt_facts
import bt_core
import bt_plan_adapter as plan_adapter
import bt_run_stores as run_stores
import bt_runstate as rs
import bt_scheduler_adapter as scheduler_

LEVELS = ("low", "medium", "high", "extreme")
ACTIVE = ("running", "waiting", "paused")
INACTIVE_PLAN = ("archived", "cancelled", "superseded")
HISTORY_CAP = 10
_LEGACY_LEVEL = {"S": "low", "M": "medium", "L": "high"}
_LEGACY_TASK = {"todo": "pending", "in_progress": "running", "done": "completed", "blocked": "blocked"}
_SCHEDULER_TASK = {"pending": "pending", "ready": "ready", "active": "running", "recovering": "rejected",
                   "completed": "completed", "blocked": "blocked", "cancelled": "cancelled"}
_LEGACY_RESULT = {"done": "completed", "blocked": "blocked"}
_WATCHED = ("PLAN.json", "PLAN.md", "RUN.json", scheduler_.PROJECTION)


def _iso(epoch: Any) -> str | None:
    if isinstance(epoch, bool) or not isinstance(epoch, (int, float)) or epoch <= 0:
        return None
    return dt.datetime.fromtimestamp(epoch, dt.UTC).isoformat(timespec="seconds")


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return None


def _front(path: Path, key: str) -> str | None:
    try:
        match = re.search(rf"^{key}:\s*(.+?)\s*$", path.read_text(encoding="utf-8")[:2000], re.M)
    except (OSError, UnicodeError):
        return None
    return match.group(1) if match else None


def _title(rdir: Path) -> str | None:
    for name in ("SPEC.md", "PLAN.md"):
        try:
            for line in (rdir / name).read_text(encoding="utf-8").splitlines():
                if line.startswith("# "):
                    return re.sub(r"^(Plan|Spec)\s*—\s*(REQ-\d+\s*—\s*)?", "", line[2:].strip()) or None
        except (OSError, UnicodeError):
            continue
    return None


def _attempt(**fields: Any) -> dict[str, Any]:
    keys = ("id", "number", "state", "provider", "model_requested", "model_reported", "effort", "account",
            "account_ref", "started_at", "ended_at", "cost_usd", "live", "duration_s", "last_activity_at", "tokens",
            "failure", "verdict")
    return {key: fields.get(key) for key in keys}


def _blank_task(tid: str, title: str | None, milestone: str | None) -> dict[str, Any]:
    return {"id": tid, "title": title, "milestone_id": milestone, "complexity": None, "scope": None, "risk": None,
            "kind": None, "after": [], "state": "pending", "attempts": 0, "attempt": None, "history": [],
            "evidence": None, "route": None, "amendments": [], "complexity_original": None, "detail": None}


def _detail(raw: dict) -> dict[str, Any]:
    """What the plan says a task must achieve and how it is checked (PLAN.json): what a reader opens a task for."""
    def strings(key: str) -> list[str]:
        return [str(x) for x in raw.get(key) or [] if isinstance(x, (str, int, float)) and str(x).strip()]
    checks = [{"value": str(v.get("value") or ""), "purpose": str(v.get("purpose") or ""), "category": v.get("category"),
               "type": v.get("type")} for v in raw.get("verification") or [] if isinstance(v, dict)]
    minutes = raw.get("estimated_minutes")
    return {"objective": str(raw.get("objective") or "").strip() or None, "acceptance_criteria": strings("acceptance_criteria"),
            "verification": checks, "expected_paths": strings("expected_paths"), "covers": strings("covers"),
            "shared_resources": strings("shared_resources"), "repository": raw.get("repository"),
            "estimated_minutes": minutes if isinstance(minutes, (int, float)) and not isinstance(minutes, bool) else None,
            "estimate_rationale": str(raw.get("estimate_rationale") or "").strip() or None}


def _contract_structure(data: dict) -> tuple[list[dict], list[dict]]:
    milestones = [{"id": m.get("id"), "title": m.get("title"), "tasks": []}
                  for m in data.get("milestones") or [] if isinstance(m, dict)]
    subplans = {item.get("id"): item.get("title") for item in data.get("subplans") or []
                if isinstance(item, dict) and isinstance(item.get("id"), str)}
    tasks = []
    for raw in data.get("tasks") or []:
        if not isinstance(raw, dict):
            continue
        task = _blank_task(str(raw.get("id")), raw.get("title"), raw.get("milestone_id"))
        task.update({key: raw.get(key) for key in ("complexity", "scope", "risk", "kind")})
        if subplans:
            task["subplan_id"] = raw.get("subplan_id")
            task["subplan_title"] = subplans.get(raw.get("subplan_id"))
        task["after"] = [str(a) for a in raw.get("after") or []]
        task["detail"] = _detail(raw)
        tasks.append(task)
    return milestones, tasks


_STRUCTURE_CACHE: dict[tuple, tuple[list[dict], list[dict]]] = {}
_STRUCTURE_CACHE_MAX = 256


def _markdown_structure(plan_md: Path) -> tuple[list[dict], list[dict]]:
    """The parsed structure of a Markdown plan, memoized by (path, mtime, size): the panel asks for every plan on each
    refresh and a plan file rarely changes. Callers get a copy, since they fill in task state afterwards."""
    try:
        stat = plan_md.stat()
        key = (str(plan_md), stat.st_mtime_ns, stat.st_size)
    except OSError:
        return _parse_markdown_structure(plan_md)
    hit = _STRUCTURE_CACHE.get(key)
    if hit is None:
        if len(_STRUCTURE_CACHE) >= _STRUCTURE_CACHE_MAX:
            _STRUCTURE_CACHE.clear()
        hit = _STRUCTURE_CACHE[key] = _parse_markdown_structure(plan_md)
    return copy.deepcopy(hit)


def _parse_markdown_structure(plan_md: Path) -> tuple[list[dict], list[dict]]:
    parsed = rs.parse_plan(plan_md)
    titles = {m["id"]: m.get("title") for m in rs.milestones(plan_md)}
    tasks = []
    for item in parsed:
        task = _blank_task(item["id"], item.get("title") or item["id"], item.get("milestone"))
        task["after"] = list(item.get("after") or [])
        task["kind"] = item.get("kind")
        task["complexity"] = _LEGACY_LEVEL.get(str(item.get("complexity") or ""))
        task["state"] = "completed" if item.get("done") else "pending"
        tasks.append(task)
    order = list(dict.fromkeys(t["milestone_id"] for t in tasks if t["milestone_id"]))
    return [{"id": mid, "title": titles.get(mid), "tasks": []} for mid in order], tasks


def _legacy_overlay(tasks: dict[str, dict], run: dict) -> None:
    log = [e for e in run.get("log") or [] if isinstance(e, dict)]
    for raw in run.get("tasks") or []:
        task = tasks.get(raw.get("id"))
        if task is None:
            continue
        task["state"] = _LEGACY_TASK.get(raw.get("status"), task["state"])
        task["evidence"] = raw.get("evidence")
        task["attempts"] = raw.get("attempts") if isinstance(raw.get("attempts"), int) else 0
        task["complexity"] = task["complexity"] or _LEGACY_LEVEL.get(str(raw.get("complexity") or "")) or (
            raw.get("complexity") if raw.get("complexity") in LEVELS else None)
        history = []
        for number, entry in enumerate((e for e in log if e.get("task") == raw.get("id")), 1):
            seconds = entry.get("seconds")
            end = _parse_iso(entry.get("at"))
            start = end - dt.timedelta(seconds=seconds) if end and isinstance(seconds, (int, float)) else None
            history.append(_attempt(
                id=f"{raw.get('id')}#{number}", number=number, state=_LEGACY_RESULT.get(entry.get("result"), "rejected"),
                provider=entry.get("agent"), model_requested=entry.get("model"), model_reported=None,
                effort=entry.get("effort"), account=entry.get("profile"), account_ref=None,
                started_at=start.isoformat(timespec="seconds") if start else None,
                ended_at=entry.get("at"), cost_usd=entry.get("cost_usd")))
        task["history"] = history[-HISTORY_CAP:]
        task["attempt"] = history[-1] if history else None
        task["attempts"] = max(task["attempts"], len(history))
        if task["state"] == "pending" and history and history[-1]["state"] == "rejected":
            task["state"] = "rejected"


def _parse_iso(value: Any) -> dt.datetime | None:
    try:
        parsed = dt.datetime.fromisoformat(str(value))
    except ValueError:
        return None
    return parsed


def _scheduler_overlay(tasks: dict[str, dict], projection: dict, facts: dict[str, list[dict]]) -> None:
    """Attempts come from the per-attempt read model (`bt_attempt_facts`): each carries the route it really ran with.
    The projection's route is the task's current/assigned one; it only fills the latest attempt when the M2 ledger
    could not resolve that attempt's own route."""
    for raw in projection.get("tasks") or []:
        task = tasks.get(raw.get("id"))
        if task is None:
            continue
        records = facts.get(raw["id"], [])
        task["state"] = _SCHEDULER_TASK.get(raw.get("scheduler_state"), "pending")
        task["attempts"] = raw.get("attempts") if isinstance(raw.get("attempts"), int) else len(records)
        for key in ("attempts_used", "max_attempts", "retries_remaining"):
            value = raw.get(key)
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                task[key] = value
        if isinstance(raw.get("retry_exhausted"), bool):
            task["retry_exhausted"] = raw["retry_exhausted"]
        if isinstance(raw.get("reason"), str):
            task["reason"] = raw["reason"]
        task["evidence"] = raw.get("evidence") or None
        task["complexity"] = task["complexity"] or (raw.get("complexity") if raw.get("complexity") in LEVELS else None)
        route = {"provider": raw.get("provider") or None, "model_requested": raw.get("model") or None,
                 "effort": raw.get("effort") or None, "account": raw.get("profile") or None,
                 "account_ref": raw.get("account_ref") or None}
        task["route"] = {"status": raw.get("route_status") or "unplanned", "reason": raw.get("route_reason") or None,
                         "selection_reason": raw.get("selection_reason") or None, **route}
        history = []
        for r in records[-HISTORY_CAP:]:
            own = r["route"]
            history.append(_attempt(
                id=r["attempt"], number=r["number"], state=r["state"], provider=own["provider"],
                model_requested=own["model"], model_reported=r["model_reported"], effort=own["effort"],
                account=own["profile"], account_ref=own["account_ref"], started_at=r["started_at"],
                ended_at=r["ended_at"], cost_usd=r["cost_usd"], live=r["live"], duration_s=r["duration_s"],
                last_activity_at=r["last_activity_at"], tokens=r["tokens"], failure=r["failure"] or None,
                verdict=r["verdict"]))
        if not history and task["attempts"]:
            history = [_attempt(id=None, number=task["attempts"], state=None)]
        if history:
            if not history[-1]["model_requested"]:
                history[-1].update({k: v for k, v in route.items() if history[-1].get(k) is None})
            task["attempt"] = history[-1]
            if task["state"] == "running" and history[-1]["state"] == "verifying":
                task["state"] = "verifying"
        task["history"] = history


def _milestone_state(tasks: list[dict]) -> str:
    states = {t["state"] for t in tasks}
    if tasks and states == {"completed"}:
        return "completed"
    if tasks and states == {"cancelled"}:
        return "cancelled"
    if "blocked" in states:
        return "blocked"
    if states & {"running", "verifying", "rejected"}:
        return "running"
    return "pending"


def _highest(levels: list[str | None]) -> str | None:
    known = [LEVELS.index(level) for level in levels if level in LEVELS]
    return LEVELS[max(known)] if known else None


def _run_block(rdir: Path, authority: str, run: dict | None) -> dict[str, Any]:
    status = run.get("status") if isinstance(run, dict) else None
    status = status if isinstance(status, str) else None
    if authority == "scheduler":
        stamp = (run or {}).get("heartbeat_at")
        path = rdir / scheduler_.PROJECTION
    else:
        beat = (run or {}).get("heartbeat")
        stamp = beat.get("at") if isinstance(beat, dict) else None
        path = rdir / "RUN.json"
    if not stamp:
        stamp = _mtime_iso(path)
    return {"authority": authority, "status": status, "active": status in ACTIVE, "updated_at": stamp}


def _mtime_iso(path: Path) -> str | None:
    try:
        return _iso(path.stat().st_mtime)
    except OSError:
        return None


def plan_status(project: str, req_dir: Path) -> dict[str, Any]:
    """Full status of one requirement's plan; see the module docstring for the shape."""
    rdir = Path(req_dir)
    contract = _read_json(rdir / "PLAN.json")
    contract = contract if isinstance(contract, dict) else None
    milestones, task_list = _contract_structure(contract) if contract else _markdown_structure(rdir / "PLAN.md")
    authority = scheduler_.authority(rdir)
    run = scheduler_.read_projection(rdir) if authority == "scheduler" else (
        _read_json(rdir / "RUN.json") if authority == "legacy" else None)
    run = run if isinstance(run, dict) else None
    if not task_list and run:
        task_list = [_blank_task(str(t.get("id")), t.get("title"), t.get("milestone")) for t in run.get("tasks") or []
                     if isinstance(t, dict)]
        milestones = [{"id": mid, "title": None, "tasks": []}
                      for mid in dict.fromkeys(t["milestone_id"] for t in task_list if t["milestone_id"])]
    by_id = {t["id"]: t for t in task_list}
    if run and authority == "scheduler":
        _scheduler_overlay(by_id, run, attempt_facts.attempt_facts(rdir))
    elif run:
        _legacy_overlay(by_id, run)
    plan_ref = (run or {}).get("plan_ref") if authority == "scheduler" else None
    evolution = _evolution(rdir, task_list, (contract or {}).get("revision", (plan_ref or {}).get("revision")))
    known = {m["id"] for m in milestones}
    for task in task_list:
        if task["milestone_id"] not in known:
            known.add(task["milestone_id"])
            milestones.append({"id": task["milestone_id"], "title": None, "tasks": []})
    for milestone in milestones:
        milestone["tasks"] = [t for t in task_list if t["milestone_id"] == milestone["id"]]
        counts = {level: sum(1 for t in milestone["tasks"] if t["complexity"] == level) for level in LEVELS}
        milestone["difficulty"] = _highest([t["complexity"] for t in milestone["tasks"]])
        milestone["difficulty_counts"] = counts
        milestone["state"] = _milestone_state(milestone["tasks"])
        milestone["progress"] = {"done": sum(t["state"] == "completed" for t in milestone["tasks"]),
                                 "total": len(milestone["tasks"])}
    plan_md = rdir / "PLAN.md"
    ref = (run or {}).get("plan_ref") if authority == "scheduler" else None
    ref = ref if isinstance(ref, dict) else {}
    digest = ref.get("sha256")
    if digest is None and contract:
        digest = _sha256(rdir / "PLAN.json")
    return {
        "project": project, "req_id": re.match(r"REQ-\d+", rdir.name).group(0) if re.match(r"REQ-\d+", rdir.name)
        else rdir.name, "title": _title(rdir),
        "plan": {"plan_id": (contract or {}).get("plan_id") or ref.get("plan_id"),
                 "revision": (contract or {}).get("revision", ref.get("revision")), "sha256": digest,
                 "status": _front(plan_md, "status") or _front(rdir / "SPEC.md", "status"),
                 "schema_version": (contract or {}).get("schema_version"), "has_contract": contract is not None},
        "run": _run_block(rdir, authority, run),
        "summary": {"tasks_total": len(task_list), "tasks_done": sum(t["state"] == "completed" for t in task_list),
                    "milestones_total": len(milestones),
                    "milestones_done": sum(m["state"] == "completed" for m in milestones),
                    "difficulty": _highest([t["complexity"] for t in task_list])},
        "milestones": milestones, "evolution": evolution}


def _evolution(rdir: Path, tasks: list[dict], revision: Any) -> dict[str, Any]:
    """Amendments per task (and the classification they put in force) plus the plan's timeline of frozen revisions and
    amendments. The amended value replaces `complexity` in the task row; `complexity_original` keeps the plan's own."""
    every = plan_adapter.amendments(rdir)                 # the timeline keeps the amendments of earlier revisions too
    records = [r for r in every if r["plan_ref"].get("revision") == revision]
    overrides = plan_adapter.effective_overrides(rdir) if records else {}
    for task in tasks:
        mine = [r for r in records if r["task"] == task["id"]]
        task["amendments"] = mine
        task["complexity_original"] = task["complexity"] if mine else None
        for name in ("complexity", "scope", "risk"):
            if name in overrides.get(task["id"], {}):
                task[name] = overrides[task["id"]][name]
    timeline = [{"at": r.get("frozen_at"), "kind": "revision", "revision": r["revision"], "source": r.get("source")}
                for r in plan_adapter.revisions(rdir)]
    timeline += [{"at": r["at"], "kind": "amendment", "task": r["task"], "field": r["field"], "from": r["from"],
                  "to": r["to"], "by": r["by"], "proposed_by": r["proposed_by"], "revision": r["plan_ref"].get("revision")}
                 for r in every]
    timeline.sort(key=lambda item: str(item["at"] or ""))
    return {"amendments": len(every), "timeline": timeline}


def _sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _requirement_dirs(root: Path) -> list[tuple[str, Path]]:
    found = []
    try:
        projects = sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith("."))
    except OSError:
        return []
    for pdir in projects:
        for rdir in sorted(pdir.glob("requirements/REQ-*")):
            if rdir.is_dir() and ((rdir / "PLAN.md").exists() or (rdir / "PLAN.json").exists()):
                found.append((pdir.name, rdir))
    return found


def _root(root: Path | None) -> Path:
    return Path(root if root is not None else bt_core.ROOT).resolve()


def list_plans(root: Path | None = None, include_inactive: bool = True) -> list[dict[str, Any]]:
    """One light row per requirement that has a plan; `include_inactive=False` drops archived/cancelled plans."""
    rows = []
    for project, rdir in _requirement_dirs(_root(root)):
        status = plan_status(project, rdir)
        if not include_inactive and status["plan"]["status"] in INACTIVE_PLAN:
            continue
        summary = status["summary"]
        rows.append({"project": project, "req_id": status["req_id"], "title": status["title"],
                     "plan_status": status["plan"]["status"], "run_status": status["run"]["status"],
                     "active": status["run"]["active"],
                     "progress": {"done": summary["tasks_done"], "total": summary["tasks_total"]},
                     "difficulty": summary["difficulty"], "updated_at": status["run"]["updated_at"]
                     or _mtime_iso(rdir / "PLAN.md"), "asks": _asks(rdir)})
    return rows


def _asks(rdir: Path) -> int:
    """How many things the plan waits on from its owner: open question rounds and decision requests (D-020)."""
    n = 0
    for f in sorted((rdir / "rounds").glob("round-*.json")):
        try:
            n += json.loads(f.read_text(encoding="utf-8")).get("status") == "open"
        except (OSError, ValueError, AttributeError):
            continue
    if (rdir / scheduler_.PROJECTION).is_file():
        try:
            import bt_scheduler_decisions
            n += len(bt_scheduler_decisions.open_requests(rdir))
        except Exception:  # noqa: BLE001 - a run whose state cannot be read asks nothing here
            pass
    return n


def fingerprint(root: Path | None = None) -> str:
    """Change token from (mtime_ns, size) of each plan/run file, with no content parsing and no file creation."""
    digest = hashlib.sha256()
    for project, rdir in _requirement_dirs(_root(root)):
        paths = [rdir / name for name in _WATCHED]
        db = scheduler_.run_db_path(rdir)
        paths += [db, db.with_name(db.name + "-wal")]
        for store in (run_stores.paths(rdir).get(name) for name in ("m2", "m4", "m5", "m6")):
            if store is not None:       # the module stores change the attempt facts (tokens, activity) too
                paths += [store, store.with_name(store.name + "-wal")]
        for path in paths:
            try:
                stat = path.stat()
                mark = f"{stat.st_mtime_ns}:{stat.st_size}"
            except OSError:
                mark = "-"
            digest.update(f"{project}/{rdir.name}/{path.name}={mark}\n".encode())
    return digest.hexdigest()
