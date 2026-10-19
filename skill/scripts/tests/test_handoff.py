"""Automatic hand-off, delegation routing, child environments, and agent context."""
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
import bt_core  # noqa: E402
import bt_config  # noqa: E402
import bt_context  # noqa: E402
import bt_delegate  # noqa: E402
import bt_events  # noqa: E402
import bt_handoff  # noqa: E402
import bt_learn  # noqa: E402
import bt_profiles  # noqa: E402


class IsolatedCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="handoff-test-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "bitacora"
        self.state = self.root / ".state"
        self.state.mkdir(parents=True)
        # The discovery isolation hook is absent when this file is run alone.
        for target, value in (
            ("bt_handoff.ROOT", self.root), ("bt_config.STATE", self.state),
            ("bt_delegate.ROOT", self.root), ("bt_delegate.STATE", self.state),
            ("bt_delegate.DIR", self.state / "delegations"),
            ("bt_agents.STATE", self.state), ("bt_profiles.STATE", self.state),
            ("bt_profiles.ROOT", self.root), ("bt_events.STATE", self.state),
            ("bt_context.ROOT", self.root), ("bt_learn.ROOT", self.root),
            ("bt_core.STATE", self.state),
        ):
            p = patch(target, value)
            p.start()
            self.addCleanup(p.stop)


