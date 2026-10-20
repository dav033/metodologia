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

import hashlib
import os
import re
import subprocess
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

IDENT = {"GIT_AUTHOR_NAME": "m3-integrator", "GIT_AUTHOR_EMAIL": "m3@localhost",
         "GIT_COMMITTER_NAME": "m3-integrator", "GIT_COMMITTER_EMAIL": "m3@localhost",
         # a fixed date makes the same parents give the same commit: a retried order sees the same base
         "GIT_AUTHOR_DATE": "1970-01-01T00:00:00+0000", "GIT_COMMITTER_DATE": "1970-01-01T00:00:00+0000"}
LOCATION_VARS = frozenset({"GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
                           "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_COMMON_DIR", "GIT_NAMESPACE", "GIT_PREFIX"})
SHA = re.compile(r"[0-9a-f]{40,64}")
SAFE = re.compile(r"[^A-Za-z0-9._-]+")


# Causes that say something about the PLAN'S work (retrying cannot change them): the order is rejected with the cause.
# Anything else (git timeout, ref lock, signal, an unbound integrator) is transient and must be retried, not burn an attempt.
PERMANENT = frozenset({"INTEGRATION_CONFLICT", "PREDECESSOR_NOT_ACCEPTED", "PREDECESSOR_HANDOFF_MISSING",
                       "INTEGRATION_REPOSITORY"})


