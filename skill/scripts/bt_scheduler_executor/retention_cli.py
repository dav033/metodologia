"""Operator-authorized three-day M3 worktree retention; preview unless --apply is explicit."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from .retention import retain_run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="executor roots directory")
    parser.add_argument("--apply", action="store_true", help="remove verified expired copies")
    args = parser.parse_args()
    if args.root.is_symlink() or not args.root.is_dir():
        parser.error("root must be an existing real directory")
    results = []
    for run in sorted(args.root.iterdir()):
        if run.is_dir():
            for result in retain_run(run, apply=args.apply):
                print(json.dumps(result, ensure_ascii=False), flush=True)
                results.append(result)
    print(json.dumps({"summary": dict(Counter(r["action"] for r in results)),
                      "reasons": dict(Counter(r.get("reason", "") for r in results if r.get("reason")))}), flush=True)
    return int(any(r["action"] == "error" for r in results))


if __name__ == "__main__":
    raise SystemExit(main())
