"""Watchdog for a Scheduler run: keeps one owner process alive until the run reaches a terminal state.

The owner (`scheduler-run`) is durable but not self-healing: a crash, an OOM kill or a SIGBUS on a full disk left the run
stopped until someone resumed it by hand. The watchdog resumes it, backs off between restarts, waits while the disk is
nearly full or a move holds the run (`bt_scheduler_ops.hold`), and gives up, with a notification, when the owner keeps
dying or fails for a reason a restart cannot fix.
"""
from __future__ import annotations

import collections
import contextlib
import fcntl
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable

import bt_notify
import bt_scheduler_adapter as adapter
import bt_scheduler_ops as ops

POLL_SECONDS = 5.0
HEAL_LIMIT = 3                # automatic answers of one kind per task before a person is asked again
BACKOFF_START = 5.0
BACKOFF_CAP = 300.0
MAX_FAILURES = 5              # this many failed owners within FAILURE_WINDOW end the watch
FAILURE_WINDOW = 1800.0
HEALTHY_SECONDS = 600.0       # an owner that ran this long before dying does not count against the budget
MIN_FREE_BYTES = 1 << 30
# `scheduler-run` exit codes: 0 the run is terminal or stalled, 2 a refusal a restart cannot change (plan mismatch,
# missing binding, unsafe store), 3 or a signal an unexpected crash worth retrying.
PERMANENT = frozenset({2})


