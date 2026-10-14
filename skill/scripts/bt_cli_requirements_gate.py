"""CLI adapter for the versioned requirements gate; no approval inference."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import bt_requirements_gate as gate
from bt_core import find_req


def add_parser(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("requirements-gate", help="record/check requirements-v1 revalidation")
    parser.add_argument("action", choices=["record", "check"])
    parser.add_argument("req", help="REQ-NNN")
    parser.add_argument("--review", type=Path, help="record: JSON review with explicit approval evidence")


def dispatch(args: argparse.Namespace, root: Path, project: str) -> int:
    rdir = find_req(root / project, args.req)
    try:
        if args.action == "record":
            if args.review is None:
                raise ValueError("record needs --review <JSON file>")
            if args.review.stat().st_size > gate.MAX_BYTES:
                raise ValueError("Review file exceeds 65536 bytes")
            gate.record(rdir, json.loads(args.review.read_text(encoding="utf-8")))
        result = gate.check(rdir)
    except (OSError, ValueError, TypeError, UnicodeError) as exc:
        raise SystemExit(f"INVALID_REQUIREMENTS_REVIEW: {type(exc).__name__}") from exc
    # CLI diagnostics never emit the full reviewed scope or approval conversation.
    print(json.dumps({key: result[key] for key in ("status", "reasons")}))
    return 2 if result["status"] == "needs_revalidation" else 0
