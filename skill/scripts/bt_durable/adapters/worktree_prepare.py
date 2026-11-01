"""An attempt worktree starts prepared exactly as the verifier prepares its clean copy before every check (D-273).

M6 runs each check in a fresh copy of the captured files after `sandbox_prepare`'s steps (workspace package builds,
`next typegen`), with the lockfile's dependencies installed. Those steps leave git-ignored files the checks then see
(`next-env.d.ts`, `.next/types/**`, `packages/*/dist`). A fresh worktree has none of them, so an agent's own run of a
check could pass where the verifier's fails (pictures REQ-021 r32 T3.91 a2-a4: `next-env.d.ts` brought Next's global
`ProcessEnv` into a full `tsc --noEmit`; three attempts were spent and the owner was asked).

So after the worktree is allocated and before the agent starts, the engine installs the lockfile with the verifier's
own arguments (`sandbox_provision.NPM_CI_ARGS`) and runs the steps the verifier's detection picks
(`sandbox_prepare.detect_steps`), bounded in time. Nothing here blocks a start: a failure or a timeout is reported in
the brief, which also names what ran. The result is kept in the attempt directory, so a retried `bt.prepare` step
writes the same brief without running anything again.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import signal
import subprocess
import time
from collections.abc import Mapping
from pathlib import Path

from bt_scheduler_quality import sandbox_prepare, sandbox_provision
from bt_scheduler_quality.policy import QualityPolicy
from bt_scheduler_quality.sandbox_mounts import COMPLETE, LOCKFILES, toolchain

from .files import atomic_write

LOG = logging.getLogger("bt_durable.worktree_prepare")
REPORT = "worktree-prepare.json"
OUTPUT = "worktree-prepare.log"
BUDGET_SECONDS = 900          # install and every step together; the verifier's own provisioning allows 600 for npm ci
TAIL_CHARS = 600


def prepare_worktree(worktree: Path, attempt_dir: Path, policy: QualityPolicy | None,
                     environ: Mapping[str, str], *, budget: float = BUDGET_SECONDS) -> str:
    """Install and prepare `worktree` as the verifier does; the brief's note about it ("" when nothing applies)."""
    report = attempt_dir / REPORT
    try:
        return str(json.loads(report.read_text(encoding="utf-8")).get("note", ""))
    except (OSError, ValueError, AttributeError):
        pass
    note, steps = _prepare(Path(worktree), attempt_dir, policy or QualityPolicy(), environ, budget)
    atomic_write(report, json.dumps({"note": note, "steps": steps}, sort_keys=True).encode(), 0o600)
    return note


def _prepare(worktree: Path, attempt_dir: Path, policy: QualityPolicy, environ: Mapping[str, str],
             budget: float) -> tuple[str, list[dict]]:
    lock = LOCKFILES["node_modules"]
    if not policy.toolchain or not (worktree / lock).is_file():
        return "", []              # without a lockfile the verifier installs nothing, so it runs no preparation either
    steps = sandbox_prepare.detect_steps(worktree)
    if not steps:
        return "", []
    env = _environment(policy, environ)
    deadline = time.monotonic() + budget
    log = attempt_dir / OUTPUT
    done: list[dict] = []
    commands: list[tuple[tuple[str, ...], str]] = []          # (argv, how the brief names it)
    if not (worktree / "node_modules" / COMPLETE["node_modules"]).is_file():
        npm = shutil.which("npm", path=env.get("PATH"))
        commands.append(((npm or "npm", *sandbox_provision.NPM_CI_ARGS), " ".join(("npm", *sandbox_provision.NPM_CI_ARGS))))
    commands.extend((step, " ".join(step)) for step in steps)
    before = _untracked(worktree)
    for argv, command in commands:
        result = _run(argv, command, worktree, env, deadline, log)
        done.append(result)
        if result["status"] != "ok":
            break
    left = sorted(_untracked(worktree) - before)
    return _note(done, steps, log) + _captured_note(left), done


def _untracked(worktree: Path) -> set[str]:
    """Untracked files git does not ignore: what `handoff.capture` would take into the attempt's snapshot."""
    try:
        listing = subprocess.run(["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"], cwd=worktree,
                                 capture_output=True, timeout=60, check=False).stdout
    except (OSError, subprocess.SubprocessError):
        return set()
    return {entry[3:].decode("utf-8", "replace") for entry in listing.split(b"\0") if entry.startswith(b"?? ")}


