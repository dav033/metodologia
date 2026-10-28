"""Shared fixture of the bt_supervisor tests: real processes only, both backends, everything cleaned up on failure.

Each test case gets a throwaway directory, its own state dir and a unique unit prefix `bt-test-<hex>-`, so cleanup can
stop exactly the units this case created (`systemctl --user stop/reset-failed 'bt-test-<hex>-*'`) and kill exactly the
processes carrying its attempt keys. The suite needs the uv environment (pydantic, psutil): under the bare system
interpreter the modules importing this file are skipped, so `python3 -m unittest discover -s tests` keeps working.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

try:
    import psutil  # noqa: F401
    import pydantic  # noqa: F401
except ImportError as error:              # the legacy suite runs under the stdlib-only system interpreter
    raise unittest.SkipTest(f"bt_supervisor tests need the uv environment: {error}") from error

from bt_supervisor import (
    AttemptAlive,
    LaunchSpec,
    Limits,
    make_supervisor,
    procs,
    systemd,
)
from bt_supervisor.base import derive_outcome

PY = "/usr/bin/python3" if Path("/usr/bin/python3").exists() else sys.executable
BASE_ENV = {"PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8"}

_SYSTEMD: tuple[bool, str] | None = None


def systemd_available() -> tuple[bool, str]:
    global _SYSTEMD
    if _SYSTEMD is None:
        _SYSTEMD = systemd.available()
    return _SYSTEMD


class SupervisorCase(unittest.TestCase):
    """Base for backend-parameterised tests; subclasses set BACKEND."""

    BACKEND = "pgroup"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if cls.BACKEND == "systemd":
            usable, why = systemd_available()
            if not usable:
                print(f"\n[bt_supervisor] skipping systemd tests: {why}", file=sys.stderr)
                raise unittest.SkipTest(f"systemctl --user unavailable: {why}")

    def setUp(self):
        super().setUp()
        self.tmp = Path(tempfile.mkdtemp(prefix="bt-supervisor-test-"))
        self.prefix = f"bt-test-{uuid.uuid4().hex[:8]}-"
        self.state_dir = self.tmp / "state"
        self.worktree = self.tmp / "worktree"
        self.worktree.mkdir()
        self.keys: list[str] = []
        self.sup = self.supervisor()
        self.addCleanup(self._cleanup)

    def supervisor(self):
        return make_supervisor(self.state_dir, self.BACKEND, unit_prefix=self.prefix)

    def key(self, label: str = "a") -> str:
        key = f"{label}-{uuid.uuid4().hex[:10]}"
        self.keys.append(key)
        return key

    def spec(self, key: str, argv: list[str], **kw) -> LaunchSpec:
        kw.setdefault("env", dict(BASE_ENV))
        kw.setdefault("kill_grace_seconds", 1.0)
        return LaunchSpec(attempt_key=key, argv=argv, cwd=kw.pop("cwd", self.worktree),
                          log_dir=kw.pop("log_dir", self.tmp / "logs" / key), **kw)

    def sh(self, key: str, script: str, **kw) -> LaunchSpec:
        return self.spec(key, ["/bin/sh", "-c", script], **kw)

    # ----------------------------------------------------------------------------------------------- waiting
    def wait_state(self, key: str, state: str = "exited", timeout: float = 20.0, sup=None):
        sup = sup or self.sup
        end = time.monotonic() + timeout
        while True:
            observation = sup.observe(key)
            if observation.state == state:
                return observation
            if time.monotonic() > end:
                self.fail(f"{key} did not reach {state} within {timeout}s: {observation}")
            time.sleep(0.05)

    def wait_file(self, path: Path, min_size: int = 1, timeout: float = 10.0) -> None:
        end = time.monotonic() + timeout
        while not (path.exists() and path.stat().st_size >= min_size):
            if time.monotonic() > end:
                self.fail(f"{path} never reached {min_size} bytes")
            time.sleep(0.02)

    def assert_size_stable(self, path: Path, seconds: float = 1.0) -> None:
        before = path.stat().st_size if path.exists() else 0
        time.sleep(seconds)
        after = path.stat().st_size if path.exists() else 0
        self.assertEqual(before, after, f"{path} still grows ({before} -> {after} bytes in {seconds}s)")

    # ----------------------------------------------------------------------------------------------- cleanup
    def _cleanup(self):
        if self.BACKEND == "systemd":
            pattern = f"{self.prefix}*"
            for verb in ("stop", "reset-failed"):
                subprocess.run(["systemctl", "--user", verb, pattern], check=False, capture_output=True, timeout=60)
        for key in self.keys:
            procs.terminate_targets(lambda key=key: procs.marked(key), 0.0)
            reaper = (self.state_dir / "attempts" / key / "reaper.json")
            if reaper.exists():
                import json
                data = json.loads(reaper.read_text())
                procs.terminate_targets(lambda data=data: {data["pid"]: data["start"]}
                                        if procs.alive(data["pid"], data["start"]) else {}, 0.0)
        shutil.rmtree(self.tmp, ignore_errors=True)


class SystemdCase(SupervisorCase):
    BACKEND = "systemd"


class PgroupCase(SupervisorCase):
    BACKEND = "pgroup"


# Test modules import bt_supervisor THROUGH this module, so the uv-environment skip above runs first.
__all__ = ["BASE_ENV", "PY", "SCRIPTS", "AttemptAlive", "LaunchSpec", "Limits", "PgroupCase", "SupervisorCase",
           "SystemdCase", "derive_outcome", "procs", "systemd_available"]
