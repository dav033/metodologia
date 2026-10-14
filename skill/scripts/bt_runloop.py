"""Bounded supervisor iteration retries, independent from task scheduling."""
from __future__ import annotations

import sys
import time
from collections.abc import Callable
from pathlib import Path

from bt_runutil import backoff_override, notify

MAX_ERRORS = 10


def run_loop(project: str, rdir: Path, state: dict, ctx: dict,
             step: Callable[[str, Path, dict], int | None], reset: Callable[[Path], None]) -> int:
    errors = 0
    while True:
        try:
            code = step(project, rdir, ctx)
            errors = 0
        except Exception as exc:  # noqa: BLE001 — preserve bounded recovery; SystemExit reaches caller.
            errors += 1
            print(f"[run] iteration failed ({errors}/{MAX_ERRORS}): {exc!r}", file=sys.stderr, flush=True)
            reset(rdir)
            if errors == 1 or errors >= MAX_ERRORS:
                notify(f"{project} {state['req']}: marathon " + ("gave up" if errors >= MAX_ERRORS else "error"),
                       repr(exc)[:200])
            if errors >= MAX_ERRORS:
                return 3
            time.sleep(1 if backoff_override() is not None else min(30 * errors, 300))
            continue
        if code is not None:
            return code
