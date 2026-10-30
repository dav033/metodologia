"""A fake `claude` CLI for the durable-runtime tests (real process, real files, real git worktree).

Behaviour comes from `SCENARIO:<name>` in the prompt (the last argument). Every start appends one line to
$FAKE_COUNT, so a test can prove an attempt was launched exactly once even across engine crashes, and on which
account (its CLAUDE_CONFIG_DIR) it ran.
"""
from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

prompt = sys.argv[-1] if len(sys.argv) > 1 else ""
scenario = next((w.split(":", 1)[1].strip(".,;") for w in prompt.split() if w.startswith("SCENARIO:")), "ok")
found = re.search(r"## Task (\S+?):", prompt)
task_id = found.group(1) if found else ""
count = os.environ.get("FAKE_COUNT")
if count:
    with open(count, "a", encoding="utf-8") as stream:
        # `seen`: the task files already in the tree it started from (which line or candidate it was given)
        stream.write(json.dumps({"cwd": os.getcwd(), "scenario": scenario, "pid": os.getpid(), "task": task_id,
                                 "seen": sorted(p.name for p in Path(".").glob("*.task")), "at": time.time(),
                                 "remediation": "REMEDIATION" in prompt, "has_note": "Decisive lines" in prompt,
                                 "account": os.environ.get("CLAUDE_CONFIG_DIR", "")}) + "\n")


def done(text: str = "done") -> None:
    print(json.dumps({"type": "system", "subtype": "init"}), flush=True)
    print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": text,
                      "total_cost_usd": 0.001, "usage": {"input_tokens": 100, "output_tokens": 20}}), flush=True)
    sys.exit(0)


if scenario == "ok":
    Path("out.txt").write_text("good\n")
    time.sleep(float(os.environ.get("FAKE_DELAY", "0.2")))
    done()
elif scenario == "own":                         # leaves a file of its own, so each line's content is visible
    Path(f"{task_id}.task").write_text(f"{task_id}\n")
    Path("out.txt").write_text("good\n")
    time.sleep(float(os.environ.get("FAKE_OWN_DELAY", "0")))     # a window to restart the engine in (chaos test)
    done()
elif scenario == "append":                      # adds its line at the end of a shared file, like an npm script entry
    Path(f"{task_id}.task").write_text(f"{task_id}\n")
    Path("out.txt").write_text("good\n")
    with open("README.md", "a", encoding="utf-8") as handle:
        handle.write(f"{task_id} was here\n")
    done()
elif scenario == "needsowner":                  # right only when the owner's note says how (a retried round)
    Path(f"{task_id}.task").write_text(f"{task_id}\n")
    Path("out.txt").write_text("good\n" if "OWNER-RETRY" in prompt else "bad\n")
    done()
elif scenario == "fixk":                        # scenario K: the defect is fixed only by a coordinated repair
    Path(f"{task_id}.task").write_text(f"{task_id}\n")
    Path("out.txt").write_text("good\n")
    if "REMEDIATION" in prompt:
        Path("fixed-k.txt").write_text("F1 and F2 fixed together\n")
    done()
elif scenario in ("auditk", "auditnever"):       # a read-only audit: its report and findings ledger, nothing else
    fixed = scenario == "auditk" and Path("fixed-k.txt").exists()
    findings = [{"id": f"F{n}", "severity": "high", "summary": summary, "tasks": ["T1"],
                 **({"status": "fixed", "evidence": "$ test -f fixed-k.txt -> exit 0"} if fixed else
                    {"status": "open", "evidence": "$ test -f fixed-k.txt -> exit 1"})}
                for n, summary in ((1, "the session is not invalidated on logout"),
                                   (2, "the same session survives a password change"))]
    Path("docs").mkdir(exist_ok=True)
    Path(f"docs/{task_id}.md").write_text(f"# Audit {task_id}\n\n{'fixed' if fixed else 'two related defects'}\n")
    Path(f"docs/{task_id}.findings.json").write_text(json.dumps({"schema": "audit-findings/1", "findings": findings}))
    done()
elif scenario in ("auditself", "auditselfnever"):  # pictures REQ-021 T2.7: a coverage gap that names only the audit
    complete = scenario == "auditself" and "gap in the audit's own coverage" in prompt
    findings = [{"id": "F2", "severity": "low", "status": "open", "summary": "a spacing defect", "tasks": ["T1"]}]   # informational (D-233)
    if not complete:
        findings.append({"id": "F8", "severity": "high", "status": "open", "tasks": [task_id],
                         "summary": f"the audit lacks fresh evidence for the account route; {task_id} must be rerun",
                         "evidence": "capture harness failed on /cuenta"})
    Path("docs").mkdir(exist_ok=True)
    Path(f"docs/{task_id}.md").write_text(f"# Audit {task_id}\n\n{'complete' if complete else 'incomplete'}\n")
    Path(f"docs/{task_id}.findings.json").write_text(json.dumps({"schema": "audit-findings/1", "findings": findings}))
    done()
elif scenario == "fixlater":                  # wrong first, right when it continues from its own snapshot
    time.sleep(float(os.environ.get("FAKE_FIXLATER_DELAY", "0")))
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
elif scenario == "quotaonce":                   # the first start hits the provider limit, later ones work
    previous = [line for line in open(count, encoding="utf-8")] if count else []
    if sum(1 for line in previous if '"quotaonce"' in line) <= 1:
        reset = os.environ.get("FAKE_RESET", str(int(time.time()) + 3))
        print(json.dumps({"type": "result", "subtype": "error", "is_error": True,
                          "result": f"Claude AI usage limit reached|{reset}"}), flush=True)
        sys.exit(1)
    Path("out.txt").write_text("good\n")
    done()
elif scenario == "quota":
    reset = os.environ.get("FAKE_RESET", str(int(time.time()) + 3))
    print(json.dumps({"type": "result", "subtype": "error", "is_error": True,
                      "result": f"Claude AI usage limit reached|{reset}"}), flush=True)
    sys.exit(1)
else:
    print(f"unknown scenario {scenario}", flush=True)
    sys.exit(9)
