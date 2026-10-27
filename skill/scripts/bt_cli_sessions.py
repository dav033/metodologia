"""Argument plumbing for hands-on subplan sessions (bt_subplan_sessions): start, status, finish."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from bt_core import find_req


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("sessions", help="work on one subplan WITH the owner in an interactive agent window")
    parser.add_argument("action", choices=("start", "status", "finish"))
    parser.add_argument("req", help="REQ-NNN")
    parser.add_argument("subplan", nargs="?", help="SP-n (start, finish; status lists every session without it)")
    parser.add_argument("--mode", choices=("hands", "auto"), default="hands",
                        help="start: hands = work with the owner at the keyboard; auto is retired (D-134: `stage run`)")
    parser.add_argument("--model", choices=("sonnet", "opus"), default="sonnet",
                        help="agent for the window: Sonnet 5.5 medium (default) or Opus 5.5 high")


def dispatch(args: argparse.Namespace, root: Path, project: str) -> int:
    import bt_subplan_sessions as sessions
    rdir = find_req(root / project, args.req)
    if args.action == "status":
        print(json.dumps([sessions.info(s) for s in sessions.sessions(rdir, args.subplan or "")], indent=1,
                         ensure_ascii=False))
        return 0
    if not args.subplan:
        raise SystemExit(f"sessions {args.action} needs SP-n")
    if args.action == "start":
        ok, msg = sessions.start(root, project, rdir, args.subplan, args.model, args.mode)
        print(msg)
        return 0 if ok else 1
    print(sessions.finish(rdir, args.subplan))
    return 0
