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


# What Claude Code prints when the account ran out: every notice typed into such a Planner is lost (pictures REQ-021,
# 2026-10-29: claude-work hit its weekly limit and five notices from the web reached nobody).
LIMITED = re.compile(r"hit your (?:weekly |usage |session )?limit|usage limit reached|/usage-credits", re.I)
# A question only the owner may answer: Claude Code's first run under an account asks him to accept bypass-permissions
# mode, and a Planner moved to that account waits on it (claude-luis, 2026-10-29); an operator may not accept it for him.
OWNER_PROMPT = re.compile(r"Bypass Permissions mode.*Yes, I accept", re.S)


def unattended(config_dir: str) -> bool:
    """Can Claude Code run under this account without asking the owner first? Only when its settings accept
    bypass-permissions mode (`skipDangerousModePermissionPrompt`), which only the owner sets."""
    base = Path(config_dir) if config_dir else Path.home() / ".claude"
    try:
        return json.loads((base / "settings.json").read_text(encoding="utf-8")).get("skipDangerousModePermissionPrompt") is True
    except (OSError, UnicodeError, ValueError, AttributeError):
        return False


def planner_route(project: str, avoid: str = "") -> dict[str, str]:
    """Where the Planner runs, {provider, home, model, effort}: the owner's override; else the Claude account the router
    ranks first for the planner role that can run unattended, other than `avoid` (it keeps its conversation); else the
    first Codex route of that ranking (the owner's codex homes never ask: a new conversation from `planning resume` and
    the saved notes); else ~/.claude-work as before. A Planner moved to an account that asks the owner first waited there
    with every notice lost (claude-luis, 2026-10-29)."""
    if override := os.environ.get("BITACORA_PLANNER_CLAUDE_CONFIG_DIR"):
        return {"provider": "claude", "home": override, "model": "opus", "effort": "high"}
    codex: dict[str, str] | None = None
    try:
        import bt_agents
        import bt_profiles
        profiles = bt_profiles.load()
        pool = bt_agents.pool_for(project, bt_agents._config("routing.pool", []) or None)
        routes, _ = bt_agents.candidates(project, pool, bt_agents.start_tier(None, "plan"), "plan", allow_explore=False,
                                         role="planner")
        for route in routes:
            env = (profiles.get(route.get("profile")) or {}).get("env") or {}
            if route.get("agent") == "claude":
                path = env.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude")
                if path != avoid and unattended(path):
                    return {"provider": "claude", "home": path, "model": "opus", "effort": "high"}
            elif route.get("agent") == "codex" and codex is None:
                home = env.get("CODEX_HOME") or str(Path.home() / ".codex")
                if home != avoid:
                    codex = {"provider": "codex", "home": home, "model": str(route.get("model") or ""),
                             "effort": str(route.get("effort") or "high")}
    except Exception:  # noqa: BLE001 - no ranking: the account it always used
        pass
    if codex:
        return codex
    work = Path.home() / ".claude-work"
    return {"provider": "claude", "home": str(work) if work.is_dir() and str(work) != avoid else "", "model": "opus",
            "effort": "high"}


