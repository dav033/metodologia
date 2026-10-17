"""Entry point for the hash-pinned Planner benchmark store."""
from __future__ import annotations

from plan_bench.cli import main as _main


def main() -> int:
    return _main()

if __name__ == "__main__":
    raise SystemExit(main())
