"""The 500-line file guard at capture time. The interactive hook only sees what a session's tools report; here the
snapshot commit is compared with the attempt's base, so every write counts whatever tool the agent used.

Advisory and deterministic: the same (base, snapshot) pair gives the same findings, a failure never fails the
capture (it is reported in the telemetry event instead), and the result travels on the Snapshot so the
coordinator can put `note(snapshot.oversized)` in the agent's next note."""
from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import file_guard
from bt_contracts.execution import AttemptRef, OversizedFile

EVENT = "file_guard"
REPORTED_MAX = 50


def check(attempt: AttemptRef, repository: Path, base_sha: str, snapshot_sha: str | None,
          telemetry=None) -> tuple[OversizedFile, ...]:
    found: tuple[OversizedFile, ...] = ()
    error = ""
    if snapshot_sha:
        try:
            found = tuple(OversizedFile(**item) for item in file_guard.snapshot_findings(repository, base_sha,
                                                                                          snapshot_sha))
        except Exception as exc:  # noqa: BLE001 - advisory: an unreadable range is reported, never fatal
            error = f"{type(exc).__name__}: {exc}"[:500]
    if telemetry is not None:
        try:
            telemetry.emit(EVENT, run_id=attempt.run.run_id, task_id=attempt.task_id,
                           attempt_key=attempt.attempt_key, base_sha=base_sha, snapshot_sha=snapshot_sha,
                           limit=file_guard.LIMIT, count=len(found), error=error or None,
                           files=[item.model_dump(mode="json") for item in found[:REPORTED_MAX]])
        except Exception:  # noqa: BLE001, S110 - telemetry is best effort; the capture result is what matters
            pass
    return found


def note(oversized: Iterable[OversizedFile]) -> str:
    """Text for the agent's next note (empty without findings)."""
    return file_guard.findings_note([item.model_dump(mode="json") for item in oversized])
