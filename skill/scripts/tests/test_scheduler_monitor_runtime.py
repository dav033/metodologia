from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bt_scheduler_m4_stream_bridge import M4StreamIngestor
from bt_scheduler_monitor.contracts import ExecutionOutputFrame, ProcessIdentity
from bt_scheduler_monitor.metrics import read_metric_snapshots
from bt_scheduler_monitor.queries import events as query_events
from bt_scheduler_monitor.store import MonitorStore
from bt_scheduler_monitor.stream import BoundedFrameQueue
from bt_scheduler_monitor_adapter import deliver_incident_outbox

NOW = "2026-10-15T20:00:00Z"
IDENTITY = ProcessIdentity("linux", "boot-1", 1234, 5678)


def frame(execution_id: str, sequence: int, offset: int, data: bytes) -> ExecutionOutputFrame:
    return ExecutionOutputFrame("1.0.0", "run-1", 1, "task-1", "attempt-1", execution_id,
                                IDENTITY, "claude", "stdout", sequence, offset, NOW, data,
                                profile_id="claude-test", model="claude-sonnet-test")


class FakeScheduler:
    contract_version = "1.2.0"

    def __init__(self) -> None:
        self.plan = type("Plan", (), {"plan_id": "REQ-TEST", "revision": 1})()
        self.events: list[dict[str, object]] = []

    def ingest(self, event: dict[str, object]):
        self.events.append(event)
        return type("Result", (), {"status": "applied"})()


class SchedulerMonitorRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.store = MonitorStore(Path(self.temp.name) / "monitor.sqlite3")
        self.queue = BoundedFrameQueue()
        self.ingestor = M4StreamIngestor(self.queue, self.store)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_split_jsonl_and_multiple_events_commit_before_ack(self) -> None:
        raw = (b'{"type":"assistant","uuid":"message-1","timestamp":"2026-10-15T20:00:00Z",'
               b'"message":{"model":"claude-sonnet-test","content":[{"type":"text","text":"private body"},'
               b'{"type":"tool_use","name":"Read","input":{"path":"/private/file"}}]}}\n')
        split = raw.index(b'"content"') + 7
        self.assertTrue(self.queue.put(frame("execution-1", 0, 0, raw[:split])))

        self.ingestor.consume("execution-1")

        self.assertEqual(self.queue.buffered_frames, 1)
        self.assertIsNone(self.store.get_cursor("execution-1", "stdout"))
        self.assertTrue(self.queue.put(frame("execution-1", 1, split, raw[split:])))
        self.ingestor.consume("execution-1")

        self.assertEqual(self.queue.buffered_frames, 0)
        stored = query_events(self.store.path, execution_id="execution-1")["items"]
        self.assertEqual([item["event_type"] for item in reversed(stored)], ["message_delta", "tool_started"])
        full_events = [self.store.get_event(item["event_id"]) for item in stored]
        self.assertNotIn("private body", repr(full_events))
        self.assertNotIn("/private/file", repr(full_events))
        cursor = self.store.get_cursor("execution-1", "stdout")
        self.assertEqual((cursor.sequence, cursor.offset_bytes), (1, len(raw)))

    def test_usage_event_and_metric_are_persisted_in_one_cursor_transaction(self) -> None:
        raw = (b'{"type":"result","uuid":"result-1","timestamp":"2026-10-15T20:00:00Z",'
               b'"usage":{"output_tokens":37}}\n')
        self.assertTrue(self.queue.put(frame("execution-2", 0, 0, raw)))

        self.ingestor.consume("execution-2", terminal_drained=True)

        samples = read_metric_snapshots(self.store.path)
        self.assertEqual(len(samples), 1)
        self.assertEqual((samples[0].provider, samples[0].name, samples[0].value, samples[0].unit),
                         ("claude", "output_tokens", 37, "tokens"))
        self.assertEqual(self.store.get_cursor("execution-2", "stdout").offset_bytes, len(raw))
        self.assertEqual(self.queue.buffered_frames, 0)

    def test_storage_failure_keeps_frame_and_retries_without_refeeding(self) -> None:
        raw = b'{"type":"system"}\n'
        self.queue.put(frame("execution-3", 0, 0, raw))
        append_batch = self.store.append_batch
        attempts = 0

        def fail_once(**kwargs):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise OSError("temporary store failure")
            return append_batch(**kwargs)

        self.store.append_batch = fail_once
        with self.assertRaisesRegex(OSError, "temporary store failure"):
            self.ingestor.consume("execution-3")
        self.assertEqual(self.queue.buffered_frames, 1)
        self.assertIsNone(self.store.get_cursor("execution-3", "stdout"))

        self.ingestor.consume("execution-3")

        self.assertEqual(attempts, 2)
        self.assertEqual(self.queue.buffered_frames, 0)
        self.assertEqual(self.store.get_cursor("execution-3", "stdout").offset_bytes, len(raw))
        self.assertEqual(query_events(self.store.path, execution_id="execution-3")["count"], 0)

    def test_source_gap_becomes_durable_event_and_audit_only_m1_outbox(self) -> None:
        self.queue.record_gap("stdout", 0, 0, 5, 1, execution_id="execution-4", host_boot_id="boot-1")
        raw = b'{"type":"system"}\n'
        self.queue.put(frame("execution-4", 1, 5, raw))

        self.ingestor.consume("execution-4", terminal_drained=True)

        stored_events = query_events(self.store.path, execution_id="execution-4")["items"]
        gaps = self.store.list_stream_gaps(execution_id="execution-4")
        self.assertIn("stream_gap", {event["event_type"] for event in stored_events})
        self.assertEqual(len(gaps), 1)
        scheduler = FakeScheduler()
        report = deliver_incident_outbox(self.store, scheduler, "test-worker", now=1)
        self.assertEqual((report.claimed, report.applied, report.pending), (1, 1, 0))
        self.assertEqual(scheduler.events[0]["kind"], "incident_observed")
        self.assertEqual(self.queue.buffered_frames, 0)
        self.assertEqual(self.queue.pending_gaps(), ())


if __name__ == "__main__":
    unittest.main()
