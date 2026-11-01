"""The engine's scratch space (D-266): attempt worktrees removed once nothing needs them, and the free-space guard.

2026-10-31 ~18:45: `/` and `/home` (one btrfs filesystem) reached 100 % and pictures REQ-021 r32 T3.91 a9 failed with
«No space left on device». `<scratch>/ws/<project>/worktrees/` held ~480 attempt worktrees of runs r15..r32, each with
its own `node_modules` and Next build (~800 MB apparent): `GitWorkspaces` never deletes, and nothing else did. What an
attempt leaves that matters is kept elsewhere: its snapshot commit (`refs/m3/handoff/<branch-name>`, written by
`handoff.capture`), its branch, and `<scratch>/attempts/<key>/` (prompt, log, handoff manifest). A retry continues from
the snapshot REF (`base_override` is a commit; `_continuation` and `_own_handoff` read refs and commit subjects in the
repository), never from an earlier attempt's checkout. The one reader of a checkout after its capture is M6, which mounts
the attempt's own `node_modules` when it verifies that attempt (`sandbox_mounts.attempt_mounts`): the first
verification, the `relaxed` re-verification and the owner's `reverify` — all of them about the LATEST attempt of an
OPEN task round.

So a worktree is removed when its attempt is captured (the handoff ref still names the manifest's snapshot) and either
its task round has ended (the task workflow is terminal) or a later attempt of the same round exists. Kept, with the
reason: the agent workflow still runs, its unit is still held, a process works inside it, the capture is missing or its
ref moved (`no-snapshot`, reported), the workflow is unknown to DBOS, or it is the latest attempt of an open round.

`<scratch>` is `execution.scratch_root` (default `<state>/durable/attempts-root`). See the README (Disk space) for the
operator's btrfs subvolume layout: everything the engine writes and deletes here would otherwise be pinned by the
hourly snapper snapshots of /home.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from collections.abc import Callable, Iterable, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

LOG = logging.getLogger("bt_durable.scratch")
TERMINAL = frozenset({"SUCCESS", "ERROR", "CANCELLED", "MAX_RECOVERY_ATTEMPTS_EXCEEDED"})
CHUNK = 200                               # workflow ids per DBOS query
DEFAULT_MIN_FREE_GB = 10
CODE = "DISK_LOW"
GB = 10 ** 9


def scratch_root(state_dir: Path) -> Path:
    """`execution.scratch_root` (`~` expanded) or `<state_dir>/attempts-root`."""
    import bt_config
    configured = str(bt_config.get("execution.scratch_root", "") or "").strip()
    return Path(configured).expanduser() if configured else Path(state_dir) / "attempts-root"


# ---------------------------------------------------------------------------------------------------- inventory
@dataclass(frozen=True)
class Candidate:
    """An attempt whose worktree is still on disk (from its `attempts/<key>/workspace.json`)."""
    key: str
    worktree: Path
    repository: Path
    attempt_dir: Path


@dataclass
class Verdict:
    key: str
    worktree: str
    action: str                       # remove (eligible) | removed | keep | failed
    reason: str
    bytes: int | None = None


@dataclass
class Report:
    root: str
    applied: bool
    verdicts: list[Verdict] = field(default_factory=list)
    orphans: list[str] = field(default_factory=list)       # worktree folders no attempt record names (never removed)

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for item in self.verdicts:
            out[item.action] = out.get(item.action, 0) + 1
        return out

    def reasons(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for item in self.verdicts:
            if item.action == "keep":
                out[item.reason] = out.get(item.reason, 0) + 1
        return out

    def summary(self) -> dict:
        sized = [v.bytes for v in self.verdicts if v.action in ("remove", "removed") and v.bytes is not None]
        return {"root": self.root, "applied": self.applied, "counts": self.counts(), "kept": self.reasons(),
                "bytes": sum(sized) if sized else None, "orphans": len(self.orphans)}

    def as_dict(self) -> dict:
        return {**self.summary(), "attempts": [asdict(v) for v in self.verdicts], "orphan_paths": self.orphans}


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _under(path: Path, root: Path) -> bool:
    try:
        return path.resolve().is_relative_to(root.resolve())
    except OSError:
        return False


def candidates(root: Path) -> tuple[list[Candidate], list[str]]:
    """(attempts whose worktree exists, worktree folders under `<root>/ws/*/worktrees` no attempt names)."""
    root = Path(root)
    found, named = [], set()
    attempts = root / "attempts"
    for adir in sorted(attempts.iterdir() if attempts.is_dir() else ()):
        data = _read_json(adir / "workspace.json")
        if not data.get("path") or not data.get("repo") or data.get("kind", "attempt") != "attempt":
            continue
        tree = Path(str(data["path"]))
        named.add(os.path.normpath(str(tree)))
        if tree.exists() or tree.is_symlink():
            found.append(Candidate(adir.name, tree, Path(str(data["repo"])), adir))
    orphans = []
    for tree in sorted(root.glob("ws/*/worktrees/*")):
        if tree.is_dir() and not tree.is_symlink() and os.path.normpath(str(tree)) not in named \
                and os.path.normpath(str(tree.resolve())) not in named:
            orphans.append(str(tree))
    return found, orphans


# --------------------------------------------------------------------------------------------- workflow facts
@dataclass(frozen=True)
class Facts:
    """What DBOS says: agent workflow key -> (status, parent task workflow, created_at); parent -> status; and, for the
    open parents, every agent child (key, created_at)."""
    agents: dict[str, tuple[str, str, int]]
    parents: dict[str, str]
    siblings: dict[str, list[tuple[str, int]]]


def _chunks(items: Sequence[str]) -> Iterable[list[str]]:
    for start in range(0, len(items), CHUNK):
        yield list(items[start:start + CHUNK])


def _agent_key(workflow_id: str) -> str:
    return workflow_id[3:-6] if workflow_id.startswith("bt:") and workflow_id.endswith(":agent") else ""


def workflow_facts(list_workflows: Callable[..., list], keys: Sequence[str]) -> Facts:
    """`list_workflows`: `DBOS.list_workflows` (inside the engine) or `DBOSClient.list_workflows` (the CLI)."""
    agents: dict[str, tuple[str, str, int]] = {}
    for chunk in _chunks([f"bt:{key}:agent" for key in keys]):
        for row in list_workflows(workflow_ids=chunk, load_input=False, load_output=False):
            agents[_agent_key(row.workflow_id)] = (str(row.status), str(row.parent_workflow_id or ""),
                                                   int(row.created_at or 0))
    parents: dict[str, str] = {}
    wanted = sorted({parent for _, parent, _ in agents.values() if parent})
    for chunk in _chunks(wanted):
        for row in list_workflows(workflow_ids=chunk, load_input=False, load_output=False):
            parents[row.workflow_id] = str(row.status)
    siblings: dict[str, list[tuple[str, int]]] = {}
    open_parents = [parent for parent in wanted if parents.get(parent) not in TERMINAL and parent in parents]
    for chunk in _chunks(open_parents):
        for row in list_workflows(parent_workflow_id=chunk, load_input=False, load_output=False):
            key = _agent_key(row.workflow_id)
            if key:
                siblings.setdefault(str(row.parent_workflow_id), []).append((key, int(row.created_at or 0)))
    return Facts(agents, parents, siblings)


# ------------------------------------------------------------------------------------------------ the decision
def captured(candidate: Candidate, git: Callable[..., subprocess.CompletedProcess]) -> str:
    """'' when the attempt's capture is complete and its snapshot ref still names it, else why not."""
    manifest = _read_json(candidate.attempt_dir / "handoff" / "manifest.json")
    snapshot = manifest.get("snapshot_sha")
    ref = (manifest.get("refs") or {}).get("snapshot") if isinstance(manifest.get("refs"), dict) else None
    if manifest.get("status") != "captured" or not isinstance(snapshot, str) or not isinstance(ref, str) \
            or not ref.startswith("refs/m3/handoff/"):
        return "no-snapshot"
    if os.path.normpath(str(manifest.get("worktree") or "")) != os.path.normpath(str(candidate.worktree)):
        return "manifest-mismatch"
    done = git(candidate.repository, "rev-parse", "-q", "--verify", f"{ref}^{{commit}}")
    if done.returncode != 0 or done.stdout.strip() != snapshot:
        return "no-snapshot"
    return ""


