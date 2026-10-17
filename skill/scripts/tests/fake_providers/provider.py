"""A fake provider CLI for the executor integration tests: argv[1] is which binary it pretends to be.

It records how it was invoked (argv, cwd, selected environment) to $FAKE_RECORD and behaves according to
`SCENARIO:<name>` found in the prompt (claude/agy: last argument; codex: stdin), writing outputs in each provider's real
shape so the methodology's own drivers parse them (stream-json result for claude, `event: result` for agy, plain text for codex).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

name, args = sys.argv[1], sys.argv[2:]
stdin_text = "" if sys.stdin.isatty() else sys.stdin.read() if name == "codex" else ""
prompt = stdin_text if name == "codex" else (args[-1] if args else "")
if name == "agy":
    prompt = next((a[len("--print="):] for a in args if a.startswith("--print=")), prompt)
scenario = (re.search(r"SCENARIO:(\w+)", prompt) or [None, "ok"])[1]
watch = ("CLAUDE_CONFIG_DIR", "CODEX_HOME", "OTHER_SECRET", "FAKE_MARK")
record = os.environ.get("FAKE_RECORD")
if record:
    with open(record, "a") as stream:
        stream.write(json.dumps({"provider": name, "argv": [a[:60] for a in args], "cwd": os.getcwd(),
                                 "env": {k: os.environ.get(k) for k in watch}, "scenario": scenario,
                                 "stdin_bytes": len(stdin_text)}) + "\n")


def git(*a):
    subprocess.run(["git", "-c", "user.name=Fake", "-c", "user.email=f@f", *a], check=True, capture_output=True)


def success():
    if name == "claude":
        if scenario == "monitor":
            print('{"type":}', flush=True)  # Invalid provider JSON must become a digest-only M4 gap.
        print(json.dumps({"type": "system", "subtype": "init"}), flush=True)
        print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": "done",
                          "total_cost_usd": 0.0123, "usage": {"input_tokens": 10, "output_tokens": 5}}), flush=True)
    elif name == "agy":
        print(json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": "done",
                                                         "usage": {"total_tokens": 99}}}), flush=True)
    else:
        print("codex working...\ntokens used\n1,234", flush=True)
    sys.exit(0)


def failure(kind):
    if kind == "quota":
        if name == "claude":
            print(json.dumps({"type": "result", "subtype": "error", "is_error": True,
                              "result": "Claude AI usage limit reached|1900000000"}), flush=True)
        elif name == "agy":
            print(json.dumps({"event": "result", "result": {"status": "FAILED",
                                                             "error": "RESOURCE_EXHAUSTED: quota exceeded"}}), flush=True)
        else:
            print("You've hit your usage limit. Try again at Oct 13th, 2026 1:08 AM.", flush=True)
        sys.exit(1)
    if kind == "net":
        print("Error: request failed: read ECONNRESET", flush=True)
        sys.exit(1)
    print("Traceback: boom", flush=True)
    sys.exit(3)


if scenario in ("ok", "commit", "dirty", "monitor"):
    Path(f"{name}-made.txt").write_text(f"made by {name}\n")
    if scenario == "commit":
        git("add", "-A")
        git("commit", "-m", f"{name} commit")
    elif scenario == "dirty":
        Path("README.md").write_text("changed by agent\n")
    time.sleep(float(os.environ.get("FAKE_DELAY", "0.1")))
    success()
elif scenario == "recover":
    marker = Path("partial-progress.txt")
    if not marker.exists():
        marker.write_text("preserved partial work\n")
        failure("net")
    if marker.read_text() != "preserved partial work\n":
        raise SystemExit("partial work was corrupted")
    Path("recovered.txt").write_text("continued from preserved snapshot\n")
    success()
elif scenario in ("quota", "net", "crash"):
    Path(f"{name}-half.txt").write_text("half\n")
    failure(scenario)
elif scenario == "sleep":
    Path(f"{name}-started.txt").write_text("started\n")
    time.sleep(120)
    success()
elif scenario == "partial":
    Path(f"{name}-p.txt").write_text("p\n")
    print("stopped without an end-of-turn event", flush=True)
    sys.exit(0 if name != "claude" else 0)
else:
    print("unknown scenario", flush=True)
    sys.exit(9)
