"""Diagnostics: `python -m bt_supervisor [--state-dir D] [--backend B] [--unit-prefix P] list [prefix] | show <key> |
stop <key> [--grace S]`. Output is JSON. The state dir comes from --state-dir or $BT_SUPERVISOR_STATE_DIR."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .api import make_supervisor
from .errors import SupervisorError


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m bt_supervisor", description=__doc__.split("\n")[0])
    parser.add_argument("--state-dir", default=os.environ.get("BT_SUPERVISOR_STATE_DIR"),
                        help="supervisor state directory (default: $BT_SUPERVISOR_STATE_DIR)")
    parser.add_argument("--backend", choices=("auto", "systemd", "pgroup"), default="auto")
    parser.add_argument("--unit-prefix", default="bt-att-")
    sub = parser.add_subparsers(dest="command", required=True)
    listing = sub.add_parser("list", help="attempts that still exist")
    listing.add_argument("prefix", nargs="?", default="")
    show = sub.add_parser("show", help="observe one attempt")
    show.add_argument("key")
    stop = sub.add_parser("stop", help="terminate one attempt")
    stop.add_argument("key")
    stop.add_argument("--grace", type=float, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.state_dir:
        print("error: pass --state-dir or set BT_SUPERVISOR_STATE_DIR", file=sys.stderr)
        return 2
    try:
        supervisor = make_supervisor(Path(args.state_dir), args.backend, unit_prefix=args.unit_prefix)
        if args.command == "list":
            payload = [item.model_dump(mode="json") for item in supervisor.list_attempts(args.prefix)]
        elif args.command == "show":
            payload = supervisor.observe(args.key).model_dump(mode="json")
        else:
            payload = supervisor.terminate(args.key, grace=args.grace).model_dump(mode="json")
    except SupervisorError as error:
        print(json.dumps({"error": error.code, "message": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps({"backend": supervisor.backend, "result": payload}, indent=2, sort_keys=True))
    return 0
