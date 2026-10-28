"""Integrator port: one integration line per run and repository, advanced only by compare-and-swap.

`refs/bt/line/<project>/<req>/r<rev>/<repository>` starts at the repository's HEAD when the run starts. Integrating a
verified snapshot is a three-way `git merge-tree` of the line tip and the snapshot (git computes the merge base), written
as a merge commit, and an `update-ref <new> <old>` that fails if anyone moved the line in between (then the step is
retried on the new tip). A conflict never touches the line: it is returned as a fact for the classifier. This keeps
the invariant the legacy line could lose under concurrent writers (M0 finding 9): accepted work is never dropped.

Plan 1.3.0 subplans (REQ-030 item 1): each subplan has its own line, `refs/bt/subplan/<project>/<req>/r<rev>/<role>/<SP>`,
holding exactly the tasks the legacy `SubplanLineRouter` scopes (members plus their frozen-plan ancestors), started at
the run line's pinned base (`<run line>-base`). A member task starts from its subplan's line, a gate task from its
composition candidate (`adapters/composition.py`), and an accepted snapshot is merged, by the same compare-and-swap,
into the run line and every subplan line whose scope holds it — all merges are computed before any ref moves, so a
conflict in any line leaves every line as it was. `sync` seeds and catches up the subplan lines from the run's accepted
snapshots (the migration of a legacy run, a task accepted before its line existed); it is idempotent.
"""
from __future__ import annotations

import re
import subprocess
from collections.abc import Callable, Mapping
from pathlib import Path

from bt_contracts.execution import RunRef, Snapshot

from ..legacy import TaskSpec

IDENT = {"GIT_AUTHOR_NAME": "Bitacora Durable", "GIT_AUTHOR_EMAIL": "durable@localhost",
         "GIT_COMMITTER_NAME": "Bitacora Durable", "GIT_COMMITTER_EMAIL": "durable@localhost",
         "GIT_AUTHOR_DATE": "1700000000 +0000", "GIT_COMMITTER_DATE": "1700000000 +0000"}
_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


class LineMoved(RuntimeError):
    """The line advanced between read and write; the DBOS step retries on the new tip."""


def _git(repo: Path, *args: str, check: bool = True, env: Mapping[str, str] | None = None) -> subprocess.CompletedProcess:
    import os
    done = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", *args], cwd=str(repo), capture_output=True, text=True,
                          env={**os.environ, **(env or {})}, check=False)
    if check and done.returncode:
        raise RuntimeError(f"git {' '.join(args[:3])}: {done.stderr.strip()[:500]}")
    return done


