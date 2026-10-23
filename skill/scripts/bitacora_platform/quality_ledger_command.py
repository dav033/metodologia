"""Execute the engine-owned ledger contract without exposing engine code to a product."""
from __future__ import annotations

from pathlib import Path

from bt_scheduler_quality.runner_types import CommandOutcome
from .cli_audit_ledger import check


def run(spec, snapshot_root: Path) -> CommandOutcome | None:
    argv = spec.argv
    if argv and argv[0] in ("python", "python3"):
        argv = argv[1:]
    if len(argv) != 4 or argv[:3] != ("bitacora.py", "audit-ledger", "check"):
        return None
    lines: list[str] = []
    try:
        root = snapshot_root.resolve(strict=True)
        path = Path(argv[3])
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("ledger path must stay inside the snapshot")
        target = (root / spec.cwd / path).resolve()
        target.relative_to(root)
    except (OSError, ValueError):
        lines.append("ERROR ledger path must stay inside the snapshot")
        code = 2
    else:
        code = check(target, emit=lines.append)
    output = ("\n".join(lines) + "\n").encode("utf-8")
    return CommandOutcome("pass" if code == 0 else "fail", code, 0, output, b"", None, True)
