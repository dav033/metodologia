"""«Ejecutar SP-N» on a stage that needs subplans not run yet queues it; approving them in «Probar» runs it (REQ-021 SP-8)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_plan_adapter
import bt_scheduler_adapter
import bt_stage_queue as sq
import bt_stages
import bt_verification


def gate(rdir, subplans, **_):
    """SP-8 alone fails (it cites SP-7's tasks); with SP-7 before it, it passes."""
    return None if subplans[:1] == ["SP-7"] or subplans == ["SP-7"] else "PLAN_INVALID: task 'T7.5' is not in this plan"


class StageQueue(unittest.TestCase):
    def setUp(self):
        self.rdir = Path(tempfile.mkdtemp(prefix="bt-stage-queue-")) / "REQ-021-x"
        (self.rdir / ".planning").mkdir(parents=True)
        for target, value in ((bt_plan_adapter, "draft_subplans"), (bt_stages, "approved"),
                              (bt_scheduler_adapter, "plan_compatibility_report")):
            result = {"draft_subplans": ["SP-5", "SP-6", "SP-7", "SP-8"], "approved": ["SP-5", "SP-6"],
                      "plan_compatibility_report": {}}[value]
            patcher = patch.object(target, value, return_value=result)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(bt_plan_adapter, "stage_problem", side_effect=gate)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch("bt_planning_activity.record")
        self.activity = patcher.start()
        self.addCleanup(patcher.stop)

    def test_a_stage_that_needs_an_earlier_subplan_is_queued_not_refused(self):
        refused = bt_stages.StageError("PLAN_INVALID", "the stage cannot be approved: task 'T7.5' is not in this plan")
        with patch.object(bt_stages, "freeze", side_effect=refused):
            message = bt_stages.run("pictures", self.rdir, ["SP-8"])
        self.assertIn("SP-8 depende de SP-7", message)
        self.assertIn("lo apruebes en «Probar»", message)
        self.assertEqual([(i["add"], i["after"]) for i in sq.pending(self.rdir)], [(["SP-8"], ["SP-7"])])

    def test_an_unconfirmed_subplan_or_an_unrelated_failure_is_still_refused(self):
        with patch.object(bt_stages, "freeze", side_effect=bt_stages.StageError("STAGE_SUBPLAN_UNCONFIRMED", "SP-8: sin confirmar")):
            with self.assertRaises(bt_stages.StageError):
                bt_stages.run("pictures", self.rdir, ["SP-8"])
        with patch.object(bt_plan_adapter, "stage_problem", return_value="PLAN_INVALID: broken"), \
                patch.object(bt_stages, "freeze", side_effect=bt_stages.StageError("PLAN_INVALID", "broken")):
            with self.assertRaises(bt_stages.StageError):
                bt_stages.run("pictures", self.rdir, ["SP-8"])
        self.assertEqual(sq.pending(self.rdir), [])

    def test_approving_the_awaited_subplan_runs_the_queued_stage_and_only_then(self):
        sq.queue(self.rdir, ["SP-8"], ["SP-7"], by="owner", via="web")
        state = {"subplans": [{"id": "SP-7", "state": "to_test"}]}
        with patch.object(bt_verification, "state", return_value=state), \
                patch.object(bt_stages, "run", return_value="Etapa r21 aprobada") as run:
            self.assertEqual(sq.drain("pictures", self.rdir), [])
            run.assert_not_called()
            state["subplans"][0]["state"] = "approved"
            self.assertEqual(sq.drain("pictures", self.rdir), ["Etapa r21 aprobada"])
            run.assert_called_once_with("pictures", self.rdir, ["SP-8"], by="owner", via="stage-queue")
        self.assertEqual(sq.pending(self.rdir), [])

    def test_a_queued_stage_that_still_cannot_run_stays_with_its_error(self):
        sq.queue(self.rdir, ["SP-8"], ["SP-7"], by="owner", via="web")
        with patch.object(bt_verification, "state", return_value={"subplans": [{"id": "SP-7", "state": "approved"}]}), \
                patch.object(bt_stages, "run", side_effect=bt_stages.StageError("STAGE_SUBPLAN_UNCONFIRMED", "SP-8: cambió")):
            self.assertEqual(sq.drain("pictures", self.rdir), [])
        self.assertIn("STAGE_SUBPLAN_UNCONFIRMED", sq.pending(self.rdir)[0]["error"])

    def test_a_queued_subplan_the_owner_ran_from_its_button_leaves_the_queue(self):
        sq.queue(self.rdir, ["SP-8"], ["SP-7"], by="owner", via="web")
        with patch.object(bt_stages, "approved", return_value=["SP-5", "SP-6", "SP-7", "SP-8"]), \
                patch.object(bt_verification, "state", return_value={"subplans": [{"id": "SP-7", "state": "approved"}]}), \
                patch.object(bt_stages, "run") as run:
            self.assertEqual(sq.drain("pictures", self.rdir), [])
        run.assert_not_called()                                # no second, identical stage
        self.assertEqual(sq.pending(self.rdir), [])
        sq.queue(self.rdir, ["SP-9"], ["SP-8"], by="owner", via="web")
        with patch.object(bt_stages, "freeze", return_value={"revision": 22, "stage": {"subplans": ["SP-5", "SP-6", "SP-9"]}}), \
                patch.object(bt_stages, "approved", return_value=["SP-5", "SP-6", "SP-9"]), \
                patch.object(bt_stages, "start_or_join", return_value="La ejecución sigue con la etapa aprobada."):
            bt_stages.run("pictures", self.rdir, ["SP-9"])
        self.assertEqual(sq.pending(self.rdir), [])

    def test_the_owners_approval_drains_the_queue(self):
        decisions = self.rdir / ".verification"
        decisions.mkdir()
        row = {"id": "SP-7", "state": "to_test", "version": 1, "commit": "abc"}
        with patch.object(bt_verification, "state", return_value={"subplans": [row]}), \
                patch.object(bt_verification, "gate", return_value=["SP-8: por probar"]), \
                patch.object(sq, "drain", return_value=["Etapa r21 aprobada con SP-8."]) as drain:
            message = bt_verification.decide("pictures", self.rdir, "SP-7", "approved")
        drain.assert_called_once_with("pictures", self.rdir)
        self.assertIn("SP-7 aprobado.", message)
        self.assertIn("Etapa r21 aprobada con SP-8.", message)


class Readiness(unittest.TestCase):
    def test_readiness_applies_the_mapping_gate_the_button_applies(self):
        rdir = Path(tempfile.mkdtemp(prefix="bt-readiness-")) / "REQ-021-x"
        rdir.mkdir()
        (rdir / "PLAN.json").write_text(json.dumps({"subplans": [{"id": "SP-6"}], "tasks": [{"id": "T6.1", "subplan_id": "SP-6"}]}))
        with patch.object(bt_plan_adapter.planner.stages, "latest", return_value=None), \
                patch.object(bt_plan_adapter, "stage_problem", return_value="PLAN_CHECKS_UNMAPPED: T6.1") as problem:
            rows = bt_plan_adapter.stage_readiness(rdir)
        self.assertEqual(rows[0]["problem"], "PLAN_CHECKS_UNMAPPED: T6.1")
        self.assertNotIn("allow_unmapped", problem.call_args.kwargs)


if __name__ == "__main__":
    unittest.main()
