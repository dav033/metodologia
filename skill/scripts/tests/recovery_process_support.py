"""Subprocess fixtures for shipped Bitacora scheduler entry points (no recovery ports are patched)."""
from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parents[1]
REPO = SCRIPTS.parents[1]
MIN_WATCH_FREE_BYTES = 2 << 30


def _recovery_temp_parent() -> Path:
    """Choose a location where the shipped scheduler-watch disk gate can start an owner."""
    candidates = (Path(tempfile.gettempdir()), REPO, Path.home())
    checked: list[str] = []
    seen: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            free = shutil.disk_usage(resolved).free
            checked.append(f"{resolved} ({free} bytes free)")
            if free >= MIN_WATCH_FREE_BYTES:
                return resolved
        except OSError as error:
            checked.append(f"{candidate} ({type(error).__name__})")
    detail = "; ".join(checked) if checked else "no usable candidates"
    raise RuntimeError(
        f"recovery CLI harness requires at least 2 GiB free for scheduler-watch; checked: {detail}"
    )


@dataclass(frozen=True)
class FixtureScenario:
    """Complete, portable input for a throwaway CLI run."""

    project: str
    requirement: str
    tasks: tuple[dict[str, Any], ...]
    repositories: dict[str, str]
    provider: str = "codex"
    provider_reference: str = "direct:codex/gpt-6-luna#low@fixture"
    environment: dict[str, str] | None = None


