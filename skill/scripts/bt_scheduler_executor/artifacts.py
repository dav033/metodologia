"""The per-attempt artefact directory: `<root>/attempts/<dirname>/`. Writers are atomic; history is never deleted."""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any

from .config import Config
from .errors import ExecutorError

MARKER = "\n[... {n} bytes of output dropped by the executor's cap ...]\n"
REPORT_MAX = 64 * 1024
DESCENDANT_MAX = 4096


def atomic_write(path: Path, data: bytes, mode: int = 0o600) -> None:
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except OSError as error:
        raise ExecutorError("ARTIFACT_ERROR", f"{path.name}: {type(error).__name__}") from None


def write_json(path: Path, value: Any) -> None:
    atomic_write(path, json.dumps(value, indent=1, sort_keys=True).encode("utf-8"))


def read_bounded(path: Path, limit: int) -> bytes | None:
    """At most `limit` bytes of a REGULAR file, never following a symlink and never blocking on a FIFO/device; None when
    it is absent, not regular or larger than `limit`. Files in the attempt directory can be written by the agent."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError:
        return None
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            return None
        with os.fdopen(fd, "rb", closefd=False) as handle:
            data = handle.read(limit + 1)
    except OSError:
        return None
    finally:
        os.close(fd)
    return None if len(data) > limit else data


def read_json(path: Path, limit: int = 1 << 20) -> Any:
    """The parsed file, or None when absent/partial/not JSON/oversized (a half-written record is the same as no record)."""
    raw = read_bounded(path, limit)
    if raw is None:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except ValueError:
        return None


def _int(value: object, low: int = 0) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= low else None


def _num(value: object) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and value == value \
        and abs(value) != float("inf") else None


def read_exit(path: Path) -> dict | None:
    """The shim's exit record, shape-checked: the agent can write files next to it, so a record that is not what the shim
    writes is NOT trusted and is treated as a vanished supervisor (`lost`), never allowed to crash the settle."""
    raw = read_json(path)
    if raw is None and (path.exists() or path.is_symlink()):
        raw = read_json(path)      # the shim's atomic rename may land between the read and the check: read once more
        if raw is None:
            return {"reason": "lost", "error": "exit record unreadable or oversized", "adopt_orphan": True}
    if raw is None:
        return None
    reason = raw.get("reason") if isinstance(raw, dict) else None
    rc = raw.get("returncode") if isinstance(raw, dict) else None
    bad = (not isinstance(raw, dict) or reason not in ("exited", "timeout", "cancelled", "spawn_error")
           or (rc is not None and (not isinstance(rc, int) or isinstance(rc, bool))))
    if bad:
        return {"reason": "lost", "error": "exit record is not what the shim writes", "adopt_orphan": True}
    out: dict = {"reason": reason, "returncode": rc, "error": str(raw.get("error", ""))[:300],
                 "output_bytes": _int(raw.get("output_bytes")) or 0, "dropped_bytes": _int(raw.get("dropped_bytes")) or 0}
    for key in ("started_at", "ended_at"):
        if _num(raw.get(key)) is not None:
            out[key] = _num(raw.get(key))
    if _int(raw.get("child_pid"), 1):
        out["child_pid"] = raw["child_pid"]
    return out


def read_shim(path: Path) -> dict:
    """The shim's identity record with only well-typed fields kept ({} when absent or unusable)."""
    raw = read_json(path)
    if not isinstance(raw, dict):
        return {}
    out: dict = {}
    for key in ("pid", "pgid", "child_pid", "child_pgid"):
        if _int(raw.get(key), 1):
            out[key] = raw[key]
    for key in ("ident", "child_ident"):
        if isinstance(raw.get(key), str) and 0 < len(raw[key]) < 200:
            out[key] = raw[key]
    if _num(raw.get("started_at")) is not None:
        out["started_at"] = _num(raw["started_at"])
    if "pid" not in out or "ident" not in out:
        out.pop("pid", None)
        out.pop("ident", None)
    return out


def read_descendants(path: Path) -> dict[int, str]:
    """Verified, bounded PID/start identities from the shim; malformed or oversized evidence authorises no sweep."""
    raw = read_json(path, limit=1 << 20)
    if not isinstance(raw, dict) or set(raw) != {"version", "truncated", "processes"} \
            or type(raw.get("version")) is not int or raw["version"] != 1 or type(raw.get("truncated")) is not bool:
        return {}
    records = raw.get("processes")
    if not isinstance(records, list) or len(records) > DESCENDANT_MAX:
        return {}
    identities: dict[int, str] = {}
    for record in records:
        if not isinstance(record, dict) or set(record) != {"pid", "ident"}:
            return {}
        pid, ident = _int(record.get("pid"), 1), record.get("ident")
        if pid is None or not isinstance(ident, str) or not 0 < len(ident) < 200 or pid in identities:
            return {}
        identities[pid] = ident
    return identities


def paths(directory: Path) -> dict[str, str]:
    return {"dir": str(directory), "order": str(directory / "order.json"), "route": str(directory / "route.json"),
            "prompt": str(directory / "prompt.txt"), "output": str(directory / "output.log"),
            "tail": str(directory / "output.tail"), "exit": str(directory / "exit.json"),
            "shim": str(directory / "shim.json"), "handoff": str(directory / "handoff")}


def read_output(directory: Path, exit_info: dict | None, cfg: Config) -> tuple[str, int, int]:
    """(text for classification, total bytes seen, bytes dropped). Complete when it fits head+tail; otherwise the start
    of the head, a marker and the tail (the end is where errors and quota messages are)."""
    head = read_bounded(directory / "output.log", cfg.output_head_bytes) or b""
    tail = read_bounded(directory / "output.tail", cfg.output_tail_bytes) or b""
    total = int((exit_info or {}).get("output_bytes", len(head) + len(tail)))
    after_head = total - len(head)
    if after_head <= 0:
        raw, dropped = head, 0
    elif len(tail) >= after_head:
        raw, dropped = head + tail[len(tail) - after_head:], 0
    else:
        dropped = after_head - len(tail)
        raw = head[: cfg.classify_head_bytes] + MARKER.format(n=dropped).encode() + tail
    return raw.decode("utf-8", "replace"), total, dropped


def log_tail(directory: Path, size: int, cap: int = 64 << 20) -> bytes:
    tail = read_bounded(directory / "output.tail", cap)
    if tail:
        return tail[-size:]
    return (read_bounded(directory / "output.log", cap) or b"")[-size:]


def read_claim(path: Path) -> dict | None:
    """What the agent said about itself (a CLAIM): bounded, parsed, never trusted."""
    raw = read_bounded(path, REPORT_MAX)
    if raw is None:
        return {"unreadable": "report absent, not a regular file, or larger than the cap"} if path.is_symlink() or \
            (path.exists() and not path.is_file()) or (path.is_file() and path.stat().st_size > REPORT_MAX) else None
    try:
        value = json.loads(raw.decode("utf-8"))
    except ValueError:
        return None
    if not isinstance(value, dict):
        return None
    return {"status": str(value.get("status", ""))[:20], "summary": str(value.get("summary", ""))[:400],
            "claimed": True}
