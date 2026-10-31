"""Revise ONE owner-picked design direction into a new revision instead of regenerating every direction.

The source direction's files stay immutable; the Designer writes `design/<ref>.r<N+1>.dir-<key>.*` and the
result is a single-direction `choosing` state the owner can iterate again or choose and finalise.
"""
from __future__ import annotations

import json
import secrets
from pathlib import Path


def source(entry: dict, key: str) -> dict | None:
    """The settled direction `key` that may be iterated from this entry's state, if any."""
    status = entry.get("status")
    if status == "choosing" or (status == "ready" and entry.get("chosen") == key):
        return next((d for d in entry.get("directions") or [] if d.get("id") == key and d.get("status") == "ready"), None)
    if status == "failed" and (entry.get("iterate_from") or {}).get("id") == key:
        return entry["iterate_from"]  # retry of an iteration that produced nothing valid
    return None


def route(entry: dict) -> str | None:
    """The direction every pending owner comment targets, when the entry can be iterated on it."""
    targets = {f.get("direction") for f in entry.get("feedback") or [] if not f.get("consumed")}
    if len(targets) != 1 or None in targets:
        return None
    key = targets.pop()
    return key if source(entry, key) else None


def add_feedback(project: str, rdir: Path, ref: str, text: str, via: str, *, direction: str | None = None) -> str:
    """Owner feedback: on one iterable direction it revises that direction; otherwise every direction is redone."""
    import bt_design_drafts as drafts
    text = " ".join(text.split())
    if not text:
        return "Escribe qué debe cambiar en el diseño."
    if not drafts.planning(rdir):
        return "El plan ya no está en planificación: los cambios de diseño van en una versión nueva del contrato."
    row = next((s for s in drafts.subplans(rdir) if s["ref"] and s["ref"] == ref), None)
    if row is None:
        return f"{ref or 'Ese contrato'} no es un subplan con interfaz de este plan."
    with drafts._locked(rdir) as data:
        entry = data["drafts"].setdefault(ref, {"feedback": [], "status": "none"})
        drafts._settle(rdir, ref, entry)
        if entry.get("status") == "approved":
            return f"{ref} ya fue aprobado con el plan; los cambios van en una versión nueva del contrato."
        if direction and direction not in {d["id"] for d in entry.get("directions", [])}:
            return "Dirección no válida para ese borrador."
        busy = entry.get("status") in drafts.ACTIVE
        # a direction awaiting the owner is iterated even after a plan change: the iteration carries it (D-263)
        late = drafts.behind(entry, row) and entry.get("status") != "choosing"
        routed = bool(direction and not busy and not late and source(entry, direction))
        if not routed:
            entry.setdefault("feedback", []).append({"id": secrets.token_hex(8), "when": drafts._now(),
                                                    "text": text[:4000], "via": via, "direction": direction})
            drafts._event(rdir, "Tú → Designer", f"{ref}: {text[:200]}", entry, kind="feedback")
    if routed:
        try:
            return iterate(project, rdir, ref, direction, text, via)
        except SystemExit as exc:
            return str(exc)
    if busy:
        return "Comentario guardado. El Designer lo tomará al terminar el trabajo en curso."
    started = drafts.request(project, rdir, [ref], reason="feedback", fresh=True)
    return (f"Comentario enviado al Designer; rediseñando {ref}." if started else
            f"Comentario guardado para {ref}; no se pudo iniciar el Designer (revisa el estado).")


