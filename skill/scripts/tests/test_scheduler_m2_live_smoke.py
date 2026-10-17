"""One opt-in, quota-gated real-provider route smoke across Planner, M1, M2 and M3."""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from scheduler_executor_support import git, make_repo

import bt_agents
import bt_agy
import bt_core
import bt_profiles
import bt_scheduler_adapter as m1
import bt_scheduler_decision_adapter as m2_sources
import bt_subscriptions
from bt_scheduler_decision import (
    DecisionRequest,
    TaskFacts,
    rank_candidates,
    resolve_executor_binding,
)
from bt_scheduler_executor import Config as M3Config
from bt_scheduler_executor_adapter import wire

M1Config = m1.core.Config
Verdict = m1.core.Verdict
PROJECT = "p036-live-smoke"
REQ = "REQ-998"
TASK_ID = "T1"
TASK_TITLE = "Implement src/greetings.py and tests/test_greetings.py with the specified greet behavior"
CLASSIFICATIONS = {"complexity": "low", "scope": "small_change", "estimated_minutes": 20,
                  "risk": "low", "coupling": "low", "confidence": "high"}
TASK_FACTS = TaskFacts(
    TASK_ID,
    "Create greet(name: str) -> str. Trim surrounding whitespace and return Hello, {name}!. Reject empty names "
    "with ValueError and non-strings with TypeError. Add five focused standard-library tests, including Unicode "
    "and apostrophes.",
    CLASSIFICATIONS,
    {},
    acceptance_criteria=("The greeting function has the exact specified behavior.",
                         "Five focused standard-library tests pass."),
    verification=({"type": "command", "value": "python3 -m unittest discover -s tests -v"},),
    expected_paths=("src/greetings.py", "tests/test_greetings.py"),
)


def _write_private(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    path.chmod(0o600)


def _refresh_live_quotas() -> tuple[dict[str, object], dict[str, object], dict[str, dict]]:
    """Use the existing bounded collectors; their own per-account/hour and 15-minute guards remain authoritative."""
    bt_subscriptions.poll()
    bt_agy.refresh()
    return bt_subscriptions.load(), bt_agy.load_cache(), bt_profiles.load()


def _prepare_plan(root: Path, repo: Path) -> tuple[Path, dict[str, object]]:
    rdir = root / PROJECT / "requirements" / f"{REQ}-real-smoke"
    rdir.mkdir(parents=True)
    (root / PROJECT / "project.json").write_text(json.dumps({
        "work": False,
        "repos": {"app": {"remote": "", "hint": str(repo)}},
    }, indent=2) + "\n", encoding="utf-8")
    (rdir / "SPEC.md").write_text(
        "# Disposable live smoke\n\n"
        "## Task\n\n"
        "Implement `src/greetings.py` with `greet(name: str) -> str`. Strip surrounding whitespace and return "
        "`Hello, {name}!`. Raise `ValueError` for an empty or whitespace-only string and `TypeError` for a non-string. "
        "Add five focused standard-library tests: normal name, trimming, Unicode/apostrophe, empty input and "
        "non-string input. Do not add dependencies, access other repositories or use the network.\n",
        encoding="utf-8",
    )
    (rdir / "PLAN.md").write_text(
        f"---\nreq: {REQ}\nstatus: approved\n---\n"
        "# Plan — P-036 real route smoke\n\n"
        "### M1 — Implement and verify the greeting helper\n"
        f"- [ ] {TASK_ID} — {TASK_TITLE} · repo: app · files: src/greetings.py, tests/test_greetings.py "
        "· verify: `python3 -m unittest discover -s tests -v`\n",
        encoding="utf-8",
    )
    output: list[str] = []
    if m1.plan_adapter.run_cli("init", rdir, emit=output.append) != 0:
        raise AssertionError("Planner init failed: " + " | ".join(output)[-1200:])

    plan_path = rdir / "PLAN.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["milestones"][0]["acceptance_criteria"] = [
        "The greeting utility and its focused tests pass the declared local test command.",
    ]
    reasons = {
        "complexity": "The task adds one specified helper and focused tests with no design migration.",
        "scope": "The task changes only its two declared files in the disposable repository.",
        "duration": "One small helper and five deterministic tests fit a brief local implementation.",
        "risk": "The task is isolated to temporary files and rejects malformed input with unit assertions.",
        "coupling": "The helper has no shared consumers, services or dependency changes.",
        "confidence": "The spec fixes the output, trimming, invalid input, paths and local verification command.",
    }
    task = plan["tasks"][0]
    task.update({
        "objective": "Implement the exact greeting behavior and five focused standard-library tests.",
        "repository": "app",
        **CLASSIFICATIONS,
        "estimate_rationale": "One small helper and five deterministic tests are a bounded smoke task.",
        "classification_evidence": {
            key: {"justification": value, "evidence": ["spec:SPEC.md#task", "file:README.md"]}
            for key, value in reasons.items()
        },
        "expected_paths": ["src/greetings.py", "tests/test_greetings.py"],
        "shared_resources": [],
        "acceptance_criteria": [
            "greet trims names and returns the exact Hello greeting.",
            "Empty input raises ValueError and non-string input raises TypeError.",
            "Five focused standard-library unit tests pass.",
        ],
        "verification": [{
            "type": "command", "value": "python3 -m unittest discover -s tests -v",
            "purpose": "Run standard-library tests against the delivered greeting helper.",
        }],
    })
    plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for action in ("check", "freeze"):
        output = []
        if m1.plan_adapter.run_cli(action, rdir, emit=output.append) != 0:
            raise AssertionError(f"Planner {action} failed: " + " | ".join(output)[-1200:])
    state = m1.plan_adapter.run_state_fields(rdir)
    if not state.get("plan_ref"):
        raise AssertionError("Planner did not freeze an approved plan")
    return rdir, state


