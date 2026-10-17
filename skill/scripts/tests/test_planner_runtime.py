from __future__ import annotations

import argparse
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

import bt_cli_planner
import bt_planner_runtime as runtime
from bt_profiles import LAUNCHABLE


class PlannerRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.cwd = self.root / "project"
        self.home.mkdir()
        self.cwd.mkdir()
        self.requirement_dir = self.root / "requirements" / "REQ-100"
        self.requirement_dir.mkdir(parents=True)
        (self.requirement_dir / "SPEC.md").write_text("# REQ-100\n", encoding="utf-8")
        self.profiles = {
            "claude-test": {"provider": "claude", "bin": "claude", "env": {
                "CLAUDE_CONFIG_DIR": str(self.home / "claude-account")}, "work_only": False},
            "codex-test": {"provider": "codex", "bin": "codex", "env": {
                "CODEX_HOME": str(self.home / "codex-account")}, "work_only": False},
            "agy-test": {"provider": "antigravity", "bin": "agy", "env": {}, "work_only": False},
        }
        claude_agent = self.home / "claude-account" / "agents" / "planner.md"
        agy_agent = self.home / ".gemini" / "config" / "agents" / "planner" / "agent.md"
        claude_agent.parent.mkdir(parents=True)
        agy_agent.parent.mkdir(parents=True)
        marker = runtime.GENERATED_AGENT_MARKER
        claude_agent.write_text(f"<!-- {marker} -->\ngenerated Planner", encoding="utf-8")
        agy_agent.write_text(f"<!-- {marker} -->\ngenerated Planner", encoding="utf-8")
        self.load_profiles = patch("bt_profiles.load", return_value=self.profiles)
        self.which = patch.object(runtime.shutil, "which", side_effect=lambda command: f"/fake/{command}")
        self.load_profiles.start()
        self.which.start()
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.load_profiles.stop)
        self.addCleanup(self.which.stop)

    def request(self, provider: str, *, profile: str | None = None, model: str = "selected-model",
                effort: str | None = "xhigh", prompt: str = "Plan this requirement",
                requirement_dir: Path | None = None, repositories: dict[str, Path] | None = None
                ) -> runtime.PlannerRequest:
        selected_profile = profile or {"claude": "claude-test", "codex": "codex-test",
                                       "antigravity": "agy-test"}.get(provider, "unknown")
        return runtime.PlannerRequest(project="metodologia", provider=provider, profile=selected_profile,
                                     model=model, effort=effort, prompt=prompt, cwd=self.cwd,
                                     requirement_dir=requirement_dir or self.requirement_dir,
                                     repositories=repositories if repositories is not None else {"skill": self.cwd})

    def test_every_registered_provider_preserves_selection_and_account(self):
        self.assertEqual(set(LAUNCHABLE), {spec["provider"] for spec in self.profiles.values()})
        foreign_env = {"PATH": "/fake", "CLAUDE_CONFIG_DIR": "/foreign/claude",
                       "CODEX_HOME": "/foreign/codex", "ANTIGRAVITY_SESSION_ID": "parent"}
        for provider in LAUNCHABLE:
            with self.subTest(provider=provider):
                request = self.request(provider)
                prepared = runtime.prepare_invocation(request, home=self.home, environ=foreign_env)
                self.assertEqual(prepared.provider, provider)
                self.assertEqual(prepared.profile, request.profile)
                self.assertEqual(prepared.model, request.model)
                self.assertEqual(prepared.effort, request.effort)
                self.assertEqual(prepared.cwd, self.cwd.resolve())
                self.assertIn("--model", prepared.argv)
                self.assertEqual(prepared.argv[prepared.argv.index("--model") + 1], request.model)
                if provider == "claude":
                    self.assertEqual(prepared.env.get("CLAUDE_CONFIG_DIR"), self.profiles[request.profile]["env"]["CLAUDE_CONFIG_DIR"])
                    self.assertNotIn("CODEX_HOME", prepared.env)
                    self.assertIn(("--effort", request.effort), tuple(zip(prepared.argv, prepared.argv[1:])))
                    self.assertIn("--agent", prepared.argv)
                    self.assertIn(runtime.CLAUDE_STDIN_PROMPT, prepared.argv)
                    self.assertNotIn(request.prompt, prepared.argv)
                    self.assertIn(str(self.requirement_dir), prepared.stdin)
                    self.assertIn(f"- skill: {self.cwd}", prepared.stdin)
                    self.assertIn(request.prompt, prepared.stdin)
                elif provider == "codex":
                    self.assertEqual(prepared.env.get("CODEX_HOME"), self.profiles[request.profile]["env"]["CODEX_HOME"])
                    self.assertNotIn("CLAUDE_CONFIG_DIR", prepared.env)
                    developer_config = next(value for value in prepared.argv if value.startswith("developer_instructions="))
                    instructions = json.loads(developer_config.removeprefix("developer_instructions="))
                    effort_config = prepared.argv[prepared.argv.index("--config") + 1]
                    self.assertEqual(json.loads(effort_config.removeprefix("model_reasoning_effort=")), request.effort)
                    root = runtime.resource_root()
                    for relative in ("agents/planner.md", *runtime.PRIVATE_SKILLS):
                        source = root / relative
                        self.assertIn(runtime._markdown_body(source), instructions)
                    self.assertIn(str(self.requirement_dir), prepared.stdin)
                    self.assertIn(request.prompt, prepared.stdin)
                else:
                    self.assertNotIn("CLAUDE_CONFIG_DIR", prepared.env)
                    self.assertNotIn("CODEX_HOME", prepared.env)
                    self.assertNotIn("ANTIGRAVITY_SESSION_ID", prepared.env)
                    self.assertIn(("--effort", request.effort), tuple(zip(prepared.argv, prepared.argv[1:])))
                    prompt_event = json.loads(prepared.stdin)
                    self.assertIn(str(self.requirement_dir), prompt_event["message"]["content"])
                    self.assertIn(request.prompt, prompt_event["message"]["content"])

    def test_fake_provider_executables_invoke_each_provider_once_without_model_calls(self):
        fake_cli = self.root / "fake-provider"
        fake_cli.write_text(
            f"#!{sys.executable}\n"
            "import json, os, sys\n"
            "details = {'args': sys.argv[1:], 'stdin': sys.stdin.read(),\n"
            "           'claude_config': os.environ.get('CLAUDE_CONFIG_DIR'),\n"
            "           'codex_home': os.environ.get('CODEX_HOME')}\n"
            "with open(os.environ['FAKE_RUNTIME_CAPTURE'], 'w', encoding='utf-8') as output:\n"
            "    json.dump(details, output)\n"
            "if os.environ['FAKE_RUNTIME_PROVIDER'] == 'antigravity':\n"
            "    print(json.dumps({'event':'init','init':{'model':'selected-model'}}))\n"
            "    print(json.dumps({'event':'result','result':{'status':'SUCCESS','response':'planned'}}))\n"
            "else:\n"
            "    print('planned')\n",
            encoding="utf-8",
        )
        fake_cli.chmod(0o700)
        for provider in LAUNCHABLE:
            with self.subTest(provider=provider):
                capture = self.root / f"{provider}.json"
                environ = {"PATH": os.environ["PATH"], "FAKE_RUNTIME_CAPTURE": str(capture),
                           "FAKE_RUNTIME_PROVIDER": provider}
                with patch.object(runtime.shutil, "which", return_value=str(fake_cli)):
                    result = runtime.invoke(self.request(provider), home=self.home, environ=environ)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.response.strip(), "planned")
                details = json.loads(capture.read_text(encoding="utf-8"))
                self.assertEqual(details["args"][details["args"].index("--model") + 1], "selected-model")
                self.assertIn(str(self.requirement_dir), details["stdin"])
                self.assertIn("Plan this requirement", details["stdin"])
                if provider == "claude":
                    self.assertEqual(details["claude_config"], self.profiles["claude-test"]["env"]["CLAUDE_CONFIG_DIR"])
                    self.assertIsNone(details["codex_home"])
                elif provider == "codex":
                    self.assertEqual(details["codex_home"], self.profiles["codex-test"]["env"]["CODEX_HOME"])
                    self.assertIsNone(details["claude_config"])
                else:
                    event = json.loads(details["stdin"])
                    self.assertEqual(event["message"]["content"], runtime._request_prompt(self.request(provider)))

    def test_missing_or_mismatched_selection_fails_without_runtime_call(self):
        cases = (
            self.request("unsupported"),
            self.request("codex", profile="claude-test"),
            self.request("codex", model=""),
            self.request("codex", prompt=""),
            self.request("codex", profile="missing-profile"),
        )
        for request in cases:
            with self.subTest(provider=request.provider, profile=request.profile, model=request.model), \
                    self.assertRaises(runtime.PlannerRuntimeError):
                runtime.prepare_invocation(request, home=self.home)

    def test_omitted_effort_keeps_provider_default_without_inserting_one(self):
        for provider in LAUNCHABLE:
            with self.subTest(provider=provider):
                request = self.request(provider, effort=None)
                prepared = runtime.prepare_invocation(request, home=self.home)
                self.assertIsNone(prepared.effort)
                self.assertNotIn("--effort", prepared.argv)
                self.assertFalse(any(value.startswith("model_reasoning_effort=") for value in prepared.argv))

    def test_missing_native_agent_and_binary_fail_closed(self):
        (self.home / "claude-account" / "agents" / "planner.md").unlink()
        with self.assertRaisesRegex(runtime.PlannerRuntimeError, "not installed"):
            runtime.prepare_invocation(self.request("claude"), home=self.home)

        with patch.object(runtime.shutil, "which", return_value=None), \
                self.assertRaisesRegex(runtime.PlannerRuntimeError, "not on PATH"):
            runtime.prepare_invocation(self.request("codex"), home=self.home)

    def test_hand_authored_native_agent_is_preserved_and_not_invoked(self):
        agent = self.home / "claude-account" / "agents" / "planner.md"
        agent.write_text("# Hand-authored Planner", encoding="utf-8")
        with self.assertRaisesRegex(runtime.PlannerRuntimeError, "preserve it"):
            runtime.prepare_invocation(self.request("claude"), home=self.home)

    def test_invalid_requirement_and_repository_context_fails_closed(self):
        request = self.request("codex", requirement_dir=self.root / "missing")
        with self.assertRaisesRegex(runtime.PlannerRuntimeError, "Requirement directory"):
            runtime.prepare_invocation(request, home=self.home)

        request = self.request("codex", repositories={"bad role": self.cwd})
        with self.assertRaisesRegex(runtime.PlannerRuntimeError, "repository roles"):
            runtime.prepare_invocation(request, home=self.home)

    def test_work_only_account_is_authorized_before_invocation(self):
        self.profiles["claude-test"]["work_only"] = True
        with patch("bt_profiles.is_work_project", return_value=False), \
                self.assertRaisesRegex(runtime.PlannerRuntimeError, "Nothing was sent"):
            runtime.prepare_invocation(self.request("claude"), home=self.home)

    def test_nonzero_provider_result_is_returned_without_fallback(self):
        calls = []

        def failed_runner(argv, **kwargs):
            calls.append(argv)
            return CompletedProcess(argv, 17, stdout="", stderr="provider rejected selection")

        result = runtime.invoke(self.request("codex"), runner=failed_runner, home=self.home)
        self.assertEqual(result.returncode, 17)
        self.assertEqual(result.stderr, "provider rejected selection")
        self.assertEqual(len(calls), 1)

    def test_antigravity_model_rejection_keeps_provider_error(self):
        payload = json.dumps({"event": "result", "result": {
            "status": "ERROR", "error": {"message": "model rejected"}}})

        def failed_runner(argv, **kwargs):
            return CompletedProcess(argv, 2, stdout=payload, stderr="")

        result = runtime.invoke(self.request("antigravity"), runner=failed_runner,
                                home=self.home, environ={"PATH": os.environ["PATH"]})
        self.assertEqual(result.returncode, 2)
        self.assertIn("model rejected", result.stderr)
        self.assertEqual(result.response, "")

    def test_antigravity_discards_response_when_effective_model_differs(self):
        payload = "\n".join((
            json.dumps({"event": "init", "init": {"model": "CCPA"}}),
            json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": "wrong model"}}),
        ))

        def mismatched_runner(*args, **kwargs):
            return CompletedProcess(args[0], 0, stdout=payload, stderr="")

        with self.assertRaisesRegex(runtime.PlannerRuntimeError, "reported model 'CCPA'.*response discarded"):
            runtime.invoke(self.request("antigravity"), runner=mismatched_runner,
                           home=self.home, environ={"PATH": os.environ["PATH"]})

    def test_antigravity_discards_response_when_effective_model_is_unreported(self):
        payload = json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": "unverified"}})

        def missing_model_runner(*args, **kwargs):
            return CompletedProcess(args[0], 0, stdout=payload, stderr="")

        with self.assertRaisesRegex(runtime.PlannerRuntimeError, "did not report exactly one valid init event"):
            runtime.invoke(self.request("antigravity"), runner=missing_model_runner,
                           home=self.home, environ={"PATH": os.environ["PATH"]})

    def test_timeout_is_reported_without_retry_or_fallback(self):
        calls = []

        def timeout_runner(argv, **kwargs):
            calls.append(argv)
            raise runtime.subprocess.TimeoutExpired(argv, kwargs["timeout"])

        with self.assertRaisesRegex(runtime.PlannerRuntimeError, "timed out"):
            runtime.invoke(self.request("codex"), runner=timeout_runner, home=self.home)
        self.assertEqual(len(calls), 1)

    def test_cli_reads_prompt_from_stdin_and_prints_only_response(self):
        args = argparse.Namespace(provider="codex", profile="codex-test", model="selected-model",
                                  effort="high", timeout=90, req="REQ-100", repo=["skill=/repo/skill"])
        result = runtime.InvocationResult(provider="codex", profile="codex-test", model="selected-model",
                                          effort="high", returncode=0, response="plan result", stderr="")
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch("bt_cli_planner.find_req", return_value=self.requirement_dir) as find_call, \
                patch("bt_cli_planner.invoke", return_value=result) as invoke_call, \
                patch("sys.stdin", io.StringIO("request text")), redirect_stdout(stdout), redirect_stderr(stderr):
            code = bt_cli_planner.dispatch(args, "metodologia", self.cwd, self.root)
        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue(), "plan result\n")
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(invoke_call.call_args.args[0].prompt, "request text")
        self.assertEqual(invoke_call.call_args.args[0].model, "selected-model")
        self.assertEqual(invoke_call.call_args.args[0].effort, "high")
        self.assertEqual(invoke_call.call_args.args[0].requirement_dir, self.requirement_dir)
        self.assertEqual(invoke_call.call_args.args[0].repositories, {"skill": Path("/repo/skill")})
        find_call.assert_called_once_with(self.root / "metodologia", "REQ-100")


if __name__ == "__main__":
    unittest.main()
