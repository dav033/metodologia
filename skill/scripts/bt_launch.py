"""Bitácora launcher: start the Scheduler run of an approved, frozen plan.

The only way to execute a plan: opens a terminal (or a detached tmux/systemd unit) in the project's repo running
`scheduler-run`. A plan without a frozen PLAN.json is refused; there is no other runner to fall back to.
"""
from __future__ import annotations

import sys

import bt_platform as host
import bt_profiles
from bt_core import *  # noqa: F403
from bt_core import _front


def open_window(repo: Path, script: Path, title: str) -> str:
    return host.open_terminal(repo, script, title)


def launch_env(project: str, profile: str | None = None) -> dict[str, str]:
    return {"BITACORA_PROJECT": project, "BITACORA_ROOT": str(ROOT), "PATH": os.environ.get("PATH", ""),
            **bt_profiles.env_of(profile)}


def scheduler_script(project: str, rid: str, repo_path: Path, launch_dir: Path) -> Path:
    argv = [sys.executable, str(SCRIPT), "--project", project, "scheduler-run", rid]
    return host.write_script(launch_dir / f"{project}-{rid}-scheduler", repo_path, argv, launch_env(project))


NOT_FROZEN_MESSAGE = (
    "PLAN_NOT_FROZEN: {req} has no frozen PLAN.json, and every plan runs through the Scheduler. "
    "Run `bitacora.py plan-json init {req}`, `plan-json check {req}` and `plan-json freeze {req}` "
    "(with the plan approved), then launch again."
)


def launch(project: str, req: str, agent: str | None = None, repo: str | None = None,
           force: bool = False, dry_run: bool = False, model: str | None = None, profile: str | None = None,
           background: bool = False, foreground: bool = False, planning_session: str | None = None) -> dict:
    """Start the Scheduler run of an approved plan. `background`: no window, a detached tmux session / systemd
    unit even on a desktop (the automatic hand-off uses it). Explicit routing overrides are refused;
    `force` never bypasses approval (it is only refused with `foreground`)."""
    if agent is not None or model is not None or profile is not None:
        raise SystemExit("SCHEDULER_ROUTING_REQUIRED: the Scheduler selects agent, model and account through M2")
    if foreground:
        if background or repo or force:
            raise SystemExit("Foreground launch cannot override approval, create a repo or detach the supervisor")
        from bt_orchestration_terminal import TerminalError
        from bt_orchestration_transition import launch as foreground_launch
        try:
            return foreground_launch(project, req, dry_run=dry_run, profile=profile,
                                     model=model, session=planning_session)
        except TerminalError as exc:
            raise SystemExit(str(exc)) from exc
    pdir = ROOT / project
    rdir = find_req(pdir, req)
    from bt_requirements_gate import PLANNING_FILES, require_ready
    require_ready(rdir, waive=PLANNING_FILES)      # approved scope of PLAN.md/SPEC.md is pinned by the plan gate
    plan = rdir / "PLAN.md"
    if not plan.exists():
        raise SystemExit(f"No PLAN.md for {req}. Plan first: bitacora.py req plan {req}")
    status = _front(plan, "status")
    if status != "approved":
        raise SystemExit(f"Scheduler launch requires PLAN.md status 'approved'; found '{status}'. Get the user's "
                         "approval and set `status: approved` first.")
    if not (rdir / "PLAN.json").is_file():
        raise SystemExit(NOT_FROZEN_MESSAGE.format(req=req_id(rdir)))
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
    import bt_plan_adapter  # the PLAN.json is validated and bound to its approved, frozen revision before anything runs
    import bt_scheduler_adapter
    bt_plan_adapter.freeze_on_launch(
        rdir, dry_run=dry_run, forced=False,
        compatibility_report=bt_scheduler_adapter.plan_compatibility_report(rdir),
    )
    if bt_scheduler_adapter.authority(rdir) == "legacy":
        raise SystemExit("AUTHORITY_CONFLICT: this requirement has a legacy RUN.json run")
    if bt_scheduler_adapter.authority(rdir) != "none":     # D-134: earlier stages already run; the whole plan joins
        if dry_run:
            return {"project": project, "req": req_id(rdir), "joined": "(dry run: the existing run would join)"}
        import bt_stages
        try:
            joined = bt_stages.start_or_join(project, rdir)
        except bt_stages.StageError as exc:
            raise SystemExit(str(exc)) from exc
        set_front(plan, "status", "launched")
        from bt_vcs import commit
        commit(ROOT, f"{project}: launch {req_id(rdir)} (joins the Scheduler run)")
        return {"project": project, "req": req_id(rdir), "workdir": (ws.workdir(ROOT, project) or Path(".")).as_posix(),
                "joined": joined, "repos": {r: p.as_posix() for r, p in repos.items()}, "handoff": None}
    workdir = ws.workdir(ROOT, project) or next(iter(repos.values()))
    repo_path = workdir
    rid = req_id(rdir)
    launch_dir = STATE / "launch"
    launch_dir.mkdir(parents=True, exist_ok=True)
    ps1 = scheduler_script(project, rid, repo_path, launch_dir)
    title = f"{project} {rid} scheduler"
    cmd = "(dry run: not opened)"
    if not dry_run:
        if background:
            os.environ["BITACORA_TERMINAL"] = "tmux"
        cmd = open_window(repo_path, ps1, title)
        with plan.open("a", encoding="utf-8") as fh:
            fh.write(f"- {dt.datetime.now():%Y-%m-%d %H:%M} launched Scheduler supervisor from HQ "
                     f"in `{repo_path.as_posix()}`\n")
        # "launched" guards against a second launch (e.g. approved on the web and in the terminal at once)
        set_front(plan, "status", "launched")
        try:
            import bt_planblock
            bt_planblock.refresh_plan_block(project, plan.parent)
        except Exception:
            pass
        from bt_vcs import commit
        commit(ROOT, f"{project}: launch {rid} (scheduler)")
    return {"project": project, "req": rid, "agent": agent, "profile": profile, "workdir": workdir.as_posix(),
            "repos": {r: p.as_posix() for r, p in repos.items()}, "handoff": None,
            "script": ps1.as_posix(), "opened": cmd}
