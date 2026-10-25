"""REQ-030 step 4: a check that passed on this exact tree is not run again, and expensive checks yield to cheap failures."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bt_scheduler_quality import reuse
from bt_scheduler_quality.engine import QualityEngine
from bt_scheduler_quality.policy import QualityPolicy
from bt_scheduler_quality.runner import CommandOutcome
from bt_scheduler_quality.store import QualityStore
from test_snapshot import _make_snapshot

ORDER = json.loads((Path(__file__).parent / "fixtures" / "verify-order-pass.json").read_text(encoding="utf-8"))


class Runner:
    """Passes everything except the commands named in `failing`; remembers what ran."""

    def __init__(self, failing=(), milliseconds=4):
        self.failing, self.milliseconds, self.calls = set(failing), milliseconds, []

    def run(self, check, snapshot_root, *, timeout_seconds=None, mounts=()):
        self.calls.append(check.command)
        bad = check.command in self.failing
        return CommandOutcome("fail" if bad else "pass", 1 if bad else 0, self.milliseconds, b"evidence\n", b"", None, True)


def order(attempt, *commands):
    criteria = [f"check {n} holds" for n, _ in enumerate(commands, 1)]
    return {**ORDER, "idempotency_key": f"verify:T-001:{attempt}", "attempt_id": attempt, "acceptance_criteria": criteria,
            "verification": [{"type": "command", "value": command, "purpose": criterion}
                             for command, criterion in zip(commands, criteria)]}


class PassCache(unittest.TestCase):
    def test_a_check_that_passed_on_this_tree_is_not_run_again_and_says_so(self):
        with tempfile.TemporaryDirectory() as tmp, QualityStore(":memory:") as store:
            _, source, _, _ = _make_snapshot(Path(tmp))
            runner = Runner()
            engine = QualityEngine(QualityPolicy(), store, runner=runner)
            first = engine.verify(order("att-1", "python3 -m unittest -q"), source)
            second = engine.verify(order("att-2", "python3 -m unittest -q"), source)
            note = store.get_artifact(second["checks"][0]["stderr_ref"])
        self.assertEqual((first["status"], second["status"]), ("PASS", "PASS"))
        self.assertEqual(len(runner.calls), 1)
        self.assertIn(b"not run again", note)

    def test_the_cache_can_be_switched_off_and_a_failure_is_never_reused(self):
        with tempfile.TemporaryDirectory() as tmp, QualityStore(":memory:") as store:
            _, source, _, _ = _make_snapshot(Path(tmp))
            runner = Runner()
            QualityEngine(QualityPolicy(cache_seconds=0), store, runner=runner).verify(order("att-1", "make test"), source)
            QualityEngine(QualityPolicy(cache_seconds=0), store, runner=runner).verify(order("att-2", "make test"), source)
            self.assertEqual(len(runner.calls), 2)
        with tempfile.TemporaryDirectory() as tmp, QualityStore(":memory:") as store:
            _, source, _, _ = _make_snapshot(Path(tmp))
            runner = Runner(failing={"make test"})
            engine = QualityEngine(QualityPolicy(), store, runner=runner)
            self.assertEqual(engine.verify(order("att-1", "make test"), source)["status"], "FAIL")
            self.assertEqual(engine.verify(order("att-2", "make test"), source)["status"], "FAIL")
            self.assertEqual(len(runner.calls), 2)                                          # the failure ran again

    def test_another_tree_or_another_environment_is_another_verdict(self):
        with tempfile.TemporaryDirectory() as tmp, QualityStore(":memory:") as store:
            (Path(tmp) / "a").mkdir()
            (Path(tmp) / "b").mkdir()
            _, one, _, _ = _make_snapshot(Path(tmp) / "a")
            _, other, _, _ = _make_snapshot(Path(tmp) / "b", files={"extra.py": "1\n"})
            runner = Runner()
            QualityEngine(QualityPolicy(), store, runner=runner).verify(order("att-1", "make test"), one)
            QualityEngine(QualityPolicy(), store, runner=runner).verify(order("att-2", "make test"), other)
            QualityEngine(QualityPolicy(network=False), store, runner=runner).verify(order("att-3", "make test"), one)
            self.assertEqual(len(runner.calls), 3)

    def test_contract_and_declared_environment_identities_bind_cached_passes_only_when_present(self):
        with tempfile.TemporaryDirectory() as tmp, QualityStore(":memory:") as store:
            _, source, _, _ = _make_snapshot(Path(tmp))
            runner = Runner()
            raw = order("att-1", "make test")
            raw["contract_identities"] = {"api@1": "a" * 64}
            raw["environment_fingerprint"] = "b" * 64
            QualityEngine(QualityPolicy(), store, runner=runner).verify(raw, source)
            same = {**raw, "idempotency_key": "verify:T-001:att-2", "attempt_id": "att-2"}
            QualityEngine(QualityPolicy(), store, runner=runner).verify(same, source)
            changed_contract = {**raw, "idempotency_key": "verify:T-001:att-3", "attempt_id": "att-3",
                                "contract_identities": {"api@1": "c" * 64}}
            QualityEngine(QualityPolicy(), store, runner=runner).verify(changed_contract, source)
        self.assertEqual(runner.calls, ["make test", "make test"])

    def test_pass_after_prior_fail_on_the_same_evidence_key_is_never_clean_pass(self):
        with tempfile.TemporaryDirectory() as tmp, QualityStore(":memory:") as store:
            _, source, _, _ = _make_snapshot(Path(tmp))
            runner = Runner(failing={"make flaky"})
            engine = QualityEngine(QualityPolicy(), store, runner=runner)
            first = engine.verify(order("att-1", "make flaky"), source)
            runner.failing.clear()
            second = engine.verify(order("att-2", "make flaky"), source)
        self.assertEqual(first["status"], "FAIL")
        self.assertEqual(second["status"], "NEEDS_REVIEW")
        self.assertEqual(second["reason_code"], "FLAKY_SUSPECTED")
        self.assertEqual(second["checks"][0]["reason_code"], "FLAKY_SUSPECTED")

    def test_a_pass_confirmed_after_the_flaky_pass_is_clean_again(self):
        # One environment failure (a database not up yet) must not mark the key flaky forever: the bounded
        # same-attempt resume re-runs the check, and a second consecutive pass is clean evidence.
        with tempfile.TemporaryDirectory() as tmp, QualityStore(":memory:") as store:
            _, source, _, _ = _make_snapshot(Path(tmp))
            runner = Runner(failing={"make flaky"})
            engine = QualityEngine(QualityPolicy(), store, runner=runner)
            engine.verify(order("att-1", "make flaky"), source)
            runner.failing.clear()
            flaky = engine.verify(order("att-2", "make flaky"), source)
            confirmed = engine.verify(order("att-3", "make flaky"), source)
        self.assertEqual(flaky["reason_code"], "FLAKY_SUSPECTED")
        self.assertEqual(confirmed["status"], "PASS")
        self.assertIsNone(confirmed["checks"][0].get("issue_code"))

    def test_the_fingerprint_hides_environment_values(self):
        policy = QualityPolicy(environment=(("TOKEN", "super-secret-value"),), secret_values=("super-secret-value",))
        self.assertNotIn("super-secret-value", reuse.environment_fingerprint(policy))
        self.assertNotEqual(reuse.environment_fingerprint(policy), reuse.environment_fingerprint(QualityPolicy()))


class ExpensiveLast(unittest.TestCase):
    SUITE = "python3 -m unittest discover -s tests"

    def test_a_whole_suite_is_recognised_and_a_focused_run_is_not(self):
        for command in (self.SUITE, "npm run gate", "npm test", "pytest", "cargo test"):
            self.assertTrue(reuse.looks_like_full_suite(command), command)
        for command in ("python3 -m unittest discover -s tests -p test_one.py", "pytest tests/test_one.py",
                        "python3 -m unittest tests.test_a", "npm run lint"):
            self.assertFalse(reuse.looks_like_full_suite(command), command)

    def test_the_suite_is_not_started_once_a_cheaper_check_failed(self):
        with tempfile.TemporaryDirectory() as tmp, QualityStore(":memory:") as store:
            _, source, _, _ = _make_snapshot(Path(tmp))
            runner = Runner(failing={"python3 -m unittest -q"})
            engine = QualityEngine(QualityPolicy(), store, runner=runner)
            result = engine.verify(order("att-1", self.SUITE, "python3 -m unittest -q"), source)   # the suite is declared first
            note = store.get_artifact(result["checks"][0]["stderr_ref"])
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(runner.calls, ["python3 -m unittest -q"])                          # the cheap one ran, the suite did not
        self.assertIn("CHECK_DEFERRED", {item["code"] for item in result["issues"]})
        self.assertIn(b"cheaper check", note)

    def test_the_suite_still_runs_when_the_cheap_checks_pass_and_deferral_can_be_switched_off(self):
        with tempfile.TemporaryDirectory() as tmp, QualityStore(":memory:") as store:
            _, source, _, _ = _make_snapshot(Path(tmp))
            runner = Runner()
            result = QualityEngine(QualityPolicy(), store, runner=runner).verify(
                order("att-1", self.SUITE, "python3 -m unittest -q"), source)
        self.assertEqual((result["status"], runner.calls), ("PASS", ["python3 -m unittest -q", self.SUITE]))
        with tempfile.TemporaryDirectory() as tmp, QualityStore(":memory:") as store:
            _, source, _, _ = _make_snapshot(Path(tmp))
            runner = Runner(failing={"python3 -m unittest -q"})
            QualityEngine(QualityPolicy(defer_expensive=False), store, runner=runner).verify(
                order("att-1", self.SUITE, "python3 -m unittest -q"), source)
        self.assertEqual(runner.calls, [self.SUITE, "python3 -m unittest -q"])               # original order, everything ran

    def test_measured_duration_beats_the_name(self):
        with tempfile.TemporaryDirectory() as tmp, QualityStore(":memory:") as store:
            _, source, _, _ = _make_snapshot(Path(tmp))
            slow = Runner(failing={"make quick"}, milliseconds=500_000)                   # 500 s: expensive whatever it is called
            engine = QualityEngine(QualityPolicy(cache_seconds=0), store, runner=slow)
            engine.verify(order("att-1", "make slow"), source)
            slow.failing = {"make quick"}
            result = engine.verify(order("att-2", "make slow", "make quick"), source)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(slow.calls, ["make slow", "make quick"])                           # `make slow` was learned expensive: after, and skipped


if __name__ == "__main__":
    unittest.main()
