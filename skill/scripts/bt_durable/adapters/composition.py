"""Composition port over the legacy composition engine (`bt_composition`, CONSERVAR): subplan versions and gate
candidates for plan 1.3.0 runs owned by the durable runtime (REQ-030 item 1).

When every member subplan of a composition gate is complete, the run workflow asks `compose`: each member's line tip is
published as an immutable subplan version (`refs/subplans/<plan>/<SP>/v<N>`, bound to its line base, its produced
contract hashes and the M6 verdicts of its accepted members), and the engine folds the member versions, in plan order,
into a candidate (`refs/compositions/<plan>/candidates/C<N>`); a text conflict between members is a rejected candidate,
never a guess. The gate task then starts from the candidate commit (`candidate_commit`, idempotent: the engine returns
the candidate it already built for the same members).

The engine's identifiers are namespaced (`<req>.bt-r<rev>`) and its store lives under the durable state directory, so
the legacy owner's composition store and refs for the same requirement are never touched. What is not ported: the
legacy owner publishes a composition only with an M6 proof bound to the candidate's exact tree; here the gate passes when
its gate task is accepted on a snapshot built on the candidate (the gate task's own test files make the trees differ).
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import threading
from collections.abc import Callable, Mapping
from pathlib import Path

from bt_contracts.execution import RunRef

from .. import reconcile
from ..legacy import Plan, TaskSpec, create_composition_engine

VERIFIER = "bt_durable"


class CompositionComposer:
    def __init__(self, state_dir: Path, *, lines, plan_for: Callable[[RunRef], Plan]):
        self.state_dir = Path(state_dir)
        self.lines = lines                       # the run's integrator: subplan line refs, tips and base
        self.plan_for = plan_for
        self._engines: dict[tuple[str, str], tuple] = {}
        self._lock = threading.Lock()

    @staticmethod
    def plan_id(run: RunRef) -> str:
        return f"{run.req}.bt-r{run.revision}"

    def _engine(self, run: RunRef, role: str):
        key = (run.run_id, role)
        with self._lock:
            if key not in self._engines:
                root = self.state_dir / "composition"
                root.mkdir(parents=True, exist_ok=True, mode=0o700)
                name = f"{run.project}-{run.req}-r{run.revision}-{role}"
                self._engines[key] = create_composition_engine(self.lines._repo(role), root / f"{name}.db",
                                                               root / "ws" / name)
            return self._engines[key]

    def close(self) -> None:
        for _engine, store in self._engines.values():
            store.close()
        self._engines.clear()

    def compose(self, run: RunRef, gate_id: str, evidence: Mapping[str, list[dict]]) -> dict:
        plan = self.plan_for(run)
        gate = next(item for item in plan.composition_gates if item.id == gate_id)
        role = plan.task(gate.task).repository
        engine, store = self._engine(run, role)
        repo = self.lines._repo(role)
        waiting = self._unreconciled(run, gate, role, repo)
        if waiting:
            return {"state": "rejected", "reason": f"{reconcile.PENDING}: {', '.join(waiting)}", "conflicts": {}}
        import bt_verification_tree as tree_rules
        resolutions = self.state_dir / "composition" / "resolutions"
        base = self.lines.line_base(run, role)
        built = [c for c in store.list_candidates(self.plan_id(run)) if c.state != "rejected" and c.integrated_commit]
        versions, previous = {}, ""
        for subplan_id in _composition_order(plan, gate):
            tip = self.lines._tip(repo, self.lines.subplan_ref(run, role, subplan_id))
            if not tip:
                return {"state": "rejected", "reason": f"SUBPLAN_LINE_MISSING: {subplan_id}"}
            # A subplan's line holds its scope: its members AND the frozen-plan tasks they depend on, so a later member
            # often contains an earlier one (pictures REQ-021: SP-2 ⊇ SP-1). Folded as a delta from the run line's
            # base, the shared work would be applied twice and conflict with itself; measured from its merge base with
            # the member folded just before it, a member brings only what it adds (the run line's base otherwise).
            # A line that holds the member before it, as a reconciled line does (D-297), adds only what it adds over that
            # member: measured from an older commit (an earlier candidate, its first snapshot) it would meet the newer
            # version of what it already combined, and an agent would settle the same clash again.
            own_base = ((previous if previous and tree_rules.holds(repo, tip, previous, resolutions) else "")
                        or _prior_candidate(repo, tip, built, set(versions))
                        or _own_work_base(repo, tip, evidence.get(subplan_id, ())) or _merge_base(repo, tip, previous)
                        or base)
            previous = tip
            items = [{"task_id": item["task_id"], "kind": item["kind"], "verdict_id": item["verdict_id"],
                      "tree_digest": _tree(repo, item.get("snapshot") or tip), "environment": VERIFIER}
                     for item in evidence.get(subplan_id, ())]
            version = engine.publish_subplan_version(self.plan_id(run), f"r{run.revision}:{run.plan_sha256}",
                                                     subplan_id, tip, own_base,
                                                     self._contracts(plan, subplan_id, repo, tip), items)
            versions[subplan_id] = version.version
        candidate = self._build(engine, plan, run, gate, versions)
        return {"state": candidate.state, "candidate_id": candidate.id, "commit": candidate.integrated_commit,
                "members": dict(candidate.members), "reason": candidate.reason_code or "",
                "conflicts": {key: list(value) for key, value in (candidate.conflicts or {}).items()}}

    def _unreconciled(self, run: RunRef, gate, role: str, repo: Path) -> list[str]:
        """The gate's members whose line does not yet hold the lines it builds on (`bt_durable.reconcile`, D-297). Composed
        now they would conflict and ask an agent to settle again, against other merge bases, the clash the reconciliation
        settles once. Its next pass sends `recheck_gates`. Empty when reconciliation is off."""
        if not reconcile.enabled():
            return []
        import json

        import bt_verification_tree as tree
        try:
            doc = json.loads(Path(run.plan_path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        names = {"project": run.project, "req": run.req, "revision": run.revision}
        resolutions = self.state_dir / "composition" / "resolutions"
        out = []
        for subplan_id in gate.subplans:
            tip = self.lines._tip(repo, self.lines.subplan_ref(run, role, subplan_id))
            preds = [(p, self.lines._tip(repo, self.lines.subplan_ref(run, role, p))) for p in tree.predecessors(doc, subplan_id)]
            preds = [(p, line) for p, line in preds if line]
            if tip and preds:
                done = tree.fold(repo, tip, preds, tree.try_ref(names, role, subplan_id), resolutions)
                if done["conflict"] or done["commit"] != tip:
                    out.append(subplan_id)
        return out

    def stale_members(self, run: RunRef, gate_id: str, snapshot: str) -> list[str]:
        """The members of a passed gate whose subplan line now holds work the gate's accepted snapshot was not built on
        (in plan order). Read-only. A candidate commit has each member's version commit as its second parent
        (`compose <plan> <SP>@v<N>`), so the gate task's snapshot names, on its first-parent history, exactly which
        member commits it was verified with, whichever revision composed it; a member is stale when its line's tree
        differs from that commit's (a stage join that re-seeds a line with the same tree changes nothing). A member the
        snapshot names no version of is stale when its line is neither in the snapshot's history nor already merged in."""
        plan = self.plan_for(run)
        gate = next(item for item in plan.composition_gates if item.id == gate_id)
        repo = self.lines._repo(plan.task(gate.task).repository)
        role = plan.task(gate.task).repository
        used = _composed_members(repo, snapshot)
        out = []
        for subplan_id in _composition_order(plan, gate):
            tip = self.lines._tip(repo, self.lines.subplan_ref(run, role, subplan_id))
            if not tip:
                continue                                 # no line: nothing newer than what the gate saw
            if subplan_id in used:
                if _tree(repo, tip) != _tree(repo, used[subplan_id]):
                    out.append(subplan_id)
            elif not _contains(repo, snapshot, tip):
                out.append(subplan_id)
        return out

    def candidate_commit(self, run: RunRef, task: TaskSpec, gate_id: str) -> str:
        plan = self.plan_for(run)
        gate = next(item for item in plan.composition_gates if item.id == gate_id)
        engine, store = self._engine(run, task.repository)
        versions = {}
        for subplan_id in gate.subplans:
            found = store.list_versions(self.plan_id(run), subplan_id)
            if not found:
                raise RuntimeError(f"GATE_NOT_COMPOSED: {gate_id} has no version of {subplan_id} yet")
            versions[subplan_id] = found[-1].version
        candidate = self._build(engine, plan, run, gate, versions)
        if candidate.state == "rejected":
            raise RuntimeError(f"GATE_CANDIDATE_REJECTED: {gate_id} {candidate.id} {candidate.reason_code}")
        return candidate.integrated_commit

    def _build(self, engine, plan: Plan, run: RunRef, gate, versions: dict[str, int]):
        order = tuple(item.id for item in plan.subplans if item.id in versions)
        return engine.build_candidate(self.plan_id(run), versions, member_order=order,
                                      required_verdicts={"M6": VERIFIER})

    @staticmethod
    def _contracts(plan: Plan, subplan_id: str, repo: Path, commit: str) -> dict[str, str]:
        """`<contract>@<version>` -> SHA-256 of the producer's file at the line tip (as the legacy owner hashes it), or
        "declared" when the producer's expected path is a pattern rather than one file."""
        spec = next(item for item in plan.subplans if item.id == subplan_id)
        out = {}
        for item in spec.produces:
            key = f"{item['contract']}@{item['version']}"
            paths = [p for p in plan.task(item["defined_by"]).expected_paths if not any(c in p for c in "*?[")]
            if spec.ui is not None and item["contract"] == spec.ui.contract:
                paths = [f"design/contracts/{spec.ui.contract}@v{spec.ui.version}.md"]
            digests = {path: _blob_sha256(repo, commit, path) for path in paths}
            digests = {path: value for path, value in digests.items() if value}
            out[key] = (next(iter(digests.values())) if len(digests) == 1 else
                        hashlib.sha256(repr(sorted(digests.items())).encode()).hexdigest() if digests else "declared")
        return out


