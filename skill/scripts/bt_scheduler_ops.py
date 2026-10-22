"""Operator moves on a Scheduler run: stop its owner, cancel a live attempt (and its agent), reopen a blocked task,
send accepted work back for rework, revise the run onto the latest frozen plan. Each one used to be a throwaway Python snippet.

Every move that writes needs the owner stopped (M1 allows one owner), and the watchdog (`bt_scheduler_watch`) would
restart it at once, so a move first puts a `hold` on the run; the watchdog honours it, and the move releases it when done.
"""
from __future__ import annotations

import contextlib
import json
import os
import signal
import sqlite3
import time
from pathlib import Path

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


@contextlib.contextmanager
def hold(rdir: Path, why: str, keep: bool = False):
    """Keep the watchdog from restarting the owner while a move is in progress."""
    path = hold_path(rdir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"why": why, "pid": os.getpid(), "at": time.time()}) + "\n", encoding="utf-8")
    try:
        yield
    finally:
        if not keep:
            path.unlink(missing_ok=True)


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
    out = {"owner_pids": owner_pids(project, req), "watcher_pids": watcher_pids(project, req),
           "hold": on_hold(rdir)}
    conn = sqlite3.connect(f"{adapter.run_db_path(rdir).resolve().as_uri()}?mode=ro", uri=True, timeout=5)
    try:
        doc = json.loads(conn.execute("SELECT doc FROM state WHERE id = 1").fetchone()[0])
    finally:
        conn.close()
    live = {s.value for s in core.states.ATTEMPT_LIVE}
    out["revision"] = doc.get("revision")
    out["live_attempts"] = [{"attempt": a["id"], "task": a["task_id"], "state": a["state"]}
                            for a in doc.get("attempts", {}).values() if a.get("state") in live]
    try:
        import bt_scheduler_decisions
        out["open_decisions"] = [r["id"] for r in bt_scheduler_decisions.open_requests(rdir)]
    except Exception:  # noqa: BLE001 - status must answer even when the run has no readable state
        out["open_decisions"] = []
    out["blocked_tasks"] = [t for t, r in doc.get("tasks", {}).items() if r.get("state") == "blocked"]
    out["task_states"] = {task: record.get("state") for task, record in doc.get("tasks", {}).items()
                          if isinstance(record, dict) and isinstance(record.get("state"), str)}
    return out


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


def apply(project: str, req: str, rdir: Path, action: str, target: str = "", reason: str = "",
          keep_held: bool = False, only: bool = False, option: str = "", *, expected_task: str = "",
          expected_task_state: str | None = None, expected_attempt_state: str | None = None) -> list[str]:
    """Run one operator move; the owner is stopped first and the watchdog restarts it afterwards."""
    lines: list[str] = []
    why = reason or f"operator {action}"
    with hold(rdir, why, keep=keep_held):
        lines.append(f"owner stopped: {stop_owner(project, req)} process(es)")
        if action == "stop":
            return lines
        if action == "remediate":
            import bt_remediation
            built = bt_remediation.apply(rdir)
            if built is None:
                return [*lines, "nothing to remediate (no request, or its tasks cannot be built: the named tasks are "
                                "sent back by the next rejection)"]
            lines.append(f"remediation of {built['audit']} round {built['round']}: plan r{built['revision']} adds "
                         f"{', '.join(built['tasks'])}")
            action = "revise"
            why = f"{why}: {built['audit']} findings remediated by {', '.join(built['tasks'])}"
        with _opened(rdir) as sch:
            if expected_task_state is not None:
                actual_state = sch.read(lambda ctx: ctx.state.tasks.get(expected_task).state
                                        if expected_task in ctx.state.tasks else None)
                if actual_state != expected_task_state:
                    raise core.SchedulerError(
                        "STALE_PRECONDITION",
                        f"task {expected_task} changed from {expected_task_state} to {actual_state}",
                    )
            if expected_attempt_state is not None:
                actual_state = sch.read(lambda ctx: ctx.state.attempts[target].state
                                        if target in ctx.state.attempts else None)
                if actual_state != expected_attempt_state:
                    raise core.SchedulerError(
                        "STALE_PRECONDITION",
                        f"attempt {target} changed from {expected_attempt_state} to {actual_state}",
                    )
            if action == "cancel-attempt":
                lines += cancel_attempts(project, req, rdir, sch, [target], why)
            elif action == "reopen":
                sch.reopen(target, OPERATOR, why)
                lines.append(f"{target}: reopened")
            elif action == "rework":
                tasks = tuple(item.strip() for item in target.split(",") if item.strip())
                moved = sch.rework(tasks, OPERATOR, why, cascade=not only)
                lines.append(f"sent back for rework: {', '.join(moved) or 'nothing (already pending)'}")
            elif action == "continue-from":
                lines.append(direct_continuation(rdir, sch, target, option))
            elif action == "withdraw-rework":
                tasks = tuple(item.strip() for item in target.split(",") if item.strip())
                restored = sch.withdraw_rework(tasks, OPERATOR, why)
                lines.append(f"rework taken back (completed again on their accepted result): {', '.join(restored)}")
            elif action == "revise":
                live = [a for a, _, _ in _live_attempts(sch)]
                lines += cancel_attempts(project, req, rdir, sch, live, f"{why}: superseded by a plan revision")
            else:
                raise core.SchedulerError("NOT_ALLOWED", f"unknown action {action}")
        if action == "revise":
            report = adapter.rebase_to_latest(rdir)
            import bt_scheduler_run
            bt_scheduler_run.rebind_runtime(rdir)
            lines.append(f"rebase r{report.from_revision} → r{report.to_revision}: kept {len(report.kept)}, "
                         f"redo {len(report.reset)}, new {len(report.added)}, removed {len(report.removed)}")
        _refresh_projection(rdir)
    return lines


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
          expected_task_state: str | None = None) -> list[str]:
    """Cancel a live attempt and reopen its task once Scheduler makes it recoverable.

    A task reopened by a separate operator move is already ready; preserve that state instead of waiting for a block
    which will never arrive. A task already recovering can be reopened directly.
    """
    current = status(project, req, rdir)
    task_state = current.get("task_states", {}).get(task)
    if expected_task_state is not None and task_state != expected_task_state:
        raise core.SchedulerError(
            "STALE_PRECONDITION", f"task {task} changed from {expected_task_state} to {task_state}",
        )
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


def resume(project: str, req: str, rdir: Path) -> str:
    """Release a hold and make sure something is watching the run."""
    hold_path(rdir).unlink(missing_ok=True)
    return "watchdog started" if ensure_watch(project, req, rdir) else "a watchdog is already running"
