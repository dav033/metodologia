"""Integrator port: one integration line per run and repository, advanced only by compare-and-swap.

`refs/bt/line/<project>/<req>/r<rev>/<repository>` starts at the repository's HEAD when the run starts. Integrating a
verified snapshot is a three-way `git merge-tree` of the line tip and the snapshot (git computes the merge base), written
as a merge commit, and an `update-ref <new> <old>` that fails if anyone moved the line in between (then the step is
retried on the new tip). A conflict never touches the line: it is returned as a fact for the classifier. This keeps
the invariant the legacy line could lose under concurrent writers (M0 finding 9): accepted work is never dropped.
"""
from __future__ import annotations

import re
import subprocess
from collections.abc import Callable, Mapping
from pathlib import Path

from bt_contracts.execution import RunRef, Snapshot
from bt_scheduler_core.plan import TaskSpec

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
    def __init__(self, repositories: Mapping[str, Path] | Callable[[str], Path | None]):
        self.repositories = repositories

    def _repo(self, role: str) -> Path:
        path = self.repositories(role) if callable(self.repositories) else self.repositories.get(role)
        if path is None:
            raise RuntimeError(f"REPOSITORY_UNKNOWN: {role}")
        return Path(path)

    @staticmethod
    def line_ref(run: RunRef, role: str) -> str:
        return f"refs/bt/line/{_SAFE.sub('-', run.project)}/{run.req}/r{run.revision}/{_SAFE.sub('-', role or 'default')}"

    def base_ref(self, run: RunRef, task: TaskSpec) -> str:
        repo, ref = self._repo(task.repository), self.line_ref(run, task.repository)
        tip = _git(repo, "rev-parse", "-q", "--verify", f"{ref}^{{commit}}", check=False).stdout.strip()
        if tip:
            return tip
        head = _git(repo, "rev-parse", "HEAD^{commit}").stdout.strip()
        # create-only: "" as the old value makes update-ref fail when another writer created the line first
        created = _git(repo, "update-ref", ref, head, "", check=False)
        if created.returncode:
            return _git(repo, "rev-parse", f"{ref}^{{commit}}").stdout.strip()
        return head

    def integrate(self, run: RunRef, task: TaskSpec, snapshot: Snapshot) -> tuple[str | None, str]:
        if not snapshot.snapshot_sha:
            return None, "nothing to integrate: the attempt left no snapshot"
        repo, ref = self._repo(task.repository), self.line_ref(run, task.repository)
        tip = self.base_ref(run, task)
        if _git(repo, "merge-base", "--is-ancestor", snapshot.snapshot_sha, tip, check=False).returncode == 0:
            return tip, ""                               # already integrated (a re-run of this step)
        if _git(repo, "merge-base", "--is-ancestor", tip, snapshot.snapshot_sha, check=False).returncode == 0:
            new = snapshot.snapshot_sha                  # fast-forward: the attempt already contains the whole line
        else:
            # git computes the merge base: a retry that continued from an earlier snapshot shares the line's history
            merged = _git(repo, "merge-tree", "--write-tree", tip, snapshot.snapshot_sha, check=False)
            if merged.returncode == 1:
                files = [line.split("\t", 1)[-1] for line in merged.stdout.splitlines()[1:] if "\t" in line]
                return None, "conflicts with accepted work in: " + ", ".join(sorted(set(files))[:20])
            if merged.returncode:
                raise RuntimeError(f"merge-tree failed: {merged.stderr.strip()[:300]}")
            tree = merged.stdout.splitlines()[0].strip()
            new = _git(repo, "commit-tree", tree, "-p", tip, "-p", snapshot.snapshot_sha, "-m",
                       f"bt: integrate {task.id} into {run.run_id}", env=IDENT).stdout.strip()
        moved = _git(repo, "update-ref", ref, new, tip, check=False)
        if moved.returncode:
            raise LineMoved(f"{ref} moved while integrating {task.id}")
        return new, ""
