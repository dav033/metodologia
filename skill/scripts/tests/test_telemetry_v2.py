"""Telemetry v2: usage of cut sessions, provider-loss class, error excerpt, change size, origin and audit coverage.

Every field is additive and informational: none of it feeds a supervisor or router decision."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bt_events
import bt_runsession


def assistant(message_id: str, **usage) -> str:
    return json.dumps({"type": "assistant", "message": {"id": message_id, "usage": usage}})


class CutSessionUsageTests(unittest.TestCase):
    def test_a_cut_claude_stream_reports_a_partial_lower_bound(self) -> None:
        raw = "\n".join([
            assistant("m1", input_tokens=10, output_tokens=5, cache_read_input_tokens=100, cache_creation_input_tokens=7),
            assistant("m1", input_tokens=10, output_tokens=9, cache_read_input_tokens=100, cache_creation_input_tokens=7),
            assistant("m2", input_tokens=4, output_tokens=2),
            "You've hit your session limit",
        ])
        usage = bt_events.extract_usage("claude", raw)
        self.assertEqual((usage["source"], usage["quality"]), ("claude-stream-json-partial", "partial"))
        self.assertEqual((usage["input_tokens"], usage["output_tokens"]), (14, 11))  # m1 counted once, latest chunk
        self.assertEqual(usage["total_tokens"], 14 + 11 + 100 + 7)

    def test_a_complete_stream_still_uses_the_result_event_and_nothing_else_is_invented(self) -> None:
        raw = assistant("m1", input_tokens=1, output_tokens=1) + "\n" + json.dumps(
            {"type": "result", "usage": {"input_tokens": 3, "output_tokens": 4}, "total_cost_usd": 0.01})
        usage = bt_events.extract_usage("claude", raw)
        self.assertEqual((usage["source"], usage["quality"], usage["input_tokens"]), ("claude-stream-json", "reported", 3))
        none = bt_events.extract_usage("claude", "no json at all")
        self.assertEqual((none["quality"], none["total_tokens"]), ("unknown", None))


class ProviderLossTests(unittest.TestCase):
    def test_classes_by_result_and_by_the_provider_words(self) -> None:
        self.assertEqual(bt_events.loss_of("usage_limit", ""), "usage_limit")
        self.assertEqual(bt_events.loss_of("failed", "ERROR: Your workspace is out of credits. Add credits to continue."),
                         "out_of_credits")
        self.assertEqual(bt_events.loss_of("failed", "Please sign in to continue"), "auth")
        self.assertIsNone(bt_events.loss_of("failed", "AssertionError: expected 3"))
        self.assertIsNone(bt_events.loss_of("done", "the report mentions out of credits as an example"))

    def test_error_excerpt_is_the_providers_last_error_line_and_bounded(self) -> None:
        raw = "prompt echo that must not be quoted\nERROR: first\nsomething\nERROR: Your workspace is out of credits.\n"
        self.assertEqual(bt_events.error_excerpt(raw), "ERROR: Your workspace is out of credits.")
        self.assertLessEqual(len(bt_events.error_excerpt("ERROR " + "x" * 1000) or ""), 240)
        self.assertIsNone(bt_events.error_excerpt('{"type": "result"}\nall fine'))


class SummaryTests(unittest.TestCase):
    def rows(self) -> list[dict]:
        base = {"agent": "codex", "model": "m", "effort": "low", "kind": "implement"}
        return [
            {**base, "result": "done", "event_id": "a"},
            {**base, "result": "failed", "event_id": "b"},
            {**base, "result": "failed", "event_id": "c", "loss": "out_of_credits"},
            {**base, "result": "usage_limit", "event_id": "d", "loss": "usage_limit"},
        ]

    def test_loss_is_visible_and_the_original_success_rate_is_unchanged(self) -> None:
        group = bt_events.summary(self.rows(), ("agent",))[0]
        self.assertEqual((group["done"], group["failed"], group["other"]), (1, 2, 1))
        self.assertEqual(group["success_rate"], 0.33)  # decisions keep reading this exact number
        self.assertEqual((group["provider_loss"], group["failed_by_loss"]), (2, 1))
        self.assertEqual(group["success_rate_excl_loss"], 0.5)

    def test_audit_report_coverage_counts_only_supervised_audits(self) -> None:
        audit = {"agent": "claude", "model": "m", "effort": None, "kind": "audit", "result": "done"}
        rows = [{**audit, "event_id": "x1", "req": "REQ-001"}, {**audit, "event_id": "x2", "req": "REQ-001"},
                {**audit, "event_id": "x3", "req": "D-20261014-0001"}]
        defects = [{"audit_event_id": "x1", "findings": 2, "builder_attempts": []}]
        group = bt_events.summary(rows, ("agent",), defects)[0]
        self.assertEqual((group["audits_done"], group["audits_unreported"]), (2, 1))
        self.assertIsNone(bt_events.summary(rows, ("agent",))[0]["audits_unreported"])  # unknown without defect rows


class OriginAndChangeSizeTests(unittest.TestCase):
    def test_origin_defaults_to_real_and_only_synthetic_is_tagged(self) -> None:
        self.assertEqual(bt_events.origin_of({}), "real")
        self.assertEqual(bt_events.origin_of({"BITACORA_ORIGIN": "Synthetic"}), "synthetic")
        self.assertEqual(bt_events.origin_of({"BITACORA_ORIGIN": "whatever"}), "real")

    def test_change_size_counts_commits_lines_and_test_files(self) -> None:
        with tempfile.TemporaryDirectory(prefix="change-size-") as tmp:
            def git(*args: str) -> None:
                subprocess.run(["git", "-C", tmp, "-c", "user.name=t", "-c", "user.email=t@t", *args],
                               check=True, capture_output=True)
            git("init", "-q")
            (Path(tmp) / "a.ts").write_text("one\n", encoding="utf-8")
            git("add", "-A")
            git("commit", "-qm", "init")
            before = bt_runsession._git_head(tmp)
            (Path(tmp) / "a.ts").write_text("one\ntwo\nthree\n", encoding="utf-8")
            (Path(tmp) / "a.spec.ts").write_text("t\n", encoding="utf-8")
            git("add", "-A")
            git("commit", "-qm", "work")
            (Path(tmp) / "b.ts").write_text("uncommitted\n", encoding="utf-8")
            size = bt_runsession._change_size(tmp, before)
        self.assertEqual(size["commits"], 1)
        self.assertEqual(size["test_files"], 1)
        self.assertEqual(size["files"], 3)
        self.assertGreaterEqual(size["insertions"], 3)
        self.assertIsNone(bt_runsession._change_size(tmp, None))


if __name__ == "__main__":
    unittest.main()
