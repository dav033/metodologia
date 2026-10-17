from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bt_scheduler_monitor.activity import ActivityState, MAX_ACTIVITY_ITEMS
from bt_scheduler_monitor.contracts import NormalizedEvent, ProcessIdentity
from bt_scheduler_monitor.process_identity import corroborate_process_identity, read_linux_process_identity


NOW = "2026-10-15T16:00:00Z"


def event(kind: str, sequence: int, payload: tuple[tuple[str, object], ...] = (), *, attempt: str = "attempt-1",
          identity: ProcessIdentity | None = None, stream: str = "stdout", offset: int | None = None,
          received_ns: int | None = None, source_at: str | None = None, provider: str = "codex",
          profile: str | None = "opaque-profile", model: str | None = "model-a",
          receive_boot_id: str | None = "boot-a") -> NormalizedEvent:
    return NormalizedEvent(
        schema_version="1.0.0", event_id=f"sha256:{sequence:064x}", source_schema_version="fixture/1",
        normalizer_version="1.0.0", run_id="run-1", plan_revision=1, task_id="task-1", attempt_id=attempt,
        execution_id=f"exec-{attempt}", process_identity=identity or ProcessIdentity("linux", "boot-a", 23, 100),
        provider=provider, profile_id=profile, model=model, event_type=kind,
        source_event_type=kind, source_occurred_at=source_at, received_at=NOW, stream=stream,
        sequence=sequence, offset_bytes=sequence * 8 if offset is None else offset,
        payload=payload, quality="reported", received_monotonic_ns=sequence * 10 if received_ns is None else received_ns,
        host_boot_id=receive_boot_id,
    )


