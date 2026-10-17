"""Validation for pinned, oracle-free repository snapshots."""
from __future__ import annotations

import tarfile
from pathlib import Path, PurePosixPath

from .contract import BenchmarkError

_FORBIDDEN_COMPONENTS = {"bitacora"}
_FORBIDDEN_PREFIX = ("skill", "scripts", "bt_planner", "tests", "scenarios")
_SAFE_ENV_SUFFIXES = (".example", ".sample", ".template")


def validate_workspace_archive(path: Path, case_id: str) -> None:
    """Reject unsafe or benchmark-contaminated paths without extracting the archive."""
    seen: set[str] = set()
    try:
        with tarfile.open(path, mode="r:") as archive:
            for member in archive:
                name = member.name
                if not isinstance(name, str) or not name or name.startswith("/") or "\\" in name:
                    raise BenchmarkError("WORKSPACE_ARCHIVE_INVALID", f"case {case_id} has an unsafe archive path")
                parts = tuple(name.rstrip("/").split("/"))
                if any(part in {"", ".", ".."} for part in parts):
                    raise BenchmarkError("WORKSPACE_ARCHIVE_INVALID", f"case {case_id} has an unsafe archive path")
                normalized = PurePosixPath(*parts).as_posix()
                if normalized in seen:
                    raise BenchmarkError("WORKSPACE_ARCHIVE_INVALID", f"case {case_id} repeats archive path {normalized!r}")
                seen.add(normalized)
                if member.issym() or member.islnk():
                    raise BenchmarkError("WORKSPACE_ARCHIVE_INVALID", f"case {case_id} contains a link at {normalized!r}")
                if not member.isfile() and not member.isdir():
                    raise BenchmarkError("WORKSPACE_ARCHIVE_INVALID", f"case {case_id} contains a special file at {normalized!r}")
                folded = tuple(part.casefold() for part in parts)
                if any(part in _FORBIDDEN_COMPONENTS for part in folded) or \
                        folded[:len(_FORBIDDEN_PREFIX)] == _FORBIDDEN_PREFIX:
                    raise BenchmarkError("WORKSPACE_ARCHIVE_INVALID", f"case {case_id} includes a forbidden path {normalized!r}")
                basename = folded[-1]
                if basename == ".env" or (basename.startswith(".env.") and not basename.endswith(_SAFE_ENV_SUFFIXES)):
                    raise BenchmarkError("WORKSPACE_ARCHIVE_INVALID", f"case {case_id} includes an environment file {normalized!r}")
    except BenchmarkError:
        raise
    except (OSError, tarfile.TarError) as exc:
        raise BenchmarkError("WORKSPACE_ARCHIVE_INVALID", f"case {case_id} has an unreadable repository archive") from exc
