"""Live API: what is running right now, and the flow events of the runs in a scope, as JSON and Server-Sent Events.

    now_items(root)               -> [{project, req_id, req_title, task, task_title, attempt{...}, progress{done,total}}]
    flow_events(root, scope, ...)  -> (events, digests, cursors)   # JSON replay: /api/flow
    run_summaries(root, scope)     -> [{run, title, status, summary, tasks[{id, state, attempt, history}]}]
    stream(handler, root, scope, last_id)                          # SSE: /live?scope=...

Each run's bus is read to the end once and then followed (`_RunLog`, shared by every reader): the newest KEEP messages
are kept, and the quiet provider detail (`bt_flow_bus.is_quiet`) is folded into one digest per attempt, so a run whose
stream produced 100 000 rows still answers with its few hundred real messages.

Scopes: `global`, `project:<p>`, `run:<p>/<REQ>`, `task:<p>/<REQ>/<T>`. A client resumes with `Last-Event-ID` (the `ord`
of the last event it saw): the stores are the log, so a resume re-reads them and drops what the client already has.
Everything is read-only (`bt_flow_bus`, `bt_planstatus`); the bus is polled every POLL seconds.
"""
from __future__ import annotations

import json
import select
import socket
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any

import bt_core
import bt_flow_bus as bus
import bt_presence
import bt_planstatus as ps
import bt_scheduler_adapter as scheduler_

POLL = 0.25
NOW_EVERY = 5.0              # the "now" list is also refreshed on a timer so durations and token counts keep moving
KEEPALIVE_SEC = 15
MAX_CLIENTS = 20
KEEP = 5000                  # messages kept in memory per run (the newest); the stores keep everything
CATCH_UP = 200               # bus cycles per read at most (LIMIT rows per store each): bounds the first read of a run
_slots = threading.BoundedSemaphore(MAX_CLIENTS)
_logs: dict[str, "_RunLog"] = {}
_logs_lock = threading.Lock()


def _root(root: Path | None) -> Path:
    return Path(root if root is not None else bt_core.ROOT).resolve()


RUNS_TTL = 2.0               # every live client polls the run list 4 times a second: one directory scan serves them all
_runs_seen: dict[Path, tuple[float, list[tuple[str, Path]]]] = {}


def runs(root: Path | None = None) -> list[tuple[str, Path]]:
    """Every requirement whose runtime is the Scheduler: (project, requirement dir)."""
    base = _root(root)
    at, found = _runs_seen.get(base, (0.0, []))
    if time.monotonic() - at > RUNS_TTL:
        found = [(project, rdir) for project, rdir in ps._requirement_dirs(base)
                 if scheduler_.authority(rdir) == "scheduler"]
        _runs_seen[base] = (time.monotonic(), found)
    return list(found)


def warm(root: Path | None = None) -> threading.Thread:
    """Read every run's bus once in the background, so the first visit to /flow does not pay for a long history."""
    thread = threading.Thread(target=lambda: flow_events(root, "global", limit=0), name="flow-warm", daemon=True)
    thread.start()
    return thread


def parse_scope(scope: str) -> tuple[str, str | None, str | None, str | None]:
    kind, _, rest = (scope or "global").partition(":")
    bits = [b for b in rest.split("/") if b]
    if kind == "project" and len(bits) == 1:
        return kind, bits[0], None, None
    if kind == "run" and len(bits) == 2:
        return kind, bits[0], bits[1], None
    if kind == "task" and len(bits) == 3:
        return kind, bits[0], bits[1], bits[2]
    return "global", None, None, None


def runs_in_scope(root: Path | None, scope: str) -> list[tuple[str, Path]]:
    kind, project, req, _ = parse_scope(scope)
    found = runs(root)
    if kind in ("project", "run", "task"):
        found = [(p, r) for p, r in found if p == project]
    if kind in ("run", "task"):
        found = [(p, r) for p, r in found if r.name.startswith(f"{req}-") or r.name == req]
    return found


