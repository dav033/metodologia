"""The tree the owner tries for a subplan that builds on others (D-246): its own version with the current accepted work of
the subplans it builds on folded in.

A subplan's line holds its members plus the frozen-plan tasks they depend on, so it never receives a repair a later stage
adds to an earlier subplan when none of its members depends on it (pictures REQ-021 r29, 2026-10-31: trying SP-14 after
an SP-2 fix showed SP-14's tree with SP-2's old defect). `fold` merges each predecessor's current subplan line tip into
the version, in plan order, with git's three-way `merge-tree` (objects only, no worktree): a predecessor whose tip is
already in the version's history, or whose merge changes nothing, is included as it is; a text conflict folds nothing and
is reported, so «Probar» says the tree lacks that work instead of showing a stale tree silently.

The folded commit is deterministic (fixed identity and dates, parents = the version and the predecessors' tips) and kept
reachable by `refs/bt/try/<project>/<REQ>/r<N>/<role>/<SP>`; a fold whose tree equals the tree that ref already holds
keeps that commit, so the owner's decision is reset only when the tried tree changes. Standard library only.
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

IDENT = {"GIT_AUTHOR_NAME": "Bitacora Verify", "GIT_AUTHOR_EMAIL": "verify@localhost",
         "GIT_COMMITTER_NAME": "Bitacora Verify", "GIT_COMMITTER_EMAIL": "verify@localhost",
         "GIT_AUTHOR_DATE": "1700000000 +0000", "GIT_COMMITTER_DATE": "1700000000 +0000"}
_CACHE: dict[tuple, dict] = {}
_SAFE_REF = re.compile(r"[^A-Za-z0-9._-]+")


def _git(repo: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    base = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=120,
                          env={**base, **(env or {})}, check=False)


def _tree(repo: Path, commit: str) -> str:
    return _git(repo, "rev-parse", "-q", "--verify", f"{commit}^{{tree}}").stdout.strip()


def predecessors(plan: dict, sid: str) -> list[str]:
    """The subplans `sid` builds on, in plan order: those owning a frozen-plan ancestor of one of its tasks, and the
    members before it of the smallest composition gate holding it (cumulative gates: SP-14 in [SP-1, SP-2, SP-14])."""
    order = [s.get("id") for s in plan.get("subplans") or () if isinstance(s, dict)]
    tasks = {t.get("id"): t for t in plan.get("tasks") or () if isinstance(t, dict) and t.get("id")}
    found: set[str] = set()
    todo = [d for t in tasks.values() if t.get("subplan_id") == sid for d in t.get("after") or ()]
    seen: set[str] = set()
    while todo:
        current = todo.pop()
        if current in seen or current not in tasks:
            continue
        seen.add(current)
        owner = tasks[current].get("subplan_id")
        if owner and owner != sid:
            found.add(str(owner))
        todo.extend(tasks[current].get("after") or ())
    holding = [g for g in plan.get("composition_gates") or () if isinstance(g, dict) and sid in (g.get("subplans") or ())]
    if holding and sid in order:
        smallest = min(holding, key=lambda g: len(g.get("subplans") or ()))
        found.update(m for m in smallest.get("subplans") or () if m in order and order.index(m) < order.index(sid))
    return [s for s in order if s in found]


def fold(repo: Path, commit: str, preds: list[tuple[str, str]], ref: str, resolutions: Path | None = None) -> dict:
    """{"commit": what the owner tries, "includes": predecessors whose tip is in it, "conflict": {} or {"with", "files"}}.
    A conflict git leaves is settled as the composer settles it (`package.json` by key, a subsumed hunk, a resolution
    recorded under `resolutions`; never a new resolution request); one that stays (or a git failure) folds nothing:
    `commit` is returned as it is."""
    key = (str(repo), commit, tuple(preds), ref, str(resolutions))
    if key not in _CACHE:
        _CACHE[key] = _fold(Path(repo), commit, preds, ref, resolutions)
    return _CACHE[key]


def _settled(repo: Path, ours: str, theirs: str, resolutions: Path | None) -> tuple[str, list[str]] | None:
    """(tree, conflicts left) by the composer's merge rules on the single merge base; None when they do not apply."""
    bases = _git(repo, "merge-base", "--all", ours, theirs).stdout.split()
    if len(bases) != 1 or resolutions is None:
        return None
    try:
        from bt_composition_adapter import GitSubprocessPort
        port = GitSubprocessPort(repo, Path(resolutions).parent / "ws")
        port.resolutions, port.request_resolutions = Path(resolutions), False
        result = port.merge_tree(bases[0], ours, theirs)
    except Exception:  # noqa: BLE001 - the plain conflict is reported instead
        return None
    return result.tree, list(result.conflicts)


