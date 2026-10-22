"""Self-evolution of the Scheduler: learn from the interventions, propose with evidence, apply only what is proven (REQ-030 step 6).

Every manual or automatic intervention on a run is a row of `RUN.interventions.jsonl` (`bt_interventions`: class, evidence,
repair, result, minutes lost). `analyse()` is a DETERMINISTIC pass over those rows (no model) that aggregates them by class,
by signature and by task, and applies a small set of rules to turn what keeps happening into proposals:

- each proposal names its evidence (how many rows, which runs, how many minutes), its risk and the change it asks for;
- a LOW-risk proposal is a change of one setting inside a bounded allowlist (`LOW_RISK`), and is applied only after an A/B on
  the replicas of earlier nights (`bt_scheduler_replica`): the candidate must make at least one replica clearly faster and
  none slower, with the same work done. Applied changes are written to `.state/evolution.json` with the previous value, so
  `revert()` puts every one back;
- everything else (a planner contract, a verifier rule, a plan structure) is HIGH risk: it becomes a numbered Proposal in the
  project's PENDING.md for the owner, never a silent change.

Nothing here calls a provider, edits code or touches a run; the only writes are the evolution state file, the setting an A/B
proved, and PENDING.md lines.
"""
from __future__ import annotations

import collections
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import bt_interventions

# setting -> (smallest, largest) value the evolution may set on its own: bounded so a bad A/B cannot run away
LOW_RISK: dict[str, tuple[int, int]] = {"scheduler.max_parallel_tasks": (1, 5)}
MIN_ROWS = 2                 # a pattern needs at least this many rows to be proposed
MIN_GAIN = 0.05             # an A/B must save at least this fraction of the wall time on some replica
STATE_FILE = "evolution.json"


# ------------------------------------------------------------------------------------------------ collection
def collect(project_dir: Path | str) -> list[dict[str, Any]]:
    """Every intervention row of every run of a project, each tagged with its requirement."""
    rows: list[dict[str, Any]] = []
    for run_dir in sorted((Path(project_dir) / "requirements").glob("REQ-*")):
        for row in bt_interventions.read(run_dir):
            rows.append({**row, "req": run_dir.name.split("-", 2)[0] + "-" + run_dir.name.split("-", 2)[1]})
    return rows


def summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_class: dict[str, dict[str, Any]] = {}
    for row in rows:
        entry = by_class.setdefault(row["class"], {"rows": 0, "manual": 0, "minutes": 0.0, "failed": 0, "tasks": set()})
        entry["rows"] += 1
        entry["manual"] += row.get("source") == "manual"
        entry["failed"] += row.get("result") == "failed"
        entry["minutes"] += float(row.get("minutes_lost") or 0)
        entry["tasks"].add(row.get("task", ""))
    return {name: {**{k: v for k, v in entry.items() if k != "tasks"}, "minutes": round(entry["minutes"], 1),
                   "tasks": sorted(t for t in entry["tasks"] if t)} for name, entry in sorted(by_class.items())}