def now_items(root: Path | None = None) -> list[dict[str, Any]]:
    """The attempts alive at this moment in every project, newest start first."""
    items = []
    for project, rdir in runs(root):
        status = ps.plan_status(project, rdir)
        if not status["run"]["active"]:
            continue
        progress = {"done": status["summary"]["tasks_done"], "total": status["summary"]["tasks_total"]}
        for milestone in status["milestones"]:
            for task in milestone["tasks"]:
                live = [a for a in task["history"] if a.get("live")]
                if not live:
                    continue
                items.append({"project": project, "req_id": status["req_id"], "req_title": status["title"],
                              "task": task["id"], "task_title": task["title"], "complexity": task["complexity"],
                              "state": task["state"], "attempt": live[-1], "route": task.get("route"),
                              "progress": progress, "run_status": status["run"]["status"]})
    items.sort(key=lambda i: i["attempt"].get("started_at") or "", reverse=True)
    return items


def sessions(root: Path | None = None) -> list[dict[str, Any]]:
    """Agent sessions seen recently (working first): planning a requirement, building, or idle."""
    return bt_presence.sessions(_root(root))


def _planning_events(root: Path | None, scope: str, after_ord: str, cursors: dict[str, dict[str, int]] | None
                     ) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Planning edits by agent sessions as `agent -> planner` messages (the Planeación module talking)."""
    kind, project, req, _ = parse_scope(scope)
    if kind in ("run", "task"):
        return [], {}
    after = int(((cursors or {}).get("presence/planning") or {}).get("line", 0))
    rows = bt_presence.planning_events(_root(root), after)
    events, last = [], after
    for row in rows:
        last = max(last, row["id"])
        if kind == "project" and row.get("project") != project:
            continue
        run = f'{row.get("project") or "?"}/{row["req"]}'
        events.append(bus.event(run, "presence", row["id"], float(row["at"]), "agent", "planner", "planning",
                                f'Agente trabaja en {row["stage"]} de {row["req"]}', from_part=row.get("session", "")))
    return [e for e in events if e["ord"] > after_ord], {"line": last}


def _match(event: dict[str, Any], task: str | None) -> bool:
    return task is None or event.get("task") == task


class _RunLog:
    """One run's bus, read to the end and followed. Every change gets a serial, so a live client asks only for what
    is new since its own serial, whatever order the stores reveal their rows in."""

    def __init__(self, rdir: Path, project: str):
        self.rdir, self.project = rdir, project
        self.cursors: dict[str, int] | None = None
        self.serial = 0
        self.events: list[dict[str, Any]] = []                          # the newest KEEP messages, by ord
        self.fresh: deque[tuple[int, dict[str, Any]]] = deque(maxlen=KEEP)  # (serial, message), in arrival order
        self.digests: dict[str, dict[str, Any]] = {}                    # "run|attempt" -> quiet detail, folded
        self.changed: dict[str, int] = {}                               # digest key -> serial of its last change
        self.files: dict[str, tuple[str, int]] = {}                     # store -> (path, inode) the cursor points into
        self.read_at = 0.0
        self.lock = threading.Lock()

    def advance(self, max_age: float = 0.0) -> None:
        """Read what the stores added since the last read. `max_age` lets many live clients share one recent read."""
        with self.lock:
            if max_age and time.monotonic() - self.read_at < max_age:
                return
            files = bus.sources(self.rdir, self.project)
            if self.cursors is not None:
                for name, ident in files.items():
                    if self.files.get(name) != ident:
                        self.cursors[name] = 0          # a new ledger or a recreated store: read it from its start
            self.files = files
            added = False
            for _ in range(CATCH_UP):
                batch, self.cursors = bus.collect(self.rdir, self.project, self.cursors)
                for e in batch:
                    self.serial += 1
                    if e.get("quiet"):
                        self._fold(e)
                    else:
                        self.fresh.append((self.serial, e))
                        self.events.append(e)
                        added = True
                if not batch:
                    break
            if added:
                self.events.sort(key=lambda e: e["ord"])
                del self.events[:-KEEP]
            self.read_at = time.monotonic()

    def _fold(self, e: dict[str, Any]) -> None:
        key = f'{e["run"]}|{e.get("attempt") or ""}'
        d = self.digests.get(key)
        if d is None:
            d = self.digests[key] = {"v": bus.VERSION, "seq": f"digest:{key}", "run": e["run"], "task": None,
                                     "attempt": e.get("attempt"), "from": "M3", "to": "M4", "kind": "digest",
                                     "first_epoch": e["at_epoch"], "at_epoch": 0.0, "stream": 0, "incidents": 0,
                                     "types": {}}
        d["task"] = d["task"] or e.get("task")
        if e["kind"] == "stream":
            d["stream"] += 1
            data = e.get("data") or {}
            label = str(data.get("cause") or data.get("event_type") or "?")
            d["types"][label] = d["types"].get(label, 0) + 1
        elif e["kind"] == "incident":                   # M4's report to M1; incident_detected is M4's own copy
            d["incidents"] += 1
        d["first_epoch"] = min(d["first_epoch"], e["at_epoch"])
        if e["at_epoch"] >= d["at_epoch"]:
            d["at_epoch"], d["at"], d["ord"] = e["at_epoch"], e["at"], e["ord"]
        d["count"] = d["stream"] + d["incidents"]
        top = sorted(d["types"].items(), key=lambda kv: -kv[1])[:3]
        d["summary"] = (f'Detalle del proveedor: {d["stream"]} eventos de flujo'
                        + (f' ({", ".join(f"{k} {n}" for k, n in top)})' if top else "")
                        + (f' y {d["incidents"]} avisos informativos' if d["incidents"] else ""))
        self.changed[key] = self.serial

    def since(self, serial: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
        events = [e for s, e in self.fresh if s > serial]
        digests = [dict(self.digests[k]) for k, s in self.changed.items() if s > serial]
        return events, digests, self.serial


def _log(rdir: Path, project: str) -> _RunLog:
    key = str(Path(rdir).resolve())
    with _logs_lock:
        if key not in _logs:
            _logs[key] = _RunLog(Path(rdir), project)
        return _logs[key]


def flow_events(root: Path | None, scope: str, after_ord: str = "", cursors: dict[str, Any] | None = None,
                limit: int = 2000, max_age: float = 0.0) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Messages of the scope and the digests of their quiet detail, plus the cursors to follow them.

    Without cursors: the newest `limit` messages with `ord` > after_ord (oldest first) and every digest. With the
    cursors a previous call returned: only what arrived since, messages and changed digests."""
    _, _, _, task = parse_scope(scope)
    out: list[dict[str, Any]] = []
    digests: list[dict[str, Any]] = []
    new: dict[str, Any] = {}
    for project, rdir in runs_in_scope(root, scope):
        key = f"{project}/{rdir.name}"
        log = _log(rdir, project)
        log.advance(max_age)
        with log.lock:
            if cursors is None:
                events, found, new[key] = list(log.events), [dict(d) for d in log.digests.values()], log.serial
            else:
                events, found, new[key] = log.since(int(cursors.get(key, 0)))
        out.extend(e for e in events if e["ord"] > after_ord and _match(e, task))
        digests.extend(d for d in found if _match(d, task))
    planning, new["presence/planning"] = _planning_events(root, scope, after_ord, cursors)
    out.extend(e for e in planning if _match(e, task))
    out.sort(key=lambda e: e["ord"])
    return out[-limit:] if limit else [], digests, new


