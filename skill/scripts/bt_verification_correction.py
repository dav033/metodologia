"""Where the correction of a rejected subplan version is: the one read model every panel view shows (D-268).

Owner, 2026-10-31, about pictures REQ-021 SP-14 (version 2 rejected in «Probar» at 15:30, its design being redone since):
«en el panel debe aparecer como rechazada en espera de iteración o algo así». The Plan tab only showed the design state
(«diseñando…»), so nothing said the subplan was a rejected version waiting for its correction.

`correction(rdir, sid)` answers, for a subplan whose latest owner decision is `rejected` for the published version N, the
phase of its correction in the order of the real pipeline, from data that already exists (no new state file):

- redesign (the subplan's UI contract is not approved, or was approved after the rejection):
  rediseñando → elige una dirección → aprueba el contrato → reconfirma el subplan → por unir a la ejecución →
  construyendo vN+1;
- repair (anything else: bounded repair tasks, the Solucionador; pictures REQ-021 SP-3): reparando.

Both end at «vN+1 lista para probar»: once the engine publishes a version above N this returns None, so the views show
«por probar» with the owner's note, as before. A version re-published at or below N does not end it: after the rejection
pictures REQ-021's new run revision re-published SP-14 v2 / SP-2 v1 / SP-3 v2 (`outdated`, `retest`) while the
decisions rejected v2 / v2 / v3 — the panel showed nothing until `in_correction` stopped requiring `state == rejected`.
«construyendo vN+1» holds only while the run the durable runtime owns runs the stage that holds the reconfirmed subplan
(its revision ≥ that stage's). Before that the phase is «por unir a la ejecución»: the change is not frozen yet (the owner
presses «Ejecutar cambios», D-259), or its stage is frozen and the join waits for live attempts or was refused (the
reason from `RUN.join.json` / `RUN.join.refused.json` goes in the detail). pictures REQ-021 2026-10-31: SP-14 confirmed
at 19:55:55, stage r34 frozen at 19:56:01, the join refused (JOIN_MATERIAL_MISSING) and the run still in r32, while the
panel said «Rechazada v2 · construyendo v3» — «sp14 no me sale en ningún lado para aprobar» (D-272). Without a durable
run, or without a known confirmation time, the phase stays «construyendo» as before.
Read-only: no lock is taken and nothing is settled or written.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import bt_design_drafts as drafts

REDESIGN = (("redesigning", "rediseñando"), ("choosing", "elige una dirección"), ("approve_contract", "aprueba el contrato"),
            ("reconfirm", "reconfirma el subplan"), ("joining", "por unir a la ejecución"),
            ("building", "construyendo v{next}"),
            ("ready", "v{next} lista para probar"))
REPAIR = (("repairing", "reparando"), ("ready", "v{next} lista para probar"))


def in_correction(row: dict | None) -> bool:
    """`row` (of `bt_verification.state`) waits for the correction of the owner's rejection: its latest decision rejects
    version N and no published version above N exists. A re-published older or equal version (`outdated` + `retest`)
    or no published version at all keeps it waiting."""
    dec = (row or {}).get("decision") or {}
    if dec.get("decision") != "rejected":
        return False
    if row.get("state") == "rejected":
        return True
    rejected, current = dec.get("version"), row.get("version")
    newer = isinstance(rejected, int) and isinstance(current, int) and current > rejected
    return not newer


def _when(stamp: object) -> float | None:
    try:
        moment = dt.datetime.fromisoformat(str(stamp or ""))
    except ValueError:
        return None
    return (moment if moment.tzinfo else moment.astimezone()).timestamp()


def _after(stamp: object, since: float | None) -> bool:
    moment = _when(stamp)
    return moment is not None and since is not None and moment >= since


def _design(rdir: Path, sid: str) -> tuple[str | None, dict | None]:
    """(UI contract ref, its draft row) of `sid` read without the drafts lock; the row is {"status": "none"} when the
    Designer has no entry for the ref yet."""
    sub = next((s for s in drafts.subplans(rdir) if s["id"] == sid), None)
    if not sub or not sub["ref"]:
        return None, None
    entry = drafts._load(rdir)["drafts"].get(sub["ref"])
    if not isinstance(entry, dict):
        return sub["ref"], {"ref": sub["ref"], "status": "none", "stale": False}
    status = str(entry.get("status") or "none")
    stale = status in ("ready", "approved", "choosing") and drafts.behind(entry, sub)
    return sub["ref"], {**entry, "ref": sub["ref"], "status": status, "stale": stale}


def _approved_at(rdir: Path, ref: str, row: dict) -> object:
    """When the contract `ref` was approved: the draft's stamp, else the approvals record; None when it is not."""
    if row.get("status") == "approved" and row.get("approved"):
        return row["approved"]
    try:
        import bt_design_approval
        record = bt_design_approval.approvals(rdir).get(ref) or {}
    except Exception:  # noqa: BLE001 - an unreadable approvals file only means «not approved» here
        record = {}
    if record.get("status") == "approved":
        return record.get("when") or "?"
    return "?" if row.get("status") == "approved" else None   # approved at an unknown time: never «after the rejection»


