from __future__ import annotations

import json
import unittest
from pathlib import Path

from bt_scheduler_monitor.providers import codex

FIXTURE = Path(__file__).parent / "fixtures" / "providers" / "codex.jsonl"


class CodexNormalizerTests(unittest.TestCase):
    def test_jsonl_fixture_normalizes_turn_items_and_usage(self) -> None:
        parsed = [codex.normalize(line)[0] for line in FIXTURE.read_bytes().splitlines()]
        self.assertEqual([event.event_type for event in parsed], ["heartbeat", "tool_started", "tool_finished", "usage_reported"])
        self.assertEqual(dict(parsed[-1].payload), {"metric_name": "total_tokens", "sample_count": 1,
                         "source": "provider_reported", "unit": "tokens", "value": 27})
        self.assertNotIn("private command", json.dumps([event.__dict__ for event in parsed]))
        self.assertNotIn("/private/worktree", json.dumps([event.__dict__ for event in parsed]))
        self.assertEqual((parsed[1].unknown_field_count, parsed[3].unknown_field_count), (1, 1))
        self.assertNotIn("nested command metadata", repr(parsed[1]))
        self.assertNotIn("nested usage metadata", repr(parsed[3]))

    def test_unknown_top_level_fields_are_counted_and_hashed_not_retained(self) -> None:
        event = codex.normalize('{"type":"turn.started","opaque":"secret-value"}')[0]
        self.assertEqual(event.unknown_field_count, 1)
        self.assertTrue(event.unknown_field_digest.startswith("sha256:"))
        self.assertNotIn("secret-value", repr(event))

    def test_unknown_event_type_is_explicit(self) -> None:
        event = codex.normalize('{"type":{"secret":"nested"},"id":"unsafe/id","text":"private"}')[0]
        self.assertEqual((event.status, event.code), ("unsupported", "unknown_event_type"))
        self.assertEqual(event.source_event_type, "unsupported")
        self.assertNotIn("private", repr(event))
        self.assertNotIn("nested", repr(event))
        self.assertNotIn("unsafe/id", repr(event))

    def test_duplicate_keys_are_rejected(self) -> None:
        event = codex.normalize('{"type":"turn.started","type":"turn.completed"}')[0]
        self.assertEqual((event.status, event.code), ("malformed", "invalid_json"))

    def test_unsafe_source_ids_are_dropped(self) -> None:
        event = codex.normalize('{"type":"turn.started","id":"../../private"}')[0]
        self.assertIsNone(event.source_event_id)
        self.assertNotIn("private", repr(event))


if __name__ == "__main__":
    unittest.main()
