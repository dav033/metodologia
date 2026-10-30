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
CHECK_GOOD = "python3 checks/check_out.py"
CHECK_HEAP = "python3 checks/check_heap.py"
CHECKS = {
    "check_out.py": "import pathlib, sys\nsys.exit(0 if pathlib.Path('out.txt').is_file() and "
                    "pathlib.Path('out.txt').read_text() == 'good\\n' else 1)\n",
    # a check that fails like a Node build out of heap unless the verifier raised the heap (an environment limit)
    "check_heap.py": "import os, re, sys\nheap = re.search(r'max-old-space-size=(\\d+)', os.environ.get('NODE_OPTIONS', ''))\n"
                     "if not heap or int(heap.group(1)) < 8000:\n"
                     "    print('FATAL ERROR: Reached heap limit Allocation failed - JavaScript heap out of memory', "
                     "file=sys.stderr)\n    sys.exit(134)\n",
}


REAL_AUDIT_POLICY = {"audit_ledger_required": True, "audit_read_only": True}   # bt_config's defaults


def git(cwd, *args) -> str:
    done = subprocess.run(["git", "-c", "user.name=T", "-c", "user.email=t@t", "-c", "core.hooksPath=/dev/null", *args],
                          cwd=str(cwd), capture_output=True, text=True, check=False)
    if done.returncode:
        raise RuntimeError(f"git {args}: {done.stderr}")
    return done.stdout.strip()


def task(tid, *, after=(), scenario="ok", check=CHECK_GOOD, paths=None, resources=(), subplan=None, kind=None,
         extra_checks=()):
    criterion = f"{tid} produces the good output"
    item = {"id": tid, "milestone_id": "M1", "title": f"{tid} SCENARIO:{scenario}", "objective": f"do {tid}",
            "repository": "app", "after": list(after), "expected_paths": paths or [f"{tid}/**", f"{tid}.task", "out.txt"],
            "shared_resources": list(resources), "acceptance_criteria": [criterion, *(c["purpose"] for c in extra_checks)],
            "verification": [{"type": "command", "value": check, "purpose": criterion, "category": "functional"},
                             *extra_checks]}
    if subplan:
        item["subplan_id"] = subplan
    if kind:
        item["kind"] = kind
    return item


def subplan(sid, members_test, audit, *, produces=()):
    """A minimal plan 1.3.0 subplan (bt_scheduler_core.subplans.parse_plan_extensions)."""
    return {"id": sid, "milestone_id": "M1", "title": f"subplan {sid}", "outcome": f"{sid} works",
            "covers": ["R1"], "acceptance_criteria": [f"{sid} is accepted"], "integration_test_task": members_test,
            "audit_task": audit, **({"produces": list(produces)} if produces else {})}


def gate(gid, members, task_id):
    return {"id": gid, "subplans": list(members), "task": task_id, "criteria": [f"{gid} composes {', '.join(members)}"]}


