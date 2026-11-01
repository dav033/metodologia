"""Confirmed content (D-276): a subplan whose draft returns to content already confirmed in that exact form is confirmed.

A confirmation (`bt_planning_flow`) is a digest of the subplan, its tasks, inputs, `## Pruebas` rows and design. Until
D-276 flow.json kept only the latest one, so undoing a change brought nothing back (pictures REQ-021 2026-10-31: the
owner withdrew the Solucionador's redundant T3.121, SP-3 became byte-identical to its r31/r32 content, confirmed by
D-241 at 16:02, and the stage freeze still asked the owner to reconfirm what they never changed).

Every subplan record now keeps `history`: each earlier confirmation (owner, D-241 policy, a mechanical re-pin) with its
digest, and the owner's rejections (`planning reject`). `restore` re-confirms `by: policy` (rule D-276) a subplan whose
current digest equals the digest of an earlier confirmation still valid (no later owner rejection of that digest), with
the reason «vuelve al contenido confirmado el <fecha> por <quién>». Any other content still waits for the owner: the
digest covers everything the owner confirmed, so content the owner never saw in that form never matches.

Records written before D-276 have no history. A D-241 record still proves its predecessor: `bt_stages.repair_reconfirm`
re-confirmed only when the confirmation it replaced was exactly the subplan as the stage frozen before it holds it.
`_legacy` derives that digest with today's inputs, tests and design, and only after checking that a frozen stage still
reproduces the D-241 record's own digest with them (so they have not changed since that record).
"""
from __future__ import annotations

import bt_design_drafts as drafts
import bt_planning_activity as activity
import bt_planning_flow as flow

RULE = "D-276"
LEGACY_RULE = "D-241"
_ENTRY = ("at", "by", "via", "digest", "policy", "repinned", "derived")
_HISTORY_CAP = 60


def entry(record: dict | None) -> dict:
    """The confirmation a record holds, without its history ({} when it holds none)."""
    if not isinstance(record, dict) or not record.get("digest"):
        return {}
    return {key: record[key] for key in _ENTRY if key in record}


def pushed(record: dict | None, new: dict) -> dict:
    """`new` as the subplan's current record; the confirmation `record` held and its history move to `history`."""
    history = [h for h in (record or {}).get("history") or [] if isinstance(h, dict)]
    if (held := entry(record)):
        history.append(held)
    return {**{k: v for k, v in new.items() if k != "history"}, "history": history[-_HISTORY_CAP:]}


def valid(record: dict | None, extra: list[dict] = ()) -> dict[str, dict]:
    """Digest -> the latest confirmation of that content still valid: earlier ones (`extra` first, then `history`, then
    the current record, in the order they were written) minus those an owner rejection named later."""
    out: dict[str, dict] = {}
    for item in [*extra, *((record or {}).get("history") or []), entry(record)]:
        if not isinstance(item, dict):
            continue
        if item.get("rejected"):
            out.pop(str(item["rejected"]), None)
        elif item.get("digest"):
            out[str(item["digest"])] = item
    return out


def who(item: dict) -> str:
    if item.get("by") == "owner":
        return "el propietario"
    rule = (item.get("policy") or {}).get("rule") if isinstance(item.get("policy"), dict) else None
    return f"la política {rule}" if rule else "la política" if item.get("by") == "policy" else str(item.get("by") or "?")


def reason(item: dict) -> str:
    when = str(item.get("at") or "?")[:16].replace("T", " ")
    return f"vuelve al contenido confirmado el {when} por {who(item)}"


def _legacy(rdir, sid: str, record: dict, rows: list[dict], current: str) -> dict | None:
    """The confirmation a pre-D-276 D-241 record replaced when it is `current` (see the module docstring), or None when
    it is other content or cannot be proven."""
    policy = record.get("policy") if isinstance(record.get("policy"), dict) else {}
    previous = policy.get("previous") if isinstance(policy.get("previous"), dict) else {}
    if (record.get("history") or record.get("by") != "policy" or policy.get("rule") != LEGACY_RULE
            or not previous or previous.get("digest")):
        return None
    import bt_plan_adapter
    import bt_stage_confirmations as sc
    store, stages = bt_plan_adapter.planner_revisions, bt_plan_adapter.planner.stages

    def digest(revision: int) -> str | None:
        doc = store.load_revision(rdir, revision)
        return flow._digest(rdir, doc, flow._row(doc, sid), rows) if sid in stages.subplans_in(doc) else None
    try:
        at = sc.stamp(record.get("at"))
        revisions = store.list_revisions(rdir)
        when = [sc.stamp(e.get("frozen_at")) for e in revisions]
        # the stage the D-241 freeze made right after its record: it reproduces the record's digest with today's
        # inputs, tests and design (so they have not changed since); the stage before it is what the record replaced
        repaired = next((i for i, w in enumerate(when) if at is not None and w is not None and w >= at
                         and digest(revisions[i]["revision"]) == record.get("digest")), None)
        if not repaired or when[repaired - 1] is None or when[repaired - 1] > at:
            return None
        replaced = revisions[repaired - 1]["revision"]
        if digest(replaced) != current:
            return None
    except Exception:  # noqa: BLE001 - an unreadable store proves nothing
        return None
    rule = {"policy": {"rule": LEGACY_RULE}} if previous.get("by") == "policy" else {}   # the only policy before D-276
    return {**{k: previous[k] for k in ("at", "by", "via") if previous.get(k)}, **rule, "digest": current,
            "derived": f"{LEGACY_RULE} record of {record.get('at')}: the confirmation it replaced was r{replaced}"}


