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

import fnmatch
import os
import subprocess
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import bt_integration_invariant as invariant
from bt_scheduler_integrator import (
    IDENT,
    LOCATION_VARS,
    SAFE,
    SHA,
    IntegrationError,
    _git,
)

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
    generated_stale: tuple[str, ...] = ()


class ApplyResult(tuple):
    """Keep the historical `(tip, conflicts)` unpacking; expose stale output paths additively."""
    generated_stale: tuple[str, ...]

    def __new__(cls, tip: str, conflicts: tuple[str, ...], generated_stale: tuple[str, ...] = ()):
        result = super().__new__(cls, (tip, conflicts))
        result.generated_stale = generated_stale
        return result


class Line:
    def __init__(self, *, plan, accepted: Callable[[], Mapping[str, str]], snapshot_of: Callable[[str], str | None],
                 repo_of: Callable[[str], Path | str | None], default_repository: str, identity: str,
                 base_of: Callable[[str], str] = lambda role: "HEAD",
                 start_base_of: Callable[[str], str | None] | None = None, ref_prefix: str = REF_PREFIX,
                 on_event: Callable[..., None] | None = None, check_files: bool = True, scope_id: str = ""):
        """`accepted()` -> {task_id: accepted attempt id}; `snapshot_of(attempt)` -> its snapshot sha (None: no handoff).
        `base_of(role)` is where the run began (pinned under `<ref>-base` the first time, so a moving HEAD cannot shift the
        line). `start_base_of(attempt)` -> the commit that attempt started from; by default the snapshot's first parent."""
        self.plan, self.accepted, self.snapshot_of, self.repo_of = plan, accepted, snapshot_of, repo_of
        self.default, self.identity = default_repository, SAFE.sub("-", identity) or "run"
        self.base_of, self.start_base_of, self.ref_prefix = base_of, start_base_of, ref_prefix.rstrip("/")
        self.scope_id = SAFE.sub("-", scope_id).strip("-")
        self.on_event, self.check_files = on_event, check_files
        self._announced: set[tuple[str, str]] = set()
        self._before_ref_update: Callable[[], None] | None = None          # test seam: a crash between objects and ref
        self._states: dict[str, tuple[Any, LineState]] = {}

    # ------------------------------------------------------------------------------------------------ public
    def is_generated(self, path: str) -> bool:
        return any(fnmatch.fnmatchcase(path, pattern) for pattern in getattr(self.plan, "generated_paths", ()))

    def roles(self) -> list[str]:
        seen: list[str] = []
        for tid in self.plan.ids():
            role = self._role(tid)
            if role not in seen:
                seen.append(role)
        return seen

    def ref(self, role: str) -> str:
        suffix = f"/{self.scope_id}" if self.scope_id else ""
        return f"{self.ref_prefix}/{self.identity}/{SAFE.sub('-', role)}{suffix}"

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

    def tip(self, role: str, without: str | None = None) -> str:
        """The integrated tree; `without=T` leaves T's own contribution out (what a redo of T starts from)."""
        state = self.state(role)
        if without is None or without not in dict(self.accepted()):
            return state.tip
        repo = self._repo(role)
        return self._replay(repo, state.base, [c for c in self.contributions(role) if c.task != without])[0]

    def needs_resolution(self, role: str, task_id: str | None = None) -> dict[str, tuple[str, ...]]:
        return dict(self.state(role).unresolved)

    def apply(self, role: str, task: str, attempt: str, snapshot: str, start_base: str | None = None) -> ApplyResult:
        """Would `task`'s candidate result apply on the current tip? -> (new tip commit, conflicting files). The candidate
        replaces any earlier contribution of the same task. Objects only, nothing is stored and no ref moves."""
        repo = self._repo(role)
        state = self.state(role)
        if task in dict(self.accepted()):
            tip, _, _, inherited = self._replay(repo, state.base, [c for c in self.contributions(role) if c.task != task])
        else:
            tip, inherited = state.tip, state.generated_stale
        start = start_base or f"{snapshot}^1"
        resolved = _git(repo, "rev-parse", "--verify", f"{start}^{{commit}}")
        merged, conflicts, stale = self._apply_one(repo, tip, Contribution(task, attempt, resolved.stdout.strip(), snapshot))
        return ApplyResult(merged or tip, conflicts, tuple(sorted(set(inherited) | set(stale))))

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

    def _ancestors(self, task_id: str) -> set[str]:
        seen: set[str] = set()
        stack = list(self.plan.task(task_id).after)
        while stack:
            current = stack.pop()
            if current not in seen:
                seen.add(current)
                stack.extend(self.plan.task(current).after)
        return seen

    def _declared(self, task_id: str) -> tuple[str, ...]:
        return tuple(getattr(self.plan.task(task_id), "expected_paths", ()) or ())

    def _guard(self, repo: Path, tip: str, contributions: list[Contribution], applied: list[str], stale: set[str]) -> str:
        """The tip never silently loses a file an applied task left (`bt_integration_invariant`): what a fold dropped is
        put back from its owner, once, as one repair commit, and reported. A repair that does not hold leaves the tip as
        the fold produced it and the lost files are reported, so the consumer decides (nothing is guessed here)."""
        if not self.check_files or not applied:
            return tip
        items = [invariant.Item(c.task, c.start_base, c.snapshot) for c in contributions if c.task in applied and c.start_base]
        report = invariant.check(_git, repo, tip, items, self._declared, self._ancestors)
        if stale:
            report = invariant.Report(*({task: kept for task, names in group.items()
                                         if (kept := tuple(name for name in names if name not in stale))}
                                        for group in (report.lost, report.reverted)))
        if report.ok:
            return tip
        fixed = invariant.restore(_git, repo, tip, items, report)
        remaining = invariant.check(_git, repo, fixed, items, self._declared, self._ancestors) if fixed else report
        ok = bool(fixed) and all(name in stale for names in remaining.files().values() for name in names)
        self._announce(report, "fixed" if ok else "failed")
        if not ok:
            return tip
        return _git(repo, "commit-tree", "--no-gpg-sign", fixed, "-p", tip, "-m",
                    f"m3 line repair: restored {report.describe(3)}"[:200]).stdout.strip()

    def _announce(self, report, result: str) -> None:
        key = (report.describe(50), result)
        if self.on_event is None or key in self._announced:
            return
        self._announced.add(key)
        try:
            self.on_event("integration_defect", task=next(iter(report.files()), ""),
                          evidence=f"the integration line lost files of accepted tasks: {report.describe()}",
                          repair="restored from the owners' snapshots" if result == "fixed" else "could not restore", result=result)
        except Exception:  # noqa: BLE001 - a listener never stops the line
            pass

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
        tip, applied, unresolved, stale = self._replay(repo, base, self.contributions(role))
        return LineState(role, base, tip, tuple(applied), dict(unresolved), tuple(sorted(stale)))

    def _replay(self, repo: Path, base: str, contributions: list[Contribution]):
        tip, applied, unresolved, stale = base, [], {}, set()
        for item in contributions:
            merged, conflicts, taken = self._apply_one(repo, tip, item)
            if conflicts:
                unresolved[item.task] = conflicts
            elif merged:
                tip = merged
                applied.append(item.task)
                stale.update(taken)
            else:
                applied.append(item.task)                  # already part of the tip: nothing to add
        return self._guard(repo, tip, contributions, applied, stale), applied, unresolved, stale

    def _apply_one(self, repo: Path, tip: str, item: Contribution) -> tuple[str | None, tuple[str, ...], tuple[str, ...]]:
        """(merged commit or None, conflicts, generated paths taken from the candidate)."""
        if item.snapshot == tip or _git(repo, "merge-base", "--is-ancestor", item.snapshot, tip, check=False).returncode == 0:
            return None, (), ()
        if item.start_base == tip:
            return item.snapshot, (), ()                     # fast-forward: the same tree a merge would give, without the commit
        if not item.start_base:
            raise IntegrationError("PREDECESSOR_HANDOFF_MISSING", f"{item.task}: no start base for snapshot {item.snapshot[:12]}")
        if _git(repo, "merge-base", "--is-ancestor", tip, item.snapshot, check=False).returncode == 0:
            # The snapshot already holds everything the tip holds (a retry continues from the rejected attempt's snapshot: david-ui
            # REQ-001 T1 att-0004, whose start base the tip never had). A 3-way merge against that start base reads "the tip deleted
            # everything the snapshot still has" and yields an EMPTY tree without a clash: fast-forward, as for `start_base == tip`.
            return item.snapshot, (), ()
        patterns = tuple(getattr(self.plan, "generated_paths", ()) or ())
        output_flags = ("-z",) if patterns else ()
        base = _real_base(repo, item.start_base)
        done = _git(repo, "merge-tree", "--write-tree", "--name-only", "--no-messages", *output_flags, f"--merge-base={base}",
                    tip, item.snapshot, check=False)
        if done.returncode == 1:
            # An attempt that continued from an earlier one (a retry carries the rejected snapshot) started from a commit the
            # tip never held: its own work is then everything since the last commit the tip and it share. Tried second, so
            # a result that really clashes (REQ-027's stale T15f) is still reported, not merged over.
            common = _git(repo, "merge-base", item.start_base, tip, check=False)
            origin = common.stdout.strip()
            if common.returncode == 0 and SHA.fullmatch(origin) and origin != item.start_base:
                again = _git(repo, "merge-tree", "--write-tree", "--name-only", "--no-messages", *output_flags, f"--merge-base={origin}",
                             tip, item.snapshot, check=False)
                if again.returncode == 0:
                    done = again
        lines = done.stdout.split("\0") if patterns else done.stdout.splitlines()
        stale = ()
        if done.returncode == 1:
            conflicts = tuple(line for line in lines[1:] if line) if patterns else tuple(line.strip() for line in lines[1:] if line.strip())
            real = tuple(path for path in conflicts if not self.is_generated(path))
            if real or not conflicts:
                return None, real or ("?",), ()
            stale = conflicts
            lines[0] = _resolve_generated(repo, lines[0], item.snapshot, stale)
        if done.returncode not in (0, 1) or not lines or not SHA.fullmatch(lines[0].strip()):
            raise IntegrationError("INTEGRATION_GIT", f"merge-tree for {item.task}: {(done.stderr or done.stdout).strip()[:300]}")
        merged = _git(repo, "commit-tree", "--no-gpg-sign", lines[0].strip(), "-p", tip, "-p", item.snapshot, "-m",
                      f"m3 line: {item.task}").stdout.strip()
        return merged, (), stale


EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


def _resolve_generated(repo: Path, tree: str, snapshot: str, paths: tuple[str, ...]) -> str:
    with tempfile.TemporaryDirectory(prefix="m3-generated-") as scratch:
        env = {k: v for k, v in os.environ.items() if k not in LOCATION_VARS}
        env.update(IDENT, GIT_INDEX_FILE=str(Path(scratch) / "index"), GIT_LITERAL_PATHSPECS="1",
                   GIT_CONFIG_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0", LC_ALL="C")

        def run(*args: str) -> str:
            try:
                done = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-c", "gc.auto=0", "-C", str(repo), *args],
                                      env=env, capture_output=True, text=True, timeout=60, check=False)
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise IntegrationError("INTEGRATION_GIT", "generated resolution: " + type(exc).__name__) from exc
            if done.returncode:
                raise IntegrationError("INTEGRATION_GIT", "generated resolution: " + done.stderr.strip()[:300])
            return done.stdout

        run("read-tree", tree)
        for path in paths:
            entry = run("ls-tree", "-z", snapshot, "--", path).split("\0")[0]
            if not entry:
                run("update-index", "--force-remove", "--", path)
                continue
            meta, name = entry.split("\t", 1)
            mode, kind, blob = meta.split()
            if kind != "blob" or name != path:
                raise IntegrationError("INTEGRATION_GIT", "generated resolution requires a file: " + path)
            run("update-index", "--add", "--cacheinfo", f"{mode},{blob},{path}")
        return run("write-tree").strip()


