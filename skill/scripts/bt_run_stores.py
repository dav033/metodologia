"""Where one Scheduler run keeps each module's store, named in one place.

The owner runtime (`bt_scheduler_run`) creates the stores; every reader (attempt facts, the live flow bus, the web) asks
here instead of rebuilding file names. `paths()` only reads: it never creates a directory, a database or a marker.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import bt_scheduler_adapter as adapter

_RUNTIME_ID = re.compile(r"[0-9a-f]{32}")


def runtime_marker(db: Path) -> Path:
    """`<db stem>-runtime.json`: binds the run to its runtime id (and so to its M2 ledger and module stores)."""
    return db.with_name(db.stem + "-runtime.json")


def m2_ledger(db: Path, runtime_id: str) -> Path:
    return db.parent / f"{db.stem}-{runtime_id}-m2.sqlite3"


def module_root(db: Path, runtime_id: str) -> Path:
    return db.parent / f"{db.stem}-{runtime_id}-modules"


def module_stores(db: Path, runtime_id: str) -> dict[str, Path]:
    root = module_root(db, runtime_id)
    return {"m4": root / "m4-monitor.sqlite3", "m5": root / "m5-recovery.sqlite3", "m6": root / "m6-quality.sqlite3"}


def runtime_id(rdir: Path) -> str | None:
    """The run's runtime id from its marker, or None when there is no (valid) marker yet."""
    try:
        data = json.loads(runtime_marker(adapter.run_db_path(rdir)).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    value = data.get("runtime_id") if isinstance(data, dict) else None
    return value if isinstance(value, str) and _RUNTIME_ID.fullmatch(value) else None


def paths(rdir: Path) -> dict[str, Path | None]:
    """Every store of the requirement's run. M2/M4/M5/M6 are None until the owner has bound a runtime id."""
    rdir = Path(rdir)
    db = adapter.run_db_path(rdir)
    rid = runtime_id(rdir)
    out: dict[str, Path | None] = {"m1": db, "projection": rdir / adapter.PROJECTION, "runtime": runtime_marker(db),
                                   "m2": None, "m4": None, "m5": None, "m6": None}
    if rid:
        out["m2"] = m2_ledger(db, rid)
        out.update(module_stores(db, rid))
    return out
