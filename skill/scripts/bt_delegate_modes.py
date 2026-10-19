"""Opt-in retries, isolated worktrees, and recovery for one-task delegations."""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

import bt_agents
import bt_delegate as delegate
import bt_runstate
import bt_worktree


def _git(cwd: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, encoding="utf-8", check=False)
    if check and result.returncode:
        raise SystemExit((result.stderr or result.stdout).strip() or "git command failed")
    return result.stdout.strip()


def _route(order: dict, tier: int, avoid: set[str]) -> dict:
    pool = bt_agents.pool_for(order["project"], bt_agents._config("routing.pool", []) or None)
    if not pool:
        raise SystemExit(f"No account may run '{order['project']}'. Check: bitacora.py agents")
    try:
        return bt_agents.route(order["project"], {"pool": pool, "model": order.get("requested_model"), "model_pinned": bool(order.get("requested_model")), "role": order.get("role")}, tier, order.get("kind") or "implement", avoid,
                                allow_explore=False, effort=order.get("requested_effort"),
                                role=order.get("role"), complexity=order.get("complexity"))
    except bt_agents.NoRoute as exc:
        raise SystemExit(f"Every account is waiting for a usage-limit reset (earliest {exc.until}).") from exc


def _error(outcome: dict) -> str:
    verify = outcome.get("verify") or {}
    return str(verify.get("tail") or outcome.get("summary") or outcome.get("status") or "attempt failed")[:600]


