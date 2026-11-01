"""The agent test environment probed before an attempt starts (D-265; the `EnvProbe` port, step `bt.env_probe`).

pictures REQ-021 r32 T3.91: the owner's agent env file named a database port nothing listened on (stale since two days),
while the verifier's copy of the same key reached the live tunnel. Attempts a5..a7 could not run their DB-backed check,
said so, and the runtime retried and healing guessed until max_attempts. The origin is closed in `bt_verifier_env.
one_source` (the checks' value wins for every key both define); this probe is the net for a resource that is down for
everyone (a stopped tunnel): before an agent starts, each network URL among the attempt's variables that the task's
checks need is opened with a short TCP connect. An unreachable one stops the task with an environment decision for the
owner instead of an attempt. Values never leave this module: only key names, `host:port` and the database name.
"""
from __future__ import annotations

import logging
import socket
import time
from collections.abc import Callable
from pathlib import Path

from .briefs import requirement_dir
from .m3 import agent_environment, agent_inherited_env, agent_test_env

LOG = logging.getLogger("bt_durable.agent_env")
PROBE_TIMEOUT = 2.0
CACHE_SECONDS = 30.0            # a reachable resource is not opened again for this long within a run
CODE = "AGENT_ENV_UNREACHABLE"


def connect(host: str, port: int, timeout: float) -> str:
    """'' when a TCP connection to host:port opens within `timeout`, else why not (no value, no credentials)."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return ""
    except ConnectionRefusedError:
        return "connection refused"
    except socket.timeout:
        return f"no answer within {timeout:g} s"
    except socket.gaierror:
        return "host name not resolved"
    except OSError as error:
        return (error.strerror or type(error).__name__).lower()


def required_names(task) -> list[str]:
    """Variable names the task's checks declare in `requires` (a `service:` probe is not a variable)."""
    names: list[str] = []
    for check in getattr(task, "verification", ()) or ():
        if isinstance(check, dict):
            names += [r for r in check.get("requires") or () if isinstance(r, str) and not r.startswith("service:")]
    return list(dict.fromkeys(names))


class AgentEnvProbe:
    """`check(run, plan, task_id)` -> {} when there is nothing to report, else {"state": "unreachable" | "ok",
    "unreachable": [{"key", "resource", "host", "port", "error", "source"}], "divergent": [...], "env_file"}.

    Probed: the variables the task's checks `require` (whatever source the attempt gets them from), or, for a task that
    declares none, every variable the attempt gets from the owner's agent env file or the verifier's explicit settings.
    A divergence (`one_source`) is reported once per process to telemetry and the run's activity."""

    def __init__(self, *, check_policy_for: Callable[[object], object] | None = None,
                 test_env_for: Callable[[str], dict] = agent_test_env, env_file_for: Callable[[str], str] | None = None,
                 telemetry=None, rdir_for: Callable[[object], Path] = requirement_dir,
                 connect: Callable[[str, int, float], str] = connect, clock: Callable[[], float] = time.monotonic,
                 timeout: float = PROBE_TIMEOUT):
        self.check_policy_for = check_policy_for
        self.test_env_for = test_env_for
        self.env_file_for = env_file_for or _agent_env_file
        self.telemetry = telemetry
        self.rdir_for = rdir_for
        self.connect = connect
        self.clock = clock
        self.timeout = timeout
        self._reachable: dict[tuple[str, str, int], float] = {}
        self._reported: set[tuple] = set()

    def check(self, run, plan, task_id: str) -> dict:
        import bt_verifier_env
        test_env = self.test_env_for(run.project)
        policy = self._policy(run)
        inherited = agent_inherited_env()
        own, divergent = agent_environment(test_env, policy, inherited)
        view = {**inherited, **own}
        checks = bt_verifier_env.verifier_values(policy)
        explicit = {name for name, _ in getattr(policy, "environment", ()) or ()}
        requires = required_names(plan.task(task_id))
        keys = [key for key in requires if key in view] if requires else sorted(own)
        unreachable = []
        for key in keys:
            resource = bt_verifier_env.resource_of(view[key])
            if resource is None:
                continue
            error = self._probe(run.run_id, resource)
            if error:
                source = ("verifier" if key in explicit else "verifier_inherited" if key in checks else
                          "agent_env_file" if key in test_env else "inherited")
                unreachable.append({"key": key, "resource": resource["label"], "host": resource["host"],
                                    "port": resource["port"], "error": error, "source": source})
        self._report(run, divergent)
        if not unreachable and not divergent:
            return {}
        return {"state": "unreachable" if unreachable else "ok", "unreachable": unreachable,
                "divergent": list(divergent), "env_file": self.env_file_for(run.project)}

    def _policy(self, run):
        if self.check_policy_for is None:
            return None
        try:
            return self.check_policy_for(run)
        except Exception as error:  # noqa: BLE001 - the verifier builds its own policy and reports; probe what is known
            LOG.warning("check environment of %s not built: %s", run.run_id, type(error).__name__)
            return None

    def _probe(self, run_id: str, resource: dict) -> str:
        key = (run_id, resource["host"], int(resource["port"]))
        seen = self._reachable.get(key)
        if seen is not None and self.clock() - seen < CACHE_SECONDS:
            return ""
        error = self.connect(resource["host"], int(resource["port"]), self.timeout)
        if error:
            self._reachable.pop(key, None)      # an unreachable resource is opened again on the owner's retry
        else:
            self._reachable[key] = self.clock()
        return error

    def _report(self, run, divergent) -> None:
        import bt_verifier_env
        fresh = [item for item in divergent
                 if (run.run_id, item["key"], item["agent"], item["verifier"]) not in self._reported]
        if not fresh:
            return
        self._reported.update((run.run_id, item["key"], item["agent"], item["verifier"]) for item in fresh)
        if self.telemetry is not None:
            try:
                self.telemetry.emit("agent_env_divergent", run_id=run.run_id, keys=[item["key"] for item in fresh],
                                    detail=bt_verifier_env.divergence_sentence(fresh)[:600])
            except Exception as error:  # noqa: BLE001 - reporting never stops the probe
                LOG.warning("agent env divergence not emitted: %s", type(error).__name__)
        try:
            import bt_planning_activity
            bt_planning_activity.record(self.rdir_for(run), "Entorno",
                                        "El archivo de entorno de agentes (" + (self.env_file_for(run.project) or "-")
                                        + ") difiere del verificador en " + bt_verifier_env.divergence_sentence(fresh)
                                        + ". Los agentes reciben el valor del verificador; corrige o borra esa línea.",
                                        kind="flow")
        except Exception as error:  # noqa: BLE001
            LOG.warning("agent env divergence not recorded: %s", type(error).__name__)


def _agent_env_file(project: str) -> str:
    import bt_config
    import bt_verifier_env
    return bt_verifier_env.path_for(bt_config.get("execution.agent_env_file", ""), project)


__all__ = ["CODE", "AgentEnvProbe", "connect", "required_names"]