class HandoffTests(IsolatedCase):
    def setUp(self) -> None:
        super().setUp()
        self.project = "sample"
        self.rdir = self.root / self.project / "requirements" / "REQ-001-demo"
        self.rdir.mkdir(parents=True)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        self.roles = {"app": self.repo}
        p = patch.object(bt_handoff.ws, "repos", lambda root, project: self.roles)
        p.start()
        self.addCleanup(p.stop)

    def write_plan(self, task_lines: list[str] | None = None, status="draft", extra="") -> Path:
        lines = ["---", f"status: {status}", "---", "# Plan", "", "### M1 — Work"]
        lines.extend(task_lines if task_lines is not None else
                     ["- [ ] T1 — implement feature · repo: app · verify: `python -m unittest`"])
        if extra:
            lines.extend(["", extra])
        path = self.rdir / "PLAN.md"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        (self.rdir / "SPEC.md").write_text("# Specification\n", encoding="utf-8")
        return path

    def test_assess_reports_unrunnable_plan_problems(self):
        missing = bt_handoff.assess(self.project, self.rdir)
        self.assertFalse(missing["ok"])
        self.assertTrue(any("no PLAN.md" in x for x in missing["problems"]))

        cases = [
            ([ ], "no task lines"),
            (["- [ ] T1 — first · repo: app · verify: `check`", "- [ ] T1 — second · repo: app · verify: `check`"], "appears more than once"),
            (["- [ ] T1 — first · repo: app · after: T9 · verify: `check`"], "depends on T9"),
            (["- [ ] T1 — first · repo: app · after: T2 · verify: `check`",
              "- [ ] T2 — second · repo: app · after: T1 · verify: `check`"], "circular dependency"),
            (["- [ ] T1 — first · repo: nowhere · verify: `check`"], "not registered"),
        ]
        for tasks, expected in cases:
            with self.subTest(expected=expected):
                self.write_plan(tasks)
                report = bt_handoff.assess(self.project, self.rdir)
                self.assertFalse(report["ok"])
                self.assertTrue(any(expected in x for x in report["problems"]), report["problems"])
        self.write_plan()
        self.roles = {}
        report = bt_handoff.assess(self.project, self.rdir)
        self.assertFalse(report["ok"])
        self.assertTrue(any("no repository is registered" in x for x in report["problems"]))

    def test_assess_requires_approval_for_each_plan_threshold_and_risk(self):
        self.write_plan(["- [ ] T1 — feature · repo: app · verify: `check`",
                         "### M2 — Another", "- [ ] T2 — next · repo: app · verify: `check`"])
        with patch.object(bt_config, "get", side_effect=lambda key, default=None:
                          {"approval.max_milestones": 1, "approval.max_tasks": 40,
                           "approval.auto": True}.get(key, default)):
            self.assertTrue(any("milestones" in x for x in bt_handoff.assess(self.project, self.rdir)["reasons"]))

        tasks = [f"- [ ] T{i} — feature {i} · repo: app · verify: `check`" for i in range(1, 3)]
        self.write_plan(tasks)
        with patch.object(bt_config, "get", side_effect=lambda key, default=None:
                          {"approval.max_milestones": 8, "approval.max_tasks": 1,
                           "approval.auto": True}.get(key, default)):
            self.assertTrue(any("pending tasks" in x for x in bt_handoff.assess(self.project, self.rdir)["reasons"]))

        for metadata, expected in (("level: architecture", "architecture-level"), ("risk: high", "risk: high")):
            with self.subTest(metadata=metadata):
                self.write_plan([f"- [ ] T1 — feature · repo: app · {metadata} · verify: `check`"])
                report = bt_handoff.assess(self.project, self.rdir)
                self.assertTrue(any(expected in x for x in report["reasons"]), report["reasons"])

        self.write_plan(["- [ ] T1 — feature · repo: app"])
        self.assertTrue(any("no task has a machine-runnable verify" in x
                            for x in bt_handoff.assess(self.project, self.rdir)["reasons"]))
        self.write_plan()
        with patch.object(bt_config, "get", side_effect=lambda key, default=None:
                          False if key == "approval.auto" else default):
            self.assertTrue(any("automatic approval is turned off" in x
                                for x in bt_handoff.assess(self.project, self.rdir)["reasons"]))

    def test_risky_words_in_plan_and_spec_require_approval(self):
        examples = ["drop table", "production deploy", "git push", "payment", "rotate the api keys", "send email"]
        for phrase, (label, _) in zip(examples, bt_handoff.RISK_WORDS):
            with self.subTest(label=label):
                self.write_plan()
                (self.rdir / "SPEC.md").write_text(f"The feature includes {phrase}.\n", encoding="utf-8")
                report = bt_handoff.assess(self.project, self.rdir)
                self.assertTrue(any(label in reason and "SPEC.md" in reason for reason in report["reasons"]),
                                report["reasons"])

        self.write_plan(extra="Never push.\nDo not deploy.\nOut of scope: payments.")
        # naming credentials or the word irreversible is not an action on them
        (self.rdir / "SPEC.md").write_text("A product author can update the page.\nThe module refuses to keep "
                                           "anything that looks like a secret or a password.\nInterrupt only for "
                                           "irreversible or external actions.\n", encoding="utf-8")
        report = bt_handoff.assess(self.project, self.rdir)
        self.assertFalse(report["reasons"], report["reasons"])
        self.assertTrue(report["auto"])

    def test_clean_small_plan_is_automatically_approved(self):
        self.write_plan()
        report = bt_handoff.assess(self.project, self.rdir)
        self.assertTrue(report["ok"])
        self.assertEqual(report["reasons"], [])
        self.assertTrue(report["auto"])

    def launch_patches(self):
        launch = patch("bt_launch.launch", return_value={"opened": "detached", "handoff": "handoff.md"})
        commit = patch("bt_vcs.commit")
        launch_mock = launch.start(); commit.start()
        self.addCleanup(launch.stop); self.addCleanup(commit.stop)
        return launch_mock

    def test_handoff_approves_and_launches_clean_plan_through_the_scheduler(self):
        plan = self.write_plan()
        launch = self.launch_patches()
        out = bt_handoff.handoff(self.project, "REQ-001")
        self.assertEqual(out["decision"], "launched")
        self.assertEqual(bt_handoff._front(plan, "status"), "approved")
        self.assertEqual(launch.call_count, 1)
        self.assertEqual(launch.call_args.kwargs, {"background": True})

    def test_handoff_window_fixed_risk_review_approval_invalid_and_existing_status(self):
        plan = self.write_plan()
        launch = self.launch_patches()
        with patch.object(bt_config, "get", side_effect=lambda key, default=None:
                          {"executor.display": "window", "routing.mode": "fixed"}.get(key, default)):
            out = bt_handoff.handoff(self.project, "REQ-001")
        self.assertEqual(out["decision"], "launched")
        self.assertNotIn("pool", out)
        self.assertFalse(launch.call_args.kwargs["background"])

        plan = self.write_plan(["- [ ] T1 — deploy app · repo: app · verify: `check`"])
        launch.reset_mock()
        with patch("bt_vcs.commit"):
            held = bt_handoff.handoff(self.project, "REQ-001")
        self.assertEqual(held["decision"], "needs_approval")
        self.assertEqual(bt_handoff._front(plan, "status"), "review")
        self.assertIn("hand-off held for approval", plan.read_text(encoding="utf-8"))
        launch.assert_not_called()
        approved_plan = plan.read_text(encoding="utf-8").replace("status: review", "status: approved")
        plan.write_text(approved_plan, encoding="utf-8")
        self.assertEqual(bt_handoff.handoff(self.project, "REQ-001")["decision"], "launched")

        launch.reset_mock()
        plan = self.write_plan([], status="draft")
        original = plan.read_text(encoding="utf-8")
        self.assertEqual(bt_handoff.handoff(self.project, "REQ-001")["decision"], "invalid")
        self.assertEqual(plan.read_text(encoding="utf-8"), original)
        launch.assert_not_called()

        self.write_plan(status="launched")
        self.assertEqual(bt_handoff.handoff(self.project, "REQ-001")["decision"], "already_running")

    def test_dry_run_does_not_write_or_launch(self):
        plan = self.write_plan()
        launch = self.launch_patches()
        before = plan.read_text(encoding="utf-8")
        out = bt_handoff.handoff(self.project, "REQ-001", dry_run=True)
        self.assertEqual(out["decision"], "would_launch")
        self.assertEqual(plan.read_text(encoding="utf-8"), before)
        launch.assert_not_called()


