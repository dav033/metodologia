"""Opt-in real CLI M5 recovery experiment in a disposable project; never runs as part of the default suite."""
from __future__ import annotations

import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from contextlib import ExitStack, redirect_stdout
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bt_core
import bt_profiles
import bt_scheduler_adapter as m1
import bt_scheduler_decision_adapter as m2_sources
import test_scheduler_m2_live_smoke as live
from bt_scheduler_decision import Candidate, DecisionRequest, rank_candidates
from bt_scheduler_executor import Config as M3Config
from bt_scheduler_executor import Launch as M3Launch
from bt_scheduler_executor_adapter import MethodologyDriver, run_identity, wire

MAX_INITIAL_QUOTA_USED_PERCENT = 50.0
TERMINAL_ATTEMPT_STATES = frozenset({"finished", "failed", "cancelled", "rejected"})


def _eligible_with_headroom(candidates: tuple[Candidate, ...]) -> tuple[Candidate, ...]:
    return tuple(candidate for candidate in candidates
                 if candidate.quota_used_percent is not None and
                 candidate.quota_used_percent <= MAX_INITIAL_QUOTA_USED_PERCENT)


def _apply_experiment_quota_bound(candidates: tuple[Candidate, ...],
                                  excluded_provider: str | None) -> tuple[Candidate, ...]:
    """Keep unknown, over-budget and already-failed providers out of this experiment's M2 retry."""
    return tuple(replace(candidate, quota_status="exhausted")
                 if candidate.quota_used_percent is None or
                 candidate.quota_used_percent > MAX_INITIAL_QUOTA_USED_PERCENT or
                 candidate.provider == excluded_provider else candidate
                 for candidate in candidates)


class _DisposableProject:
    """Retain experiment files by default; remove them only after every M3 attempt is confirmed terminal."""

    def __init__(self, prefix: str):
        self.path = Path(tempfile.mkdtemp(prefix=prefix))
        self._cleanup_allowed = False

    def __enter__(self):
        return self

    def __exit__(self, *_exc_info):
        if self._cleanup_allowed:
            shutil.rmtree(self.path)
        else:
            print("M5_LIVE_RETAINED " + str(self.path))

    def allow_cleanup(self) -> None:
        self._cleanup_allowed = True

    def preserve(self) -> Path:
        self._cleanup_allowed = False
        return self.path


class _DistinctProviderAssignment:
    """Use real M2 decisions, but fail closed if a retry resolves to the first provider."""

    def __init__(self, delegate, ledger_path: Path, allowed_providers: frozenset[str]):
        self.delegate = delegate
        self.ledger_path = ledger_path
        self.allowed_providers = allowed_providers
        self.providers: list[str] = []
        self.no_alternate = False

    def propose(self, request):
        assignments = self.delegate.propose(request)
        for assignment in assignments:
            route = m1.resolve_m2_route(self.ledger_path, assignment.executor)
            if route is None:
                self.no_alternate = True
                return ()
            provider = route["provider"]
            if provider not in self.allowed_providers or provider in self.providers:
                self.no_alternate = True
                return ()
            self.providers.append(provider)
        if not assignments and self.providers:
            self.no_alternate = True
        return assignments

    def close(self) -> None:
        self.delegate.close()


def _attempts_are_terminal(wiring) -> bool:
    for attempt_id in wiring.executor.ledger.all_ids():
        description = wiring.executor.describe(attempt_id)
        if not description or description.get("state") not in TERMINAL_ATTEMPT_STATES:
            return False
    return True


