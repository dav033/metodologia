"""Quota relay: find the terminal CLIENT of a session and the multiplexer pane it lives in.

Claude Code hosts sessions in a background daemon, so the session process and its hooks carry no ZELLIJ_PANE_ID /
TMUX_PANE / KITTY_WINDOW_ID. The visible terminal is a separate `claude` client process attached to the daemon.
Order: (1) multiplexer variables in the calling environment (the agent is then an ancestor of this command);
(2) the client linked to this session through <config>/sessions/*.json (`parkedJobId` = the daemon session's jobId).
Anything that cannot be tied to the session (Codex outside a multiplexer, a Claude session with no record), several
candidates, nested multiplexers, an ssh ancestry or no multiplexer variable ends in "manual": nothing is guessed,
nothing is typed or closed.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import bt_relay_proc as proc

MUX_VARS = {"zellij": ("ZELLIJ_PANE_ID", ("ZELLIJ_SESSION_NAME",)), "tmux": ("TMUX_PANE", ("TMUX",)),
            "kitty": ("KITTY_WINDOW_ID", ("KITTY_LISTEN_ON",))}
WRAPPER_VAR = "METODOLOGIA_RELAY_WRAPPER"
DAEMON_WORDS = ("daemon", "bg-pty-host", "bg-spare", "app-server")


def mux_candidates(environ: dict) -> list[dict]:
    found = []
    for kind, (var, extra) in MUX_VARS.items():
        value = environ.get(var)
        if value:
            target = value if kind != "zellij" or value.startswith(("terminal_", "plugin_")) else f"terminal_{value}"
            found.append({"kind": kind, "target": target, "env": {k: environ[k] for k in extra if environ.get(k)}})
    return found


def mux_from_env(environ: dict) -> dict | None:
    """The multiplexer pane, only when unambiguous (nested multiplexers set several variables)."""
    found = mux_candidates(environ)
    return found[0] if len(found) == 1 else None


def under_ssh(pid: int) -> bool:
    seen = set()
    while pid and pid > 1 and pid not in seen:
        seen.add(pid)
        info = proc.read(pid)
        if info is None:
            return False
        if info["comm"] == "sshd" or info["argv0"] == "sshd":
            return True
        pid = info["ppid"]
    return False


def config_dir(environ: dict) -> str:
    return os.path.expanduser(environ.get("CLAUDE_CONFIG_DIR") or "~/.claude").rstrip("/")


def _records(directory: str) -> list[dict]:
    out = []
    for path in sorted((Path(directory) / "sessions").glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(data, dict) and isinstance(data.get("pid"), int):
            out.append(data)
    return out


def _client_pids(session: str | None, directory: str) -> tuple[list[dict], str]:
    """(candidate client records, how they were found)."""
    records = _records(directory)
    mine = [r for r in records if session and r.get("sessionId") == session]
    if mine:
        direct = [r for r in mine if r.get("kind") == "interactive"]
        if direct:
            return direct, "session record"
        jobs = {r.get("jobId") for r in mine if r.get("jobId")}
        return [r for r in records if r.get("kind") == "interactive" and r.get("parkedJobId") in jobs], "parked job"
    return [], "unlinked"


def record_matches(record: dict, info: dict) -> bool:
    """The record still describes the live process: its recorded start time equals the /proc start time (a stale
    record whose pid was recycled fails)."""
    return record.get("procStart") is not None and str(record["procStart"]) == str(info["start"])


def is_client(info: dict | None) -> bool:
    """A terminal client: an agent process with a tty that is not a daemon/host helper."""
    return bool(info) and bool(info.get("tty")) and proc.is_agent(info) and not any(
        w in info.get("args", [])[:2] for w in DAEMON_WORDS)


def _is_wrapper(winfo: dict | None) -> bool:
    if not winfo or winfo["state"] == "Z":
        return False
    mine = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "relay_run.py"))
    return any(os.path.basename(a) == "relay_run.py" and os.path.realpath(a) == mine
               for a in ([winfo.get("argv0", "")] + winfo.get("args", [])[:2]))


def wrapper_proof(pid: int, info: dict) -> dict | None:
    """{"pid","start"} of the relay_run.py parent of client `pid`, or None. Proof: the client's environment names the
    wrapper, the client is its direct child (ppid), and the wrapper's command line is relay_run.py. Works over ssh."""
    env = proc.environ_of(pid) or {}
    value = env.get(WRAPPER_VAR, "")
    if not value.isdigit() or int(value) != info.get("ppid"):
        return None
    winfo = proc.read(int(value))
    return {"pid": int(value), "start": winfo["start"]} if _is_wrapper(winfo) else None


