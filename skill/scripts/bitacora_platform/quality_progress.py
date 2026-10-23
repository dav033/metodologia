"""Private, read-only diagnostics for checks currently running in M6."""
from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
import time
from pathlib import Path

LOGGER = logging.getLogger(__name__)


def directory(store: Path) -> Path:
    return store.with_suffix(".progress")


class ProgressJournal:
    """Keep output timing, never output content or command arguments."""

    def __init__(self, store: Path):
        self.root = directory(store)
        self.local = threading.local()

    def observe(self, attempt: str, check: str, phase: str, size: int) -> None:
        now = time.time()
        state = getattr(self.local, "state", None)
        if state is None or state["attempt"] != attempt or state["check"] != check or state["phase"] == "finished":
            state = {"attempt": attempt, "check": check, "started_at": now,
                     "last_output_at": None, "output_bytes": 0, "written_at": 0, "pid": os.getpid()}
            self.local.state = state
        if size > state["output_bytes"]:
            state["last_output_at"] = now
            state["output_bytes"] = size
        state["phase"] = phase
        if now - state["written_at"] < 1 and phase != "finished":
            return
        state["updated_at"] = now
        state["written_at"] = now
        temporary = None
        try:
            self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", dir=self.root, delete=False, encoding="utf-8") as stream:
                temporary = Path(stream.name)
                json.dump(state, stream)
            os.replace(temporary, self.root / f"{attempt}.json")
        except OSError as error:
            LOGGER.warning("M6 progress unavailable (%s)", type(error).__name__)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def observer(port):
    journal = ProgressJournal(port.store.path) if port.store.path is not None else None

    def observe(check: str, phase: str, size: int) -> None:
        order = getattr(port._audit_runner.context, "order", None)
        if order is not None and journal is not None:
            journal.observe(order.attempt_id, check, phase, size)

    return observe


def enrich(store: Path | None, attempts: list[dict], owners: list[int]) -> None:
    """Enrich only live verification attempts; old files cannot imply a live owner."""
    if store is None:
        return
    now = time.time()
    for attempt in attempts:
        if attempt["state"] != "verifying":
            continue
        path = directory(store) / f"{attempt['attempt']}.json"
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            if record["attempt"] != attempt["attempt"]:
                raise ValueError("attempt mismatch")
            started, updated = float(record["started_at"]), float(record["updated_at"])
            output = record["last_output_at"]
            attempt["verification"] = {
                "check": record["check"], "phase": record["phase"],
                "elapsed_seconds": round(max(0, (updated if record["phase"] == "finished" else now) - started), 1),
                "heartbeat_age_seconds": round(max(0, now - updated), 1),
                "last_output_age_seconds": None if output is None else round(max(0, now - float(output)), 1),
                "owner_alive": record["pid"] in owners,
            }
        except FileNotFoundError:
            continue
        except (OSError, ValueError, TypeError, KeyError) as error:
            attempt["verification_progress_error"] = type(error).__name__
