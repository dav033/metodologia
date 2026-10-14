"""Command line: `python -m bt_scheduler_core <action> ...`. Exit 0 = ok, 2 = refused / invalid.

Actions: validate, simulate, status, audit. Nothing here starts a process, opens a network connection or reads the
environment; the executor and validator of `simulate` are in-process doubles.
"""
from __future__ import annotations

import argparse
import json
import sys

from .config import Config
from .errors import SchedulerError
from .plan import load_plan_file
from .repository import InMemoryRepository
from .scheduler import SchedulerCore
from .simulation import Script, simulate
from .sqlite_repository import SqliteRepository


def _counts(items: list[str] | None) -> dict[str, int]:
    out: dict[str, int] = {}
    for item in items or []:
        name, _, n = item.partition(":")
        out[name] = int(n) if n else 1
    return out


def _plan(args):
    return load_plan_file(args.plan, approved_sha256=args.sha256, plan_id=args.plan_id, revision=args.revision)


def _emit(data, as_json: bool, text: str) -> None:
    print(json.dumps(data, indent=2, sort_keys=True) if as_json else text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m bt_scheduler_core", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="action", required=True)

    def common(p, needs_plan=True):
        if needs_plan:
            p.add_argument("plan", help="path of the approved PLAN.json (read only)")
            p.add_argument("--sha256", required=True, help="sha256 of the approved revision (no hash, no run)")
            p.add_argument("--plan-id")
            p.add_argument("--revision", type=int)
        p.add_argument("--json", action="store_true")

    common(sub.add_parser("validate", help="load and check a plan against its approved hash"))
    sim = sub.add_parser("simulate", help="run the whole plan against in-process doubles")
    common(sim)
    sim.add_argument("--db", help="SQLite file for the run state (default: in memory)")
    sim.add_argument("--parallel", type=int, default=1)
    sim.add_argument("--max-attempts", type=int, default=1)
    sim.add_argument("--fail", action="append", metavar="TASK[:N]", help="first N attempts of TASK fail")
    sim.add_argument("--reject", action="append", metavar="TASK[:N]", help="first N verdicts of TASK reject")
    st = sub.add_parser("status", help="snapshot of a persisted run")
    common(st)
    st.add_argument("--db", required=True)
    au = sub.add_parser("audit", help="print the audit trail of a persisted run")
    au.add_argument("--db", required=True)
    au.add_argument("--since", type=int, default=0)
    au.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.action == "audit":
            rows = [e.to_dict() for e in SqliteRepository(args.db, create=False).audit_log(args.since)]
            _emit(rows, args.json, "\n".join(f"{r['seq']:>5} {r['kind']:<22} {r['task_id']:<6} {r['attempt_id']:<9} {r['detail']}"
                                             for r in rows))
            return 0
        plan = _plan(args)
        if args.action == "validate":
            data = {"plan_id": plan.plan_id, "revision": plan.revision, "sha256": plan.sha256, "tasks": len(plan.tasks)}
            _emit(data, args.json, f"ok {plan.plan_id} r{plan.revision} {len(plan.tasks)} tasks")
        elif args.action == "simulate":
            repo = SqliteRepository(args.db) if args.db else InMemoryRepository()
            config = Config(max_parallel_tasks=args.parallel, max_attempts=args.max_attempts)
            snap, core = simulate(plan, repo, config, Script(_counts(args.fail), _counts(args.reject)))
            data = {**snap.to_dict(), "audit_entries": len(core.audit_log())}
            _emit(data, args.json, f"{snap.status}: " + ", ".join(f"{k}={v['state']}" for k, v in snap.tasks.items()))
        else:
            core = SchedulerCore(plan, SqliteRepository(args.db, create=False), config=Config())
            snap = core.inspect()                                # verifies the binding; changes nothing
            _emit(snap.to_dict(), args.json, f"{snap.status}: " + ", ".join(f"{k}={v['state']}" for k, v in snap.tasks.items()))
        return 0
    except SchedulerError as exc:
        print(f"{exc.code}: " + "; ".join(exc.issues), file=sys.stderr)
        return 2
    except (OSError, ValueError) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
