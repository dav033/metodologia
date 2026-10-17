from __future__ import annotations

import ast
import hashlib
import io
import json
import shutil
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

from support import make_store, write_json

from plan_bench import (
    RUBRIC_SHA256,
    BenchmarkError,
    build_report,
    load_rubric,
    parse_check_output,
    parse_quality_report,
    verify_store,
)
from plan_bench.contract import case_input_sha256, strict_json_loads
from plan_bench.storage import MAX_JSON_BYTES

PACKAGE = Path(__file__).resolve().parents[1]


def _snapshot_tar(members: dict[str, bytes], *, symlinks: dict[str, str] | None = None) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        for name, raw in members.items():
            member = tarfile.TarInfo(name)
            member.size = len(raw)
            archive.addfile(member, io.BytesIO(raw))
        for name, target in (symlinks or {}).items():
            member = tarfile.TarInfo(name)
            member.type = tarfile.SYMTYPE
            member.linkname = target
            archive.addfile(member)
    return buffer.getvalue()


class PlannerBenchmarkModuleTests(unittest.TestCase):
    def test_pinned_rubric_and_readme_match_the_public_api(self):
        rubric = load_rubric()
        readme = (PACKAGE / "README.md").read_text(encoding="utf-8")
        self.assertEqual(hashlib.sha256((PACKAGE / "data" / "rubric-v1.json").read_bytes()).hexdigest(), RUBRIC_SHA256)
        self.assertEqual(rubric["version"], "1.0.0")
        for name in ("validate_manifest", "verify_store", "score_store", "build_report", "load_rubric",
                     "parse_check_output", "parse_quality_report"):
            self.assertIn(name, readme)

    def test_strict_json_rejects_duplicate_keys_and_nonfinite_values(self):
        with self.assertRaises(BenchmarkError) as duplicate:
            strict_json_loads(b'{"a":1,"a":2}', "test")
        self.assertEqual(duplicate.exception.code, "JSON_DUPLICATE_KEY")
        with self.assertRaises(BenchmarkError) as nonfinite:
            strict_json_loads(b'{"a":NaN}', "test")
        self.assertEqual(nonfinite.exception.code, "JSON_NONFINITE")

    def test_planner_json_outputs_are_validated_and_keep_the_120_fields(self):
        check = parse_check_output('{"ok":false,"errors":["T1 is invalid"],"warnings":[]}')
        self.assertEqual(check["errors"], ["T1 is invalid"])
        with self.assertRaises(BenchmarkError) as raised:
            parse_check_output('{"ok":true,"errors":["bad"],"warnings":[]}')
        self.assertEqual(raised.exception.code, "PLANNER_REPORT_INVALID")

        report = {
            "tasks": 1, "milestones": 1, "total_minutes": 30,
            "critical_path": {"tasks": ["T1"], "minutes": 30}, "widest_level": 1,
            "distribution": {key: {} for key in ("complexity", "scope", "risk", "coupling", "confidence")},
            "without_command_verification": [], "low_confidence": [], "with_evidence": [],
            "unordered_conflicts": [], "unordered_shared": [], "unconsumed_results": [], "redundant_edges": [],
            "coverage": {"R1": ["T1"]}, "interfaces": [{"id": "IF-1"}],
            "verification_categories": {"R1": {"categories": ["test"], "verifications": [],
                                                 "planned_work": [], "manual_only": False}},
            "criteria_without_command": [{"task_id": "T1", "criterion": "runs", "reason": "no_command",
                                          "m6_criterion_status": "NEEDS_REVIEW", "verification_indexes": []}],
        }
        parsed = parse_quality_report(json.dumps(report))
        for field in ("coverage", "interfaces", "verification_categories", "criteria_without_command"):
            self.assertEqual(parsed[field], report[field])

    def test_planner_quality_report_rejects_missing_or_mistyped_fields(self):
        with self.assertRaises(BenchmarkError) as missing:
            parse_quality_report("{}")
        self.assertEqual(missing.exception.code, "PLANNER_REPORT_INVALID")

        raw = json.dumps({"tasks": True})
        with self.assertRaises(BenchmarkError) as malformed:
            parse_quality_report(raw)
        self.assertEqual(malformed.exception.code, "PLANNER_REPORT_INVALID")

    def test_verify_accepts_frozen_manifest_before_any_cells_exist(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "store"
            make_store(root)
            result = verify_store(root)
            self.assertEqual(result["cells"], [])
            self.assertEqual(result["reviews"], [])
            self.assertEqual(len(result["manifest_sha256"]), 64)

    def test_manifest_hash_failure_precedes_cell_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "store"
            make_store(root)
            (root / "runs").mkdir()
            (root / "runs" / "unexpected").mkdir()
            (root / "manifest.json").write_text("{}\n", encoding="utf-8")
            with self.assertRaises(BenchmarkError) as raised:
                verify_store(root)
            self.assertEqual(raised.exception.code, "MANIFEST_HASH_MISMATCH")

    def test_manifest_requires_repository_digest_to_pin_the_workspace_archive(self):
        mutations = ("missing", "mismatch")
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "store"
                manifest = make_store(root)
                case = manifest["cases"][0]
                snapshot_path = f"workspaces/{case['case_id']}/source.tar"
                if mutation == "missing":
                    case["input_files"] = [entry for entry in case["input_files"] if entry["path"] != snapshot_path]
                else:
                    case["repository_sha256"] = "0" * 64
                case["input_sha256"] = case_input_sha256(case)
                raw = write_json(root / "manifest.json", manifest)
                (root / "manifest.sha256").write_text(hashlib.sha256(raw).hexdigest() + "\n", encoding="ascii")
                with self.assertRaises(BenchmarkError) as raised:
                    verify_store(root)
                self.assertEqual(raised.exception.code, "MANIFEST_INVALID")
                self.assertIn(snapshot_path, str(raised.exception))

    def test_large_repository_snapshot_hash_is_stream_verified(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "store"
            manifest = make_store(root)
            case = manifest["cases"][0]
            entry = next(item for item in case["input_files"] if item["path"].endswith("/source.tar"))
            snapshot = root / entry["path"]
            size = MAX_JSON_BYTES + 1
            snapshot_raw = _snapshot_tar({"src/large.bin": b"\0" * size})
            snapshot.write_bytes(snapshot_raw)
            entry["sha256"] = hashlib.sha256(snapshot_raw).hexdigest()
            case["repository_sha256"] = entry["sha256"]
            case["input_sha256"] = case_input_sha256(case)
            raw = write_json(root / "manifest.json", manifest)
            (root / "manifest.sha256").write_text(hashlib.sha256(raw).hexdigest() + "\n", encoding="ascii")
            result = verify_store(root)
            self.assertEqual(result["cells"], [])

    def test_workspace_archive_rejects_oracles_links_and_unsafe_paths(self):
        archives = (
            (_snapshot_tar({"bitacora/metodologia/PLAN.md": b"hidden plan"}), "forbidden path"),
            (_snapshot_tar({"skill/scripts/bt_planner/tests/scenarios/C4/EXPECT.json": b"oracle"}), "forbidden path"),
            (_snapshot_tar({"config/.env.production": b"secret"}), "environment file"),
            (_snapshot_tar({"../../outside.txt": b"outside"}), "unsafe archive path"),
            (_snapshot_tar({}, symlinks={"src/escape": "../../bitacora"}), "contains a link"),
        )
        for snapshot_raw, expected_message in archives:
            with self.subTest(expected_message=expected_message), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "store"
                manifest = make_store(root)
                case = manifest["cases"][0]
                entry = next(item for item in case["input_files"] if item["path"].endswith("/source.tar"))
                (root / entry["path"]).write_bytes(snapshot_raw)
                entry["sha256"] = hashlib.sha256(snapshot_raw).hexdigest()
                case["repository_sha256"] = entry["sha256"]
                case["input_sha256"] = case_input_sha256(case)
                raw = write_json(root / "manifest.json", manifest)
                (root / "manifest.sha256").write_text(hashlib.sha256(raw).hexdigest() + "\n", encoding="ascii")
                with self.assertRaises(BenchmarkError) as raised:
                    verify_store(root)
                self.assertEqual(raised.exception.code, "WORKSPACE_ARCHIVE_INVALID")
                self.assertIn(expected_message, str(raised.exception))

    def test_manifest_run_order_rejects_boolean_replicate_ids(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "store"
            manifest = make_store(root)
            manifest["run_order"][0]["replicate"] = True
            raw = write_json(root / "manifest.json", manifest)
            (root / "manifest.sha256").write_text(hashlib.sha256(raw).hexdigest() + "\n", encoding="ascii")
            with self.assertRaises(BenchmarkError) as raised:
                verify_store(root)
            self.assertEqual(raised.exception.code, "MANIFEST_INVALID")

    def test_manifest_requires_independent_reviewer_profiles_and_models(self):
        mutations = (
            ("profile_id", lambda value: value, "distinct profiles"),
            ("model_id", lambda value: value, "distinct models"),
            ("profile_id", lambda value: f"{value} ", "surrounding whitespace"),
            ("model_id", lambda value: f"{value} ", "surrounding whitespace"),
        )
        for field, mutate, message in mutations:
            with self.subTest(field=field, message=message), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "store"
                manifest = make_store(root)
                manifest["reviewers"][1][field] = mutate(manifest["reviewers"][0][field])
                raw = write_json(root / "manifest.json", manifest)
                (root / "manifest.sha256").write_text(hashlib.sha256(raw).hexdigest() + "\n", encoding="ascii")
                with self.assertRaises(BenchmarkError) as raised:
                    verify_store(root)
                self.assertEqual(raised.exception.code, "MANIFEST_INVALID")
                self.assertIn(message, str(raised.exception))

    def test_controlled_arms_require_the_same_profile_and_runtime(self):
        mutations = (
            ("profile_id", "claude-personal"),
            ("runtime_id", "other-cli"),
            ("runtime_version", "2.1.300"),
        )
        for field, value in mutations:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "store"
                manifest = make_store(root)
                manifest["arms"][1][field] = value
                raw = write_json(root / "manifest.json", manifest)
                (root / "manifest.sha256").write_text(hashlib.sha256(raw).hexdigest() + "\n", encoding="ascii")
                with self.assertRaises(BenchmarkError) as raised:
                    verify_store(root)
                self.assertEqual(raised.exception.code, "MANIFEST_CONTROL_MISMATCH")

    def test_cell_metadata_must_match_the_pinned_profile_and_runtime(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "store"
            manifest = make_store(root, write_cells=True)
            cell = manifest["run_order"][0]
            path = root / "runs" / cell["case_id"] / cell["arm_id"] / str(cell["replicate"]) / "meta.json"
            meta = _load_json(path)
            meta["profile_id"] = "claude-personal"
            write_json(path, meta)
            with self.assertRaises(BenchmarkError) as raised:
                verify_store(root)
            self.assertEqual(raised.exception.code, "CELL_CONTROL_MISMATCH")

    def test_all_scheduled_cells_and_plan_output_hashes_are_required(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "store"
            make_store(root, write_cells=True)
            shutil.rmtree(root / "runs" / "C5" / "B" / "3")
            with self.assertRaises(BenchmarkError) as raised:
                verify_store(root)
            self.assertEqual(raised.exception.code, "CELL_MISSING")

    def test_cell_directory_without_metadata_is_not_treated_as_an_empty_store(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "store"
            make_store(root)
            (root / "runs" / "C1" / "A" / "1").mkdir(parents=True)
            with self.assertRaises(BenchmarkError) as raised:
                verify_store(root)
            self.assertEqual(raised.exception.code, "CELL_MISSING")

    def test_cell_store_rejects_unapproved_files_and_symlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "store"
            manifest = make_store(root, write_cells=True)
            cell = manifest["run_order"][0]
            cell_path = root / "runs" / cell["case_id"] / cell["arm_id"] / str(cell["replicate"])
            (cell_path / "prompt.txt").write_text("private prompt", encoding="utf-8")
            with self.assertRaises(BenchmarkError) as raised:
                verify_store(root)
            self.assertEqual(raised.exception.code, "CELL_UNEXPECTED")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "store"
            manifest = make_store(root, write_cells=True)
            cell = manifest["run_order"][0]
            cell_path = root / "runs" / cell["case_id"] / cell["arm_id"] / str(cell["replicate"])
            target = cell_path / "PLAN.md"
            link = cell_path / "shadow.txt"
            link.symlink_to(target.name)
            with self.assertRaises(BenchmarkError) as raised:
                verify_store(root)
            self.assertEqual(raised.exception.code, "STORE_SYMLINK")

    def test_complete_cell_requires_observed_metrics(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "store"
            manifest = make_store(root, write_cells=True)
            cell = manifest["run_order"][0]
            cell_path = root / "runs" / cell["case_id"] / cell["arm_id"] / str(cell["replicate"])
            (cell_path / "observed.json").unlink()
            with self.assertRaises(BenchmarkError) as raised:
                verify_store(root)
            self.assertEqual(raised.exception.code, "STORE_FILE_MISSING")

    def test_every_observed_metric_requires_source_command_and_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "store"
            manifest = make_store(root, write_cells=True)
            cell = manifest["run_order"][0]
            cell_id = f"{cell['case_id']}-{cell['arm_id']}-{cell['replicate']}"
            path = root / "runs" / cell["case_id"] / cell["arm_id"] / str(cell["replicate"]) / "observed.json"
            observed = _load_json(path)
            observed["metrics"]["O3"].pop("source_command")
            write_json(path, observed)
            with self.assertRaises(BenchmarkError) as raised:
                verify_store(root)
            self.assertEqual(raised.exception.code, "METRIC_SOURCE_MISSING")
            self.assertIn(cell_id, str(raised.exception))

    def test_metric_source_artifact_hash_is_verified(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "store"
            manifest = make_store(root, write_cells=True)
            cell = manifest["run_order"][0]
            cell_path = root / "runs" / cell["case_id"] / cell["arm_id"] / str(cell["replicate"])
            (cell_path / "sources" / "O3.json").write_text("tampered\n", encoding="utf-8")
            with self.assertRaises(BenchmarkError) as raised:
                verify_store(root)
            self.assertEqual(raised.exception.code, "METRIC_SOURCE_HASH_MISMATCH")

    def test_scoring_keeps_metric_directions_separate_and_never_builds_overall_score(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "store"
            make_store(root, write_cells=True, write_reviews=True)
            report = build_report(root)
            self.assertEqual(report["status"], "complete")
            self.assertEqual(report["observed"]["directional_findings"]["O2"]["status"], "directional_difference")
            self.assertEqual(report["judged"]["directional_findings"]["J1"]["status"], "directional_difference")
            self.assertEqual(report["judged"]["directional_findings"]["J5_detection_rate"]["status"],
                             "directional_difference")
            self.assertEqual(report["execution_and_rework"]["status"], "not_measured")
            self.assertNotIn("overall_score", report)
            self.assertNotIn("aggregate_score", report)
            self.assertNotIn("overall_superiority", report)
            self.assertIn("O10", report["observed"]["stability"])

    def test_three_cases_are_descriptive_and_missing_cases_are_not_imputed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "store"
            make_store(root, included_cases=3, write_cells=True, write_reviews=True)
            report = build_report(root)
            self.assertEqual(report["status"], "incomplete")
            self.assertEqual(report["observed"]["directional_findings"]["O2"]["status"], "no_supported_difference")
            self.assertEqual(report["observed"]["directional_findings"]["O2"]["reason"],
                             "fewer_than_four_complete_cases")
            self.assertEqual(len(report["missing_cells"]), 0)

    def test_blind_reviews_require_two_reviewers_and_forbid_arm_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "store"
            make_store(root, write_cells=True, write_reviews=True)
            blind = next((root / "reviews").iterdir())
            (blind / "reviewer-2.json").unlink()
            with self.assertRaises(BenchmarkError) as raised:
                verify_store(root, reviews=True)
            self.assertEqual(raised.exception.code, "STORE_FILE_MISSING")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "store"
            make_store(root, write_cells=True, write_reviews=True)
            blind = next((root / "reviews").iterdir())
            path = blind / "reviewer-1.json"
            review = _load_json(path)
            review["arm_id"] = "A"
            write_json(path, review)
            with self.assertRaises(BenchmarkError) as raised:
                verify_store(root, reviews=True)
            self.assertEqual(raised.exception.code, "REVIEW_INVALID")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "store"
            make_store(root, write_cells=True, write_reviews=True)
            map_path = root / "review-map.private.json"
            mapping = _load_json(map_path)
            mapping["outputs"][0]["output_id"] = ["malformed"]
            write_json(map_path, mapping)
            with self.assertRaises(BenchmarkError) as raised:
                verify_store(root, reviews=True)
            self.assertEqual(raised.exception.code, "REVIEW_INVALID")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "store"
            make_store(root, write_cells=True, write_reviews=True)
            blind = next((root / "reviews").iterdir())
            path = blind / "reviewer-1.json"
            review = _load_json(path)
            review["scores"]["J1"]["score"] = 1.0
            write_json(path, review)
            with self.assertRaises(BenchmarkError) as raised:
                verify_store(root, reviews=True)
            self.assertEqual(raised.exception.code, "REVIEW_INVALID")

    def test_unapproved_metadata_fields_cannot_smuggle_raw_prompt_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "store"
            manifest = make_store(root, write_cells=True)
            cell = manifest["run_order"][0]
            path = root / "runs" / cell["case_id"] / cell["arm_id"] / str(cell["replicate"]) / "meta.json"
            meta = _load_json(path)
            meta["raw_prompt"] = "private content"
            write_json(path, meta)
            with self.assertRaises(BenchmarkError) as raised:
                verify_store(root)
            self.assertEqual(raised.exception.code, "CELL_INVALID")

    def test_package_imports_only_the_standard_library_and_itself(self):
        stdlib = set(sys.stdlib_module_names)
        for path in PACKAGE.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = {alias.name.split(".")[0] for alias in node.names}
                    self.assertTrue(names <= (stdlib | {"plan_bench"}), path.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    self.assertTrue(node.level > 0 or node.module.split(".")[0] in (stdlib | {"plan_bench"}),
                                    f"{path.name}:{node.lineno} imports {node.module}")

def _load_json(path: Path):
    import json
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
