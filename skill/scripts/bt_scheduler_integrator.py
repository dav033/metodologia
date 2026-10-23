"""Predecessor integrator: hands accepted prerequisite work to the tasks that come `after` it (P-031).

M3 starts every attempt in its own worktree from a `base_ref` and preserves the result as a snapshot commit
(`refs/m3/handoff/...`); nothing merges that snapshot anywhere, so without this a dependent task would start from the
repository HEAD and never see what its predecessors produced. `PredecessorIntegrator.base_ref(task_id)` closes that gap:

- it looks at every ancestor of the task (transitively) that lives in the same repository and was ACCEPTED by the core;
- it takes each one's handoff snapshot and merges them with `git merge-tree --write-tree` (objects only: no worktree, no
  index, the user's checkout is never touched) into one commit, kept alive under `refs/m3/integration/<run>/<task>`;
- it returns that commit's sha as the task's `base_ref`, so the executor pins it like any other base.

Honest failure, never a stale tree: an ancestor that was accepted but has no usable snapshot, or two predecessors whose
changes conflict, raise `IntegrationError`; the adapter turns it into a rejected order with that cause, so the task ends
blocked and says why instead of running against work it cannot see. Nothing here decides anything about acceptance.

Dependency direction: adapter -> this module. It imports no scheduler or executor class: everything arrives as callables.
"""
from __future__ import annotations

import fnmatch
import hashlib
import logging
import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

import bt_integration_invariant as invariant

IDENT = {"GIT_AUTHOR_NAME": "m3-integrator", "GIT_AUTHOR_EMAIL": "m3@localhost",
         "GIT_COMMITTER_NAME": "m3-integrator", "GIT_COMMITTER_EMAIL": "m3@localhost",
         # a fixed date makes the same parents give the same commit: a retried order sees the same base
         "GIT_AUTHOR_DATE": "1970-01-01T00:00:00+0000", "GIT_COMMITTER_DATE": "1970-01-01T00:00:00+0000"}
LOCATION_VARS = frozenset({"GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
                           "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_COMMON_DIR", "GIT_NAMESPACE", "GIT_PREFIX"})
LOGGER = logging.getLogger(__name__)
SHA = re.compile(r"[0-9a-f]{40,64}")
SAFE = re.compile(r"[^A-Za-z0-9._-]+")


# Causes that say something about the PLAN'S work (retrying cannot change them): the order is rejected with the cause.
# Anything else (git timeout, ref lock, signal, an unbound integrator) is transient and must be retried, not burn an attempt.
# PREDECESSOR_NEEDS_RESOLUTION (integration line) is permanent too: the scheduler has no "wait" for an order, and a transient
# error there leaves the attempt `uncertain` (a human decision about identity). Rejected with its cause, the task blocks
# and says which prerequisites do not fit the integrated tree.
PERMANENT = frozenset({"INTEGRATION_CONFLICT", "PREDECESSOR_NOT_ACCEPTED", "PREDECESSOR_HANDOFF_MISSING",
                       "INTEGRATION_REPOSITORY", "PREDECESSOR_NEEDS_RESOLUTION", "INTEGRATION_FILES_LOST",
                       "INTEGRATION_EVIDENCE_UNAVAILABLE"})


class IntegrationError(Exception):
    """The predecessors' work cannot be handed over; `code` is stable, `detail` is for the operator."""

    def __init__(self, code: str, detail: str = "", *, conflict_data: Mapping[str, Any] | None = None):
        self.code, self.detail = code, detail
        # Additive structured evidence; callers relying on code/detail and str(error) keep the old contract.
        self.conflict_data = _freeze(conflict_data) if conflict_data is not None else None
        super().__init__(f"{code}: {detail}" if detail else code)

    @property
    def permanent(self) -> bool:
        return self.code in PERMANENT


def _freeze(value):
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in LOCATION_VARS}      # never another repository's GIT_DIR
    env.update({**IDENT, "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C"})
    try:
        done = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-c", "gc.auto=0", "-c", "commit.gpgSign=false",
                               "-c", "tag.gpgSign=false", *args], cwd=str(repo),
                              env=env, capture_output=True, text=True, timeout=60, check=False)
    except (OSError, subprocess.SubprocessError) as error:
        raise IntegrationError("INTEGRATION_GIT", f"git {args[0]}: {type(error).__name__}") from None
    if check and done.returncode:
        raise IntegrationError("INTEGRATION_GIT", f"git {' '.join(args[:3])}: {(done.stderr or done.stdout).strip()[:300]}")
    return done