def _fold(repo: Path, commit: str, preds: list[tuple[str, str]], ref: str, resolutions: Path | None) -> dict:
    acc, included = commit, []
    for sid, tip in preds:
        if _git(repo, "merge-base", "--is-ancestor", tip, acc).returncode == 0:
            included.append(sid)
            continue
        merged = _git(repo, "merge-tree", "--write-tree", "--name-only", "--no-messages", acc, tip)
        lines = merged.stdout.splitlines()
        tree = lines[0].strip() if merged.returncode == 0 and lines else ""
        if merged.returncode == 1:
            settled = _settled(repo, acc, tip, resolutions)
            if settled is None or settled[1]:
                files = settled[1] if settled else [line for line in lines[1:] if line.strip()]
                return _unfolded(repo, commit, preds, {"with": sid, "files": files[:20]})
            tree = settled[0]
        if not tree:
            return _unfolded(repo, commit, preds, {"with": sid, "files": [], "error": (merged.stderr or "").strip()[:200]})
        included.append(sid)
        if tree == _tree(repo, acc):
            continue                                     # its work is already there (e.g. a re-seeded line)
        made = _git(repo, "commit-tree", tree, "-p", acc, "-p", tip, "-m",
                    f"bt: try with {sid}'s current line", env=IDENT)
        if made.returncode != 0:
            return _unfolded(repo, commit, preds, {"with": sid, "files": [], "error": (made.stderr or "").strip()[:200]})
        acc = made.stdout.strip()
    if acc != commit:
        tree = _tree(repo, acc)
        if tree == _tree(repo, commit):
            acc = commit
        else:
            kept = _git(repo, "rev-parse", "-q", "--verify", f"{ref}^{{commit}}").stdout.strip()
            if kept and _tree(repo, kept) == tree:
                acc = kept                               # the same tree as before: the same version
            else:
                _git(repo, "update-ref", ref, acc)       # keeps the commit reachable while it is offered
    return {"commit": acc, "includes": included, "conflict": {}}


def _unfolded(repo: Path, commit: str, preds: list[tuple[str, str]], conflict: dict) -> dict:
    """Nothing folded: the version as it is, with the predecessors its own history already holds."""
    held = [sid for sid, tip in preds if _git(repo, "merge-base", "--is-ancestor", tip, commit).returncode == 0]
    return {"commit": commit, "includes": held, "conflict": conflict}


def folded(rows: list[dict], lines: dict) -> list[dict]:
    """Each version with the current accepted work of the subplans it builds on (bt_verification_tree, D-246): a later
    subplan's line never takes a repair added to an earlier one that none of its members depends on, so trying it
    showed the earlier subplan's old defect. A changed tree is one more version; `includes` names what it holds."""
    if not lines:
        return rows
    plan, tips = lines["plan"], lines["tips"]
    order = [s.get("id") for s in plan.get("subplans") or () if isinstance(s, dict)]
    versions: dict[str, int] = {}                        # what the owner tries for each subplan
    own: dict[str, int] = {}                             # the version that is exactly its line's tip, before any fold
    for row in sorted(rows, key=lambda r: order.index(r["id"]) if r["id"] in order else len(order)):
        sid = row["id"]
        if sid in tips and row["commit"] == tips[sid][0]:
            own[sid] = row["version"]
        if sid in tips:
            _tip, repo, role = tips[sid]
            preds = [(p, tips[p][0]) for p in predecessors(plan, sid) if p in tips and tips[p][2] == role]
            if preds:
                ref = (f"refs/bt/try/{_SAFE_REF.sub('-', lines['project'])}/{lines['req']}/r{lines['revision']}/"
                       f"{_SAFE_REF.sub('-', role)}/{_SAFE_REF.sub('-', sid)}")
                done = fold(repo, row["commit"], preds, ref, lines.get("resolutions"))
                if done["commit"] != row["commit"]:
                    row["version"], row["commit"] = row["version"] + 1, done["commit"]
                # folded: each predecessor as the owner tries it (its own predecessors are folded here too); not
                # folded: only the predecessors' own line versions are in the tree
                named = own if done["conflict"] else versions
                row["includes"] = [{"id": p, "version": named.get(p)} for p in done["includes"]]
                if done["conflict"]:
                    row["fold_conflict"] = done["conflict"]
        versions[sid] = row["version"]
    return rows
