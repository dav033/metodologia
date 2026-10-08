"""Bitácora launcher: hand an approved plan from the HQ session to a fresh executor session.

Writes HANDOFF.md next to the plan, then opens a new terminal window in the project's repo running Claude Code
(self-paced /loop, or /goal) or Codex (/goal) with permission prompts disabled.
"""
from __future__ import annotations

import shutil
import subprocess

from bt_core import *  # noqa: F403
from bt_core import _first_heading, _front

# Executor sessions ALWAYS start with permission prompts disabled (user rule): claude --dangerously-skip-permissions,
# codex --yolo (alias of --dangerously-bypass-approvals-and-sandbox).
AGENTS = {
    "claude": ["claude", "--dangerously-skip-permissions"],
    "codex": ["codex", "--yolo"],
}


def write_handoff(project: str, rdir: Path, workdir: Path, repos: dict[str, Path], agent: str, mode: str,
                  new_repos: list[str]) -> Path:
    pdir = ROOT / project
    spec, plan = rdir / "SPEC.md", rdir / "PLAN.md"
    rid = req_id(rdir)
    branch = f"feat/{rdir.name.lower()}"[:60]
    repo_lines = [f"  - **{role}** → `{p.as_posix()}`" for role, p in repos.items()]
    steps = [
        f"You are the **executor** for {rid} — {_first_heading(spec)} (project `{project}`).",
        "A planning session (the HQ) already interviewed the user, wrote the spec and the plan, and the user "
        "**approved the plan**. Do not ask for approval again and do not re-run the interview.",
        "",
        "## Read first",
        f"- Spec: `{spec.as_posix()}`",
        f"- Plan: `{plan.as_posix()}` (its Progress log tells you what's already done if this is a resume)",
        f"- Project bitácora: `{pdir.as_posix()}` — SUMMARY.md, ARCHITECTURE.md, PENDING.md, DECISIONS.md",
        f"- Workspace (project `{project}`), working directory `{workdir.as_posix()}`. Repos by role:",
        *repo_lines,
        f"- Tools & infra: `{(pdir / 'TOOLS.md').as_posix()}` and shared `{(ROOT / 'TOOLS.md').as_posix()}` "
        "(servers, hosting CLIs, storage — see references/tools.md)",
    ]
    for role in new_repos:
        steps.append(f"- Repo **{role}** is new and empty: initialize it (git init, scaffold per the plan and the "
                     "default stack in references/engineering.md §8, tooling per §9) as the plan's first phase.")
    steps += [
        "",
        "## How to work",
        "- Follow the `metodologia` skill: references/execution.md §2–§5 and references/engineering.md "
        "(+ the matching stacks/*.md).",
        "- Permission prompts are disabled for this session. That makes you fast, not reckless: the stop-and-ask "
        "list in execution.md §2 still applies (destroying unrecoverable data, push/deploy/publish, external "
        "messages, payments, credentials). Everything else: decide, record a ruling, keep going.",
        "- Delegate per references/subagents.md: explorer / researcher / runner for context-heavy reads, an "
        "implementer per task (one at a time), reviewer x2 (spec + standards) after each phase.",
        f"- Git, per repo: create branch `{branch}` in **every** repo you touch (same name in all), commit there "
        "after each green phase, run each repo's own verification; never push without asking. The change ships as "
        "one unit: all those branches get merged together.",
        "- Each plan task says which repo (role) it belongs to; keep cross-repo contracts (API shapes, types) in "
        "sync within the same phase.",
        "- Keep PLAN.md's checkboxes and Progress log current after every phase: it's how a resumed or new "
        "session continues.",
        "- Log to the bitácora as you go (your session section is created by the SessionStart hook).",
        "",
        "## Done means",
        "Every task ticked, the plan's Verification passes with evidence, fresh-eyes review done, spec/plan "
        "statuses updated, bitácora updated (day log + walkthrough, PENDING, SUMMARY), and a final report in "
        "Spanish (built / verified / rulings / needs your eyes / proposals / pending).",
    ]
    if agent == "claude" and mode == "loop":
        steps += ["", "## Run mode", "This session was started with a self-paced `/loop`. Do as much as is sensible "
                  "per iteration (a whole phase or more). End the loop yourself when done or blocked."]
    out = rdir / "HANDOFF.md"
    out.write_text("# Handoff — executor\n\n" + "\n".join(steps) + "\n", encoding="utf-8")
    return out


