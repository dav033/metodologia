from __future__ import annotations

import unittest
from unittest.mock import patch

from bt_scheduler_monitor.contracts import ExecutionOutputFrame, ProcessIdentity
from bt_scheduler_monitor.stream import BoundedFrameQueue, GapCapacityError


def frame(sequence: int, data: bytes, stream: str = "stdout") -> ExecutionOutputFrame:
    return ExecutionOutputFrame(
        schema_version="1.0.0", run_id="run", plan_revision=1, task_id="task", attempt_id="attempt",
        execution_id="execution", process_identity=ProcessIdentity("linux"), provider="codex", stream=stream,
        sequence=sequence, offset_bytes=sequence * 10 + (1000 if stream == "stderr" else 0),
        received_at="2026-10-15T00:00:00Z", data=data)


class StreamQueueTests(unittest.TestCase):
    def test_queue_enforces_byte_budget_and_reports_rejected_range(self):
        queue = BoundedFrameQueue(max_frames=4, max_bytes=3)
        self.assertTrue(queue.put(frame(0, b"ab")))
        self.assertFalse(queue.put(frame(1, b"cd")))
        self.assertEqual(queue.buffered_bytes, 2)
        gap, = queue.drain_gaps()
        self.assertEqual((gap.stream, gap.sequence, gap.offset_bytes, gap.dropped_bytes), ("stdout", 1, 10, 2))
        self.assertEqual(queue.get().data, b"ab")
        self.assertEqual(queue.buffered_bytes, 0)

    def test_queue_enforces_frame_budget_without_blocking(self):
        queue = BoundedFrameQueue(max_frames=1, max_bytes=10)
        self.assertTrue(queue.put(frame(0, b"a")))
        self.assertFalse(queue.put(frame(1, b"b")))
        self.assertEqual(queue.drain_gaps()[0].reason, "queue_overflow")

    def test_more_than_64_alternating_gaps_coalesce_separately_per_stream(self):
        queue = BoundedFrameQueue(max_frames=1, max_bytes=100)
        self.assertTrue(queue.put(frame(0, b"x")))
        sequences = {"stdout": 0, "stderr": 0}
        for index in range(70):
            stream = "stdout" if index % 2 == 0 else "stderr"
            sequences[stream] += 1
            self.assertFalse(queue.put(frame(sequences[stream], b"x", stream)))

        gaps = queue.drain_gaps()
        self.assertEqual(len(gaps), 66)
        coalesced = [gap for gap in gaps if gap.reason == "queue_overflow_ranges_coalesced"]
        self.assertEqual({gap.stream for gap in coalesced}, {"stdout", "stderr"})
        self.assertEqual(len(coalesced), 2)
        self.assertEqual({gap.dropped_bytes for gap in coalesced}, {3})
        self.assertEqual({gap.dropped_frames for gap in coalesced}, {3})
        by_stream = {gap.stream: gap for gap in coalesced}
        self.assertEqual((by_stream["stdout"].sequence, by_stream["stdout"].offset_bytes,
                          by_stream["stdout"].last_sequence, by_stream["stdout"].last_offset_bytes), (33, 330, 35, 351))
        self.assertEqual((by_stream["stderr"].sequence, by_stream["stderr"].offset_bytes,
                          by_stream["stderr"].last_sequence, by_stream["stderr"].last_offset_bytes), (33, 1330, 35, 1351))
        self.assertTrue(all(gap.coalesced for gap in coalesced))

    def test_record_gap_preserves_disjoint_span_instead_of_inferencing_contiguity(self):
        queue = BoundedFrameQueue()
        queue.record_gap("stdout", 10, 100, 3, 2, last_sequence=14, last_offset_bytes=501,
                         coalesced=True, reason="source_gap_ranges_coalesced")
        gap, = queue.drain_gaps()
        self.assertTrue(gap.coalesced)
        self.assertEqual((gap.sequence, gap.last_sequence, gap.dropped_frames), (10, 14, 2))
        self.assertEqual((gap.offset_bytes, gap.last_offset_bytes, gap.dropped_bytes), (100, 501, 3))

    def test_growing_cumulative_source_gap_emits_only_new_losses_after_drain(self):
        queue = BoundedFrameQueue()
        queue.record_gap("stdout", 10, 100, 3, 2, last_sequence=14, last_offset_bytes=103,
                         coalesced=True, source_id="m3:attempt:stdout")
        initial, = queue.drain_gaps()
        self.assertEqual((initial.dropped_bytes, initial.dropped_frames), (3, 2))

        queue.record_gap("stdout", 10, 100, 7, 4, last_sequence=20, last_offset_bytes=107,
                         coalesced=True, source_id="m3:attempt:stdout")
        delta, = queue.drain_gaps()

        self.assertEqual((delta.dropped_bytes, delta.dropped_frames), (4, 2))
        self.assertEqual((delta.sequence, delta.last_sequence), (15, 20))
        self.assertEqual((delta.offset_bytes, delta.last_offset_bytes), (103, 107))
        self.assertTrue(delta.coalesced)

    def test_source_gap_tracking_has_a_hard_capacity_and_bounded_ids(self):
        queue = BoundedFrameQueue()
        with patch("bt_scheduler_monitor.stream.MAX_TRACKED_SOURCE_GAPS", 1):
            queue.record_gap("stdout", 0, 0, 1, 1, source_id="source-0")
            with self.assertRaisesRegex(GapCapacityError, "tracking limit"):
                queue.record_gap("stdout", 1, 1, 1, 1, source_id="source-1")
        with self.assertRaisesRegex(ValueError, "512 characters"):
            queue.record_gap("stdout", 1, 1, 1, 1, source_id="x" * 513)
        self.assertEqual(len(queue._source_gap_snapshots), 1)

    def test_pending_gap_metadata_has_a_global_cap_and_recovers_after_ack(self):
        queue = BoundedFrameQueue()
        with patch("bt_scheduler_monitor.stream.MAX_PENDING_GAPS", 1):
            queue.record_gap("stdout", 1, 10, 1, 1, execution_id="execution-1")
            first, = queue.pending_gaps()
            with self.assertRaisesRegex(GapCapacityError, "pending stream gap metadata limit"):
                queue.record_gap("stderr", 1, 10, 1, 1, execution_id="execution-2")
            self.assertEqual(queue.pending_gaps(), (first,))
            self.assertTrue(queue.acknowledge_gap(first))
            queue.record_gap("stderr", 1, 10, 1, 1, execution_id="execution-2")
            self.assertEqual(len(queue.pending_gaps()), 1)


if __name__ == "__main__":
    unittest.main()
