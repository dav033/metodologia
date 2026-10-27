"""Amend an owner-chosen design when the plan changes, instead of regenerating its directions.

Two shapes of chosen work exist. A finalised contract (`ready` with `chosen`, or a failed amendment of one) is
revised by one Designer session that writes revision-specific files `design/<ref>.amend-<N>.{md,html,tsx}`;
only a valid result is copied over the canonical contract, so a failure leaves the previous files and the choice
untouched. A `choosing` entry whose single direction continues the owner's choice (an iteration of the chosen
direction) is revised through bt_design_iterate with the same plan-delta preamble.

The amendment runs under its own status `amending`, which earlier settlement code leaves alone.
"""
from __future__ import annotations

import json
import secrets
from pathlib import Path

REASON = "plan changed"


def files(rdir: Path, ref: str, n: int) -> dict[str, Path]:
    base = Path(rdir) / "design" / f"{ref}.amend-{n}"
    out = {ext: Path(f"{base}.{ext}") for ext in ("md", "html", "tsx")}
    # the canonical files as they were before the session (not `.md`: they are never translated or listed)
    return {**out, "before_md": Path(f"{base}.md.orig"), "before_html": Path(f"{base}.html.orig")}


def last_chosen(entry: dict) -> str | None:
    """The owner's latest choice, also after an iteration cleared `chosen` (it survives in direction_history)."""
    if entry.get("chosen"):
        return entry["chosen"]
    return next((h["chosen"] for h in reversed(entry.get("direction_history") or []) if h.get("chosen")), None)


def _recorded(rdir: Path, ref: str, entry: dict) -> bool:
    import bt_design_drafts as drafts
    md, html = drafts.paths(rdir, ref)
    return bool(entry.get("sha256")) and drafts._sha(md) == entry["sha256"] and html.is_file()


def mode(rdir: Path, ref: str, entry: dict) -> str | None:
    """`contract`, `direction` or None: how this entry's chosen work is extended (None means there is none)."""
    if not entry or not _recorded(rdir, ref, entry):
        return None
    status, chosen = entry.get("status"), last_chosen(entry)
    retry = status == "failed" and entry.get("amend") and entry.get("reason") == REASON
    if entry.get("chosen") and (status == "ready" or retry) and \
            any(d.get("id") == chosen and d.get("status") == "ready" for d in entry.get("directions") or []):
        return "contract"
    ready = [d for d in entry.get("directions") or [] if d.get("status") == "ready"]
    if status == "choosing" and len(ready) == 1 and ready[0].get("iterated_from") and ready[0]["id"] == chosen:
        return "direction"
    if status == "failed" and entry.get("reason") == REASON and (entry.get("iterate_from") or {}).get("id") == chosen:
        return "direction"
    return None


def delta(project: str, rdir: Path, row: dict, entry: dict) -> dict:
    """The previous UI brief (the one the design was built from), the current one and their mechanical diff."""
    import bt_design_brief_diff as brief_diff
    import bt_design_ui_brief as ui_brief
    prev_path = Path(rdir) / "design" / entry["behavior"] if entry.get("behavior") else None
    try:
        before = prev_path.read_text(encoding="utf-8") if prev_path else ""
    except (OSError, UnicodeError):
        before = ""
    after = ui_brief.build(rdir, row, ui_brief.cloned_repos(project) if project else {})
    return {"previous_path": prev_path if before else None, "previous": before, "new": after,
            "changes": brief_diff.diff(before, after)}


