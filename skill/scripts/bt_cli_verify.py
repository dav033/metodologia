"""Argument plumbing for per-subplan verification (bt_verification): status, open a version locally, approve, reject."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from bt_core import find_req


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("verify", help="try each finished subplan on its own: status, open, approve, reject")
    parser.add_argument("action", choices=("status", "open", "close", "approve", "reject", "revert-command"))
    parser.add_argument("req", help="REQ-NNN")
    parser.add_argument("subplan", nargs="?", help="SP-n (every action but status)")
    parser.add_argument("--note", default="", help="why it is rejected (required to reject)")
    parser.add_argument("--by", choices=("owner", "planner"),
                        help="approve/reject record the owner's decision: an agent passes `owner` only to relay the "
                             "owner's explicit words, never on its own judgment")


def dispatch(args: argparse.Namespace, root: Path, project: str) -> int:
    import bt_verification as verification
    rdir = find_req(root / project, args.req)
    if args.action == "status":
        st = verification.state(rdir)
        for row in st["subplans"]:
            row["state_es"] = verification.STATES_ES[row["state"]]
        st["blocking"] = verification.gate(rdir)
        print(json.dumps(st, indent=1, ensure_ascii=False))
        return 0
    if not args.subplan:
        raise SystemExit(f"verify {args.action} needs SP-n")
    if args.action in ("approve", "reject") and args.by != "owner":
        raise SystemExit(f"verify {args.action} records the owner's decision: pass --by owner, and only when the "
                         "owner said so")
    if args.action == "open":
        target, msg = verification.open_local(root, project, rdir, args.subplan)
        print(msg)
        return 0 if target else 1
    if args.action == "close":
        print(verification.close_local(root, project, rdir, args.subplan))
    elif args.action == "revert-command":
        print(verification.revert_command(root, project, rdir, args.subplan) or "no revert range found")
    else:
        print(verification.decide(project, rdir, args.subplan, "approved" if args.action == "approve" else "rejected",
                                  args.note, "owner", via="conversation"))
    return 0
