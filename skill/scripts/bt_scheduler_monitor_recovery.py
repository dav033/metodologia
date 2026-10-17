"""Operator CLI for offline M4 archive verification and candidate preparation."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections.abc import Sequence
from datetime import datetime

from bt_scheduler_monitor_adapter import (
    RecoveryError,
    StoreError,
    export_archive,
    prepare_candidate,
    verify_archive,
    verify_candidate,
)


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="bt-scheduler-monitor-recovery")
    commands = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)

    archive = commands.add_parser("archive", help="export a full, no-overwrite M4 archive")
    archive.add_argument("--store", required=True)
    archive.add_argument("--archive", required=True)
    archive.add_argument("--manifest", required=True)
    archive.add_argument("--max-store-bytes", type=int)

    verify = commands.add_parser("verify-archive", help="verify archive hash, integrity, schema and manifest")
    verify.add_argument("--archive", required=True)
    verify.add_argument("--manifest", required=True)

    prepare = commands.add_parser("prepare-candidate", help="build a bounded candidate from a verified archive")
    prepare.add_argument("--archive", required=True)
    prepare.add_argument("--archive-manifest", required=True)
    prepare.add_argument("--candidate", required=True)
    prepare.add_argument("--candidate-manifest", required=True)
    prepare.add_argument("--sqlite-temp-dir", action="append", required=True,
                         help="each caller-owned SQLite temporary directory; repeat for the complete list")
    prepare.add_argument("--max-store-bytes", type=int)
    prepare.add_argument("--now", help="optional timezone-qualified ISO-8601 retention timestamp")

    verify_candidate_parser = commands.add_parser("verify-candidate", help="verify a recovery candidate")
    verify_candidate_parser.add_argument("--candidate", required=True)
    verify_candidate_parser.add_argument("--manifest", required=True)
    return parser


def _emit(value: object, stream: object | None = None) -> None:
    destination = sys.stdout if stream is None else stream
    destination.write(json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n")


def _timestamp(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError as exc:
        raise ValueError("--now must be a timezone-qualified ISO-8601 timestamp") from exc


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        if args.command == "archive":
            options = {} if args.max_store_bytes is None else {"max_store_bytes": args.max_store_bytes}
            result = export_archive(args.store, args.archive, args.manifest, **options)
        elif args.command == "verify-archive":
            result = verify_archive(args.archive, args.manifest)
        elif args.command == "prepare-candidate":
            options = {} if args.max_store_bytes is None else {"max_store_bytes": args.max_store_bytes}
            result = prepare_candidate(args.archive, args.archive_manifest, args.candidate,
                                       args.candidate_manifest, sqlite_temp_dirs=args.sqlite_temp_dir,
                                       now=_timestamp(args.now), **options)
        else:
            result = verify_candidate(args.candidate, args.manifest)
        _emit(result)
        return 0
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2
    except ValueError as exc:
        _emit({"ok": False, "code": "M4_RECOVERY_INVALID_ARGUMENT", "error": str(exc)}, sys.stderr)
        return 2
    except (RecoveryError, StoreError, OSError, sqlite3.Error) as exc:
        _emit({"ok": False, "code": "M4_RECOVERY_FAILED", "error": str(exc)}, sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
