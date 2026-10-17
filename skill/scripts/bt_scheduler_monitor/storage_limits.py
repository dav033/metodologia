"""SQLite size accounting and conservative write headroom for the M4 store."""
from __future__ import annotations

from pathlib import Path

MAX_STORE_BYTES = 512 * 1024 * 1024
# Reserving 256 KiB covers an event row, indexes, page splits and a bounded write-ahead-log batch.
WRITE_RESERVE_BYTES = 256 * 1024


class StoreError(RuntimeError):
    """A durable write or schema operation failed; callers must not acknowledge input."""


def measured_store_bytes(path: str | Path) -> int:
    database = Path(path)
    return sum(candidate.stat().st_size for candidate in (database, Path(str(database) + "-wal"))
               if candidate.exists())


def ensure_write_capacity(path: str | Path, max_bytes: int,
                          reserve_bytes: int = WRITE_RESERVE_BYTES) -> int:
    """Reject mutations before measured DB+WAL bytes enter the reserved safety margin."""
    measured = measured_store_bytes(path)
    if measured + reserve_bytes > max_bytes:
        raise StoreError(f"storage_pressure: measured_bytes={measured} limit_bytes={max_bytes} "
                         f"reserve_bytes={reserve_bytes}")
    return measured
