"""Marathon supervisor: runs an approved PLAN for days, one FRESH headless agent session per task.

All state lives in RUN.json (bt_runstate). The supervisor enforces the caps itself (attempts, timeout, sessions),
detects stuck tasks, waits out usage limits, notifies, and can be restarted at any time (`--resume`, autostart).
Sessions: bt_runsession (model tier: bt_runtier). Prompts: bt_runprompt. Outcomes: bt_runsettle.
Agent-facing commands (task done/fail/note/escalate, run-control): bt_runtask.
"""
from __future__ import annotations

import concurrent.futures
import socket
import time

from bt_core import *  # noqa: F403
import bt_agents
import bt_events
import bt_profiles
import bt_runprompt as rp
import bt_runstate as rs
import bt_runtier as tier_
from bt_runsession import AgentNotFound, reap_orphans, run_session, session_route, session_tier
from bt_runsettle import LIMIT_RESULTS, detect_limit, enter_wait, limit_line, recover_claims, settle_final, settle_task
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
                                ("session_timeout_min", o.get("session_timeout")),
                                ("workers", min(int(o["workers"]), rs.MAX_WORKERS) if o.get("workers") else None)) if v}
    state = rs.load(rdir)
    profile = o.get("profile") or (state or {}).get("profile")
    if profile:
        bt_profiles.authorize(profile, project)
        o = {**o, "agent": bt_profiles.require_launchable(profile)}
    pool = _pool(project, o.get("pool"), profile)
    if pool is None and state and state.get("pool"):  # a saved pool is re-checked: the work flag may have changed
        pool = bt_agents.pool_for(project, [p for p in state["pool"] if p in bt_profiles.load()])
        if not pool:
            raise SystemExit(f"None of the accounts this run used ({', '.join(state['pool'])}) may run '{project}' "
                             f"any more. Choose again: run {state['req']} --resume --pool auto")
    if pool and not o.get("agent"):
        o = {**o, "agent": bt_profiles.provider_of(pool[0])}
    audit = o.get("audit") if o.get("audit") is not None else (
        bt_agents._config("audit.mode", "milestone") == "milestone" if pool else None)
    if state is None:
        state = rs.init_state(project, rdir, o.get("agent") or "claude", o.get("model") or "haiku",
                              o.get("ultracode") is not False, limits, pool, bool(audit))
        if profile:
            state["profile"] = profile
        rs.save(rdir, state)
        return state
    hb = state.get("heartbeat") or {}
    if (hb.get("machine") == socket.gethostname() and hb.get("pid") not in (None, os.getpid())
            and state["status"] in ("running", "waiting", "paused") and not rs.is_stale(state, 3)
            and pid_alive(hb["pid"])):
        print(f"A supervisor is already running this marathon (pid {hb['pid']}).")
        return None
    for orphan in reap_orphans(project, state):
        print(f"[run] {orphan}", flush=True)

    def fn(s):
        rs.sync_plan(s, rdir)
        for t in s["tasks"]:
            if t["status"] == "in_progress":
                t["status"] = "todo"
            elif t["status"] == "blocked" and o.get("retry_blocked"):
                t.update(status="todo", attempts=0, error_hashes=[], pending_id=None, limit_streak=0,
                         tier=tier_.start_tier(t.get("level"), t.get("kind")))
        s["limits"].update(limits)
        if pool is not None:
            s["pool"] = pool
        if audit is not None:
            s["audit"] = bool(audit)
            rs.sync_plan(s, rdir)
        for key, value in (("agent", o.get("agent")), ("model", o.get("model")), ("profile", profile)):
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


def _pool(project: str, requested: str | list | None, profile: str | None) -> list[str] | None:
    """None = leave the run's pool as it is; [] = pinned to one agent; otherwise the accounts the router may use.
    `auto` = every account allowed for the project (the routing.pool setting restricts it)."""
    if requested is None:
        return None
    names = [n.strip() for n in (requested.split(",") if isinstance(requested, str) else requested) if n.strip()]
    if names in (["none"], ["off"]):
        return []
    if names == ["auto"]:
        pool = bt_agents.pool_for(project, bt_agents._config("routing.pool", []) or None)
    else:
        pool = bt_agents.pool_for(project, names)
    if profile and profile in pool:  # the profile the user named is the first choice among equals
        pool = [profile] + [p for p in pool if p != profile]
    if not pool:
        raise SystemExit(f"No account may run '{project}' (asked for: {', '.join(names)}). Check: bitacora.py agents")
    return pool


