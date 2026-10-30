"""pgroup backend: for hosts without a user systemd manager (CI containers, minimal VMs).

Launch starts `tee.py reap` in a new session; it double-forks (so it is nobody's child and survives the orchestrator),
records its own identity (`reaper.json`), starts the agent with `start_new_session=True` (session + group leader) and
records the agent's pid, start time and boot id in `started.json` — atomically, BEFORE `launch` returns. The reaper is
the agent's parent, so it alone gets the true wait status and writes `exit.json`; an orchestrator that died and came
back reads it from disk. The reaper carries no marker and no secrets in its own environment.

Termination reaches: the agent's process group (only while the leader's incarnation is verified, alive or as the
zombie the reaper deliberately keeps unreaped), and every process whose environment carries `BT_ATTEMPT_KEY=<key>`
(psutil scan) — which catches children that called `setsid`. Not reached: a process that both left the group and
cleared or rewrote its environment (the systemd backend has no such hole: cgroups are inescapable for it).
"""
from __future__ import annotations

import os
import signal
import subprocess
import uuid

from . import procs
from .base import BaseSupervisor, derive_outcome
from .errors import AttemptAlive, LaunchFailed, TerminationUncertain, UnknownAttempt
from .model import LaunchSpec, Observation, ProcessIdentity

START_WAIT_SECONDS = 60.0
REAPER_EXIT_WAIT_SECONDS = 10.0


