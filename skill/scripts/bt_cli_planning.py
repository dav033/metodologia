"""Argument plumbing for the collaborative planning flow (bt_planning_flow): requirements → skeleton → subplans."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from bt_core import find_req


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("planning", help="collaborative planning: skeleton, subplan focus and confirmations")
    parser.add_argument("action", choices=("start", "status", "outline-confirm", "focus", "confirm"))
    parser.add_argument("req", help="REQ-NNN")
    parser.add_argument("subplan", nargs="?", help="SP-n (focus, confirm)")
    parser.add_argument("--by", choices=("owner", "planner"),
                        help="who decided (required to confirm): an agent passes `owner` only to relay the owner's "
                             "explicit words in the conversation, never on its own judgment")


def dispatch(args: argparse.Namespace, root: Path, project: str) -> int:
    import bt_planning_flow as flow
    rdir = find_req(root / project, args.req)
    if args.action == "start":
        print("Collaborative planning on." if flow.start(rdir) else "Collaborative planning was already on.")
    elif args.action == "status":
        st = flow.state(rdir)
        st["inputs"] = [row for row in st["inputs"] if row["pending"]]
        print(json.dumps(st, indent=1, ensure_ascii=False))
    elif args.action in ("outline-confirm", "confirm") and args.by != "owner":
        raise SystemExit(f"planning {args.action} records the owner's confirmation: pass --by owner, and only when "
                         "the owner said so")
    elif args.action == "outline-confirm":
        print(flow.confirm_outline(project, rdir, "owner", via="conversation"))
    elif not args.subplan:
        raise SystemExit(f"planning {args.action} needs SP-n")
    elif args.action == "focus":
        print(flow.focus(project, rdir, args.subplan, args.by or "planner"))
    else:
        print(flow.confirm(project, rdir, args.subplan, "owner", via="conversation"))
    return 0
