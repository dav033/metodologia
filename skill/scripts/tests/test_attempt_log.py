"""The Scheduler's attempts reach the attempt log with a verdict the router can learn from."""
import unittest

import bt_attempt_log as log
import bt_events

PLAN = {
    "T1": {"id": "T1", "kind": "implement", "complexity": "low", "title": "one", "milestone_id": "M1", "after": []},
    "T2": {"id": "T2", "kind": "implement", "complexity": "high", "title": "two", "milestone_id": "M1", "after": ["T1"]},
    "T3": {"id": "T3", "kind": "audit", "complexity": "medium", "title": "audit", "milestone_id": "M2", "after": ["T1", "T2"]},
    "T4": {"id": "T4", "kind": "docs", "complexity": "low", "title": "docs", "milestone_id": "M2", "after": []},
}


def attempt(aid, number, state, failure="", ended="2026-10-19T12:00:00+00:00", tokens=None):
    return {"attempt": aid, "number": number, "state": state, "failure": failure, "ended_at": ended, "duration_s": 60.0,
            "tokens": tokens, "model_reported": None,
            "route": {"provider": "codex", "model": "gpt-6-luna", "effort": "high", "profile": "codex-1",
                      "source": "m2-ledger"}}


def doc(states):
    return {"plan_id": "REQ-9", "created_at": 1.0, "tasks": {tid: {"state": state} for tid, state in states.items()}}


def rows(states, facts, reworks=None):
    return log.rows("proj", "REQ-9", PLAN, doc(states), facts, "2026-10-19T12:00:00-05:00", reworks)


class Verdicts(unittest.TestCase):
    def test_accepted_work_waits_for_the_audit_over_it_then_counts_as_verified(self):
        facts = {"T1": [attempt("att-0001", 1, "accepted")]}
        self.assertEqual(rows({"T1": "completed", "T3": "running"}, facts), [])           # the audit has not spoken
        found = rows({"T1": "completed", "T3": "completed"}, facts)
        self.assertEqual([(r["task"], r["result"], r["outcome"]) for r in found], [("T1", "verified", "verified")])

    def test_work_with_no_audit_over_it_is_verified_at_once(self):
        found = rows({"T4": "completed"}, {"T4": [attempt("att-0002", 1, "accepted")]})
        self.assertEqual([(r["result"], r["kind"]) for r in found], [("verified", "docs")])

    def test_a_finding_that_names_the_task_makes_its_accepted_attempt_a_failure(self):
        event = {"at": 2e9, "by": "audit-gate", "named": {"T1"}, "tasks": {"T1", "T2"}}
        facts = {"T1": [attempt("att-0001", 1, "accepted", ended="2026-10-19T12:00:00+00:00"),
                        attempt("att-0003", 2, "accepted", ended="2033-05-19T12:00:00+00:00")],
                 "T2": [attempt("att-0002", 1, "accepted")]}
        by = {(r["task"], r["session"]): (r["result"], r["outcome"]) for r in
              rows({"T1": "completed", "T2": "completed", "T3": "completed"}, facts, [event])}
        self.assertEqual(by[("T1", 1)], ("verify_failed", "audit_rejected"))
        self.assertEqual(by[("T2", 2)], ("stopped", "reset_by_rework"))     # redone because T1 was, nobody's fault
        self.assertEqual(by[("T1", 3)], ("verified", "verified"))           # the redo survived

    def test_rejections_infrastructure_and_the_audit_that_found_problems(self):
        facts = {"T2": [attempt("att-0004", 1, "rejected", "m6://result/abc"),
                        attempt("att-0005", 2, "failed", "start rejected: INTEGRATION_CONFLICT"),
                        attempt("att-0006", 3, "failed", "the agent exited 2"),
                        attempt("att-0007", 4, "cancelled", "cancelled_by_executor"),
                        attempt("att-0008", 5, "running")],
                 "T3": [attempt("att-0009", 1, "rejected", "audit gate: 3 open blocking finding(s): F1 (high)")]}
        by = {r["session"]: (r["result"], r["outcome"]) for r in rows({"T2": "running", "T3": "pending"}, facts)}
        self.assertEqual(by, {4: ("verify_failed", "verify_failed"), 5: ("stopped", "infrastructure"),
                              6: ("failed", "failed"), 7: ("stopped", "cancelled"), 9: ("stopped", "gate_found_problems")})

    def test_rows_are_valid_replayable_and_carry_what_the_provider_reported(self):
        facts = {"T4": [attempt("att-0002", 1, "accepted", tokens={"input": 10, "output": 5, "total": 15})]}
        first = rows({"T4": "completed"}, facts)
        self.assertEqual(first, rows({"T4": "completed"}, facts))                 # same ids: appending twice writes once
        row = first[0]
        self.assertTrue(bt_events._valid_row(row))
        self.assertEqual((row["agent"], row["model"], row["effort"], row["complexity"], row["origin"], row["source"]),
                         ("codex", "gpt-6-luna", "high", "S", "real", "scheduler"))
        self.assertEqual((row["usage"]["input_tokens"], row["usage"]["output_tokens"], row["usage"]["quality"]),
                         (10, 5, "reported"))
        empty = rows({"T4": "completed"}, {"T4": [attempt("att-0002", 1, "accepted")]})[0]["usage"]
        self.assertEqual((empty["input_tokens"], empty["quality"]), (None, "unknown"))     # unreported is null, never 0


class Appending(unittest.TestCase):
    def test_a_row_is_appended_once_however_often_the_run_is_synced(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        row = rows({"T4": "completed"}, {"T4": [attempt("att-0002", 1, "accepted")]})[0]
        with tempfile.TemporaryDirectory() as tmp, patch.object(bt_events, "STATE", Path(tmp)):
            known = bt_events.known_event_ids()
            self.assertIsNotNone(bt_events.append_row(row, known))
            self.assertIsNone(bt_events.append_row(row, known))                      # the set already holds it
            self.assertIsNone(bt_events.append_row(row, bt_events.known_event_ids()))   # and so does the file
            self.assertEqual(len(bt_events.read_all()), 1)


if __name__ == "__main__":
    unittest.main()
