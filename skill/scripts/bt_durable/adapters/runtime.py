"""Runtime port over bt_supervisor: systemd user units on cgroup v2 (or the process-group fallback).

The attempt key is the unit identity, so `launch` from a re-run step adopts the unit the first run started. The
agent environment comes from the attempt's 0600 JSON file (secrets never reach a command line or a checkpoint).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from bt_contracts.execution import AttemptRef, Prepared, ProcessRecord
from bt_supervisor.api import make_supervisor
from bt_supervisor.errors import TerminationUncertain
from bt_supervisor.model import LaunchSpec, Limits, Observation

LOG = logging.getLogger("bt_durable.runtime")


def _record(obs: Observation) -> ProcessRecord:
    ident = obs.identity
    return ProcessRecord(backend=ident.backend, unit=ident.unit, invocation_id=ident.invocation_id, state=obs.state,
                         exit_code=obs.exit_code, result=obs.result, oom_killed=obs.oom_killed,
                         live_pids=tuple(obs.live_pids),
                         started_at=obs.started_at, ended_at=obs.ended_at, log_path=obs.log_path)


class SupervisorRuntime:
    def __init__(self, state_dir: Path, *, backend: str = "auto", unit_prefix: str | None = None):
        kwargs = {"backend": backend}
        if unit_prefix is not None:
            kwargs["unit_prefix"] = unit_prefix
        self.supervisor = make_supervisor(Path(state_dir), **kwargs)

    def launch(self, attempt: AttemptRef, prepared: Prepared, limits: dict) -> ProcessRecord:
        env = json.loads(prepared.env_file.read_text(encoding="utf-8"))
        env["BT_ATTEMPT_WORKFLOW"] = attempt.workflow_id
        spec = LaunchSpec(attempt_key=attempt.attempt_key, argv=list(prepared.argv), cwd=prepared.worktree, env=env,
                          log_dir=prepared.attempt_dir,
                          stdin_text=prepared.stdin_path.read_text(encoding="utf-8") if prepared.stdin_path else None,
                          limits=Limits(memory_max_bytes=limits.get("memory_max_bytes"),
                                        tasks_max=limits.get("tasks_max"),
                                        cpu_quota_percent=limits.get("cpu_quota_percent"),
                                        runtime_max_seconds=limits.get("runtime_max_seconds") or prepared.timeout_seconds))
        self.supervisor.launch(spec)
        return _record(self.supervisor.observe(attempt.attempt_key))

    def observe(self, attempt: AttemptRef) -> ProcessRecord:
        return _record(self.supervisor.observe(attempt.attempt_key))

    def terminate(self, attempt: AttemptRef) -> ProcessRecord:
        return _record(self.supervisor.terminate(attempt.attempt_key))

    def release(self, attempt: AttemptRef) -> None:
        try:
            self.supervisor.release(attempt.attempt_key)
        except TerminationUncertain:
            raise
        except Exception as error:  # noqa: BLE001 - an already released attempt is fine
            LOG.debug("release %s: %s", attempt.attempt_key, error)

    def owned(self, prefix: str) -> list[str]:
        return [i.attempt_key for i in self.supervisor.list_attempts(prefix)]