def verify_wrapper(pid: int, start: int, wrapper_pid: int, wrapper_start: int) -> bool:
    """The same proof, re-checked later against the start times pinned at handoff (a recycled pid fails)."""
    info = proc.read(pid)
    winfo = proc.read(wrapper_pid)
    return (bool(info) and info["start"] == start and info["ppid"] == wrapper_pid and is_client(info)
            and bool(winfo) and winfo["start"] == wrapper_start and _is_wrapper(winfo)
            and (proc.environ_of(pid) or {}).get(WRAPPER_VAR) == str(wrapper_pid))


def locate(environ: dict, session: str | None, provider: str, own_pid: int | None = None) -> dict:
    """{"pid","start","mux","wrapper","why"}. Primary: the client is a child of relay_run.py (`wrapper`). Secondary:
    a verified multiplexer pane (`mux`). Neither: pid/start are None and `why` says why (manual)."""
    own_pid = own_pid or os.getpid()
    none = lambda why: {"pid": None, "start": None, "mux": None, "wrapper": None, "why": why}  # noqa: E731
    muxes = mux_candidates(environ)
    record = None
    if muxes or environ.get(WRAPPER_VAR):
        found = proc.find_agent(own_pid)
        if not found:
            return none("no agent process found above this command")
        pid, how = found[0], "ancestor"
    else:
        if provider != "claude":
            return none("outside a multiplexer a Codex client cannot be tied to its session")
        candidates, how = _client_pids(session, config_dir(environ))
        if how == "unlinked":
            return none("no session record links this session to a terminal client")
        if not candidates:
            return none("the session has no attached terminal client")
        if len(candidates) > 1:
            return none(f"several terminal clients match ({', '.join(str(c['pid']) for c in candidates)}): not guessing")
        record = candidates[0]
        pid = record["pid"]
    info = proc.read(pid)
    if not is_client(info):
        return none(f"pid {pid} is not a terminal client")
    if record is not None and not record_matches(record, info):
        return none(f"the session record of pid {pid} is stale (start time differs): not trusting it")
    cenv = proc.environ_of(pid) or {}
    cmux = mux_candidates(cenv)
    pane = cmux[0] if len(cmux) == 1 and (not muxes or (len(muxes) == 1 and muxes[0]["target"] == cmux[0]["target"])) else None
    wrapper = wrapper_proof(pid, info)
    if wrapper:
        return {"pid": pid, "start": info["start"], "mux": pane, "wrapper": wrapper,
                "why": "parent relay_run.py wrapper" + (" (client found by " + how + ")" if record else "")}
    if len(muxes) > 1 or len(cmux) > 1:
        return none("nested multiplexers: not guessing the pane")
    if under_ssh(pid):
        return none("the client runs over ssh without the relay wrapper: no local pane to type into")
    if muxes and not pane:
        return none("the client's own environment does not carry the same pane variable: pane not proven")
    if not cmux:
        return none("the client is not inside zellij, tmux or kitty and has no relay wrapper")
    return {"pid": pid, "start": info["start"], "mux": pane, "wrapper": None, "why": f"client found by {how}"}
