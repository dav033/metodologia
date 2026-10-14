"""Argument registration for the bounded delegation CLI."""
import json
import os
import sys
from pathlib import Path

from bt_core import ROOT, slugify


def register(sub) -> None:
    p_del = sub.add_parser("delegate", help="run ONE task in a headless agent session and get a compact checked result")
    p_del.add_argument("action", choices=["start", "exec", "status", "list", "resume", "cleanup"])
    p_del.add_argument("target", nargs="?", help="start: task text; exec/status/resume/cleanup: delegation id")
    p_del.add_argument("--profile", help="account profile (sets the agent; work gate applies)")
    p_del.add_argument("--agent", choices=["claude", "codex", "antigravity"], help="when no --profile (neither: the router chooses)")
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
    p_del.add_argument("--retries", type=int, default=0, help="start: retry failures up to 3 times, climbing one tier")
    p_del.add_argument("--worktree", action="store_true", help="start: run in an isolated git worktree and branch")


def dispatch(a) -> None:
    import bt_delegate
    import bt_delegate_modes
    if a.action == "list":
        print(json.dumps(bt_delegate.listing(), indent=1, ensure_ascii=False))
        return
    if a.action == "status":
        print(json.dumps(bt_delegate.summary(a.target or ""), indent=1, ensure_ascii=False))
        return
    if a.action == "exec":  # internal: runs a delegation that `start --background` created
        print(json.dumps(bt_delegate_modes.execute(a.target or "", a.agent_cmd), indent=1, ensure_ascii=False))
        return
    if a.action == "resume":
        print(json.dumps(bt_delegate_modes.resume(a.target or "", a.agent_cmd), indent=1, ensure_ascii=False))
        return
    if a.action == "cleanup":
        print(json.dumps(bt_delegate_modes.cleanup(a.target or ""), indent=1, ensure_ascii=False))
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
    if a.retries < 0 or a.retries > 3:
        sys.exit("--retries must be between 0 and 3")
    order = bt_delegate.create(project, a.target, a.profile, a.agent, Path(a.workdir or a.cwd), a.allow,
                               a.verify, a.timeout, a.model, a.effort, a.kind, a.tier, a.complexity, a.wait_quota)
    order["retries"], order["worktree_mode"] = a.retries, a.worktree
    (bt_delegate.path_of(order["id"]) / "TASK.json").write_text(
        json.dumps(order, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if a.background:
        print(json.dumps({"id": order["id"], "status": "started", "pid": bt_delegate.start_background(order["id"])}))
    else:
        print(json.dumps(bt_delegate_modes.execute(order["id"], a.agent_cmd, a.retries, a.worktree),
                         indent=1, ensure_ascii=False))
    return

