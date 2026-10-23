"""Content provenance survives report commits and sends stale evidence to its producer."""
import json
import tempfile
import unittest
from pathlib import Path

import bt_audit_gate as gate
from scheduler_executor_support import git, make_repo
from test_remediation import plan, task


class Evidence(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = make_repo(Path(self.tmp.name) / "app")
        self.plan = plan(task("T1"), task("T14a", ["T1"], kind="test", category="integration",
                              paths=["docs/integration.json"]),
                         task("T15", ["T14a"], kind="audit",
                              paths=["docs/audit.md", "docs/audit.findings.json"]))
        self.paths = gate.evidence_outputs(self.plan["tasks"], "app")

    def digest(self, revision="HEAD"):
        return gate.tree_digest(self.repo, revision, self.paths)

    def commit(self, path, text):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "change")
        return git(self.repo, "rev-parse", "HEAD")

    def judge(self, evidence):
        return gate.evidence_gate({"integration_evidence": ["docs/integration.json"], "tree_digest": self.digest()},
                                  self.plan["tasks"], "T15", self.digest(), lambda path: json.dumps(evidence),
                                  digest_at=self.digest)

    def test_reports_and_commit_identity_do_not_change_the_digest(self):
        original = self.digest()
        self.commit("docs/integration.json", "{}")
        self.commit("docs/audit.findings.json", "{}")
        self.commit("docs/audit.md", "audit")
        self.assertEqual(original, self.digest())
        self.assertTrue(self.judge({"tree_digest": original, "revision": "an-old-sha"}).ok)

    def test_source_changes_send_the_evidence_producer_back(self):
        original = self.digest()
        self.commit("README.md", "changed source\n")
        result = self.judge({"tree_digest": original})
        self.assertFalse(result.ok)
        self.assertEqual(result.rework, ("T14a",))
        self.assertEqual(result.problems, ())
        self.assertEqual(result.blocking[0]["code"], "STALE_EVIDENCE")
        self.assertIn("regenerate", result.blocking[0]["summary"])

    def test_legacy_revision_is_compared_by_content(self):
        revision = git(self.repo, "rev-parse", "HEAD")
        self.commit("docs/integration.json", "{}")
        self.assertTrue(self.judge({"revision": revision}).ok)
        self.commit("README.md", "new source\n")
        self.assertEqual(self.judge({"revision": revision}).rework, ("T14a",))

    def test_unknown_provenance_and_bad_evidence_fail_closed(self):
        for evidence in ({}, {"tree_digest": "bad"}, {"revision": "unknown"}, {"revision": "HEAD"}, []):
            with self.subTest(evidence=evidence):
                result = self.judge(evidence)
                self.assertFalse(result.ok)
                self.assertEqual(result.rework, ("T14a",))

    def test_an_invalid_audit_digest_is_the_auditors_problem(self):
        result = gate.evidence_gate({"tree_digest": "bad"}, self.plan["tasks"], "T15", self.digest(), lambda _: None)
        self.assertFalse(result.ok)
        self.assertFalse(result.rework)

    def test_unowned_evidence_is_not_silently_accepted(self):
        result = gate.evidence_gate({"integration_evidence": ["other.json"]}, self.plan["tasks"], "T15",
                                    self.digest(), lambda _: None)
        self.assertTrue(result.problems)
        self.assertFalse(result.ok)

    def test_legacy_ledgers_without_provenance_remain_valid(self):
        self.assertTrue(gate.evidence_gate({}, self.plan["tasks"], "T15", self.digest(), lambda _: None).ok)

    def test_optional_provenance_fields_are_validated_by_the_public_contract(self):
        for fields in ({"tree_digest": "bad"}, {"tree_digest": 1}, {"integration_evidence": "x.json"},
                       {"integration_evidence": ["../outside.json"]}):
            with self.subTest(fields=fields):
                self.assertTrue(gate.validate_ledger({"schema": gate.SCHEMA, "findings": [], **fields}))

    def test_no_source_or_other_repository_output_is_excluded(self):
        self.plan["tasks"] += [task("T9", kind="test", paths=["src/test.py"]),
                               task("T10", kind="test", paths=["other.json"], repository="other")]
        self.assertEqual(gate.evidence_outputs(self.plan["tasks"], "app"), self.paths)

    def test_unknown_revision_is_an_outage(self):
        with self.assertRaises(RuntimeError):
            self.digest("missing")

    def test_explicit_evidence_from_an_implement_producer_does_not_hash_itself(self):
        self.plan["tasks"][1]["kind"] = "implement"
        self.paths = gate.evidence_outputs(self.plan["tasks"], "app", ["docs/integration.json"])
        original = self.digest()
        self.commit("docs/integration.json", json.dumps({"tree_digest": original}))
        self.assertEqual(original, self.digest())
        self.assertTrue(self.judge({"tree_digest": original}).ok)

    def test_cli_produces_the_same_digest_without_writing_either_document(self):
        from bitacora_platform import cli_audit_ledger

        path = Path(self.tmp.name) / "PLAN.json"
        path.write_text(json.dumps(self.plan))
        original = path.read_bytes()
        output = []
        self.assertEqual(cli_audit_ledger.digest(path, self.repo, "app", "HEAD", emit=output.append), 0)
        self.assertEqual(output, [self.digest()])
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(cli_audit_ledger.digest(path, self.repo, "other", "HEAD", emit=output.append), 2)
