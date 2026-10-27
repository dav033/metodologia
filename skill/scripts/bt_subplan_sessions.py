"""Hands-on sessions for one subplan: the owner works WITH an agent instead of waiting for the engine (D-132).

Some subplans (a rectangular table, a Backing category) are better built with the owner in the loop. From the web or
`bitacora.py sessions start REQ SP` an interactive agent opens (in a tmux session the web can read and type into, see
`bt_agent_terminal`) in its own worktree on its own branch, outside every repository, with the subplan's outcome, criteria and the rules of the work as its first message. Nothing here
integrates, pushes or deploys: the branch is the result, `finish` records where it ended, and the Planner builds the
subplan's tasks around that branch (`planning resume` lists it).

State per requirement: `<req>/.sessions/sessions.json`. The launcher is injectable so tests never start an agent.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import shlex
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Callable

import bt_agent_terminal as terminal
import bt_planning_activity as activity
import bt_planning_flow as flow

DIR, FILE = ".sessions", "sessions.json"
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,40}")
MODELS = {"sonnet": ("sonnet", "medium", "Sonnet 5.5 · medium"), "opus": ("opus", "high", "Opus 5.5 · high")}
DEFAULT_MODEL = "sonnet"
MODES = ("hands",)              # built with the owner at the keyboard; running a subplan alone is the Scheduler's (D-134)


def _now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def _req(rdir: Path) -> str:
    found = re.match(r"REQ-\d+", Path(rdir).name)
    return found.group(0) if found else Path(rdir).name


def _git(repo: Path, *args: str, timeout: int = 120) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=timeout, env=env,
                          check=False)


@contextmanager
def _locked(rdir: Path):
    target = Path(rdir) / DIR / f".{FILE}.lock"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a+b") as handle:
        try:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        except (ImportError, OSError):
            pass
        data = _load(rdir)
        yield data
        fd, tmp = tempfile.mkstemp(prefix=f".{FILE}.", dir=target.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(data, stream, ensure_ascii=False, indent=1, sort_keys=True)
                stream.write("\n")
            os.replace(tmp, Path(rdir) / DIR / FILE)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


def _load(rdir: Path) -> dict:
    try:
        data = json.loads((Path(rdir) / DIR / FILE).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        data = {}
    if not isinstance(data, dict) or not isinstance(data.get("sessions"), list):
        data = {"sessions": []}
    return data


def base_dir() -> Path:
    return Path(os.environ.get("BITACORA_SESSIONS_DIR") or Path.home() / ".local" / "share" / "bitacora-sessions")


# ------------------------------------------------------------------ what the session is told

def _spec_excerpt(rdir: Path, covers: list[str]) -> str:
    """The SPEC lines (R1…) the subplan covers, so the agent does not have to hunt for them."""
    try:
        text = (Path(rdir) / "SPEC.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""
    wanted = {c for c in covers if isinstance(c, str)}
    return "\n".join(line for line in text.splitlines()
                     if (m := re.match(r"\s*-\s*(R\d+)\.", line)) and m.group(1) in wanted)


def prompt(root: Path, project: str, rdir: Path, sub: dict, *, branch: str, worktree: Path, base: str) -> str:
    req = _req(rdir)
    lines = [
        f"You are working WITH the owner (David) on subplan {sub['id']} of {req} in project {project}. Talk to him in "
        "Spanish, be direct, and build it together step by step: show what you did, ask when a choice is his.",
        "", f"## Subplan {sub['id']}: {sub['title']}", sub.get("outcome", ""), ""]
    if sub.get("criteria"):
        lines += ["Acceptance criteria:"] + [f"- {c}" for c in sub["criteria"] if isinstance(c, str)] + [""]
    excerpt = _spec_excerpt(rdir, list(sub.get("covers") or []))
    if excerpt:
        lines += ["Requirements it covers (from SPEC.md):", excerpt, ""]
    ui = sub.get("ref") or ""
    lines += [
        "## Where things are",
        f"- Plan and decisions: {rdir}/SPEC.md (Clarifications = what the owner already decided), {rdir}/PLAN.md"
        + (f"; the design contract is `{ui}` (see the Plan tab)" if ui else "") + ".",
        f"- Your worktree: {worktree} on branch `{branch}`, created from `{base}`. Work only there.",
        "- Inputs, test databases and credentials: the `## Inputs` table of SPEC.md says where each one lives. Never "
        "print or paste secret values.", "",
        "## Rules",
        "- Commit in small, meaningful commits on your branch. Do not push, merge, open a PR, deploy or touch any other "
        "checkout or worktree.",
        "- Follow the repository's own instructions (CLAUDE.md / AGENTS.md) and tests; run the relevant checks before "
        "saying something works.",
        "- Stay inside this subplan. Ideas outside it become notes for the owner, not changes.",
        f"- When the owner says it is done, run: python ~/.claude/skills/metodologia/scripts/bitacora.py --project "
        f"{project} sessions finish {req} {sub['id']}  (it records the branch and its last commit for the Planner).",
    ]
    return "\n".join(lines) + "\n"


def _tasks_in_order(rdir: Path, sid: str) -> list[dict]:
    """The subplan's tasks, each after the ones it depends on (ties keep the plan's order)."""
    import bt_design_drafts as drafts
    mine = [x for x in (drafts._plan(rdir).get("tasks") or []) if isinstance(x, dict) and x.get("subplan_id") == sid]
    done, ordered, ids = set(), [], {x["id"] for x in mine}
    while mine:
        ready = [x for x in mine if all(d in done or d not in ids for d in (x.get("after") or []))] or mine[:1]
        ordered.append(ready[0])
        done.add(ready[0]["id"])
        mine = [x for x in mine if x is not ready[0]]
    return ordered


# ------------------------------------------------------------------ the agent

def launch_agent(worktree: Path, name: str, prompt_file: Path, model: str, effort: str) -> str:
    """Start Claude Code interactively in a tmux session of its own with the prompt as its first message."""
    account = os.environ.get("BITACORA_SESSION_CLAUDE_CONFIG_DIR")
    env = {"CLAUDE_CONFIG_DIR": account} if account else {}
    terminal.start(name, worktree, f'claude --model {shlex.quote(model)} --effort {shlex.quote(effort)} '
                   f'--dangerously-skip-permissions "$(cat {shlex.quote(str(prompt_file))})"', env)
    return name


# ------------------------------------------------------------------ actions

def _repo(root: Path, project: str) -> tuple[Path | None, str]:
    """A local clone of the project's code and the ref new work starts from (origin's default branch)."""
    import bt_workspace as ws
    for path in ws.repos(root, project).values():
        path = Path(path)
        if path.exists() and _git(path, "rev-parse", "--git-dir").returncode == 0:
            _git(path, "fetch", "--quiet", "origin", timeout=60)                  # best effort: offline still works
            for ref in ("origin/main", "origin/master"):
                if _git(path, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").returncode == 0:
                    return path, ref
            return path, "HEAD"
    return None, ""


def _alive(name: object) -> bool:
    return isinstance(name, str) and terminal.exists(name)


def sessions(rdir: Path, sid: str = "") -> list[dict]:
    return [s for s in _load(rdir)["sessions"] if not sid or s["subplan"] == sid]


def active(rdir: Path, sid: str) -> dict | None:
    return next((s for s in sessions(rdir, sid) if s["status"] == "running"), None)


def start(root: Path, project: str, rdir: Path, sid: str, model: str = DEFAULT_MODEL, mode: str = "hands", *,
          launcher: Callable[..., str] | None = None) -> tuple[bool, str]:
    sub = next((s for s in flow._plan_order(rdir) if s["id"] == sid), None) if SAFE_ID.fullmatch(sid or "") else None
    if sub is None:
        return False, "Ese subplan no existe en el plan."
    if mode == "auto":
        return False, (f"SESSION_AUTO_SUPERSEDED: un subplan ya no se ejecuta solo en una sesión; lo ejecuta el Scheduler "
                       f"(«Ejecutar subplan» en la pestaña Plan o `bitacora.py stage run {_req(rdir)} {sid}`).")
    mode = "hands"
    if (live := active(rdir, sid)) is not None:
        if _alive(live.get("tmux")):
            return False, f"Ya hay una sesión en marcha para {sid} (rama {live['branch']}). Termínala antes de abrir otra."
        with _locked(rdir) as data:        # the window is gone and nobody finished it: keep the branch, free the slot
            for s in data["sessions"]:
                if s["subplan"] == sid and s["status"] == "running":
                    s["status"] = "closed"
    repo, base = _repo(root, project)
    if repo is None:
        return False, "No encuentro un clon local del código del proyecto."
    req, number = _req(rdir), len(sessions(rdir, sid)) + 1
    name = f"{sid.lower()}" + (f"-{number}" if number > 1 else "")
    branch, worktree = f"session/{req.lower()}-{name}", base_dir() / project / req / name
    if worktree.exists():
        return False, f"{worktree} ya existe; ábrelo desde ahí o bórralo a mano."
    worktree.parent.mkdir(parents=True, exist_ok=True)
    _git(repo, "worktree", "prune")
    done = _git(repo, "worktree", "add", "-b", branch, str(worktree), base)
    if done.returncode != 0:
        return False, "No pude crear la copia de trabajo: " + (done.stderr or "").strip()[:200]
    base_sha = _git(worktree, "rev-parse", "HEAD").stdout.strip()
    spec = MODELS.get(model) or MODELS[DEFAULT_MODEL]
    text = prompt(root, project, rdir, sub, branch=branch, worktree=worktree, base=f"{base} ({base_sha[:10]})")
    prompt_file = worktree.parent / f"{name}.prompt.md"
    prompt_file.write_text(text, encoding="utf-8")
    tmux_name = terminal.name_for(project, req, f"{mode}-{name}")
    try:
        (launcher or launch_agent)(worktree, tmux_name, prompt_file, spec[0], spec[1])
    except Exception as exc:  # noqa: BLE001 - the worktree stays; the owner can open it by hand
        return False, f"Creé la copia en {worktree}, pero no pude arrancar el agente: {exc}"
    with _locked(rdir) as data:
        data["sessions"].append({"subplan": sid, "branch": branch, "worktree": str(worktree), "base": base,
                                 "base_sha": base_sha, "agent": f"claude {spec[2]}", "mode": mode, "tmux": tmux_name, "status": "running",
                                 "started_at": _now(), "repo": str(repo)})
    activity.record(rdir, "Sesión", f"Sesión con un agente abierta para {sid} (rama {branch})", kind="session", sp=sid)
    return True, f"Sesión abierta para {sid} en {worktree} (rama {branch})."


def info(s: dict) -> dict:
    """The session plus what git says now: commits ahead of its base and uncommitted files."""
    wt, out = Path(s["worktree"]), dict(s)
    out["exists"] = wt.exists()
    out["ahead"] = out["dirty"] = 0
    if wt.exists():
        ahead = _git(wt, "rev-list", "--count", f"{s['base_sha']}..HEAD").stdout.strip()
        out["ahead"] = int(ahead) if ahead.isdigit() else 0
        out["dirty"] = len(_git(wt, "status", "--porcelain").stdout.splitlines())
        out["head"] = _git(wt, "rev-parse", "HEAD").stdout.strip() or s.get("head", "")
    out["window"] = s["status"] == "running" and _alive(s.get("tmux"))
    return out


def finish(rdir: Path, sid: str, by: str = "owner") -> str:
    live = active(rdir, sid)
    if live is None:
        return f"{sid} no tiene una sesión en marcha."
    now = info(live)
    if not now["exists"]:
        return f"La copia de trabajo {live['worktree']} ya no existe; no hay nada que registrar."
    with _locked(rdir) as data:
        for s in data["sessions"]:
            if s["subplan"] == sid and s["status"] == "running":
                s.update(status="finished", finished_at=_now(), head=now["head"], commits=now["ahead"],
                         uncommitted=now["dirty"], finished_by=by)
    activity.record(rdir, "Sesión", f"Sesión de {sid} terminada: {now['ahead']} commit(s) en {live['branch']}",
                    kind="session", sp=sid)
    tail = f" Quedan {now['dirty']} archivo(s) sin commit en la copia." if now["dirty"] else ""
    return f"Sesión de {sid} terminada: {now['ahead']} commit(s) en la rama {live['branch']}.{tail}"