class RecoveryProcessHarness:
    """Own temporary roots and drive only the real CLI, executor, verifier, and supplied provider executables."""

    def __init__(self, scenario: FixtureScenario, provider_executables: dict[str, str | Path], *, root: Path | None = None):
        self.scenario = scenario
        self.provider_executables = {name: Path(path).resolve() for name, path in provider_executables.items()}
        parent = Path(root).resolve() if root is not None else _recovery_temp_parent()
        if shutil.disk_usage(parent).free < MIN_WATCH_FREE_BYTES:
            raise RuntimeError(f"recovery CLI harness root {parent} requires at least 2 GiB free")
        self.temp = Path(tempfile.mkdtemp(prefix="recovery-cli-", dir=parent))
        self.bitacora_root = self.temp / "bitacora"
        self.home = self.temp / "home"
        self.bin = self.temp / "bin"
        self.bitacora_root.mkdir()
        self.home.mkdir()
        self.bin.mkdir()
        self.rdir = self.bitacora_root / scenario.project / "requirements" / f"{scenario.requirement.upper()}-fixture"
        self.rdir.mkdir(parents=True)
        self.processes: list[subprocess.Popen] = []
        self.watch_log = self.temp / "scheduler-watch.log"
        self._setup_project()
        self._setup_repositories()
        self._setup_providers()
        self._freeze_plan()

    def close(self) -> None:
        for process in self.processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
        try:
            log = self.watch_log.read_text(encoding="utf-8")
        except OSError:
            log = ""
        for raw_pid in re.findall(r"owner started \(pid ([0-9]+)\)", log):
            try:
                os.killpg(int(raw_pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                try:
                    os.kill(int(raw_pid), 0)
                except ProcessLookupError:
                    break
                time.sleep(0.05)
        shutil.rmtree(self.temp, ignore_errors=True)

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()

    def env(self) -> dict[str, str]:
        result = {"PATH": f"{self.bin}:/usr/local/bin", "HOME": str(self.home),
                  "BITACORA_ROOT": str(self.bitacora_root), "PYTHONPATH": str(SCRIPTS),
                  "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
        result.update(self.scenario.environment or {})
        return result

    def cli(self, *arguments: str, timeout: float = 120) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(SCRIPTS / "bitacora.py"), "--project", self.scenario.project,
                               *arguments], cwd=self.temp, env=self.env(), text=True, capture_output=True,
                              timeout=timeout, check=False)

    def start_watch(self) -> subprocess.Popen:
        output = self.watch_log.open("w", encoding="utf-8")
        process = subprocess.Popen([sys.executable, str(SCRIPTS / "bitacora.py"), "--project",
                                    self.scenario.project, "scheduler-watch", self.scenario.requirement],
                                   cwd=self.temp, env=self.env(), stdin=subprocess.DEVNULL,
                                   stdout=output, stderr=subprocess.STDOUT, text=True)
        output.close()
        self.processes.append(process)
        return process

    def wait_for(self, predicate, *, timeout: float, interval: float = 0.05, label: str = "condition"):
        """Poll an explicit durable observation; timeout diagnostics include the current watch output."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            result = predicate()
            if result:
                return result
            time.sleep(interval)
        tails = []
        for process in self.processes:
            tails.append(f"process pid={process.pid} returncode={process.poll()}")
            if process.stdout:
                try:
                    tails.append(process.stdout.read() if process.poll() is not None else "")
                except OSError:
                    pass
        try:
            watch_output = self.watch_log.read_text(encoding="utf-8")
        except OSError:
            watch_output = "<watch log unavailable>"
        tails.append(f"watch log: {watch_output[-4000:]}")
        scheduler_db = self.bitacora_root / ".state" / "scheduler" / f"{self.scenario.project}-{self.scenario.requirement}.db"
        tails.append(f"scheduler database exists={scheduler_db.is_file()}")
        raise TimeoutError(f"timed out waiting for {label}; watch output: {' '.join(tails)[-2000:]}")

    def snapshot(self) -> str:
        """Stable digest over the checked-out repository content, excluding git internals."""
        digest = hashlib.sha256()
        for path in sorted(p for p in self.temp.rglob("*") if p.is_file() and ".git" not in p.parts):
            digest.update(path.relative_to(self.temp).as_posix().encode() + b"\0")
            digest.update(hashlib.sha256(path.read_bytes()).digest())
        return digest.hexdigest()

    def _setup_project(self) -> None:
        pdir = self.bitacora_root / self.scenario.project
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / "project.json").write_text(json.dumps({"work": False, "repos": {}}), encoding="utf-8")
        (pdir / "requirements").mkdir(exist_ok=True)

    def _setup_repositories(self) -> None:
        repos = {}
        for role, relative in self.scenario.repositories.items():
            path = (self.temp / relative).resolve()
            path.mkdir(parents=True, exist_ok=True)
            self._git(path, "init", "-q", "-b", "main")
            (path / "README.md").write_text("fixture repository\n", encoding="utf-8")
            self._git(path, "add", "-A")
            self._git(path, "commit", "-q", "-m", "fixture baseline")
            repos[role] = str(path)
        meta_path = self.bitacora_root / self.scenario.project / "project.json"
        meta_path.write_text(json.dumps({"work": False, "repos": repos}), encoding="utf-8")
        local = {f"{self.scenario.project}/{role}": path for role, path in repos.items()}
        state = self.bitacora_root / ".state"
        state.mkdir(exist_ok=True)
        (state / "paths.json").write_text(json.dumps(local), encoding="utf-8")
        (state / "repos.json").write_text("{}\n", encoding="utf-8")

    def _setup_providers(self) -> None:
        profiles = {}
        for name, executable in self.provider_executables.items():
            target = self.bin / name
            target.write_text(f"#!/bin/sh\nexec {json.dumps(str(executable))} \"$@\"\n", encoding="utf-8")
            target.chmod(0o755)
        git_binary = shutil.which("git")
        if git_binary:
            (self.bin / "git").symlink_to(git_binary)
        profiles["fixture"] = {"provider": self.scenario.provider, "bin": self.scenario.provider,
                               "env": {"HOME": str(self.home)}}
        state = self.bitacora_root / ".state"
        (state / "profiles.json").write_text(json.dumps(profiles), encoding="utf-8")

    def _freeze_plan(self) -> None:
        plan = {"schema_version": "1.2.0", "plan_id": self.scenario.requirement, "revision": 1,
                "tasks": [dict(task) for task in self.scenario.tasks]}
        raw = json.dumps(plan, indent=1, sort_keys=True) + "\n"
        revisions = self.rdir / "plan-revisions"
        revisions.mkdir()
        (revisions / "PLAN.r1.json").write_text(raw, encoding="utf-8")
        digest = hashlib.sha256(raw.encode()).hexdigest()
        (revisions / "MANIFEST.json").write_text(json.dumps({"schema": 1, "revisions": [
            {"revision": 1, "sha256": digest, "frozen_at": "2026-10-01T00:00:00+00:00"}]}), encoding="utf-8")

    @staticmethod
    def _git(path: Path, *args: str) -> None:
        subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@invalid",
                        "-c", "core.hooksPath=/dev/null", *args], cwd=path, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