def decide(candidate: Candidate, facts: Facts, *, held: frozenset[str], busy: frozenset[str], capture: str) -> str:
    """'' = remove; else the reason it is kept. Pure over the facts gathered for this pass."""
    if candidate.key in held:
        return "unit-held"
    if os.path.normpath(str(candidate.worktree)) in busy:
        return "in-use"
    agent = facts.agents.get(candidate.key)
    if agent is None:
        return "no-workflow"
    status, parent, created = agent
    if status not in TERMINAL:
        return "running"
    if capture:
        return capture
    if not parent or parent not in facts.parents:
        return "no-workflow"
    if facts.parents[parent] in TERMINAL:
        return ""                                                    # the task round ended
    later = [key for key, at in facts.siblings.get(parent, ()) if key != candidate.key and at > created]
    return "" if later else "latest-of-open-round"


def processes_inside(trees: Iterable[Path], proc: Path = Path("/proc")) -> frozenset[str]:
    """The trees some process of this user has as its working directory (one scan of /proc for the pass)."""
    roots = {os.path.realpath(tree): os.path.normpath(str(tree)) for tree in trees}     # the kernel names real paths
    if not roots:
        return frozenset()
    busy = set()
    uid = os.getuid()
    for entry in proc.iterdir() if proc.is_dir() else ():
        if not entry.name.isdigit():
            continue
        try:
            if entry.stat().st_uid != uid:
                continue
            cwd = os.readlink(entry / "cwd")
        except OSError:
            continue
        for real, norm in roots.items():
            if cwd == real or cwd.startswith(real + os.sep):
                busy.add(norm)
    return frozenset(busy)


