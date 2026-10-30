"""The Solucionador (REQ-031): the rung after the durable healing, a full-access session that fixes a block at its origin.

On 2026-10-29 every block of pictures REQ-021 that D-167's healing could not answer waited for an operator session that
did by hand: read the evidence, find the origin (an integrator that could never merge, D-169; a verification killed by
a restart, D-171; a plan dependency nobody typed, D-165), fix it where it lives, regression, backup, integrate, restart,
record a rule. This module makes the engine start that operator itself, from its maintenance pass, outside the
workflows (the order of steps in bt.run/bt.task is unchanged; no DBOS.patch is needed).

Triggers (`Trigger`), each launched at most once per key:
- `decision`: healing left an open decision for the owner (limit reached, diagnosis failed, low confidence, an option
  the diagnosis chose that is not offered, the plan blamed, no retry offered at all) — `healing.heal(escalate=...)`;
- `repeat`: the failure signature healing already answered came back in a later round;
- `stuck`: a PENDING task whose state did not move for `solver.stuck_minutes` beyond its known waits (a running agent
  gets `scheduler.attempt_timeout_minutes` more, a quota wait counts from its `until`, a pause or a decision never);
- `error`: the run workflow ended in ERROR;
- `stalled`: the run workflow is PENDING and not paused, but no task workflow is live (nothing runs, waits for quota or
  recovers) and no decision is open, unchanged for `solver.stuck_minutes`: pictures REQ-021 r25 sat like that while gate
  CG-7's composition failed every turn (a GitCommandError), and no other trigger saw it (2026-10-29);
- `resolution`: a composition conflict waits in `<state>/composition/resolutions/<key>.json` without `<key>.resolved`
  for `solver.resolution_after_seconds` (`bt_durable.resolutions`): no retry can settle it.

One session per run (`bit-<project>-<REQ>-solver` in the bitácora tmux socket), at most `solver.max_concurrent` on the
machine and `solver.max_per_task` per task; a trigger that finds its run's session busy is queued in that session's
`inbox.jsonl` and typed into it. A session gets a brief and a context bundle in `<rdir>/RUN.solver/<id>/`, runs on the
account `role_route(..., "solver")` picks (Claude Opus high, unattended, with quota; Codex otherwise), is moved to
another account when its own runs out, and is closed when it writes `result.json`, when its tmux session is gone, or
after `solver.max_minutes` (then `gave_up`, and the trigger is the owner's). State: `<rdir>/RUN.solver/state.json`
(the panel reads it). Nothing here claims a session runs exactly once: a crash between a launch and the state write
can start a second one on the next pass, which then finds the same tmux name taken and does not start.
"""
from __future__ import annotations

import hashlib
import json
import logging
import shlex
import shutil
import time
import uuid
from collections.abc import Callable, Iterable
from pathlib import Path

from . import healing

LOG = logging.getLogger("bt_durable.solver")
DIR = "RUN.solver"
STATE = "state.json"
OUTCOMES = ("fixed", "answered", "asked_owner", "gave_up")
OUTCOME_ES = {"fixed": "arreglado en su origen", "answered": "decisión respondida", "asked_owner": "te pregunta algo",
              "gave_up": "no pudo resolverlo"}
ERRORED = frozenset({"ERROR", "MAX_RECOVERY_ATTEMPTS_EXCEEDED"})
QUIET = frozenset({"paused", "needs_decision"})          # waiting for someone else: never "stuck"
MAX_RESTARTS = 2                                          # account moves per session (quota, an owner-only prompt)
WORK = Path.home() / ".local" / "share" / "bitacora-solver"   # sessions' working folders, outside every repository
RESTART_MESSAGE = ("You were restarted on another account (the previous one ran out). Your earlier conversation is above "
                   "when it could be kept; otherwise read BRIEF.md and NOTES.md in your session folder. Carry on.")


def enabled() -> bool:
    """The Solucionador runs only while the healing before it runs: it is the next rung, never the first."""
    import bt_config
    return bt_config.get("solver.enabled") is True and healing.enabled()


