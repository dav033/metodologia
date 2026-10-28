"""A fake `claude` CLI for the durable-runtime tests (real process, real files, real git worktree).

Behaviour comes from `SCENARIO:<name>` in the prompt (the last argument). Every start appends one line to
$FAKE_COUNT, so a test can prove an attempt was launched exactly once even across engine crashes.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

prompt = sys.argv[-1] if len(sys.argv) > 1 else ""
scenario = next((w.split(":", 1)[1].strip(".,;") for w in prompt.split() if w.startswith("SCENARIO:")), "ok")
count = os.environ.get("FAKE_COUNT")
if count:
    with open(count, "a", encoding="utf-8") as stream:
        stream.write(json.dumps({"cwd": os.getcwd(), "scenario": scenario, "pid": os.getpid(),
                                 "remediation": "REMEDIATION" in prompt, "has_note": "Decisive lines" in prompt}) + "\n")


def done(text: str = "done") -> None:
    print(json.dumps({"type": "system", "subtype": "init"}), flush=True)
    print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": text,
                      "total_cost_usd": 0.001, "usage": {"input_tokens": 100, "output_tokens": 20}}), flush=True)
    sys.exit(0)


if scenario == "ok":
    Path("out.txt").write_text("good\n")
    time.sleep(float(os.environ.get("FAKE_DELAY", "0.2")))
    done()
elif scenario == "fixlater":                    # wrong first, right when it continues from its own snapshot
    if Path("attempt-marker.txt").exists():
        Path("out.txt").write_text("good\n")
    else:
        Path("attempt-marker.txt").write_text("first attempt\n")
        Path("out.txt").write_text("bad\n")
    done()
elif scenario == "neverfix":
    Path("out.txt").write_text(f"bad {time.time()}\n")
    done()
elif scenario == "slow":                        # keeps writing until killed (cancellation / crash tests)
    Path("out.txt").write_text("good\n")
    with open("heartbeat.txt", "a", encoding="utf-8") as beat:
        for _ in range(int(float(os.environ.get("FAKE_SLOW_SECONDS", "8")) / 0.1)):
            beat.write(f"{time.time()}\n")
            beat.flush()
            time.sleep(0.1)
    done()
elif scenario == "escape":                      # a setsid grandchild that ignores SIGTERM and keeps writing
    child = ("import os,signal,time\nsignal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
             "f=open('escaped.txt','a')\nwhile True:\n f.write(str(time.time())+'\\n'); f.flush(); time.sleep(0.05)\n")
    subprocess.Popen([sys.executable, "-c", child], start_new_session=True)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    time.sleep(600)
elif scenario == "quota":
    reset = os.environ.get("FAKE_RESET", str(int(time.time()) + 3))
    print(json.dumps({"type": "result", "subtype": "error", "is_error": True,
                      "result": f"Claude AI usage limit reached|{reset}"}), flush=True)
    sys.exit(1)
else:
    print(f"unknown scenario {scenario}", flush=True)
    sys.exit(9)
