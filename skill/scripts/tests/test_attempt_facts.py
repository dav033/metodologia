import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_attempt_facts as facts
import bt_scheduler_monitor_adapter as monitor_

T0 = 1_000_000.0


def doc(state="running"):
    def att(n, st, **kw):
        return {"id": f"A-{n}", "task_id": "T1", "number": n, "state": st, "executor": f"route:r{n}",
                "created_at": T0 + n * 100, "updated_at": T0 + n * 100 + 50, "last_event_at": T0 + n * 100 + 10,
                "failure": kw.get("failure", ""), "verifier": kw.get("verifier", "")}
    return {"tasks": {"T1": {"attempts": ["A-1", "A-2"]}},
            "attempts": {"A-1": att(1, "rejected", failure="verify_failed"), "A-2": att(2, state)}}


def m4_store(path, events):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE normalized_events (body TEXT)")
    for body in events:
        conn.execute("INSERT INTO normalized_events VALUES (?)", (json.dumps(body),))
    conn.commit()
    conn.close()


def usage(attempt, name, value, at="2026-10-18T10:00:00+00:00", model="m-x"):
    return {"attempt_id": attempt, "task_id": "T1", "run_id": "r", "provider": "codex", "model": model,
            "event_type": "usage_reported", "received_at": at,
            "payload": {"metric_name": name, "value": value}}


class BuildTests(unittest.TestCase):
    def setUp(self):
        facts._routes.clear()

    def route(self, _ledger, ref):
        return {"provider": "claude", "model": "sonnet", "profile": "claude-work", "effort": "high"} \
            if ref == "route:r2" else {"provider": "codex", "model": "gpt", "profile": "codex1", "effort": ""}

    def test_every_attempt_gets_its_own_route_not_only_the_last(self):
        with patch.object(facts.scheduler_, "resolve_m2_route", self.route):
            rows = facts.build(doc(), Path("x"), {}, now=T0 + 400)["T1"]
        self.assertEqual([r["route"]["provider"] for r in rows], ["codex", "claude"])
        self.assertEqual(rows[0]["route"]["effort"], None)
        self.assertEqual(rows[1]["route"]["source"], "m2-ledger")

    def test_a_resolved_route_is_read_once_and_a_missing_one_is_retried(self):
        calls = []

        def resolve(_ledger, ref):
            calls.append(ref)
            return self.route(_ledger, ref) if len(calls) > 1 else None
        with patch.object(facts.scheduler_, "resolve_m2_route", resolve):
            self.assertIsNone(facts._route(Path("x"), "route:r2")["source"])       # not written yet
            self.assertEqual(facts._route(Path("x"), "route:r2")["provider"], "claude")
            facts._route(Path("x"), "route:r2")["provider"] = "changed"           # callers get copies
            self.assertEqual(facts._route(Path("x"), "route:r2")["provider"], "claude")
        self.assertEqual(len(calls), 2)

    def test_unresolvable_route_is_blank_never_guessed(self):
        rows = facts.build(doc(), None, {}, now=T0 + 400)["T1"]
        self.assertTrue(all(r["route"]["model"] is None for r in rows))

    def test_unresolvable_route_falls_back_to_what_m4_observed_without_inventing_effort(self):
        seen = {"A-1": {"provider": "codex", "model": "gpt-x", "profile_id": "codex1"}}
        rows = facts.build(doc(), None, seen, now=T0 + 400)["T1"]
        self.assertEqual((rows[0]["route"]["provider"], rows[0]["route"]["model"], rows[0]["route"]["source"]),
                         ("codex", "gpt-x", "m4-observed"))
        self.assertIsNone(rows[0]["route"]["effort"])
        self.assertIsNone(rows[1]["route"]["model"])            # no observation, no route

    def test_duration_live_vs_terminal_and_flags(self):
        rows = facts.build(doc(), None, {}, now=T0 + 400)["T1"]
        self.assertEqual(rows[0]["duration_s"], 50.0)          # rejected: created_at -> updated_at
        self.assertFalse(rows[0]["live"])
        self.assertEqual(rows[0]["failure"], "verify_failed")
        self.assertEqual(rows[1]["duration_s"], 200.0)          # live: created_at -> now
        self.assertTrue(rows[1]["live"])
        self.assertIsNone(rows[1]["ended_at"])

    def test_tokens_null_without_samples_and_never_a_computed_total(self):
        seen = {"A-2": {"model": "claude-x", "last_received_at": "2026-10-18T10:00:00+00:00",
                        "tokens_by_metric": {"input_tokens": 10, "output_tokens": 5}}}
        rows = facts.build(doc(), None, seen, now=T0 + 400)["T1"]
        self.assertIsNone(rows[0]["tokens"])
        self.assertEqual(rows[1]["tokens"], {"input": 10, "output": 5, "total": None, "source": "provider_reported"})
        self.assertEqual(rows[1]["model_reported"], "claude-x")

    def test_output_only_provider_keeps_total_unknown(self):
        seen = {"A-2": {"tokens_by_metric": {"output_tokens": 7}}}
        tokens = facts.build(doc(), None, seen, now=T0 + 400)["T1"][1]["tokens"]
        self.assertEqual((tokens["input"], tokens["output"], tokens["total"]), (None, 7, None))

    def test_last_activity_is_the_latest_of_m1_and_m4(self):
        late = "2030-01-01T00:00:00+00:00"
        rows = facts.build(doc(), None, {"A-2": {"last_received_at": late}}, now=T0 + 400)["T1"]
        self.assertTrue(rows[1]["last_activity_at"].startswith("2030-01-01"))
        self.assertTrue(rows[0]["last_activity_at"].startswith("1970-01-12"))

    def test_garbage_document_gives_nothing(self):
        self.assertEqual(facts.build({}, None, {}), {})


