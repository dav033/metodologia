"""Regression tests for the second adversarial audit fixes."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

# Import the disposable-root harness first so bt_core never captures the real bitácora.
import run_case_support  # noqa: E402,F401
from test_handoff import IsolatedCase  # noqa: E402
import bt_agents  # noqa: E402
import bt_config  # noqa: E402
import bt_core  # noqa: E402
import bt_delegate  # noqa: E402
import bt_events  # noqa: E402
import bt_handoff  # noqa: E402
import bt_learn  # noqa: E402
import bt_profiles  # noqa: E402
import bt_runprompt as rp  # noqa: E402
import bt_runsettle as settle  # noqa: E402
import bt_runstate as rs  # noqa: E402
import bt_runtask as rt  # noqa: E402


class HandoffRound2(IsolatedCase):
    def setUp(self):
        super().setUp()
        self.project = "sample"
        self.rdir = self.root / self.project / "requirements" / "REQ-001-demo"
        self.rdir.mkdir(parents=True)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        p = patch.object(bt_handoff.ws, "repos", lambda root, project: {"app": self.repo})
        p.start()
        self.addCleanup(p.stop)

    def write_plan(self, verify):
        (self.rdir / "PLAN.md").write_text(
            "---\nstatus: draft\n---\n# Plan\n\n### M1 — Work\n"
            f"- [ ] T1 — check · repo: app · verify: `{verify}`\n", encoding="utf-8")
        (self.rdir / "SPEC.md").write_text("# Specification\n", encoding="utf-8")

    def reasons_for(self, verify):
        self.write_plan(verify)
        return bt_handoff.assess(self.project, self.rdir)["reasons"]

    def test_verify_approves_read_only_interpreters_and_common_test_commands(self):
        safe = (
            'python3 -c "import calc; assert calc.add(2, 3) == 5"', "npm test", "npx vitest run src",
            'env -i PATH="$PATH" npm run typecheck', "pytest -q", "cargo test",
        )
        for command in safe:
            with self.subTest(command=command):
                self.assertEqual(self.reasons_for(command), [])

    def test_verify_requires_approval_for_inline_code_with_side_effects(self):
        risky = (
            'python3 -c "from pathlib import Path; Path(\'/tmp/p\').write_text(\'x\')"',
            'node -e "require(\'fs\').writeFileSync(\'x\',\'y\')"',
            'bash -c "echo hi > x"',
        )
        for command in risky:
            with self.subTest(command=command):
                self.assertTrue(self.reasons_for(command))

    def test_do_not_forget_to_deploy_requires_approval(self):
        self.assertTrue(bt_handoff._risky_text("Do not forget to deploy production"))

    def test_dont_skip_production_deploy_requires_approval(self):
        self.assertTrue(bt_handoff._risky_text("Don't skip the production deploy"))

    def test_never_deploy_to_production_is_not_risky(self):
        self.assertEqual(bt_handoff._risky_text("Never deploy to production"), [])


class ProfileRound2(IsolatedCase):
    def test_profiles_reject_foreign_account_selectors_and_handmade_profiles_ignore_them(self):
        with self.assertRaises(bt_profiles.ProfileError):
            bt_profiles.add("codex-cross", "codex", {"CLAUDE_CONFIG_DIR": "/tmp/claude"})
        with self.assertRaises(bt_profiles.ProfileError):
            bt_profiles.add("claude-cross", "claude", {"CODEX_HOME": "/tmp/codex"})

        profiles = self.state / "profiles.json"
        profiles.write_text(json.dumps({
            "codex-cross": {"provider": "codex", "env": {"CODEX_HOME": "/tmp/codex",
                                                               "CLAUDE_CONFIG_DIR": "/tmp/claude"}},
            "claude-cross": {"provider": "claude", "env": {"CLAUDE_CONFIG_DIR": "/tmp/claude",
                                                                  "CODEX_HOME": "/tmp/codex"}},
        }), encoding="utf-8")
        codex = bt_profiles.session_env("codex-cross", "codex", {}, "personal")
        claude = bt_profiles.session_env("claude-cross", "claude", {}, "personal")
        self.assertEqual(codex.get("CODEX_HOME"), "/tmp/codex")
        self.assertNotIn("CLAUDE_CONFIG_DIR", codex)
        self.assertEqual(claude.get("CLAUDE_CONFIG_DIR"), "/tmp/claude")
        self.assertNotIn("CODEX_HOME", claude)

    def test_ambient_work_account_requires_work_project_and_work_repo_cwd(self):
        work_project = "work"
        project_dir = self.root / work_project
        repo = project_dir / "repo"
        repo.mkdir(parents=True)
        bt_profiles.set_work(work_project, True)
        bt_profiles.add("claude-work", "claude", {"CLAUDE_CONFIG_DIR": str(self.base / "account")},
                        work_only=True)
        outside = self.base / "outside"
        outside.mkdir()
        with patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(self.base / "account")}):
            with self.assertRaises(bt_profiles.ProfileError):
                bt_profiles.authorize_ambient("claude", work_project, outside)
            bt_profiles.authorize_ambient("claude", work_project, repo)

    def test_delegate_create_applies_ambient_work_cwd_gate_for_pinned_agent(self):
        project = "work"
        repo = self.root / project / "repo"
        repo.mkdir(parents=True)
        bt_profiles.set_work(project, True)
        account = self.base / "work-account"
        account.mkdir()
        bt_profiles.add("claude-work", "claude", {"CLAUDE_CONFIG_DIR": str(account)}, work_only=True)
        outside = self.base / "personal"
        outside.mkdir()
        with patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(account)}):
            with self.assertRaises(SystemExit):
                bt_delegate.create(project, "Task", None, "claude", outside, [], None, 1, None, None)
            order = bt_delegate.create(project, "Task", None, "claude", repo, [], None, 1, None, None)
        self.assertIsNone(order["profile"])
        self.assertEqual(order["agent"], "claude")


class DelegateRound2(IsolatedCase):
    def test_claim_recovers_dead_pid_but_rejects_live_pid_and_existing_outcome(self):
        d = self.state / "delegations" / "claim-test"
        d.mkdir(parents=True)
        claim = d / "CLAIMED"
        claim.write_text("2147483647", encoding="utf-8")
        bt_delegate._claim(d, "claim-test")
        self.assertEqual(claim.read_text(encoding="utf-8"), str(os.getpid()))

        claim.write_text(str(os.getppid()), encoding="utf-8")
        with self.assertRaisesRegex(SystemExit, "already started"):
            bt_delegate._claim(d, "claim-test")
        claim.write_text("2147483647", encoding="utf-8")
        (d / "OUTCOME.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(SystemExit, "already started"):
            bt_delegate._claim(d, "claim-test")

    def test_next_route_rechecks_after_wait_and_stops_at_deadline(self):
        order = {"project": "sample", "profile": None, "agent": "claude", "kind": "implement",
                 "wait_quota": True, "auto": True}
        ready = {"profile": "codex-work", "agent": "codex", "model": "gpt", "effort": "high"}
        calls = []

        def candidates(*args, **kwargs):
            calls.append(1)
            return ([], 200.0) if len(calls) < 3 else ([ready], None)

        waits = []
        with patch.object(bt_agents, "pool_for", return_value=["claude-work", "codex-work"]), \
             patch.object(bt_agents, "candidates", side_effect=candidates), \
             patch.object(bt_delegate, "_wait_for", side_effect=lambda until: waits.append(until)), \
             patch.object(bt_delegate.time, "time", return_value=100.0):
            self.assertEqual(bt_delegate._next_route(order), ready)
        self.assertEqual(len(calls), 3)
        self.assertEqual(len(waits), 2)

        with patch.object(bt_agents, "pool_for", return_value=["claude-work"]), \
             patch.object(bt_agents, "candidates", return_value=([], 200.0)), \
             patch.object(bt_delegate, "_wait_for") as wait, \
             patch.object(bt_delegate.time, "time", side_effect=[0.0, bt_delegate.MAX_QUOTA_WAIT_SEC + 1]):
            self.assertIsNone(bt_delegate._next_route(order))
        wait.assert_not_called()

        no_wait = {**order, "wait_quota": False}
        with patch.object(bt_agents, "pool_for", return_value=["claude-work"]), \
             patch.object(bt_agents, "candidates", return_value=([], 200.0)), \
             patch.object(bt_delegate, "_wait_for") as wait:
            self.assertIsNone(bt_delegate._next_route(no_wait))
        wait.assert_not_called()

    def test_pinned_provider_waits_for_and_returns_same_ambient_account(self):
        order = {"project": "sample", "profile": None, "agent": "claude", "model": "haiku", "effort": None,
                 "kind": "implement", "wait_quota": True, "auto": False}
        cooling = [1234.0, None]
        waits = []
        with patch.object(bt_agents, "cooling_until", side_effect=lambda profile, agent: cooling.pop(0)) as cooldown, \
             patch.object(bt_delegate, "_wait_for", side_effect=lambda until: waits.append(until)):
            route = bt_delegate._next_route(order)
        self.assertEqual(route["profile"], None)
        self.assertEqual(route["agent"], "claude")
        self.assertEqual(route["model"], "haiku")
        self.assertEqual(waits, [1234.0])
        self.assertEqual(cooldown.call_args_list[0].args, (None, "claude"))


class RunStateRound2(IsolatedCase):
    def test_builders_uses_last_task_log_agent_before_run_agent(self):
        state = {"agent": "claude", "tasks": [{"id": "T1", "status": "done", "attempts": 0}],
                 "log": [{"task": "T1", "agent": "codex"}]}
        self.assertEqual(rs.builders_of(state, {"after": ["T1"]}), {"codex"})

    def test_sync_plan_raises_legacy_complexity_tier_without_lowering_escalated_tier(self):
        rdir = self.root / "sample" / "requirements" / "REQ-001-demo"
        rdir.mkdir(parents=True)
        (rdir / "PLAN.md").write_text("# Plan\n- [ ] T1 — large · complexity: L\n", encoding="utf-8")
        state = {"tasks": [{"id": "T1", "title": "large", "status": "todo", "attempts": 0, "tier": 0}],
                 "audit": False}
        rs.sync_plan(state, rdir)
        self.assertEqual(state["tasks"][0]["tier"], 1)
        state["tasks"][0]["tier"] = 2
        rs.sync_plan(state, rdir)
        self.assertEqual(state["tasks"][0]["tier"], 2)


class ResetRound2(IsolatedCase):
    def test_limit_reset_ignores_later_local_cache(self):
        cache_only = {"rc": 1, "text": "Usage limit reached\nChecking session\nStill working\n"
                                          "No provider reset listed\nThe local token cache resets in 2 days"}
        self.assertEqual(settle.detect_limit(cache_only), 0)

    def test_limit_reset_on_limit_line_is_honored(self):
        limit_line = {"rc": 1, "text": "Usage limit reached; resets in 2 hours"}
        self.assertGreater(settle.detect_limit(limit_line), 0)

    def test_reset_phrase_on_following_line_is_honored(self):
        next_line = {"rc": 1, "text": "Usage limit reached\nResets in 2 hours"}
        self.assertGreater(settle.detect_limit(next_line), 0)

    def test_absolute_reset_parses_spanish_december_abbreviation(self):
        import datetime as dt
        now = dt.datetime(2026, 12, 12, 0, 0).timestamp()
        parsed = settle.absolute_reset_epoch("try again at dic 13 2026 1:08 AM", now=now)
        self.assertEqual(parsed, int(dt.datetime(2026, 12, 13, 1, 8).timestamp()))


class PromptAndSecretRound2(IsolatedCase):
    def setUp(self):
        super().setUp()
        for module, attrs in ((rp, {"ROOT": self.root}), (rs, {"STATE": self.state}),
                              (bt_events, {"STATE": self.state}), (settle, {"ROOT": self.root})):
            for name, value in attrs.items():
                p = patch.object(module, name, value)
                p.start()
                self.addCleanup(p.stop)

    def test_single_milestone_and_audit_prompts_withhold_legacy_secret_text(self):
        rdir = self.root / "sample" / "requirements" / "REQ-001-demo"
        rdir.mkdir(parents=True)
        (rdir / "PLAN.md").write_text("---\nstatus: approved\n---\n# Plan\n\n### M1 — First\n"
                                      "- [ ] T1 — one\n- [ ] T2 — two\n", encoding="utf-8")
        state = rs.init_state("sample", rdir, "claude", "haiku", True, audit=True)
        secret = "token=abcdef123456"
        first = rs.get_task(state, "T1")
        first.update(evidence=secret, last_error=secret, notes=[secret])
        milestone = rs.get_task(state, "T1")
        audit = rs.get_task(state, "M1-audit")
        prompts = [
            rp.session_prompt("sample", rdir, state, milestone, 1, "branch"),
            rp.session_prompt("sample", rdir, state, milestone, 1, "branch", rs.unit_of(state, milestone)),
            rp.session_prompt("sample", rdir, state, audit, 2, "branch"),
        ]
        for prompt in prompts:
            with self.subTest(prompt=prompt[:40]):
                self.assertNotIn(secret, prompt)
                self.assertIn("[withheld", prompt)

    def test_event_detail_withholds_secret_looking_last_error(self):
        detail = bt_events.detail_for([{"id": "T1", "attempts": 1, "last_error": "token=abcdef123456"}], "failed")
        self.assertIn("[withheld", detail["why"])
        self.assertNotIn("abcdef123456", detail["why"])

    def test_safe_text_fails_closed_when_secret_detector_raises(self):
        with patch.object(bt_learn, "_secret", side_effect=RuntimeError("detector unavailable")):
            filtered = rt._safe_text("ordinary non-empty evidence")
        self.assertTrue(filtered.startswith("[withheld"))
        self.assertNotIn("ordinary non-empty evidence", filtered)

    def test_stopped_session_is_logged_as_stopped(self):
        rdir = self.root / "sample" / "requirements" / "REQ-001-demo"
        rdir.mkdir(parents=True)
        (rdir / "PLAN.md").write_text("# Plan\n- [ ] T1 — one\n", encoding="utf-8")
        state = rs.init_state("sample", rdir, "claude", "haiku", True, audit=False)
        rs.save(rdir, state)
        info = {"rc": -15, "text": "", "seconds": 1, "stopped": True, "timed_out": False,
                "agent": "claude", "profile": None, "model": "haiku", "effort": None, "kind": "implement"}
        settle.settle_task("sample", rdir, "T1", 1, info, self.base)
        self.assertEqual(rs.load(rdir)["log"][-1]["result"], "stopped")


if __name__ == "__main__":
    unittest.main()