def _limited(project: str, rdir: Path, c: dict, state: dict, infos: list[dict]) -> None:
    """A session hit a usage limit. Pinned run: wait for the reset. Pool: put that account on cooldown and carry on
    with another one; wait only when every account is cooling down."""
    epochs = [detect_limit(i) or 0 for i in infos]
    if not state.get("pool"):
        enter_wait(rdir, project, state["req"], max(epochs), c["notified_wait"])
        c["notified_wait"] = True
        return
    for info, epoch in zip(infos, epochs):
        until = bt_agents.quota_mark(info.get("profile"), info.get("agent"), epoch,
                                     limit_line(info.get("text", "")[-4000:]), info.get("model"))
        say(state, f"{info.get('profile') or info.get('agent')} hit a usage limit; cooling until "
                   f"{dt.datetime.fromtimestamp(until):%m-%d %H:%M}")
    routes, soonest = bt_agents.candidates(project, state["pool"], 0)
    if routes:
        say(state, f"continuing on {routes[0]['profile']} ({routes[0]['agent']})")
        c["notified_wait"] = False
        return
    enter_wait(rdir, project, state["req"], int(soonest or 0), c["notified_wait"])
    c["notified_wait"] = True


def _settle_unit(project: str, rdir: Path, unit: list[dict], n: int, info: dict, workdir: Path) -> dict:
    """Settle every task of a session, in plan order. A task the session never reached because one it depends on did
    not finish is skipped (no attempt counted). Returns {task id: result}."""
    results: dict[str, str] = {}
    for t in unit:
        current = rs.get_task(rs.load(rdir), t["id"])
        untouched = current["status"] == "in_progress" and not current.get("claimed_done") and not current.get("escalation")
        broken = [a for a in t["after"] if a in results and results[a] != "done"]
        skip = f"not reached: depends on {', '.join(broken)}, which did not finish" if untouched and broken else None
        results[t["id"]] = settle_task(project, rdir, t["id"], n, info, workdir, skip)
    return results


def _overall(results: dict) -> str:
    """One result for the session's telemetry row: done only when every task is."""
    values = list(results.values())
    if all(v == "done" for v in values):
        return "done"
    for bad in ("usage_limit", "limit_streak", "timeout", "verify_failed", "failed", "blocked", "escalated"):
        if bad in values:
            return bad if not any(v == "done" for v in values) else "partial"
    return values[0] if values else "failed"


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
    if task and not once and (state["limits"].get("workers") or 1) > 1:
        units = rs.ready_units(state, state["limits"]["workers"])
        if len(units) > 1:
            return _run_batch(project, rdir, c, state, units)
    unit = rs.unit_of(state, task) if task else []
    tid = rs.unit_label(unit) if task else rp.FINAL_TASK
    try:
        route = session_route(project, state, task, unit)
    except bt_agents.NoRoute as exc:  # every account of the pool is cooling down
        enter_wait(rdir, project, state["req"], int(exc.until), c["notified_wait"])
        c["notified_wait"] = True
        return 0 if once else None
    n = state["sessions"] + 1

    def begin(s):
        s["sessions"] = n
        for t in unit:
            rs.mark(s, t["id"], "in_progress")
        rs.heartbeat(s, task=tid, session=n, state="session starting")
    state = rs.update(rdir, begin)
    started = time.time()
    who = f"{route['profile'] or route['agent']} " if state.get("pool") else ""
    title = (task["title"][:60] if len(unit) == 1 else f"milestone: {', '.join(t['id'] for t in unit)}") \
        if task else "final review + REPORT.md"
    say(state, f"S{n:04d} {tid} [{who}{tier_.label(route['model'], route['effort'])}] {title}")
    try:
        info = run_session(project, rdir, state, task, n, c["workdir"], c["agent_cmd"], unit, route)
    except AgentNotFound as exc:
        _reset_in_progress(rdir)
        _finish(project, rdir, "stopped", f"agent executable not found: {exc}", install)
        return 1
    if task:
        results = _settle_unit(project, rdir, unit, n, info, c["workdir"])
        result = results[unit[0]["id"]] if len(unit) == 1 else _overall(results)
    else:
        results, result = {}, settle_final(project, rdir, n, info, started)
    state = rs.load(rdir)
    bt_events.record_attempt(project, state, tid, n, info, "stopped" if info.get("stopped") else result)
    ended = ", ended after task done" if info.get("early_exit") else ""
    detail = " [" + " ".join(f"{k}:{v}" for k, v in results.items()) + "]" if len(results) > 1 else ""
    say(state, f"S{n:04d} {tid} -> {result}{detail} ({info['seconds']}s{ended})")
    beat(rdir, task=tid, session=n, state=f"{result}")
    commit_bitacora(project, f"marathon {state['req']} S{n:04d} {tid} {result}")
    if result in LIMIT_RESULTS or any(r in LIMIT_RESULTS for r in results.values()):
        _limited(project, rdir, c, state, [info])
        if once:  # the wait itself is handled at the top of the next iteration; no wait = nothing is running now
            if rs.load(rdir)["status"] == "running":
                set_fields(rdir, status="paused")
            return 0
    else:
        c["notified_wait"] = False
    if once and not (task is None and result == "done"):
        if rs.load(rdir)["status"] == "running":
            set_fields(rdir, status="paused")
        return 0
    return None


