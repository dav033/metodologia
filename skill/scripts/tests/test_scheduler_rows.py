import unittest

import bt_events
import bt_scheduler_rows as sr


def attempt(state, tokens=None):
    return {"attempt": "A-1", "task": "T1", "number": 1, "state": state, "duration_s": 12.5,
            "started_at": "2026-10-18T10:00:00+00:00", "ended_at": "2026-10-18T10:00:12+00:00",
            "route": {"provider": "claude", "model": "sonnet", "effort": "high", "profile": "claude-work"},
            "model_reported": "claude-sonnet-5-5", "tokens": tokens, "failure": ""}


class Rows(unittest.TestCase):
    task = {"complexity": "high", "kind": "implement", "title": "Do it", "milestone_id": "M1"}

    def test_finished_attempts_become_valid_schema2_rows(self):
        for state, result in (("accepted", "done"), ("rejected", "verify_failed"), ("failed", "failed")):
            row = sr.row_of("p", "REQ-001", self.task, attempt(state))
            self.assertTrue(bt_events._valid_row(row), state)
            self.assertEqual((row["result"], row["agent"], row["model"], row["complexity"]), (result, "claude", "sonnet", "L"))

    def test_live_attempt_is_not_an_outcome(self):
        self.assertIsNone(sr.row_of("p", "REQ-001", self.task, attempt("running")))

    def test_unreported_tokens_stay_none_and_summary_counts_the_attempt(self):
        rows = [sr.row_of("p", "REQ-001", self.task, attempt("accepted")),
                sr.row_of("p", "REQ-001", self.task, attempt("accepted", {"input": 5, "output": 6, "total": 11}))]
        self.assertIsNone(rows[0]["usage"]["total_tokens"])
        group = bt_events.summary(rows, ("agent", "model", "effort"))[0]
        self.assertEqual((group["attempts"], group["done"]), (2, 2))


if __name__ == "__main__":
    unittest.main()
