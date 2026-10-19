"""CLI entry for the explicitly opted-in Scheduler owner process."""
from __future__ import annotations

import argparse

import bt_scheduler_run


def register(subparsers) -> None:
    parser = subparsers.add_parser("scheduler-run", help="iniciar o reanudar un plan con Scheduler M1–M6")
    parser.add_argument("req", help="REQ-NNN")
    parser.add_argument("--resume", action="store_true", help="reanudar la misma ejecución Scheduler durable")
    parser.add_argument("--rebase", action="store_true",
                        help="pasar la ejecución a la última revisión congelada del plan conservando lo aceptado, y reanudar")
    parser.add_argument("--no-autostart", action="store_true", help="no instalar reanudación al iniciar sesión")


def dispatch(args: argparse.Namespace, project: str, pdir) -> int:
    from bt_core import find_req

    rdir = find_req(pdir, args.req)
    resume = args.resume
    if getattr(args, "rebase", False):
        import bt_scheduler_adapter
        try:
            report = bt_scheduler_adapter.rebase_to_latest(rdir)
        except bt_scheduler_adapter.core.SchedulerError as exc:
            print(f"{exc.code}: {exc}")
            return 2
        print(f"rebase r{report.from_revision} → r{report.to_revision}: conservadas {len(report.kept)}, "
              f"rehacer {len(report.reset)}, nuevas {len(report.added)}, quitadas {len(report.removed)}")
        try:
            bt_scheduler_run.rebind_runtime(rdir)
        except bt_scheduler_run.RuntimeErrorCode as exc:
            print(f"{exc.code}: {exc}")
            return 2
        resume = True
    return bt_scheduler_run.dispatch(project, args.req, rdir, resume=resume, no_autostart=args.no_autostart)
