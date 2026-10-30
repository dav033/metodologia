"""A repaired integration must be observed by the next same-snapshot verification."""
from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bt_contracts.execution import AttemptRef, AttemptStatus, RunRef
from bt_contracts.owner import OwnerAnswer
from bt_durable import projection
from bt_durable.execution import workflows as w
from durable_support import git, task, wait_until
from test_durable_e2e import FAST, EngineCase


class Reintegrate(unittest.TestCase):
    def setUp(self):
        self.attempt = AttemptRef(run=RunRef(project="p", req="REQ-900", plan_id="REQ-900", revision=1,
                                           plan_sha256="a" * 64, plan_path=Path("/tmp/PLAN.json")),
                                  task_id="T1", number=1, workflow_id="task")
        self.agent = {"snapshot": {"snapshot_sha": "b" * 40, "base_sha": "c" * 40},
                      "agent": {"status": "completed"}}
        self.verdict = {"status": "PASS", "reason_code": "PASS"}

    def test_a_resolution_is_retried_on_each_verification_but_replay_reuses_its_result(self):
        cache, calls = {}, []
        repaired = False

        def enqueue(queue, key, func, *args):
            self.assertEqual(queue, w.engine.INTEGRATE)
            if key not in cache:
                calls.append((key, args[-1]))
                cache[key] = {"ref": "d" * 40, "conflict": ""} if repaired else {"conflict": "README.md"}
            return cache[key]

        with mock.patch.object(w, "_enqueue", side_effect=enqueue), mock.patch.object(w.DBOS, "patch", return_value=True):
            first = w._evaluate(self.attempt, None, self.agent, self.verdict, w.STANDARD)
            self.assertEqual(first.failure.code, "INTEGRATION_CONFLICT")
            second = w._evaluate(self.attempt, None, self.agent, self.verdict, "owner1")
            self.assertEqual(second.failure.code, "INTEGRATION_CONFLICT")
            repaired = True
            third = w._evaluate(self.attempt, None, self.agent, self.verdict, "owner2")
            self.assertEqual(third.status, AttemptStatus.ACCEPTED)
            self.assertEqual(third.integrated_ref, "d" * 40)
            replay = w._evaluate(self.attempt, None, self.agent, self.verdict, "owner2")
            self.assertEqual(replay, third)
        self.assertEqual(len(calls), 3)
        self.assertTrue(all(snapshot == self.agent["snapshot"] for _, snapshot in calls))

    def test_old_histories_keep_the_recorded_child_id(self):
        with mock.patch.object(w.DBOS, "patch", return_value=False), mock.patch.object(
                w, "_enqueue", return_value={"conflict": "README.md"}) as enqueue:
            w._evaluate(self.attempt, None, self.agent, self.verdict, "owner1")
        self.assertEqual(enqueue.call_args.args[1], f"bt:{self.attempt.attempt_key}:integrate")

    def test_a_failed_verification_never_attempts_integration(self):
        with mock.patch.object(w, "_enqueue") as enqueue:
            result = w._evaluate(self.attempt, None, self.agent, {"status": "FAIL", "digest": "assertion failed"}, "owner1")
        self.assertEqual(result.status, AttemptStatus.REJECTED)
        enqueue.assert_not_called()

    def test_projection_uses_latest_integration_in_either_database_order(self):
        key = self.attempt.attempt_key
        rows = [SimpleNamespace(workflow_id=f"bt:{key}:integrate" + suffix, name="bt.integrate",
                                created_at=created, updated_at=created, status="SUCCESS", input=None,
                                output=output)
                for suffix, created, output in [("", 1, {"conflict": "README.md"}),
                                                (":owner1", 2, {"ref": "d" * 40})]]
        rows.append(SimpleNamespace(workflow_id=f"bt:{key}:agent", name="bt.agent", created_at=0, updated_at=0,
                                    status="SUCCESS", input={"args": [self.attempt.model_dump(mode="json")]}, output={}))
        for order in (rows, rows[::-1]):
            source = SimpleNamespace(list_workflows=lambda order=order, **kwargs: order)
            item = projection._attempts(source, self.attempt.run)["T1"][0]
            self.assertEqual(item["state"], "accepted")


class ReintegrateEndToEnd(EngineCase):
    def test_recorded_resolution_after_two_conflicts_survives_restart_without_another_agent(self):
        os.environ["FAKE_DELAY"] = "4"
        self.addCleanup(os.environ.pop, "FAKE_DELAY", None)
        run = RunRef.model_validate(self.lab.freeze([task("T1")]))
        self.start_engine()
        settings = FAST.model_copy(update={"budget": FAST.budget.model_copy(update={"max_same_signature": 1})})
        self.client.start(run, settings)
        wait_until(lambda: self.lab.launches(), 60, what="the captured task base")
        # Only the laboratory's line moves: another accepted writer adds the same file.
        (self.lab.repo / "out.txt").write_text("earlier accepted value\n")
        (self.lab.repo / "accepted.txt").write_text("preserve this other writer\n")
        git(self.lab.repo, "add", "out.txt", "accepted.txt")
        git(self.lab.repo, "commit", "-qm", "another accepted writer")
        git(self.lab.repo, "update-ref", "refs/bt/line/proj/REQ-900/r1/app", "HEAD")

        def decision(number):
            value = (self.client.status(run)["tasks"].get("T1") or {}).get("decision") or {}
            return value if value.get("request_id") == f"T1:d{number}" else None

        first = wait_until(lambda: decision(1), 120, what="the real integration conflict")
        self.assertEqual(first["failure"]["code"], "INTEGRATION_CONFLICT")
        self.client.answer(run, "T1", OwnerAnswer(request_id="T1:d1", action="reverify", by="solver"))
        wait_until(lambda: decision(2), 120, what="the unresolved conflict's second decision")
        self.kill_engine()
        folder = self.lab.state / "composition" / "resolutions"
        requests = list(folder.glob("*.json"))
        self.assertEqual(len(requests), 1)
        self.assertEqual(json.loads(requests[0].read_text())["path"], "out.txt")
        requests[0].with_suffix(".resolved").write_text("good\n")
        self.start_engine()
        self.client.answer(run, "T1", OwnerAnswer(request_id="T1:d2", action="reverify", by="solver"))

        def observed():
            status = self.client.status(run)
            return status if status["workflow_status"] in ("SUCCESS", "ERROR") or decision(3) else None

        status = wait_until(observed, 120, what="the repaired integration's outcome")
        self.assertEqual(status["summary"]["status"], "completed", status["tasks"])
        self.assertEqual(len(self.lab.launches()), 1)
        tip = git(self.lab.repo, "rev-parse", "refs/bt/line/proj/REQ-900/r1/app")
        self.assertEqual(git(self.lab.repo, "show", f"{tip}:out.txt"), "good")
        self.assertEqual(git(self.lab.repo, "show", f"{tip}:accepted.txt"), "preserve this other writer")
        attempt = AttemptRef(run=run, task_id="T1", number=1, workflow_id="task")
        integrations = [r for r in self.client.workflows(f"bt:{attempt.attempt_key}") if r.name == "bt.integrate"]
        self.assertEqual(len(integrations), 3)
        self.assertTrue(all(r.status == "SUCCESS" for r in integrations))


if __name__ == "__main__":
    unittest.main()
