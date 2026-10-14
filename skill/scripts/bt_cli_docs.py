"""CLI for small documentation helpers: `bitacora.py --project P glossary`."""
from __future__ import annotations

import sys
from pathlib import Path


def register(sub) -> None:
    sub.add_parser("glossary", help="create the project's GLOSSARY.md from the template if missing; print its path")


def dispatch(a, project: str | None, root: Path) -> int:
    import bt_core
    if not project or not (root / project).is_dir():
        sys.exit("No project resolved; pass --project <name> (run `init` first).")
    path = bt_core.ensure_glossary(root / project)
    bt_core.write_index(root / project)
    print(path)
    return 0
