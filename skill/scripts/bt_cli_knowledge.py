"""CLI integration for the isolated knowledge store."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bt_knowledge_adapter as adapter


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
    claims = actions.add_parser("claims", help="ingest and retrieve external research claims")
    claim_actions = claims.add_subparsers(dest="claims_action", required=True)
    put_claims = claim_actions.add_parser("ingest", help="validate and merge one research-claims/1 report")
    put_claims.add_argument("document", help="JSON file, or - for stdin")
    put_claims.add_argument("--json", action="store_true")
    query = claim_actions.add_parser("query", help="query external claims and freshness status")
    query.add_argument("--topic")
    query.add_argument("--kind", choices=("package_version", "api_behavior", "price", "license", "changelog",
                                           "security_advisory", "docs", "other"))
    query.add_argument("--facts-only", action="store_true")
    query.add_argument("--json", action="store_true")
    dossier = claim_actions.add_parser("dossier", help="render a bounded subplan research dossier")
    dossier.add_argument("--subplan", required=True)
    dossier.add_argument("--max-bytes", type=int, default=12000)
    invalidate = claim_actions.add_parser("invalidate", help="mark matching research claims stale")
    invalidate.add_argument("--topic", required=True)
    invalidate.add_argument("--kind", choices=("package_version", "api_behavior", "price", "license", "changelog",
                                                 "security_advisory", "docs", "other"))
    invalidate.add_argument("--reason", required=True)
    claim_stats = claim_actions.add_parser("stats", help="count external claims, evidence and history")
    claim_stats.add_argument("--json", action="store_true")


def dispatch(args: argparse.Namespace, project: str, root: Path) -> int:
    db_path = root / ".state" / "knowledge" / f"{project}.db"
    external_db_path = root / ".state" / "knowledge" / f"{project}.external.db"
    try:
        action = args.knowledge_action
        if action == "claims":
            claim_action = args.claims_action
            if claim_action == "ingest":
                raw = sys.stdin.read() if args.document == "-" else Path(args.document).read_text(encoding="utf-8")
                result = adapter.ingest_claims(external_db_path, json.loads(raw))
                _print(result, args.json)
            elif claim_action == "query":
                _print(adapter.query_claims(external_db_path, project, topic=args.topic, kind=args.kind,
                                            facts_only=args.facts_only), args.json)
            elif claim_action == "dossier":
                print(adapter.claims_dossier(external_db_path, project, args.subplan, max_bytes=args.max_bytes), end="")
            elif claim_action == "invalidate":
                _print(adapter.invalidate_claims(external_db_path, project, args.topic, args.reason, kind=args.kind),
                       True)
            else:
                _print(adapter.claims_stats(external_db_path, project), args.json)
            return 0
        if action == "ingest":
            raw = sys.stdin.read() if args.delta == "-" else Path(args.delta).read_text(encoding="utf-8")
            result = adapter.ingest(db_path, json.loads(raw), args.repo_path)
            _print(result, args.json)
        elif action == "query":
            result = adapter.query(db_path, project, commit=args.commit, area=args.area, status=args.status,
                                   repo_path=args.repo_path)
            _print(result, args.json)
        elif action == "export":
            print(adapter.export(db_path, project, args.format, commit=args.commit))
        else:
            _print(adapter.stats(db_path, project), args.json)
        return 0
    except (adapter.KnowledgeError, json.JSONDecodeError, OSError) as exc:
        if isinstance(exc, adapter.KnowledgeError):
            print(str(exc), file=sys.stderr)
        elif isinstance(exc, json.JSONDecodeError):
            print("INVALID_JSON: delta is not valid JSON", file=sys.stderr)
        else:
            print("INPUT_ERROR: could not read delta input", file=sys.stderr)
        return 2


def _print(value: object, compact: bool) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":") if compact else None))
