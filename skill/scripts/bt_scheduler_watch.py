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
import json
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
COORDINATE_SECONDS = 30.0
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
                 pending: Callable[[], int] | None = None, heal: Callable[[], bool] | None = None,
                 capture: Callable[[], str] | None = None, coordinate: Callable[[], bool] | None = None):
        self.project, self.req, self.rdir = project, req, Path(rdir)
        self.now, self.sleep, self.notify = now, sleep, notify
        self.spawn = spawn or self._spawn
        self.free_bytes = free_bytes or (lambda: shutil.disk_usage(self.rdir).free)
        self.announce = announce or self._announce
        self.pending = pending or self._pending
        self.heal = heal or self._heal
        self.capture = capture or self._capture
        self.coordinate = coordinate or self._coordinate
        self.log = log or (lambda text: print(f"{time.strftime('%H:%M:%S')} {text}", flush=True))
        self.failures: collections.deque[float] = collections.deque()
        self.backoff = BACKOFF_START
        self.low_disk_notified = False

    @staticmethod
    def _min_free() -> int:
        import bt_config

        try:
            mb = bt_config.get("scheduler.min_free_mb", MIN_FREE_BYTES >> 20)
        except (KeyError, TypeError):
            return MIN_FREE_BYTES
        return mb << 20 if isinstance(mb, int) and not isinstance(mb, bool) and mb >= 0 else MIN_FREE_BYTES

    def _spawn(self, resume: bool) -> "subprocess.Popen":
        cli = Path(__file__).with_name("bitacora.py")
        argv = [sys.executable, str(cli), "--project", self.project, "scheduler-run", self.req]
        if resume:
            argv.append("--resume")
        return subprocess.Popen(argv, stdin=subprocess.DEVNULL, close_fds=True, start_new_session=True)

    def _has_run(self) -> bool:
        return adapter.authority(self.rdir) == adapter.AUTHORITY

    def _wait_owner_gone(self) -> None:
        """Wait for the owner to end. A verification that waits for the coordinator's manual evidence keeps the owner ALIVE, so the
        coordinator's turn (opt-in per project) also runs here, every COORDINATE_SECONDS, not only between owners."""
        last = self.now()
        while ops.owner_pids(self.project, self.req):
            self.sleep(POLL_SECONDS)
            if self.now() - last >= COORDINATE_SECONDS:
                last = self.now()
                try:
                    self.coordinate()
                except Exception as error:  # noqa: BLE001 - an extra: its failure never stops the watch
                    self.log(f"coordinator failed ({type(error).__name__}: {error})")
                last = self.now()

    def _coordinate(self) -> bool:
        import bt_coordinator

        return bt_coordinator.cycle(self.project, self.req, self.rdir, log=self.log)

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
            if self.free_bytes() < self._min_free():
                if not self.low_disk_notified:
                    self.low_disk_notified = True
                    self.log(f"disk almost full: {self.free_bytes() >> 20} MiB free under {self.rdir} and the owner needs "
                             f"{self._min_free() >> 20} MiB (config scheduler.min_free_mb): waiting before restarting it")
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
                try:
                    saved = self.capture()
                except Exception as error:  # noqa: BLE001 - the replica is an extra: its failure never changes how the run ends
                    saved = ""
                    self.log(f"replica not saved ({type(error).__name__}: {error})")
                if saved:
                    self.log(saved)
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

    def _capture(self) -> str:
        """P-163: a run that ended with every task completed leaves its replica (plan + measured times) in `<project>/replicas/`, so the
        benchmark and the A/B settings (`scheduler-evolve`) grow with each real run. A stalled run is not a replica of anything."""
        states = ops.status(self.project, self.req, self.rdir)["task_states"]
        if not states or any(state not in ("completed", "cancelled") for state in states.values()):
            return ""
        import bt_scheduler_replica as replica

        target = self.rdir.parent.parent / "replicas" / f"{self.req}.json"
        fixture = replica.extract(adapter.run_db_path(self.rdir), self.rdir / "PLAN.json", name=self.req)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(fixture, indent=1, sort_keys=True), encoding="utf-8")
        return f"replica of {self.req} saved in {target} ({fixture['recorded']['attempts']} attempts)"

    def _heal(self) -> bool:
        """The self-healing cycle first (`bt_scheduler_healing`: diagnose each open stop in a closed taxonomy and apply the
        smallest safe repair, bounded and recorded); then the older clash answer below, which it supersedes when on."""
        import bt_scheduler_healing

        try:
            if bt_scheduler_healing.cycle(self.project, self.req, self.rdir, log=self.log, notify=self.notify):
                return True
        except Exception as error:  # noqa: BLE001 - healing is an extra: a failure in it never stops the watch
            self.log(f"healing failed ({type(error).__name__}: {error})")
        try:
            import bt_recovery_pipeline

            if bt_recovery_pipeline.advance(self.project, self.req, self.rdir, log=self.log):
                return True
        except Exception as error:  # noqa: BLE001 - the structural cycle is opt-in and bounded: its failure never stops the watch
            self.log(f"recovery cycle failed ({type(error).__name__}: {error})")
        try:
            import bt_coordinator

            if bt_coordinator.cycle(self.project, self.req, self.rdir, log=self.log):
                return True
        except Exception as error:  # noqa: BLE001 - opt-in per project: its failure never stops the watch
            self.log(f"coordinator failed ({type(error).__name__}: {error})")
        return self._heal_conflicts()

    def _heal_conflicts(self) -> bool:
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
            import bt_interventions
            bt_interventions.record(self.rdir, kind="integration_defect", source="auto", task=request["task"],
                                    evidence=str(diagnosis.get("headline") or "integration clash"),
                                    repair="redo the task built on the stale result", result="fixed", run=f"{self.project}-{self.req}")
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
