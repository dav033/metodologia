"""Which stage carries an owner's subplan (re)confirmation, and what that confirms when the stage joins the durable run.

One set of facts for the panel and the join, read-only:

- `holding_stage`: the first stage frozen at or after a confirmation that holds the subplan and did not keep it as the
  revision before (D-259). The D-268/D-272 read model says «por unir a la ejecución» until the run holds it.
- `owner_reconfirmations`: the subplans the OWNER confirmed after the running stage whose holding stage is in the join.
  D-275, the owner's choice «Reconfirmar = confirmar» (pictures REQ-021, 2026-10-31: SP-14 reconfirmed at 19:55 while
  stage r34 changed its accepted T14.2–T14.5): reconfirming a subplan also confirms redoing its changed accepted tasks.
  A confirmation `by: policy` (D-241) is not the owner's.
- `join_confirmation`: the latest stage waits for the owner to confirm the redone tasks nothing covered (the last join was
  refused JOIN_NEEDS_CONFIRM while the run is behind): the Plan tab shows them with «Confirmar y unir».
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import bt_planning_flow


def stamp(value: object) -> float | None:
    """An ISO time as epoch seconds (a naive one is local, like `frozen_at`); None when it is not one."""
    try:
        moment = dt.datetime.fromisoformat(str(value or ""))
    except ValueError:
        return None
    return (moment if moment.tzinfo else moment.astimezone()).timestamp()


def holding_stage(stages: list[dict], sid: str, confirmed: float | None) -> int | None:
    """The revision of the first stage (`bt_plan_adapter.stage_summary` rows) frozen at or after `confirmed` that holds
    `sid` and did not keep it as the revision before (D-259): the stage that carries that confirmation; None when none."""
    if confirmed is None:
        return None
    return next((s["revision"] for s in stages if sid in s.get("subplans", ()) and sid not in s.get("kept", ())
                 and (when := stamp(s.get("frozen_at"))) is not None and when >= confirmed), None)


def owner_reconfirmations(rdir: Path, subplans, *, after: int, upto: int) -> dict[str, dict]:
    """Subplan -> {"at", "via", "stage"} for each of `subplans` the OWNER confirmed after revision `after` was frozen
    (a confirmation `by: policy`, D-241, is not the owner's) whose holding stage is in (`after`, `upto`]. D-275: the
    owner's choice «Reconfirmar = confirmar» — reconfirming a subplan also confirms redoing its changed accepted tasks
    when that stage joins the durable run. Read-only; unreadable stores give {}."""
    import bt_plan_adapter
    try:
        frozen = {e["revision"]: e for e in bt_plan_adapter.planner_revisions.list_revisions(rdir)}
        stages = bt_plan_adapter.stage_summary(rdir).get("stages") or []
    except Exception:  # noqa: BLE001 - nothing readable confirms nothing
        return {}
    since = stamp((frozen.get(after) or {}).get("frozen_at"))
    if since is None:
        return {}
    records = bt_planning_flow._load(rdir)["subplans"]
    out = {}
    for sid in sorted(set(subplans)):
        record = records.get(sid) or {}
        at = stamp(record.get("at"))
        if record.get("by") != "owner" or at is None or at <= since:
            continue
        holder = holding_stage(stages, sid, at)
        if holder is not None and after < holder <= upto:
            out[sid] = {"at": str(record["at"]), "via": str(record.get("via") or ""), "stage": holder}
    return out


def join_confirmation(rdir: Path) -> dict | None:
    """The latest stage waits for the owner to confirm redoing accepted tasks at the durable join (D-275): the run the
    durable runtime owns is behind that stage and its last join was refused with JOIN_NEEDS_CONFIRM. Returns {"revision",
    "running", "tasks": [{"id", "title", "subplan"}], "message", "at"}, else None. Read-only."""
    import bt_stages
    if not bt_stages.durable_owner(rdir):
        return None
    try:
        running = json.loads((Path(rdir) / "RUN.durable-run.json").read_text(encoding="utf-8")).get("revision")
        refused = json.loads((Path(rdir) / "RUN.join.refused.json").read_text(encoding="utf-8"))
        import bt_plan_adapter
        found = bt_plan_adapter.planner.stages.latest(rdir)
    except Exception:  # noqa: BLE001 - nothing to confirm when any of it is unreadable
        return None
    if not found or not isinstance(running, int) or not isinstance(refused, dict):
        return None
    revision = found[0]["revision"]
    if refused.get("code") != "JOIN_NEEDS_CONFIRM" or refused.get("revision") != revision or running >= revision:
        return None
    tasks = {t.get("id"): t for t in found[1].get("tasks", ())}
    ids = [t for t in refused.get("tasks") or () if isinstance(t, str)]
    return {"revision": revision, "running": running, "message": str(refused.get("message") or ""),
            "at": str(refused.get("at") or ""),
            "tasks": [{"id": t, "title": str((tasks.get(t) or {}).get("title") or ""),
                       "subplan": str((tasks.get(t) or {}).get("subplan_id") or "")} for t in ids]}
