"""Bitácora launcher: hand an approved plan from the HQ session to a fresh executor session.

Writes HANDOFF.md next to the plan, then opens a new terminal window in the project's repo running Claude Code
(self-paced /loop, or /goal) or Codex (/goal) with permission prompts disabled.
"""
from __future__ import annotations

import sys

import bt_platform as host
import bt_profiles
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
    from bt_review import feature_branch
    branch = feature_branch(rdir)
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
        "implementer per task (one at a time), reviewer x2 (spec + standards) after each phase, and the "
        "antagonist before EVERY commit (one review + at most one re-review; you triage: fix now or defer to "
        "PENDING.md with urgency/complexity).",
        "- Start every message to the user with `Aye`.",
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
        "Spanish (built / verified / rulings / needs your eyes / proposals / pending). Also write that report to "
        f"`{(rdir / 'REPORT.md').as_posix()}` (sections: Built, Verification evidence, Rulings, Needs your eyes, "
        "Proposals, Pending, Walkthrough) and set PLAN.md `status: done` — the web UI's Review tab shows it and "
        "offers the merge.",
    ]
    if agent == "claude" and mode == "loop":
        steps += ["", "## Run mode", "This session was started with a self-paced `/loop`. Do as much as is sensible "
                  "per iteration (a whole phase or more). End the loop yourself when done or blocked."]
    if mode == "marathon":
        steps += ["", "## Run mode", "A marathon supervisor runs this plan: each session is fresh and handles exactly "
                  "ONE task (given in its prompt). Do only that task, then report with `bitacora.py task done` or "
                  "`task fail`. Do not run the final review or write REPORT.md unless the prompt says so."]
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
    return host.open_terminal(repo, script, title)


def launch_env(project: str, profile: str | None = None) -> dict[str, str]:
    return {"BITACORA_PROJECT": project, "BITACORA_ROOT": str(ROOT), "PATH": os.environ.get("PATH", ""),
            **bt_profiles.env_of(profile)}


def marathon_script(project: str, rid: str, agent: str, model: str, repo_path: Path, launch_dir: Path,
                    profile: str | None = None) -> Path:
    argv = [sys.executable, str(SCRIPT), "--project", project, "run", rid, "--agent", agent]
    if profile:
        argv += ["--profile", profile]
    if agent == "claude" or model != "haiku":
        argv += ["--model", model]
    return host.write_script(launch_dir / f"{project}-{rid}-marathon", repo_path, argv,
                             launch_env(project, profile))


def launch(project: str, req: str, agent: str = "claude", mode: str = "loop", repo: str | None = None,
           force: bool = False, dry_run: bool = False, model: str = "haiku", profile: str | None = None) -> dict:
    if profile:
        bt_profiles.authorize(profile, project)  # before any prompt or handoff with project content exists
        agent = bt_profiles.require_launchable(profile)
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
    launch_dir = STATE / "launch"
    launch_dir.mkdir(parents=True, exist_ok=True)
    marathon = mode == "marathon"
    if marathon:
        prompt = ""  # no /loop prompt: the supervisor builds one prompt per task
        ps1 = marathon_script(project, rid, agent, model, repo_path, launch_dir, profile)
        title, what = f"{project} {rid} marathon", f"marathon supervisor ({agent}, {model})"
    else:
        prompt = initial_prompt(agent, mode, rid, handoff)
        (launch_dir / f"{project}-{rid}.prompt.txt").write_text(prompt, encoding="utf-8")
        ps1 = host.write_script(launch_dir / f"{project}-{rid}", repo_path, AGENTS[agent], launch_env(project, profile),
                                launch_dir / f"{project}-{rid}.prompt.txt")
        title, what = f"{project} {rid}", f"executor ({agent}, {mode})"
    cmd = "(dry run: not opened)"
    monitor = None
    if not dry_run:
        cmd = open_window(repo_path, ps1, title)
        if marathon and agent == "claude":  # companion session reachable from the phone through Remote Control
            from bt_monitor import open_monitor
            try:
                monitor = open_monitor(project, rid, profile=profile)["session"]
            except Exception as exc:  # the marathon must start even if the monitor can't
                monitor = f"monitor not opened: {exc}"
        with plan.open("a", encoding="utf-8") as fh:
            fh.write(f"- {dt.datetime.now():%Y-%m-%d %H:%M} launched {what} from HQ "
                     f"in `{repo_path.as_posix()}`\n")
        # "launched" guards against a second launch (e.g. approved on the web and in the terminal at once)
        set_front(plan, "status", "launched")
        from bt_vcs import commit
        commit(ROOT, f"{project}: launch {rid} ({agent}{', marathon' if marathon else ''})")
    return {"project": project, "req": rid, "agent": agent, "profile": profile, "mode": mode, "model": model, "workdir": workdir.as_posix(),
            "repos": {r: p.as_posix() for r, p in repos.items()}, "new_repos": new_repos,
            "handoff": handoff.as_posix(), "script": ps1.as_posix(), "prompt": prompt, "opened": cmd,
            "monitor": monitor}
