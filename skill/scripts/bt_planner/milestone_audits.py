"""Advisory product-feedback gates between implementation milestones."""
from __future__ import annotations


def advice(plan: dict, ancestors: dict[str, set[str]]) -> list[str]:
    if not isinstance(plan.get("tasks"), list) or not isinstance(plan.get("milestones"), list):
        return []
    tasks = {t["id"]: t for t in plan.get("tasks", []) if isinstance(t, dict) and isinstance(t.get("id"), str)}
    milestones = [m["id"] for m in plan.get("milestones", []) if isinstance(m, dict) and isinstance(m.get("id"), str)]
    implementation = {mid: {tid for tid, task in tasks.items()
                            if task.get("kind") == "implement" and task.get("milestone_id") == mid}
                      for mid in milestones}
    active = [mid for mid in milestones if implementation[mid]]
    audits = {tid for tid, task in tasks.items() if task.get("kind") == "audit"}
    warnings = []
    for index, mid in enumerate(active[:-1]):
        later = set().union(*(implementation[m] for m in active[index + 1:]))
        covered = {audit for audit in audits if implementation[mid] <= ancestors.get(audit, set())}
        if covered and all(covered & ancestors.get(tid, set()) for tid in later):
            continue
        warnings.append(f"{mid}: add a milestone product audit with real entry-point probes and its own findings ledger, "
                        "and make later implementation wait for it; final-only feedback can force broad rework after the time window")
    return warnings