class Watch:
    def __init__(self, project: str, req: str, rdir: Path, *, now: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep, spawn: Callable[[bool], "subprocess.Popen"] | None = None,
                 free_bytes: Callable[[], int] | None = None, notify: Callable[[str, str], None] = bt_notify.notify,
                 log: Callable[[str], None] | None = None, announce: Callable[[], object] | None = None,
                 pending: Callable[[], int] | None = None, heal: Callable[[], bool] | None = None):
        self.project, self.req, self.rdir = project, req, Path(rdir)
        self.now, self.sleep, self.notify = now, sleep, notify
        self.spawn = spawn or self._spawn
        self.free_bytes = free_bytes or (lambda: shutil.disk_usage(self.rdir).free)
        self.announce = announce or self._announce
        self.pending = pending or self._pending
        self.heal = heal or self._heal
        self.log = log or (lambda text: print(f"{time.strftime('%H:%M:%S')} {text}", flush=True))
        self.failures: collections.deque[float] = collections.deque()
        self.backoff = BACKOFF_START
        self.low_disk_notified = False

    def _spawn(self, resume: bool) -> "subprocess.Popen":
        cli = Path(__file__).with_name("bitacora.py")
        argv = [sys.executable, str(cli), "--project", self.project, "scheduler-run", self.req]
        if resume:
            argv.append("--resume")
        return subprocess.Popen(argv, stdin=subprocess.DEVNULL, close_fds=True, start_new_session=True)

    def _has_run(self) -> bool:
        return adapter.authority(self.rdir) == adapter.AUTHORITY

    def _wait_owner_gone(self) -> None:
        while ops.owner_pids(self.project, self.req):
            self.sleep(POLL_SECONDS)

    def _fail(self, why: str) -> bool:
        """Record one failed owner; True when the budget is spent."""
        now = self.now()
        self.failures.append(now)
        while self.failures and now - self.failures[0] > FAILURE_WINDOW:
            self.failures.popleft()
        if len(self.failures) >= MAX_FAILURES:
            self.log(f"giving up: {len(self.failures)} failures within {int(FAILURE_WINDOW // 60)} min ({why})")
            self.notify(f"Bitácora · {self.req}", f"El scheduler de {self.req} se cayó {len(self.failures)} veces seguidas ({why}); "
                                                  "el vigilante se detuvo. Revisa el log y reanuda con scheduler-watch.")
            return True
        return False

    def run(self, max_loops: int | None = None) -> int:
        """0 when the run ended on its own, 4 when the watch gave up, 2 when the owner refuses to start for good."""
        loops = 0
        while max_loops is None or loops < max_loops:
            loops += 1
            if ops.on_hold(self.rdir):
                self.sleep(POLL_SECONDS)
                continue
            if ops.owner_pids(self.project, self.req):
                self._wait_owner_gone()
                continue
            if self._remediate() or self.heal():
                continue
            if self.free_bytes() < MIN_FREE_BYTES:
                if not self.low_disk_notified:
                    self.low_disk_notified = True
                    self.log("disk almost full: waiting before restarting the owner")
                    self.notify(f"Bitácora · {self.req}", "Disco casi lleno: el scheduler no se reinicia hasta liberar espacio.")
                self.sleep(60.0)
                continue
            self.low_disk_notified = False
            started = self.now()
            owner = self.spawn(self._has_run())
            self.log(f"owner started (pid {owner.pid})")
            code = self._wait(owner)
            if code == 0:
                if self._remediate():
                    continue
                if self._wait_for_decisions():
                    continue
                self.log("owner finished: the run is terminal or stalled")
                return 0
            if ops.on_hold(self.rdir) or code == -signal.SIGTERM:      # stopped on purpose, not a crash
                continue
            ran = self.now() - started
            self.log(f"owner exited with {code} after {int(ran)} s")
            if code in PERMANENT:
                self.notify(f"Bitácora · {self.req}", f"El scheduler de {self.req} no arranca (código {code}); revisa el log.")
                return 2
            if ran >= HEALTHY_SECONDS:
                self.failures.clear()
                self.backoff = BACKOFF_START
            if self._fail(f"exit {code}"):
                return 4
            self.log(f"restarting in {int(self.backoff)} s")
            self.sleep(self.backoff)
            self.backoff = min(BACKOFF_CAP, self.backoff * 2)
        return 0

    def _remediate(self) -> bool:
        """An audit asked for remediation tasks (REQ-028): put them in the plan, rebase the run onto it, and run again."""
        import bt_remediation

        if not bt_remediation.requested(self.rdir):
            return False
        self.log("an audit's findings become remediation tasks: new plan revision")
        try:
            for line in ops.apply(self.project, self.req, self.rdir, "remediate",
                                  reason="audit findings become remediation tasks"):
                self.log(line)
        except Exception as error:  # noqa: BLE001 - a failed move must not loop: drop the request, the gate falls back
            self.log(f"remediation failed ({type(error).__name__}: {error}); request dropped")
            bt_remediation.clear_request(self.rdir)
        return True

    def _heal(self) -> bool:
        """A stop whose diagnosis is a plain integration clash is answered by the scheduler itself: redo the task that
        was built on a stale result, as the card's recommended option does. It used to wait for a person (REQ-027 asked
        24 such cards); `HEAL_LIMIT` automatic answers per task keep a loop from running unnoticed, after which the card
        stays for the owner. Nothing else is ever answered here."""
        import bt_scheduler_decisions as decisions

        try:
            requests = decisions.open_requests(self.rdir)
        except Exception:  # noqa: BLE001 - a run without readable state asks nothing
            return False
        for request in requests:
            diagnosis = request.get("diagnosis") or {}
            if (diagnosis.get("kind"), diagnosis.get("option"), diagnosis.get("confidence")) != ("conflict", "rework_conflict", "alta"):
                continue
            if "rework_conflict" not in {o["id"] for o in request.get("options") or ()}:
                continue
            if decisions.automatic_answers(self.rdir, request["task"], "rework_conflict") >= HEAL_LIMIT:
                continue
            try:
                lines = decisions.answer(self.project, self.req, self.rdir, request["id"], "rework_conflict",
                                         reason="automatic: " + str(diagnosis.get("headline") or "integration clash"),
                                         by="scheduler")
            except Exception as error:  # noqa: BLE001 - a failed move leaves the card for a person
                self.log(f"automatic answer for {request['id']} failed ({type(error).__name__}: {error})")
                continue
            for line in lines:
                self.log(f"automatic: {line}")
            return True
        return False

    def _pending(self) -> int:
        import bt_scheduler_decisions

        try:
            return len(bt_scheduler_decisions.open_requests(self.rdir))
        except Exception:  # noqa: BLE001 - a run without readable state asks nothing
            return 0

    def _wait_for_decisions(self) -> bool:
        """A stalled run that asks its owner something is not finished: wait for the answer, then run again. Waiting is
        the safe state, so no timeout ever answers for the owner."""
        if not self.pending():
            return False
        self.log("the run waits for a decision of its owner")
        while self.pending():
            if self.heal():
                return True
            self.announce()
            self.sleep(POLL_SECONDS * 4)
        return True

    def _announce(self) -> None:
        import bt_scheduler_decisions

        bt_scheduler_decisions.announce(self.project, self.req, self.rdir,
                                        diagnose=bt_scheduler_decisions.auto_diagnoser(self.project, self.req, self.rdir))

    def _wait(self, owner) -> int:
        while True:
            code = owner.poll()
            if code is not None:
                return code
            self.announce()
            self.heal()                       # a clash card is answered while the owner keeps working on the rest
            self.sleep(POLL_SECONDS)


@contextlib.contextmanager
def single_instance(rdir: Path):
    """One watchdog per run: a second one exits quietly."""
    path = ops.watch_lock_path(rdir)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            yield False
            return
        yield True
    finally:
        handle.close()


def log_path(project: str, req: str) -> Path:
    import bt_core

    return bt_core.STATE / "watch" / f"{project}-{req}.log"


def watch(project: str, req: str, rdir: Path, *, detach: bool = False) -> int:
    if detach:
        path = log_path(project, req)
        path.parent.mkdir(parents=True, exist_ok=True)
        cli = Path(__file__).with_name("bitacora.py")
        with path.open("ab") as out:
            process = subprocess.Popen([sys.executable, str(cli), "--project", project, "scheduler-watch", req],
                                       stdin=subprocess.DEVNULL, stdout=out, stderr=out, start_new_session=True,
                                       close_fds=True)
        print(f"watchdog started (pid {process.pid}); log: {path}")
        return 0
    with single_instance(rdir) as first:
        if not first:
            print(f"another watchdog already runs {req}")
            return 0
        os.environ.setdefault("PYTHONFAULTHANDLER", "1")
        return Watch(project, req, rdir).run()