def _setup_worktree(order: dict, d: Path) -> dict:
    workdir = Path(order["workdir"]).resolve()
    repo = _git(workdir, "rev-parse", "--show-toplevel", check=False)
    if not repo:
        raise SystemExit(f"--worktree requires a working directory inside a git repository: {workdir}")
    repo_path = Path(repo)
    base = _git(repo_path, "rev-parse", "HEAD")
    allocation_path = d / "WORKTREE.json"
    if allocation_path.exists():
        return json.loads(allocation_path.read_text(encoding="utf-8"))
    root = delegate.STATE / "delegations-worktrees" / order["id"]
    allocation = bt_worktree.allocate(repo_path, order["id"], base, root)
    allocation["allowed_paths"] = order.get("allow") or []
    allocation["allow_all"] = not bool(order.get("allow"))
    allocation_path.write_text(json.dumps(allocation, indent=2) + "\n", encoding="utf-8")
    order["caller_workdir"] = order["workdir"]
    order["workdir"] = allocation["worktree"]
    (d / "TASK.json").write_text(json.dumps(order, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return allocation


def _worktree_result(order: dict, allocation: dict, outcome: dict) -> dict:
    workdir = Path(allocation["worktree"])
    try:
        scope = bt_worktree.check_scope(allocation, allocation.get("allowed_paths"))
        scope_error = None
    except bt_worktree.WorktreeError as exc:
        scope, scope_error = {"status": "blocked"}, str(exc)
    candidate = bt_worktree.candidate(allocation)
    stat = _git(workdir, "diff", "--stat", allocation["base_sha"], candidate, check=False)
    allocation.update(candidate_sha=candidate, diff_stat=stat)
    allocation["scope"] = scope
    allocation["scope_error"] = scope_error
    Path(delegate.path_of(order["id"]) / "WORKTREE.json").write_text(
        json.dumps(allocation, indent=2) + "\n", encoding="utf-8")
    outcome.update({"branch": allocation["branch"], "worktree": str(workdir), "base_sha": allocation["base_sha"],
                    "candidate_sha": candidate, "diff_stat": stat,
                    "merge_hint": f"git merge {allocation['branch']} (after reviewing candidate {candidate[:12]})"})
    if scope_error:
        outcome["status"] = "blocked"
        outcome["scope_error"] = scope_error
    elif scope.get("status") == "serialize":
        outcome["scope"] = scope
    return outcome


def execute(did: str, agent_cmd: str | None, retries: int = 0, worktree: bool = False,
            force_enhanced: bool = False) -> dict:
    """Run opted-in attempts; the zero-retry, non-worktree path remains the legacy executor."""
    if retries == 0 and not worktree and not force_enhanced:
        return delegate.execute(did, agent_cmd)
    if retries < 0 or retries > 3:
        raise SystemExit("--retries must be between 0 and 3")
    d = delegate.path_of(did)
    order = json.loads((d / "TASK.json").read_text(encoding="utf-8"))
    retries = max(retries, int(order.get("retries", 0)))
    worktree = worktree or bool(order.get("worktree_mode"))
    order["retries"], order["worktree_mode"] = retries, worktree
    allocation = _setup_worktree(order, d) if worktree else None
    delegate._claim(d, did)
    history = list(order.get("attempt_history") or [])
    errors = [str(row.get("error") or "") for row in history]
    route_avoid: set[str] = ({str(history[-1].get("provider"))} if history and
                             history[-1].get("provider") and history[-1].get("result") in
                             ("failed", "verify_failed", "timeout") else set())
    outcome: dict = {}
    for attempt in range(len(history) + 1, retries + 2):
        order["attempt"] = attempt
        if attempt > 1:
            order["tier"] = min(int(order.get("tier") or 0) + 1, bt_agents.TOP)
            if order.get("auto"):
                route = _route(order, order["tier"], route_avoid)
                order.update(profile=route.get("profile"), agent=route["agent"], model=route.get("model"),
                             effort=route.get("effort"), routed=route.get("why"))
            order["previous_attempt"] = errors[-1][:600]
        outcome = delegate._attempt(d, order, agent_cmd)
        attempt_row = {"attempt": attempt, "route": order.get("profile") or order["agent"],
                       "provider": order["agent"],
                       "result": outcome["status"], "seconds": outcome.get("seconds", 0)}
        if outcome["status"] == "usage_limit":
            while True:
                next_route = delegate._next_route(order)
                if next_route is None:
                    break
                order.update(profile=next_route["profile"], agent=next_route["agent"], model=next_route["model"],
                             effort=next_route["effort"], routed=next_route.get("why"))
                outcome = delegate._attempt(d, order, agent_cmd)
                attempt_row = {"attempt": attempt, "route": order.get("profile") or order["agent"],
                               "provider": order["agent"],
                               "result": outcome["status"], "seconds": outcome.get("seconds", 0)}
                if outcome["status"] != "usage_limit":
                    break
            if outcome["status"] == "usage_limit":
                break
        error = _error(outcome) if outcome["status"] in ("failed", "verify_failed", "timeout") else ""
        attempt_row["error"] = error[:600]
        history.append(attempt_row)
        order["attempt_history"] = history
        (d / "TASK.json").write_text(json.dumps(order, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        if outcome["status"] not in ("failed", "verify_failed", "timeout") or attempt > retries:
            break
        fingerprint = bt_runstate.error_hash(error)
        if errors and fingerprint == bt_runstate.error_hash(errors[-1]):
            outcome["status"] = "blocked"
            outcome["summary"] = "blocked: two consecutive attempts ended with the same normalized error"
            break
        errors.append(error)
        route_avoid = {order["agent"]}
    outcome["attempts"] = [{key: row.get(key) for key in ("attempt", "route", "result", "seconds")}
                           for row in history]
    outcome["status"] = "verified" if (outcome.get("verify") or {}).get("exit") == 0 else outcome["status"]
    if allocation:
        outcome = _worktree_result(order, allocation, outcome)
    (d / "TASK.json").write_text(json.dumps(order, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (d / "OUTCOME.json").write_text(json.dumps(outcome, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return delegate.summary(did)


def cleanup(did: str) -> dict:
    """Remove a clean delegation worktree while retaining its branch."""
    d = delegate.path_of(did)
    path = d / "WORKTREE.json"
    if not path.exists():
        raise SystemExit(f"Delegation {did} has no worktree")
    allocation = json.loads(path.read_text(encoding="utf-8"))
    worktree = Path(allocation["worktree"])
    if _git(worktree, "status", "--porcelain"):
        raise SystemExit("Refusing cleanup: worktree is dirty; preserve or commit its files first")
    _git(Path(allocation["repo"]), "worktree", "remove", str(worktree))
    return {"id": did, "worktree_removed": str(worktree), "branch_kept": allocation["branch"]}


def resume(did: str, agent_cmd: str | None = None) -> dict:
    """Take over an interrupted delegation without changing its id or attempt history."""
    d = delegate.path_of(did)
    saved = d / "OUTCOME.json"
    if saved.exists():
        outcome = json.loads(saved.read_text(encoding="utf-8"))
        if outcome.get("status") == "verified":
            return delegate.summary(did)
    claim = d / "CLAIMED"
    if claim.exists():
        try:
            pid = int(claim.read_text().strip() or 0)
        except ValueError:
            pid = 0
        from bt_runutil import pid_alive
        if pid and pid_alive(pid):
            raise SystemExit(f"Delegation {did} is still running (pid {pid})")
        claim.unlink(missing_ok=True)
    order = json.loads((d / "TASK.json").read_text(encoding="utf-8"))
    return execute(did, agent_cmd, int(order.get("retries", 0)), bool(order.get("worktree_mode")),
                   force_enhanced=True)
