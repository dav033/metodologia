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
        inside = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=REPO,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if inside.returncode or inside.stdout.strip() != "true":
            raise unittest.SkipTest("compatibility comparison requires a git checkout")
        tag = subprocess.run(["git", "rev-parse", "--verify", "refs/tags/pre-engine-v2"], cwd=REPO,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if tag.returncode:
            raise AssertionError("git tag pre-engine-v2 is required inside a git checkout")
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp)
            result = subprocess.run(["git", "archive", "pre-engine-v2", "skill/scripts/bt_planner"],
                                    cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode:
                raise AssertionError(f"cannot extract required pre-engine-v2 tag: {result.stderr.decode(errors='replace')}")
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
        # Plans that declare 1.3.0 postdate the tag, which cannot read them; they are compared with the current planner,
        # the runtime loader and the typed contract by test_plan_contract_models. Everything older stays pinned here.
        cls.schema_13 = []
        cls.plans, cls.revisions = [], []
        for target, pattern in ((cls.plans, "*/requirements/*/PLAN.json"),
                                (cls.revisions, "*/requirements/*/plan-revisions/PLAN.r*.json")):
            for path in sorted((REPO / "bitacora").glob(pattern)):
                declared = json.loads(path.read_text(encoding="utf-8")).get("schema_version")
                (cls.schema_13 if cls.current.contract.schema_tuple({"schema_version": declared}) >= (1, 3, 0)
                 else target).append(path)

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

    def test_only_plans_that_declare_schema_13_are_left_to_the_current_readers(self):
        for path in self.schema_13:
            with self.subTest(path=path.relative_to(REPO)):
                plan = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(plan.get("schema_version"), self.current.contract.LATEST_SCHEMA_VERSION)

    def test_synthetic_legacy_plans_match_tag_with_schema_13_names(self):
        golden = SCRIPTS / ("bt_" + "planner") / "tests" / "golden"
        for version in ("1.0.0", "1.1.0", "1.2.0"):
            plan = json.loads((golden / f"input-{version}.json").read_text(encoding="utf-8"))
            plan["subplans"] = []
            plan["composition_gates"] = []
            task = plan["tasks"][0]
            task["subplan_id"] = "SP-1"
            task["ui"] = False
            task["kind"] = "design"
            for verification in task["verification"]:
                verification["environment"] = "sandbox"
                verification["requires"] = ["DATABASE_URL"]
                verification["authorization_needed"] = "Owner approves a later production check"
            with self.subTest(schema_version=version):
                old = self.baseline.validate(plan)
                consumer = self.current.contract.validate(plan)
                self.assertEqual((consumer.errors, consumer.warnings), (old.errors, old.warnings))
                publication = self.current.contract.validate(plan, strict_publication=True)
                self.assertTrue(any(line.startswith("SCHEMA_FIELD_UNSUPPORTED:") for line in publication.errors),
                                publication.errors)
                self.assertTrue(any(line.startswith("SCHEMA_FIELD_UNSUPPORTED:") and ".kind:" in line
                                    for line in publication.errors), publication.errors)
                self.assertFalse(any(line.startswith("SCHEMA_FIELD_UNSUPPORTED:") for line in consumer.errors),
                                 consumer.errors)


if __name__ == "__main__":
    unittest.main()
