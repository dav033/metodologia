from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bt_recovery_evidence import (collect_recovery_evidence, recovery_coverage_problems,
                                  validate_recovery_verification_map)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RecoveryEvidence(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("-c", "user.name=T", "-c", "user.email=t@t", "commit", "--allow-empty", "-qm", "base")
        self.base = self.git("rev-parse", "HEAD")
        (self.repo / "web").mkdir()
        (self.repo / "web/page.ts").write_text("export const attempt: Attempt = undefined;\n")
        self.git("add", "web/page.ts")
        self.git("-c", "user.name=T", "-c", "user.email=t@t", "commit", "-qm", "snapshot")
        self.snapshot = self.git("rev-parse", "HEAD")
        self.sources = self.root / "sources"
        self.sources.mkdir()
        self.audit = {"task_id": "T8", "plan_id": "REQ-029", "revision": 1, "prerequisite_status": "pass"}
        docs = {
            "m1": {"plan_id": "REQ-029", "revision": 1, "plan_sha256": "",
                   "attempts": [{"id": "att-1", "task_id": "T8", "state": "rejected"}]},
            "plan": {"plan_id": "REQ-029", "revision": 1, "tasks": [{"id": "T8"}]},
            "m6": {"identity": {"plan_id": "REQ-029", "revision": 1, "task_id": "T8", "attempt_id": "att-1",
                                 "plan_sha256": ""}, "checks": [{"command": "python3 test_smoke.py", "status": "pass", "exit_code": 0}]},
            "remediation": {"events": []},
        }
        for key, data in docs.items():
            (self.sources / f"{key}.json").write_text(json.dumps(data))
            self.audit[f"{key}_path"] = f"{key}.json"
            self.audit[f"{key}_sha256"] = sha(self.sources / f"{key}.json")
        m1 = json.loads((self.sources / "m1.json").read_text())
        m1["plan_sha256"] = self.audit["plan_sha256"]
        (self.sources / "m1.json").write_text(json.dumps(m1))
        self.audit["m1_sha256"] = sha(self.sources / "m1.json")
        self.attempt = {"attempt_id": "att-1", "manifest_path": "manifest.json", "repository": str(self.repo),
                        "base_sha": self.base, "snapshot_sha": self.snapshot}
        (self.sources / "manifest.json").write_text(json.dumps({"schema": 1, "status": "captured",
            "attempt_id": "att-1", "repository": str(self.repo), "base_sha": self.base,
            "snapshot_sha": self.snapshot}))
        self.attempt["manifest_sha256"] = sha(self.sources / "manifest.json")
        # The M6 plan identity binds the exact frozen PLAN document digest.
        m6 = json.loads((self.sources / "m6.json").read_text())
        m6["identity"]["plan_sha256"] = self.audit["plan_sha256"]
        (self.sources / "m6.json").write_text(json.dumps(m6))
        self.audit["m6_sha256"] = sha(self.sources / "m6.json")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], capture_output=True, text=True,
                              check=True).stdout.strip()

    def test_captures_pinned_snapshot_not_live_worktree_and_keeps_prerequisite_not_run_separate(self):
        evidence = collect_recovery_evidence(self.sources, self.audit, self.attempt)
        self.assertTrue(evidence["diagnosable"], evidence["validation_problems"])
        self.assertEqual(evidence["snapshot_ledger"]["snapshot_sha"], self.snapshot)
        self.assertEqual(evidence["snapshot_ledger"]["files"][0]["path"], "web/page.ts")
        (self.repo / "web/page.ts").write_text("changed current worktree")
        repeated = collect_recovery_evidence(self.sources, self.audit, self.attempt)
        self.assertEqual(evidence["snapshot_ledger"], repeated["snapshot_ledger"])
        self.audit["prerequisite_status"] = "fail"
        failed = collect_recovery_evidence(self.sources, self.audit, self.attempt)
        self.assertTrue(failed["diagnosable"])
        self.assertEqual(failed["not_run"], ["audit_gate_evaluation"])

    def test_mismatched_m6_plan_hash_blocks_diagnosis(self):
        m6 = json.loads((self.sources / "m6.json").read_text())
        m6["identity"]["plan_sha256"] = "e" * 64
        (self.sources / "m6.json").write_text(json.dumps(m6))
        self.audit["m6_sha256"] = sha(self.sources / "m6.json")
        evidence = collect_recovery_evidence(self.sources, self.audit, self.attempt)
        self.assertFalse(evidence["diagnosable"])
        self.assertIn("M6 identity or frozen plan hash mismatch", evidence["validation_problems"][0])

    def test_non_object_historical_sources_are_not_silently_skipped(self):
        for name in ("m1", "plan", "m6", "remediation"):
            (self.sources / f"{name}.json").write_text("[]")
            self.audit[f"{name}_sha256"] = sha(self.sources / f"{name}.json")
            evidence = collect_recovery_evidence(self.sources, self.audit, self.attempt)
            self.assertFalse(evidence["diagnosable"], name)
            self.assertTrue(evidence["validation_problems"], name)
            (self.sources / f"{name}.json").write_text("{}")
            self.audit[f"{name}_sha256"] = sha(self.sources / f"{name}.json")

    def test_wrong_base_and_missing_sources_block_evidence(self):
        manifest = {"schema": 1, "status": "captured", "attempt_id": "att-1", "repository": str(self.repo),
                    "base_sha": "0" * 40, "snapshot_sha": self.snapshot}
        (self.sources / "manifest.json").write_text(json.dumps(manifest))
        self.attempt["manifest_sha256"] = sha(self.sources / "manifest.json")
        self.attempt["base_sha"] = manifest["base_sha"]
        evidence = collect_recovery_evidence(self.sources, self.audit, self.attempt)
        self.assertFalse(evidence["diagnosable"])
        self.assertIn("does not descend", evidence["validation_problems"][0])
        self.audit["m1_path"] = "missing.json"
        evidence = collect_recovery_evidence(self.sources, self.audit, self.attempt)
        self.assertFalse(evidence["diagnosable"])
        self.assertTrue(evidence["validation_problems"])

    def test_smoke_stdout_cannot_claim_a_web_check(self):
        plan = {"tasks": [{"id": "T1", "expected_paths": ["web"],
                            "verification": [{"value": "python3 web/typecheck.py"}]}]}
        result_checks = [{"id": "smoke", "command": "python3 test_smoke.py", "status": "pass", "exit_code": 0,
                          "stdout": "verify: python3 web/typecheck.py"}]
        map_data = {"schema_version": "recovery-verification-map/1",
                    "changed_paths": [{"path": "web/page.ts", "source_digest": "d" * 64,
                                       "owner_task_id": "T1"}],
                    "existing_owner_commands": ["python3 web/typecheck.py"], "uncovered_paths": [],
                    "uncovered_checks": [],
                    "checks": [{"check_id": "typecheck", "owner_task_id": "T1", "command": "python3 web/typecheck.py",
                                "symptom": "web_typecheck", "verdict_identity": "m6:" + "a" * 64}]}
        problems = validate_recovery_verification_map(("web/page.ts",), map_data, plan, result_checks,
                                                      "m6:" + "a" * 64)
        self.assertTrue(any("executed independent" in problem for problem in problems))
        result_checks.append({"id": "typecheck", "command": "python3 web/typecheck.py", "status": "pass", "exit_code": 0})
        self.assertEqual(validate_recovery_verification_map(("web/page.ts",), map_data, plan, result_checks,
                                                            "m6:" + "a" * 64), ())
        self.assertTrue(validate_recovery_verification_map(("web/page.ts", "server/api.py"), map_data, plan,
                                                           result_checks, "m6:" + "a" * 64))

    def test_scheduler_recovery_guard_checks_the_pinned_map_before_acceptance(self):
        snapshot_root = self.root / "pinned"
        snapshot_root.mkdir()
        (snapshot_root / "web").mkdir()
        (snapshot_root / "web/page.ts").write_text("export const attempt: Attempt = undefined;\n")
        map_data = {"schema_version": "recovery-verification-map/1",
                    "changed_paths": [{"path": "web/page.ts", "source_digest": hashlib.sha256(
                        b"export const attempt: Attempt = undefined;\n").hexdigest(), "owner_task_id": "T1"}],
                    "existing_owner_commands": ["python3 web/typecheck.py"], "uncovered_paths": [],
                    "uncovered_checks": [],
                    "checks": [{"check_id": "typecheck", "owner_task_id": "T1", "command": "python3 web/typecheck.py",
                                "symptom": "web_typecheck", "verdict_identity": "m6:" + "a" * 64}]}
        (snapshot_root / "recovery-verification-map.json").write_text(json.dumps(map_data))

        class Resolver:
            @contextmanager
            def materialize(self, _source):
                yield SimpleNamespace(directory=snapshot_root)

        state = SimpleNamespace(tasks={"T1": SimpleNamespace(attempts=["old", "new"])},
                                attempts={"old": SimpleNamespace(failure="audit-gate: F7")})
        core = SimpleNamespace(read=lambda fn: fn(SimpleNamespace(state=state)),
            plan=SimpleNamespace(tasks=[SimpleNamespace(id="T1", expected_paths=("web",),
                                                          verification=({"value": "python3 web/typecheck.py"},))]))
        # The process output mentions typecheck, while the check M6 ran was only the backend smoke command.
        result = {"evidence_manifest": "m6://result/" + "a" * 64, "checks":[{"id":"smoke",
                  "command":"python3 test_smoke.py",
                  "status":"pass", "exit_code":0, "stdout":"verify: python3 web/typecheck.py"}]}
        problems = recovery_coverage_problems(core, SimpleNamespace(task_id="T1"), result, Resolver(),
                                              lambda _order: object(), lambda _order: ("web/page.ts",))
        self.assertTrue(any("executed independent" in item for item in problems or ()))


if __name__ == "__main__":
    unittest.main()