def _confirm_quiescence(wiring, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        wiring.scheduler.step()
        status = wiring.scheduler.snapshot().status
        if status in {"completed", "blocked", "cancelled"} and _attempts_are_terminal(wiring) and \
                wiring.executor.wait_idle(0.1):
            return True
        time.sleep(0.1)
    return False


@dataclass(frozen=True)
class _RouteProbe:
    provider: str
    account_ref: str
    quota_used_percent: float | None
    quota_status: str = "available"


class M5ExperimentGuardTests(unittest.TestCase):
    def test_preflight_requires_quota_headroom_on_two_distinct_accounts_and_providers(self):
        candidates = (
            _RouteProbe("claude", "acct-a", 40),
            _RouteProbe("codex", "acct-b", 50),
            _RouteProbe("gemini", "acct-c", 51),
        )
        eligible = _eligible_with_headroom(candidates)

        self.assertEqual({candidate.account_ref for candidate in eligible}, {"acct-a", "acct-b"})
        self.assertEqual({candidate.provider for candidate in eligible}, {"claude", "codex"})

    def test_controlled_quota_failure_excludes_the_prior_provider_and_over_budget_routes(self):
        candidates = (
            _RouteProbe("claude", "acct-a", 40),
            _RouteProbe("codex", "acct-b", 50),
            _RouteProbe("gemini", "acct-c", 51),
        )

        bounded = _apply_experiment_quota_bound(candidates, "claude")

        self.assertEqual([candidate.quota_status for candidate in bounded],
                         ["exhausted", "available", "exhausted"])

    def test_retry_assignment_fails_closed_if_m2_repeats_a_provider(self):
        assigned = SimpleNamespace(executor="m2-ref")
        delegate = SimpleNamespace(propose=lambda _request: (assigned,), close=lambda: None)
        port = _DistinctProviderAssignment(delegate, Path("unused"), frozenset({"claude", "codex"}))
        with patch.object(m1, "resolve_m2_route", return_value={"provider": "claude"}):
            self.assertEqual(port.propose(None), (assigned,))
            self.assertEqual(port.propose(None), ())

        self.assertTrue(port.no_alternate)
        self.assertEqual(port.providers, ["claude"])

    def test_retry_assignment_accepts_a_distinct_allowed_provider(self):
        assigned = SimpleNamespace(executor="m2-ref")
        delegate = SimpleNamespace(propose=lambda _request: (assigned,), close=lambda: None)
        port = _DistinctProviderAssignment(delegate, Path("unused"), frozenset({"claude", "codex"}))
        with patch.object(m1, "resolve_m2_route",
                          side_effect=({"provider": "claude"}, {"provider": "codex"})):
            self.assertEqual(port.propose(None), (assigned,))
            self.assertEqual(port.propose(None), (assigned,))

        self.assertFalse(port.no_alternate)
        self.assertEqual(port.providers, ["claude", "codex"])

    def test_disposable_project_preserve_prevents_cleanup_after_unsafe_stop(self):
        with redirect_stdout(io.StringIO()), _DisposableProject(prefix="m5-live-preserve-") as temporary:
            path = temporary.path
            self.addCleanup(shutil.rmtree, path, ignore_errors=True)
            temporary.allow_cleanup()
            self.assertEqual(temporary.preserve(), path)

        self.assertTrue(path.is_dir())
        shutil.rmtree(path)

    def test_controlled_cli_quota_message_uses_real_provider_classification(self):
        driver = _QuotaExhaustionThenRealDriver("m5-live-unit")
        route = SimpleNamespace(provider="claude")
        launch = driver.prepare(route, "unused", SimpleNamespace(), 10)
        classification = driver.classify(route, "Usage limit reached. Resets in 2s.", 1)

        self.assertEqual(launch.argv[0], sys.executable)
        self.assertEqual(launch.env_remove, tuple(os.environ))
        self.assertEqual(classification.status, "limit")
        self.assertIsNotNone(classification.reset_epoch)
        self.assertGreater(classification.reset_epoch, time.time())
        self.assertEqual(driver.injected_failures, 1)
        self.assertEqual(driver.real_invocations, 0)


class _QuotaExhaustionThenRealDriver:
    """Inject one quota-shaped local CLI failure, then delegate every later launch to the real provider driver."""

    def __init__(self, project: str):
        self.delegate = MethodologyDriver(project)
        self.injected_failures = 0
        self.real_invocations = 0

    def prepare(self, route, prompt, workspace, timeout_seconds):
        if self.injected_failures == 0:
            self.injected_failures = 1
            code = "import sys; print('Usage limit reached. Resets in 2s.'); sys.exit(1)"
            return M3Launch(argv=(sys.executable, "-I", "-c", code), env_remove=tuple(os.environ))
        self.real_invocations += 1
        return self.delegate.prepare(route, prompt, workspace, timeout_seconds)

    def classify(self, route, raw, returncode, *, timed_out=False, cancelled=False):
        return self.delegate.classify(route, raw, returncode, timed_out=timed_out, cancelled=cancelled)


class LiveM5RecoveryExperiment(unittest.TestCase):
    def test_real_cli_recovers_one_controlled_quota_failure_in_a_disposable_project(self):
        if os.environ.get("BITACORA_LIVE_SCHEDULER_M5_EXPERIMENT") != "1":
            self.skipTest("set BITACORA_LIVE_SCHEDULER_M5_EXPERIMENT=1 for the bounded real CLI experiment")

        actual_state = bt_core.STATE
        source_profiles = bt_profiles.load()
        subscription_rows, agy_row, refreshed_profiles = live._refresh_live_quotas()
        self.assertEqual(set(source_profiles), set(refreshed_profiles))

        with _DisposableProject(prefix="m5-live-") as temporary:
            tmp_name = str(temporary.path)
            temp_root = Path(tmp_name) / "bitacora"
            state_dir = temp_root / ".state"
            state_dir.mkdir(parents=True, mode=0o700)
            repo = live.make_repo(Path(tmp_name) / "project")
            (repo / "AGENTS.md").write_text(
                "# Disposable M5 live experiment\n\n"
                "Work only in this repository. Do not inspect or modify other repositories, settings, credentials or "
                "runs. Do not use the network or install dependencies. Implement only the approved task and its focused "
                "tests.\n", encoding="utf-8")
            live.git(repo, "add", "AGENTS.md")
            live.git(repo, "commit", "-q", "-m", "test: define disposable M5 experiment boundaries")
            source_head = live.git(repo, "rev-parse", "HEAD")
            source_status = live.git(repo, "status", "--porcelain")

            live._write_private(state_dir / "profiles.json", source_profiles)
            if isinstance(subscription_rows, dict):
                live._write_private(state_dir / "subscription-usage.json",
                                    {"schema_version": 1, "accounts": subscription_rows})
            if agy_row:
                live._write_private(state_dir / "agy-usage.json", agy_row)
            try:
                quota_state = json.loads((actual_state / "quota.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                quota_state = {}
            live._write_private(state_dir / "quota.json", quota_state)

            with ExitStack() as stack:
                stack.enter_context(patch.object(bt_core, "ROOT", temp_root))
                stack.enter_context(patch.object(bt_core, "STATE", state_dir))
                stack.enter_context(patch.object(bt_profiles, "ROOT", temp_root))
                stack.enter_context(patch.object(bt_profiles, "STATE", state_dir))
                stack.enter_context(patch.object(live.bt_agents, "STATE", state_dir))
                stack.enter_context(patch.object(live.bt_subscriptions, "STATE", state_dir))

                rdir, plan_state = live._prepare_plan(temp_root, repo)
                plan_ref = plan_state["plan_ref"]
                sampled_at = time.time()
                candidates = m2_sources._candidate_rows(live.PROJECT, "implement", live.CLASSIFICATIONS, sampled_at)
                request = DecisionRequest(plan_ref["plan_id"], plan_ref["revision"], plan_ref["sha256"], 1,
                                          sampled_at, live.TASK_FACTS, candidates,
                                          m2_sources.POLICY_VERSION, None)
                ranking = rank_candidates(request)
                bounded = _eligible_with_headroom(ranking.eligible)
                if len({candidate.account_ref for candidate in bounded}) < 2 or \
                        len({candidate.provider for candidate in bounded}) < 2:
                    temporary.allow_cleanup()
                    self.skipTest("M5 live experiment not launched: two fresh providers with distinct accounts and "
                                  "at least 50% quota headroom are unavailable")
                if os.environ.get("BITACORA_LIVE_SCHEDULER_M5_PREFLIGHT_ONLY") == "1":
                    temporary.allow_cleanup()
                    self.skipTest("M5 live quota preflight passed; no agent was launched")

                ledger_path = Path(tmp_name) / "m2-decisions.sqlite3"
                delegate = m1.DecisionAssignmentPort(live.PROJECT, ledger_path,
                                                     laya_root=Path(tmp_name) / "laya-unused")
                allowed_providers = frozenset(candidate.provider for candidate in bounded)
                assignment = _DistinctProviderAssignment(delegate, ledger_path, allowed_providers)
                original_candidates = m2_sources._candidate_rows

                def candidates_with_controlled_quota_failure(project, task_kind, classifications, now):
                    rows = original_candidates(project, task_kind, classifications, now)
                    excluded_provider = assignment.providers[0] if assignment.providers else None
                    return _apply_experiment_quota_bound(rows, excluded_provider)

                stack.enter_context(patch.object(m2_sources, "_candidate_rows",
                                                 candidates_with_controlled_quota_failure))
                verifier = live._IndependentVerifier()
                quota_driver = _QuotaExhaustionThenRealDriver(live.PROJECT)
                m5_path = Path(tmp_name) / "m5" / "history.db"
                try:
                    wiring = wire(
                        rdir, project=live.PROJECT, assignment=assignment, verification=verifier,
                        driver=quota_driver,
                        repos={"app": repo}, default_repository="app", m2_ledger=ledger_path,
                        config=m1.core.Config(max_parallel_tasks=1, max_attempts=2, lease_seconds=600),
                        executor_config=M3Config(max_running=1, timeout_seconds=120, max_timeout_seconds=150,
                                                 grace_seconds=2, heartbeat_seconds=15, poll_seconds=0.1),
                        recovery_store_path=m5_path,
                    )
                except Exception:
                    assignment.close()
                    temporary.allow_cleanup()
                    raise
                verifier.wiring, verifier.scheduler = wiring, wiring.scheduler
                started = time.monotonic()
                timed_out = False
                cancel_requested = False
                stopped = False
                latest = None
                metrics = None
                snapshot = None
                attempts = []
                try:
                    deadline = started + 300
                    while time.monotonic() < deadline:
                        wiring.scheduler.step()
                        for attempt_id in wiring.executor.ledger.all_ids():
                            description = wiring.executor.describe(attempt_id)
                            if description and (Path(description["artifacts"]["dir"])
                                                / description["stream"]["stream_ref"]).exists():
                                wiring.drain_stream(attempt_id, run_identity(wiring.scheduler))
                        if wiring.scheduler.snapshot().status in {"completed", "blocked", "cancelled"}:
                            break
                        if assignment.no_alternate:
                            wiring.scheduler.cancel("m5-live-experiment",
                                                     "no distinct eligible provider remains for the retry")
                            cancel_requested = True
                            break
                        time.sleep(0.1)
                    else:
                        timed_out = True
                        wiring.scheduler.cancel("m5-live-experiment", "300 second deadline expired")
                        cancel_requested = True
                    stopped = _confirm_quiescence(wiring, 45 if cancel_requested else 20)
                    if stopped:
                        latest = wiring.recovery.latest()
                        metrics = wiring.recovery.metrics()
                        snapshot = wiring.scheduler.snapshot()
                        attempts = [wiring.executor.ledger.get(attempt_id)
                                    for attempt_id in wiring.executor.ledger.all_ids()]
                        attempts.sort(key=lambda row: row["request"]["token"])
                finally:
                    if not stopped and not cancel_requested:
                        wiring.scheduler.cancel("m5-live-experiment", "experiment exited before clean completion")
                        cancel_requested = True
                        stopped = _confirm_quiescence(wiring, 45)
                    if stopped:
                        wiring.close()
                        temporary.allow_cleanup()
                    else:
                        temporary.preserve()
                        states = []
                        for attempt_id in wiring.executor.ledger.all_ids():
                            description = wiring.executor.describe(attempt_id)
                            states.append({"attempt_id": attempt_id,
                                           "state": description.get("state") if description else "unknown"})
                        live._write_private(state_dir / "m5-live-cleanup-failure.json", {
                            "cancel_requested": cancel_requested,
                            "attempts": states,
                            "scheduler_status": wiring.scheduler.snapshot().status,
                        })
                    assignment.close()

                if not stopped:
                    self.fail("M3 process termination was not confirmed; disposable evidence was retained")

                elapsed = round(time.monotonic() - started, 3)
                first, second = attempts if len(attempts) == 2 else (None, None)
                route_results = [row["route"] for row in attempts if isinstance(row, dict)]
                source_unchanged = (live.git(repo, "rev-parse", "HEAD"), live.git(repo, "status", "--porcelain")) == \
                    (source_head, source_status)
                result = {
                    "plan_id": plan_ref["plan_id"], "revision": plan_ref["revision"],
                    "eligible_provider_count": len({candidate.provider for candidate in bounded}),
                    "attempt_count": len(attempts), "attempt_states": [row["state"] for row in attempts],
                    "attempt_providers": [route.get("provider") for route in route_results],
                    "attempt_causes": [row["outcome"]["cause"] for row in attempts],
                    "controlled_quota_injected": quota_driver.injected_failures == 1,
                    "real_cli_invocations": quota_driver.real_invocations,
                    "distinct_retry_provider": len(assignment.providers) == 2 and
                                               assignment.providers[0] != assignment.providers[1],
                    "m1_state": snapshot.status, "task_state": snapshot.tasks[live.TASK_ID]["state"],
                    "m5_latest_action": latest["action"] if latest else None,
                    "m5_latest_reason": latest["reason_code"] if latest else None,
                    "m5_decision_count": metrics["decisions"] if metrics else None,
                    "m5_quota_policy_executed": bool(
                        latest and latest["action"] == "retry" and latest["reason_code"] == "quota_reset_ready"
                        and metrics and metrics["decisions"] >= 2),
                    "final_verifier_accepted": bool(verifier.results and verifier.results[-1]["accepted"]),
                    "snapshot_continued": bool(first and second and first["handoff"]["status"] == "captured"
                                                and second["request"]["base_ref"] == first["handoff"]["snapshot_sha"]),
                    "elapsed_seconds": elapsed, "timed_out": timed_out,
                    "disposable_source_unchanged": source_unchanged,
                }
                artifact_root = Path.home() / ".local" / "share" / "bt-scheduler-m5-experiment"
                artifact_root.mkdir(parents=True, exist_ok=True, mode=0o700)
                artifact_dir = Path(tempfile.mkdtemp(prefix="run-", dir=artifact_root))
                artifact = artifact_dir / "result.json"
                live._write_private(artifact, result)
                print("M5_LIVE_ARTIFACT " + str(artifact))

                self.assertFalse(timed_out, "real CLI experiment exceeded 300 seconds")
                self.assertEqual((snapshot.status, snapshot.tasks[live.TASK_ID]["state"]), ("completed", "completed"))
                self.assertEqual(len(verifier.results), 1)
                self.assertEqual(len(attempts), 2)
                self.assertEqual([row["state"] for row in attempts], ["failed", "finished"])
                self.assertEqual(result["attempt_causes"], ["quota_exhausted", "clean"])
                self.assertTrue(result["controlled_quota_injected"])
                self.assertEqual(result["real_cli_invocations"], 1)
                self.assertTrue(result["distinct_retry_provider"])
                self.assertEqual(len({route.get("provider") for route in route_results}), 2)
                self.assertEqual((result["m5_latest_action"], result["m5_latest_reason"]), ("retry", "quota_reset_ready"))
                self.assertTrue(result["m5_quota_policy_executed"])
                self.assertTrue(result["final_verifier_accepted"])
                self.assertTrue(result["snapshot_continued"])
                self.assertTrue(source_unchanged, "the disposable source checkout changed")


if __name__ == "__main__":
    unittest.main()
