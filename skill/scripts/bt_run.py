"""Marathon supervisor: runs an approved PLAN for days, one FRESH headless agent session per task.

All state lives in RUN.json (bt_runstate). The supervisor enforces the caps itself (attempts, timeout, sessions),
detects stuck tasks, waits out usage limits, notifies, and can be restarted at any time (`--resume`, autostart).
Sessions: bt_runsession (model tier: bt_runtier). Prompts: bt_runprompt. Outcomes: bt_runsettle.
Agent-facing commands (task done/fail/note/escalate, run-control): bt_runtask.
"""
from __future__ import annotations

import socket
import time

from bt_core import *  # noqa: F403
import bt_runprompt as rp
import bt_runstate as rs
import bt_runtier as tier_
from bt_runsession import AgentNotFound, run_session, session_tier
from bt_runsettle import LIMIT_RESULTS, detect_limit, enter_wait, recover_claims, settle_final, settle_task
from bt_runutil import (autostart, backoff_override, beat, commit_bitacora, keep_awake, notify, pid_alive, say,
                        set_fields, wait_or_control)

MAX_ERRORS = 10  # consecutive failed supervisor iterations before giving up


# ---------------------------------------------------------------- supervisor

def _finish(project: str, rdir: Path, status: str, message: str, remove_autostart: bool) -> None:
    state = set_fields(rdir, status=status, control=None, waiting_until=None)
    beat(rdir, task=None, state=status)
    say(state, f"{status.upper()} - {message}")
    notify(f"{project} {state['req']}: marathon {status}", message)
    if remove_autostart:
        autostart("remove", project, state["req"])
    commit_bitacora(project, f"marathon {state['req']} {status}")


def _open(project: str, rdir: Path, o: dict) -> dict | None:
    limits = {k: v for k, v in (("max_attempts", o.get("max_attempts")),
                                ("session_timeout_min", o.get("session_timeout"))) if v}
    state = rs.load(rdir)
    if state is None:
        state = rs.init_state(project, rdir, o.get("agent") or "claude", o.get("model") or "haiku",
                              o.get("ultracode") is not False, limits)
        rs.save(rdir, state)
        return state
    hb = state.get("heartbeat") or {}
    if (hb.get("machine") == socket.gethostname() and hb.get("pid") not in (None, os.getpid())
            and state["status"] in ("running", "waiting", "paused") and not rs.is_stale(state, 3)
            and pid_alive(hb["pid"])):
        print(f"A supervisor is already running this marathon (pid {hb['pid']}).")
        return None

    def fn(s):
        rs.sync_plan(s, rdir)
        for t in s["tasks"]:
            if t["status"] == "in_progress":
                t["status"] = "todo"
            elif t["status"] == "blocked" and o.get("retry_blocked"):
                t.update(status="todo", attempts=0, error_hashes=[], pending_id=None, limit_streak=0,
                         tier=tier_.start_tier(t.get("level")))
        s["limits"].update(limits)
        for key, value in (("agent", o.get("agent")), ("model", o.get("model"))):
            if value:
                s[key] = value
        if o.get("ultracode") is not None:
            s["ultracode"] = o["ultracode"]
        # a restart (reboot, autostart) must not undo an explicit pause or cut a usage-limit wait short
        paused = s.get("control") == "pause"
        until = rs._parse_time(s.get("waiting_until"))
        waiting = until is not None and until > dt.datetime.now()
        s["status"] = "paused" if paused else "waiting" if waiting else "running"
        if not paused:
            s["control"] = None
        if not waiting:
            s["waiting_until"] = None
        if s.get("final", {}).get("attempts"):
            s["final"]["attempts"] = 0
    state = rs.update(rdir, fn)
    if state.get("plan_drift"):
        msg = f"PLAN.md changed {', '.join(state['plan_drift'])} after approval; RUN.json keeps the approved values"
        say(state, msg)
        notify(f"{project} {state['req']}: plan drift", msg)
    return state


def _reset_in_progress(rdir: Path) -> None:
    """After a crash mid-session: a task left in_progress would look 'not runnable' and block the whole run."""
    def fn(s):
        for t in s["tasks"]:
            if t["status"] == "in_progress":
                t["status"] = "todo"
    try:
        rs.update(rdir, fn)
    except Exception:
        pass


