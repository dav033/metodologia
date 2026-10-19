"""Attempt telemetry: usage extraction per provider, unknown stays null, idempotent append, coverage summary."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import bt_events  # noqa: E402  (imports bt_core: test_00_isolation establishes the disposable root)

CLAUDE_RESULT = {"type": "result", "subtype": "success", "is_error": False, "total_cost_usd": 0.0037, "result": "ok",
                 "usage": {"input_tokens": 2, "cache_creation_input_tokens": 18058, "cache_read_input_tokens": 8607,
                           "output_tokens": 7, "output_tokens_details": {"thinking_tokens": 0}}}
CODEX_TEXT = "model: gpt-5.6-luna\n--------\nuser\nresponde solo: ok\ncodex\nok\ntokens used\n5,604\nok\n"


class UsageExtractionTests(unittest.TestCase):
    def test_claude_result_event(self):
        raw = json.dumps({"type": "assistant"}) + "\n" + json.dumps(CLAUDE_RESULT)
        u = bt_events.extract_usage("claude", raw)
        self.assertEqual((u["input_tokens"], u["output_tokens"], u["cache_read_tokens"], u["cache_write_tokens"],
                          u["reasoning_tokens"]), (2, 7, 8607, 18058, 0))
        self.assertEqual(u["quality"], "reported")
        self.assertIsNone(u["total_tokens"])  # Claude does not report a total: not invented
        self.assertAlmostEqual(u["cost_usd_reported"], 0.0037)

    def test_codex_only_reports_a_grand_total(self):
        u = bt_events.extract_usage("codex", CODEX_TEXT)
        self.assertEqual(u["total_tokens"], 5604)
        self.assertEqual(u["quality"], "total_only")
        self.assertIsNone(u["input_tokens"])

    def test_missing_usage_is_null_never_zero(self):
        for agent in ("claude", "codex", None):
            u = bt_events.extract_usage(agent, "plain text without any usage")
            self.assertEqual(u["quality"], "unknown")
            self.assertTrue(all(u[k] is None for k in ("input_tokens", "output_tokens", "total_tokens")))
        broken = bt_events.extract_usage("claude", '{"type": "result", "usage": {"input_tokens": "many"}}')
        self.assertIsNone(broken["input_tokens"])


class RecordingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="telemetry-test-")
        self.addCleanup(self.tmp.cleanup)
        for target, value in (("bt_events.STATE", Path(self.tmp.name) / ".state"),
                              ("bt_events.bt_profiles.is_work_project", lambda project: project == "pictures")):
            patcher = patch(target, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def _record(self, session=1, result="done", agent="claude", text=None):
        state = {"agent": agent, "req": "REQ-001", "profile": "claude-work"}
        info = {"rc": 0, "text": text if text is not None else json.dumps(CLAUDE_RESULT), "seconds": 12,
                "model": "haiku", "effort": None, "timed_out": False, "stopped": False}
        return bt_events.record_attempt("pictures", state, "T1", session, info, result)

    def test_appends_one_line_and_is_idempotent_per_session(self):
        path = self._record()
        self.assertIsNotNone(path)
        self.assertIsNone(self._record())  # same (project, run, session): not written twice
        self._record(session=2, result="verify_failed")
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertEqual([r["session"] for r in rows], [1, 2])
        self.assertTrue(rows[0]["work"])
        self.assertEqual(rows[0]["profile"], "claude-work")
        self.assertEqual(rows[0]["usage"]["output_tokens"], 7)

    def test_a_telemetry_failure_never_raises(self):
        with patch("bt_events.extract_usage", side_effect=RuntimeError("boom")):
            self.assertIsNone(self._record(session=9))

    def test_summary_reports_coverage_and_does_not_count_unknown_as_zero(self):
        self._record(session=1)
        self._record(session=2, result="failed", text="no usage here")
        self._record(session=3, agent="codex", text=CODEX_TEXT)
        self._record(session=4, result="verified")  # a delegation verified by its independent check counts as done
        rows = bt_events.read_all()
        by_agent = {g["agent"]: g for g in bt_events.summary(rows)}
        claude = by_agent["claude"]
        self.assertEqual((claude["attempts"], claude["done"], claude["failed"]), (3, 2, 1))
        self.assertAlmostEqual(claude["coverage"], 0.67)
        self.assertEqual(claude["tokens_measured"], 2 * (2 + 7 + 8607 + 18058))
        self.assertEqual(by_agent["codex"]["tokens_measured"], 5604)


class MetricsPageTests(unittest.TestCase):
    def render(self, rows):
        import bt_page_metrics
        with patch("bt_page_metrics.bt_events.read_all", return_value=rows):
            return bt_page_metrics.metrics_page()

    def test_unknown_usage_renders_as_a_dash_and_coverage_is_shown(self):
        rows = [{"ts": "2026-10-12T20:00:00", "project": "p", "task": "T1", "agent": "claude", "profile": "claude-work",
                 "model": "haiku", "seconds": 10, "result": "done", "usage": {"total_tokens": None}},
                {"ts": "2026-10-12T20:05:00", "project": "p", "task": "T2", "agent": "codex", "profile": None,
                 "model": None, "seconds": 5, "result": "failed", "usage": {"total_tokens": 5604}}]
        html = self.render(rows)
        self.assertIn("Cobertura", html)
        self.assertIn("<td>0%</td>", html)      # claude: no usage reported
        self.assertIn("<td>100%</td>", html)    # codex: total reported
        self.assertIn("5.604", html)
        self.assertRegex(html, r"<td>—</td>(<td>—</td>)*<td>0%</td>")  # claude: tokens are a dash, never 0

    def test_values_from_the_log_are_escaped(self):
        rows = [{"ts": "t", "project": "<script>alert(1)</script>", "task": "T1", "agent": "claude",
                 "profile": "x", "model": "m", "seconds": 1, "result": "done", "usage": {}}]
        self.assertNotIn("<script>alert(1)</script>", self.render(rows))

    def test_empty_state_is_explained(self):
        self.assertIn("Aún no hay intentos", self.render([]))


if __name__ == "__main__":
    unittest.main()
