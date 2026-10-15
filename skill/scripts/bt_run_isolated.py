"""Glue between marathon task state and durable same-repo worktree integration."""
from __future__ import annotations

import json
import shlex
import secrets
import subprocess
from pathlib import Path

import bt_runsettle
import bt_runstate as rs
import bt_worktree
from bt_core import ROOT, STATE, find_req, ws
from bt_integration_lock import IntegrationLock


class IsolationError(RuntimeError):
    """Worktree isolation could not start safely."""


def _repo(project: str, role: str) -> Path:
    repos = ws.repos(ROOT, project)
    if role not in repos:
        raise IsolationError(f"Unknown repo role '{role}' (registered: {', '.join(repos) or 'none'}).")
    repo = Path(repos[role]).resolve()
    try:
        result = subprocess.run(["git", "rev-parse", "--verify", "HEAD^{commit}"], cwd=repo,
                                capture_output=True, text=True, check=False)
    except OSError as exc:
        raise IsolationError(f"Isolation requires Git to be installed and available: {exc}") from exc
    if result.returncode:
        raise IsolationError(f"Isolation requires Git and a committed HEAD in repo '{role}': "
                             f"{(result.stderr or result.stdout).strip()}")
    return repo


def _root(project: str, req: str) -> Path:
    path = STATE / "runs" / f"{project}-{req}" / "worktrees"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _integration_key(role: str) -> str:
    return f"__integration__:{role}"


def integration_for(state: dict, role: str | None) -> dict | None:
    """Find the integration allocation for a repo role, including legacy state."""
    worktrees = state.get("worktrees") or {}
    if role:
        current = worktrees.get(_integration_key(role))
        if current:
            return current
    legacy = worktrees.get("__integration__")
    roles = {task.get("repo") for task in state.get("tasks", []) if task.get("repo")}
    if legacy and (not role or legacy.get("repo_role") == role or
                   (legacy.get("repo_role") is None and len(roles) == 1 and role in roles)):
        return legacy
    return None


def _repo_refs(repo: Path) -> set[str]:
    result = subprocess.run(["git", "for-each-ref", "--format=%(refname)", "refs/heads", "refs/tags"],
                            cwd=repo, capture_output=True, text=True, check=True)
    return {line for line in result.stdout.splitlines() if line}


def _audit_warning(rdir: Path, label: str, allocation: dict, reason: str) -> None:
    path = allocation.get("worktree", "<unknown>")
    warning = f"audit_cleanup_failed: {reason}; review worktree kept for owner at {path}"
    allocation["state"] = "needs_attention"
    allocation["last_error"] = warning
    def record(saved: dict) -> None:
        saved.setdefault("worktrees", {})[label] = allocation
        if not any(entry.get("warning") == warning for entry in saved.get("log", [])):
            saved.setdefault("log", []).append({"at": rs.now_iso(), "session": saved.get("sessions", 0),
                "task": label, "result": "plan_warning", "warning": warning, "summary": warning, "seconds": 0})
    rs.update(rdir, record)


def prepare(project: str, state: dict, rdir: Path, units: list[list[dict]]) -> dict[str, dict]:
    """Allocate and durably record each unit and the requirement integration branch."""
    allocations = state.get("worktrees") or {}
    out = {}
    for unit in units:
        label = rs.unit_label(unit)
        if any(task.get("synthetic") or not task.get("repo") for task in unit):
            continue
        current = allocations.get(label)
        if current and current.get("state") not in ("accepted", "blocked"):
            allocation = current
        else:
            roles = {task.get("repo") for task in unit}
            if len(roles) != 1 or None in roles:
                raise IsolationError(f"Isolation requires one registered repo role for unit {label}.")
            repo = _repo(project, next(iter(roles)))
            sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True,
                                 check=True).stdout.strip()
            allocation = bt_worktree.allocate(repo, label, sha, _root(project, state["req"]))
            allocation.update(task_ids=[task["id"] for task in unit],
                              allowed_paths=sorted({path for task in unit for path in (task.get("files") or [])}),
                              resources=sorted({tag for task in unit for tag in (task.get("resources") or [])}),
                              repo_role=next(iter(roles)))
            rs.update(rdir, lambda saved: saved.setdefault("worktrees", {}).update({label: allocation}))
        for task in unit:
            task["_worktree_branch"] = allocation["branch"]
        out[label] = allocation
    return out


