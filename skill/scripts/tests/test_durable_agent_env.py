"""An agent of a durable run receives the owner's test variables (`execution.agent_env_file`) and its brief names them;
cache reads count a tenth of the task's token budget (pictures REQ-021 T4.2)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import bt_config
from bt_contracts.execution import AttemptRef, Route, RunRef
from bt_durable.adapters.m3 import M3Attempts, budget_tokens
from bt_durable.control import frontier
from bt_durable.legacy import load_plan
from durable_support import Lab, git, task

URL = "postgresql://agent:s3cret@127.0.0.1:55965/req021_visual"


class Driver:
    def prepare(self, route, prompt, ws, timeout):
        return SimpleNamespace(env_remove=(), env_set=(("DRIVER_SET", "1"),), argv=("true",), stdin=None)


class AgentTestEnvironment(unittest.TestCase):
    def setUp(self):
        self.lab = Lab(backend="pgroup")
        self.addCleanup(self.lab.cleanup)
        run = self.lab.freeze([task("T1", paths=["**"])])
        self.plan = load_plan(Path(run["plan_path"]).read_text(encoding="utf-8"), approved_sha256=run["plan_sha256"],
                              plan_id=run["plan_id"], revision=run["revision"])
        self.run_ref = RunRef.model_validate(run)
        self.attempts = M3Attempts(root=self.lab.state / "attempts-root",
                                   repositories_for=lambda project: {"app": self.lab.repo},
                                   plan_for=lambda attempt: self.plan, driver_for=lambda project: Driver())
        self.tmp = Path(tempfile.mkdtemp(prefix="bt-agent-env-"))

    def prepare(self, env_file: str):
        real = bt_config.get
        with patch.object(bt_config, "get", side_effect=lambda key, default=None:
                          env_file if key == "execution.agent_env_file" else real(key, default)):
            attempt = AttemptRef(run=self.run_ref, task_id="T1", number=1, workflow_id="wf-1")
            return self.attempts.prepare(attempt, frontier.task(self.plan, "T1"), Route(provider="codex", model="gpt-6-luna"),
                                         base_ref=git(self.lab.repo, "rev-parse", "HEAD"), note="", limits={})

    def test_the_agent_receives_the_owners_test_variables_and_its_brief_names_them(self):
        (self.tmp / "agent-proj.env").write_text(f"# test values for agents\nPICTURES_REQ021_DATABASE_URL={URL}\n")
        prepared = self.prepare(str(self.tmp / "agent-{project}.env"))
        env = json.loads(prepared.env_file.read_text())
        self.assertEqual(env["PICTURES_REQ021_DATABASE_URL"], URL)
        self.assertEqual(env["DRIVER_SET"], "1")
        prompt = prepared.prompt_path.read_text()
        self.assertIn("Test environment: PICTURES_REQ021_DATABASE_URL is set", prompt)
        self.assertNotIn("s3cret", prompt)

    def test_without_the_file_nothing_is_added(self):
        prepared = self.prepare(str(self.tmp / "missing-{project}.env"))
        self.assertNotIn("PICTURES_REQ021_DATABASE_URL", json.loads(prepared.env_file.read_text()))
        self.assertNotIn("Test environment", prepared.prompt_path.read_text())


class BudgetTokens(unittest.TestCase):
    def test_codex_cache_reads_count_a_tenth(self):
        usage = {"input_tokens": 12_355_995, "cached_input_tokens": 12_161_920, "output_tokens": 58_843}
        self.assertEqual(budget_tokens(usage), 12_355_995 - 12_161_920 + 1_216_192 + 58_843)
        self.assertLess(budget_tokens(usage), 8_000_000)

    def test_reported_totals_and_odd_usage(self):
        self.assertEqual(budget_tokens({"total_tokens": 5000, "input_tokens": 1}), 5000)
        self.assertEqual(budget_tokens({"input_tokens": 100, "output_tokens": 20}), 120)
        self.assertEqual(budget_tokens({"input_tokens": 100, "cached_input_tokens": 500, "output_tokens": 20}), 120)
        self.assertIsNone(budget_tokens({"output_tokens": 20}))
        self.assertIsNone(budget_tokens({}))


if __name__ == "__main__":
    unittest.main()