class Lab:
    def __init__(self, root: Path | None = None, *, backend: str = "auto"):
        self.root = Path(root or tempfile.mkdtemp(prefix="bt-durable-lab-", dir=os.environ.get("BT_LAB_DIR") or None))
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
            (self.repo / "checks").mkdir()
            for name, body in CHECKS.items():
                (self.repo / "checks" / name).write_text(body)
            git(self.repo, "add", "-A")
            git(self.repo, "commit", "-q", "-m", "initial")
        self.rdir = self.bitacora / "proj" / "requirements" / "REQ-900-lab"
        self.rdir.mkdir(parents=True, exist_ok=True)
        self.database_override: str | None = None
        self.routes = ["claude::sonnet"]              # execution.routes of the lab engine ("provider:profile:model")
        self.quota = self.root / "quota.json"         # what LiveQuota reads in the engine (bt_quota_live rows)
        # the lab's audit tasks are placeholders (no findings ledger, they write outside a report): the audit gate is
        # told so explicitly; suites about audits call `configure(gates=REAL_AUDIT_POLICY)` (the legacy defaults)
        if not (self.bitacora / ".state" / "config.json").exists():      # the engine's own Lab must not reset it
            self.configure(gates={"audit_ledger_required": False, "audit_read_only": False})
        self.unit_prefix = f"bt-test-{hashlib.sha256(str(self.root).encode()).hexdigest()[:6]}-"

    def configure(self, **sections) -> None:
        """The machine configuration (bt_config) the engine of this lab reads: <lab bitácora>/.state/config.json."""
        path = self.bitacora / ".state" / "config.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(sections))

    # ---------------------------------------------------------------------------------------------- plan
    def freeze(self, tasks, revision=1, *, schema="1.0.0", **extra) -> dict:
        text = json.dumps({"schema_version": schema, "plan_id": "REQ-900", "revision": revision, "tasks": tasks,
                           **extra}, indent=1) + "\n"
        folder = self.rdir / "plan-revisions"
        folder.mkdir(exist_ok=True)
        path = folder / f"PLAN.r{revision}.json"
        path.write_text(text, encoding="utf-8")
        return {"project": "proj", "req": "REQ-900", "plan_id": "REQ-900", "revision": revision,
                "plan_sha256": hashlib.sha256(text.encode()).hexdigest(), "plan_path": str(path)}

    # ------------------------------------------------------------------------------------ accounts, quota
    def use_accounts(self, *profiles: str, model: str = "sonnet") -> None:
        """Claude accounts as named profiles (each its own CLAUDE_CONFIG_DIR) and the routes over them, in order."""
        state = self.bitacora / ".state"
        state.mkdir(parents=True, exist_ok=True)
        spec = {}
        for pid in profiles:
            folder = self.root / f"cfg-{pid}"
            folder.mkdir(exist_ok=True)
            spec[pid] = {"provider": "claude", "env": {"CLAUDE_CONFIG_DIR": str(folder)}, "work_only": False,
                         "bin": "claude"}
        (state / "profiles.json").write_text(json.dumps(spec, indent=1))
        self.routes = [f"claude:{pid}:{model}" for pid in profiles]

    def set_quota(self, rows: list[dict]) -> None:
        """Live quota readings, shaped as bt_quota_live rows; the engine reads the file on every routing decision."""
        tmp = self.quota.with_suffix(".tmp")
        tmp.write_text(json.dumps(rows))
        tmp.replace(self.quota)

    def read_quota(self) -> list[dict]:
        try:
            return json.loads(self.quota.read_text())
        except OSError:
            return []

    def telemetry(self) -> list[dict]:
        try:
            return [json.loads(line) for line in (self.state / "telemetry.jsonl").read_text().splitlines() if line]
        except OSError:
            return []

    def own(self, run: dict) -> None:
        """Make the lab requirement a durable-owned run the panels and `bt-durable` CLI see: PLAN.json/PLAN.md for the
        plan pages, RUN.owner.json (backend dbos), RUN.durable-run.json, and the lab database in the lab's config."""
        import bt_run_owner
        frozen = Path(run["plan_path"]).read_text(encoding="utf-8")
        (self.rdir / "PLAN.json").write_text(frozen, encoding="utf-8")
        (self.rdir / "PLAN.md").write_text("---\nstatus: approved\n---\n# Plan — REQ-900 — Lab\n", encoding="utf-8")
        run_id = f"{run['project']}:{run['req']}:r{run['revision']}"
        record = {"run_id": run_id, "backend": "dbos", "workflow_id": f"bt:{run_id}", "since": time.time(),
                  "by": "lab", "migrated_from": None}
        bt_run_owner.write(self.rdir, record, expect=bt_run_owner.read(self.rdir))
        (self.rdir / "RUN.durable-run.json").write_text(json.dumps(run, indent=1), encoding="utf-8")
        state = self.bitacora / ".state"
        state.mkdir(mode=0o700, exist_ok=True)
        (state / "config.json").write_text(json.dumps({"execution": {"database_url": self.database_url}}))

    def env(self) -> dict:
        return {"BITACORA_ROOT": str(self.bitacora), "PATH": f"{self.bin}:{os.environ.get('PATH', '')}",
                "FAKE_COUNT": str(self.count), "PYTHONPATH": f"{SCRIPTS}:{HERE}",
                "CLAUDE_CONFIG_DIR": str(self.root / "claude-config"), "HOME": os.environ.get("HOME", str(self.root))}

    def write_config(self, **settings) -> Path:
        path = self.root / "lab.json"
        path.write_text(json.dumps({"root": str(self.root), "backend": self.backend, "settings": settings,
                                    "database_url": self.database_override, "routes": self.routes}))
        return path

    def launches(self) -> list[dict]:
        try:
            return [json.loads(line) for line in self.count.read_text().splitlines() if line.strip()]
        except OSError:
            return []

    @property
    def database_url(self) -> str:
        if self.database_override:
            return self.database_override
        return f"sqlite:///{(self.state / 'dbos.sqlite3').resolve()}"

    # ------------------------------------------------------------------------------------------- engine
    def ports(self):
        """Real ports for the lab (call only in a process whose BITACORA_ROOT points at the lab)."""
        from bt_contracts.execution import Route
        from bt_durable.adapters.routes import LiveQuota
        from bt_durable.adapters.runtime import SupervisorRuntime
        from bt_durable.service import operator_verifier, wire
        from bt_scheduler_executor_adapter import MethodologyDriver

        cfg = self.engine_config()
        runtime = SupervisorRuntime(self.state / "supervisor", backend=self.backend, unit_prefix=self.unit_prefix)
        routes = [Route(provider=p, profile=f, model=m) for p, f, m in (r.split(":") for r in self.routes)]
        return cfg, wire(cfg, repositories_for=lambda project: {"app": self.repo},
                         driver_for=lambda project: MethodologyDriver(project), routes=routes, runtime=runtime,
                         capacity=LiveQuota(reader=self.read_quota),
                         verifier=operator_verifier(self.state / "m6-quality.sqlite3"))

    def engine_config(self):
        from bt_durable.settings import EngineConfig
        return EngineConfig(system_database_url=self.database_url, state_dir=self.state, agent_concurrency=2,
                            verify_concurrency=2)

    @property
    def marker(self) -> Path:
        return self.bitacora / ".state" / "durable" / "engine.json"

    def engine_ready(self, engine: subprocess.Popen) -> bool:
        """The engine wrote its marker (after DBOS launched and its schema was complete). The database file alone
        appears before the schema migrations end: a client that queried it then met «no such column:
        workflow_status.queue_partition_key» under load (test_durable_attestations/audits, 2026-10-29)."""
        try:
            return json.loads(self.marker.read_text()).get("pid") == engine.pid
        except (OSError, ValueError):
            return False

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
        if not os.environ.get("BT_KEEP_LAB"):
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