class M4SummaryTests(unittest.TestCase):
    def test_summaries_split_metrics_and_keep_none_without_usage(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "m4.sqlite3"
            m4_store(path, [usage("A-1", "input_tokens", 100), usage("A-1", "output_tokens", 20),
                            usage("A-1", "total_tokens", 120), usage("A-1", "total_tokens", 30),
                            {"attempt_id": "A-2", "event_type": "heartbeat", "received_at": "x"}])
            out = monitor_.attempt_usage(path)["attempts"]
        self.assertEqual(out["A-1"]["tokens_by_metric"],
                         {"input_tokens": 100, "output_tokens": 20, "total_tokens": 150})
        self.assertEqual(out["A-1"]["tokens_total"], 150)
        self.assertEqual(out["A-2"]["tokens_by_metric"], {})
        self.assertIsNone(out["A-2"]["tokens_total"])

    def test_usage_is_read_past_the_window_and_then_only_new_rows(self):
        import bt_scheduler_monitor.queries as queries
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "m4.sqlite3"
            m4_store(path, [usage("A-1", "total_tokens", 10)] * 5 + [usage("A-2", "output_tokens", 7, model="m-y")])
            with patch.object(facts.bt_run_stores, "paths", return_value={"m4": path}), \
                    patch.object(queries, "MAX_SUMMARY_EVENTS", 2):
                first = facts.usage_by_attempt(Path(d))
                self.assertEqual((first["A-1"]["events"], first["A-1"]["tokens_total"]), (5, 50))
                self.assertEqual(first["A-2"]["tokens_by_metric"], {"output_tokens": 7})
                conn = sqlite3.connect(path)
                conn.execute("INSERT INTO normalized_events VALUES (?)", (json.dumps(usage("A-1", "total_tokens", 1)),))
                conn.commit()
                conn.close()
                with patch.object(monitor_, "attempt_usage", wraps=monitor_.attempt_usage) as read:
                    again = facts.usage_by_attempt(Path(d))
                self.assertEqual(read.call_args_list[0].kwargs["since_rowid"], 6)     # the decoded rows are not re-read
                self.assertEqual((again["A-1"]["events"], again["A-1"]["tokens_total"]), (6, 51))
                self.assertEqual(first["A-1"]["tokens_total"], 50)                  # callers never share the totals


if __name__ == "__main__":
    unittest.main()
