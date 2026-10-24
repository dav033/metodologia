"""CLI integration for the isolated knowledge store."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bt_knowledge


def add_parser(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("knowledge", help="ingest, query, export or inspect the project knowledge map")
    actions = parser.add_subparsers(dest="knowledge_action", required=True)
    put = actions.add_parser("ingest", help="validate and merge one knowledge-delta/1 report")
    put.add_argument("delta", help="JSON file, or - for stdin")
    put.add_argument("--repo-path", help="local repository used to verify commit-bound evidence")
    put.add_argument("--json", action="store_true")
    read = actions.add_parser("query", help="query relations and their revision validity")
    read.add_argument("--commit")
    read.add_argument("--area", help="evidence path prefix or entity-id prefix")
    read.add_argument("--status", help="filter by status/validity label")
    read.add_argument("--repo-path", help="local repository used to check unchanged evidence")
    read.add_argument("--json", action="store_true")
    exp = actions.add_parser("export", help="generate a human-readable view")
    exp.add_argument("--format", required=True, choices=("md", "mermaid", "json"))
    exp.add_argument("--commit")
    st = actions.add_parser("stats", help="count stored relations, evidence and history")
    st.add_argument("--json", action="store_true")


def dispatch(args: argparse.Namespace, project: str, root: Path) -> int:
    db_path = root / ".state" / "knowledge" / f"{project}.db"
    try:
        action = args.knowledge_action
        if action == "ingest":
            raw = sys.stdin.read() if args.delta == "-" else Path(args.delta).read_text(encoding="utf-8")
            result = bt_knowledge.ingest(db_path, json.loads(raw), args.repo_path)
            _print(result, args.json)
        elif action == "query":
            result = bt_knowledge.query(db_path, project, commit=args.commit, area=args.area, status=args.status,
                                        repo_path=args.repo_path)
            _print(result, args.json)
        elif action == "export":
            print(bt_knowledge.export(db_path, project, args.format, commit=args.commit))
        else:
            _print(bt_knowledge.stats(db_path, project), args.json)
        return 0
    except (bt_knowledge.KnowledgeError, json.JSONDecodeError, OSError) as exc:
        if isinstance(exc, bt_knowledge.KnowledgeError):
            print(str(exc), file=sys.stderr)
        elif isinstance(exc, json.JSONDecodeError):
            print("INVALID_JSON: delta is not valid JSON", file=sys.stderr)
        else:
            print("INPUT_ERROR: could not read delta input", file=sys.stderr)
        return 2


def _print(value: object, compact: bool) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":") if compact else None))
