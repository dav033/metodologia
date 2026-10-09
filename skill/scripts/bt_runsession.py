"""One marathon session: launch the agent at the task's tier, stream its output to the session log as it runs, enforce
the timeout, honor a stop, and end it early once the agent has reported (task done / fail / escalate, or REPORT.md for
the final session) and a grace period passed: `claude -p` can stay alive for many minutes on background work after
the agent has finished."""
from __future__ import annotations

import subprocess
import time

from bt_core import *  # noqa: F403
import bt_runprompt as rp
import bt_runstate as rs
import bt_runtier as tier_
from bt_runutil import beat

BEAT_EVERY = 60
GRACE_SEC = 90  # after the agent's verdict, how long the session may keep running before the supervisor ends it
LOG_KEEP_CHARS = 1_000_000


class AgentNotFound(RuntimeError):
    """The agent executable could not be started."""


def grace_seconds() -> float:
    """BITACORA_RUN_GRACE_SEC overrides the grace period (tests)."""
    try:
        return float(os.environ["BITACORA_RUN_GRACE_SEC"])
    except (KeyError, ValueError):
        return GRACE_SEC


def kill_tree(proc: subprocess.Popen) -> None:
    """Kill the session's process tree and reap it; never wait forever on a process that refuses to die."""
    if os.name == "nt":
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True, timeout=30)
        except subprocess.TimeoutExpired:
            pass
    else:
        proc.kill()
    for _ in range(2):
        try:
            proc.wait(timeout=30)
            return
        except subprocess.TimeoutExpired:
            proc.kill()
    print(f"[run] session process {proc.pid} did not exit after kill; moving on", file=sys.stderr)


def session_tier(state: dict, task: dict | None) -> int:
    """A task's own tier; the final review climbs one tier per failed attempt."""
    if task is None:
        return min((state.get("final") or {}).get("attempts", 0), tier_.TOP)
    return tier_.tier_of(task)


def _reported(rdir: Path, task: dict | None, n: int, started: float) -> bool:
    """The agent already gave its verdict: task done / fail / blocked / escalate for this session (the supervisor marked
    the task in_progress when the session began), or, for the final session, a fresh REPORT.md."""
    if task is None:
        try:
            return (rdir / "REPORT.md").stat().st_mtime >= started - 1
        except OSError:
            return False
    try:
        t = rs.get_task(rs.load(rdir) or {"tasks": []}, task["id"]) or {}
    except Exception:  # a locked RUN.json is retried on the next poll
        return False
    esc = t.get("escalation") or {}
    return t.get("status") in ("done", "blocked", "todo") or str(esc.get("session")) == str(n)


def _beat(rdir: Path, **fields) -> dict:
    try:
        return beat(rdir, **fields)
    except Exception:  # never let a heartbeat hiccup orphan the running agent
        return {}


def _argv(project: str, state: dict, workdir: Path, prompt: str, prompt_file: Path, tid: str, agent_cmd: str | None,
          model: str | None, effort: str | None) -> tuple[list[str] | str, str | None, bool]:
    if agent_cmd:
        args = tier_.args_text(tier_.model_args(state.get("agent"), model, effort))
        return agent_cmd.format_map({"prompt_file": prompt_file.as_posix(), "workdir": workdir.as_posix(), "task": tid,
                                     "req": state["req"], "project": project, "model_args": args}), None, True
    argv, stdin_text = rp.agent_argv(state, workdir, prompt, model, effort)
    return argv, stdin_text, False


def run_session(project: str, rdir: Path, state: dict, task: dict | None, n: int, workdir: Path,
                agent_cmd: str | None) -> dict:
    """Run one fresh agent session. Returns {rc, timed_out, stopped, early_exit, text, seconds, model, effort}."""
    tid = task["id"] if task else rp.FINAL_TASK
    model, effort = tier_.model_for(state, session_tier(state, task))
    run_dir = STATE / "runs" / f"{project}-{state['req']}"
    run_dir.mkdir(parents=True, exist_ok=True)
    from bt_review import feature_branch
    prompt = rp.session_prompt(project, rdir, state, task, n, feature_branch(rdir))
    prompt_file, log_file = run_dir / f"prompt-{n:04d}.txt", run_dir / f"session-{n:04d}.log"
    prompt_file.write_text(prompt, encoding="utf-8")
    env = {**os.environ, "BITACORA_PROJECT": project, "BITACORA_RUN": state["req"], "BITACORA_TASK": tid,
           "BITACORA_SESSION": str(n)}
    argv, stdin_text, shell = _argv(project, state, workdir, prompt, prompt_file, tid, agent_cmd, model, effort)
    timeout, grace = state["limits"]["session_timeout_min"] * 60, grace_seconds()
    poll = min(5.0, max(0.2, grace / 2))
    start = last_beat = time.time()
    timed_out = stopped = early = False
    reported_at = None
    with log_file.open("wb", buffering=0) as out:  # the agent writes straight into the log: a killed session keeps it
        try:
            proc = subprocess.Popen(argv, cwd=str(workdir), env=env, shell=shell, stdout=out, stderr=subprocess.STDOUT,
                                    stdin=subprocess.PIPE if stdin_text else subprocess.DEVNULL)
        except FileNotFoundError as exc:
            raise AgentNotFound(str(exc)) from exc
        try:
            if stdin_text:
                try:
                    proc.stdin.write(stdin_text.encode("utf-8"))
                    proc.stdin.close()
                except OSError:
                    pass
            while True:
                try:
                    proc.wait(timeout=poll)
                    break
                except subprocess.TimeoutExpired:
                    pass
                now = time.time()
                if now - start > timeout:
                    timed_out = True
                    break
                if _reported(rdir, task, n, start):
                    reported_at = reported_at or now
                    if now - reported_at >= grace:
                        early = True
                        break
                else:  # the agent took it back (done, then fail): the grace starts over at its next verdict
                    reported_at = None
                if now - last_beat >= BEAT_EVERY:
                    last_beat = now
                    current = _beat(rdir, task=tid, session=n, state=f"session running {int(now - start) // 60} min")
                    if current.get("control") == "stop":
                        stopped = True
                        break
        finally:
            if proc.poll() is None:
                kill_tree(proc)
    text = log_file.read_bytes().decode("utf-8", errors="replace")
    if len(text) > LOG_KEEP_CHARS:
        try:
            log_file.write_text(text[-LOG_KEEP_CHARS:], encoding="utf-8")
        except OSError:  # a leftover grandchild may still hold the file; the full log is fine too
            pass
    return {"rc": proc.returncode, "timed_out": timed_out, "stopped": stopped, "early_exit": early, "text": text,
            "seconds": int(time.time() - start), "model": model, "effort": effort}
