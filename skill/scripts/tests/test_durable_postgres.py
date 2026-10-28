"""Scenario H (REQ-030 M9): the PostgreSQL system database goes away mid-run and comes back. Confirmed durable state
survives, the engine (restarted if it died, as systemd would) finishes the run, and the agent is launched once.

Uses a throwaway local container (`bt-durable-pg-test-<pid>`, loopback only) and removes it afterwards; skipped when
docker is not usable."""
from __future__ import annotations

import os
import secrets
import shutil
import signal
import subprocess
import sys
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from bt_contracts.execution import RunRef
from bt_durable.client import Client
from bt_durable.settings import Settings
from durable_support import Lab, task, wait_until

FAST = Settings(max_parallel=1, poll_seconds=0.5, run_poll_seconds=5, owner_wait_seconds=5)


def docker(*args, check=True):
    return subprocess.run(["docker", *args], capture_output=True, text=True, check=check, timeout=120)


def docker_ok() -> bool:
    return bool(shutil.which("docker")) and subprocess.run(["docker", "info"], capture_output=True,
                                                           check=False).returncode == 0


@unittest.skipUnless(docker_ok(), "docker is not usable here")
class PostgresOutage(unittest.TestCase):
    def setUp(self):
        self.name = f"bt-durable-pg-test-{os.getpid()}"
        self.password = secrets.token_hex(12)
        port = _free_port()                 # fixed: a restarted container must come back on the same port
        docker("run", "-d", "--name", self.name, "-e", f"POSTGRES_PASSWORD={self.password}", "-p",
               f"127.0.0.1:{port}:5432", "postgres:16-alpine")
        self.addCleanup(docker, "rm", "-f", self.name, check=False)
        self.url = f"postgresql://postgres:{self.password}@127.0.0.1:{port}/bt_durable"
        wait_until(lambda: docker("exec", self.name, "pg_isready", "-U", "postgres", check=False).returncode == 0,
                   60, what="postgres to accept connections")
        time.sleep(1)
        self.lab = Lab(backend="auto")
        self.addCleanup(self.lab.cleanup)
        self.lab.database_override = self.url

    def spawn(self):
        proc = self.lab.spawn_engine()
        self.addCleanup(lambda: proc.poll() is None and os.killpg(proc.pid, signal.SIGKILL))
        return proc

    def test_the_run_survives_a_database_outage_without_a_duplicate_launch(self):
        os.environ["FAKE_SLOW_SECONDS"] = "12"
        self.addCleanup(os.environ.pop, "FAKE_SLOW_SECONDS", None)
        run = RunRef.model_validate(self.lab.freeze([task("T1", scenario="slow"), task("T2", after=["T1"])]))
        engine = self.spawn()
        client = wait_until(lambda: _client(self.url), 90, interval=1, what="the DBOS schema in postgres")
        self.addCleanup(client.close)
        client.start(run, FAST)
        wait_until(lambda: self.lab.launches(), 90, what="the agent to start")
        docker("stop", "-t", "1", self.name)                        # the database disappears mid-attempt
        time.sleep(6)
        docker("start", self.name)
        wait_until(lambda: docker("exec", self.name, "pg_isready", "-U", "postgres", check=False).returncode == 0,
                   60, what="postgres to come back")
        restarts = 0

        def settled():
            nonlocal engine, restarts
            if engine.poll() is not None:                           # what systemd's Restart=always would do
                restarts += 1
                engine = self.spawn()
            try:
                status = client.status(run)
            except Exception:  # noqa: BLE001 - the client reconnects on the next poll
                return None
            return status if status["workflow_status"] in ("SUCCESS", "ERROR") else None

        status = wait_until(settled, 240, interval=1, what="the run to settle after the outage")
        self.assertEqual(status["summary"]["status"], "completed", status)
        launches = [x["scenario"] for x in self.lab.launches()]
        self.assertEqual(launches.count("slow"), 1, launches)      # T1 adopted, never launched twice
        self.assertEqual(len(launches), 2)
        print(f"engine restarts during the outage: {restarts}", file=sys.stderr)


def _free_port() -> int:
    import socket
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def _client(url):
    try:
        client = Client(url)
        client.client.list_workflows(limit=1)
        return client
    except Exception:  # noqa: BLE001 - schema not created yet
        return None


if __name__ == "__main__":
    unittest.main()
