"""Compare the approved Pictures proposal copy without exposing the host to sandbox code."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from bt_scheduler_quality.runner_types import CommandOutcome

APPROVAL = "aprobacion-backing-mesas.json"
REPO_FILE = "docs/req021/" + APPROVAL
MAX_BYTES = 65536


def compare(order, spec, snapshot: Path, rdir: Path) -> CommandOutcome | None:
    if (order.plan_id, order.task_id) != ("REQ-021", "T3.4") or len(spec.argv) != 4 or spec.argv[:3] != (
        "cmp", "--", REPO_FILE
    ) or not Path(spec.argv[3]).is_absolute() or Path(spec.argv[3]).resolve() != (rdir / APPROVAL).resolve() or spec.cwd != ".":
        return None
    try:
        root = snapshot.resolve(strict=True)
        target = (root / REPO_FILE).resolve(strict=True)
        target.relative_to(root)
        proposal = (root / "docs/req021/propuesta-backing-mesas.json").resolve(strict=True)
        proposal.relative_to(root)
        host = rdir / APPROVAL
        journal = rdir / "RUN.owner-proposal.json"
        if host.is_symlink() or journal.is_symlink() or not host.is_file() or not journal.is_file():
            raise ValueError("owner evidence unavailable")
        if any(p.stat().st_size > MAX_BYTES for p in (target, proposal, host, journal)):
            raise ValueError("owner evidence too large")
        reference = host.read_bytes()
        approved = json.loads(reference)
        receipt = json.loads(journal.read_bytes())
        if (receipt.get("schema") != 1 or receipt.get("approval") != approved or
                approved.get("aprobadoPor") != "owner" or
                approved.get("propuestaSha256") != hashlib.sha256(proposal.read_bytes()).hexdigest()):
            raise ValueError("owner evidence mismatch")
        equal = target.read_bytes() == reference
    except (OSError, ValueError, TypeError, AttributeError):
        return CommandOutcome("unknown", None, 0, b"", b"[M6] owner approval evidence unavailable or invalid\n", "CHECK_UNAVAILABLE", False)
    return CommandOutcome("pass" if equal else "fail", 0 if equal else 1, 0,
                          b"[M6] compared snapshot bytes with the recorded owner approval\n", b"", None, False)


def run(order, spec, snapshot: Path) -> CommandOutcome | None:
    if order is None or (order.plan_id, order.task_id) != ("REQ-021", "T3.4"):
        return None
    import bt_core
    try:
        rdir = bt_core.find_req(bt_core.ROOT / "pictures", "REQ-021").resolve()
    except (OSError, SystemExit):
        return CommandOutcome("unknown", None, 0, b"", b"[M6] owner approval unavailable\n", "CHECK_UNAVAILABLE", False)
    return compare(order, spec, snapshot, rdir)
