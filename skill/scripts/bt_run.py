"""Marathon supervisor: runs an approved PLAN for days, one FRESH headless agent session per task.

All state lives in RUN.json (bt_runstate). The supervisor enforces the caps itself (attempts, timeout, sessions),
detects stuck tasks, waits out usage limits, notifies, and can be restarted at any time (`--resume`, autostart).
Sessions: bt_runsession (model tier: bt_runtier). Prompts: bt_runprompt. Outcomes: bt_runsettle.
Agent-facing commands (task done/fail/note/escalate, run-control): bt_runtask.
"""
from __future__ import annotations

import concurrent.futures
import socket
import subprocess
import time

from bt_core import *  # noqa: F403
import bt_agents
import bt_events
import bt_profiles
import bt_quality
import bt_runprompt as rp
import bt_runstate as rs
import bt_runtier as tier_
from bt_runsession import AgentNotFound, reap_orphans, run_session, session_route, session_tier
from bt_runsettle import LIMIT_RESULTS, detect_limit, enter_wait, limit_line, recover_claims, settle_final, settle_task
import bt_run_isolated as isolated
from bt_runutil import (autostart, beat, commit_bitacora, notify, pid_alive, say,
                        set_fields, wait_or_control)

# ---------------------------------------------------------------- supervisor

def _finish(project: str, rdir: Path, status: str, message: str, remove_autostart: bool) -> None:
    state = set_fields(rdir, status=status, control=None, waiting_until=None)
    beat(rdir, task=None, state=status)
    say(state, f"{status.upper()} - {message}")
    notify(f"{project} {state['req']}: marathon {status}", message)
    if remove_autostart:
        autostart("remove", project, state["req"])
    if state.get("orchestration_mode") != "foreground-v1":
        commit_bitacora(project, f"marathon {state['req']} {status}")


def _open(project: str, rdir: Path, o: dict) -> dict | None:
    from bt_runentry import isolation_of
    state = rs.load(rdir)
    isolation = isolation_of(state, o)
    if (state and o.get("isolation") == "off" and state.get("limits", {}).get("isolation") == "worktree" and
            (any(label != "__integration__" and not label.startswith("__integration__:") and item.get("state") != "accepted"
                 for label, item in (state.get("worktrees") or {}).items()) or
             any(task.get("status") == "integration_pending" for task in state["tasks"]))):
        raise SystemExit("Cannot disable worktree isolation while allocations are in flight; resume with --isolation worktree.")
    limits = {k: v for k, v in (("max_attempts", o.get("max_attempts")),
                                ("session_timeout_min", o.get("session_timeout")),
                                ("workers", min(int(o["workers"]), 3 if isolation == "worktree" else rs.MAX_WORKERS)
                                 if o.get("workers") else None)) if v}
    limits["isolation"] = isolation
    if o.get("session_timeout"):  # an explicit timeout is a deliberate budget: the tier table must not shorten it
        limits["session_timeout_by_tier"] = None
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
    from bt_run_plan_gate import validate_run_plan
    validate_run_plan(rdir, state)
    if state is None:  # a NEW run: its plan must be valid and exactly the approved revision (a resume is left alone)
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
                t.update(status="todo", attempts=0, error_hashes=[], pending_id=None, limit_streak=0, idle_attempts=0,
                         tier=tier_.start_tier(t.get("level"), t.get("kind"), t.get("complexity"), t.get("risk")),
                         tree_sig=None)
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
    """A session hit a usage limit. Pinned run: wait for the reset. Pool: put the account that really reported the
    limit on cooldown and carry on with another route that is admissible for the SAME work (tier, kind, configured
    model of the session that was limited, never a lighter one); wait only when no such route exists."""
    epochs = [detect_limit(i) for i in infos]
    if not state.get("pool"):
        enter_wait(rdir, project, state["req"], max(e or 0 for e in epochs), c["notified_wait"])
        c["notified_wait"] = True
        return
    marked = set()
    for info, epoch in zip(infos, epochs):
        key = bt_agents.account_key(info.get("profile"), info.get("agent"))
        if epoch is None or key in marked:  # no provider limit message in this session (e.g. a limit_streak misread)
            continue
        marked.add(key)
        until = bt_agents.quota_mark(info.get("profile"), info.get("agent"), epoch,
                                     limit_line(info.get("text", "")[-4000:]), info.get("model"))
        say(state, f"{info.get('profile') or info.get('agent')} hit a usage limit; cooling until "
                   f"{dt.datetime.fromtimestamp(until):%m-%d %H:%M}")
    soonest = None
    for info in infos:
        tier, kind = int(info.get("tier") or 0), info.get("kind") or "implement"
        routes, free_at = bt_agents.candidates(project, state["pool"], tier, kind, state.get("model"),
                                               allow_explore=False)  # a recovery re-route is not an exploration
        if routes:
            say(state, f"continuing on {routes[0]['profile']} ({routes[0]['agent']}) for tier {tier} {kind}")
            continue
        soonest = free_at if soonest is None or (free_at and free_at < soonest) else soonest
        break
    else:
        c["notified_wait"] = False
        return
    enter_wait(rdir, project, state["req"], int(soonest or 0), c["notified_wait"])
    c["notified_wait"] = True


