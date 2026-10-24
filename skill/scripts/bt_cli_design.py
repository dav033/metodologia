"""Argument plumbing for owner approval of UI design contracts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import bt_design_approval as approval
from bt_core import find_req


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("design", help="approve versioned UI design contracts")
    parser.add_argument("action", choices=("list", "show", "approve", "changes"))
    parser.add_argument("req", help="REQ-NNN")
    parser.add_argument("contract", nargs="?", help="<contract>@vN")
    parser.add_argument("--comments", default="")


def dispatch(args: argparse.Namespace, root: Path, project: str) -> int:
    rdir = find_req(root / project, args.req)
    rows = approval.ui_contracts(rdir, project)
    if args.action in ("list", "show"):
        selected = [row for row in rows if args.action == "show" and
                    (args.contract is None or row["contract"] == args.contract)]
        if args.action == "list":
            selected = [row for row in rows if row["design_state"] == "completed" and
                        (not row["approval"] or row["approval"].get("status") != "approved")]
        if args.action == "show" and args.contract and not selected:
            raise SystemExit(f"No UI design contract {args.contract} in {args.req}")
        print(json.dumps(selected, indent=1, ensure_ascii=False))
        return 0
    if not args.contract:
        raise SystemExit(f"design {args.action} needs <contract>@vN")
    if args.action == "changes" and not args.comments.strip():
        raise SystemExit("design changes needs --comments")
    if approval.repository_for_contract(root, project, rdir, args.contract) is None:
        raise SystemExit(f"{args.contract} is not a UI contract in {args.req}, or its repository is not registered")
    import bt_design_web
    import bt_vcs
    message = bt_design_web.decide(root, project, approval_req_id(rdir), rdir,
                                  {"contract": args.contract, "decision": args.action,
                                   "comments": args.comments},
                                  lambda path, text: bt_vcs.commit(path, text, push=False), via="cli")
    print(message)
    return 0


def approval_req_id(rdir: Path) -> str:
    import re
    match = re.match(r"REQ-\d+", rdir.name)
    if not match:
        raise SystemExit(f"Invalid requirement directory: {rdir}")
    return match.group(0)
