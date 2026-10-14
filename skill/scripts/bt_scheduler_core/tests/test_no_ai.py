"""SC-AC01 / SC-AC20: a full run needs no credentials, no network, no provider, no process; the package never even
imports a module capable of them."""
from __future__ import annotations

import socket
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]

from support import approved, indep, plan_text

import bt_scheduler_core as sc
from bt_scheduler_core.simulation import Script, simulate

PACKAGE_PARENT = Path(__file__).resolve().parents[2]
FORBIDDEN = {"socket", "ssl", "http", "urllib", "subprocess", "asyncio", "ctypes", "multiprocessing", "requests", "httpx",
             "anthropic", "openai", "google", "langchain"}


class NoAI(unittest.TestCase):
    def test_importing_and_running_pulls_in_no_network_process_or_provider_module(self):
        code = ("import sys; sys.path.insert(0, sys.argv[1])\n"
                "import bt_scheduler_core as sc\n"
                "from bt_scheduler_core.simulation import simulate\n"
                "from bt_scheduler_core import cli\n"
                "import hashlib, json\n"
                "t = json.dumps({'schema_version': '1.0.0', 'plan_id': 'P', 'revision': 1, 'tasks': ["
                "{'id': 'T1', 'repository': 'a', 'expected_paths': ['a']}, {'id': 'T2', 'after': ['T1'], 'repository': 'a'}]})\n"
                "plan = sc.load_plan(t, approved_sha256=hashlib.sha256(t.encode()).hexdigest())\n"
                "snap, core = simulate(plan, sc.InMemoryRepository())\n"
                "assert snap.status == 'completed'\n"
                "print(sorted(m for m in sys.modules if m.split('.')[0] in " + repr(sorted(FORBIDDEN)) + "))")
        out = subprocess.run([sys.executable, "-I", "-c", code, str(PACKAGE_PARENT)], capture_output=True, text=True, check=False,
                             cwd="/", env={"PATH": "/usr/bin:/bin"}, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.strip(), "[]")

    def test_a_whole_simulation_runs_with_the_network_and_processes_forbidden(self):
        def refuse(*a, **k):
            raise AssertionError("the core tried to use the network or start a process")

        plan, _ = approved(plan_text([indep("T1"), indep("T2", ["T1"]), indep("T3")]))
        with mock.patch.object(socket, "socket", refuse), mock.patch.object(socket, "create_connection", refuse), \
                mock.patch.object(socket, "getaddrinfo", refuse), mock.patch.object(subprocess, "Popen", refuse), \
                mock.patch.dict("os.environ", {}, clear=True):
            snap, _core = simulate(plan, sc.InMemoryRepository(), sc.Config(max_parallel_tasks=2), Script(fail={"T3": 1}))
        self.assertEqual(snap.status, "blocked")

    def test_the_decision_port_receives_classification_but_the_core_never_branches_on_it(self):
        """Same plan, different classification metadata -> identical audit trail (modulo nothing)."""
        trails = []
        for risk, complexity in (("low", "low"), ("high", "extreme")):
            plan, _ = approved(plan_text([indep("T1", risk=risk, complexity=complexity), indep("T2", ["T1"], risk=risk)]))
            _snap, core = simulate(plan, sc.InMemoryRepository())
            trails.append([(e.kind, e.task_id, e.attempt_id) for e in core.audit_log()])
        self.assertEqual(trails[0], trails[1])


if __name__ == "__main__":
    unittest.main()
