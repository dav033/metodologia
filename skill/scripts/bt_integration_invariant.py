"""Integration invariant: an integrated tree never silently loses the work of an accepted task (REQ-030 step 1).

Both ways of building "the tree a task starts from" (the predecessor merge of snapshots and the integration line) can end
with a clean merge that is still incomplete: a snapshot that is an ancestor of another is assumed to be "already part of
it" although its tree dropped the file, or a later task deleted something it never declared. REQ-020's T14 started from a
tree that kept T10's `voice.ts` and lost T12's `directions.ts` and T13's `packages.ts`; nobody noticed until a test failed
three attempts later.

The rule, checked after every integration: every file an accepted task left (`start -> snapshot`, added or changed) is in
the integrated tree with the task's content, unless the tree legitimately differs:

- another accepted task also changed that file (a merge may combine them: the tree is allowed to differ from both), or
- another accepted task deleted it AND either declares the path in `expected_paths` or is built on the owner (a task
  that comes after the owner may replace what it built on: that is the plan's own order, not a sibling's loss).

Anything else is `lost` (absent) or `reverted` (back at exactly the content it had before the task, nobody else touched it). `restore` writes the
owner's version back into the tree, so the repair is deterministic and never invents content. Pure functions over git
objects; `git` arrives as a callable so this module imports nothing from the integrator.
"""
from __future__ import annotations

import fnmatch
import os
import shutil
import subprocess
import tempfile
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

Git = Callable[..., subprocess.CompletedProcess]
MAX_FILES = 5000


@dataclass(frozen=True)
class Item:
    """An accepted task: where its attempt started and the snapshot it left."""
    task: str
    start: str
    snapshot: str


@dataclass(frozen=True)
class Report:
    lost: Mapping[str, tuple[str, ...]]          # task -> files absent from the tree
    reverted: Mapping[str, tuple[str, ...]]      # task -> files back at the content they had before the task changed them

    @property
    def ok(self) -> bool:
        return not self.lost and not self.reverted

    def files(self) -> dict[str, tuple[str, ...]]:
        merged: dict[str, tuple[str, ...]] = {}
        for source in (self.lost, self.reverted):
            for task, names in source.items():
                merged[task] = tuple(dict.fromkeys((*merged.get(task, ()), *names)))
        return merged

    def describe(self, limit: int = 6) -> str:
        parts = []
        for task, names in self.files().items():
            more = f" +{len(names) - limit}" if len(names) > limit else ""
            parts.append(f"{task}: {', '.join(names[:limit])}{more}")
        return "; ".join(parts)


def covers(pattern: str, path: str) -> bool:
    """Does an `expected_paths` entry name `path` (exactly, as a directory prefix or as a glob)?"""
    pattern = pattern.strip().replace("\\", "/").lstrip("./").rstrip("/")
    if not pattern:
        return False
    if any(ch in pattern for ch in "*?["):
        return fnmatch.fnmatchcase(path, pattern) or fnmatch.fnmatchcase(path, pattern.rstrip("*").rstrip("/") + "/*")
    return path == pattern or path.startswith(pattern + "/")


def _raw(git: Git, repo: Path, start: str, snapshot: str) -> dict[str, tuple[str, str, str]]:
    """{path: (status, blob in snapshot, blob in start)} of start -> snapshot, files only (no renames)."""
    done = git(repo, "diff-tree", "-r", "--no-renames", "--no-commit-id", "-z", start, snapshot, check=False)
    if done.returncode:
        return {}
    fields = done.stdout.split("\0")
    out: dict[str, tuple[str, str, str]] = {}
    index = 0
    while index + 1 < len(fields) and fields[index].startswith(":"):
        meta, name = fields[index].split(), fields[index + 1]
        index += 2
        if len(meta) < 5 or meta[1] == "160000" or meta[0].endswith("160000"):
            continue                                         # a submodule pointer is not a file of the task
        status = meta[4][:1]
        out[name] = (status, meta[3], meta[2])
        if len(out) >= MAX_FILES:
            break
    return out


def _tree(git: Git, repo: Path, tree: str) -> dict[str, str] | None:
    done = git(repo, "ls-tree", "-r", "-z", "--full-tree", tree, check=False)
    if done.returncode:
        return None
    found: dict[str, str] = {}
    for entry in done.stdout.split("\0"):
        if not entry or "\t" not in entry:
            continue
        meta, name = entry.split("\t", 1)
        parts = meta.split()
        if len(parts) == 3 and parts[1] == "blob":
            found[name] = parts[2]
    return found


