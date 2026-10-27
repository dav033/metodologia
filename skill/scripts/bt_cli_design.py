"""Argument plumbing for owner approval of UI design contracts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import bt_design_approval as approval
from bt_core import find_req


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("design", help="planning-time design drafts and approval of UI design contracts")
    parser.add_argument("action", choices=("list", "show", "approve", "changes", "draft", "drafts", "feedback", "sync", "choose", "iterate", "amend"))
    parser.add_argument("req", help="REQ-NNN")
    parser.add_argument("contract", nargs="?", help="<contract>@vN")
    parser.add_argument("--comments", default="")
    parser.add_argument("--force", action="store_true", help="draft: redo the design even when it is current")
    parser.add_argument("--fresh", action="store_true", help="compose from requirements, preserving previous revisions "
                        "(the only way to regenerate directions over a chosen design)")
    parser.add_argument("--directions", type=int, choices=range(1, 4), default=3, help="number of creative directions (1–3)")
    parser.add_argument("--direction", help="direction id to choose, iterate or comment on")
    translate = subparsers.add_parser("translate", help="translate SPEC, PLAN and design drafts to Spanish")
    translate.add_argument("req", help="REQ-NNN")
    translate.add_argument("--status", action="store_true", help="only report what is pending")


def dispatch(args: argparse.Namespace, root: Path, project: str) -> int:
    rdir = find_req(root / project, args.req)
    if args.cmd == "translate":
        return _translate(args, project, rdir)
    if args.action in ("draft", "drafts", "feedback", "sync", "choose", "iterate", "amend"):
        return _drafts(args, project, rdir)
    rows = approval.ui_contracts(rdir, project)
    if args.action in ("list", "show"):
        selected = [row for row in rows if args.action == "show" and
                    (args.contract is None or row["contract"] == args.contract)]
        if args.action == "list":
            selected = [row for row in rows if row["design_state"] == "completed" and
                        (not row["approval"] or row["approval"].get("status") != "approved")]
        if args.action == "show" and args.contract and not selected:
            raise SystemExit(f"No UI design contract {args.contract} in {args.req}")
        if args.action == "show":
            for row in selected:
                repo = approval.repository_for_contract(root, project, rdir, row["contract"])
                revision = approval.revision_for_contract(root, project, rdir, row["contract"], repo) if repo else "HEAD"
                snapshot = approval.contract_snapshot(repo, row["path"], revision) if repo else None
                row["revision"] = revision
                row["text"], row["sha256"] = snapshot if snapshot else (None, None)
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


def _drafts(args: argparse.Namespace, project: str, rdir: Path) -> int:
    """Planning-time Designer: start drafts, list them, send owner feedback, or follow plan changes."""
    import bt_design_drafts as drafts
    refs = [args.contract] if args.contract else None
    if args.action == "draft":
        started = drafts.request(project, rdir, refs, force=args.force, fresh=args.fresh,
                                 directions=args.directions, reason="requested")
        print(f"Designer started for: {', '.join(started)}" if started else "Nothing to draft: every design is current, "
              "in progress or approved (use --force to redo one).")
    elif args.action == "choose":
        import bt_design_directions
        print(bt_design_directions.choose(project, rdir, args.contract or "", args.direction or "", "cli"))
    elif args.action == "iterate":
        import bt_design_iterate
        if not args.contract or not args.direction or not args.comments.strip():
            raise SystemExit("design iterate needs <contract>@vN, --direction and --comments")
        print(bt_design_iterate.iterate(project, rdir, args.contract, args.direction, args.comments, "cli"))
    elif args.action == "amend":
        import bt_design_amend
        if not args.contract:
            raise SystemExit("design amend needs <contract>@vN")
        try:
            print(bt_design_amend.start(project, rdir, args.contract, args.comments, "cli"))
        except SystemExit as exc:
            print(exc)
            return 1
    elif args.action == "feedback":
        if not args.contract or not args.comments.strip():
            raise SystemExit("design feedback needs <contract>@vN and --comments")
        print(drafts.add_feedback(project, rdir, args.contract, args.comments, "cli", direction=args.direction))
    elif args.action == "sync":
        import bt_translate
        started = drafts.sync(project, rdir)
        translating = bt_translate.ensure(project, rdir)
        print(f"Designer: {', '.join(started) or 'nothing to redo'} · translation: "
              f"{'started' if translating else 'current or waiting'}")
    else:
        keep = ("id", "ref", "status", "stale", "pending_feedback", "summary", "questions", "error", "delegation")
        print(json.dumps([{k: row.get(k) for k in keep} for row in drafts.rows(rdir)], indent=1, ensure_ascii=False))
    return 0


def _translate(args: argparse.Namespace, project: str, rdir: Path) -> int:
    import os
    import time

    import bt_translate
    if args.status:
        print(json.dumps(bt_translate.status(rdir)))
        return 0
    lock = bt_translate._lock(rdir)
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(json.dumps({"pid": os.getpid(), "at": time.time()}), encoding="utf-8")
    try:
        result = bt_translate.translate(project, rdir)
    finally:
        lock.unlink(missing_ok=True)
    print(json.dumps(result))
    return 1 if result["failed"] and not result["translated"] else 0
