"""Remote monitor for a marathon: an interactive Claude session with Remote Control enabled.

Marathon task sessions are headless (`claude -p`), and Remote Control only attaches to interactive sessions. So the
marathon gets a companion: a cheap interactive session (Haiku) named "<project> <REQ> maratón", opened with
`claude --remote-control <name>`, whose only job is to answer the user — from claude.ai/code or the Claude app — about
the run (RUN.json, session logs, git, PENDING) and to control it (pause / resume / stop / retry / notes). It is
independent from the supervisor: closing it never stops the marathon, and it costs nothing while nobody asks.
"""
from __future__ import annotations

import shutil
import subprocess

from bt_core import *  # noqa: F403

MONITOR_BRIEF = """# Marathon monitor — {project} {rid}

You are the **remote monitor** of a marathon run. The user talks to you from claude.ai/code or the Claude mobile app
through Remote Control. Start every reply with `Aye`. Speak Spanish, be brief (phone screen), lead with the answer.

You do NOT implement anything and you do NOT edit project code. A supervisor in another window runs the plan, one
fresh headless session per task. Your job is to report and, when asked, steer it.

## Where things are
- Run state: `{run_json}` — status, current task, heartbeat, tasks (status/attempts/last_error/notes), log.
- Plan / spec / report: `{rdir}` (PLAN.md, SPEC.md, REPORT.md when finished).
- Session transcripts (one per task attempt): `{logs_dir}` (session-NNNN.log).
- Project bitácora: `{pdir}` — PENDING.md (blocked tasks land there), today's day log, SUMMARY.md.
- Repos: {repos}. Feature branch: `{branch}` (git log/diff there shows what was done).

## What the user may ask, and how to answer
- "¿Cómo va?" → status, progress x/y, current task + how long it has been running, last 3 log lines, anything blocked
  or waiting (usage limit → until when). Check that the heartbeat is fresh (stale = supervisor window closed/crashed).
- "¿Qué hizo en T3?" / "muéstrame el último commit" → read the task's log entries, its session log tail, git log/diff.
- "¿Por qué se bloqueó?" → the task's last_error, notes, the PENDING item, and your own short diagnosis.
- Control (run them, then confirm what changed):
  - pause / resume / stop: `python "{script}" --project {project} run-control {rid} pause|resume|stop`
  - note for the next attempt: `python "{script}" --project {project} task note {rid} T3 --text "..."`
  - retry blocked tasks: stop, then restart the supervisor with `--resume --retry-blocked` in a new window:
    `python "{script}" --project {project} launch {rid} --mode marathon --force` (only if the user asks).
- Anything destructive (deleting branches, force-push, deploy) → refuse; that's not your role.

When idle, do nothing. Don't poll. Answer only when asked.
"""


def write_brief(project: str, rdir: Path) -> Path:
    from bt_review import feature_branch
    rid = req_id(rdir)
    pdir = ROOT / project
    repos = ", ".join(f"{r} → `{p.as_posix()}`" for r, p in ws.repos(ROOT, project, discover=False).items()) or "—"
    brief = MONITOR_BRIEF.format(project=project, rid=rid, run_json=(rdir / "RUN.json").as_posix(),
                                 rdir=rdir.as_posix(), logs_dir=(STATE / "runs" / f"{project}-{rid}").as_posix(),
                                 pdir=pdir.as_posix(), repos=repos, branch=feature_branch(rdir),
                                 script=SCRIPT.as_posix())
    out = rdir / "MONITOR.md"
    out.write_text(brief, encoding="utf-8")
    return out


def session_name(project: str, rid: str) -> str:
    return f"{project} {rid} maratón"


def monitor_script(project: str, rdir: Path, model: str = "haiku") -> Path:
    """.ps1 that opens the interactive Remote Control monitor session."""
    rid = req_id(rdir)
    brief = write_brief(project, rdir)
    launch_dir = STATE / "launch"
    launch_dir.mkdir(parents=True, exist_ok=True)
    prompt = (f"Lee {brief.as_posix()} y sigue esas instrucciones: eres el monitor remoto del maratón {rid} de "
              f"{project}. Confirma en una línea que estás listo y espera preguntas.")
    ps1 = launch_dir / f"{project}-{rid}-monitor.ps1"
    ps1.write_text(
        f"$Host.UI.RawUI.WindowTitle = '{session_name(project, rid)} (monitor)'\n"
        f"$env:BITACORA_PROJECT = '{project}'\n"
        f"Set-Location -LiteralPath '{(ROOT / project).as_posix()}'\n"
        f"claude --remote-control '{session_name(project, rid)}' --model {model} --dangerously-skip-permissions "
        f"'{prompt.replace(chr(39), chr(39) * 2)}'\n",
        encoding="utf-8")
    return ps1


def open_monitor(project: str, req: str, model: str = "haiku", dry_run: bool = False) -> dict:
    rdir = find_req(ROOT / project, req)
    ps1 = monitor_script(project, rdir, model)
    title = session_name(project, req_id(rdir))
    cmd = "(dry run: not opened)"
    if not dry_run:
        pwsh = shutil.which("pwsh") or shutil.which("powershell")
        if shutil.which("wt"):
            args = ["wt", "-w", "new", "--title", title, pwsh, "-NoExit", "-File", str(ps1)]
        else:
            args = ["cmd", "/c", "start", title, pwsh, "-NoExit", "-File", str(ps1)]
        subprocess.Popen(args, creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
        cmd = " ".join(args)
    return {"session": title, "script": ps1.as_posix(), "brief": (rdir / "MONITOR.md").as_posix(), "opened": cmd,
            "connect": "claude.ai/code o la app de Claude → sesiones → '" + title + "'"}
