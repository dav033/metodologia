"""Comparable metrics for the legacy and the durable runtime (REQ-030 M10), computed from the records each one keeps.

  python -m bt_durable.bench legacy <bitacora root> <project> <REQ>   attempts, verify failures, tokens, interventions
  python -m bt_durable.bench durable <telemetry.jsonl> [<launches.jsonl>]  launches, decisions, escalations, recovery

Nothing is estimated: a metric a source does not record is reported as null. Workloads differ between a real legacy
plan and the durable lab, so the numbers are evidence for specific mechanisms (one environment repair, one crash),
not a like-for-like throughput benchmark.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path


def _jsonl(path: Path) -> list[dict]:
    try:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except OSError:
        return []


def legacy(root: Path, project: str, req: str) -> dict:
    rdir = next((root / project / "requirements").glob(f"{req}-*"))
    events = [e for path in sorted((root / ".state" / "events").glob("attempts-*.jsonl")) for e in _jsonl(path)
              if e.get("project") == project and e.get("req") == req]
    decisions = _jsonl(rdir / "RUN.decisions.jsonl")
    interventions = _jsonl(rdir / "RUN.interventions.jsonl")
    per_task = collections.Counter(e.get("task") for e in events)
    results = collections.Counter(e.get("result") for e in events)
    return {
        "runtime": "legacy", "run": f"{project}/{req}",
        "attempts": len(events), "results": dict(results),
        "verify_failed_share": round(results.get("verify_failed", 0) / len(events), 3) if events else None,
        "tokens_reported": sum((e.get("usage") or {}).get("total_tokens") or 0 for e in events),
        "max_attempts_one_task": per_task.most_common(1)[0] if per_task else None,
        "human_decisions": sum(1 for d in decisions if d.get("by") == "owner"),
        "manual_interventions": sum(1 for i in interventions if i.get("source") == "manual"),
        "automatic_interventions": sum(1 for i in interventions if i.get("source") == "auto"),
        "minutes_lost_recorded": round(sum(i.get("minutes_lost") or 0 for i in interventions), 1),
    }


def durable(telemetry: Path, launches: Path | None = None) -> dict:
    events = _jsonl(telemetry)
    kinds = collections.Counter(e.get("event") for e in events)
    actions = collections.Counter(e.get("action") for e in events if e.get("event") == "recovery_decision")
    classes = collections.Counter(e.get("failure_class") for e in events if e.get("event") == "recovery_decision")
    started = {e.get("attempt_key") for e in events if e.get("event") == "attempt_started"}
    launched = _jsonl(launches) if launches else []
    settled = [e for e in events if e.get("event") == "task_settled"]
    return {
        "runtime": "durable", "attempt_workflows": len(started),
        "agent_processes": len(launched) if launches else None,
        "duplicate_launches": (len(launched) - len(started)) if launches else None,
        "recovery_decisions": dict(actions), "failure_classes": dict(classes),
        "human_decisions_requested": kinds.get("decision_requested", 0),
        "orphans_reaped": kinds.get("orphan_reaped", 0),
        "tasks_completed": sum(1 for e in settled if e.get("status") == "completed"),
        "tasks_blocked": sum(1 for e in settled if e.get("status") == "blocked"),
        "commands_refused": kinds.get("command_refused", 0),
    }


def main(argv: list[str]) -> int:
    if len(argv) == 4 and argv[0] == "legacy":
        print(json.dumps(legacy(Path(argv[1]), argv[2], argv[3]), indent=1))
        return 0
    if len(argv) in (2, 3) and argv[0] == "durable":
        print(json.dumps(durable(Path(argv[1]), Path(argv[2]) if len(argv) == 3 else None), indent=1))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
