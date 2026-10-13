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

import bt_agents
from bt_core import STATE
from bt_runtier import start_tier

LOG_KEEP = 200
DEFAULT_LIMITS = {"max_attempts": 4, "session_timeout_min": 60, "max_sessions": 300, "workers": 1}  # 4 = haiku, sonnet, opus, opus
TASK_RE = re.compile(r"^\s*[-*]\s+\[( |x|X)\]\s+(T\d+(?:\.\d+)?[a-z]?)\s*(?:—|–|--|-|:)\s*(.+?)\s*$")
MILESTONE_RE = re.compile(r"^#{3,4}\s+(M\d+)\b\s*(?:—|–|--|-|:)?\s*(.*?)\s*$")
HEADING_RE = re.compile(r"^#{1,4}\s+\S")
AUDIT_SUFFIX = "-audit"
MILESTONE_TIMEOUT_FACTOR = 3  # a milestone session gets at most this many task timeouts


def now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def _parse_time(text: str | None) -> dt.datetime | None:
    try:
        return dt.datetime.fromisoformat(text) if text else None
    except ValueError:
        return None


# ---------------------------------------------------------------- PLAN.md tasks

def parse_task_line(rest: str) -> dict:
    """'<title> · repo: x · after: T1, T2 · verify: `cmd` · level: architecture · covers: R1' -> task fields
    (verify only if backticked)."""
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
    title = parts[0].strip()
    return {"title": title, "repo": fields.get("repo") or None, "verify": verify,
            "after": [t for t in re.split(r"[,\s]+", fields.get("after", "")) if re.fullmatch(r"T\d+(?:\.\d+)?[a-z]?", t)],
            "level": (fields.get("level") or "").lower() or None,
            "kind": bt_agents.infer_kind(title, fields.get("kind")),
            "risk": (fields.get("risk") or "").lower() or None,
            "complexity": _complexity(fields.get("complexity") or fields.get("size"))}


def _complexity(text: str | None) -> str | None:
    """`complexity: S|M|L` (also small/medium/large, low/med/high) on the PLAN line; None when not declared."""
    word = (text or "").strip().lower()
    return {"s": "S", "small": "S", "low": "S", "m": "M", "medium": "M", "med": "M", "l": "L", "large": "L",
            "high": "L", "xl": "L"}.get(word)


def parse_plan(plan: Path) -> list[dict]:
    try:
        text = re.sub(r"<!--.*?-->", "", plan.read_text(encoding="utf-8"), flags=re.S)
    except OSError:
        return []
    tasks, milestone = [], None
    for line in text.splitlines():
        head = MILESTONE_RE.match(line)
        if head:  # `### M2 — title`: the tasks below belong to it until the next heading
            milestone = head.group(1)
            continue
        if HEADING_RE.match(line):
            milestone = None
            continue
        m = TASK_RE.match(line)
        if m:
            tasks.append({"id": m.group(2), "done": m.group(1) != " ", "milestone": milestone,
                          **parse_task_line(m.group(3))})
    return tasks


def milestones(plan: Path) -> list[dict]:
    """[{id, title, tasks: [ids]}] in plan order; [] for a plan without `### Mn` groups."""
    try:
        text = re.sub(r"<!--.*?-->", "", plan.read_text(encoding="utf-8"), flags=re.S)
    except OSError:
        return []
    titles = {m.group(1): m.group(2) for m in map(MILESTONE_RE.match, text.splitlines()) if m}
    out: dict[str, dict] = {}
    for t in parse_plan(plan):
        if t.get("milestone"):
            out.setdefault(t["milestone"], {"id": t["milestone"], "title": titles.get(t["milestone"], ""),
                                            "tasks": []})["tasks"].append(t["id"])
    return list(out.values())


def _new_task(p: dict) -> dict:
    return {"id": p["id"], "title": p["title"], "repo": p["repo"], "after": p["after"], "verify": p["verify"],
            "level": p["level"], "kind": p.get("kind") or "implement", "risk": p.get("risk"),
            "complexity": p.get("complexity"),
            "milestone": p.get("milestone"), "tier": start_tier(p["level"], p.get("kind"), p.get("complexity")),
            "status": "done" if p["done"] else "todo",
            "attempts": 0, "last_error": None, "error_hashes": [], "evidence": None, "pending_id": None, "notes": []}


