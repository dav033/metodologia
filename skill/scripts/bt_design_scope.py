"""Runtime write scope of the Designer role (CONTRACT §3): a `kind: design` result may change only `design/**`.

The prompt alone is not a boundary; M3 refuses a snapshot that escapes it before verification.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

_DESIGN_SCOPE_VERSION = (1, 3, 0)


def designer_scope_refusal(repository: Path | str, base_sha: str, snapshot_sha: str, *, kind: str,
                           role: str, preview_enabled: bool = False,
                           plan_version: str = "1.3.0") -> tuple[str, tuple[str, ...]] | None:
    """Return the permanent refusal for a Designer result, comparing both sides of renames."""
    try:
        version = tuple(int(part) for part in plan_version.split("."))
    except (AttributeError, ValueError):
        return None
    if version < _DESIGN_SCOPE_VERSION or (kind != "design" and role != "designer"):
        return None
    try:
        done = subprocess.run(["git", "-C", str(repository), "diff", "--name-status", "-z", "-M", base_sha, snapshot_sha],
                              capture_output=True, timeout=60, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return "DESIGN_SCOPE_UNAVAILABLE", ()
    if done.returncode:
        return "DESIGN_SCOPE_UNAVAILABLE", ()
    fields = done.stdout.decode("utf-8", "surrogateescape").split("\0")
    changed = []
    scope_violations = set()
    index = 0
    while index < len(fields) and fields[index]:
        status = fields[index]
        index += 1
        count = 2 if status.startswith(("R", "C")) else 1
        paths = fields[index:index + count]
        changed.extend(paths)
        if count == 2 and any(not path.startswith("design/") for path in paths):
            scope_violations.update(paths)
        index += count
    offending = tuple(sorted(scope_violations | {path for path in changed if not path.startswith("design/")}))
    if offending:
        return "DESIGN_SCOPE_VIOLATION", offending
    if not preview_enabled:
        preview = tuple(sorted(path for path in set(changed) if path.startswith("design/preview/")))
        if preview:
            return "DESIGN_PREVIEW_DISABLED", preview
    return None
