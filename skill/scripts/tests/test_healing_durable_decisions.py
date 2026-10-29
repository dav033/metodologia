"""The engine answers a durable run's open decision the way the legacy Scheduler's self-healing did: a diagnosing model
reads the failure and its validated `retry`/`retry_with_note` goes to that exact round, once per signature; a plan defect
goes to the Planner and stays for the owner (D-167; pictures REQ-021 T4.2, T7.4 and T93 waited for a person)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_block_agent
from bt_durable import healing

FLAGS = {"healing.enabled": True, "healing.model_diagnosis": True, "diagnosis.auto": True,
         "healing.max_per_task": 2, "healing.max_actions": 40}


class Client:
    def __init__(self, decision: dict, round_no: int = 2):
        self.item = {"workflow_id": f"bt:proj:REQ-900:r1:T7.4:k{round_no}", "decision": decision,
                     "state": {"state": "needs_decision"}}
        self.answers = []

    def status(self, run):
        return {"tasks": {"T7.4": self.item}}

    def answer(self, run, task_id, answer, round_no=None):
        self.answers.append((task_id, answer.request_id, answer.action, answer.note, answer.by, round_no))
        return "bt:wf"


def decision(signature: str = "sig-1", request: str = "T7.4:d1") -> dict:
    return {"request_id": request, "task_id": "T7.4", "reason": "the task used its attempts", "limit_hit": "max_attempts",
            "options": ["reverify", "retry", "retry_with_note", "retry_other_route", "stop"],
            "failure": {"failure_class": "implementation", "code": "CHECK_FAILED", "signature": signature,
                        "summary": "checks failed: npm run herramientas:test-checkpoint",
                        "evidence": [{"kind": "output_line", "excerpt": "counter.form: Expected HTTP 200; got 502"}]}}


class DurableHealing(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="bt-healing-"))
        self.rdir = self.root / "proj" / "requirements" / "REQ-900-x"
        (self.rdir / "plan-revisions").mkdir(parents=True)
        plan = self.rdir / "plan-revisions" / "PLAN.r1.json"
        plan.write_text(json.dumps({"tasks": [{"id": "T7.4", "title": "Checkpoint", "subplan_id": "SP-7", "after": ["T7.3"],
                                               "objective": "Counter on a running server", "acceptance_criteria": ["200"],
                                               "verification": [{"value": "npm run herramientas:test-checkpoint",
                                                                 "category": "integration"}]}]}))
        (self.rdir / "RUN.durable-run.json").write_text(json.dumps(
            {"project": "proj", "req": "REQ-900", "revision": 1, "plan_id": "REQ-900", "plan_path": str(plan),
             "plan_sha256": "0" * 64}))
        self.planner = []
        self.patches = [patch("bt_config.get", side_effect=lambda key, default=None: FLAGS.get(key, default)),
                        patch("bt_planning_activity.record")]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def diagnosis(self, **answer):
        def diagnose(project, rdir, request, evidence):
            self.request, self.evidence = request, evidence
            bt_block_agent._write(rdir, request["id"], {"state": "done", **answer})
        return diagnose

    def heal(self, client, diagnose):
        return healing.heal(self.root, client, diagnose=diagnose, start=lambda job: job(),
                            notify=lambda *args: self.planner.append(args))

    def test_a_diagnosed_note_goes_to_that_round_once_per_signature(self):
        client = Client(decision())
        diagnose = self.diagnosis(kind="environment", option="retry_with_note", confidence="alta",
                                  headline="El checkpoint no arranca ai-api",
                                  note="Start services/ai-api with a shared INTERNAL_HMAC_SECRET before next dev.")
        self.assertEqual(self.heal(client, diagnose), ["proj:REQ-900:r1:T7.4:T7.4:d1@k2: diagnosing"])
        self.assertIn("npm run herramientas:test-checkpoint", self.evidence)
        self.assertEqual([o["id"] for o in self.request["options"]],
                         ["reverify", "retry", "retry_with_note", "retry_other_route", "stop"])
        self.assertEqual(self.heal(client, diagnose), ["proj:REQ-900:r1:T7.4:T7.4:d1@k2: retry_with_note"])
        self.assertEqual(client.answers, [("T7.4", "T7.4:d1", "retry_with_note",
                                           "Start services/ai-api with a shared INTERNAL_HMAC_SECRET before next dev.",
                                           "healing", 2)])
        self.assertEqual(self.heal(client, diagnose), [])                    # the same request: answered already
        client.item["decision"] = decision(request="T7.4:d2")                # the same failure again: the owner's
        client.item["workflow_id"] = "bt:proj:REQ-900:r1:T7.4:k3"
        self.assertEqual(self.heal(client, diagnose), [])
        self.assertEqual(len(client.answers), 1)

    def test_a_plan_defect_goes_to_the_planner_and_stays_for_the_owner(self):
        client = Client(decision())
        diagnose = self.diagnosis(kind="plan", option="retry", confidence="alta", headline="T7.4 no depende de SP-6",
                                  origin="The ledger capture is built in SP-6.", steps=["Make T7.4 depend on T96"])
        self.heal(client, diagnose)
        self.assertEqual(self.heal(client, diagnose), ["proj:REQ-900:r1:T7.4:T7.4:d1@k2: sent to the Planner"])
        self.assertEqual(client.answers, [])
        self.assertIn("blames the plan: T7.4 no depende de SP-6", self.planner[0][2])

    def test_an_unsure_or_unoffered_choice_and_a_disabled_healer_leave_the_decision(self):
        client = Client(decision())
        diagnose = self.diagnosis(kind="code", option="retry", confidence="baja", headline="?")
        self.heal(client, diagnose)
        self.assertEqual(self.heal(client, diagnose), ["proj:REQ-900:r1:T7.4:T7.4:d1@k2: left to the owner"])
        self.assertEqual(client.answers, [])
        only = decision(signature="sig-2", request="T7.4:d3")
        only["options"] = ["reverify", "stop"]
        self.assertEqual(self.heal(Client(only), diagnose), [])
        FLAGS["healing.model_diagnosis"] = False
        try:
            self.assertEqual(self.heal(Client(decision(signature="sig-3")), diagnose), [])
        finally:
            FLAGS["healing.model_diagnosis"] = True


if __name__ == "__main__":
    unittest.main()
