"""Recovery metrics stay honest about unresolved cases; evolution proposes only with evidence."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bt_evolution as evolution
import bt_interventions
import bt_recovery_benchmark as bench
import bt_scheduler_replica as replica

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class Benchmark(unittest.TestCase):
    def test_every_recorded_stop_obeys_its_safety_contract_and_history_is_preserved(self):
        result = bench.run()
        for row in result["scenarios"]:
            self.assertTrue(row["class_ok"], row)
            self.assertTrue(row["auto_ok"], row)
        versions = bench.history()["versions"]
        order = list(versions)
        for before, after in zip(order, order[1:]):
            self.assertEqual(bench.regressions(versions[before], versions[after]), [], f"{before} -> {after}")
        recorded = versions[order[-1]]
        # P-186 removes a fabricated recovery in S10. Keep that historical regression visible rather than
        # replacing the golden or counting a blocked audit as automatically recovered.
        self.assertEqual(bench.regressions(recorded, result["totals"]), [
            "human_interventions: 0 -> 1", "minutes_to_recovery: 7.8 -> 51.9"])

    def test_the_night_needed_ten_people_and_the_current_code_retains_one_unresolved_audit(self):
        totals = bench.run()["totals"]
        self.assertEqual((totals["human_interventions_night"], totals["human_interventions"]), (10, 1))
        self.assertLess(totals["minutes_to_recovery"], totals["minutes_to_recovery_night"] / 10)
        self.assertEqual(totals["as_expected"], totals["scenarios"])

    def test_an_audit_without_producer_repair_stays_blocked_instead_of_reporting_recovery(self):
        rows = bench.run()["scenarios"]
        asking = [row for row in rows if not row["auto"]]
        self.assertEqual([row["id"] for row in asking], ["S10"])
        self.assertEqual(asking[0]["blocker"], "producer_remediation_required")
        self.assertEqual(asking[0]["repair"], "none")
        self.assertTrue(asking[0]["recovery_pending"])
        self.assertEqual(asking[0]["minutes_after"], asking[0]["minutes_before"])

    def test_a_worse_version_is_reported(self):
        base = {"human_interventions": 2, "minutes_to_recovery": 76.3, "classified": 11, "as_expected": 12}
        self.assertEqual(bench.regressions(base, base), [])
        worse = {**base, "human_interventions": 3, "classified": 10}
        self.assertEqual(len(bench.regressions(base, worse)), 2)


class Evolution(unittest.TestCase):
    def rows(self, tmp, **counts):
        run = Path(tmp) / "requirements" / "REQ-001-x"
        run.mkdir(parents=True)
        for kind, count in counts.items():
            for n in range(count):
                bt_interventions.record(run, kind=kind, source="manual", task=f"T{n}", evidence=f"{kind} {n}", repair="by hand",
                                        minutes_lost=30.0)
        return evolution.collect(tmp)

    def test_patterns_become_proposals_with_their_evidence_and_nothing_else_does(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = self.rows(tmp, criterion_unmapped=3, regression=2, quota=1)
            keys = {p["key"]: p for p in evolution.analyse(rows)}
        self.assertEqual(set(keys), {"planner-purposes", "guard-tests"})                  # one quota stop is not a pattern
        self.assertIn("3 stops", keys["planner-purposes"]["evidence"])
        self.assertEqual(keys["planner-purposes"]["minutes"], 90.0)
        self.assertEqual({p["risk"] for p in keys.values()}, {"high"})
        self.assertEqual(evolution.analyse([]), [])

    def test_a_plan_that_serialises_itself_through_one_resource_is_pointed_out(self):
        fixture = replica.load(FIXTURES / "replica-req029.json")
        keys = [p["key"] for p in evolution.analyse([], plans=[fixture])]
        self.assertTrue(any(k.startswith("shared-resource-recovery-case-v1") for k in keys), keys)
        clean = replica.load(FIXTURES / "replica-req020.json")
        self.assertEqual([p for p in evolution.analyse([], plans=[clean]) if p["key"].startswith("shared-resource")], [])

    def test_an_old_exclusive_scope_setting_is_a_low_risk_proposal_to_remove(self):
        found = evolution.analyse([], current={"scheduler.exclusive_scopes": ["large_change"]})
        self.assertEqual((found[0]["risk"], found[0]["change"]), ("low", {"key": "scheduler.exclusive_scopes", "value": []}))

    def test_a_setting_is_applied_only_when_the_replicas_prove_it_and_can_be_put_back(self):
        replicas = [replica.load(FIXTURES / "replica-req020.json"), replica.load(FIXTURES / "replica-req029.json")]
        results = evolution.propose_settings(replicas, {"scheduler.max_parallel_tasks": 3})
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0]["apply"])                                              # the graph, not the slots, is the limit
        self.assertEqual(results[0]["reason"], "no replica saves enough time")
        changed = {}
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(evolution.apply_proven(results, tmp, changed.__setitem__), [])
            self.assertEqual(changed, {})
            wide = {"name": "wide", "plan": {"plan_id": "W", "tasks": [
                {"id": f"T{n}", "after": [], "repository": "r", "expected_paths": [f"d{n}/**"], "shared_resources": []} for n in range(1, 5)]},
                    "attempts": {f"T{n}": [{"exec_min": 30, "verify_min": 5, "outcome": "accepted"}] for n in range(1, 5)}, "reworks": []}
            proven = evolution.propose_settings([wide], {"scheduler.max_parallel_tasks": 3})
            self.assertTrue(proven[0]["apply"], proven)                                    # four independent tasks do gain from a 4th slot
            lines = evolution.apply_proven(proven, tmp, changed.__setitem__)
            self.assertEqual((changed, len(lines)), ({"scheduler.max_parallel_tasks": 4}, 1))
            self.assertEqual(evolution.revert(tmp, changed.__setitem__), ["scheduler.max_parallel_tasks: back to 3"])
            self.assertEqual(changed, {"scheduler.max_parallel_tasks": 3})
            self.assertEqual(evolution.revert(tmp, changed.__setitem__), [])               # nothing left to undo
            out_of_bounds = [{**proven[0], "candidate": 99}]
            self.assertEqual(evolution.apply_proven(out_of_bounds, tmp, changed.__setitem__), [])   # outside the allowlist bounds

    def test_high_risk_proposals_become_numbered_pending_items_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdir = Path(tmp) / "proj"
            pdir.mkdir()
            (pdir / "PENDING.md").write_text("# proj — Pending\n\n## Open\n\n- P-007 · an older item · urgency: low · complexity: S · added 2026-10-01 · x\n\n## Blocked\n")
            props = [{"key": "planner-purposes", "risk": "high", "title": "Use the criterion text", "evidence": "3 stops", "change": None},
                     {"key": "exclusive-scopes", "risk": "low", "title": "drop it", "evidence": "x", "change": {"key": "k", "value": 1}}]
            first = evolution.file_proposals(pdir, props, today="2026-10-22")
            again = evolution.file_proposals(pdir, props, today="2026-10-22")
            text = (pdir / "PENDING.md").read_text()
        self.assertEqual((first, again), (["P-008"], []))
        self.assertIn("[evolution:planner-purposes]", text)
        self.assertNotIn("exclusive-scopes", text)                                        # a low-risk proposal is not a pending item
        self.assertLess(text.index("P-008"), text.index("## Blocked"))


if __name__ == "__main__":
    unittest.main()
