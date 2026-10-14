"""Read-only interactive review using a detached throwaway worktree."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import bt_agents
import bt_delegate


def _git(cwd: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, encoding="utf-8", check=False)
    if check and result.returncode:
        raise SystemExit((result.stderr or result.stdout).strip() or "git command failed")
    return result.stdout.strip()


def _base(repo: Path, requested: str | None) -> str:
    if requested:
        return requested
    default = ""
    for branch in ("main", "master", "trunk"):
        if _git(repo, "rev-parse", "--verify", branch, check=False):
            default = branch
            break
    if default:
        merge = _git(repo, "merge-base", "HEAD", default, check=False)
        if merge:
            return merge
    return _git(repo, "rev-parse", "HEAD~1", check=False) or _git(repo, "rev-parse", "HEAD")


def _copy_dirty(repo: Path, worktree: Path) -> None:
    raw = _git(repo, "diff", "HEAD", "--name-status", "-z")
    fields = raw.split("\0") if raw else []
    for index in range(0, len(fields) - 1, 2):
        status, name = fields[index:index + 2]
        source, target = repo / name, worktree / name
        if status.startswith("D"):
            target.unlink(missing_ok=True)
            continue
        if not source.exists() or not source.is_file():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    untracked = _git(repo, "ls-files", "--others", "--exclude-standard", "-z").split("\0")
    for name in filter(None, untracked):
        source, target = repo / name, worktree / name
        if source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def _fingerprint(worktree: Path) -> str:
    data = subprocess.run(["git", "diff", "HEAD", "--binary"], cwd=worktree, capture_output=True, check=True).stdout
    untracked = _git(worktree, "ls-files", "--others", "--exclude-standard", "-z").split("\0")
    for name in sorted(filter(None, untracked)):
        path = worktree / name
        data += name.encode("utf-8", "surrogateescape") + b"\0" + (path.read_bytes() if path.is_file() else b"")
    return hashlib.sha256(data).hexdigest()


def _provider(project: str, requested: str | None) -> tuple[str | None, str]:
    pool = bt_agents.pool_for(project, bt_agents._config("routing.pool", []) or None)
    if not pool:
        raise SystemExit(f"No account may run '{project}'. Check: bitacora.py agents")
    builder = os.environ.get("BITACORA_BUILDER_PROVIDER")
    avoid = {builder} if builder in bt_agents.PROVIDERS else set()
    routes, _ = bt_agents.candidates(project, pool, bt_agents.start_tier(None, "audit"), "audit", avoid_providers=avoid)
    route = next((item for item in routes if item["agent"] == requested), None) if requested else (routes[0] if routes else None)
    if not requested and builder in bt_agents.PROVIDERS and route and route["agent"] == builder:
        route = next((item for item in routes if item["agent"] != builder), None)
    if route is None:
        raise SystemExit(f"No eligible audit route for provider {requested or 'router choice'}")
    return route.get("profile"), route["agent"]


def review(workdir: Path, base: str | None = None, focus: str | None = None, provider: str | None = None,
           project: str | None = None, agent_cmd: str | None = None) -> dict:
    """Audit the caller's committed and uncommitted changes without touching its checkout."""
    repo_text = _git(workdir.resolve(), "rev-parse", "--show-toplevel", check=False)
    if not repo_text:
        raise SystemExit(f"review requires a working directory inside a git repository: {workdir}")
    repo = Path(repo_text)
    project = project or "review"
    start_base = _base(repo, base)
    _git(repo, "rev-parse", "--verify", f"{start_base}^{{commit}}")
    pid, agent = _provider(project, provider)
    review_root = bt_delegate.STATE / "reviews"
    review_root.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix="review-", dir=review_root))
    path = temporary / "snapshot"
    _git(repo, "worktree", "add", "--detach", str(path), "HEAD")
    try:
        _copy_dirty(repo, path)
        before = _fingerprint(path)
        task = (f"Review changes against base {start_base}. Include committed changes since the base, uncommitted "
                f"changes, and untracked files. Focus: {focus or 'correctness, regressions, security, and tests'}. "
                "Do not edit files. Return a JSON object in the summary with keys verdict and findings. Rank each "
                "finding high, med, or low and include file:line evidence. Verdict must be approve or findings.")
        order = bt_delegate.create(project, task, pid, None if pid else agent, repo, [], None, 30, None, None,
                                   kind="audit")
        order["workdir"] = str(path)
        (bt_delegate.path_of(order["id"]) / "TASK.json").write_text(
            json.dumps(order, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        started = time.time()
        outcome = bt_delegate._attempt(bt_delegate.path_of(order["id"]), order, agent_cmd)
        modified = _fingerprint(path) != before
        report_path = bt_delegate.path_of(order["id"]) / "RESULT.json"
        report = bt_delegate._read_result(report_path) if report_path.exists() else None
        payload = {}
        if report:
            try:
                payload = json.loads(report.get("summary") or "{}")
            except ValueError:
                payload = {"verdict": "incomplete", "findings": []}
        result = {"verdict": payload.get("verdict", "incomplete"),
                  "findings": payload.get("findings", []),
                  "route": {"provider": agent, "profile": pid},
                  "seconds": int(time.time() - started), "modified_tree": modified}
        if outcome.get("status") in ("failed", "timeout", "usage_limit"):
            result["verdict"] = "incomplete"
        if modified:
            removed = subprocess.run(["git", "worktree", "remove", str(path)], cwd=repo, capture_output=True,
                                     text=True, encoding="utf-8", errors="replace", check=False)
            if removed.returncode:
                result["throwaway_worktree"] = str(path)
                result["cleanup"] = "removal refused without force; retained at the reported path"
            else:
                temporary.rmdir()
        else:
            _git(repo, "worktree", "remove", str(path))
            temporary.rmdir()
        return result
    except BaseException:
        # Keep a registered worktree intact when any review or cleanup step fails.
        raise
