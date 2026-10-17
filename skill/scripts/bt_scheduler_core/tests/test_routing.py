"""Whole-plan route recommendations remain advisory until M1 revalidates and reserves a READY task."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]

import bt_scheduler_core as core
from support import approved, indep, plan_text


def route(model: str, effort: str) -> dict[str, str]:
    return {"schema_version": core.ROUTING_CONTRACT_VERSION, "provider": "claude", "model": model,
            "effort": effort, "route_id": f"claude:{model}:{effort}"}


class M2Port:
    def __init__(self):
        self.routing_request = None
        self.assignment_request = None

    def plan(self, request):
        self.routing_request = request
        return tuple(core.PlannedRoute(task.id, route("sonnet", "xhigh")) for task in request.tasks)

    def propose(self, request):
        self.assignment_request = request
        task = request.ready[0]
        return (core.Assignment(task.id, "route:m2:ready", route_metadata=route("haiku", "low")),)


class IncompleteM2(M2Port):
    def plan(self, request):
        self.routing_request = request
        return ()


class FullPlanRouting(unittest.TestCase):
    def setUp(self):
        tasks = [
            indep("T1", title="Ready task", milestone="M1", complexity="low", risk="low",
                  scope="small_change"),
            indep("T2", after=("T1",), title="Blocked task", milestone="M1", complexity="high", risk="high",
                  scope="large_change"),
            indep("T3", title="Independent task", milestone="M2", complexity="medium", risk="medium",
                  scope="small_change"),
        ]
        text = plan_text(tasks, plan_id="REQ-ROUTING")
        self.plan, _ = approved(text)

    def test_full_dag_is_recorded_then_ready_route_is_revalidated_without_executor(self):
        m2 = M2Port()
        repository = core.InMemoryRepository()
        scheduler = core.SchedulerCore(
            self.plan, repository, ports=core.Ports(assignment=m2, routing=m2),
            config=core.Config(max_parallel_tasks=1), clock=lambda: 100.0,
        )

        before = scheduler.start()
        self.assertEqual([task.id for task in m2.routing_request.tasks], ["T1", "T2", "T3"])
        self.assertEqual([task.milestone_id for task in m2.routing_request.tasks], ["M1", "M1", "M2"])
        self.assertEqual(m2.routing_request.tasks[1].dependencies, ("T1",))
        self.assertEqual(m2.routing_request.tasks[1].meta["complexity"], "high")
        self.assertEqual(before.tasks["T2"]["state"], "pending")
        self.assertTrue(all(before.tasks[task_id]["route_status"] == "recommended"
                            for task_id in ("T1", "T2", "T3")))
        self.assertEqual(scheduler.read(lambda ctx: (ctx.state.schema, ctx.state.routing_complete)), (2, True))

        report = scheduler.step()
        after = scheduler.snapshot()
        self.assertEqual([task.id for task in m2.assignment_request.ready], ["T1", "T3"])
        self.assertEqual(m2.assignment_request.free_slots, 1)
        self.assertEqual(len(report.claimed), 1)
        self.assertEqual(after.tasks["T1"]["route_status"], "assigned")
        self.assertEqual(after.tasks["T1"]["route_metadata"]["model"], "haiku")
        self.assertEqual(after.tasks["T2"]["route_metadata"]["model"], "sonnet")
        self.assertEqual(after.pending_outbox, 1)
        self.assertIsNone(scheduler.ports.execution)

    def test_incomplete_full_plan_map_stops_before_any_task_reservation(self):
        m2 = IncompleteM2()
        scheduler = core.SchedulerCore(self.plan, core.InMemoryRepository(),
                                       ports=core.Ports(assignment=m2, routing=m2), clock=lambda: 100.0)

        with self.assertRaises(core.SchedulerError) as error:
            scheduler.start()

        self.assertEqual(error.exception.code, "ROUTING_INVALID")
        self.assertEqual(scheduler.snapshot().pending_outbox, 0)
        self.assertFalse(scheduler.read(lambda ctx: ctx.state.routing_complete))
        self.assertIsNone(m2.assignment_request)


if __name__ == "__main__":
    unittest.main()
