"""Reproducible D-10 replay against the real M1 SchedulerCore and recovery benchmark.

No providers are called. Token figures are a labeled proxy derived from actual M1 task attempts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from collections import deque
from pathlib import Path
from typing import Any

from bt_scheduler_adapter import core as m1

Plan = m1.Plan

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "skill/scripts/bt_planner/tests/fixtures"
DEFECTS = FIXTURES / "P-177-defect-map.json"
TOKEN_PROXY_PER_ATTEMPT_MINUTE = 32
PARALLELISM = 3
SAFETY_LIMIT = 100_000
FIXTURES_USED = {
    "legacy": FIXTURES / "P-177-legacy-1.2.0.json",
    "subplans": FIXTURES / "P-177-schema-1.3.0.json",
}


class BenchmarkClock:
    """Clock controlled only by the deterministic event loop."""

    def __init__(self, start: float):
        self.now = float(start)

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> float:
        self.now += seconds
        return self.now


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> Plan:
    # Planner's validator emits subplan_id:null for composition tasks; M1's optional-field wire format omits it.
    # This normalization preserves the fixture's graph and task semantics while using the core's public loader.
    data = json.loads(path.read_text(encoding="utf-8"))
    for task in data["tasks"]:
        if task.get("subplan_id", "missing") is None:
            task.pop("subplan_id")
    raw = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return m1.load_plan(raw, approved_sha256=hashlib.sha256(raw.encode("utf-8")).hexdigest())


def _reachable_distance(plan: Plan, source: str, target: str) -> int | None:
    queue = deque([(source, 0)])
    seen = {source}
    while queue:
        task_id, distance = queue.popleft()
        if task_id == target:
            return distance
        for task in plan.tasks:
            if task.id not in seen and task_id in task.after:
                seen.add(task.id)
                queue.append((task.id, distance + 1))
    return None


def barrier_map(plan: Plan, defect_map: dict[str, Any]) -> dict[str, str]:
    """Find each defect's earliest reachable declared checkpoint/audit from the actual plan graph."""
    candidates: list[str] = []
    for subplan in plan.subplans:
        candidates.extend(checkpoint["task"] for checkpoint in subplan.checkpoints)
        if subplan.audit_task:
            candidates.append(subplan.audit_task)
    if not candidates:
        candidates.extend(task.id for task in plan.tasks if task.meta.get("kind") == "audit")
    found: dict[str, str] = {}
    for defect in defect_map["defects"]:
        source = defect["introducing_task"]
        reachable = [(plan.ids().index(task_id), task_id)
                     for task_id in dict.fromkeys(candidates)
                     if _reachable_distance(plan, source, task_id) is not None]
        if not reachable:
            raise ValueError(f"no declared barrier is reachable from {source}")
        found[defect["defect"]] = min(reachable)[1]
    return found


