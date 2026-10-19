import unittest

import bt_page_now as pn


def item(**kw):
    a = {"id": "A-1", "number": 2, "state": "running", "live": True, "provider": "claude", "model_requested": "sonnet",
         "effort": "high", "account": "claude-work", "started_at": "2026-10-18T10:00:00+00:00", "duration_s": 184,
         "last_activity_at": "2026-10-18T10:03:02+00:00", "tokens": {"input": 1, "output": 2, "total": 46351}}
    a.update(kw.pop("attempt", {}))
    base = {"project": "metodologia", "req_id": "REQ-026", "req_title": "Demo", "task": "T4", "task_title": "Bus <x>",
            "state": "running", "attempt": a, "route": None, "progress": {"done": 4, "total": 9}}
    base.update(kw)
    return base


class NowHtml(unittest.TestCase):
    def test_bar_is_empty_when_nothing_runs_and_links_each_task(self):
        self.assertEqual(pn.bar_html([]), "")
        html = pn.bar_html([item()])
        self.assertIn("Ahora <sl-badge", html)
        self.assertIn(">1</sl-badge>", html)
        self.assertIn('href="/plans/metodologia/REQ-026#t-T4"', html)
        self.assertIn("data-since=", html)

    def test_bar_caps_chips_and_counts_the_rest(self):
        html = pn.bar_html([item(task=f"T{n}") for n in range(9)])
        self.assertEqual(html.count('class="nchip"'), 6)
        self.assertIn("+3", html)

    def test_card_shows_model_link_tokens_progress_and_escapes_titles(self):
        html = pn.card_html(item())
        self.assertIn('href="/metrics/model/claude/sonnet/high"', html)
        self.assertIn("46.4k", html)
        self.assertIn("plan 4/9", html)
        self.assertIn("Bus &lt;x&gt;", html)
        self.assertNotIn("quiet", html)

    def test_silent_attempt_is_grey_and_not_declared_dead(self):
        html = pn.card_html(item(attempt={"last_activity_at": None, "tokens": None}))
        self.assertIn("ncard quiet", html)
        self.assertIn("sin actividad registrada", html)
        self.assertNotIn("caíd", html)
        self.assertIn("no informado", html)

    def test_verifying_label_and_empty_state(self):
        self.assertIn("verificando", pn.card_html(item(state="verifying")))
        self.assertIn("Nada se está ejecutando", pn.cards_html([]))

    def test_page_and_layout_carry_the_bar_and_script(self):
        page = pn.now_page([item()])
        self.assertIn('id="nowbar"', page)
        self.assertIn("/static/live.js", page)
        self.assertIn('id="now-cards"', page)


if __name__ == "__main__":
    unittest.main()
