"""Read-only recovery inspection on the existing Bitacora CLI."""
from __future__ import annotations

import argparse
import json

import bt_scheduler_recovery_adapter as recovery


def register(subparsers):
    parser = subparsers.add_parser("recovery", help="consultar decisiones de recuperación M5")
    parser.add_argument("action", choices=("inspect", "metrics"))
    parser.add_argument("--store", required=True, help="historial M5 de esta ejecución")
    parser.add_argument("--json", action="store_true")


def dispatch(args):
    try:
        result = recovery.inspect_store(args.store, metrics=args.action == "metrics")
    except ValueError as error:
        code = getattr(error, "code", "INVALID_INPUT")
        print(json.dumps({"error": code}) if args.json else f"M5: {code}")
        return 2
    if args.json:
        print(json.dumps(result, sort_keys=True, allow_nan=False))
    elif result is None:
        print("Sin decisiones de recuperación.")
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    register(sub)
    return dispatch(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
