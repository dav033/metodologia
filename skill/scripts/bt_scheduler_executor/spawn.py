"""Preparing and spawning: brief, worktree, prompt, launch through the driver, the detached shim, and what to do when
any step after the spawn fails (an agent nobody tracks must never be left running)."""
from __future__ import annotations

import dataclasses
import json
import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Any

from . import artifacts, procinfo
from . import model as m
from .errors import ExecutorError
from .model import Route, StartRequest, Workspace
from .prompt import build_prompt


class SpawnMixin:
    # ================================================================================================ prepare + spawn
    def _launch_job(self, attempt_id: str) -> None:
        try:
            self._launch(attempt_id)
        except Exception as error:
            self._log(f"launch crashed for {attempt_id}: {type(error).__name__}: {error}")
            self._fail_start(attempt_id, f"internal error: {type(error).__name__}")
        finally:
            with self._guard:
                self._starting.discard(attempt_id)
            self._wake.set()

    def _launch(self, attempt_id: str) -> None:
        row = self.ledger.get(attempt_id)
        if row is None or row["state"] not in (m.QUEUED, m.PREPARING):
            return
        if row["state"] == m.QUEUED and not self.ledger.transition(attempt_id, m.PREPARING, expect=(m.QUEUED,)):
            return          # a cancel (or another worker) took it first
        request = StartRequest.from_dict(row["request"])
        if row.get("base_sha"):                    # the base was pinned when the order was accepted
            request = dataclasses.replace(request, base_ref=row["base_sha"])
        route = Route.from_dict(row["route"])
        adir = self.attempts_dir / row["dirname"]
        if self._cancelled(attempt_id):
            return self._settle(attempt_id, {"reason": "cancelled", "returncode": None})
        try:
            brief = self._guard_port(lambda: self.briefs.brief(request))
            ws = self._guard_port(lambda: self.workspaces.allocate(request))
            if any(o["attempt_id"] != attempt_id and (o.get("workspace") or {}).get("path") == ws.path
                   for o in self.ledger.in_states(m.LIVE)):
                raise ExecutorError("WORKSPACE_ERROR", "the workspace manager returned a directory another live attempt uses")
            self.ledger.update(attempt_id, expect=(m.PREPARING,), workspace=ws.to_dict())
            artifacts.write_json(adir / "brief.json", {
                "task_id": request.task_id, "title": brief.title, "objective": brief.objective,
                "acceptance_criteria": list(brief.acceptance_criteria), "verification": list(brief.verification),
                "expected_paths": list(brief.expected_paths), "notes": brief.notes})
            if self._cancelled(attempt_id):
                return self._settle(attempt_id, {"reason": "cancelled", "returncode": None})
            timeout = min(request.timeout_seconds or self.cfg.timeout_seconds, self.cfg.max_timeout_seconds)
            prompt = build_prompt(brief, request, workdir=ws.path, branch=ws.branch,
                                  report_path=str(adir / "report.json"))
            artifacts.atomic_write(adir / "prompt.txt", prompt.encode("utf-8"), 0o600)
            launch = self._guard_port(lambda: self.driver.prepare(route, prompt, ws, timeout))
            shim = self._spawn(attempt_id, adir, launch, ws, timeout)
        except ExecutorError as error:
            return self._settle(attempt_id, {"reason": "start_failed", "returncode": None,
                                             "error": f"{error.code}: {error.detail}"})
        except OSError as error:              # the artefact directory became unusable
            return self._settle(attempt_id, {"reason": "start_failed", "returncode": None,
                                             "error": f"ARTIFACT_ERROR: {type(error).__name__}"})
        event = self._event(row, m.EV_STARTED, "started", {
            "provider": route.provider, "model": route.model, "profile": route.profile, "effort": route.effort,
            "route": route.reference, "worktree": ws.path, "branch": ws.branch, "base_sha": ws.base_sha,
            "shim_pid": shim["pid"], "artifacts": artifacts.paths(adir)})
        try:
            moved = self.ledger.transition(attempt_id, m.RUNNING, expect=(m.PREPARING,), event=event, shim=shim,
                                           started_at=self.clock())
        except ExecutorError:
            self._abort_spawn(adir)                # the ledger could not record it: do not leave an untracked agent
            raise
        if not moved:
            return          # lost a race with a cancel that already moved it to settling
        self._wake.set()

    def _cancelled(self, attempt_id: str) -> bool:
        row = self.ledger.get(attempt_id)
        return bool(row and row["cancel_requested"])

    def _child_env(self, launch) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items() if k not in launch.env_remove}
        env.update(dict(launch.env_set))
        return env

    def _spawn(self, attempt_id: str, adir: Path, launch, ws: Workspace, timeout: float) -> dict[str, Any]:
        """Start the shim detached and wait for its identity record. Leftovers of a crashed earlier spawn are removed
        first: this point is only reached when recovery found no live process for the attempt."""
        for leftover in ("exit.json", "shim.json", "output.log", "output.tail", "spec.json", "abort"):
            try:
                (adir / leftover).unlink()
            except FileNotFoundError:
                pass
        spec = {"attempt_id": attempt_id, "argv": list(launch.argv), "stdin": launch.stdin, "cwd": ws.path,
                "timeout_seconds": timeout, "grace_seconds": self.cfg.grace_seconds,
                "head_bytes": self.cfg.output_head_bytes, "tail_bytes": self.cfg.output_tail_bytes}
        artifacts.atomic_write(adir / "spec.json", json.dumps(spec).encode("utf-8"), 0o600)
        try:
            proc = subprocess.Popen([self.python, str(self.shim_path), str(adir)], cwd=str(adir), env=self._child_env(launch),
                                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                    start_new_session=True, close_fds=True)
        except OSError as error:
            raise ExecutorError("START_FAILED", f"cannot start the supervising shim: {type(error).__name__}") from None
        old = self._procs.get(attempt_id)
        if old is not None:
            old.poll()                                  # reap an earlier launcher of this attempt before replacing it
        self._procs[attempt_id] = proc
        deadline = time.monotonic() + self.cfg.spawn_wait_seconds
        while time.monotonic() < deadline:
            info = artifacts.read_shim(adir / "shim.json")
            if info.get("ident"):
                return {"pid": info["pid"], "ident": info["ident"], "pgid": info.get("pgid", info["pid"])}
            if proc.poll() not in (None, 0):
                raise ExecutorError("START_FAILED", f"shim launcher exited with {proc.returncode}")
            time.sleep(0.01)
        self._abort_spawn(adir)                    # a slow shim must not start an agent nobody is tracking
        raise ExecutorError("START_FAILED", "the shim did not identify itself in time")

    def _abort_spawn(self, adir: Path) -> None:
        """Stop whatever a failed spawn may have left: tell a late shim not to start the agent, and stop one that did."""
        try:
            artifacts.atomic_write(adir / "abort", b"abort\n")
        except ExecutorError:
            pass
        info = artifacts.read_shim(adir / "shim.json")
        if info.get("pid") and procinfo.alive(info.get("pid"), info.get("ident")):
            procinfo.signal_pid(info["pid"], signal.SIGTERM)
        self._kill_child(info)

    def _fail_start(self, attempt_id: str, detail: str) -> None:
        row = self.ledger.get(attempt_id)
        if row is not None:                        # an unexpected error after the spawn must not leave an untracked agent
            self._abort_spawn(self.attempts_dir / row["dirname"])
        try:
            self._settle(attempt_id, {"reason": "start_failed", "returncode": None, "error": detail})
        except Exception as error:
            self._log(f"cannot settle failed start of {attempt_id}: {type(error).__name__}")

