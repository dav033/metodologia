"""The agent's brief in the durable runtime carries what the legacy owner puts in it (REQ-030 item 2).

The sections are built by the legacy functions themselves (`bt_scheduler_executor_wiring.owner_notes`,
`contract_notes`), so both runtimes cannot drift apart: the owner's indications (`RUN.notes/<task>.md`), the audit's
findings for a task sent back, the history of earlier attempts, the independent failure analysis, the last
verification failure, the audit ledger help, and the UI contract with its approval state. The history reads the legacy
run's M1 document when the run was migrated, plus the attempts the durable verifier recorded in the same
`RUN.notes/<task>.history.jsonl` (one history across both runtimes). When the task workflow hands the agent a note of
its own (the failure the recovery policy just classified), the last-verification note is left out: it is the same text.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

from bt_contracts.execution import AttemptRef

from ..legacy import (
    PlanBriefs,
    check_design_approval,
    contract_notes,
    design_execution_notes,
    design_gates,
    joined_notes,
    legacy_attempts_doc,
    owner_notes,
    with_recorded_history,
)


def requirement_dir(run) -> Path:
    return Path(run.plan_path).parent.parent              # <req dir>/plan-revisions/PLAN.rN.json


class DurableBriefs:
    """`briefs_for(attempt, plan, note)` for `M3Attempts`: a PlanBriefs whose notes are the legacy owner's."""

    def __init__(self, *, repositories_for: Callable[[str], Mapping[str, Path] | Callable[[str], Path | None]],
                 rdir_for: Callable[[object], Path] = requirement_dir):
        self.repositories_for = repositories_for
        self.rdir_for = rdir_for

    def __call__(self, attempt: AttemptRef, plan, note: str) -> PlanBriefs:
        rdir = self.rdir_for(attempt.run)
        repos = self.repositories_for(attempt.run.project)

        def repository(task):
            found = repos(task.repository) if callable(repos) else repos.get(task.repository)
            return Path(found) if found else None

        def design(request) -> str:
            return contract_notes(plan, request, repository,
                                  lambda repo, base, path: check_design_approval(rdir, repo, base, path),
                                  lambda ref: design_execution_notes(rdir, ref))

        def attempts(task_id: str) -> dict:
            try:
                doc = legacy_attempts_doc(rdir)
            except Exception:  # noqa: BLE001 - a run born in the durable runtime has no M1 document
                doc = {}
            return with_recorded_history(doc, rdir, task_id)

        notes = owner_notes(rdir, plan, joined_notes(design), state=attempts, verify=not note.strip())
        return PlanBriefs(plan, notes=notes)


class DurableDesignGate:
    """The legacy start gate of a `ui: true` task, read on the base an attempt would start from (D-262).

    `check(run, plan, task_id, base)` -> {} for a task without a UI contract, else {"path", "state", "sha256",
    "design_task", "code"}: `state` is `bt_design_approval.check_tree`'s (approved | unapproved | missing |
    hash-mismatch) and `code` the legacy blocked reason (`gates.approval_problem`, '' when approved). The legacy
    scheduler refused such a start (`CoreExecutionPort.start`); the durable runtime only wrote the state into the brief
    and ran the agent anyway: pictures REQ-021 r32 T2.57 spent five attempts on a base without its v2 contract."""

    def __init__(self, *, repositories_for: Callable[[str], Mapping[str, Path] | Callable[[str], Path | None]],
                 rdir_for: Callable[[object], Path] = requirement_dir):
        self.repositories_for = repositories_for
        self.rdir_for = rdir_for

    def check(self, run, plan, task_id: str, base: str) -> dict:
        path = design_gates.contract_path(plan, task_id)
        if path is None:
            return {}
        task = plan.task(task_id)
        subplan = next((item for item in plan.subplans if item.id == task.meta.get("subplan_id")), None)
        design_task = subplan.ui.design_task if subplan is not None and subplan.ui is not None else ""
        repos = self.repositories_for(run.project)
        found = repos(task.repository) if callable(repos) else repos.get(task.repository)
        if not path or not found:
            detail = path or "invalid frozen UI contract"
            return {"path": detail, "state": "unapproved", "sha256": "", "design_task": design_task,
                    "code": "DESIGN_CONTRACT_UNAPPROVED"}
        try:
            gate = check_design_approval(self.rdir_for(run), Path(found), base, path)
        except Exception as error:  # noqa: BLE001 - approval storage is a fail-closed boundary, as in the legacy gate
            return {"path": path, "state": "unapproved", "sha256": "", "design_task": design_task,
                    "code": "DESIGN_CONTRACT_UNAPPROVED", "detail": f"approval unavailable ({type(error).__name__})"}
        state = str(gate.get("state") or "unapproved")
        return {"path": path, "state": state, "sha256": str(gate.get("sha256") or ""), "design_task": design_task,
                "code": design_gates.approval_problem(state) or ""}
