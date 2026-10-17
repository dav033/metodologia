"""M3's binary stream frames stay atomic, bounded and explicitly lossy without a reader."""
from __future__ import annotations

import importlib.util
import os
import sqlite3
import struct
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from bt_scheduler_monitor.contracts import (
    ExecutionOutputFrame,
    NormalizedEvent,
    ProcessIdentity,
)
from bt_scheduler_monitor.queries import status
from bt_scheduler_monitor.store import MonitorStore, SourceCursor, StoreError
from bt_scheduler_monitor_adapter import GapCapacityError, persist_frame_event

SHIM = Path(__file__).resolve().parents[1] / "bt_scheduler_executor" / "shim.py"
spec = importlib.util.spec_from_file_location("scheduler_shim", SHIM)
shim = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(shim)
sys.path[:0] = [str(SHIM.parent), str(SHIM.parents[1])]
from bt_scheduler_stream_adapter import M3StreamAdapter


class StreamWireTests(unittest.TestCase):
    def test_summary_gap_tracking_has_a_global_capacity(self):
        with tempfile.TemporaryDirectory() as temp:
            adapter = M3StreamAdapter(temp)
            gap = {"stream": "stdout", "first_sequence": 1, "last_sequence": 1,
                   "first_offset": 8, "last_offset": 16, "dropped_bytes": 8, "dropped_frames": 1}
            with patch("bt_scheduler_stream_adapter.MAX_TRACKED_SUMMARY_GAPS", 1):
                adapter._recover_summary_gaps("execution-a", {"dropped_ranges": [gap]})
                with self.assertRaisesRegex(GapCapacityError, "tracked M3 summary gap limit"):
                    adapter._recover_summary_gaps("execution-b", {"dropped_ranges": [gap]})
            self.assertEqual(len(adapter._summary_gaps), 1)

    def test_gap_metadata_capacity_preserves_fifo_frame_for_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            adapter = M3StreamAdapter(root, max_frames=1, max_bytes=16, max_open_streams=2)
            attempts = {}
            statuses = {}
            for index, execution_id in enumerate(("execution-a", "execution-b")):
                attempt = root / f"attempt-{index}"
                attempt.mkdir()
                os.mkfifo(attempt / "stream.fifo", 0o600)
                attempts[execution_id] = attempt
                statuses[execution_id] = {
                    "execution_id": execution_id, "attempt_id": f"attempt-{index}",
                    "plan_revision": 1, "task_id": f"task-{index}", "stream_ref": "stream.fifo",
                    "provider": "codex", "process_identity": {
                        "platform": "linux", "host_boot_id": "boot", "pid": 100 + index,
                        "start_ticks": 1000 + index}, "dropped_ranges": [],
                }
                self.assertEqual(adapter.drain(statuses[execution_id], attempt, run_id="run"), 0)
            self.addCleanup(adapter.close_all)

            writer = os.open(attempts["execution-a"] / "stream.fifo", os.O_WRONLY | os.O_NONBLOCK)
            try:
                os.write(writer, shim.encode_stream_frame("stdout", 0, 0, b"a"))
                os.write(writer, shim.encode_stream_frame("stdout", 1, 1, b"b"))
            finally:
                os.close(writer)
            with patch("bt_scheduler_monitor.stream.MAX_PENDING_GAPS", 1):
                self.assertEqual(adapter.drain(statuses["execution-a"], attempts["execution-a"], run_id="run"), 2)

                writer = os.open(attempts["execution-b"] / "stream.fifo", os.O_WRONLY | os.O_NONBLOCK)
                try:
                    frame_bytes = shim.encode_stream_frame("stdout", 0, 0, b"c")
                    os.write(writer, frame_bytes)
                finally:
                    os.close(writer)
                with self.assertRaisesRegex(ValueError, "pending stream gap metadata limit"):
                    adapter.drain(statuses["execution-b"], attempts["execution-b"], run_id="run")
                self.assertEqual(bytes(adapter._buffers["execution-b"]), frame_bytes)
                self.assertEqual(len(adapter.queue.pending_gaps()), 1)

            adapter.queue.get()
            adapter.queue.drain_gaps()
            self.assertEqual(adapter.drain(statuses["execution-b"], attempts["execution-b"], run_id="run"), 1)
            self.assertEqual(adapter.queue.peek_frame().execution_id, "execution-b")
            self.assertEqual(adapter._buffers["execution-b"], bytearray())

    def test_storage_pressure_keeps_gap_pending_then_recovers_it_idempotently(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "monitor.sqlite3"
            MonitorStore(path)
            limited = MonitorStore(path, max_store_bytes=910_000)
            connection = sqlite3.connect(path)
            try:
                connection.execute("CREATE TABLE pressure_fixture(payload BLOB)")
                connection.execute("INSERT INTO pressure_fixture VALUES(zeroblob(900000))")
                connection.commit()
                connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            finally:
                connection.close()
            adapter = M3StreamAdapter(temp)
            adapter.queue.record_gap("stdout", 4, 32, 24, 3, last_sequence=6,
                                     last_offset_bytes=56, source_id="m3:execution:stdout:4",
                                     execution_id="execution")

            with self.assertRaisesRegex(StoreError, "storage_pressure"):
                adapter.persist_gaps(limited, recorded_at="2026-10-15T16:00:00Z")
            self.assertEqual(len(adapter.queue.pending_gaps()), 1)
            self.assertEqual(limited.list_stream_gaps(), ())
            self.assertEqual(status(path)["storage"]["state"], "storage_pressure")

            recovered = MonitorStore(path, max_store_bytes=2_000_000)
            self.assertEqual(adapter.persist_gaps(recovered, recorded_at="2026-10-15T16:05:00Z"), 1)
            self.assertEqual(adapter.queue.pending_gaps(), ())
            self.assertEqual(adapter.persist_gaps(recovered, recorded_at="2026-10-15T16:10:00Z"), 0)
            gaps = recovered.list_stream_gaps(execution_id="execution")
            self.assertEqual(len(gaps), 1)
            self.assertEqual((gaps[0]["first_sequence"], gaps[0]["last_sequence"], gaps[0]["dropped_frames"]),
                             (4, 6, 3))
            self.assertIsNone(recovered.get_cursor("execution", "stdout"))

    def test_gap_queue_is_acknowledged_only_after_durable_recovery(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "monitor.sqlite3"
            store = MonitorStore(path)
            adapter = M3StreamAdapter(temp)
            adapter.queue.record_gap("stdout", 4, 32, 24, 3, last_sequence=6,
                                     last_offset_bytes=56, source_id="m3:execution:stdout:4",
                                     execution_id="execution")
            connection = sqlite3.connect(path)
            try:
                connection.execute("CREATE TRIGGER reject_gap BEFORE INSERT ON stream_gaps "
                                   "BEGIN SELECT RAISE(ABORT, 'database or disk is full'); END")
            finally:
                connection.close()
            with self.assertRaises(StoreError):
                adapter.persist_gaps(store, recorded_at="2026-10-15T16:00:00Z")
            self.assertEqual(len(adapter.queue.pending_gaps()), 1)
            self.assertEqual(store.list_stream_gaps(), ())
            connection = sqlite3.connect(path)
            try:
                connection.execute("DROP TRIGGER reject_gap")
            finally:
                connection.close()
            self.assertEqual(adapter.persist_gaps(store, recorded_at="2026-10-15T16:00:00Z"), 1)
            self.assertEqual(adapter.queue.pending_gaps(), ())
            reopened = MonitorStore(path)
            self.assertEqual(len(reopened.list_stream_gaps()), 1)
            self.assertIsNone(reopened.get_cursor("execution", "stdout"))

    def test_durable_consumer_keeps_frame_until_busy_store_recovers_and_commits(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "monitor.sqlite3"
            store = MonitorStore(path)
            connection = sqlite3.connect(path)
            try:
                connection.execute("CREATE TRIGGER reject_event BEFORE INSERT ON normalized_events "
                                   "BEGIN SELECT RAISE(ABORT, 'database or disk is full'); END")
            finally:
                connection.close()
            frame = ExecutionOutputFrame("1.0.0", "run", 1, "task", "attempt", "execution",
                                         ProcessIdentity("linux", "boot", 7, 99), "codex", "stdout", 1, 8,
                                         "2026-10-15T16:00:00Z", b"data", host_boot_id="boot")
            queue = M3StreamAdapter(temp).queue
            self.assertTrue(queue.put(frame))
            event = NormalizedEvent("1.0.0", "event-1", "fixture/1", "1.0.0", "run", 1,
                                    "task", "attempt", "execution", frame.process_identity, "codex", None, None,
                                    "heartbeat", "heartbeat", "2026-10-15T16:00:00Z", "stdout", 1, 8,
                                    (("status", "started"),), "reported", host_boot_id="boot")
            cursor = SourceCursor("execution", "stdout", "boot", 1, 8)
            with self.assertRaises(StoreError):
                persist_frame_event(queue, store, frame, event, cursor)
            self.assertIs(queue.peek_frame(), frame)
            self.assertIsNone(store.get_cursor("execution", "stdout"))
            connection = sqlite3.connect(path)
            try:
                connection.execute("DROP TRIGGER reject_event")
            finally:
                connection.close()
            self.assertTrue(persist_frame_event(queue, store, frame, event, cursor))
            self.assertIsNone(queue.peek_frame())
            self.assertEqual(store.get_cursor("execution", "stdout"), cursor)

    def test_frame_codec_keeps_stream_sequence_offset_and_data(self):
        encoded = shim.encode_stream_frame("stderr", 9, 123, b"diagnostic")
        self.assertLessEqual(len(encoded), 4096)
        self.assertEqual(shim.decode_stream_frame(encoded), ("stderr", 9, 123, b"diagnostic"))

    def test_oversized_payload_is_rejected_before_wire_write(self):
        with self.assertRaises(ValueError):
            shim.encode_stream_frame("stdout", 0, 0, b"x" * 3841)

    def test_missing_reader_creates_bounded_drop_summary(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            import os
            os.mkfifo(directory / "stream.fifo", 0o600)
            with patch.object(shim, "STREAM_READER_STARTUP_GRACE_SECONDS", 0.0):
                tap = shim.StreamTap(directory)
            tap.feed("stdout", b"x" * 5000)
            snapshot = tap._summary()
            snapshot["stdout"]["pending"]["dropped_bytes"] = 0
            self.assertEqual(tap.streams["stdout"]["pending"]["dropped_bytes"], 5000)
            tap.close()
            summary = __import__("json").loads((directory / "stream.json").read_text())
            self.assertEqual(summary["stdout"]["read"], 5000)
            self.assertEqual(summary["stdout"]["sent"], 0)
            self.assertEqual(summary["stdout"]["dropped"], 5000)
            self.assertEqual(summary["stdout"]["ranges"][0]["dropped_frames"], 2)
            status = {"execution_id": "execution", "attempt_id": "attempt", "plan_revision": 1,
                      "task_id": "task", "stream_ref": "stream.fifo", "provider": "codex",
                      "process_identity": {"platform": "linux"},
                      "dropped_ranges": [{**summary["stdout"]["ranges"][0], "stream": "stdout"}]}
            adapter = M3StreamAdapter(directory)
            self.addCleanup(adapter.close, "execution")
            self.assertEqual(adapter.drain(status, directory, run_id="run"), 0)
            self.assertEqual(adapter.drain(status, directory, run_id="run"), 0)
            gap, = adapter.queue.drain_gaps()
            self.assertEqual((gap.stream, gap.dropped_bytes, gap.dropped_frames), ("stdout", 5000, 2))

    def test_stream_writer_waits_briefly_for_the_m4_reader(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            os.mkfifo(directory / "stream.fifo", 0o600)
            tap = shim.StreamTap(directory)
            self.addCleanup(tap.close)
            producer = threading.Thread(target=tap.feed, args=("stdout", b'{"type":"result"}\n'))
            producer.start()
            time.sleep(0.02)
            reader = os.open(directory / "stream.fifo", os.O_RDONLY | os.O_NONBLOCK)
            try:
                producer.join(timeout=1)
                self.assertFalse(producer.is_alive())
                wire = os.read(reader, 4096)
            finally:
                os.close(reader)
            self.assertEqual(tap.streams["stdout"]["sent"], len(b'{"type":"result"}\n'))
            self.assertEqual(tap.streams["stdout"]["dropped"], 0)
            self.assertEqual(shim.decode_stream_frame(wire), ("stdout", 0, 0, b'{"type":"result"}\n'))

    def test_m3_coalesces_disjoint_ranges_with_explicit_true_bounds(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            tap = shim.StreamTap(directory)
            self.addCleanup(tap.close)
            state = tap.streams["stdout"]
            for index in range(70):
                sequence = index * 2
                shim.StreamTap._drop(state, sequence, sequence * 10, 1)
            self.assertEqual(len(state["ranges"]), 64)
            self.assertNotIn("coalesced", state["ranges"][-1])
            gap = state["ranges"][-1]
            self.assertGreater(gap["last_sequence"] - gap["first_sequence"] + 1, gap["dropped_frames"])
            self.assertEqual((gap["first_sequence"], gap["last_sequence"], gap["dropped_frames"]), (126, 138, 7))
            self.assertEqual((gap["first_offset"], gap["last_offset"], gap["dropped_bytes"]), (1260, 1381, 7))

    def test_methodology_reader_converts_fifo_data_and_gap_to_memory_records(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            attempt = root / "attempt"
            attempt.mkdir()
            os.mkfifo(attempt / "stream.fifo", 0o600)
            status = {"execution_id": "execution", "attempt_id": "attempt", "plan_revision": 1,
                      "task_id": "task", "stream_ref": "stream.fifo", "provider": "codex", "profile_id": None,
                      "model": "model", "process_identity": {"platform": "linux", "pid": 7, "start_ticks": 9},
                      "dropped_ranges": [{"stream": "stdout", "first_sequence": 0, "last_sequence": 1,
                                          "first_offset": 0, "last_offset": 6, "dropped_bytes": 6,
                                          "dropped_frames": 2}]}
            adapter = M3StreamAdapter(root)
            self.addCleanup(adapter.close, "execution")
            self.assertEqual(adapter.drain(status, attempt, run_id="run"), 0)
            writer = os.open(attempt / "stream.fifo", os.O_WRONLY | os.O_NONBLOCK)
            try:
                gap = struct.pack("!QQ", 6, 2)
                os.write(writer, shim.encode_stream_frame_id(3, 0, 0, gap))
                os.write(writer, shim.encode_stream_frame("stdout", 2, 6, b"ok"))
            finally:
                os.close(writer)
            self.assertEqual(adapter.drain(status, attempt, run_id="run"), 2)
            output = adapter.queue.get()
            self.assertEqual((output.run_id, output.data), ("run", b"ok"))
            item, = adapter.queue.drain_gaps()
            self.assertEqual((item.sequence, item.last_sequence, item.dropped_bytes, item.dropped_frames), (0, 1, 6, 2))
            self.assertEqual(item.reason, "source_gap")

    def test_reopened_reader_deduplicates_summary_delta_against_complete_fifo_gap(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            attempt = root / "attempt"
            attempt.mkdir()
            os.mkfifo(attempt / "stream.fifo", 0o600)
            status = {"execution_id": "execution", "attempt_id": "attempt", "plan_revision": 1,
                      "task_id": "task", "stream_ref": "stream.fifo", "provider": "codex",
                      "process_identity": {"platform": "linux"}, "dropped_ranges": [
                          {"stream": "stdout", "first_sequence": 0, "last_sequence": 1,
                           "first_offset": 0, "last_offset": 2, "dropped_bytes": 2, "dropped_frames": 2}]}
            adapter = M3StreamAdapter(root)
            self.addCleanup(adapter.close, "execution")
            self.assertEqual(adapter.drain(status, attempt, run_id="run"), 0)
            adapter.close("execution")
            status["dropped_ranges"] = [{"stream": "stdout", "first_sequence": 0, "last_sequence": 2,
                                         "first_offset": 0, "last_offset": 3,
                                         "dropped_bytes": 3, "dropped_frames": 3}]
            self.assertEqual(adapter.drain(status, attempt, run_id="run"), 0)
            writer = os.open(attempt / "stream.fifo", os.O_WRONLY | os.O_NONBLOCK)
            try:
                payload = struct.pack("!QQ", 3, 3)
                os.write(writer, shim.encode_stream_frame_id(3, 0, 0, payload))
            finally:
                os.close(writer)
            self.assertEqual(adapter.drain(status, attempt, run_id="run"), 1)
            gap, = adapter.queue.drain_gaps()
            self.assertEqual((gap.dropped_bytes, gap.dropped_frames, gap.sequence, gap.last_sequence), (3, 3, 0, 2))

    def test_forget_releases_terminal_execution_gap_snapshots(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            attempt = root / "attempt"
            attempt.mkdir()
            os.mkfifo(attempt / "stream.fifo", 0o600)
            status = {"execution_id": "execution", "stream_ref": "stream.fifo", "dropped_ranges": [
                {"stream": "stdout", "first_sequence": 0, "last_sequence": 1,
                 "first_offset": 0, "last_offset": 2, "dropped_bytes": 2, "dropped_frames": 2}]}
            adapter = M3StreamAdapter(root)
            self.addCleanup(adapter.close, "execution")

            with patch("bt_scheduler_monitor.stream.MAX_TRACKED_SOURCE_GAPS", 1):
                self.assertEqual(adapter.drain(status, attempt, run_id="run"), 0)
                self.assertEqual(len(adapter.queue.drain_gaps()), 1)
                self.assertEqual(len(adapter.queue._source_gap_snapshots), 1)
                self.assertEqual(len(adapter._summary_gaps), 1)

                adapter.forget("execution")

                adapter.queue.record_gap("stdout", 0, 0, 1, 1, source_id="m3:next-execution:stdout:0")

            self.assertNotIn("m3:execution:stdout:0", adapter.queue._source_gap_snapshots)
            self.assertIn("m3:next-execution:stdout:0", adapter.queue._source_gap_snapshots)
            self.assertNotIn("m3:execution:stdout:0", adapter.queue._source_gap_indices)
            self.assertEqual(adapter._summary_gaps, {})
            self.assertEqual(adapter._seen_gap_keys, set())
            self.assertEqual(adapter._seen_gap_order, [])

    def test_terminal_status_and_fifo_eof_release_execution_tracking(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            attempt = root / "attempt"
            attempt.mkdir()
            os.mkfifo(attempt / "stream.fifo", 0o600)
            status = {"execution_id": "execution", "state": "finished", "stream_ref": "stream.fifo",
                      "dropped_ranges": [{"stream": "stdout", "first_sequence": 0, "last_sequence": 0,
                                          "first_offset": 0, "last_offset": 1,
                                          "dropped_bytes": 1, "dropped_frames": 1}]}
            adapter = M3StreamAdapter(root)

            self.assertEqual(adapter.drain(status, attempt, run_id="run"), 0)
            gap, = adapter.queue.drain_gaps()

            self.assertEqual(gap.dropped_bytes, 1)
            self.assertEqual(adapter._fds, {})
            self.assertEqual(adapter._buffers, {})
            self.assertEqual(adapter._summary_gaps, {})
            self.assertEqual(adapter.queue._source_gap_snapshots, {})

    def test_rejected_source_gap_does_not_poison_adapter_deduplication(self):
        with tempfile.TemporaryDirectory() as temp:
            adapter = M3StreamAdapter(temp)
            with patch("bt_scheduler_monitor.stream.MAX_TRACKED_SOURCE_GAPS", 1):
                adapter._record_source_gap("execution", "stdout", 0, 0, 1, 1, 0, 1, reason="source_gap")
                with self.assertRaisesRegex(ValueError, "tracking limit"):
                    adapter._record_source_gap("execution", "stdout", 1, 1, 1, 1, 1, 2,
                                               reason="source_gap")
            self.assertEqual(len(adapter._seen_gap_keys), 1)
            self.assertEqual(len(adapter.queue._source_gap_snapshots), 1)
            self.assertEqual(next(iter(adapter._seen_gap_keys))[2], 0)

    def test_open_stream_limit_is_released_by_forget_and_close_all(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            attempts = [root / "attempt-one", root / "attempt-two"]
            for attempt in attempts:
                attempt.mkdir()
                os.mkfifo(attempt / "stream.fifo", 0o600)
            adapter = M3StreamAdapter(root, max_open_streams=1)
            status = lambda execution_id: {"execution_id": execution_id, "stream_ref": "stream.fifo",
                                           "dropped_ranges": []}
            self.addCleanup(adapter.close_all)
            self.assertEqual(adapter.drain(status("one"), attempts[0], run_id="run"), 0)
            with self.assertRaisesRegex(ValueError, "reader limit"):
                adapter.drain(status("two"), attempts[1], run_id="run")
            adapter.forget("one")
            self.assertEqual(adapter.drain(status("two"), attempts[1], run_id="run"), 0)
            fd = adapter._fds["two"]

            adapter.close_all()

            self.assertEqual(adapter._fds, {})
            self.assertEqual(adapter._buffers, {})
            with self.assertRaises(OSError):
                os.fstat(fd)

    def test_coalesced_summary_growth_and_control_preserve_disjoint_bounds_idempotently(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            attempt = root / "attempt"
            attempt.mkdir()
            os.mkfifo(attempt / "stream.fifo", 0o600)
            status = {"execution_id": "execution", "attempt_id": "attempt", "plan_revision": 1,
                      "task_id": "task", "stream_ref": "stream.fifo", "provider": "codex",
                      "process_identity": {"platform": "linux"}, "dropped_ranges": [
                          {"stream": "stdout", "first_sequence": 126, "last_sequence": 128,
                           "first_offset": 1260, "last_offset": 1281, "dropped_bytes": 2,
                           "dropped_frames": 2}]}
            adapter = M3StreamAdapter(root)
            self.addCleanup(adapter.close, "execution")
            self.assertEqual(adapter.drain(status, attempt, run_id="run"), 0)
            status["dropped_ranges"] = [{"stream": "stdout", "first_sequence": 126, "last_sequence": 130,
                                         "first_offset": 1260, "last_offset": 1301, "dropped_bytes": 3,
                                         "dropped_frames": 3}]
            self.assertEqual(adapter.drain(status, attempt, run_id="run"), 0)
            self.assertEqual(adapter.drain(status, attempt, run_id="run"), 0)
            writer = os.open(attempt / "stream.fifo", os.O_WRONLY | os.O_NONBLOCK)
            try:
                control = struct.pack("!QQ", 1, 1)
                os.write(writer, shim.encode_stream_frame_id(3, 130, 1300, control))
            finally:
                os.close(writer)
            self.assertEqual(adapter.drain(status, attempt, run_id="run"), 1)
            gap, = adapter.queue.drain_gaps()
            self.assertTrue(gap.coalesced)
            self.assertEqual((gap.sequence, gap.last_sequence, gap.offset_bytes, gap.last_offset_bytes),
                             (126, 130, 1260, 1301))
            self.assertEqual((gap.dropped_bytes, gap.dropped_frames), (3, 3))

    def test_drain_frame_budget_leaves_remaining_fifo_frames_for_next_call(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            attempt = root / "attempt"
            attempt.mkdir()
            os.mkfifo(attempt / "stream.fifo", 0o600)
            status = {"execution_id": "execution", "attempt_id": "attempt", "plan_revision": 1,
                      "task_id": "task", "stream_ref": "stream.fifo", "provider": "codex", "profile_id": None,
                      "model": "model", "process_identity": {"platform": "linux", "pid": 7, "start_ticks": 9},
                      "dropped_ranges": []}
            adapter = M3StreamAdapter(root)
            self.addCleanup(adapter.close, "execution")
            self.assertEqual(adapter.drain(status, attempt, run_id="run"), 0)
            writer = os.open(attempt / "stream.fifo", os.O_WRONLY | os.O_NONBLOCK)
            try:
                for sequence in range(130):
                    os.write(writer, shim.encode_stream_frame("stdout", sequence, sequence, b"x"))
            finally:
                os.close(writer)
            self.assertEqual(adapter.drain(status, attempt, run_id="run"), 128)
            self.assertEqual(adapter.drain(status, attempt, run_id="run"), 2)
            frames = [adapter.queue.get() for _ in range(130)]
            self.assertEqual([item.sequence for item in frames], list(range(130)))

    def test_drain_rejects_more_than_128_status_ranges_before_caching_them(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            attempt = root / "attempt"
            attempt.mkdir()
            os.mkfifo(attempt / "stream.fifo", 0o600)
            status = {"execution_id": "execution", "dropped_ranges": [
                {"stream": "stdout", "first_sequence": seq, "last_sequence": seq,
                 "first_offset": seq, "last_offset": seq + 1, "dropped_bytes": 1, "dropped_frames": 1}
                for seq in range(129)]}
            adapter = M3StreamAdapter(root)
            with self.assertRaisesRegex(ValueError, "at most 128"):
                adapter.drain(status, attempt, run_id="run")
            self.assertEqual(adapter._summary_gaps, {})


if __name__ == "__main__":
    unittest.main()