def size_of(path: Path) -> int:
    """Allocated bytes under `path` (st_blocks, symlinks not followed). Shared reflinks and snapshots are not seen."""
    total, stack = 0, [str(path)]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    try:
                        info = entry.stat(follow_symlinks=False)
                    except OSError:
                        continue
                    total += getattr(info, "st_blocks", 0) * 512
                    if entry.is_dir(follow_symlinks=False):
                        stack.append(entry.path)
        except OSError:
            continue
    return total


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False, timeout=600)


def remove(candidate: Candidate, root: Path, git: Callable[..., subprocess.CompletedProcess] = _git) -> str:
    """Remove the worktree under its repository's workspace lock; '' or why it could not. Branch, refs and the attempt
    folder stay. A folder git no longer knows (pruned, a removal cut short by a restart) is deleted only inside
    `<root>/ws`."""
    from .legacy import GitWorkspaces
    tree = candidate.worktree
    ws_root = Path(root) / "ws"
    if tree.is_symlink() or not _under(tree, ws_root):
        return "outside-scratch"
    workspaces = GitWorkspaces(tree.parent.parent, {})
    with workspaces._repo_lock(candidate.repository.resolve()):             # the lock `allocate` takes
        done = git(candidate.repository, "worktree", "remove", "--force", str(tree))
        if tree.exists() and not tree.is_symlink():
            shutil.rmtree(tree, ignore_errors=True)
        git(candidate.repository, "worktree", "prune")
    if tree.exists():
        return f"still present ({(done.stderr or '').strip()[:200]})"
    return ""


def collect(root: Path, list_workflows: Callable[..., list], *, apply: bool, held: Iterable[str] = (),
            sizes: bool = False, limit: int | None = None, git: Callable[..., subprocess.CompletedProcess] = _git,
            proc: Path = Path("/proc"), emit: Callable[..., None] | None = None) -> Report:
    """One pass: decide every attempt worktree of `root`; with `apply`, remove the eligible ones (at most `limit`)."""
    root = Path(root)
    report = Report(root=str(root), applied=apply)
    found, report.orphans = candidates(root)
    if not found:
        return report
    facts = workflow_facts(list_workflows, [c.key for c in found])
    busy = processes_inside([c.worktree for c in found], proc)
    held = frozenset(held)
    removed = 0
    for candidate in found:
        agent = facts.agents.get(candidate.key)
        capture = captured(candidate, git) if agent is not None and agent[0] in TERMINAL else ""
        reason = decide(candidate, facts, held=held, busy=busy, capture=capture)
        verdict = Verdict(candidate.key, str(candidate.worktree), "keep" if reason else "remove", reason or "settled")
        if not reason and sizes:
            verdict.bytes = size_of(candidate.worktree)
        if not reason and apply and (limit is None or removed < limit):
            why = remove(candidate, root, git)
            verdict.action, verdict.reason = ("failed", why) if why else ("removed", verdict.reason)
            removed += not why
            if emit is not None:
                emit("worktree_removed" if not why else "worktree_remove_failed", attempt_key=candidate.key,
                     worktree=str(candidate.worktree), **({"error": why} if why else {}))
        report.verdicts.append(verdict)
    return report


