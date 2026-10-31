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

import bt_agent_wall as wall

# what an agent prints when its account ran out; a question only the owner may answer (the Solucionador reads them here)
LIMITED, OWNER_PROMPT = wall.LIMITED, wall.OWNER_PROMPT

NAME_OK = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,80}")
ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)")
MAX_SAY = 2000


def socket() -> str:
    return os.environ.get("BITACORA_TMUX_SOCKET") or "bitacora"


def _tmux_path() -> str | None:
    extra = os.pathsep.join([str(Path.home() / ".local" / "bin"), "/usr/local/bin", "/usr/bin"])
    return shutil.which("tmux", path=os.environ.get("PATH", "") + os.pathsep + extra)


# what the bitácora's tmux server must not inherit from the process that happens to start it: bt-durable.service starts
# it for the Solucionador (REQ-031), and every later session on the socket (Planners, subplan sessions) gets the server's
# environment — the engine's database URL with its password (BT_DURABLE_DATABASE_URL) and the engine's own `uv run`
# virtual environment (VIRTUAL_ENV, its bin first on PATH) included (audit of REQ-030, 2026-10-29)
ENGINE_ONLY_PREFIXES = ("BT_DURABLE_", "DBOS_")
ENGINE_INTERPRETER_ENV = frozenset({"VIRTUAL_ENV", "VIRTUAL_ENV_PROMPT", "UV_RUN_RECURSION_DEPTH"})


def session_environment(environ: dict[str, str] | None = None) -> dict[str, str]:
    environ = dict(os.environ if environ is None else environ)
    venv = environ.get("VIRTUAL_ENV", "")
    out = {k: v for k, v in environ.items()
           if not k.startswith(ENGINE_ONLY_PREFIXES) and k not in ENGINE_INTERPRETER_ENV}
    if venv and "PATH" in out:
        own = str(Path(venv) / "bin")
        out["PATH"] = os.pathsep.join(p for p in out["PATH"].split(os.pathsep) if p and p.rstrip("/") != own)
    return out


def _run(*args: str, timeout: int = 15, prefix: tuple[str, ...] = ()) -> subprocess.CompletedProcess:
    exe = _tmux_path()
    if exe is None:
        raise RuntimeError("tmux no está instalado.")
    return subprocess.run([*prefix, exe, "-L", socket(), *args], capture_output=True, text=True, timeout=timeout,
                          check=False, env=session_environment())


def name_for(project: str, req: str, role: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "-", f"bit-{project}-{req}-{role}")[:80]


def exists(name: str) -> bool:
    try:
        return bool(NAME_OK.fullmatch(name)) and _run("has-session", "-t", f"={name}").returncode == 0
    except (RuntimeError, OSError, subprocess.SubprocessError):
        return False


def start(name: str, cwd: Path, command: str, env: dict[str, str] | None = None, *, scope: str = "") -> None:
    """Run `command` (a shell line) in a new detached session; the shell stays open when the agent exits.

    `scope`: a systemd scope unit name to start it in. A tmux server started from a service lives in that service's
    cgroup and dies with it: the Solucionador is launched by bt-durable.service and restarts that very unit when it
    integrates a fix (REQ-031). Without systemd-run, or when the scope cannot be created, it starts as before."""
    if not NAME_OK.fullmatch(name):
        raise ValueError("nombre de sesión no válido")
    if exists(name):
        raise RuntimeError(f"La sesión {name} ya existe.")
    args = ["new-session", "-d", "-s", name, "-c", str(cwd), "-x", "200", "-y", "50"]
    for key, value in (env or {}).items():
        args += ["-e", f"{key}={value}"]
    line = f"bash -lc {shlex.quote(command + '; exec bash')}"
    runner = shutil.which("systemd-run") if scope else None
    done = None
    if runner:
        done = _run(*args, line, prefix=(runner, "--user", "--scope", "--quiet", "--collect", f"--unit={scope}"))
    if done is None or (done.returncode != 0 and not exists(name)):
        done = _run(*args, line)
    if done.returncode != 0:
        raise RuntimeError("No pude abrir la sesión: " + (done.stderr or "").strip()[:200])


