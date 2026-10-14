"""Argument plumbing for `bitacora.py plan-json ...`; the work is done by the planner module through the adapter."""
from __future__ import annotations

import argparse
from pathlib import Path

import bt_plan_adapter as adapter
from bt_core import find_req


def add_parser(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("plan-json", help="planner module: derive a PLAN.json skeleton, validate, freeze an approved "
                                              "revision, or report compatibility of a legacy plan (bt_planner)")
    parser.add_argument("action", choices=["init", "check", "freeze", "show", "compat"])
    parser.add_argument("req", help="REQ-NNN")
    parser.add_argument("--force", action="store_true", help="init: overwrite an existing PLAN.json")
    parser.add_argument("--json", action="store_true", help="check: machine-readable output")


def dispatch(args: argparse.Namespace, root: Path, project: str) -> int:
    return adapter.run_cli(args.action, find_req(root / project, args.req), force=args.force, as_json=args.json)
