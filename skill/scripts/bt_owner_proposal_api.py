"""Flow transport for the named Pictures proposal decision."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import bt_owner_proposal as proposal
import bt_owner_proposal_store as durable
import bt_plans_api as plans


def _directory(root: Path, project: str, req: str) -> Path:
    if (project, req) != ("pictures", "REQ-021"):
        raise plans.PlanError("Esta selección no corresponde al requerimiento.")
    return plans.req_dir(root, project, req)


def view(root: Path, project: str, req: str, attempt: str) -> dict:
    try:
        _, data = proposal.verified_proposal(_directory(root, project, req), attempt)
        return data
    except proposal.ProposalError as exc:
        raise plans.PlanError(str(exc)) from exc


def decide(root: Path, form: dict, by: str = "flow") -> str:
    project, req = form.get("project", ""), form.get("req", "")
    if form.get("option") != "owner_proposal":
        return plans.decide(root, project, req, form.get("request", ""), form.get("option", ""),
                            form.get("reason", ""), by=by)
    rdir = _directory(root, project, req)
    try:
        choices = json.loads(form.get("selection", ""))
        if not isinstance(choices, dict) or set(choices) != {"backings", "mesas"}:
            raise proposal.ProposalError("La selección no es válida.")
        with durable.locked(rdir):
            raw, data = proposal.verified_proposal(rdir, form.get("attempt", ""))
            if data["request"] != form.get("request"):
                raise proposal.ProposalError("La revisión cambió; recarga la página.")
            journal = rdir / durable.JOURNAL
            prior = json.loads(journal.read_text(encoding="utf-8")) if journal.exists() else {}
            saved_date = date.fromisoformat(prior["approval"]["fecha"]) if prior else None
            approval = proposal.selection(raw, form.get("sha256", ""), choices["backings"], choices["mesas"], today=saved_date)
            durable.stage(rdir, data["request"], data["attempt"], approval)
    except (proposal.ProposalError, ValueError, TypeError, KeyError) as exc:
        raise plans.PlanError(str(exc)) from exc
    return "Selección guardada; el scheduler registrará la evidencia y reanudará la verificación."
