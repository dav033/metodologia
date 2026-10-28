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
