"""Command line for validating and reporting frozen Planner benchmark records."""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from .contract import BenchmarkError, load_rubric
from .report import build_report, score_store
from .verify import verify_store


def _write(root: Path, name: str, value: dict[str, Any]) -> None:
    root_path = root.resolve(strict=True)
    target = root_path / name
    if target.is_symlink() or target.parent != root_path:
        raise BenchmarkError("STORE_WRITE_REFUSED", f"refusing unsafe output path {name!r}")
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    descriptor, temporary = tempfile.mkstemp(prefix=f".{name}.", suffix=".tmp", dir=root_path)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    except OSError as exc:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise BenchmarkError("STORE_WRITE_FAILED", f"cannot write {name!r}") from exc


def _render(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    verify = commands.add_parser("verify", help="validate manifest, scheduled cells, then optional blind reviews")
    verify.add_argument("store", type=Path)
    verify.add_argument("--reviews", action="store_true")
    score = commands.add_parser("score", help="summarize deterministic observed metrics without imputation")
    score.add_argument("store", type=Path)
    report = commands.add_parser("report", help="publish observed and judged metrics without an overall score")
    report.add_argument("store", type=Path)
    commands.add_parser("rubric", help="print the hash-pinned v1 review rubric")
    args = parser.parse_args(argv)
    try:
        if args.action == "verify":
            result = verify_store(args.store, reviews=args.reviews)
            output = {"ok": True, "manifest_sha256": result["manifest_sha256"],
                      "cells": [{"cell_id": item["cell_id"], "status": item["meta"]["status"]}
                                for item in result["cells"]],
                      "reviews_verified": len(result["reviews"])}
        elif args.action == "score":
            output = score_store(args.store)
            _write(args.store, "observed-summary.json", output)
        elif args.action == "report":
            output = build_report(args.store)
            if "overall_score" in output or "aggregate_score" in output or "overall_superiority" in output:
                raise BenchmarkError("REPORT_AGGREGATE_REFUSED", "overall scores and superiority claims are prohibited")
            _write(args.store, "report.json", output)
        else:
            output = load_rubric()
        sys.stdout.write(_render(output))
        return 0
    except BenchmarkError as exc:
        print(f"ERROR {exc.code}: {exc.message}", file=sys.stderr)
        return 2


def main() -> int:
    return run()
