"""Durable owner process for Scheduler runs (M1 state, M2 assignment, M3 execution, M4-M6 required modules)."""
from __future__ import annotations

import contextlib
import json
import os
import re
import stat
import sys
import tempfile
import time
import uuid
from pathlib import Path

import bt_core
import bt_attempt_log
import bt_remediation
import bt_notify
import bt_run_stores
import bt_scheduler_adapter as adapter
import bt_scheduler_executor_adapter as executor_runtime
import bt_scheduler_m4_wiring as m4_runtime

HEARTBEAT_SECONDS = 5.0
M4_PENDING_NOTICE_SECONDS = 30.0
M4_STREAM_POLL_SECONDS = 0.1


class RuntimeErrorCode(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _ceiling() -> int:
    import bt_rework_impact
    return bt_rework_impact.ceiling()


LEGACY_EXCLUSIVE_SCOPES = ("large_change", "full_feature", "full_system")


def _in_flight_without_line(rdir: Path | None) -> bool:
    """A run that already accepted work through the predecessor merge (no `RUN.integration-line`): its tasks were never
    integrated with each other, so letting large tasks overlap would multiply the clashes the line is there to resolve."""
    if rdir is None or (Path(rdir) / "RUN.integration-line").exists():
        return False
    return adapter.authority(rdir) == adapter.AUTHORITY and adapter.run_db_path(rdir).exists()


def _run_config(rdir: Path | None = None):
    """Operating limits of a run. A run without a human needs retries: three attempts per task unless configured. With
    `scheduler.exclusive_scopes` empty (the default since REQ-030) a run in flight on the predecessor merge keeps the
    legacy exclusive scopes until it is on the integration line (an explicit owner setting always wins)."""
    import bt_config

    def number(key: str, default: int) -> int:
        value = bt_config.get(key, default)
        return value if isinstance(value, int) and not isinstance(value, bool) and value >= 1 else default

    scopes = bt_config.get("scheduler.exclusive_scopes", [])
    scopes = tuple(s for s in scopes if isinstance(s, str) and s) if isinstance(scopes, list) else ()
    explicit = isinstance(bt_config._stored().get("scheduler"), dict) and "exclusive_scopes" in bt_config._stored()["scheduler"]
    if not scopes and not explicit and _in_flight_without_line(rdir):
        scopes = LEGACY_EXCLUSIVE_SCOPES
    return adapter.core.Config(max_attempts=number("scheduler.max_attempts", 3),
                               max_parallel_tasks=number("scheduler.max_parallel_tasks", 3), exclusive_scopes=scopes,
                               max_reworks=number("gates.max_reworks", 2),
                               rework_confirm_over=_ceiling())


def _executor_config():
    """Wall-clock limit of one agent process, from `scheduler.attempt_timeout_minutes` (the executor default is 30 min)."""
    import bt_config

    minutes = bt_config.get("scheduler.attempt_timeout_minutes", 120)
    minutes = minutes if isinstance(minutes, int) and not isinstance(minutes, bool) and minutes >= 1 else 120
    parallel = bt_config.get("scheduler.max_parallel_tasks", 3)
    parallel = parallel if isinstance(parallel, int) and not isinstance(parallel, bool) and parallel >= 1 else 3
    # M1 decides how many run; the executor's own ceiling must not be lower, or the extra orders are refused
    return executor_runtime.m3.Config(timeout_seconds=float(minutes * 60), max_running=max(parallel, 2))


def _wire(project: str, rdir: Path):
    import bt_scheduler_executor_wiring as composition
    from bt_scheduler_owner_composition import OwnerCompositionRuntime
    import bt_workspace

    run_id = _runtime_binding(rdir, resume=adapter.authority(rdir) == adapter.AUTHORITY)
    db_path = adapter.run_db_path(rdir)
    ledger = bt_run_stores.m2_ledger(db_path, run_id)
    stores = _required_module_stores(db_path, run_id)
    plan = adapter.approved_plan(rdir)
    repos = bt_workspace.repos(bt_core.ROOT, project, False)
    import bt_plan_adapter
    assignment = adapter.DecisionAssignmentPort(project, ledger, laya_root=bt_core.ROOT / ".state" / "laya")
    assignment.run_dir = rdir
    if hasattr(assignment, "classification_overlay"):      # M2 decides with the classification in force (amendments)
        assignment.classification_overlay = lambda: bt_plan_adapter.effective_overrides(rdir)
    wiring = None
    owner_composition = None
    try:
        if OwnerCompositionRuntime.supports(plan):
            req_match = re.match(r"REQ-\d+", rdir.name)
            owner_composition = OwnerCompositionRuntime.create(
                rdir=rdir, project=project, req=req_match.group(0) if req_match else rdir.name,
                plan=plan, repositories=repos, verifier_id="m6-quality/checker-v1")
        wiring = composition.wire(
            rdir, project=project, assignment=assignment, m2_ledger=ledger,
            repos=repos, autostart=True,
            config=_run_config(rdir), executor_config=_executor_config(),
            integrate_predecessors=True,
            monitor_store_path=stores["m4"], recovery_store_path=stores["m5"],
            quality_store_path=stores["m6"],
            composition_base=owner_composition.composition_base if owner_composition is not None else None,
            composition_runtime=owner_composition,
        )
        _secure_store_file(stores["m4"])
        _secure_store_file(stores["m5"])
        _secure_store_file(stores["m6"])
        if owner_composition is not None:
            owner_composition.bind_m6_store(wiring.verification_store)
        if wiring.monitor is None or wiring.recovery is None or wiring.verification_runtime is None:
            raise RuntimeError("required M4/M5/M6 runtime ports were not composed")
        return wiring, assignment, run_id
    except RuntimeErrorCode:
        if wiring is not None:
            with contextlib.suppress(Exception):
                wiring.close()
        with contextlib.suppress(Exception):
            assignment.close()
        if owner_composition is not None and wiring is None:
            with contextlib.suppress(Exception):
                owner_composition.close()
        raise
    except adapter.core.SchedulerError:
        if wiring is not None:
            with contextlib.suppress(Exception):
                wiring.close()
        with contextlib.suppress(Exception):
            assignment.close()
        if owner_composition is not None and wiring is None:
            with contextlib.suppress(Exception):
                owner_composition.close()
        raise
    except Exception as exc:
        if wiring is not None:
            with contextlib.suppress(Exception):
                wiring.close()
        with contextlib.suppress(Exception):
            assignment.close()
        if owner_composition is not None and wiring is None:
            with contextlib.suppress(Exception):
                owner_composition.close()
        raise RuntimeErrorCode(
            "REQUIRED_MODULE_INIT_FAILED",
            f"required M4/M5/M6 stores or ports could not be initialized: {exc}",
        ) from exc
    except BaseException:
        if wiring is not None:
            with contextlib.suppress(Exception):
                wiring.close()
        with contextlib.suppress(Exception):
            assignment.close()
        if owner_composition is not None and wiring is None:
            with contextlib.suppress(Exception):
                owner_composition.close()
        raise

def _required_module_stores(db_path: Path, run_id: str) -> dict[str, Path]:
    if not re.fullmatch(r"[0-9a-f]{32}", run_id):
        raise RuntimeErrorCode("RUNTIME_BINDING_INVALID", "Scheduler runtime identity is invalid")
    root = bt_run_stores.module_root(db_path, run_id)
    try:
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = root.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() \
                or stat.S_IMODE(info.st_mode) != 0o700:
            raise OSError("module store directory must be owned by this user with mode 0700")
        stores = bt_run_stores.module_stores(db_path, run_id)
        for path in stores.values():
            try:
                file_info = path.lstat()
            except FileNotFoundError:
                continue
            if not stat.S_ISREG(file_info.st_mode) or file_info.st_uid != os.getuid():
                raise OSError(f"module store is not a regular file owned by this user: {path.name}")
            if stat.S_IMODE(file_info.st_mode) & 0o077:
                os.chmod(path, 0o600, follow_symlinks=False)
        return stores
    except OSError as exc:
        raise RuntimeErrorCode(
            "MODULE_STORE_UNAVAILABLE",
            f"required Scheduler module store directory or file is unsafe or unavailable: {exc}",
        ) from exc


def _secure_store_file(path: Path) -> None:
    try:
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise OSError("module store is not a regular file owned by this user")
        os.chmod(path, 0o600, follow_symlinks=False)
    except OSError as exc:
        raise RuntimeErrorCode(
            "MODULE_STORE_UNAVAILABLE", f"required Scheduler module store is unsafe or unavailable: {exc}"
        ) from exc


def _runtime_binding(rdir: Path, *, resume: bool) -> str:
    """Keep a run-scoped local M2 ledger namespace without opening a second M1 core."""
    plan = adapter.approved_plan(rdir)
    db = adapter.run_db_path(rdir)
    marker = bt_run_stores.runtime_marker(db)
    if resume:
        try:
            data = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeErrorCode("RUNTIME_BINDING_MISSING", "the Scheduler run has no valid runtime binding") from exc
        identity = data.get("runtime_id") if isinstance(data, dict) else None
        if not isinstance(identity, str) or not re.fullmatch(r"[0-9a-f]{32}", identity) or \
                (data.get("plan_id"), data.get("revision"), data.get("sha256")) != \
                (plan.plan_id, plan.revision, plan.sha256):
            raise RuntimeErrorCode("PLAN_MISMATCH", "runtime binding does not match the approved frozen plan")
        return identity

    identity = uuid.uuid4().hex
    marker.parent.mkdir(parents=True, exist_ok=True)
    tmp = marker.with_suffix(".tmp")
    tmp.write_text(json.dumps({"runtime_id": identity, "plan_id": plan.plan_id,
                               "revision": plan.revision, "sha256": plan.sha256}, sort_keys=True) + "\n",
                   encoding="utf-8")
    os.replace(tmp, marker)
    return identity


def rebind_runtime(rdir: Path) -> None:
    """After a rebase the run keeps its runtime id (M2 ledger and module stores) but follows the new plan revision."""
    plan = adapter.approved_plan(rdir)
    marker = bt_run_stores.runtime_marker(adapter.run_db_path(rdir))
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
        identity = data["runtime_id"]
        if not isinstance(identity, str) or not re.fullmatch(r"[0-9a-f]{32}", identity):
            raise ValueError("runtime_id")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise RuntimeErrorCode("RUNTIME_BINDING_MISSING", "the Scheduler run has no valid runtime binding") from exc
    tmp = marker.with_suffix(".tmp")
    tmp.write_text(json.dumps({"runtime_id": identity, "plan_id": plan.plan_id, "revision": plan.revision,
                               "sha256": plan.sha256}, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, marker)


def _install_autostart(project: str, req: str) -> None:
    bt_notify.install_autostart(project, req, scheduler=True)


def _remove_autostart(project: str, req: str) -> None:
    bt_notify.remove_autostart(project, req)


def _notification_generation(scheduler) -> int:
    """Return the newest state-changing audit sequence, ignoring process-only resume records."""
    for entry in reversed(scheduler.audit_log()):
        if entry.kind != "run_resumed_by_process":
            return entry.seq
    return 0


def _notify_terminal(rdir: Path, req: str, status: str, run_id: str, generation: int) -> None:
    if status not in {"blocked", "completed", "cancelled"}:
        return
    state = adapter.run_db_path(rdir).with_name(adapter.run_db_path(rdir).stem + "-notifications.json")
    try:
        previous = json.loads(state.read_text(encoding="utf-8"))
    except FileNotFoundError:
        previous = None
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Scheduler notification state unavailable: {exc}", file=sys.stderr)
        return
    if previous is not None and (not isinstance(previous, dict)
                                 or not isinstance(previous.get("runtime_id"), str)
                                 or not re.fullmatch(r"[0-9a-f]{32}", previous["runtime_id"])
                                 or previous.get("terminal_status") not in {"blocked", "completed", "cancelled"}
                                 or type(previous.get("generation")) is not int
                                 or previous["generation"] < 0):
        print("Scheduler notification state is malformed; skipping notification", file=sys.stderr)
        return
    if previous is not None and (previous["runtime_id"], previous["terminal_status"], previous["generation"]) == \
            (run_id, status, generation):
        return
    fd = -1
    tmp: Path | None = None
    try:
        state.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=state.parent, prefix=state.name + ".", suffix=".tmp")
        tmp = Path(tmp_name)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            fd = -1
            json.dump({"runtime_id": run_id, "terminal_status": status, "generation": generation},
                      handle, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, state)
    except OSError as exc:
        if fd >= 0:
            with contextlib.suppress(OSError):
                os.close(fd)
        if tmp is not None:
            with contextlib.suppress(OSError):
                tmp.unlink(missing_ok=True)
        print(f"Scheduler notification deduplication unavailable; skipping notification: {exc}", file=sys.stderr)
        return
    try:
        bt_notify.notify(f"Bitácora · {req}", f"Ejecución Scheduler {status}: {req}")
    except Exception as exc:  # noqa: BLE001 - notification delivery is best-effort
        print(f"Scheduler notification delivery failed: {exc}", file=sys.stderr)


def _notify_design_completions(project: str, req: str, rdir: Path, snapshot) -> None:
    """Observe completed design-task state changes and claim one owner notice per contract version."""
    try:
        from bt_design_approval import ui_contracts
        states = {task: item.get("state") for task, item in snapshot.tasks.items()}
        for row in ui_contracts(Path(rdir), project, states):
            task = row.get("design_task")
            if states.get(task) == "completed" and not (row.get("approval") or {}).get("status") == "approved":
                bt_notify.notify_design_waiting(bt_core.ROOT, project, req, row["contract"])
    except (OSError, ValueError, KeyError, TypeError):
        return


def run(project: str, req: str, rdir: Path, *, resume: bool, no_autostart: bool = False,
        max_steps: int | None = None) -> int:
    rdir = Path(rdir)
    with adapter.owner_lock(rdir):
        import bt_scheduler_ops as ops
        if ops.on_hold(rdir):
            raise RuntimeErrorCode("OWNER_HELD", "an operator hold is active; release it with scheduler-op resume")
        from bt_requirements_gate import require_ready

        require_ready(rdir)
        authority = adapter.authority(rdir)
        if (rdir / adapter.RUN_JSON).exists():
            raise RuntimeErrorCode("AUTHORITY_CONFLICT", f"{req} already has legacy RUN.json state")
        if resume and authority != adapter.AUTHORITY:
            raise RuntimeErrorCode("SCHEDULER_RUN_MISSING", f"{req} has no Scheduler database to resume")
        if not resume and authority == adapter.AUTHORITY:
            raise RuntimeErrorCode("SCHEDULER_RUN_EXISTS", f"{req} already has Scheduler state; use --resume")
        wiring, assignment, run_id = _wire(project, rdir)
        try:
            if no_autostart:
                _remove_autostart(project, req)
            else:
                _install_autostart(project, req)
            scheduler = wiring.scheduler
            m1_run_id = executor_runtime.run_identity(scheduler)
            steps = 0
            last_heartbeat = 0.0
            last_m4_pending_notice = 0.0
            while True:
                owner_composition = getattr(wiring, "composition_runtime", None)
                owner_progress = False
                if owner_composition is not None:
                    owner_progress = bool(owner_composition.reserve_candidates())
                report = scheduler.step()
                if owner_composition is not None:
                    owner_progress = bool(owner_composition.reserve_candidates()) or owner_progress
                    owner_progress = bool(owner_composition.reconcile_subplans()) or owner_progress
                    owner_progress = bool(owner_composition.reserve_candidates()) or owner_progress
                    owner_progress = bool(owner_composition.reconcile_compositions()) or owner_progress
                    owner_composition.reconcile_propagation()
                    for identity, reason in owner_composition.drain_attentions():
                        print(f"OWNER_COMPOSITION_ATTENTION: {identity}: {reason}", file=sys.stderr)
                steps += 1
                recovery_tick = getattr(wiring.recovery, "tick_diagnostic_recovery", None)
                if callable(recovery_tick):
                    recovery_result = recovery_tick()
                    if recovery_result.get("state") not in {"preview_only", "ordinary_path_first",
                                                               "waiting_ordinary_remediation"} \
                            and not recovery_result.get("duplicate"):
                        print(f"SCHEDULER_RECOVERY: {recovery_result.get('state')}: "
                              f"{recovery_result.get('blocker', recovery_result.get('cycle_token', ''))}",
                              file=sys.stderr)
                m4_runtime.drain_pending_streams(wiring, m1_run_id)
                incident_report = m4_runtime.deliver_incidents(
                    wiring, f"scheduler-m4:{run_id}", now=time.time())
                if incident_report.status != "complete":
                    raise RuntimeErrorCode(
                        "M4_INCIDENT_DELIVERY_UNAVAILABLE",
                        f"M4 incident outbox could not be delivered through M1: {incident_report.status}",
                    )
                now = time.monotonic()
                if incident_report.pending and now - last_m4_pending_notice >= M4_PENDING_NOTICE_SECONDS:
                    print(f"M4_INCIDENTS_PENDING: {incident_report.pending} incident(s) remain leased for retry",
                          file=sys.stderr)
                    last_m4_pending_notice = now
                snap = scheduler.snapshot()
                _notify_design_completions(project, req, rdir, snap)
                if now - last_heartbeat >= HEARTBEAT_SECONDS or steps == 1:
                    adapter.write_projection(rdir, scheduler)
                    bt_attempt_log.sync(project, req, rdir)
                    last_heartbeat = now
                if bt_remediation.requested(rdir):
                    # an audit's findings become new plan tasks: the watcher applies them with this owner stopped
                    adapter.write_projection(rdir, scheduler)
                    return 0
                _notify_terminal(rdir, req, snap.status, run_id, _notification_generation(scheduler))
                terminal_run = (snap.status in {"completed", "cancelled"} or
                                (not owner_progress and adapter.is_stalled(scheduler, snap)))
                if terminal_run and not m4_runtime.has_pending_streams(wiring) \
                        and not m4_runtime.has_pending_incidents(wiring):
                    _remove_autostart(project, req)
                    adapter.write_projection(rdir, scheduler)
                    bt_attempt_log.sync(project, req, rdir)
                    return 0
                if max_steps is not None and steps >= max_steps:
                    return 0
                delay = min(scheduler.next_deadline(), HEARTBEAT_SECONDS - (time.monotonic() - last_heartbeat))
                if not report.progress:
                    if m4_runtime.has_live_attempts(wiring) or m4_runtime.has_pending_streams(wiring):
                        delay = min(delay, M4_STREAM_POLL_SECONDS)
                    time.sleep(max(0.05, delay))
        finally:
            wiring.close()
            assignment.close()


def dispatch(project: str, req: str, rdir: Path, *, resume: bool, no_autostart: bool = False) -> int:
    try:
        return run(project, req, rdir, resume=resume, no_autostart=no_autostart)
    except RuntimeErrorCode as exc:
        print(f"{exc.code}: {exc}", file=sys.stderr)
        return 2
    except adapter.core.SchedulerError as exc:
        print(f"{exc.code}: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - CLI boundary renders unexpected runtime failures
        print(f"SCHEDULER_RUNTIME_ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 3
