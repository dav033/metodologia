"""Opt-in REQ-020 T24 run: eight independently verified tasks through live M1/M2/M3."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import ExitStack
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import bt_agents
import bt_agy
import bt_core
import bt_profiles
import bt_scheduler_adapter as m1
import bt_scheduler_decision_adapter as m2_sources
import bt_subscriptions
import test_scheduler_m2_live_smoke as live_support
from bt_scheduler_decision import DecisionRequest, rank_candidates
from bt_scheduler_executor import Config as M3Config
from bt_scheduler_executor_adapter import wire
from scheduler_executor_support import git, make_repo
from scheduler_m2_live_experiment_support import (
    attempt_task_id,
    settle_after_stop,
    workspace_scope,
)

PROJECT = "req020-t24-live"
REQ = "REQ-997"
MAX_TASKS = 8
MAX_CONCURRENCY = 2
MAX_RUN_SECONDS = 2 * 60 * 60
ATTEMPT_TIMEOUT_SECONDS = 300
MAX_QUOTA_USED_PERCENT = 50.0

TASKS: tuple[dict[str, object], ...] = (
    {
        "id": "T1", "name": "collapse_ws", "title": "Collapse whitespace in text",
        "objective": "Implement collapse_whitespace(text: str) -> str. Replace every run of whitespace with one ASCII space and trim both ends. Raise TypeError for non-string input.",
        "acceptance": ("Whitespace runs collapse to one space.", "Leading and trailing whitespace are removed.",
                       "Non-string input raises TypeError."),
        "probe": "from collapse_ws import collapse_whitespace; assert collapse_whitespace('  a\\t b\\n') == 'a b'; assert collapse_whitespace('') == ''; exec(\"try:\\n collapse_whitespace(1)\\nexcept TypeError:\\n pass\\nelse:\\n raise AssertionError()\")",
    },
    {
        "id": "T2", "name": "snake_case", "title": "Convert identifiers to snake case",
        "objective": "Implement to_snake_case(identifier: str) -> str. Convert camelCase, PascalCase and acronym boundaries to lowercase snake_case, preserve existing word boundaries, and reject non-string input with TypeError.",
        "acceptance": ("HTTPServer becomes http_server.", "parseURLValue becomes parse_url_value.",
                       "Existing underscores are normalized without duplicate separators.", "Non-string input raises TypeError."),
        "probe": "from snake_case import to_snake_case; assert to_snake_case('HTTPServer') == 'http_server'; assert to_snake_case('parseURLValue') == 'parse_url_value'; assert to_snake_case('Already_Snake') == 'already_snake'",
    },
    {
        "id": "T3", "name": "slugify", "title": "Create deterministic ASCII slugs",
        "objective": "Implement slugify(text: str) -> str. Lowercase ASCII letters, retain ASCII digits, replace every run of other characters with one hyphen, trim edge hyphens, and reject non-string input with TypeError.",
        "acceptance": ("ASCII letters are lowercase and digits are retained.", "Punctuation and non-ASCII characters become separators.",
                       "Repeated separators and edge hyphens are removed."),
        "probe": "from slugify import slugify; assert slugify('Hello, World!') == 'hello-world'; assert slugify('Café & Tea!') == 'caf-and-tea'; assert slugify('---A__B---') == 'a-b'",
    },
    {
        "id": "T4", "name": "truncate_text", "title": "Truncate text within a character limit",
        "objective": "Implement truncate_text(text: str, limit: int, suffix: str = '...') -> str. Return unchanged text within the limit; otherwise include a prefix and suffix whose combined length is exactly limit. Require a non-negative integer limit (booleans are invalid), a string suffix, and a suffix no longer than limit; use TypeError for wrong types and ValueError for invalid values.",
        "acceptance": ("Text at or below the limit is unchanged.", "Long text is truncated with the requested suffix.",
                       "The output never exceeds the limit.", "Invalid types and limits raise deliberate errors."),
        "probe": "from truncate_text import truncate_text; assert truncate_text('abcd', 4) == 'abcd'; assert truncate_text('abcdef', 5) == 'ab...'; assert len(truncate_text('abcdef', 2, '!')) <= 2",
    },
    {
        "id": "T5", "name": "parse_bool", "title": "Parse explicit boolean values",
        "objective": "Implement parse_bool(value: str | bool) -> bool. Pass booleans through. Accept case-insensitive trimmed true/1/yes/on and false/0/no/off strings. Raise ValueError for other strings and TypeError for other types.",
        "acceptance": ("Supported true and false spellings parse correctly.", "Whitespace and case are normalized.",
                       "Unknown strings raise ValueError; unrelated types raise TypeError."),
        "probe": "from parse_bool import parse_bool; assert parse_bool(' YES ') is True; assert parse_bool('Off') is False; assert parse_bool(True) is True; exec(\"try:\\n parse_bool('maybe')\\nexcept ValueError:\\n pass\\nelse:\\n raise AssertionError()\")",
    },
    {
        "id": "T6", "name": "count_words", "title": "Count whitespace-delimited words",
        "objective": "Implement count_words(text: str) -> int using Python's Unicode-aware whitespace splitting. Empty or whitespace-only text returns zero. Reject non-string input with TypeError.",
        "acceptance": ("Whitespace separates words, including newlines and tabs.", "Empty input returns zero.",
                       "Unicode text is preserved and counted as tokens.", "Non-string input raises TypeError."),
        "probe": "from count_words import count_words; assert count_words('one\\ttwo\\nthree') == 3; assert count_words('  ') == 0; assert count_words('café tea') == 2",
    },
    {
        "id": "T7", "name": "format_list", "title": "Format a list with an Oxford comma",
        "objective": "Implement format_list(items: list[str], conjunction: str = 'and') -> str. Return an empty string for no items, the item itself for one, join two with the conjunction, and use an Oxford comma for three or more. Require string items and a non-empty string conjunction; use TypeError for wrong types and ValueError for an empty or whitespace-only conjunction.",
        "acceptance": ("Empty, single-item and two-item forms are exact.", "Three or more items use an Oxford comma.",
                       "Invalid items and conjunctions fail deliberately."),
        "probe": "from format_list import format_list; assert format_list([]) == ''; assert format_list(['a']) == 'a'; assert format_list(['a', 'b']) == 'a and b'; assert format_list(['a', 'b', 'c']) == 'a, b, and c'",
    },
    {
        "id": "T8", "name": "normalize_newlines", "title": "Normalize common newline sequences",
        "objective": "Implement normalize_newlines(text: str) -> str. Convert CRLF and lone CR to LF, preserve existing LF and all other characters, and reject non-string input with TypeError.",
        "acceptance": ("CRLF and lone CR become LF.", "Existing LF and trailing newline are preserved.",
                       "Normalization is idempotent.", "Non-string input raises TypeError."),
        "probe": "from normalize_newlines import normalize_newlines; value = 'a\\r\\nb\\rc\\n'; assert normalize_newlines(value) == 'a\\nb\\nc\\n'; assert normalize_newlines(normalize_newlines(value)) == 'a\\nb\\nc\\n'",
    },
)

TASK_BY_ID = {str(task["id"]): task for task in TASKS}


def _task_paths(task: dict[str, object]) -> tuple[str, str]:
    name = str(task["name"])
    tid = str(task["id"]).lower()
    return f"src/{name}.py", f"tests/test_{tid}.py"


def _prepare_plan(root: Path, repo: Path) -> tuple[Path, dict[str, object]]:
    project_dir = root / PROJECT
    project_dir.mkdir(parents=True)
    (project_dir / "project.json").write_text(json.dumps({
        "work": False,
        "repos": {"app": {"remote": "", "hint": str(repo)}},
    }, indent=2) + "\n", encoding="utf-8")
    rdir = project_dir / "requirements" / f"{REQ}-bounded-live"
    rdir.mkdir(parents=True)
    spec_lines = ["# T24 disposable task set", "", "Each task is independent and modifies only its declared files.", ""]
    plan_lines = ["---", f"req: {REQ}", "status: approved", "---", "", "# Plan — REQ-020 T24", "", "### M1 — Implement eight isolated text utilities"]
    for task in TASKS:
        tid = str(task["id"])
        source_path, test_path = _task_paths(task)
        spec_lines.extend([f"## {tid} — {task['title']}", "", str(task["objective"]), "",
                           "Acceptance:", *(f"- {item}" for item in task["acceptance"]), ""])
        plan_lines.append(
            f"- [ ] {tid} — {task['title']} · repo: app · files: {source_path}, {test_path} "
            f"· verify: `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_{tid.lower()}.py' -v`"
        )
    (rdir / "SPEC.md").write_text("\n".join(spec_lines) + "\n", encoding="utf-8")
    (rdir / "PLAN.md").write_text("\n".join(plan_lines) + "\n", encoding="utf-8")
    output: list[str] = []
    if m1.plan_adapter.run_cli("init", rdir, emit=output.append) != 0:
        raise AssertionError("Planner init failed: " + " | ".join(output)[-1000:])
    plan_path = rdir / "PLAN.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["milestones"][0]["acceptance_criteria"] = [
        "Each task changes only its declared module and test file.",
        "Every completed task passes an independent test run and behavior probe.",
        "No dependencies, network access, or changes outside the disposable repository.",
    ]
    for task_view in plan["tasks"]:
        task = TASK_BY_ID[task_view["id"]]
        source_path, test_path = _task_paths(task)
        task_id, title = str(task["id"]), str(task["title"])
        evidence_reasons = {
            "complexity": f"{task_id} {title} is one deterministic pure-Python helper with explicit edge cases.",
            "scope": f"{task_id} {title} changes only {source_path} and {test_path}.",
            "duration": f"{task_id} {title} is one isolated helper and fits a short bounded attempt.",
            "risk": f"{task_id} {title} runs in the disposable repository without network or dependencies.",
            "coupling": f"{task_id} {title} has no consumers or shared state outside its declared module.",
            "confidence": f"SPEC.md section {task_id} fixes the {title.lower()} signature, behavior, paths and checks.",
        }
        task_view.update({
            "objective": task["objective"], "repository": "app", "complexity": "low",
            "scope": "small_change", "estimated_minutes": 15, "risk": "low", "coupling": "low",
            "confidence": "high", "estimate_rationale": "One pure helper and focused standard-library tests.",
            "classification_evidence": {
                key: {"justification": value, "evidence": ["spec:SPEC.md", "file:AGENTS.md"]}
                for key, value in evidence_reasons.items()
            },
            "expected_paths": [source_path, test_path], "shared_resources": [],
            "acceptance_criteria": list(task["acceptance"]),
            "verification": [{
                "type": "command",
                "value": f"PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_{str(task['id']).lower()}.py' -v",
                "purpose": "Run the declared tests in the isolated M3 task worktree.",
            }],
        })
    plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for action in ("check", "freeze"):
        output = []
        if m1.plan_adapter.run_cli(action, rdir, emit=output.append) != 0:
            raise AssertionError(f"Planner {action} failed: " + " | ".join(output)[-1000:])
    state = m1.plan_adapter.run_state_fields(rdir)
    if not state.get("plan_ref"):
        raise AssertionError("Planner did not freeze the T24 plan")
    return rdir, state


class _IndependentVerifier:
    """Verify each task in its actual isolated M3 handoff before submitting the M1 verdict."""

    def __init__(self) -> None:
        self.scheduler = None
        self.wiring = None
        self.results: list[dict[str, object]] = []

    def request(self, order):
        row = self.wiring.executor.ledger.get(order.attempt_id)
        workspace = Path(row["workspace"]["path"]) if isinstance(row, dict) and isinstance(
            row.get("workspace"), dict) and isinstance(row["workspace"].get("path"), str) else None
        task = TASK_BY_ID.get(order.task_id)
        accepted, test_count, test_exit, probe_exit = False, 0, None, None
        paths_ok = False
        changed_paths: tuple[str, ...] = ()
        undeclared_paths: tuple[str, ...] = ()
        if workspace is not None and task is not None:
            paths_ok, changed_paths, undeclared_paths = workspace_scope(workspace, _task_paths(task))
            env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(workspace / "src")}
            try:
                tested = subprocess.run(
                    [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests",
                     "-p", f"test_{order.task_id.lower()}.py", "-v"],
                    cwd=workspace, env=env, text=True, capture_output=True, timeout=60, check=False,
                )
                test_exit = tested.returncode
                match = re.search(r"Ran (\d+) tests?", tested.stdout + tested.stderr)
                test_count = int(match.group(1)) if match else 0
                probe = subprocess.run(
                    [sys.executable, "-B", "-c", str(task["probe"])], cwd=workspace, env=env,
                    text=True, capture_output=True, timeout=15, check=False,
                )
                probe_exit = probe.returncode
                accepted = paths_ok and test_exit == 0 and test_count >= 3 and probe_exit == 0
            except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
                accepted = False
        details = (f"tests_exit={test_exit}; tests_run={test_count}; behavior_probe_exit={probe_exit}; "
                   f"declared_scope_valid={paths_ok}; changed_paths={json.dumps(changed_paths)}; "
                   f"undeclared_paths={json.dumps(undeclared_paths)}")
        self.results.append({"attempt_id": order.attempt_id, "task_id": order.task_id,
                             "accepted": accepted, "evidence": details})
        self.scheduler.submit_verdict(m1.core.Verdict(
            verdict_id=f"t24-verdict-{order.attempt_id}", plan_id=order.plan_id, revision=order.revision,
            task_id=order.task_id, attempt_id=order.attempt_id, accepted=accepted,
            verifier="req020-t24-independent-unittest", evidence=details, token=order.token,
        ))
        return m1.core.Ack("accepted")


def _quota_summary(row: dict[str, object]) -> dict[str, object]:
    windows = row.get("windows") if isinstance(row.get("windows"), dict) else {}
    return {
        "status": row.get("status"), "observed_at": row.get("observed_at"),
        "windows": {name: {key: value for key, value in value_row.items()
                           if key in ("used_percent", "resets_at", "window_minutes")}
                    for name, value_row in windows.items() if isinstance(value_row, dict)},
    }


def _write_artifact(result: dict[str, object]) -> Path:
    root = Path.home() / ".local" / "share" / "bt-scheduler-m2-experiment"
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    run_dir = Path(tempfile.mkdtemp(prefix="t24-", dir=root))
    artifact = run_dir / "result.json"
    live_support._write_private(artifact, result)
    return artifact


class LiveSchedulerM2ExperimentTests(unittest.TestCase):
    def test_bounded_eight_task_experiment(self):
        if os.environ.get("BITACORA_LIVE_SCHEDULER_M2_EXPERIMENT") != "1":
            self.skipTest("set BITACORA_LIVE_SCHEDULER_M2_EXPERIMENT=1 only after owner authorization")

        actual_state = bt_core.STATE
        source_profiles = bt_profiles.load()
        subscription_rows, agy_row, refreshed_profiles = live_support._refresh_live_quotas()
        self.assertEqual(set(source_profiles), set(refreshed_profiles))
        task_manifest_sha256 = hashlib.sha256(json.dumps(TASKS, sort_keys=True).encode()).hexdigest()

        with tempfile.TemporaryDirectory(prefix="req020-t24-") as tmp_name:
            temp_root = Path(tmp_name) / "bitacora"
            state_dir = temp_root / ".state"
            state_dir.mkdir(parents=True, mode=0o700)
            repo = make_repo(Path(tmp_name) / "project")
            (repo / "AGENTS.md").write_text(
                "# Disposable T24 repository\n\n"
                "Work only on the files declared by your assigned task in the approved plan. Do not inspect or modify "
                "other repositories, settings, credentials or runs. Do not use the network or install dependencies. "
                "Implement only the requested pure-Python helper and its tests.\n",
                encoding="utf-8",
            )
            (repo / ".gitignore").write_text("__pycache__/\n*.py[cod]\n", encoding="utf-8")
            git(repo, "add", "AGENTS.md", ".gitignore")
            git(repo, "commit", "-q", "-m", "test: define disposable T24 boundaries")
            before_head, before_status = git(repo, "rev-parse", "HEAD"), git(repo, "status", "--porcelain")
            live_support._write_private(state_dir / "profiles.json", source_profiles)
            if isinstance(subscription_rows, dict):
                live_support._write_private(state_dir / "subscription-usage.json",
                                           {"schema_version": 1, "accounts": subscription_rows})
            if agy_row:
                live_support._write_private(state_dir / "agy-usage.json", agy_row)
            try:
                quota_state = json.loads((actual_state / "quota.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                quota_state = {}
            live_support._write_private(state_dir / "quota.json", quota_state)

            with ExitStack() as stack:
                for target, attribute, replacement in (
                    (bt_core, "ROOT", temp_root), (bt_core, "STATE", state_dir),
                    (bt_profiles, "ROOT", temp_root), (bt_profiles, "STATE", state_dir),
                    (bt_agents, "STATE", state_dir), (bt_subscriptions, "STATE", state_dir),
                ):
                    stack.enter_context(patch.object(target, attribute, replacement))

                rdir, plan_state = _prepare_plan(temp_root, repo)
                plan_ref = plan_state["plan_ref"]
                preflight_at = time.time()
                candidate_rows = m2_sources._candidate_rows(PROJECT, "implement", {
                    "complexity": "low", "scope": "small_change", "estimated_minutes": 15,
                    "risk": "low", "coupling": "low", "confidence": "high",
                }, preflight_at)
                request = DecisionRequest(
                    plan_ref["plan_id"], plan_ref["revision"], plan_ref["sha256"], MAX_CONCURRENCY,
                    preflight_at, live_support.TASK_FACTS, candidate_rows, m2_sources.POLICY_VERSION, None,
                )
                ranking = rank_candidates(request)
                eligible = ranking.eligible
                eligible_models = sorted({(candidate.provider, candidate.model) for candidate in eligible})
                eligible_accounts = {candidate.account_ref for candidate in eligible}
                fresh = all(candidate.quota_valid_until is not None and preflight_at < candidate.quota_valid_until
                            and candidate.quota_observed_at is not None
                            and 0 <= preflight_at - candidate.quota_observed_at <= 7200
                            for candidate in eligible)
                usage_values = [candidate.quota_used_percent for candidate in eligible
                                if candidate.quota_used_percent is not None]
                usage_under_limit = bool(usage_values) and max(usage_values) < MAX_QUOTA_USED_PERCENT
                gate_passed = len(eligible_models) >= 2 and bool(eligible_accounts) and fresh and usage_under_limit

                exhausted_request = replace(request, candidates=tuple(
                    replace(candidate, quota_status="exhausted", quota_used_percent=100.0)
                    for candidate in candidate_rows
                ))
                exhausted_ranking = rank_candidates(exhausted_request)
                self.assertEqual(exhausted_ranking.eligible, (), "controlled quota exhaustion must fail closed")
                control = {"simulated": True, "eligible_after_exhaustion": 0, "provider_calls": 0}

                gate_result = {
                    "authorized_by_owner": True, "authorization_date": "2026-10-16",
                    "plan_id": plan_ref["plan_id"], "plan_revision": plan_ref["revision"],
                    "plan_sha256": plan_ref["sha256"], "task_manifest_sha256": task_manifest_sha256,
                    "tasks_planned": MAX_TASKS, "max_concurrency": MAX_CONCURRENCY,
                    "attempt_timeout_seconds": ATTEMPT_TIMEOUT_SECONDS, "overall_deadline_seconds": MAX_RUN_SECONDS,
                    "eligible_models": [{"provider": provider, "model": model} for provider, model in eligible_models],
                    "eligible_effective_accounts": len(eligible_accounts),
                    "fresh_quota": fresh, "quota_used_percent_max": max(usage_values) if usage_values else None,
                    "preflight_passed": gate_passed, "controlled_quota_failure": control,
                    "quota_before": _quota_summary(agy_row),
                    "account_level_route_comparison": "unavailable" if len(eligible_accounts) < 2 else "available",
                }
                if not gate_passed:
                    artifact = _write_artifact({**gate_result, "experiment_started": False,
                                                "stop_reason": "T24 quota/model-route preflight failed"})
                    self.skipTest(f"T24 preflight failed before provider launch; artifact={artifact}")
                if os.environ.get("BITACORA_LIVE_SCHEDULER_M2_PREFLIGHT_ONLY") == "1":
                    artifact = _write_artifact({**gate_result, "experiment_started": False,
                                                "stop_reason": "preflight-only mode"})
                    self.skipTest(f"T24 preflight passed; no agent launched; artifact={artifact}")

                ledger_path = Path(tmp_name) / "m2-decisions.sqlite3"
                assignment = m1.DecisionAssignmentPort(PROJECT, ledger_path, laya_root=Path(tmp_name) / "laya-unused")
                verifier = _IndependentVerifier()
                wiring = wire(
                    rdir, project=PROJECT, assignment=assignment, verification=verifier,
                    repos={"app": repo}, default_repository="app", m2_ledger=ledger_path,
                    config=m1.core.Config(max_parallel_tasks=MAX_CONCURRENCY, max_attempts=1, lease_seconds=900),
                    executor_config=M3Config(max_running=MAX_CONCURRENCY, timeout_seconds=ATTEMPT_TIMEOUT_SECONDS,
                                             max_timeout_seconds=ATTEMPT_TIMEOUT_SECONDS, grace_seconds=2,
                                             heartbeat_seconds=15, poll_seconds=0.1),
                )
                verifier.wiring, verifier.scheduler = wiring, wiring.scheduler
                started = time.monotonic()
                started_at = time.time()
                deadline = started + MAX_RUN_SECONDS
                max_active = 0
                stop_reason = None
                timed_out = False
                m3_idle_after_stop: bool | None = None
                m1_settled_after_stop: bool | None = None
                try:
                    while time.monotonic() < deadline:
                        wiring.scheduler.step()
                        snapshot = wiring.scheduler.snapshot()
                        active = sum(task["state"] == "active" for task in snapshot.tasks.values())
                        max_active = max(max_active, active)
                        bad = [task_id for task_id, task in snapshot.tasks.items()
                               if task["state"] in ("blocked", "recovering")]
                        if bad:
                            stop_reason = "task entered blocked/recovering state: " + ",".join(sorted(bad))
                            wiring.scheduler.cancel(plan_ref["plan_id"], stop_reason)
                            break
                        if snapshot.status in ("completed", "blocked", "cancelled"):
                            break
                        time.sleep(0.1)
                    else:
                        timed_out = True
                        stop_reason = "T24 overall 2-hour deadline expired"
                        wiring.scheduler.cancel(plan_ref["plan_id"], stop_reason)
                    if stop_reason:
                        m3_idle_after_stop, m1_settled_after_stop = settle_after_stop(
                            wiring.scheduler, wiring.executor, deadline)
                    else:
                        m3_idle_after_stop = wiring.executor.wait_idle(
                            min(60.0, max(0.0, deadline - time.monotonic())))
                finally:
                    wiring.close()
                    assignment.close()

                elapsed = round(time.monotonic() - started, 3)
                final = wiring.scheduler.snapshot()
                quota_after = bt_agy.refresh()
                task_results = {
                    task_id: {"state": row["state"], "attempt_state": row.get("attempt_state"),
                      "attempt_id": None, "executor": row.get("executor")}
                    for task_id, row in final.tasks.items()
                }
                attempt_ids = wiring.executor.ledger.all_ids()
                attempts = []
                for attempt_id in attempt_ids:
                    attempt = wiring.executor.ledger.get(attempt_id)
                    if not isinstance(attempt, dict):
                        continue
                    route = attempt.get("route") if isinstance(attempt.get("route"), dict) else {}
                    outcome = attempt.get("outcome") if isinstance(attempt.get("outcome"), dict) else {}
                    task_id = attempt_task_id(attempt, task_results)
                    route_ref = route.get("reference") if isinstance(route.get("reference"), str) else None
                    attempts.append({
                        "attempt_id": attempt_id, "task_id": task_id, "state": attempt.get("state"),
                        "executor_ref": route_ref,
                        "provider": route.get("provider"), "model": route.get("model"),
                        "returncode": outcome.get("returncode"), "terminal_event": outcome.get("terminal_event"),
                        "usage": {key: value for key, value in (outcome.get("usage") or {}).items()
                                  if key in ("input_tokens", "output_tokens", "total_tokens")}
                        if isinstance(outcome.get("usage"), dict) else None,
                    })
                    if task_id in task_results:
                        task_results[task_id]["attempt_id"] = attempt_id
                accepted = sum(result["accepted"] for result in verifier.results)
                source_unchanged = (git(repo, "rev-parse", "HEAD"), git(repo, "status", "--porcelain")) == \
                    (before_head, before_status)
                result = {
                    **gate_result, "experiment_started": True, "started_at": started_at,
                    "elapsed_seconds": elapsed, "timed_out": timed_out, "stop_reason": stop_reason,
                    "m3_idle_after_stop": m3_idle_after_stop,
                    "m1_settled_after_stop": m1_settled_after_stop,
                    "m1_status": final.status, "tasks": task_results, "attempts": attempts,
                    "verifier_results": verifier.results, "verified_tasks": accepted,
                    "max_simultaneous_active_tasks": max_active,
                    "source_checkout_unchanged": source_unchanged,
                    "quota_after": _quota_summary(quota_after),
                    "quota_sample_advanced": quota_after.get("observed_at", 0) > agy_row.get("observed_at", 0),
                }
                artifact = _write_artifact(result)
                self.assertEqual(len(task_results), MAX_TASKS)
                self.assertTrue(all(task["state"] == "completed" for task in task_results.values()),
                                f"T24 ended without all tasks completed; artifact={artifact}")
                self.assertEqual(accepted, MAX_TASKS, f"independent verification failed; artifact={artifact}")
                self.assertEqual(len(attempts), len(verifier.results), "each attempt must have one verifier result")
                self.assertTrue(all(isinstance(attempt["task_id"], str) for attempt in attempts),
                                f"an attempt could not be attributed to one task; artifact={artifact}")
                self.assertEqual(len({attempt["task_id"] for attempt in attempts}), len(attempts),
                                 "an attempt was duplicated for a task")
                self.assertTrue(all(task["attempt_id"] is not None for task in task_results.values()),
                                f"a task has no correlated executor attempt; artifact={artifact}")
                self.assertEqual({attempt["task_id"] for attempt in attempts},
                                 {result["task_id"] for result in verifier.results},
                                 "attempt and independent-verifier task attribution differs")
                self.assertGreaterEqual(max_active, 2, f"did not observe two concurrent tasks; artifact={artifact}")
                self.assertTrue(source_unchanged, f"the disposable source checkout changed; artifact={artifact}")
                self.assertFalse(timed_out, f"T24 exceeded its deadline; artifact={artifact}")
                print("REQ020_T24_ARTIFACT " + str(artifact))


if __name__ == "__main__":
    unittest.main()
