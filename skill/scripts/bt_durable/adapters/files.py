"""Small file helpers shared by the adapters."""
from __future__ import annotations

import os
from pathlib import Path


def atomic_write(path: Path, data: bytes, mode: int = 0o644) -> None:
    """Write-then-rename with fsync, so a crash leaves the old content or the new one, never a torn file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.chmod(tmp, mode)
    os.replace(tmp, path)
