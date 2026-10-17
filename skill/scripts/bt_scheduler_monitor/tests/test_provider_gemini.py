from __future__ import annotations

import json
import unittest
from pathlib import Path

from bt_scheduler_monitor import PROVIDERS
from bt_scheduler_monitor.providers import gemini

FIXTURE = Path(__file__).parent / "fixtures" / "providers" / "gemini.jsonl"


class GeminiFixtureNormalizerTests(unittest.TestCase):
    def test_fixture_events_normalize_without_retaining_message_or_path(self) -> None:
        parsed = [gemini.normalize(line)[0] for line in FIXTURE.read_bytes().splitlines()]
        self.assertEqual([event.status for event in parsed], ["ignored", "parsed", "parsed", "parsed"])
        self.assertEqual([event.event_type for event in parsed], [None, "message_delta", "tool_started", "usage_reported"])
        encoded = json.dumps([event.__dict__ for event in parsed])
        self.assertNotIn("fixture only private answer", encoded)
        self.assertNotIn("/private/file", encoded)
        self.assertIn("gemini_fixture", PROVIDERS)
        self.assertEqual(parsed[3].unknown_field_count, 1)
        self.assertNotIn("nested stats metadata", repr(parsed[3]))

    def test_parser_is_explicitly_fixture_versioned(self) -> None:
        event = gemini.normalize('{"type":"result","status":"success","stats":{"total_tokens":1}}')[0]
        self.assertEqual(event.source_schema_version, "gemini-cli-0.63-jsonl-fixture/1")
        self.assertEqual(event.event_type, "usage_reported")


if __name__ == "__main__":
    unittest.main()
