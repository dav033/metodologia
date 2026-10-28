"""Agent windows the web can see and talk to: an agent runs inside a detached tmux session of its own.

The owner is not always in front of the desktop, and a session that finished its turn cannot be woken by anything but
typed input. Running the agent in tmux (a private socket, so it never mixes with the owner's own tmux) lets the web
`send` a message exactly as if it were typed, show the `screen` and tell whether the agent is still alive. The same
pieces serve the dedicated Planner (`start_planner`) and the hands-on subplan sessions (`bt_subplan_sessions`).
Attach by hand with `tmux -L bitacora attach -t <name>`.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import time
import uuid
from pathlib import Path

NAME_OK = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,80}")
ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)")
MAX_SAY = 2000


def socket() -> str:
    return os.environ.get("BITACORA_TMUX_SOCKET") or "bitacora"


def _tmux_path() -> str | None:
    extra = os.pathsep.join([str(Path.home() / ".local" / "bin"), "/usr/local/bin", "/usr/bin"])
    return shutil.which("tmux", path=os.environ.get("PATH", "") + os.pathsep + extra)


def _run(*args: str, timeout: int = 15) -> subprocess.CompletedProcess:
    exe = _tmux_path()
    if exe is None:
        raise RuntimeError("tmux no está instalado.")
    return subprocess.run([exe, "-L", socket(), *args], capture_output=True, text=True, timeout=timeout, check=False)


def name_for(project: str, req: str, role: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "-", f"bit-{project}-{req}-{role}")[:80]


def exists(name: str) -> bool:
    try:
        return bool(NAME_OK.fullmatch(name)) and _run("has-session", "-t", f"={name}").returncode == 0
    except (RuntimeError, OSError, subprocess.SubprocessError):
        return False


def start(name: str, cwd: Path, command: str, env: dict[str, str] | None = None) -> None:
    """Run `command` (a shell line) in a new detached session; the shell stays open when the agent exits."""
    if not NAME_OK.fullmatch(name):
        raise ValueError("nombre de sesión no válido")
    if exists(name):
        raise RuntimeError(f"La sesión {name} ya existe.")
    args = ["new-session", "-d", "-s", name, "-c", str(cwd), "-x", "200", "-y", "50"]
    for key, value in (env or {}).items():
        args += ["-e", f"{key}={value}"]
    done = _run(*args, f"bash -lc {shlex.quote(command + '; exec bash')}")
    if done.returncode != 0:
        raise RuntimeError("No pude abrir la sesión: " + (done.stderr or "").strip()[:200])


def send(name: str, text: str) -> str:
    """Type `text` into the agent and press Enter; newlines become spaces so one message is one submission."""
    text = re.sub(r"\s+", " ", ANSI.sub("", text or "")).strip()[:MAX_SAY]
    if not text:
        return "No hay nada que enviar."
    if not exists(name):
        return "El agente ya no está en marcha."
    if _run("send-keys", "-t", f"={name}:", "-l", text).returncode != 0:
        return "No pude escribirle al agente."
    time.sleep(0.4)                                   # let the TUI take the text before the Enter that submits it
    _run("send-keys", "-t", f"={name}:", "Enter")
    return "Enviado."


def screen(name: str, lines: int = 40) -> str:
    """The last `lines` non-empty lines of what the agent shows, without colour codes."""
    if not exists(name):
        return ""
    out = _run("capture-pane", "-p", "-t", f"={name}:", "-S", f"-{max(lines * 3, 120)}").stdout
    rows = [ANSI.sub("", line).rstrip() for line in out.splitlines()]
    while rows and not rows[-1]:
        rows.pop()
    return "\n".join(rows[-lines:])


def kill(name: str) -> bool:
    return exists(name) and _run("kill-session", "-t", f"={name}").returncode == 0


# ------------------------------------------------------------------ the dedicated Planner

def planner_prompt(project: str, rdir: Path) -> str:
    req = re.match(r"REQ-\d+", Path(rdir).name)
    req = req.group(0) if req else Path(rdir).name
    extra = ""
    brief = Path(rdir) / "PLANNER-PROMPT.md"
    if brief.is_file():
        extra = "\n\nOwner brief for this plan:\n" + brief.read_text(encoding="utf-8")[:8000]
    return (
        f"You are the dedicated Planner for {project} {req}, run through the metodologia skill in HQ mode. Talk to the owner "
        "in Spanish; bitácora files in English. Do NOT implement anything: your job is the plan, built WITH the owner "
        "through the collaborative planning flow.\n\n"
        f"Before anything else run: python ~/.claude/skills/metodologia/scripts/bitacora.py --project {project} planning "
        f"resume {req}  and follow its NEXT line. Read SPEC.md (its Clarifications are the owner's decisions) and the "
        "project DECISIONS.md. Never re-ask a round that is answered. The owner talks to you through the web: a message "
        "typed there arrives as a normal user message in this window.\n\n"
        "Rules: write each subplan's `## Pruebas` row in SPEC.md as you define it (D-131); never confirm a subplan or the "
        "skeleton for the owner; a subplan the owner wants to build hands-on has a session branch (`sessions status`): "
        "plan its tasks around that branch; do not launch the plan yourself; never print secrets.\n\n"
        "Memory: this session can be killed at any moment and replaced. What you learn must live in files, not in your "
        f"head. After each finding (with file paths), decision (with its reason), open question or to-do run "
        f"`bitacora.py --project {project} planning note {req} --kind finding|decision|question|todo --text '...'`, and "
        "before you end a turn write a `--kind handoff` note: what you were doing, why, and what comes next." + extra)


RECORD = ".planning/planner.json"
RESTART_MESSAGE = ("You were restarted. Your earlier conversation is above: continue from it. Run `planning resume` first "
                   "(it prints your saved notes and what comes next), then carry on with the owner's plan.")


def _record(rdir: Path) -> dict:
    try:
        data = json.loads((Path(rdir) / RECORD).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _save_record(rdir: Path, data: dict) -> None:
    target = Path(rdir) / RECORD
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def transcript(config_dir: str, cwd: str, session_id: str) -> Path:
    """Where Claude Code keeps a session's conversation: <config>/projects/<cwd with non-alphanumerics as dashes>/<id>.jsonl."""
    base = Path(config_dir) if config_dir else Path.home() / ".claude"
    return base / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(Path(cwd).resolve())) / f"{session_id}.jsonl"