def settings() -> dict[str, int]:
    import bt_config
    defaults = {"max_concurrent": 1, "max_per_task": 3, "max_minutes": 120, "stuck_minutes": 45,
                "resolution_after_seconds": 120}
    out = {}
    for name, default in defaults.items():
        value = bt_config.get(f"solver.{name}", default)
        out[name] = value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else default
    attempt = bt_config.get("scheduler.attempt_timeout_minutes", 120)
    out["attempt_minutes"] = attempt if isinstance(attempt, int) and not isinstance(attempt, bool) else 120
    return out


def load(rdir: Path) -> dict:
    try:
        data = json.loads((Path(rdir) / DIR / STATE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    return data if isinstance(data, dict) else {}


def save(rdir: Path, data: dict) -> None:
    target = Path(rdir) / DIR / STATE
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f".{target.name}.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    tmp.replace(target)


def _iso(epoch: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(epoch))


def round_of(task: dict) -> int | None:
    return healing.round_of(task)


def trigger(kind: str, key: str, run_id: str, *, task_id: str = "", request_id: str = "", round_no: int | None = None,
            reason: str = "") -> dict:
    return {"kind": kind, "key": key, "run_id": run_id, "task_id": task_id, "request_id": request_id,
            "round": round_no, "reason": reason[:400]}


def error_triggers(run, status: dict) -> list[dict]:
    if status.get("workflow_status") in ERRORED:
        workflow = status.get("workflow_id") or f"bt:{run.run_id}"
        return [trigger("error", f"{run.run_id}:error:{workflow}", run.run_id,
                        reason=f"the run workflow {workflow} ended in {status['workflow_status']}")]
    return []


def _live_tasks(status: dict) -> list[str]:
    """Task workflows that still run (each is watched by `stuck_triggers`, or waits for the owner's decision)."""
    return [t for t, item in (status.get("tasks") or {}).items()
            if (item or {}).get("workflow_status") in ("PENDING", "ENQUEUED")]


def stalled_triggers(run, status: dict, state: dict, now: float, cfg: dict) -> list[dict]:
    """A PENDING, unpaused run workflow with no live task workflow, unchanged (summary and gates) for `stuck_minutes`.
    The `since` mark starts when the picture last changed, so an engine restart or a deploy never fires it at once.
    Updates `state["stall"]`."""
    summary = status.get("summary") if isinstance(status.get("summary"), dict) else None
    # no summary: the run workflow has not set its first one (it sets one before anything else), nothing to judge yet
    if status.get("workflow_status") != "PENDING" or not summary or summary.get("status") == "paused" \
            or _live_tasks(status):
        state.pop("stall", None)
        return []
    basis = json.dumps([status.get("workflow_id"), summary.get("status"), summary.get("tasks"), summary.get("gates")],
                       sort_keys=True, default=str)
    fingerprint = hashlib.sha256(basis.encode()).hexdigest()[:16]
    mark = state.get("stall") or {}
    if mark.get("fp") != fingerprint:
        state["stall"] = mark = {"fp": fingerprint, "since": now}
    since = float(mark.get("since", now))
    if now < since + cfg["stuck_minutes"] * 60:
        return []
    rejected = ", ".join(sorted((summary.get("gates") or {}).get("rejected") or {}))
    return [trigger("stalled", f"{run.run_id}:stalled:{fingerprint}", run.run_id,
                    reason=f"the run workflow {status.get('workflow_id')} is PENDING with no live task and no open "
                           f"decision since {_iso(since)}" + (f"; rejected gates: {rejected}" if rejected else ""))]


def stuck_triggers(run, status: dict, state: dict, now: float, cfg: dict) -> list[dict]:
    """PENDING tasks whose state did not move for `stuck_minutes` beyond their known waits. Updates `state["watch"]`."""
    watch = state.setdefault("watch", {})
    seen, found = set(), []
    for task_id, item in sorted((status.get("tasks") or {}).items()):
        item = item or {}
        if item.get("workflow_status") != "PENDING":
            continue
        seen.add(task_id)
        event = item.get("state") if isinstance(item.get("state"), dict) else {}
        decision = item.get("decision") if isinstance(item.get("decision"), dict) else None
        basis = json.dumps([item.get("workflow_id"), event, (decision or {}).get("request_id")], sort_keys=True,
                           default=str)
        fingerprint = hashlib.sha256(basis.encode()).hexdigest()[:16]
        mark = watch.get(task_id) or {}
        if mark.get("fp") != fingerprint:
            watch[task_id] = mark = {"fp": fingerprint, "since": now}
        name = event.get("state")
        if decision or name in QUIET:
            continue
        since = float(mark.get("since", now))
        limit = cfg["stuck_minutes"] * 60
        if name in ("waiting_quota", "recovering") and isinstance(event.get("until"), (int, float)):
            deadline = max(since, float(event["until"])) + limit
        elif name == "running":
            deadline = since + cfg["attempt_minutes"] * 60 + limit
        else:
            deadline = since + limit
        if now >= deadline:
            found.append(trigger("stuck", f"{run.run_id}:{task_id}:stuck:{fingerprint}", run.run_id, task_id=task_id,
                                 reason=f"state {name or 'none'} unchanged since {_iso(since)} while its workflow is "
                                        "PENDING"))
    for task_id in list(watch):
        if task_id not in seen:
            del watch[task_id]
    return found


class Solver:
    """One maintenance pass over every durable run. Everything that touches the world is injected: `terminal` (tmux:
    exists/start/screen/send/kill, `bt_agent_terminal` by default), `route_for(project, avoid)` (the account), `notify`
    (the owner's desktop), `record` (the run's activity feed) and `now`."""

    def __init__(self, root: Path, client, *, terminal=None, route_for: Callable | None = None,
                 notify: Callable | None = None, record: Callable | None = None, now: Callable[[], float] = time.time,
                 work: Path | None = None, state_dir: Path | None = None):
        import bt_agent_terminal
        self.root, self.client, self.now = Path(root), client, now
        self.state_dir = Path(state_dir or Path(root) / ".state" / "durable")
        self.resolutions = self.state_dir / "composition" / "resolutions"
        self.terminal = terminal or bt_agent_terminal
        self.route_for = route_for or (lambda project, avoid: bt_agent_terminal.role_route(
            project, "solver", avoid, override="BITACORA_SOLVER_CLAUDE_CONFIG_DIR"))
        if notify is None:
            import bt_runutil
            notify = bt_runutil.notify
        if record is None:
            import bt_planning_activity
            record = lambda rdir, text: bt_planning_activity.record(rdir, "Solucionador", text, kind="flow")  # noqa: E731
        self.notify, self.record, self.work = notify, record, Path(work or WORK)

    # ------------------------------------------------------------------------------------------------ the pass
    def run_pass(self, escalations: Iterable[dict] = ()) -> list[str]:
        if not enabled():
            return []
        cfg = settings()
        by_run: dict[str, list[dict]] = {}
        for item in escalations:
            by_run.setdefault(str(item.get("run_id")), []).append(item)
        runs = list(healing.runs(self.root))
        states = {str(rdir): load(rdir) for rdir, _ in runs}
        before = {key: json.dumps(value, sort_keys=True) for key, value in states.items()}
        said: list[str] = []
        for rdir, run in runs:                     # close finished sessions first: they free the machine's slots
            said += self._supervise(run, rdir, states[str(rdir)], cfg)
        active = sum(1 for s in states.values() if s.get("active"))
        statuses: dict[str, dict] = {}
        for _, run in runs:
            try:
                statuses[run.run_id] = self.client.status(run)
            except Exception as error:  # noqa: BLE001 - a run that cannot be read is tried on the next pass
                LOG.warning("solver: %s status failed: %s", run.run_id, error)
        from . import resolutions
        for item in resolutions.triggers(self.resolutions, statuses, self.now(), cfg["resolution_after_seconds"]):
            by_run.setdefault(item["run_id"], []).append(item)
        for rdir, run in runs:
            state = states[str(rdir)]
            status = statuses.get(run.run_id)
            if status is None:
                continue
            found = by_run.get(run.run_id, []) + error_triggers(run, status) + \
                stuck_triggers(run, status, state, self.now(), cfg) + stalled_triggers(run, status, state, self.now(), cfg)
            for item in found:
                said += self._register(run, rdir, state, item)
            if state.get("active"):
                said += self._queue(run, rdir, state)
            elif active < cfg["max_concurrent"] and (items := self._pending(run, rdir, state, status, cfg)):
                said += self._launch(run, rdir, state, status, items)
                active += bool(state.get("active"))
        for rdir, _ in runs:
            key = str(rdir)
            if json.dumps(states[key], sort_keys=True) != before[key]:
                save(rdir, states[key])
        return said

    def _register(self, run, rdir, state, item: dict) -> list[str]:
        triggers = state.setdefault("triggers", {})
        if item["key"] in triggers:
            return []
        triggers[item["key"]] = {**item, "status": "pending", "at": _iso(self.now())}
        what = {"decision": "la autocuración dejó la decisión para ti", "repeat": "el mismo fallo volvió",
                "stuck": "la tarea no avanza", "error": "el workflow del run terminó en error",
                "stalled": "el run no avanza: nada corre y nada espera tu decisión",
                "resolution": "un conflicto de composición espera una resolución"}.get(item["kind"], item["kind"])
        self.record(rdir, f"{item.get('task_id') or 'run'}: {what}; pasa al Solucionador ({item['reason'][:160]})")
        return [f"{item['key']}: {item['kind']} queued for the Solucionador"]

    def _pending(self, run, rdir, state, status, cfg) -> list[dict]:
        """Pending triggers still worth a session; stale ones (the decision moved on, the task moved) are dropped and
        those whose task used its sessions are left for the owner."""
        out = []
        counts = state.setdefault("tasks", {})
        tasks = status.get("tasks") or {}
        for key, item in sorted(state.get("triggers", {}).items(), key=lambda kv: str(kv[1].get("at"))):
            if item.get("status") != "pending":
                continue
            if not self._current(item, tasks, status):
                item["status"] = "stale"
                continue
            if int(counts.get(item.get("task_id") or "run", 0)) >= cfg["max_per_task"]:
                item["status"] = "limit"
                text = (f"{item.get('task_id') or 'run'}: el Solucionador ya lo intentó {cfg['max_per_task']} veces; "
                        f"queda para ti ({item['reason'][:160]})")
                self.record(rdir, text)
                self.notify("El Solucionador necesita tu ayuda", f"{run.project} {run.req} {text}")
                continue
            out.append(item)
        return out

    @staticmethod
    def _current(item: dict, tasks: dict, status: dict) -> bool:
        task = tasks.get(item.get("task_id") or "") or {}
        if item["kind"] in ("decision", "repeat"):
            decision = task.get("decision") if isinstance(task.get("decision"), dict) else {}
            return decision.get("request_id") == item.get("request_id") and \
                healing.round_of(task) == item.get("round")
        if item["kind"] == "error":
            return status.get("workflow_status") in ERRORED
        if item["kind"] == "stuck":
            return task.get("workflow_status") == "PENDING"
        if item["kind"] == "stalled":
            summary = status.get("summary") if isinstance(status.get("summary"), dict) else {}
            return status.get("workflow_status") == "PENDING" and summary.get("status") != "paused" \
                and not _live_tasks(status)
        if item["kind"] == "resolution":
            return not Path((item.get("resolution") or {}).get("resolved") or "/").exists()
        return True

    # ---------------------------------------------------------------------------------------------- a session
    def _launch(self, run, rdir, state, status, items: list[dict]) -> list[str]:
        name = self.terminal.name_for(run.project, run.req, "solver")
        if self.terminal.exists(name):                   # started by a pass whose state write was lost: said once
            if state.get("orphan") == name:
                return []
            state["orphan"] = name
            return [f"{run.run_id}: a session named {name} exists without a record; not starting another"]
        state.pop("orphan", None)
        sid = time.strftime("%Y%m%d-%H%M%S", time.localtime(self.now())) + "-" + uuid.uuid4().hex[:4]
        folder = Path(rdir) / DIR / sid
        folder.mkdir(parents=True, exist_ok=True)
        cwd = self.work / run.project / sid
        cwd.mkdir(parents=True, exist_ok=True)
        session = {"id": sid, "name": name, "status": "running", "started": self.now(), "started_at": _iso(self.now()),
                   "triggers": [i["key"] for i in items], "queued": [], "restarts": 0, "dir": str(folder),
                   "cwd": str(cwd), "task": items[0].get("task_id") or "run", "kind": items[0]["kind"],
                   "reason": items[0]["reason"]}
        (folder / "triggers.json").write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        (folder / "status.json").write_text(json.dumps(status, ensure_ascii=False, indent=1, default=str) + "\n",
                                            encoding="utf-8")
        (folder / "inbox.jsonl").touch()
        from .solver_brief import brief, prompt
        (folder / "BRIEF.md").write_text(brief(run, rdir, session, items, status,
                                               telemetry=self.state_dir / "telemetry.jsonl"), encoding="utf-8")
        (folder / "PROMPT.md").write_text(prompt(folder), encoding="utf-8")
        error = self._start(run, session, avoid="")
        if error:
            for item in items:
                item["status"] = "failed"
            session.update(status="gave_up", ended_at=_iso(self.now()), summary=f"no arrancó: {error}"[:300])
            state.setdefault("sessions", []).append(session)
            self.record(rdir, f"{session['task']}: el Solucionador no pudo arrancar ({error[:160]}); queda para ti")
            self.notify("El Solucionador no arrancó", f"{run.project} {run.req}: {error[:200]}")
            return [f"{run.run_id}: solver could not start: {error}"]
        for item in items:
            item.update(status="running", session=sid)
            task = item.get("task_id") or "run"
            state.setdefault("tasks", {})[task] = int(state["tasks"].get(task, 0)) + 1
        state.setdefault("sessions", []).append(session)
        state["active"] = sid
        self.record(rdir, f"{session['task']}: el Solucionador empezó ({name}, {session.get('provider')} "
                    f"{session.get('model') or ''}): {session['reason'][:160]}")
        return [f"{run.run_id}: solver {sid} started in {name} for {', '.join(session['triggers'])}"]

    def _start(self, run, session: dict, avoid: str) -> str:
        """Start (or restart, `avoid` = the account to leave) the session in tmux. Returns an error text or ""."""
        route = self.route_for(run.project, avoid)
        folder, home = Path(session["dir"]), str(route.get("home") or "")
        prompt_file = shlex.quote(str(folder / "PROMPT.md"))
        env = {"BITACORA_SOLVER": session["id"]}
        if route.get("provider") == "codex":
            model = f"-m {shlex.quote(route['model'])} " if route.get("model") else ""
            command = (f"codex --dangerously-bypass-approvals-and-sandbox {model}-c model_reasoning_effort="
                       f"{shlex.quote(route.get('effort') or 'high')} \"$(cat {prompt_file})\"")
            if home:
                env["CODEX_HOME"] = home
        else:
            flags = "--model opus --effort high --dangerously-skip-permissions"
            old = session.get("session_id") or ""
            if home:
                env["CLAUDE_CONFIG_DIR"] = home
            if old and self._carry(session, home):
                command = f"claude --resume {shlex.quote(old)} {flags} {shlex.quote(RESTART_MESSAGE)}"
            else:
                session["session_id"] = str(uuid.uuid4())
                command = f"claude --session-id {session['session_id']} {flags} \"$(cat {prompt_file})\""
        try:
            self.terminal.start(session["name"], Path(session["cwd"]), command, env,
                                scope=f"bt-solver-{session['id']}-{uuid.uuid4().hex[:6]}")
        except Exception as error:  # noqa: BLE001 - tmux missing, a name taken: reported, never raised into the pass
            return str(error)[:300] or type(error).__name__
        session.update(provider=route.get("provider") or "claude", model=route.get("model") or "", home=home)
        return ""

    def _carry(self, session: dict, home: str) -> bool:
        """Copy the Claude conversation to the new account so `--resume` finds it (the Planner's pattern)."""
        import bt_agent_terminal
        old = bt_agent_terminal.transcript(session.get("home") or "", session["cwd"], session["session_id"])
        new = bt_agent_terminal.transcript(home, session["cwd"], session["session_id"])
        try:
            if old.is_file() and not new.is_file():
                new.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(old, new)
        except OSError:
            return False
        return new.is_file()

    def _supervise(self, run, rdir, state, cfg) -> list[str]:
        sid = state.get("active")
        session = next((s for s in state.get("sessions", []) if s.get("id") == sid), None)
        if not sid or session is None:
            state.pop("active", None)
            return []
        result = read_result(Path(session["dir"]))
        if result is not None:
            return self._finish(run, rdir, state, session, result)
        if self.now() - float(session.get("started") or 0) > cfg["max_minutes"] * 60:
            return self._finish(run, rdir, state, session, {
                "outcome": "gave_up", "summary": f"pasó {cfg['max_minutes']} min sin escribir result.json; detenido"})
        if not self.terminal.exists(session["name"]):
            return self._finish(run, rdir, state, session, {
                "outcome": "gave_up", "summary": "la sesión terminó sin escribir result.json"})
        import bt_agent_terminal
        shown = self.terminal.screen(session["name"], 20)
        if bt_agent_terminal.LIMITED.search(shown) or bt_agent_terminal.OWNER_PROMPT.search(shown):
            if int(session.get("restarts", 0)) >= MAX_RESTARTS:
                return self._finish(run, rdir, state, session, {
                    "outcome": "gave_up", "summary": "ninguna cuenta con cuota pudo seguir la sesión"})
            self.terminal.kill(session["name"])
            left = session.get("home") or ""
            error = self._start(run, session, avoid=left)
            session["restarts"] = int(session.get("restarts", 0)) + 1
            if error:
                return self._finish(run, rdir, state, session, {"outcome": "gave_up",
                                                                "summary": f"no pudo cambiar de cuenta: {error}"})
            self.record(rdir, f"{session['task']}: el Solucionador cambió de cuenta (la anterior se quedó sin cuota)")
            return [f"{run.run_id}: solver {sid} moved off {left or 'its account'}"]
        return []

    def _finish(self, run, rdir, state, session: dict, result: dict) -> list[str]:
        outcome = result.get("outcome") if result.get("outcome") in OUTCOMES else "gave_up"
        summary = str(result.get("summary") or "")[:300]
        session.update(status=outcome, ended=self.now(), ended_at=_iso(self.now()), summary=summary,
                       question=str(result.get("question") or "")[:600], report=str(Path(session["dir"]) / "REPORT.md"))
        if self.terminal.exists(session["name"]):
            self.terminal.kill(session["name"])
        handled = set(result.get("handled") or ()) if isinstance(result.get("handled"), list) else None
        for key in [*session.get("triggers", []), *session.get("queued", [])]:
            item = state.get("triggers", {}).get(key)
            if item is None:
                continue
            if key in session.get("triggers", []) or handled is None or key in handled:
                item["status"] = outcome                 # a trigger that started a session never starts another
            else:
                item["status"] = "pending"               # queued in its inbox and not handled: the next session's
        state.pop("active", None)
        text = f"{session['task']}: Solucionador · {OUTCOME_ES[outcome]}" + (f": {summary}" if summary else "")
        self.record(rdir, text[:400])
        if outcome in ("asked_owner", "gave_up"):
            ask = session["question"] or summary or "mira su informe"
            self.notify("El Solucionador te necesita" if outcome == "asked_owner" else "El Solucionador no pudo",
                        f"{run.project} {run.req} {session['task']}: {ask}"[:400])
        LOG.info("solver %s of %s ended %s: %s", session["id"], run.run_id, outcome, summary)
        return [f"{run.run_id}: solver {session['id']} {outcome}"]

    def _queue(self, run, rdir, state) -> list[str]:
        """Triggers that arrive while the run's session works go to its inbox and are typed into it."""
        sid = state["active"]
        session = next((s for s in state.get("sessions", []) if s.get("id") == sid), None)
        if session is None:
            return []
        said = []
        for key, item in sorted(state.get("triggers", {}).items(), key=lambda kv: str(kv[1].get("at"))):
            if item.get("status") != "pending":
                continue
            item.update(status="queued", session=sid)
            session.setdefault("queued", []).append(key)
            with (Path(session["dir"]) / "inbox.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(item, ensure_ascii=False) + "\n")
            try:
                self.terminal.send(session["name"], f"[Automatic notice from the engine, not typed by the owner] A new "
                                   f"trigger is queued in inbox.jsonl: {key} ({item['kind']}, "
                                   f"{item.get('task_id') or 'run'}): {item['reason'][:300]}. Handle it after the "
                                   "current one and list it in result.json `handled`.")
            except Exception:  # noqa: BLE001 - the inbox file is what counts; typing it is a courtesy
                pass
            said.append(f"{key}: queued to solver {sid}")
        return said


def read_result(folder: Path) -> dict | None:
    try:
        data = json.loads((Path(folder) / "result.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) and data.get("outcome") in OUTCOMES else None


__all__ = ["Solver", "enabled", "error_triggers", "load", "read_result", "round_of", "settings", "stalled_triggers",
           "stuck_triggers", "trigger"]