def _run_flow(plan: Plan, *, defects: bool) -> dict[str, Any]:
    repository, clock = m1.InMemoryRepository(), BenchmarkClock(1_000_000)
    executor, verifier = m1.FakeExecutor(), m1.FakeVerifier()
    core = m1.SchedulerCore(plan, repository, ports=m1.Ports(execution=executor, verification=verifier),
                            config=m1.Config(max_parallel_tasks=PARALLELISM, max_attempts=1), clock=clock)
    data = json.loads(DEFECTS.read_text(encoding="utf-8"))
    barriers = barrier_map(plan, data)
    by_barrier: dict[str, list[dict[str, str]]] = {}
    audit_to_subplan = {subplan.audit_task: subplan.id for subplan in plan.subplans}
    if defects:
        for item in data["defects"]:
            by_barrier.setdefault(barriers[item["defect"]], []).append(item)

    core.start()
    completed_exec: set[str] = set()
    completed_verify: set[str] = set()
    due: dict[str, float] = {}
    detected: set[str] = set()
    attempt_minutes = 0
    accepted_minutes_discarded = 0
    rework_transitions = 0
    redone_ids: set[str] = set()
    first_exposure: dict[str, str] = {}

    for _ in range(SAFETY_LIMIT):
        core.step()
        for attempt_id, order in list(executor.started.items()):
            if attempt_id not in due:
                estimate = int(plan.task(order.task_id).meta.get("estimated_minutes") or 0)
                attempt_minutes += estimate
                due[attempt_id] = clock.now + estimate * 60
        now_due = sorted((when, attempt_id) for attempt_id, when in due.items()
                         if when <= clock.now and attempt_id not in completed_exec)
        if not now_due and due:
            next_due = min(when for attempt_id, when in due.items() if attempt_id not in completed_exec)
            clock.advance(next_due - clock.now)
            now_due = sorted((when, attempt_id) for attempt_id, when in due.items()
                             if when <= clock.now and attempt_id not in completed_exec)
        for _, attempt_id in now_due:
            order = executor.started[attempt_id]
            completed_exec.add(attempt_id)
            core.ingest(m1.Event(f"bench-finish-{attempt_id}", plan.plan_id, plan.revision, order.task_id, attempt_id,
                                 "benchmark-executor", m1.EventKind.EXECUTION_FINISHED.value, str(clock.now)))
        core.step()
        for attempt_id, order in list(verifier.requests.items()):
            if attempt_id in completed_verify:
                continue
            completed_verify.add(attempt_id)
            core.submit_verdict(m1.Verdict(f"bench-accept-{attempt_id}", plan.plan_id, plan.revision,
                                           order.task_id, attempt_id, True, "benchmark-validator",
                                           "simulated checks passed", occurred_at=str(clock.now)))
            if order.task_id in audit_to_subplan:
                subplan_id = audit_to_subplan[order.task_id]
                with repository.read_transaction() as tx:
                    version = 1 + tx.state.subplan_versions.get(subplan_id, {}).get("version", 0)
                manifest = hashlib.sha256(f"{plan.sha256}:{subplan_id}:v{version}".encode()).hexdigest()
                commit = hashlib.sha256(f"commit:{plan.sha256}:{subplan_id}:v{version}".encode()).hexdigest()[:40]
                core.record_subplan_version(subplan_id, version, commit, manifest)
            if order.task_id in by_barrier:
                observed = [item for item in by_barrier[order.task_id] if item["defect"] not in detected]
                for item in observed:
                    detected.add(item["defect"])
                    first_exposure[item["defect"]] = order.task_id
                if observed:
                    roots = tuple(item["introducing_task"] for item in observed)
                    impact = core.rework_impact(roots)
                    accepted_minutes_discarded += sum(
                        int(plan.task(task_id).meta.get("estimated_minutes") or 0) for task_id in impact
                    )
                    reset = core.rework(roots, "benchmark-m6", "simulated barrier found injected defect")
                    redone_ids.update(reset)
                    rework_transitions += 1

        snap = core.snapshot()
        if snap.status == m1.RunStatus.BLOCKED.value and snap.counts.get("live_attempts", 0) == 0:
            # A just-published subplan version wakes its composition gate on the next M1 refresh.
            report = core.step()
            snap = core.snapshot()
            if report.progress:
                continue
        if snap.status in (m1.RunStatus.COMPLETED.value, m1.RunStatus.BLOCKED.value, m1.RunStatus.CANCELLED.value) \
                and snap.counts.get("live_attempts", 0) == 0:
            attempts_by_task = {task_id: view["attempts"] for task_id, view in snap.tasks.items()}
            actual_redo_attempts = sum(max(0, count - 1) for count in attempts_by_task.values())
            if defects and detected != {d["defect"] for d in data["defects"]}:
                raise RuntimeError(f"not every injected defect was observed: {detected}")
            return {
                "status": snap.status,
                "accepted": snap.status == m1.RunStatus.COMPLETED.value and snap.counts.get("completed", 0) == len(plan.tasks),
                "task_count": len(plan.tasks),
                "attempts": sum(attempts_by_task.values()),
                "rework_transitions": rework_transitions,
                "redone_tasks": len({task_id for task_id, count in attempts_by_task.items() if count > 1}),
                "redone_task_attempts": actual_redo_attempts,
                "accepted_estimated_minutes_discarded": accepted_minutes_discarded,
                "attempt_minutes": attempt_minutes,
                "simulated_wall_seconds": round(clock.now - 1_000_000, 3),
                "token_proxy": {
                    "label": "estimated proxy; no provider tokens observed",
                    "fixed_proxy_tokens_per_attempt_minute": TOKEN_PROXY_PER_ATTEMPT_MINUTE,
                    "value": attempt_minutes * TOKEN_PROXY_PER_ATTEMPT_MINUTE,
                },
                "first_exposure": first_exposure,
                "reset_task_ids": sorted(redone_ids),
                "subplan_status": core.subplan_status(),
                "parallelism": PARALLELISM,
            }
    raise RuntimeError("M1 benchmark did not terminate")


def run_engine_benchmark() -> dict[str, Any]:
    data = json.loads(DEFECTS.read_text(encoding="utf-8"))
    scenarios = {}
    for flow, path in FIXTURES_USED.items():
        plan = _load(path)
        derived = barrier_map(plan, data)
        scenarios[flow] = {
            "fixture": str(path.relative_to(ROOT)),
            "fixture_sha256": _sha(path),
            "fixture_plan_id": plan.plan_id,
            "fixture_revision": plan.revision,
            "fixture_schema": plan.schema_version,
            "core_input_normalization": "subplan_id:null omitted for M1 optional-field wire compatibility",
            "clean": _run_flow(plan, defects=False),
            "with_defects": _run_flow(plan, defects=True),
            "derived_barriers": derived,
        }
    return {
        "schema": "engine-v2-d10/1",
        "identity": {
            "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                                      capture_output=True, text=True).stdout.strip(),
            "config": {"parallelism": PARALLELISM, "token_proxy_per_attempt_minute": TOKEN_PROXY_PER_ATTEMPT_MINUTE},
            "reference_command": "PYTHONPATH=skill/scripts python -m bt_engine_benchmark --recovery-baseline <pre-engine-v2-worktree> --json <result.json> --markdown <result.md>",
            "defect_fixture": str(DEFECTS.relative_to(ROOT)),
            "defect_fixture_sha256": _sha(DEFECTS),
        },
        "scenarios": scenarios,
    }


