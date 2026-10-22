import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_block_agent as agent
import bt_planner_runtime as runtime
import bt_profiles

HELP = "--tools --strict-mcp-config --mcp-config --setting-sources --disable-slash-commands"
ROUTE = {"role": "planner", "verified": True, "provider": "claude", "profile": "p1", "model": "m-1",
         "effort": "high", "authorized_by": "m2-role-policy"}
IDENTITY = {"run_id": "RUN-1", "task_id": "T1", "cycle": 1}
PROPOSAL = json.dumps({"schema_version": "recovery-proposal/1"}).encode()


def evidence(**extra):
    base = {"schema_version": "recovery-evidence/1", "diagnosable": True, "missing_sources": [],
            "sources": {"m1_attempts": {"attempts": [1, 2]}}, "source_identities": {}, "not_run_checks": [],
            "evidence_sha256": "e" * 64}
    base.update(extra)
    return base


class FakeCli:
    """Models the CLI's tool semantics: only `--tools` names exist, MCP servers only from the strict config."""

    def __init__(self, stdout=PROPOSAL, returncode=0, help_text=HELP, timeout=False, attempt_writes=False):
        self.calls, self.stdout, self.returncode = [], stdout, returncode
        self.help_text, self.timeout, self.attempt_writes = help_text, timeout, attempt_writes
        self.writes = []
        self.denied = []

    def probe(self, argv, **kw):
        return subprocess.CompletedProcess(argv, 0, self.help_text, "")

    def run(self, argv, **kw):
        self.calls.append((argv, kw))
        if self.timeout:
            raise subprocess.TimeoutExpired(argv, kw["timeout"])
        tools = argv[argv.index("--tools") + 1].split(",") if argv[argv.index("--tools") + 1] else []
        servers = {}
        if "--strict-mcp-config" in argv:
            servers = json.loads(Path(argv[argv.index("--mcp-config") + 1]).read_text())["mcpServers"]
        if self.attempt_writes:
            for tool in ("Write", "mcp__files__write"):
                if tool in tools or (tool.startswith("mcp__") and servers):
                    self.writes.append(tool)
                else:
                    self.denied.append(tool)
        return subprocess.CompletedProcess(argv, self.returncode, self.stdout, b"")


class RecoveryDiagnosisTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Path(self.tmp.name) / "store"
        self.run_dir = Path(self.tmp.name) / "run"
        self.run_dir.mkdir()
        (self.run_dir / "RUN.json").write_text("{}")
        self.home = Path(self.tmp.name) / "home"
        agent_file = self.home / ".claude" / "agents" / "planner.md"
        agent_file.parent.mkdir(parents=True)
        agent_file.write_text(runtime.GENERATED_AGENT_MARKER)
        spec = {"provider": "claude", "bin": "claude", "env": {}}
        for name, value in (("get", spec), ("require_launchable", "claude"), ("authorize", None),
                            ("session_env", {"PATH": "/usr/bin"})):
            patcher = patch.object(bt_profiles, name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(runtime.shutil, "which", return_value="/usr/bin/claude")
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(runtime, "_native_agent_path", return_value=agent_file)
        patcher.start()
        self.addCleanup(patcher.stop)

    def call(self, cli, route=None, ev=None, identity=IDENTITY):
        before = sorted(p.name for p in self.run_dir.iterdir())
        run_digest = (self.run_dir / "RUN.json").read_bytes()
        result = agent.diagnose_recovery("proj", ev or evidence(), identity, route or ROUTE, store=self.store,
                                         timeout_seconds=30, runner=cli.run, probe_runner=cli.probe, home=self.home)
        self.assertEqual(before, sorted(p.name for p in self.run_dir.iterdir()))  # target run untouched
        self.assertEqual((self.run_dir / "RUN.json").read_bytes(), run_digest)
        return result

    def test_ok_returns_untrusted_bytes_and_persists_provenance(self):
        cli = FakeCli()
        result = self.call(cli)
        self.assertEqual(result["outcome"], "ok")
        self.assertEqual(result["raw"], PROPOSAL)
        argv, kw = cli.calls[0]
        self.assertEqual(argv[argv.index("--model") + 1], "m-1")
        self.assertEqual(argv[argv.index("--agent") + 1], "planner")
        self.assertEqual(kw["timeout"], 30)
        self.assertNotEqual(Path(kw["cwd"]), self.run_dir)
        stored = json.loads(next((self.store / agent.RECOVERY_DIR).glob("*.json")).read_text())
        self.assertEqual(stored["provenance"]["route"]["authorized_by"], "m2-role-policy")
        self.assertEqual(stored["provenance"]["authorization_status"], "authorized")
        self.assertEqual(stored["provenance"]["evidence_sha256"], "e" * 64)

    def test_builtin_write_and_mcp_write_cannot_be_invoked(self):
        cli = FakeCli(attempt_writes=True)
        self.assertEqual(self.call(cli)["outcome"], "ok")
        self.assertEqual(cli.writes, [])
        self.assertEqual(sorted(cli.denied), ["Write", "mcp__files__write"])
        argv = cli.calls[0][0]
        self.assertEqual(argv[argv.index("--tools") + 1], "")
        self.assertIn("--strict-mcp-config", argv)

    def test_single_invocation_per_cycle(self):
        cli = FakeCli(timeout=True)
        self.assertEqual(self.call(cli)["outcome"], "timeout")
        self.assertEqual(self.call(cli)["outcome"], "already_invoked")
        self.assertEqual(len(cli.calls), 1)

    def test_unsupported_sandbox_blocks_before_dispatch(self):
        cli = FakeCli(help_text="--tools")
        self.assertEqual(self.call(cli)["outcome"], "unsupported_diagnostic_sandbox")
        self.assertEqual(cli.calls, [])
        other = dict(ROUTE, provider="codex")
        with patch.object(bt_profiles, "require_launchable", return_value="codex"):
            self.assertEqual(self.call(FakeCli(), route=other, identity={"c": 2})["outcome"],
                             "unsupported_diagnostic_sandbox")

    def test_malformed_json_and_nonzero_exit_are_blockers_without_retry(self):
        for identity, raw in (({"case": "text"}, b"not json"), ({"case": "nan"}, b'{"value": NaN}')):
            cli = FakeCli(stdout=raw)
            result = self.call(cli, identity=identity)
            self.assertEqual(result["outcome"], "invalid_json")
            self.assertEqual(result["raw"], raw)
        failed = FakeCli(returncode=2)
        self.assertEqual(self.call(failed, identity={"c": 3})["outcome"], "unavailable")
        self.assertEqual(len(failed.calls), 1)

    def test_unauthorized_profile_and_unverified_route(self):
        cli = FakeCli()
        with patch.object(bt_profiles, "authorize", side_effect=bt_profiles.ProfileError("work only")):
            self.assertEqual(self.call(cli)["outcome"], "unauthorized_route")
        for bad in (dict(ROUTE, verified=False), dict(ROUTE, role="advice"), {k: v for k, v in ROUTE.items() if k != "model"},
                    dict(ROUTE, authorized_by="")):
            self.assertEqual(self.call(cli, route=bad, identity={"bad": str(bad)})["outcome"], "unauthorized_route")
        self.assertEqual(cli.calls, [])

    def test_incomplete_or_oversized_evidence_is_never_truncated(self):
        cli = FakeCli()
        self.assertEqual(self.call(cli, ev=evidence(diagnosable=False))["outcome"], "evidence_incomplete")
        self.assertEqual(self.call(cli, ev=evidence(missing_sources=["m6_results"]), identity={"c": 2})["outcome"],
                         "evidence_incomplete")
        huge = evidence(sources={"m1_attempts": {"blob": "x" * (agent.EVIDENCE_BYTES + 10)}})
        self.assertEqual(self.call(cli, ev=huge, identity={"c": 3})["outcome"], "evidence_incomplete")
        self.assertEqual(cli.calls, [])

    def test_large_source_is_read_in_bounded_sections_without_loss(self):
        payload = "Q" * (agent.SECTION_BYTES * 2 + 5)
        cli = FakeCli()
        self.assertEqual(self.call(cli, ev=evidence(sources={"m1_attempts": {"blob": payload}}))["outcome"], "ok")
        prompt = cli.calls[0][1]["input"].decode()
        self.assertIn("[3/3]", prompt)
        self.assertEqual(prompt.count("Q"), len(payload))

    def test_all_top_level_evidence_is_sent_and_unicode_is_preserved_at_section_boundaries(self):
        payload = "á" * (agent.SECTION_BYTES // 2 + 2)
        ev = evidence(snapshot_ledger={"integrated_tree": payload}, not_run=["audit_gate_evaluation"])
        cli = FakeCli()
        self.assertEqual(self.call(cli, ev=ev)["outcome"], "ok")
        prompt = cli.calls[0][1]["input"].decode()
        self.assertIn('"snapshot_ledger"', prompt)
        self.assertIn('"not_run"', prompt)
        self.assertEqual(prompt.count("á"), len(payload))

    def test_does_not_use_card_advice_settings(self):
        with patch.object(agent, "settings", side_effect=AssertionError("card advice settings used")):
            self.assertEqual(self.call(FakeCli())["outcome"], "ok")


if __name__ == "__main__":
    unittest.main()
