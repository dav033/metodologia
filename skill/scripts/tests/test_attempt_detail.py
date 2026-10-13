"""Attempt detail telemetry: classification, summaries, pages, CLI and execution paths."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import bt_agents  # noqa: E402
import bt_config  # noqa: E402
import bt_core  # noqa: E402
import bt_delegate  # noqa: E402
import bt_events  # noqa: E402
import bt_notify  # noqa: E402
import bt_page_metrics  # noqa: E402
import bt_profiles  # noqa: E402
import bt_run  # noqa: E402
import bt_runprompt as rp  # noqa: E402
import bt_runsettle as settle  # noqa: E402
import bt_runstate as rs  # noqa: E402
import bt_runtask as rt  # noqa: E402


MARATHON_STUB = r'''
import os, pathlib, subprocess, sys
env = os.environ
task = env["BITACORA_TASK"]
if task == "FINAL":
    pathlib.Path(env["STUB_RDIR"], "REPORT.md").write_text("# report\n")
    raise SystemExit(0)
cli = [sys.executable, env["STUB_SCRIPT"], "--project", env["BITACORA_PROJECT"]]
subprocess.run(cli + ["task", "done", env["BITACORA_RUN"], task, "--evidence", "verify evidence <ok>"], check=True)
'''


class IsolatedCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="attempt-detail-test-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "bitacora"
        self.state = self.root / ".state"
        self.state.mkdir(parents=True)
        # Patch every module-level root used by the code under test; this test also runs by itself.
        replacements = {
            bt_core: {"ROOT": self.root, "STATE": self.state},
            bt_config: {"STATE": self.state},
            bt_agents: {"STATE": self.state},
            bt_profiles: {"ROOT": self.root, "STATE": self.state},
            bt_events: {"STATE": self.state},
            bt_delegate: {"ROOT": self.root, "STATE": self.state, "DIR": self.state / "delegations"},
            bt_run: {"ROOT": self.root},
            rs: {"STATE": self.state},
            rp: {"ROOT": self.root},
            settle: {"ROOT": self.root},
            rt: {"ROOT": self.root},
        }
        for module, attrs in replacements.items():
            for name, value in attrs.items():
                p = patch.object(module, name, value)
                p.start()
                self.addCleanup(p.stop)
        old_root = os.environ.get("BITACORA_ROOT")
        os.environ["BITACORA_ROOT"] = str(self.root)
        self.addCleanup(lambda: os.environ.__setitem__("BITACORA_ROOT", old_root)
                        if old_root is not None else os.environ.pop("BITACORA_ROOT", None))
        for key in ("CODEX_HOME", "CLAUDE_CONFIG_DIR", "BITACORA_RUN_BACKOFF_SEC", "STUB_CFG", "STUB_ORDER",
                    "STUB_RDIR", "STUB_SCRIPT"):
            old = os.environ.pop(key, None)
            self.addCleanup(lambda name=key, value=old: os.environ.__setitem__(name, value)
                            if value is not None else os.environ.pop(name, None))
        p = patch("bt_agents.shutil.which", return_value="/stub-agent")
        p.start()
        self.addCleanup(p.stop)
        bt_run.commit_bitacora = lambda *args, **kwargs: None
        bt_notify.notify = lambda *args, **kwargs: None
        bt_notify.install_autostart = lambda *args, **kwargs: None
        bt_notify.remove_autostart = lambda *args, **kwargs: None

    def make_run(self, task_line: str, behavior: dict | None = None):
        self.project = "sample"
        self.rdir = self.root / self.project / "requirements" / "REQ-001-demo"
        self.rdir.mkdir(parents=True)
        (self.rdir / "SPEC.md").write_text("---\nstatus: approved\n---\n# Demo\n", encoding="utf-8")
        (self.rdir / "PLAN.md").write_text(
            "---\nstatus: approved\n---\n# Plan\n\n## Tasks\n" + task_line + "\n", encoding="utf-8")
        self.work = self.base / "work"
        self.work.mkdir()
        cfg = self.work / "stub.json"
        cfg.write_text(json.dumps(behavior or {}), encoding="utf-8")
        self.stub = self.base / "marathon_stub.py"
        self.stub.write_text(MARATHON_STUB, encoding="utf-8")
        os.environ.update(STUB_CFG=str(cfg), STUB_ORDER=str(self.work / "order.json"), STUB_RDIR=str(self.rdir),
                          STUB_SCRIPT=str(SCRIPTS / "bitacora.py"))
        self.cmd = f'"{sys.executable}" "{self.stub.as_posix()}"'
        return self.project, self.rdir


class AttemptDetails(IsolatedCase):
    def test_complexity_declared_largest_and_inference_rules(self):
        self.assertEqual(bt_events.complexity_of([{"complexity": "S"}, {"complexity": "L"}, {"complexity": "M"}]),
                         ("L", "declared"))
        self.assertEqual(bt_events.complexity_of([{"level": "architecture"}]), ("L", "inferred"))
        self.assertEqual(bt_events.complexity_of([{}, {}, {}]), ("M", "inferred"))
        self.assertEqual(bt_events.complexity_of([{}, {}]), ("S", "inferred"))

    def test_plan_parser_reads_complexity_and_size_alias_and_absence(self):
        self.assertEqual(rs.parse_task_line("Declared · complexity: M")["complexity"], "M")
        self.assertEqual(rs.parse_task_line("Large · size: large")["complexity"], "L")
        self.assertIsNone(rs.parse_task_line("No size declared")["complexity"])

    def test_outcome_classes(self):
        cases = {
            ("done", None): "verified", ("verify_failed", "pytest failed"): "verify_failed",
            ("timeout", None): "timeout", ("usage_limit", None): "usage_limit",
            ("failed", "session ended without task done/fail"): "no_verdict",
            ("failed", "I could not finish"): "agent_reported_failure", ("blocked", None): "blocked_needs_human",
            ("skipped", None): "skipped_dependency", ("stopped", None): "stopped_by_user",
        }
        for args, expected in cases.items():
            with self.subTest(args=args):
                self.assertEqual(bt_events.outcome_of(*args), expected)

    def test_detail_uses_last_error_or_evidence_and_caps_why(self):
        failed = {"id": "T1", "last_error": "verify command failed: pytest -q", "attempts": 1}
        detail = bt_events.detail_for([failed], "verify_failed", {"T1": "verify_failed"})
        self.assertIn("pytest -q", detail["why"])
        self.assertEqual(detail["outcome"], "verify_failed")
        done = {"id": "T2", "evidence": "all checks passed", "attempts": 1}
        self.assertIn("all checks passed", bt_events.detail_for([done], "done")["why"])
        long_tasks = [{"id": f"T{i}", "last_error": "x" * 500, "attempts": 1} for i in range(10)]
        self.assertLessEqual(len(bt_events.detail_for(long_tasks, "failed")["why"]), 700)

    def test_record_attempt_detail_key_values_summary_and_reasons(self):
        state = {"req": "REQ-001", "agent": "claude", "profile": "work-account"}
        info = {"agent": "codex", "profile": "acct", "model": "gpt-test", "effort": None,
                "kind": "test", "tier": 1, "tasks": ["T1"], "seconds": 12, "why": "selected for test"}
        detail = {"complexity": "L", "complexity_source": "declared", "attempt": 2,
                  "outcome": "verified", "why": "pytest passed", "titles": ["Task title"]}
        path = bt_events.record_attempt("sample", state, "T1", 2, info, "done", detail)
        self.assertIsNotNone(path)
        row = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual((row["complexity"], row["complexity_source"], row["attempt"], row["outcome"],
                          row["why"], row["route_why"]), ("L", "declared", 2, "verified", "pytest passed", "selected for test"))
        pairs = dict(bt_events.key_values(row))
        for key in ("kind of work", "complexity", "agent", "account", "model", "effort", "result", "outcome",
                    "why", "duration", "tokens (measured)", "cost reported (USD)"):
            self.assertIn(key, pairs)
        self.assertEqual(pairs["effort"], "CLI default")
        self.assertEqual(pairs["tokens (measured)"], "—")
        self.assertEqual(pairs["complexity"], "L (declared)")

        rows = [row, {**row, "event_id": "other", "result": "verify_failed", "outcome": "verify_failed",
                      "why": "pytest failed"}]
        self.assertEqual(len(bt_events.summary(rows, ("kind", "complexity"))), 1)
        group = bt_events.reasons(rows)[0]
        self.assertEqual(group["outcomes"], {"verified": 1, "verify_failed": 1})
        self.assertEqual(group["worked_because"], ["pytest passed"])
        self.assertEqual(group["failed_because"], ["pytest failed"])

    def test_metrics_page_has_new_sections_and_escapes_attempt_values(self):
        row = {"ts": "2026-10-12T12:00:00", "project": "sample", "task": "T1", "agent": "codex",
               "profile": "account", "model": "model", "effort": None, "kind": "test", "complexity": "M",
               "complexity_source": "declared", "result": "done", "outcome": "verified", "why": "<script>alert(1)</script>",
               "seconds": 3, "usage": {}, "req": "REQ-001", "tasks": ["T1"], "titles": ["<img src=x>"]}
        with patch.object(bt_events, "read_all", return_value=[row]), \
                patch.object(bt_agents, "catalog", return_value={"accounts": [], "ladder": {}}):
            page = bt_page_metrics.metrics_page()
        for heading in ("Por tipo y complejidad", "Por qué falló y por qué salió bien",
                        "Intentos recientes, clave por clave"):
            self.assertIn(heading, page)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page)
        self.assertIn("&lt;img src=x&gt;", page)
        self.assertNotIn("<script>alert(1)</script>", page)

    def test_marathon_attempt_telemetry_declared_verified_and_verify_failed(self):
        verify = f'"{sys.executable}" -c "import sys; sys.exit(0)"'
        self.make_run(f"- [ ] T1 — Build feature · complexity: L · verify: `{verify}`")
        self.assertEqual(bt_run.supervise(self.project, "REQ-001", agent_cmd=self.cmd, once=True,
                                          no_autostart=True, audit=False), 0)
        row = bt_events.read_all()[0]
        self.assertEqual((row["complexity"], row["complexity_source"], row["outcome"]), ("L", "declared", "verified"))
        self.assertIn("verify evidence <ok>", row["why"])

        bad_verify = f'"{sys.executable}" -c "import sys; sys.exit(1)"'
        self.project = "sample"
        self.rdir = self.root / self.project / "requirements" / "REQ-002-demo"
        self.rdir.mkdir(parents=True)
        (self.rdir / "SPEC.md").write_text("---\nstatus: approved\n---\n# Demo\n", encoding="utf-8")
        (self.rdir / "PLAN.md").write_text(
            "---\nstatus: approved\n---\n# Plan\n\n## Tasks\n"
            f"- [ ] T1 — Build feature · complexity: M · verify: `{bad_verify}`\n", encoding="utf-8")
        self.assertEqual(bt_run.supervise(self.project, "REQ-002", agent_cmd=self.cmd, once=True,
                                          no_autostart=True, audit=False), 0)
        row = bt_events.read_all()[1]
        self.assertEqual(row["outcome"], "verify_failed")
        self.assertIn(bad_verify, row["why"])

    def test_metrics_cli_attempts_and_why_read_a_handwritten_month_file(self):
        events = self.state / "events"
        events.mkdir()
        rows = [
            {"ts": "2026-10-01T12:00:00", "project": "sample", "req": "REQ-1", "task": "T1", "tasks": ["T1"],
             "titles": ["First"], "kind": "test", "complexity": "S", "complexity_source": "inferred", "attempt": 1,
             "agent": "claude", "profile": "acct", "model": "sonnet", "effort": None, "route_why": "routed",
             "result": "failed", "outcome": "agent_reported_failure", "why": "fixture failure", "seconds": 4, "usage": {}},
            {"ts": "2026-10-02T12:00:00", "project": "sample", "req": "REQ-1", "task": "T2", "tasks": ["T2"],
             "titles": ["Second"], "kind": "test", "complexity": "M", "complexity_source": "declared", "attempt": 2,
             "agent": "codex", "profile": "acct2", "model": "gpt-test", "effort": "high", "route_why": None,
             "result": "done", "outcome": "verified", "why": "checks passed", "seconds": 5, "usage": {}}
        ]
        (events / "attempts-2026-10.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        env = {**os.environ, "BITACORA_ROOT": str(self.root)}
        script = SCRIPTS / "bitacora.py"
        attempts = subprocess.run([sys.executable, str(script), "metrics", "--attempts", "2"],
                                  env=env, capture_output=True, text=True, check=False)
        self.assertEqual(attempts.returncode, 0, attempts.stderr)
        self.assertIn("complexity", attempts.stdout)
        self.assertIn("CLI default", attempts.stdout)
        self.assertIn("checks passed", attempts.stdout)
        why = subprocess.run([sys.executable, str(script), "metrics", "--why"], env=env,
                             capture_output=True, text=True, check=False)
        self.assertEqual(why.returncode, 0, why.stderr)
        self.assertIn("fixture failure", why.stdout)
        self.assertIn("worked_because", why.stdout)

    def test_auto_delegation_reroutes_usage_limit_to_second_account(self):
        first_home, second_home = self.base / "first-home", self.base / "second-home"
        first_home.mkdir(); second_home.mkdir()
        bt_profiles.add("first", "codex", {"CODEX_HOME": str(first_home)})
        bt_profiles.add("second", "codex", {"CODEX_HOME": str(second_home)})
        work = self.base / "delegate-work"
        work.mkdir()
        with patch.object(bt_agents, "pool_for", return_value=["first", "second"]):
            order = bt_delegate.create("sample", "Run delegated task", None, None, work, [], "true", 1,
                                       None, None, kind="test")
        stub = self.base / "delegate_stub.py"
        stub.write_text(
            'import json, os, pathlib, sys\n'
            'if os.environ["CODEX_HOME"].endswith("first-home"):\n'
            ' print("usage limit reached; try again later"); raise SystemExit(1)\n'
            'pathlib.Path(sys.argv[1]).write_text(json.dumps({"task_id": os.environ["BITACORA_DELEGATION"], '
            '"status":"done", "summary":"done", "evidence":"ok", "changed_files":[], '
            '"test_result":"pass", "notes":"", "followups":[]}))\n', encoding="utf-8")
        cmd = f'"{sys.executable}" "{stub}" "{{result}}"'
        with patch.object(bt_agents, "pool_for", return_value=["first", "second"]):
            outcome = bt_delegate.execute(order["id"], cmd)
        self.assertEqual(outcome["status"], "verified")
        self.assertEqual([s.split(":")[0] for s in outcome["rerouted"]], ["first", "second"])
        rows = bt_events.read_all()
        self.assertEqual(len(rows), 2)
        self.assertEqual(len({row["event_id"] for row in rows}), 2)
        self.assertEqual([row["attempt"] for row in rows], [1, 2])

    def test_wait_quota_rechecks_after_short_override_without_real_sleep(self):
        os.environ["BITACORA_RUN_BACKOFF_SEC"] = "0.05"
        calls = []
        def candidates(*args, **kwargs):
            calls.append(len(calls) + 1)
            if len(calls) == 1:
                return [], 1234567890
            return ([{"profile": "second", "agent": "codex", "model": "gpt-test", "effort": "high",
                      "why": "available"}], None)
        order = {"id": "D-test", "project": "sample", "agent": "codex", "profile": "first", "auto": True,
                 "wait_quota": True, "pool": ["first", "second"], "kind": "test"}
        with patch.object(bt_agents, "pool_for", return_value=["first", "second"]), \
                patch.object(bt_agents, "candidates", side_effect=candidates), \
                patch.object(bt_delegate.time, "sleep") as sleep:
            nxt = bt_delegate._next_route(order)
        self.assertEqual(nxt["profile"], "second")
        sleep.assert_called_once_with(0.05)
        self.assertEqual(len(calls), 2)

    def test_pinned_delegation_without_wait_quota_keeps_retry_after_and_does_not_reroute(self):
        home = self.base / "pinned-home"
        home.mkdir()
        bt_profiles.add("pinned", "codex", {"CODEX_HOME": str(home)})
        work = self.base / "pinned-work"
        work.mkdir()
        with patch.object(bt_agents, "pool_for", return_value=["pinned", "other"]):
            order = bt_delegate.create("sample", "Pinned task", "pinned", None, work, [], None, 1,
                                       None, None, kind="test", wait_quota=False)
        stub = self.base / "pinned_limit_stub.py"
        stub.write_text('print("usage limit reached; try again later")\nraise SystemExit(1)\n', encoding="utf-8")
        cmd = f'"{sys.executable}" "{stub}"'
        with patch.object(bt_agents, "pool_for", return_value=["pinned", "other"]):
            outcome = bt_delegate.execute(order["id"], cmd)
        self.assertEqual(outcome["status"], "usage_limit")
        self.assertIn("retry_after", outcome)
        self.assertNotIn("rerouted", outcome)
        self.assertEqual(len(bt_events.read_all()), 1)


class ComplexityStartsHigherTests(unittest.TestCase):
    def test_declared_large_work_starts_at_the_standard_tier(self):
        import bt_agents
        import bt_runstate
        self.assertEqual(bt_agents.start_tier(None, "implement", "L"), 1)
        self.assertEqual(bt_agents.start_tier(None, "implement", "M"), 0)
        self.assertEqual(bt_agents.start_tier("architecture", "implement", "S"), 2)
        task = bt_runstate._new_task({"id": "T1", "done": False, "milestone": None,
                                      **bt_runstate.parse_task_line("Big screen · complexity: L")})
        self.assertEqual((task["complexity"], task["tier"]), ("L", 1))


if __name__ == "__main__":
    unittest.main()
