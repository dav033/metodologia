"""Marathon run state: RUN.json, the supervisor's on-disk memory for one requirement.

Lives in <project>/requirements/REQ-NNN-slug/RUN.json (synced by git, so a run survives a reboot or a machine
change). Writers (supervisor, agent CLI `task done/fail/note`, web buttons) never hold the file in memory across a
session: they go through `update()`, which locks, reloads, applies one change and saves atomically.
Shape and rules: references/marathon.md.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import json
import os
import re
import socket
import time
from pathlib import Path

from bt_core import STATE

LOG_KEEP = 200
DEFAULT_LIMITS = {"max_attempts": 3, "session_timeout_min": 60, "max_sessions": 300}
TASK_RE = re.compile(r"^\s*[-*]\s+\[( |x|X)\]\s+(T\d+(?:\.\d+)?[a-z]?)\s*(?:—|–|--|-|:)\s*(.+?)\s*$")


def now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def _parse_time(text: str | None) -> dt.datetime | None:
    try:
        return dt.datetime.fromisoformat(text) if text else None
    except ValueError:
        return None


# ---------------------------------------------------------------- PLAN.md tasks

def parse_task_line(rest: str) -> dict:
    """'<title> · repo: x · after: T1, T2 · verify: `cmd` · covers: R1' -> task fields (verify only if backticked)."""
    verify = None
    m = re.search(r"verify:\s*`([^`]+)`", rest)
    if m:
        verify = m.group(1).strip()
        rest = rest[:m.start()] + "verify:" + rest[m.end():]
    parts = re.split(r"\s+·\s+", rest)
    fields = {}
    for p in parts[1:]:
        key, _, value = p.partition(":")
        fields[key.strip().lower()] = value.strip()
    return {"title": parts[0].strip(), "repo": fields.get("repo") or None, "verify": verify,
            "after": [t for t in re.split(r"[,\s]+", fields.get("after", "")) if re.fullmatch(r"T\d+(?:\.\d+)?[a-z]?", t)]}


def parse_plan(plan: Path) -> list[dict]:
    try:
        text = re.sub(r"<!--.*?-->", "", plan.read_text(encoding="utf-8"), flags=re.S)
    except OSError:
        return []
    tasks = []
    for line in text.splitlines():
        m = TASK_RE.match(line)
        if m:
            tasks.append({"id": m.group(2), "done": m.group(1) != " ", **parse_task_line(m.group(3))})
    return tasks


def _new_task(p: dict) -> dict:
    return {"id": p["id"], "title": p["title"], "repo": p["repo"], "after": p["after"], "verify": p["verify"],
            "status": "done" if p["done"] else "todo", "attempts": 0, "last_error": None, "error_hashes": [],
            "evidence": None, "pending_id": None, "notes": []}


def sync_plan(state: dict, rdir: Path) -> dict:
    """Merge PLAN.md into the state. New tasks are added and titles refreshed. What the supervisor acts on
    (verify, after, repo) and the done status are frozen from the approved plan: a change in PLAN.md is only reported
    in state['plan_drift'], never adopted, so the agent cannot rewrite its own gate or tick its way past verify."""
    by_id = {t["id"]: t for t in state["tasks"]}
    drift = []
    for p in parse_plan(rdir / "PLAN.md"):
        t = by_id.get(p["id"])
        if t is None:
            state["tasks"].append(_new_task(p))
            continue
        t["title"] = p["title"]
        drift += [f"{t['id']}.{k}" for k in ("repo", "after", "verify") if t.get(k) != p[k]]
    state["plan_drift"] = drift
    return state


def init_state(project: str, rdir: Path, agent: str, model: str | None, ultracode: bool,
               limits: dict | None = None) -> dict:
    state = {"req": "-".join(rdir.name.split("-")[:2]), "project": project, "status": "running", "agent": agent,
             "model": model, "ultracode": ultracode, "limits": {**DEFAULT_LIMITS, **(limits or {})},
             "control": None, "heartbeat": None, "waiting_until": None, "sessions": 0, "tasks": [], "log": []}
    return sync_plan(state, rdir)


# ---------------------------------------------------------------- persistence

def run_path(rdir: Path) -> Path:
    return Path(rdir) / "RUN.json"


class RunStateError(RuntimeError):
    """RUN.json exists but could not be read (locked by git/AV/web, or corrupt)."""


def load(rdir: Path) -> dict | None:
    """The state, or None if RUN.json does not exist. Raises RunStateError if it exists but stays unreadable."""
    last = None
    for attempt in range(8):  # a concurrent atomic replace or a scanner can make a read fail for a moment on Windows
        try:
            return json.loads(run_path(rdir).read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        except (OSError, ValueError) as exc:
            last = exc
            time.sleep(0.25)
    raise RunStateError(f"cannot read {run_path(rdir)}: {last}")


def save(rdir: Path, state: dict) -> None:
    state["log"] = state.get("log", [])[-LOG_KEEP:]
    target = run_path(rdir)
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=1, ensure_ascii=False), encoding="utf-8")
    for attempt in range(10):
        try:
            os.replace(tmp, target)
            return
        except PermissionError:
            time.sleep(0.1)
    target.write_text(tmp.read_text(encoding="utf-8"), encoding="utf-8")


@contextlib.contextmanager
def _locked(rdir: Path, timeout: float = 10.0):
    lock_dir = STATE / "locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock = lock_dir / f"{Path(rdir).parents[1].name}-{Path(rdir).name}.lock"
    deadline, fd = time.time() + timeout, None
    while fd is None:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                if time.time() - lock.stat().st_mtime > 30:  # a crashed writer left it behind
                    lock.unlink(missing_ok=True)
                    continue
            except OSError:
                pass
            if time.time() > deadline:
                break  # better a rare unlocked write than a stuck supervisor
            time.sleep(0.05)
    try:
        yield
    finally:
        if fd is not None:
            os.close(fd)
            lock.unlink(missing_ok=True)


def update(rdir: Path, fn) -> dict:
    """Locked read-modify-write: fn(state) mutates the freshly loaded state; returns the saved state."""
    with _locked(rdir):
        state = load(rdir)
        if state is None:
            raise SystemExit(f"No RUN.json in {rdir}. Start the marathon first: bitacora.py run {rdir.name[:7]}")
        fn(state)
        save(rdir, state)
        return state


# ---------------------------------------------------------------- state operations

def get_task(state: dict, task_id: str) -> dict | None:
    return next((t for t in state["tasks"] if t["id"] == task_id), None)


def next_task(state: dict) -> dict | None:
    done = {t["id"] for t in state["tasks"] if t["status"] == "done"}
    return next((t for t in state["tasks"] if t["status"] == "todo" and all(a in done for a in t["after"])), None)


def mark(state: dict, task_id: str, status: str, **fields) -> dict:
    t = get_task(state, task_id)
    if t is None:
        raise SystemExit(f"{task_id} is not in RUN.json")
    t["status"] = status
    t.update(fields)
    return t


def record(state: dict, session: int, task_id: str, result: str, summary: str, seconds: int) -> None:
    state.setdefault("log", []).append({"at": now_iso(), "session": session, "task": task_id, "result": result,
                                         "summary": " ".join(summary.split())[:300], "seconds": int(seconds)})
    state["log"] = state["log"][-LOG_KEEP:]


def heartbeat(run: dict, /, **fields) -> dict:
    """Stamp the run's heartbeat; `state=` is a free-text field of the heartbeat itself, hence positional-only."""
    hb = run.get("heartbeat") or {}
    hb.update({"at": now_iso(), "pid": os.getpid(), "machine": socket.gethostname()})
    hb.update(fields)
    run["heartbeat"] = hb
    return hb


def is_stale(state: dict, minutes: float) -> bool:
    at = _parse_time((state.get("heartbeat") or {}).get("at"))
    return at is None or dt.datetime.now() - at > dt.timedelta(minutes=minutes)


def progress(state: dict) -> tuple[int, int]:
    return sum(t["status"] == "done" for t in state["tasks"]), len(state["tasks"])


_HEX = re.compile(r"\b(?=[0-9a-f]*\d)[0-9a-f]{7,}\b|\b0x[0-9a-f]+\b")
_PATH = re.compile(r"[a-z]:[\\/]\S*|(?<![\w.])/[\w.\-]+(?:/[\w.\-]*)*")


def error_hash(text: str) -> str:
    """Same failure, different numbers/paths/ids -> same hash (so 'fails the same way twice' is detectable)."""
    t = _PATH.sub("<path>", (text or "").lower())
    t = _HEX.sub("<hex>", t)
    t = re.sub(r"\d+", "<n>", t)
    return hashlib.sha1(" ".join(t.split()).encode("utf-8")).hexdigest()[:12]
