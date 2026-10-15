from __future__ import annotations

import json
import unittest
from pathlib import Path

from bt_scheduler_benchmark import FixtureError, laya_payload, load_fixtures

REQ = Path(__file__).resolve().parents[3] / "bitacora" / "metodologia" / "requirements" / \
      "REQ-013-scheduler-m2-decision-engine-with-local"


class SchedulerBenchmarkFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus, cls.manifest = load_fixtures(REQ / "fixtures-v1.json", REQ / "fixture-manifest-v1.json")

    def test_frozen_corpus_has_disjoint_calibration_and_heldout_splits(self):
        cases = self.corpus["cases"]
        self.assertEqual(len(cases), 200)
        self.assertTrue(self.manifest["frozen_before_first_laya_call"])
        self.assertEqual(len(self.manifest["calibration_case_ids"]), 100)
        self.assertEqual(len(self.manifest["held_out_case_ids"]), 100)
        self.assertFalse(set(self.manifest["calibration_case_ids"]) & set(self.manifest["held_out_case_ids"]))
        self.assertEqual(self.manifest["duplicate_canonical_task_digests_across_splits"], 0)

    def test_model_payload_contains_no_labels_or_utilities(self):
        case = self.corpus["cases"][0]
        payload, labels = laya_payload(case)
        encoded = json.dumps(payload, sort_keys=True)
        self.assertNotIn("oracle_route_id", encoded)
        self.assertNotIn("oracle_utilities", encoded)
        self.assertNotIn("deterministic_route_id", encoded)
        self.assertEqual(set(labels.values()), set(case["eligible_route_ids"]))
        self.assertTrue(all("eligible_candidates" in payload["state"] for _ in (0,)))

    def test_laya_payload_uses_route_order_not_baseline_order(self):
        case = next(item for item in self.corpus["cases"] if item["options"] != sorted(
            item["options"], key=lambda row: row["route_id"]))
        payload, labels = laya_payload(case)
        self.assertEqual(list(labels.values()), sorted(labels.values()))
        self.assertEqual(len(payload["questions"]["decision"]["criteria"]), len(case["options"]))
        self.assertIn("eligible_candidates", payload["state"])

    def test_changed_dataset_bytes_fail_closed_against_frozen_manifest(self):
        path = REQ / "fixtures-v1.json"
        original = path.read_bytes()
        self.assertIn(self.manifest["dataset_sha256"].encode(), json.dumps(self.manifest).encode())
        with self.assertRaises(FixtureError):
            import tempfile

            from bt_scheduler_benchmark import load_fixtures
            with tempfile.TemporaryDirectory() as temporary:
                altered = Path(temporary) / "fixtures.json"
                altered.write_bytes(original + b" ")
                load_fixtures(altered, REQ / "fixture-manifest-v1.json")


if __name__ == "__main__":
    unittest.main()
