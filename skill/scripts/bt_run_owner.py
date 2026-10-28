"""Which runtime owns a run's execution state (REQ-030 M2/M8). Stdlib only: the legacy owner reads it at start.

`RUN.owner.json` in the requirement folder: {"run_id", "backend": "legacy"|"dbos", "workflow_id", "since", "by",
"migrated_from"}. No file means legacy (every run that existed before the durable runtime). Writes are
compare-and-swap on the previous content under an exclusive lock, so two migrations cannot both win.
"""
from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path

NAME = "RUN.owner.json"


class OwnerConflict(RuntimeError):
    pass


def path(rdir: Path | str) -> Path:
    return Path(rdir) / NAME


def read(rdir: Path | str) -> dict | None:
    try:
        data = json.loads(path(rdir).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as error:
        raise OwnerConflict(f"{NAME} is unreadable: {error}") from error   # never guess an owner
    if not isinstance(data, dict) or data.get("backend") not in ("legacy", "dbos"):
        raise OwnerConflict(f"{NAME} has no valid backend")
    return data


def backend(rdir: Path | str) -> str:
    current = read(rdir)
    return current["backend"] if current else "legacy"


def write(rdir: Path | str, record: dict, *, expect: dict | None) -> None:
    target = path(rdir)
    lock = target.with_name(f".{NAME}.lock")
    with open(lock, "a+") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        if read(rdir) != expect:
            raise OwnerConflict("the run's owner changed while this move was being prepared")
        tmp = target.with_name(f".{NAME}.{os.getpid()}.tmp")
        tmp.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        with open(tmp, "rb") as stream:
            os.fsync(stream.fileno())
        os.replace(tmp, target)


def refuse_legacy_start(rdir: Path | str) -> str:
    """'' when the legacy runtime may own this run; otherwise why it must not start (the durable runtime owns it)."""
    try:
        owner = backend(rdir)
    except OwnerConflict as error:
        return str(error)
    return "" if owner == "legacy" else "OWNED_BY_DBOS: this run is owned by the durable runtime (bt_durable)"
