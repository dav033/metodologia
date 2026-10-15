"""`AgentExecutor`: runs authorised orders as supervised agent processes and preserves their work.

Flow of an attempt (every arrow is one atomic ledger transition; a crash between two of them is recovered):

    start -> QUEUED -> PREPARING (route + brief + worktree + spawn shim) -> RUNNING (started event)
          -> SETTLING (outcome persisted; handoff captured) -> FINISHED | FAILED | CANCELLED (terminal event, same txn)

The executor never decides who runs (M2 route), whether a retry is worthwhile (M5) or whether work is acceptable (the
independent verifier). A clean exit is reported as `execution_finished` = "the agent stopped", nothing more.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from . import artifacts, procinfo
from . import model as m
from .config import Config
from .errors import ExecutorError
from .ledger import Ledger
from .model import AttemptStatus, Receipt, StartRequest, TechnicalEvent
from .ports import AgentDriver, BriefSource, EventSink, RouteResolver, WorkspaceManager
from .recovery import RecoverMixin
from .settle import SettleMixin
from .spawn import SpawnMixin
from .workspace import dirname_of

SHIM = Path(__file__).with_name("shim.py")
LOG_MAX = 1 << 20


class AgentExecutor(SpawnMixin, SettleMixin, RecoverMixin):
    def __init__(self, root: Path | str, *, resolver: RouteResolver, briefs: BriefSource, driver: AgentDriver,
                 workspaces: WorkspaceManager, sink: EventSink, config: Config | None = None,
                 clock: Callable[[], float] = time.time, python: str | None = None, autostart: bool = True):
        procinfo.require_posix()
        self.cfg = (config or Config()).validate()
        self.root = Path(root).resolve()         # worktrees and the shim run with other cwds: never a relative root
        self.resolver, self.briefs, self.driver, self.workspaces, self.sink = resolver, briefs, driver, workspaces, sink
        self.clock = clock
        self.python = python or sys.executable
        self.shim_path = SHIM
        self.attempts_dir = self.root / "attempts"
        try:
            self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
            os.chmod(self.root, 0o700)               # the ledger, logs and worktrees are the owner's business only
            self.attempts_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        except OSError as error:
            raise ExecutorError("ARTIFACT_ERROR", f"cannot create {self.attempts_dir}: {type(error).__name__}") from None
        self._lock_handle = self._take_root()
        self.ledger = Ledger(self.root / "ledger.db", clock=clock)
        self._guard = threading.RLock()
        self._starting: set[str] = set()       # submitted to the prepare pool, not yet running or settled
        self._settling: set[str] = set()       # settle jobs in flight
        self._procs: dict[str, subprocess.Popen] = {}
        self._heartbeat: dict[str, tuple[float, int]] = {}
        self._cancel_sent: dict[str, float] = {}
        self._settle_tried: dict[str, float] = {}
        self._prepare_tried: dict[str, float] = {}
        self._settle_busy: set[str] = set()
        self._deliver_lock = threading.Lock()
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._prep_pool = ThreadPoolExecutor(max_workers=self.cfg.max_running, thread_name_prefix="m3-prepare")
        self._settle_pool = ThreadPoolExecutor(max_workers=self.cfg.max_running, thread_name_prefix="m3-settle")
        self._thread: threading.Thread | None = None
        self._recover()
        if autostart:
            self.start_loop()

    def _take_root(self):
        """One live supervisor per root: a second one would race the first for the same queue and processes."""
        import fcntl
        handle = open(self.root / "executor.lock", "a+")
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            handle.close()
            raise ExecutorError("ROOT_BUSY", f"another executor is serving {self.root}") from None
        return handle

    # ================================================================================================ lifecycle
    def start_loop(self) -> None:
        if self._thread is None or not self._thread.is_alive():
            self._stop.clear()
            self._thread = threading.Thread(target=self._loop, name="m3-supervisor", daemon=True)
            self._thread.start()

    def close(self, wait: bool = True) -> None:
        """Stop supervising. Agent processes are NOT stopped: they belong to their shims and survive (that is the point);
        a later executor on the same root picks them up. Use `cancel` to stop an attempt."""
        self._stop.set()
        self._wake.set()
        if self._thread is not None:
            self._thread.join(timeout=10)
        for proc in list(self._procs.values()):          # the launchers exit at once; reap them (the shims live on)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
        self._procs.clear()
        self._prep_pool.shutdown(wait=wait, cancel_futures=True)
        self._settle_pool.shutdown(wait=wait, cancel_futures=True)
        try:
            self._lock_handle.close()                    # releases the root lock
        except OSError:
            pass

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.tick()
            except Exception as error:
                self._log(f"tick error: {type(error).__name__}: {error}")
            self._wake.wait(self.cfg.poll_seconds)
            self._wake.clear()

    def _log(self, line: str) -> None:
        try:
            path = self.root / "executor.log"
            if path.exists() and path.stat().st_size > LOG_MAX:      # one old generation is kept; never unbounded
                os.replace(path, path.with_suffix(".log.1"))
            with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600), "a", encoding="utf-8") as stream:
                stream.write(f"{self._iso()} {line[:500]}\n")
        except OSError:
            pass

    def _iso(self) -> str:
        return dt.datetime.fromtimestamp(self.clock(), dt.UTC).isoformat(timespec="seconds")

    # ================================================================================================ M1 operations
    def start(self, request: StartRequest) -> Receipt:
        """Accept an order exactly once. Everything refusable is refused here, before any process or worktree exists."""
        try:
            if not isinstance(request, StartRequest):
                raise ExecutorError("ORDER_INVALID", "not a StartRequest")
            request.validate()
            if not self.ledger.run_matches(request.plan_id, request.revision):
                return Receipt("rejected", "FOREIGN_RUN", "this executor serves another plan/revision", request.attempt_id)
            replay = self.ledger.by_key(request.idempotency_key)
            if replay is not None:
                return self._replay(replay, request)
            route = self._guard_port(lambda: self.resolver.resolve(request))
            base_sha = self._guard_port(lambda: self.workspaces.check(request))
            dirname = dirname_of(request.attempt_id)
            adir = self.attempts_dir / dirname
            try:
                adir.mkdir(parents=True, exist_ok=True, mode=0o700)
            except OSError as error:
                raise ExecutorError("ARTIFACT_ERROR", f"{type(error).__name__}") from None
            row, created = self.ledger.insert(request, dirname=dirname, state=m.QUEUED, route=route.to_dict(),
                                              max_queued=self.cfg.max_queued, max_backlog=self.cfg.max_event_backlog,
                                              base_sha=base_sha if isinstance(base_sha, str) else None)
        except ExecutorError as error:
            if isinstance(request, StartRequest) and error.code in ("FOREIGN_RUN", "KEY_CONFLICT"):
                try:
                    (self.attempts_dir / dirname_of(request.attempt_id)).rmdir()   # a refused order leaves no empty directory
                except OSError:
                    pass
            return self._reject(request, error)
        if row["state"] == m.REJECTED:
            if created:
                try:
                    adir.rmdir()                        # nothing was started: leave no empty directory behind
                except OSError:
                    pass
            rejection = row["rejection"] or {}
            return Receipt("rejected", rejection.get("code", "QUEUE_FULL"), rejection.get("detail", ""), request.attempt_id)
        if created:
            try:
                artifacts.write_json(adir / "order.json", request.to_dict())
                artifacts.write_json(adir / "route.json", route.to_dict())
            except ExecutorError as error:
                self._log(f"artifact write failed for {request.attempt_id}: {error.detail}")
            self._wake.set()
            return Receipt("accepted", attempt_id=request.attempt_id)
        return Receipt("duplicate", attempt_id=request.attempt_id)

    def _guard_port(self, call):
        try:
            return call()
        except ExecutorError:
            raise
        except Exception as error:
            raise ExecutorError("PORT_ERROR", type(error).__name__) from None

    def _replay(self, row: dict[str, Any], request: StartRequest) -> Receipt:
        if row["request"] != _normal(request.to_dict()):
            return Receipt("rejected", "KEY_CONFLICT", "the idempotency key was used with a different order",
                           request.attempt_id)
        if row["state"] == m.REJECTED:
            rejection = row["rejection"] or {}
            return Receipt("rejected", rejection.get("code", ""), rejection.get("detail", ""), request.attempt_id)
        return Receipt("duplicate", attempt_id=request.attempt_id)

    def _reject(self, request: object, error: ExecutorError) -> Receipt:
        attempt_id = getattr(request, "attempt_id", "") if isinstance(request, StartRequest) else ""
        if isinstance(request, StartRequest) and error.code not in ("KEY_CONFLICT", "LEDGER_ERROR", "ARTIFACT_ERROR", "ORDER_INVALID",
                                                                  "FOREIGN_RUN", "PORT_ERROR"):   # only deterministic refusals are sticky
            try:      # a refusal is part of the record: the same key answers the same way on replay
                self.ledger.insert(request, dirname=dirname_of(request.attempt_id), state=m.REJECTED,
                                   rejection={"code": error.code, "detail": error.detail[:300]})
            except ExecutorError:
                pass
        return Receipt("rejected", error.code, error.detail[:300], str(attempt_id))

    def cancel(self, attempt_id: str, token: int, key: str, reason: str = "") -> Receipt:
        row = self.ledger.get(attempt_id)
        if row is None:
            return Receipt("rejected", "UNKNOWN_ATTEMPT", "no such attempt", attempt_id)
        if row["request"]["token"] != token:
            return Receipt("rejected", "TOKEN_MISMATCH", "fencing token does not match", attempt_id)
        verdict = self.ledger.request_cancel(attempt_id, key, reason)
        if verdict == "terminal":
            return Receipt("duplicate", detail=f"already {row['state']}", attempt_id=attempt_id)
        if verdict == "duplicate":
            return Receipt("duplicate", detail="cancel already requested", attempt_id=attempt_id)
        row = self.ledger.get(attempt_id) or row
        if row["state"] == m.QUEUED:        # never started: no process will ever exist
            exit_info = {"reason": "cancelled", "returncode": None}
            if self.ledger.transition(attempt_id, m.SETTLING, expect=(m.QUEUED,),
                                      outcome=self._outcome_for(row, exit_info)):
                self._submit_settle(attempt_id, None)
        else:
            self._wake.set()                 # the supervisor signals a running shim; a preparing job checks the flag
        return Receipt("accepted", attempt_id=attempt_id)

    def query(self, attempt_id: str) -> AttemptStatus:
        """What is really going on, not only what the ledger last said."""
        row = self.ledger.get(attempt_id)
        if row is None:
            return AttemptStatus("not_found", "no record of this attempt")
        state = row["state"]
        gone = False
        if state == m.RUNNING:
            gone = self._watch(row, act=False)           # a query observes: it never signals or emits (it may start a settle)
            row = self.ledger.get(attempt_id) or row
            state = row["state"]
        outcome = row.get("outcome") or {}
        if state == m.RUNNING:
            return AttemptStatus(m.SETTLING, "the process is gone; the outcome is being settled") if gone \
                else AttemptStatus("running")
        if state in (m.QUEUED, m.PREPARING, m.SETTLING):
            return AttemptStatus(state, outcome.get("cause", ""))
        if state == m.REJECTED:
            return AttemptStatus("failed", (row.get("rejection") or {}).get("detail", ""), "rejected")
        return AttemptStatus(state, outcome.get("detail", ""), outcome.get("cause", ""), row.get("handoff") or {})

    # ================================================================================================ the loop
    def tick(self) -> None:
        for phase in (self._deliver, self._reap, self._watch_all, self._retry_settling, self._retry_preparing,
                      self._schedule):
            try:                       # one failing phase (a corrupt row, a sink bug) must not starve the others
                phase()
            except Exception as error:
                self._log(f"{phase.__name__} failed: {type(error).__name__}: {error}")

    def _reap(self) -> None:
        for attempt_id, proc in list(self._procs.items()):   # our own launchers: no zombies
            if proc.poll() is not None:
                self._procs.pop(attempt_id, None)

    def _watch_all(self) -> None:
        for row in self.ledger.in_states((m.RUNNING,)):
            try:
                self._watch(row)
            except Exception as error:
                self._log(f"watch of {row['attempt_id']} failed: {type(error).__name__}: {error}")

    def _retry_preparing(self) -> None:
        """A PREPARING attempt that no job is driving (its settle failed transiently, a job died) is not left holding a
        slot forever: after the retry delay it is reconciled like after a restart."""
        now = time.monotonic()
        for row in self.ledger.in_states((m.PREPARING,)):
            attempt_id = row["attempt_id"]
            if attempt_id in self._starting or attempt_id in self._settle_busy \
                    or now - self._prepare_tried.get(attempt_id, -1e9) < self.cfg.settle_retry_seconds:
                continue
            self._prepare_tried[attempt_id] = now
            self._reconcile_preparing(row)

    def _retry_settling(self) -> None:
        """A settle that failed (disk, git, ledger hiccup) is retried, slowly: the attempt must not stay SETTLING forever."""
        now = time.monotonic()
        for row in self.ledger.in_states((m.SETTLING,)):
            attempt_id = row["attempt_id"]
            if attempt_id in self._settling or now - self._settle_tried.get(attempt_id, -1e9) < self.cfg.settle_retry_seconds:
                continue
            self._settle_tried[attempt_id] = now
            self._submit_settle(attempt_id, None)

    def _schedule(self) -> None:
        with self._guard:
            busy = {r["attempt_id"] for r in self.ledger.in_states((m.PREPARING, m.RUNNING))} | self._starting
            room = self.cfg.max_running - len(busy)
            if room <= 0:
                return
            for row in self.ledger.in_states((m.QUEUED,), limit=room + len(self._starting)):
                if room <= 0:
                    break
                if row["attempt_id"] in self._starting:
                    continue
                self._starting.add(row["attempt_id"])
                self._prep_pool.submit(self._launch_job, row["attempt_id"])
                room -= 1

    def wake(self) -> None:
        self._wake.set()

    # ================================================================================================ events
    def _event(self, row: dict[str, Any], kind: str, suffix: str, payload: Mapping[str, Any]) -> TechnicalEvent:
        req = row["request"]
        return TechnicalEvent(f"{req['attempt_id']}:{suffix}", kind, req["plan_id"], req["revision"], req["task_id"],
                              req["attempt_id"], req["token"], self._iso(), dict(payload))

    def _deliver(self) -> None:
        """Deliver pending events in ledger order. One that fails stays in the outbox and holds back only ITS OWN
        attempt's later events (their order matters); other attempts' events go on (no global head-of-line blocking)."""
        with self._deliver_lock:
            held: set[str] = set()
            for event in self.ledger.pending_events(self.cfg.deliver_batch):
                if event.attempt_id in held:
                    continue
                try:
                    self.sink.deliver(event)
                except Exception:
                    held.add(event.attempt_id)
                    continue
                self.ledger.mark_delivered(event.event_id)

    def flush_events(self) -> int:
        """Deliver what is pending now; returns how many remain."""
        self._deliver()
        return self.ledger.undelivered()

    # ================================================================================================ watching
    def _watch(self, row: dict[str, Any], act: bool = True) -> bool:
        """Look at one RUNNING attempt. True when its process is gone (a settle was, or already is, in flight)."""
        attempt_id = row["attempt_id"]
        if attempt_id in self._settling:
            return True
        adir = self.attempts_dir / row["dirname"]
        exit_info = artifacts.read_exit(adir / "exit.json")
        if exit_info:
            self._submit_settle(attempt_id, exit_info)
            return True
        shim = row.get("shim") or {}
        alive = procinfo.alive(shim.get("pid"), shim.get("ident"))
        if act and row["cancel_requested"] and alive:
            self._enforce_cancel(attempt_id, shim, adir)
        if alive:
            if act:
                self._beat(row)
            return False
        exit_info = artifacts.read_exit(adir / "exit.json")      # written before the shim exits: re-read after the death check
        if exit_info:
            self._submit_settle(attempt_id, exit_info)
            return True
        self._submit_settle(attempt_id, {"reason": "lost", "returncode": None, "adopt_orphan": True})
        return True

    def _enforce_cancel(self, attempt_id: str, shim: dict[str, Any], adir: Path) -> None:
        sent = self._cancel_sent.get(attempt_id)
        now = time.monotonic()
        if sent is None:
            self._cancel_sent[attempt_id] = now
            procinfo.signal_pid(shim["pid"], signal.SIGTERM)
        elif now - sent > self.cfg.grace_seconds * 3 + 5:        # the shim ignored us: stop the agent group ourselves
            info = artifacts.read_shim(adir / "shim.json")
            self._kill_child(info)
            procinfo.signal_pid(shim["pid"], signal.SIGKILL)

    def _beat(self, row: dict[str, Any]) -> None:
        attempt_id = row["attempt_id"]
        now = self.clock()
        if attempt_id not in self._heartbeat:        # the first hint comes one interval after we first saw it alive
            self._heartbeat[attempt_id] = (now, 0)
            return
        last, n = self._heartbeat[attempt_id]
        if now - last < self.cfg.heartbeat_seconds:
            return
        self._heartbeat[attempt_id] = (now, n + 1)
        if self.ledger.has_undelivered(attempt_id):     # never let a hint overtake the attempt's own pending events
            return
        try:
            with self._deliver_lock:
                self.sink.deliver(self._event(row, m.EV_HEARTBEAT, f"hb:{int(now * 1000)}", {"seq": n + 1}))
        except Exception:  # noqa: BLE001 - a heartbeat is a hint; never stored, never retried
            pass

    @staticmethod
    def _kill_child(info: Mapping[str, Any]) -> bool:
        """Stop the agent's group if (and only if) the recorded leader is still the same process."""
        pid, ident = info.get("child_pid"), info.get("child_ident")
        if pid and procinfo.alive(pid, ident):
            try:
                if os.getpgid(pid) != (info.get("child_pgid") or pid):      # not the group we recorded: do not signal it
                    return False
            except ProcessLookupError:
                return False
            procinfo.signal_group(info.get("child_pgid") or pid, signal.SIGKILL)
            return True
        return False

    # ================================================================================================ helpers
    def wait_idle(self, timeout: float = 30.0) -> bool:
        """Block until no attempt is live and every event is delivered (tests, CLI)."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if not self.ledger.count(m.LIVE) and not self._starting and not self._settling \
                    and self.ledger.undelivered() == 0:
                return True
            self._wake.set()
            time.sleep(0.02)
        return False

    def wait_state(self, attempt_id: str, states: tuple[str, ...], timeout: float = 30.0) -> str | None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            row = self.ledger.get(attempt_id)
            if row and row["state"] in states:
                return row["state"]
            time.sleep(0.02)
        return None

    def describe(self, attempt_id: str) -> dict[str, Any] | None:
        row = self.ledger.get(attempt_id)
        if row is None:
            return None
        return {"attempt_id": attempt_id, "state": row["state"], "outcome": row.get("outcome"),
                "handoff": row.get("handoff"), "artifacts": artifacts.paths(self.attempts_dir / row["dirname"])}


def _normal(value: Any) -> Any:
    return json.loads(json.dumps(value, sort_keys=True))