def restorable(rdir) -> dict[str, tuple[dict, dict | None]]:
    """Subplan -> (the earlier confirmation its current content equals, the legacy entry derived for it or None), for
    every subplan whose stored confirmation is not its current content. Read-only."""
    if not flow.active(rdir):
        return {}
    data, plan = flow._load(rdir), drafts._plan(rdir)
    if not data.get("outline") or not plan:
        return {}
    rows, out = flow.inputs(rdir), {}
    for sp in flow._plan_order(rdir):
        record = data["subplans"].get(sp["id"])
        if not isinstance(record, dict):
            continue
        current = flow._digest(rdir, plan, sp, rows)
        if record.get("digest") == current:
            continue
        derived = _legacy(rdir, sp["id"], record, rows, current)
        found = valid(record, [derived] if derived else []).get(current)
        if found and not flow.problems(rdir, sp, None, rows):
            out[sp["id"]] = (found, derived if found is derived else None)
    return out


def restore(rdir) -> list[str]:
    """Re-confirm `by: policy` (D-276) every subplan whose current content was already confirmed in that exact form;
    the record, the activity log and a planning note say which confirmation it returns to. Returns the subplans."""
    try:
        found = restorable(rdir)
    except Exception:  # noqa: BLE001 - a plan caught mid-edit restores nothing; the owner path stays as it was
        return []
    if not found:
        return []
    plan, rows = drafts._plan(rdir), flow.inputs(rdir)
    by_id = {sp["id"]: sp for sp in flow._plan_order(rdir)}
    done = []
    with flow._locked(rdir) as data:
        for sid, (item, derived) in found.items():
            record = data["subplans"].get(sid)
            if not isinstance(record, dict) or sid not in by_id:
                continue
            current = flow._digest(rdir, plan, by_id[sid], rows)
            if current != item.get("digest") or record.get("digest") == current:
                continue            # moved again, or already restored by someone else
            base = {**record, "history": [derived, *(record.get("history") or [])]} if derived else record
            previous = {k: record.get(k) for k in ("at", "by", "via", "digest") if record.get(k)}
            data["subplans"][sid] = pushed(base, {
                "at": flow._now(), "by": "policy", "via": "policy", "digest": current,
                "policy": {"rule": RULE, "requested_by": "policy", "reason": reason(item), "previous": previous,
                           "restores": {k: item[k] for k in ("at", "by", "via", "digest", "derived", "policy")
                                        if item.get(k)}}})
            done.append((sid, item))
    for sid, item in done:
        text = (f"{sid} sigue confirmado por la regla {RULE}: {reason(item)}; lo que cambió después se deshizo y su "
                "contenido (tareas, entradas, pruebas y diseño) es exactamente el que se confirmó")
        activity.record(rdir, "Política", text, kind="flow", sp=sid)
        try:
            import bt_planning_notes as notes
            notes.add(rdir, text, kind="decision", by="policy")
        except SystemExit:
            pass
    return [sid for sid, _ in done]


def reject(rdir, sid: str, *, by: str = "owner", via: str = "conversation", why: str = "") -> str:
    """The owner rejects the content `sid` is confirmed with now (for instance a D-241 repair they withdraw): that
    digest is never restored again unless the owner confirms it anew, and the subplan waits for their confirmation."""
    if not flow.active(rdir):
        return "Este requerimiento no está en la planificación conjunta (bitacora.py planning start)."
    with flow._locked(rdir) as data:
        record = data["subplans"].get(sid)
        if not entry(record):
            return f"{sid} no tiene una confirmación que rechazar."
        rejected = {"at": flow._now(), "by": by, "via": via, "rejected": record["digest"], "reason": why}
        new = pushed(record, {})
        new["history"] = [*new["history"], rejected][-_HISTORY_CAP:]
        new["rejected"] = rejected
        data["subplans"][sid] = new
    activity.record(rdir, "Tú" if by == "owner" else by, f"Rechazaste el contenido confirmado de {sid}"
                    + (f": {why}" if why else ""), kind="flow", sp=sid)
    return (f"{sid}: rechazado el contenido con que estaba confirmado; no vuelve a contar como confirmado y el subplan "
            "espera tu confirmación.")
