"""Command line for the planner module: `python -m bt_planner <action> ...` (exit 0 ok, 2 invalid/refused).

    init <dir>      derive PLAN.json skeleton from <dir>/PLAN.md (classification stays absent, reported as gaps)
    check <dir>     publication gate: schema, graph, PLAN.md consistency, frozen-revision integrity
    freeze <dir>    freeze the checked PLAN.json as an immutable revision (PLAN.md status must be approved)
    bind <dir>      launch gate, read-only: PLAN.json is valid and is exactly the approved (frozen) revision
    report <dir>    quality summary of PLAN.json: critical path, distributions, evidence and verification coverage
    show <dir>      list frozen revisions
    compat <dir>    read-only report for a plan written before the contract
    validate <file> validate one PLAN.json on its own (no PLAN.md needed), e.g. a scheduler's input
    schema|example  print the bundled JSON Schema / example plan
"""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

from .command_checks import IgnoredPath
from . import contract as pc
from . import amendments, interfaces, quality, resources, subplan_graph, sync, traceability
from . import revisions as rev

ACTIONS = ("retrofit-audit", "init", "check", "freeze", "bind", "report", "show", "compat", "validate", "schema", "example", "amend",
           "amendments")


def _report(report: pc.Report, as_json: bool, emit: Callable[[str], None]) -> None:
    if as_json:
        emit(json.dumps({"ok": report.ok, "errors": report.errors, "warnings": report.warnings}, ensure_ascii=False))
        return
    for line in report.errors:
        emit(f"ERROR {line}")
    for line in report.warnings:
        emit(f"WARN  {line}")
    emit("OK: PLAN.json is publishable" if report.ok else f"INVALID: {len(report.errors)} error(s)")


