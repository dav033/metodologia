"""Audit budget policy across automatic routes, pinned providers and quota fallback."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bt_agents
import bt_delegate
import bt_runprompt
import bt_runsession
import bt_runstate
from test_agents import AgentTests


class AuditRoutingTests(AgentTests):
    def test_audit_model_does_not_inherit_builder_model_or_effort(self):
        for tier in (0, 1):
            with self.subTest(tier=tier):
                self.assertEqual(bt_agents.model_for("claude", tier, "opus", "audit"),
                                 ("sonnet", "medium"))
                self.assertEqual(bt_agents.model_for("codex", tier, "gpt-6-luna", "audit"),
                                 ("gpt-6.1-sol", "medium"))

    def test_escalated_audit_uses_high_not_xhigh(self):
        self.assertEqual(bt_agents.model_for("claude", 2, kind="audit"), ("opus", "high"))
        self.assertEqual(bt_agents.model_for("codex", 2, kind="audit"), ("gpt-6.1-sol", "high"))

    def test_automatic_audit_prefers_claude_over_pool_order(self):
        routes, _ = bt_agents.candidates("personal-project", ["codex-named", "claude"], 1,
                                         "audit", "opus")
        self.assertEqual((routes[0]["agent"], routes[0]["model"], routes[0]["effort"]),
                         ("claude", "sonnet", "medium"))

    def test_audit_keeps_provider_diversity_from_the_builder_before_claude_preference(self):
        # D-004: the audit still prefers a provider other than the builder's; Claude-first is the fallback order.
        routes, _ = bt_agents.candidates("personal-project", ["codex-named", "claude"], 1,
                                         "audit", "opus", avoid_providers={"claude"})
        self.assertEqual((routes[0]["agent"], routes[0]["model"], routes[0]["effort"]),
                         ("codex", "gpt-6.1-sol", "medium"))

    def test_codex_fallback_when_claude_cools_down(self):
        with patch.object(bt_agents.time, "time", return_value=1_800_000_000.0):
            bt_agents.quota_mark("claude", "claude", 1_800_000_100.0)
            route = bt_agents.route("personal-project", {"pool": ["claude", "codex-named"]}, 1, "audit")
        self.assertEqual((route["agent"], route["model"], route["effort"]),
                         ("codex", "gpt-6.1-sol", "medium"))

    def test_work_only_claude_is_not_used_for_personal_audit(self):
        route = bt_agents.route("personal-project", {"pool": ["claude-work", "codex-named"]}, 1, "audit")
        self.assertEqual(route["profile"], "codex-named")

    def test_fixed_provider_audits_follow_budget_policy(self):
        for provider, model in (("claude", "sonnet"), ("codex", "gpt-6.1-sol")):
            with self.subTest(provider=provider):
                route = bt_agents.route("personal-project", {"agent": provider, "model": "opus"}, 1, "audit")
                self.assertEqual((route["model"], route["effort"]), (model, "medium"))

    def test_final_review_uses_audit_budget_policy(self):
        route = bt_runsession.session_route("personal-project", {"agent": "claude", "model": "opus"}, None)
        self.assertEqual((route["model"], route["effort"]), ("sonnet", "medium"))

    def test_pinned_delegation_uses_audit_defaults_and_preserves_explicit_override(self):
        with patch.object(bt_delegate, "DIR", self.state / "delegations"), patch.object(
                bt_delegate.bt_profiles, "authorize_ambient"):
            default = bt_delegate.create("personal-project", "Audit change", None, "claude", self.base,
                                         [], None, 1, None, None, kind="audit")
            explicit = bt_delegate.create("personal-project", "Audit change", None, "claude", self.base,
                                          [], None, 1, "opus", "high", kind="audit")
            model_only = bt_delegate.create("personal-project", "Audit change", None, "claude", self.base,
                                            [], None, 1, "sonnet", None, kind="audit")
            escalated = bt_delegate.create("personal-project", "Audit change", None, "codex", self.base,
                                           [], None, 1, "gpt-6.1-sol", None, kind="audit", tier=2)
        self.assertEqual((default["model"], default["effort"]), ("sonnet", "medium"))
        self.assertEqual((explicit["model"], explicit["effort"]), ("opus", "high"))
        self.assertEqual((model_only["model"], model_only["effort"]), ("sonnet", "medium"))
        self.assertEqual((escalated["model"], escalated["effort"]), ("gpt-6.1-sol", "high"))

    def test_closing_consolidates_existing_audits_but_keeps_review_without_coverage(self):
        state = {"req": "REQ-001", "audit": True,
                 "tasks": [{"synthetic": True, "kind": "audit", "status": "done"}]}
        covered = bt_runprompt.session_prompt("personal-project", self.base, state, None, 1, "feature")
        self.assertIn("consolidate AUDIT-M*.md", covered)
        self.assertIn("missing/stale", covered)
        state["audit"] = False
        resumed = bt_runprompt.session_prompt("personal-project", self.base, state, None, 1, "feature")
        self.assertIn("consolidate AUDIT-M*.md", resumed)
        state["tasks"] = []
        uncovered = bt_runprompt.session_prompt("personal-project", self.base, state, None, 1, "feature")
        self.assertIn("fresh-eyes review", uncovered)

    def test_busy_claude_account_does_not_block_idle_codex(self):
        routes, _ = bt_agents.candidates("personal-project", ["claude", "codex-named"], 1, "audit",
                                         busy={bt_agents.account_key("claude", "claude")})
        self.assertEqual(routes[0]["agent"], "codex")

    def test_implementation_ladder_is_unchanged(self):
        self.assertEqual(bt_agents.model_for("claude", 1), ("sonnet", "medium"))
        self.assertEqual(bt_agents.model_for("codex", 2), ("gpt-6.1-sol", "high"))

    def test_high_risk_milestone_audit_starts_at_escalated_budget(self):
        for signal in ({"risk": "high"}, {"level": "architecture"}):
            with self.subTest(signal=signal):
                member = {"id": "T1", "status": "todo", "milestone": "M1", **signal}
                audit = bt_runstate._audit_task("M1", [member], False)
                self.assertEqual(audit["tier"], 2)
                route = bt_agents.route("personal-project", {"agent": "claude"}, audit["tier"], "audit")
                self.assertEqual((route["model"], route["effort"]), ("opus", "high"))

    def test_resume_promotes_high_risk_audit_without_losing_prior_escalation(self):
        member = {"id": "T1", "status": "todo", "milestone": "M1"}
        audit = bt_runstate._audit_task("M1", [member], False)
        state = {"tasks": [member, audit], "audit": True}
        member["risk"] = "high"
        bt_runstate._sync_audits(state)
        self.assertEqual(audit["tier"], 2)
        member["risk"] = None
        bt_runstate._sync_audits(state)
        self.assertEqual(audit["tier"], 2)


if __name__ == "__main__":
    unittest.main()
