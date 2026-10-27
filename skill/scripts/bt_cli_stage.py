"""Argument plumbing for staged execution (bt_stages, D-134): run, freeze, status."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from bt_core import find_req


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("stage", help="run approved subplans through the Scheduler while the plan is planned")
    parser.add_argument("action", choices=("run", "freeze", "status"),
                        help="run = approve the stage and have the Scheduler run it; freeze = approve only; status = list")
    parser.add_argument("req", help="REQ-NNN")
    parser.add_argument("subplans", nargs="?", default="", help="SP-1[,SP-2]: subplans to add to the approved stage")


def dispatch(args: argparse.Namespace, root: Path, project: str) -> int:
    import bt_stages
    rdir = find_req(root / project, args.req)
    if args.action == "status":
        print(json.dumps(bt_stages.info(rdir), indent=1, ensure_ascii=False))
        return 0
    add = [item.strip().upper() for item in args.subplans.split(",") if item.strip()]
    try:
        if args.action == "freeze":
            entry = bt_stages.freeze(project, rdir, add)
            print(f"etapa r{entry['revision']} aprobada: {', '.join(bt_stages.approved(rdir))}")
        else:
            print(bt_stages.run(project, rdir, add, by="owner", via="cli"))
    except bt_stages.StageError as exc:
        print(f"{exc.code}: {exc.message}")
        return 2
    from bt_vcs import commit
    commit(root, f"{project}: {args.req} stage {args.action} {','.join(add)} (cli)", push=False)
    return 0