class DelegateTests(IsolatedCase):
    def setUp(self) -> None:
        super().setUp()
        self.work = self.base / "work"
        self.work.mkdir()
        self.account = self.base / "account"
        self.account.mkdir()
        self.work_account = self.base / "work-account"
        self.work_account.mkdir()
        bt_profiles.add("codex-test", "codex", {"CODEX_HOME": str(self.account)})
        bt_profiles.add("claude-test", "claude", {"CLAUDE_CONFIG_DIR": str(self.account)})

    def test_create_routes_with_kind_tier_model_and_effort_without_profile_or_agent(self):
        with patch("bt_agents.pool_for", return_value=["codex-test"]), patch("bt_agents.shutil.which", return_value="/bin/true"):
            order = bt_delegate.create("sample", "Investigate the docs", None, None, self.work, [], None, 1,
                                       None, None, kind="research", tier=1)
        self.assertEqual(order["profile"], "codex-test")
        self.assertEqual(order["agent"], "codex")
        self.assertEqual((order["kind"], order["tier"], order["model"], order["effort"]),
                         ("research", 1, "gpt-6-luna", "high"))
        self.assertEqual(json.loads((bt_delegate.DIR / order["id"] / "TASK.json").read_text()), order)

    def test_audit_created_inside_claude_prefers_codex_account(self):
        seen = {}
        def route(project, kind, tier, avoid=None, **kwargs):
            seen.update(project=project, kind=kind, tier=tier, avoid=avoid, **kwargs)
            return {"profile": "codex-test", "agent": "codex", "model": "gpt-6.1-sol", "effort": "high",
                    "tier": tier, "why": "other provider"}
        with patch.dict(os.environ, {"CLAUDECODE": "1", "BITACORA_KIND": "implement"}), \
             patch.object(bt_delegate, "auto_route", side_effect=route):
            order = bt_delegate.create("sample", "Review this change", None, None, self.work, [], None, 1,
                                       None, None, kind="audit")
        self.assertEqual(seen["avoid"], {"claude"})
        self.assertEqual(seen["role"], "reviewer")
        self.assertEqual(order["profile"], "codex-test")

    def test_all_accounts_cooling_says_nothing_was_sent(self):
        with patch("bt_agents.pool_for", return_value=["claude-test"]), \
             patch("bt_agents.route", side_effect=bt_agents.NoRoute(2_000_000_000)):
            with self.assertRaisesRegex(SystemExit, "Nothing was sent"):
                bt_delegate.auto_route("sample", "implement", None)

    def test_inherited_work_only_claude_account_is_refused_for_non_work_project(self):
        bt_profiles.add("claude-work", "claude", {"CLAUDE_CONFIG_DIR": str(self.work_account)}, work_only=True)
        with patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(self.work_account)}):
            with self.assertRaisesRegex(SystemExit, "Nothing was sent"):
                bt_delegate.create("personal", "Task", None, "claude", self.work, [], None, 1, None, None)

    def test_execute_sets_profile_environment_and_drops_parent_task_variables(self):
        result_env = self.base / "child-env.json"
        stub = self.base / "dump_env.py"
        stub.write_text("import json, os, pathlib, sys; pathlib.Path(sys.argv[1]).write_text(json.dumps(dict(os.environ)))\n"
                        "pathlib.Path(sys.argv[2]).write_text(json.dumps({'task_id':'x','status':'done','summary':'ok'}))\n",
                        encoding="utf-8")
        bt_profiles.add("claude-child", "claude", {"CLAUDE_CONFIG_DIR": str(self.account)})
        inherited = {"CLAUDE_CONFIG_DIR": str(self.base / "wrong"), "BITACORA_RUN": "parent-run",
                     "BITACORA_TASK": "parent-task", "BITACORA_SESSION": "parent-session"}
        with patch.dict(os.environ, inherited):
            order = bt_delegate.create("sample", "Write an environment report", "claude-child", None,
                                       self.work, [], None, 1, None, None, kind="docs")
            cmd = f'"{sys.executable}" "{stub}" "{result_env}" "{{result}}"'
            bt_delegate.execute(order["id"], cmd)
        child = json.loads(result_env.read_text(encoding="utf-8"))
        self.assertEqual(child["CLAUDE_CONFIG_DIR"], str(self.account))
        self.assertEqual(child["BITACORA_KIND"], "docs")
        for key in ("BITACORA_RUN", "BITACORA_TASK", "BITACORA_SESSION"):
            self.assertNotIn(key, child)

    def test_usage_limit_outcome_marks_account_cooling(self):
        stub = self.base / "limit.py"
        stub.write_text("import sys; print('usage limit reached'); sys.exit(1)\n", encoding="utf-8")
        order = bt_delegate.create("sample", "Task", "claude-test", None, self.work, [], None, 1, None, None)
        cmd = f'"{sys.executable}" "{stub}"'
        with patch("bt_events.record_attempt"):
            outcome = bt_delegate.execute(order["id"], cmd)
        self.assertEqual(outcome["status"], "usage_limit")
        self.assertIsNotNone(bt_agents.cooling_until("claude-test", "claude"))


class ContextTests(IsolatedCase):
    def test_text_contains_catalog_delegate_learning_commands_and_confirmed_project_learning(self):
        project = "sample"
        learned = "The project keeps API schemas in the contracts directory"
        with patch.object(bt_learn, "ROOT", self.root):
            item = bt_learn.add(project, learned, "Observed in the project repository", "REQ-001/T1")
            bt_learn.confirm(project, item["id"])
            with patch("bt_agents.brief", return_value="### Agents available\n| account table |"), \
                 patch("bt_events.advice", return_value=["Measured route advice"]), \
                 patch("bt_events.read_all", return_value=[]):
                context = bt_context.text(project)
        self.assertIn("Agents available", context)
        self.assertIn("delegate start", context)
        self.assertIn("learn add", context)
        self.assertIn("learn confirm|reject", context)
        self.assertIn(learned, context)


if __name__ == "__main__":
    unittest.main()
