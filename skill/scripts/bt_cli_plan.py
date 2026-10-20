"""Argument plumbing for `bitacora.py plan-json ...`; the work is done by the planner module through the adapter."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import bt_links
import bt_plan_adapter as adapter
import bt_plan_history
from bt_core import find_req


def add_parser(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("plan-json", help="manage PLAN.json or read the conservative planning-history projection")
    parser.add_argument("action", choices=["init", "check", "freeze", "bind", "report", "show", "compat", "history",
                                           "amend", "amendments", "retrofit-audit"])
    parser.add_argument("req", nargs="?", help="REQ-NNN (not used by history)")
    parser.add_argument("rest", nargs="*", help="amend: TASK FIELD VALUE (e.g. T4 complexity high)")
    parser.add_argument("--reason", help="amend: why the classification changed")
    parser.add_argument("--evidence", action="append", default=[], help="amend: evidence reference, repeatable")
    parser.add_argument("--by", help="amend: who or what makes the change (default: the proposer)")
    parser.add_argument("--proposed-by", choices=["owner", "agent"], default="owner",
                        help="amend: an agent may only raise a level, and needs evidence; lowering is the owner's")
    parser.add_argument("--force", action="store_true", help="init: overwrite an existing PLAN.json")
    parser.add_argument("--cross-check", action="store_true", dest="cross_check",
                        help="retrofit-audit: also add an independent cross-check audit when the plan has a single audit")
    parser.add_argument("--json", action="store_true", help="check: machine-readable output")
    parser.add_argument("--kind", choices=bt_plan_history.TASK_KINDS,
                        help="history: task kind")
    parser.add_argument("--complexity", choices=bt_plan_history.CONTEXT_VALUES["complexity"])
    parser.add_argument("--scope", choices=bt_plan_history.CONTEXT_VALUES["scope"])
    parser.add_argument("--risk", choices=bt_plan_history.CONTEXT_VALUES["risk"])
    parser.add_argument("--coupling", choices=bt_plan_history.CONTEXT_VALUES["coupling"])


def add_status_parser(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("plan-status", help="progress of one plan or all plans (read-only unless --write)")
    parser.add_argument("req", nargs="?", help="REQ-NNN")
    parser.add_argument("--all", action="store_true", help="every plan of the project")
    parser.add_argument("--write", action="store_true", help="refresh the generated status block in PLAN.md")
    parser.add_argument("--json", action="store_true", help="machine-readable output")


def dispatch_status(args: argparse.Namespace, root: Path, project: str) -> int:
    import bt_planblock
    import bt_planstatus
    pdir = root / project
    if args.req and not args.all:
        rdirs = [find_req(pdir, args.req)]
    else:
        rdirs = [d for d in sorted(pdir.glob("requirements/REQ-*")) if (d / "PLAN.md").exists() or (d / "PLAN.json").exists()]
    statuses = [bt_planstatus.plan_status(project, d) for d in rdirs]
    if args.write:
        for d in rdirs:
            bt_planblock.refresh_plan_block(project, d)
    if args.json:
        print(json.dumps(statuses if args.all or not args.req else statuses[0], ensure_ascii=False, indent=1))
    else:
        print(bt_links.linkify("\n".join(bt_planblock.status_table(s) for s in statuses) or "no hay planes", project))
    return 0


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
    if action in {"amend", "amendments"}:
        return _amend(args, rdir, project)
    compatibility_report = None
    if action in {"freeze", "bind", "compat"}:
        import bt_scheduler_adapter
        compatibility_report = bt_scheduler_adapter.plan_compatibility_report(rdir)
    return adapter.run_cli(action, rdir, force=force, as_json=as_json,
                           compatibility_report=compatibility_report, cross_check=bool(getattr(args, "cross_check", False)))


def _amend(args: argparse.Namespace, rdir: Path, project: str) -> int:
    """`plan-json amend REQ T4 complexity high --reason ... [--evidence ...] [--proposed-by agent]`: the classification
    changes without a new revision; it is noted in the run's audit and the next assignment uses it."""
    if args.action == "amendments":
        print(json.dumps(adapter.amendments(rdir), indent=1, ensure_ascii=False))
        return 0
    if len(args.rest) != 3 or not args.reason:
        print("plan-json amend REQ-NNN TASK FIELD VALUE --reason TEXT [--evidence REF]... [--proposed-by owner|agent]")
        return 2
    task, field, value = args.rest
    value = int(value) if field == "estimated_minutes" and value.isdigit() else value
    try:
        record = adapter.amend(rdir, task, field, value, reason=args.reason, evidence=args.evidence,
                               by=args.by or args.proposed_by, proposed_by=args.proposed_by)
    except adapter.planner.PlanContractError as exc:
        print(f"{exc.code}: " + "; ".join(exc.issues))
        return 2
    import bt_scheduler_adapter
    noted = bt_scheduler_adapter.record_amendment(rdir, record)
    print(f"amended {record['task']}.{record['field']}: {record['from']} → {record['to']} "
          f"(#{record['seq']}, {record['proposed_by']}); the next assignment uses it"
          + ("; noted in the run audit" if noted else "; no Scheduler run yet"))
    return 0