def iterate(project: str, rdir: Path, ref: str, key: str, comments: str, via: str, *, plan_delta: str = "") -> str:
    """Revise direction `key` into a new revision; `plan_delta` (from bt_design_amend) applies a plan change instead
    of owner comments to the direction that continues the owner's choice.

    When the subplan changed after the direction was drawn (`behind`), the iteration carries the plan delta together
    with the owner's comments instead of refusing. A refusal never drops the owner's text: while the Designer works it
    is kept as feedback that `follow` iterates on afterwards, otherwise under the entry's `refused` list; every refusal
    is logged in the activity. Incident: pictures REQ-021 planes@v2, 2026-10-31 (D-263) — the owner's comments on
    direction C were refused because the Planner had updated SP-14, the text was dropped, and «Actualizar diseño» did
    not apply to a direction never chosen, so the owner could not move."""
    import bt_delegate
    import bt_design_directions as directions
    import bt_design_drafts as drafts
    comments = " ".join((comments or "").split())
    if not drafts.planning(rdir):
        _refuse(rdir, ref, key, comments, "El plan ya no está en planificación.")
    row = next((s for s in drafts.subplans(rdir) if s["ref"] and s["ref"] == ref), None)
    if row is None:
        _refuse(rdir, ref, key, comments, "Contrato de interfaz no válido.")
    amending, refusal = bool(plan_delta), ""
    with drafts._locked(rdir) as data:  # a refusal leaves the lock normally so that what it records is saved
        for name, other in data["drafts"].items():
            drafts._settle(rdir, name, other)
        entry = data["drafts"].get(ref) or {}
        prior = source(entry, key)
        if entry.get("status") in drafts.ACTIVE:
            refusal = f"El Designer ya está trabajando en {ref}; itera cuando termine."
            if comments and key in {d.get("id") for d in entry.get("directions") or []}:
                _feedback(rdir, ref, key, comments, via, entry)
                comments, refusal = "", (f"El Designer ya está trabajando en {ref}; tu comentario quedó guardado y se "
                                         f"aplicará a la dirección {key.upper()} cuando termine.")
        elif prior is None:
            refusal = "Esa dirección no está lista para iterar."
        elif not directions.unchanged(rdir, ref, prior):
            refusal = "La dirección cambió después de la comparación; hay que rehacerla."
        else:
            plan_delta = plan_delta or _carried(project, rdir, row, key, entry)
            if comments:
                _feedback(rdir, ref, key, comments, via, entry)
                comments = ""
            feedback = [f for f in entry.get("feedback", []) if not f.get("consumed")]
            if not feedback and not plan_delta:
                refusal = "Escribe qué debe cambiar en la dirección."
        if refusal:
            _keep_refused(rdir, ref, key, comments, refusal, entry if ref in data["drafts"] else None)
        else:
            for f in feedback:
                f.setdefault("id", secrets.token_hex(8))
            rev = int(entry.get("attempt") or 0) + 1
            continuation_choice = key if entry.get("chosen") == key else entry.get("continuation_choice")
            if entry.get("directions"):
                entry.setdefault("direction_history", []).append({"revision": entry["attempt"],
                    "chosen": entry.get("chosen"), "directions": entry["directions"], "comparison": entry.get("comparison")})
            prior = json.loads(json.dumps(prior))
            entry.update(status="drafting", phase="explore", attempt=rev, chosen=None, comparison=None,
                         digest=row["digest"], ui_digest=row["ui_digest"], started=drafts._now(), error="",
                         reason="plan changed" if amending else "iterate", fresh=False, subplan_id=row["id"],
                         feedback_batch=[f["id"] for f in feedback], iterate_from=prior,
                         continuation_choice=continuation_choice, plan_delta=plan_delta,
                         behavior=directions.write_behavior(rdir, ref, rev, row, project).name,
                         directions=[{"id": key, "status": "queued", "seed": prior.get("seed"), "revision": rev,
                                      "name": prior.get("name"), "iterated_from": prior["revision"]}])
    if refusal:
        raise SystemExit(refusal)
    brief = _brief(project, rdir, row, feedback, prior, rev) + plan_delta
    try:
        order = bt_delegate.create(project, brief, None, None, Path(rdir), [], None, drafts.TIMEOUT_MIN,
                                   None, None, kind="design", role="designer")
        with drafts._locked(rdir) as data:  # ownership before spawning, as in an exploration
            data["drafts"][ref]["directions"][0].update(delegation=order["id"], status="drafting")
            data["drafts"][ref]["delegation"] = order["id"]
        bt_delegate.start_background(order["id"])
    except (SystemExit, Exception) as exc:
        with drafts._locked(rdir) as data:
            data["drafts"][ref]["directions"][0].update(status="failed", error=str(exc)[:400])
        raise SystemExit(f"No se pudo iniciar la iteración: {exc}") from exc
    with drafts._locked(rdir) as data:
        what = ("actualizando por cambio del plan la" if amending else
                "iterando con el cambio del plan la" if plan_delta else "iterando")
        drafts._event(rdir, "Designer", f"{ref}: {what} dirección {key.upper()} · {prior.get('name') or key}",
                      data["drafts"][ref])
    return (f"Iterando la dirección {key.upper()} de {ref}"
            f"{' con tus comentarios y el cambio del plan' if plan_delta and not amending else ''}; "
            f"el Designer prepara la revisión {rev}.")


def follow(project: str, rdir: Path, ref: str, key: str, via: str) -> str | None:
    """Iterate on pending owner comments (no new text); None when it cannot start now."""
    try:
        return iterate(project, rdir, ref, key, "", via)
    except SystemExit:
        return None


def _feedback(rdir: Path, ref: str, key: str, text: str, via: str, entry: dict) -> None:
    import bt_design_drafts as drafts
    entry.setdefault("feedback", []).append({"id": secrets.token_hex(8), "when": drafts._now(),
                                             "text": text[:4000], "via": via, "direction": key})
    drafts._event(rdir, "Tú → Designer", f"{ref} · {key.upper()}: {text[:200]}", entry, kind="feedback")


