# bt_supervisor — process runtime for agent attempts (REQ-030 M3)

Runs one agent attempt (Claude/Codex CLI, 10–120 min, writing into a git worktree) per `attempt_key`, so that the DBOS
execution plane can launch, observe, cancel, pause and forget it — and find it again after its own crash. It replaces
the home-grown double-forked shim of `bt_scheduler_executor` (`shim.py`, `procinfo.py`) with **systemd user services
on cgroup v2**, and keeps a **process-group fallback** for hosts without a user manager (CI containers).

Needs the uv environment (pydantic, psutil). Nothing on the legacy stdlib path imports it (`test_stdlib_boundary`).

```python
from bt_supervisor import LaunchSpec, Limits, make_supervisor
sup = make_supervisor(state_dir)                       # "auto": systemd if a user manager answers, else pgroup
identity = sup.launch(LaunchSpec(attempt_key="REQ-030.T4.a1", argv=[...], cwd=worktree, env=env,
                                 log_dir=artifacts, stdin_text=prompt, limits=Limits(runtime_max_seconds=7200)))
sup.observe(key)      # Observation: running|exited|absent|unknown, exit_code, signal, result, oom_killed, live_pids
sup.terminate(key)    # SIGTERM tree -> grace -> SIGKILL; returns only when nothing is alive
sup.freeze(key); sup.thaw(key); sup.release(key); sup.list_attempts("REQ-030.")
```

Files: `model.py` (pydantic contract), `api.py` (Protocol + factory), `systemd.py`, `pgroup.py`, `base.py` (shared
outcome derivation), `store.py` (state dir, locks, records — the layout is documented there), `procs.py` (psutil,
pidfd, cgroup helpers), `tee.py` (stdlib-only in-attempt helper), `cli.py`.

## Guarantees

1. **No duplicates.** `launch` is idempotent per key while a record exists (running, or exited and not released).
   It writes `launch.json` (status `starting`) *before* starting anything, under a per-key `flock`; a re-run after a
   crash adopts whatever evidence exists (a loaded unit, `started.json`, `exit.json`, a live reaper) instead of starting
   again. Only a record with no evidence at all is (re)started. systemd adds a second barrier: a unit name is unique.
2. **Survives the orchestrator.** The attempt is a user-manager service (systemd) or a double-forked reaper in its own
   session (pgroup). Exit status and output are written to disk by that process, never by the orchestrator.
3. **Termination is complete or loud.** `terminate` returns only when the unit is dead, its cgroup empty, and no
   process carrying `BT_ATTEMPT_KEY=<key>` is left anywhere (psutil scan); otherwise `TerminationUncertain` — the caller
   must keep the worktree busy. A `setsid` grandchild that ignores SIGTERM is covered by a test on both backends.
4. **Exact environment.** `env` is the agent's whole environment plus the marker; nothing leaks in from the
   orchestrator or the user manager's environment (which may hold another account's tokens).
5. **Secrets stay off command lines.** `env` travels in a 0600 file (systemd `EnvironmentFile`, pgroup `env.json`) in a
   0700 dir and is deleted as soon as the agent has started; `stdin_text` likewise. Neither appears in `systemctl show`
   or `/proc/<pid>/cmdline` (tested).
6. **Signals never hit a recycled pid.** Every signal goes through a pidfd opened before the start time is re-checked;
   process groups are signalled only while the leader's incarnation is verified (the pgroup reaper keeps the leader
   as an unreaped zombie via `waitid(WNOWAIT)` until its stragglers are dead, so the pgid cannot be reused).

## Design decisions

**Transient service, not scope.** `systemd-run --user --unit=<prefix><key[:48]>-<sha256[:12]>.service
--service-type=exec --expand-environment=no` with `KillMode=control-group`, `SendSIGKILL=yes`, `OOMPolicy=stop`,
`TimeoutStopSec=<kill_grace>`, `RuntimeMaxSec`, `MemoryMax` (+ `MemorySwapMax=0`, or zram swap would hide the OOM),
`TasksMax`, `CPUQuota`. `--setenv` carries only the marker and the supervisor id (sha of the state dir path), which is
how `list_attempts` recognises our units even if the state dir was wiped, and why another state dir's unit with the
same name is refused (`LaunchConflict`), never adopted.

**Exit record.** `ExecStopPost=:<python3> -I tee.py exit-record <dir>` (`:` = no `$` expansion) writes `exit.json`
atomically from `$SERVICE_RESULT $EXIT_CODE $EXIT_STATUS $INVOCATION_ID` plus the cgroup's `memory.events` oom_kill
counter. systemd runs it after SIGKILL, OOM and RuntimeMaxSec too, before the unit becomes inactive — so a
garbage-collected successful unit always has its record first. No `--collect`: failed units stay loaded until
`release` (`reset-failed`), so `systemctl show` (`Result`, `ExecMainCode/Status`) is a fallback when the record is
missing. pgroup: the reaper is the agent's parent and writes `exit.json` with the true wait status after killing the
stragglers. Result precedence: `oom-kill > spawn-error > terminated > timeout > manager results > signal/core-dump >
success/exit-code`; `lost` when the process is gone and no record could ever be written.