class GitLineIntegrator:
    def __init__(self, repositories: Mapping[str, Path] | Callable[[str], Path | None], composer=None):
        self.repositories = repositories
        self.composer = composer                 # gate tasks start from a composition candidate (subplan runs only)

    def _repo(self, role: str) -> Path:
        path = self.repositories(role) if callable(self.repositories) else self.repositories.get(role)
        if path is None:
            raise RuntimeError(f"REPOSITORY_UNKNOWN: {role}")
        return Path(path)

    @staticmethod
    def line_ref(run: RunRef, role: str) -> str:
        return f"refs/bt/line/{_SAFE.sub('-', run.project)}/{run.req}/r{run.revision}/{_SAFE.sub('-', role or 'default')}"

    @staticmethod
    def subplan_ref(run: RunRef, role: str, subplan_id: str) -> str:
        return (f"refs/bt/subplan/{_SAFE.sub('-', run.project)}/{run.req}/r{run.revision}/"
                f"{_SAFE.sub('-', role or 'default')}/{_SAFE.sub('-', subplan_id)}")

    def _tip(self, repo: Path, ref: str) -> str:
        return _git(repo, "rev-parse", "-q", "--verify", f"{ref}^{{commit}}", check=False).stdout.strip()

    def line_base(self, run: RunRef, role: str) -> str:
        """Where the run line began (pinned when it was created). A line created before the pin existed has none: the
        operator pins it (`git update-ref <line>-base <commit>`) before subplan lines can be built from it."""
        base = self._tip(self._repo(role), self.line_ref(run, role) + "-base")
        if not base:
            raise RuntimeError(f"LINE_BASE_UNKNOWN: {self.line_ref(run, role)}-base is not pinned")
        return base

    def base_ref(self, run: RunRef, task: TaskSpec, *, home: str = "") -> str:
        """`home` (control.subplans.home): `gate:<CG>` -> the gate's composition candidate; `<SP>` -> that subplan's
        line once it exists; "" -> the run line."""
        repo = self._repo(task.repository)
        if home.startswith("gate:"):
            if self.composer is None:
                raise RuntimeError("GATE_UNSUPPORTED: no composition port is wired")
            return self.composer.candidate_commit(run, task, home.removeprefix("gate:"))
        if home:
            tip = self._tip(repo, self.subplan_ref(run, task.repository, home))
            if tip:
                return tip
        ref = self.line_ref(run, task.repository)
        tip = self._tip(repo, ref)
        if tip:
            return tip
        head = _git(repo, "rev-parse", "HEAD^{commit}").stdout.strip()
        # create-only: "" as the old value makes update-ref fail when another writer created the line first
        created = _git(repo, "update-ref", ref, head, "", check=False)
        if created.returncode:
            return _git(repo, "rev-parse", f"{ref}^{{commit}}").stdout.strip()
        _git(repo, "update-ref", ref + "-base", head, "", check=False)     # the pin subplan lines start from
        return head

    def _merge(self, repo: Path, tip: str, snapshot: str, message: str) -> tuple[str | None, str]:
        """(new tip or None when the snapshot is already in, conflict text). Objects only: no ref moves here."""
        if _git(repo, "merge-base", "--is-ancestor", snapshot, tip, check=False).returncode == 0:
            return None, ""                              # already integrated (a re-run of this step)
        if _git(repo, "merge-base", "--is-ancestor", tip, snapshot, check=False).returncode == 0:
            return snapshot, ""                          # fast-forward: the attempt already contains the whole line
        # git computes the merge base: a retry that continued from an earlier snapshot shares the line's history
        merged = _git(repo, "merge-tree", "--write-tree", tip, snapshot, check=False)
        if merged.returncode == 1:
            files = [line.split("\t", 1)[-1] for line in merged.stdout.splitlines()[1:] if "\t" in line]
            return None, "conflicts with accepted work in: " + ", ".join(sorted(set(files))[:20])
        if merged.returncode:
            raise RuntimeError(f"merge-tree failed: {merged.stderr.strip()[:300]}")
        tree = merged.stdout.splitlines()[0].strip()
        return _git(repo, "commit-tree", tree, "-p", tip, "-p", snapshot, "-m", message, env=IDENT).stdout.strip(), ""

    def integrate(self, run: RunRef, task: TaskSpec, snapshot: Snapshot, *,
                  lines: tuple[str, ...] = ()) -> tuple[str | None, str]:
        """Into the run line and the existing subplan lines named in `lines`; returns the run line's new tip."""
        if not snapshot.snapshot_sha:
            return None, "nothing to integrate: the attempt left no snapshot"
        repo = self._repo(task.repository)
        targets = [(self.line_ref(run, task.repository), self.base_ref(run, task), "")]
        for subplan_id in lines:
            ref = self.subplan_ref(run, task.repository, subplan_id)
            tip = self._tip(repo, ref)
            if tip:                                     # a line that does not exist yet is seeded by `sync`
                targets.append((ref, tip, subplan_id))
        moves = []
        for ref, tip, scope in targets:
            new, conflict = self._merge(repo, tip, snapshot.snapshot_sha,
                                        f"bt: integrate {task.id} into {run.run_id}" + (f" ({scope})" if scope else ""))
            if conflict:
                return None, conflict + (f" (line of {scope})" if scope else "")
            moves.append((ref, new or tip, tip))
        for ref, new, old in moves:
            if new != old and _git(repo, "update-ref", ref, new, old, check=False).returncode:
                raise LineMoved(f"{ref} moved while integrating {task.id}")
        return moves[0][1], ""

    def sync(self, run: RunRef, role: str, items: Mapping[str, list[tuple[str, str]]]) -> dict[str, dict]:
        """Seed/catch up each subplan line with its accepted snapshots `(task, snapshot)` in plan order. A snapshot
        that conflicts stays out and is reported (its own integration already proved it against its own line)."""
        repo = self._repo(role)
        report: dict[str, dict] = {}
        for subplan_id, entries in items.items():
            ref = self.subplan_ref(run, role, subplan_id)
            tip = self._tip(repo, ref)
            if not tip:
                base = self.line_base(run, role)
                created = _git(repo, "update-ref", ref, base, "", check=False)
                tip = base if created.returncode == 0 else self._tip(repo, ref)
            applied, conflicts = [], {}
            for task_id, snapshot in entries:
                new, conflict = self._merge(repo, tip, snapshot, f"bt: integrate {task_id} into {run.run_id} ({subplan_id})")
                if conflict:
                    conflicts[task_id] = conflict
                    continue
                if new:
                    if _git(repo, "update-ref", ref, new, tip, check=False).returncode:
                        raise LineMoved(f"{ref} moved while seeding {task_id}")
                    tip = new
                    applied.append(task_id)
            report[subplan_id] = {"tip": tip, "applied": applied, "conflicts": conflicts}
        return report