def _composition_order(plan: Plan, gate) -> list[str]:
    """The gate's members in the order `_build` folds them (plan order)."""
    return [item.id for item in plan.subplans if item.id in gate.subplans]


_SNAPSHOT = re.compile(r"^m3 snapshot \S+-(T[A-Za-z0-9.]+)-a\d+-[0-9a-f]{8}$")


def _own_work_base(repo: Path, tip: str, items) -> str:
    """Where the member's own work starts on its line: the first commit, walking back the line's first parents from its
    tip, that is not a snapshot of one of its own tasks. A line a stage join built carries its prerequisites as
    integrations of other subplans' work, not as their published tips (pictures REQ-021 SP-4 at r16), so a delta from its
    merge base with the member folded before it re-applied copies of SP-1, SP-2 and SP-14 and every candidate of r19
    conflicted. Used only when every accepted snapshot of the member lies on that stretch; otherwise "" (the merge-base
    rule decides, as for lines whose history predates the durable runtime)."""
    own = {str(item.get("task_id")) for item in items if item.get("task_id")}
    snapshots = [str(item["snapshot"]) for item in items if item.get("snapshot")]
    if not own or not snapshots:
        return ""
    log = subprocess.run(["git", "-C", str(repo), "log", "--first-parent", "--format=%H%x00%s", tip], capture_output=True,
                         text=True, check=False)
    if log.returncode:
        return ""
    boundary, mine = "", 0
    for line in log.stdout.splitlines():
        sha, _, subject = line.partition("\0")
        found = _SNAPSHOT.match(subject.strip())
        if found and found.group(1) in own:
            mine += 1
            continue
        boundary = sha
        break
    if not boundary or not mine:
        return ""
    for snapshot in snapshots:
        inside = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", boundary, snapshot],
                                capture_output=True, check=False).returncode == 0
        if not inside or snapshot == boundary:
            return ""
    return boundary


