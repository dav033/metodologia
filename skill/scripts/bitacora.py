#!/usr/bin/env python3
"""Bitácora: deterministic half of the `metodologia` skill.

Creates and locates the per-project documentation tree, hands out IDs, keeps INDEX.md
in sync, and implements the Claude Code hooks (SessionStart / Stop / SessionEnd).
The agent writes the content; this script never invents prose.

Layout (root = $BITACORA_ROOT or ~/bitacora):
  <root>/<project>/
    SUMMARY.md ARCHITECTURE.md DECISIONS.md PENDING.md INDEX.md
    requirements/REQ-001-<slug>/SPEC.md, PLAN.md
    2026-10/MONTH.md
    2026-10/W2/WEEK.md
    2026-10/W2/2026-10-08.md          (one file per day, one section per session)

Weeks are week-of-month, Monday-based: W1 is the (possibly partial) week containing day 1.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from bt_core import *  # noqa: F403
from bt_core import _first_heading, _load_bindings, _save_bindings
from bt_views import *  # noqa: F403
from bt_hooks import hook_end, hook_start, hook_stop
import bt_cli_accounts
import bt_cli_diagram
import bt_cli_docs
import bt_cli_launch
import bt_cli_scheduler_recovery
import bt_cli_scheduler_run
import bt_cli_delegate
import bt_cli_learn
import bt_cli_review
import bt_cli_requirements_gate
import bt_cli_plan
import bt_cli_planner

# ---------------------------------------------------------------- CLI

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", help="override project name")
    ap.add_argument("--cwd", default=os.getcwd())
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("where", help="ensure today's files exist and print all paths")
    sub.add_parser("init", help="create the project tree")
    p_id = sub.add_parser("id", help="next free ID")
    p_id.add_argument("kind", choices=["D", "P", "REQ", "d", "p", "req"])
    p_req = sub.add_parser("req", help="requirements")
    p_req.add_argument("action", choices=["new", "plan"])
    p_req.add_argument("arg", help='title for "new", REQ-NNN for "plan"')
    sub.add_parser("index", help="regenerate INDEX.md")
    sub.add_parser("rollups", help="list past week/month summaries still in draft")
    p_bind = sub.add_parser("bind", help="bind a session to a project (for non-repo folders)")
    p_bind.add_argument("session_id")
    p_bind.add_argument("project")
    bt_cli_launch.register(sub)
    p_run = sub.add_parser("run", help="marathon: supervise a plan, a fresh headless session per task or per milestone (days)")
    p_run.add_argument("req", help="REQ-NNN")
    p_run.add_argument("--agent", choices=["claude", "codex", "antigravity"])
    p_run.add_argument("--pool", help="accounts the router may use: auto (every account allowed for the project), "
                                      "profile ids a,b, or none (pin to --agent/--profile)")
    p_run.add_argument("--audit", dest="audit", action="store_true", default=None,
                       help="independent audit session after each milestone (default with a pool)")
    p_run.add_argument("--no-audit", dest="audit", action="store_false")
    p_run.add_argument("--workers", type=int, help="sessions at once, only across different repos (default 1, max 2)")
    p_run.add_argument("--isolation", choices=["off", "worktree"], help="isolate same-repo sessions in worktrees")
    p_run.add_argument("--profile", help="account profile (bitacora.py profiles list); sets the agent")
    p_run.add_argument("--model", help="tier 0 of the escalation ladder (default haiku)")
    p_run.add_argument("--no-ultracode", action="store_true")
    p_run.add_argument("--max-attempts", type=int, help="per task (default 4: haiku, sonnet, opus, opus)")
    p_run.add_argument("--session-timeout", type=int, help="minutes per session (default 60)")
    p_run.add_argument("--resume", action="store_true", help="continue from RUN.json (autostart uses this)")
    p_run.add_argument("--retry-blocked", action="store_true", help="with --resume: give blocked tasks a fresh start")
    p_run.add_argument("--agent-cmd", help="tests: command template with {prompt_file} {workdir} {task} {req} {project} "
                                           "{model_args}")
    p_run.add_argument("--once", action="store_true", help="run a single session and exit")
    p_run.add_argument("--no-autostart", action="store_true", help="do not install the per-user login resume entry")
    p_run.add_argument("--foreground", action="store_true", help="same-terminal bounded milestone coordinator (runtime capability preflight)")
    p_task = sub.add_parser("task", help="marathon agent report: done / fail / note / escalate on a plan task")
    p_task.add_argument("action", choices=["done", "fail", "note", "escalate"])
    p_task.add_argument("req", help="REQ-NNN")
    p_task.add_argument("task", help="T3")
    p_task.add_argument("--evidence", default="", help="done: what proves it")
    p_task.add_argument("--findings", type=int, help="done (audit): number of defects found in the milestone, 0 when clean")
    p_task.add_argument("--severity", help="done (audit): high=N,med=N,low=N; must add up to --findings")
    p_task.add_argument("--reason", default="", help="fail / escalate: why")
    p_task.add_argument("--to", choices=["standard", "top", "sonnet", "opus"],
                        help="escalate: top (architecture; alias opus) or standard (stuck; alias sonnet)")
    p_task.add_argument("--text", default="", help="note: advice for the next attempt")
    p_task.add_argument("--blocked", action="store_true", help="fail: needs a human, do not retry")
    p_rc = sub.add_parser("run-control", help="pause / resume / stop a running marathon")
    p_rc.add_argument("req", help="REQ-NNN")
    p_rc.add_argument("action", choices=["pause", "resume", "stop"])
    p_watch = sub.add_parser("watch", help="wait for the next news of a run (settled session, block, wait, end), "
                                           "print it and exit; run it in the background and re-arm it")
    p_watch.add_argument("req", help="REQ-NNN")
    p_watch.add_argument("--timeout", type=float, default=360, help="minutes to wait for news (default 360)")
    p_watch.add_argument("--poll", type=float, default=15, help="seconds between checks")
    p_mon = sub.add_parser("monitor", help="open the marathon's Remote Control monitor session (watch it from the phone)")
    p_mon.add_argument("req", help="REQ-NNN")
    p_mon.add_argument("--model", default="haiku")
    p_mon.add_argument("--dry-run", action="store_true")
    p_round = sub.add_parser("round", help="question rounds shared with the web UI")
    p_round.add_argument("action", choices=["new", "wait", "answer", "show"])
    p_round.add_argument("req", help="REQ-NNN")
    p_round.add_argument("--file", help="JSON file: the round (new) or the answers (answer)")
    p_round.add_argument("--timeout", type=int, default=3600)
    p_plan = sub.add_parser("plan", help="plan review shared with the web UI")
    p_plan.add_argument("action", choices=["review", "wait", "approve", "changes"])
    p_plan.add_argument("req", help="REQ-NNN")
    p_plan.add_argument("--comments", default="")
    p_plan.add_argument("--timeout", type=int, default=3600)
    p_ws = sub.add_parser("workspace", help="the project's repos (a project is a workspace of repos)")
    p_ws.add_argument("action", choices=["show", "add", "remove", "root", "clone"])
    p_ws.add_argument("role", nargs="?", help="add/remove: role name (frontend, backend…); root: the folder")
    p_ws.add_argument("path", nargs="?", help="add: repo path")
    p_prof = sub.add_parser("profiles", help="account profiles: list, doctor, or check one against a project")
    p_prof.add_argument("action", choices=["list", "doctor", "check", "add", "gate", "wrapper"])
    p_prof.add_argument("profile", nargs="?", help="check/add: profile id")
    p_prof.add_argument("--provider", choices=["claude", "codex", "antigravity"], help="add: provider")
    p_prof.add_argument("--env", action="append", default=[], metavar="KEY=VALUE",
                        help="add: environment selecting the account, e.g. CLAUDE_CONFIG_DIR=~/.claude-work")
    p_prof.add_argument("--work-only", action="store_true", help="add: only runs projects with work=true")
    p_prof.add_argument("--bin", help="add: executable name if not the provider default")
    p_prof.add_argument("--relay", action="store_true", help="wrapper: run the agent under relay_run.py (quota relay parent launcher)")
    p_prof.add_argument("--dir", help="wrapper: directory for the launcher (default ~/.local/bin)")
    p_work = sub.add_parser("work", help="show or set the project's work flag (gates work-only profiles)")
    p_work.add_argument("value", nargs="?", choices=["true", "false"])
    bt_cli_requirements_gate.add_parser(sub)
    bt_cli_plan.add_parser(sub)
    bt_cli_planner.register(sub)
    bt_cli_delegate.register(sub)
    bt_cli_review.register(sub)
    bt_cli_accounts.register(sub)
    bt_cli_diagram.register(sub)
    bt_cli_docs.register(sub)
    bt_cli_scheduler_recovery.register(sub)
    bt_cli_scheduler_run.register(sub)
    bt_cli_learn.register(sub)
    p_ho = sub.add_parser("handoff", help="validate a plan, approve it when safe and start it in the background")
    p_ho.add_argument("req", help="REQ-NNN")
    p_ho.add_argument("--dry-run", action="store_true", help="only say what would happen and why")
    p_ho.add_argument("--pool", help="accounts the router may use (default: auto)")
    p_ho.add_argument("--profile", help="preferred account among equals")
    p_ho.add_argument("--model", help="tier 0 model of the preferred provider")
    p_ho.add_argument("--foreground", action="store_true", help="approved same-terminal transition via the relay parent")
    p_ho.add_argument("--planning-session", help="provider session id for verified end-of-turn handoff")
    sub.add_parser("context", help="one screen for an agent: who is available, routing, delegation, learnings, docs")
    sub.add_parser("audit", help="prepare a read-only inventory for a workspace architecture audit")
    p_serve = sub.add_parser("serve", help="run the local web server in the foreground")
    p_serve.add_argument("--port", type=int)
    p_graph = sub.add_parser("graph", help="open the trace graph of the project in the browser (starts the server)")
    p_graph.add_argument("--no-open", action="store_true")
    p_web = sub.add_parser("web", help="start the web server if needed, open the browser, print the URL")
    p_web.add_argument("--no-open", action="store_true")
    sub.add_parser("secrets", help="install the gitleaks pre-commit hook in every workspace repo on this machine")
    p_pd = sub.add_parser("pending", help="sort PENDING.md by urgency then complexity (all projects with --all)")
    p_pd.add_argument("--all", action="store_true")
    p_tr = sub.add_parser("trace", help="trace graph from IDs (REQ/US/R/T/D/P), commits and files; lint drift")
    p_tr.add_argument("--node", help="neighborhood of an ID, e.g. REQ-001 or REQ-001/T3")
    p_tr.add_argument("--file", help="impact: which REQ/D/P touched files matching this text")
    p_tr.add_argument("--bundle", help="context bundle for an ID (for handoffs / subagent briefs)")
    p_tr.add_argument("--depth", type=int, default=2)
    p_tr.add_argument("--json", action="store_true", help="print the whole graph as JSON")
    p_tr.add_argument("--no-commits", action="store_true")
    p_commit = sub.add_parser("commit", help="commit the bitácora (local git)")
    p_commit.add_argument("message")
    p_hook = sub.add_parser("hook", help="Claude Code hook entry point (reads JSON on stdin)")
    p_hook.add_argument("event", choices=["start", "stop", "end", "relay"])
    p_hook.add_argument("--harness", choices=["claude", "codex", "antigravity"], default="claude")
    p_relay = sub.add_parser("relay", help="quota relay: hand an interactive session over to another account")
    p_relay.add_argument("action", choices=["handoff", "launch", "cancel", "install", "status", "wrap-status"])
    p_relay.add_argument("--to", help="handoff/launch: successor profile (default: the router chooses)")
    p_relay.add_argument("--session", help="handoff/launch: session id of the agent being relayed")
    p_relay.add_argument("--handoff", help="launch: handoff file")
    p_relay.add_argument("--mux", choices=["zellij", "tmux", "kitty"], help="launch: multiplexer of the pane")
    p_relay.add_argument("--target", help="launch: pane id in that multiplexer")
    p_relay.add_argument("--pid", type=int, help="launch: verified agent pid")
    p_relay.add_argument("--start", type=int, help="launch: start time of that pid (/proc ticks)")
    p_relay.add_argument("--force", action="store_true", help="handoff: write the handoff even if relay.enabled is false (never auto-closes)")
    p_relay.add_argument("--mux-env", help="launch: JSON of the multiplexer variables of the client")
    p_relay.add_argument("--wrapper-pid", type=int, help="launch: pid of the relay_run.py parent of the client")
    p_relay.add_argument("--wrapper-start", type=int, help="launch: start time of that wrapper (/proc ticks)")
    p_relay.add_argument("--apply", action="store_true", help="wrap-status: regenerate the wrappers (default: only report)")
    p_relay.add_argument("--dir", help="wrap-status: wrapper directory (default ~/.local/bin)")
    p_relay.add_argument("--exit-current", choices=["0", "1"], default="1")
    p_relay.add_argument("--settings", help="install: settings.json to merge the hooks into (default: print only)")
    p_relay.add_argument("--dry-run", action="store_true", help="install: print, change nothing")
    a = ap.parse_args()

    if a.cmd == "relay":
        import bt_relay_cli
        return bt_relay_cli.dispatch(a)
    if a.cmd == "hook":
        if a.event == "relay":
            import bt_relay
            return bt_relay.hook_main(sys.stdin.read())
        try:
            if a.event == "end":
                hook_end()
            else:
                {"start": hook_start, "stop": hook_stop}[a.event](a.harness)
        except Exception as exc:  # a broken hook must never break the session
            print(f"[bitácora] hook error: {exc}", file=sys.stderr)
        return
    if a.cmd == "serve":
        from bt_server import DEFAULT_PORT, serve
        return serve(a.port or DEFAULT_PORT)
    if a.cmd in ("web", "graph"):
        import webbrowser
        from bt_server import ensure_server
        target = ensure_server()
        project = a.project and slugify(a.project, 60) or resolve_project(Path(a.cwd))
        if a.cmd == "graph" and not project:
            sys.exit("Which project? bitacora.py --project <name> graph")
        if project:
            target += f"/p/{project}" + ("/graph" if a.cmd == "graph" else "")
        if not a.no_open:
            webbrowser.open(target)
        return print(target)
    if a.cmd == "commit":
        from bt_secrets import alert
        from bt_vcs import commit
        if commit(ROOT, a.message):
            return print("committed")
        return print(f"BLOCKED — possible secret:\n{alert(ROOT)}" if alert(ROOT) else "nothing to commit")
    if a.cmd == "pending" and a.all:
        import bt_pending
        for d in sorted(p for p in ROOT.iterdir() if (p / "PENDING.md").exists()):
            print(f"{d.name}: {'sorted' if bt_pending.sort_file(d) else 'already sorted'}")
            write_index(d)
        write_global_index()
        return
    if a.cmd == "secrets":
        from bt_secrets import find_gitleaks, install_hook
        if not find_gitleaks():
            from bt_platform import gitleaks_install_hint
            print(f"gitleaks not found — {gitleaks_install_hint()}")
        for d in sorted(p for p in ROOT.iterdir() if (p / "project.json").exists()):
            for role, path in ws.repos(ROOT, d.name).items():
                if path.exists() and path.resolve() != ROOT.resolve().parent:
                    print(f"{d.name}/{role}: {install_hook(path)}")
        return

    if a.cmd == "delegate":
        bt_cli_delegate.dispatch(a)
        return

    if a.cmd == "review":
        project = slugify(a.project, 60) if a.project else (
            slugify(os.environ["BITACORA_PROJECT"], 60) if os.environ.get("BITACORA_PROJECT") else None)
        if not project:
            import bt_audit
            project = bt_audit.project_for_cwd(ROOT, Path(a.cwd))
        bt_cli_review.dispatch(a, project)
        return

    if a.cmd == "recovery":
        sys.exit(bt_cli_scheduler_recovery.dispatch(a))

    if a.cmd == "glossary":
        project = slugify(a.project, 60) if a.project else (
            slugify(os.environ["BITACORA_PROJECT"], 60) if os.environ.get("BITACORA_PROJECT") else None)
        if not project:
            import bt_audit
            project = bt_audit.project_for_cwd(ROOT, Path(a.cwd))
        sys.exit(bt_cli_docs.dispatch(a, project, ROOT))

    if a.cmd == "diagram":
        project = slugify(a.project, 60) if a.project else (
            slugify(os.environ["BITACORA_PROJECT"], 60) if os.environ.get("BITACORA_PROJECT") else None)
        if not project:
            import bt_audit
            project = bt_audit.project_for_cwd(ROOT, Path(a.cwd))
        sys.exit(bt_cli_diagram.dispatch(a, project, ROOT))

    if bt_cli_accounts.dispatch_machine(a):
        return

    if a.cmd in ("agents", "context", "learn"):  # the project is optional: owner-level answers work anywhere
        project = slugify(a.project, 60) if a.project else (
            slugify(os.environ["BITACORA_PROJECT"], 60) if os.environ.get("BITACORA_PROJECT") else None)
        if not project:
            import bt_audit
            project = bt_audit.project_for_cwd(ROOT, Path(a.cwd))
        if a.cmd == "context":
            import bt_context
            print(bt_context.text(project))
            return
        if a.cmd == "agents":
            bt_cli_accounts.dispatch_agents(a, project)
            return
        bt_cli_learn.dispatch(a, project)
        return

    if a.cmd == "profiles" and a.action in ("list", "doctor", "add", "gate", "wrapper"):  # machine-level
        import bt_profiles
        if a.action == "gate":  # exit status 0 = allowed; used by generated launchers before the CLI starts
            ok, why = bt_profiles.gate_cwd(a.profile or "", a.cwd)
            if not ok:
                print(why, file=sys.stderr)
            sys.exit(0 if ok else 1)
        if a.action == "wrapper":
            if not a.profile:
                sys.exit("profiles wrapper needs a profile id")
            target = Path(a.dir).expanduser() if a.dir else Path.home() / ".local" / "bin"
            print(bt_profiles.write_wrapper(a.profile, target, a.relay))
            return
        if a.action == "add":
            if not (a.profile and a.provider):
                sys.exit("profiles add needs a profile id and --provider")
            env = dict(item.split("=", 1) for item in a.env if "=" in item)
            print(f"{bt_profiles.add(a.profile, a.provider, env, a.work_only, a.bin)}: {a.profile}")
            return
        print(json.dumps(bt_profiles.doctor() if a.action == "doctor" else bt_profiles.load(), indent=1,
                         ensure_ascii=False))
        return

    if a.cmd == "audit":
        import bt_audit
        project = slugify(a.project, 60) if a.project else (
            slugify(os.environ["BITACORA_PROJECT"], 60) if os.environ.get("BITACORA_PROJECT") else
            bt_audit.project_for_cwd(ROOT, Path(a.cwd))
        )
        if not project:
            sys.exit("No project could be resolved without changing workspace state; pass --project <name>.")
        print(json.dumps(bt_audit.inventory(ROOT, project), indent=1, ensure_ascii=False))
        return

    cwd = Path(a.cwd)
    if a.cmd == "bind":
        project = slugify(a.project, 60)
        b = _load_bindings()
        b[a.session_id] = project
        _save_bindings(b)
        print(build_context(project, a.session_id, cwd, "bind"))
        return

    project = resolve_project(cwd, None, a.project)
    if not project:
        sys.exit("No project: pass --project <name>, run inside a git repo, or create a .bitacora marker file.")
    pdir, created = ensure_project(project)

    if a.cmd in ("where", "init"):
        p = ensure_day(pdir, today())
        info = {"project": project, "project_dir": pdir.as_posix(), "created": created,
                **{k: v.as_posix() for k, v in p.items() if not k.endswith("_dir")},
                **{f[:-3].lower(): (pdir / f).as_posix() for f in CENTRAL},
                "week_of_month": week_of_month(today())}
        print(json.dumps(info, indent=1, ensure_ascii=False))
    elif a.cmd == "id":
        print(next_id(pdir, a.kind))
    elif a.cmd == "req":
        if a.action == "new":
            rid = next_id(pdir, "REQ")
            d = pdir / "requirements" / f"{rid}-{slugify(a.arg)}"
            d.mkdir(parents=True)
            spec = d / "SPEC.md"
            spec.write_text(render("SPEC.md", id=rid, title=a.arg, date=today().isoformat(), project=project),
                            encoding="utf-8")
            write_index(pdir)
            print(spec.as_posix())
        else:
            matches = list((pdir / "requirements").glob(f"{a.arg.upper()}-*"))
            if not matches:
                sys.exit(f"{a.arg} not found")
            plan = matches[0] / "PLAN.md"
            if not plan.exists():
                plan.write_text(render("PLAN.md", id=a.arg.upper(), title=_first_heading(matches[0] / "SPEC.md"),
                                       date=today().isoformat()), encoding="utf-8")
            write_index(pdir)
            print(plan.as_posix())
    elif a.cmd == "profiles":  # add a profile, or check one against the bound project
        import bt_profiles
        if not a.profile:
            sys.exit("profiles check needs a profile id")
        bt_profiles.authorize(a.profile, project)
        print(f"OK: {a.profile} may run {project}")
    elif a.cmd == "work":
        import bt_profiles
        if a.value:
            print(f"{bt_profiles.set_work(project, a.value == 'true')}: work={a.value}")
        else:
            print(f"{project}: work={str(bt_profiles.is_work_project(project)).lower()}")
    elif a.cmd == "requirements-gate":
        sys.exit(bt_cli_requirements_gate.dispatch(a, ROOT, project))
    elif a.cmd == "plan-json":
        sys.exit(bt_cli_plan.dispatch(a, ROOT, project))
    elif a.cmd == "planner":
        sys.exit(bt_cli_planner.dispatch(a, project, cwd, ROOT))
    elif a.cmd == "launch":
        bt_cli_launch.dispatch(a, project)
    elif a.cmd == "run":
        from bt_run import supervise
        sys.exit(supervise(project, a.req, agent=a.agent, model=a.model, ultracode=False if a.no_ultracode else None,
                           max_attempts=a.max_attempts, session_timeout=a.session_timeout,
                           retry_blocked=a.retry_blocked, agent_cmd=a.agent_cmd, once=a.once,
                           no_autostart=a.no_autostart, profile=a.profile,
                           workers=a.workers, pool=a.pool, audit=a.audit, isolation=a.isolation,
                           foreground=a.foreground))
    elif a.cmd == "scheduler-run":
        sys.exit(bt_cli_scheduler_run.dispatch(a, project, pdir))
    elif a.cmd == "handoff":
        import bt_handoff
        extra = {"foreground": True, "planning_session": a.planning_session} if a.foreground else {}
        result = bt_handoff.handoff(project, a.req, a.dry_run, a.pool, a.model, a.profile, **extra)
        print(json.dumps(result, indent=1, ensure_ascii=False))
        sys.exit(0 if result["decision"] in ("launched", "would_launch", "already_running", "done", "prepared", "would_prepare") else
                 3 if result["decision"] == "needs_approval" else 2)
    elif a.cmd == "watch":
        import bt_watch
        print(bt_watch.watch(project, a.req, a.timeout, a.poll))
    elif a.cmd == "monitor":
        from bt_monitor import open_monitor
        print(json.dumps(open_monitor(project, a.req, a.model, a.dry_run), indent=1, ensure_ascii=False))
    elif a.cmd in ("task", "run-control"):
        rdir = find_req(pdir, a.req)
        if a.cmd == "run-control":
            import bt_cli_run_control
            print(bt_cli_run_control.dispatch(rdir, a.action))
        else:
            import bt_runtask as rt
            print({"done": lambda: rt.task_done(rdir, a.task, a.evidence, a.findings, a.severity),
                   "fail": lambda: rt.task_fail(rdir, a.task, a.reason, a.blocked),
                   "note": lambda: rt.task_note(rdir, a.task, a.text),
                   "escalate": lambda: rt.task_escalate(rdir, a.task, a.to or "", a.reason)}[a.action]())
    elif a.cmd == "workspace":
        if a.action == "add":
            if not (a.role and a.path):
                sys.exit("usage: workspace add <role> <path>")
            register_repo(project, Path(a.path), a.role)
        elif a.action == "remove":
            ws.remove_repo(ROOT, project, a.role or "")
        elif a.action == "root":
            ws.set_root(ROOT, project, Path(a.role) if a.role else None)
        elif a.action == "clone":
            print("cloned:", ", ".join(ws.clone_missing(ROOT, project)) or "nothing missing")
        local = {r: p.as_posix() + ("" if p.exists() else "  (not cloned here)") for r, p in ws.repos(ROOT, project).items()}
        print(json.dumps({"project": project, **ws.meta(ROOT, project), "local_paths": local,
                          "workdir": (ws.workdir(ROOT, project) or Path(".")).as_posix()}, indent=1,
                         ensure_ascii=False))
    elif a.cmd == "trace":
        import bt_trace as tr
        g = tr.build(project, with_commits=not a.no_commits)
        if a.json:
            return print(json.dumps({**g.to_dict(), "lint": tr.lint(g)}, indent=1, ensure_ascii=False))
        if a.bundle:
            return print(tr.bundle(g, a.bundle, a.depth))
        if a.file:
            return print(json.dumps(tr.files_impact(g, a.file), indent=1, ensure_ascii=False))
        if a.node:
            return print("\n".join(sorted(tr.neighborhood(g, a.node, a.depth))))
        kinds = {}
        for n in g.nodes.values():
            kinds[n["type"]] = kinds.get(n["type"], 0) + 1
        print(f"{project}: " + ", ".join(f"{v} {k}" for k, v in sorted(kinds.items())) + f", {len(g.edges)} edges")
        issues = tr.lint(g)
        print("\n".join(f"[{i['level']}] {i['code']}: {i['message']}" for i in issues) or "lint: clean")
    elif a.cmd in ("round", "plan"):
        from bt_cli_flows import run_flow
        run_flow(a, project, pdir)
    elif a.cmd == "pending":
        import bt_pending
        print("sorted" if bt_pending.sort_file(pdir) else "already sorted")
        print("\n".join(bt_pending.top(pdir, 10)))
    elif a.cmd == "index":
        print(write_index(pdir).as_posix())
        print(write_global_index().as_posix())
    elif a.cmd == "rollups":
        print("\n".join(pending_rollups(pdir)) or "none")


if __name__ == "__main__":
    main()
