"""D-265 (pictures REQ-021 r32 T3.91): the attempt's test resources are probed before an agent starts. The agent env
file named a database port nothing listened on; attempts a5..a7 could not run their DB-backed check and the runtime
retried until max_attempts. An unreachable resource the task's checks need now stops the task with an environment
decision (key, host:port, never the value) without an agent or an attempt; `retry` probes again.

    PYTHONPATH=skill/scripts:skill/scripts/tests uv run python -m unittest test_durable_env_probe
"""
from __future__ import annotations

import json
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import bt_verifier_env
import durable_support as lab_support
from bt_contracts.execution import RunRef
from bt_durable.adapters import agent_env
from bt_durable.control import classify
from bt_scheduler_quality.policy import QualityPolicy
from durable_support import task
from test_durable_e2e import FAST, EngineCase

SECRET = "s3cret-pw"


def url(port: int, db: str = "req021") -> str:
    return f"postgresql://agent:{SECRET}@127.0.0.1:{port}/{db}"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def listen(port: int) -> socket.socket:
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", port))
    sock.listen(16)
    return sock


class ResourceOf(unittest.TestCase):
    def test_labels_never_carry_credentials(self):
        found = bt_verifier_env.resource_of(url(55965, "req021_visual"))
        self.assertEqual(found["label"], "postgresql 127.0.0.1:55965/req021_visual")
        self.assertNotIn(SECRET, json.dumps(found))
        self.assertEqual(bt_verifier_env.resource_of("redis://localhost")["port"], 6379)
        self.assertEqual(bt_verifier_env.resource_of("https://api.example.test/v1")["label"], "https api.example.test:443")
        self.assertEqual(bt_verifier_env.resource_of("postgresql+psycopg://u:p@db:6543/x")["label"], "postgresql db:6543/x")
        for value in ("plain", "postgresql:///db?host=/run/postgresql", "postgresql://h1:5432,h2:5432/db",
                      "file:///tmp/x", "postgresql://h:99999/db"):
            self.assertIsNone(bt_verifier_env.resource_of(value), value)