# ------------------------------------------------------------------------------------------------ rules
def analyse(rows: list[dict[str, Any]], *, plans: list[dict[str, Any]] | None = None,
            current: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Proposals (deterministic order) from the intervention rows and, when given, the plan graphs of the runs
    (`plans`: replica fixtures) and the settings in force (`current`: dotted key -> value)."""
    current = current or {}
    stats = summary(rows)
    proposals: list[dict[str, Any]] = []

    def propose(key: str, risk: str, title: str, change: dict[str, Any] | None, evidence: str, minutes: float = 0.0) -> None:
        proposals.append({"key": key, "risk": risk, "title": title, "change": change, "evidence": evidence,
                          "minutes": round(minutes, 1)})

    def seen(name: str) -> dict[str, Any]:
        return stats.get(name, {"rows": 0, "manual": 0, "minutes": 0.0, "failed": 0, "tasks": []})

    manual = [r for r in rows if r.get("source") == "manual"]
    unmapped = seen("criterion_unmapped")
    if unmapped["rows"] >= MIN_ROWS:
        propose("planner-purposes", "high", "The planner must write each check's purpose with the exact text of its criterion",
                None, f"{unmapped['rows']} stops over criteria the verifier could not map to a check ({unmapped['manual']} by hand, "
                      f"{unmapped['minutes']} minutes waiting); tasks {', '.join(unmapped['tasks'][:6])}", unmapped["minutes"])
    regression = seen("regression")
    if regression["rows"] >= MIN_ROWS:
        propose("guard-tests", "high", "Tasks that rework shared code must run the guard tests of the modules they touch",
                None, f"{regression['rows']} regressions in tests owned by other tasks ({regression['minutes']} minutes); "
                      f"tasks {', '.join(regression['tasks'][:6])}", regression["minutes"])
    plan_defect = seen("plan_defect")
    if plan_defect["rows"] >= MIN_ROWS:
        propose("plan-check-lint", "high", "plan-json check must reject a check the verifier cannot run and an execute-only task "
                "over code no task repairs", None, f"{plan_defect['rows']} stops over plan defects "
                f"({plan_defect['minutes']} minutes)", plan_defect["minutes"])
    environment = collections.Counter(r.get("evidence", "")[:90] for r in rows if r["class"] == "environment")
    for text, count in environment.most_common(3):
        if count >= MIN_ROWS:
            propose("env-" + hashlib.sha256(text.encode()).hexdigest()[:8], "high", "The same environment fault stopped the run again and again", None,
                    f"{count} times: {text}", seen("environment")["minutes"])
    if seen("transient")["rows"] >= 4:
        propose("transient-churn", "high", "Transient start failures keep costing attempts: look at the routes and the verifier host",
                None, f"{seen('transient')['rows']} transient stops ({seen('transient')['minutes']} minutes)", seen("transient")["minutes"])
    if len(manual) >= 5 and sum(1 for r in manual if r["class"] == "unknown") >= len(manual) // 2:
        propose("unplaced-stops", "high", "Most manual interventions are stops the taxonomy cannot place: classify them",
                None, f"{sum(1 for r in manual if r['class'] == 'unknown')} of {len(manual)} manual interventions have class unknown")
    for plan in plans or ():
        tasks = plan.get("plan", {}).get("tasks", [])
        counts = collections.Counter(res for t in tasks for res in set(t.get("shared_resources") or ()))
        for resource, count in counts.most_common(1):
            if tasks and count / len(tasks) >= 0.6 and count >= 4:
                propose(f"shared-resource-{resource}", "high",
                        f"{plan.get('name', 'a plan')} serialises itself: `{resource}` is claimed by {count} of {len(tasks)} tasks", None,
                        "a shared resource is always exclusive, so tasks that claim it never run side by side")
    scopes = current.get("scheduler.exclusive_scopes")
    if scopes:
        propose("exclusive-scopes", "low", "scheduler.exclusive_scopes serialises large tasks that declare disjoint paths",
                {"key": "scheduler.exclusive_scopes", "value": []}, f"set to {scopes}")
    return proposals


# ------------------------------------------------------------------------------------------------ A/B on the replicas
def ab_parallel(replicas: list[dict[str, Any]], key: str, candidate: int, baseline: int) -> dict[str, Any]:
    """Replay every replica with `baseline` and with `candidate` slots: the verdict is `apply` only when no replica gets slower
    and at least one saves `MIN_GAIN` of its wall time, with the same number of attempts."""
    import bt_scheduler_replica as replica

    rows, better, worse = [], False, False
    for fixture in replicas:
        before = replica.replay(fixture, max_parallel_tasks=baseline)
        after = replica.replay(fixture, max_parallel_tasks=candidate)
        gain = (before["wall_minutes"] - after["wall_minutes"]) / before["wall_minutes"] if before["wall_minutes"] else 0.0
        rows.append({"replica": fixture.get("name"), "before": before["wall_minutes"], "after": after["wall_minutes"],
                     "gain": round(gain, 3), "attempts_equal": before["attempts"] == after["attempts"]})
        better = better or gain >= MIN_GAIN
        worse = worse or after["wall_minutes"] > before["wall_minutes"] or before["attempts"] != after["attempts"]
    return {"key": key, "baseline": baseline, "candidate": candidate, "replicas": rows, "apply": better and not worse,
            "reason": "no replica saves enough time" if not better else ("a replica got worse" if worse else "faster, same work")}


def propose_settings(replicas: list[dict[str, Any]], current: dict[str, Any]) -> list[dict[str, Any]]:
    """The A/B of every low-risk setting that has a model on the replicas (today: the number of parallel slots)."""
    out = []
    slots = current.get("scheduler.max_parallel_tasks", 3)
    low, high = LOW_RISK["scheduler.max_parallel_tasks"]
    if isinstance(slots, int) and slots < high and replicas:
        out.append(ab_parallel(replicas, "scheduler.max_parallel_tasks", slots + 1, slots))
    return out


def apply_proven(results: list[dict[str, Any]], state_dir: Path | str, setter, *, now=time.time) -> list[str]:
    """Write the settings whose A/B said `apply` (inside the allowlist and its bounds) and remember what they replaced."""
    path = Path(state_dir) / STATE_FILE
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    state.setdefault("applied", [])
    lines = []
    for result in results:
        key, value = result["key"], result["candidate"]
        bounds = LOW_RISK.get(key)
        if not result.get("apply") or bounds is None or not isinstance(value, int) or not bounds[0] <= value <= bounds[1]:
            continue
        state["applied"].append({"key": key, "was": result["baseline"], "now": value, "at": round(now(), 1),
                                 "evidence": result["replicas"]})
        setter(key, value)
        lines.append(f"{key}: {result['baseline']} -> {value} (A/B on {len(result['replicas'])} replicas)")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return lines


def revert(state_dir: Path | str, setter) -> list[str]:
    """Put back every setting the evolution changed, newest first."""
    path = Path(state_dir) / STATE_FILE
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    lines = []
    for item in reversed(state.get("applied", [])):
        setter(item["key"], item["was"])
        lines.append(f"{item['key']}: back to {item['was']}")
    state["applied"] = []
    path.write_text(json.dumps(state, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return lines


# ------------------------------------------------------------------------------------------------ proposals in the bitácora
def file_proposals(project_dir: Path | str, proposals: list[dict[str, Any]], *, today: str | None = None) -> list[str]:
    """Write each HIGH-risk proposal as a numbered `P-NNN` line of PENDING.md (once: the proposal key is part of the line, so
    a second analysis does not file it again). Returns the ids it wrote."""
    import bt_core
    import bt_pending

    pdir = Path(project_dir)
    path = pdir / "PENDING.md"
    text = path.read_text(encoding="utf-8") if path.exists() else bt_pending.HEADER.format(project=pdir.name) + "\n## Open\n"
    stamp = today or time.strftime("%Y-%m-%d")
    written = []
    for item in proposals:
        if item["risk"] != "high" or f"[evolution:{item['key']}]" in text:
            continue
        new_id = bt_core.next_id(pdir, "P")
        line = (f"- {new_id} · {item['title']} [evolution:{item['key']}] · urgency: med · complexity: M · added {stamp} · REQ-030 "
                f"evolution analysis\n  Evidence: {item['evidence']}\n")
        if "## Open" in text:
            head, tail = text.split("## Open", 1)
            first, _, rest = tail.partition("\n")
            text = f"{head}## Open{first}\n{line}{rest}"
        else:
            text = text.rstrip("\n") + "\n\n## Open\n" + line
        path.write_text(text, encoding="utf-8")
        written.append(new_id)
    if written:
        bt_pending.sort_file(pdir)
    return written
