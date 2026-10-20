from __future__ import annotations

import unittest
from dataclasses import replace

from bt_scheduler_monitor.contracts import NormalizedEvent, ProcessIdentity
from bt_scheduler_monitor.detectors import DetectorConfig, DetectorContext, detect_events
from bt_scheduler_monitor.incidents import IncidentLifecycle, MAX_LIFECYCLE_EVIDENCE


NOW = "2026-10-15T16:00:00Z"
IDENTITY = ProcessIdentity("linux", "boot-a", 23, 100)


def event(kind: str, sequence: int = 1, payload: tuple[tuple[str, object], ...] = (), *, mono: int = 1,
          boot: str = "boot-a", identity: ProcessIdentity = IDENTITY, stream: str = "stdout",
          schema: str = "provider/1") -> NormalizedEvent:
    return NormalizedEvent("1.0.0", f"sha256:{sequence:064x}", schema, "1.0.0", "run-1", 1,
                           "task-1", "attempt-1", "exec-1", identity, "codex", "profile-1", "model-1",
                           kind, kind, NOW, stream, sequence, sequence * 10, payload, "reported",
                           received_monotonic_ns=mono, host_boot_id=boot)


class DetectorTests(unittest.TestCase):
    def test_structured_quota_detected_but_unrelated_text_is_not(self) -> None:
        quota = event("quota_error", payload=(("source_code", "rate_limit"),))
        found = detect_events((quota,), DetectorContext(NOW))
        self.assertEqual([item.detector_id for item in found], ["quota_explicit"])
        self.assertEqual(found[0].type, "quota_error")
        self.assertEqual(detect_events((event("stderr_diagnostic", payload=(("diagnostic_code", "other"),)),),
                                       DetectorContext(NOW, m3_exit_code=1)), ())

    def test_plain_text_on_stderr_is_not_a_stream_gap_incident_but_a_real_gap_is(self) -> None:
        gap = (("cause", "malformed_json"), ("dropped_bytes", 21), ("dropped_frames", 1))
        text_line = event("stream_gap", payload=gap, stream="stderr")
        self.assertEqual(detect_events((text_line,), DetectorContext(NOW)), ())
        scalar = (("cause", "unsupported_event"), ("dropped_bytes", 6), ("dropped_frames", 1))   # a "12345" line
        self.assertEqual(detect_events((event("stream_gap", payload=scalar, stream="stderr"),), DetectorContext(NOW)), ())
        overflow = (("cause", "source_gap"), ("dropped_bytes", 4096), ("dropped_frames", 3))
        self.assertEqual(detect_events((event("stream_gap", payload=overflow, stream="stderr"),), DetectorContext(NOW)), ())
        for stream, cause in (("stdout", "source_gap"), ("stdout", "malformed_json"), ("stdout", "unsupported_event"), ("stderr", "invalid_utf8"),
                              ("stderr", "oversized_line")):
            with self.subTest(stream=stream, cause=cause):
                real = event("stream_gap", payload=(("cause", cause), ("dropped_bytes", 21), ("dropped_frames", 1)),
                             stream=stream)
                found = detect_events((real,), DetectorContext(NOW))
                self.assertEqual([item.detector_id for item in found], ["stream_gap"])

    def test_gaps_of_one_attempt_stream_and_cause_collapse_into_one_incident(self) -> None:
        def gap(first):
            return event("stream_gap", payload=(("cause", "source_gap"), ("first_sequence", first), ("first_offset", first * 10),
                                                ("dropped_bytes", 21), ("dropped_frames", 1)), stream="stdout")
        first, second = (detect_events((gap(n),), DetectorContext(NOW))[0] for n in (1, 5))
        self.assertEqual(first.incident_id, second.incident_id)
        other = event("stream_gap", payload=(("cause", "malformed_event"), ("dropped_bytes", 9), ("dropped_frames", 1)),
                      stream="stdout")
        self.assertNotEqual(detect_events((other,), DetectorContext(NOW))[0].incident_id, first.incident_id)

    def test_structured_errors_without_source_code_use_event_identity(self) -> None:
        for kind, detector in (("quota_error", "quota_explicit"), ("auth_error", "auth_failure"),
                               ("transport_error", "connection_error")):
            with self.subTest(kind=kind):
                source = event(kind, payload=())
                found, = detect_events((source,), DetectorContext(NOW))
                self.assertEqual(found.detector_id, detector)
                self.assertEqual(found.facts, ())
                self.assertEqual(detect_events((source,), DetectorContext(NOW))[0].incident_id,
                                 found.incident_id)

    def test_quota_auth_connection_and_timeout_use_structured_triggers(self) -> None:
        probable = event("stderr_diagnostic", payload=(("diagnostic_code", "quota"), ("byte_count", 8),
                                                        ("digest", "sha256:" + "a" * 64)), stream="stderr")
        self.assertIn("quota_probable", {i.detector_id for i in detect_events(
            (probable,), DetectorContext(NOW, m3_exit_code=1))})
        self.assertEqual(detect_events((probable,), DetectorContext(NOW, m3_exit_code=0)), ())
        auth = event("auth_error", payload=(("source_code", "unauthorized"),))
        self.assertIn("auth_failure", {i.detector_id for i in detect_events((auth,), DetectorContext(NOW))})
        transport = event("transport_error", payload=(("source_code", "econnreset"),))
        self.assertIn("connection_error", {i.detector_id for i in detect_events(
            (transport,), DetectorContext(NOW))})
        timeout = event("timeout", payload=(("deadline_ms", 30_000),))
        self.assertEqual(detect_events((timeout,), DetectorContext(NOW)), ())
        self.assertEqual(detect_events((timeout,), DetectorContext(NOW, authorized_cancel=True)), ())
        m3_timeout = DetectorContext(NOW, m3_process_state="terminal", m3_state_version="1.0.0",
                                     m3_process_identity=IDENTITY, m3_terminal_reason="timeout",
                                     m3_terminal_monotonic_ns=10, m3_terminal_boot_id="boot-a")
        high_timeout, = detect_events((timeout,), m3_timeout)
        self.assertEqual((high_timeout.severity, high_timeout.confidence), ("high", "high"))
        self.assertEqual(detect_events((timeout,), replace(m3_timeout,
            m3_process_identity=ProcessIdentity("linux", "boot-a", 99, 100))), ())
        deadline = DetectorContext(NOW, monotonic_now_ns=30, monotonic_boot_id="boot-a",
                                   deadline_monotonic_ns=30, deadline_boot_id="boot-a",
                                   deadline_version="1.0.0")
        self.assertEqual(detect_events((event("heartbeat"),), deadline)[0].confidence, "medium")

    def test_unexpected_exit_requires_identity_and_active_attempt(self) -> None:
        exited = event("process_exited", payload=(("exit_code", 2),))
        self.assertEqual(detect_events((exited,), DetectorContext(NOW, m1_attempt_state="active")), ())
        observed = DetectorContext(NOW, m1_attempt_state="active", m1_state_version="1.0.0",
                                   m3_process_state="terminal", m3_state_version="1.0.0",
                                   m3_process_identity=IDENTITY)
        incident, = detect_events((exited,), observed)
        self.assertEqual((incident.detector_id, incident.severity, incident.confidence),
                         ("unexpected_exit", "high", "high"))
        cancelled = DetectorContext(NOW, m1_attempt_state="active", m1_state_version="1.0.0",
                                    m3_process_state="terminal", m3_state_version="1.0.0",
                                    m3_process_identity=IDENTITY,
                                    authorized_cancel=True)
        self.assertEqual(detect_events((exited,), cancelled), ())

    def test_missed_heartbeat_requires_matching_monotonic_boot_and_threshold(self) -> None:
        seed = event("heartbeat")
        threshold = 90_000_000_000
        base = dict(observed_at=NOW, monotonic_now_ns=threshold, monotonic_boot_id="boot-a",
                    last_heartbeat_monotonic_ns=0, last_heartbeat_boot_id="boot-a",
                    m3_process_identity=IDENTITY, m3_state_version="1.0.0")
        incident, = detect_events((seed,), DetectorContext(**base))
        self.assertEqual(incident.detector_id, "missed_heartbeat")
        before = DetectorContext(**(base | {"monotonic_now_ns": threshold - 1}))
        self.assertEqual(detect_events((seed,), before), ())
        wrong_boot = DetectorContext(**(base | {"monotonic_boot_id": "boot-b"}))
        self.assertEqual(detect_events((seed,), wrong_boot), ())

    def test_silent_alive_and_provider_silence_need_independent_proofs(self) -> None:
        seed = event("heartbeat", mono=0)
        now = 300_000_000_000
        common = dict(observed_at=NOW, monotonic_now_ns=now, monotonic_boot_id="boot-a",
                      m3_process_state="running", m3_state_version="1.0.0", m3_process_identity=IDENTITY,
                      last_output_monotonic_ns=0, last_output_boot_id="boot-a")
        self.assertIn("silent_but_alive", {i.detector_id for i in detect_events((seed,), DetectorContext(**common))})
        first_quiet, = [i for i in detect_events((seed,), DetectorContext(**common))
                        if i.detector_id == "silent_but_alive"]
        later_output = common | {"monotonic_now_ns": 310_000_000_000,
                                 "last_output_monotonic_ns": 10_000_000_000}
        second_quiet, = [i for i in detect_events((seed,), DetectorContext(**later_output))
                         if i.detector_id == "silent_but_alive"]
        self.assertNotEqual(first_quiet.incident_id, second_quiet.incident_id)
        no_identity = DetectorContext(**(common | {"m3_process_identity": None}))
        self.assertNotIn("silent_but_alive", {i.detector_id for i in detect_events((seed,), no_identity)})
        parser = common | {"last_parser_event_monotonic_ns": 0, "last_parser_event_boot_id": "boot-a",
                          "m3_last_heartbeat_monotonic_ns": now, "m3_last_heartbeat_boot_id": "boot-a",
                          "stream_version": "1.0.0"}
        ids = {i.detector_id for i in detect_events((seed,), DetectorContext(**parser))}
        self.assertIn("provider_stream_silence", ids)
        self.assertNotIn("provider_stream_silence", {i.detector_id for i in detect_events(
            (seed,), DetectorContext(**(parser | {"m3_last_heartbeat_boot_id": "boot-b"})))})
        never_parsed = common | {"stream_started_monotonic_ns": 0, "stream_started_boot_id": "boot-a",
                                "stream_version": "1.0.0", "m3_last_heartbeat_monotonic_ns": now,
                                "m3_last_heartbeat_boot_id": "boot-a"}
        self.assertIn("provider_stream_silence", {i.detector_id for i in detect_events(
            (seed,), DetectorContext(**never_parsed))})
        self.assertNotIn("provider_stream_silence", {i.detector_id for i in detect_events(
            (seed,), DetectorContext(**(never_parsed | {"stream_started_monotonic_ns": None})))})
        self.assertNotIn("provider_stream_silence", {i.detector_id for i in detect_events(
            (seed,), DetectorContext(**(never_parsed | {"stream_version": "invalid"})))})
        self.assertNotIn("silent_but_alive", {i.detector_id for i in detect_events(
            (seed,), DetectorContext(**(common | {"m3_state_version": "invalid"})))})
        invalid_snapshots = DetectorContext(NOW, m1_attempt_state="active", m1_state_version="v1",
                                            m3_process_state="terminal", m3_state_version="1.00",
                                            m3_process_identity=IDENTITY)
        self.assertEqual(detect_events((event("process_exited", payload=(("exit_code", 1),)),),
                                       invalid_snapshots), ())
        invalid_deadline = DetectorContext(NOW, monotonic_now_ns=30, monotonic_boot_id="boot-a",
                                           deadline_monotonic_ns=30, deadline_boot_id="boot-a",
                                           deadline_version="v1")
        self.assertNotIn("timeout", {i.detector_id for i in detect_events((seed,), invalid_deadline)})

    def test_configured_repetitive_activity_and_oversize(self) -> None:
        events = tuple(event("tool_started", i + 1, (("tool_label", "exec"), ("argument_bytes", 0)),
                             mono=i * 1_000_000_000) for i in range(20))
        self.assertIn("repetitive_activity", {i.detector_id for i in detect_events(
            events, DetectorContext(NOW), DetectorConfig(repetitive_count=20))})
        self.assertNotIn("repetitive_activity", {i.detector_id for i in detect_events(
            events[:19], DetectorContext(NOW), DetectorConfig(repetitive_count=20))})
        shuffled_with_replay = tuple(reversed(events)) + (events[0],)
        self.assertIn("repetitive_activity", {i.detector_id for i in detect_events(
            shuffled_with_replay, DetectorContext(NOW), DetectorConfig(repetitive_count=20))})
        interleaved = events[:10] + (event("heartbeat", 50, mono=10_500_000_000),) + events[10:]
        self.assertNotIn("repetitive_activity", {i.detector_id for i in detect_events(
            interleaved, DetectorContext(NOW), DetectorConfig(repetitive_count=20))})
        oversized = detect_events((events[0],), DetectorContext(NOW, stream_frame_bytes=65_537))
        self.assertIn("oversized_output", {i.detector_id for i in oversized})

    def test_pid_reuse_stale_cancel_and_disagreement_thresholds(self) -> None:
        seed = event("message_delta", mono=30_000_000_000, payload=(("message_count", 1), ("byte_count", 2)))
        changed = ProcessIdentity("linux", "boot-a", 23, 101)
        reused = DetectorContext(NOW, proc_identity=changed, m3_process_identity=IDENTITY,
                                 m3_state_version="1.0.0")
        pid_incident, = [i for i in detect_events((seed,), reused) if i.detector_id == "pid_reuse"]
        changed_boot = ProcessIdentity("linux", "boot-b", 23, 102)
        other_reuse = DetectorContext(NOW, proc_identity=changed_boot, m3_process_identity=IDENTITY,
                                      m3_state_version="1.0.0")
        other_pid_incident, = [i for i in detect_events((seed,), other_reuse) if i.detector_id == "pid_reuse"]
        self.assertNotEqual(pid_incident.incident_id, other_pid_incident.incident_id)
        inside_grace = DetectorContext(NOW, monotonic_now_ns=30_000_000_000, monotonic_boot_id="boot-a",
                                authorized_cancel=True, cancel_revision="cancel-1", cancel_monotonic_ns=0,
                                cancel_boot_id="boot-a", m3_process_state="terminal",
                                m3_process_identity=IDENTITY,
                                m3_state_version="1.0.0",
                                m3_terminal_reason="cancelled", m3_terminal_monotonic_ns=28_000_000_000,
                                m3_terminal_boot_id="boot-a")
        self.assertNotIn("stale_post_cancel", {i.detector_id for i in detect_events((seed,), inside_grace)})
        stale_frame = event("message_delta", 2, (("message_count", 1), ("byte_count", 2)), mono=30_000_000_001)
        stale = DetectorContext(NOW, monotonic_now_ns=30_000_000_001, monotonic_boot_id="boot-a",
                                authorized_cancel=True, cancel_revision="cancel-1", cancel_monotonic_ns=0,
                                cancel_boot_id="boot-a", m3_process_state="terminal",
                                m3_process_identity=IDENTITY,
                                m3_state_version="1.0.0",
                                m3_terminal_reason="cancelled", m3_terminal_monotonic_ns=28_000_000_000,
                                m3_terminal_boot_id="boot-a")
        self.assertIn("stale_post_cancel", {i.detector_id for i in detect_events((stale_frame,), stale)})
        wrong_process = replace(stale, m3_process_identity=ProcessIdentity("linux", "boot-a", 99, 100))
        self.assertNotIn("stale_post_cancel", {i.detector_id for i in detect_events((stale_frame,), wrong_process)})
        disagreement = DetectorContext(NOW, monotonic_now_ns=30_000_000_000, monotonic_boot_id="boot-a",
                                       m1_attempt_state="terminal", m1_terminal_monotonic_ns=0,
                                       m1_terminal_boot_id="boot-a", m1_state_version="1.0.0",
                                       m3_state_version="1.0.0", m3_process_state="running",
                                       m3_process_identity=IDENTITY)
        self.assertIn("source_disagreement", {i.detector_id for i in detect_events((seed,), disagreement)})

    def test_lifecycle_deduplicates_and_requires_corresponding_resolution(self) -> None:
        source = event("quota_error", payload=(("source_code", "quota"),))
        incident, = detect_events((source,), DetectorContext(NOW))
        lifecycle = IncidentLifecycle()
        first = lifecycle.observe(incident)
        replayed = lifecycle.observe(incident)
        self.assertEqual(replayed.occurrence_count, 1)
        later = detect_events((event("quota_error", 2, (("source_code", "quota"),)),),
                              DetectorContext("2026-10-15T16:01:00Z"))[0]
        updated = lifecycle.observe(later)
        self.assertEqual(updated.incident_id, first.incident_id)
        self.assertEqual(updated.occurrence_count, 2)
        with self.assertRaises(ValueError):
            lifecycle.resolve(incident.incident_id, "2026-10-15T16:02:00Z", "matching_heartbeat")
        resolved = lifecycle.resolve(incident.incident_id, "2026-10-15T16:02:00Z", "m3_terminal_complete")
        self.assertEqual(resolved.resolution_state, "resolved")

    def test_lifecycle_caps_external_refs_but_counts_new_evidence_and_dedupes_recent_replays(self) -> None:
        source = event("quota_error", payload=(("source_code", "quota"),))
        incident, = detect_events((source,), DetectorContext(NOW))
        lifecycle = IncidentLifecycle()
        lifecycle.observe(incident)
        latest = incident
        for index in range(1, MAX_LIFECYCLE_EVIDENCE + 5):
            latest = replace(incident, evidence_refs=(f"event:{index}",))
            lifecycle.observe(latest)
        full = lifecycle.get(incident.incident_id)
        self.assertIsNotNone(full)
        self.assertEqual(len(full.evidence_refs), MAX_LIFECYCLE_EVIDENCE)
        self.assertEqual(full.occurrence_count, MAX_LIFECYCLE_EVIDENCE + 5)
        replayed = lifecycle.observe(latest)
        self.assertEqual(replayed.occurrence_count, full.occurrence_count)
        self.assertEqual(len(replayed.evidence_refs), MAX_LIFECYCLE_EVIDENCE)
        later = replace(incident, evidence_refs=("event:later",),
                        last_seen_at="2026-10-15T16:01:00Z")
        advanced = lifecycle.observe(later)
        self.assertEqual(advanced.occurrence_count, full.occurrence_count + 1)
        self.assertEqual(advanced.last_seen_at, later.last_seen_at)

    def test_context_rejects_non_boolean_cancel_and_invalid_byte_counts(self) -> None:
        for value in ("false", 0, 1):
            with self.subTest(authorized_cancel=value), self.assertRaises(ValueError):
                DetectorContext(NOW, authorized_cancel=value)
        for field in ("stream_frame_bytes", "normalized_event_bytes", "evidence_bytes"):
            for value in (True, -1, 1.5):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    DetectorContext(NOW, **{field: value})


if __name__ == "__main__":
    unittest.main()
