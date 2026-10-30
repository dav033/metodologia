"""Allowed role choices and explicit-complexity transitions."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bt_role_policy as policy


class RolePolicyTests(unittest.TestCase):
    def test_ordinary_choices_match_owner_selection(self):
        expected = {
            "planner": [("codex", "gpt-6.1-sol", "high"), ("claude", "opus", "high")],
            "reviewer": [("codex", "gpt-6.1-sol", "medium"), ("claude", "sonnet", "medium")],
            "designer": [("claude", "opus", "high"), ("codex", "gpt-6.1-terra", "high")],
            "explorer": [("codex", "gpt-6-luna", "high"), ("claude", "sonnet", "medium")],
            "implementer": [("claude", "sonnet", "medium"), ("codex", "gpt-6-luna", "high")],
            "researcher": [("codex", "gpt-6-luna", "high"), ("claude", "sonnet", "low")],
            "runner": [("codex", "gpt-6-luna", "high"), ("claude", "sonnet", "low")],
            "antagonist": [("claude", "sonnet", "medium"), ("claude", "opus", "high")],
            "solver": [("claude", "opus", "high"), ("codex", "gpt-6.1-sol", "high")],
        }
        self.assertEqual(set(policy.ROLES), set(expected))
        for role, choices in expected.items():
            with self.subTest(role=role):
                self.assertEqual(policy.options(role), choices)

    def test_explicit_high_complexity_changes_only_approved_choices(self):
        for label in ("L", "high", "high_complexity", " HIGH "):
            with self.subTest(label=label):
                self.assertEqual(policy.options("reviewer", label), [
                    ("codex", "gpt-6.1-sol", "high"), ("claude", "sonnet", "high")])
                self.assertEqual(policy.options("explorer", label), [
                    ("codex", "gpt-6.1-sol", "medium"), ("claude", "sonnet", "medium")])
                for role in ("planner", "researcher", "runner", "antagonist"):
                    self.assertEqual(policy.options(role, label), list(reversed(policy.options(role))))

    def test_implementer_complexity_does_not_promote_the_availability_alternative(self):
        for label in ("L", "high", "high_complexity", " HIGH "):
            with self.subTest(label=label):
                self.assertEqual(policy.options("implementer", label), policy.options("implementer"))

    def test_unrecognized_labels_do_not_escalate(self):
        for label in (None, "", "M", "low", "risky", "error", "timeout", "large", True):
            for role in policy.ROLES:
                self.assertEqual(policy.options(role, label), policy.options(role))

    def test_no_unselected_provider_or_model(self):
        # gpt-6.1-terra: the Designer's fallback, selected by the owner on 2026-10-29 (D-151)
        allowed = {"codex": {"gpt-6-astra", "gpt-6.1-sol", "gpt-6-luna", "gpt-6.1-terra"}, "claude": {"sonnet", "opus"}}
        for role in policy.ROLES:
            for complexity in (None, "high"):
                for provider, model, effort in policy.options(role, complexity):
                    self.assertIn(model, allowed[provider])
                    self.assertIn(effort, {"low", "medium", "high", "xhigh"})
        self.assertIsNone(policy.native_option("antagonist", "codex"))
        self.assertIsNone(policy.native_option("runner", "antigravity"))

    def test_kind_mapping_and_unknown_roles(self):
        self.assertEqual([policy.role_for_kind(k) for k in ("implement", "test", "audit", "research")],
                         ["implementer", "runner", "reviewer", "researcher"])
        self.assertEqual(policy.role_for_kind("design"), "designer")
        self.assertEqual(policy.role_for_task("audit", "visual"), "reviewer")
        self.assertEqual(policy.role_for_task("audit", None), "reviewer")
        self.assertIsNone(policy.role_for_task("unknown", "visual"))
        for unknown in ("docs", "unknown", None):
            self.assertIsNone(policy.role_for_kind(unknown))
            self.assertEqual(policy.options(unknown), [])
            self.assertEqual(policy.options(unknown, "high"), [])
            self.assertIsNone(policy.native_option(unknown, "codex"))

    def test_native_option_is_ordinary_and_returned_options_are_independent(self):
        self.assertEqual(policy.native_option("explorer", "codex"), ("gpt-6-luna", "high"))
        self.assertEqual(policy.native_option("antagonist", "claude"), ("sonnet", "medium"))
        policy.options("runner").clear()
        self.assertEqual(len(policy.options("runner")), 2)


class EscalatedAudit(unittest.TestCase):
    """The one exception to «risk does not change the options»: an audit the run escalated (tier 2) reads at high."""

    def test_only_an_escalated_audit_changes_the_reviewer_options(self):
        import bt_role_policy as policy
        normal = policy.options("reviewer")
        self.assertEqual(normal[0], ("codex", "gpt-6.1-sol", "medium"))
        escalated = policy.options("reviewer", escalated=True)
        self.assertEqual(escalated, [("codex", "gpt-6.1-sol", "high"), ("claude", "opus", "high")])
        for role in ("planner", "implementer", "runner"):
            self.assertEqual(policy.options(role, escalated=True), policy.options(role))

    def test_escalation_needs_an_audit_at_tier_two(self):
        import bt_role_policy as policy
        self.assertTrue(policy.escalated_audit("audit", 2))
        self.assertFalse(policy.escalated_audit("audit", 1))
        self.assertFalse(policy.escalated_audit("implement", 2))
        self.assertFalse(policy.escalated_audit("audit", None))
        self.assertFalse(policy.escalated_audit("audit", True))


if __name__ == "__main__":
    unittest.main()
