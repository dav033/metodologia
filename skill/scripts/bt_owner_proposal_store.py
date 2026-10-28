"""Durable, serialized storage for a single named proposal decision."""
from __future__ import annotations

import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

from bt_owner_proposal import ProposalError

JOURNAL = "RUN.owner-proposal.json"
APPROVAL = "aprobacion-backing-mesas.json"


@contextmanager
def locked(rdir: Path):
    fd = os.open(rdir / "RUN.owner-proposal.lock", os.O_CREAT | os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def _write(path: Path, data: dict) -> None:
    content = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode()
    fd, name = tempfile.mkstemp(prefix=".owner-proposal-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
        parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def stage(rdir: Path, request: str, attempt: str, approval: dict) -> dict:
    """Save a recoverable intent before its approval; refuse incompatible repeats.

    Call under locked() after checking the still-current attempt and verified bytes.
    """
    journal = rdir / JOURNAL
    expected = {"schema": 1, "request": request, "attempt": attempt, "approval": approval}
    if journal.exists():
        try:
            saved = json.loads(journal.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            raise ProposalError("La decisión guardada no se puede leer.") from exc
        if saved != expected:
            raise ProposalError("Ya existe una decisión incompatible para esta propuesta.")
    target = rdir / APPROVAL
    if target.exists():
        try:
            saved = json.loads(target.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            raise ProposalError("La aprobación existente no se puede leer.") from exc
        if saved != approval:
            raise ProposalError("Ya existe una aprobación incompatible.")
    if not journal.exists():
        _write(journal, expected)
    if not target.exists():
        _write(target, approval)
    return expected
