from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from contextlib import ExitStack, contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bt_plan_adapter
import bt_recovery_apply as apply
import bt_recovery_authorization as auth
import bt_scheduler_adapter
import bt_scheduler_ops
import bt_scheduler_run
from test_remediation import BASE, finding
import bt_remediation


def sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class RecoveryApplyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name)
        frozen = bt_plan_adapter.freeze_revision(self.rdir, BASE, "approval")
        self.source = frozen["sha256"]
        self.compiled_plan = bt_remediation.build_revision(BASE, "T4", [finding("F1", ["T1"])])
        self.target = hashlib.sha256(bt_plan_adapter.planner_contract.dumps(self.compiled_plan).encode()).hexdigest()
        self.new_core_plan = bt_scheduler_adapter.core.load_plan(
            bt_plan_adapter.planner_contract.dumps(self.compiled_plan), approved_sha256=self.target,
            plan_id="REQ-X", revision=2)
        self.scope = ["T4.1"]
        self.grant = {"case_id": "case-1", "case_hash": sha("case"), "proposal_hash": sha("proposal"),
                      "source_sha256": self.source, "target_sha256": self.target, "scope": self.scope,
                      "accepted_map_digest": sha("accepted"), "base_digest": sha("base"),
                      "stop_generation": 0, "cycle_token": "cycle-1"}
        self.key = auth.open_for_run(self.rdir).issue_task_grant(self.grant)
        self.compiled = {"plan": self.compiled_plan, "scope": self.scope, "proposal_hash": self.grant["proposal_hash"],
                         "source_sha256": self.source, "case_id": "case-1", "cycle_token": "cycle-1",
                         "changed_paths": ["src/t1.py"],
                         "verification_map": {"src/t1.py": ["verdict-1"]},
                         "oracle_provenance": {"red": {"identity": "red-1", "source_sha256": sha("broken"),
                                                         "output_sha256": sha("red-output"), "exit_code": 1,
                                                         "source": "captured_broken_source", "overlay_only": True},
                                               "green": {"identity": "green-1", "source_sha256": sha("fixed"),
                                                          "output_sha256": sha("green-output"), "exit_code": 0,
                                                          "source": "corrected_integrated_tree"}}}
        self.identity = {"source_sha256": self.source, "accepted_map_digest": self.grant["accepted_map_digest"],
                         "stop_generation": 0, "paused": False, "cancelled": False, "revision": 1,
                         "plan_id": "REQ-X"}

    def _patch_runtime(self, identity=None, apply_result=None):
        @contextmanager
        def no_hold(_rdir, _why):
            yield

        return (
            patch.object(bt_scheduler_adapter, "revision_identity", return_value=identity or self.identity),
            patch.object(bt_scheduler_adapter, "apply_plan_revision", return_value=apply_result or
                         {"status": "applied", "report": SimpleNamespace(from_revision=1, to_revision=2, kept=("T1",),
                                                                               reset=("T4",), added=("T4.1",), removed=())}),
            patch.object(bt_scheduler_adapter, "approved_plan", return_value=self.new_core_plan),
            patch.object(bt_scheduler_ops, "hold", no_hold),
            patch.object(bt_scheduler_run, "rebind_runtime"),
        )

    def test_stale_accepted_map_and_m1_pause_refuse_before_journal_or_freeze(self):
        stale = {**self.identity, "accepted_map_digest": sha("moved")}
        with patch.object(bt_scheduler_adapter, "revision_identity", return_value=stale):
            result = apply.apply_recovery_revision(self.rdir, self.compiled, self.key, current_base=lambda: sha("base"))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(apply._read(apply.journal_path(self.rdir))["stage"], "blocked")
        apply.journal_path(self.rdir).unlink()
        with patch.object(bt_scheduler_adapter, "revision_identity", return_value={**self.identity, "paused": True}):
            result = apply.apply_recovery_revision(self.rdir, self.compiled, self.key, current_base=lambda: sha("base"))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(len(bt_plan_adapter.revisions(self.rdir)), 1)

    def test_tampered_compiled_proposal_refuses_without_journal_or_plan_write(self):
        altered = {**self.compiled, "proposal_hash": sha("other-proposal")}
        with self.assertRaisesRegex(apply.RecoveryApplyError, "compiled proposal does not match its grant"):
            apply.apply_recovery_revision(self.rdir, altered, self.key, current_base=lambda: sha("base"))
        self.assertFalse(apply.journal_path(self.rdir).exists())
        self.assertEqual(len(bt_plan_adapter.revisions(self.rdir)), 1)

    def test_a_plan_with_more_corrective_tasks_than_the_cycle_allows_is_refused_before_any_write(self):
        tasks = [{"id": f"R{n}", "recovery_task": True} for n in range(9)]
        over = {**self.compiled, "plan": {**self.compiled_plan, "tasks": [*self.compiled_plan["tasks"], *tasks]}}
        with self.assertRaises(apply.RecoveryApplyError) as caught:
            apply.apply_recovery_revision(self.rdir, over, self.key, current_base=lambda: sha("base"))
        self.assertEqual(caught.exception.code, "CORRECTIVE_LIMIT")
        self.assertFalse(apply.journal_path(self.rdir).exists())
        self.assertEqual(len(bt_plan_adapter.revisions(self.rdir)), 1)

    def test_crash_after_freeze_adopts_the_same_revision_and_commits_once(self):
        with ExitStack() as stack:
            for item in self._patch_runtime():
                stack.enter_context(item)
            with self.assertRaises(RuntimeError):
                apply.apply_recovery_revision(self.rdir, self.compiled, self.key, current_base=lambda: sha("base"),
                                              crash_hook=lambda stage: (_ for _ in ()).throw(RuntimeError("crash"))
                                              if stage == "frozen" else None)
            result = apply.apply_recovery_revision(self.rdir, self.compiled, self.key, current_base=lambda: sha("base"))
        self.assertEqual(result["schema"], "recovery-application-receipt/1")
        self.assertEqual(len(bt_plan_adapter.revisions(self.rdir)), 2)
        self.assertEqual(apply._read(apply.journal_path(self.rdir))["stage"], "committed")

    def test_crash_after_m1_apply_resumes_without_reapplying_revision(self):
        target_identity = {**self.identity, "source_sha256": self.target, "revision": 2}
        def fake_apply(*_args):
            return {"status": "applied", "report": {"from_revision": 1, "to_revision": 2}}
        with patch.object(bt_scheduler_adapter, "revision_identity", return_value=self.identity), \
                patch.object(bt_scheduler_adapter, "apply_plan_revision", side_effect=fake_apply), \
                patch.object(bt_scheduler_adapter, "approved_plan", return_value=self.new_core_plan), \
                patch.object(bt_scheduler_ops, "hold", self._patch_runtime()[3].new), \
                patch.object(bt_scheduler_run, "rebind_runtime"):
            with self.assertRaises(RuntimeError):
                apply.apply_recovery_revision(self.rdir, self.compiled, self.key, current_base=lambda: sha("base"),
                                              crash_hook=lambda stage: (_ for _ in ()).throw(RuntimeError("crash"))
                                              if stage == "after_m1_apply_before_journal" else None)
        with patch.object(bt_scheduler_adapter, "revision_identity", return_value=target_identity), \
                patch.object(bt_scheduler_adapter, "apply_plan_revision", side_effect=AssertionError("must not reapply")), \
                patch.object(bt_scheduler_adapter, "approved_plan", return_value=self.new_core_plan), \
                patch.object(bt_scheduler_ops, "hold", self._patch_runtime()[3].new), \
                patch.object(bt_scheduler_run, "rebind_runtime"):
            receipt = apply.apply_recovery_revision(self.rdir, self.compiled, self.key, current_base=lambda: sha("base"))
        self.assertEqual(receipt["target_sha256"], self.target)
        self.assertEqual(len(bt_plan_adapter.revisions(self.rdir)), 2)

    def test_real_adapter_applies_revision_through_m1_and_keeps_counters(self):
        with patch.object(bt_scheduler_adapter, "plan_consumer_problem", return_value=None):
            scheduler = bt_scheduler_adapter.open_scheduler(self.rdir)
            before = scheduler.read(lambda ctx: dict(ctx.state.counters))
            identity = bt_scheduler_adapter.revision_identity(self.rdir)
            frozen = bt_plan_adapter.freeze_revision(self.rdir, self.compiled_plan, "recovery")
            scope = ["T4", "T4.1"]
            grant = {**self.grant, "source_sha256": identity["source_sha256"],
                     "target_sha256": frozen["sha256"], "accepted_map_digest": identity["accepted_map_digest"],
                     "stop_generation": identity["stop_generation"], "scope": scope,
                     "case_id": "case-2", "case_hash": sha("case-2"), "cycle_token": "cycle-2",
                     "proposal_hash": sha("proposal-2")}
            key = auth.open_for_run(self.rdir).issue_task_grant(grant)
            compiled = {**self.compiled, "scope": scope, "source_sha256": identity["source_sha256"],
                        "case_id": "case-2", "cycle_token": "cycle-2", "proposal_hash": grant["proposal_hash"]}
            with patch.object(bt_scheduler_run, "rebind_runtime"):
                receipt = apply.apply_recovery_revision(self.rdir, compiled, key, current_base=lambda: sha("base"))
            after = bt_scheduler_adapter.revision_identity(self.rdir)
        self.assertEqual(after["source_sha256"], frozen["sha256"])
        after_counters = scheduler.read(lambda ctx: dict(ctx.state.counters))
        self.assertEqual({key: after_counters[key] for key in ("attempt", "token", "outbox")},
                         {key: before[key] for key in ("attempt", "token", "outbox")})
        self.assertGreater(after_counters["audit"], before["audit"])
        self.assertEqual(receipt["schema"], "recovery-application-receipt/1")

    def test_hold_waits_for_live_work_and_closure_refuses_unverified_web_surface(self):
        with ExitStack() as stack:
            for item in self._patch_runtime(identity={**self.identity, "live_attempts": ["att-1"]},
                                            apply_result={"status": "waiting", "reason": "live_attempts",
                                                          "live_attempts": ["att-1"], "stop_generation": 0}):
                stack.enter_context(item)
            result = apply.apply_recovery_revision(self.rdir, self.compiled, self.key, current_base=lambda: sha("base"))
        self.assertEqual((result["status"], result["reason"], result["live_attempts"]),
                         ("waiting", "live_attempts", ["att-1"]))
        receipt = {"lineage": {"case_id": "case-1"}, "verdicts": ["missing"],
                   "changed_paths": ["apps/web/page.tsx"], "verification_map": {},
                   "oracle_provenance": {"red": {"identity": "r", "source_sha256": sha("broken"),
                                                  "output_sha256": sha("red-output"), "exit_code": 1,
                                                  "source": "captured_broken_source", "overlay_only": True},
                                         "green": {"identity": "g", "source_sha256": sha("fixed"),
                                                   "output_sha256": sha("green-output"), "exit_code": 0,
                                                   "source": "corrected_integrated_tree"}}}
        self.assertIn("changed path", apply.closure_problem(receipt, []))
        receipt["verification_map"] = {"apps/web/page.tsx": ["missing"]}
        self.assertIn("changed path", apply.closure_problem(receipt, []))
        self.assertIsNone(apply.closure_problem(receipt, [{"identity": "missing", "independent": True,
                                                            "accepted": True}]))

    def test_closure_uses_actual_changed_paths_against_the_t4b_map(self):
        receipt = {"lineage": {"case_id": "case-1"}, "verdicts": ["m6:" + sha("verdict")],
                   "changed_paths": ["src/declared.py"], "actual_changed_paths": ["apps/page.tsx"],
                   "verification_map": {"schema_version": "recovery-verification-map/1",
                                        "changed_paths": [{"path": "src/declared.py", "owner_task_id": "T1"}],
                                        "checks": [], "existing_owner_commands": [],
                                        "uncovered_paths": [], "uncovered_checks": []}}
        self.assertIn("changed paths", apply.closure_problem(receipt, []))

    def test_existing_operator_hold_blocks_without_journal_or_plan_write(self):
        hold = bt_scheduler_ops.hold_path(self.rdir)
        hold.write_text('{"why":"operator maintenance","pid":99999999}\n', encoding="utf-8")
        result = apply.apply_recovery_revision(self.rdir, self.compiled, self.key, current_base=lambda: sha("base"))
        self.assertEqual((result["status"], result["reason"]), ("blocked", "run is already on hold"))
        self.assertFalse(apply.journal_path(self.rdir).exists())
        self.assertEqual(len(bt_plan_adapter.revisions(self.rdir)), 1)

    def test_operator_stop_during_transactional_base_recheck_is_preserved_and_blocks_revision(self):
        base_reads = 0

        def current_base():
            nonlocal base_reads
            base_reads += 1
            return sha("base")

        def m1_apply(_rdir, _old, _new, guard):
            self.assertEqual(guard["current_base"](), "operator-hold-changed")
            return {"status": "blocked", "reason": "stale_base", "stop_generation": 0}

        with patch.object(bt_scheduler_adapter, "revision_identity", return_value=self.identity), \
                patch.object(bt_scheduler_adapter, "apply_plan_revision", side_effect=m1_apply), \
                patch.object(bt_scheduler_adapter, "approved_plan", return_value=self.new_core_plan), \
                patch.object(bt_scheduler_ops, "stop_owner", return_value=0), \
                patch.object(bt_scheduler_adapter, "apply_control") as apply_control, \
                patch.object(bt_scheduler_run, "rebind_runtime"):
            def stop_on_third_read():
                nonlocal base_reads
                base_reads += 1
                if base_reads == 3:
                    bt_scheduler_ops.apply("p", "REQ-X", self.rdir, "stop", keep_held=True)
                return sha("base")

            result = apply.apply_recovery_revision(self.rdir, self.compiled, self.key, current_base=stop_on_third_read)

        self.assertEqual(base_reads, 3)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(json.loads(bt_scheduler_ops.hold_path(self.rdir).read_text())["why"], "operator stop")
        apply_control.assert_called_once_with(self.rdir, "stop", by=bt_scheduler_ops.OPERATOR)

    def test_operator_stop_during_m1_base_recheck_advances_stop_generation_without_revision(self):
        with patch.object(bt_scheduler_adapter, "plan_consumer_problem", return_value=None), \
                patch.object(bt_scheduler_ops, "stop_owner", return_value=0):
            scheduler = bt_scheduler_adapter.open_scheduler(self.rdir)
            identity = bt_scheduler_adapter.revision_identity(self.rdir)
            frozen = bt_plan_adapter.freeze_revision(self.rdir, self.compiled_plan, "recovery")
            scope = ["T4", "T4.1"]
            grant = {**self.grant, "source_sha256": identity["source_sha256"],
                     "target_sha256": frozen["sha256"], "accepted_map_digest": identity["accepted_map_digest"],
                     "stop_generation": identity["stop_generation"], "scope": scope,
                     "case_id": "case-stop", "case_hash": sha("case-stop"), "cycle_token": "cycle-stop",
                     "proposal_hash": sha("proposal-stop")}
            key = auth.open_for_run(self.rdir).issue_task_grant(grant)
            compiled = {**self.compiled, "scope": scope, "source_sha256": identity["source_sha256"],
                        "case_id": grant["case_id"], "cycle_token": grant["cycle_token"],
                        "proposal_hash": grant["proposal_hash"]}
            reads = 0

            def current_base():
                nonlocal reads
                reads += 1
                if reads == 3:
                    bt_scheduler_ops.apply("p", "REQ-X", self.rdir, "stop", keep_held=True)
                return sha("base")

            result = apply.apply_recovery_revision(self.rdir, compiled, key, current_base=current_base)
            final = bt_scheduler_adapter.revision_identity(self.rdir)

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(final["source_sha256"], identity["source_sha256"])
        self.assertEqual(final["stop_generation"], identity["stop_generation"] + 1)
        self.assertTrue(bt_scheduler_ops.on_hold(self.rdir))
        self.assertEqual(scheduler.read(lambda ctx: ctx.state.revision), 1)

    def test_two_barrier_expiries_write_durable_quiescence_blocker(self):
        wait = {"status": "waiting", "reason": "barrier_expired", "live_attempts": ["att-live"],
                "stop_generation": 0}
        with patch.object(bt_scheduler_adapter, "revision_identity", return_value=self.identity), \
                patch.object(bt_scheduler_adapter, "apply_plan_revision", return_value=wait), \
                patch.object(bt_scheduler_adapter, "approved_plan", return_value=self.new_core_plan), \
                patch.object(bt_scheduler_adapter, "abort_revision_barrier", return_value=True) as abort_barrier, \
                patch.object(bt_scheduler_ops, "hold", self._patch_runtime()[3].new), \
                patch.object(bt_scheduler_run, "rebind_runtime"):
            first = apply.apply_recovery_revision(self.rdir, self.compiled, self.key, current_base=lambda: sha("base"))
            second = apply.apply_recovery_revision(self.rdir, self.compiled, self.key, current_base=lambda: sha("base"))
        self.assertEqual(first["reason"], "barrier_expired")
        self.assertEqual(second["reason"], "revision_quiescence_timeout")
        self.assertTrue(abort_barrier.called)
        self.assertEqual(apply._read(apply.journal_path(self.rdir))["blocker"], "revision_quiescence_timeout")

    def test_quiescence_retry_accepts_only_m1_tracked_live_work_settlement(self):
        wait = {"status": "waiting", "reason": "live_attempts", "live_attempts": ["att-live"],
                "stop_generation": 0}
        applied = {"status": "applied", "report": {"from_revision": 1, "to_revision": 2}}
        moved_map = {**self.identity, "accepted_map_digest": sha("after-live-settlement")}
        with patch.object(bt_scheduler_adapter, "revision_identity", side_effect=[self.identity, moved_map]), \
                patch.object(bt_scheduler_adapter, "apply_plan_revision", side_effect=[wait, applied]) as apply_m1, \
                patch.object(bt_scheduler_adapter, "approved_plan", return_value=self.new_core_plan), \
                patch.object(bt_scheduler_ops, "hold", self._patch_runtime()[3].new), \
                patch.object(bt_scheduler_run, "rebind_runtime"):
            first = apply.apply_recovery_revision(self.rdir, self.compiled, self.key, current_base=lambda: sha("base"))
            second = apply.apply_recovery_revision(self.rdir, self.compiled, self.key,
                                                   current_base=lambda: sha("base"))
        self.assertEqual(first["status"], "waiting")
        self.assertEqual(second["schema"], "recovery-application-receipt/1")
        self.assertEqual(apply_m1.call_count, 2)

if __name__ == "__main__":
    unittest.main()
