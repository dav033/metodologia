import hashlib
import json
import unittest
from datetime import date

from bt_owner_proposal import ProposalError, selection


class OwnerProposalTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.dumps({"backings": [{"id": f"b{i}"} for i in range(7)],
                               "mesas": [{"tipo": f"m{i}"} for i in range(4)]}).encode()
        self.digest = hashlib.sha256(self.raw).hexdigest()

    def test_selection_and_empty_selection(self):
        result = selection(self.raw, self.digest, ["b1"], ["m2"], today=date(2026, 10, 28))
        self.assertEqual(result, {"propuestaSha256": self.digest, "aprobadoPor": "owner", "fecha": "2026-10-28",
                                  "backings": ["b1"], "mesas": ["m2"]})
        self.assertEqual(selection(self.raw, self.digest, [], [])["backings"], [])

    def test_limits_duplicates_unknown_and_stale_hash(self):
        cases = [("wrong", [], []), (self.digest, ["b1", "b1"], []),
                 (self.digest, ["missing"], []), (self.digest, [f"b{i}" for i in range(7)], []),
                 (self.digest, [], [f"m{i}" for i in range(4)])]
        for digest, backings, mesas in cases:
            with self.subTest(digest=digest, backings=backings, mesas=mesas), self.assertRaises(ProposalError):
                selection(self.raw, digest, backings, mesas)
        selection(self.raw, self.digest, [f"b{i}" for i in range(6)], [f"m{i}" for i in range(3)])

    def test_rejects_duplicate_proposal_candidates(self):
        raw = b'{"backings":[{"id":"same"},{"id":"same"}],"mesas":[]}'
        with self.assertRaises(ProposalError):
            selection(raw, hashlib.sha256(raw).hexdigest(), [], [])
