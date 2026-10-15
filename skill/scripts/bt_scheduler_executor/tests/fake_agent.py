"""A scripted stand-in for a provider CLI. argv[1] = scenario. Runs in the attempt's worktree (cwd)."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

scenario = sys.argv[1] if len(sys.argv) > 1 else "ok"
arg = sys.argv[2] if len(sys.argv) > 2 else ""
here = Path.cwd()


def git(*a):
    subprocess.run(["git", "-c", "user.name=Fake", "-c", "user.email=f@f", *a], check=True, capture_output=True)


def finish(code=0):
    print("TERMINAL-EVENT: done", flush=True)
    sys.exit(code)


if scenario == "ok":
    Path("result.txt").write_text("hello\n")
    print("working...", flush=True)
    finish()
elif scenario == "commit":
    Path("feature.txt").write_text("committed work\n")
    git("add", "-A")
    git("commit", "-m", "agent commit")
    finish()
elif scenario == "dirty":                      # modifies a tracked file + creates an untracked one, no commit
    Path("README.md").write_text("changed by agent\n")
    Path("untracked.txt").write_text("new\n")
    finish()
elif scenario == "both":                       # one commit, then more uncommitted work
    Path("a.txt").write_text("a\n")
    git("add", "-A")
    git("commit", "-m", "first")
    Path("b.txt").write_text("b\n")
    Path("README.md").write_text("edited after commit\n")
    finish()
elif scenario == "nothing":
    finish()
elif scenario == "special":                    # deletion, binary, spaces in the name
    os.remove("README.md")
    Path("with space.txt").write_text("x\n")
    Path("blob.bin").write_bytes(bytes(range(256)) * 4)
    finish()
elif scenario == "quota":
    Path("partial.txt").write_text("half done\n")
    reset = arg or "4102444800"
    print(f'{{"type":"result","is_error":true,"result":"usage limit reached|{reset}"}}', flush=True)
    sys.exit(1)
elif scenario == "net":
    Path("partial.txt").write_text("half done\n")
    print("Error: request failed: read ECONNRESET", flush=True)
    sys.exit(1)
elif scenario == "nettext":                    # prints connection words but succeeds
    print("fixing the ECONNRESET handler in the client", flush=True)
    finish()
elif scenario == "crash":
    Path("partial.txt").write_text("x\n")
    print("Traceback: boom", flush=True)
    sys.exit(3)
elif scenario == "partial":                    # exits 0 without the end-of-turn marker
    Path("p.txt").write_text("x\n")
    print("I stopped", flush=True)
    sys.exit(0)
elif scenario == "sleep":
    Path("started.txt").write_text("started\n")
    print("sleeping", flush=True)
    time.sleep(float(arg or 60))
    finish()
elif scenario == "stubborn":                   # ignores SIGTERM
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    Path("started.txt").write_text("started\n")
    print("ignoring term", flush=True)
    time.sleep(float(arg or 60))
    finish()
elif scenario == "grandchild":                 # leaves a background process in its group
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
    Path("grandchild.pid").write_text(str(child.pid))
    Path("started.txt").write_text("started\n")
    time.sleep(float(arg or 60))
    finish()
elif scenario == "big":
    n = int(arg or 3_000_000)
    chunk = ("x" * 99 + "\n")
    sent = 0
    while sent < n:
        sys.stdout.write(chunk * 100)
        sent += len(chunk) * 100
    sys.stdout.flush()
    print("THE-END-MARKER", flush=True)
    finish()
elif scenario == "once":                       # records every run in the (per-attempt) worktree: >1 line = a second writer
    with open("runs.txt", "a") as stream:
        stream.write(f"run pid={os.getpid()}\n")
    time.sleep(float(arg or 0.8))
    Path("work.txt").write_text("work\n")
    finish()
elif scenario == "marker":                     # prove isolation: print and write its own unique marker
    Path("marker.txt").write_text(arg + "\n")
    print("MARKER=" + arg, flush=True)
    time.sleep(0.2)
    finish()
elif scenario == "env":                        # report selected environment variables
    keys = arg.split(",")
    Path("env.txt").write_text("\n".join(f"{k}={os.environ.get(k, '<unset>')}" for k in keys))
    finish()
else:
    print("unknown scenario", flush=True)
    sys.exit(9)
