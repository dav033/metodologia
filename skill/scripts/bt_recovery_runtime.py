"""Production sources for the diagnostic recovery cycle (REQ-029 G3): what the owner loop tells `tick_diagnostic_recovery`.

The cycle opens only when the ordinary paths are exhausted. This module reads that from the run's own records: an audit or task that
ended in `rework_limit` / `rework_impact`, a self-healing case that gave up (`exhausted`), or an open remediation request. It does
NOT invent evidence or a model route: `planner_route` is None and `evidence_available` False until a verified Planner-role route and
the stop the cycle is about exist (`bt_recovery_diagnosis`), so the cycle ends in an exact durable blocker (`authorized_planner_route_unavailable`,
`recovery_evidence_unavailable`) that the plan page shows, instead of staying silent.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

EXHAUSTED_REASONS = ("rework_limit", "rework_impact")


def sources(rdir: Path | str, run_id: str) -> dict[str, Any]:
    rdir = Path(rdir)
    import bt_remediation
    import bt_scheduler_decisions as decisions
    import bt_scheduler_healing as healing

    out: dict[str, Any] = {"run_id": run_id, "conflict_observations": [], "observations": [], "planner_route": None,
                           "evidence_available": False, "owner_only_decision_pending": False,
                           "ordinary_remediation_pending": bool(bt_remediation.requested(rdir))}
    lineage = []
    try:
        for request in decisions.open_requests(rdir):
            code = decisions.reason_code(str(request.get("reason") or ""))
            if code in EXHAUSTED_REASONS:
                lineage.append(f"{request.get('task')}:{code}")
    except Exception:  # noqa: BLE001 - unreadable state: nothing is exhausted that we can prove
        pass
    try:
        for case in healing.load(rdir)["cases"].values():
            if case.get("status") == "exhausted":
                lineage.append(f"{case.get('task')}:{case.get('class')}:{case.get('id')}")
    except Exception:  # noqa: BLE001
        pass
    out["ordinary_exhausted"] = bool(lineage)
    try:
        import bt_recovery_diagnosis as diagnosis

        goal = diagnosis.target(rdir, decisions.open_requests(rdir))
        project = rdir.parent.parent.name
        route = diagnosis.route(project) if goal else None
    except Exception:  # noqa: BLE001 - no target or no route: the cycle ends in its exact blocker
        goal, route = None, None
    if goal:                                    # the exhausted audit stop the structural cycle is about (REQ-029 P-152)
        out["diagnosis_target"], out["evidence_available"] = goal, True
        out["planner_route"] = route
    if lineage:
        out["audit_lineage"] = "|".join(sorted(set(lineage)))
        out["source_digests"] = [hashlib.sha256(json.dumps(sorted(set(lineage))).encode()).hexdigest()]
    return out
