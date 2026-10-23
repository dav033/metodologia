"""Read-only operational inspection: python -m bt_scheduler_recovery."""
from __future__ import annotations

import argparse
import json

from .history import inspect_store
from .validation import RecoveryError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect M5 recovery decisions without changing scheduler state")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("inspect", "metrics"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("--store", required=True)
        command_parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = inspect_store(args.store, metrics=args.command == "metrics")
    except RecoveryError as error:
        print(json.dumps({"error": error.code}) if args.json else "M5: " + error.code)
        return 2
    if args.json:
        print(json.dumps(result, sort_keys=True, allow_nan=False))
    elif result is None:
        print("No recovery decisions")
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