def _real_base(repo: Path, base: str) -> str:
    """A start base whose tree is EMPTY while a parent's is not is a line commit an earlier bug built (david-ui REQ-001: `m3 line: T1`
    with no files). Attempts started from it did not start from nothing: read their work against the parent that holds the files."""
    if _git(repo, "rev-parse", f"{base}^{{tree}}", check=False).stdout.strip() != EMPTY_TREE:
        return base
    for number in (2, 1):
        parent = _git(repo, "rev-parse", "--verify", "--quiet", f"{base}^{number}", check=False)
        if parent.returncode == 0:
            sha = parent.stdout.strip()
            if SHA.fullmatch(sha) and _git(repo, "rev-parse", f"{sha}^{{tree}}", check=False).stdout.strip() != EMPTY_TREE:
                return sha
    return base


def _missing(repo: Path, sha: str) -> bool:
    """True when the commit is not in the repository."""
    return _git(repo, "cat-file", "-e", f"{sha}^{{commit}}", check=False).returncode != 0


def scoped_task_ids(plan, subplan_id: str) -> frozenset[str]:
    """Subplan members plus their frozen-plan ancestors; membership never comes from runtime state."""
    members = {task.id for task in plan.tasks if task.meta.get("subplan_id") == subplan_id}
    included = set(members)
    for task_id in members:
        included.update(plan.ancestors(task_id))
    return frozenset(included)


