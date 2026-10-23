"""Public result type for sandboxed verification commands."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class CommandOutcome:
    status: Literal["pass", "fail", "unknown"]
    exit_code: int | None
    duration_ms: int
    stdout: bytes
    stderr: bytes
    issue_code: str | None
    sandboxed: bool
    output_truncated: bool = False
    namespace_ids: tuple[tuple[str, int], ...] = ()