def _attempt(a: dict[str, Any] | None) -> dict[str, Any] | None:
    if not a:
        return None
    keys = ("id", "number", "state", "provider", "effort", "account", "started_at", "ended_at", "duration_s", "live",
            "verdict", "failure", "last_activity_at")
    return {**{k: a.get(k) for k in keys}, "model": a.get("model_reported") or a.get("model_requested")}


def agent_activity(root: Path | None, run: str) -> dict[str, dict[str, Any]]:
    """What each live attempt of one run (`project/REQ-NNN`) is doing right now, from its own log (`bt_agent_now`)."""
    import bt_agent_now
    project, _, req = (run or "").partition("/")
    for found_project, rdir in runs_in_scope(root, f"run:{project}/{req}"):
        status = ps.plan_status(found_project, rdir)
        live = [t["attempt"]["id"] for m in status["milestones"] for t in m["tasks"]
                if t.get("attempt") and t["attempt"].get("live") and t["attempt"].get("id")]
        return bt_agent_now.now(rdir, found_project, live)
    return {}


def run_summaries(root: Path | None, scope: str) -> list[dict[str, Any]]:
    """Each run of the scope as the plan sees it (`bt_planstatus`, the authority on task state), newest change first."""
    out = []
    for project, rdir in runs_in_scope(root, scope):
        try:
            status = ps.plan_status(project, rdir)
        except Exception:                               # one unreadable plan must not blank the whole map
            continue
        tasks = [{"id": t["id"], "title": t["title"], "objective": (t.get("detail") or {}).get("objective"),
                  "milestone_id": t.get("milestone_id"), "state": t["state"],
                  "attempts": t["attempts"], "attempt": _attempt(t.get("attempt")),
                  "attempts_used": t.get("attempts_used"), "max_attempts": t.get("max_attempts"),
                  "retries_remaining": t.get("retries_remaining"),
                  "retry_exhausted": t.get("retry_exhausted"), "reason": t.get("reason"),
                  "history": [_attempt(a) for a in t.get("history") or []]}
                 for m in status["milestones"] for t in m["tasks"]]
        out.append({"run": f'{project}/{status["req_id"]}', "project": project, "req_id": status["req_id"],
                    "title": status["title"], "status": status["run"].get("status"), "active": status["run"].get("active"),
                    "updated_at": status["run"].get("updated_at"), "summary": status["summary"], "tasks": tasks})
    out.sort(key=lambda r: r["updated_at"] or "", reverse=True)
    out.sort(key=lambda r: not r["active"])            # live runs first, each group newest first
    return out


