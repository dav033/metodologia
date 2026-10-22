"""Structured record of every intervention on a run, automatic or manual (REQ-030 step 6).

One JSON line per intervention in `<run dir>/RUN.interventions.jsonl`:

    at, run, task, class (CLASSES), source ("auto" | "manual"), evidence, repair, result ("fixed" | "failed" | "pending"),
    minutes_lost (how long the run waited because of it, when known)

The record is the raw material of the evolution analysis (`bt_evolution`): what failed, how often, what it cost and which
repair worked. It is append-only and best-effort: a record that cannot be written never stops a run. Writes are single
`O_APPEND` writes of one line, so concurrent writers (owner, watcher, operator CLI) do not interleave.
"""
from __future__ import annotations

import json
import os
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

FILE = "RUN.interventions.jsonl"
# The closed taxonomy of failures a run can hit (REQ-030 step 5). Anything the diagnosis cannot place is `unknown`.
CLASSES = ("plan_defect", "integration_defect", "regression", "environment", "criterion_unmapped", "quota", "transient",
           "unknown")
SOURCES = ("auto", "manual")
RESULTS = ("fixed", "failed", "pending")
MAX_TEXT = 600


def _clip(value: Any) -> Any:
    return value[:MAX_TEXT] if isinstance(value, str) else value


def record(run_dir: Path | str, *, kind: str, source: str = "auto", task: str = "", evidence: str = "", repair: str = "",
           result: str = "pending", minutes_lost: float | None = None, run: str = "", **extra: Any) -> dict[str, Any] | None:
    """Append one intervention. Returns the stored row (None when it could not be written)."""
    row = {"at": round(time.time(), 3), "run": run, "task": task,
           "class": kind if kind in CLASSES else "unknown", "source": source if source in SOURCES else "auto",
           "evidence": _clip(evidence), "repair": _clip(repair), "result": result if result in RESULTS else "pending",
           "minutes_lost": None if minutes_lost is None else round(float(minutes_lost), 2)}
    for key, value in extra.items():
        row.setdefault(key, _clip(value))
    try:
        fd = os.open(Path(run_dir) / FILE, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
        try:
            os.write(fd, (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
        finally:
            os.close(fd)
    except OSError:
        return None
    return row


MAX_BYTES = 2_000_000        # the feed and the page read at most this much from the END of the file


def _clean(row: dict[str, Any]) -> dict[str, Any] | None:
    """A row an agent could have forged is reduced to known fields of the right type; anything else is dropped."""
    import math

    at = row.get("at")
    if isinstance(at, bool) or not isinstance(at, (int, float)) or not math.isfinite(at):
        return None
    minutes = row.get("minutes_lost")
    minutes = float(minutes) if isinstance(minutes, (int, float)) and not isinstance(minutes, bool) and math.isfinite(minutes) else None
    text = lambda key: str(row.get(key) or "")[:MAX_TEXT]  # noqa: E731
    return {**{k: v for k, v in row.items() if k not in ("at", "minutes_lost", "class", "source", "result")},
            "at": float(at), "minutes_lost": minutes, "class": row["class"] if row.get("class") in CLASSES else "unknown",
            "source": row["source"] if row.get("source") in SOURCES else "auto",
            "result": row["result"] if row.get("result") in RESULTS else "pending",
            "task": text("task"), "evidence": text("evidence"), "repair": text("repair"), "run": text("run")}


def read(run_dir: Path | str) -> Iterator[dict[str, Any]]:
    """Every readable, well-formed row, oldest first (the last `MAX_BYTES` of the file at most). A damaged or forged line is
    skipped, never fatal."""
    try:
        with open(Path(run_dir) / FILE, "rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(0, size - MAX_BYTES))
            raw = handle.read()
    except OSError:
        return
    lines = raw.decode("utf-8", "replace").splitlines()
    if size > MAX_BYTES:
        lines = lines[1:]                              # the first line of a tail may be cut in half
    for line in lines:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict) and row.get("class"):
            clean = _clean(row)
            if clean is not None:
                yield clean