def ensure_integration(project: str, state: dict, rdir: Path, repo: Path) -> dict:
    """Create the shared integration worktree once, before worker sessions start."""
    role = next((task.get("repo") for task in state.get("tasks", [])
                 if task.get("repo") and _repo(project, task["repo"]) == repo.resolve()), None)
    if role is None:
        raise IsolationError(f"Cannot identify repository role for integration repo {repo}.")
    key = _integration_key(role)
    current = integration_for(state, role)
    if current and Path(current["worktree"]).is_dir() and Path(current["repo"]).resolve() == repo.resolve():
        return current
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True,
                         check=True).stdout.strip()
    allocation = bt_worktree.allocate(repo, f"{state['req']}-integration", sha, _root(project, state["req"]))
    allocation["integration"] = True
    allocation["repo_role"] = role
    rs.update(rdir, lambda saved: saved.setdefault("worktrees", {}).__setitem__(key, allocation))
    return allocation


def prepare_audit(project: str, state: dict, rdir: Path, task: dict | None) -> dict:
    """Record and create a detached disposable worktree for an audit or final review."""
    label = task["id"] if task else "FINAL"
    current = (rs.load(rdir).get("worktrees") or {}).get(label)
    if current and Path(current["worktree"]).is_dir():
        return current
    related = [rs.get_task(state, task_id) for task_id in (task or {}).get("after", [])]
    related = [item for item in related if item]
    if not related:
        related = [item for item in state.get("tasks", []) if item.get("repo")]
    role = next((item.get("repo") for item in related if item.get("repo")), None)
    if role is None:
        raise IsolationError(f"Cannot find a registered repository for isolated review {label}.")
    repo = _repo(project, role)
    integration = integration_for(rs.load(rdir), role)
    source = Path(integration["worktree"]) if integration and Path(integration["worktree"]).is_dir() else repo
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=source, capture_output=True, text=True,
                         check=True).stdout.strip()
    root = _root(project, state["req"])
    path = root / f"{label}-{secrets.token_hex(4)}"
    allocation = {"task_id": label, "worktree": str(path), "repo": str(repo), "repo_role": role,
                  "base_sha": sha,
                  "journal": str(root / "integration.jsonl"), "state": "audit_allocating", "audit": True,
                  "allowed_roots": [str(root)], "refs_before": sorted(_repo_refs(repo))}
    rs.update(rdir, lambda saved: saved.setdefault("worktrees", {}).__setitem__(label, allocation))
    path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(["git", "worktree", "add", "--detach", str(path), sha], cwd=repo,
                            capture_output=True, text=True, check=False)
    if result.returncode:
        raise bt_worktree.WorktreeError(f"git worktree add --detach failed: {(result.stderr or result.stdout).strip()}")
    allocation["state"] = "audit_running"
    rs.update(rdir, lambda saved: saved.setdefault("worktrees", {}).__setitem__(label, allocation))
    return allocation


