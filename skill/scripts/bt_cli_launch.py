"""CLI surface for starting an approved requirement plan."""
from __future__ import annotations

import argparse
import json


def register(subparsers) -> None:
    parser = subparsers.add_parser("launch", help="HQ: open a new executor session for an approved plan")
    parser.add_argument("req", help="REQ-NNN")
    parser.add_argument("--agent", choices=["claude", "codex", "antigravity"], default="claude")
    parser.add_argument("--profile", help="account profile (bitacora.py profiles list); sets the agent")
    parser.add_argument("--mode", choices=["loop", "goal", "marathon"], default="loop",
                        help="loop/goal: one long session (codex always /goal); marathon: supervisor, a fresh session per task or milestone")
    parser.add_argument("--model", help="marathon: model alias for the sessions (default haiku)")
    parser.add_argument("--repo", help="repo path (remembered for next time)")
    parser.add_argument("--pool", help="marathon: accounts the router may use: auto, or profile ids a,b")
    parser.add_argument("--scheduler", action="store_true",
                        help="marathon: opt in to the durable Scheduler M1/M2/M3 supervisor")
    parser.add_argument("--background", action="store_true", help="no window: detached tmux session / systemd unit")
    parser.add_argument("--force", action="store_true", help="launch even if PLAN.md is not 'approved'")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--foreground", action="store_true",
                        help="replace a verified planning child in the same terminal (bounded runtime required)")
    parser.add_argument("--planning-session", help="provider session id for verified end-of-turn handoff")


def dispatch(args: argparse.Namespace, project: str) -> None:
    from bt_launch import launch

    extra = {"model": args.model or "haiku"} if args.mode == "marathon" or args.model else {}
    for name in ("profile", "pool"):
        value = getattr(args, name)
        if value:
            extra[name] = value
    if args.scheduler:
        extra["scheduler"] = True
    if args.background:
        extra["background"] = True
    if args.foreground:
        extra.update(foreground=True, planning_session=args.planning_session)
    result = launch(project, args.req, args.agent, args.mode, args.repo, args.force, args.dry_run, **extra)
    print(json.dumps(result, indent=1, ensure_ascii=False))