def recovery_snapshot(repo: Path) -> dict[str, Any]:
    """Call the existing recovery benchmark with deterministic free-space input and no real state."""
    code = ("import json, shutil; "
            "from types import SimpleNamespace; "
            "shutil.disk_usage=lambda path: SimpleNamespace(total=20<<30, used=1<<30, free=19<<30); "
            "import bt_recovery_benchmark as b; "
            "print(json.dumps(b.run()))")
    env = {**os.environ, "PYTHONPATH": str(repo / "skill/scripts")}
    result = subprocess.run([sys.executable, "-c", code], cwd=repo, env=env, check=True,
                            capture_output=True, text=True)
    return json.loads(result.stdout)


def compare_recovery(baseline: Path, candidate: Path) -> dict[str, Any]:
    before, after = recovery_snapshot(baseline), recovery_snapshot(candidate)
    sys.path.insert(0, str(candidate / "skill/scripts"))
    try:
        import bt_recovery_benchmark
        regressions = bt_recovery_benchmark.regressions(before["totals"], after["totals"])
    finally:
        sys.path.pop(0)
        sys.modules.pop("bt_recovery_benchmark", None)
    baseline_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=baseline, check=True,
                                     capture_output=True, text=True).stdout.strip()
    candidate_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=candidate, check=True,
                                      capture_output=True, text=True).stdout.strip()
    known_pending = [row["id"] for row in before["scenarios"] if row["recovery_pending"]]
    return {"baseline_commit": baseline_commit, "candidate_commit": candidate_commit,
            "free_space_mock": "19 GiB free, injected for both revisions; no healing code changed",
            "baseline": before, "candidate": after, "regressions": regressions,
            "known_baseline_issues": [{"scenario": scenario, "classification": "P-186 unresolved audit retained",
                                       "preserved_in_candidate": scenario in
                                       [row["id"] for row in after["scenarios"] if row["recovery_pending"]]}
                                      for scenario in known_pending]}


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# Engine v2 D-10 benchmark", "", f"Commit: `{report['identity']['commit']}`", "",
             "| Flow | Scenario | Accepted | Attempts | Redone tasks | Discarded accepted min | Wall seconds | Token proxy |",
             "|---|---|---:|---:|---:|---:|---:|---:|"]
    for flow, group in report["scenarios"].items():
        for name in ("clean", "with_defects"):
            item = group[name]
            lines.append(f"| {flow} | {name} | {item['accepted']} | {item['attempts']} | {item['redone_tasks']} | "
                         f"{item['accepted_estimated_minutes_discarded']} | {item['simulated_wall_seconds']} | "
                         f"{item['token_proxy']['value']} |")
    lines.extend(["", f"Token proxy: **{TOKEN_PROXY_PER_ATTEMPT_MINUTE} proxy tokens per actual attempt minute**; "
                  "no provider tokens or cost were observed.", ""])
    recovery = report.get("recovery_no_regression")
    if recovery:
        lines.extend(["## Recovery benchmark", "", "| Metric | Pre-engine-v2 | Candidate |",
                      "|---|---:|---:|"])
        for metric in ("human_interventions", "minutes_to_recovery", "classified", "as_expected"):
            lines.append(f"| {metric} | {recovery['baseline']['totals'][metric]} | "
                         f"{recovery['candidate']['totals'][metric]} |")
        lines.extend(["", f"No-regression metrics: {'PASS' if not recovery['regressions'] else 'FAIL'}; "
                      f"known baseline issues remain separately represented in per-scenario rows.", ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, help="write deterministic JSON report")
    parser.add_argument("--markdown", type=Path, help="write readable comparison")
    parser.add_argument("--recovery-baseline", type=Path, help="pre-engine-v2 worktree for recovery comparison")
    parser.add_argument("--recovery-candidate", type=Path, default=ROOT, help="candidate worktree")
    args = parser.parse_args(argv)
    result = run_engine_benchmark()
    if args.recovery_baseline:
        result["recovery_no_regression"] = compare_recovery(args.recovery_baseline, args.recovery_candidate)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.json:
        args.json.write_text(encoded, encoding="utf-8")
    if args.markdown:
        args.markdown.write_text(render_markdown(result), encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
