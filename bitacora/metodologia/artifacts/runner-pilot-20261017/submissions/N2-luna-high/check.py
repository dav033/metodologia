import json
import sys
import time
from pathlib import Path

mode = sys.argv[1]
started = time.monotonic()
events = Path(".runner-events.jsonl")
def record(value):
    with events.open("a") as stream:
        stream.write(json.dumps(value) + "\n")
record({"mode": mode, "event": "start", "at": started})
lines, code = [], 0
if mode == "success":
    lines = ["12 tests passed", "WARNING: deprecated option legacy_mode at config/options.py:18"]
elif mode == "misleading":
    lines, code = ["PASS: preflight only", "FAILED test_balance — AssertionError: expected 120, got 90 — tests/test_balance.py:42"], 3
elif mode == "repeated":
    lines = ["FAILED test_cache — AssertionError: stale cache — tests/test_cache.py:27"] * 14
    lines += ["FAILED test_auth — PermissionError: forbidden — tests/test_auth.py:61"]
    code = 1
elif mode == "long":
    lines = [f"INFO build step {i:04d}: processing deterministic asset bundle" for i in range(1800)]
    lines[847] = "ERROR TS2322: string is not assignable to number — src/price.ts:87"
    lines += ["INFO cleanup completed"]
    code = 1
elif mode == "hang":
    print("Waiting for worker; no completion yet", flush=True)
    time.sleep(60)
elif mode == "upstream":
    lines, code = ["ERROR: corrupt archive — build/archive.py:19"], 7
elif mode == "downstream":
    lines = ["5 tests passed"]
elif mode == "unavailable":
    lines, code = ["BLOCKED: missing declared dependency runner_optional_sdk; do not install packages"], 4
else:
    raise SystemExit(64)
Path("logs").mkdir(exist_ok=True)
body = "\n".join(lines) + "\n"
Path("logs/" + mode + ".log").write_text(body)
print(body, end="", flush=True)
record({"mode": mode, "event": "end", "exit": code, "seconds": time.monotonic() - started})
raise SystemExit(code)
