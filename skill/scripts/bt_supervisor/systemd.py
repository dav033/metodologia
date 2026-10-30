"""systemd backend: one transient user SERVICE per attempt, on cgroup v2.

Why a service and not a scope: a service is owned by the user manager, so the attempt outlives the orchestrator, and
systemd itself enforces RuntimeMaxSec, MemoryMax, TasksMax, CPUQuota and, with KillMode=control-group, kills every
process of the cgroup when the main process ends or the unit is stopped — `setsid` does not escape a cgroup.

Unit layout (see `_systemd_run_argv`): ExecStart is `tee.py run` (captures output, mirrors the agent's status);
ExecStopPost is `tee.py exit-record` (the exit record, written even after SIGKILL/OOM/timeout). No `--collect`: a
failed unit stays loaded until `release()` (reset-failed), and a successful one is garbage-collected only after
ExecStopPost has written `exit.json`. Secrets travel in a 0600 EnvironmentFile that `tee.py run` deletes once started;
only the marker and the supervisor id are on the systemd-run command line.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import signal
import subprocess
import time
from pathlib import Path

from . import procs
from .base import BaseSupervisor, derive_outcome
from .errors import (
    AttemptAlive,
    LaunchConflict,
    LaunchFailed,
    ManagerUnavailable,
    SupervisorError,
    TerminationUncertain,
    UnknownAttempt,
)
from .model import (
    MARKER_ENV,
    SUPERVISOR_ENV,
    LaunchSpec,
    Observation,
    ProcessIdentity,
    validate_attempt_key,
)

PROPS = ("LoadState", "ActiveState", "SubState", "Result", "ExecMainCode", "ExecMainStatus", "InvocationID",
         "ControlGroup", "MainPID", "FreezerState", "Environment")
LIVE_STATES = {"active", "activating", "deactivating", "reloading", "refreshing"}
POST_STATES = {"stop-post", "final-sigterm", "final-sigkill", "final-watchdog"}   # ExecStopPost may be running
PREFIX_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,40}$")
KILL_WINDOW_SECONDS = 15.0
START_WAIT_SECONDS = 15.0


ManagerError = ManagerUnavailable


def available(timeout: float = 10.0) -> tuple[bool, str]:
    """(usable, why not). Needs cgroup v2, systemctl + systemd-run, and a reachable user manager."""
    if not Path("/sys/fs/cgroup/cgroup.controllers").exists():
        return False, "cgroup v2 is not mounted at /sys/fs/cgroup"
    if not shutil.which("systemctl") or not shutil.which("systemd-run"):
        return False, "systemctl/systemd-run not found"
    try:
        done = subprocess.run(["systemctl", "--user", "show", "-p", "Version", "--value"], check=False, capture_output=True,
                              text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, f"systemctl --user failed: {error}"
    if done.returncode != 0 or not done.stdout.strip():
        return False, f"no user systemd manager: {done.stderr.strip() or 'empty answer'}"
    return True, ""


def _quote(arg: str | Path) -> str:
    """Quote one word of a unit-file command line (used only for ExecStopPost; ExecStart goes as an argv array)."""
    return '"' + str(arg).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _environment(props: dict) -> dict[str, str]:
    pairs = (item.partition("=") for item in props.get("Environment", "").split())
    return {name: value for name, _, value in pairs if name}


class SystemdSupervisor(BaseSupervisor):
    backend = "systemd"

    def __init__(self, state_dir: Path, *, unit_prefix: str = "bt-att-", helper_python: str | None = None,
                 timeout: float = 30.0):
        super().__init__(state_dir, helper_python=helper_python)
        if not PREFIX_PATTERN.match(unit_prefix):
            raise ValueError("unit_prefix must match [A-Za-z0-9_.-]{1,40}")
        self.prefix, self.timeout = unit_prefix, timeout

    def unit_name(self, key: str) -> str:
        """Deterministic: readable key prefix + a hash of the full key (truncation can never collide)."""
        validate_attempt_key(key)
        return f"{self.prefix}{key[:48]}-{hashlib.sha256(key.encode()).hexdigest()[:12]}.service"

    # -------------------------------------------------------------------------------------------- manager access
    def _ctl(self, *args: str) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(["systemctl", "--user", *args], check=False, capture_output=True, text=True, timeout=self.timeout)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise ManagerError(f"systemctl --user {args[0]}: {error}") from error

    def _show(self, *units: str) -> list[dict]:
        done = self._ctl("show", *units, "-p", ",".join(PROPS))
        if done.returncode != 0:
            raise ManagerError(f"systemctl --user show failed: {done.stderr.strip()}")
        blocks = [block for block in done.stdout.split("\n\n") if block.strip()]
        parsed = [dict(line.partition("=")[::2] for line in block.splitlines() if "=" in line) for block in blocks]
        if len(parsed) != len(units):
            raise ManagerError("systemctl --user show returned an unexpected number of units")
        return parsed

    def _show_one(self, unit: str) -> dict:
        return self._show(unit)[0]

    def _ours(self, props: dict, key: str) -> bool:
        env = _environment(props)
        return env.get(SUPERVISOR_ENV) == self.store.supervisor_id and env.get(MARKER_ENV) == key

    # ----------------------------------------------------------------------------------------------- identity
    def _identity(self, key: str, record: dict | None, props: dict | None) -> ProcessIdentity:
        if record and record.get("identity"):
            return ProcessIdentity(**record["identity"])
        started, props = self.store.read(key, "started.json") or {}, props or {}
        main_pid = started.get("pid") or int(props.get("MainPID") or 0) or None
        return ProcessIdentity(
            attempt_key=key, backend="systemd", unit=self.unit_name(key),
            invocation_id=started.get("invocation_id") or props.get("InvocationID") or None,
            control_group=started.get("control_group") or props.get("ControlGroup") or None,
            main_pid=main_pid, main_start_time=started.get("start") if started else procs.start_time(main_pid),
            boot_id=started.get("boot_id") or procs.boot_id())

    def _finalize(self, key: str, record: dict, props: dict | None) -> ProcessIdentity:
        """Mark the record started; freeze the identity into it once the helper has reported (started.json)."""
        identity = self._identity(key, None, props)
        frozen = identity.model_dump(mode="json") if self.store.exists(key, "started.json") else None
        self.store.write(key, "launch.json", {**record, "status": "started", "identity": frozen})
        return identity

    def _foreign_invocation(self, identity: ProcessIdentity, props: dict) -> bool:
        current = props.get("InvocationID")
        return props.get("LoadState") == "loaded" and bool(identity.invocation_id and current) \
            and current != identity.invocation_id

    # ---------------------------------------------------------------------------------------------------- launch
    def launch(self, spec: LaunchSpec) -> ProcessIdentity:
        key, unit = spec.attempt_key, self.unit_name(spec.attempt_key)
        with self._locked(key):
            record = self._record(key)
            try:
                props = self._show_one(unit)
            except ManagerError:
                # A re-run launch (the engine stopped before DBOS recorded the step) met a user manager that did not
                # answer. The attempt's own files prove it was started: adopt it from them, and let the observation
                # (D-188's grace) wait for the manager. Without that, the step ran out of DBOS's tries in seconds, the
                # agent workflow failed, the reaper killed the healthy agent and the task asked the owner about a
                # runtime defect (test_durable_launch_hiccup; test_durable_shutdown under load, 2026-10-30).
                # Without such proof nothing is started blind: the unit may exist, so the error stands.
                if record and (record.get("status") == "started" or self.store.exists(key, "started.json")
                               or self.store.exists(key, "exit.json")):
                    return self._identity(key, record, None) if record.get("status") == "started" \
                        else self._finalize(key, record, None)
                raise
            loaded = props.get("LoadState") == "loaded"
            if loaded and not self._ours(props, key):
                raise LaunchConflict(f"unit {unit} exists but was not started by this supervisor for {key}")
            if record and record.get("status") == "started":
                return self._identity(key, record, props)
            evidence = loaded or any(self.store.exists(key, name) for name in ("started.json", "child.json", "exit.json"))
            if evidence:                     # a previous launch got the unit going and then crashed: adopt it
                if record is None:
                    record = self.store.new_record(spec, backend=self.backend, unit=unit, unenforced=[])
                    self.store.adopt(spec, record)
                self._wait_for(lambda: self.store.exists(key, "started.json") or self.store.exists(key, "exit.json"),
                               START_WAIT_SECONDS if loaded else 0)
                return self._finalize(key, record, props)
            if not spec.cwd.is_dir():
                raise LaunchFailed(f"cwd is not a directory: {spec.cwd}")
            record = self.store.new_record(spec, backend=self.backend, unit=unit, unenforced=[])
            adir = self.store.prepare(spec, record, env_format="systemd")
            try:
                done = subprocess.run(self._systemd_run_argv(spec, unit, adir), check=False, capture_output=True, text=True,
                                      timeout=max(60.0, self.timeout))
                failure = done.stderr.strip() if done.returncode != 0 else ""
            except (OSError, subprocess.TimeoutExpired) as error:
                failure = f"systemd-run: {error}"
            try:
                props = self._show_one(unit)
            except ManagerError:
                if failure:
                    raise                    # the unit may or may not exist: the record stays "starting" (adoptable)
                props = {}                   # systemd-run created it: its files will say so, the manager need not
            if failure and not (props.get("LoadState") == "loaded" and self._ours(props, key)):
                self.store.remove(key)       # nothing started: a retry may start it cleanly
                if props.get("LoadState") == "loaded":
                    raise LaunchConflict(f"unit {unit} appeared but is not ours: {failure}")
                raise LaunchFailed(failure)
            self._wait_for(lambda: self.store.exists(key, "started.json") or self.store.exists(key, "exit.json"),
                           START_WAIT_SECONDS)
            return self._finalize(key, record, props)

    def _systemd_run_argv(self, spec: LaunchSpec, unit: str, adir: Path) -> list[str]:
        limits, tee = spec.limits, adir / "tee.py"
        properties = [
            f"EnvironmentFile=-{adir / 'env'}",              # '-': it is deleted at start; ExecStopPost must not fail
            "KillMode=control-group", "SendSIGKILL=yes", "OOMPolicy=stop",
            f"TimeoutStopSec={max(1, int(spec.kill_grace_seconds * 1000))}ms",
            "StandardInput=null",                             # tee.py feeds stdin_text itself (see tee.cmd_run)
            f"StandardOutput=append:{adir / 'runner.log'}", f"StandardError=append:{adir / 'runner.log'}",
            # ':' = no $VAR expansion; transient units do not expand %-specifiers.
            f"ExecStopPost=:{_quote(self.python)} -I {_quote(tee)} exit-record {_quote(adir)}",
        ]
        if limits.memory_max_bytes:
            properties += [f"MemoryMax={limits.memory_max_bytes}", "MemorySwapMax=0"]   # swap would hide the OOM
        if limits.tasks_max:
            properties.append(f"TasksMax={limits.tasks_max}")
        if limits.cpu_quota_percent:
            properties.append(f"CPUQuota={limits.cpu_quota_percent}%")
        if limits.runtime_max_seconds:
            properties.append(f"RuntimeMaxSec={limits.runtime_max_seconds}s")
        argv = ["systemd-run", "--user", "--quiet", "--no-ask-password", f"--unit={unit}",
                f"--description=bt attempt {spec.attempt_key}", "--service-type=exec", "--expand-environment=no",
                f"--working-directory={spec.cwd}", f"--setenv={MARKER_ENV}={spec.attempt_key}",
                f"--setenv={SUPERVISOR_ENV}={self.store.supervisor_id}"]
        for item in properties:
            argv += ["-p", item]
        return argv + ["--", self.python, "-I", str(tee), "run", str(adir)]

    # ---------------------------------------------------------------------------------------------- observation
    def _escapers(self, key: str, control_group: str | None) -> dict[int, float]:
        """Marked processes OUTSIDE the unit's cgroup (moved themselves out). Inside is cgroup.kill's job, and the
        ExecStopPost helper, which also carries the marker, must never be hit."""
        return {pid: start for pid, start in procs.marked(key, self.store.supervisor_id).items()
                if not procs.inside(procs.cgroup_of(pid), control_group)}

    def observe(self, attempt_key: str) -> Observation:
        key, unit = attempt_key, self.unit_name(attempt_key)
        record = self._record(key)
        try:
            props = self._show_one(unit)
        except ManagerError:
            identity = self._identity(key, record, None) if record else self._bare_identity(key, unit)
            return self._observation(identity, "unknown", record, live=[])
        loaded = props.get("LoadState") == "loaded"
        if loaded and not self._ours(props, key):
            return self._observation(self._bare_identity(key, unit), "unknown", None, live=[])
        if record is None and not loaded:
            return self._absent(key, unit)
        identity = self._identity(key, record, props)
        if self._foreign_invocation(identity, props):
            return self._observation(identity, "unknown", record, live=[])
        live_group = props.get("ControlGroup") if loaded else None
        live = procs.cgroup_pids(live_group) + list(self._escapers(key, identity.control_group))
        exit_rec, child = self.store.read(key, "exit.json"), self.store.read(key, "child.json")
        terminated = self._terminate_requested(key)
        if loaded and props.get("ActiveState") in LIVE_STATES:
            return self._observation(identity, "running", record, live=live)
        if loaded or exit_rec:
            outcome = derive_outcome(exit_rec, child, terminated, fallback=props if loaded else None)
            return self._observation(identity, "exited", record, live=live, outcome=outcome)
        if record and record.get("status") == "starting" and not self.store.exists(key, "started.json"):
            return self._observation(identity, "unknown" if self._launch_in_flight(key) else "absent", record, live=live)
        # Ran, but the unit is gone without an exit record (manager restart, reboot, ExecStopPost killed).
        return self._observation(identity, "exited", record, live=live, outcome=(None, None, "lost", False))

    # ------------------------------------------------------------------------------------------------- terminate
    def _settled(self, key: str, unit: str, control_group: str | None) -> bool:
        try:
            props = self._show_one(unit)
        except ManagerError:
            return False
        if props.get("LoadState") == "loaded" and props.get("ActiveState") in LIVE_STATES:
            return False
        return not procs.cgroup_pids(control_group) and not procs.marked(key, self.store.supervisor_id)

    def terminate(self, attempt_key: str, *, grace: float | None = None) -> Observation:
        """SIGTERM the whole cgroup (+ marked escapers), wait `grace`, then cgroup.kill until the unit is dead and
        no marked process is left anywhere. Raises TerminationUncertain otherwise."""
        key, unit = attempt_key, self.unit_name(attempt_key)
        with self._locked(key):
            record = self._record(key)
            try:
                props = self._show_one(unit)
            except ManagerError as error:
                raise TerminationUncertain(f"cannot reach the user manager: {error}") from error
            loaded = props.get("LoadState") == "loaded"
            if loaded and not self._ours(props, key):
                raise LaunchConflict(f"unit {unit} was not started by this supervisor")
            if record is None and not loaded:
                return self._absent(key, unit)
            identity = self._identity(key, record, props)
            if self._foreign_invocation(identity, props):
                raise LaunchConflict(f"unit {unit} now runs invocation {props.get('InvocationID')}, not ours")
            grace = float(grace if grace is not None else (record or {}).get("kill_grace_seconds", 30.0))
            group = identity.control_group or props.get("ControlGroup") or None
            if loaded and props.get("ActiveState") in LIVE_STATES:
                if record is not None:
                    self._request_terminate(key, grace)
                try:
                    if props.get("FreezerState") in ("frozen", "freezing"):
                        self._ctl("thaw", unit)              # a frozen task cannot act on SIGTERM
                    self._ctl("kill", "--signal=SIGTERM", unit)
                except ManagerError:
                    pass                                     # escalation below works on the cgroup directly
            escapers = self._escapers(key, group)
            procs.signal_all(escapers, signal.SIGTERM)
            procs.signal_all(escapers, signal.SIGCONT)
            settled = self._wait_for(lambda: self._settled(key, unit, group), grace, step=0.05)
            end = time.monotonic() + KILL_WINDOW_SECONDS
            while not settled and time.monotonic() < end:
                try:
                    current = self._show_one(unit)
                except ManagerError:
                    current = {}
                if current.get("LoadState") == "loaded" and current.get("ActiveState") in LIVE_STATES \
                        and current.get("SubState") not in POST_STATES \
                        and not procs.cgroup_kill(current.get("ControlGroup")):
                    try:
                        self._ctl("kill", "--signal=SIGKILL", unit)  # fallback when cgroup.kill is unavailable
                    except ManagerError:
                        pass
                procs.signal_all(self._escapers(key, group), signal.SIGKILL)
                settled = self._wait_for(lambda: self._settled(key, unit, group), 0.3, step=0.05)
            observation = self.observe(key)
            if not settled:
                raise TerminationUncertain(f"attempt {key} still has live processes after SIGKILL", observation)
            return observation

    # ---------------------------------------------------------------------------------------- freeze / release
    def _freezer(self, key: str, verb: str) -> None:
        unit = self.unit_name(key)
        record = self._record(key)
        props = self._show_one(unit)
        if props.get("LoadState") != "loaded" or not self._ours(props, key):
            if record is None:
                raise UnknownAttempt(f"no attempt {key}")
            return                                       # already exited: nothing to freeze or thaw
        if props.get("ActiveState") not in LIVE_STATES:
            return
        done = self._ctl(verb, unit)
        if done.returncode != 0:
            raise SupervisorError(f"systemctl --user {verb} {unit} failed: {done.stderr.strip()}")

    def freeze(self, attempt_key: str) -> None:
        self._freezer(attempt_key, "freeze")

    def thaw(self, attempt_key: str) -> None:
        self._freezer(attempt_key, "thaw")

    def release(self, attempt_key: str) -> None:
        key, unit = attempt_key, self.unit_name(attempt_key)
        with self._locked(key):
            record = self._record(key)
            observation = self.observe(key)
            if record is None and observation.state in ("absent", "unknown"):
                return                                   # nothing of ours: never touch a foreign unit
            if observation.state in ("running", "unknown") or observation.live_pids:
                raise AttemptAlive(f"attempt {key} is {observation.state} (live pids {observation.live_pids})")
            self._ctl("reset-failed", unit)              # a failed unit stays loaded until this
            self.store.remove(key)

    # ------------------------------------------------------------------------------------------------- listing
    def list_attempts(self, prefix: str = "") -> list[ProcessIdentity]:
        """Every attempt with a started record, plus units of ours (by supervisor id) whose record was lost."""
        keys = [key for key in self.store.attempt_keys() if key.startswith(prefix)]
        done = self._ctl("list-units", "--all", "--plain", "--no-legend", "--full", f"{self.prefix}*")
        units = [word for line in done.stdout.splitlines() for word in line.split()[:2] if word.endswith(".service")]
        by_unit = dict(zip(units, self._show(*units), strict=True)) if units else {}
        found: list[ProcessIdentity] = []
        for key in keys:
            record = self._record(key)
            props = by_unit.get(self.unit_name(key))
            loaded = bool(props) and props.get("LoadState") == "loaded" and self._ours(props, key)
            if record and (record.get("status") == "started" or loaded or self.store.exists(key, "started.json")):
                found.append(self._identity(key, record, props if loaded else None))
        for props in by_unit.values():
            key = _environment(props).get(MARKER_ENV, "")
            if key and key not in keys and key.startswith(prefix) and self._ours(props, key):
                found.append(self._identity(key, None, props))
        return found