class IntegrationError(Exception):
    """The predecessors' work cannot be handed over; `code` is stable, `detail` is for the operator."""

    def __init__(self, code: str, detail: str = ""):
        self.code, self.detail = code, detail
        super().__init__(f"{code}: {detail}" if detail else code)

    @property
    def permanent(self) -> bool:
        return self.code in PERMANENT


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

    def bind(self, *, plan, accepted: Callable[[], Mapping[str, str]], snapshot_of: Callable[[str], str | None],
             repo_of: Callable[[str], Path | str | None], default_repository: str, identity: str,
             earlier_of: Callable[[str], list[str]] | None = None) -> None:
        """`accepted()` -> {task_id: accepted attempt id} (read once per call); `snapshot_of(attempt_id)` -> its snapshot commit sha
        (None when the handoff has none; the sha of an EMPTY handoff is the base itself and merges as a no-op).
        `earlier_of(task_id)` -> the attempts whose accepted results an audit sent back, newest first: when a redone task
        clashes with a dependent that was built on its earlier result, that result is the merge base that tells the fix
        from the dependent's own work."""
        self._bound = {"plan": plan, "accepted": accepted, "snapshot_of": snapshot_of, "repo_of": repo_of,
                       "default": default_repository, "identity": SAFE.sub("-", identity) or "run",
                       "earlier_of": earlier_of}

    # ------------------------------------------------------------------------------------------------ public
    def base_ref(self, task_id: str) -> str:
        if self._bound is None:
            raise IntegrationError("INTEGRATION_UNBOUND", "the integrator was not bound to a run")
        if task_id in self._memo:
            return self._memo[task_id]
        result = self._integrate(task_id)
        self._memo[task_id] = result
        return result

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
        """A task's own earlier result carried onto the base it would start from today: its new base (the redone
        prerequisites) plus what the earlier result added, as one commit that has both as parents. None when the two
        overlap (the caller then starts on the new base and shows the earlier result as a reference). Objects only, like
        every other merge here; the commit is kept alive under `refs/m3/integration/<run>/<task>-carried`. What the earlier
        result added is measured from the base it was built on (`previous_base`; by default the snapshot's first parent)."""
        bound = self._bound
        if bound is None or not SHA.fullmatch(snapshot or ""):
            return None
        path = bound["repo_of"](self._role(task_id))
        if not path:
            return None
        repo, base = Path(path), self.base_ref(task_id)
        if _git(repo, "cat-file", "-e", f"{snapshot}^{{commit}}", check=False).returncode:
            return None
        resolved = _git(repo, "rev-parse", "--verify", f"{base}^{{commit}}", check=False)
        if resolved.returncode:
            return None
        base = resolved.stdout.strip()
        if base == snapshot or _git(repo, "merge-base", "--is-ancestor", base, snapshot, check=False).returncode == 0:
            return snapshot                                   # the earlier result already builds on the new base
        origin = previous_base if SHA.fullmatch(previous_base or "") else f"{snapshot}^1"
        done = _git(repo, "merge-tree", "--write-tree", "--name-only", "--no-messages", f"--merge-base={origin}", base,
                    snapshot, check=False)
        if done.returncode:
            return None
        tree = done.stdout.splitlines()[0].strip()
        carried = _git(repo, "commit-tree", "--no-gpg-sign", tree, "-p", base, "-p", snapshot, "-m",
                       f"m3 carried result of {task_id} onto its new base").stdout.strip()
        _git(repo, "update-ref", f"{self.ref_prefix}/{bound['identity']}/{self._ref_leaf(task_id)}-carried", carried)
        return carried

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
                self._integrate(later, accepted, overlay, write_ref=False)
            except IntegrationError as error:
                pair = error.detail.split(" for ")[0]
                if error.code != "INTEGRATION_CONFLICT" or task_id not in re.split(r"\+| vs ", pair):
                    continue                                # a clash the candidate takes no part in
                if before is not None and self._clashes_without(later, accepted, task_id, before):
                    continue                                # the same clash exists with its previous result: not its doing
                return error.detail
        return self._clash_with_built_on(task_id, snapshot, accepted, overlay, current, before)

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
                return error.detail
        return ""

    def _clashes_without(self, later: str, accepted: dict, task_id: str, before_attempt: str) -> bool:
        """Does `later` clash even with the candidate's previous result (or the accepted result it replaces)?"""
        try:
            self._integrate(later, {**accepted, task_id: before_attempt}, None, write_ref=False)
        except IntegrationError as error:
            return error.code == "INTEGRATION_CONFLICT"
        return False

    def _integrate(self, task_id: str, accepted_map=None, snapshot_of=None, *, write_ref: bool = True) -> str:
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
        merged = self._merge(repo, task_id, commits, same_repo, snapshot_of)
        if write_ref:
            ref = f"{self.ref_prefix}/{bound['identity']}/{self._ref_leaf(task_id)}"
            _git(repo, "update-ref", ref, merged)
        return merged

    def _merge(self, repo: Path, task_id: str, commits: list[tuple[str, str]], owners=(), snapshot_of=None) -> str:
        def contains(ancestor: str, descendant: str) -> bool:
            return _git(repo, "merge-base", "--is-ancestor", ancestor, descendant, check=False).returncode == 0

        maximal = [(t, c) for t, c in commits if not any(c != o and contains(c, o) for _, o in commits)]
        seen: set[str] = set()
        commits = [(t, c) for t, c in maximal if not (c in seen or seen.add(c))]      # drop what another snapshot already holds
        current_task, current = commits[0]
        members = [current_task]                           # the tasks whose work `current` holds
        for tid, sha in commits[1:]:
            if sha == current or contains(sha, current):
                continue                                    # already part of what we have
            if contains(current, sha):
                current_task, current, members = tid, sha, [tid]   # the new one builds on the old: just move forward
                continue
            done = _git(repo, "merge-tree", "--write-tree", "--name-only", "--no-messages", current, sha, check=False)
            if done.returncode == 1:
                done = self._merge_over_earlier_result(repo, contains, current, sha, owners, snapshot_of) or done
            if done.returncode == 1:
                files = [line for line in done.stdout.splitlines()[1:] if line.strip()][:6]
                raise IntegrationError("INTEGRATION_CONFLICT",       # the core keeps ~200 chars: who clashes comes first
                                       f"{current_task} vs {tid} for {task_id}: {', '.join(files)}"[:170])
            if done.returncode:
                raise IntegrationError("INTEGRATION_GIT", f"merge-tree: {(done.stderr or done.stdout).strip()[:300]}")
            tree = done.stdout.splitlines()[0].strip()
            current = _git(repo, "commit-tree", "--no-gpg-sign", tree, "-p", current, "-p", sha, "-m",
                           f"m3 integration of {current_task} + {tid} for {task_id}").stdout.strip()
            current_task = f"{current_task}+{tid}"
            members.append(tid)
        return current

    def _merge_over_earlier_result(self, repo: Path, contains, current: str, sha: str, owners, snapshot_of):
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
