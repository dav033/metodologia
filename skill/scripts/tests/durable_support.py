"""A reproducible lab for the durable runtime: real git repositories, a frozen plan, the real provider driver with a
fake `claude` on PATH, systemd user units (bt-test-* prefix) or process groups, the real M6 sandbox, and DBOS on an
isolated SQLite database. The engine runs either in-process or as a separate process that tests can SIGKILL.

Usage as a process: `python durable_support.py serve <lab.json>` (lab.json written by `Lab.write_config`).
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
AGENT = HERE / "fake_providers" / "durable_agent.py"
CHECK_GOOD = "python3 -c \"import pathlib,sys; sys.exit(0 if pathlib.Path('out.txt').read_text()=='good\\n' else 1)\""
CHECK_HEAP = ("python3 -c \"import os,sys; ok='max-old-space' in os.environ.get('NODE_OPTIONS',''); "
              "print('' if ok else 'FATAL ERROR: Reached heap limit Allocation failed - JavaScript heap out of memory',"
              " file=sys.stderr); sys.exit(0 if ok else 134)\"")


def git(cwd, *args) -> str:
    done = subprocess.run(["git", "-c", "user.name=T", "-c", "user.email=t@t", "-c", "core.hooksPath=/dev/null", *args],
                          cwd=str(cwd), capture_output=True, text=True, check=False)
    if done.returncode:
        raise RuntimeError(f"git {args}: {done.stderr}")
    return done.stdout.strip()


def task(tid, *, after=(), scenario="ok", check=CHECK_GOOD, paths=None, resources=()):
    criterion = f"{tid} produces the good output"
    return {"id": tid, "milestone_id": "M1", "title": f"{tid} SCENARIO:{scenario}", "objective": f"do {tid}",
            "repository": "app", "after": list(after), "expected_paths": paths or [f"{tid}/**", "out.txt"],
            "shared_resources": list(resources), "acceptance_criteria": [criterion],
            "verification": [{"type": "command", "value": check, "purpose": criterion}]}


class Lab:
    def __init__(self, root: Path | None = None, *, backend: str = "auto"):
        self.root = Path(root or tempfile.mkdtemp(prefix="bt-durable-lab-"))
        self.backend = backend
        self.bitacora = self.root / "bitacora"
        (self.bitacora / "proj").mkdir(parents=True, exist_ok=True)
        (self.bitacora / "proj" / "project.json").write_text(json.dumps({"work": False}))
        self.bin = self.root / "bin"
        self.bin.mkdir(exist_ok=True)
        wrapper = self.bin / "claude"
        wrapper.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{AGENT}" "$@"\n')
        wrapper.chmod(wrapper.stat().st_mode | stat.S_IEXEC)
        self.count = self.root / "launches.jsonl"
        self.state = self.root / "state"
        self.repo = self.root / "app"
        if not self.repo.exists():
            self.repo.mkdir()
            git(self.repo, "init", "-q", "-b", "main")
            (self.repo / "README.md").write_text("lab\n")
            git(self.repo, "add", "-A")
            git(self.repo, "commit", "-q", "-m", "initial")
        self.rdir = self.bitacora / "proj" / "requirements" / "REQ-900-lab"
        self.rdir.mkdir(parents=True, exist_ok=True)
        self.unit_prefix = f"bt-test-{hashlib.sha256(str(self.root).encode()).hexdigest()[:6]}-"

    # ---------------------------------------------------------------------------------------------- plan
    def freeze(self, tasks, revision=1) -> dict:
        text = json.dumps({"schema_version": "1.0.0", "plan_id": "REQ-900", "revision": revision, "tasks": tasks},
                          indent=1) + "\n"
        folder = self.rdir / "plan-revisions"
        folder.mkdir(exist_ok=True)
        path = folder / f"PLAN.r{revision}.json"
        path.write_text(text, encoding="utf-8")
        return {"project": "proj", "req": "REQ-900", "plan_id": "REQ-900", "revision": revision,
                "plan_sha256": hashlib.sha256(text.encode()).hexdigest(), "plan_path": str(path)}

    def env(self) -> dict:
        return {"BITACORA_ROOT": str(self.bitacora), "PATH": f"{self.bin}:{os.environ.get('PATH', '')}",
                "FAKE_COUNT": str(self.count), "PYTHONPATH": f"{SCRIPTS}:{HERE}",
                "CLAUDE_CONFIG_DIR": str(self.root / "claude-config"), "HOME": os.environ.get("HOME", str(self.root))}

    def write_config(self, **settings) -> Path:
        path = self.root / "lab.json"
        path.write_text(json.dumps({"root": str(self.root), "backend": self.backend, "settings": settings}))
        return path

    def launches(self) -> list[dict]:
        try:
            return [json.loads(line) for line in self.count.read_text().splitlines() if line.strip()]
        except OSError:
            return []

    @property
    def database_url(self) -> str:
        return f"sqlite:///{(self.state / 'dbos.sqlite3').resolve()}"

    # ------------------------------------------------------------------------------------------- engine
    def ports(self):
        """Real ports for the lab (call only in a process whose BITACORA_ROOT points at the lab)."""
        from bt_contracts.execution import Route
        from bt_durable.adapters.runtime import SupervisorRuntime
        from bt_durable.service import operator_verifier, wire
        from bt_scheduler_executor_adapter import MethodologyDriver

        cfg = self.engine_config()
        runtime = SupervisorRuntime(self.state / "supervisor", backend=self.backend, unit_prefix=self.unit_prefix)
        return cfg, wire(cfg, repositories_for=lambda project: {"app": self.repo},
                         driver_for=lambda project: MethodologyDriver(project),
                         routes=[Route(provider="claude", model="sonnet")], runtime=runtime,
                         verifier=operator_verifier(self.state / "m6-quality.sqlite3"))

    def engine_config(self):
        from bt_durable.settings import EngineConfig
        return EngineConfig(system_database_url=self.database_url, state_dir=self.state, agent_concurrency=2,
                            verify_concurrency=2)

    def spawn_engine(self) -> subprocess.Popen:
        log = open(self.root / "engine.log", "ab")  # noqa: SIM115 - handed to the child process, closed with it
        return subprocess.Popen([sys.executable, str(Path(__file__)), "serve", str(self.write_config())],
                                env={**os.environ, **self.env()}, stdout=log, stderr=subprocess.STDOUT,
                                start_new_session=True)

    def cleanup(self) -> None:
        subprocess.run(["systemctl", "--user", "stop", f"{self.unit_prefix}*"], capture_output=True, check=False)
        subprocess.run(["systemctl", "--user", "reset-failed", f"{self.unit_prefix}*"], capture_output=True, check=False)
        for entry in Path("/proc").iterdir():
            if not entry.name.isdigit() or int(entry.name) == os.getpid():
                continue
            try:
                if str(self.root) in (entry / "cmdline").read_bytes().decode("utf-8", "replace") or \
                        os.readlink(entry / "cwd").startswith(str(self.root)):
                    os.kill(int(entry.name), signal.SIGKILL)
            except OSError:
                pass
        shutil.rmtree(self.root, ignore_errors=True)


def wait_until(predicate, timeout: float, interval: float = 0.25, what: str = "condition"):
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        last = predicate()
        if last:
            return last
        time.sleep(interval)
    raise AssertionError(f"timed out after {timeout}s waiting for {what} (last: {last!r})")


def _serve(config_path: str) -> None:
    data = json.loads(Path(config_path).read_text())
    lab = Lab(Path(data["root"]), backend=data["backend"])
    from bt_durable.service import serve
    cfg, ports = lab.ports()
    serve(cfg, ports, reap_seconds=2.0)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "serve":
        _serve(sys.argv[2])
    else:
        raise SystemExit("usage: durable_support.py serve <lab.json>")