def finish_audit(rdir: Path, label: str) -> str | None:
    """Remove a clean review worktree or preserve changed review work on an isolated branch."""
    state = rs.load(rdir) or {}
    allocation = (state.get("worktrees") or {}).get(label)
    if not allocation or not allocation.get("audit"):
        return None
    repo, worktree = Path(allocation["repo"]), Path(allocation["worktree"])
    try:
        if not worktree.is_dir():
            subprocess.run(["git", "worktree", "prune"], cwd=repo, capture_output=True, text=True, check=True)
            rs.update(rdir, lambda saved: saved.get("worktrees", {}).pop(label, None))
            return None
        refs_after = _repo_refs(repo)
        new_refs = refs_after - set(allocation.get("refs_before", [])) if "refs_before" in allocation else set()
        for ref in sorted(new_refs):
            warning = f"audit_modified_tree: review {label} created shared ref {ref}"
            def record_ref(saved: dict) -> None:
                if not any(entry.get("warning") == warning for entry in saved.get("log", [])):
                    saved.setdefault("log", []).append({"at": rs.now_iso(), "session": saved.get("sessions", 0),
                        "task": label, "result": "plan_warning", "warning": warning, "summary": warning,
                        "seconds": 0})
            rs.update(rdir, record_ref)
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=worktree, capture_output=True, text=True,
                              check=True).stdout.strip()
        status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=worktree,
                                capture_output=True, text=True, check=True).stdout
        if not status and head == allocation["base_sha"]:
            subprocess.run(["git", "worktree", "remove", str(worktree)], cwd=repo, capture_output=True, text=True,
                           check=True)
            rs.update(rdir, lambda saved: saved.get("worktrees", {}).pop(label, None))
            return None
        branch = allocation.get("preserve_branch")
        if not branch:
            branches = subprocess.run(["git", "branch", "--list", f"wt/{label}-audit-changes-*"], cwd=repo,
                                      capture_output=True, text=True, check=True).stdout.splitlines()
            used = {line.strip().removeprefix("* ") for line in branches}
            index = 1
            branch = f"wt/{label}-audit-changes-{index}"
            while branch in used:
                index += 1
                branch = f"wt/{label}-audit-changes-{index}"
            allocation["preserve_branch"] = branch
            rs.update(rdir, lambda saved: saved.setdefault("worktrees", {}).__setitem__(label, allocation))
        if status:
            subprocess.run(["git", "add", "-A"], cwd=worktree, check=True)
            staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=worktree, check=False)
            if staged.returncode == 1:
                subprocess.run(["git", "-c", "user.name=Bitacora Audit", "-c", "user.email=audit@localhost",
                                "commit", "-m", f"audit changes: {label}"], cwd=worktree, capture_output=True,
                                text=True, check=True)
        preserved_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=worktree, capture_output=True,
                                        text=True, check=True).stdout.strip()
        existing = subprocess.run(["git", "rev-parse", "--verify", f"refs/heads/{branch}"], cwd=repo,
                                  capture_output=True, text=True, check=False)
        if existing.returncode == 0 and existing.stdout.strip() != preserved_head:
            raise bt_worktree.WorktreeError(f"Preservation branch {branch} points to unexpected commit")
        if existing.returncode:
            subprocess.run(["git", "branch", branch, preserved_head], cwd=repo, capture_output=True, text=True,
                           check=True)
        warning = f"audit_modified_tree: review {label} changed its disposable tree; preserved on branch {branch}"
        def record(saved: dict) -> None:
            if not any(entry.get("warning") == warning for entry in saved.get("log", [])):
                saved.setdefault("log", []).append({"at": rs.now_iso(), "session": saved.get("sessions", 0),
                    "task": label, "result": "plan_warning", "warning": warning, "summary": warning,
                    "seconds": 0})
        rs.update(rdir, record)
        subprocess.run(["git", "worktree", "remove", str(worktree)], cwd=repo, capture_output=True, text=True,
                       check=True)
        rs.update(rdir, lambda saved: saved.get("worktrees", {}).pop(label, None))
        return branch
    except (bt_worktree.WorktreeError, subprocess.CalledProcessError, OSError) as exc:
        _audit_warning(rdir, label, allocation, str(exc))
        return None


def _integration(project: str, state: dict, rdir: Path, repo: Path) -> dict:
    return ensure_integration(project, state, rdir, repo)


def _verify_cmd(tasks: list[dict]) -> str:
    commands = list(dict.fromkeys(task["verify"] for task in tasks if task.get("verify")))
    return " && ".join(f"({command})" for command in commands) or "true"


def _mark_integration(project: str, rdir: Path, allocation: dict, outcome: str, reason: str = "") -> None:
    ids = allocation.get("task_ids") or [allocation["task_id"]]
    def update(state: dict) -> None:
        worktrees = state.setdefault("worktrees", {})
        saved = worktrees.get(rs.unit_label([rs.get_task(state, ids[0])])) or worktrees.get(allocation.get("task_id"))
        if saved:
            saved.update(allocation)
        for task_id in ids:
            task = rs.get_task(state, task_id)
            if not task:
                continue
            if outcome == "accepted":
                task.update(status="done", last_error=None)
            else:
                error = f"integration: {reason}"[:1000]
                stuck = bt_runsettle._fail_attempt(task, error, state["limits"]["max_attempts"])
                if stuck:
                    task.update(status="blocked", last_error=error)
                else:
                    task.update(status="todo", last_error=error)
    state = rs.update(rdir, update)
    if outcome == "accepted":
        from bt_runtask import tick_plan
        for task_id in ids:
            task = rs.get_task(state, task_id)
            tick_plan(rdir, task_id, f"{task_id} done (isolated integration) — {task.get('evidence') or 'combined verify passed'}")


