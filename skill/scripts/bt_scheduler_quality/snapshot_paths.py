"""Path safety rules shared by Git tree verification and tar extraction."""

from __future__ import annotations

from pathlib import PurePosixPath


def safe_snapshot_path(value: str) -> bool:
    path = PurePosixPath(value)
    return bool(
        value
        and not value.startswith("/")
        and "\\" not in value
        and "\x00" not in value
        and path.parts
        and "." not in path.parts
        and ".." not in path.parts
        and path.parts[0] != ".git"
        and all(part not in {"", ".", ".."} for part in value.split("/"))
    )