def _prompt_file(project: str, name: str, text: str) -> Path:
    path = Path.home() / ".local" / "share" / "bitacora-sessions" / project / f"{name}.prompt.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def start_planner(root: Path, project: str, rdir: Path, *, fresh: bool = False, avoid: str = "",
                  message: str = "") -> tuple[bool, str]:
    """Start the dedicated Planner in tmux where it can run unattended (`planner_route`). On Claude it picks up its own
    earlier CONVERSATION (`claude --resume`) when that exists, copied to that account when it lived in another one, so
    killing it and starting another loses nothing; `fresh`, a missing transcript or Codex starts a new conversation that
    relies on `planning resume` and the saved notes. `message` is told on start (a notice that found it unable to run)."""
    req = re.match(r"REQ-\d+", Path(rdir).name)
    name = name_for(project, req.group(0) if req else Path(rdir).name, "planner")
    if exists(name):
        return False, f"Ya hay un Planner en marcha para este plan ({name})."
    route = planner_route(project, avoid)
    account = route["home"]
    extra = f"\n\n{message}" if message else ""
    if route["provider"] == "codex":
        prompt_file = _prompt_file(project, name, planner_prompt(project, rdir) + extra)
        model = f"-m {shlex.quote(route['model'])} " if route["model"] else ""
        command = (f"codex --dangerously-bypass-approvals-and-sandbox {model}-c "
                   f"model_reasoning_effort={shlex.quote(route['effort'])} \"$(cat {shlex.quote(str(prompt_file))})\"")
        try:
            start(name, Path(root), command, {"CODEX_HOME": account})
        except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as exc:
            return False, str(exc)
        _save_record(rdir, {**_record(rdir), "provider": "codex", "codex_home": account, "cwd": str(root),
                            "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "resumed": False})
        return True, (f"Planner abierto ({name}) en Codex {route['model']}: ninguna cuenta de Claude con cuota puede correr "
                      "sin pedirte permiso, así que empezó desde el plan y sus notas guardadas.")
    env = {"CLAUDE_CONFIG_DIR": account} if account else {}
    flags = "--model opus --effort high --dangerously-skip-permissions"
    prior = {} if fresh else _record(rdir)
    sid = prior.get("session_id") or ""
    if sid:
        old = transcript(prior.get("config_dir", account), prior.get("cwd", str(root)), sid)
        new = transcript(account, str(root), sid)
        if old.is_file() and not new.is_file():
            new.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(old, new)
    resumed = bool(sid) and transcript(account, str(root), sid).is_file()
    if resumed:
        command = f'claude --resume {shlex.quote(sid)} {flags} {shlex.quote(RESTART_MESSAGE + extra)}'
        how = "retomó su conversación anterior"
    else:
        sid = str(uuid.uuid4())
        prompt_file = _prompt_file(project, name, planner_prompt(project, rdir) + extra)
        command = f'claude --session-id {sid} {flags} "$(cat {shlex.quote(str(prompt_file))})"'
        how = "empezó una conversación nueva (leerá el plan y sus notas guardadas)"
    try:
        start(name, Path(root), command, env)
    except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as exc:
        return False, str(exc)
    _save_record(rdir, {**_record(rdir), "provider": "claude", "session_id": sid, "config_dir": account, "cwd": str(root),
                        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "resumed": resumed})
    return True, f"Planner abierto ({name}): {how}."


def notify_planner(project: str, req: str, text: str) -> bool:
    """Tell the dedicated Planner, if it runs here, what the owner just did on the web (an idle agent never learns it
    otherwise). A Planner whose account ran out is started again on one with quota and told on start. Returns False
    when there is no such Planner or the message could not be typed."""
    name = name_for(project, req, "planner")
    if not exists(name):
        return False
    notice = "[Automatic notice from the web, not typed by the owner] " + text
    shown = screen(name, 20)
    if OWNER_PROMPT.search(shown):
        _ask_owner(project, req, name)
        return False
    if LIMITED.search(shown):
        from bt_core import ROOT
        rdir = next(iter(sorted((Path(ROOT) / project / "requirements").glob(f"{req}-*"))), None)
        if rdir is not None:
            record = _record(rdir)
            avoid = record.get("codex_home", "") if record.get("provider") == "codex" else record.get("config_dir", "")
            kill(name)
            return start_planner(Path(ROOT), project, rdir, avoid=avoid, message=notice)[0]
    return send(name, notice) == "Enviado."


def _ask_owner(project: str, req: str, name: str) -> None:
    """The Planner waits on a question only the owner answers: tell him where, on the desktop and in the plan's feed."""
    text = (f"El Planner de {req} espera que aceptes el modo Bypass Permissions en su cuenta: abre una terminal, "
            f"`tmux -L {socket()} attach -t {name}`, elige «Yes, I accept» y sal con Ctrl-b d. Hasta entonces no recibe "
            "los avisos de la web.")
    try:
        import bt_runutil
        bt_runutil.notify("El Planner espera tu respuesta", text)
        from bt_core import ROOT
        import bt_planning_activity as activity
        rdir = next(iter(sorted((Path(ROOT) / project / "requirements").glob(f"{req}-*"))), None)
        if rdir is not None:
            activity.record(rdir, "Planner", text, kind="flow")
    except Exception:  # noqa: BLE001 - telling him is best effort; the panel's agent strip shows the screen too
        pass


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
