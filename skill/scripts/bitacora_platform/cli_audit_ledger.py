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