class Said(str):
    """What `send` reports, a plain Spanish text (callers compare it with «Enviado.»), plus `state`: sent | empty |
    gone | error | unsent | limited (a quota wall answered the message; `until` is when the account comes back, epoch
    or None) | owner (a question only the owner answers) | blocked (a modal nobody here may answer); and `answered`,
    the harmless modals answered on the way."""
    state: str = "sent"
    until: float | None = None
    answered: tuple[str, ...] = ()

    @classmethod
    def of(cls, text: str, state: str, until: float | None = None, answered: list[str] | None = None) -> Said:
        said = cls(text)
        said.state, said.until, said.answered = state, until, tuple(answered or ())
        return said


WALL_WAIT = 4.0                                       # seconds a quota wall takes to answer a submitted message


def send(name: str, text: str) -> Said:
    """Type `text` into the agent and press Enter; newlines become spaces so one message is one submission. It counts
    as sent only when the agent can act on it: a harmless modal in the way is answered first (Codex's «Switch to
    <model>?»: «Keep current model»), and a quota wall that answers the message makes it «limited», never «Enviado»
    (pictures REQ-021's Planner, 2026-10-30 16:25)."""
    text = re.sub(r"\s+", " ", ANSI.sub("", text or "")).strip()[:MAX_SAY]
    if not text:
        return Said.of("No hay nada que enviar.", "empty")
    if not exists(name):
        return Said.of("El agente ya no está en marcha.", "gone")
    answered: list[str] = []
    if stop := _clear_modals(name, answered):
        return stop
    before = screen(name, 200)
    if _run("send-keys", "-t", f"={name}:", "-l", text).returncode != 0:
        return Said.of("No pude escribirle al agente.", "error")
    time.sleep(0.4)                                   # let the TUI take the text before the Enter that submits it
    _run("send-keys", "-t", f"={name}:", "Enter")
    for _ in range(SUBMIT_TRIES):                     # a long text can wait in the composer as a paste (D-199)
        time.sleep(0.6)
        if not unsent(screen(name, 12), text):
            break
        _run("send-keys", "-t", f"={name}:", "Enter")
    else:
        time.sleep(0.6)
        if unsent(screen(name, 12), text):
            return Said.of("Quedó escrito en el agente sin enviarse.", "unsent", answered=answered)
    return _watch(name, text, before, answered)


def _watch(name: str, text: str, before: str, answered: list[str]) -> Said:
    """After the submit: does a quota wall answer the message, or a modal stop it, within `WALL_WAIT` seconds?"""
    deadline = time.monotonic() + WALL_WAIT
    while True:
        shown = screen(name, 200)
        after = _after(shown, text, before)
        hit, until = wall.limited(after, time.time(), fresh=True)
        if hit:
            when = wall.clock(until)
            return Said.of("El agente no lo leyó: su cuenta se quedó sin cuota"
                           + (f" (vuelve a las {when})." if when else "."), "limited", until, answered)
        if stop := _clear_modals(name, answered, submitted=True):
            return stop
        if unsent(screen(name, 12), text):            # a modal that took the Enter left the message in the box
            _run("send-keys", "-t", f"={name}:", "Enter")
        if time.monotonic() >= deadline:
            return Said.of("Enviado.", "sent", answered=answered)
        time.sleep(0.4)


def _after(shown: str, text: str, before: str) -> str:
    """What the agent printed after the message (flattened): what follows its echo, or, when the echo is not found,
    whatever walls are new since `before` (a wall left above from earlier never counts)."""
    flat, said = " ".join((shown or "").split()), " ".join(text.split())
    key = said[:60]
    if key and (at := flat.rfind(key)) >= 0:          # the message's own words never count (it may quote a wall)
        rest = flat[at:]
        return rest[len(said):] if rest.startswith(said) else rest[len(key):]
    found = list(wall.LIMITED.finditer(shown or ""))
    if len(found) > len(wall.LIMITED.findall(before or "")):
        return (shown or "")[found[-1].start():]
    return ""


