"""CLI for the unattended Scheduler: `scheduler-watch` keeps a run alive, `scheduler-op` is the operator's hand on it."""
from __future__ import annotations

import argparse
import json

import bt_scheduler_adapter as adapter

ACTIONS = ("status", "decisions", "decide", "stop", "resume", "cancel-attempt", "reopen", "retry", "rework", "revise")


def register(subparsers) -> None:
    watch = subparsers.add_parser("scheduler-watch", help="vigilar un plan: reanuda el scheduler si muere, hasta que termine")
    watch.add_argument("req", help="REQ-NNN")
    watch.add_argument("--detach", action="store_true", help="correr en segundo plano (log en .state/watch/)")
    op = subparsers.add_parser("scheduler-op", help="mover un plan en marcha: cancelar intento, reabrir tarea, revisar el plan")
    op.add_argument("req", help="REQ-NNN")
    op.add_argument("action", choices=ACTIONS)
    op.add_argument("target", nargs="?", default="",
                    help="attempt id for cancel-attempt, task id for reopen and retry, comma-separated task ids for rework "
                         "(they and everything downstream go back to be redone), request id for decide")
    op.add_argument("option", nargs="?", default="", help="the option to take, for decide")
    op.add_argument("--reason", default="", help="why (kept in the run's audit trail)")
    op.add_argument("--hold", action="store_true", help="leave the run stopped; `resume` releases it")
    op.add_argument("--only", action="store_true",
                    help="rework: send back only the tasks named, not what depends on them")


def dispatch(args: argparse.Namespace, project: str, pdir) -> int:
    from bt_core import find_req

    import bt_scheduler_ops as ops

    rdir = find_req(pdir, args.req)
    if args.cmd == "scheduler-watch":
        import bt_scheduler_watch
        return bt_scheduler_watch.watch(project, args.req, rdir, detach=args.detach)
    if adapter.authority(rdir) != adapter.AUTHORITY:
        print(f"{args.req} has no Scheduler run")
        return 2
    if args.action == "status":
        print(json.dumps(ops.status(project, args.req, rdir), indent=1))
        return 0
    if args.action == "decisions":
        import bt_scheduler_decisions as decisions
        print(decisions.render(decisions.open_requests(rdir), args.req))
        return 0
    if args.action == "decide":
        import bt_scheduler_decisions as decisions
        if not args.target or not args.option:
            print("decide needs a request id and an option: scheduler-op REQ decide <request> <option> [--reason …]")
            return 2
        try:
            for line in decisions.answer(project, args.req, rdir, args.target, args.option, args.reason):
                print(line)
        except (ValueError, adapter.core.SchedulerError) as exc:
            print(exc)
            return 2
        return 0
    if args.action == "resume":
        print(ops.resume(project, args.req, rdir))
        return 0
    if args.action in {"cancel-attempt", "reopen", "retry", "rework"} and not args.target:
        print(f"{args.action} needs a target (attempt id, or task id(s) for reopen, retry and rework)")
        return 2
    try:
        if args.action == "stop":
            ops.hold_path(rdir).write_text('{"why": "operator stop"}\n', encoding="utf-8")
            print(f"owner stopped: {ops.stop_owner(project, args.req)}; held — `scheduler-op {args.req} resume` releases it")
            return 0
        if args.action == "retry":
            for line in ops.retry(project, args.req, rdir, args.target, args.reason):
                print(line)
            print(ops.resume(project, args.req, rdir))
            return 0
        for line in ops.apply(project, args.req, rdir, args.action, args.target, args.reason, keep_held=args.hold,
                           only=args.only):
            print(line)
    except adapter.core.SchedulerError as exc:
        print(f"{exc.code}: {exc}")
        ops.resume(project, args.req, rdir) if not args.hold else None
        return 2
    print("held" if args.hold else ops.resume(project, args.req, rdir))
    return 0