class SubplanLineRouter:
    """Route line operations to refs/m3/line/<run>/<role>/<SP-id> without changing legacy refs."""

    def __init__(self, *, plan, accepted: Callable[[], Mapping[str, str]], snapshot_of,
                 repo_of: Callable[[str], Path | str | None], default_repository: str, identity: str,
                 base_of, start_base_of=None, on_event=None, check_files: bool = True):
        self.plan = plan
        self.lines = {}
        self.members = {}
        all_accepted = accepted
        for subplan in plan.subplans:
            scope = scoped_task_ids(plan, subplan.id)
            self.members[subplan.id] = scope
            self.lines[subplan.id] = Line(
                plan=plan,
                accepted=lambda scope=scope: {task: attempt for task, attempt in all_accepted().items()
                                              if task in scope},
                snapshot_of=snapshot_of, repo_of=repo_of, default_repository=default_repository,
                identity=identity, base_of=base_of, start_base_of=start_base_of,
                on_event=on_event, check_files=check_files, scope_id=subplan.id)

    def _for_task(self, task_id: str | None):
        if not task_id:
            return None
        return self.lines.get(self.plan.task(task_id).meta.get("subplan_id"))

    def is_generated(self, path: str) -> bool:
        return any(line.is_generated(path) for line in self.lines.values())

    def roles(self) -> list[str]:
        found = []
        for subplan_id in self.lines:
            for task_id in {t.id for t in self.plan.tasks if t.meta.get("subplan_id") == subplan_id}:
                role = self.plan.task(task_id).repository or self.lines[subplan_id].default
                if role not in found:
                    found.append(role)
        return found

    def state(self, role: str) -> LineState:
        states = [line.state(role) for subplan_id, line in self.lines.items()
                  if any((self.plan.task(task).repository or line.default) == role
                         for task in {t.id for t in self.plan.tasks if t.meta.get("subplan_id") == subplan_id})]
        if not states:
            raise ValueError(f"no subplan line for repository role {role!r}")
        return LineState(role, states[0].base, states[0].tip,
                         tuple(task for state in states for task in state.applied),
                         {task: paths for state in states for task, paths in state.unresolved.items()},
                         tuple(path for state in states for path in state.generated_stale))

    def needs_resolution(self, role: str, task_id: str | None = None) -> dict[str, tuple[str, ...]]:
        line = self._for_task(task_id)
        if line:
            return line.needs_resolution(role)
        return {task: paths for candidate in self.lines.values()
                for task, paths in candidate.needs_resolution(role).items()}

    def tip(self, role: str, without: str | None = None):
        line = self._for_task(without)
        return line.tip(role, without=without) if line else None

    def apply(self, role: str, task: str, attempt: str, snapshot: str, start_base: str | None = None):
        line = self._for_task(task)
        if line is None:
            return snapshot, ()
        return line.apply(role, task, attempt, snapshot, start_base)

    def recompute(self, roles: list[str] | None = None):
        done = {}
        for subplan_id, line in self.lines.items():
            members = {t.id for t in self.plan.tasks if t.meta.get("subplan_id") == subplan_id}
            line_roles = list(dict.fromkeys(self.plan.task(t).repository or line.default for t in members))
            selected = [role for role in (roles or line_roles) if role in line_roles]
            for role, state in line.recompute(selected).items():
                done[(role, subplan_id)] = state
        return done
