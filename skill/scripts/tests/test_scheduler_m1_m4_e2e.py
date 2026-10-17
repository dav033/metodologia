from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import scheduler_chain_support as chain
import scheduler_executor_support as support
from scheduler_executor_support import adapter, core

from bt_scheduler_executor_adapter import run_identity
from bt_scheduler_monitor.metrics import read_metric_snapshots
from bt_scheduler_monitor.queries import events as query_events
from bt_scheduler_monitor.storage_limits import measured_store_bytes


class PlannerM1M2M3M4Flow(support.World):
    def setUp(self):
        super().setUp()
        support.bt_profiles.add("agy-1", "antigravity")
        self.ledger_path = self.tmp / "m2-ledger.sqlite3"

    def test_frozen_plan_routes_executes_normalizes_and_delivers_audit_incident(self):
        tasks = [{"id": "T1", "title": "SCENARIO:monitor provider output", "repo": "app", "after": []}]
        pipeline = chain.Pipeline(self, "chainproj", "REQ-059", tasks, ["README.md"])
        planner_state = pipeline.run()
        self.rdir = pipeline.rdir
        route_table = lambda _task_id: [("claude", "sonnet", "claude-personal", "low")]
        self.m2port = chain.M2Port(self.ledger_path, route_table)
        monitor_path = self.tmp / "disposable-m4.sqlite3"
        verifier = support.Verifier()
        with patch.object(support.bt_profiles, "ROOT", self.root):
            wiring = adapter.wire(
                self.rdir, project="chainproj", assignment=self.m2port, verification=verifier,
                repos=self.repos, default_repository="app", m2_ledger=self.ledger_path,
                config=core.Config(max_parallel_tasks=1, max_attempts=1),
                executor_config=adapter.m3.Config(poll_seconds=0.05, grace_seconds=1.0,
                                                  timeout_seconds=60, heartbeat_seconds=3600),
                monitor_store_path=monitor_path)
        verifier.scheduler = wiring.scheduler
        self.wirings.append(wiring)

        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            wiring.scheduler.step()
            for attempt_id in wiring.executor.ledger.all_ids():
                description = wiring.executor.describe(attempt_id)
                if not description:
                    continue
                fifo = Path(description["artifacts"]["dir"]) / description["stream"]["stream_ref"]
                if fifo.exists():
                    wiring.drain_stream(attempt_id, run_identity(wiring.scheduler))
            attempt_ids = wiring.executor.ledger.all_ids()
            drained = bool(attempt_ids) and all(wiring.stream_adapter.is_terminal_drained(item)
                                                for item in attempt_ids)
            samples = read_metric_snapshots(monitor_path)
            current_status = wiring.scheduler.snapshot().status
            if current_status == "blocked" or current_status == "completed" and drained and samples:
                break
            time.sleep(0.05)

        attempt_ids = wiring.executor.ledger.all_ids()
        self.assertEqual(len(attempt_ids), 1)
        self.assertEqual(wiring.scheduler.snapshot().status, "completed",
                         (wiring.scheduler.snapshot(), [wiring.executor.ledger.get(item) for item in attempt_ids],
                          self.records()))
        self.assertEqual(wiring.scheduler.snapshot().plan_sha256, planner_state["plan_ref"]["sha256"])
        self.assertEqual(self.m2port.decisions["T1"].selected.provider, "claude")
        self.assertEqual(wiring.executor.ledger.get(attempt_ids[0])["route"]["provider"], "claude")
        self.assertEqual([order.task_id for order in verifier.orders], ["T1"])

        stored = query_events(monitor_path, execution_id=attempt_ids[0])["items"]
        event_types = {item["event_type"] for item in stored}
        self.assertIn("usage_reported", event_types)
        self.assertIn("stream_gap", event_types)
        samples = read_metric_snapshots(monitor_path)
        self.assertEqual(len(samples), 1)
        self.assertEqual((samples[0].provider, samples[0].profile_id, samples[0].model,
                          samples[0].name, samples[0].value),
                         ("claude", "claude-personal", "sonnet", "output_tokens", 5))

        before_m4_bytes = measured_store_bytes(monitor_path)
        selected = wiring.monitor.metric_snapshots_for_route(
            provider=samples[0].provider, profile=samples[0].profile_id, model=samples[0].model,
            name=samples[0].name, unit=samples[0].unit, comparability_key=samples[0].comparability_key)
        self.assertEqual(selected, samples)
        self.assertEqual(measured_store_bytes(monitor_path), before_m4_bytes)

        state_before_incident = wiring.scheduler.snapshot()
        report = wiring.monitor.deliver_incidents("e2e-m4", now=time.time())
        state_after_incident = wiring.scheduler.snapshot()
        self.assertEqual((report.claimed, report.applied, report.pending), (1, 1, 0))
        self.assertEqual(state_after_incident.tasks["T1"]["state"], "completed")
        self.assertEqual(state_after_incident.tasks["T1"]["attempts"],
                         state_before_incident.tasks["T1"]["attempts"])
        self.assertEqual(wiring.stream_adapter.queue.buffered_frames, 0)
        self.assertEqual(wiring.stream_adapter.queue.pending_gaps(), ())


if __name__ == "__main__":
    unittest.main()