SYSTEMD = subprocess.run(["systemctl", "--user", "is-system-running"], capture_output=True, text=True,
                         check=False).stdout.strip() in ("running", "degraded")


def engine_client(case, lab: Lab):
    """Spawn the lab engine for a TestCase and return (engine process, DBOS client); both are cleaned up."""
    from bt_durable.client import Client
    engine = lab.spawn_engine()

    def stop():
        if engine.poll() is None:
            engine.send_signal(signal.SIGTERM)
            try:
                engine.wait(20)
            except subprocess.TimeoutExpired:
                engine.kill()
    case.addCleanup(stop)
    wait_until(lambda: lab.engine_ready(engine) or engine.poll() is not None, 120, what="the engine to start")
    if engine.poll() is not None:
        raise AssertionError("engine exited: " + (lab.root / "engine.log").read_text()[-3000:])
    client = Client(lab.database_url)
    case.addCleanup(client.close)
    return engine, client


def _serve(config_path: str) -> None:
    data = json.loads(Path(config_path).read_text())
    lab = Lab(Path(data["root"]), backend=data["backend"])
    lab.database_override = data.get("database_url")
    lab.routes = data.get("routes") or lab.routes
    from bt_durable.service import serve
    cfg, ports = lab.ports()
    serve(cfg, ports, reap_seconds=2.0, marker=lab.marker)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "serve":
        _serve(sys.argv[2])
    else:
        raise SystemExit("usage: durable_support.py serve <lab.json>")
