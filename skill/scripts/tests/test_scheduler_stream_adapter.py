"""The scheduler owner closes the M3-to-M4 FIFO reader during shutdown."""
from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import call, patch

import bt_scheduler_m4_wiring as m4_wiring
import scheduler_executor_support as s
from bt_scheduler_executor import shim


class StreamWiringTests(s.World):
    def test_pending_drain_skips_rejected_attempts_without_a_stream_endpoint(self):
        self.approve([s.task("T1", "x")])
        wiring = self.wire("direct:claude/haiku")
        wiring.monitor = SimpleNamespace()
        missing_dir = wiring.executor.attempts_dir / "rejected-before-spawn"
        description = {"state": "rejected", "artifacts": {"dir": str(missing_dir)}}
        wiring.stream_candidates.track("rejected")

        with patch.object(wiring.executor.ledger, "all_ids", side_effect=AssertionError("full history scan")), \
                patch.object(wiring.executor, "describe", return_value=description):
            self.assertEqual(m4_wiring.drain_pending_streams(wiring, s.adapter.run_identity(wiring.scheduler)), 0)
        self.assertFalse(wiring.stream_candidates.pending)

    def test_pending_drain_reports_a_missing_terminal_fifo_for_a_started_attempt(self):
        self.approve([s.task("T1", "x")])
        wiring = self.wire("direct:claude/haiku")
        wiring.monitor = SimpleNamespace()
        attempt_dir = wiring.executor.attempts_dir / "started-without-fifo"
        attempt_dir.mkdir()
        (attempt_dir / "shim.json").write_text("{}", encoding="utf-8")
        description = {"state": "finished", "artifacts": {"dir": str(attempt_dir)},
                       "stream": {"execution_id": "started", "stream_ref": "stream.fifo",
                                  "dropped_ranges": []}}
        wiring.stream_candidates.track("started")

        with patch.object(wiring.executor.ledger, "all_ids", side_effect=AssertionError("full history scan")), \
                patch.object(wiring.executor, "describe", return_value=description), \
                self.assertRaisesRegex(ValueError, "terminal M3 stream endpoint is missing"):
            m4_wiring.drain_pending_streams(wiring, s.adapter.run_identity(wiring.scheduler))

    def test_wiring_drain_rejects_a_different_m1_run_identity(self):
        self.approve([s.task("T1", "x")])
        wiring = self.wire("direct:claude/haiku")

        with (patch.object(wiring.executor, "describe") as describe,
              self.assertRaisesRegex(ValueError, "active M1 run identity")):
            wiring.drain_stream("att-1", "r1-foreign-run")

        describe.assert_not_called()

    def test_wiring_drain_reports_an_unknown_attempt(self):
        self.approve([s.task("T1", "x")])
        wiring = self.wire("direct:claude/haiku")

        with (patch.object(wiring.executor, "describe", return_value=None),
              self.assertRaisesRegex(LookupError, "unknown M3 attempt")):
            wiring.drain_stream("missing", s.adapter.run_identity(wiring.scheduler))

    def test_wiring_close_releases_open_m3_stream_readers(self):
        self.approve([s.task("T1", "x")])
        wiring = self.wire("direct:claude/haiku")
        attempt_dir = wiring.executor.attempts_dir / "stream-test"
        attempt_dir.mkdir()
        os.mkfifo(attempt_dir / "stream.fifo", 0o600)
        status = {"execution_id": "execution", "stream_ref": "stream.fifo", "dropped_ranges": []}

        self.assertEqual(wiring.stream_adapter.drain(status, attempt_dir, run_id="run"), 0)
        fd = wiring.stream_adapter._fds["execution"]

        wiring.close()

        with self.assertRaises(OSError):
            os.fstat(fd)

    def test_terminal_drain_keeps_source_gaps_available_for_m4_persistence(self):
        self.approve([s.task("T1", "x")])
        wiring = self.wire("direct:claude/haiku")
        attempt_dir = wiring.executor.attempts_dir / "stream-terminal"
        attempt_dir.mkdir()
        os.mkfifo(attempt_dir / "stream.fifo", 0o600)
        described = {"state": "finished", "artifacts": {"dir": str(attempt_dir)},
                     "stream": {"execution_id": "execution", "stream_ref": "stream.fifo",
                                "dropped_ranges": [{"stream": "stdout", "first_sequence": 0, "last_sequence": 0,
                                                    "first_offset": 0, "last_offset": 1,
                                                    "dropped_bytes": 1, "dropped_frames": 1}]}}

        with patch.object(wiring.executor, "describe", return_value=described):
            self.assertEqual(wiring.drain_stream("execution", s.adapter.run_identity(wiring.scheduler)), 0)

        gap, = wiring.stream_adapter.queue.pending_gaps()
        self.assertEqual((gap.dropped_bytes, gap.dropped_frames), (1, 1))
        self.assertEqual(wiring.stream_adapter._fds, {})
        self.assertTrue(wiring.stream_adapter.queue._source_gap_snapshots)
        self.assertTrue(wiring.stream_adapter.is_terminal_drained("execution"))

    def test_intermediate_symlink_cannot_redirect_fifo_read_outside_attempt_directory(self):
        self.approve([s.task("T1", "x")])
        wiring = self.wire("direct:claude/haiku")
        attempt_dir = wiring.executor.attempts_dir / "stream-symlink"
        outside = self.root / "outside"
        attempt_dir.mkdir()
        outside.mkdir()
        os.mkfifo(outside / "stream.fifo", 0o600)
        os.symlink(outside, attempt_dir / "nested")
        status = {"execution_id": "escape", "stream_ref": "nested/stream.fifo", "dropped_ranges": []}

        with self.assertRaisesRegex(ValueError, "symlink or non-directory"):
            wiring.stream_adapter.drain(status, attempt_dir, run_id="run")

        self.assertNotIn("escape", wiring.stream_adapter._fds)

    def test_attempt_directory_symlink_cannot_redirect_fifo_read_outside_project_state(self):
        self.approve([s.task("T1", "x")])
        wiring = self.wire("direct:claude/haiku")
        self.addCleanup(wiring.close)
        attempts_root = wiring.stream_adapter.project_state
        attempt_dir = attempts_root / "attempt-race"
        outside = self.root / "outside-attempt"
        attempt_dir.mkdir()
        outside.mkdir()
        os.mkfifo(outside / "stream.fifo", 0o600)
        os.rename(attempt_dir, attempts_root / "attempt-race-real")
        os.symlink(outside, attempt_dir)

        with self.assertRaisesRegex(ValueError, "symlink or non-directory"):
            wiring.stream_adapter._open_fifo(attempts_root, ("attempt-race",), ("stream.fifo",))

    def test_missing_fifo_retries_while_active_but_fails_when_terminal(self):
        self.approve([s.task("T1", "x")])
        wiring = self.wire("direct:claude/haiku")
        attempt_dir = wiring.executor.attempts_dir / "stream-not-ready"
        attempt_dir.mkdir()
        status = {"execution_id": "waiting", "state": "running", "stream_ref": "stream.fifo",
                  "dropped_ranges": []}

        self.assertEqual(wiring.stream_adapter.drain(status, attempt_dir, run_id="run"), 0)
        status["state"] = "finished"
        with self.assertRaisesRegex(ValueError, "terminal M3 stream endpoint is missing"):
            wiring.stream_adapter.drain(status, attempt_dir, run_id="run")

    def test_pending_drain_keeps_open_fifo_reader_slots_bounded(self):
        self.approve([s.task("T1", "x")])
        wiring = self.wire("direct:claude/haiku")
        self.addCleanup(wiring.close)
        wiring.stream_adapter._max_open_streams = 1
        wiring.monitor = SimpleNamespace(consume=lambda *_args: 0)
        descriptions = {}
        for attempt_id in ("first", "second"):
            attempt_dir = wiring.executor.attempts_dir / attempt_id
            attempt_dir.mkdir()
            os.mkfifo(attempt_dir / "stream.fifo", 0o600)
            descriptions[attempt_id] = {
                "state": "running", "artifacts": {"dir": str(attempt_dir)},
                "stream": {"execution_id": attempt_id, "stream_ref": "stream.fifo", "dropped_ranges": []},
            }
        for attempt_id in descriptions:
            wiring.stream_candidates.track(attempt_id)

        with patch.object(wiring.executor.ledger, "all_ids", side_effect=AssertionError("full history scan")), \
                patch.object(wiring.executor, "describe", side_effect=descriptions.__getitem__):
            m4_wiring.drain_pending_streams(wiring, s.adapter.run_identity(wiring.scheduler))

        self.assertEqual(set(wiring.stream_adapter._fds), {"first"})
        self.assertTrue(wiring.stream_adapter.can_open_reader("first"))
        self.assertFalse(wiring.stream_adapter.can_open_reader("second"))

    def test_pending_drain_reuses_one_description_per_tracked_attempt(self):
        self.approve([s.task("T1", "x")])
        wiring = self.wire("direct:claude/haiku")
        wiring.monitor = SimpleNamespace()
        description = {"state": "running", "artifacts": {"dir": str(wiring.executor.attempts_dir)},
                       "stream": {"execution_id": "tracked", "stream_ref": "stream.fifo",
                                  "dropped_ranges": []}}

        with (patch.object(wiring.executor.ledger, "all_ids", side_effect=AssertionError("full history scan")),
              patch.object(wiring.executor.ledger, "ids_in_states", return_value=["tracked"]) as active_ids,
              patch.object(wiring.executor, "describe", return_value=description) as describe,
              patch.object(wiring.stream_adapter, "can_open_reader", return_value=True),
              patch.object(wiring, "drain_stream", return_value=0) as drain):
            m4_wiring.drain_pending_streams(wiring, s.adapter.run_identity(wiring.scheduler))

        active_ids.assert_called_once_with(m4_wiring.M3_LIVE_STATES)
        describe.assert_called_once_with("tracked")
        drain.assert_called_once_with("tracked", s.adapter.run_identity(wiring.scheduler), description=description)
        self.assertEqual(wiring.stream_candidates.pending, {"tracked"})

    def test_resume_seeds_older_terminal_attempt_while_a_new_retry_is_live(self):
        self.approve([s.task("T1", "x")])
        wiring = self.wire("direct:claude/haiku")
        self.addCleanup(wiring.close)
        wiring.monitor = SimpleNamespace(consume=lambda *_args: 0)
        old_dir = wiring.executor.attempts_dir / "older-terminal"
        old_dir.mkdir()
        os.mkfifo(old_dir / "stream.fifo", 0o600)
        retry_dir = wiring.executor.attempts_dir / "newer-live"
        retry_dir.mkdir()
        descriptions = {
            "older-terminal": {
                "state": "finished", "artifacts": {"dir": str(old_dir)},
                "stream": {"execution_id": "older-terminal", "stream_ref": "stream.fifo", "dropped_ranges": []},
            },
            "newer-live": {
                "state": "running", "artifacts": {"dir": str(retry_dir)},
                "stream": {"execution_id": "newer-live", "stream_ref": "stream.fifo", "dropped_ranges": []},
            },
        }

        def ids_in_states(states):
            if states == m4_wiring.M3_TERMINAL_STATES:
                return ["older-terminal"]
            if states == m4_wiring.M3_LIVE_STATES:
                return ["newer-live"]
            return []

        with (patch.object(wiring.executor.ledger, "ids_in_states", side_effect=ids_in_states),
              patch.object(wiring.executor, "describe", side_effect=descriptions.__getitem__)):
            self.assertEqual(m4_wiring.seed_terminal_streams(wiring), 1)
            m4_wiring.drain_pending_streams(wiring, s.adapter.run_identity(wiring.scheduler))

        self.assertNotIn("older-terminal", wiring.stream_candidates.pending)
        self.assertIn("newer-live", wiring.stream_candidates.pending)
        self.assertIn("older-terminal", wiring.stream_adapter._terminal_drained)

    def test_terminal_output_over_frame_budget_is_requeued_until_eof(self):
        self.approve([s.task("T1", "x")])
        wiring = self.wire("direct:claude/haiku")
        self.addCleanup(wiring.close)
        consumed = []
        wiring.monitor = SimpleNamespace(consume=lambda _execution_id, stream_adapter: consumed.extend(
            stream_adapter.queue.get() for _ in stream_adapter.queue.pending_frames()))
        attempt_id = "large-terminal"
        execution_id = attempt_id
        attempt_dir = wiring.executor.attempts_dir / attempt_id
        attempt_dir.mkdir()
        os.mkfifo(attempt_dir / "stream.fifo", 0o600)
        stream_status = {
            "execution_id": execution_id, "attempt_id": attempt_id, "plan_revision": 1,
            "task_id": "T1", "provider": "codex", "profile_id": None, "model": "test",
            "process_identity": {"platform": "linux", "pid": 7, "start_ticks": 9},
            "stream_ref": "stream.fifo", "dropped_ranges": [], "state": "running",
        }
        run_id = s.adapter.run_identity(wiring.scheduler)
        wiring.stream_adapter.drain(stream_status, attempt_dir, run_id=run_id, preserve_for_consumer=True)
        writer = os.open(attempt_dir / "stream.fifo", os.O_WRONLY | os.O_NONBLOCK)
        try:
            for sequence in range(130):
                os.write(writer, shim.encode_stream_frame("stdout", sequence, sequence, b"x"))
        finally:
            os.close(writer)
        wiring.stream_candidates.track(attempt_id)
        description = {"state": "finished", "artifacts": {"dir": str(attempt_dir)},
                       "stream": stream_status}

        with patch.object(wiring.executor, "describe", return_value=description):
            self.assertEqual(m4_wiring.drain_pending_streams(wiring, run_id), 128)
            self.assertIn(attempt_id, wiring.stream_candidates.pending)
            self.assertEqual(m4_wiring.drain_pending_streams(wiring, run_id), 2)

        self.assertFalse(wiring.stream_candidates.pending)
        self.assertTrue(wiring.stream_adapter.is_terminal_drained(execution_id))
        self.assertEqual([frame.sequence for frame in consumed], list(range(130)))

    def test_large_terminal_backlog_is_bounded_and_active_stream_has_priority(self):
        self.approve([s.task("T1", "x")])
        wiring = self.wire("direct:claude/haiku")
        self.addCleanup(wiring.close)
        wiring.monitor = SimpleNamespace()
        for index in range(10_000):
            wiring.stream_candidates.track(f"terminal-{index:05d}")
        active_description = {
            "state": "running", "artifacts": {"dir": str(wiring.executor.attempts_dir)},
            "stream": {"execution_id": "active", "stream_ref": "stream.fifo", "dropped_ranges": []},
        }

        def describe(attempt_id):
            return active_description if attempt_id == "active" else {
                "state": "rejected", "artifacts": {"dir": str(wiring.executor.attempts_dir)}}

        run_id = s.adapter.run_identity(wiring.scheduler)
        with (patch.object(wiring.executor.ledger, "ids_in_states", return_value=["active"]),
              patch.object(wiring.executor, "describe", side_effect=describe) as described,
              patch.object(wiring.stream_adapter, "can_open_reader", side_effect=lambda attempt: attempt == "active"),
              patch.object(wiring, "drain_stream", return_value=0)):
            m4_wiring.drain_pending_streams(wiring, run_id)
            self.assertEqual(described.call_args_list, [call("active")])

        with (patch.object(wiring.executor.ledger, "ids_in_states", return_value=["active"]),
              patch.object(wiring.executor, "describe", side_effect=describe) as described,
              patch.object(wiring.stream_adapter, "can_open_reader", return_value=True),
              patch.object(wiring, "drain_stream", return_value=0)):
            m4_wiring.drain_pending_streams(wiring, run_id)

        self.assertEqual(described.call_count, m4_wiring.MAX_TERMINAL_STREAMS_PER_POLL + 1)
        self.assertEqual(described.call_args_list[0], call("active"))
        self.assertEqual(len(wiring.stream_candidates.pending), 10_000 - m4_wiring.MAX_TERMINAL_STREAMS_PER_POLL + 1)

    def test_terminal_gaps_are_forgotten_only_after_monitor_consumes_them(self):
        self.approve([s.task("T1", "x")])
        wiring = self.wire("direct:claude/haiku")
        attempt_dir = wiring.executor.attempts_dir / "stream-consume"
        attempt_dir.mkdir()
        os.mkfifo(attempt_dir / "stream.fifo", 0o600)
        described = {"state": "finished", "artifacts": {"dir": str(attempt_dir)},
                     "stream": {"execution_id": "execution", "stream_ref": "stream.fifo",
                                "dropped_ranges": [{"stream": "stdout", "first_sequence": 0,
                                                    "last_sequence": 0, "first_offset": 0, "last_offset": 1,
                                                    "dropped_bytes": 1, "dropped_frames": 1}]}}
        observed = []

        def consume(execution_id, stream_adapter):
            self.assertEqual(execution_id, "execution")
            observed.extend(stream_adapter.queue.pending_gaps())
            stream_adapter.queue.drain_gaps()

        wiring.monitor = type("Monitor", (), {"consume": staticmethod(consume)})()
        with patch.object(wiring.executor, "describe", return_value=described):
            wiring.drain_stream("execution", s.adapter.run_identity(wiring.scheduler))

        self.assertEqual(len(observed), 1)
        self.assertTrue(wiring.stream_adapter.is_terminal_drained("execution"))
        self.assertFalse(wiring.stream_adapter.queue.pending_gaps())
        self.assertFalse(wiring.stream_adapter.queue._source_gap_snapshots)


if __name__ == "__main__":
    import unittest

    unittest.main()
