"""Deliver a durable named approval through the running scheduler's M6 store."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import bt_attestation
import bt_owner_proposal as proposal
import bt_owner_proposal_store as durable

_last_error = ""


def tick(project: str, req: str, rdir: Path, wiring) -> None:
    global _last_error
    try:
        if deliver(project, req, rdir, wiring):
            print("OWNER_PROPOSAL: verification requeued", file=sys.stderr)
        _last_error = ""
    except Exception as exc:  # noqa: BLE001 - preserve the live scheduler and report the blocked delivery
        message = f"{type(exc).__name__}: {exc}"
        if message != _last_error:
            print(f"OWNER_PROPOSAL_BLOCKED: {message}", file=sys.stderr)
            _last_error = message


def deliver(project: str, req: str, rdir: Path, wiring) -> bool:
    if (project, req) != ("pictures", "REQ-021") or not (rdir / durable.JOURNAL).is_file():
        return False
    store, scheduler = wiring.verification_store, wiring.scheduler
    if store is None:
        raise proposal.ProposalError("M6 no está disponible para registrar la decisión.")
    with durable.locked(rdir):
        item = json.loads((rdir / durable.JOURNAL).read_text(encoding="utf-8"))
        attempt, request, approval = item["attempt"], item["request"], item["approval"]
        reason = f"Owner approved proposal {attempt}: {approval['propuestaSha256']}"
        with store._lock:
            done = store._connection.execute(
                "SELECT operator,reason FROM verification_retries WHERE request_key=?", (request,)).fetchone()
        if done:
            if (done[0], done[1]) != ("owner", reason):
                raise proposal.ProposalError("La revisión ya fue reencolada por otra decisión.")
            return False
        snap = scheduler.snapshot()
        task = snap.tasks.get("T3.2", {})
        if task.get("attempt") != attempt or task.get("attempt_state") != "verifying":
            raise proposal.ProposalError("El intento ya no espera la decisión.")
        if any(snap.tasks.get(task_id, {}).get("attempts", 0) for task_id in ("T3.5", "T3.6")):
            raise proposal.ProposalError("El modelado ya comenzó antes de la aprobación.")
        result = store.get_result(request)
        if request not in store.open_reviews_of("T3.2") or not result:
            raise proposal.ProposalError("La revisión ya no está abierta.")
        proposal.require_manual_review(result)
        identity, inputs = result["identity"], result["input"]
        if (identity["attempt_id"], identity["task_id"], identity["revision"]) != (attempt, "T3.2", snap.revision):
            raise proposal.ProposalError("La evidencia corresponde a otro intento o revisión.")
        handoff = (wiring.executor.describe(attempt) or {}).get("handoff") or {}
        if handoff.get("status") != "captured" or handoff.get("snapshot_sha") != inputs["snapshot_sha"]:
            raise proposal.ProposalError("El snapshot de M3 no coincide con M6.")
        repo, ref, sha = handoff["repository"], handoff["refs"]["snapshot"], inputs["snapshot_sha"]
        if not ref.startswith("refs/m3/handoff/"):
            raise proposal.ProposalError("La referencia M3 no es válida.")
        def git(*args):
            return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, timeout=10).stdout
        if git("rev-parse", "--verify", ref).decode().strip() != sha or \
                git("rev-parse", "--verify", f"{sha}^{{tree}}").decode().strip() != inputs["tree_digest"]:
            raise proposal.ProposalError("El árbol verificado ha cambiado.")
        raw = git("show", f"{sha}:docs/req021/propuesta-backing-mesas.json")
        confirmed = proposal.selection(raw, approval["propuestaSha256"], approval["backings"], approval["mesas"],
                                       today=date.fromisoformat(approval["fecha"]))
        if confirmed != approval:
            raise proposal.ProposalError("La aprobación no coincide con la selección registrada.")
        durable.stage(rdir, request, attempt, approval)
        checks = bt_attestation.manual_checks(scheduler.plan, "T3.2")
        if len(checks) != 1:
            raise proposal.ProposalError("El contrato manual de T3.2 cambió.")
        check = checks[0]
        bt_attestation.mint(rdir, "T3.2", check["purpose"], check["value"], check["expected"], reason, "owner",
                            attempt=attempt)
        store.retry_attested(request, "owner", reason)
        return True
