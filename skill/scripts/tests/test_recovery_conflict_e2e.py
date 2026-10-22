"""Historical provenance and shipped-entrypoint structural replay checks for REQ-027."""
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import recovery_conflict_support as support


class HistoricalConflictSources(unittest.TestCase):
    def test_official_hashes_dag_scopes_and_preserved_behavior_are_recorded(self):
        fixture = support.load_fixture()
        artifacts = {row["id"]: row["sha256"] for row in fixture["source_artifacts"]}
        self.assertEqual(artifacts["req027-plan-r7"], "17522cd6ebedff79ca9fefa0550e06518996f2067cee9d3071f0f83e68cc675a")
        self.assertEqual(artifacts["req027-plan-r9"], "e2d7030f678abcca2c1e3f0cee1cba62f85fd471c1274c6171e7ad26f257510c")
        revisions = {row["revision"]: row for row in fixture["plan_revisions"]}
        self.assertEqual(revisions["r7"]["sha256"], artifacts["req027-plan-r7"])
        self.assertEqual(revisions["r9"]["sha256"], artifacts["req027-plan-r9"])
        self.assertEqual(revisions["r7"]["tasks"], revisions["r9"]["tasks"])
        self.assertEqual(revisions["r7"]["tasks"], fixture["ordered_dag"])
        self.assertEqual(support.ordered_dag(fixture), {
            "T3": ["T2"], "T15": ["T3"], "T15a": ["T15"],
            "T15b": ["T15a"], "T15c": ["T15b", "T7"]})
        tasks = {row["id"]: row for row in fixture["ordered_dag"]}
        self.assertEqual(tasks["T15a"]["scope"], ["remote/web/**"])
        self.assertEqual(tasks["T15b"]["scope"], ["remote/web/**"])
        self.assertEqual(fixture["run_policy"]["max_reworks"], 2)
        self.assertEqual(fixture["run_policy"]["reworks_at_capture"]["T15b"], 2)
        self.assertIn("already sent back 2 time(s)", fixture["run_policy"]["ordinary_give_way_refusal"])
        lineage = {row["attempt"]: row for row in fixture["source_attempt_lineage"]}
        self.assertEqual(lineage["att-0130"]["task"], "T3")
        self.assertEqual(lineage["att-0142"]["task"], "T15b")
        self.assertEqual(lineage["att-0204"]["task"], "T15")
        preserved = {row["attempt"]: row for row in fixture["preserved_attempts"]}
        self.assertEqual(preserved["att-0142"]["task"], "T15b")
        self.assertEqual(preserved["att-0204"]["task"], "T15")
        self.assertNotEqual(preserved["att-0204"]["snapshot_sha"], preserved["att-0142"]["base_sha"],
                            "the accepted descendant was built before the replacement T15 source")
        self.assertEqual(len(preserved["att-0142"]["behavior_contract"]), 3)
        self.assertEqual(len(preserved["att-0204"]["behavior_contract"]), 3)

    def test_clipped_start_and_gate_context_never_become_path_authority(self):
        fixture = support.load_fixture()
        sources = {row["id"]: row for row in fixture["conflict_sources"]}
        self.assertEqual(sources["req027-r7-start-att-0124"]["known"]["rejected_task"], "T15b")
        self.assertEqual(sources["req027-r7-start-att-0124"]["known"]["conflicting_tasks"], ["T3", "T15a"])
        self.assertEqual(sources["req027-r9-m6-att-0206-0207-0208"]["attempts"],
                         ["att-0206", "att-0207", "att-0208"])
        gate = sources["req027-r9-m6-att-0206-0207-0208"]
        self.assertEqual(gate["known"]["ordinary_rework_refusal"],
                         "limit: T15b was already sent back 2 time(s)")
        self.assertFalse(gate["known"]["current_t15_is_ancestor_of_t15b_base"])
        for source in sources.values():
            with self.assertRaisesRegex(ValueError, "complete historical merge paths unavailable"):
                support.require_complete_paths(source)
        self.assertFalse(fixture["reconstruction"]["historical_paths_are_authority"])

    def test_fixture_is_sanitized_versioned_json_with_stable_content_digest(self):
        raw = support.FIXTURE.read_bytes()
        first = hashlib.sha256(raw).hexdigest()
        second = hashlib.sha256(json.dumps(json.loads(raw), sort_keys=True).encode()).hexdigest()
        self.assertEqual(len(first), 64)
        self.assertEqual(len(second), 64)
        self.assertNotIn(b"/home/david/", raw)
        self.assertNotIn(b"RUN.recovery", raw)


if __name__ == "__main__":
    unittest.main()