def render(report: Report) -> str:
    """The operator's summary lines (the CLI prints them before the JSON)."""
    summary = report.summary()
    counts = summary["counts"]
    size = summary["bytes"]
    lines = [f"scratch root: {report.root}",
             f"{'removed' if report.applied else 'eligible (dry run)'}: "
             f"{counts.get('removed' if report.applied else 'remove', 0)} worktrees"
             + (f", {size / GB:.2f} GB allocated" if size is not None else ""),
             "kept: " + (", ".join(f"{reason} {n}" for reason, n in sorted(summary["kept"].items())) or "none")]
    if counts.get("failed"):
        lines.append(f"failed: {counts['failed']}")
    if report.applied and counts.get("remove"):
        lines.append(f"left for the next pass (limit): {counts['remove']}")
    if report.orphans:
        lines.append(f"orphan worktree folders (no attempt record, never removed): {len(report.orphans)}")
    if not report.applied:
        lines.append("nothing was removed; run again with --apply to remove the eligible worktrees")
    return "\n".join(lines)


def enabled() -> bool:
    import bt_config
    return bt_config.get("execution.worktree_gc", True) is True


# ------------------------------------------------------------------------------------------------- disk guard
def min_free_bytes() -> int:
    """`execution.min_free_gb` (GB, 10**9 bytes); 0 turns the guard off."""
    import bt_config
    value = bt_config.get("execution.min_free_gb", DEFAULT_MIN_FREE_GB)
    return int(value) * GB if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else \
        DEFAULT_MIN_FREE_GB * GB


def _existing(path: Path) -> Path:
    path = Path(path)
    while not path.exists() and path != path.parent:
        path = path.parent
    return path


def consumers(root: Path, extra: dict[str, Path] | None = None, top: int = 5) -> list[dict]:
    """The engine-owned scratch, counted cheaply (directory entries, no sizes): attempt worktrees per project and the
    legacy executor's worktrees."""
    found = []
    for project in sorted((Path(root) / "ws").iterdir() if (Path(root) / "ws").is_dir() else ()):
        trees = project / "worktrees"
        count = sum(1 for p in trees.iterdir() if p.is_dir()) if trees.is_dir() else 0
        if count:
            found.append({"what": f"attempt worktrees ({project.name})", "count": count, "path": str(trees)})
    for label, base in (extra or {}).items():
        count = sum(1 for p in Path(base).glob("*/ws/worktrees/*") if p.is_dir()) if Path(base).is_dir() else 0
        if count:
            found.append({"what": label, "count": count, "path": str(base)})
    return sorted(found, key=lambda item: -item["count"])[:top]


class DiskGuard:
    """`check(run=None, plan=None, task_id="")` -> {} when every watched filesystem has at least the configured free
    space, else {"state": "low", "free_bytes", "threshold_bytes", "path", "consumers"}. Watched: the scratch root (the
    attempts' worktrees) and the engine's state folder (M6 store, telemetry, DBOS on SQLite)."""

    def __init__(self, root: Path, *, state_dir: Path | None = None, extra: dict[str, Path] | None = None,
                 threshold: Callable[[], int] = min_free_bytes,
                 usage: Callable[[str], object] = shutil.disk_usage):
        self.root, self.state_dir, self.extra = Path(root), state_dir, extra or {}
        self.threshold, self.usage = threshold, usage

    def check(self, run=None, plan=None, task_id: str = "") -> dict:
        threshold = self.threshold()
        if threshold <= 0:
            return {}
        lowest: tuple[int, Path] | None = None
        for path in (self.root, *([self.state_dir] if self.state_dir else [])):
            where = _existing(path)
            try:
                free = int(self.usage(str(where)).free)
            except OSError:
                continue
            if lowest is None or free < lowest[0]:
                lowest = (free, where)
        if lowest is None or lowest[0] >= threshold:
            return {}
        return {"state": "low", "free_bytes": lowest[0], "threshold_bytes": threshold, "path": str(lowest[1]),
                "consumers": consumers(self.root, self.extra), "task_id": task_id}


def verify_refusal(found: dict) -> dict:
    """The fields of the VerifyOutcome a verification refused for disk space carries (NEEDS_REVIEW, DISK_LOW)."""
    return {"reason_code": CODE, "digest": describe(found), "issue_codes": (CODE,)}


def describe(found: dict) -> str:
    free, threshold = int(found.get("free_bytes") or 0), int(found.get("threshold_bytes") or 0)
    biggest = "; ".join(f"{item['what']}: {item['count']}" for item in found.get("consumers") or ())
    return (f"{CODE}: {free / GB:.2f} GB free on {found.get('path')} (below execution.min_free_gb = "
            f"{threshold / GB:g} GB)" + (f"; engine scratch: {biggest}" if biggest else "")
            + ". Free space (`uv run bt-durable gc-worktrees --apply` removes the worktrees of settled attempts), "
              "then retry")
