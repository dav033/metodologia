"""REQ-029 T11/T13: replay of the REQ-027 T18 audit history through the read-only preview: what persisted, what was fixed, what is
new, with finding numbers that mean nothing across rounds, and a coverage gap found without patching any product code."""
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bt_recovery_preview as preview

FIXTURE = HERE / "fixtures" / "recovery_req027_preview.json"


def load():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class Req027History(unittest.TestCase):
    def setUp(self):
        self.data = load()
        self.rounds = self.data["rounds"]
        self.result = preview.history(self.rounds)

    def summary_of(self, step, occurrence, which):
        return preview.label(self.rounds[which], occurrence)

    def texts(self, step_index, group):
        step = self.result["steps"][step_index]
        ledger = self.rounds[step["to"] - 1]
        return [preview.label(ledger, i) for i in step[group]]

    def test_the_fixture_is_sanitized_and_bound_to_the_ledgers_it_came_from(self):
        self.assertEqual([len(r["findings"]) for r in self.rounds], [17, 23, 32])        # the count says nothing about progress
        for r in self.rounds:
            self.assertRegex(r["ledger_sha256"], r"^[0-9a-f]{64}$")
            for f in r["findings"]:
                self.assertLessEqual(len(f["summary"]), 240)
        blob = FIXTURE.read_text()
        self.assertNotRegex(blob, r"\bsk-[A-Za-z0-9]{10,}|BEGIN [A-Z ]*PRIVATE|client_secret=|ghp_[A-Za-z0-9]{10,}")

    def test_caddy_is_fixed_the_e2e_persists_and_the_build_and_oauth_defects_are_new(self):
        fixed = " ".join(self.texts(0, "fixed"))
        self.assertIn("Caddy", fixed)                                                    # round 1 -> 2
        persisted = " ".join(self.texts(0, "persisted") + self.texts(1, "persisted"))
        self.assertRegex(persisted, r"E2E|end-to-end|built-web")                         # the E2E defect survives both rounds
        new = " ".join(self.texts(0, "new") + self.texts(1, "new"))
        self.assertRegex(new, r"typecheck")                                              # F19: the build does not typecheck
        self.assertRegex(new, r"OAuth")                                                  # F20: real OAuth sessions cannot load the panel

    def test_the_relation_is_by_evidence_not_by_number(self):
        first = self.result["steps"][0]
        # F6 of round 1 (retry envelope) is not F6 of round 2 (alerts and actions): same number, different relation
        r1, r2 = self.rounds[0], self.rounds[1]
        same_number = {f["id"]: f for f in r1["findings"]}["F6"], {f["id"]: f for f in r2["findings"]}["F6"]
        self.assertLess(preview.score(*same_number), preview.STRONG + 0.4)
        for occurrence, why in first["relations"].items():
            self.assertGreaterEqual(why["score"], preview.WEAK)
        self.assertTrue(all(v["decision"].startswith(("related", "uncertain")) for v in first["relations"].values()))

    def test_a_finding_that_just_disappears_or_matches_weakly_is_uncertain_never_fixed_or_new(self):
        for step in self.result["steps"]:
            groups = [set(step[g]) for g in ("persisted", "fixed", "new", "regressed", "uncertain")]
            for i in range(len(groups)):
                for j in range(i + 1, len(groups)):
                    self.assertFalse(groups[i] & groups[j])                              # every occurrence is in exactly one group
        weak = {"ledger_sha256": "a" * 64, "findings": [{"id": "F1", "status": "open", "tasks": ["T1", "T2"],
                                                         "summary": "login redirect loops forever behind the proxy"}]}
        other = {"ledger_sha256": "b" * 64, "findings": [{"id": "F1", "status": "open", "tasks": ["T1"],
                                                          "summary": "the proxy configuration drops the login cookie"}]}
        step = preview.compare(weak, other)
        self.assertIn("b" * 64 + ":F1", step["uncertain"])
        self.assertEqual(step["relations"]["b" * 64 + ":F1"]["decision"], "uncertain: weak evidence")
        self.assertEqual((step["persisted"], step["new"], step["fixed"]), ([], [], []))

    def test_the_preview_is_read_only_model_free_and_digest_bound(self):
        before = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
        again = preview.history(load()["rounds"])
        self.assertEqual(again["digest"], self.result["digest"])                         # deterministic
        self.assertEqual((self.result["writes"], self.result["diagnosis_invoked"]), (0, False))
        self.assertEqual(hashlib.sha256(FIXTURE.read_bytes()).hexdigest(), before)
        import subprocess
        probe = subprocess.run([sys.executable, "-c", "import sys, bt_recovery_preview as p; "
                                "sys.exit(1 if {'bt_block_agent', 'bt_scheduler_recovery'} & set(sys.modules) else 0)"],
                               cwd=HERE.parent, capture_output=True)
        self.assertEqual(probe.returncode, 0, probe.stderr)                              # nothing asked a model, no M5 import

    def test_att_0196_changed_a_web_page_with_backend_only_checks_and_the_preview_says_so(self):
        gaps = preview.coverage_gaps(self.data["coverage_gap"])
        self.assertEqual([g["path"] for g in gaps], ["remote/web/src/app/page.tsx"])
        covered = {**self.data["coverage_gap"], "checks": ["cd remote/web && npm run typecheck"]}
        self.assertEqual(preview.coverage_gaps(covered), [])                             # a web check closes the gap


if __name__ == "__main__":
    unittest.main()
