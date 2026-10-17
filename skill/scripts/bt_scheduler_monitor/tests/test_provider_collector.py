from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

from bt_scheduler_monitor.contracts import DroppedRange, ExecutionOutputFrame, ProcessIdentity
from bt_scheduler_monitor.providers import JsonlCollector

FIXTURE = Path(__file__).parent / "fixtures" / "providers" / "split-utf8.jsonl"


def frame(sequence: int, offset: int, data: bytes, *, provider: str = "claude") -> ExecutionOutputFrame:
    return ExecutionOutputFrame("1.0.0", "run", 1, "task", "attempt", "execution", ProcessIdentity("linux"),
                                provider, "stdout", sequence, offset, "2026-10-15T00:00:00Z", data)


class ProviderCollectorTests(unittest.TestCase):
    def test_reassembles_json_and_utf8_across_frames_with_source_bounds(self) -> None:
        raw = FIXTURE.read_bytes()
        split = raw.index(b"\xc3") + 1
        collector = JsonlCollector("claude")
        self.assertEqual(collector.feed(frame(8, 100, raw[:split])).records, ())
        output = collector.feed(frame(9, 100 + split, raw[split:]))
        self.assertEqual(len(output.records), 1)
        record = output.records[0]
        self.assertEqual((record.first_sequence, record.last_sequence, record.first_offset,
                          record.last_offset, dict(record.parsed.payload)["byte_count"]),
                         (8, 9, 100, 100 + len(raw), len("café".encode())))
        self.assertEqual(output.gaps, ())

    def test_malformed_unsupported_and_invalid_utf8_lines_become_digest_gaps(self) -> None:
        collector = JsonlCollector("claude")
        raw_lines = (b'{"type":}\n', b'{"type":{"private":"kind"}}\n', b'{"type":"system"}\xff\n')
        results = []
        offset = 0
        for sequence, raw in enumerate(raw_lines):
            results.extend(collector.feed(frame(sequence, offset, raw)).gaps)
            offset += len(raw)
        self.assertEqual([gap.reason for gap in results], ["malformed_json", "unsupported_event", "invalid_utf8"])
        self.assertTrue(all(gap.digest.startswith("sha256:") and gap.byte_count > 0 for gap in results))
        self.assertNotIn("private", repr(results))

    def test_discontinuity_and_final_truncation_are_explicit(self) -> None:
        collector = JsonlCollector("claude")
        partial = b'{"type":"assistant","message":'
        self.assertEqual(collector.feed(frame(0, 0, partial)).gaps, ())
        current = b'{"type":"assistant","message":{"content":[{"type":"text","text":"ok"}]}}\n'
        skipped = collector.feed(frame(2, len(partial) + 3, current))
        self.assertEqual([(gap.reason, gap.first_sequence, gap.last_sequence, gap.first_offset,
                           gap.last_offset, gap.byte_count, gap.frame_count) for gap in skipped.gaps],
                         [("truncated_input", 0, 0, 0, len(partial), len(partial), 1),
                          ("sequence_discontinuity", 1, 1, len(partial), len(partial) + 3, 3, 1)])
        self.assertEqual(len(skipped.records), 1)
        self.assertEqual((skipped.records[0].first_sequence, skipped.records[0].last_sequence,
                          skipped.records[0].first_offset, skipped.records[0].last_offset),
                         (2, 2, len(partial) + 3, len(partial) + 3 + len(current)))

        another = JsonlCollector("claude")
        trailing = another.feed(frame(4, 50, b'{"type":"assistant"'))
        self.assertEqual(trailing.gaps, ())
        final = another.finish("stdout")
        self.assertEqual(final.gaps[0].reason, "truncated_input")
        self.assertEqual(final.gaps[0].digest, "sha256:" + hashlib.sha256(b'{"type":"assistant"').hexdigest())

    def test_offset_only_discontinuity_covers_missing_interval_and_keeps_current_record(self) -> None:
        collector = JsonlCollector("claude")
        first = b'{"type":"system"}\n'
        collector.feed(frame(4, 100, first))
        current = FIXTURE.read_bytes()
        output = collector.feed(frame(5, 100 + len(first) + 7, current))
        gap = output.gaps[0]
        self.assertEqual((gap.reason, gap.first_sequence, gap.last_sequence,
                          gap.first_offset, gap.last_offset, gap.byte_count, gap.frame_count),
                         ("offset_discontinuity", 4, 4, 100 + len(first),
                          100 + len(first) + 7, 7, 0))
        self.assertEqual(len(output.records), 1)
        record = output.records[0]
        self.assertEqual((record.first_sequence, record.last_sequence, record.first_offset,
                          record.last_offset),
                         (5, 5, 100 + len(first) + 7, 100 + len(first) + 7 + len(current)))

    def test_oversized_line_is_bounded_and_source_drop_metadata_is_reported(self) -> None:
        collector = JsonlCollector("claude")
        data = b"x" * 65_537 + b"\n"
        gaps = []
        offset = 0
        for sequence, start in enumerate(range(0, len(data), 3_840)):
            chunk = data[start:start + 3_840]
            gaps.extend(collector.feed(frame(sequence, offset, chunk)).gaps)
            offset += len(chunk)
        self.assertEqual(gaps[0].reason, "oversized_line")
        self.assertEqual(gaps[0].byte_count, 65_537)
        source = collector.feed_source_gap(DroppedRange("stdout", 18, 19, offset, offset + 4, 4, 2))
        self.assertEqual(source.gaps[0].reason, "source_gap")
        self.assertEqual((source.gaps[0].byte_count, source.gaps[0].frame_count), (4, 2))
        self.assertEqual(source.gaps[0].last_offset, offset + 4)

    def test_source_gap_counts_every_frame_of_a_partial_multiframe_line(self) -> None:
        collector = JsonlCollector("claude")
        first = b'{"type":'
        second = b'"assistant"'
        collector.feed(frame(0, 10, first))
        collector.feed(frame(1, 10 + len(first), second))
        dropped = DroppedRange("stdout", 2, 2, 10 + len(first) + len(second),
                               10 + len(first) + len(second) + 4, 4, 1)
        output = collector.feed_source_gap(dropped)
        gap = output.gaps[-1]
        self.assertEqual((gap.first_sequence, gap.last_sequence, gap.first_offset, gap.last_offset,
                          gap.byte_count, gap.frame_count),
                         (0, 2, 10, dropped.last_offset, len(first) + len(second) + 4, 3))

    def test_provider_mismatch_separates_pending_line_from_incoming_frame(self) -> None:
        collector = JsonlCollector("claude")
        pending = b'{"type":"assistant"'
        collector.feed(frame(6, 200, pending))
        incoming = b'{"type":"system"}\n'
        output = collector.feed(frame(7, 200 + len(pending), incoming, provider="codex"))
        self.assertEqual([(gap.reason, gap.first_sequence, gap.last_sequence, gap.first_offset,
                           gap.last_offset, gap.byte_count, gap.frame_count) for gap in output.gaps],
                         [("truncated_input", 6, 6, 200, 200 + len(pending), len(pending), 1),
                          ("provider_mismatch", 7, 7, 200 + len(pending),
                           200 + len(pending) + len(incoming), len(incoming), 1)])


if __name__ == "__main__":
    unittest.main()
