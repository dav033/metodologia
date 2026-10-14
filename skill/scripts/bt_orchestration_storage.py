"""Atomic durable orchestration evidence; no credentials or worker transcripts."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from bt_orchestration_context import encode


def atomic_json(path: Path, value: object) -> None:
    fd, name = tempfile.mkstemp(prefix='.orchestration-', dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(encode(value).encode())
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)