def _captured_note(paths: list[str]) -> str:
    """A repository that does not ignore what its preparation generates would get those files captured as the agent's."""
    if not paths:
        return ""
    shown = ", ".join(f"`{path}`" for path in paths[:10]) + (f" and {len(paths) - 10} more" if len(paths) > 10 else "")
    return (f" The preparation left files this repository does not git-ignore ({shown}): they become part of your "
            "captured work unless you delete them.")


def _environment(policy: QualityPolicy, environ: Mapping[str, str]) -> dict[str, str]:
    """What the verifier's checks get, on the host: its toolchain (Node first on PATH, NODE_OPTIONS), the owner's
    ambient variables for names not already set and the policy's explicit ones, which win (as in the sandbox)."""
    tools = toolchain(policy)
    env = {name: environ[name] for name in sandbox_provision.KEPT_ENV if name in environ}
    env["PATH"] = os.pathsep.join((*tools.path, environ.get("PATH", "/usr/bin:/bin")))
    explicit = dict(policy.environment)
    env.update((k, v) for k, v in tools.environment if k not in explicit)
    for name, value in policy.ambient_environment:
        env.setdefault(name, value)
    env.update(explicit)
    env["npm_config_update_notifier"] = "false"
    return env


def _run(argv: tuple[str, ...], command: str, cwd: Path, env: dict[str, str], deadline: float, log: Path) -> dict:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return {"command": command, "status": "timeout", "exit": None, "seconds": 0, "tail": ""}
    started = time.monotonic()
    with open(log, "ab") as output:
        output.write(f"$ {command}\n".encode())
        output.flush()
        try:
            process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=output,
                                       stderr=subprocess.STDOUT, start_new_session=True)
        except OSError as error:
            return {"command": command, "status": "failed", "exit": None, "seconds": 0, "tail": type(error).__name__}
        try:
            code = process.wait(timeout=remaining)
            status = "ok" if code == 0 else "failed"
        except subprocess.TimeoutExpired:
            _kill(process)
            code, status = None, "timeout"
    seconds = round(time.monotonic() - started, 1)
    if status != "ok":
        LOG.warning("worktree preparation `%s` %s (exit %s) in %s", command, status, code, cwd)
    return {"command": command, "status": status, "exit": code, "seconds": seconds,
            "tail": _tail(log) if status != "ok" else ""}


def _kill(process: subprocess.Popen) -> None:
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=5)
            return
        except subprocess.TimeoutExpired:
            continue


def _tail(log: Path) -> str:
    try:
        with open(log, "rb") as stream:
            stream.seek(max(0, stream.seek(0, os.SEEK_END) - TAIL_CHARS * 2))
            text = stream.read().decode("utf-8", "replace")
    except OSError:
        return ""
    return text.strip()[-TAIL_CHARS:]


def _note(done: list[dict], steps: tuple[tuple[str, ...], ...], log: Path) -> str:
    ran = " then ".join(f"`{item['command']}`" for item in done)
    outputs = ", ".join(dict.fromkeys(filter(None, map(sandbox_prepare.generated_by, steps))))
    mirror = ("This mirrors the verifier, which prepares its clean copy of your final files the same way before every "
              f"check; their git-ignored output ({outputs}) is part of what the checks see.")
    failed = next((item for item in done if item["status"] != "ok"), None)
    if failed is None:
        return (f"Worktree prepared before you started: {ran} ran here. {mirror} Run the checks in this worktree as it "
                "is, and rerun those steps after you change a workspace package, the routes or the dependencies.")
    how = "timed out" if failed["status"] == "timeout" else f"failed (exit {failed['exit']})"
    attempted = {item["command"] for item in done}
    skipped = [" ".join(step) for step in steps if " ".join(step) not in attempted]
    rest = f" Not run after it: {', '.join(f'`{s}`' for s in skipped)}." if skipped else ""
    return (f"Worktree preparation before you started: {ran}; `{failed['command']}` {how}.{rest} {mirror} The verifier "
            "runs the same steps before every check, so a check will fail the same way unless your change fixes the "
            f"cause; full output in {log}. Last lines:\n```\n{failed['tail']}\n```")