def _run_batch(project: str, rdir: Path, c: dict, state: dict, units: list[list[dict]]) -> int | None:
    """Run units of different repositories at the same time (one thread per session) and settle each one on its own;
    every shared-file write underneath goes through bt_lock. Session numbers are reserved up front so logs, ids and
    telemetry never collide."""
    units = units[:max(1, state["limits"]["max_sessions"] - state["sessions"])]
    base = state["sessions"]
    plan, busy = [], set()
    for unit in units:
        try:
            route = session_route(project, state, unit[0], unit, busy)  # spread a batch over different accounts
            busy.add(bt_agents.account_key(route.get("profile"), route.get("agent")))
            plan.append((unit, route))
        except bt_agents.NoRoute as exc:
            if not plan:
                enter_wait(rdir, project, state["req"], int(exc.until), c["notified_wait"])
                c["notified_wait"] = True
                return None
            break
    nums = {rs.unit_label(u): base + 1 + i for i, (u, _) in enumerate(plan)}

    def begin(s):
        s["sessions"] = base + len(plan)
        for unit, _ in plan:
            for t in unit:
                rs.mark(s, t["id"], "in_progress")
        rs.heartbeat(s, task=",".join(nums), session=s["sessions"], state=f"{len(plan)} sessions starting")
    state = rs.update(rdir, begin)
    for unit, route in plan:
        label = rs.unit_label(unit)
        who = f"{route['profile'] or route['agent']} " if state.get("pool") else ""
        say(state, f"S{nums[label]:04d} {label} [{who}{tier_.label(route['model'], route['effort'])}] "
                   f"(parallel x{len(plan)}) {unit[0]['title'][:50]}")

    def run_unit(unit: list[dict], route: dict):
        label = rs.unit_label(unit)
        n = nums[label]
        info = run_session(project, rdir, rs.load(rdir), unit[0], n, c["workdir"], c["agent_cmd"], unit, route)
        results = _settle_unit(project, rdir, unit, n, info, c["workdir"])
        return label, n, info, (results[unit[0]["id"]] if len(unit) == 1 else _overall(results)), results

    outcomes, missing = [], None
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(plan)) as pool:
        futures = [pool.submit(run_unit, unit, route) for unit, route in plan]
        for fut in futures:
            try:
                outcomes.append(fut.result())
            except AgentNotFound as exc:
                missing = exc
    if missing is not None:
        _reset_in_progress(rdir)
        _finish(project, rdir, "stopped", f"agent executable not found: {missing}", c["install"])
        return 1
    state = rs.load(rdir)
    for label, n, info, result, _ in outcomes:
        bt_events.record_attempt(project, state, label, n, info, "stopped" if info.get("stopped") else result)
        say(state, f"S{n:04d} {label} -> {result} ({info['seconds']}s)")
    beat(rdir, task=",".join(o[0] for o in outcomes), state="batch settled")
    commit_bitacora(project, f"marathon {state['req']} " + " ".join(f"S{n:04d} {t} {r}" for t, n, _, r, _ in outcomes))
    limited = [info for _, _, info, r, results in outcomes
               if r in LIMIT_RESULTS or any(v in LIMIT_RESULTS for v in results.values())]
    if limited:
        _limited(project, rdir, c, state, limited)
    else:
        c["notified_wait"] = False
    return None


def supervise(project: str, req: str, **o) -> int:
    """Run the marathon until done/blocked/stopped. Options: agent, model, ultracode, max_attempts, session_timeout,
    retry_blocked, agent_cmd, once, no_autostart, pool (accounts the router may use), audit (milestone audits). Returns a process exit code. A crash inside one iteration (a locked
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
    who = f"pool {', '.join(state['pool'])}" if state.get("pool") else f"{state['agent']}/{state['model']}"
    say(state, f"{project} {state['req']} marathon started ({who}, "
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
