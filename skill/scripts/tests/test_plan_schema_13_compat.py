"""Frozen and live pre-1.3 plans must keep their exact Planner behaviour."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
REPO = SCRIPTS.parents[1]


class PlanSchema13Compatibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        current_path = SCRIPTS / ("bt_" + "planner")
        current_spec = importlib.util.spec_from_file_location("current_planner", current_path / "__init__.py",
                                                              submodule_search_locations=[str(current_path)])
        cls.current = importlib.util.module_from_spec(current_spec)
        sys.modules[current_spec.name] = cls.current
        current_spec.loader.exec_module(cls.current)
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp)
            result = subprocess.run(["git", "archive", "pre-engine-v2", "skill/scripts/bt_planner"],
                                    cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode:
                raise unittest.SkipTest("git tag pre-engine-v2 is unavailable")
            import tarfile
            import io
            with tarfile.open(fileobj=io.BytesIO(result.stdout)) as tar:
                tar.extractall(archive, filter="data")
            package_path = archive / "skill/scripts/bt_planner"
            spec = importlib.util.spec_from_file_location("baseline_planner", package_path / "__init__.py",
                                                          submodule_search_locations=[str(package_path)])
            cls.baseline = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = cls.baseline
            spec.loader.exec_module(cls.baseline)
        cls.plans = sorted((REPO / "bitacora").glob("*/requirements/*/PLAN.json"))
        cls.revisions = sorted((REPO / "bitacora").glob("*/requirements/*/plan-revisions/PLAN.r*.json"))

    def test_plan_files_match_tag_validation_and_canonical_bytes(self):
        self.assertTrue(self.plans, "expected live PLAN.json files")
        self.assertTrue(self.revisions, "expected frozen revision files")
        for path in [*self.plans, *self.revisions]:
            with self.subTest(path=path.relative_to(REPO)):
                plan = json.loads(path.read_text(encoding="utf-8"))
                old = self.baseline.validate(plan)
                new = self.current.contract.validate(plan)
                self.assertEqual((new.errors, new.warnings), (old.errors, old.warnings))
                new_bytes = self.current.contract.dumps(plan).encode("utf-8")
                old_bytes = self.baseline.dumps(plan).encode("utf-8")
                self.assertEqual(new_bytes, old_bytes)
                self.assertEqual(hashlib.sha256(new_bytes).hexdigest(), hashlib.sha256(old_bytes).hexdigest())

    def test_frozen_manifests_verify_and_no_plan_uses_schema_13_names(self):
        forbidden = {"subplans", "composition_gates"}
        for path in [*self.plans, *self.revisions]:
            with self.subTest(path=path):
                plan = json.loads(path.read_text(encoding="utf-8"))
                self.assertFalse(forbidden & set(plan))
                for task in plan.get("tasks", []):
                    self.assertFalse({"subplan_id", "ui"} & set(task))
                    for verification in task.get("verification", []):
                        self.assertFalse({"environment", "requires", "authorization_needed"} & set(verification))
        for manifest in (REPO / "bitacora").glob("*/requirements/*/plan-revisions/MANIFEST.json"):
            self.assertEqual(self.current.verify_store(manifest.parent.parent), [], str(manifest))


if __name__ == "__main__":
    unittest.main()
