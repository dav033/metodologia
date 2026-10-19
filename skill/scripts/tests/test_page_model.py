import unittest

import bt_page_model as pm
import bt_scheduler_rows as sr


def row(result="done", seconds=60, effort="high", model="sonnet", agent="claude", task="T1", tokens=None):
    r = sr.row_of("p", "REQ-001", {"complexity": "high", "kind": "implement", "title": "x"},
                  {"attempt": f"A-{task}-{seconds}", "task": task, "number": 1,
                   "state": {"done": "accepted", "verify_failed": "rejected", "failed": "failed"}[result],
                   "duration_s": seconds, "started_at": "2026-10-18T10:00:00+00:00",
                   "ended_at": "2026-10-18T10:01:00+00:00", "model_reported": None, "failure": "",
                   "tokens": tokens, "route": {"provider": agent, "model": model, "effort": effort,
                                               "profile": "claude-work"}})
    return r


class ModelPage(unittest.TestCase):
    rows = [row("done", 30, task="T1", tokens={"input": 1, "output": 2, "total": 100}),
            row("done", 90, task="T2", tokens={"input": 1, "output": 2, "total": 300}),
            row("verify_failed", 120, task="T3"), row("done", 60, effort="low", task="T4"),
            row("done", 10, model="opus", agent="claude", task="T5")]

    def test_selection_by_model_and_optionally_effort(self):
        self.assertEqual(len(pm.select(self.rows, "claude", "sonnet", None)), 4)
        self.assertEqual(len(pm.select(self.rows, "claude", "sonnet", "high")), 3)
        self.assertEqual(pm.select(self.rows, "codex", "sonnet", None), [])

    def test_facts_percentiles_and_no_invented_numbers(self):
        f = pm.facts(pm.select(self.rows, "claude", "sonnet", "high"))
        self.assertEqual((f["attempts"], f["done"], f["p50"], f["p90"]), (3, 2, 90, 120))
        self.assertIsNone(pm.facts([row("done", 5)])["tokens_per_done"])      # no tokens reported
        self.assertEqual(pm.percentile([], 0.5), None)

    def test_page_lists_attempts_with_links_efforts_and_breakdown(self):
        html = pm.model_page("claude", "sonnet", "high", self.rows)
        self.assertIn("sonnet · high", html)
        self.assertIn('href="/plans/p/REQ-001#t-T3"', html)
        self.assertIn("/metrics/model/claude/sonnet/low", html)          # other efforts are one click away
        self.assertIn("implement", html)
        self.assertIn("nunca en 0", html)

    def test_unknown_model_is_an_empty_state_not_an_error(self):
        self.assertIn("Aún no hay intentos", pm.model_page("claude", "ghost", None, self.rows))


if __name__ == "__main__":
    unittest.main()
