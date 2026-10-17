from __future__ import annotations

import unittest

from bt_scheduler_monitor.activity import ActivityState
from bt_scheduler_monitor.contracts import NormalizedEvent, ProcessIdentity


def event(*, provider: str, profile: str, identity: ProcessIdentity, run_id: str, task_id: str,
          attempt_id: str, execution_id: str, event_type: str, sequence: int, offset: int,
          received_at: str, source_at: str | None, payload: tuple[tuple[str, object], ...],
          monotonic_ns: int) -> NormalizedEvent:
    return NormalizedEvent(
        schema_version="1.0.0", event_id=f"event:{execution_id}:{sequence}", source_schema_version="fixture/1",
        normalizer_version="1.0.0", run_id=run_id, plan_revision=1, task_id=task_id, attempt_id=attempt_id,
        execution_id=execution_id, process_identity=identity, provider=provider, profile_id=profile,
        model=f"{provider}-model", event_type=event_type, source_event_type=event_type,
        source_occurred_at=source_at, received_at=received_at, stream="stdout", sequence=sequence,
        offset_bytes=offset, payload=payload, quality="reported", received_monotonic_ns=monotonic_ns,
        host_boot_id=identity.host_boot_id,
    )


class ConcurrentActivityIntegrationTests(unittest.TestCase):
    def test_three_attempts_keep_provider_identity_activity_offsets_and_metrics_correlated(self) -> None:
        attempts = (
            ("codex", "profile-codex", ProcessIdentity("linux", "boot-a", 201, 1001),
             "run-a", "task-a", "attempt-a", "exec-a", 11, 1_000, "2026-10-15T16:00:01Z", 17),
            ("claude", "profile-claude", ProcessIdentity("linux", "boot-b", 202, 1002),
             "run-b", "task-b", "attempt-b", "exec-b", 22, 2_000, "2026-10-15T16:00:02Z", 23),
            ("antigravity", "profile-agy", ProcessIdentity("linux", "boot-c", 203, 1003),
             "run-c", "task-c", "attempt-c", "exec-c", 33, 3_000, "2026-10-15T16:00:03Z", 31),
        )
        states: dict[str, ActivityState] = {}

        for provider, profile, identity, run_id, task_id, attempt_id, execution_id, base_offset, monotonic_ns, stamp, value in attempts:
            state = ActivityState()
            state.add(event(
                provider=provider, profile=profile, identity=identity, run_id=run_id, task_id=task_id,
                attempt_id=attempt_id, execution_id=execution_id, event_type="heartbeat", sequence=1,
                offset=base_offset, received_at=stamp, source_at=stamp, payload=(("status", "running"),),
                monotonic_ns=monotonic_ns,
            ))
            metric_stamp = stamp.replace("01Z", "04Z").replace("02Z", "05Z").replace("03Z", "06Z")
            state.add(event(
                provider=provider, profile=profile, identity=identity, run_id=run_id, task_id=task_id,
                attempt_id=attempt_id, execution_id=execution_id, event_type="usage_reported", sequence=2,
                offset=base_offset + 8, received_at=metric_stamp, source_at=metric_stamp,
                payload=(("metric_name", "total_tokens"), ("value", value), ("unit", "tokens"),
                         ("source", "provider_reported"), ("sample_count", 1)),
                monotonic_ns=monotonic_ns + 10,
            ))
            states[execution_id] = state

        for provider, profile, identity, run_id, task_id, attempt_id, execution_id, base_offset, monotonic_ns, stamp, value in attempts:
            with self.subTest(execution_id=execution_id):
                view = states[execution_id].snapshot()
                self.assertEqual((view.run_id, view.task_id, view.attempt_id, view.execution_id),
                                 (run_id, task_id, attempt_id, execution_id))
                self.assertEqual((view.provider, view.profile_id, view.model),
                                 (provider, profile, f"{provider}-model"))
                self.assertEqual(view.process_identity, identity)
                self.assertEqual((view.last_sequence, view.last_offset_bytes), (2, base_offset + 8))
                self.assertEqual(view.last_received_io_at, view.last_source_at)
                self.assertEqual(view.last_source_event_type, "usage_reported")
                self.assertEqual(len(view.metrics), 1)
                self.assertEqual(dict(view.metrics[0].payload)["value"], value)
                self.assertEqual(view.pending_tools, ())
                self.assertIsNone(view.last_tool_label)
                self.assertEqual(view.stream_integrity, "complete")

        unknown = ActivityState().snapshot()
        self.assertIsNone(unknown.provider)
        self.assertIsNone(unknown.profile_id)
        self.assertIsNone(unknown.process_identity)
        self.assertIsNone(unknown.last_offset_bytes)
        self.assertEqual(unknown.stream_integrity, "unknown")


if __name__ == "__main__":
    unittest.main()