def _carried(project: str, rdir: Path, row: dict, key: str, entry: dict) -> str:
    """The plan change an owner's iteration of `key` must carry: the delta since the direction was drawn when the
    subplan changed (`behind`), plus the delta a failed iteration of the same direction had carried (the failed start
    already moved the entry to the current brief, so a retry could not recompute it)."""
    import bt_design_amend
    import bt_design_drafts as drafts
    parts = []
    if entry.get("status") == "failed" and (entry.get("iterate_from") or {}).get("id") == key and entry.get("plan_delta"):
        parts.append(entry["plan_delta"])
    if drafts.behind(entry, row):
        change = bt_design_amend.delta(project, rdir, row, entry)
        parts.append(bt_design_amend.preamble(rdir, row["ref"], change, lead=CARRIED_LEAD))
    return "".join(parts)


CARRIED_LEAD = ("This direction was drawn before the plan changed and the owner now asks to revise it. Fold the plan "
                "change into this revision together with the owner's comments; do not redesign.")


def _keep_refused(rdir: Path, ref: str, key: str, text: str, reason: str, entry: dict | None) -> None:
    """Log a refused iteration in the activity and keep the owner's unsaved text with the entry (not as feedback:
    pending feedback would start Designer work the owner was just told did not start)."""
    import bt_design_drafts as drafts
    if text and entry is not None:
        entry["refused"] = [*(entry.get("refused") or []), {"when": drafts._now(), "direction": key, "via": "iterate",
                                                            "text": text[:4000], "reason": reason}][-20:]
    drafts._event(rdir, "Designer", f"{ref} · {str(key).upper()}: iteración rechazada — {reason}"
                  f"{f' · Tu texto: {text[:200]}' if text else ''}", entry or {}, kind="refused")


def _refuse(rdir: Path, ref: str, key: str, text: str, reason: str) -> None:
    _keep_refused(rdir, ref, key, text, reason, None)
    raise SystemExit(reason)


def _brief(project: str, rdir: Path, row: dict, feedback: list[dict], prior: dict, rev: int) -> str:
    import bt_design_directions as directions
    import bt_design_drafts as drafts
    old = directions.files(rdir, row["ref"], prior["revision"], prior["id"])
    out = directions.files(rdir, row["ref"], rev, prior["id"])
    behavior = Path(rdir) / "design" / f"{row['ref']}.r{rev}.behavior.md"
    md = drafts.paths(rdir, row["ref"])[0]
    shape = ('{"name":"...","axes":{' + ",".join(json.dumps(k) + ':"..."' for k in directions.AXES) + '},'
             '"evidence":{"layout":["CSS selector"],"navigation":["CSS selector"],"typography":["CSS selector"],'
             '"motion":["CSS selector"]}}')
    return drafts._brief(project, rdir, row, feedback, behavior=behavior) + f"""
ITERATION OF ONE DIRECTION. The output list and previous-draft note above are superseded by this scoped list.
Do NOT write the canonical contract or canonical HTML, and do not explore new directions.
Revise direction {prior['id'].upper()} «{prior.get('name') or prior['id']}» (revision {prior['revision']}) into revision {rev}.
Read its files first: {old['html']}, {old['tsx']}, {old['md']} and {old['json']}, plus the shared behavioural
source (the UI brief) {behavior}. Apply the owner's comments above that target direction={prior['id']} or all; comments
about other directions are context only. Keep this direction's name, composition, navigation and motion except
where a comment asks to change them, and keep it inside the existing product: its shell, navigation, tokens, fonts
and components stay fixed; if the previous revision introduced a new palette, font family or brand, bring it back
to the product's design system. {directions._ledger(rdir, row['ref'])}
Those source files are immutable: never edit them. If the canonical contract {md} or mockup {md.with_suffix('.html')}
carries later plan-change amendments, keep them in this revision.
Write ONLY {out['tsx']} (start from a copy of the previous source), {out['html']}, {out['md']} and {out['json']}.
Keep the eight-axis note in {out['md']} and the JSON shape valid, updating them only where the changes demand:
{shape}
Selectors must match rendered elements that demonstrate the claims; motion evidence must actually animate.
Rebuild {out['tsx']} with the CURRENT offline builder into {out['html']}, then run contrast.py and the offline
kit/audit_mockup.py on {out['html']}. Both themes, responsive layouts and reduced-motion parity stay mandatory.
No shared contract writes, no plan edits, no approval. Report the audit's real RESULT line.
"""
