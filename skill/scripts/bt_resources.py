"""One resolver for the folder that holds templates/, assets/, references/, agents/ and SKILL.md.

Order: the BITACORA_RESOURCES override (when it is a valid resource folder), the checkout's `skill/` next to
`scripts/`, then the `bitacora_resources` package an installed wheel carries. An override that is set but invalid
is reported once on stderr and ignored, so a typo cannot silently mix sources.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_warned = False


def resource_root(here: Path | None = None) -> Path:
    global _warned
    here = here or Path(__file__).resolve().parent
    override = os.environ.get("BITACORA_RESOURCES")
    if override and (Path(override) / "templates").is_dir():
        return Path(override).resolve()
    if override and not _warned:
        _warned = True
        print(f"BITACORA_RESOURCES={override!r} has no templates/ folder; ignoring it.", file=sys.stderr)
    for candidate in (here.parent, here / "bitacora_resources"):
        if (candidate / "templates").is_dir():
            return candidate.resolve()
    return here.parent