def _flow(rdir: Path, sid: str) -> dict | None:
    """The planning flow's confirmation of `sid` ({"state", "confirmed_at"}), or None when the flow is off."""
    import bt_planning_flow
    if not bt_planning_flow.active(rdir):
        return None
    record = bt_planning_flow._load(rdir)["subplans"].get(sid) or {}
    try:
        ok = bt_planning_flow.confirmed_as(rdir, sid, drafts._plan(rdir))
    except Exception:  # noqa: BLE001 - a plan caught mid-edit reads as «not confirmed»
        ok = False
    return {"state": "confirmed" if ok else "changed", "confirmed_at": record.get("at", "")}


def _running_revision(rdir: Path) -> int | None:
    """The plan revision of the run the durable runtime owns (`RUN.durable-run.json`), or None for any other run."""
    try:
        import bt_run_owner
        if bt_run_owner.backend(rdir) != "dbos":
            return None
        revision = json.loads((Path(rdir) / "RUN.durable-run.json").read_text(encoding="utf-8")).get("revision")
    except Exception:  # noqa: BLE001 - an unreadable run record only means «no durable run known» here
        return None
    return revision if isinstance(revision, int) else None


def _join_reason(rdir: Path, holder: int | None) -> tuple[bool, dict | None]:
    """(a join waits for live attempts, the refusal of the last join) for the stage `holder` (None: any stage)."""
    def concerns(revision: object) -> bool:
        return isinstance(revision, int) and (holder is None or revision >= holder)
    try:
        pending = json.loads((Path(rdir) / "RUN.join.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pending = None
    if isinstance(pending, dict) and concerns((pending.get("run") or {}).get("revision")):
        if pending.get("error"):
            code, _, message = str(pending["error"]).partition(": ")
            return False, {"code": code, "message": message, "at": ""}
        return True, None
    try:
        refused = json.loads((Path(rdir) / "RUN.join.refused.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        refused = None
    if isinstance(refused, dict) and concerns(refused.get("revision")):
        return False, {k: str(refused.get(k) or "") for k in ("code", "message", "at")}
    return False, None


def join_state(rdir: Path, sid: str, confirmed: float | None) -> dict | None:
    """Where the reconfirmed `sid` (confirmed at `confirmed`) stands against the durable run: None while that run holds
    it, or when that cannot be known (no durable run, no stage, no confirmation time); else {"stage": the frozen
    revision that holds it or None, "running": the run's revision, "waiting": bool, "refused": {code, message, at} or
    None}. The holding stage is the first frozen after the confirmation with `sid` in it and not kept as before (D-259)."""
    running = _running_revision(rdir)
    if running is None or confirmed is None:
        return None
    import bt_plan_adapter
    stages = bt_plan_adapter.stage_summary(rdir).get("stages") or []
    if not stages:
        return None
    holder = next((s["revision"] for s in stages if sid in s.get("subplans", ()) and sid not in s.get("kept", ())
                   and _after(s.get("frozen_at"), confirmed)), None)
    if holder is not None and running >= holder:
        return None
    waiting, refused = _join_reason(rdir, holder) if holder is not None else (False, None)
    return {"stage": holder, "running": running, "waiting": waiting, "refused": refused}


def _join_detail(state: dict) -> str:
    if state["stage"] is None:
        return f"aprueba la etapa con «Ejecutar cambios»; la ejecución sigue en r{state['running']}"
    text = f"etapa r{state['stage']} aprobada; la ejecución sigue en r{state['running']}"
    if state["waiting"]:
        text += " · se une en cuanto terminen los intentos en curso"
    if state["refused"]:
        said = " ".join(f"{state['refused']['code']}: {state['refused']['message']}".split())
        text += f" · la unión se rechazó: {said[:300]}"
    return text


def _redesign_phase(design: dict, flow: dict | None, since: float | None, approved: object) -> str:
    status = design["status"]
    if status == "choosing" and not design.get("chosen") and not design.get("stale"):
        return "choosing"
    if status == "ready" and not design.get("stale"):
        return "approve_contract"
    if not approved or design.get("stale") or design.get("amend"):
        return "redesigning"                 # queued, drafting, amending, failed or a new contract not started yet
    if flow is not None and not (flow.get("state") == "confirmed" and _after(flow.get("confirmed_at"), since)):
        return "reconfirm"
    return "building"


def correction(rdir: Path, sid: str, *, row: dict | None = None, design: dict | None = None,
               flow: dict | None | bool = False, progress: tuple[int, int] | None = None) -> dict | None:
    """The correction phase of a rejected subplan version, or None when `sid` is not waiting for one.

    `row` is `sid`'s row of `bt_verification.state` (read when omitted); `design` its draft row (`bt_design_drafts.rows`,
    read lock-free when omitted); `flow` its planning-flow item ({"state", "confirmed_at"}; None = no flow; omitted =
    read); `progress` the run's (completed, total) tasks of the subplan, shown while building. Returns {"id", "version",
    "next", "path" (redesign | repair), "phase", "phase_es", "label", "steps", "detail", "note", "pending", "at", "retest", "join"}; `retest` is the re-published older version, or None;
    `join` is `join_state` while the phase is «por unir a la ejecución», else None."""
    rdir = Path(rdir)
    if row is None:
        import bt_verification
        row = next((r for r in bt_verification.state(rdir)["subplans"] if r["id"] == sid), None)
    if not in_correction(row):
        return None                          # nothing rejected, or a version above N is published: «por probar» again
    dec = row.get("decision") or {}
    version = dec.get("version") or row.get("version")
    upcoming = version + 1 if isinstance(version, int) else "?"
    since = _when(dec.get("at"))
    ref = (design or {}).get("ref")
    if design is None:
        ref, design = _design(rdir, sid)
    approved = _approved_at(rdir, ref, design) if ref and design else None
    redesign = bool(ref and design and drafts.active(rdir) and (not approved or _after(approved, since)
                                                                or design.get("stale") or design.get("amend")))
    if redesign:
        if flow is False:
            flow = _flow(rdir, sid)
        phase, table = _redesign_phase(design, flow, since, approved), REDESIGN
    else:
        phase, table = "repairing", REPAIR
    joining = None
    if phase == "building":
        confirmed = _when(flow.get("confirmed_at")) if flow else _when(approved)
        joining = join_state(rdir, sid, confirmed)
        phase = "joining" if joining else phase
    keys = [k for k, _ in table]
    names = {k: label.format(next=upcoming) for k, label in table}
    detail = _join_detail(joining) if joining else ""
    if phase in ("building", "repairing") and progress and progress[1]:
        detail = f"{progress[0]}/{progress[1]} tareas"
    if phase == "repairing" and (said := (row.get("solver") or {}).get("text")):
        detail = said + (f" · {detail}" if detail else "")
    if phase == "redesigning" and design and design.get("status") == "failed":
        detail = "el Designer falló en su último intento"
    if row.get("state") == "outdated" and row.get("version"):     # an older (or equal) tree published again to retry
        detail += ("" if not detail else " · ") + f"v{row['version']} publicada de nuevo para volver a probarla"
    pending = dec.get("pending") or next(iter(reversed([p for p in dec.get("open_pending") or [] if isinstance(p, str)])), "")
    return {"id": sid, "version": version, "next": upcoming, "path": "redesign" if redesign else "repair", "phase": phase,
            "phase_es": names[phase], "label": f"Rechazada v{version} · {names[phase]}",
            "steps": [{"key": k, "label": names[k], "state": "done" if keys.index(k) < keys.index(phase) else
                       "now" if k == phase else "todo"} for k in keys],
            "detail": detail, "note": str(dec.get("note") or ""), "pending": str(pending or ""), "at": str(dec.get("at") or ""),
            "retest": row.get("version") if row.get("state") == "outdated" else None, "join": joining}


def corrections(rdir: Path, ctx: dict | None = None) -> dict[str, dict]:
    """Every rejected subplan's correction, keyed by id; with a Plan tab `ctx` its draft rows, flow and run progress are
    reused and the result is cached in it for the fragment."""
    if ctx is not None and "corrections" in ctx:
        return ctx["corrections"]
    import bt_verification
    out: dict[str, dict] = {}
    try:
        rows = bt_verification.state(rdir)["subplans"] if bt_verification.applies(rdir) else []
    except Exception:  # noqa: BLE001 - a status label never breaks a page
        rows = []
    rejected = [r for r in rows if in_correction(r)]
    progress: dict = {}
    if ctx is not None and rejected:
        try:
            import bt_page_planning_run as run_view
            progress = run_view.counts(ctx)
        except Exception:  # noqa: BLE001 - no run progress: the label goes without it
            progress = {}
    for r in rejected:
        kwargs: dict = {"row": r, "progress": progress.get(r["id"])}
        if ctx is not None:
            sub = next((s for s in ctx.get("subplans") or [] if s["id"] == r["id"]), None)
            if sub is not None:
                kwargs["design"] = (ctx.get("rows") or {}).get(sub["ref"]) if sub["ref"] else None
                if sub["ref"] and kwargs["design"] is None:
                    kwargs["design"] = {"ref": sub["ref"], "status": "none", "stale": False}
            if ctx.get("flow"):
                kwargs["flow"] = ctx["flow"]["subplans"].get(r["id"])
        try:
            found = correction(rdir, r["id"], **kwargs)
        except Exception:  # noqa: BLE001 - one unreadable subplan keeps the others' labels
            found = None
        if found:
            out[r["id"]] = found
    if ctx is not None:
        ctx["corrections"] = out
    return out