def start(project: str, rdir: Path, ref: str, comments: str, via: str, *, auto: bool = False) -> str:
    """Start the amendment of `ref`'s chosen design with the plan delta; refuses while any Designer works."""
    import bt_design_drafts as drafts
    import bt_design_iterate as iterate
    comments = " ".join((comments or "").split())
    if not drafts.planning(rdir):
        raise SystemExit("El plan ya no está en planificación: los cambios van en una versión nueva del contrato.")
    row = next((s for s in drafts.subplans(rdir) if s["ref"] and s["ref"] == ref), None)
    if row is None:
        raise SystemExit(f"{ref or 'Ese contrato'} no es un subplan con interfaz de este plan.")
    with drafts._locked(rdir) as data:
        for name, other in data["drafts"].items():
            drafts._settle(rdir, name, other)
        if any(e.get("status") in drafts.ACTIVE for e in data["drafts"].values()):
            raise SystemExit("Otro Designer está trabajando en este requerimiento; actualiza el diseño cuando termine.")
        entry = data["drafts"].get(ref) or {}
        if entry.get("status") == "approved":
            raise SystemExit(f"{ref} ya fue aprobado con el plan; los cambios van en una versión nueva del contrato.")
        how = mode(rdir, ref, entry)
        if how is None:
            raise SystemExit(f"{ref} no tiene un diseño elegido que actualizar; pide un diseño nuevo.")
        if not drafts.behind(entry, row) and not (entry.get("status") == "failed"):
            raise SystemExit(f"El diseño de {ref} ya está al día con el plan.")
        if comments:
            entry.setdefault("feedback", []).append({"id": secrets.token_hex(8), "when": drafts._now(),
                                                     "text": comments[:4000], "via": via, "direction": None})
            drafts._event(rdir, "Tú → Designer", f"{ref}: {comments[:200]}", entry, kind="feedback")
        if auto:
            entry["auto_runs"] = int(entry.get("auto_runs") or 0) + 1
        change = delta(project, rdir, row, entry)
        if how == "direction":
            key = last_chosen(entry)
        else:
            feedback = [f for f in entry.get("feedback", []) if not f.get("consumed")]
            for f in feedback:
                f.setdefault("id", secrets.token_hex(8))
            n = int(entry.get("amends") or 0) + 1
            out = files(rdir, ref, n)
            behavior = Path(rdir) / "design" / f"{ref}.amend-{n}.behavior.md"
            behavior.write_text(change["new"], encoding="utf-8")
            chosen = next(d for d in entry["directions"] if d.get("id") == entry["chosen"])
            import bt_design_directions as directions
            source = Path(rdir) / "design" / entry["amend_source"] if entry.get("amend_source") else \
                directions.files(rdir, ref, chosen["revision"], chosen["id"])["tsx"]
            md, html = drafts.paths(rdir, ref)
            out["before_md"].write_bytes(md.read_bytes())  # restored if a failing session touched the canonical files
            out["before_html"].write_bytes(html.read_bytes())
            entry["amends"] = n
            entry["amend"] = {"n": n, "from_revision": int(entry.get("revision") or 0), "digest": row["digest"],
                              "ui_digest": row["ui_digest"], "behavior": behavior.name,
                              "feedback_batch": [f["id"] for f in feedback], "via": via}
            entry.update(status="amending", reason=REASON, error="", started=drafts._now(), subplan_id=row["id"],
                         delegation=None)
            brief = drafts._brief(project, rdir, row, feedback, behavior=behavior) + _contract_brief(
                rdir, ref, change, out, source if source.is_file() else None)
    if how == "direction":
        return iterate.iterate(project, rdir, ref, key, "", via, plan_delta=preamble(rdir, ref, change))
    return _launch(project, rdir, ref, brief, n)


def _launch(project: str, rdir: Path, ref: str, brief: str, n: int) -> str:
    import bt_delegate
    import bt_design_drafts as drafts
    try:
        order = bt_delegate.create(project, brief, None, None, Path(rdir), [], None, drafts.TIMEOUT_MIN,
                                   None, None, kind="design", role="designer")
        with drafts._locked(rdir) as data:  # ownership before spawning, as in an exploration
            data["drafts"][ref].update(delegation=order["id"], agent=order.get("agent"), model=order.get("model"))
        bt_delegate.start_background(order["id"])
    except (SystemExit, Exception) as exc:  # no account, usage limits: the choice stays intact
        with drafts._locked(rdir) as data:
            _fail(rdir, ref, data["drafts"][ref], f"No se pudo iniciar el Designer: {str(exc)[:300]}")
        raise SystemExit(f"No se pudo actualizar el diseño: {exc}") from exc
    with drafts._locked(rdir) as data:
        drafts._event(rdir, "Designer", f"{ref}: actualizando el diseño elegido por cambio del plan", data["drafts"][ref])
    return f"Actualizando {ref} con el cambio del plan; el Designer revisa el diseño elegido (versión {n})."


def preamble(rdir: Path, ref: str, change: dict) -> str:
    """What changed in the plan, for any amendment brief."""
    import bt_design_brief_diff as brief_diff
    previous = change["previous_path"] or "(no previous UI brief was recorded: check the whole contract against the new one)"
    return f"""
PLAN CHANGE. The design below was confirmed by the owner; the plan changed afterwards. Extend it, do not redesign.
Previous UI brief (what the current design was built from): {previous}
Mechanical diff of the UI brief, previous → new (+ added, - removed, ~ changed):
{brief_diff.render(change['changes'])}
Apply ONLY this delta plus the owner's comments above: update names, copy, states and components the delta touches;
when it adds screens or states, extend the contract sections and the mockup's views/state switches for them; when it
removes something, remove it. Keep composition, navigation, motion, tokens and every decision the delta does not touch.
"""


def _contract_brief(rdir: Path, ref: str, change: dict, out: dict[str, Path], source: Path | None) -> str:
    import bt_design_drafts as drafts
    md, html = drafts.paths(rdir, ref)
    start = (f"Start {out['tsx']} from a copy of {source}, edit only what the delta needs, and rebuild it with the "
             f"CURRENT offline builder into {out['html']}." if source else
             f"There is no TSX source: start {out['html']} from a copy of {html} and edit it in place; say so in CONCERNS.")
    return f"""
AMENDMENT OF THE CHOSEN, FINALISED DESIGN. The output list and previous-draft note above are superseded by this
scoped list. Do NOT explore directions and do NOT redesign.
Current canonical contract: {md} · mockup: {html}. Read both first; they are immutable: never edit them.
{preamble(rdir, ref, change)}
Write ONLY {out['md']} (the complete revised twelve-section contract `{ref}`, status `draft`: never approve it),
{out['html']} and {out['tsx']}. {start}
Run contrast.py and the offline kit/audit_mockup.py on {out['html']}; both themes, responsive layouts and
reduced-motion parity stay mandatory. No SPEC, PLAN, history or repository writes, no approval.
Report the audit's real RESULT line (or "audit not run: <reason>") and one "Q:" line per open question in "notes".
"""


