from __future__ import annotations

import dataclasses
import unittest

from bt_scheduler_decision import rank_candidates
from bt_scheduler_decision.tests.support import candidate, request


class CandidateEnumerationTests(unittest.TestCase):
    def test_ranker_preserves_configured_inventory_and_places_missing_baseline_rank_last(self):
        ranked = candidate(provider="codex", model="sol", profile="ranked", rank=1)
        unranked = candidate(provider="claude", model="opus", profile="unranked", rank=None)
        excluded = dataclasses.replace(candidate(profile="denied", rank=0), profile_authorized=False)
        result = rank_candidates(request(candidates=(unranked, excluded, ranked)))
        self.assertEqual(len(result.eligible) + len(result.exclusions), 3)
        self.assertEqual(tuple(item.profile for item in result.eligible), ("ranked", "unranked"))
        self.assertEqual(result.exclusions[0].profile, "denied")
        self.assertEqual(result.selected, ranked)


if __name__ == "__main__":
    unittest.main()
