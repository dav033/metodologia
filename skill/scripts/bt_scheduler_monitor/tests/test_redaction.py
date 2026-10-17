from __future__ import annotations

import unittest

from bt_scheduler_monitor.redaction import allowlist_payload, redact_evidence


class AllowlistTests(unittest.TestCase):
    def test_payload_drops_unknown_fields_without_serializing_nested_content(self) -> None:
        secret = "private-project-content-742"
        result = allowlist_payload("tool_started", {
            "tool_label": "exec", "command": {"token": secret}, "unexpected": [secret],
        })
        self.assertEqual(result.fields, (("tool_label", "exec"),))
        self.assertEqual(result.dropped_field_count, 2)
        self.assertNotIn(secret, repr(result))

    def test_invalid_allowed_value_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            allowlist_payload("usage_reported", {"value": "secret text"})

    def test_unknown_event_and_non_object_are_rejected(self) -> None:
        for event_type, payload in (("unknown", {}), ("tool_started", "raw")):
            with self.subTest(event_type=event_type):
                with self.assertRaises(ValueError):
                    allowlist_payload(event_type, payload)


class RedactedEvidenceTests(unittest.TestCase):
    def test_secret_like_fields_are_redacted_and_digest_is_of_source(self) -> None:
        text = "Bearer abc.def API_KEY=sk_live_verysecret123 sk-12345678901234567890"
        result = redact_evidence(text)
        self.assertFalse(result.withheld)
        self.assertNotIn("abc.def", result.excerpt)
        self.assertNotIn("sk_live_verysecret123", result.excerpt)
        self.assertNotIn("sk-12345678901234567890", result.excerpt)
        self.assertTrue(result.digest.startswith("sha256:"))

    def test_bytes_and_excerpt_cap_are_bounded(self) -> None:
        result = redact_evidence(b"x" * 100, max_bytes=12)
        self.assertEqual(result.excerpt, "x" * 12)
        self.assertEqual(result.byte_count, 100)
        self.assertFalse(result.withheld)

    def test_large_nested_and_invalid_utf8_inputs_withhold_excerpt(self) -> None:
        oversized = redact_evidence(b"x" * 65_537)
        nested = None
        with self.assertRaises(ValueError):
            nested = redact_evidence({"text": "private"})
        invalid = redact_evidence(b"\xff")
        self.assertTrue(oversized.withheld)
        self.assertIsNone(oversized.excerpt)
        self.assertEqual(oversized.byte_count, 65_537)
        self.assertTrue(invalid.withheld)
        self.assertIsNone(invalid.excerpt)
        self.assertIsNone(nested)

    def test_filter_failure_and_malformed_filter_withhold_text(self) -> None:
        def fail(_text: str) -> str:
            raise RuntimeError("filter failed")

        for callback in (fail, object(), lambda _text: {"raw": "secret"}):
            result = redact_evidence("private evidence", filter_text=callback)
            self.assertTrue(result.withheld)
            self.assertIsNone(result.excerpt)
            self.assertIsNotNone(result.digest)


if __name__ == "__main__":
    unittest.main()