**Output cap.** `ExecStart` is `tee.py run` (pgroup: the reaper does the same): it owns the agent's stdout/stderr
pipes and writes `log_dir/output.log` = the first `output_cap_bytes` bytes + one marker line, and `output.tail` = the
last `min(256 KiB, cap)` bytes, rewritten atomically at most once a second, only after an overflow (the legacy
head+tail shape). Lines are merged chronologically but never split: a partial line is held ≤64 KiB / ≤1 s, so a
stream-json event on stdout is not cut by a stderr chunk. Trade-offs vs `StandardOutput=append:` + periodic
truncation: (+) bounded without any watcher alive, (+) exact head preserved, (−) one extra Python process per attempt,
(−) the agent is not `MainPID` — the wrapper mirrors its exit code and re-raises its signal so `ExecMainStatus` still
describes the agent, (−) if the wrapper is SIGKILLed the tail on disk may be up to 1 s stale. stdin is fed by the
wrapper from a file it unlinks, not `StandardInput=file:` (ExecStopPost would re-open the deleted file and fail 208).

**Helper interpreter.** `tee.py` is copied into each attempt dir and run with `/usr/bin/python3 -I` (fallback: the
real path of the current interpreter): a `uv sync`, a deleted checkout or a worktree switch cannot break a running
attempt or its ExecStopPost.

**Identity.** `ProcessIdentity` = unit + `invocation_id` (systemd: a reused unit name gets a new one, and an
observation of a different invocation reports `unknown`; terminate refuses it) or, on pgroup, leader pid +
`main_start_time` (kernel start time, seconds since boot: exact, unlike epoch create_time which drifts with btime) +
`boot_id` + a random invocation id from the reaper.

## Non-guarantees

- **pgroup enforces only `runtime_max_seconds`.** Memory/tasks/CPU limits are recorded in `launch.json`
  `unenforced_limits`; RLIMIT_AS would break Node/V8 agents and RLIMIT_NPROC is per user, not per attempt. OOM is not
  detected (a global OOM kill reads as `signal`).
- **pgroup can miss** a process that both left the process group/session *and* cleared or rewrote its environment.
  systemd cannot miss it inside the cgroup; there, only processes that moved themselves to another cgroup are
  "escapers", handled by the same marker scan.
- **Hand-offs to another manager** (`systemd-run --user` from inside the agent, `at`, a D-Bus-activated service) leave
  the attempt on both backends: the new process is not our child, not in our cgroup, and does not inherit the marker.
- **freeze on pgroup** is SIGSTOP of what a scan found: a process forked between scan and signal keeps running (call
  again); the reaper's runtime deadline keeps counting while frozen. systemd uses the cgroup freezer (atomic).
- **A tiny SIGKILL/ExecStopPost race** on systemd: if escalation's `cgroup.kill` lands in the millisecond in which
  systemd starts ExecStopPost, the exit record is lost; the failed unit's `systemctl show` fallback still gives the
  status, and `terminate.json` still yields `terminated`.
- **D-state processes**, a mute user manager or an unreadable process table make `terminate` raise
  `TerminationUncertain` rather than guess.
- After a reboot, records of the previous boot report `exited`/`lost` (boot id mismatch); nothing survives a reboot.
- `release` keeps `log_dir` (it belongs to the caller); it deletes the attempt state dir and resets the unit.

## Mapping from the legacy shim

| shim / procinfo | bt_supervisor |
|---|---|
| double-forked `shim.py` owning the agent | systemd service (manager owns it) / double-forked `tee.py reap` |
| `spec.json` read then deleted | `launch.json` (no secrets) + `env`/`env.json`/`stdin` deleted at start |
| `shim.json` identity `boot_id:starttime` | `started.json`; `ProcessIdentity` (unit+invocation_id, or pid+start seconds+boot_id) |
| `output.log` head + `output.tail` window, `Output` class | same files and shape, plus line integrity (`tee.Output`) |
| `exit.json` written by the shim as its last act | `exit.json` by ExecStopPost (systemd) or the reaper (pgroup) |
| timeout loop + SIGTERM/grace/SIGKILL of the group | `RuntimeMaxSec` + `TimeoutStopSec` (systemd) / reaper deadline (pgroup) |
| `DescendantRecorder` + `kill_in_cwd` for `setsid` escapers | cgroup (systemd) + `BT_ATTEMPT_KEY` environ marker scan (both) |
| `alive(pid, ident)` before signalling | pidfd + start-time re-check (`tee.send`) |
| `abort` file / SIGTERM to the shim | `terminate.json` (durable: the pgroup reaper finishes a terminate whose caller died) |
| `StreamTap` FIFO for live streaming | not ported: readers tail `output.log` (M4 stream bridge decides) |

## CLI

`python -m bt_supervisor --state-dir D [--backend auto|systemd|pgroup] [--unit-prefix P] list [prefix] | show KEY |
stop KEY [--grace S]` — JSON on stdout; `$BT_SUPERVISOR_STATE_DIR` replaces `--state-dir`.

## Tests

`uv run python -m unittest test_supervisor_lifecycle test_supervisor_limits test_supervisor_kill` from
`skill/scripts/tests`: real processes, both backends, units prefixed `bt-test-<hex>-` and removed in `addCleanup`.
systemd cases skip (printing why) only when `systemctl --user` is unavailable; under the bare system interpreter the
modules skip because pydantic/psutil are missing.
