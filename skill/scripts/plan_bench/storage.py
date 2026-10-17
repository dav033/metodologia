"""Bounded-memory, symlink-safe readers and immutable digest checks for benchmark stores."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .contract import BenchmarkError, strict_json_loads

MAX_JSON_BYTES = 8 * 1024 * 1024


def contained_file(root: Path, relative: str) -> Path:
    base = root.resolve(strict=True)
    path = base
    for part in Path(relative).parts:
        path = path / part
        try:
            if path.is_symlink():
                raise BenchmarkError("STORE_SYMLINK", f"store path {relative!r} contains a symlink")
        except OSError as exc:
            raise BenchmarkError("STORE_READ_ERROR", f"cannot inspect store path {relative!r}") from exc
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(base)
        if not resolved.is_file():
            raise BenchmarkError("STORE_FILE_INVALID", f"store path {relative!r} is not a regular file")
    except (OSError, ValueError) as exc:
        raise BenchmarkError("STORE_FILE_MISSING", f"store file {relative!r} is missing or outside the store") from exc
    return resolved


def read_bytes(root: Path, relative: str, *, maximum: int = MAX_JSON_BYTES) -> bytes:
    path = contained_file(root, relative)
    try:
        if path.stat().st_size > maximum:
            raise BenchmarkError("STORE_FILE_TOO_LARGE", f"store file {relative!r} exceeds {maximum} bytes")
        return path.read_bytes()
    except OSError as exc:
        raise BenchmarkError("STORE_READ_ERROR", f"cannot read store file {relative!r}") from exc


def read_json(root: Path, relative: str) -> Any:
    return strict_json_loads(read_bytes(root, relative), relative)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def verify_digest(root: Path, relative: str, expected: str) -> None:
    path = contained_file(root, relative)
    hasher = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                hasher.update(chunk)
    except OSError as exc:
        raise BenchmarkError("STORE_READ_ERROR", f"cannot read store file {relative!r}") from exc
    actual = hasher.hexdigest()
    if actual != expected:
        raise BenchmarkError("CONTENT_HASH_MISMATCH", f"SHA-256 mismatch for {relative!r}")
