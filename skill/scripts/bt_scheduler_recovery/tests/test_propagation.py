import unittest

from bt_scheduler_recovery import DemonstratedFrontier, RecoveryError


def frontier(action="modify", tasks=None):
    return {
        "schema_version": "m5.demonstrated-frontier/1",
        "change_id": "change-1",
        "source_task_id": "T1",
        "composition_id": "C7",
        "manifest_sha256": "a" * 64,
        "tree_digest": "b" * 40,
        "action": action,
        "frontier": list(tasks if tasks is not None else (["T2"] if action != "none" else [])),
        "evidence_refs": ["m6:" + "c" * 64],
    }


class PropagationTests(unittest.TestCase):
    def test_internal_change_has_no_consumer_action(self):
        result = DemonstratedFrontier.from_dict(frontier("none"))
        self.assertEqual((result.action, result.frontier), ("none", ()))
        self.assertEqual(result.to_dict(), frontier("none"))

    def test_only_composition_demonstrated_frontier_is_returned(self):
        result = DemonstratedFrontier.from_dict(frontier("reverify", ["T2", "T5"]))
        self.assertEqual(result.frontier, ("T2", "T5"))
        for action in ("reintegrate", "audit", "adapt_contract", "modify", "reimplement"):
            self.assertEqual(DemonstratedFrontier.from_dict(frontier(action)).action, action)

    def test_invalid_or_ancestry_expanded_frontiers_are_refused(self):
        for raw in (
            frontier("modify", []),
            {**frontier("none"), "frontier": ["T2"]},
            {**frontier("modify"), "frontier": ["T2", "T2"]},
            {**frontier("modify"), "action": "reset_descendants"},
            {**frontier("modify"), "tree_digest": "bad"},
            {**frontier("modify"), "unexpected": "field"},
        ):
            with self.subTest(raw=raw), self.assertRaises(RecoveryError):
                DemonstratedFrontier.from_dict(raw)


if __name__ == "__main__":
    unittest.main()
