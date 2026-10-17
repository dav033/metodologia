"""Argument plumbing for `bitacora.py plan-json ...`; the work is done by the planner module through the adapter."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import bt_plan_adapter as adapter
import bt_plan_history
from bt_core import find_req


def add_parser(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("plan-json", help="manage PLAN.json or read the conservative planning-history projection")
    parser.add_argument("action", choices=["init", "check", "freeze", "bind", "report", "show", "compat", "history"])
    parser.add_argument("req", nargs="?", help="REQ-NNN (not used by history)")
    parser.add_argument("--force", action="store_true", help="init: overwrite an existing PLAN.json")
    parser.add_argument("--json", action="store_true", help="check: machine-readable output")
    parser.add_argument("--kind", choices=bt_plan_history.TASK_KINDS,
                        help="history: task kind")
    parser.add_argument("--complexity", choices=bt_plan_history.CONTEXT_VALUES["complexity"])
    parser.add_argument("--scope", choices=bt_plan_history.CONTEXT_VALUES["scope"])
    parser.add_argument("--risk", choices=bt_plan_history.CONTEXT_VALUES["risk"])
    parser.add_argument("--coupling", choices=bt_plan_history.CONTEXT_VALUES["coupling"])


def dispatch(args: argparse.Namespace, root: Path, project: str) -> int:
    action = args.action
    req = getattr(args, "req", None)
    kind = getattr(args, "kind", None)
    context = {field: getattr(args, field, None) for field in bt_plan_history.CONTEXT_FIELDS}
    force = getattr(args, "force", False)
    as_json = getattr(args, "json", False)
    if action == "history":
        if req is not None:
            print("plan-json history does not accept REQ-NNN")
            return 2
        if force:
            print("plan-json history does not accept --force")
            return 2
        if kind is None:
            print("plan-json history requires --kind")
            return 2
        try:
            report = bt_plan_history.project_history(kind, context)
        except bt_plan_history.PlanningHistoryInputError as exc:
            print(str(exc))
            return 2
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0
    if kind is not None or any(value is not None for value in context.values()):
        print("planning-history options are only valid with plan-json history")
        return 2
    if req is None:
        print(f"plan-json {action} requires REQ-NNN")
        return 2
    rdir = find_req(root / project, req)
    compatibility_report = None
    if action in {"freeze", "bind", "compat"}:
        import bt_scheduler_adapter
        compatibility_report = bt_scheduler_adapter.plan_compatibility_report(rdir)
    return adapter.run_cli(action, rdir, force=force, as_json=as_json,
                           compatibility_report=compatibility_report)
