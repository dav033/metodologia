"""Integrator port: one integration line per run and repository, advanced only by compare-and-swap.

`refs/bt/line/<project>/<req>/r<rev>/<repository>` starts at the repository's HEAD when the run starts. Integrating a
verified snapshot is a three-way `git merge-tree` of the line tip and the snapshot (git computes the merge base), written
as a merge commit, and an `update-ref <new> <old>` that fails if anyone moved the line in between (then the step is
retried on the new tip). A conflict never touches the line: it is returned as a fact for the classifier. This keeps
the invariant the legacy line could lose under concurrent writers (M0 finding 9): accepted work is never dropped.

Plan 1.3.0 subplans (REQ-030 item 1): each subplan has its own line, `refs/bt/subplan/<project>/<req>/r<rev>/<role>/<SP>`,
holding the tasks the legacy `SubplanLineRouter` scopes (members plus their frozen-plan ancestors; a migrated run's
legacy snapshots also bring their own history), started at the run line's pinned base (`<run line>-base`). A member
task starts from its subplan's line, a gate task from its composition candidate (`adapters/composition.py`), and an
accepted snapshot is merged, by the same compare-and-swap, into the run line and every subplan line whose scope holds
it — all merges are computed before any ref moves, and the moves are one `git update-ref --stdin` transaction, so a
conflict, or a writer that moved any of the lines in between, leaves every line as it was. `sync` seeds and catches
up the subplan lines from the run's accepted snapshots (the migration of a legacy run, a task accepted before its
line existed); it is idempotent.
"""
from __future__ import annotations

import logging
import re
import subprocess
from collections.abc import Callable, Mapping
from pathlib import Path

from bt_contracts.execution import RunRef, Snapshot

from ..legacy import TaskSpec

LOG = logging.getLogger("bt_durable.integration")
IDENT = {"GIT_AUTHOR_NAME": "Bitacora Durable", "GIT_AUTHOR_EMAIL": "durable@localhost",
         "GIT_COMMITTER_NAME": "Bitacora Durable", "GIT_COMMITTER_EMAIL": "durable@localhost",
         "GIT_AUTHOR_DATE": "1700000000 +0000", "GIT_COMMITTER_DATE": "1700000000 +0000"}
_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


class LineMoved(RuntimeError):
    """The line advanced between read and write; the DBOS step retries on the new tip."""


