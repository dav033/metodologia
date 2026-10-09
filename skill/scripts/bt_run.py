"""Marathon supervisor: runs an approved PLAN for days, one FRESH headless agent session per task.

All state lives in RUN.json (bt_runstate). The supervisor enforces the caps itself (attempts, timeout, sessions),
detects stuck tasks, waits out usage limits, notifies, and can be restarted at any time (`--resume`, autostart).
Session prompts: bt_runprompt. Agent-facing commands (task done/fail/note, run-control): bt_runtask.
"""
from __future__ import annotations

import socket
import subprocess
import time

from bt_core import *  # noqa: F403
import bt_runprompt as rp
import bt_runstate as rs
from bt_runsettle import detect_limit, settle_final, settle_task, enter_wait
from bt_runutil import (autostart, backoff_override, beat, commit_bitacora, keep_awake, notify, pid_alive, say,
                        set_fields, wait_or_control)

BEAT_EVERY = 60


# ---------------------------------------------------------------- one session

def _kill(proc: subprocess.Popen) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
    else:
        proc.kill()


def run_session(project: str, rdir: Path, state: dict, task: dict | None, n: int, workdir: Path,
                agent_cmd: str | None) -> dict:
    """Run one fresh agent session with a hard timeout. Returns {rc, timed_out, stopped, text, seconds}."""
    tid = task["id"] if task else rp.FINAL_TASK
    run_dir = STATE / "runs" / f"{project}-{state['req']}"
    run_dir.mkdir(parents=True, exist_ok=True)
    from bt_review import feature_branch
    prompt = rp.session_prompt(project, rdir, state, task, n, feature_branch(rdir))
    prompt_file, log_file = run_dir / f"prompt-{n:04d}.txt", run_dir / f"session-{n:04d}.log"
    prompt_file.write_text(prompt, encoding="utf-8")
    env = {**os.environ, "BITACORA_PROJECT": project, "BITACORA_RUN": state["req"], "BITACORA_TASK": tid}
    stdin_text, shell = None, False
    if agent_cmd:
        argv, shell = agent_cmd.format_map({"prompt_file": prompt_file.as_posix(), "workdir": workdir.as_posix(),
                                            "task": tid, "req": state["req"], "project": project}), True
    else:
        argv, stdin_text = rp.agent_argv(state, workdir, prompt)
    timeout = state["limits"]["session_timeout_min"] * 60
    start = last_beat = time.time()
    timed_out = stopped = False
    with log_file.open("wb") as out:
        proc = subprocess.Popen(argv, cwd=str(workdir), env=env, shell=shell, stdout=out, stderr=subprocess.STDOUT,
                                stdin=subprocess.PIPE if stdin_text else subprocess.DEVNULL)
        if stdin_text:
            try:
                proc.stdin.write(stdin_text.encode("utf-8"))
                proc.stdin.close()
            except OSError:
                pass
        while True:
            try:
                proc.wait(timeout=5)
                break
            except subprocess.TimeoutExpired:
                pass
            if time.time() - start > timeout:
                timed_out = True
                _kill(proc)
                break
            if time.time() - last_beat >= BEAT_EVERY:
                last_beat = time.time()
                current = beat(rdir, task=tid, session=n, state=f"session running {int(last_beat - start) // 60} min")
                if current.get("control") == "stop":
                    stopped = True
                    _kill(proc)
                    break
        proc.wait()
    text = log_file.read_bytes().decode("utf-8", errors="replace")
    log_file.write_text(text[-200_000:], encoding="utf-8")
    return {"rc": proc.returncode, "timed_out": timed_out, "stopped": stopped, "text": text,
            "seconds": int(time.time() - start)}


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
                t.update(status="todo", attempts=0, error_hashes=[], pending_id=None)
        s["limits"].update(limits)
        for key, value in (("agent", o.get("agent")), ("model", o.get("model"))):
            if value:
                s[key] = value
        if o.get("ultracode") is not None:
            s["ultracode"] = o["ultracode"]
        s.update(status="running", control=None, waiting_until=None)
        if s.get("final", {}).get("attempts"):
            s["final"]["attempts"] = 0
    return rs.update(rdir, fn)


def supervise(project: str, req: str, **o) -> int:
    """Run the marathon until done/blocked/stopped. Options: agent, model, ultracode, max_attempts, session_timeout,
    retry_blocked, agent_cmd, once, no_autostart. Returns a process exit code."""
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
    notified_wait = False
    while True:
        state = rs.load(rdir)
        control = state.get("control")
        if control == "stop":
            _finish(project, rdir, "stopped", "stopped by the user", install)
            return 0
        if control == "pause":
            set_fields(rdir, status="paused")
            if once:
                return 0
            say(state, "paused (run-control resume to continue)")
            wait_or_control(rdir, None, "paused", ignore="pause")
            continue
        if state["sessions"] >= state["limits"]["max_sessions"]:
            _finish(project, rdir, "stopped", f"session cap reached ({state['limits']['max_sessions']})", install)
            return 0
        if state["status"] != "running" or state.get("waiting_until"):
            set_fields(rdir, status="running", waiting_until=None)
        task = rs.next_task(state)
        if task is None and not all(t["status"] == "done" for t in state["tasks"]):
            left = [t["id"] for t in state["tasks"] if t["status"] != "done"]
            _finish(project, rdir, "blocked", f"nothing runnable; open: {', '.join(left)} "
                    "(see PENDING.md; fix, then run --resume --retry-blocked)", install)
            return 2
        if task is None and (state.get("final") or {}).get("done"):
            plan = rdir / "PLAN.md"
            if plan.exists():
                set_front(plan, "status", "done")
            _finish(project, rdir, "done", f"all {len(state['tasks'])} tasks done and reported", install)
            return 0
        if task is None and (state.get("final") or {}).get("attempts", 0) >= state["limits"]["max_attempts"]:
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
        say(state, f"S{n:04d} {tid} {task['title'][:60] if task else 'final review + REPORT.md'}")
        info = run_session(project, rdir, state, task, n, workdir, agent_cmd)
        result = settle_task(project, rdir, tid, n, info, workdir) if task else \
            settle_final(project, rdir, n, info, started)
        state = rs.load(rdir)
        say(state, f"S{n:04d} {tid} -> {result} ({info['seconds']}s)")
        beat(rdir, task=tid, session=n, state=f"{result}")
        commit_bitacora(project, f"marathon {state['req']} S{n:04d} {tid} {result}")
        if result == "usage_limit":
            enter_wait(rdir, project, state["req"], detect_limit(info) or 0, notified_wait)
            notified_wait = True
            if once:
                return 0
            remaining = (dt.datetime.fromisoformat(rs.load(rdir)["waiting_until"]) - dt.datetime.now()).total_seconds()
            wait_or_control(rdir, max(0 if backoff_override() is not None else 60, remaining),
                            "waiting for the usage limit")
        else:
            notified_wait = False
        if once and not (task is None and result == "done"):
            if rs.load(rdir)["status"] == "running":
                set_fields(rdir, status="paused")
            return 0
