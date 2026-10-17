"""Headless, read-only operator interface for an M4 monitor store."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections.abc import Sequence

from . import queries
from .store import StoreError


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="bt-scheduler-monitor")
    commands = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    for name in ("status", "events", "incidents", "metrics", "activity"):
        command = commands.add_parser(name)
        command.add_argument("--store", required=True, help="path to the M4 monitor SQLite database")
        if name != "status":
            command.add_argument("--limit", type=int, default=50)
        if name in ("events", "activity"):
            command.add_argument("--execution-id")
        if name == "incidents":
            command.add_argument("--state", choices=("open", "resolved"))
    return parser


def _emit(value: object, stream: object | None = None) -> None:
    destination = sys.stdout if stream is None else stream
    destination.write(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        if args.command == "status":
            result = queries.status(args.store)
        elif args.command == "events":
            result = queries.events(args.store, limit=args.limit, execution_id=args.execution_id)
        elif args.command == "incidents":
            result = queries.incidents(args.store, limit=args.limit, resolution_state=args.state)
        elif args.command == "activity":
            result = queries.activity(args.store, limit=args.limit, execution_id=args.execution_id)
        else:
            result = queries.metrics(args.store, limit=args.limit)
        _emit(result)
        return 0
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2
    except json.JSONDecodeError:
        _emit({"error": "monitor store is corrupt", "code": "M4_STORE_ERROR"}, sys.stderr)
        return 3
    except ValueError:
        _emit({"error": "invalid query arguments", "code": "M4_INVALID_ARGUMENT"}, sys.stderr)
        return 2
    except (sqlite3.Error, StoreError, OSError, RuntimeError):
        _emit({"error": "monitor store unavailable", "code": "M4_STORE_ERROR"}, sys.stderr)
        return 3


__all__ = ["main"]
