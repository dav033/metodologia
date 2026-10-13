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
    p_launch.add_argument("--profile", help="account profile (bitacora.py profiles list); sets the agent")
    p_launch.add_argument("--mode", choices=["loop", "goal", "marathon"], default="loop",
                          help="loop/goal: one long session (codex always /goal); marathon: supervisor, a fresh session per task or milestone")
    p_launch.add_argument("--model", help="marathon: model alias for the sessions (default haiku)")
    p_launch.add_argument("--repo", help="repo path (remembered for next time)")
    p_launch.add_argument("--pool", help="marathon: accounts the router may use: auto, or profile ids a,b")
    p_launch.add_argument("--background", action="store_true", help="no window: detached tmux session / systemd unit")
    p_launch.add_argument("--force", action="store_true", help="launch even if PLAN.md is not 'approved'")
    p_launch.add_argument("--dry-run", action="store_true")
    p_run = sub.add_parser("run", help="marathon: supervise a plan, a fresh headless session per task or per milestone (days)")
    p_run.add_argument("req", help="REQ-NNN")
    p_run.add_argument("--agent", choices=["claude", "codex"])
    p_run.add_argument("--pool", help="accounts the router may use: auto (every account allowed for the project), "
                                      "profile ids a,b, or none (pin to --agent/--profile)")
    p_run.add_argument("--audit", dest="audit", action="store_true", default=None,
                       help="independent audit session after each milestone (default with a pool)")
    p_run.add_argument("--no-audit", dest="audit", action="store_false")
    p_run.add_argument("--workers", type=int, help="sessions at once, only across different repos (default 1, max 2)")
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
    p_task = sub.add_parser("task", help="marathon agent report: done / fail / note / escalate on a plan task")
    p_task.add_argument("action", choices=["done", "fail", "note", "escalate"])
    p_task.add_argument("req", help="REQ-NNN")
    p_task.add_argument("task", help="T3")
    p_task.add_argument("--evidence", default="", help="done: what proves it")
    p_task.add_argument("--reason", default="", help="fail / escalate: why")
    p_task.add_argument("--to", choices=["standard", "top", "sonnet", "opus"],
                        help="escalate: top (architecture; alias opus) or standard (stuck; alias sonnet)")
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
    p_prof = sub.add_parser("profiles", help="account profiles: list, doctor, or check one against a project")
    p_prof.add_argument("action", choices=["list", "doctor", "check", "add", "gate", "wrapper"])
    p_prof.add_argument("profile", nargs="?", help="check/add: profile id")
    p_prof.add_argument("--provider", choices=["claude", "codex"], help="add: provider")
    p_prof.add_argument("--env", action="append", default=[], metavar="KEY=VALUE",
                        help="add: environment selecting the account, e.g. CLAUDE_CONFIG_DIR=~/.claude-work")
    p_prof.add_argument("--work-only", action="store_true", help="add: only runs projects with work=true")
    p_prof.add_argument("--bin", help="add: executable name if not the provider default")
    p_prof.add_argument("--dir", help="wrapper: directory for the launcher (default ~/.local/bin)")
    p_work = sub.add_parser("work", help="show or set the project's work flag (gates work-only profiles)")
    p_work.add_argument("value", nargs="?", choices=["true", "false"])
    p_del = sub.add_parser("delegate", help="run ONE task in a headless agent session and get a compact checked result")
    p_del.add_argument("action", choices=["start", "exec", "status", "list"])
    p_del.add_argument("target", nargs="?", help="start: the task text; exec/status: delegation id")
    p_del.add_argument("--profile", help="account profile (sets the agent; work gate applies)")
    p_del.add_argument("--agent", choices=["claude", "codex"], help="when no --profile (neither: the router chooses)")
    p_del.add_argument("--kind", choices=["implement", "test", "docs", "audit", "research"],
                       help="what the work is (routing; default: inferred from the task text)")
    p_del.add_argument("--tier", type=int, choices=[0, 1, 2], help="capability tier: 0 light, 1 standard, 2 top")
    p_del.add_argument("--complexity", choices=["S", "M", "L"], help="how big the task is (telemetry)")
    p_del.add_argument("--wait-quota", action="store_true",
                       help="when every account is waiting for a usage-limit reset, wait and run it then")
    p_del.add_argument("--workdir", help="folder the agent works in (default: --cwd)")
    p_del.add_argument("--allow", action="append", default=[], help="path the agent may modify (repeatable)")
    p_del.add_argument("--verify", help="command whose exit status decides success (run by the supervisor)")
    p_del.add_argument("--timeout", type=float, default=30, help="minutes (default 30)")
    p_del.add_argument("--model")
    p_del.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"])
    p_del.add_argument("--background", action="store_true", help="start: return the id immediately")
    p_del.add_argument("--agent-cmd", help="tests: command template with {prompt_file} {workdir} {result} {id}")
    p_met = sub.add_parser("metrics", help="attempt telemetry per agent/profile/model/effort (null = not reported)")
    p_met.add_argument("--by", help="group keys, comma separated: agent,profile,model,effort,kind,tier,project")
    p_met.add_argument("--advice", action="store_true", help="plain-language observations instead of the table")
    p_met.add_argument("--attempts", type=int, metavar="N", help="the last N attempts, each as a key/value table")
    p_met.add_argument("--why", action="store_true", help="how attempts ended per agent/model/effort/kind/complexity, "
                                                          "with the reasons they failed or worked")
    p_ag = sub.add_parser("agents", help="agent catalog: models, ladder, accounts and usage-limit state; route preview")
    p_ag.add_argument("action", nargs="?", choices=["list", "route", "brief", "quota-clear"], default="list")
    p_ag.add_argument("profile", nargs="?", help="quota-clear: profile id")
    p_ag.add_argument("--kind", choices=["implement", "test", "docs", "audit", "research"], default="implement")
    p_ag.add_argument("--tier", type=int, choices=[0, 1, 2])
    p_cfg = sub.add_parser("config", help="machine settings (.state/config.json): get | set KEY VALUE | unset KEY")
    p_cfg.add_argument("action", choices=["get", "set", "unset"])
    p_cfg.add_argument("key", nargs="?")
    p_cfg.add_argument("value", nargs="?")
    p_learn = sub.add_parser("learn", help="evidence-backed learnings about the project and the owner's preferences")
    p_learn.add_argument("action", choices=["add", "list", "confirm", "reject", "brief"])
    p_learn.add_argument("target", nargs="?", help="add: the learning (one sentence); confirm/reject: L-NNN")
    p_learn.add_argument("--evidence", default="", help="add: what was observed (required)")
    p_learn.add_argument("--source", default="", help="add: where it was observed, e.g. REQ-006/T3")
    p_learn.add_argument("--scope", choices=["project", "owner", "skill"], default="project")
    p_learn.add_argument("--kind", choices=["preference", "convention", "pitfall", "tooling", "decision"],
                         default="convention")
    p_learn.add_argument("--status", choices=["candidate", "confirmed", "rejected"], help="list: filter")
    p_learn.add_argument("--reason", default="", help="reject: why")
    p_ho = sub.add_parser("handoff", help="validate a plan, approve it when safe and start it in the background")
    p_ho.add_argument("req", help="REQ-NNN")
    p_ho.add_argument("--dry-run", action="store_true", help="only say what would happen and why")
    p_ho.add_argument("--pool", help="accounts the router may use (default: auto)")
    p_ho.add_argument("--profile", help="preferred account among equals")
    p_ho.add_argument("--model", help="tier 0 model of the preferred provider")
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
            from bt_platform import gitleaks_install_hint
            print(f"gitleaks not found — {gitleaks_install_hint()}")
        for d in sorted(p for p in ROOT.iterdir() if (p / "project.json").exists()):
            for role, path in ws.repos(ROOT, d.name).items():
                if path.exists() and path.resolve() != ROOT.resolve().parent:
                    print(f"{d.name}/{role}: {install_hook(path)}")
        return

    if a.cmd == "delegate":  # no project binding needed beyond the name
        import bt_delegate
        if a.action == "list":
            print(json.dumps(bt_delegate.listing(), indent=1, ensure_ascii=False))
            return
        if a.action == "status":
            print(json.dumps(bt_delegate.summary(a.target or ""), indent=1, ensure_ascii=False))
            return
        if a.action == "exec":  # internal: runs a delegation that `start --background` created
            print(json.dumps(bt_delegate.execute(a.target or "", a.agent_cmd), indent=1, ensure_ascii=False))
            return
        project = slugify(a.project, 60) if a.project else (
            slugify(os.environ["BITACORA_PROJECT"], 60) if os.environ.get("BITACORA_PROJECT") else None)
        if not project:
            import bt_audit
            project = bt_audit.project_for_cwd(ROOT, Path(a.workdir or a.cwd))
        if not project:
            sys.exit("No project resolved; pass --project <name>.")
        if not a.target:
            sys.exit("delegate start needs the task text")
        order = bt_delegate.create(project, a.target, a.profile, a.agent, Path(a.workdir or a.cwd), a.allow,
                                   a.verify, a.timeout, a.model, a.effort, a.kind, a.tier, a.complexity, a.wait_quota)
        if a.background:
            print(json.dumps({"id": order["id"], "status": "started", "pid": bt_delegate.start_background(order["id"])}))
        else:
            print(json.dumps(bt_delegate.execute(order["id"], a.agent_cmd), indent=1, ensure_ascii=False))
        return

    if a.cmd == "metrics":  # machine-level: reads <root>/.state/events
        import bt_events
        rows = bt_events.read_all()
        if a.advice:
            print("\n".join(bt_events.advice(rows)))
            return
        if a.attempts:
            for row in rows[-a.attempts:]:
                pairs = bt_events.key_values(row)
                width = max(len(k) for k, _ in pairs)
                print("\n".join(f"{k.ljust(width)} : {v}" for k, v in pairs) + "\n" + "-" * 60)
            return
        if a.why:
            print(json.dumps(bt_events.reasons(rows), indent=1, ensure_ascii=False))
            return
        by = [k.strip() for k in (a.by or "").split(",") if k.strip()] or None
        print(json.dumps(bt_events.summary(rows, by), indent=1, ensure_ascii=False))
        return

    if a.cmd == "config":  # machine-level
        import bt_config
        print(bt_config.cli(a.action, a.key, a.value))
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
            import bt_agents
            if a.action == "brief":
                print(bt_agents.brief(project))
            elif a.action == "quota-clear":
                print("cleared" if bt_agents.quota_clear(a.profile or "") else "nothing to clear")
            elif a.action == "route":
                if not project:
                    sys.exit("agents route needs a project (--project <name>)")
                import bt_delegate
                print(json.dumps(bt_delegate.auto_route(project, a.kind, a.tier), indent=1, ensure_ascii=False))
            else:
                print(json.dumps(bt_agents.catalog(project), indent=1, ensure_ascii=False))
            return
        import bt_config
        import bt_learn
        if a.action in ("confirm", "reject") and bt_learn.scope_of_id(a.target or "") is None and a.scope == "project":
            a.scope = "owner"  # an LG- id is global: no --scope needed
        scope_project = project if a.scope == "project" else None
        if a.action in ("add", "confirm", "reject") and a.scope == "project" and not project:
            sys.exit("No project resolved; pass --project <name> or --scope owner.")
        if a.action == "add":
            item = bt_learn.add(scope_project, a.target or "", a.evidence, a.source, a.scope, a.kind,
                                bt_config.get("learn.promote_after", 3))
            state = "ignored (the owner rejected it before)" if item.get("ignored") else item["status"]
            print(f"{item['id']} {state} ({item['sightings']} sighting(s)){'' if item['created'] else ' — merged into an existing learning'}")
        elif a.action in ("confirm", "reject"):
            item = (bt_learn.confirm(scope_project, a.target or "", a.scope) if a.action == "confirm" else
                    bt_learn.reject(scope_project, a.target or "", a.scope, a.reason))
            print(f"{item['id']} {item['status']}: {item['text']}")
        elif a.action == "brief":
            print(bt_learn.brief(project, bt_config.get("learn.inject_max", 12)) or "(nothing learned yet)")
        else:
            for item in bt_learn.listing(project, None, a.status):
                print(f"{item['id']} [{item['scope']} · {item['kind']} · {item['status']} · {item['sightings']}x] {item['text']}")
        if a.action in ("add", "confirm", "reject"):
            from bt_vcs import commit
            commit(ROOT, f"{project or 'owner'}: learning {a.action}")
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
            print(bt_profiles.write_wrapper(a.profile, target))
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
    elif a.cmd == "launch":
        from bt_launch import launch
        extra = {"model": a.model or "haiku"} if a.mode == "marathon" or a.model else {}
        if a.profile:
            extra["profile"] = a.profile
        if a.pool:
            extra["pool"] = a.pool
        if a.background:
            extra["background"] = True
        print(json.dumps(launch(project, a.req, a.agent, a.mode, a.repo, a.force, a.dry_run, **extra), indent=1,
                         ensure_ascii=False))
    elif a.cmd == "run":
        from bt_run import supervise
        sys.exit(supervise(project, a.req, agent=a.agent, model=a.model, ultracode=False if a.no_ultracode else None,
                           max_attempts=a.max_attempts, session_timeout=a.session_timeout,
                           retry_blocked=a.retry_blocked, agent_cmd=a.agent_cmd, once=a.once,
                           no_autostart=a.no_autostart, profile=a.profile,
                           workers=a.workers, pool=a.pool, audit=a.audit))
    elif a.cmd == "handoff":
        import bt_handoff
        result = bt_handoff.handoff(project, a.req, a.dry_run, a.pool, a.model, a.profile)
        print(json.dumps(result, indent=1, ensure_ascii=False))
        sys.exit(0 if result["decision"] in ("launched", "would_launch", "already_running", "done") else
                 3 if result["decision"] == "needs_approval" else 2)
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
