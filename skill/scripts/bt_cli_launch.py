"""CLI surface for starting an approved requirement plan."""
from __future__ import annotations

import argparse
import json


def register(subparsers) -> None:
    parser = subparsers.add_parser("launch", help="HQ: start the Scheduler run of an approved, frozen plan (plan-json freeze first)",
                                   allow_abbrev=False)  # a dropped --mode must not match --model
    parser.add_argument("req", help="REQ-NNN")
    parser.add_argument("--repo", help="repo path (remembered for next time)")
    parser.add_argument("--background", action="store_true", help="no window: detached tmux session / systemd unit")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--foreground", action="store_true",
                        help="replace a verified planning child in the same terminal (bounded runtime required)")
    parser.add_argument("--planning-session", help="provider session id for verified end-of-turn handoff")


def dispatch(args: argparse.Namespace, project: str) -> None:
    from bt_launch import launch

    extra = {}
    if args.background:
        extra["background"] = True
    if args.foreground:
        extra.update(foreground=True, planning_session=args.planning_session)
    result = launch(project, args.req, repo=args.repo, dry_run=args.dry_run, **extra)
    print(json.dumps(result, indent=1, ensure_ascii=False))
