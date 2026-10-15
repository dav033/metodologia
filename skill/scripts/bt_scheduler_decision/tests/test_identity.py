from __future__ import annotations

import unittest

from bt_scheduler_decision import (
    account_reference,
    candidate_route_id,
    canonical_json,
    executor_reference,
    parse_executor_reference,
    sha256_json,
)


class IdentityTests(unittest.TestCase):
    def test_canonical_json_sorts_keys_and_normalizes_unicode(self):
        self.assertEqual(canonical_json({"z": 1, "e\u0301": "e\u0301"}), canonical_json({"é": "é", "z": 1}))
        self.assertEqual(sha256_json({"a": 1, "b": 2}), sha256_json({"b": 2, "a": 1}))

    def test_unicode_key_collision_is_rejected(self):
        with self.assertRaises(ValueError):
            canonical_json({"é": 1, "e\u0301": 2})

    def test_unpaired_surrogates_are_rejected_before_utf8_hashing(self):
        with self.assertRaises(ValueError):
            sha256_json({"text": "invalid-\ud800-text"})
        with self.assertRaises(ValueError):
            sha256_json({"\ud800": 1})
        with self.assertRaises(ValueError):
            account_reference("invalid-\ud800-account")

    def test_route_and_account_references_are_hashes(self):
        account_key = "claude:/home/david/private-account"
        account = account_reference(account_key)
        route = candidate_route_id("claude", "sonnet", "work", "high")
        self.assertEqual(len(route), 64)
        self.assertEqual(len(account), 69)
        self.assertNotIn("private-account", account)
        self.assertEqual(account, account_reference(account_key))

    def test_executor_reference_resolves_only_its_two_content_ids(self):
        decision = "a" * 64
        route = "b" * 64
        reference = executor_reference(decision, route)
        self.assertEqual(parse_executor_reference(reference), (decision, route))
        self.assertIsNone(parse_executor_reference(reference + ":extra"))
        with self.assertRaises(ValueError):
            executor_reference("bad", route)


if __name__ == "__main__":
    unittest.main()
