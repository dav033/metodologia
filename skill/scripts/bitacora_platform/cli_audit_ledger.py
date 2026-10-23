"""Read-only entry point for the engine-owned audit ledger contract."""
from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import bt_audit_gate as gate


def check(path: Path, emit: Callable[[str], None] = print) -> int:
    try:
        with path.open("rb") as source:
            raw = source.read(gate.MAX_BYTES + 1)
    except OSError as error:
        emit(f"ERROR findings ledger unreadable: {error}")
        return 2
    if len(raw) > gate.MAX_BYTES:
        problems = [f"the findings ledger is larger than {gate.MAX_BYTES} bytes"]
    else:
        try:
            data = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeError, RecursionError):
            problems = ["the findings ledger is not valid UTF-8 JSON"]
        else:
            problems = gate.validate_ledger(data)
    for problem in problems:
        emit(f"ERROR {problem}")
    if not problems:
        emit("OK: audit ledger contract is valid")
    return 2 if problems else 0


def digest(plan_path: Path, repository: Path, role: str, revision: str = "HEAD",
           emit: Callable[[str], None] = print, evidence_files: tuple[str, ...] = ()) -> int:
    """Print provenance for a producer or auditor to record; the plan defines the shared exclusions."""
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        tasks = plan["tasks"]
        if not isinstance(tasks, list) or not all(isinstance(t, dict) for t in tasks):
            raise ValueError("plan tasks must be objects")
        if not any(t.get("repository") == role for t in tasks):
            raise ValueError(f"repository role {role!r} is absent from the plan")
        value = gate.tree_digest(repository, revision, gate.evidence_outputs(tasks, role, evidence_files))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        emit(f"ERROR source tree digest unavailable: {error}")
        return 2
    emit(value)
    return 0