def _step(project: str, rdir: Path, c: dict) -> int | None:
    """One supervisor iteration: honor controls and caps, pick a task, run one session, settle it.
    Returns an exit code to stop the supervisor, None to keep going. `c` is the run context built by supervise()."""
    state = rs.load(rdir)
    if state is None:
        raise rs.RunStateError(f"RUN.json disappeared from {rdir}")
    control, install, once = state.get("control"), c["install"], c["once"]
    if control == "stop":
        _finish(project, rdir, "stopped", "stopped by the user", install)
        return 0
    if control == "pause":
        set_fields(rdir, status="paused")
        if once:
            return 0
        say(state, "paused (run-control resume to continue)")
        wait_or_control(rdir, None, "paused", ignore="pause")
        return None
    if state["sessions"] >= state["limits"]["max_sessions"]:
        _finish(project, rdir, "stopped", f"session cap reached ({state['limits']['max_sessions']})", install)
        return 0
    until = rs._parse_time(state.get("waiting_until"))
    if until and until > dt.datetime.now():
        if once:
            return 0
        wait_or_control(rdir, (until - dt.datetime.now()).total_seconds(), "waiting for the usage limit")
        return None
    if state["status"] != "running" or state.get("waiting_until"):
        set_fields(rdir, status="running", waiting_until=None)
    if any(t.get("claimed_done") and t["status"] in ("todo", "in_progress") for t in state["tasks"]):
        recover_claims(project, rdir, c["workdir"])  # a claimed `done` is never trusted until verify passed
        state = rs.load(rdir)
    task = rs.next_task(state)
    if task is None and not all(t["status"] == "done" for t in state["tasks"]):
        left = [t["id"] for t in state["tasks"] if t["status"] != "done"]
        _finish(project, rdir, "blocked", f"nothing runnable; open: {', '.join(left)} "
                "(see PENDING.md; fix, then run --resume --retry-blocked)", install)
        return 2
    final = state.get("final") or {}
    if task is None and final.get("done"):
        plan = rdir / "PLAN.md"
        if plan.exists():
            set_front(plan, "status", "done")
        _finish(project, rdir, "done", f"all {len(state['tasks'])} tasks done and reported", install)
        return 0
    if task is None and final.get("attempts", 0) >= state["limits"]["max_attempts"]:
        import bt_runtask
        bt_runtask.add_blocked_pending(project, state["req"], {"id": rp.FINAL_TASK, "title": "final review + REPORT.md"},
                                       "the final session did not produce REPORT.md")
        _finish(project, rdir, "blocked", "the final review session failed repeatedly", install)
        return 2
    tid = task["id"] if task else rp.FINAL_TASK
    n = state["sessions"] + 1

    def begin(s):
        s["sessions"] = n
        if task:
            rs.mark(s, tid, "in_progress")
        rs.heartbeat(s, task=tid, session=n, state="session starting")
    state = rs.update(rdir, begin)
    started = time.time()
    model = tier_.label(*tier_.model_for(state, session_tier(state, task)))
    say(state, f"S{n:04d} {tid} [{model}] {task['title'][:60] if task else 'final review + REPORT.md'}")
    try:
        info = run_session(project, rdir, state, task, n, c["workdir"], c["agent_cmd"])
    except AgentNotFound as exc:
        _reset_in_progress(rdir)
        _finish(project, rdir, "stopped", f"agent executable not found: {exc}", install)
        return 1
    result = settle_task(project, rdir, tid, n, info, c["workdir"]) if task else \
        settle_final(project, rdir, n, info, started)
    state = rs.load(rdir)
    ended = ", ended after task done" if info.get("early_exit") else ""
    say(state, f"S{n:04d} {tid} -> {result} ({info['seconds']}s{ended})")
    beat(rdir, task=tid, session=n, state=f"{result}")
    commit_bitacora(project, f"marathon {state['req']} S{n:04d} {tid} {result}")
    if result in LIMIT_RESULTS:
        enter_wait(rdir, project, state["req"], detect_limit(info) or 0, c["notified_wait"])
        c["notified_wait"] = True
        if once:
            return 0  # the wait itself is handled at the top of the next iteration
    else:
        c["notified_wait"] = False
    if once and not (task is None and result == "done"):
        if rs.load(rdir)["status"] == "running":
            set_fields(rdir, status="paused")
        return 0
    return None


def supervise(project: str, req: str, **o) -> int:
    """Run the marathon until done/blocked/stopped. Options: agent, model, ultracode, max_attempts, session_timeout,
    retry_blocked, agent_cmd, once, no_autostart. Returns a process exit code. A crash inside one iteration (a locked
    RUN.json, a git hiccup) is reported once, retried with a growing pause, and only given up on after MAX_ERRORS."""
    rdir = find_req(ROOT / project, req)
    existing = rs.load(rdir)
    if existing and existing["status"] == "done":
        print(f"{existing['req']} already finished (RUN.json status done).")
        return 0
    state = _open(project, rdir, o)
    if state is None:
        return 1
    once, agent_cmd = bool(o.get("once")), o.get("agent_cmd")
    install = not once and not agent_cmd and not o.get("no_autostart")
    if install:
        autostart("install", project, state["req"])
    keep_awake()
    workdir = ws.workdir(ROOT, project) or (Path.cwd() if agent_cmd else None)
    if workdir is None:
        raise SystemExit(f"No repos registered for '{project}': bitacora.py --project {project} workspace add <role> <path>")
    say(state, f"{project} {state['req']} marathon started ({state['agent']}/{state['model']}, "
                f"ultracode={state['ultracode']}, workdir {workdir})")
    ctx = {"install": install, "once": once, "agent_cmd": agent_cmd, "workdir": workdir, "notified_wait": False}
    errors = 0
    while True:
        try:
            code = _step(project, rdir, ctx)
            errors = 0
        except Exception as exc:  # SystemExit (deliberate exits) passes through
            errors += 1
            print(f"[run] iteration failed ({errors}/{MAX_ERRORS}): {exc!r}", file=sys.stderr, flush=True)
            _reset_in_progress(rdir)
            if errors == 1 or errors >= MAX_ERRORS:
                notify(f"{project} {state['req']}: marathon " + ("gave up" if errors >= MAX_ERRORS else "error"),
                       repr(exc)[:200])
            if errors >= MAX_ERRORS:
                return 3
            time.sleep(1 if backoff_override() is not None else min(30 * errors, 300))
            continue
        if code is not None:
            return code
