"""REQ-030 step 2: scope no longer serialises tasks; what keeps two apart is the overlap of their declared surface.
Measured on frozen replicas of the REQ-020 and REQ-029 nights (tests/fixtures/replica-*.json)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bt_config
import bt_scheduler_replica as replica

FIXTURES = Path(__file__).resolve().parent / "fixtures"
OLD_SCOPES = ("large_change", "full_feature", "full_system")


def small(*tasks):
    return {"version": replica.FIXTURE_VERSION, "name": "t", "plan": {"plan_id": "R", "tasks": list(tasks)},
            "attempts": {t["id"]: [{"exec_min": 10, "verify_min": 2, "outcome": "accepted"}] for t in tasks}, "reworks": []}


def task(tid, paths, scope="large_change", after=()):
    return {"id": tid, "after": list(after), "repository": "app", "expected_paths": paths, "scope": scope, "shared_resources": []}


class Defaults(unittest.TestCase):
    def test_scope_does_not_serialise_by_default_and_the_old_list_is_still_available(self):
        self.assertEqual(bt_config.DEFAULTS["scheduler"]["exclusive_scopes"], [])
        self.assertIs(bt_config.DEFAULTS["gates"]["remediation_parallel"], True)
        self.assertIs(bt_config.DEFAULTS["gates"]["integration_line"], True)


class Claims(unittest.TestCase):
    def test_large_tasks_with_disjoint_paths_run_side_by_side_and_overlapping_ones_do_not(self):
        disjoint = small(task("T1", ["src/a/**"]), task("T2", ["src/b/**"]))
        new, old = replica.replay(disjoint), replica.replay(disjoint, exclusive_scopes=OLD_SCOPES)
        self.assertEqual((new["max_width"], old["max_width"]), (2, 1))
        self.assertLess(new["wall_minutes"], old["wall_minutes"])
        overlap = small(task("T1", ["src/a/**"]), task("T2", ["src/a/x.ts"]))
        self.assertEqual(replica.replay(overlap)["max_width"], 1)                    # the same file is never edited by two
        unknown = small(task("T1", ["src/a/**"]), {**task("T2", []), "repository": ""})
        self.assertEqual(replica.replay(unknown)["max_width"], 1)                    # no declared surface: serialised anyway


class Nights(unittest.TestCase):
    def test_the_recorded_nights_replay_to_completion_and_never_get_slower(self):
        for name in ("req020", "req029"):
            fixture = replica.load(FIXTURES / f"replica-{name}.json")
            old = replica.replay(fixture, exclusive_scopes=OLD_SCOPES)
            new = replica.replay(fixture)
            self.assertEqual((old["status"], new["status"]), ("completed", "completed"), name)
            self.assertEqual(old["attempts"], new["attempts"], name)                  # the same work, scheduled differently
            self.assertLessEqual(new["wall_minutes"], old["wall_minutes"], name)
            self.assertGreaterEqual(new["ratio"], old["ratio"], name)
            self.assertEqual(old["ratio"], 1.0, name)                                  # last night really was serial

    def test_req020_gains_what_its_graph_allows_and_more_slots_do_not_help(self):
        fixture = replica.load(FIXTURES / "replica-req020.json")
        three, six = replica.replay(fixture), replica.replay(fixture, max_parallel_tasks=6)
        self.assertGreaterEqual(three["ratio"], 1.1)
        self.assertEqual(three["wall_minutes"], six["wall_minutes"])                  # the graph is the limit, not the slots

    def test_the_recorded_rework_cost_is_what_the_minimal_rework_policy_has_to_beat(self):
        cost = replica.rework_cost(replica.load(FIXTURES / "replica-req029.json"))
        self.assertEqual(cost["requests"], 22)
        self.assertGreater(cost["tasks_invalidated"], 100)


if __name__ == "__main__":
    unittest.main()