class Probe(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.down: set[int] = set()
        self.test_env = {}
        self.policy = QualityPolicy()
        self.task = SimpleNamespace(verification=[{"value": "npm test", "requires": ["DB_URL", "service:db"]}])
        self.plan = SimpleNamespace(task=lambda task_id: self.task)
        self.run = SimpleNamespace(run_id="proj:REQ-1:r1", project="proj")
        self.clock = [100.0]
        self.probe = agent_env.AgentEnvProbe(check_policy_for=lambda run: self.policy,
                                             test_env_for=lambda project: dict(self.test_env),
                                             env_file_for=lambda project: "~/.config/metodologia/agent-proj.env",
                                             rdir_for=lambda run: Path(tempfile.mkdtemp(prefix="bt-probe-")),
                                             connect=self.connect, clock=lambda: self.clock[0])

    def connect(self, host, port, timeout):
        self.calls.append((host, port, timeout))
        return "connection refused" if port in self.down else ""

    def test_an_unreachable_required_resource_names_key_host_port_and_source_never_the_value(self):
        self.test_env = {"DB_URL": url(55965, "req021_visual"), "OTHER_URL": url(1)}
        self.down = {55965, 1}
        found = self.probe.check(self.run, self.plan, "T1")
        self.assertEqual(found["state"], "unreachable")
        self.assertEqual(found["unreachable"], [{"key": "DB_URL", "resource": "postgresql 127.0.0.1:55965/req021_visual",
                                                 "host": "127.0.0.1", "port": 55965, "error": "connection refused",
                                                 "source": "agent_env_file"}])           # OTHER_URL: not required
        self.assertNotIn(SECRET, json.dumps(found))
        failure = classify.agent_env_unreachable(found)
        self.assertEqual((failure.failure_class.value, failure.code), ("environment", "AGENT_ENV_UNREACHABLE"))
        self.assertIn("DB_URL -> postgresql 127.0.0.1:55965/req021_visual connection refused", failure.summary)
        self.assertIn("agent env file ~/.config/metodologia/agent-proj.env stale", failure.summary)
        self.assertIn("retry (probes again)", failure.summary)
        self.assertNotIn(SECRET, failure.model_dump_json())

    def test_a_reachable_resource_is_cached_briefly_and_a_refused_one_is_probed_again(self):
        self.test_env = {"DB_URL": url(5432)}
        self.assertEqual(self.probe.check(self.run, self.plan, "T1"), {})
        self.assertEqual(self.probe.check(self.run, self.plan, "T1"), {})
        self.assertEqual(len(self.calls), 1)                                    # cached within the run
        self.clock[0] += agent_env.CACHE_SECONDS + 1
        self.down = {5432}
        self.assertEqual(self.probe.check(self.run, self.plan, "T1")["state"], "unreachable")
        self.assertEqual(self.probe.check(self.run, self.plan, "T1")["state"], "unreachable")
        self.assertEqual(len(self.calls), 3)                                    # a failure is never cached
        self.assertEqual(self.calls[0][2], agent_env.PROBE_TIMEOUT)

    def test_the_verifiers_value_is_probed_and_a_divergence_is_reported_once(self):
        """The T3.91 shape: the agent file is stale, the verifier's value is what the attempt gets, and is probed."""
        events = []
        self.probe.telemetry = SimpleNamespace(emit=lambda event, **fields: events.append((event, fields)))
        self.test_env = {"DB_URL": url(55965, "req021_visual")}
        self.policy = QualityPolicy(environment=(("DB_URL", url(55433)),))
        self.down = {55965}
        with patch("bt_planning_activity.record") as record:
            found = self.probe.check(self.run, self.plan, "T1")
            self.probe.check(self.run, self.plan, "T1")
        self.assertEqual(found["state"], "ok")                                  # 55433 answers: the stale port is unused
        self.assertEqual([port for _, port, _ in self.calls], [55433])
        self.assertEqual(found["divergent"], [{"key": "DB_URL", "agent": "postgresql 127.0.0.1:55965/req021_visual",
                                               "verifier": "postgresql 127.0.0.1:55433/req021", "same_resource": False}])
        self.assertEqual([event for event, _ in events], ["agent_env_divergent"])     # once, not per attempt
        self.assertEqual(record.call_count, 1)
        self.assertIn("DB_URL", record.call_args.args[2])
        self.assertNotIn(SECRET, json.dumps([found, events, record.call_args.args], default=str))
        self.clock[0] += agent_env.CACHE_SECONDS + 1                             # past the reachable cache
        self.down = {55433}                                                     # the tunnel itself is down
        down = self.probe.check(self.run, self.plan, "T1")
        self.assertEqual((down["state"], down["unreachable"][0]["source"]), ("unreachable", "verifier"))
        self.assertIn("set by the verifier too", classify.agent_env_unreachable(down).summary)

    def test_without_declared_requires_the_agent_file_and_verifier_keys_are_probed(self):
        self.task = SimpleNamespace(verification=[{"value": "npm test"}])
        self.test_env = {"A_URL": url(1001), "NOT_A_URL": "flag", "SOCKET": "postgresql:///db?host=/run/postgresql"}
        self.policy = QualityPolicy(environment=(("B_URL", "redis://127.0.0.1:1002"),))
        self.down = {1002}
        found = self.probe.check(self.run, self.plan, "T1")
        self.assertEqual(sorted(port for _, port, _ in self.calls), [1001, 1002])
        self.assertEqual([item["key"] for item in found["unreachable"]], ["B_URL"])

    def test_nothing_to_probe_and_a_broken_policy_are_quiet(self):
        self.assertEqual(self.probe.check(self.run, self.plan, "T1"), {})
        self.probe.check_policy_for = lambda run: (_ for _ in ()).throw(ValueError("bad verifier file"))
        self.test_env = {"DB_URL": url(5432)}
        self.assertEqual(self.probe.check(self.run, self.plan, "T1"), {})

    def test_the_real_connect_tells_refused_from_reachable(self):
        port = free_port()
        self.assertEqual(agent_env.connect("127.0.0.1", port, 2.0), "connection refused")
        server = listen(port)
        self.addCleanup(server.close)
        self.assertEqual(agent_env.connect("127.0.0.1", port, 2.0), "")


SERIAL = FAST.model_copy(update={"max_parallel": 1})


class EnvProbeInTheRun(EngineCase):
    """End to end: the real engine, the real probe (TCP to 127.0.0.1), the real M6 check with `requires`."""

    def configure(self, *, agent_port: int, verifier_port: int, agent_db: str = "req021_visual"):
        agent_file, verifier_file = self.lab.root / "agent-proj.env", self.lab.root / "verifier-proj.env"
        agent_file.write_text(f"LAB_DATABASE_URL={url(agent_port, agent_db)}\nAGENT_ONLY=yes\n")
        verifier_file.write_text(f"LAB_DATABASE_URL={url(verifier_port)}\n")
        self.lab.configure(gates={"audit_ledger_required": False, "audit_read_only": False},
                           execution={"agent_env_file": str(agent_file)}, verifier={"env_file": str(verifier_file)})
        needs = task("T1")
        needs["verification"][0]["requires"] = ["LAB_DATABASE_URL"]
        return RunRef.model_validate(self.lab.freeze([needs]))

    def agent_env(self) -> dict:
        found = sorted((self.lab.state / "attempts-root" / "attempts").glob("*/agent.env.json"))
        self.assertEqual(len(found), 1)
        return json.loads(found[0].read_text())

    def test_an_unreachable_resource_starts_no_agent_and_retry_probes_again(self):
        stale, live = free_port(), free_port()
        run = self.configure(agent_port=stale, verifier_port=live)            # nothing listens on either yet
        self.start_engine()
        self.client.start(run, SERIAL)
        decision = lab_support.wait_until(lambda: (self.client.status(run)["tasks"].get("T1") or {}).get("decision"),
                                          240, interval=1, what="the environment decision")
        self.assertEqual(decision["failure"]["code"], "AGENT_ENV_UNREACHABLE")
        self.assertIn(f"LAB_DATABASE_URL -> postgresql 127.0.0.1:{live}/req021", decision["reason"])
        self.assertIn(f"agent: postgresql 127.0.0.1:{stale}/req021_visual", decision["reason"])     # the divergence
        self.assertNotIn(SECRET, json.dumps(decision))
        self.assertEqual(self.lab.launches(), [])                                # no agent ran
        server = listen(live)                                                    # the owner starts the tunnel
        self.addCleanup(server.close)
        from bt_contracts.owner import OwnerAnswer
        self.client.answer(run, "T1", OwnerAnswer(request_id=decision["request_id"], action="retry"))
        status = self.settled(run, timeout=240)
        self.assertEqual(status["summary"]["status"], "completed", status)
        self.assertEqual(len(self.lab.launches()), 1)
        self.assertEqual(status["summary"]["results"]["T1"]["attempts"], 1)     # the refused start used no attempt
        env = self.agent_env()
        self.assertEqual(env["LAB_DATABASE_URL"], url(live))                     # never the stale agent copy
        self.assertEqual(env["AGENT_ONLY"], "yes")
        events = [row for row in self.lab.telemetry() if row.get("event") == "agent_env_divergent"]
        self.assertEqual(len(events), 1)
        self.assertNotIn(SECRET, json.dumps(self.lab.telemetry()))

    def test_a_reachable_resource_lets_the_task_run(self):
        live = free_port()
        server = listen(live)
        self.addCleanup(server.close)
        run = self.configure(agent_port=live, verifier_port=live, agent_db="req021")   # same value: no divergence
        self.start_engine()
        self.client.start(run, SERIAL)
        status = self.settled(run, timeout=240)
        self.assertEqual(status["summary"]["status"], "completed", status)
        self.assertEqual(len(self.lab.launches()), 1)
        self.assertEqual(self.agent_env()["LAB_DATABASE_URL"], url(live))
        self.assertFalse([row for row in self.lab.telemetry() if row.get("event") == "agent_env_divergent"])


if __name__ == "__main__":
    unittest.main()
