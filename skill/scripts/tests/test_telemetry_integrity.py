"""Telemetry consumers preserve measured coverage and the canonical verdict semantics."""
import contextlib
import datetime as dt
import io
import json
import runpy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bt_agents
import bt_events


class TelemetryIntegrityTests(unittest.TestCase):
    def test_reader_rejects_invalid_sessions_before_quality_and_routing(self):
        now = dt.datetime.now().astimezone().isoformat()
        row = {"agent": "codex", "model": "gpt-6-luna", "project": "sample", "req": "REQ-001",
               "task": "T1", "result": "done", "session": 1, "ts": now, "seconds": 10}
        invalid = [{**row, "session": value} for value in ("2", {}, -1, True)]
        with tempfile.TemporaryDirectory() as directory, patch.object(bt_events, "STATE", Path(directory)), \
                patch.object(bt_agents, "account_key", return_value="account"):
            events = Path(directory) / "events"
            events.mkdir()
            (events / "attempts-2026-10.jsonl").write_text('\n'.join(map(json.dumps, [row] + invalid)))
            rows = bt_events.read_all()
            self.assertEqual(rows, [row])
            self.assertEqual(bt_events.summary(rows)[0]["done"], 1)
            rates, load = bt_agents._stats()
            self.assertEqual(rates.samples[("codex", "gpt-6-luna", None, "implement")], 1)
            self.assertEqual(load["account"], 10 * bt_agents.MODELS["gpt-6-luna"]["cost"])

    def test_duration_average_uses_only_measured_attempts_and_exposes_coverage(self):
        mixed = bt_events.summary([{"result": "done", "seconds": 20}, {"result": "done"}])[0]
        self.assertEqual(mixed["seconds"], 20)
        self.assertEqual(mixed["avg_seconds"], 20)
        self.assertEqual(mixed["seconds_measured"], 1)
        self.assertEqual(mixed["seconds_coverage"], 0.5)
        unknown = bt_events.summary([{"result": "done"}])[0]
        self.assertIsNone(unknown["seconds"])
        self.assertIsNone(unknown["avg_seconds"])
        self.assertEqual(unknown["seconds_measured"], 0)
        self.assertEqual(unknown["seconds_coverage"], 0.0)

    def test_advice_does_not_rank_by_unknown_or_under_sampled_durations(self):
        rows = [{"agent": "a", "model": "slow", "result": "done", "seconds": 10} for _ in range(5)]
        rows += [{"agent": "b", "model": "unknown", "result": "done"} for _ in range(5)]
        self.assertIn("best measured is a/slow", bt_events.advice(rows)[0])
        rows[5]["seconds"] = 0
        self.assertIn("best measured is a/slow", bt_events.advice(rows)[0])
        rows[0].pop("seconds")
        advice = bt_events.advice(rows)[0]
        self.assertIn("duration needs 5 measured attempts", advice)
        self.assertNotIn("s avg", advice)

    def test_recording_does_not_present_requested_model_as_provider_confirmation(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(bt_events, "STATE", Path(directory)), \
                patch.object(bt_events.bt_profiles, "is_work_project", return_value=False):
            bt_events.record_attempt("sample", {"req": "REQ-001", "agent": "codex"}, "T1", 1,
                                     {"model": "gpt-6-luna", "text": "no provider identity"}, "done")
            row = bt_events.read_all()[0]
        self.assertEqual(row["model"], "gpt-6-luna")
        self.assertEqual(row["requested_model"], "gpt-6-luna")
        self.assertIsNone(row["reported_model"])
        self.assertEqual(row["identity_source"], "requested")

    def test_globalusage_uses_canonical_daily_summary_and_exposes_unknown_coverage(self):
        import bt_profiles
        import bt_quota_live
        today = dt.datetime.now().astimezone().date().isoformat()
        rows = [{"ts": today + "T12:00:00", "agent": "claude", "model": "haiku", "result": "done",
                 "usage": {"input_tokens": 1000, "output_tokens": 1000, "cache_read_tokens": 8000,
                           "cache_write_tokens": 0}},
                {"ts": today + "T12:01:00", "agent": "claude", "model": "haiku", "result": "verified"},
                {"ts": today + "T12:02:00", "agent": "codex", "model": "unknown", "result": "done"}]
        with tempfile.TemporaryDirectory() as directory, patch.object(bt_events, "STATE", Path(directory)), \
                patch.object(bt_quota_live, "read_all_live", return_value=[]), \
                patch.object(bt_quota_live, "current_profile", return_value=None), \
                patch.object(bt_profiles, "load", return_value={}), patch.object(sys, "argv", ["globalusage"]):
            events = Path(directory) / "events"
            events.mkdir()
            (events / f"attempts-{today[:7]}.jsonl").write_text(
                json.dumps(rows[0]) + '\n{broken\n' + '\n'.join(map(json.dumps, rows[1:])))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                runpy.run_path(str(Path(__file__).resolve().parent.parent / "globalusage.py"))
        text = output.getvalue()
        self.assertIn("10k", text)
        self.assertIn("1/2", text)
        self.assertIn("0/1", text)
        self.assertRegex(text, r"claude/haiku\s+2 ·\s+2")
        self.assertRegex(text, r"codex/unknown\s+1 ·\s+1 ·\s+—")

    def test_codex_stream_usage_keeps_cached_input_inside_total(self):
        raw = json.dumps({"type": "turn.completed", "usage": {
            "input_tokens": 120, "cached_input_tokens": 100, "output_tokens": 8}})
        usage = bt_events.extract_usage("codex", raw)
        self.assertEqual(usage["source"], "codex-exec-json")
        self.assertEqual(usage["quality"], "reported")
        self.assertEqual((usage["input_tokens"], usage["cache_read_tokens"], usage["output_tokens"],
                          usage["total_tokens"]), (120, 100, 8, 128))
        self.assertIsNone(usage["reasoning_tokens"])

    def test_reader_skips_invalid_rows_without_losing_later_attempts(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(bt_events, "STATE", Path(directory)):
            events = Path(directory) / "events"
            events.mkdir()
            row = {"agent": "codex", "result": "done", "usage": {"total_tokens": 30}}
            (events / "attempts-2026-10.jsonl").write_text(
                'null\n[]\n{"broken"\n' + json.dumps(row) + '\n{"result":"done","usage":[]}\n' +
                '\n'.join(json.dumps(bad) for bad in [
                    {"result": "done", "model": []}, {"result": "done", "seconds": "ten"},
                    {"result": "done", "usage": {"input_tokens": "many", "output_tokens": 2}}]))
            self.assertEqual(bt_events.read_all(), [row])

    def test_router_excludes_unjudged_attempts_but_counts_their_load(self):
        now = dt.datetime.now().astimezone()
        rows = [{"agent": "codex", "model": "gpt-6-luna", "profile": "p", "kind": "implement",
                 "ts": now.isoformat(), "seconds": 10, "result": result}
                for result in ["done"] * 5 + ["blocked", "claimed", "escalated", "usage_limit"]]
        with patch.object(bt_events, "read_all", return_value=rows), patch.object(
                bt_agents, "account_key", return_value="account"):
            rates, load = bt_agents._stats()
        key = ("codex", "gpt-6-luna", None, "implement")
        self.assertEqual(rates[key], 1.0)
        self.assertEqual(rates.samples[key], 5)
        self.assertEqual(load["account"], 90 * bt_agents.MODELS["gpt-6-luna"]["cost"])


if __name__ == "__main__":
    unittest.main()
