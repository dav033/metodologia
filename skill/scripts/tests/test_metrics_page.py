from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bt_page_metrics


CATALOG = {
    "accounts": [{"profile": "claude-work", "provider": "claude", "work_only": True,
                  "installed": True, "cooling_until": "2026-10-12 22:30"}],
    "ladder": {"claude": [{"tier": 0, "model": "haiku", "effort": None},
                           {"tier": 1, "model": "sonnet", "effort": "xhigh"},
                           {"tier": 2, "model": "opus", "effort": "xhigh"}]},
}


class MetricsPageTests(unittest.TestCase):
    def render(self, rows):
        with patch("bt_page_metrics.bt_events.read_all", return_value=rows), \
                patch("bt_page_metrics.bt_agents.catalog", return_value=CATALOG):
            return bt_page_metrics.metrics_page()

    def test_empty_rows_keep_accounts_table_and_message(self):
        html = self.render([])
        self.assertIn("Aún no hay intentos", html)
        self.assertIn("En espera hasta", html)
        self.assertIn("claude-work", html)

    def test_rows_render_effort_kind_advice_and_cooling_account(self):
        rows = [{"ts": "2026-10-12T21:00:00", "project": "demo", "task": "Task", "agent": "claude",
                 "profile": "claude-work", "model": "sonnet", "effort": "xhigh", "kind": "audit",
                 "seconds": 8, "result": "done", "usage": {"total_tokens": 100,
                 "cost_usd_reported": 0.002}} for _ in range(5)]
        html = self.render(rows)
        self.assertIn("xhigh", html)
        self.assertIn("audit", html)
        self.assertIn("best measured is claude/sonnet", html)
        self.assertIn("2026-10-12 22:30", html)
        self.assertIn("sonnet · xhigh", html)
        self.assertIn("<td>100%</td><td>8</td>", html)

    def test_hostile_task_and_model_are_escaped(self):
        rows = [{"ts": "now", "project": "demo", "task": "<script>bad</script>", "agent": "claude",
                 "profile": "p", "model": "<script>evil</script>", "effort": "low", "kind": "docs",
                 "seconds": 1, "result": "done", "usage": {}}]
        html = self.render(rows)
        self.assertNotIn("<script>bad</script>", html)
        self.assertNotIn("<script>evil</script>", html)
        self.assertIn("&lt;script&gt;evil&lt;/script&gt;", html)

    def test_none_measurements_render_as_dashes(self):
        rows = [{"ts": "now", "project": "demo", "task": "Task", "agent": "codex", "profile": None,
                 "model": None, "effort": None, "kind": "test", "seconds": None, "result": "usage_limit",
                 "usage": {}}]
        html = self.render(rows)
        self.assertIn("<td>—</td>", html)
        self.assertIn("Tokens medidos", html)
        self.assertIn("Coste USD informado", html)
        self.assertIn("Modelo·esfuerzo", html)


if __name__ == "__main__":
    unittest.main()