def run(action: str, target: str | Path | None = None, *, plan_id: str | None = None, force: bool = False,
        as_json: bool = False, approved_states: tuple[str, ...] | None = None,
        repo_roots: dict[str, Path] | None = None, ref_exists=None, amend: dict | None = None,
        cross_check: bool = False, ignored_path: IgnoredPath | None = None,
        ledger_command: str = "engine audit-ledger check",
        emit: Callable[[str], None] = print) -> int:
    """Execute one action and return the exit code. `target` is a plan directory (a file for `validate`).
    `repo_roots` maps repository roles to paths so that `file:` evidence is verified, not just accepted; `ref_exists`
    (kind, value, repository) does the same for `command:` / `precedent:` references."""
    states = approved_states or sync.APPROVED_STATES
    try:
        if action == "schema":
            emit(resources.schema_text().rstrip("\n"))
            return 0
        if action == "example":
            emit(resources.example_text().rstrip("\n"))
            return 0
        if target is None:
            emit(f"ERROR {action} needs a {'file' if action == 'validate' else 'directory'}")
            return 2
        target = Path(target)
        if action == "validate":
            try:
                plan = pc.loads(target.read_text(encoding="utf-8"))
            except FileNotFoundError:
                emit(f"ERROR {target}: not found")
                return 2
            except (OSError, ValueError, UnicodeError) as exc:
                emit(f"ERROR {target.name}: unreadable ({type(exc).__name__})")
                return 2
            report = pc.validate(plan, ignored_path=ignored_path)
            _report(report, as_json, emit)
            return 0 if report.ok else 2
        if not target.is_dir():
            emit(f"ERROR {target}: not a directory")
            return 2
        if action == "init":
            path = sync.write_skeleton(target, force=force, plan_id=plan_id)
            gaps: dict[str, int] = {}
            errors = sync.check(target, plan_id=plan_id, repo_roots=repo_roots, ref_exists=ref_exists, ignored_path=ignored_path).errors
            for line in errors:
                name = line.split(":")[0].split(".", 1)[-1]
                gaps[name] = gaps.get(name, 0) + 1
            emit(f"{path.as_posix()} written from PLAN.md; classification is intentionally absent "
                 f"({len(errors)} gap(s) to fill before `check` passes):")
            emit("  " + ", ".join(f"{name} x{count}" for name, count in sorted(gaps.items())))
            return 0
        if action == "check":
            report = sync.check(target, plan_id=plan_id, repo_roots=repo_roots, ref_exists=ref_exists, ignored_path=ignored_path,
                                ledger_command=ledger_command)
            _report(report, as_json, emit)
            return 0 if report.ok else 2
        if action == "bind":
            entry = sync.bind_approved(target, plan_id, states, repo_roots=repo_roots, freeze=False, ref_exists=ref_exists, ignored_path=ignored_path)
            if entry is None:
                emit("legacy plan: no PLAN.json and nothing frozen; nothing to bind")
            else:
                emit(f"bound: PLAN.json is revision {entry['revision']} sha256 {entry['sha256'][:12]}"
                     + (" (frozen)" if entry["frozen_at"] else " (not frozen yet: freeze on approval or launch)"))
            return 0
        if action == "report":
            plan, report = sync.read_plan(target)
            if plan is None or not isinstance(plan, dict) or not pc.validate(plan).ok:
                for line in report.errors or pc.validate(plan).errors:
                    emit(f"ERROR {line}")
                emit("INVALID: the report needs a valid PLAN.json")
                return 2
            summary = quality.analyze(plan)
            if pc.schema_tuple(plan) >= pc.EXTENSIONS_SINCE:
                summary.update({"coverage": traceability.coverage_report(plan),
                                "interfaces": interfaces.report(plan),
                                **quality.verification_report(plan)})
            if pc.schema_tuple(plan) >= pc.SCHEMA_13:
                summary["subplans"] = subplan_graph.report(plan)
            emit(json.dumps(summary, indent=1, ensure_ascii=False))
            return 0
        if action == "freeze":
            entry = sync.approve_freeze(target, plan_id, states, repo_roots, ref_exists=ref_exists, ignored_path=ignored_path,
                                        ledger_command=ledger_command)
            emit(f"frozen {plan_id or sync.default_plan_id(target)} revision {entry['revision']} "
                 f"sha256 {entry['sha256'][:12]}")
            return 0
        if action == "retrofit-audit":
            changed = sync.retrofit_audit(target, cross_check=cross_check)
            for line in changed:
                emit(line)
            emit(f"{len(changed)} audit task(s) updated: PLAN.json is a new working revision; review it, then `freeze`"
                 if changed else "every audit task already declares its findings ledger")
            return 0
        if action == "show":
            found = rev.list_revisions(target)
            emit(f"{plan_id or sync.default_plan_id(target)} frozen revisions: " +
                 (", ".join(f"r{r['revision']}@{r['sha256'][:8]}({r.get('source', 'approval')})" for r in found) or "none"))
            return 0
        if action == "compat":
            emit(json.dumps(sync.compat(target, plan_id), indent=1, ensure_ascii=False))
            return 0
        if action == "amendments":
            emit(json.dumps(amendments.read(target), indent=1, ensure_ascii=False))
            return 0
        if action == "amend":
            if not amend:
                emit("ERROR amend needs --task, --field, --to, --reason and --by")
                return 2
            record = amendments.append(target, **amend)
            emit(f"amended {record['task']}.{record['field']}: {record['from']} → {record['to']} "
                 f"(#{record['seq']}, {record['proposed_by']})")
            return 0
        emit(f"ERROR unknown action {action!r}")
        return 2
    except pc.PlanContractError as exc:
        for line in exc.issues:
            emit(f"ERROR {line}")
        emit(exc.code)
        return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m bt_planner", description=__doc__.split("\n\n")[0],
                                     formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    parser.add_argument("action", choices=ACTIONS)
    parser.add_argument("target", nargs="?", help="plan directory (file for `validate`)")
    parser.add_argument("--plan-id", help="override the plan id (default: REQ-042 from a directory named REQ-042-slug)")
    parser.add_argument("--force", action="store_true", help="init: overwrite an existing PLAN.json")
    parser.add_argument("--json", action="store_true", help="check/validate: machine-readable output")
    parser.add_argument("--repo", action="append", default=[], metavar="ROLE=PATH",
                        help="repository role and its checkout, repeatable; makes check/freeze verify `file:` evidence")
    parser.add_argument("--approved-states", help="comma-separated PLAN.md status words that allow freeze "
                                                  f"(default {','.join(sync.APPROVED_STATES)})")
    parser.add_argument("--task", help="amend: task id (T4)")
    parser.add_argument("--field", help=f"amend: one of {', '.join(amendments.FIELDS)}")
    parser.add_argument("--to", dest="to_value", help="amend: the new value")
    parser.add_argument("--reason", help="amend: why the classification changed")
    parser.add_argument("--evidence", action="append", default=[], help="amend: evidence reference, repeatable")
    parser.add_argument("--by", default="cli", help="amend: who or what makes the change")
    parser.add_argument("--proposed-by", choices=amendments.PROPOSERS, default="owner")
    args = parser.parse_args(argv)
    states = tuple(s.strip() for s in args.approved_states.split(",") if s.strip()) if args.approved_states else None
    amend_args = None
    if args.action == "amend" and args.task and args.field and args.to_value is not None and args.reason:
        value = int(args.to_value) if args.field == "estimated_minutes" and args.to_value.isdigit() else args.to_value
        amend_args = {"task": args.task, "field": args.field, "to": value, "reason": args.reason,
                      "evidence": args.evidence, "by": args.by, "proposed_by": args.proposed_by}
    roots = {role.strip(): Path(path) for role, _, path in (item.partition("=") for item in args.repo)
             if role.strip() and path}
    return run(args.action, args.target, plan_id=args.plan_id, force=args.force, as_json=args.json,
               approved_states=states, repo_roots=roots or None, amend=amend_args)


if __name__ == "__main__":
    sys.exit(main())