def visible(name: str) -> str:
    """What the agent's window shows right now (no scrollback): where a modal waits for a key."""
    if not exists(name):
        return ""
    rows = [ANSI.sub("", line).rstrip() for line in _run("capture-pane", "-p", "-t", f"={name}:").stdout.splitlines()]
    return "\n".join(row for row in rows if row.strip())


def _clear_modals(name: str, answered: list[str], *, submitted: bool = False) -> Said | None:
    """Answer the harmless modals at the bottom of the window; a question that is not ours to answer stops the send.
    Once the message is `submitted`, a selection list is the agent acting on it (a question to the owner): left alone."""
    for _ in range(3):
        shown = "\n".join(visible(name).splitlines()[-16:])
        kind, key = wall.modal(shown)
        if kind == "owner":
            return Said.of("El agente espera una respuesta que solo tú puedes dar; no le escribí.", "owner",
                           answered=answered)
        if kind == "blocking" and not submitted:
            return Said.of("El agente espera que elijas una opción en su ventana; no le escribí para no elegir por ti.",
                           "blocked", answered=answered)
        if kind != "model-switch":
            return None
        _run("send-keys", "-t", f"={name}:", "-l", key)            # «Keep current model»: digits select in Codex lists
        time.sleep(0.6)
        still = "\n".join(visible(name).splitlines()[-16:])
        if wall.MODEL_SWITCH.search(still) and re.search(rf"^\s*›\s*{key}\.", still, re.MULTILINE):
            _run("send-keys", "-t", f"={name}:", "Enter")          # the digit only moved the selection there
            time.sleep(0.6)
        answered.append("Codex ofrecía cambiar a un modelo más barato: elegí «Keep current model»")
    return Said.of("El agente muestra un aviso que no pude cerrar; no le escribí.", "blocked", answered=answered)


SUBMIT_TRIES = 3
PASTED = re.compile(r"\[Pasted (?:Content|text)[^\]]*\]", re.IGNORECASE)


def unsent(shown: str, text: str) -> bool:
    """Is the message still in the agent's input box? Codex keeps a long typed text as «[Pasted Content N chars]» and
    needs another Enter; tell-planner said «Enviado» while pictures REQ-021's Planner never got the 039 defect
    (2026-10-30 07:40, D-199). Only the last prompt line counts: the input box is at the bottom."""
    prompts = [line.strip() for line in (shown or "").splitlines() if line.strip().startswith(("›", ">"))]
    if not prompts:
        return False
    content = prompts[-1][1:].strip()                 # the last prompt line is the input box
    return bool(content) and (bool(PASTED.search(content)) or (text or "").startswith(content[:30]))


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
    return role_route(project, "planner", avoid, override="BITACORA_PLANNER_CLAUDE_CONFIG_DIR")


