"""Recoverable handoff of an attempt's work, whatever way the agent ended.

Captures committed + uncommitted + untracked state WITHOUT touching the attempt's branch, its real index or the base:
a temporary index is filled from HEAD plus the working tree, written as a tree, and committed with `commit-tree` onto a
private ref (`refs/m3/handoff/<branch-without-m3/>`); HEAD itself is pinned under `refs/m3/head/<branch-without-m3/>`. A binary-safe patch
(`base..snapshot`) and a manifest are written next to it. The same call can be repeated after a crash: the dates come
from the caller, so the same work yields the same snapshot commit.

What is handed over is CODE STATE plus a plain-text brief. Nothing here claims that an agent's reasoning, context or
conversation transfers to another provider: a different agent starts from the files and the brief only.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

from . import gitutil
from .errors import ExecutorError
from .model import Workspace

MAX_LISTED = 200
MAX_COMMITS = 50


def _atomic(path: Path, data: bytes) -> None:
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    with os.fdopen(os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def capture(ws: Workspace, directory: Path, *, dirname: str, attempt_id: str, when: float, patch_max: int,
            log_tail: bytes = b"") -> dict[str, Any]:
    """Write `<directory>/handoff/*` and the private refs; returns the manifest. Raises WORKSPACE_ERROR on a git failure
    (the worktree directory itself is untouched, so the work is still physically there)."""
    out = Path(directory) / "handoff"
    out.mkdir(parents=True, exist_ok=True)
    tree = Path(ws.path)
    if not tree.is_dir():
        raise ExecutorError("WORKSPACE_ERROR", f"worktree is gone: {ws.path}")
    stamp = f"{int(when)} +0000"
    ident = {"GIT_AUTHOR_NAME": "Bitacora M3", "GIT_AUTHOR_EMAIL": "m3@localhost", "GIT_AUTHOR_DATE": stamp,
             "GIT_COMMITTER_NAME": "Bitacora M3", "GIT_COMMITTER_EMAIL": "m3@localhost", "GIT_COMMITTER_DATE": stamp}
    head = gitutil.run(tree, ["rev-parse", "HEAD"])
    branch_now = gitutil.run(tree, ["symbolic-ref", "-q", "--short", "HEAD"], check=False) or "(detached)"
    commits = gitutil.run(tree, ["rev-list", "--reverse", f"{ws.base_sha}..HEAD"], check=False).split()
    status = gitutil.run(tree, ["status", "--porcelain=v1", "-z", "--untracked-files=all"], binary=True)
    entries = [e for e in status.split(b"\0") if e]
    untracked = sum(1 for e in entries if e.startswith(b"??"))

    with tempfile.TemporaryDirectory(prefix="m3-index-") as scratch:
        env = {**ident, "GIT_INDEX_FILE": str(Path(scratch) / "index")}
        gitutil.run(tree, ["read-tree", "HEAD"], env=env)
        gitutil.run(tree, ["add", "-A"], env=env)
        snap_tree = gitutil.run(tree, ["write-tree"], env=env)
        if snap_tree == gitutil.run(tree, ["rev-parse", "HEAD^{tree}"]):
            snapshot = head
        else:
            snapshot = gitutil.run(tree, ["commit-tree", snap_tree, "-p", head, "-m", f"m3 snapshot {attempt_id}"],
                                   env=env)
    repo = Path(ws.repo)
    key = ws.branch.removeprefix("m3/") if ws.branch.startswith("m3/") else dirname    # root-scoped, see workspace.allocate
    gitutil.run(repo, ["update-ref", f"refs/m3/handoff/{key}", snapshot])
    gitutil.run(repo, ["update-ref", f"refs/m3/head/{key}", head])

    names = gitutil.run(repo, ["diff", "--no-renames", "--name-status", ws.base_sha, snapshot], check=False).splitlines()
    patch_info: dict[str, Any] = {"path": None, "bytes": 0, "sha256": None, "skipped": ""}
    if snapshot != ws.base_sha:
        raw = gitutil.run_capped(repo, ["diff", "--binary", "--full-index", "--no-renames", ws.base_sha, snapshot],
                                 patch_max)                       # streamed: a huge diff is never held in memory
        if raw is None:
            patch_info["skipped"] = f"patch is over the {patch_max} byte cap; the snapshot ref holds the work"
        else:
            _atomic(out / "changes.patch", raw)
            patch_info.update(path=str(out / "changes.patch"), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    if log_tail:
        _atomic(out / "log-tail.txt", log_tail)
    manifest = {
        "schema": 1, "attempt_id": attempt_id, "worktree": ws.path, "repository": ws.repo,
        "base_sha": ws.base_sha, "branch": ws.branch, "branch_at_end": branch_now, "head_sha": head,
        "snapshot_sha": snapshot, "has_commits": bool(commits), "commit_count": len(commits),
        "commits": commits[:MAX_COMMITS], "dirty": bool(entries), "untracked_count": untracked,
        "empty": snapshot == ws.base_sha, "changed_total": len(names), "changed": names[:MAX_LISTED],
        "patch": patch_info, "log_tail": str(out / "log-tail.txt") if log_tail else None,
        "refs": {"snapshot": f"refs/m3/handoff/{key}", "head": f"refs/m3/head/{key}"},
        "status": "captured"}
    _atomic(out / "manifest.json", json.dumps(manifest, indent=1, sort_keys=True).encode())
    return manifest


def write_brief(directory: Path, *, attempt_id: str, task_id: str, title: str, outcome: str, cause: str,
                manifest: dict[str, Any] | None, detail: str = "") -> Path:
    """A plain-text continuation note for a DIFFERENT agent or a human. Facts about the files and the stop, nothing more."""
    out = Path(directory) / "handoff"
    out.mkdir(parents=True, exist_ok=True)
    lines = [f"# Continuation brief — {task_id}", "",
             f"Task: {title}", f"Attempt: {attempt_id}", f"Ended: {outcome} ({cause})"]
    if detail:
        lines.append(f"Detail: {detail}")
    if manifest and manifest.get("status") == "captured":
        lines += ["", "## Preserved state",
                  f"- base commit: {manifest['base_sha']}", f"- attempt branch: {manifest['branch']}",
                  f"- last commit: {manifest['head_sha']} ({manifest['commit_count']} commit(s) after the base)",
                  f"- snapshot incl. uncommitted/untracked files: {manifest['snapshot_sha']}",
                  f"- files changed vs base: {manifest['changed_total']}",
                  "", "## To continue", f"- inspect: `git -C {manifest['repository']} diff {manifest['base_sha']} {manifest['snapshot_sha']}`",
                  f"- or apply `changes.patch` on a fresh worktree from {manifest['base_sha']}",
                  f"- the snapshot lives under `{manifest['refs']['snapshot']}`"]
        if manifest.get("empty"):
            lines.append("- NOTE: the attempt left no change at all")
    else:
        lines += ["", "No work could be captured (see manifest.json); the worktree may still hold files."]
    lines += ["", "## Limits",
              "- The previous agent's reasoning and conversation are NOT transferred; start from the files above.",
              "- Verify the state before relying on it: the agent's own report is a claim, not a verdict.", ""]
    path = out / "continue.md"
    _atomic(path, "\n".join(lines).encode())
    return path