def _audit_task(milestone: str, members: list[dict], fresh: bool) -> dict:
    """The independent audit that closes a milestone: runs after its tasks, re-runs their verifies, may fix. Only a
    milestone that was already ticked when the run was CREATED is taken as audited; on any later sync (a resume, an
    old RUN.json gaining audits) the audit is real work to do."""
    done = fresh and bool(members) and all(m["status"] == "done" and m.get("attempts", 0) == 0 for m in members)
    return {"id": milestone + AUDIT_SUFFIX, "title": f"Independent audit of milestone {milestone}", "repo": None,
            "after": [m["id"] for m in members], "verify": None, "level": None, "kind": "audit", "risk": None,
            "milestone": milestone, "synthetic": True, "tier": start_tier(None, "audit"),
            "status": "done" if done else "todo", "attempts": 0, "last_error": None, "error_hashes": [],
            "evidence": "already ticked in the approved plan" if done else None, "pending_id": None, "notes": []}


def _sync_audits(state: dict) -> None:
    """One audit task per milestone, placed right after the milestone's last task (plan order = run order)."""
    if not state.get("audit"):  # turned off (run --no-audit): audits that never ran are dropped, finished ones stay
        state["tasks"] = [t for t in state["tasks"] if not (t.get("synthetic") and t["status"] != "done")]
        return
    fresh = not state.get("sessions") and not state.get("log")
    have = {t["id"] for t in state["tasks"]}
    groups: dict[str, list[dict]] = {}
    for t in state["tasks"]:
        if t.get("milestone") and not t.get("synthetic"):
            groups.setdefault(t["milestone"], []).append(t)
    for milestone, members in groups.items():
        aid = milestone + AUDIT_SUFFIX
        if aid in have:
            audit = get_task(state, aid)
            ids = [m["id"] for m in members]
            if audit["after"] != ids:
                if audit["status"] == "done" and set(ids) - set(audit["after"]):  # new work joined an audited milestone
                    audit.update(status="todo", evidence=None, attempts=0)
                audit["after"] = ids
            continue
        at = max(state["tasks"].index(m) for m in members) + 1
        state["tasks"].insert(at, _audit_task(milestone, members, fresh))


def sync_plan(state: dict, rdir: Path) -> dict:
    """Merge PLAN.md into the state. New tasks are added and titles refreshed. What the supervisor acts on
    (verify, after, repo, level) and the done status are frozen from the approved plan: a change in PLAN.md is only reported
    in state['plan_drift'], never adopted, so the agent cannot rewrite its own gate or tick its way past verify."""
    by_id = {t["id"]: t for t in state["tasks"]}
    drift = []
    for p in parse_plan(rdir / "PLAN.md"):
        t = by_id.get(p["id"])
        if t is None:
            state["tasks"].append(_new_task(p))
            continue
        t["title"] = p["title"]
        for key in ("milestone", "kind", "risk", "complexity"):  # a RUN.json from before these fields existed adopts them once
            if key not in t:
                t[key] = p.get(key)
        drift += [f"{t['id']}.{k}" for k in ("repo", "after", "verify", "level") if t.get(k) != p[k]]
    state["plan_drift"] = drift
    _sync_audits(state)
    return state


def init_state(project: str, rdir: Path, agent: str, model: str | None, ultracode: bool,
               limits: dict | None = None, pool: list[str] | None = None, audit: bool = False) -> dict:
    state = {"req": "-".join(rdir.name.split("-")[:2]), "project": project, "status": "running", "agent": agent,
             "model": model, "ultracode": ultracode, "limits": {**DEFAULT_LIMITS, **(limits or {})},
             "control": None, "heartbeat": None, "waiting_until": None, "sessions": 0, "tasks": [], "log": [],
             "pool": list(pool or []), "audit": bool(audit)}
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


def unit_of(state: dict, first: dict) -> list[dict]:
    """The tasks one session takes: a task of a milestone brings along the milestone's other pending tasks whose
    dependencies are done or inside the unit (plan order). A task outside a milestone, and an audit, run alone."""
    if not first.get("milestone") or first.get("kind") == "audit" or first.get("synthetic"):
        return [first]
    done = {t["id"] for t in state["tasks"] if t["status"] == "done"}
    unit, ids = [first], {first["id"]}
    grew = True
    while grew:  # every pending member whose dependencies are done or already in the unit, wherever it sits in the plan
        grew = False
        for t in state["tasks"]:
            if (t["id"] not in ids and t["status"] == "todo" and t.get("milestone") == first["milestone"]
                    and not t.get("synthetic") and all(a in done or a in ids for a in t["after"])):
                unit.append(t)
                ids.add(t["id"])
                grew = True
    order = {t["id"]: i for i, t in enumerate(state["tasks"])}
    return sorted(unit, key=lambda t: order[t["id"]])


