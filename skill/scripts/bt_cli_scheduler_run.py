"""CLI entry for the explicitly opted-in Scheduler owner process."""
from __future__ import annotations

import argparse

import bt_scheduler_run


def register(subparsers) -> None:
    parser = subparsers.add_parser("scheduler-run", help="iniciar o reanudar un plan con Scheduler M1–M6")
    parser.add_argument("req", help="REQ-NNN")
    parser.add_argument("--resume", action="store_true", help="reanudar la misma ejecución Scheduler durable")
    parser.add_argument("--no-autostart", action="store_true", help="no instalar reanudación al iniciar sesión")


def dispatch(args: argparse.Namespace, project: str, pdir) -> int:
    from bt_core import find_req

    return bt_scheduler_run.dispatch(project, args.req, find_req(pdir, args.req), resume=args.resume,
                                    no_autostart=args.no_autostart)