class PgroupSupervisor(BaseSupervisor):
    backend = "pgroup"

    # ----------------------------------------------------------------------------------------------- identity
    def _identity(self, key: str, record: dict | None) -> ProcessIdentity:
        if record and record.get("identity"):
            return ProcessIdentity(**record["identity"])
        started = self.store.read(key, "started.json") or {}
        return ProcessIdentity(attempt_key=key, backend="pgroup", unit=None,
                               invocation_id=started.get("invocation_id"), control_group=None,
                               main_pid=started.get("child_pid"), main_start_time=started.get("child_start"),
                               boot_id=started.get("boot_id") or procs.boot_id())

    def _reaper_alive(self, key: str) -> bool:
        reaper = self.store.read(key, "reaper.json") or {}
        return reaper.get("boot_id") == procs.boot_id() and procs.alive(reaper.get("pid"), reaper.get("start"))

    def _targets(self, key: str) -> dict[int, float]:
        """Everything of the attempt that is alive: marked processes + the leader's group while its pgid is ours."""
        found = procs.marked(key, self.store.supervisor_id)
        started = self.store.read(key, "started.json") or {}
        if started.get("boot_id") == procs.boot_id() and started.get("pgid") \
                and procs.same_incarnation(started.get("child_pid"), started.get("child_start")):
            found.update(procs.group_members(int(started["pgid"])))
        return found

    # ---------------------------------------------------------------------------------------------------- launch
    def launch(self, spec: LaunchSpec) -> ProcessIdentity:
        key = spec.attempt_key
        with self._locked(key):
            record = self._record(key)
            if record and record.get("status") == "started":
                return self._identity(key, record)
            if record and (self.store.exists(key, "started.json") or self.store.exists(key, "exit.json")
                           or self._reaper_alive(key)):
                return self._finish_start(key, record)     # a crashed launcher got this far: adopt
            # The reaper died before recording the agent: kill anything it may have spawned, then start over.
            if record and not procs.terminate_targets(lambda: procs.marked(key, self.store.supervisor_id), 0.0):
                raise LaunchFailed(f"leftover processes of a crashed launch of {key} could not be killed")
            if not spec.cwd.is_dir():
                raise LaunchFailed(f"cwd is not a directory: {spec.cwd}")
            limits = spec.limits
            unenforced = [name for name in ("memory_max_bytes", "tasks_max", "cpu_quota_percent")
                          if getattr(limits, name) is not None]
            record = {**self.store.new_record(spec, backend=self.backend, unit=None, unenforced=unenforced),
                      "launch_id": uuid.uuid4().hex}     # a stale reaper of a wiped attempt dir must not start ours
            adir = self.store.prepare(spec, record, env_format="json")
            env = {"PATH": os.environ.get("PATH", os.defpath), "LANG": "C.UTF-8"}   # no secrets, no marker
            try:
                launcher = subprocess.Popen([self.python, "-I", str(adir / "tee.py"), "reap", str(adir),
                                             record["launch_id"]], cwd="/",
                                            env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                            stderr=subprocess.DEVNULL, close_fds=True, start_new_session=True)
                launcher.wait(timeout=30)                  # it forks the reaper and exits at once
            except (OSError, subprocess.TimeoutExpired) as error:
                self.store.remove(key)
                raise LaunchFailed(f"could not start the reaper: {error}") from error
            return self._finish_start(key, record)

    def _finish_start(self, key: str, record: dict) -> ProcessIdentity:
        ready = self._wait_for(lambda: self.store.exists(key, "started.json") or self.store.exists(key, "exit.json"),
                               START_WAIT_SECONDS)
        if not ready:
            # Never return with an attempt nobody records: stop the reaper and anything it started.
            reaper = self.store.read(key, "reaper.json") or {}
            if procs.alive(reaper.get("pid"), reaper.get("start")):
                procs.signal_all({reaper["pid"]: reaper["start"]}, signal.SIGKILL)
            procs.terminate_targets(lambda: procs.marked(key, self.store.supervisor_id), 0.0)
            self.store.remove(key)
            raise LaunchFailed(f"the reaper for {key} did not report a start within {START_WAIT_SECONDS:.0f}s")
        identity = self._identity(key, None)
        self.store.write(key, "launch.json", {**record, "status": "started", "identity": identity.model_dump(mode="json")})
        return identity

    # ---------------------------------------------------------------------------------------------- observation
    def observe(self, attempt_key: str) -> Observation:
        key = attempt_key
        record = self._record(key)
        if record is None:
            return self._absent(key)
        started = self.store.read(key, "started.json")
        if started is None and not self.store.exists(key, "exit.json"):
            busy = self._launch_in_flight(key) or self._reaper_alive(key)
            return self._observation(self._bare_identity(key), "unknown" if busy else "absent", record, live=[])
        identity = self._identity(key, record)
        same_boot = identity.boot_id == procs.boot_id()
        exit_rec = self.store.read(key, "exit.json")
        if exit_rec is None and same_boot and (procs.alive(identity.main_pid, identity.main_start_time)
                                               or self._reaper_alive(key)):
            return self._observation(identity, "running", record, live=list(self._targets(key)))
        exit_rec = exit_rec or self.store.read(key, "exit.json")       # it may have landed meanwhile
        # Sample the processes only now: the reaper writes exit.json once the tree is gone, so a sample taken before
        # reading it could list an agent the reaper killed in between, and an exited attempt then reported its dead
        # leader as a straggler (test_supervisor_limits under load, 2026-10-29). The systemd backend reads the unit
        # state first for the same reason.
        live = list(self._targets(key)) if same_boot else []
        if exit_rec is None:          # the reaper is gone without a record: killed, or the host rebooted
            return self._observation(identity, "exited", record, live=live, outcome=(None, None, "lost", False))
        outcome = derive_outcome(exit_rec, None, self._terminate_requested(key))
        return self._observation(identity, "exited", record, live=live, outcome=outcome)

    # ------------------------------------------------------------------------------------------------- terminate
    def terminate(self, attempt_key: str, *, grace: float | None = None) -> Observation:
        key = attempt_key
        with self._locked(key):
            record = self._record(key)
            if record is None:
                return self._absent(key)
            grace = float(grace if grace is not None else record.get("kill_grace_seconds", 30.0))
            if self.observe(key).state == "running":
                self._request_terminate(key, grace)   # durable: the reaper finishes the job if we die now
            if not procs.terminate_targets(lambda: self._targets(key), grace):
                raise TerminationUncertain(f"attempt {key} still has live processes after SIGKILL", self.observe(key))
            if self._reaper_alive(key):              # let it reap the leader and write exit.json
                self._wait_for(lambda: self.store.exists(key, "exit.json") or not self._reaper_alive(key),
                               REAPER_EXIT_WAIT_SECONDS, step=0.05)
            observation = self.observe(key)
            if observation.live_pids:
                raise TerminationUncertain(f"attempt {key} respawned processes during termination", observation)
            return observation

    # ---------------------------------------------------------------------------------------- freeze / release
    def _signal_tree(self, key: str, sig: int) -> None:
        if self._record(key) is None:
            raise UnknownAttempt(f"no attempt {key}")
        procs.signal_all(self._targets(key), sig)

    def freeze(self, attempt_key: str) -> None:
        """SIGSTOP the group and every marked process. Weaker than the cgroup freezer: a process forked between the
        scan and the signal runs on (call again), and the reaper's runtime deadline keeps counting while frozen."""
        self._signal_tree(attempt_key, signal.SIGSTOP)

    def thaw(self, attempt_key: str) -> None:
        self._signal_tree(attempt_key, signal.SIGCONT)

    def release(self, attempt_key: str) -> None:
        key = attempt_key
        with self._locked(key):
            record = self._record(key)
            if record is None:
                return
            observation = self.observe(key)
            if observation.state in ("running", "unknown") or observation.live_pids or self._reaper_alive(key):
                raise AttemptAlive(f"attempt {key} is {observation.state} (live pids {observation.live_pids})")
            self.store.remove(key)

    # ------------------------------------------------------------------------------------------------- listing
    def list_attempts(self, prefix: str = "") -> list[ProcessIdentity]:
        found = []
        for key in self.store.attempt_keys():
            if not key.startswith(prefix):
                continue
            record = self._record(key)
            if record and (record.get("status") == "started" or self.store.exists(key, "started.json")
                           or self._reaper_alive(key)):
                found.append(self._identity(key, record))
        return found

