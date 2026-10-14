"""Task routing ignores kind keywords embedded in other words and identifiers."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bt_agents


class KindWordBoundaryTests(unittest.TestCase):
    def test_implementation_preview_is_not_review(self) -> None:
        self.assertEqual(bt_agents.infer_kind("Add role impact preview"), "implement")

    def test_implementation_identifier_is_not_an_audit(self) -> None:
        self.assertEqual(
            bt_agents.infer_kind("Implement list_role_audit MCP tool"), "implement"
        )

    def test_maros_t6_capability_implementation_keeps_implementation_kind(self) -> None:
        title = (
            "MCP tools for the new capabilities (duplicate_role, role_impact, "
            "get_user_access, bulk_assign_role, list_role_audit, list_access_requests, "
            "resolve_access_request, list_role_templates, apply_role_template) "
            "built on the shared services"
        )
        self.assertEqual(bt_agents.infer_kind(title), "implement")

    def test_nested_identifiers_do_not_supply_kind_keywords(self) -> None:
        for title in (
            "Implement tools.list_role_audit",
            "Implement role_reviews and role_docs",
            "Implement access_tests and user_research",
            "Implement latest_status and prerevision",
        ):
            with self.subTest(title=title):
                self.assertEqual(bt_agents.infer_kind(title), "implement")

    def test_keyword_starts_and_prefixes_still_classify_titles(self) -> None:
        for title, expected in (
            ("Audit role capabilities", "audit"),
            ("Review implementation", "audit"),
            ("Independent reviews", "audit"),
            ("Revisión de permisos", "audit"),
            ("Revisar permisos", "audit"),
            ("Update README and docs", "docs"),
            ("Documentation updates", "docs"),
            ("Update skill.md", "docs"),
            ("Update skillXmd integration", "implement"),
            ("Run tests", "test"),
            ("Pruebas de permisos", "test"),
            ("Research alternatives", "research"),
            ("Compare providers", "research"),
            ("(audit) permissions", "audit"),
            ("Update docs/README.md", "docs"),
        ):
            with self.subTest(title=title):
                self.assertEqual(bt_agents.infer_kind(title), expected)

    def test_explicit_kind_takes_precedence_over_all_title_keywords(self) -> None:
        for kind in ("implement", "test", "docs", "audit", "research"):
            with self.subTest(kind=kind):
                self.assertEqual(
                    bt_agents.infer_kind("Audit docs test research", f"  {kind.upper()} "),
                    kind,
                )

    def test_invalid_explicit_kind_falls_back_to_boundary_matching(self) -> None:
        self.assertEqual(bt_agents.infer_kind("Add impact preview", "unknown"), "implement")
        self.assertEqual(bt_agents.infer_kind("Run tests", "unknown"), "test")

    def test_empty_titles_and_existing_kind_priority_are_preserved(self) -> None:
        self.assertEqual(bt_agents.infer_kind(None), "implement")
        self.assertEqual(bt_agents.infer_kind(""), "implement")
        self.assertEqual(bt_agents.infer_kind("Research docs, test and review"), "audit")