def _prior_candidate(repo: Path, tip: str, built, folded: set[str]) -> str:
    """The commit of an earlier candidate the member's line already holds, whose members are all folded before it (the
    largest such): the member then brings only what its line added on top. Gate tasks integrate into their members'
    lines, so a later member's line holds the earlier gates' candidates (pictures REQ-021 r25: SP-7's line held CG-6's
    C3; folded from where SP-7's own snapshots start it re-applied SP-3..SP-6 and CG-7 conflicted in 13 files, D-187).
    "" when there is none."""
    fitting = [c for c in built if c.members and set(c.members) <= folded]
    for candidate in sorted(fitting, key=lambda c: (len(c.members), int(c.id.rsplit("C", 1)[-1] or 0)), reverse=True):
        inside = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", candidate.integrated_commit, tip],
                                capture_output=True, check=False).returncode == 0
        if inside:
            return candidate.integrated_commit
    return ""


_COMPOSED = re.compile(r"^compose \S+ (\S+)@v\d+$")


def _composed_members(repo: Path, snapshot: str) -> dict[str, str]:
    """Subplan -> the version commit the newest candidate on `snapshot`'s first-parent history folded for it."""
    log = subprocess.run(["git", "-C", str(repo), "log", "--first-parent", "--format=%P%x00%s", snapshot],
                         capture_output=True, text=True, check=False)
    out: dict[str, str] = {}
    for line in log.stdout.splitlines() if log.returncode == 0 else ():
        parents, _, subject = line.partition("\0")
        found = _COMPOSED.match(subject.strip())
        parents = parents.split()
        if found and len(parents) == 2:
            out.setdefault(found.group(1), parents[1])
    return out


def _contains(repo: Path, snapshot: str, tip: str) -> bool:
    """`tip` is in `snapshot`'s history, or merging it into `snapshot` changes nothing."""
    if subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", tip, snapshot], capture_output=True,
                      check=False).returncode == 0:
        return True
    merged = subprocess.run(["git", "-C", str(repo), "merge-tree", "--write-tree", "--no-messages", snapshot, tip],
                            capture_output=True, text=True, check=False)
    return merged.returncode == 0 and merged.stdout.split("\n", 1)[0].strip() == _tree(repo, snapshot)


def _merge_base(repo: Path, tip: str, other: str) -> str:
    if not other:
        return ""
    done = subprocess.run(["git", "-C", str(repo), "merge-base", tip, other], capture_output=True, text=True,
                          check=False)
    return done.stdout.strip() if done.returncode == 0 else ""


def _tree(repo: Path, commit: str) -> str:
    done = subprocess.run(["git", "-C", str(repo), "rev-parse", f"{commit}^{{tree}}"], capture_output=True, text=True,
                          check=False)
    return done.stdout.strip() if done.returncode == 0 else "unknown"


def _blob_sha256(repo: Path, commit: str, path: str) -> str:
    done = subprocess.run(["git", "-C", str(repo), "cat-file", "blob", f"{commit}:{path}"], capture_output=True,
                          check=False)
    return hashlib.sha256(done.stdout).hexdigest() if done.returncode == 0 else ""


__all__ = ["CompositionComposer"]