def _git(repo: Path, *args: str, check: bool = True, env: Mapping[str, str] | None = None,
         stdin: str | None = None) -> subprocess.CompletedProcess:
    import os
    done = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", *args], cwd=str(repo), capture_output=True, text=True,
                          env={**os.environ, **(env or {})}, check=False, input=stdin)
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

    def base_ref(self, run: RunRef, task: TaskSpec, *, home: str = "", lines: tuple[str, ...] = ()) -> str:
        """`home` (control.subplans.home): `gate:<CG>` -> the gate's composition candidate, caught up with the subplan
        `lines` its work will be integrated into; `<SP>` -> that subplan's line once it exists; "" -> the run line."""
        repo = self._repo(task.repository)
        if home.startswith("gate:"):
            if self.composer is None:
                raise RuntimeError("GATE_UNSUPPORTED: no composition port is wired")
            return self._caught_up(repo, run, task, self.composer.candidate_commit(run, task, home.removeprefix("gate:")),
                                   lines)
        if home:
            tip = self._tip(repo, self.subplan_ref(run, task.repository, home))
            if tip:
                return tip
        return self._run_line(run, task.repository)

    def _caught_up(self, repo: Path, run: RunRef, task: TaskSpec, candidate: str, lines: tuple[str, ...]) -> str:
        """The candidate with the newer work of each existing subplan line in `lines` merged in (objects only, the
        composer's settling rules); a line that conflicts with it is left out, and its conflict reaches the task at
        integration as before. The candidate is built from the members' registered versions, while the lines keep
        moving: pictures REQ-021 r25 gate T95 started six attempts from the same candidate and met, at integration, work
        T93 and SP-8 had put on the SP-7 and SP-8 lines since (D-173)."""
        tip = candidate
        for subplan_id in lines:
            line = self._tip(repo, self.subplan_ref(run, task.repository, subplan_id))
            if not line:
                continue
            new, conflict = self._merge(repo, tip, line, f"bt: {task.id} starts from {subplan_id}'s line")
            if conflict:
                LOG.info("%s: base left %s's line out (%s)", task.id, subplan_id, conflict[:200])
                continue
            tip = new or tip
        return tip

    def _run_line(self, run: RunRef, role: str) -> str:
        """The run line's tip, created at the repository's HEAD (and its base pinned) the first time it is needed."""
        repo, ref = self._repo(role), self.line_ref(run, role)
        tip = self._tip(repo, ref)
        if tip:
            return tip
        head = _git(repo, "rev-parse", "HEAD^{commit}").stdout.strip()
        # the line and its pin (where subplan lines start) in ONE create-only transaction: written by two update-refs,
        # a crash between them left a line without a pin, and every later sync reported LINE_BASE_UNKNOWN until an
        # operator pinned it by hand (audit of REQ-030, 2026-10-29). A writer that created the line first wins.
        script = f"start\ncreate {ref} {head}\ncreate {ref}-base {head}\nprepare\ncommit\n"
        if _git(repo, "update-ref", "--stdin", check=False, stdin=script).returncode:
            pin = self._tip(repo, ref + "-base")
            if not self._tip(repo, ref) and pin:          # a pin without its line: the line starts at the pin
                _git(repo, "update-ref", ref, pin, "", check=False)
            return _git(repo, "rev-parse", f"{ref}^{{commit}}").stdout.strip()
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
            if not files:                                # git failed without naming a conflicted file: not a conflict
                raise RuntimeError(f"merge-tree failed: {(merged.stderr or merged.stdout).strip()[:300]}")
            tree, files = self._settle(repo, tip, snapshot, files)
            if files:
                return None, "conflicts with accepted work in: " + ", ".join(sorted(set(files))[:20])
        elif merged.returncode:
            raise RuntimeError(f"merge-tree failed: {merged.stderr.strip()[:300]}")
        else:
            tree = merged.stdout.splitlines()[0].strip()
        return _git(repo, "commit-tree", tree, "-p", tip, "-p", snapshot, "-m", message, env=IDENT).stdout.strip(), ""

    def _settle(self, repo: Path, tip: str, snapshot: str, files: list[str]) -> tuple[str, list[str]]:
        """Settle the conflicts the composer settles (D-160) the same way on a line: `package.json` merged by key and
        the recorded resolutions in `<state>/composition/resolutions`. pictures REQ-021 r24: gate task T93, built on the
        composed CG-3 candidate, conflicted with SP-11's line on the npm scripts every subplan appends (D-164).
        A criss-cross history (several merge bases) is settled against a virtual base, as git's recursive merge does
        (D-169). Returns (tree, conflicts left); with no composer the conflicts stay as git found them."""
        bases = _git(repo, "merge-base", "--all", tip, snapshot, check=False).stdout.split()
        state_dir = getattr(self.composer, "state_dir", None)
        if not bases or state_dir is None:
            return "", files
        from bt_composition_adapter import GitSubprocessPort
        root = Path(state_dir) / "composition"
        port = GitSubprocessPort(repo, root / "ws")
        port.resolutions = root / "resolutions"
        if len(bases) == 1:
            base = bases[0]
        else:
            quiet = GitSubprocessPort(repo, root / "ws")
            quiet.resolutions, quiet.request_resolutions = root / "resolutions", False
            base = self._virtual_base(repo, quiet, bases)
        if not base:
            return "", files
        result = port.merge_tree(base, tip, snapshot)
        return result.tree, list(result.conflicts)

    def _virtual_base(self, repo: Path, port, bases: list[str], depth: int = 0) -> str:
        """The merge bases merged into one commit, recursively, like git's recursive strategy: package.json by key and the
        recorded resolutions, and a conflict left between bases keeps git's markers in the virtual base (a later merge of
        that file then conflicts). pictures REQ-021 r25: gate T93 and SP-7's line had both taken SP-3 and SP-4, three
        bases, and the same package.json conflict came back on every retry (D-169). `port` uses the recorded resolutions
        but asks for none: without them T95's virtual base kept SP-4 × SP-5's markers in dependientes.ts, already resolved
        for the composer, and conflicted with SP-8's line on every retry (D-174)."""
        if depth > 3:
            return ""
        merged = bases[0]
        for other in bases[1:]:
            inner = _git(repo, "merge-base", "--all", merged, other, check=False).stdout.split()
            base = inner[0] if len(inner) == 1 else self._virtual_base(repo, port, inner, depth + 1) if inner else ""
            if not base:
                return ""
            tree = port.merge_tree(base, merged, other).tree
            merged = _git(repo, "commit-tree", tree, "-p", merged, "-p", other, "-m", "bt: virtual merge base",
                          env=IDENT).stdout.strip()
        return merged

    def integrate(self, run: RunRef, task: TaskSpec, snapshot: Snapshot, *,
                  lines: tuple[str, ...] = ()) -> tuple[str | None, str, str]:
        """Into the run line and the existing subplan lines named in `lines`: (new tip, conflict, run-line note).

        A subplan member counts as integrated once its subplan lines take it, as in the legacy runtime, where the line of
        a 1.3.0 run IS the subplan router (`bt_integration_line.SubplanLineRouter`): work of different subplans meets at
        a composition gate. The run line takes the member too when it merges cleanly; when it does not (another subplan
        changed the same lines, pictures REQ-021 package.json), the member is still accepted and the run-line conflict
        is returned as a note: retrying could never fix it, the member starts from its own line every time."""
        if not snapshot.snapshot_sha:
            return None, "nothing to integrate: the attempt left no snapshot", ""
        repo = self._repo(task.repository)
        targets = [(self.line_ref(run, task.repository), self.base_ref(run, task), "")]
        for subplan_id in lines:
            ref = self.subplan_ref(run, task.repository, subplan_id)
            tip = self._tip(repo, ref)
            if tip:                                     # a line that does not exist yet is seeded by `sync`
                targets.append((ref, tip, subplan_id))
        moves, note = [], ""
        member = len(targets) > 1                       # at least one of its subplan lines exists
        for ref, tip, scope in targets:
            new, conflict = self._merge(repo, tip, snapshot.snapshot_sha,
                                        f"bt: integrate {task.id} into {run.run_id}" + (f" ({scope})" if scope else ""))
            if conflict and not scope and member:
                note = conflict                         # the run line only: left to the composition gates
                continue
            if conflict:
                return None, conflict + (f" (line of {scope})" if scope else ""), ""
            moves.append((ref, new or tip, tip))
        changed = [(ref, new, old) for ref, new, old in moves if new != old]
        if changed:                                     # all lines or none: each `update` checks its old value
            script = "start\n" + "".join(f"update {ref} {new} {old}\n" for ref, new, old in changed) + "prepare\ncommit\n"
            moved = _git(repo, "update-ref", "--stdin", check=False, stdin=script)
            if moved.returncode:
                raise LineMoved(f"{', '.join(ref for ref, _, _ in changed)} moved while integrating {task.id}: "
                                f"{moved.stderr.strip()[:300]}")
        return moves[0][1], "", note

    def sync(self, run: RunRef, role: str, items: Mapping[str, list[tuple[str, str]]]) -> dict[str, dict]:
        """Seed/catch up each subplan line with its accepted snapshots `(task, snapshot)` in plan order. A snapshot
        that conflicts stays out and is reported (its own integration already proved it against its own line)."""
        repo = self._repo(role)
        self._run_line(run, role)                       # a fresh run: the line and its base pin exist from here on
        report: dict[str, dict] = {}
        try:
            base = self.line_base(run, role)
        except RuntimeError as error:                   # a line made by an engine before the pin: the operator pins it
            return {"error": str(error)}
        for subplan_id, entries in items.items():
            ref = self.subplan_ref(run, role, subplan_id)
            tip = self._tip(repo, ref)
            if not tip:
                created = _git(repo, "update-ref", ref, base, "", check=False)
                tip = base if created.returncode == 0 else self._tip(repo, ref)
                if not tip:                              # e.g. a stale ref lock: never seed or merge on nothing
                    raise RuntimeError(f"SUBPLAN_LINE_UNWRITABLE: {ref}: {created.stderr.strip()[:300]}")
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