def role_route(project: str, role: str, avoid: str = "", *, override: str = "") -> dict[str, str]:
    """`planner_route` for any long-lived full-access session of a role (the Planner, the Solucionador of REQ-031):
    Claude Opus at high effort on the first unattended account the router ranks for `role`, else that ranking's first
    Codex route, else ~/.claude-work. `override` names an environment variable that pins the Claude account. When the
    ranking leaves no account but `avoid` (every other one is spent or cooling), the fallback says so: `exhausted` and
    `until`, the epoch the first one frees up ("" when unknown); a caller leaving a spent account waits instead."""
    if override and (pinned := os.environ.get(override)):
        return {"provider": "claude", "home": pinned, "model": "opus", "effort": "high"}
    codex: dict[str, str] | None = None
    spent: dict[str, str] = {}
    try:
        import bt_agents
        import bt_profiles
        profiles = bt_profiles.load()
        pool = bt_agents.pool_for(project, bt_agents._config("routing.pool", []) or None)
        routes, frees = bt_agents.candidates(project, pool, bt_agents.start_tier(None, "plan"), "plan",
                                             allow_explore=False, role=role)
        others = 0
        for route in routes:
            env = (profiles.get(route.get("profile")) or {}).get("env") or {}
            if route.get("agent") == "claude":
                path = env.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude")
                others += path != avoid
                if path != avoid and unattended(path):
                    return {"provider": "claude", "home": path, "model": "opus", "effort": "high"}
            elif route.get("agent") == "codex" and codex is None:
                home = env.get("CODEX_HOME") or str(Path.home() / ".codex")
                others += home != avoid
                if home != avoid:
                    codex = {"provider": "codex", "home": home, "model": str(route.get("model") or ""),
                             "effort": str(route.get("effort") or "high")}
        if not others:
            spent = {"exhausted": "1", "until": str(frees or "")}
    except Exception:  # noqa: BLE001 - no ranking: the account it always used
        pass
    if codex:
        return codex
    work = Path.home() / ".claude-work"
    return {"provider": "claude", "home": str(work) if work.is_dir() and str(work) != avoid else "", "model": "opus",
            "effort": "high", **spent}


def _prompt_file(project: str, name: str, text: str) -> Path:
    path = Path.home() / ".local" / "share" / "bitacora-sessions" / project / f"{name}.prompt.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def start_planner(root: Path, project: str, rdir: Path, *, fresh: bool = False, avoid: str = "",
                  message: str = "", route: dict[str, str] | None = None) -> tuple[bool, str]:
    """Start the dedicated Planner in tmux where it can run unattended (`planner_route`). On Claude it picks up its own
    earlier CONVERSATION (`claude --resume`) when that exists, copied to that account when it lived in another one, so
    killing it and starting another loses nothing; `fresh`, a missing transcript or Codex starts a new conversation that
    relies on `planning resume` and the saved notes. `message` is told on start (a notice that found it unable to run)."""
    req = re.match(r"REQ-\d+", Path(rdir).name)
    name = name_for(project, req.group(0) if req else Path(rdir).name, "planner")
    if exists(name):
        return False, f"Ya hay un Planner en marcha para este plan ({name})."
    route = route or planner_route(project, avoid)
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
    otherwise). True when the Planner got it or was started again elsewhere with it (`bt_planner_notices.tell`: a
    Planner whose account ran out moves to one with quota; with none, the notice is held and sent again on its own)."""
    import bt_planner_notices as notices
    return notices.tell(project, req, notices.WEB_NOTICE + text)[0] in ("sent", "moved")


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


def main(argv: list[str] | None = None) -> int:
    """`bt_agent_terminal.py tell-planner <project> <REQ> <text>`: what the Solucionador (REQ-031) uses to send a plan
    change request to the run's Planner; a Planner that is not running is started with the request as its first notice
    (on an account with quota, like any Planner start). It prints what really happened, and exits 0 when the Planner got
    it (or was started with it), 3 when it is held to be sent again on its own (no account with quota), 1 otherwise."""
    import sys
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 4 or args[0] != "tell-planner":
        print("usage: bt_agent_terminal.py tell-planner <project> <REQ> <text>", file=sys.stderr)
        return 2
    project, req, text = args[1:]
    import bt_planner_notices as notices
    notice = "[Automatic notice, not typed by the owner] " + text
    state, message = notices.tell(project, req, notice)
    if state == "absent":
        from bt_core import ROOT
        rdir = notices._rdir(project, req)
        if rdir is None:
            print(f"No encuentro el plan {project} {req}.", file=sys.stderr)
            return 1
        ok, message = start_planner(Path(ROOT), project, rdir, message=notice)
        state = "moved" if ok else "failed"
    print(message, file=sys.stdout if state != "failed" else sys.stderr)
    return {"sent": 0, "moved": 0, "held": 3}.get(state, 1)


if __name__ == "__main__":
    raise SystemExit(main())
