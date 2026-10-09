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
    p_launch = sub.add_parser("launch", help="HQ: open a new executor session for an approved plan")
    p_launch.add_argument("req", help="REQ-NNN")
    p_launch.add_argument("--agent", choices=["claude", "codex"], default="claude")
    p_launch.add_argument("--mode", choices=["loop", "goal", "marathon"], default="loop",
                          help="loop/goal: one long session (codex always /goal); marathon: supervisor, a fresh session per task")
    p_launch.add_argument("--model", help="marathon: model alias for the sessions (default haiku)")
    p_launch.add_argument("--repo", help="repo path (remembered for next time)")
    p_launch.add_argument("--force", action="store_true", help="launch even if PLAN.md is not 'approved'")
    p_launch.add_argument("--dry-run", action="store_true")
    p_run = sub.add_parser("run", help="marathon: supervise a plan, a fresh headless session per task (days)")
    p_run.add_argument("req", help="REQ-NNN")
    p_run.add_argument("--agent", choices=["claude", "codex"])
    p_run.add_argument("--model", help="default haiku")
    p_run.add_argument("--no-ultracode", action="store_true")
    p_run.add_argument("--max-attempts", type=int)
    p_run.add_argument("--session-timeout", type=int, help="minutes per session (default 60)")
    p_run.add_argument("--resume", action="store_true", help="continue from RUN.json (autostart uses this)")
    p_run.add_argument("--retry-blocked", action="store_true", help="with --resume: give blocked tasks a fresh start")
    p_run.add_argument("--agent-cmd", help="tests: command template with {prompt_file} {workdir} {task} {req} {project}")
    p_run.add_argument("--once", action="store_true", help="run a single session and exit")
    p_run.add_argument("--no-autostart", action="store_true", help="do not install the Windows Startup entry")
    p_task = sub.add_parser("task", help="marathon agent report: done / fail / note on a plan task")
    p_task.add_argument("action", choices=["done", "fail", "note"])
    p_task.add_argument("req", help="REQ-NNN")
    p_task.add_argument("task", help="T3")
    p_task.add_argument("--evidence", default="", help="done: what proves it")
    p_task.add_argument("--reason", default="", help="fail: why")
    p_task.add_argument("--text", default="", help="note: advice for the next attempt")
    p_task.add_argument("--blocked", action="store_true", help="fail: needs a human, do not retry")
    p_rc = sub.add_parser("run-control", help="pause / resume / stop a running marathon")
    p_rc.add_argument("req", help="REQ-NNN")
    p_rc.add_argument("action", choices=["pause", "resume", "stop"])
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
    p_hook.add_argument("event", choices=["start", "stop", "end"])
    p_hook.add_argument("--harness", choices=["claude", "codex"], default="claude")
    a = ap.parse_args()

    if a.cmd == "hook":
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
            print("gitleaks not found — install with: winget install Gitleaks.Gitleaks")
        for d in sorted(p for p in ROOT.iterdir() if (p / "project.json").exists()):
            for role, path in ws.repos(ROOT, d.name).items():
                if path.exists() and path.resolve() != ROOT.resolve().parent:
                    print(f"{d.name}/{role}: {install_hook(path)}")
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
    elif a.cmd == "launch":
        from bt_launch import launch
        extra = {"model": a.model or "haiku"} if a.mode == "marathon" or a.model else {}
        print(json.dumps(launch(project, a.req, a.agent, a.mode, a.repo, a.force, a.dry_run, **extra), indent=1,
                         ensure_ascii=False))
    elif a.cmd == "run":
        from bt_run import supervise
        sys.exit(supervise(project, a.req, agent=a.agent, model=a.model, ultracode=False if a.no_ultracode else None,
                           max_attempts=a.max_attempts, session_timeout=a.session_timeout,
                           retry_blocked=a.retry_blocked, agent_cmd=a.agent_cmd, once=a.once,
                           no_autostart=a.no_autostart))
    elif a.cmd == "monitor":
        from bt_monitor import open_monitor
        print(json.dumps(open_monitor(project, a.req, a.model, a.dry_run), indent=1, ensure_ascii=False))
    elif a.cmd in ("task", "run-control"):
        import bt_runtask as rt
        rdir = find_req(pdir, a.req)
        if a.cmd == "run-control":
            print(rt.run_control(rdir, a.action))
        else:
            print({"done": lambda: rt.task_done(rdir, a.task, a.evidence),
                   "fail": lambda: rt.task_fail(rdir, a.task, a.reason, a.blocked),
                   "note": lambda: rt.task_note(rdir, a.task, a.text)}[a.action]())
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
