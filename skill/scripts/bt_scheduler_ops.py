"""Operator moves on a Scheduler run: stop its owner, cancel a live attempt (and its agent), reopen a blocked task,
send accepted work back for rework, revise the run onto the latest frozen plan. Each one used to be a throwaway Python snippet.

Every move that writes needs the owner stopped (M1 allows one owner), and the watchdog (`bt_scheduler_watch`) would
restart it at once, so a move first puts a `hold` on the run; the watchdog honours it, and the move releases it when done.
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import signal
import sqlite3
import time
import uuid
from pathlib import Path

import bt_config
import bt_core
import bt_scheduler_adapter as adapter

core = adapter.core
OPERATOR = "operator"
STOP_SECONDS = 30.0


def hold_path(rdir: Path) -> Path:
    return adapter.run_db_path(rdir).with_suffix(".hold")


def watch_lock_path(rdir: Path) -> Path:
    return adapter.run_db_path(rdir).with_suffix(".watch.lock")


def on_hold(rdir: Path) -> bool:
    return hold_path(rdir).exists()


def owns_hold(rdir: Path, token: str | None) -> bool:
    """Whether the caller's hold still owns the marker after a nested operator action."""
    if not isinstance(token, str) or not token:
        return False
    try:
        data = json.loads(hold_path(rdir).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    return isinstance(data, dict) and data.get("token") == token


@contextlib.contextmanager
def hold(rdir: Path, why: str, keep: bool = False):
    """Keep the watchdog from restarting the owner while a move is in progress. A hold that was already there (an operator's
    stop) is never destroyed: it is put back on exit, and a stop that lands DURING the move (the marker no longer carries our
    token) is left as it is. The stop always wins."""
    path = hold_path(rdir)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        prior = path.read_text(encoding="utf-8")
    except OSError:
        prior = None
    token = uuid.uuid4().hex
    path.write_text(json.dumps({"why": why, "pid": os.getpid(), "at": time.time(), "token": token}) + "\n",
                    encoding="utf-8")
    try:
        yield token
    finally:
        if not keep and owns_hold(rdir, token):
            if prior is None:
                path.unlink(missing_ok=True)
            else:
                path.write_text(prior, encoding="utf-8")


def _processes(match) -> list[int]:
    found = []
    proc = Path("/proc")
    if not proc.exists():
        return found
    for entry in proc.iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            argv = (entry / "cmdline").read_bytes().decode("utf-8", "replace").split("\0")
        except OSError:
            continue
        if match([a for a in argv if a]):
            found.append(int(entry.name))
    return found


def _command_matches(argv: list[str], command: str, project: str, req: str) -> bool:
    """`<python> .../bitacora.py --project P <command> REQ …`: an exact argv, so an editor or `tail` of the same words
    does not match."""
    if len(argv) < 5 or not argv[1].endswith("bitacora.py") or "python" not in Path(argv[0]).name:
        return False
    try:
        at = argv.index(command, 2)
    except ValueError:
        return False
    return argv[at + 1:at + 2] == [req] and ["--project", project] == argv[2:4]


def owner_pids(project: str, req: str) -> list[int]:
    return _processes(lambda argv: _command_matches(argv, "scheduler-run", project, req))


def watcher_pids(project: str, req: str) -> list[int]:
    return _processes(lambda argv: _command_matches(argv, "scheduler-watch", project, req))


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    try:
        return (Path("/proc") / str(pid) / "stat").read_text().rsplit(")", 1)[1].split()[0] != "Z"
    except (OSError, IndexError):
        return True


def stop_owner(project: str, req: str, *, timeout: float = STOP_SECONDS) -> int:
    """SIGTERM the owner process(es) of this run, SIGKILL after `timeout`. The run state is durable: the next owner
    reconciles whatever was in flight. Returns how many were stopped."""
    pids = owner_pids(project, req)
    for pid in pids:
        with contextlib.suppress(OSError):
            os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + timeout
    while any(_alive(p) for p in pids) and time.monotonic() < deadline:
        time.sleep(0.2)
    for pid in pids:
        if _alive(pid):
            with contextlib.suppress(OSError):
                os.kill(pid, signal.SIGKILL)
    while any(_alive(p) for p in pids) and time.monotonic() < deadline + 5:
        time.sleep(0.1)
    return len(pids)


def bound_plan(rdir: Path):
    """The plan revision the run is bound to (not necessarily the latest frozen one)."""
    db = adapter.run_db_path(rdir)
    conn = sqlite3.connect(f"{db.resolve().as_uri()}?mode=ro", uri=True, timeout=5)
    try:
        doc = json.loads(conn.execute("SELECT doc FROM state WHERE id = 1").fetchone()[0])
    except (TypeError, ValueError) as exc:
        raise core.SchedulerError("STATE_UNREADABLE", f"cannot read the run of {rdir.name}") from exc
    finally:
        conn.close()
    return core.load_plan_file(rdir / adapter.REVISIONS / f"PLAN.r{doc['revision']}.json",
                               approved_sha256=doc["plan_sha256"], plan_id=doc["plan_id"], revision=doc["revision"])


@contextlib.contextmanager
def _opened(rdir: Path):
    """The run's core with the owner lock held: only possible once the owner is gone."""
    plan = bound_plan(rdir)
    with adapter.owner_lock(rdir):
        sch = core.SchedulerCore(plan, core.SqliteRepository(adapter.run_db_path(rdir), create=False))
        sch.inspect()
        yield sch


def _live_attempts(sch) -> list[tuple[str, str, str]]:
    live = {state.value for state in core.states.ATTEMPT_LIVE}
    return sch.read(lambda c: [(a.id, a.task_id, a.state) for a in c.state.attempts.values() if a.state in live])


def status(project: str, req: str, rdir: Path) -> dict:
    from bitacora_platform import scheduler_status
    return scheduler_status.status(rdir, owner_pids(project, req), watcher_pids(project, req), on_hold(rdir))


def recovery_status(rdir: Path) -> dict:
    from bitacora_platform import scheduler_status
    return scheduler_status.recovery_status(rdir)


def recovery_enable(rdir: Path, preview_digest: str, stop_generation: int, by: str = "owner-control") -> dict:
    """Opt ONE existing run into diagnostic recovery from the web control (REQ-029 R7/R9): bound to the run's identity, the
    preview the owner saw and the stop generation. A stale digest, a stop in force or a paused/cancelled run refuses; opening a
    view never calls this."""
    import tempfile
    import uuid

    preview = recovery_preview(rdir)
    if "identity" not in preview or "preview_digest" not in preview:
        return {"enabled": False, "blocker": preview.get("blocker", "preview_unavailable")}
    identity = preview["identity"]
    if preview["preview_digest"] != preview_digest or identity.get("stop_generation") != stop_generation:
        return {"enabled": False, "blocker": "stale_preview_or_stop_generation"}
    if identity.get("paused") or identity.get("cancelled") or on_hold(rdir):
        return {"enabled": False, "blocker": "owner_stop_or_hold"}
    record = {"schema_version": "recovery-policy/1", "run_id": preview["run_id"], "identity": {
        "plan_id": identity.get("plan_id"), "revision": identity.get("revision"), "plan_sha256": identity.get("source_sha256"),
        "stop_generation": identity.get("stop_generation"), "accepted_map_digest": identity.get("accepted_map_digest"),
        "paused": False, "cancelled": False, "live_attempts": identity.get("live_attempts", [])},
        "preview_digest": preview_digest, "authorization_ref": f"owner-control:{uuid.uuid4().hex}", "by": by,
        "limits": {"diagnoses": 1, "corrective_tasks": 8, "supplemental_audits_per_lineage": 1}}
    target = Path(rdir) / "RUN.recovery-policy.json"
    fd, temp = tempfile.mkstemp(prefix=".recovery-policy-", dir=target.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(record, stream, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, target)
    finally:
        Path(temp).unlink(missing_ok=True)
    return {"enabled": True, "authorization_ref": record["authorization_ref"]}


def recovery_preview(rdir: Path) -> dict:
    """Read current M1, M5/M6 and audit-observation identities without activation or diagnosis."""
    try:
        import bt_run_stores

        identity = adapter.revision_identity(rdir)
        marker = json.loads(bt_run_stores.runtime_marker(adapter.run_db_path(rdir)).read_text(encoding="utf-8"))
        run_id = marker.get("runtime_id") if isinstance(marker, dict) else None
        if not isinstance(run_id, str) or not run_id:
            raise ValueError("runtime identity missing")
        stores = bt_run_stores.module_stores(adapter.run_db_path(rdir), run_id)
        source_digests = {}
        for name in ("m5", "m6"):
            path = stores[name]
            if path.is_file():
                source_digests[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        observations = []
        for path in sorted(Path(rdir).glob("RUN.notes/*.audit-observations.jsonl")):
            observations.append({"task": path.stem.split(".", 1)[0],
                                 "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        source_facts = {"module_store_digests": source_digests, "audit_observation_digests": observations}
        activation_path = Path(rdir) / "RUN.recovery-policy.json"
        lifecycle_identity = {"plan_id": identity.get("plan_id"), "revision": identity.get("revision"),
                              "plan_sha256": identity.get("source_sha256"),
                              "stop_generation": identity.get("stop_generation"),
                              "accepted_map_digest": identity.get("accepted_map_digest"),
                              "paused": identity.get("paused", False), "cancelled": identity.get("cancelled", False),
                              "live_attempts": identity.get("live_attempts", [])}
        source_digest = hashlib.sha256(json.dumps(source_facts, sort_keys=True, separators=(",", ":"),
                                                  allow_nan=False).encode()).hexdigest()
        preview_body = {"schema_version": "recovery-preview/1", "run_id": run_id,
                        "identity": lifecycle_identity, "source_digest": source_digest, "sources": source_facts,
                        "activation_present": activation_path.is_file()}
        digest = hashlib.sha256(json.dumps(preview_body, sort_keys=True, separators=(",", ":"),
                                           allow_nan=False).encode()).hexdigest()
        return {"schema_version": "recovery-preview/1", "run_id": run_id, "identity": identity,
                "sources": source_facts,
                "activation_present": activation_path.is_file(), "preview_digest": digest,
                "diagnosis_invoked": False, "decision_answered": False}
    except Exception as error:  # noqa: BLE001 - read-only preview reports unavailable M1 state
        return {"schema_version": "recovery-preview/1", "status": "unavailable",
                "blocker": f"recovery_preview_unavailable:{type(error).__name__}",
                "diagnosis_invoked": False, "decision_answered": False}


def kill_agent(project: str, req: str, attempt_id: str) -> int:
    """Stop what the executor started for this attempt (shim, process group, stragglers in its worktree)."""
    import bt_scheduler_executor_adapter as executor

    return executor.kill_attempt_processes(project, req, attempt_id)


def cancel_attempts(project: str, req: str, rdir: Path, sch, attempt_ids: list[str], reason: str) -> list[str]:
    done = []
    for attempt_id in attempt_ids:
        done.append(f"{attempt_id}: {sch.resolve_attempt(attempt_id, 'cancelled', OPERATOR, reason)}")
        kill_agent(project, req, attempt_id)
    return done


def watching(rdir: Path) -> bool:
    """Whether a watchdog holds this run's lock."""
    import fcntl

    path = watch_lock_path(rdir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return True
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    return False


def ensure_watch(project: str, req: str, rdir: Path) -> bool:
    """Start a detached watchdog unless one is running; True when it started one."""
    if watching(rdir):
        return False
    import bt_scheduler_watch

    bt_scheduler_watch.watch(project, req, rdir, detach=True)
    return True


def direct_continuation(rdir: Path, sch, task_id: str, attempt_id: str) -> str:
    """Tell the next attempt of `task_id` to continue from the accepted result of `attempt_id` (RUN.continue.json). It
    applies to that one start only; the choice is written to the run's audit trail."""
    if not attempt_id:
        raise core.SchedulerError("NOT_ALLOWED", "continue-from needs the accepted attempt to continue from")

    def check(ctx):
        rec = ctx.state.tasks.get(task_id)
        att = ctx.state.attempts.get(attempt_id)
        if rec is None or att is None or attempt_id not in rec.attempts or att.state != "accepted":
            raise core.SchedulerError("NOT_ALLOWED", f"{attempt_id} is not an accepted attempt of {task_id}")
        if rec.state in ("active",):
            raise core.SchedulerError("NOT_ALLOWED", f"{task_id} is running: direct its next attempt before it starts")
        return len(rec.attempts)
    count = sch.read(check)
    path = Path(rdir) / "RUN.continue.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    data[task_id] = {"attempt": attempt_id, "attempts": count}
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return f"{task_id}: its next attempt continues from the accepted result of {attempt_id}"


def _revise_impact(rdir: Path, sch) -> tuple[int, tuple[str, ...]]:
    """(bound revision, the ACCEPTED tasks a rebase onto the latest frozen plan would redo). Nothing is written; any trouble
    reading either plan means "no impact known" (the rebase itself reports its own errors)."""
    try:
        plan, latest = bound_plan(rdir), adapter.approved_plan(rdir)
        if latest.revision <= plan.revision:
            return plan.revision, ()
        would = sch.read(lambda ctx: core.plan_rebase(ctx.state, plan, latest, cascade=adapter.rebase_cascade()))
        done = sch.read(lambda ctx: tuple(t for t in would.reset
                                          if ctx.state.tasks.get(t) and ctx.state.tasks[t].state == "completed"))
        return plan.revision, tuple(done)
    except (core.SchedulerError, OSError, sqlite3.Error, ValueError, KeyError):
        return 0, ()


def _impact_guard(rdir: Path, sch, action: str, lost, confirm: bool) -> None:
    """Refuse an action that would invalidate more accepted tasks than the ceiling without `--confirm`, saying what it costs."""
    import bt_rework_impact as impact

    limit = impact.ceiling()
    if confirm or not limit or len(lost) <= limit:
        return
    cost = impact.estimate(adapter.run_db_path(rdir), lost, bound_plan(rdir))
    raise core.SchedulerError("NOT_ALLOWED", impact.describe(action, cost, limit))


def apply(project: str, req: str, rdir: Path, action: str, target: str = "", reason: str = "",
          keep_held: bool = False, only: bool = False, option: str = "", *, expected_task: str = "",
          expected_task_state: str | None = None, expected_attempt_state: str | None = None,
          confirm: bool = False, block_task: bool = False) -> list[str]:
    from bitacora_platform.scheduler_ops_apply import apply as move

    return move(project, req, rdir, action, target, reason, keep_held, only, option,
                expected_task=expected_task, expected_task_state=expected_task_state,
                expected_attempt_state=expected_attempt_state, confirm=confirm, block_task=block_task)


def _refresh_projection(rdir: Path) -> bool:
    """Rewrite the read model after a move: a held run has no owner to do it, and the plan page would keep showing the
    old routes and states (after a rebase, routes chosen for a previous revision). Best effort."""
    try:
        with _opened(rdir) as sch:
            adapter.write_projection(rdir, sch)
    except Exception:  # noqa: BLE001 - the move itself already succeeded; the owner rewrites it when it runs
        return False
    return True


def retry(project: str, req: str, rdir: Path, task: str, reason: str = "", *, wait: float = 180.0,
          expected_task_state: str | None = None, on_accepted=None) -> list[str]:
    """Cancel a live attempt and reopen its task once Scheduler makes it recoverable.

    A task reopened by a separate operator move is already ready; preserve that state instead of waiting for a block
    which will never arrive. A task already recovering can be reopened directly. `on_accepted()` runs once the task
    state matched `expected_task_state` and before anything is cancelled or reopened (the remote route pin).
    """
    current = status(project, req, rdir)
    task_state = current.get("task_states", {}).get(task)
    if expected_task_state is not None and task_state != expected_task_state:
        raise core.SchedulerError(
            "STALE_PRECONDITION", f"task {task} changed from {expected_task_state} to {task_state}",
        )
    if on_accepted is not None:
        on_accepted()
    attempts = [a["attempt"] for a in current["live_attempts"] if a["task"] == task]
    lines = []
    for attempt in attempts:
        lines += apply(project, req, rdir, "cancel-attempt", attempt, reason,
                       expected_task=task, expected_task_state=expected_task_state)
        expected_task_state = None
    if task_state == "ready":
        return lines + [f"{task}: already ready"]
    if task_state == "recovering":
        return lines + apply(project, req, rdir, "reopen", task, reason,
                             expected_task=task, expected_task_state=expected_task_state)
    if task_state == "blocked" or task in current.get("blocked_tasks", []):
        return lines + apply(project, req, rdir, "reopen", task, reason,
                             expected_task=task, expected_task_state=expected_task_state)
    deadline = time.monotonic() + wait
    while True:
        current = status(project, req, rdir)
        task_state = current.get("task_states", {}).get(task)
        if task_state == "ready":
            return lines + [f"{task}: already ready"]
        if task_state == "recovering" or task_state == "blocked" or task in current.get("blocked_tasks", []):
            return lines + apply(project, req, rdir, "reopen", task, reason)
        if time.monotonic() > deadline:
            return lines + [f"{task}: not blocked after {int(wait)} s; reopen it by hand if it needs to"]
        time.sleep(2)


def _review_cards(rdir: Path, task: str) -> list[dict]:
    import bt_scheduler_decisions as decisions
    return [card for card in decisions.open_requests(rdir) if card.get("source") == "review" and card.get("task") == task]


def review_attempts(rdir: Path, task: str) -> tuple[str, ...]:
    """Read only reviews whose attempts are still waiting in M1; never claim the M6 writer lock."""
    return tuple(dict.fromkeys(card["attempt"] for card in _review_cards(rdir, task) if card.get("attempt")))


def attest(project: str, req: str, rdir: Path, task: str, which: str, evidence: str, by: str = "coordinator", *, requeue: bool = True, expected_attempt: str | None = None) -> list[str]:
    """Leave the coordinator's receipt for the manual check(s) of `task` (`which`: a purpose text or 1-based index; empty =
    every manual check of the task) and send the task's open review back to the verifier, which then finds the receipt."""
    import bt_attestation
    import bt_run_stores
    from bt_scheduler_quality.store import QualityStore

    plan = bound_plan(rdir)
    try:
        checks = bt_attestation.manual_checks(plan, task)
    except core.SchedulerError as exc:
        raise core.SchedulerError("NOT_ALLOWED", f"{task} is not a task of the plan") from exc
    if which:
        picked = [checks[int(which) - 1]] if which.isdigit() and 0 < int(which) <= len(checks) \
            else [c for c in checks if which.lower() in c["purpose"].lower() or which.lower() in c["value"].lower()]
    else:
        picked = checks
    if not picked:
        raise core.SchedulerError("NOT_ALLOWED", f"{task} has no manual check{f' matching {which!r}' if which else ''} to attest")
    lines = []
    attempts: tuple[str, ...] = ("",)
    if bt_config.get("gates.attestation_bind_attempt", True) is True:
        # the receipt covers the attempt being verified: a redone task has to be attested again (REQ-029 A11)
        attempts = review_attempts(rdir, task)
        if not attempts:
            raise core.SchedulerError("NOT_ALLOWED", f"{task} has no verification waiting for evidence: a receipt covers the attempt "
                                      "being verified, so attest once the verifier asks")
    if expected_attempt is not None and attempts != (expected_attempt,):
        raise core.SchedulerError("STALE_PRECONDITION", "the live evidence belongs to a different verification attempt")
    try:
        for check in picked:
            for attempt in attempts:
                path = bt_attestation.mint(rdir, task, check["purpose"], check["value"], check["expected"], evidence, by,
                                           attempt=attempt)
                lines.append(f"attested {task}{'@' + attempt if attempt else ''}: «{check['purpose'][:80]}» -> {path.name}")
    except bt_attestation.AttestationError as exc:
        raise core.SchedulerError("NOT_ALLOWED", str(exc)) from exc
    if not requeue:
        return lines
    with hold(rdir, f"attestation of {task}"):
        stopped = stop_owner(project, req)
        with adapter.owner_lock(rdir):
            cards = [card for card in _review_cards(rdir, task) if card.get("attempt") in attempts]
            store = QualityStore(bt_run_stores.paths(rdir)["m6"])
            try:
                for card in cards:
                    try:
                        store.retry_attested(card["id"], by, f"manual evidence attested by {by}: {evidence[:120]}")
                        lines.append(f"verification of {task} requeued: the verifier will find the receipt")
                    except Exception as exc:  # noqa: BLE001 - QualityError: not only manual evidence, or already retried
                        lines.append(f"verification of {task} stays for a person ({getattr(exc, 'code', type(exc).__name__)})")
            finally:
                store.close()
        lines.insert(0, f"owner stopped: {stopped} process(es)")
    return lines


def resume(project: str, req: str, rdir: Path) -> str:
    """Release a hold and make sure something is watching the run."""
    hold_path(rdir).unlink(missing_ok=True)
    return "watchdog started" if ensure_watch(project, req, rdir) else "a watchdog is already running"
