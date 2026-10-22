from __future__ import annotations

import hashlib
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_recovery_authorization as auth


def digest(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def task_grant(**over):
    return {"case_id": "case-1", "case_hash": digest("case"), "proposal_hash": digest("proposal"),
            "source_sha256": digest("source"), "target_sha256": digest("target"), "scope": ["T4.1"],
            "accepted_map_digest": digest("accepted"), "base_digest": digest("base"), "stop_generation": 3,
            "cycle_token": "cycle-1", **over}


class AuthorizationLedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "RUN.recovery-authorization.db"
        self.ledger = auth.Ledger(self.path)

    def test_task_grant_is_stable_and_consumption_is_idempotent_across_restart(self):
        grant = task_grant()
        key = self.ledger.issue_task_grant(grant)
        self.assertEqual(self.ledger.issue_task_grant(grant), key)
        identities = {"source_sha256": grant["source_sha256"], "accepted_map_digest": grant["accepted_map_digest"],
                      "base_digest": grant["base_digest"], "stop_generation": grant["stop_generation"]}
        self.assertEqual(auth.Ledger(self.path).consume("task", key, "apply-1", identities), grant)
        self.assertEqual(self.ledger.consume("task", key, "apply-1", identities), grant)
        with self.assertRaises(auth.AuthorizationError):
            self.ledger.consume("task", key, "apply-2")
        with self.assertRaises(auth.AuthorizationError):
            self.ledger.consume("task", key, "apply-1", {"base_digest": digest("stale")})
        for name, value in (("source_sha256", digest("stale-source")),
                            ("accepted_map_digest", digest("stale-accepted")),
                            ("stop_generation", grant["stop_generation"] + 1)):
            with self.subTest(identity=name), self.assertRaises(auth.AuthorizationError):
                self.ledger.consume("task", key, "apply-1", {name: value})

    def test_concurrent_consumers_with_same_identity_all_observe_one_consumption(self):
        key = self.ledger.issue_task_grant(task_grant())
        barrier = threading.Barrier(8)

        def consume():
            barrier.wait()
            return auth.Ledger(self.path).consume("task", key, "same-consumer")

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: consume(), range(8)))
        self.assertEqual(len(results), 8)
        self.assertTrue(all(result["case_id"] == "case-1" for result in results))

    def test_supplemental_audit_is_unique_per_lineage_and_cycle(self):
        grant = {"case_id": "case-1", "case_hash": digest("case"), "cycle_token": "cycle-1",
                 "stop_generation": 3, "audit_lineage": "T8", "accepted_map_digest": digest("accepted"),
                 "base_digest": digest("base")}
        self.ledger.issue_supplementary_audit_grant(grant)
        with self.assertRaises(auth.AuthorizationError):
            self.ledger.issue_supplementary_audit_grant({**grant, "base_digest": digest("other")})

    def test_bootstrap_binds_order_sources_digests_and_stop_generation(self):
        grant = {"case_id": "case-1", "case_hash": digest("case"), "cycle_token": "cycle-1", "stop_generation": 3,
                 "order_id": "ord-1", "task_id": "T20", "plan_hash": digest("plan"),
                 "source_parents": [digest("left"), digest("right")], "conflict_tree": digest("tree"),
                 "base": digest("base"), "marker_path_digest": digest("markers"),
                 "accepted_map_digest": digest("accepted")}
        key = self.ledger.issue_conflict_bootstrap_grant(grant)
        order = {"grant_key": key, "order_id": "ord-1", "task_id": "T20", "source_parents": grant["source_parents"],
                 "conflict_tree": grant["conflict_tree"], "base": grant["base"],
                 "marker_path_digest": grant["marker_path_digest"]}
        identities = {name: grant[name] for name in ("case_id", "cycle_token", "plan_hash", "accepted_map_digest", "stop_generation")}
        self.assertEqual(self.ledger.consume_bootstrap(order, identities), grant)
        with self.assertRaises(auth.AuthorizationError):
            self.ledger.consume_bootstrap({**order, "order_id": "other"}, identities)
        for name, value in (("source_parents", [digest("left"), digest("tampered-right")]),
                            ("conflict_tree", digest("tampered-tree")), ("base", digest("tampered-base")),
                            ("marker_path_digest", digest("tampered-markers"))):
            with self.subTest(order_field=name), self.assertRaises(auth.AuthorizationError):
                self.ledger.consume_bootstrap({**order, name: value}, identities)
        for name, value in (("plan_hash", digest("stale-plan")), ("accepted_map_digest", digest("stale-map")),
                            ("stop_generation", identities["stop_generation"] + 1)):
            with self.subTest(identity=name), self.assertRaises(auth.AuthorizationError):
                self.ledger.consume_bootstrap(order, {**identities, name: value})

    def test_bootstrap_rejects_malformed_captured_tree_digest(self):
        grant = {"case_id": "case-1", "case_hash": digest("case"), "cycle_token": "cycle-1", "stop_generation": 3,
                 "order_id": "ord-1", "task_id": "T20", "plan_hash": digest("plan"),
                 "source_parents": [digest("left"), digest("right")], "conflict_tree": "not-a-digest",
                 "base": digest("base"), "marker_path_digest": digest("markers"),
                 "accepted_map_digest": digest("accepted")}
        with self.assertRaises(auth.AuthorizationError):
            self.ledger.issue_conflict_bootstrap_grant(grant)


if __name__ == "__main__":
    unittest.main()