def check(git: Git, repo: Path, tree: str, items: Iterable[Item], declared: Callable[[str], tuple[str, ...]] = lambda t: (),
          ancestors: Callable[[str], Iterable[str]] = lambda t: ()) -> Report:
    """The files of `items` that `tree` (a tree-ish) lost or silently reverted. Any git trouble reports nothing (the check
    never blocks a run on its own failure)."""
    items = list(items)
    present = _tree(git, repo, tree)
    if present is None:
        return Report({}, {})
    changes = {item.task: _raw(git, repo, item.start, item.snapshot) for item in items if item.start}
    owners: dict[str, set[str]] = {}
    for task, diff in changes.items():
        for name in diff:
            owners.setdefault(name, set()).add(task)
    lost: dict[str, list[str]] = {}
    reverted: dict[str, list[str]] = {}
    for task, diff in changes.items():
        for name, (status, blob, old) in diff.items():
            if status == "D":
                continue
            others = owners[name] - {task}
            if name not in present:
                removed = any(changes[o][name][0] == "D" and (task in set(ancestors(o)) or any(covers(p, name) for p in declared(o)))
                              for o in others if name in changes[o])
                if not removed:
                    lost.setdefault(task, []).append(name)
            elif present[name] == old and old != blob and not others:        # back to exactly what it was before the task
                reverted.setdefault(task, []).append(name)
    return Report({k: tuple(v) for k, v in lost.items()}, {k: tuple(v) for k, v in reverted.items()})


def foreign_deletions(git: Git, repo: Path, candidate: Item, others: Iterable[Item],
                      declared: Callable[[str], tuple[str, ...]] = lambda t: (),
                      ancestors: Callable[[str], Iterable[str]] = lambda t: (),
                      generated: Callable[[str], bool] = lambda path: False) -> dict[str, tuple[str, ...]]:
    """Files the candidate deletes that another accepted task left and the candidate does not declare: {owner: files}.
    Such a result cannot be integrated without erasing someone else's work, so it is the candidate that is sent back."""
    if not candidate.start:
        return {}
    mine = {name for name, (status, _new, _old) in _raw(git, repo, candidate.start, candidate.snapshot).items()
            if status == "D" and not generated(name)}
    if not mine:
        return {}
    found: dict[str, list[str]] = {}
    built_on = set(ancestors(candidate.task))
    for other in others:
        if other.task == candidate.task or not other.start or other.task in built_on:
            continue
        theirs = _raw(git, repo, other.start, other.snapshot)
        for name in sorted(mine):
            if name in theirs and theirs[name][0] != "D" and not any(covers(p, name) for p in declared(candidate.task)):
                found.setdefault(other.task, []).append(name)
    return {task: tuple(names) for task, names in found.items()}


def restore(git: Git, repo: Path, tree: str, items: Iterable[Item], report: Report) -> str | None:
    """A tree like `tree` with every lost or reverted file put back from its owner's snapshot. None when it cannot be done."""
    wanted = report.files()
    if not wanted:
        return tree
    snapshots = {item.task: item.snapshot for item in items}
    scratch = Path(tempfile.mkdtemp(prefix="m3-invariant-"))
    try:
        env = {**os.environ, "GIT_INDEX_FILE": str(scratch / "index")}
        read = subprocess.run(["git", "-C", str(repo), "read-tree", tree], env=env, capture_output=True, text=True)
        if read.returncode:
            return None
        for task, names in wanted.items():
            snapshot = snapshots.get(task)
            if not snapshot:
                return None
            for name in names:
                entry = git(repo, "ls-tree", snapshot, "--", name, check=False).stdout.split()
                if len(entry) < 3:
                    return None
                upd = subprocess.run(["git", "-C", str(repo), "update-index", "--add", "--cacheinfo",
                                      f"{entry[0]},{entry[2]},{name}"], env=env, capture_output=True, text=True)
                if upd.returncode:
                    return None
        written = subprocess.run(["git", "-C", str(repo), "write-tree"], env=env, capture_output=True, text=True)
        return written.stdout.strip() if written.returncode == 0 and written.stdout.strip() else None
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