def initial_prompt(agent: str, mode: str, rid: str, handoff: Path) -> str:
    h = handoff.as_posix()
    if agent == "codex" or mode == "goal":
        return (f"/goal Complete {rid} by following {h} without stopping until every task in the plan is ticked, "
                f"the plan's Verification passes with evidence, and the bitácora and final report are done "
                f"- or a stop-and-ask item blocks progress.")
    return (f"/loop Execute the approved plan for {rid}: read {h} and follow it. Each iteration: next phase, "
            f"verify, commit, update PLAN.md. Stop the loop when everything is done and reported, or when blocked.")


def open_window(repo: Path, script: Path, title: str) -> str:
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    if not pwsh:
        raise SystemExit(f"No PowerShell found. Run manually:\n  cd {repo}\n  {script}")
    if shutil.which("wt"):
        cmd = ["wt", "-w", "new", "--title", title, "-d", str(repo), pwsh, "-NoExit", "-File", str(script)]
    else:
        cmd = ["cmd", "/c", "start", title, pwsh, "-NoExit", "-File", str(script)]
    subprocess.Popen(cmd, cwd=str(repo), creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
    return " ".join(cmd)


def launch(project: str, req: str, agent: str = "claude", mode: str = "loop", repo: str | None = None,
           force: bool = False, dry_run: bool = False) -> dict:
    pdir = ROOT / project
    rdir = find_req(pdir, req)
    plan = rdir / "PLAN.md"
    if not plan.exists():
        raise SystemExit(f"No PLAN.md for {req}. Plan first: bitacora.py req plan {req}")
    status = _front(plan, "status")
    if status != "approved" and not force:
        raise SystemExit(f"PLAN.md status is '{status}', not 'approved'. Get the user's approval and set "
                         f"`status: approved` first (or pass --force if the user explicitly said to launch).")
    if repo and not dry_run:  # a new or extra repo for this workspace (remembered)
        Path(repo).mkdir(parents=True, exist_ok=True)
        register_repo(project, Path(repo))
    if not dry_run:
        ws.clone_missing(ROOT, project)  # this machine may not have every repo of the workspace yet
    repos = ws.repos(ROOT, project)
    if repo and dry_run:
        repos.setdefault(Path(repo).name, Path(repo))
    if not repos:
        raise SystemExit(f"No repos registered for '{project}'. Pass --repo <path> or run "
                         f"`bitacora.py --project {project} workspace add <role> <path>`.")
    new_repos = [role for role, p in repos.items() if not p.exists() or not any(p.iterdir())]
    workdir = ws.workdir(ROOT, project) or next(iter(repos.values()))
    repo_path = workdir
    rid = req_id(rdir)
    handoff = write_handoff(project, rdir, workdir, repos, agent, mode, new_repos)
    prompt = initial_prompt(agent, mode, rid, handoff)
    launch_dir = STATE / "launch"
    launch_dir.mkdir(parents=True, exist_ok=True)
    (launch_dir / f"{project}-{rid}.prompt.txt").write_text(prompt, encoding="utf-8")
    exe = " ".join(AGENTS[agent])
    ps1 = launch_dir / f"{project}-{rid}.ps1"
    ps1.write_text(
        f"$Host.UI.RawUI.WindowTitle = '{project} {rid} ({agent})'\n"
        f"$env:BITACORA_PROJECT = '{project}'\n"
        f"Set-Location -LiteralPath '{repo_path}'\n"
        f"$prompt = Get-Content -Raw -LiteralPath '{launch_dir / f'{project}-{rid}.prompt.txt'}'\n"
        f"{exe} $prompt\n", encoding="utf-8")
    cmd = "(dry run: not opened)"
    if not dry_run:
        cmd = open_window(repo_path, ps1, f"{project} {rid}")
        with plan.open("a", encoding="utf-8") as fh:
            fh.write(f"- {dt.datetime.now():%Y-%m-%d %H:%M} launched executor ({agent}, {mode}) from HQ "
                     f"in `{repo_path.as_posix()}`\n")
        # "launched" guards against a second launch (e.g. approved on the web and in the terminal at once)
        set_front(plan, "status", "launched")
        from bt_vcs import commit
        commit(ROOT, f"{project}: launch {rid} ({agent})")
    return {"project": project, "req": rid, "agent": agent, "mode": mode, "workdir": workdir.as_posix(),
            "repos": {r: p.as_posix() for r, p in repos.items()}, "new_repos": new_repos,
            "handoff": handoff.as_posix(), "script": ps1.as_posix(), "prompt": prompt, "opened": cmd}
