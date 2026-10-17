from __future__ import annotations

import unittest
from unittest.mock import patch

from bt_scheduler_monitor import (
    DroppedRange,
    ExecutionOutputFrame,
    Incident,
    MAX_UNKNOWN_DIGEST_INPUT_BYTES,
    MAX_UNKNOWN_FIELDS,
    M3StreamSummary,
    MetricSample,
    NormalizedEvent,
    ProcessIdentity,
)
from bt_scheduler_monitor import serialization

NOW = "2026-10-15T16:00:00Z"
IDENTITY = ProcessIdentity("linux", "boot-1", 1234, 5678)


class ContractTests(unittest.TestCase):
    def frame(self, **changes):
        values = dict(
            schema_version="1.0.0", run_id="run-1", plan_revision=3, task_id="T4", attempt_id="attempt-1",
            execution_id="execution-1", process_identity=IDENTITY, provider="codex", stream="stdout",
            sequence=1, offset_bytes=0, received_at=NOW, data=b"{}",
        )
        values.update(changes)
        return ExecutionOutputFrame(**values)

    def event(self, **changes):
        values = dict(
            schema_version="1.0.0", event_id="sha256:abc", source_schema_version="codex-v1",
            normalizer_version="1.0.0", run_id="run-1", plan_revision=3, task_id="T4",
            attempt_id="attempt-1", execution_id="execution-1", process_identity=IDENTITY, provider="codex",
            profile_id=None, model=None, event_type="tool_started", source_event_type="item.started",
            received_at=NOW, stream="stdout", sequence=1, offset_bytes=0, payload=(("tool_label", "exec"),),
            quality="reported",
        )
        values.update(changes)
        return NormalizedEvent(**values)

    def incident(self, **changes):
        values = dict(
            schema_version="1.0.0", incident_id="sha256:incident", run_id="run-1", task_id="T4",
            attempt_id="attempt-1", execution_id="execution-1", detector_id="quota_explicit", type="quota_error",
            severity="high", confidence="high", first_seen_at=NOW, last_seen_at=NOW, occurrence_count=1,
            facts=(("source_code", "quota"),), evidence_refs=("event:sha256:abc",), resolution_state="open",
            process_identity=IDENTITY,
        )
        values.update(changes)
        return Incident(**values)

    def test_stream_frame_enforces_version_identity_and_size(self):
        self.assertEqual(self.frame().data, b"{}")
        wire = self.frame().to_dict()
        self.assertEqual(ExecutionOutputFrame.from_dict(wire), self.frame())
        self.assertEqual(len(self.frame(data=b"x" * 3840).to_dict()["data"]), 5120)
        with self.assertRaises(ValueError):
            self.frame(unknown_field_count=4097, unknown_field_digest="sha256:" + "a" * 64)
        oversized = dict(wire, data="A" * 5124)
        with self.assertRaises(ValueError):
            ExecutionOutputFrame.from_dict(oversized)
        for revision in (0, True):
            with self.assertRaises(ValueError):
                self.frame(plan_revision=revision)
        for changes in ({"schema_version": "2.0.0"}, {"plan_revision": True}, {"sequence": -1},
                        {"received_at": "2026-10-15T11:00:00-05:00"}, {"data": "raw"},
                        {"data": b"x" * 3841}, {"provider": "mystery"}, {"run_id": "invalid-\ud800"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.frame(**changes)

    def test_m3_summary_contains_bounded_drops_without_output(self):
        drop = DroppedRange("stderr", 2, 3, 100, 200, 100, 2)
        summary = M3StreamSummary(
            "1.0.0", "execution-1", IDENTITY, "codex", 200, 100, 100, 0, 0, 0,
            stdout_last_sequence=3, stdout_last_offset=200, dropped_ranges=(drop,), stream_ref="attempt/stream.fifo",
        )
        self.assertEqual(summary.dropped_ranges, (drop,))
        self.assertEqual(M3StreamSummary.from_dict(summary.to_dict()), summary)
        self.assertEqual(DroppedRange.from_dict(drop.to_dict()).stream, "stderr")
        with self.assertRaises(ValueError):
            M3StreamSummary("1.0.0", "execution-1", IDENTITY, "codex", 0, 0, 0, 0, 0, 0,
                            stream_ref="../outside")

    def test_normalized_event_has_optional_unknowns_and_rejects_raw_payload(self):
        event = self.event(profile_id=None, model=None, source_event_id=None, source_occurred_at=None)
        self.assertIsNone(event.model)
        self.assertEqual(NormalizedEvent.from_dict(event.to_dict()), event)
        source_time = "2026-10-15T11:00:00-05:00"
        source_event = self.event(source_occurred_at=source_time)
        self.assertEqual(source_event.source_occurred_at, source_time)
        self.assertEqual(NormalizedEvent.from_dict(source_event.to_dict()), source_event)
        with self.assertRaises(ValueError):
            self.event(source_occurred_at="not-a-timestamp")
        with self.assertRaises(ValueError):
            self.event(schema_version="2.0.0")
        self.assertEqual(self.event(schema_version="1.2.0").schema_version, "1.2.0")
        with self.assertRaises(ValueError):
            self.event(received_at="2026-10-15T11:00:00-05:00")
        with self.assertRaises(ValueError):
            self.event(payload=(("body", "unredacted provider text"),))
        with self.assertRaises(ValueError):
            self.event(payload=(("tool_label", {"arbitrary": "provider object"}),))
        with self.assertRaises(ValueError):
            self.event(payload=(("argument_digest", "x" * 16_000),))
        external = self.event().to_dict()
        external["payload"] = {"tool_label": "exec", "private_secret": "must not survive"}
        external["private_secret"] = "root secret must not survive"
        clean = NormalizedEvent.from_dict(external)
        self.assertEqual(dict(clean.payload), {"tool_label": "exec"})
        self.assertEqual(clean.unknown_field_count, 2)
        self.assertRegex(clean.unknown_field_digest, r"^sha256:[0-9a-f]{64}$")
        self.assertNotIn("private_secret", str(clean.to_dict()))
        self.assertEqual(NormalizedEvent.from_dict(clean.to_dict()), clean)
        with self.assertRaises(ValueError):
            self.event(payload=(("tool_label", ("nested",)),))
        with self.assertRaises(ValueError):
            NormalizedEvent.from_dict({"schema_version": "1.0.0"})
        external["private_secret"] = "must also not survive"
        clean_with_unknown_envelope = NormalizedEvent.from_dict(external)
        self.assertEqual(clean_with_unknown_envelope.unknown_field_count, 2)
        self.assertNotIn("private_secret", str(clean_with_unknown_envelope.to_dict()))
        self.assertEqual(NormalizedEvent.from_dict(clean_with_unknown_envelope.to_dict()), clean_with_unknown_envelope)
        with self.assertRaises(ValueError):
            self.event(payload=(("tool_label", "/tmp/file"),))
        with self.assertRaises(ValueError):
            self.event(payload=(("tool_label", 8),))
        with self.assertRaises(ValueError):
            self.event(event_type="checkpoint_written", payload=(("checkpoint_ref", "/tmp/file"),))
        with self.assertRaises(ValueError):
            self.event(event_type="quota_error", payload=(("source_code", "raw provider text"),))
        with self.assertRaises(ValueError):
            self.event(event_type="process_exited", payload=(("exit_code", True),))
        with self.assertRaises(ValueError):
            self.event(payload=(("argument_bytes", True),))
        with self.assertRaises(ValueError):
            self.event(event_type="process_exited", payload=(("signal", 65),))

    def test_incident_enum_resolution_and_evidence_bounds(self):
        self.assertEqual(self.incident().resolution_state, "open")
        self.assertEqual(self.incident(resolution_state="resolved", resolved_at=NOW).resolved_at, NOW)
        self.assertEqual(Incident.from_dict(self.incident().to_dict()), self.incident())
        for changes in ({"severity": "urgent"}, {"confidence": "certain"}, {"type": "made_up"},
                        {"resolution_state": "resolved"}, {"resolved_at": NOW},
                        {"occurrence_count": True}, {"facts": (("excerpt", "x" * 5000),)},
                        {"last_seen_at": "2026-10-15T15:59:00Z"},
                        {"facts": (("source_code", {"raw": "object"}),)},
                        {"facts": (("source_code", "raw provider text"),)},
                        {"facts": (("tool_label", "/tmp/file"),)},
                        {"facts": (("process_exit", True),)},
                        {"facts": (("process_exit", 256),)},
                        {"evidence_refs": ("x" * 128,) * 257},
                        {"evidence_refs": ("x" * 128,) * 129}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.incident(**changes)

    def test_metric_provenance_and_numbers_are_validated(self):
        metric = MetricSample("1.0.0", "sha256:m", "codex", "output_tokens", 128, "tokens",
                              "provider_reported", NOW, "reported", 1,
                              "codex/profile/unknown-model/output_tokens")
        self.assertEqual(metric.value, 128)
        self.assertEqual(MetricSample.from_dict(metric.to_dict()), metric)
        for value in (True, "128", float("nan")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                MetricSample("1.0.0", "m", "codex", "output_tokens", value, "tokens",
                             "provider_reported", NOW, "reported", 1, "key")
        with self.assertRaises(ValueError):
            MetricSample("1.0.0", "m", "codex", "output_tokens", None, "tokens",
                         "provider_reported", NOW, "reported", True, "key")
        for quality, count in (("reported", 0), ("unknown", 1), ("unavailable", 1)):
            with self.subTest(quality=quality, count=count), self.assertRaises(ValueError):
                MetricSample("1.0.0", "m", "codex", "output_tokens", None, "tokens",
                             "provider_reported", NOW, quality, count, "key")
        for value in (-1, float("inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                MetricSample("1.0.0", "m", "codex", "output_tokens", value, "tokens",
                             "provider_reported", NOW, "reported", 1, "key")
        missing = MetricSample("1.0.0", "m", "codex", "output_tokens", None, "tokens",
                               "provider_reported", NOW, "unknown", 0, "key")
        self.assertIsNone(missing.value)

    def test_every_codec_digests_unknown_names_without_retaining_values(self):
        identity_data = IDENTITY.to_dict() | {"private_identity": "identity secret"}
        identity = ProcessIdentity.from_dict(identity_data)
        self.assertEqual(identity.unknown_field_count, 1)
        self.assertNotIn("identity secret", str(identity.to_dict()))
        self.assertEqual(ProcessIdentity.from_dict(identity.to_dict()), identity)

        frame_data = self.frame().to_dict() | {"private_frame": "frame secret", "process_identity": identity_data}
        frame = ExecutionOutputFrame.from_dict(frame_data)
        self.assertEqual((frame.unknown_field_count, frame.process_identity.unknown_field_count), (1, 1))
        self.assertNotIn("frame secret", str(frame.to_dict()))
        self.assertEqual(ExecutionOutputFrame.from_dict(frame.to_dict()), frame)

        range_data = DroppedRange("stderr", 1, 1, 0, 3, 3, 1).to_dict() | {"private_range": "range secret"}
        dropped = DroppedRange.from_dict(range_data)
        self.assertEqual(dropped.unknown_field_count, 1)
        self.assertNotIn("range secret", str(dropped.to_dict()))
        self.assertEqual(DroppedRange.from_dict(dropped.to_dict()), dropped)

        summary_data = M3StreamSummary(
            "1.0.0", "execution-1", IDENTITY, "codex", 1, 1, 0, 0, 0, 0,
            dropped_ranges=(DroppedRange("stderr", 1, 1, 0, 3, 3, 1),),
        ).to_dict()
        summary_data["private_summary"] = "summary secret"
        summary_data["process_identity"] = identity_data
        summary_data["dropped_ranges"][0]["private_nested"] = "range secret"
        summary = M3StreamSummary.from_dict(summary_data)
        self.assertEqual((summary.unknown_field_count, summary.process_identity.unknown_field_count,
                          summary.dropped_ranges[0].unknown_field_count), (1, 1, 1))
        self.assertNotIn("summary secret", str(summary.to_dict()))
        self.assertNotIn("range secret", str(summary.to_dict()))
        self.assertEqual(M3StreamSummary.from_dict(summary.to_dict()), summary)

        event_data = self.event().to_dict() | {"private_event": "event secret"}
        event = NormalizedEvent.from_dict(event_data)
        self.assertEqual(event.unknown_field_count, 1)
        self.assertNotIn("event secret", str(event.to_dict()))

        incident_data = self.incident().to_dict() | {"private_incident": "incident secret"}
        incident_data["facts"]["private_fact"] = "fact secret"
        incident_data["process_identity"] = identity_data
        incident = Incident.from_dict(incident_data)
        self.assertEqual((incident.unknown_field_count, incident.process_identity.unknown_field_count), (2, 1))
        self.assertNotIn("private_fact", str(incident.to_dict()))
        self.assertNotIn("fact secret", str(incident.to_dict()))
        self.assertNotIn("incident secret", str(incident.to_dict()))
        self.assertEqual(Incident.from_dict(incident.to_dict()), incident)

        metric_data = MetricSample("1.0.0", "m", "codex", "output_tokens", 1, "tokens",
                                   "provider_reported", NOW, "reported", 1, "key").to_dict()
        metric_data["private_metric"] = "metric secret"
        metric = MetricSample.from_dict(metric_data)
        self.assertEqual(metric.unknown_field_count, 1)
        self.assertNotIn("metric secret", str(metric.to_dict()))
        self.assertEqual(MetricSample.from_dict(metric.to_dict()), metric)

    def test_unknown_digest_covers_values_and_is_bounded(self):
        base = self.event().to_dict()
        first = NormalizedEvent.from_dict(base | {"private_secret": "value one"})
        second = NormalizedEvent.from_dict(base | {"private_secret": "value two"})
        self.assertEqual(first.unknown_field_count, 1)
        self.assertNotEqual(first.unknown_field_digest, second.unknown_field_digest)
        self.assertNotIn("value one", str(first.to_dict()))
        self.assertEqual(NormalizedEvent.from_dict(first.to_dict()), first)
        with self.assertRaises(ValueError):
            with patch.object(serialization.json, "dumps", side_effect=AssertionError("must prevalidate")):
                NormalizedEvent.from_dict(base | {"private_secret": "x" * MAX_UNKNOWN_DIGEST_INPUT_BYTES})
        with self.assertRaises(ValueError):
            NormalizedEvent.from_dict(base | {"private_secret": object()})

    def test_unknown_count_is_rejected_before_digest_collection(self):
        external = self.event().to_dict()
        external.update({f"unknown_{index}": "discard" for index in range(MAX_UNKNOWN_FIELDS + 1)})
        with patch.object(serialization, "_unknown_pairs_digest",
                          side_effect=AssertionError("must reject before hashing")):
            with self.assertRaises(ValueError):
                NormalizedEvent.from_dict(external)

    def test_oversized_unknown_name_is_rejected_before_digest(self):
        external = self.event().to_dict() | {"x" * 1_000_000: "discard"}
        with patch.object(serialization, "_unknown_pairs_digest",
                          side_effect=AssertionError("must reject before hashing")):
            with self.assertRaises(ValueError):
                NormalizedEvent.from_dict(external)

    def test_contract_types_are_frozen(self):
        frame = self.frame()
        with self.assertRaises((AttributeError, TypeError)):
            frame.sequence = 2


if __name__ == "__main__":
    unittest.main()