NOW_TTL = 1.0                # one "now" frame serves every live client for a second (it reads every run's plan)
_now_cache: dict[Path, tuple[float, bytes]] = {}
_now_data_cache: dict[Path, tuple[float, dict[str, Any]]] = {}
_now_lock = threading.Lock()


def now_frame_data(root: Path | None) -> dict[str, Any]:
    """Return the shared, one-second now read model used by SSE and remote snapshots."""
    base = _root(root)
    with _now_lock:
        at, payload = _now_data_cache.get(base, (0.0, {}))
        if time.monotonic() - at > NOW_TTL:
            payload = {"items": now_items(root), "sessions": sessions(root)}
            _now_data_cache[base] = (time.monotonic(), payload)
        return payload


def _now_frame(root: Path | None) -> bytes:
    import bt_page_now          # the web layer renders the fragments; this module only decides when to send them
    base = _root(root)
    now_frame_data(root)
    with _now_lock:
        at, payload = _now_data_cache.get(base, (0.0, {}))
        frame_at, frame = _now_cache.get(base, (0.0, b""))
        if frame and frame_at == at:
            return frame
        data = {**payload, "html": bt_page_now.fragments(payload["items"], payload["sessions"])}
        frame = _frame("now", data)
        _now_cache[base] = (at, frame)
        return frame


def _frame(name: str, data: Any, ident: str = "") -> bytes:
    head = f"id: {ident}\n" if ident else ""
    return f"{head}event: {name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n".encode()


def stream(handler, root: Path | None, scope: str, last_id: str = "") -> None:
    """Serve one SSE client until it disconnects. `flow` events carry the bus events; `now` the live attempts."""
    if not _slots.acquire(blocking=False):
        return handler.send("Demasiados clientes en vivo", 503, "text/plain")
    try:
        handler.send_response(200)
        for key, value in (("Content-Type", "text/event-stream; charset=utf-8"), ("Cache-Control", "no-store"),
                           ("X-Accel-Buffering", "no"), ("Connection", "close")):
            handler.send_header(key, value)
        handler.end_headers()
        handler.close_connection = True
        out = handler.wfile
        out.write(b"retry: 2000\n: connected\n\n")
        # without a Last-Event-ID the client starts at "now": skip the past instead of replaying it
        events, _, cursors = flow_events(root, scope, last_id)
        if last_id:
            for e in events:
                out.write(_frame("flow", e, e["ord"]))
        out.write(_now_frame(root))
        out.flush()
        last_beat = last_now = time.monotonic()
        while True:
            readable, _, _ = select.select([handler.connection], [], [], POLL)
            if readable and not handler.connection.recv(1, socket.MSG_PEEK):
                return
            events, digests, cursors = flow_events(root, scope, "", cursors, max_age=POLL * 0.8)
            tick = time.monotonic()
            wrote = bool(events or digests)
            for e in events:
                out.write(_frame("flow", e, e["ord"]))
            for d in digests:
                out.write(_frame("digest", d))
            if events or tick - last_now >= NOW_EVERY:
                out.write(_now_frame(root))
                last_now, wrote = tick, True
            if not wrote and tick - last_beat >= KEEPALIVE_SEC:
                out.write(b": keepalive\n\n")
                wrote = True
            if wrote:
                out.flush()
                last_beat = tick
    except (BrokenPipeError, ConnectionResetError, OSError, ValueError):
        return
    finally:
        _slots.release()
