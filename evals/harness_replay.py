"""Deterministic before/after replay of the harness routing and grouping policy (no provider calls, no quota).

The "before" policy is reproduced from commit 98e375c (unbounded milestone grouping, tier = max of the unit, ladder with
xhigh at the top rungs, an Antagonist pass before every commit). The "after" policy runs the real code of this tree.
Consumption figures are RELATIVE ESTIMATES (model cost x effort weight per task-session), not measured quota.

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
OLD_WEIGHT = {None: 1.0, "low": 1.0, "medium": 1.0, "high": 1.0, "xhigh": 1.0}  # the old estimate ignored effort

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


def replay(state, unit_fn, ladder, effort_weight, antagonist_per_commit):
    sessions, sessions_log = 0, []
    while True:
        done = {t["id"] for t in state["tasks"] if t["status"] == "done"}
        first = next((t for t in state["tasks"] if t["status"] == "todo" and all(a in done for a in t["after"])), None)
        if first is None:
            break
        unit = unit_fn(state, first)
        tier = max(t["tier"] for t in unit)
        model, effort = ladder["claude"][tier] if first["kind"] != "audit" else bt_agents.AUDIT_LADDER["claude"][1]
        cost = bt_agents.MODELS[model]["cost"] * effort_weight.get(effort, 1.0)
        common = bt_agents.MODELS[model]["cost"] * policy.effort_weight(effort)
        sessions += 1
        sessions_log.append({"tasks": [t["id"] for t in unit], "tier": tier, "model": model, "effort": effort,
                             "overprovisioned": [t["id"] for t in unit if t["tier"] < tier],
                             "relative_cost": round(cost * len(unit), 2),
                             "relative_cost_common_weights": round(common * len(unit), 2)})
        for t in unit:
            t["status"] = "done"
    builders = [s for s in sessions_log if not any(i.endswith("-audit") for i in s["tasks"])]
    return {"sessions": sessions, "builder_sessions": len(builders),
            "audit_sessions": sessions - len(builders),
            "xhigh_sessions": sum(s["effort"] == "xhigh" for s in sessions_log),
            "overprovisioned_tasks": sum(len(s["overprovisioned"]) for s in sessions_log),
            "antagonist_passes_per_commit": (len(PLAN) if antagonist_per_commit else
                                             sum(1 for _, _, _, lv, _, rk, _ in PLAN if rk == "high" or lv == "architecture")),
            "relative_cost_estimate": round(sum(s["relative_cost"] for s in sessions_log), 2),
            "relative_cost_estimate_common_weights": round(sum(s["relative_cost_common_weights"] for s in sessions_log), 2),
            "log": sessions_log}


def main() -> int:
    old_tier = lambda level, kind, cx, risk: (2 if level == "architecture" else 1 if cx == "L" else 0)  # noqa: E731
    before = replay(build(old_tier), old_unit_of, OLD_LADDER, OLD_WEIGHT, True)
    after = replay(build(bt_agents.start_tier), rs.unit_of, bt_agents.LADDER,
                   {e: policy.effort_weight(e) for e in (None, "low", "medium", "high", "xhigh")}, False)
    json.dump({"fixture": f"{len(PLAN)} tasks, 3 milestones, audit per milestone",
               "caveat": "relative estimates from model cost x effort weight; not measured quota or tokens",
               "before": before, "after": after}, sys.stdout, indent=1)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