def block_integration(project: str, rdir: Path, allocation: dict, reason: str) -> None:
    """Settle a worker task as blocked when Git cannot safely integrate its candidate."""
    allocation["state"] = "blocked"
    allocation["last_error"] = f"integration: {reason}"
    _mark_integration(project, rdir, allocation, "blocked", reason)
    rs.update(rdir, lambda saved: saved.setdefault("worktrees", {}).__setitem__(allocation["task_id"], allocation))


def _allocation_tasks(state: dict, allocation: dict) -> list[dict]:
    return [rs.get_task(state, task_id) for task_id in allocation.get("task_ids", []) if rs.get_task(state, task_id)]


def _overall(results: dict[str, str]) -> str:
    values = list(results.values())
    if all(value == "done" for value in values):
        return "done"
    for failed in ("usage_limit", "limit_streak", "timeout", "verify_failed", "failed", "blocked", "escalated",
                   "integration_failed"):
        if failed in values:
            return failed if not any(value == "done" for value in values) else "partial"
    return values[0] if values else "failed"


def _integrate_one(project: str, rdir: Path, state: dict, allocation: dict,
                   lock: IntegrationLock | None = None, lock_held: bool = False) -> str:
    unit_tasks = _allocation_tasks(state, allocation)
    accepted_tasks = []
    allocation_repo = Path(allocation.get("repo", "")).resolve() if allocation.get("repo") else None
    for previous in (state.get("worktrees") or {}).values():
        if previous.get("state") == "accepted":
            previous_repo = Path(previous.get("repo", "")).resolve() if previous.get("repo") else None
            if not allocation_repo or previous_repo == allocation_repo:
                accepted_tasks.extend(_allocation_tasks(state, previous))
    command = _verify_cmd([*accepted_tasks, *unit_tasks])
    try:
        repo = Path(allocation["repo"])
        integration = _integration(project, state, rdir, repo)
        result = bt_worktree.recover([{"allocation": allocation, "sha": allocation["candidate_sha"]}],
                                     integration["worktree"], command,
                                     lock or IntegrationLock(Path(allocation["journal"]).parent),
                                     lock_held=lock_held)
    except bt_worktree.WorktreeError as exc:
        reason = str(exc)
        block_integration(project, rdir, allocation, reason)
        return "blocked"
    outcome = result.get(allocation["task_id"], "blocked")
    if outcome == "accepted":
        allocation["state"] = "accepted"
        _mark_integration(project, rdir, allocation, "accepted")
        bt_worktree.cleanup(allocation)
        allocation["cleaned"] = True
        rs.update(rdir, lambda saved: saved["worktrees"].update({allocation["task_id"]: allocation}))
        return "accepted"
    rows = []
    journal = Path(allocation["journal"])
    if journal.exists():
        rows = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines() if line]
    reason = next((row.get("reason", "candidate was rejected") for row in reversed(rows)
                   if row.get("task_id") == allocation["task_id"] and row.get("stage") == "blocked"),
                  "candidate was rejected")
    allocation["state"] = "blocked"
    allocation["last_error"] = f"integration: {reason}"
    _mark_integration(project, rdir, allocation, "blocked", reason)
    rs.update(rdir, lambda saved: saved["worktrees"].update({allocation["task_id"]: allocation}))
    return "blocked"


