"""Monitor a run and recover the ready-task starvation while a decision stays open."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import bt_core
import bt_scheduler_adapter as adapter
import bt_scheduler_decisions as decisions
import bt_scheduler_monitor_repairs as repairs
import bt_scheduler_ops as ops


def ready_signature(status: dict, state: dict) -> str | None:
    if status.get("hold") or status.get("owner_pids") or status.get("live_attempts") or not status.get("open_decisions"):
        return None
    ready = sorted((task, len(state.get("tasks", {}).get(task, {}).get("attempts", [])))
                   for task, value in status.get("task_states", {}).items() if value == "ready")
    if not ready:
        return None
    return hashlib.sha256(json.dumps([status.get("revision"), ready], separators=(",", ":")).encode()).hexdigest()


def start_once(project: str, req: str, rdir: Path) -> str:
    status = ops.status(project, req, rdir)
    repaired = repairs.repair_once(project, req, rdir, status)
    if repaired:
        return repaired
    signature = ready_signature(status, decisions._state(rdir))
    if signature is None:
        states = status.get("task_states", {})
        focus = ", ".join(f"{task}={state}" for task, state in sorted(states.items())
                          if state in {"ready", "active", "blocked"})
        return f"monitoring: {focus or 'no ready, active or blocked tasks'}; decisions={len(status.get('open_decisions', []))}"
    marker = adapter.run_db_path(rdir).with_suffix(".ready-monitor.json")
    try:
        saved = json.loads(marker.read_text(encoding="utf-8"))
    except FileNotFoundError:
        saved = {}
    if saved.get("signature") == signature:
        return "already attempted"
    unit = f"metodologia-ready-owner-{project}-{req}-{signature[:12]}"
    command = ["systemd-run", "--user", "--collect", f"--unit={unit}", "--property=Type=exec",
               f"--setenv=PATH={os.environ.get('PATH', '/usr/bin:/bin')}", f"--setenv=BITACORA_ROOT={bt_core.ROOT}",
               sys.executable, str(Path(__file__).with_name("bitacora.py")), "--project", project,
               "scheduler-run", req, "--resume"]
    subprocess.run(command, check=True, capture_output=True, text=True, timeout=20)
    fd, name = tempfile.mkstemp(prefix=".ready-monitor-", dir=marker.parent)
    with os.fdopen(fd, "w", encoding="utf-8") as out:
        json.dump({"signature": signature, "unit": unit}, out)
        out.flush()
        os.fsync(out.fileno())
    os.replace(name, marker)
    return f"started owner {unit}"


def main() -> None:
    project, req = sys.argv[1:3]
    rdir = bt_core.find_req(bt_core.ROOT / project, req).resolve()
    previous = ""
    while True:
        try:
            message = start_once(project, req, rdir)
        except Exception as exc:  # noqa: BLE001 - keep monitoring; every failure is visible in the journal
            message = f"error: {type(exc).__name__}: {exc}"
        if message != previous:
            print(message, flush=True)
            previous = message
        time.sleep(20)


if __name__ == "__main__":
    main()
