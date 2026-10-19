from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bt_scheduler_quality.contracts import VerifyRequest
from bt_scheduler_quality.engine import QualityEngine
from bt_scheduler_quality.evidence import validate_result_contract
from bt_scheduler_quality.policy import QualityPolicy
from bt_scheduler_quality.runner import CommandOutcome
from bt_scheduler_quality.store import QualityStore
from test_snapshot import _make_snapshot

ORDER_FIXTURE = Path(__file__).parent / "fixtures" / "verify-order-pass.json"


class ScriptedRunner:
    def __init__(self, status="pass", exit_code=0):
        self.status, self.exit_code = status, exit_code
        self.calls = []

    def run(self, check, snapshot_root, *, timeout_seconds=None, mounts=()):
        self.calls.append((check.id, timeout_seconds))
        return CommandOutcome(
            self.status,
            self.exit_code,
            4,
            b"unit suite evidence\n",
            b"",
            None,
            True,
            False,
            (
                ("mnt", 4026533000),
                ("net", 4026533001),
                ("pid", 4026533002),
                ("ipc", 4026533003),
                ("uts", 4026533004),
            ),
        )


class QualityEngineTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads(ORDER_FIXTURE.read_text(encoding="utf-8"))

    def test_exactly_mapped_passing_check_produces_content_addressed_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo, source, _, _ = _make_snapshot(
                root, files={"check.py": "print('ok')\n"}
            )
            before_refs = _git(repo, "show-ref")
            before_head = _git(repo, "rev-parse", "HEAD")
            runner = ScriptedRunner()
            store = QualityStore(":memory:")
            engine = QualityEngine(QualityPolicy(), store, runner=runner)

            result = engine.verify(self.raw, source)
            manifest = store.get_result_manifest(result["evidence_manifest"])
            stdout = store.get_artifact(result["checks"][0]["stdout_ref"])

            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["criteria"][0]["status"], "pass")
            self.assertEqual(result["input"]["snapshot_sha"], source.snapshot_sha)
            self.assertEqual(result["input"]["base_sha"], source.base_sha)
            self.assertIn(b"unit suite evidence", stdout)
            self.assertIn(b"checks_sha256", manifest)
            validate_result_contract(result)
            self.assertEqual(_git(repo, "show-ref"), before_refs)
            self.assertEqual(_git(repo, "rev-parse", "HEAD"), before_head)
            store.close()

    def test_nonzero_required_check_produces_fail_not_a_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, source, _, _ = _make_snapshot(root)
            runner = ScriptedRunner("fail", 3)
            with QualityStore(":memory:") as store:
                result = QualityEngine(QualityPolicy(), store, runner=runner).verify(
                    self.raw, source
                )

        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["checks"][0]["exit_code"], 3)
        self.assertEqual(result["criteria"][0]["status"], "fail")

    def test_completed_nonzero_check_is_fail_even_when_its_mapping_is_invalid(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, source, _, _ = _make_snapshot(root)
            self.raw["verification"][0]["purpose"] = "unmapped check"
            with QualityStore(":memory:") as store:
                result = QualityEngine(
                    QualityPolicy(), store, runner=ScriptedRunner("fail", 7)
                ).verify(self.raw, source)

        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["checks"][0]["exit_code"], 7)
        self.assertIn("CHECK_UNMAPPED", {item["code"] for item in result["issues"]})

    def test_manual_check_and_unmapped_check_remain_needs_review(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, source, _, _ = _make_snapshot(root)
            self.raw["verification"] = [
                {
                    "type": "manual",
                    "value": "inspect the image",
                    "purpose": "unit tests pass",
                    "expected": "no layout defects",
                }
            ]
            runner = ScriptedRunner()
            with QualityStore(":memory:") as store:
                result = QualityEngine(QualityPolicy(), store, runner=runner).verify(
                    self.raw, source
                )

        self.assertEqual(result["status"], "NEEDS_REVIEW")
        self.assertEqual(result["criteria"][0]["status"], "unknown")
        self.assertEqual(runner.calls, [])

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, source, _, _ = _make_snapshot(root)
            self.raw["verification"][0] = {
                "type": "command",
                "value": "python3 -m unittest -q",
                "purpose": "a different criterion",
            }
            with QualityStore(":memory:") as store:
                result = QualityEngine(
                    QualityPolicy(), store, runner=ScriptedRunner()
                ).verify(self.raw, source)

        self.assertEqual(result["status"], "NEEDS_REVIEW")
        self.assertIn("CHECK_UNMAPPED", {item["code"] for item in result["issues"]})

    def test_multiple_checks_for_one_criterion_are_ambiguous(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, source, _, _ = _make_snapshot(root)
            self.raw["verification"].append(
                dict(self.raw["verification"][0], value="python3 another.py")
            )
            runner = ScriptedRunner()
            with QualityStore(":memory:") as store:
                result = QualityEngine(QualityPolicy(), store, runner=runner).verify(
                    self.raw, source
                )

        self.assertEqual(result["status"], "NEEDS_REVIEW")
        self.assertEqual(result["criteria"][0]["status"], "unknown")
        self.assertIn(
            "CRITERION_AMBIGUOUS", {item["code"] for item in result["issues"]}
        )
        self.assertEqual(len(runner.calls), 2)

    def test_the_same_command_serving_several_criteria_runs_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, source, _, _ = _make_snapshot(root)
            self.raw["acceptance_criteria"] = ["first criterion", "second criterion"]
            self.raw["verification"] = [
                dict(self.raw["verification"][0], purpose="first criterion"),
                dict(self.raw["verification"][0], purpose="second criterion"),
            ]
            runner = ScriptedRunner()
            with QualityStore(":memory:") as store:
                result = QualityEngine(QualityPolicy(), store, runner=runner).verify(
                    self.raw, source
                )

        self.assertEqual(result["status"], "PASS")
        self.assertEqual([item["status"] for item in result["criteria"]], ["pass", "pass"])
        self.assertEqual(len(runner.calls), 1)

    def test_duplicate_request_returns_persisted_result_without_rerunning_checks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, source, _, _ = _make_snapshot(root)
            runner = ScriptedRunner()
            with QualityStore(":memory:") as store:
                engine = QualityEngine(QualityPolicy(), store, runner=runner)
                first = engine.verify(self.raw, source)
                second = engine.verify(self.raw, source)

        self.assertEqual(first, second)
        self.assertEqual(len(runner.calls), 1)

    def test_unsupported_shell_command_is_not_partially_executed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, source, _, _ = _make_snapshot(root)
            self.raw["verification"][0]["value"] = "python3 check.py && echo unsafe"
            runner = ScriptedRunner()
            with QualityStore(":memory:") as store:
                result = QualityEngine(QualityPolicy(), store, runner=runner).verify(
                    self.raw, source
                )

        self.assertEqual(result["status"], "NEEDS_REVIEW")
        self.assertIn("CHECK_UNSUPPORTED", {item["code"] for item in result["issues"]})
        self.assertEqual(runner.calls, [])

    def test_production_deployment_or_migration_stays_for_operator_review(self):
        for command in ("npm run deploy:production", "alembic upgrade head"):
            with (
                self.subTest(command=command),
                tempfile.TemporaryDirectory() as temporary,
            ):
                root = Path(temporary)
                _, source, _, _ = _make_snapshot(root)
                self.raw["verification"][0]["value"] = command
                runner = ScriptedRunner()
                with QualityStore(":memory:") as store:
                    result = QualityEngine(
                        QualityPolicy(), store, runner=runner
                    ).verify(self.raw, source)

            self.assertEqual(result["status"], "NEEDS_REVIEW")
            self.assertIn(
                "CHECK_PRODUCTION_ACTION", {item["code"] for item in result["issues"]}
            )
            self.assertEqual(runner.calls, [])

    def test_missing_handoff_returns_review_with_null_snapshot_ids(self):
        with QualityStore(":memory:") as store:
            runner = ScriptedRunner()
            result = QualityEngine(QualityPolicy(), store, runner=runner).verify(
                self.raw, None
            )

        self.assertEqual(result["status"], "NEEDS_REVIEW")
        self.assertIsNone(result["input"]["base_sha"])
        self.assertIsNone(result["input"]["snapshot_sha"])
        self.assertEqual(runner.calls, [])
        validate_result_contract(result)

    def test_startup_recovery_persists_interrupted_request_without_replaying_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "quality.sqlite3"
            request = VerifyRequest.from_mapping(self.raw)
            first_store = QualityStore(database)
            first_store.reserve(request)
            first_store.claim_work(request.idempotency_key)
            first_store.close()

            restarted_store = QualityStore(database)
            runner = ScriptedRunner()
            engine = QualityEngine(QualityPolicy(), restarted_store, runner=runner)
            recovered = engine.recover_interrupted()
            result = restarted_store.get_result(request.idempotency_key)
            restarted_store.close()

        self.assertEqual(recovered, (request.idempotency_key,))
        self.assertEqual(result["status"], "NEEDS_REVIEW")
        self.assertIsNone(result["input"]["base_sha"])
        self.assertIn("ENGINE_INTERRUPTED", {item["code"] for item in result["issues"]})
        self.assertEqual(runner.calls, [])


def _git(repo: Path, *arguments: str) -> str:
    import os
    import subprocess

    result = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        env={
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": "/nonexistent",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
        },
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )
    return result.stdout.strip()


if __name__ == "__main__":
    unittest.main()
