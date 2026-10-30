"""How the previous engine stopped, so that a deliberate restart costs the work nothing (D-210).

The owner, 2026-10-30: restarts must be a property of the engine, not something deploys avoid. Every integration
restarts the engine, several times an hour; until now an interruption counted like a crash. D-171 queued an interrupted
M6 verification again ONCE per request, so a second deploy over the same verification turned it into a decision for
the owner (pictures REQ-021 r26 T10.45, 09:31 and 10:06); and DBOS counts every recovery of an agent, verify or
integrate workflow against its poison limit (100, D-182).

The engine writes `engine.session.json` (a fresh session id) when it starts and, when it stops on a signal,
`engine.stopped.json` with the same id, durably, before DBOS is destroyed and the process exits (D-181). The next start
reads both before anything recovers: the same id means a recorded, deliberate stop (`clean`); a session without its
stop record is an unexplained end — a crash, an OOM kill, a SIGKILL — (`unexplained`); no session at all is a first
start. Work interrupted by a clean stop resumes without spending a budget: the M6 request is queued again without
using its one interrupted retry (adapters/m6.py), and the PENDING workflows DBOS is about to recover are credited the
dispatch that recovery will count (`credit_recoveries`). Only unexplained ends keep counting, which is what protects
against crash loops.
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from pathlib import Path

LOG = logging.getLogger("bt_durable.restarts")
SESSION = "engine.session.json"
STOPPED = "engine.stopped.json"
CLEAN, UNEXPLAINED, FIRST = "clean", "unexplained", "first"

_previous: dict[str, str] = {}             # state dir -> how the previous engine stopped (read once per process)
_session: dict[str, str] = {}              # state dir -> this engine's session id


def _read(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _write_durably(path: Path, data: dict) -> None:
    """Write-then-rename with fsync of the file and its directory: after a crash the file is whole or absent."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    fd = os.open(tmp, os.O_CREAT | os.O_TRUNC | os.O_WRONLY | os.O_CLOEXEC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(data, stream)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)
    dfd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)


def previous_stop(state_dir: Path) -> str:
    """`clean`, `unexplained` or `first`: how the engine that used `state_dir` before this process ended. Read once
    and kept for the life of the process (`begin` replaces the session file right after)."""
    key = str(Path(state_dir).resolve())
    if key not in _previous:
        session = _read(Path(state_dir) / SESSION)
        stopped = _read(Path(state_dir) / STOPPED)
        if session is None:
            _previous[key] = FIRST
        elif stopped is not None and stopped.get("session") and stopped.get("session") == session.get("session"):
            _previous[key] = CLEAN
        else:
            _previous[key] = UNEXPLAINED
    return _previous[key]


def begin(state_dir: Path) -> str:
    """Record this engine's session (after `previous_stop` was read). Returns its id."""
    previous_stop(state_dir)
    session = uuid.uuid4().hex
    _session[str(Path(state_dir).resolve())] = session
    (Path(state_dir) / STOPPED).unlink(missing_ok=True)
    _write_durably(Path(state_dir) / SESSION, {"session": session, "pid": os.getpid(), "started_at": time.time()})
    return session


def record_clean_stop(state_dir: Path, reason: str = "signal") -> None:
    """The deliberate stop of this engine's session: written before DBOS is destroyed and the process exits."""
    session = _session.get(str(Path(state_dir).resolve()))
    if not session:
        return
    _write_durably(Path(state_dir) / STOPPED, {"session": session, "pid": os.getpid(), "stopped_at": time.time(),
                                               "reason": reason})


def credit_recoveries(system_database_url: str, executor_id: str) -> int:
    """Before DBOS launches after a clean stop: give each of this executor's PENDING workflows back the dispatch DBOS
    is about to count when it recovers them, so a deliberate restart never brings a workflow nearer its poison limit.
    Returns how many were credited. A database without DBOS's tables yet (first start) credits nothing."""
    import sqlalchemy as sa
    table = "workflow_status" if system_database_url.startswith("sqlite") else "dbos.workflow_status"
    engine = sa.create_engine(system_database_url)
    try:
        with engine.begin() as conn:
            done = conn.execute(sa.text(f"UPDATE {table} SET recovery_attempts = recovery_attempts - 1 "
                                        "WHERE status = 'PENDING' AND executor_id = :executor "
                                        "AND recovery_attempts > 0"), {"executor": executor_id})
            return done.rowcount or 0
    except sa.exc.SQLAlchemyError as error:
        LOG.info("no recovery credit: %s", str(error).splitlines()[0][:200])
        return 0
    finally:
        engine.dispose()


def _reset_for_tests() -> None:
    _previous.clear()
    _session.clear()


__all__ = ["CLEAN", "FIRST", "UNEXPLAINED", "begin", "credit_recoveries", "previous_stop", "record_clean_stop"]
