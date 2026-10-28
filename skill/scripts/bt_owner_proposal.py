"""Validate a named owner selection against the exact proposal bytes.

This module has no persistence or scheduler side effects. The caller must establish
the current attempt and verified snapshot before using these functions.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import subprocess
from contextlib import closing
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any


class ProposalError(ValueError):
    """The proposal or selection cannot be accepted."""


def require_manual_review(result: dict[str, Any]) -> None:
    checks = result.get("checks", [])
    issues = {issue.get("code") for issue in result.get("issues", [])}
    manual = [check for check in checks if check.get("issue_code") == "CHECK_MANUAL"]
    if (result.get("status") != "NEEDS_REVIEW" or issues != {"CRITERION_MANUAL"} or len(manual) != 1 or
            any(check.get("status") != "pass" for check in checks if check not in manual)):
        raise ProposalError("La revisión contiene comprobaciones pendientes adicionales.")


def verified_proposal(rdir: Path, attempt: str) -> tuple[bytes, dict[str, Any]]:
    """Read proposal bytes only when M1, M3, M6 and the private Git ref agree."""
    import bt_run_stores
    import bt_scheduler_decisions

    cards = [card for card in bt_scheduler_decisions.open_requests(rdir)
             if card.get("task") == "T3.2" and card.get("attempt") == attempt and card.get("source") == "review"]
    if len(cards) != 1:
        raise ProposalError("El intento ya no espera esta decisión.")
    card = cards[0]
    state = bt_scheduler_decisions._state(rdir)
    if any(state.get("tasks", {}).get(task, {}).get("attempts") for task in ("T3.5", "T3.6")):
        raise ProposalError("El modelado ya comenzó; no se puede registrar esta aprobación.")
    m6 = bt_run_stores.paths(rdir).get("m6")
    if m6 is None:
        raise ProposalError("No está disponible la evidencia de verificación.")
    try:
        with closing(sqlite3.connect(f"{Path(m6).resolve().as_uri()}?mode=ro", uri=True)) as db:
            row = db.execute("SELECT request_json,result_json,result_hash,state FROM requests WHERE idempotency_key=?",
                             (card["id"],)).fetchone()
        if not row or row[3] != "needs_review" or hashlib.sha256(row[1].encode()).hexdigest() != row[2]:
            raise ValueError("invalid M6 result")
        request, result = json.loads(row[0]), json.loads(row[1])
        require_manual_review(result)
        identity, inputs = result["identity"], result["input"]
        if (request["attempt_id"] != attempt or identity["attempt_id"] != attempt or
                request["task_id"] != "T3.2" or identity["task_id"] != "T3.2" or
                request["revision"] != identity["revision"]):
            raise ValueError("M6 identity mismatch")
        sha, tree = inputs["snapshot_sha"], inputs["tree_digest"]
        if not re.fullmatch(r"[0-9a-f]{40}", sha) or not re.fullmatch(r"[0-9a-f]{40}", tree):
            raise ValueError("invalid snapshot")
        root = Path(bt_run_stores.paths(rdir)["m1"]).parent.parent / "executor"
        prefix = Path(bt_run_stores.paths(rdir)["m1"]).stem
        records = []
        for ledger in root.glob(f"{prefix}-r*/ledger.db"):
            with closing(sqlite3.connect(f"{ledger.resolve().as_uri()}?mode=ro", uri=True)) as db:
                found = db.execute("SELECT handoff FROM attempts WHERE attempt_id=?", (attempt,)).fetchone()
            if found and found[0]:
                records.append(json.loads(found[0]))
        records = [item for item in records if item.get("status") == "captured" and item.get("snapshot_sha") == sha]
        if len(records) != 1:
            raise ValueError("M3 handoff unavailable or ambiguous")
        handoff = records[0]
        repo, ref = handoff["repository"], handoff["refs"]["snapshot"]
        if not ref.startswith("refs/m3/handoff/"):
            raise ValueError("invalid M3 ref")
        def git(*args: str) -> bytes:
            return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, timeout=10).stdout
        if git("rev-parse", "--verify", ref).decode().strip() != sha:
            raise ValueError("M3 ref changed")
        if git("rev-parse", "--verify", f"{sha}^{{tree}}").decode().strip() != tree:
            raise ValueError("M6 tree mismatch")
        raw = git("show", f"{sha}:docs/req021/propuesta-backing-mesas.json")
        proposal = json.loads(raw)
        return raw, {"attempt": attempt, "request": card["id"], "snapshot": sha,
                     "sha256": hashlib.sha256(raw).hexdigest(), "proposal": proposal}
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error, subprocess.SubprocessError) as exc:
        raise ProposalError("No se pudo verificar la procedencia de la propuesta.") from exc


def selection(proposal_bytes: bytes, expected_hash: str, backings: list[str],
              mesas: list[str], *, today: date | None = None) -> dict[str, Any]:
    digest = hashlib.sha256(proposal_bytes).hexdigest()
    if expected_hash != digest:
        raise ProposalError("La propuesta cambió; recarga la decisión.")
    try:
        proposal = json.loads(proposal_bytes)
        candidates = {
            "backings": [item["id"] for item in proposal["backings"]],
            "mesas": [item["tipo"] for item in proposal["mesas"]],
        }
        if any(not isinstance(values, list) or any(not isinstance(value, str) for value in values)
               or len(values) != len(set(values)) for values in candidates.values()):
            raise ValueError("invalid candidate ids")
    except (ValueError, TypeError, KeyError, UnicodeDecodeError) as exc:
        raise ProposalError("La propuesta no tiene candidatos válidos.") from exc
    for name, chosen, limit in (("backings", backings, 6), ("mesas", mesas, 3)):
        if not isinstance(chosen, list) or any(not isinstance(value, str) for value in chosen):
            raise ProposalError(f"Selección inválida: {name}.")
        if len(chosen) != len(set(chosen)):
            raise ProposalError(f"Hay identificadores duplicados en {name}.")
        if len(chosen) > limit:
            raise ProposalError(f"El límite de {name} es {limit}.")
        if not set(chosen) <= set(candidates[name]):
            raise ProposalError(f"Hay identificadores desconocidos en {name}.")
    return {"propuestaSha256": digest, "aprobadoPor": "owner", "fecha": (today or datetime.now(UTC).date()).isoformat(),
            "backings": backings.copy(), "mesas": mesas.copy()}
