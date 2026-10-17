from __future__ import annotations

import json
import unittest
from pathlib import Path

from bt_scheduler_monitor.providers import antigravity

FIXTURE = Path(__file__).parent / "fixtures" / "providers" / "antigravity.jsonl"


class AntigravityNormalizerTests(unittest.TestCase):
    def test_fixture_stream_maps_deltas_usage_and_structured_quota(self) -> None:
        parsed = [antigravity.normalize(line)[0] for line in FIXTURE.read_bytes().splitlines()]
        self.assertEqual([event.status for event in parsed], ["ignored", "parsed", "parsed", "parsed"])
        self.assertEqual([event.event_type for event in parsed], [None, "message_delta", "usage_reported", "quota_error"])
        self.assertEqual(dict(parsed[1].payload), {"message_count": 1, "byte_count": len(b"private answer")})
        self.assertNotIn("private answer", json.dumps([event.__dict__ for event in parsed]))
        self.assertNotIn("private quota details", json.dumps([event.__dict__ for event in parsed]))
        self.assertEqual((parsed[1].unknown_field_count, parsed[3].unknown_field_count), (1, 1))
        self.assertNotIn("nested step metadata", repr(parsed[1]))
        self.assertNotIn("nested result metadata", repr(parsed[3]))

    def test_missing_nested_result_is_malformed(self) -> None:
        event = antigravity.normalize('{"event":"result","result":"unexpected"}')[0]
        self.assertEqual((event.status, event.code), ("malformed", "invalid_result"))


if __name__ == "__main__":
    unittest.main()
