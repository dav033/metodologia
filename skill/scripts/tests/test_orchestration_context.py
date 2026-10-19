"""Behavioral contracts for bounded context and durable rotation checkpoints."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# Configure the disposable bitácora root before importing the prompt module.
import run_case_support  # noqa: F401 — Establish the disposable root before prompt imports.

# isort: split

import bt_orchestration_context as context
import bt_requirements_gate as gate
import bt_runprompt


class OrchestrationContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.rdir = Path(self.temp.name)
        (self.rdir / "SPEC.md").write_text("Approved scope\n")
        (self.rdir / "PLAN.md").write_text("---\nstatus: approved\nexecution_contract: requirements-v1\n---\nPlan\n")
        self.review = {key: key + " approved" for key in gate.FIELDS}
        self.review.update(evidence=["SPEC.md", "PLAN.md"], unresolved=[])
        gate.record(self.rdir, self.review)
        self.task = {
            "id": "T1",
            "title": "Build",
            "repo": "skill",
            "verify": "python -m unittest",
            "after": [],
            "milestone": "M1",
            "status": "todo",
            "notes": ["large" * 10000],
            "last_error": "error" * 10000,
        }
        self.state = {
            "req": "REQ-001",
            "project": "test",
            "context_run_id": "run-1",
            "tasks": [self.task],
            "log": ["old" * 100000],
        }

    def test_real_session_prompt_preserves_authority_and_bounds_history(self):
        prompt = bt_runprompt.session_prompt("test", self.rdir, self.state, self.task, 1, "feature", [self.task])
        self.assertLessEqual(len(prompt.encode()), 16384)
        package = json.loads(prompt)
        self.assertEqual(package["authority"]["limits"], "limits approved")
        self.assertEqual(package["authority"]["acceptance"], "acceptance approved")
        self.assertIn("SPEC.md", package["references"])
        self.assertEqual(package["history"]["omitted"], 2)
        self.assertNotIn("oldold", prompt)
        self.assertNotIn("Commit on", prompt)
        self.assertIn("No commits", prompt)

    def test_oversized_mandatory_authority_fails_without_truncation(self):
        gate.record(self.rdir, {**self.review, "limits": "é" * 8000, "scope": "x" * 8000})
        with self.assertRaisesRegex(context.ContextError, "mandatory"):
            context.build_package(self.rdir, self.state, [self.task], "M1")

    def test_runtime_admission_counts_utf8_envelopes_and_reserves_checkpoint(self):
        budget = context.Budget(context.BudgetPolicy(runtime_bytes=256))
        receipt = budget.admit({"output": "é" * 100, "error": None})
        self.assertEqual(receipt.bytes, 226)
        self.assertEqual(budget.remaining_bytes, 30)
        with self.assertRaises(context.ContextPressure):
            budget.admit({"output": "x" * 30})
        self.assertEqual(budget.remaining_bytes, 30)
        checkpoint = context.save_checkpoint(
            self.rdir,
            self.state,
            "M1",
            completed=[],
            remaining=["T1"],
            delegation_refs=["delegate-1/result.json"],
            evidence_refs=["verify.log"],
            budget=budget,
        )
        self.assertEqual(checkpoint["runtime"]["used_bytes"], 226)
        self.assertEqual(context.load_checkpoint(self.rdir, self.state, "M1", budget.policy), checkpoint)

    def test_checkpoint_cas_partition_staleness_and_progress(self):
        budget = context.Budget()
        arguments = {"completed": [], "remaining": ["T1"], "delegation_refs": [], "evidence_refs": [], "budget": budget}
        first = context.save_checkpoint(self.rdir, self.state, "M1", **arguments)
        with self.assertRaisesRegex(context.ContextError, "revision"):
            context.save_checkpoint(self.rdir, self.state, "M1", **arguments)
        second = context.save_checkpoint(
            self.rdir,
            self.state,
            "M1",
            **{**arguments, "completed": ["T1"], "remaining": [], "expected_revision": first["revision"]},
        )
        with self.assertRaisesRegex(context.ContextError, "undo"):
            context.save_checkpoint(self.rdir, self.state, "M1", **arguments, expected_revision=second["revision"])
        with self.assertRaisesRegex(context.ContextError, "run_id"):
            context.load_checkpoint(self.rdir, {**self.state, "context_run_id": "another-run"}, "M1")
        gate.record(self.rdir, {**self.review, "acceptance": "new acceptance"})
        with self.assertRaisesRegex(context.ContextError, "authority_digest"):
            context.load_checkpoint(self.rdir, self.state, "M1")

    def test_checkpoint_rejects_unknown_schema_oversize_and_unknown_tasks(self):
        budget = context.Budget()
        arguments = {"completed": [], "remaining": ["T1"], "delegation_refs": [], "evidence_refs": [], "budget": budget}
        with self.assertRaisesRegex(context.ContextError, "partition"):
            context.save_checkpoint(self.rdir, self.state, "M1", **{**arguments, "remaining": ["missing"]})
        saved = context.save_checkpoint(self.rdir, self.state, "M1", **arguments)
        path = context.checkpoint_path(self.rdir, "M1")
        path.write_text(json.dumps({**saved, "schema": 2}))
        with self.assertRaisesRegex(context.ContextError, "schema"):
            context.load_checkpoint(self.rdir, self.state, "M1")
        path.write_text("x" * 8193)
        with self.assertRaisesRegex(context.ContextError, "Oversized"):
            context.load_checkpoint(self.rdir, self.state, "M1")

    def test_history_count_is_aggregate_and_small_notes_fit(self):
        self.task["notes"] = ["short note"] * 10000
        self.task["last_error"] = "recent error"
        package = context.build_package(self.rdir, self.state, [self.task], "M1")
        self.assertLessEqual(context.byte_size(package), 16384)
        history = package["history"]
        self.assertGreater(history["omitted"], 0)
        self.assertEqual(len(history["items"]) + history["omitted"], 10001)

    def test_policy_invalid_and_explicit_larger_entry_is_supported(self):
        for value in (True, 1, -1, "16384"):
            with self.subTest(value=value), self.assertRaises(context.ContextError):
                context.BudgetPolicy(entry_bytes=value)
        gate.record(self.rdir, {**self.review, "scope": "x" * 8000, "limits": "é" * 8000})
        package = context.build_package(
            self.rdir, self.state, [self.task], "M1", context.BudgetPolicy(entry_bytes=32768)
        )
        self.assertEqual(package["authority"]["limits"], "é" * 8000)

    def test_supervised_hook_omits_full_skill_and_history_and_rejects_unknown_task(self):
        import os
        from unittest.mock import patch

        root = self.rdir / "root"
        req = root / "test" / "requirements" / "REQ-001-example"
        req.mkdir(parents=True)
        for name in ("SPEC.md", "PLAN.md"):
            (req / name).write_text((self.rdir / name).read_text())
        gate.record(req, self.review)
        (req / "RUN.json").write_text(json.dumps(self.state))
        with patch.dict(os.environ, {"BITACORA_PROJECT": "test", "BITACORA_RUN": "REQ-001", "BITACORA_TASK": "T1"}):
            result = context.supervised_hook(root)
            self.assertLess(len(result.encode()), 1024)
            self.assertIn("REQUIREMENTS.json", result)
            self.assertNotIn("oldold", result)
            with patch.dict(os.environ, {"BITACORA_TASK": "unknown"}):
                self.assertIn("STOP", context.supervised_hook(root))

    def test_checkpoint_rejects_unknown_fields(self):
        saved = context.save_checkpoint(
            self.rdir,
            self.state,
            "M1",
            completed=[],
            remaining=["T1"],
            delegation_refs=[],
            evidence_refs=[],
            budget=context.Budget(),
        )
        path = context.checkpoint_path(self.rdir, "M1")
        path.write_text(json.dumps({**saved, "unknown": "injected state"}))
        with self.assertRaisesRegex(context.ContextError, "fields"):
            context.load_checkpoint(self.rdir, self.state, "M1")

    def test_concurrent_writers_cannot_overwrite_same_revision(self):
        from concurrent.futures import ThreadPoolExecutor

        def write():
            try:
                return context.save_checkpoint(
                    self.rdir,
                    self.state,
                    "M1",
                    completed=[],
                    remaining=["T1"],
                    delegation_refs=[],
                    evidence_refs=[],
                    budget=context.Budget(),
                )
            except context.ContextError:
                return None

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: write(), range(2)))
        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(context.load_checkpoint(self.rdir, self.state, "M1")["revision"], 1)

    def test_explicit_successor_resets_instance_budget_without_losing_receipt_count(self):
        policy = context.BudgetPolicy(runtime_bytes=256)
        budget = context.Budget(policy)
        budget.admit({"output": "x" * 200})
        saved = context.save_checkpoint(
            self.rdir,
            self.state,
            "M1",
            completed=[],
            remaining=["T1"],
            delegation_refs=[],
            evidence_refs=[],
            budget=budget,
        )
        successor = budget.successor()
        self.assertEqual(successor.remaining_bytes, 256)
        self.assertEqual(successor.sequence, 1)
        self.assertEqual(successor.generation, 1)
        resumed = context.save_checkpoint(
            self.rdir,
            self.state,
            "M1",
            completed=[],
            remaining=["T1"],
            delegation_refs=[],
            evidence_refs=[],
            budget=successor,
            expected_revision=saved["revision"],
        )
        self.assertEqual(resumed["runtime"]["generation"], 1)

    def test_audit_and_builder_checkpoint_assignments_are_independent(self):
        audit = {
            "id": "M1-audit",
            "title": "Audit",
            "milestone": "M1",
            "kind": "audit",
            "synthetic": True,
            "after": ["T1"],
            "verify": None,
            "repo": None,
            "status": "todo",
        }
        self.state["tasks"].append(audit)
        builder = context.save_checkpoint(
            self.rdir,
            self.state,
            "M1",
            completed=[],
            remaining=["T1"],
            delegation_refs=[],
            evidence_refs=[],
            budget=context.Budget(),
        )
        auditor = context.save_checkpoint(
            self.rdir,
            self.state,
            "M1-audit",
            completed=[],
            remaining=["M1-audit"],
            delegation_refs=[],
            evidence_refs=[],
            budget=context.Budget(),
        )
        self.assertNotEqual(builder["milestone"], auditor["milestone"])
        package = json.loads(bt_runprompt.session_prompt("test", self.rdir, self.state, audit, 2, "feature", [audit]))
        self.assertEqual(package["milestone"], "M1-audit")
        self.assertEqual(package["assignment"]["kind"], "audit")
        self.assertIn("AUDIT-M1.md", package["assignment"]["required_artifact"])
        self.assertEqual(package["assignment"]["members"][0]["verify"], "python -m unittest")
        self.assertIn("--findings", package["assignment"]["verdicts"][0]["done"])

    def test_assignment_retains_verdict_commands_and_final_report_objective(self):
        package = context.build_package(self.rdir, self.state, [self.task], "M1")
        self.assertIn("task", package["assignment"]["verdicts"][0]["done"])
        self.assertIn("--evidence", package["assignment"]["verdicts"][0]["done"])
        final = json.loads(bt_runprompt.session_prompt("test", self.rdir, self.state, None, 3, "feature"))
        self.assertEqual(final["assignment"]["kind"], "final")
        self.assertIn("REPORT.md", final["assignment"]["required_artifact"])
        self.assertIn("Verification evidence", final["assignment"]["sections"])

    def test_history_prioritizes_recent_error_over_old_notes(self):
        self.task["notes"] = ["old note" * 100] * 100
        self.task["last_error"] = "decisive verification failure"
        package = context.build_package(self.rdir, self.state, [self.task], "M1")
        self.assertEqual(package["history"]["items"][0]["text"], "decisive verification failure")




if __name__ == "__main__":
    unittest.main()