def settle(rdir: Path, ref: str, entry: dict) -> None:
    """Fold a finished amendment into its entry: a valid result becomes the next revision, anything else fails it."""
    import bt_design_directions as directions
    import bt_design_drafts as drafts
    if entry.get("status") != "amending":
        return
    job = entry.get("amend") or {}
    if not entry.get("delegation"):
        if drafts._age(entry.get("started")) > drafts.QUEUED_TTL_SEC:
            _fail(rdir, ref, entry, "El Designer nunca empezó la actualización.")
        return
    outcome = directions._outcome(entry["delegation"])
    if outcome.get("status") == "running_or_pending":
        if drafts._age(entry.get("started")) < drafts.TIMEOUT_MIN * 60 + drafts.STALE_GRACE_SEC:
            return
        outcome = {"status": "failed", "summary": "el Designer terminó sin resultado"}
    out = files(rdir, ref, int(job.get("n") or 0))
    try:
        if outcome.get("status") not in directions.SUCCESS:
            raise ValueError(str(outcome.get("summary") or outcome.get("status") or "sin resultado"))
        text = out["md"].read_text(encoding="utf-8", errors="replace") if out["md"].is_file() else ""
        if sum(1 for line in text.splitlines() if line.startswith("## ")) < drafts.MIN_SECTIONS:
            raise ValueError(f"el contrato actualizado no existe o tiene menos de {drafts.MIN_SECTIONS} secciones")
        if not out["html"].is_file() or not out["html"].stat().st_size:
            raise ValueError("falta el mockup actualizado")
    except (OSError, ValueError) as exc:
        return _fail(rdir, ref, entry, f"La actualización por cambio del plan falló: {exc}"[:600])
    md, html = drafts.paths(rdir, ref)
    md.write_bytes(out["md"].read_bytes())
    html.write_bytes(out["html"].read_bytes())
    report = _report(outcome)
    entry["revision"] = int(entry.get("revision") or 0) + 1
    entry.update(status="ready", sha256=drafts._sha(md), mockup=True, error="", failures=0, finished=drafts._now(),
                 report=outcome.get("status"), digest=job.get("digest"), ui_digest=job.get("ui_digest"),
                 behavior=job.get("behavior") or entry.get("behavior"), summary=str(outcome.get("summary") or "")[:600],
                 questions=[line.strip()[2:].strip() for line in str(report.get("notes") or "").splitlines()
                            if line.strip().upper().startswith("Q:")])
    if out["tsx"].is_file():
        entry["amend_source"] = out["tsx"].name
    drafts._archive(rdir, ref, entry["revision"])
    entry.setdefault("history", []).append({"rev": entry["revision"], "at": entry["finished"],
                                            "summary": entry["summary"], "reason": REASON})
    for f in entry.get("feedback", []):
        if f.get("id") in job.get("feedback_batch", []) and not f.get("consumed"):
            f["consumed"] = entry["delegation"]
    entry.setdefault("amend_history", []).append({**job, "delegation": entry["delegation"], "at": entry["finished"],
                                                  "revision": entry["revision"]})
    entry.pop("amend", None)
    drafts._event(rdir, "Designer", f"{ref}: contrato actualizado por cambio del plan", entry)


def _report(outcome: dict) -> dict:
    try:
        return json.loads(Path(outcome["result_file"]).read_text(encoding="utf-8")) if outcome.get("result_file") else {}
    except (OSError, UnicodeError, ValueError):
        return {}


def _fail(rdir: Path, ref: str, entry: dict, error: str) -> None:
    """A failed amendment keeps the chosen direction, the canonical files (restored if a session touched them) and
    the plan delta still pending, so it can be retried or the owner can ask for a fresh design."""
    import bt_design_drafts as drafts
    md, html = drafts.paths(rdir, ref)
    saved = files(rdir, ref, int((entry.get("amend") or {}).get("n") or 0))
    for target, copy in ((md, saved["before_md"]), (html, saved["before_html"])):
        if copy.is_file() and drafts._sha(target) != drafts._sha(copy):
            target.write_bytes(copy.read_bytes())
    entry.update(status="failed", error=error[:600], finished=drafts._now())
    entry["failures"] = int(entry.get("failures") or 0) + 1
    drafts._event(rdir, "Designer", f"{ref} · la actualización del diseño falló: {error[:120]}", entry)
