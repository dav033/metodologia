import unittest

import bt_page_attempts as pa
import bt_page_plans as pp


def attempt(n, state, live=False, **kw):
    base = {"id": f"A-{n}", "number": n, "state": state, "provider": "claude", "model_requested": "sonnet",
            "model_reported": None, "effort": "high", "account": "claude-work", "started_at": "2026-10-18T10:00:00+00:00",
            "duration_s": 75, "tokens": None, "cost_usd": None, "failure": None, "live": live}
    base.update(kw)
    return base


class AttemptHtml(unittest.TestCase):
    def test_model_chip_links_to_model_and_effort_stats(self):
        self.assertIn('href="/metrics/model/claude/sonnet/high"', pa.model_chip("claude", "sonnet", "high"))
        self.assertIn('href="/metrics/model/codex/gpt-6-luna"', pa.model_chip("codex", "gpt-6-luna", None))
        self.assertNotIn("<a", pa.model_chip(None, "sonnet"))
        self.assertNotIn("<a", pa.model_chip("claude", None))

    def test_unreported_values_are_dashes_never_zero(self):
        self.assertIn("no informado", pa.tokens_html(None))
        self.assertEqual(pa.fmt_duration(None), "—")
        self.assertEqual(pa.fmt_count(None), "—")
        self.assertEqual(pa.fmt_count(46351), "46.4k")
        self.assertEqual(pa.fmt_duration(75), "1 min 15 s")
        self.assertIn("↓7", pa.tokens_html({"input": None, "output": 7, "total": None}))

    def test_table_has_a_row_per_attempt_and_opens_when_live(self):
        html = pa.attempts_table([attempt(1, "rejected", failure="verify_failed"), attempt(2, "running", True)])
        self.assertEqual(html.count('<tr id="a-'), 2)                           # each row is a link target
        self.assertIn(" open", html.split(">")[0] + ">")
        self.assertIn("verify_failed", html)

    def test_task_shows_working_indicator_only_for_a_live_attempt(self):
        live = attempt(2, "running", True, tokens={"input": 1, "output": 2, "total": 3})
        task = {"id": "T1", "title": "x", "complexity": "high", "attempts": 2, "after": [], "state": "running",
                "attempt": live, "history": [attempt(1, "rejected"), live],
                "route": {"status": "assigned", "provider": "claude", "model_requested": "sonnet", "effort": "high",
                          "account": "claude-work", "reason": None, "selection_reason": "best fit"}}
        html = pp._task(task)
        self.assertIn("trabajando", html)
        self.assertIn('id="t-T1"', html)
        self.assertIn("best fit", html)
        task["attempt"] = task["history"][0]
        self.assertNotIn("trabajando", pp._task(task))


if __name__ == "__main__":
    unittest.main()


class Evolution(unittest.TestCase):
    def test_amended_task_shows_old_to_new_and_the_plan_timeline_lists_both_kinds(self):
        rec = {"seq": 1, "task": "T4", "field": "complexity", "from": "medium", "to": "high", "reason": "bigger",
               "evidence": ["file:a.py"], "by": "claude", "proposed_by": "agent", "at": "2026-10-18T22:42:00+00:00",
               "plan_ref": {"revision": 1}}
        task = {"id": "T4", "title": "x", "complexity": "high", "attempts": 0, "after": [], "state": "pending",
                "attempt": None, "history": [], "route": None, "amendments": [rec]}
        html = pp._task(task)
        self.assertIn("<s>media</s> → <b>alta</b>", html)
        self.assertIn("22:42", html)
        self.assertIn("por el agente", html)
        self.assertIn('content="file:a.py"', html)
        status = {"evolution": {"amendments": 1, "timeline": [
            {"at": "2026-10-18T22:00:00", "kind": "revision", "revision": 1, "source": "approval"},
            {"at": rec["at"], "kind": "amendment", "task": "T4", "field": "complexity", "from": "medium", "to": "high",
             "by": "claude", "proposed_by": "agent"}]}}
        timeline = pp._timeline(status)
        self.assertIn("revisión 1", timeline)
        self.assertIn("T4: complejidad <s>media</s> → alta", timeline)
        self.assertEqual(pp._timeline({"evolution": {"amendments": 0, "timeline": []}}), "")
        self.assertEqual(pp._amended({"amendments": []}), "")