class _IndependentVerifier:
    """Rerun declared tests and separate behavior probes on the actual M3 handoff worktree."""

    def __init__(self) -> None:
        self.scheduler = None
        self.wiring = None
        self.results: list[dict[str, object]] = []

    def request(self, order):
        row = self.wiring.executor.ledger.get(order.attempt_id)
        workspace = Path(row["workspace"]["path"]) if isinstance(row, dict) and isinstance(
            row.get("workspace"), dict) and isinstance(row["workspace"].get("path"), str) else None
        accepted = False
        details = "M3 did not record a workspace."
        if workspace is not None:
            env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
            try:
                tests = subprocess.run(
                    [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"],
                    cwd=workspace, env=env, text=True, capture_output=True, timeout=60, check=False,
                )
                probe = subprocess.run(
                    [sys.executable, "-B", "-c", (
                        "from greetings import greet; assert greet('  María O\\'Neil  ') == \"Hello, María O'Neil!\"; "
                        "assert greet('Ada') == 'Hello, Ada!'; "
                        "exec(\"try:\\n greet('  ')\\nexcept ValueError:\\n pass\\nelse:\\n raise AssertionError()\"); "
                        "exec(\"try:\\n greet(1)\\nexcept TypeError:\\n pass\\nelse:\\n raise AssertionError()\")"
                    )],
                    cwd=workspace, env={**env, "PYTHONPATH": str(workspace / "src")},
                    text=True, capture_output=True, timeout=15, check=False,
                )
                paths_ok = (workspace / "src/greetings.py").is_file() and \
                    (workspace / "tests/test_greetings.py").is_file()
                accepted = tests.returncode == 0 and probe.returncode == 0 and paths_ok
                details = (f"unittest_exit={tests.returncode}; behavior_probe_exit={probe.returncode}; "
                           f"expected_paths_present={paths_ok}; test_output_tail="
                           f"{(tests.stdout + tests.stderr)[-800:]}")
            except (OSError, subprocess.TimeoutExpired) as exc:
                details = f"verification_error={type(exc).__name__}"
        self.results.append({"attempt_id": order.attempt_id, "accepted": accepted, "evidence": details})
        self.scheduler.submit_verdict(Verdict(
            verdict_id=f"p036-verdict-{order.attempt_id}", plan_id=order.plan_id, revision=order.revision,
            task_id=order.task_id, attempt_id=order.attempt_id, accepted=accepted,
            verifier="p036-independent-unittest", evidence=details[:2500], token=order.token,
        ))
        return m1.core.Ack("accepted")


class LiveSchedulerM2RouteSmokeTests(unittest.TestCase):
    def test_real_route_is_selected_from_two_fresh_profiles_and_reaches_m3(self):
        if os.environ.get("BITACORA_LIVE_SCHEDULER_SMOKE") != "1":
            self.skipTest("set BITACORA_LIVE_SCHEDULER_SMOKE=1 to run the bounded real-provider smoke")

        actual_state = bt_core.STATE
        source_profiles = bt_profiles.load()
        subscription_rows, agy_row, refreshed_profiles = _refresh_live_quotas()
        self.assertEqual(set(source_profiles), set(refreshed_profiles))

        with tempfile.TemporaryDirectory(prefix="p036-live-") as tmp_name:
            temp_root = Path(tmp_name) / "bitacora"
            state_dir = temp_root / ".state"
            state_dir.mkdir(parents=True, mode=0o700)
            repo = make_repo(Path(tmp_name) / "project")
            (repo / "AGENTS.md").write_text(
                "# Disposable smoke repository\n\n"
                "Work only in this repository. Do not inspect or modify other repositories, settings, credentials or "
                "runs. Do not use the network or install dependencies. Implement only the greeting helper in the "
                "approved task and its focused tests.\n",
                encoding="utf-8",
            )
            git(repo, "add", "AGENTS.md")
            git(repo, "commit", "-q", "-m", "test: document disposable smoke boundaries")
            before_head, before_status = git(repo, "rev-parse", "HEAD"), git(repo, "status", "--porcelain")

            _write_private(state_dir / "profiles.json", source_profiles)
            if isinstance(subscription_rows, dict):
                _write_private(state_dir / "subscription-usage.json",
                               {"schema_version": 1, "accounts": subscription_rows})
            if agy_row:
                _write_private(state_dir / "agy-usage.json", agy_row)
            try:
                quota_state = json.loads((actual_state / "quota.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                quota_state = {}
            _write_private(state_dir / "quota.json", quota_state)

            with ExitStack() as stack:
                stack.enter_context(patch.object(bt_core, "ROOT", temp_root))
                stack.enter_context(patch.object(bt_core, "STATE", state_dir))
                stack.enter_context(patch.object(bt_profiles, "ROOT", temp_root))
                stack.enter_context(patch.object(bt_profiles, "STATE", state_dir))
                stack.enter_context(patch.object(bt_agents, "STATE", state_dir))
                stack.enter_context(patch.object(bt_subscriptions, "STATE", state_dir))

                rdir, plan_state = _prepare_plan(temp_root, repo)
                plan_ref = plan_state["plan_ref"]
                quota_sampled_at = time.time()
                candidate_rows = m2_sources._candidate_rows(PROJECT, "implement", CLASSIFICATIONS, quota_sampled_at)
                if not candidate_rows:
                    self.skipTest("no real catalog candidates; P-036 remains pending")
                preflight = DecisionRequest(
                    plan_ref["plan_id"], plan_ref["revision"], plan_ref["sha256"], 1, quota_sampled_at,
                    TASK_FACTS, candidate_rows, m2_sources.POLICY_VERSION, None,
                )
                ranking = rank_candidates(preflight)
                eligible_by_account = {candidate.account_ref: candidate for candidate in ranking.eligible}
                eligible_providers = {candidate.provider for candidate in ranking.eligible}
                if len(eligible_by_account) < 2 or len(eligible_providers) < 2:
                    evidence = [
                        {"profile": row.profile, "provider": row.provider, "quota_status": row.quota_status,
                         "auth_status": row.auth_status, "runtime_status": row.runtime_status,
                         "quota_used_percent": row.quota_used_percent,
                         "sample_age_seconds": None if row.quota_observed_at is None else
                         round(quota_sampled_at - row.quota_observed_at, 2)}
                        for row in candidate_rows
                    ]
                    self.skipTest("P-036 remains pending: two distinct providers lack fresh verified, permitted quota; "
                                  + json.dumps(evidence, sort_keys=True))
                self.assertTrue(all(candidate.quota_valid_until is not None and
                                    quota_sampled_at < candidate.quota_valid_until
                                    for candidate in ranking.eligible))
                if os.environ.get("BITACORA_LIVE_SCHEDULER_PREFLIGHT_ONLY") == "1":
                    quota_evidence = [{
                        "profile": candidate.profile, "provider": candidate.provider,
                        "quota_used_percent": candidate.quota_used_percent,
                        "sample_age_seconds": round(quota_sampled_at - candidate.quota_observed_at, 2),
                        "valid_for_seconds": round(candidate.quota_valid_until - quota_sampled_at, 2),
                    } for candidate in ranking.eligible]
                    self.skipTest("quota gate passed with two fresh permitted providers; no agent launched: "
                                  + json.dumps(quota_evidence, sort_keys=True))

                ledger_path = Path(tmp_name) / "m2-decisions.sqlite3"
                assignment = m1.DecisionAssignmentPort(PROJECT, ledger_path,
                                                       laya_root=Path(tmp_name) / "laya-unused")
                verifier = _IndependentVerifier()
                wiring = wire(
                    rdir, project=PROJECT, assignment=assignment, verification=verifier,
                    repos={"app": repo}, default_repository="app", m2_ledger=ledger_path,
                    config=M1Config(max_parallel_tasks=1, max_attempts=1, lease_seconds=600),
                    executor_config=M3Config(max_running=1, timeout_seconds=150, max_timeout_seconds=180,
                                             grace_seconds=2, heartbeat_seconds=15, poll_seconds=0.1),
                )
                verifier.wiring, verifier.scheduler = wiring, wiring.scheduler
                started = time.monotonic()
                timed_out = False
                try:
                    deadline = started + 180
                    while time.monotonic() < deadline:
                        wiring.scheduler.step()
                        snapshot = wiring.scheduler.snapshot()
                        if snapshot.status in ("completed", "blocked", "cancelled"):
                            break
                        time.sleep(0.1)
                    else:
                        timed_out = True
                        wiring.scheduler.cancel("p036-live-smoke", "180 second smoke deadline expired")
                        cancel_deadline = time.monotonic() + 15
                        while time.monotonic() < cancel_deadline:
                            wiring.scheduler.step()
                            if wiring.scheduler.snapshot().status in ("blocked", "cancelled"):
                                break
                            time.sleep(0.1)
                    wiring.executor.wait_idle(20)
                finally:
                    wiring.close()
                    assignment.close()
                elapsed = round(time.monotonic() - started, 3)
                snapshot = wiring.scheduler.snapshot()
                task_view = snapshot.tasks[TASK_ID]
                connection = sqlite3.connect(ledger_path.as_uri() + "?mode=ro", uri=True)
                try:
                    saved = connection.execute(
                        "SELECT record_json FROM decision_records WHERE plan_id=? ORDER BY seq DESC LIMIT 1",
                        (plan_ref["plan_id"],),
                    ).fetchone()
                finally:
                    connection.close()
                decision = json.loads(saved[0]) if saved is not None else {}
                selected = decision.get("selected")
                selected = selected if isinstance(selected, dict) else {}
                persisted_routes = [selected, *decision["alternatives"]]
                persisted_accounts = {route["account_ref"] for route in persisted_routes}
                persisted_providers = {route["provider"] for route in persisted_routes}
                attempt_ids = wiring.executor.ledger.all_ids()
                attempt = wiring.executor.ledger.get(attempt_ids[0]) if attempt_ids else None
                task_reference = task_view.get("executor")
                raw_reference = task_reference.removeprefix("route:") if isinstance(task_reference, str) else ""
                binding = resolve_executor_binding(ledger_path, raw_reference) if raw_reference else None
                launched = attempt.get("route", {}) if isinstance(attempt, dict) else {}
                repo_unchanged = (git(repo, "rev-parse", "HEAD"), git(repo, "status", "--porcelain")) == \
                    (before_head, before_status)

                result = {
                    "plan_id": plan_ref["plan_id"], "revision": plan_ref["revision"],
                    "candidate_sampled_at": quota_sampled_at,
                    "eligible": [{
                        "profile": candidate.profile, "provider": candidate.provider, "model": candidate.model,
                        "quota_used_percent": candidate.quota_used_percent,
                        "sample_age_seconds": round(quota_sampled_at - candidate.quota_observed_at, 2),
                        "valid_until": candidate.quota_valid_until,
                    } for candidate in ranking.eligible],
                    "selected": {key: selected.get(key) for key in ("profile", "provider", "model")},
                    "persisted_distinct_accounts": len(persisted_accounts),
                    "m1_state": snapshot.status, "m1_task_state": task_view.get("state"),
                    "m2_binding_valid": binding is not None,
                    "m3_route": {key: launched.get(key) for key in ("profile", "provider", "model", "reference")},
                    "m3_attempt_state": attempt.get("state") if isinstance(attempt, dict) else None,
                    "m3_returncode": (attempt.get("outcome") or {}).get("returncode")
                    if isinstance(attempt, dict) else None,
                    "independent_verifier_passed": bool(verifier.results and verifier.results[0]["accepted"]),
                    "handoff": (attempt.get("handoff") or {}).get("status") if isinstance(attempt, dict) else None,
                    "elapsed_seconds": elapsed, "timed_out": timed_out,
                    "source_checkout_unchanged": repo_unchanged,
                }
                artifact_root = Path.home() / ".local" / "share" / "bt-scheduler-p036"
                artifact_root.mkdir(parents=True, exist_ok=True, mode=0o700)
                artifact_dir = Path(tempfile.mkdtemp(prefix="smoke-", dir=artifact_root))
                artifact = artifact_dir / "result.json"
                _write_private(artifact, result)
                print("P036_ARTIFACT " + str(artifact))

                self.assertFalse(timed_out, "real-provider smoke exceeded 180 seconds")
                self.assertEqual((snapshot.status, task_view["state"]), ("completed", "completed"))
                self.assertEqual(len(verifier.results), 1)
                self.assertTrue(verifier.results[0]["accepted"], verifier.results[0]["evidence"])
                self.assertIsNotNone(saved, "M2 did not persist its route decision")
                self.assertTrue(selected, "M2 did not persist a selected route")
                self.assertGreaterEqual(len(persisted_accounts), 2,
                                        "persisted M2 record lacks a second quota-valid account")
                self.assertGreaterEqual(len(persisted_providers), 2,
                                        "persisted M2 record lacks a second provider")
                for route in persisted_routes:
                    source = eligible_by_account.get(route["account_ref"])
                    self.assertIsNotNone(source, "persisted route was not in the preflight eligible set")
                    self.assertGreater(route["quota_valid_until"], decision["created_at"])
                    self.assertEqual((route["profile"], route["provider"]), (source.profile, source.provider))
                self.assertEqual(len(attempt_ids), 1)
                self.assertIsInstance(attempt, dict)
                self.assertEqual(attempt["state"], "finished")
                self.assertEqual((attempt["outcome"]["returncode"], attempt["outcome"]["terminal_event"]), (0, True))
                self.assertEqual(attempt["handoff"]["status"], "captured")
                self.assertIsNotNone(binding)
                self.assertEqual((launched["profile"], launched["provider"], launched["model"]),
                                 (selected["profile"], selected["provider"], selected["model"]))
                self.assertEqual(launched["reference"], task_reference)
                self.assertTrue(repo_unchanged, "the disposable source checkout changed")


if __name__ == "__main__":
    unittest.main()
