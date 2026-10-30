"""Runtime port over bt_supervisor: systemd user units on cgroup v2 (or the process-group fallback).

The attempt key is the unit identity, so `launch` from a re-run step adopts the unit the first run started. The
agent environment comes from the attempt's 0600 JSON file (secrets never reach a command line or a checkpoint).
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from bt_contracts.execution import AttemptRef, Prepared, ProcessRecord
from bt_supervisor.api import make_supervisor
from bt_supervisor.errors import TerminationUncertain
from bt_supervisor.model import LaunchSpec, Limits, Observation

LOG = logging.getLogger("bt_durable.runtime")
# how long an `unknown` observation is looked at again before it counts. The supervisor answers `unknown` when the user
# manager does not answer (`systemctl --user show` failed or timed out), and the agent workflow terminates whatever is
# not `running`: one unanswered call under load killed a healthy agent and launched it again (audit of REQ-030,
# 2026-10-29: test_durable_postgres ['slow', 'slow', 'ok']; test_durable_observe_hiccup). A real `unknown` (a foreign
# unit, a launch still in flight) is still `unknown` after the grace and is handled as before.
UNKNOWN_GRACE_SECONDS = 30.0


def _record(obs: Observation) -> ProcessRecord:
    ident = obs.identity
    return ProcessRecord(backend=ident.backend, unit=ident.unit, invocation_id=ident.invocation_id, state=obs.state,
                         exit_code=obs.exit_code, result=obs.result, oom_killed=obs.oom_killed,
                         live_pids=tuple(obs.live_pids),
                         started_at=obs.started_at, ended_at=obs.ended_at, log_path=obs.log_path)


class SupervisorRuntime:
    def __init__(self, state_dir: Path, *, backend: str = "auto", unit_prefix: str | None = None,
                 unknown_grace: float = UNKNOWN_GRACE_SECONDS, sleep=time.sleep):
        self.unknown_grace, self._sleep = unknown_grace, sleep
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
        return self.observe(attempt)

    def observe(self, attempt: AttemptRef) -> ProcessRecord:
        obs = self.supervisor.observe(attempt.attempt_key)
        waited, delay = 0.0, 0.5
        while obs.state == "unknown" and waited < self.unknown_grace:
            self._sleep(delay)
            waited += delay
            delay = min(delay * 2, 5.0)
            obs = self.supervisor.observe(attempt.attempt_key)
        if waited:
            LOG.info("%s: observation unknown for %.1f s, now %s", attempt.attempt_key, waited, obs.state)
        return _record(obs)

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
