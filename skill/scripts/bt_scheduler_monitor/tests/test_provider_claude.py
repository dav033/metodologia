from __future__ import annotations

import json
import unittest
from pathlib import Path

from bt_scheduler_monitor.providers import claude

FIXTURE = Path(__file__).parent / "fixtures" / "providers" / "claude.jsonl"


class ClaudeNormalizerTests(unittest.TestCase):
    def test_fixture_events_are_allowlisted_and_text_is_discarded(self) -> None:
        parsed = [event for line in FIXTURE.read_bytes().splitlines() for event in claude.normalize(line)]
        self.assertEqual([event.event_type for event in parsed], ["message_delta", "message_delta", "tool_started", "usage_reported"])
        self.assertNotEqual(parsed[0].source_event_id, parsed[1].source_event_id)
        self.assertEqual(dict(parsed[0].payload), {"message_count": 1, "byte_count": len(b"private answer")})
        self.assertEqual(dict(parsed[2].payload)["tool_label"], "Bash")
        self.assertEqual((parsed[0].unknown_field_count, parsed[3].unknown_field_count), (1, 1))
        self.assertNotIn("nested private", repr(parsed[0]))
        self.assertNotIn("nested usage secret", repr(parsed[3]))
        serialized = json.dumps([event.__dict__ for event in parsed])
        self.assertNotIn("private answer", serialized)
        self.assertNotIn("secret command", serialized)

    def test_structured_error_codes_are_normalized_without_error_text(self) -> None:
        event = claude.normalize(b'{"type":"result","is_error":true,"error_code":"quota_exceeded","result":"secret"}')[0]
        self.assertEqual((event.event_type, dict(event.payload)), ("quota_error", {"source_code": "quota_exceeded"}))
        self.assertNotIn("secret", repr(event))

    def test_invalid_utf8_and_oversized_lines_are_bounded_statuses(self) -> None:
        self.assertEqual(claude.normalize(b"\xff")[0].code, "invalid_utf8")
        self.assertEqual(claude.normalize(b" " * 65_537)[0].code, "line_too_large")

    def test_duplicate_keys_and_untrusted_event_types_are_rejected_without_copying_values(self) -> None:
        duplicate = claude.normalize('{"type":"system","type":"result"}')[0]
        self.assertEqual(duplicate.code, "invalid_json")
        adversarial = (FIXTURE.parent / "adversarial-unknown-type.jsonl").read_bytes().strip()
        unsupported = claude.normalize(adversarial)[0]
        self.assertEqual(unsupported.source_event_type, "unsupported")
        self.assertNotIn("must not escape", repr(unsupported))
        self.assertNotIn("unsafe", repr(unsupported))

    def test_non_ascii_tool_label_uses_safe_fallback(self) -> None:
        event = claude.normalize('{"type":"assistant","message":{"content":[{"type":"tool_use","name":"λ","input":{}}]}}')[0]
        self.assertEqual(dict(event.payload)["tool_label"], "tool")


if __name__ == "__main__":
    unittest.main()
