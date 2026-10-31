"""The note an attempt (and the diagnosis, and the self-healing) reads after a failed verification must show what FAILED.
REQ-020 T14a: two manual checks and a deferred one came first in the plan, the three-block cap filled with them, and the e2e
that really failed never appeared: 14 attempts went on blind."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bt_scheduler_quality_adapter import QualityVerificationPort

ARTIFACTS = {"err": b"[FAIL] asesor M1: Expected values to be strictly equal: 'error' !== 'final'\n", "out": b""}


def digest(checks):
    port = SimpleNamespace(store=SimpleNamespace(get_artifact=lambda ref: ARTIFACTS.get(ref)))
    return QualityVerificationPort._failure_digest(port, {"checks": checks})


def check(command, status, code, ref=None):
    return {"command": command, "status": status, "exit_code": code, "stderr_ref": ref, "stdout_ref": None}


class FailureDigest(unittest.TestCase):
    def test_the_check_that_failed_is_in_the_note_even_behind_checks_that_never_ran(self):
        note = digest([check("Coordinator runs `run.ts --live`", "unknown", None), check("npm run gate", "unknown", None),
                       check("Coordinator runs `run.ts --deployed`", "unknown", None),
                       check("npx tsx scripts/e2e/asesor/run.ts --milestone M1", "fail", 1, "err")])
        self.assertIn("exit code 1", note)
        self.assertIn("'error' !== 'final'", note)
        self.assertLess(note.index("--milestone M1"), note.index("npm run gate"))            # the failure comes first

    def test_a_note_with_only_checks_that_never_ran_still_says_so(self):
        note = digest([check("Coordinator runs `run.ts --live`", "unknown", None)])
        self.assertIn("exit code None", note)

    def test_the_note_states_the_environment_the_checks_really_had(self):
        """pictures REQ-021 r30 T10.45 (D-257): every note said «none of your environment variables» while the verifier
        gave the checks the owner's verifier file and, under `verifier.inherit_env`, his whole environment."""
        from bt_scheduler_quality.policy import QualityPolicy
        failing = [check("npm run idioma:test-harness-resto", "fail", 1, "err")]
        port = SimpleNamespace(store=SimpleNamespace(get_artifact=lambda ref: ARTIFACTS.get(ref)),
                               policy=QualityPolicy(environment=(("GEMINI_CHAT_MODEL", "m-value"),),
                                                    ambient_environment=(("FNM_DIR", "/fnm"),)))
        note = QualityVerificationPort._failure_digest(port, {"checks": failing})
        self.assertNotIn("none of your environment variables", note)
        self.assertIn("NOT your environment: they receive only GEMINI_CHAT_MODEL from the owner's verifier settings, plus 1 "
                      "variable of the owner's own environment", note)
        self.assertNotIn("m-value", note)
        empty = SimpleNamespace(store=port.store, policy=QualityPolicy())
        self.assertIn("none of your environment variables", QualityVerificationPort._failure_digest(empty, {"checks": failing}))

    def test_passing_checks_are_not_in_the_note(self):
        self.assertEqual(digest([check("npm run lint", "pass", 0)]), "")


if __name__ == "__main__":
    unittest.main()