def remember_planner(rdir: Path, session_id: str, config_dir: str, cwd: str) -> None:
    """Record the conversation of an already running Planner (started before this record existed)."""
    _save_record(rdir, {**_record(rdir), "session_id": session_id, "config_dir": config_dir, "cwd": str(cwd)})


def start_planner(root: Path, project: str, rdir: Path, *, fresh: bool = False) -> tuple[bool, str]:
    """Start the dedicated Planner in tmux. It picks up its own earlier CONVERSATION (`claude --resume`) when that exists,
    so killing it and starting another loses nothing; `fresh` or a missing transcript starts a new conversation that
    relies on `planning resume` and the saved notes."""
    req = re.match(r"REQ-\d+", Path(rdir).name)
    name = name_for(project, req.group(0) if req else Path(rdir).name, "planner")
    if exists(name):
        return False, f"Ya hay un Planner en marcha para este plan ({name})."
    account = os.environ.get("BITACORA_PLANNER_CLAUDE_CONFIG_DIR") or (
        str(Path.home() / ".claude-work") if (Path.home() / ".claude-work").is_dir() else "")
    env = {"CLAUDE_CONFIG_DIR": account} if account else {}
    flags = "--model opus --effort high --dangerously-skip-permissions"
    prior = {} if fresh else _record(rdir)
    sid = prior.get("session_id") or ""
    resumed = bool(sid) and transcript(prior.get("config_dir", account), prior.get("cwd", str(root)), sid).is_file()
    if resumed:
        command = f'claude --resume {shlex.quote(sid)} {flags} {shlex.quote(RESTART_MESSAGE)}'
        how = "retomó su conversación anterior"
    else:
        sid = str(uuid.uuid4())
        prompt_file = Path.home() / ".local" / "share" / "bitacora-sessions" / project / f"{name}.prompt.md"
        prompt_file.parent.mkdir(parents=True, exist_ok=True)
        prompt_file.write_text(planner_prompt(project, rdir), encoding="utf-8")
        command = f'claude --session-id {sid} {flags} "$(cat {shlex.quote(str(prompt_file))})"'
        how = "empezó una conversación nueva (leerá el plan y sus notas guardadas)"
    try:
        start(name, Path(root), command, env)
    except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as exc:
        return False, str(exc)
    _save_record(rdir, {**_record(rdir), "session_id": sid, "config_dir": account, "cwd": str(root),
                        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "resumed": resumed})
    return True, f"Planner abierto ({name}): {how}."


def notify_planner(project: str, req: str, text: str) -> bool:
    """Tell the dedicated Planner, if it runs here, what the owner just did on the web (an idle agent never learns it
    otherwise). Returns False when there is no such Planner or the message could not be typed."""
    name = name_for(project, req, "planner")
    return exists(name) and send(name, "[Automatic notice from the web, not typed by the owner] " + text) == "Enviado."


REVIVE_WITHIN_DAYS = 3
_DONE = {"approved", "launched", "in-progress", "done", "cancelled"}


def revive_planners(root: Path) -> list[str]:
    """Start again, after a reboot, the Planners that were running: tmux does not survive it and nothing else brought them
    back, so the owner's answers on the web reached nobody (REQ-021 SP-3). A Planner comes back only when its plan is still
    being planned, it ran in the last `REVIVE_WITHIN_DAYS` days and it has a conversation to resume. Returns what was started."""
    from bt_core import _front

    started: list[str] = []
    limit = time.time() - REVIVE_WITHIN_DAYS * 86400
    for record in sorted(Path(root).glob("*/requirements/REQ-*/" + RECORD)):
        rdir, project = record.parents[1], record.parents[3].name
        try:
            data = _record(rdir)
            when = time.mktime(time.strptime(data.get("started_at", "")[:19], "%Y-%m-%dT%H:%M:%S"))
            req = re.match(r"REQ-\d+", rdir.name)
            if (not data.get("session_id") or when < limit or not req
                    or _front(rdir / "PLAN.md", "status") in _DONE or exists(name_for(project, req.group(0), "planner"))):
                continue
            ok, message = start_planner(Path(root), project, rdir)
            if ok:
                started.append(f"{project}/{req.group(0)}")
        except (ValueError, OSError, RuntimeError, subprocess.SubprocessError):
            continue
    return started


def restart_planner(root: Path, project: str, rdir: Path) -> tuple[bool, str]:
    """Kill the running Planner and start it again on the same conversation; nothing it knew is lost."""
    req = re.match(r"REQ-\d+", Path(rdir).name)
    name = name_for(project, req.group(0) if req else Path(rdir).name, "planner")
    if not _record(rdir).get("session_id"):
        return False, "No sé qué conversación llevaba este Planner, así que no lo reinicio: ábrelo desde cero o dime cuál es."
    kill(name)
    return start_planner(root, project, rdir)
