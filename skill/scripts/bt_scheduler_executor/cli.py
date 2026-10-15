"""Command line: read-only inspection of an executor root, and a provider-free self-test.

    python -m bt_scheduler_executor status   --root DIR [--json]
    python -m bt_scheduler_executor show     --root DIR ATTEMPT [--json]
    python -m bt_scheduler_executor events   --root DIR [--undelivered] [--json]
    python -m bt_scheduler_executor selftest [--keep DIR] [--json]

Exit 0 ok, 2 refused/failed. `status`/`show`/`events` never write; they open the ledger read-only in effect (no executor
is started, no process touched).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .config import Config
from .errors import ExecutorError
from .executor import AgentExecutor
from .ledger import Ledger
from .model import LIVE, TERMINAL, Route, StartRequest
from .simulators import ListSink, ScriptedDriver, StaticBriefs, StaticResolver
from .workspace import GitWorkspaces


def _ledger(root: str) -> Ledger:
    path = Path(root) / "ledger.db"
    if not path.exists():
        raise ExecutorError("LEDGER_ERROR", f"no ledger at {path}")
    return Ledger(path)


def _emit(value: Any, as_json: bool, lines: list[str]) -> None:
    print(json.dumps(value, indent=1, sort_keys=True) if as_json else "\n".join(lines))


def cmd_status(args) -> int:
    led = _ledger(args.root)
    rows = [led.get(i) for i in led.all_ids()]
    data = [{"attempt_id": r["attempt_id"], "task_id": r["request"]["task_id"], "state": r["state"],
             "cause": (r.get("outcome") or {}).get("cause", ""), "cancel_requested": r["cancel_requested"]} for r in rows]
    live = sum(1 for r in rows if r["state"] in LIVE)
    _emit({"attempts": data, "live": live, "terminal": sum(1 for r in rows if r["state"] in TERMINAL),
           "undelivered_events": led.undelivered()}, args.json,
          [f"{d['attempt_id']:<14} {d['task_id']:<10} {d['state']:<10} {d['cause']}" for d in data]
          + [f"live={live} undelivered_events={led.undelivered()}"])
    return 0


def cmd_show(args) -> int:
    row = _ledger(args.root).get(args.attempt)
    if row is None:
        print(f"no such attempt: {args.attempt}", file=sys.stderr)
        return 2
    keep = {k: row.get(k) for k in ("attempt_id", "state", "route", "workspace", "outcome", "handoff", "rejection",
                                    "cancel_requested", "cancel_reason")}
    _emit(keep, True, [])
    return 0


def cmd_events(args) -> int:
    rows = [e for e in _ledger(args.root).events() if not args.undelivered or not e["delivered"]]
    _emit(rows, args.json, [f"{e['seq']:>4} {e['event_id']:<28} delivered={e['delivered']}" for e in rows])
    return 0


def cmd_selftest(args) -> int:
    """Two attempts through the real executor with a scripted driver on a throw-away git repository."""
    work = Path(args.keep) if args.keep else Path(tempfile.mkdtemp(prefix="m3-selftest-"))
    repo = work / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    for cmd in (["git", "init", "-q", "-b", "main"], ["git", "-c", "user.name=t", "-c", "user.email=t@t",
                                                       "commit", "-q", "--allow-empty", "-m", "init"]):
        subprocess.run(cmd, cwd=repo, check=True, capture_output=True)
    routes = {"ok": Route("scripted", "ok", reference="ok"), "bad": Route("scripted", "bad", reference="bad")}
    driver = ScriptedDriver({"ok": [sys.executable, "-c", "open('made.txt','w').write('x'); print('done')"],
                             "bad": [sys.executable, "-c", "import sys; open('half.txt','w').write('x'); sys.exit(3)"]})
    sink = ListSink()
    x = AgentExecutor(work / "root", resolver=StaticResolver(routes), briefs=StaticBriefs(), driver=driver,
                      workspaces=GitWorkspaces(work / "root" / "ws", {"main": repo}), sink=sink,
                      config=Config(poll_seconds=0.05, grace_seconds=1, timeout_seconds=60))
    try:
        for n, ref in ((1, "ok"), (2, "bad")):
            x.start(StartRequest(f"k{n}", "SELFTEST", 1, f"T{n}", f"att-{n}", n, ref, "main"))
        done = x.wait_idle(60)
        result = {"idle": done, "root": str(work / "root"),
                  "attempts": {a: {"state": x.ledger.get(a)["state"], "cause": x.ledger.get(a)["outcome"]["cause"],
                                   "handoff": x.ledger.get(a)["handoff"]["status"]} for a in ("att-1", "att-2")},
                  "events": [e.event_id for e in sink.events]}
    finally:
        x.close()
    good = (result["idle"] and result["attempts"]["att-1"]["state"] == "finished"
            and result["attempts"]["att-2"]["cause"] == "agent_error"
            and all(a["handoff"] == "captured" for a in result["attempts"].values()))
    result["ok"] = bool(good)
    _emit(result, args.json, [f"{k}: {v}" for k, v in result.items()])
    return 0 if good else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m bt_scheduler_executor", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="action", required=True)
    for name, fn in (("status", cmd_status), ("events", cmd_events)):
        p = sub.add_parser(name)
        p.add_argument("--root", required=True)
        p.add_argument("--json", action="store_true")
        if name == "events":
            p.add_argument("--undelivered", action="store_true")
        p.set_defaults(fn=fn)
    p = sub.add_parser("show")
    p.add_argument("--root", required=True)
    p.add_argument("attempt")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_show)
    p = sub.add_parser("selftest")
    p.add_argument("--keep")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_selftest)
    args = parser.parse_args(argv)
    try:
        return args.fn(args)
    except ExecutorError as error:
        print(str(error), file=sys.stderr)
        return 2
