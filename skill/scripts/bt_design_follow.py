"""Follow planning changes and owner feedback to schedule design work."""
from __future__ import annotations

import time
from pathlib import Path

import bt_design_drafts as drafts


def sync(project: str, rdir: Path, *, now: float | None = None) -> list[str]:
    """Follow the conversation: draft new UI subplans, pending feedback, and subplans that changed and settled."""
    if not drafts.active(rdir) or not drafts.planning(rdir) or (Path(rdir) / ".planning" / "designers.paused").exists():
        return []                            # the owner (or the orchestrating session) paused automatic Designer runs
    now = time.time() if now is None else now
    try:
        settled = now - (Path(rdir) / "PLAN.json").stat().st_mtime >= drafts.DEBOUNCE_SEC
    except OSError:
        return []
    import bt_design_iterate as iterate
    import bt_planning_flow
    scope = bt_planning_flow.design_scope(rdir)  # collaborative flow: the focus and every subplan with tasks, in parallel
    due = []
    for r in drafts.rows(rdir):
        if r["status"] in (*drafts.ACTIVE, "approved"):
            continue
        new_feedback = any(not f.get("consumed") and (f.get("id") or f["when"]) not in r.get("feedback_batch", [])
                           for f in r.get("feedback", []))
        if (r["status"] == "choosing" and not r["stale"] and not new_feedback and
                r.get("continuation_choice") and r.get("comparison", {}).get("ok")):
            import bt_design_directions
            try:
                bt_design_directions.choose(project, rdir, r["ref"], r["continuation_choice"], "continued choice")
                return [r["ref"]]
            except SystemExit:
                continue  # comparison or source changed; retain the revision for explicit recovery
        if r["status"] == "choosing" and not new_feedback and not (r["stale"] and r.get("amend")):
            continue        # directions wait for the owner, even after a plan change: choosing folds it in (D-162);
                            # an iteration of a direction already chosen is extended with the delta, as before
        if scope is not None and r["ref"] not in scope and not r["pending_feedback"]:
            continue
        if r["status"] == "failed" and (drafts._age(r.get("finished")) < drafts.FAIL_BACKOFF_SEC or
                                        int(r.get("failures") or 0) >= drafts.MAX_FAILURES):
            continue  # do not relaunch a failing Designer on every page poll; after N failures only on drafts.request
        key = None if r["stale"] else iterate.route(r)
        if key:  # owner comments on one direction while another Designer was busy
            return [r["ref"]] if iterate.follow(project, rdir, r["ref"], key, "sync") else []
        changed = settled and (r["status"] == "none" or r["stale"]) and int(r.get("auto_runs") or 0) < drafts.MAX_AUTO_RUNS
        if r["pending_feedback"] or changed:
            due.append(r["ref"])
    return drafts.request(project, rdir, due, reason="plan changed") if due else []

