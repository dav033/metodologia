"""Review & merge gate: what the executor changed in each workspace repo, and merging it as one unit.

The executor works on the same feature branch in every repo it touches (`feature_branch(rdir)`). Merging is
local (`--no-ff` into the repo's default branch); pushing happens only when the user presses the
"merge and publish" button — that click is the authorization.
"""
from __future__ import annotations

import subprocess

from bt_core import *  # noqa: F403


def feature_branch(rdir: Path) -> str:
    return f"feat/{rdir.name.lower()}"[:60]


def _git(repo: Path, *args: str, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, timeout=timeout,
                          encoding="utf-8", errors="replace")


def default_branch(repo: Path) -> str:
    head = _git(repo, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD").stdout.strip()
    if head:
        return head.split("/", 1)[-1]
    for name in ("main", "master"):
        if _git(repo, "rev-parse", "--verify", "--quiet", name).returncode == 0:
            return name
    return "main"


def repo_state(repo: Path, branch: str) -> dict:
    """Branch existence, commits ahead of the default branch, diff stat, dirtiness."""
    if not (repo / ".git").exists():
        return {"exists": False, "note": "not cloned on this machine"}
    base = default_branch(repo)
    if _git(repo, "rev-parse", "--verify", "--quiet", branch).returncode != 0:
        return {"exists": True, "branch": None, "base": base}
    commits = _git(repo, "log", "--format=%h %ad %s", "--date=short", f"{base}..{branch}").stdout.strip().splitlines()
    stat = _git(repo, "diff", "--stat", f"{base}...{branch}").stdout.strip().splitlines()
    dirty = [l for l in _git(repo, "status", "--porcelain").stdout.splitlines() if not l.startswith("??")]
    merged = _git(repo, "merge-base", "--is-ancestor", branch, base).returncode == 0
    return {"exists": True, "branch": branch, "base": base, "commits": commits, "stat": stat[-25:],
            "dirty": dirty, "merged": merged}


def review_state(project: str, rdir: Path) -> dict[str, dict]:
    branch = feature_branch(rdir)
    return {role: repo_state(path, branch) for role, path in ws.repos(ROOT, project, discover=False).items()}


def merge(project: str, rdir: Path, push: bool) -> list[str]:
    """Merge the feature branch into the default branch of every repo that has it. All-or-nothing pre-checks:
    nothing is merged if any repo is dirty."""
    branch = feature_branch(rdir)
    targets = {r: (p, s) for r, (p, s) in
               {role: (path, repo_state(path, branch)) for role, path in ws.repos(ROOT, project).items()}.items()
               if s.get("branch") and not s.get("merged")}
    if not targets:
        return ["Nada que fusionar: ningún repo tiene la rama " + branch + " pendiente."]
    dirty = [r for r, (_, s) in targets.items() if s["dirty"]]
    if dirty:
        return [f"No fusioné nada: hay cambios sin commit en {', '.join(dirty)}. Haz commit o stash y vuelve a intentar."]
    out = []
    req = req_id(rdir)
    for role, (path, st) in targets.items():
        current = _git(path, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        if _git(path, "checkout", "-q", st["base"]).returncode != 0:
            out.append(f"{role}: no pude cambiar a {st['base']}")
            continue
        res = _git(path, "merge", "--no-ff", "-m", f"merge: {req} ({branch})", branch)
        if res.returncode != 0:
            _git(path, "merge", "--abort")
            _git(path, "checkout", "-q", current)
            out.append(f"{role}: conflicto al fusionar — dejé el repo como estaba ({current})")
            continue
        line = f"{role}: fusionada {branch} → {st['base']} ({len(st['commits'])} commits)"
        if push:
            p = _git(path, "push", "-q", "origin", st["base"], timeout=120)
            line += " · push OK" if p.returncode == 0 else f" · push FALLÓ: {(p.stderr or '').strip()[:150]}"
        out.append(line)
    return out
