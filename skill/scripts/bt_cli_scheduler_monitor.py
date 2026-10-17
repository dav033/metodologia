"""Read-only SSH command for querying the methodology M4 monitor adapter."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections.abc import Sequence
from json import JSONDecodeError

from bt_scheduler_monitor_adapter import operator_query


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
        result = operator_query(args.command, args.store, limit=getattr(args, "limit", 50),
                                execution_id=getattr(args, "execution_id", None),
                                state=getattr(args, "state", None))
        _emit(result)
        return 0
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2
    except JSONDecodeError:
        _emit({"error": "monitor store is corrupt", "code": "M4_STORE_ERROR"}, sys.stderr)
        return 3
    except ValueError:
        _emit({"error": "invalid query arguments", "code": "M4_INVALID_ARGUMENT"}, sys.stderr)
        return 2
    except (sqlite3.Error, OSError, RuntimeError):
        _emit({"error": "monitor store unavailable", "code": "M4_STORE_ERROR"}, sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
