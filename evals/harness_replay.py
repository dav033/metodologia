"""Deterministic before/after replay of the harness routing and grouping policy (no provider calls, no quota).

The "before" policy is reproduced from commit 98e375c (unbounded milestone grouping, tier = max of the unit, ladder with
xhigh at the top rungs, an Antagonist pass before every commit). The "after" policy runs the real code of this tree.

This is a SIMULATION, not a measurement. Both policies are costed with the SAME units: the model's catalog cost x the
current effort weight x one unit of work per task-session (a heuristic in relative units, never tokens or quota), and
both replay the same fixture, including deterministic first-attempt failures that are retried one tier up. Only the
shape of the policies differs. No provider is called. The output never contains a percentage of real quota saved: the
real figure needs measured tokens from the telemetry (bt_efficiency) of runs under each policy.

    python evals/harness_replay.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skill" / "scripts"))

import bt_agents  # noqa: E402
import bt_review_policy  # noqa: E402
import bt_routing_policy as policy  # noqa: E402
import bt_runstate as rs  # noqa: E402

OLD_LADDER = {"claude": (("haiku", None), ("sonnet", "xhigh"), ("opus", "xhigh")),
              "codex": (("gpt-6-luna", "medium"), ("gpt-6.1-sol", "high"), ("gpt-6.1-sol", "xhigh"))}
FAILS = {"T7": 1, "T11": 1, "T4": 1}  # task id -> first attempts that fail verification (same for both policies)

# (id, milestone, kind, level, complexity, risk, after)
PLAN = [
    ("T1", "M1", "implement", None, "S", None, []), ("T2", "M1", "docs", None, "S", None, []),
    ("T3", "M1", "test", None, "S", None, ["T1"]), ("T4", "M1", "implement", "architecture", "L", "high", []),
    ("T5", "M1", "implement", None, "M", None, ["T1"]),
    ("T6", "M2", "research", None, "S", None, []), ("T7", "M2", "implement", None, "S", None, ["T6"]),
    ("T8", "M2", "implement", None, "S", None, []), ("T9", "M2", "docs", None, "L", None, []),
    ("T10", "M2", "test", None, "S", None, ["T7"]), ("T11", "M2", "implement", None, "S", None, []),
    ("T12", "M3", "implement", None, "S", None, []), ("T13", "M3", "implement", None, "S", None, []),
    ("T14", "M3", "implement", None, "S", None, []), ("T15", "M3", "implement", None, "S", None, []),
]


def build(tier_fn):
    tasks = [{"id": i, "title": i, "repo": "r", "after": after, "verify": "true", "kind": kind, "level": level,
              "complexity": cx, "risk": risk, "milestone": m, "status": "todo", "attempts": 0, "error_hashes": [],
              "tier": tier_fn(level, kind, cx, risk)} for i, m, kind, level, cx, risk, after in PLAN]
    for m in ("M1", "M2", "M3"):
        members = [t["id"] for t in tasks if t["milestone"] == m]
        tasks.append({"id": f"{m}-audit", "title": "audit", "repo": None, "after": members, "verify": None,
                      "kind": "audit", "synthetic": True, "milestone": m, "status": "todo", "tier": 1, "risk": None,
                      "attempts": 0, "error_hashes": []})
    return {"tasks": tasks, "limits": dict(rs.DEFAULT_LIMITS)}


def old_unit_of(state, first):
    if not first.get("milestone") or first.get("kind") == "audit" or first.get("synthetic"):
        return [first]
    done = {t["id"] for t in state["tasks"] if t["status"] == "done"}
    unit, ids, grew = [first], {first["id"]}, True
    while grew:
        grew = False
        for t in state["tasks"]:
            if (t["id"] not in ids and t["status"] == "todo" and t.get("milestone") == first["milestone"]
                    and not t.get("synthetic") and all(a in done or a in ids for a in t["after"])):
                unit.append(t)
                ids.add(t["id"])
                grew = True
    order = {t["id"]: i for i, t in enumerate(state["tasks"])}
    return sorted(unit, key=lambda t: order[t["id"]])


def replay(state, unit_fn, ladder, antagonist_per_commit, floor_fn):
    sessions_log, fails = [], dict(FAILS)
    attempts = verified = failed = escalations = violations = 0
    while True:
        done = {t["id"] for t in state["tasks"] if t["status"] == "done"}
        first = next((t for t in state["tasks"] if t["status"] == "todo" and all(a in done for a in t["after"])), None)
        if first is None:
            break
        unit = unit_fn(state, first)
        tier = max(t["tier"] for t in unit)
        model, effort = ladder["claude"][tier] if first["kind"] != "audit" else bt_agents.AUDIT_LADDER["claude"][1]
        # one session is paid once whatever number of tasks it carries; the unit is the same for both policies
        cost = bt_agents.MODELS[model]["cost"] * policy.effort_weight(effort)
        failing = [t["id"] for t in unit if fails.get(t["id"], 0) > 0]
        sessions_log.append({"tasks": [t["id"] for t in unit], "tier": tier, "model": model, "effort": effort,
                             "overprovisioned": [t["id"] for t in unit if t["tier"] < tier], "failed": failing,
                             "relative_cost": round(cost * len(unit), 2)})
        for t in unit:
            attempts += 1
            violations += tier < floor_fn(t)  # ran below the floor the CURRENT policy declares for the task
            if t["id"] in failing:
                fails[t["id"]] -= 1
                t["tier"] = min(bt_agents.TOP, t["tier"] + 1)  # a failed task retries one tier up
                failed += 1
                escalations += t["tier"] > tier
            else:
                t["status"] = "done"
                verified += not t.get("synthetic")
    builders = [s for s in sessions_log if not any(i.endswith("-audit") for i in s["tasks"])]
    total = round(sum(s["relative_cost"] for s in sessions_log), 2)
    return {"sessions": len(sessions_log), "builder_sessions": len(builders),
            "audit_sessions": len(sessions_log) - len(builders),
            "task_attempts": attempts, "verified_builder_tasks": verified, "failed_attempts": failed,
            "escalations": escalations, "below_floor_attempts": violations,
            "xhigh_sessions": sum(s["effort"] == "xhigh" for s in sessions_log),
            "overprovisioned_tasks": sum(len(s["overprovisioned"]) for s in sessions_log),
            "antagonist_passes_per_commit": (len(PLAN) if antagonist_per_commit else
                                             sum(1 for _, _, _, lv, _, rk, _ in PLAN if rk == "high" or lv == "architecture")),
            "relative_cost_units": total,
            "relative_cost_units_per_verified_task": round(total / verified, 2) if verified else None,
            "log": sessions_log}


def main() -> int:
    old_tier = lambda level, kind, cx, risk: (2 if level == "architecture" else 1 if cx == "L" else 0)  # noqa: E731
    new_floor = lambda t: bt_agents.start_tier(t.get("level"), t.get("kind"), t.get("complexity"), t.get("risk"))  # noqa: E731
    before = replay(build(old_tier), old_unit_of, OLD_LADDER, True, new_floor)
    after = replay(build(bt_agents.start_tier), rs.unit_of, bt_agents.LADDER, False, new_floor)
    comparable = before["verified_builder_tasks"] == after["verified_builder_tasks"]
    json.dump({"fixture": f"{len(PLAN)} tasks, 3 milestones, audit per milestone, first-attempt failures {FAILS}",
               "kind": "simulation",
               "measured": None,
               "units": "relative cost units (model cost x effort weight x tasks per session): a heuristic, not tokens",
               "caveat": "both policies are costed with the same units on the same fixture; this is not measured quota, "
                         "tokens or a real saving, and it does not show that the changes caused any real improvement",
               "same_verified_work": comparable,
               "quality_guard": {"verified_tasks_before": before["verified_builder_tasks"],
                                 "verified_tasks_after": after["verified_builder_tasks"],
                                 "below_floor_before": before["below_floor_attempts"],
                                 "below_floor_after": after["below_floor_attempts"],
                                 "after_not_worse": comparable and after["below_floor_attempts"] <= before["below_floor_attempts"]},
               "before": before, "after": after}, sys.stdout, indent=1)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
