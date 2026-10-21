"""Integration line: the one place that holds "the current integrated tree" of a run (REQ-028, P-134).

`PredecessorIntegrator` merges the accepted SNAPSHOTS of a task's ancestors, and every snapshot keeps the version of
each file its task was built on. When a task is redone, the accepted tasks built on its old result keep carrying the old
text, and a later merge can return it: the fix never reaches the audit. The line fixes the cause instead of the symptoms.

Per repository role of the run there is one ref, `refs/m3/line/<run>/<role>`, that points at the integrated tree:

- every accepted task contributes `(start_base, snapshot)`: the commit its attempt started from and the snapshot it left.
  Only its own work counts (`start_base -> snapshot`), never the lineage it was built on;
- the tip is a deterministic fold of the contributions of the CURRENTLY accepted tasks, in plan order, each applied with
  `git merge-tree --write-tree --merge-base=<start_base> <tip> <snapshot>` (objects only: no worktree, no index);
- a contribution that does not apply cleanly is not guessed and not dropped silently: its task is reported in
  `needs_resolution()` with the conflicting files and stays out of the tip;
- a redone task replaces its previous contribution, so the next `recompute()` replays everything else on top of the fix.

The tip is a pure function of persisted facts (accepted map, snapshots, start bases): `recompute()` is idempotent, the
commits are deterministic (fixed identity and date) and the ref moves only after every object exists, so a crash leaves
the old tip or the new one, never half of one.

Dependency direction: adapter -> this module. It imports no scheduler or executor class: everything arrives as callables.
It reuses the integrator's `_git` so git is called the same safe way (no foreign GIT_DIR, fixed identity, no hooks).
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bt_scheduler_integrator import SAFE, SHA, IntegrationError, _git

REF_PREFIX = "refs/m3/line"


@dataclass(frozen=True)
class Contribution:
    task: str
    attempt: str
    start_base: str
    snapshot: str


@dataclass(frozen=True)
class LineState:
    """`applied` are the tasks folded into `tip`, in order; `unresolved` maps a task that did not apply to its files."""
    role: str
    base: str
    tip: str
    applied: tuple[str, ...]
    unresolved: Mapping[str, tuple[str, ...]]


class Line:
    def __init__(self, *, plan, accepted: Callable[[], Mapping[str, str]], snapshot_of: Callable[[str], str | None],
                 repo_of: Callable[[str], Path | str | None], default_repository: str, identity: str,
                 base_of: Callable[[str], str] = lambda role: "HEAD",
                 start_base_of: Callable[[str], str | None] | None = None, ref_prefix: str = REF_PREFIX):
        """`accepted()` -> {task_id: accepted attempt id}; `snapshot_of(attempt)` -> its snapshot sha (None: no handoff).
        `base_of(role)` is where the run began (pinned under `<ref>-base` the first time, so a moving HEAD cannot shift the
        line). `start_base_of(attempt)` -> the commit that attempt started from; by default the snapshot's first parent."""
        self.plan, self.accepted, self.snapshot_of, self.repo_of = plan, accepted, snapshot_of, repo_of
        self.default, self.identity = default_repository, SAFE.sub("-", identity) or "run"
        self.base_of, self.start_base_of, self.ref_prefix = base_of, start_base_of, ref_prefix.rstrip("/")
        self._before_ref_update: Callable[[], None] | None = None          # test seam: a crash between objects and ref
        self._states: dict[str, tuple[Any, LineState]] = {}

    # ------------------------------------------------------------------------------------------------ public
    def roles(self) -> list[str]:
        seen: list[str] = []
        for tid in self.plan.ids():
            role = self._role(tid)
            if role not in seen:
                seen.append(role)
        return seen

    def ref(self, role: str) -> str:
        return f"{self.ref_prefix}/{self.identity}/{SAFE.sub('-', role)}"

    def contributions(self, role: str) -> list[Contribution]:
        """The accepted tasks of `role` that left a usable snapshot, in plan order (topological, deterministic)."""
        accepted, repo = dict(self.accepted()), self._repo(role)
        found: list[Contribution] = []
        for tid in self.plan.ids():
            attempt = accepted.get(tid)
            if not attempt or self._role(tid) != role:
                continue
            snapshot = self.snapshot_of(attempt)
            if not snapshot or not SHA.fullmatch(snapshot) or _missing(repo, snapshot):
                raise IntegrationError("PREDECESSOR_HANDOFF_MISSING", f"{tid} ({attempt}) was accepted but left no snapshot")
            start = (self.start_base_of(attempt) if self.start_base_of else None) or f"{snapshot}^1"
            resolved = _git(repo, "rev-parse", "--verify", "--quiet", f"{start}^{{commit}}", check=False)
            # no start base is only an error when the snapshot has to be merged (an empty handoff of a root commit is not)
            found.append(Contribution(tid, attempt, "" if resolved.returncode else resolved.stdout.strip(), snapshot))
        return found

    def state(self, role: str) -> LineState:
        """The line of `role` for the facts as they are now (computed in memory; nothing is written)."""
        key = (tuple(sorted(dict(self.accepted()).items())), role)
        cached = self._states.get(role)
        if cached and cached[0] == key:
            return cached[1]
        state = self._fold(role)
        self._states[role] = (key, state)
        return state

    def tip(self, role: str) -> str:
        return self.state(role).tip

    def needs_resolution(self, role: str) -> dict[str, tuple[str, ...]]:
        return dict(self.state(role).unresolved)

    def apply(self, role: str, task: str, attempt: str, snapshot: str, start_base: str | None = None) -> tuple[str, tuple[str, ...]]:
        """Would `task`'s candidate result apply on the current tip? -> (new tip commit, conflicting files). The candidate
        replaces any earlier contribution of the same task. Objects only, nothing is stored and no ref moves."""
        repo = self._repo(role)
        others = [c for c in self.contributions(role) if c.task != task]
        base = self._base(role, repo)
        tip, _, _ = self._replay(repo, base, [c for c in others if self._precedes(c.task, task)])
        start = start_base or f"{snapshot}^1"
        resolved = _git(repo, "rev-parse", "--verify", f"{start}^{{commit}}")
        merged, conflicts = self._apply_one(repo, tip, Contribution(task, attempt, resolved.stdout.strip(), snapshot))
        return merged or tip, conflicts

    def recompute(self, roles: list[str] | None = None) -> dict[str, LineState]:
        """Recompute every line from the persisted facts and move its ref. Idempotent; safe at owner start-up."""
        self._states.clear()
        done: dict[str, LineState] = {}
        for role in roles or self.roles():
            state = self.state(role)
            repo = self._repo(role)
            if self._before_ref_update:
                self._before_ref_update()
            _git(repo, "update-ref", self.ref(role), state.tip)
            done[role] = state
        return done

    # ------------------------------------------------------------------------------------------------ internals
    def _role(self, task_id: str) -> str:
        return self.plan.task(task_id).repository or self.default

    def _repo(self, role: str) -> Path:
        path = self.repo_of(role)
        if not path:
            raise IntegrationError("INTEGRATION_REPOSITORY", f"repository {role!r} is not registered")
        return Path(path)

    def _precedes(self, first: str, second: str) -> bool:
        ids = list(self.plan.ids())
        return ids.index(first) < ids.index(second)

    def _base(self, role: str, repo: Path) -> str:
        pin = f"{self.ref(role)}-base"
        pinned = _git(repo, "rev-parse", "--verify", "--quiet", f"{pin}^{{commit}}", check=False)
        if pinned.returncode == 0:
            return pinned.stdout.strip()
        sha = _git(repo, "rev-parse", "--verify", f"{self.base_of(role)}^{{commit}}").stdout.strip()
        _git(repo, "update-ref", pin, sha)
        return sha

    def _fold(self, role: str) -> LineState:
        repo = self._repo(role)
        base = self._base(role, repo)
        tip, applied, unresolved = self._replay(repo, base, self.contributions(role))
        return LineState(role, base, tip, tuple(applied), dict(unresolved))

    def _replay(self, repo: Path, base: str, contributions: list[Contribution]):
        tip, applied, unresolved = base, [], {}
        for item in contributions:
            merged, conflicts = self._apply_one(repo, tip, item)
            if conflicts:
                unresolved[item.task] = conflicts
            elif merged:
                tip = merged
                applied.append(item.task)
            else:
                applied.append(item.task)                  # already part of the tip: nothing to add
        return tip, applied, unresolved

    @staticmethod
    def _apply_one(repo: Path, tip: str, item: Contribution) -> tuple[str | None, tuple[str, ...]]:
        """(merged commit, ()) when it applies; (None, ()) when the tip already holds it; (None, files) on a clash."""
        if item.snapshot == tip or _git(repo, "merge-base", "--is-ancestor", item.snapshot, tip, check=False).returncode == 0:
            return None, ()
        if not item.start_base:
            raise IntegrationError("PREDECESSOR_HANDOFF_MISSING", f"{item.task}: no start base for snapshot {item.snapshot[:12]}")
        done = _git(repo, "merge-tree", "--write-tree", "--name-only", "--no-messages", f"--merge-base={item.start_base}",
                    tip, item.snapshot, check=False)
        lines = done.stdout.splitlines()
        if done.returncode == 1:
            return None, tuple(line.strip() for line in lines[1:] if line.strip()) or ("?",)
        if done.returncode or not lines or not SHA.fullmatch(lines[0].strip()):
            raise IntegrationError("INTEGRATION_GIT", f"merge-tree for {item.task}: {(done.stderr or done.stdout).strip()[:300]}")
        merged = _git(repo, "commit-tree", "--no-gpg-sign", lines[0].strip(), "-p", tip, "-p", item.snapshot, "-m",
                      f"m3 line: {item.task}").stdout.strip()
        return merged, ()


def _missing(repo: Path, sha: str) -> bool:
    """True when the commit is not in the repository."""
    return _git(repo, "cat-file", "-e", f"{sha}^{{commit}}", check=False).returncode != 0