def _settle_unit(project: str, rdir: Path, unit: list[dict], n: int, info: dict, workdir: Path,
                 workdir_override: Path | None = None, defer_done: bool = False) -> dict:
    """Settle every task of a session, in plan order. A task the session never reached because one it depends on did
    not finish is skipped (no attempt counted). Returns {task id: result}."""
    results: dict[str, str] = {}
    for t in unit:
        if info.get('orchestration') and (rs.load(rdir) or {}).get('control') == 'stop':
            info['stopped'] = True
        current = rs.get_task(rs.load(rdir), t["id"])
        untouched = current["status"] == "in_progress" and not current.get("claimed_done") and not current.get("escalation")
        broken = [a for a in t["after"] if a in results and results[a] != "done"]
        skip = f"not reached: depends on {', '.join(broken)}, which did not finish" if untouched and broken else None
        task_info = {**info, **info.get('delegations', {}).get(t['id'], {})}
        task_info['stopped'] = info['stopped'] or task_info.get('stopped', False)
        task_info['timed_out'] = info['timed_out'] or task_info.get('timed_out', False)
        task_info['rc'] = info['rc'] or task_info['rc']
        results[t["id"]] = settle_task(project, rdir, t["id"], task_info.get('session', n), task_info, workdir, skip,
                                        workdir_override, defer_done)
    return results


