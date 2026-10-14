"""Quality by defects: findings flag validation, null vs 0, attribution to accepted attempts, rework, metrics fields."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_marathon_robust import RobustCase  # noqa: F401  (sets BITACORA_ROOT before bt_* imports)

import bt_events  # noqa: E402
import bt_quality  # noqa: E402
import bt_runstate as rs  # noqa: E402
import bt_runtask as rt  # noqa: E402

EXISTING_FIELDS = ("attempts", "done", "failed", "other", "seconds", "measured", "tokens_measured",
                   "cost_usd_reported", "cost_measured", "success_rate", "avg_seconds", "coverage", "tokens_per_done")


class ParseFindingsTests(unittest.TestCase):
    def test_not_reported_is_unknown(self):
        self.assertEqual(bt_quality.parse_findings(None, None), (None, None))

    def test_zero_is_a_clean_audit_with_zero_severities(self):
        self.assertEqual(bt_quality.parse_findings(0, None), (0, {"high": 0, "med": 0, "low": 0}))

    def test_severity_must_add_up(self):
        self.assertEqual(bt_quality.parse_findings(3, "high=1,low=2"), (3, {"high": 1, "med": 0, "low": 2}))
        with self.assertRaises(SystemExit):
            bt_quality.parse_findings(3, "high=1,med=1")

    def test_invalid_input_is_rejected(self):
        for findings, severity in ((-1, None), (None, "high=1"), (1, "critical=1"), (1, "high=x"), (1, "high=-1")):
            with self.assertRaises(SystemExit, msg=(findings, severity)):
                bt_quality.parse_findings(findings, severity)

    def test_non_ascii_digits_and_duplicate_keys_are_rejected(self):
        for severity in ("high=\u0661", "high=1,high=1", "high=", "", ",", "high=1,"):
            if not severity:
                continue
            with self.assertRaises(SystemExit, msg=severity):
                bt_quality.parse_findings(1, severity)

    def test_positive_count_without_severity_keeps_severity_unknown(self):
        self.assertEqual(bt_quality.parse_findings(2, None), (2, None))


class TaskDonePersistsFindingsTests(RobustCase):
    def test_flag_is_stored_and_missing_flag_is_null(self):
        self.seed(["- [ ] T1 — a"])
        rt.task_done(self.rdir, "T1", "ok", 2, "high=1,med=1")
        task = rs.get_task(rs.load(self.rdir), "T1")
        self.assertEqual((task["findings"], task["severity"]), (2, {"high": 1, "med": 1, "low": 0}))
        rt.task_done(self.rdir, "T1", "again")
        task = rs.get_task(rs.load(self.rdir), "T1")
        self.assertIsNone(task["findings"])  # unknown, never 0
        self.assertIsNone(task["severity"])


def attempt(session, task, result="done", kind="implement", model="haiku", milestone="M1", tokens=100, **extra):
    return {"event_id": f"e{session}", "project": "p", "req": "REQ-001", "task": task, "tasks": [task],
            "session": session, "agent": "claude", "model": model, "effort": None, "kind": kind, "result": result,
            "milestone": milestone, "seconds": 10, "usage": {"total_tokens": tokens}, **extra}


class AttributionTests(unittest.TestCase):
    def test_only_the_last_accepted_attempt_is_attributed_and_earlier_failures_are_rework(self):
        rows = [attempt(1, "T1", "verify_failed", model="haiku"), attempt(2, "T1", "done", model="sonnet"),
                attempt(3, "T2", "done"), attempt(4, "M1-audit", "done", kind="audit", model="opus")]
        tasks = [{"id": "T1", "status": "done"}, {"id": "T2", "status": "done"},
                 {"id": "M1-audit", "status": "done", "kind": "audit", "synthetic": True}]
        ids, rework = bt_quality.attribution(rows, "p", "REQ-001", tasks)
        self.assertEqual((ids, rework), (["e2", "e3"], 1))

    def test_a_task_that_is_not_done_is_not_attributed(self):
        ids, rework = bt_quality.attribution([attempt(1, "T1", "failed")], "p", "REQ-001",
                                             [{"id": "T1", "status": "todo"}])
        self.assertEqual((ids, rework), ([], 0))


class BatchAndReadTests(unittest.TestCase):
    def test_mixed_batch_result_still_attributes_the_done_task_and_counts_rework_per_task(self):
        rows = [attempt(1, "T1,T2", "partial", tasks=["T1", "T2"], task_results={"T1": "verify_failed", "T2": "verify_failed"}),
                attempt(2, "T1,T2", "partial", tasks=["T1", "T2"], task_results={"T1": "done", "T2": "verify_failed"}),
                attempt(3, "T2", "done")]
        tasks = [{"id": "T1", "status": "done"}, {"id": "T2", "status": "done"}]
        ids, rework = bt_quality.attribution(rows, "p", "REQ-001", tasks)
        self.assertEqual((ids, rework), (["e2", "e3"], 1 + 2))
        self.assertEqual(len(bt_quality.rework_events(rows)), 3)  # same per-task rule as attribution

    def test_detail_for_keeps_per_task_results(self):
        tasks = [{"id": "T1", "milestone": "M1"}, {"id": "T2", "milestone": "M1"}]
        detail = bt_events.detail_for(tasks, "partial", {"T1": "done", "T2": "verify_failed"})
        self.assertEqual(detail["task_results"], {"T1": "done", "T2": "verify_failed"})

    def test_unreadable_defect_files_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            events = Path(tmp) / "events"
            events.mkdir()
            (events / "defects-2026-01.jsonl").write_bytes(b"\xff\xfe\x00bad")
            (events / "defects-2026-02.jsonl").write_text('{"findings": 1}\nnot json\n[1]\n')
            with patch("bt_events.STATE", Path(tmp)):
                self.assertEqual(bt_quality.read_defects(), [{"findings": 1}])


class RecordingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="quality-test-")
        self.addCleanup(self.tmp.cleanup)
        patcher = patch("bt_events.STATE", Path(self.tmp.name) / ".state")
        patcher.start()
        self.addCleanup(patcher.stop)
        self.attempts = [attempt(1, "T1", "verify_failed", model="haiku"), attempt(2, "T1", "done", model="sonnet"),
                         attempt(3, "M1-audit", "done", kind="audit", model="opus")]
        self.state = {"req": "REQ-001", "agent": "claude", "tasks": [
            {"id": "T1", "status": "done", "milestone": "M1"},
            {"id": "M1-audit", "status": "done", "kind": "audit", "synthetic": True, "milestone": "M1",
             "findings": 2, "severity": {"high": 1, "med": 1, "low": 0}}]}
        self.info = {"agent": "claude", "model": "opus", "effort": "high"}
        self.audit = self.state["tasks"][1]

    def record(self, audit=None):
        with patch("bt_events.read_all", return_value=self.attempts):
            return bt_quality.record_audit_verdict("p", self.state, audit or self.audit, 3, self.info)

    def test_row_attributes_findings_to_builders_and_is_idempotent(self):
        path = self.record()
        self.assertIsNone(self.record())
        row = json.loads(path.read_text().splitlines()[0])
        self.assertEqual((row["findings"], row["builder_attempts"], row["rework_attempts"]), (2, ["e2"], 1))
        self.assertEqual(row["auditor"], {"agent": "claude", "model": "opus", "effort": "high"})
        self.assertEqual(row["audit_event_id"], bt_events.event_id_for("p", "REQ-001", 3))
        self.assertEqual(len(path.read_text().splitlines()), 1)

    def test_audit_without_the_flag_records_null_not_zero(self):
        path = self.record({**self.audit, "findings": None, "severity": None})
        self.assertIsNone(json.loads(path.read_text())["findings"])

    def test_only_accepted_synthetic_audits_are_recorded(self):
        self.assertIsNone(self.record({**self.audit, "status": "todo"}))
        self.assertIsNone(self.record({**self.audit, "synthetic": False}))

    def test_a_recording_failure_never_raises(self):
        with patch("bt_quality.attribution", side_effect=RuntimeError("boom")):
            self.assertIsNone(self.record())


class MetricsFieldsTests(unittest.TestCase):
    def rows(self):
        return [attempt(1, "T1", "verify_failed", model="haiku", tokens=50), attempt(2, "T1", "done", model="sonnet"),
                attempt(3, "T2", "done", model="sonnet", tokens=300),
                attempt(4, "T3", "done", model="haiku", tokens=40),
                attempt(5, "M1-audit", "done", kind="audit", model="opus")]

    def defects(self, **override):
        return [{"event_id": "e5", "findings": 3, "severity": {"high": 1, "med": 1, "low": 1},
                 "builder_attempts": ["e2"], **override},
                {"event_id": "e6", "findings": 0, "severity": {"high": 0, "med": 0, "low": 0},
                 "builder_attempts": ["e3"]}]

    def group(self, groups, model, kind="implement"):
        return next(g for g in groups if g["model"] == model and g["kind"] == kind)

    def test_quality_fields_per_group(self):
        groups = bt_events.summary(self.rows(), ("model", "kind"), self.defects())
        sonnet = self.group(groups, "sonnet")
        self.assertEqual((sonnet["audited"], sonnet["findings"], sonnet["findings_per_audited_task"],
                          sonnet["high_findings"]), (2, 3, 1.5, 1))
        self.assertEqual(sonnet["tokens_per_clean_task"], 300)  # only e3 is clean: its tokens only, not e2's
        haiku = self.group(groups, "haiku")
        self.assertEqual((haiku["rework_attempts"], haiku["rework_rate"]), (1, 0.5))  # e1 failed before e2

    def test_findings_are_split_in_shares_across_attributed_attempts(self):
        rows = [attempt(1, "T1", model="a"), attempt(2, "T2", model="b"), attempt(3, "T3", model="b")]
        defects = [{"event_id": "x", "findings": 3, "severity": {"high": 1, "med": 2, "low": 0},
                    "builder_attempts": ["e1", "e2", "e3"]}]
        groups = bt_events.summary(rows, ("model",), defects)
        by = {g["model"]: g for g in groups}
        self.assertEqual((by["a"]["findings"], by["b"]["findings"]), (1, 2))
        self.assertEqual(sum(g["findings"] for g in groups), 3)  # the audit's true total
        self.assertEqual(by["b"]["findings_per_audited_task"], 1)
        self.assertAlmostEqual(by["a"]["high_findings"] + by["b"]["high_findings"], 1)
        odd = bt_events.summary(rows[:2], ("model",), [{**defects[0], "builder_attempts": ["e1", "e2"], "findings": 1,
                                                        "severity": {"high": 0, "med": 1, "low": 0}}])
        self.assertEqual([g["findings"] for g in odd], [0.5, 0.5])

    def test_clean_tokens_need_every_clean_attempt_measured(self):
        rows = [attempt(1, "T1"), {**attempt(2, "T2"), "usage": {}}]
        zero = {"high": 0, "med": 0, "low": 0}
        defects = [{"event_id": "x", "findings": 0, "severity": zero, "builder_attempts": ["e1"]},
                   {"event_id": "y", "findings": 0, "severity": zero, "builder_attempts": ["e2"]}]
        self.assertIsNone(bt_events.summary(rows, ("model",), defects)[0]["tokens_per_clean_task"])

    def test_rework_rate_uses_the_same_classes_as_the_summary(self):
        rows = [attempt(1, "T1", "escalated"), attempt(2, "T1", "timeout"), attempt(3, "T1", "done")]
        g = bt_events.summary(rows, ("model",), [])[0]
        self.assertEqual((g["rework_attempts"], g["failed"], g["rework_rate"]), (2, 1, 0.5))  # 1 judged failure over 2 judged (done + failed)

    def test_unknown_stays_null(self):
        groups = bt_events.summary(self.rows(), ("model", "kind"), self.defects())
        haiku = self.group(groups, "haiku")  # T3's attempt was never audited
        self.assertEqual(haiku["audited"], 0)
        for field in ("findings", "findings_per_audited_task", "high_findings", "tokens_per_clean_task"):
            self.assertIsNone(haiku[field], field)
        without = bt_events.summary(self.rows(), ("model", "kind"))
        self.assertTrue(all(g["findings_per_audited_task"] is None for g in without))

    def test_the_auditor_is_not_judged_on_its_own_findings(self):
        groups = bt_events.summary(self.rows(), ("model", "kind"), self.defects(builder_attempts=["e2", "e5"]))
        opus = self.group(groups, "opus", "audit")
        self.assertEqual(opus["audited"], 0)
        self.assertIsNone(opus["findings"])

    def test_unreported_audits_are_not_counted_as_clean(self):
        groups = bt_events.summary(self.rows(), ("model", "kind"), self.defects(findings=None, severity=None))
        self.assertEqual(self.group(groups, "sonnet")["audited"], 1)  # only the e3 verdict is known

    def test_existing_fields_keep_their_meaning(self):
        rows = self.rows()
        with_quality = bt_events.summary(rows, ("model", "kind"), self.defects())
        plain = bt_events.summary(rows, ("model", "kind"))
        for a, b in zip(with_quality, plain):
            for field in EXISTING_FIELDS:
                self.assertEqual(a[field], b[field], field)
        sonnet = self.group(plain, "sonnet")
        self.assertEqual((sonnet["attempts"], sonnet["done"], sonnet["success_rate"], sonnet["tokens_per_done"]),
                         (2, 2, 1.0, 200))

    def test_advice_mentions_quality_only_with_enough_audited_tasks(self):
        before = bt_events.advice(self.rows(), 2)
        self.assertEqual(bt_events.advice(self.rows(), 2, []), before)
        self.assertFalse(any(line.startswith("quality") for line in before))
        enough = bt_events.advice(self.rows(), 2, self.defects())
        self.assertTrue(any(line.startswith("quality implement: claude/sonnet") for line in enough))
        self.assertEqual([line for line in enough if not line.startswith("quality")], before)
        self.assertFalse(any(line.startswith("quality") for line in bt_events.advice(self.rows(), 3, self.defects())))


if __name__ == "__main__":
    unittest.main()
