"""Test doubles and helpers: a scripted fake provider, a real git repository, a recording sink."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[1])]

import bt_scheduler_executor as ex
from bt_scheduler_executor import model as m

FAKE_AGENT = HERE / "fake_agent.py"
os.environ.setdefault("GIT_CONFIG_NOSYSTEM", "1")


def git(cwd, *args, check=True):
    done = subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=t@t", "-c", "core.hooksPath=/dev/null", *args],
                          cwd=str(cwd), capture_output=True, text=True, check=False)
    if check and done.returncode:
        raise RuntimeError(f"git {args}: {done.stderr}")
    return done.stdout.strip()


def make_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q", "-b", "main")
    (path / "README.md").write_text("original\n")
    (path / "src.txt").write_text("source\n")
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", "initial")
    return path


class FakeResolver:
    """`fake:<scenario>[:<arg>]` -> a route whose model is the scenario; anything else is unresolvable."""

    def __init__(self):
        self.calls = 0
        self.fail: ex.ExecutorError | None = None

    def resolve(self, request):
        self.calls += 1
        if self.fail:
            raise self.fail
        ref = request.executor
        if not ref.startswith("fake:"):
            raise ex.ExecutorError("ROUTE_UNRESOLVABLE", f"unknown reference {ref!r}")
        _, scenario, *rest = ref.split(":")
        return ex.Route(provider="fake", model=scenario + (":" + rest[0] if rest else ""), profile="acct-1",
                        effort="low", reference=ref)


class FakeBriefs:
    def brief(self, request):
        return ex.Brief(title=f"Task {request.task_id}", objective="do the thing",
                        acceptance_criteria=("thing is done",), verification=("check it",))


class FakeDriver:
    """argv = python fake_agent.py <scenario> [arg]; classification mimics what the real drivers report."""

    def __init__(self):
        self.prepared: list[tuple] = []
        self.timeouts: list[float] = []

    def prepare(self, route, prompt, workspace, timeout_seconds):
        scenario, _, arg = route.model.partition(":")
        self.prepared.append((route, workspace.path))
        self.timeouts.append(timeout_seconds)
        argv = [sys.executable, str(FAKE_AGENT), scenario] + ([arg] if arg else [])
        return ex.Launch(argv=tuple(argv), env_remove=("OTHER_PROFILE_SECRET",),
                         env_set=(("PROFILE_TOKEN", "secret-for-" + route.profile),))

    def classify(self, route, raw, returncode, *, timed_out=False, cancelled=False):
        if timed_out:
            return ex.Classification("timeout")
        if "usage limit reached" in raw and returncode:
            import re
            found = re.search(r"usage limit reached\|(\d+)", raw)
            reset = int(found.group(1)) if found else None
            return ex.Classification("limit", reset_epoch=reset, terminal_event=True)
        terminal = "TERMINAL-EVENT" in raw
        if returncode:
            return ex.Classification("failed", terminal_event=terminal, text=raw[-200:])
        return ex.Classification("completed" if terminal else "partial", terminal_event=terminal, text=raw[-200:])


class Sink:
    def __init__(self):
        self.events: list[ex.TechnicalEvent] = []
        self.fail = False
        self.lock = threading.Lock()
        self.attempts = 0

    def deliver(self, event):
        with self.lock:
            self.attempts += 1
            if self.fail:
                raise RuntimeError("sink down")
            self.events.append(event)

    def kinds(self, attempt_id=None):
        with self.lock:
            return [e.kind for e in self.events if attempt_id is None or e.attempt_id == attempt_id
                    if e.kind != m.EV_HEARTBEAT]

    def of(self, attempt_id, kind):
        with self.lock:
            return [e for e in self.events if e.attempt_id == attempt_id and e.kind == kind]


def order(n: int = 1, scenario: str = "ok", *, repo: str = "main", plan: str = "REQ-T", revision: int = 1,
          token: int = 1, timeout: float | None = None, base: str = "HEAD", executor: str | None = None,
          attempt_id: str | None = None, key: str | None = None) -> ex.StartRequest:
    return ex.StartRequest(idempotency_key=key or f"{plan}:r{revision}:att-{n:04d}:start", plan_id=plan,
                           revision=revision, task_id=f"T{n}", attempt_id=attempt_id or f"att-{n:04d}", token=token,
                           executor=executor or f"fake:{scenario}", repository=repo, project="proj", base_ref=base,
                           timeout_seconds=timeout)


class World:
    """One executor root + one repository, torn down at the end. `restart()` builds a fresh executor on the same root
    (what a restarted process would do) after the old one's supervision is stopped but its agents left running."""

    def __init__(self, test, *, config: ex.Config | None = None, repos: int = 1, autostart: bool = True,
                 resolver=None, driver=None, sink=None, briefs=None):
        self.tmp = Path(tempfile.mkdtemp(prefix="m3-test-"))
        test.addCleanup(self.cleanup)
        self.repos = {("main" if i == 0 else f"repo{i}"): make_repo(self.tmp / ("repo" if i == 0 else f"repo{i}"))
                      for i in range(repos)}
        self.repo = self.repos["main"]
        self.root = self.tmp / "exec-root"
        self.config = config or ex.Config(poll_seconds=0.05, heartbeat_seconds=3600, grace_seconds=1.0,
                                          timeout_seconds=60)
        self.resolver, self.driver = resolver or FakeResolver(), driver or FakeDriver()
        self.sink, self.briefs = sink or Sink(), briefs or FakeBriefs()
        self.executors: list[ex.AgentExecutor] = []
        self.x = self.build(autostart)

    def build(self, autostart: bool = True) -> ex.AgentExecutor:
        workspaces = ex.GitWorkspaces(self.root / "ws", self.repos)
        x = ex.AgentExecutor(self.root, resolver=self.resolver, briefs=self.briefs, driver=self.driver,
                             workspaces=workspaces, sink=self.sink, config=self.config, autostart=autostart)
        self.executors.append(x)
        return x

    def restart(self, autostart: bool = True) -> ex.AgentExecutor:
        self.x.close(wait=True)
        self.x = self.build(autostart)
        return self.x

    def cleanup(self):
        for x in self.executors:
            try:
                x.close(wait=True)
            except Exception:
                pass
        for row in self._live_rows():
            for key in ("pid",):
                pid = (row.get("shim") or {}).get(key)
                if pid:
                    try:
                        os.killpg(int(pid), 9)
                    except OSError:
                        pass
        self.kill_strays()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _live_rows(self):
        try:
            return self.x.ledger.in_states(m.LIVE)
        except Exception:
            return []

    def strays(self):
        """Processes (agents, shims, stragglers) still running inside this world: tests that must leave none assert this
        BEFORE the cleanup below kills whatever is left."""
        found, needle = [], str(self.tmp)
        for entry in Path("/proc").iterdir():
            if not entry.name.isdigit() or int(entry.name) == os.getpid():
                continue
            try:
                cmd = (entry / "cmdline").read_bytes().decode("utf-8", "replace")
                if needle in cmd or os.readlink(entry / "cwd").startswith(needle):
                    found.append((int(entry.name), cmd[:80]))
            except OSError:
                continue
        return found

    def kill_strays(self):
        """Any process still running inside this world's tmp dir (agents, shims) is stopped."""
        needle = str(self.tmp)
        for entry in Path("/proc").iterdir():
            if not entry.name.isdigit():
                continue
            try:
                cmd = (entry / "cmdline").read_bytes().decode("utf-8", "replace")
                if needle in cmd or os.readlink(entry / "cwd").startswith(needle):
                    os.kill(int(entry.name), 9)
            except OSError:
                continue

    def finish(self, attempt_id: str, timeout: float = 30.0) -> dict:
        state = self.x.wait_state(attempt_id, m.TERMINAL, timeout)
        assert state, f"{attempt_id} did not finish; ledger: {self.x.ledger.get(attempt_id)}"
        assert wait_for(lambda: all(e["delivered"] for e in self.x.ledger.events(attempt_id)), timeout), \
            "events were not delivered"
        return self.x.describe(attempt_id)


def wait_for(predicate, timeout: float = 20.0, interval: float = 0.02) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return False
