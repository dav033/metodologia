"""Standalone command line for the package."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import KnowledgeError, benchmark, export, ingest, query, stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    put = commands.add_parser("ingest")
    put.add_argument("delta")
    put.add_argument("--repo-path")
    put.add_argument("--json", action="store_true")
    read = commands.add_parser("query")
    read.add_argument("project")
    read.add_argument("--commit")
    read.add_argument("--area")
    read.add_argument("--status")
    read.add_argument("--repo-path")
    read.add_argument("--json", action="store_true")
    exp = commands.add_parser("export")
    exp.add_argument("project")
    exp.add_argument("--format", required=True, choices=("md", "mermaid", "json"))
    exp.add_argument("--commit")
    st = commands.add_parser("stats")
    st.add_argument("project")
    args = parser.parse_args()
    try:
        if args.command == "ingest":
            raw = sys.stdin.read() if args.delta == "-" else Path(args.delta).read_text(encoding="utf-8")
            result = ingest(args.db, json.loads(raw), args.repo_path)
        elif args.command == "query":
            result = query(args.db, args.project, commit=args.commit, area=args.area, status=args.status, repo_path=args.repo_path)
        elif args.command == "export":
            print(export(args.db, args.project, args.format, commit=args.commit))
            return 0
        else:
            result = stats(args.db, args.project)
        print(json.dumps(result, ensure_ascii=False, indent=None if getattr(args, "json", False) else 2, sort_keys=True))
        return 0
    except (KnowledgeError, json.JSONDecodeError, OSError) as exc:
        if isinstance(exc, KnowledgeError):
            print(str(exc), file=sys.stderr)
        elif isinstance(exc, json.JSONDecodeError):
            print("INVALID_JSON: delta is not valid JSON", file=sys.stderr)
        else:
            print("INPUT_ERROR: could not read delta input", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