def _record_defects(project: str, state: dict, settled: list, session: int, info: dict) -> None:
    for t in settled:
        if t and t.get("synthetic") and t.get("kind") == "audit":
            bt_quality.record_audit_verdict(project, state, t, session, info)


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
    from bt_requirements_gate import check
    gate = check(rdir)
    if gate["status"] == "needs_revalidation":
        set_fields(rdir, status="needs_revalidation", requirements_reasons=gate["reasons"])
        if not once:
            wait_or_control(rdir, 5, "requirements revalidation required")
        return 0 if once else None
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
        if not c.get('foreground_runtime'):
            recover_claims(project, rdir, c["workdir"])  # foreground claims require durable finish receipts too
        state = rs.load(rdir)
    if state.get("limits", {}).get("isolation") == "worktree":
        isolated.recover_recorded(project, rdir)
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
    isolation_enabled = state["limits"].get("isolation") == "worktree"
    if task and (isolation_enabled or (not once and (state["limits"].get("workers") or 1) > 1)):
        units = rs.ready_units(state, state["limits"]["workers"])
        if len(units) > 1 or isolation_enabled:
            return _run_batch(project, rdir, c, state, units)
    unit = rs.unit_of(state, task) if task else []
    tid = rs.unit_label(unit) if task else rp.FINAL_TASK
    try:
        runtime = c.get("foreground_runtime")
        route = (runtime.session_route if runtime else session_route)(project, state, task, unit)
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
    integration_role = next((item.get("repo") for item in state.get("tasks", []) if item.get("repo")), None)
    integration = isolated.integration_for(state, integration_role) if isolation_enabled else None
    session_workdir = (Path(integration["worktree"]) if integration and Path(integration["worktree"]).is_dir()
                       else c["workdir"])
    review_allocation = isolated.prepare_audit(project, state, rdir, None) if isolation_enabled and task is None else None
    if review_allocation:
        session_workdir = Path(review_allocation["worktree"])
    try:
        info = (runtime.run_session if runtime else run_session)(
            project, rdir, state, task, n, session_workdir, c["agent_cmd"], unit, route)
    except AgentNotFound as exc:
        _reset_in_progress(rdir)
        _finish(project, rdir, "stopped", f"agent executable not found: {exc}", install)
        return 1
    if task:
        results = _settle_unit(project, rdir, unit, n, info, c["workdir"],
                               session_workdir if isolation_enabled else None)
        result = results[unit[0]["id"]] if len(unit) == 1 else _overall(results)
    else:
        results, result = {}, settle_final(project, rdir, n, info, started)
    if review_allocation:
        isolated.finish_audit(rdir, "FINAL")
    state = rs.load(rdir)
    if runtime and state.get('control') == 'stop':
        info['stopped'] = True
    shown = "stopped" if info.get("stopped") else result
    settled = [rs.get_task(state, t["id"]) for t in unit]
    bt_events.record_attempt(project, state, tid, n, info, shown,
                             bt_events.detail_for(settled, shown, results) if settled else
                             {"complexity": "M", "complexity_source": "inferred", "outcome": bt_events.outcome_of(shown, None),
                              "why": "final review: REPORT.md written" if result == "done" else "final review did not produce REPORT.md",
                              "titles": ["final review + REPORT.md"]})
    _record_defects(project, state, settled, n, info)
    ended = ", ended after task done" if info.get("early_exit") else ""
    detail = " [" + " ".join(f"{k}:{v}" for k, v in results.items()) + "]" if len(results) > 1 else ""
    say(state, f"S{n:04d} {tid} -> {result}{detail} ({info['seconds']}s{ended})")
    beat(rdir, task=tid, session=n, state=f"{result}")
    if not c.get("foreground_runtime"):
        commit_bitacora(project, f"marathon {state['req']} S{n:04d} {tid} {result}")
    if c.get('foreground_runtime') and info.get('stopped'):
        _finish(project, rdir, 'stopped', 'foreground session interrupted by the user', install)
        set_fields(rdir, control='stop')
        return 0
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
    if c.get("foreground_runtime") or state.get("orchestration_mode") == "foreground-v1":
        raise SystemExit("FOREGROUND_SERIAL_REQUIRED: native batch dispatch is forbidden")
    isolation = state.get("limits", {}).get("isolation") == "worktree"
    units = units[:max(1, state["limits"]["max_sessions"] - state["sessions"])]
    try:
        allocations = isolated.prepare(project, state, rdir, units) if isolation and units else {}
        if allocations:
            isolated.ensure_integration(project, state, rdir, Path(next(iter(allocations.values()))["repo"]))
        if isolation:
            for unit in units:
                if any(task.get("synthetic") or not task.get("repo") for task in unit):
                    allocations[rs.unit_label(unit)] = isolated.prepare_audit(project, rs.load(rdir), rdir, unit[0])
    except isolated.IsolationError as exc:
        _finish(project, rdir, "stopped", str(exc), c["install"])
        return 1
    base = state["sessions"]
    plan, busy = [], set()
    for unit in units:
        try:
            route = session_route(project, state, unit[0], unit, busy)  # spread a batch over different accounts
            account = bt_agents.account_key(route.get("profile"), route.get("agent"))
            if account in busy and state.get("pool"):
                break  # fewer free accounts than units: the rest waits for the next iteration
            busy.add(account)
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
        allocation = allocations.get(label)
        synthetic = any(task.get("synthetic") for task in unit)
        current_state = rs.load(rdir)
        integration_role = next((rs.get_task(current_state, task_id).get("repo")
                                 for task_id in unit[0].get("after", [])
                                 if rs.get_task(current_state, task_id) and rs.get_task(current_state, task_id).get("repo")), None)
        integration = isolated.integration_for(current_state, integration_role) if isolation and synthetic else None
        workdir = (Path(allocation["worktree"]) if allocation else
                   Path(integration["worktree"]) if integration and Path(integration["worktree"]).is_dir() else
                   c["workdir"])
        try:
            info = run_session(project, rdir, rs.load(rdir), unit[0], n, workdir, c["agent_cmd"], unit, route)
            if isolation and allocation and allocation.get("audit"):
                info.update(isolation="worktree", branch=allocation.get("branch"))
                results = _settle_unit(project, rdir, unit, n, info, workdir, workdir_override=workdir)
                isolated.finish_audit(rdir, label)
            elif isolation and allocation:
                info.update(isolation="worktree", branch=allocation["branch"])
                results = _settle_unit(project, rdir, unit, n, info, workdir, workdir, defer_done=True)
            elif integration and Path(integration["worktree"]).is_dir():
                results = _settle_unit(project, rdir, unit, n, info, c["workdir"], workdir)
            else:
                results = _settle_unit(project, rdir, unit, n, info, c["workdir"])
        except (isolated.bt_worktree.WorktreeError, subprocess.CalledProcessError, OSError) as exc:
            if allocation and allocation.get("audit"):
                isolated._audit_warning(rdir, label, allocation, str(exc))
                failed = {"rc": 1, "text": str(exc), "stopped": False, "timed_out": False, "seconds": 0,
                          "agent": route["agent"], "profile": route.get("profile"), "model": route.get("model"),
                          "effort": route.get("effort"), "early_exit": False}
                results = {}
                for task in unit:
                    current = rs.get_task(rs.load(rdir), task["id"])
                    if current and current["status"] == "in_progress":
                        results[task["id"]] = settle_task(project, rdir, task["id"], n, failed, workdir,
                                                           workdir_override=workdir)
                    else:
                        results[task["id"]] = current["status"]
                isolated.finish_audit(rdir, label)
                info = failed
            elif not allocation:
                raise
            else:
                isolated.block_integration(project, rdir, allocation, str(exc))
                info = {"rc": 1, "text": str(exc), "stopped": False, "timed_out": False, "seconds": 0,
                        "agent": route["agent"], "profile": route.get("profile"), "model": route.get("model"),
                        "effort": route.get("effort"), "early_exit": False}
                results = {task["id"]: "integration_failed" for task in unit}
        return label, n, info, (results[unit[0]["id"]] if len(unit) == 1 else _overall(results)), results, unit

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
    if isolation:
        outcomes = isolated.settle_batch(project, rdir, outcomes, allocations)
    for label, n, info, result, results, unit in outcomes:
        shown = "stopped" if info.get("stopped") else result
        bt_events.record_attempt(project, state, label, n, info, shown,
                                 bt_events.detail_for([rs.get_task(state, t["id"]) for t in unit], shown, results))
        _record_defects(project, state, [rs.get_task(state, t["id"]) for t in unit], n, info)
        say(state, f"S{n:04d} {label} -> {result} ({info['seconds']}s)")
    beat(rdir, task=",".join(o[0] for o in outcomes), state="batch settled")
    commit_bitacora(project, f"marathon {state['req']} " + " ".join(f"S{n:04d} {t} {r}" for t, n, _, r, _, _ in outcomes))
    limited = [info for _, _, info, r, results, _ in outcomes
               if r in LIMIT_RESULTS or any(v in LIMIT_RESULTS for v in results.values())]
    if limited:
        _limited(project, rdir, c, state, limited)
    else:
        c["notified_wait"] = False
    return None


def supervise(project: str, req: str, **o) -> int:
    """Run the existing scheduler with a legacy worker or verified foreground runtime."""
    from bt_runentry import supervise as enter
    return enter(project, req, **o)
