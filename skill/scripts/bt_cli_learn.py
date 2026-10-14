"""CLI boundary for learning creation, review and scope filtering."""
from __future__ import annotations

import sys

import bt_config
import bt_learn
from bt_core import ROOT


def register(sub) -> None:
    parser = sub.add_parser("learn", help="evidence-backed project, owner and skill learnings")
    parser.add_argument("action", choices=["add", "list", "confirm", "reject", "brief"])
    parser.add_argument("target", nargs="?", help="add: sentence; confirm/reject: learning ID")
    parser.add_argument("--evidence", default="", help="add: observed evidence (required)")
    parser.add_argument("--source", default="", help="independent observation source, e.g. REQ-006/T3")
    parser.add_argument("--scope", choices=bt_learn.SCOPES)
    parser.add_argument("--kind", choices=bt_learn.KINDS, default="convention")
    parser.add_argument("--status", choices=bt_learn.STATUSES)
    parser.add_argument("--reason", default="", help="reject: why")


def dispatch(args, project: str | None) -> None:
    scope = args.scope or "project"
    if args.action in ("confirm", "reject") and bt_learn.scope_of_id(args.target or "") is None and scope == "project":
        scope = "owner"
    scope_project = project if scope == "project" else None
    if args.action in ("add", "confirm", "reject") and scope == "project" and not project:
        sys.exit("No project resolved; pass --project <name> or --scope owner.")
    if args.action == "add":
        item = bt_learn.add(scope_project, args.target or "", args.evidence, args.source, scope, args.kind,
                            bt_config.get("learn.promote_after", 3))
        state = "ignored (the owner rejected it before)" if item.get("ignored") else item["status"]
        suffix = "" if item["created"] else " — merged into an existing learning"
        print(f"{item['id']} {state} ({item['sightings']} sighting(s)){suffix}")
    elif args.action in ("confirm", "reject"):
        item = (bt_learn.confirm(scope_project, args.target or "", scope) if args.action == "confirm" else
                bt_learn.reject(scope_project, args.target or "", scope, args.reason))
        print(f"{item['id']} {item['status']}: {item['text']}")
    elif args.action == "brief":
        print(bt_learn.brief(project, bt_config.get("learn.inject_max", 12)) or "(nothing learned yet)")
    else:
        for item in bt_learn.listing(project, args.scope, args.status):
            print(f"{item['id']} [{item['scope']} · {item['kind']} · {item['status']} · {item['sightings']}x] {item['text']}")
    if args.action in ("add", "confirm", "reject"):
        from bt_vcs import commit
        commit(ROOT, f"{project or 'owner'}: learning {args.action}")