class PredecessorIntegrator:
    """Bind it once the run exists (`bind`), then use `base_ref` as the adapter's `base_ref` callable.

    `fallback` is what a task with nothing to integrate starts from (the adapter's own default, `HEAD`)."""

    def __init__(self, fallback: str | Callable[[str], str] = "HEAD", ref_prefix: str = "refs/m3/integration"):
        self.fallback, self.ref_prefix = fallback, ref_prefix.rstrip("/")
        self._bound: dict[str, Any] | None = None
        self._memo: dict[str, str] = {}
        self._announced: set[tuple[str, str, str, str]] = set()
        self.line = None                                   # bt_integration_line.Line when gates.integration_line is on
        self.check_files = True                            # gates.integration_check_files: the invariant of bt_integration_invariant

    def bind(self, *, plan, accepted: Callable[[], Mapping[str, str]], snapshot_of: Callable[[str], str | None],
             repo_of: Callable[[str], Path | str | None], default_repository: str, identity: str,
             earlier_of: Callable[[str], list[str]] | None = None,
             start_base_of: Callable[[str], str | None] | None = None,
             on_event: Callable[..., None] | None = None,
             on_conflict: Callable[..., None] | None = None,
             conflict_context: Callable[[str, str, Mapping[str, Any]], Mapping[str, Any]] | None = None,
             conflict_sink: Callable[[Mapping[str, Any]], str] | None = None) -> None:
        """`accepted()` -> {task_id: accepted attempt id} (read once per call); `snapshot_of(attempt_id)` -> its snapshot commit sha
        (None when the handoff has none; the sha of an EMPTY handoff is the base itself and merges as a no-op).
        `earlier_of(task_id)` -> the attempts whose accepted results an audit sent back, newest first: when a redone task
        clashes with a dependent that was built on its earlier result, that result is the merge base that tells the fix
        from the dependent's own work. `start_base_of(attempt)` -> the commit that attempt started from (default: the snapshot's
        first parent); `on_event(kind, **fields)` hears about every repair the invariant makes (`bt_interventions`);
        `on_conflict(task, left, right, files)` hears about every clash with ALL its paths, before any clipping (REQ-029 R11)."""
        self._bound = {"plan": plan, "accepted": accepted, "snapshot_of": snapshot_of, "repo_of": repo_of,
                       "default": default_repository, "identity": SAFE.sub("-", identity) or "run",
                       "earlier_of": earlier_of, "start_base_of": start_base_of, "on_event": on_event, "on_conflict": on_conflict,
                       "conflict_context": conflict_context, "conflict_sink": conflict_sink}

    def attach_line(self, line) -> None:
        """Make the integration line authoritative (REQ-028): new attempts start from its tip and acceptance is checked
        against it. Without a line (the default) everything below behaves exactly as before."""
        self.line = line

    def recompute_line(self) -> None:
        """Rebuild every line from the persisted facts and move its refs (owner start-up). Never raises: a run is not
        blocked by the line; the next call that needs it computes it again or falls back."""
        if self.line is None:
            return
        try:
            self.line.recompute()
        except IntegrationError as error:
            LOGGER.warning("integration line not recomputed (%s: %s)", error.code, str(error)[:240])

    # ------------------------------------------------------------------------------------------------ public
    def base_ref(self, task_id: str) -> str:
        if self._bound is None:
            raise IntegrationError("INTEGRATION_UNBOUND", "the integrator was not bound to a run")
        if task_id in self._memo and self._bootstrap_of(task_id) is not None:
            return self._memo[task_id]
        if self._bootstrap_of(task_id) is not None:                  # a convergence writer starts from the merge in progress, never the tip
            result = self._bootstrap_base(task_id)
            if result is not None:
                self._memo[task_id] = result
                return result
        if self.line is not None:
            tip = self._line_base(task_id)
            if tip is not None:
                return tip
        if task_id in self._memo:
            return self._memo[task_id]
        result = self._integrate(task_id)
        self._memo[task_id] = result
        return result

    def _bootstrap_of(self, task_id: str) -> dict | None:
        """The bootstrap a structural recovery froze into a convergence task (`bt_recovery_lineage`), else None."""
        try:
            meta = self._bound["plan"].task(task_id).meta
        except Exception:  # noqa: BLE001 - an unknown task has none
            return None
        boot = meta.get("bootstrap") if isinstance(meta, Mapping) and meta.get("recovery_task") is True else None
        parents = boot.get("parents") if isinstance(boot, Mapping) else None
        if (isinstance(boot, Mapping) and boot.get("required") is True and isinstance(parents, list) and len(parents) == 2
                and all(isinstance(p, str) and SHA.fullmatch(p) for p in parents)):
            return {"parents": list(parents), "owners": list(meta.get("recovery_owner_tasks") or [])}
        return None

    def _bootstrap_base(self, task_id: str) -> str | None:
        """The start of a convergence writer: what its own prerequisites hold, plus each accepted side's work measured from where
        THAT side started, as one commit that has both sides as parents. Where the two overlap the files hold git's conflict markers
        (a merge in progress) and the writer resolves them; `unresolved` refuses its result while any is left. None when git cannot
        build it (the writer then starts from the ordinary base, and the cycle's own checks refuse it)."""
        boot, bound = self._bootstrap_of(task_id), self._bound
        path = bound["repo_of"](self._role(task_id))
        if boot is None or not path:
            return None
        repo = Path(path)
        try:
            base = self._integrate(task_id, write_ref=False)
        except IntegrationError:
            return None
        accepted, snapshot_of, start_of = bound["accepted"](), bound["snapshot_of"], bound.get("start_base_of")
        current = base
        for parent in boot["parents"]:
            origin = None
            for owner in boot["owners"]:
                attempt = accepted.get(owner)
                if attempt and snapshot_of(attempt) == parent:
                    origin = (start_of(attempt) if start_of else None) or f"{parent}^1"
            origin = origin or f"{parent}^1"
            done = _git(repo, "merge-tree", "--write-tree", "--name-only", "--no-messages", f"--merge-base={origin}", current,
                        parent, check=False)
            lines = done.stdout.splitlines()
            if done.returncode not in (0, 1) or not lines or not SHA.fullmatch(lines[0].strip()):
                return None
            conflicts = done.returncode == 1
            current = _git(repo, "commit-tree", "--no-gpg-sign", lines[0].strip(), "-p", current, "-p", parent, "-m",
                           f"m3 bootstrap of {task_id}: {parent[:12]}" + (" (conflicts to resolve)" if conflicts else "")
                           ).stdout.strip()
        _git(repo, "update-ref", f"{self.ref_prefix}/{bound['identity']}/{self._ref_leaf(task_id)}-bootstrap", current)
        return current

    def ancestors(self, task_id: str) -> list[str]:
        """Every transitive predecessor of the task, in plan order (the deterministic merge order)."""
        plan = self._bound["plan"]
        seen: set[str] = set()
        stack = list(plan.task(task_id).after)
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(plan.task(current).after)
        return [tid for tid in plan.ids() if tid in seen]

    def rebase(self, task_id: str, snapshot: str, previous_base: str | None = None) -> str | None:
        """`carry` when the earlier result moves onto the new base cleanly; None when the two overlap."""
        commit, conflicts = self.carry(task_id, snapshot, previous_base)
        return None if conflicts else commit

    def carry(self, task_id: str, snapshot: str, previous_base: str | None = None) -> tuple[str | None, tuple[str, ...]]:
        """A task's own earlier result carried onto the base it would start from today: its new base (the redone
        prerequisites) plus what the earlier result added, as one commit that has both as parents. Objects only, like
        every other merge here; the commit is kept alive under `refs/m3/integration/<run>/<task>-carried`. What the earlier
        result added is measured from the base it was built on (`previous_base`; by default the snapshot's first parent).

        Returns (commit, conflicts). When the two overlap the commit still exists, as a merge in progress: the conflicted
        files hold git's `<<<<<<<` / `=======` / `>>>>>>>` markers (first side: the new base, second: the earlier result)
        and `conflicts` names them, so the task resolves them in place instead of redoing its work from nothing.
        (None, ()) when nothing can be carried."""
        bound = self._bound
        if bound is None or not SHA.fullmatch(snapshot or ""):
            return None, ()
        path = bound["repo_of"](self._role(task_id))
        if not path:
            return None, ()
        repo, base = Path(path), self.base_ref(task_id)
        if _git(repo, "cat-file", "-e", f"{snapshot}^{{commit}}", check=False).returncode:
            return None, ()
        resolved = _git(repo, "rev-parse", "--verify", f"{base}^{{commit}}", check=False)
        if resolved.returncode:
            return None, ()
        base = resolved.stdout.strip()
        if base == snapshot or _git(repo, "merge-base", "--is-ancestor", base, snapshot, check=False).returncode == 0:
            return snapshot, ()                               # the earlier result already builds on the new base
        origin = previous_base if SHA.fullmatch(previous_base or "") else f"{snapshot}^1"
        done = _git(repo, "merge-tree", "--write-tree", "--name-only", "--no-messages", f"--merge-base={origin}", base,
                    snapshot, check=False)
        if done.returncode not in (0, 1):
            return None, ()
        lines = done.stdout.splitlines()
        if not lines or not SHA.fullmatch(lines[0].strip()):
            return None, ()
        conflicts = tuple(line.strip() for line in lines[1:] if line.strip()) if done.returncode else ()
        message = f"m3 carried result of {task_id} onto its new base" + (" (conflicts to resolve)" if conflicts else "")
        carried = _git(repo, "commit-tree", "--no-gpg-sign", lines[0].strip(), "-p", base, "-p", snapshot, "-m",
                       message).stdout.strip()
        _git(repo, "update-ref", f"{self.ref_prefix}/{bound['identity']}/{self._ref_leaf(task_id)}-carried", carried)
        return carried, conflicts

    def unresolved(self, task_id: str, snapshot: str) -> tuple[str, ...]:
        """Files of `snapshot` that still hold merge conflict markers a carried base put there and the repository's own
        head does not: a task that was handed a merge in progress must not hand it back unresolved."""
        bound = self._bound
        path = bound["repo_of"](self._role(task_id)) if bound is not None and SHA.fullmatch(snapshot or "") else None
        if not path:
            return ()
        repo = Path(path)
        pattern = ("-e", "^<<<<<<< ", "-e", "^>>>>>>> ")
        found = _git(repo, "grep", "-lI", "-E", *pattern, snapshot, "--", check=False)
        if found.returncode:
            return ()
        files = {line.split(":", 1)[1] for line in found.stdout.splitlines() if ":" in line}
        known = _git(repo, "grep", "-lI", "-E", *pattern, "HEAD", "--", check=False)
        files -= {line.split(":", 1)[1] for line in known.stdout.splitlines() if ":" in line}
        return tuple(sorted(files))

    def reverted(self, task_id: str, snapshot: str, depth: int = 40, limit: int = 200,
                 base: str | None = None) -> tuple[str, ...]:
        """Files the result changed BACK to an older version of themselves than the one it started from (`base`, the
        trusted start of the attempt; the first parent of the snapshot when not given), outside the files the task
        declares. An attempt that continues from an earlier snapshot starts from that snapshot, not from `snapshot^1`
        (REQ-027 T17: a no-change attempt was rejected for a file its predecessor had already resolved). A task that resolves a merge by taking the stale
        side hands every later merge a regression: REQ-027's T15f carried the old `bt_remote_edit.py` (57 lines) over
        T8a's fix (103 lines), so the fix never reached the tasks built after it and the audit found it five rounds."""
        bound = self._bound
        path = bound["repo_of"](self._role(task_id)) if bound is not None and SHA.fullmatch(snapshot or "") else None
        if not path:
            return ()
        repo = Path(path)
        parent = base if base and SHA.fullmatch(base) else f"{snapshot}^1"
        diff = _git(repo, "diff", "--name-only", "--no-renames", parent, snapshot, check=False)
        if diff.returncode:
            return ()
        try:
            declared = tuple(bound["plan"].task(task_id).expected_paths or ())
        except Exception:  # noqa: BLE001 - no declared paths known: every changed file counts
            declared = ()
        found = []
        for name in diff.stdout.splitlines()[:limit]:
            if any(fnmatch.fnmatch(name, pattern) or name == pattern for pattern in declared):
                continue
            new = _git(repo, "rev-parse", "--verify", f"{snapshot}:{name}", check=False)
            now = _git(repo, "rev-parse", "--verify", f"{parent}:{name}", check=False)
            if new.returncode or now.returncode or new.stdout.strip() == now.stdout.strip():
                continue                                   # deleted, brand new or unchanged: not a revert
            history = _git(repo, "log", f"-n{depth}", "--format=%H", parent, "--", name, check=False)
            earlier = set()
            for commit in history.stdout.split()[1:]:       # the newest one made the version it started from
                blob = _git(repo, "rev-parse", "--verify", f"{commit}:{name}", check=False)
                if blob.returncode == 0:
                    earlier.add(blob.stdout.strip())
            if new.stdout.strip() in earlier:
                found.append(name)
        return tuple(found)

    # ------------------------------------------------------------------------------------------------ internals
    @staticmethod
    def _ref_leaf(task_id: str) -> str:
        """A valid, collision-free ref component for any task id: a readable slug plus a hash of the exact id."""
        slug = re.sub(r"\.+", ".", SAFE.sub("-", task_id)).strip(".-")[:60] or "task"
        return f"{slug}-{hashlib.sha256(task_id.encode()).hexdigest()[:8]}"

    def _fallback(self, task_id: str) -> str:
        return self.fallback(task_id) if callable(self.fallback) else self.fallback

    def _role(self, task_id: str) -> str:
        return self._bound["plan"].task(task_id).repository or self._bound["default"]

    def would_conflict(self, task_id: str, attempt_id: str, snapshot: str) -> str:
        """Would accepting `attempt_id` (snapshot `snapshot`) for `task_id` leave the run unable to combine its work? The
        tasks after it that are about to start are integrated as if it were accepted (objects only: no ref, no memo). ''
        when everything still merges, else the clash (`T6+T10 vs T13 for T14: files`). Checked when the result is verified,
        so the task that caused a clash is the one sent back, not a bystander blocked later when it tries to start."""
        bound = self._bound
        if bound is None or not SHA.fullmatch(snapshot or ""):
            return ""
        gone = self._foreign_deletions(task_id, attempt_id, snapshot)
        if gone:
            return gone
        if self.line is not None:
            clash = self._line_conflict(task_id, attempt_id, snapshot)
            if clash is not None:
                return clash
        current = dict(bound["accepted"]())
        accepted = {**current, task_id: attempt_id}
        real = bound["snapshot_of"]
        overlay = lambda attempt: snapshot if attempt == attempt_id else real(attempt)      # noqa: E731
        role = self._role(task_id)
        before = current.get(task_id) or next(iter(bound["earlier_of"](task_id) if bound.get("earlier_of") else ()), None)
        for later in bound["plan"].ids():
            if later == task_id or self._role(later) != role or task_id not in self.ancestors(later):
                continue
            if any(parent not in accepted for parent in self.ancestors(later)):
                continue                                    # not about to start: some prerequisite is still open
            try:
                self._integrate(later, accepted, overlay, write_ref=False, source_type="integration_gate")
            except IntegrationError as error:
                if error.code == "INTEGRATION_EVIDENCE_UNAVAILABLE":
                    raise
                pair = error.detail.split(" for ")[0]
                if error.code != "INTEGRATION_CONFLICT" or task_id not in re.split(r"\+| vs ", pair):
                    continue                                # a clash the candidate takes no part in
                if before is not None and self._clashes_without(later, accepted, task_id, before):
                    continue                                # the same clash exists with its previous result: not its doing
                reference = error.conflict_data.get("evidence_ref") if error.conflict_data else None
                return f"{error.detail} | conflict evidence: {reference}" if reference else error.detail
        return self._clash_with_built_on(task_id, snapshot, accepted, overlay, current, before)

    def _foreign_deletions(self, task_id: str, attempt_id: str, snapshot: str) -> str:
        """'' or the cause: the candidate deletes files other accepted tasks left without declaring them in its
        `expected_paths` (an undeclared deletion is what loses work silently, so it is rejected, not repaired)."""
        bound = self._bound
        if not self.check_files:
            return ""
        role = self._role(task_id)
        path = bound["repo_of"](role)
        if not path:
            return ""
        repo = Path(path)
        accepted = {t: a for t, a in dict(bound["accepted"]()).items() if t != task_id and self._role(t) == role}
        rows = []
        for tid, attempt in accepted.items():
            sha = bound["snapshot_of"](attempt)
            if sha and SHA.fullmatch(sha):
                rows.append((tid, attempt, sha))
        mine = self._items(repo, [(task_id, attempt_id, snapshot)])[0]
        found = invariant.foreign_deletions(_git, repo, mine, self._items(repo, rows), self._declared, self.ancestors, self.line.is_generated if self.line else lambda _: False)
        if not found:
            return ""
        text = "; ".join(f"{owner}: {', '.join(names[:4])}" for owner, names in found.items())
        return f"INTEGRATION_FILES_LOST {task_id} deletes files of accepted tasks it does not declare ({text})"[:170]

    def _line_base(self, task_id: str) -> str | None:
        """The line's tip for a task that has same-repository prerequisites, without the task's own earlier result (a
        redo replaces it). None = use the predecessor merge (nothing to integrate, or the line cannot be computed)."""
        role = self._role(task_id)
        same_repo = [t for t in self.ancestors(task_id) if self._role(t) == role]
        if not same_repo:
            return None
        try:
            accepted = self._bound["accepted"]()
            for tid in same_repo:
                if tid not in accepted:
                    raise IntegrationError("PREDECESSOR_NOT_ACCEPTED", f"{tid} is a prerequisite of {task_id} but is not accepted")
            waiting = [tid for tid in same_repo if tid in self.line.needs_resolution(role)]
            if waiting:
                raise IntegrationError("PREDECESSOR_NEEDS_RESOLUTION",
                                       f"{', '.join(waiting)} is accepted but does not fit the integrated tree yet")
            tip = self.line.tip(role, without=task_id)
            self.line.recompute([role])
            return tip
        except IntegrationError as error:
            if error.code in ("PREDECESSOR_NOT_ACCEPTED", "PREDECESSOR_NEEDS_RESOLUTION"):
                raise
            LOGGER.warning("integration line unavailable for %s (%s): using the predecessor merge", task_id, error.code)
            return None

    def _line_conflict(self, task_id: str, attempt_id: str, snapshot: str) -> str | None:
        """'' when the candidate applies on the tip, the clash when it does not, None when the line cannot say."""
        role = self._role(task_id)
        try:
            _, conflicts = self.line.apply(role, task_id, attempt_id, snapshot)
        except IntegrationError as error:
            LOGGER.warning("integration line cannot check %s (%s: %s): using the predecessor check", task_id, error.code, str(error)[:240])
            return None
        return f"{task_id} vs line for {task_id}: {', '.join(conflicts[:6])}"[:170] if conflicts else ""

    def _clash_with_built_on(self, task_id: str, snapshot: str, accepted: dict, overlay, current: dict, before) -> str:
        """The candidate against each accepted task that comes after it. Such a task was built on the candidate's earlier
        result; nobody else combines the two until a task further down needs both, and then it is that bystander that
        blocks. The pair is merged here (with the earlier results as merge bases, like everywhere else)."""
        bound = self._bound
        role = self._role(task_id)
        path = bound["repo_of"](role)
        if not path:
            return ""
        repo = Path(path)
        for later in bound["plan"].ids():
            if later == task_id or self._role(later) != role or task_id not in self.ancestors(later) \
                    or later not in current:
                continue
            built = overlay(current[later])
            if not built or not SHA.fullmatch(built):
                continue
            owners = [*self.ancestors(later), task_id]
            try:
                self._merge(repo, later, [(task_id, snapshot), (later, built)], owners, overlay)
            except IntegrationError as error:
                if error.code != "INTEGRATION_CONFLICT":
                    continue
                old = overlay(before) if before is not None else None
                if old and SHA.fullmatch(old):
                    try:
                        self._merge(repo, later, [(task_id, old), (later, built)], owners, overlay)
                    except IntegrationError as again:
                        if again.code == "INTEGRATION_CONFLICT":
                            continue                # it clashed with the previous result too: not this one's doing
                self._publish_conflict(task_id, "integration_gate", error)
                if error.conflict_data.get("evidence_unavailable"):
                    raise IntegrationError("INTEGRATION_EVIDENCE_UNAVAILABLE",
                                           "evidence_unavailable: integration conflict could not be published",
                                           conflict_data=error.conflict_data) from None
                reference = error.conflict_data.get("evidence_ref") if error.conflict_data else None
                return f"{error.detail} | conflict evidence: {reference}" if reference else error.detail
        return ""

    def _clashes_without(self, later: str, accepted: dict, task_id: str, before_attempt: str) -> bool:
        """Does `later` clash even with the candidate's previous result (or the accepted result it replaces)?"""
        try:
            self._integrate(later, {**accepted, task_id: before_attempt}, None, write_ref=False,
                            source_type="diagnostic")
        except IntegrationError as error:
            return error.code == "INTEGRATION_CONFLICT"
        return False

    def _integrate(self, task_id: str, accepted_map=None, snapshot_of=None, *, write_ref: bool = True,
                   source_type: str = "start") -> str:
        bound = self._bound
        role = self._role(task_id)
        same_repo = [t for t in self.ancestors(task_id) if self._role(t) == role]
        if not same_repo:
            return self._fallback(task_id)
        path = bound["repo_of"](role)
        if not path:
            raise IntegrationError("INTEGRATION_REPOSITORY", f"repository {role!r} is not registered")
        repo = Path(path)
        commits: list[tuple[str, str]] = []
        accepted = accepted_map if accepted_map is not None else bound["accepted"]()
        snapshot_of = snapshot_of or bound["snapshot_of"]
        for tid in same_repo:
            attempt = accepted.get(tid)
            if not attempt:
                raise IntegrationError("PREDECESSOR_NOT_ACCEPTED", f"{tid} is a prerequisite of {task_id} but is not accepted")
            sha = snapshot_of(attempt)
            if not sha or not SHA.fullmatch(sha):
                raise IntegrationError("PREDECESSOR_HANDOFF_MISSING",
                                       f"{tid} ({attempt}) was accepted but left no snapshot to build on")
            if _git(repo, "cat-file", "-e", f"{sha}^{{commit}}", check=False).returncode:
                raise IntegrationError("PREDECESSOR_HANDOFF_MISSING", f"{tid}: snapshot {sha[:12]} is not in {repo.name}")
            commits.append((tid, sha))
        try:
            merged = self._merge(repo, task_id, commits, same_repo, snapshot_of)
        except IntegrationError as error:
            if error.code == "INTEGRATION_CONFLICT" and source_type != "diagnostic":
                self._publish_conflict(task_id, source_type, error)
                if source_type == "integration_gate" and error.conflict_data.get("evidence_unavailable"):
                    raise IntegrationError("INTEGRATION_EVIDENCE_UNAVAILABLE",
                                           "evidence_unavailable: integration conflict could not be published",
                                           conflict_data=error.conflict_data) from None
            raise
        merged = self._guarantee(repo, task_id, merged, self._items(repo, [(t, accepted[t], sha) for t, sha in commits]))
        if write_ref:
            ref = f"{self.ref_prefix}/{bound['identity']}/{self._ref_leaf(task_id)}"
            _git(repo, "update-ref", ref, merged)
        return merged

    def _items(self, repo: Path, rows: list[tuple[str, str, str]]) -> list[invariant.Item]:
        """(task, attempt, snapshot) -> the invariant's view: where each attempt started and what it left."""
        start_of = self._bound.get("start_base_of")
        items = []
        for tid, attempt, sha in rows:
            start = (start_of(attempt) if start_of else None) or f"{sha}^1"
            if not SHA.fullmatch(start):
                resolved = _git(repo, "rev-parse", "--verify", "--quiet", f"{start}^{{commit}}", check=False)
                start = resolved.stdout.strip() if resolved.returncode == 0 else ""
            items.append(invariant.Item(tid, start, sha))
        return items

    def _declared(self, task_id: str) -> tuple[str, ...]:
        try:
            return tuple(getattr(self._bound["plan"].task(task_id), "expected_paths", ()) or ())
        except Exception:  # noqa: BLE001 - an unknown task declares nothing
            return ()

    def _guarantee(self, repo: Path, task_id: str, merged: str, items: list[invariant.Item]) -> str:
        """No integrated tree silently loses an accepted task's file (`bt_integration_invariant`). A violation is repaired
        with the owner's own version, recorded, and the repaired commit is what the task starts from; a repair that does
        not hold is a stated error, never an incomplete tree."""
        if not self.check_files:
            return merged
        report = invariant.check(_git, repo, merged, items, self._declared, self.ancestors)
        if report.ok:
            return merged
        fixed = invariant.restore(_git, repo, merged, items, report)
        again = invariant.check(_git, repo, fixed, items, self._declared, self.ancestors) if fixed else report
        if not fixed or not again.ok:
            self._announce("integration_defect", task_id, report, "failed")
            raise IntegrationError("INTEGRATION_FILES_LOST", f"{task_id}: {report.describe()}"[:170])
        self._announce("integration_defect", task_id, report, "fixed")
        return _git(repo, "commit-tree", "--no-gpg-sign", fixed, "-p", merged, "-m",
                    f"m3 integration repair for {task_id}: restored {report.describe(3)}"[:200]).stdout.strip()

    def _announce(self, kind: str, task_id: str, report, result: str) -> None:
        notify = self._bound.get("on_event")
        key = (kind, task_id, report.describe(50), result)
        if notify is None or key in self._announced:
            return
        self._announced.add(key)
        try:
            notify(kind, task=task_id, evidence=f"integrated tree for {task_id} lost files of accepted tasks: {report.describe()}",
                   repair="restored from the owners' snapshots" if result == "fixed" else "could not restore", result=result)
        except Exception:  # noqa: BLE001 - a listener never stops an integration
            LOGGER.debug("integration event listener failed", exc_info=True)

    def _publish_conflict(self, task_id: str, source_type: str, error: IntegrationError) -> None:
        bound = self._bound
        if bound is None or bound.get("conflict_context") is None or bound.get("conflict_sink") is None:
            return
        try:
            supplied = bound["conflict_context"](task_id, source_type, error.conflict_data or {})
            if not isinstance(supplied, Mapping) or not isinstance(supplied.get("source_records"), Mapping):
                raise ValueError("trusted conflict source context is incomplete")
            from bt_recovery_conflicts import collect_conflict_evidence
            observation = collect_conflict_evidence(supplied["source_records"], source_type=source_type,
                                                    conflict=supplied.get("conflict", error.conflict_data or {}))
            reference = bound["conflict_sink"](observation)
            if not isinstance(reference, str) or not reference:
                raise ValueError("conflict evidence sink returned no reference")
        except Exception as cause:  # noqa: BLE001 - failure to publish must be visible and block automated repair
            raise IntegrationError("INTEGRATION_EVIDENCE_UNAVAILABLE",
                                   f"evidence_unavailable: conflict publication failed ({type(cause).__name__})",
                                   conflict_data={"source_type": source_type, "task_id": task_id}) from None
        # Keep the historical code/detail but make the trusted evidence reference available to the rejection boundary.
        error.conflict_data = _freeze({**dict(error.conflict_data or {}), "evidence_ref": reference,
                                       "observation": observation})

    def _merge(self, repo: Path, task_id: str, commits: list[tuple[str, str]], owners=(), snapshot_of=None) -> str:
        def contains(ancestor: str, descendant: str) -> bool:
            return _git(repo, "merge-base", "--is-ancestor", ancestor, descendant, check=False).returncode == 0

        maximal = [(t, c) for t, c in commits if not any(c != o and contains(c, o) for _, o in commits)]
        seen: set[str] = set()
        commits = [(t, c) for t, c in maximal if not (c in seen or seen.add(c))]      # drop what another snapshot already holds
        current_task, current = commits[0]
        members = [current_task]                           # the tasks whose work `current` holds
        ancestry: list[str] = []                           # earlier results a side was built on (REQ-029 G4: carry ancestry)
        for tid, sha in commits[1:]:
            if sha == current or contains(sha, current):
                continue                                    # already part of what we have
            if contains(current, sha):
                current_task, current, members = tid, sha, [tid]   # the new one builds on the old: just move forward
                continue
            done = _git(repo, "merge-tree", "--write-tree", "--name-only", "--no-messages", current, sha, check=False)
            if done.returncode == 1:
                done = self._merge_over_earlier_result(repo, contains, current, sha, owners, snapshot_of, ancestry) or done
            if done.returncode == 1:
                files = tuple(sorted(set(line.strip() for line in done.stdout.splitlines()[1:] if line.strip())))
                # Keep the historical operator string bounded, but attach the exact merge-tree result first.
                merge_base = _git(repo, "merge-base", current, sha).stdout.strip()
                heard = (self._bound or {}).get("on_conflict")
                if heard is not None:
                    try:
                        heard(task=task_id, left=current_task, right=tid, files=list(files))
                    except Exception:  # noqa: BLE001 - the record is best effort; the clash itself is raised below
                        pass
                conflict_data = {"task_id": task_id, "sides": ((current_task, current), (tid, sha)),
                                 "paths": files, "merge_base": merge_base,
                                 "trees": (done.stdout.splitlines()[0].strip(),),
                                 "carry_ancestry": tuple(sorted({hashlib.sha256(prior.encode()).hexdigest()
                                                                 for prior in ancestry}))[:128]}
                detail = f"{current_task} vs {tid} for {task_id}: {', '.join(files)}"
                raise IntegrationError("INTEGRATION_CONFLICT", detail[:170], conflict_data=conflict_data)
            if done.returncode:
                raise IntegrationError("INTEGRATION_GIT", f"merge-tree: {(done.stderr or done.stdout).strip()[:300]}")
            tree = self._keep_newer_versions(repo, done.stdout.splitlines()[0].strip(), current, sha)
            current = _git(repo, "commit-tree", "--no-gpg-sign", tree, "-p", current, "-p", sha, "-m",
                           f"m3 integration of {current_task} + {tid} for {task_id}").stdout.strip()
            current_task = f"{current_task}+{tid}"
            members.append(tid)
        return current

    def _keep_newer_versions(self, repo: Path, tree: str, a: str, b: str, depth: int = 40, limit: int = 400) -> str:
        """A clean merge can still lose a fix. Snapshots are whole trees, so a stale one (built before a redo) carries
        the old content of files it never touched; merged over the git ancestor, "the stale side removed what the
        ancestor had, the new side left it alone" resolves to the removal. REQ-027's T18 audit found the same fixes
        open five rounds running: `/challenges` (T5b) and `bt_remote_edit.py` (T8a, 108 -> 47 lines) vanished that way.
        A file whose merged content is exactly one side's, while that content is an older version already in the
        other side's history, takes the other side's (newer) version. A real divergence (merged equals neither side)
        is never touched. Any git trouble returns the merged tree unchanged."""
        diff = _git(repo, "diff", "--name-only", "--no-renames", a, b, check=False)
        if diff.returncode:
            return tree
        fixes: dict[str, str] = {}
        for name in diff.stdout.splitlines()[:limit]:
            blobs = {}
            for key, ref in (("a", a), ("b", b), ("m", tree)):
                got = _git(repo, "rev-parse", "--verify", f"{ref}:{name}", check=False)
                blobs[key] = got.stdout.strip() if got.returncode == 0 else None
            if not (blobs["a"] and blobs["b"] and blobs["m"]) or blobs["a"] == blobs["b"]:
                continue
            for loser, winner in (("b", "a"), ("a", "b")):
                if blobs["m"] != blobs[loser]:
                    continue
                other = a if winner == "a" else b
                history = _git(repo, "log", f"-n{depth}", "--format=%H", other, "--", name, check=False)
                older = set()
                for commit in history.stdout.split()[1:]:
                    got = _git(repo, "rev-parse", "--verify", f"{commit}:{name}", check=False)
                    if got.returncode == 0:
                        older.add(got.stdout.strip())
                if blobs[loser] in older:
                    fixes[name] = blobs[winner]
                break
        if not fixes:
            return tree
        index = Path(tempfile.mkdtemp(prefix="m3-keepnewer-")) / "index"
        try:
            env = {**os.environ, "GIT_INDEX_FILE": str(index)}
            read = subprocess.run(["git", "-C", str(repo), "read-tree", tree], env=env, capture_output=True, text=True)
            if read.returncode:
                return tree
            for name, blob in fixes.items():
                mode = _git(repo, "ls-tree", a if blob == _git(repo, "rev-parse", f"{a}:{name}", check=False).stdout.strip() else b,
                            "--", name, check=False).stdout.split()
                if not mode:
                    return tree
                upd = subprocess.run(["git", "-C", str(repo), "update-index", "--cacheinfo", f"{mode[0]},{blob},{name}"],
                                     env=env, capture_output=True, text=True)
                if upd.returncode:
                    return tree
            written = subprocess.run(["git", "-C", str(repo), "write-tree"], env=env, capture_output=True, text=True)
            return written.stdout.strip() if written.returncode == 0 and written.stdout.strip() else tree
        finally:
            shutil.rmtree(index.parent, ignore_errors=True)

    def _merge_over_earlier_result(self, repo: Path, contains, current: str, sha: str, owners, snapshot_of,
                                   ancestry: list[str] | None = None):
        """A clash can be a redone task meeting work built on the result it replaced: both then changed the same lines of
        that earlier result. Any prerequisite of the task being integrated may be the redone one, so each earlier result
        of each of them is tried as the merge base, when one side was built on it. Merging over it keeps the fix and
        the other side's own work (a real overlap still conflicts). Returns the clean merge-tree outcome, or None."""
        earlier_of = self._bound.get("earlier_of")
        if earlier_of is None:
            return None
        resolve = snapshot_of or self._bound["snapshot_of"]
        newest: list[str] = []                              # per prerequisite, the earlier result a side was built on
        for owner in owners:
            for attempt in earlier_of(owner):
                prior = resolve(attempt)
                if not prior or not SHA.fullmatch(prior) or not (contains(prior, current) or contains(prior, sha)):
                    continue
                if prior not in newest:
                    newest.append(prior)
                    if ancestry is not None:
                        ancestry.append(prior)
                done = _git(repo, "merge-tree", "--write-tree", "--name-only", "--no-messages", f"--merge-base={prior}",
                            current, sha, check=False)
                if done.returncode == 0:
                    return done
                break                                       # older results of the same prerequisite are not what a side holds
        for built_on in (f"{sha}^1", f"{current}^1"):      # several were redone: the base a side was itself built on
            done = _git(repo, "merge-tree", "--write-tree", "--name-only", "--no-messages", f"--merge-base={built_on}",
                        current, sha, check=False)
            if done.returncode == 0:
                return done
        return None