def settle_unit(project: str, rdir: Path, unit: list[dict], allocation: dict,
                lock: IntegrationLock | None = None, lock_held: bool = False) -> dict[str, str]:
    """Commit a verified session candidate, then integrate it before reporting task completion."""
    worktree = Path(allocation["worktree"])
    results = {task["id"]: ("done" if rs.get_task(rs.load(rdir), task["id"])["status"] == "integration_pending"
                            else "failed") for task in unit}
    if not all(value == "done" for value in results.values()):
        return results
    if not allocation.get("allowed_paths"):
        changed = subprocess.run(["git", "diff", "--name-only", "-z", allocation["base_sha"]],
                                 cwd=allocation["worktree"], capture_output=True, text=True, check=True).stdout
        untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "-z"],
                                   cwd=allocation["worktree"], capture_output=True, text=True, check=True).stdout
        allocation["allowed_paths"] = sorted(set(changed.split("\0") + untracked.split("\0")) - {""})
        if not allocation["allowed_paths"]:
            allocation["allowed_paths"] = ["__no_changes__"]
    if not allocation.get("candidate_sha"):
        try:
            allocation["candidate_sha"] = bt_worktree.candidate(allocation)
        except bt_worktree.WorktreeError as exc:
            block_integration(project, rdir, allocation, str(exc))
            return {task_id: "integration_failed" for task_id in results}
        allocation["state"] = "candidate"
        rs.update(rdir, lambda saved: saved.setdefault("worktrees", {}).__setitem__(allocation["task_id"], allocation))
    outcome = _integrate_one(project, rdir, rs.load(rdir), allocation, lock, lock_held)
    return {task_id: "done" if outcome == "accepted" else "integration_failed" for task_id in results}


def settle_batch(project: str, rdir: Path, outcomes: list[tuple], allocations: dict[str, dict]) -> list[tuple]:
    """Commit and integrate batch candidates serially under one integration lease."""
    pending = [(unit, allocations[rs.unit_label(unit)]) for _, _, _, _, _, unit in outcomes
               if rs.unit_label(unit) in allocations and not allocations[rs.unit_label(unit)].get("audit")]
    if pending:
        lock = IntegrationLock(Path(pending[0][1]["journal"]).parent)
        with lock.acquire():
            for unit, allocation in pending:
                settle_unit(project, rdir, unit, allocation, lock=lock, lock_held=True)
    state = rs.load(rdir)
    settled = []
    for label, number, info, result, results, unit in outcomes:
        allocation = allocations.get(label)
        if allocation and not allocation.get("audit") and all(value == "done" for value in results.values()):
            results = {task["id"]: ("done" if rs.get_task(state, task["id"])["status"] == "done"
                                     else "integration_failed") for task in unit}
            result = results[unit[0]["id"]] if len(unit) == 1 else _overall(results)
        settled.append((label, number, info, result, results, unit))
    return settled


def recover_recorded(project: str, rdir: Path) -> None:
    """Finish journaled candidates before the scheduler can start new tasks."""
    state = rs.load(rdir) or {}
    allocations = state.get("worktrees") or {}
    for label, allocation in list(allocations.items()):
        if allocation.get("audit"):
            try:
                finish_audit(rdir, label)
            except (OSError, subprocess.SubprocessError, bt_worktree.WorktreeError) as exc:
                warning = f"audit recovery for {label} needs inspection: {exc}"
                rs.update(rdir, lambda saved: saved.setdefault("log", []).append({"at": rs.now_iso(),
                    "session": saved.get("sessions", 0), "task": label, "result": "plan_warning",
                    "warning": warning, "summary": warning, "seconds": 0}))
    state = rs.load(rdir) or {}
    allocations = state.get("worktrees") or {}
    for label, allocation in list(allocations.items()):
        if label == "__integration__" or label.startswith("__integration__:") or allocation.get("state") in ("accepted", "blocked"):
            continue
        tasks = _allocation_tasks(state, allocation)
        pending = [task for task in tasks if task.get("status") == "integration_pending"]
        if not pending:
            continue
        if not allocation.get("candidate_sha"):
            try:
                allocation["candidate_sha"] = bt_worktree.candidate(allocation)
            except bt_worktree.WorktreeError as exc:
                allocation["state"] = "needs_attention"
                allocation["last_error"] = str(exc)
                rs.update(rdir, lambda saved: saved.setdefault("worktrees", {}).__setitem__(label, allocation))
                warning = f"worktree recovery for {label} needs attention: {exc}"
                rs.update(rdir, lambda saved: saved.setdefault("log", []).append({"at": rs.now_iso(),
                    "session": saved.get("sessions", 0), "task": label, "result": "plan_warning",
                    "warning": warning, "summary": warning, "seconds": 0}))
                continue
            allocation["state"] = "candidate"
            rs.update(rdir, lambda saved: saved["worktrees"].update({label: allocation}))
        _integrate_one(project, rdir, rs.load(rdir), allocation)