class ActivityStateTests(unittest.TestCase):
    def test_aggregates_activity_without_crossing_attempts(self) -> None:
        first = ActivityState()
        first.add(event("tool_started", 1, (("tool_label", "command"), ("argument_bytes", 4)),
                      source_at="2026-10-15T15:59:00Z"))
        first.add(event("tool_finished", 2, (("tool_label", "command"), ("exit_code", 0)),
                      source_at="2026-10-15T16:00:00Z"))
        first.add(event("usage_reported", 3, (("metric_name", "total_tokens"), ("value", 12), ("unit", "tokens"),
                                              ("source", "provider_reported"), ("sample_count", 1)),
                         source_at="2026-10-15T16:00:01Z"))
        second = ActivityState()
        second.add(event("heartbeat", 1, (("status", "started"),), attempt="attempt-2",
                         identity=ProcessIdentity("linux", "boot-b", 24, 200)))

        view = first.snapshot()
        other = second.snapshot()
        self.assertEqual((view.run_id, view.task_id, view.attempt_id, view.execution_id),
                         ("run-1", "task-1", "attempt-1", "exec-attempt-1"))
        self.assertEqual(view.process_identity, ProcessIdentity("linux", "boot-a", 23, 100))
        self.assertEqual(view.last_source_event_type, "usage_reported")
        self.assertEqual(view.last_received_io_at, NOW)
        self.assertEqual(view.last_tool_label, "command")
        self.assertEqual(view.pending_tools, ())
        self.assertEqual(len(view.metrics), 1)
        self.assertEqual(other.attempt_id, "attempt-2")
        self.assertEqual(other.process_identity.pid, 24)

    def test_missing_activity_and_identity_remain_unknown(self) -> None:
        view = ActivityState().snapshot()
        self.assertEqual(view.display_state, "unknown")
        self.assertIsNone(view.last_source_event_type)
        self.assertIsNone(view.process_identity)
        self.assertEqual(view.stream_integrity, "unknown")

    def test_open_tool_is_pending_and_process_facts_are_separate(self) -> None:
        state = ActivityState()
        state.add(event("tool_started", 1, (("tool_label", "mcp_tool"), ("argument_bytes", 1))))
        identity = ProcessIdentity("linux", "boot-a", 23, 100)
        view = state.snapshot(proc_identity=identity, m3_process_identity=identity, m3_process_state="running",
                              stream_integrity="complete")
        self.assertEqual(view.display_state, "tool_pending")
        self.assertEqual(view.pending_tools, ("mcp_tool",))
        self.assertEqual((view.process_status, view.stream_integrity), ("alive", "complete"))

    def test_process_status_requires_explicit_m3_state_and_corroborated_identity(self) -> None:
        state = ActivityState()
        state.add(event("heartbeat", 1, (("status", "started"),)))
        expected = ProcessIdentity("linux", "boot-a", 23, 100)
        self.assertEqual(state.snapshot(proc_identity=expected).process_status, "unknown")
        self.assertEqual(state.snapshot(m3_process_identity=expected, m3_process_state="running").process_status,
                         "unknown")
        self.assertEqual(state.snapshot(proc_identity=expected, m3_process_identity=expected,
                                        m3_process_state="running").process_status, "alive")
        changed_pid = ProcessIdentity("linux", "boot-a", 24, 100)
        reused = state.snapshot(proc_identity=ProcessIdentity("linux", "boot-a", 23, 101),
                                m3_process_identity=expected, m3_process_state="running")
        disagreement = state.snapshot(proc_identity=expected, m3_process_identity=changed_pid,
                                      m3_process_state="terminal")
        self.assertEqual(reused.identity_corroboration, "pid_reuse")
        self.assertEqual(disagreement.identity_corroboration, "disagreement")
        self.assertEqual(reused.process_status, "unknown")
        self.assertNotEqual(reused.display_state, "process_confirmed_dead")
        confirmed = state.snapshot(m3_process_identity=expected, m3_process_state="terminal")
        self.assertEqual((confirmed.process_status, confirmed.display_state), ("dead", "process_confirmed_dead"))
        contradiction = state.snapshot(proc_identity=expected, m3_process_identity=expected,
                                       m3_process_state="terminal")
        self.assertEqual(contradiction.process_status, "unknown")
        self.assertEqual(contradiction.identity_corroboration, "disagreement")

    def test_cross_stream_offsets_do_not_order_receipt_or_source_event(self) -> None:
        state = ActivityState()
        state.add(event("tool_started", 90, (("tool_label", "stdout_tool"), ("argument_bytes", 0)),
                        stream="stdout", offset=9_000, received_ns=20, source_at="2026-10-15T16:01:00Z"))
        state.add(event("tool_finished", 1, (("tool_label", "stderr_tool"), ("exit_code", 0)),
                        stream="stderr", offset=3, received_ns=30, source_at="2026-10-15T15:59:00Z"))
        view = state.snapshot()
        self.assertEqual(view.last_received_monotonic_ns, 30)
        self.assertEqual(view.last_sequence, 1)
        self.assertEqual(view.last_tool_label, "stderr_tool")
        self.assertEqual(view.last_source_event_type, "tool_started")
        self.assertEqual(view.last_source_at, "2026-10-15T16:01:00Z")

    def test_tool_finish_only_closes_an_earlier_comparable_start(self) -> None:
        before = ActivityState()
        before.add(event("tool_started", 10, (("tool_label", "command"), ("argument_bytes", 0)),
                         source_at="2026-10-15T16:01:00Z"))
        before.add(event("tool_finished", 11, (("tool_label", "command"), ("exit_code", 0)),
                         source_at="2026-10-15T15:59:00Z"))
        self.assertEqual(before.snapshot().pending_tools, ("command",))

        after = ActivityState()
        after.add(event("tool_finished", 20, (("tool_label", "command"), ("exit_code", 0)),
                        source_at="2026-10-15T16:01:00Z"))
        after.add(event("tool_started", 21, (("tool_label", "command"), ("argument_bytes", 0)),
                        source_at="2026-10-15T15:59:00Z"))
        self.assertEqual(after.snapshot().pending_tools, ())

        incomparable = ActivityState()
        incomparable.add(event("tool_started", 30, (("tool_label", "command"), ("argument_bytes", 0))))
        incomparable.add(event("tool_finished", 31, (("tool_label", "command"), ("exit_code", 0))))
        uncertain_view = incomparable.snapshot()
        self.assertEqual(uncertain_view.pending_tools, ("command",))
        self.assertTrue(uncertain_view.pending_tools_uncertain)

    def test_silent_but_live_requires_same_boot_monotonic_clock(self) -> None:
        state = ActivityState()
        state.add(event("heartbeat", 1, (("status", "started"),), received_ns=100))
        identity = ProcessIdentity("linux", "boot-a", 23, 100)
        common = {"proc_identity": identity, "m3_process_identity": identity, "m3_process_state": "running",
                  "monotonic_now_ns": 100 + 300_000_000_000}
        same_boot = state.snapshot(**common, monotonic_boot_id="boot-a")
        self.assertEqual(same_boot.display_state, "silent_but_live")
        self.assertEqual(state.snapshot(**(common | {"monotonic_now_ns": 100 + 299_999_999_999}),
                                        monotonic_boot_id="boot-a").display_state, "active")
        self.assertEqual(state.snapshot(**common, monotonic_boot_id="boot-b").display_state, "active")
        self.assertEqual(state.snapshot(**common).display_state, "active")
        self.assertEqual(state.snapshot(**(common | {"monotonic_now_ns": 99}),
                                        monotonic_boot_id="boot-a").display_state, "active")

        no_event_boot = ActivityState()
        no_event_boot.add(event("heartbeat", 1, (("status", "started"),), receive_boot_id=None))
        self.assertEqual(no_event_boot.snapshot(proc_identity=identity, m3_process_identity=identity,
                                                m3_process_state="running",
                                                monotonic_now_ns=300_000_000_100,
                                                monotonic_boot_id="boot-a").display_state, "active")

    def test_execution_metadata_cannot_change_mid_attempt(self) -> None:
        state = ActivityState()
        state.add(event("heartbeat", 1, (("status", "started"),)))
        for changes in ({"provider": "claude"}, {"profile": None}, {"model": "model-b"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                state.add(event("heartbeat", 2, (("status", "started"),), **changes))

    def test_activity_collections_are_bounded_and_expose_truncation(self) -> None:
        state = ActivityState()
        for sequence in range(1, MAX_ACTIVITY_ITEMS + 20):
            state.add(event("tool_started", sequence, (("tool_label", "command"), ("argument_bytes", 0))))
            usage_sequence = sequence + 10_000
            state.add(event("usage_reported", usage_sequence, (("metric_name", "total_tokens"), ("value", sequence),
                                                                ("unit", "tokens"),
                                                                ("source", "provider_reported"),
                                                                ("sample_count", 1))))
        view = state.snapshot()
        self.assertEqual(len(view.pending_tools), MAX_ACTIVITY_ITEMS)
        self.assertEqual(len(view.metrics), MAX_ACTIVITY_ITEMS)
        self.assertEqual(view.pending_tools_dropped_count, 19)
        self.assertEqual(view.metrics_dropped_count, 19)
        self.assertTrue(view.projection_truncated)

    def test_replayed_event_id_does_not_duplicate_projection(self) -> None:
        state = ActivityState()
        started = event("tool_started", 1, (("tool_label", "command"), ("argument_bytes", 0)))
        state.add(started)
        state.add(started)
        view = state.snapshot()
        self.assertEqual(view.pending_tools, ("command",))
        self.assertEqual(view.pending_tools_dropped_count, 0)


class ProcessIdentityTests(unittest.TestCase):
    def test_reads_linux_identity_from_proc_stat_with_parenthesized_comm(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sys/kernel/random").mkdir(parents=True)
            (root / "sys/kernel/random/boot_id").write_text("boot-a\n")
            proc = root / "23"
            proc.mkdir()
            # comm may contain spaces and closing parentheses; starttime is field 22.
            tail = ["S", "1"] + ["0"] * 17 + ["100"]
            (proc / "stat").write_text(f"23 (worker ) with spaces) {' '.join(tail)}")
            self.assertEqual(read_linux_process_identity(23, root), ProcessIdentity("linux", "boot-a", 23, 100))
            for state in ("Z", "X", "x"):
                (proc / "stat").write_text(f"23 (worker ) with spaces) {state} {' '.join(tail[1:])}")
                self.assertIsNone(read_linux_process_identity(23, root), state)

    def test_pid_reuse_and_disagreement_are_not_matches(self) -> None:
        expected = ProcessIdentity("linux", "boot-a", 23, 100)
        self.assertEqual(corroborate_process_identity(expected, ProcessIdentity("linux", "boot-a", 23, 101)),
                         "pid_reuse")
        self.assertEqual(corroborate_process_identity(expected, ProcessIdentity("linux", "boot-b", 23, 100)),
                         "pid_reuse")
        self.assertEqual(corroborate_process_identity(expected, ProcessIdentity("linux", "boot-a", 24, 100)),
                         "disagreement")

    def test_identity_match_and_unknown_are_explicit(self) -> None:
        expected = ProcessIdentity("linux", "boot-a", 23, 100)
        self.assertEqual(corroborate_process_identity(expected, expected), "match")
        self.assertEqual(corroborate_process_identity(expected, None), "unknown")
        self.assertEqual(corroborate_process_identity(ProcessIdentity("linux", None, 23, None), expected), "unknown")
        self.assertIsNone(read_linux_process_identity(23, Path("/not-a-proc")))


if __name__ == "__main__":
    unittest.main()