def next_unit(state: dict) -> list[dict]:
    first = next_task(state)
    return unit_of(state, first) if first else []


def unit_label(unit: list[dict]) -> str:
    """What a session is called in logs: the task id, or the milestone when it carries several tasks."""
    if len(unit) == 1:
        return unit[0]["id"]
    return unit[0].get("milestone") or ",".join(t["id"] for t in unit)


def unit_tier(unit: list[dict]) -> int:
    from bt_runtier import tier_of
    return max(tier_of(t) for t in unit)


def unit_kind(unit: list[dict]) -> str:
    kinds = {t.get("kind") or "implement" for t in unit}
    return kinds.pop() if len(kinds) == 1 else "implement"


def builders_of(state: dict, audit: dict) -> set:
    """Providers that built the work an audit reviews (so the router can pick another one)."""
    out = set()
    for tid in audit.get("after") or []:
        member = get_task(state, tid) or {}
        route = member.get("last_route") or {}
        if route.get("agent"):
            out.add(route["agent"])
        elif member.get("status") == "done" and member.get("attempts") is not None and state.get("agent"):
            out.add(state["agent"])  # built before routes were recorded: the run's own agent did it
    return out


MAX_WORKERS = 2  # until the machine's behaviour under several agent sessions has been measured


def ready_units(state: dict, workers: int = 1) -> list[list[dict]]:
    """Units that may run at the same time: ready_batch's rule applied to whole units. Further units join only when
    every task of both names a repo role and the role sets do not overlap."""
    first = next_unit(state)
    if not first:
        return []
    cap = max(1, min(int(workers or 1), MAX_WORKERS))
    units = [first]
    if cap == 1 or any(not t.get("repo") for t in first):
        return units
    done = {t["id"] for t in state["tasks"] if t["status"] == "done"}
    taken_repos = {t["repo"] for t in first} | {t.get("repo") for t in state["tasks"] if t["status"] == "in_progress"}
    taken_ids = {t["id"] for t in first}
    for t in state["tasks"]:
        if len(units) >= cap:
            break
        if t["id"] in taken_ids or t["status"] != "todo" or not all(a in done for a in t["after"]):
            continue
        unit = unit_of(state, t)
        repos = {u.get("repo") for u in unit}
        if None in repos or repos & taken_repos or any(u["id"] in taken_ids for u in unit):
            continue
        units.append(unit)
        taken_repos |= repos
        taken_ids |= {u["id"] for u in unit}
    return units


def ready_batch(state: dict, workers: int = 1) -> list[dict]:
    """Tasks that may run at the same time, in plan order. The first runnable task always runs; further tasks join only
    when everything is safe: both name a repo role, the roles differ, and no task of that role is already in
    progress. A task without a repo role (workspace root) may touch anything, so it runs alone. Two sessions are
    therefore never editing the same repository."""
    done = {t["id"] for t in state["tasks"] if t["status"] == "done"}
    busy = {t.get("repo") for t in state["tasks"] if t["status"] == "in_progress"}
    runnable = [t for t in state["tasks"] if t["status"] == "todo" and all(a in done for a in t["after"])]
    if busy:  # something is still running: never start a task on that repo, nor an unscoped one
        runnable = [t for t in runnable if t.get("repo") and t["repo"] not in busy]
    if not runnable:
        return []
    first = runnable[0]
    cap = max(1, min(int(workers or 1), MAX_WORKERS))
    batch = [first]
    if cap == 1 or not first.get("repo"):
        return batch
    taken = {first["repo"]} | busy
    for t in state["tasks"]:
        if len(batch) >= cap:
            break
        if (t is first or t["status"] != "todo" or not t.get("repo") or t["repo"] in taken
                or not all(a in done for a in t["after"])):
            continue
        batch.append(t)
        taken.add(t["repo"])
    return batch


def mark(state: dict, task_id: str, status: str, **fields) -> dict:
    t = get_task(state, task_id)
    if t is None:
        raise SystemExit(f"{task_id} is not in RUN.json")
    t["status"] = status
    t.update(fields)
    return t


def record(state: dict, session: int, task_id: str, result: str, summary: str, seconds: int, **extra) -> None:
    """Append a log entry; extra = what the session ran with (model, effort, cost_usd, early_exit)."""
    state.setdefault("log", []).append({"at": now_iso(), "session": session, "task": task_id, "result": result,
                                         "summary": " ".join(summary.split())[:300], "seconds": int(seconds),
                                         **{k: v for k, v in extra.items() if v is not None}})
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
