"""Bounded, independent design explorations and an owner-selected final contract.

drafts.json remains the transaction boundary. Exploration files are revision-specific;
only the selected direction's finalizer writes the canonical contract and mockup.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import subprocess
from pathlib import Path

SEEDS = (
    ("Operational: dense working information in the existing shell; hierarchy by type scale and grouping, precise "
     "quick transitions."),
    ("Spatial: the same product shell with a different arrangement of the changed area (panels, inspector, canvas), "
     "alternative in-page navigation, spatial transitions."),
    ("Direct manipulation: the same product shell with in-place editing, progressive disclosure and tactile "
     "press/settle feedback on the changed controls."),
)
AXES = ("concept", "layout", "navigation", "typography", "density", "components", "colour", "motion")
SUCCESS = ("claimed", "verified", "partial")


def files(rdir: Path, ref: str, revision: int, key: str) -> dict[str, Path]:
    base = Path(rdir) / "design" / f"{ref}.r{revision}.dir-{key}"
    return {ext: Path(f"{base}.{ext}") for ext in ("html", "md", "json", "tsx")}


def choosable(ref: str, entry: dict, direction: dict) -> bool:
    """May the owner pick this direction? Yes when the comparison passed. When it failed ONLY because some other direction
    declares traits its mockup does not show (REQ-021 SP-14: B's `.rail-mark`), the directions whose own evidence is
    sound and whose pairs are distinct stay choosable: one broken alternative must not hide the good ones."""
    comparison = entry.get("comparison") or {}
    if comparison.get("ok"):
        return True
    report = comparison.get("report") or {}
    if comparison.get("error") and report.get("evidence_ok") is not False:
        return False
    if report.get("evidence_ok") is not False or not all(p.get("ok") for p in report.get("pairs") or ()):
        return False
    name = f"{ref}.r{direction.get('revision')}.dir-{direction.get('id')}.html"
    mine = next((x for x in report.get("directions") or () if x.get("id") == name), None)
    return mine is not None and all(row.get("ok") for rows in (mine.get("evidence") or {}).values() for row in rows)


def _outcome(did: str) -> dict:
    import bt_delegate
    try:
        return bt_delegate.summary(did)
    except (SystemExit, OSError, ValueError) as exc:
        return {"status": "failed", "summary": str(exc)[:300]}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _note(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("name"), str) or not data["name"].strip():
        raise ValueError("direction needs a name")
    axes = data.get("axes")
    if not isinstance(axes, dict) or any(not isinstance(axes.get(k), str) or not axes[k].strip() for k in AXES):
        raise ValueError("direction needs all eight axes")
    evidence = data.get("evidence")
    if not isinstance(evidence, dict) or any(not isinstance(evidence.get(k), list) or not evidence[k]
                                            or any(not isinstance(s, str) or not s.strip() for s in evidence[k])
                                            for k in ("layout", "navigation", "typography", "motion")):
        raise ValueError("direction needs selectors proving layout, navigation, typography and motion claims")
    return data


def write_behavior(rdir: Path, ref: str, rev: int, row: dict, project: str | None = None) -> Path:
    """The shared behavioural source of one revision (the UI brief); visual explorations cannot rewrite it."""
    import bt_design_ui_brief as ui_brief
    behavior = Path(rdir) / "design" / f"{ref}.r{rev}.behavior.md"
    repos = ui_brief.cloned_repos(project) if project else {}
    behavior.write_text(ui_brief.build(rdir, row, repos), encoding="utf-8")
    return behavior


def unchanged(rdir: Path, ref: str, d: dict) -> bool:
    """A settled direction's files still match the digests recorded when it was compared."""
    import bt_design_drafts as drafts
    out = files(rdir, ref, d["revision"], d["id"])
    try:
        same = all(_digest(out[ext]) == d.get(field) for ext, field in
                   (("html", "sha256"), ("md", "note_sha256"), ("json", "json_sha256")))
    except OSError:
        return False
    return same and drafts._sha(out["tsx"]) == d.get("tsx_sha256")


def start(project: str, rdir: Path, ref: str, reason: str, fresh: bool, count: int) -> dict:
    import bt_delegate
    import bt_design_drafts as drafts
    if type(count) is not int or not 1 <= count <= 3:
        raise SystemExit("El número de direcciones debe estar entre 1 y 3.")
    row = next((s for s in drafts.subplans(rdir) if s["ref"] == ref), None)
    if row is None:
        raise SystemExit("Contrato de interfaz no válido.")
    with drafts._locked(rdir) as data:
        entry = data["drafts"].setdefault(ref, {"feedback": []})
        if entry.get("status") in drafts.ACTIVE or entry.get("status") in ("choosing", "approved"):
            return entry
        rev = int(entry.get("attempt") or entry.get("revision") or 0) + 1
        feedback = [f for f in entry.get("feedback", []) if not f.get("consumed")]
        for f in feedback:
            f.setdefault("id", secrets.token_hex(8))
        if entry.get("directions"):
            entry.setdefault("direction_history", []).append({"revision": entry["attempt"],
                "chosen": entry.get("chosen"), "directions": entry["directions"], "comparison": entry.get("comparison")})
        entry.update(status="drafting", phase="explore", attempt=rev, directions=[], chosen=None, comparison=None,
                     continuation_choice=None,
                     digest=row["digest"], ui_digest=row["ui_digest"], started=drafts._now(), error="",
                     reason=reason, fresh=fresh,
                     subplan_id=row["id"], feedback_batch=[f["id"] for f in feedback], iterate_from=None)
        if reason == "plan changed":
            entry["auto_runs"] = int(entry.get("auto_runs") or 0) + 1
        behavior = write_behavior(rdir, ref, rev, row, project)
        entry["behavior"] = behavior.name
        for i in range(count):
            key = chr(97 + i)
            entry["directions"].append({"id": key, "status": "queued", "seed": SEEDS[i], "revision": rev})
    for i in range(count):
        key = chr(97 + i)
        out = files(rdir, ref, rev, key)
        base = drafts._brief(project, rdir, row, feedback, fresh=fresh, behavior=behavior)
        brief = base + f"""
EXPLORATION ONLY. The output list above is superseded by this scoped list. Do NOT write the canonical contract
or canonical HTML. The shared behavioural source is the UI brief {behavior}. Seed: {SEEDS[i]}
Read the local directions guidance in david-ui-kit/directions.md. The three directions of THIS subplan differ among
themselves in layout, hierarchy, density, component arrangement, in-page navigation and motion, all inside the
existing product: same app shell, navigation, tokens, fonts and component vocabulary.
{_ledger(rdir, ref)}
Draw TWO candidate thumbnail HTMLs first at {out['html']}.candidate-1.html and .candidate-2.html.
These are small visual compositions, not text lists. Choose the stronger candidate, then build the full mockup at
{out['html']} using entry {out['tsx']}. Write {out['md']} with name, approach (how this direction changes the
existing surface), its interaction/motion detail, why it fits the existing product, eight-axis table, chosen
thumbnail and honest audit results. Write {out['json']} with this JSON shape:
{{"name":"...","axes":{{{','.join(json.dumps(k)+':"..."' for k in AXES)}}},
"evidence":{{"layout":["CSS selector"],"navigation":["CSS selector"],"typography":["CSS selector"],"motion":["CSS selector"]}}}}
Selectors must match rendered elements that demonstrate the claims. Motion evidence must actually animate.
Both themes, responsive layouts, native selectors, expressive choreography and reduced-motion parity are mandatory.
Run the builder and audit on YOUR output path. You may write only the listed revision-specific files under design/.
No shared contract writes, no plan edits, no approval. Report the audit's real RESULT line.
"""
        try:
            order = bt_delegate.create(project, brief, None, None, Path(rdir), [], None, drafts.TIMEOUT_MIN,
                                       None, None, kind="design", role="designer")
            # Persist ownership before spawning so polling cannot mistake a live process for a missing one.
            with drafts._locked(rdir) as data:
                direction = data["drafts"][ref]["directions"][i]
                direction.update(delegation=order["id"], status="drafting")
            bt_delegate.start_background(order["id"])
        except (SystemExit, Exception) as exc:  # noqa: BLE001 - isolate a launch failure and show it on its direction
            with drafts._locked(rdir) as data:
                data["drafts"][ref]["directions"][i].update(status="failed", error=str(exc)[:400])
    with drafts._locked(rdir) as data:
        entry = data["drafts"][ref]
        entry["delegation"] = next((d["delegation"] for d in entry["directions"] if d.get("delegation")), None)
        drafts._event(rdir, "Designer", f"{ref}: explorando {count} direcciones", entry)
        return json.loads(json.dumps(entry))


def _ledger(rdir: Path, ref: str) -> str:
    """Sibling subplans' chosen/finalised contracts are the shared product language to reuse, never to avoid."""
    import bt_design_ui_brief as ui_brief
    found = ui_brief.siblings(rdir, ref)
    head = ("Reuse the app shell, navigation structure, tokens and component vocabulary established by sibling "
            "subplans' chosen/finalised contracts")
    if not found:
        return head + " (none yet: take them from the existing product); differ only in what is specific to this subplan."
    return head + "; differ only in what is specific to this subplan. Read them:\n" + "\n".join(f"  - {p}" for p in found)


def settle(rdir: Path, ref: str, entry: dict) -> None:
    import bt_design_drafts as drafts
    if entry.get("phase") == "finalise":
        return _settle_final(rdir, ref, entry)
    if entry.get("status") != "drafting":
        return
    for d in entry["directions"]:
        if d["status"] == "queued" and drafts._age(entry.get("started")) > drafts.QUEUED_TTL_SEC:
            d.update(status="failed", error="El lanzador terminó antes de iniciar esta dirección.")
        if d["status"] != "drafting":
            continue
        outcome = _outcome(d["delegation"])
        if outcome.get("status") == "running_or_pending":
            if drafts._age(entry.get("started")) < (drafts.TIMEOUT_MIN * 60 + drafts.STALE_GRACE_SEC):
                continue
            outcome = {"status": "failed", "summary": "Designer terminó sin resultado"}
        out = files(rdir, ref, d["revision"], d["id"])
        try:
            if outcome.get("status") not in SUCCESS or not out["html"].is_file():
                raise ValueError(str(outcome.get("summary") or "mockup ausente"))
            note = _note(out["json"])
            if not out["md"].is_file():
                raise ValueError("falta la nota de la dirección")
            if not d.get("iterated_from") and not all(Path(f"{out['html']}.candidate-{i}.html").is_file() for i in (1, 2)):
                raise ValueError("faltan las miniaturas de las dos candidatas")
            d.update(status="ready", name=note["name"], axes=note["axes"], sha256=_digest(out["html"]),
                     note_sha256=_digest(out["md"]), json_sha256=_digest(out["json"]), tsx_sha256=drafts._sha(out["tsx"]))
        except (OSError, ValueError, TypeError) as exc:
            d.update(status="failed", error=str(exc)[:400])
    if any(d["status"] in ("queued", "drafting") for d in entry["directions"]):
        return
    ready = [d for d in entry["directions"] if d["status"] == "ready"]
    iterated = entry.get("iterate_from")
    if iterated and ready and not unchanged(rdir, ref, iterated):
        ready[0].update(status="failed", error="se modificó la revisión anterior; las revisiones son inmutables")
        ready = []
    if not ready:
        error = "Ninguna dirección terminó correctamente."
        if iterated:
            error = (f"La iteración de la dirección {iterated['id'].upper()} no produjo una versión válida: "
                     + str(entry["directions"][0].get("error") or "sin resultado"))[:400]
        entry.update(status="failed", finished=drafts._now(), error=error)
        entry["failures"] = int(entry.get("failures") or 0) + 1
        drafts._event(rdir, "Designer", f"{ref}: " + ("falló la iteración" if iterated else "fallaron todas las direcciones"), entry)
        return
    entry.update(status="choosing", finished=drafts._now())
    entry["comparison"] = compare(rdir, ref, ready)
    # the comments the batch was given are applied, by an exploration as by an iteration: left pending, the next request
    # (moving the focus, D-146) took them for new ones and explored again over directions the owner was about to choose
    # between (pictures REQ-021 SP-5, 2026-10-29)
    for f in entry.get("feedback", []):
        if (f.get("id") or f["when"]) in entry.get("feedback_batch", []) and not f.get("consumed"):
            f["consumed"] = ready[0]["delegation"]
    if not iterated:
        drafts._event(rdir, "Designer", f"{ref}: direcciones listas para comparar y elegir", entry)
        return
    entry.pop("iterate_from")
    entry["failures"] = 0
    drafts._event(rdir, "Designer", f"{ref}: dirección {ready[0]['id'].upper()} iterada", entry)


def compare(rdir: Path, ref: str, directions: list[dict]) -> dict:
    import bt_design_drafts as drafts
    tool = drafts.KIT / "compare_directions.py"
    paths = [files(rdir, ref, d["revision"], d["id"])["html"] for d in directions]
    try:
        proc = subprocess.run(["uv", "run", "--offline", "--with", "playwright", "python", str(tool),
                               *map(str, paths), "--json"], cwd="/tmp", capture_output=True, text=True, timeout=120,
                              env={**os.environ, "UV_OFFLINE": "1"}, check=False)
        report = json.loads(proc.stdout)
        if not isinstance(report, dict) or report.get("ok") is not True or proc.returncode:
            if report.get("error"):
                reason = report["error"]
            elif report.get("evidence_ok") is False:
                reason = ("Alguna dirección declara rasgos que no se ven en su mockup: "
                          + "; ".join(report.get("missing_evidence") or [])[:300])
            else:
                reason = "Las direcciones son demasiado similares."
            return {"ok": False, "error": reason, "report": report}
        return report
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": f"Comparación no ejecutada: {str(exc)[:300]}"}


def preview(rdir: Path, ref: str, key: str, revision: int | None = None) -> Path | None:
    import bt_design_drafts as drafts
    if not drafts._REF.fullmatch(ref or "") or key not in ("a", "b", "c"):
        return None
    entry = drafts._load(rdir)["drafts"].get(ref, {})
    rev = revision or entry.get("attempt")
    if not isinstance(rev, int) or rev < 1:
        return None
    out = files(rdir, ref, rev, key)["html"]
    return out if out.is_file() else None


def choose(project: str, rdir: Path, ref: str, key: str, via: str) -> str:
    import bt_delegate
    import bt_design_drafts as drafts
    if not drafts.planning(rdir):
        raise SystemExit("El plan ya no está en planificación.")
    with drafts._locked(rdir) as data:
        entry = data["drafts"].get(ref)
        if not entry or entry.get("status") != "choosing":
            raise SystemExit("No hay direcciones pendientes de elección.")
        row = next((s for s in drafts.subplans(rdir) if s["ref"] == ref), None)
        if row is None:
            raise SystemExit("Contrato de interfaz no válido.")
        chosen = next((d for d in entry["directions"] if d["id"] == key and d["status"] == "ready"), None)
        if chosen is None:
            raise SystemExit("Esa dirección no está lista.")
        if not choosable(ref, entry, chosen):
            raise SystemExit("La comparación de direcciones no pasa; hay que rehacerlas.")
        if any(d["status"] == "ready" and not unchanged(rdir, ref, d) for d in entry["directions"]):
            raise SystemExit("Una dirección cambió después de la comparación; hay que rehacerla.")
        out = files(rdir, ref, chosen["revision"], key)
        md, html = drafts.paths(rdir, ref)
        brief = f"""Finalise the owner's chosen direction {chosen['name']} ({key}) for {ref}.
Read SPEC.md, PLAN.json, {Path(rdir) / 'design' / entry['behavior']}, {out['md']} and {out['html']}.
The owner chose this direction via {via}; preserve its composition and motion. Write ONLY {md} (complete twelve-section
behavioural and visual contract, draft) and {html}. If source {out['tsx']} exists, rebuild it with the CURRENT offline
builder into {html}, retaining its visual composition; this incorporates runtime fixes without editing the exploration.
Otherwise copy its self-contained HTML and explicitly report fallback/toolchain concerns. Change only verified
behavioural defects. Name components as source:id variant state. Read the Designer's david-ui-kit skill.
Run contrast.py and the offline audit on {html}. Report the actual RESULT or AUDIT NOT RUN in CONCERNS.
Do not edit any exploration, history, SPEC, PLAN or production file. Do not approve the contract.
"""
        if drafts.behind(entry, row):        # the plan changed after the directions were drawn: fold it in (D-162)
            brief += _plan_change(project, rdir, ref, row, entry, chosen)
        order = bt_delegate.create(project, brief, None, None, Path(rdir), [], None, drafts.TIMEOUT_MIN,
                                   None, None, kind="design", role="designer")
        entry.update(chosen=key, phase="finalise", status="drafting", delegation=order["id"],
                     continuation_choice=None,
                     before=drafts._sha(md), before_html=drafts._sha(html), selected_sha256=chosen["sha256"],
                     started=drafts._now())
        drafts._event(rdir, "Tú → Designer", f"{ref}: elegida dirección {key.upper()} · {chosen['name']}", entry)
    try:
        bt_delegate.start_background(order["id"])
    except (SystemExit, Exception) as exc:
        with drafts._locked(rdir) as data:
            data["drafts"][ref].update(status="failed", error=str(exc)[:400])
        raise SystemExit(f"No se pudo finalizar la dirección: {exc}") from exc
    return f"Dirección {key.upper()} elegida; el Designer está finalizando el contrato."


def _plan_change(project: str, rdir: Path, ref: str, row: dict, entry: dict, chosen: dict) -> str:
    """The plan delta since the directions were drawn, for the finalise brief; the entry then follows the current brief
    (pictures REQ-021 SP-12, 2026-10-29: one engineering sentence in a UI task's objective discarded three directions
    awaiting the owner's choice and started three new explorations)."""
    import bt_design_amend
    import bt_design_brief_diff as brief_diff
    change = bt_design_amend.delta(project, rdir, row, entry)
    behavior = Path(rdir) / "design" / f"{ref}.r{chosen['revision']}.chosen.behavior.md"
    behavior.write_text(change["new"], encoding="utf-8")
    previous = change["previous_path"] or "(not recorded: check the whole contract against the new brief)"
    entry.update(behavior=behavior.name, digest=row["digest"], ui_digest=row["ui_digest"])
    return f"""
PLAN CHANGE. The plan changed after these directions were drawn. The direction was drawn from {previous}; the current
UI brief is {behavior}. Mechanical diff, previous → new (+ added, - removed, ~ changed):
{brief_diff.render(change['changes'])}
Fold ONLY this delta into the contract and the mockup; keep the chosen composition, navigation, motion and tokens.
"""


def _settle_final(rdir: Path, ref: str, entry: dict) -> None:
    import bt_design_drafts as drafts
    if entry.get("status") != "drafting":
        return
    outcome = _outcome(entry["delegation"])
    if outcome.get("status") in SUCCESS:
        html = drafts.paths(rdir, ref)[1]
        digest = drafts._sha(html)
        if not digest or (digest == entry.get("before_html") and digest != entry.get("selected_sha256")):
            entry.update(status="failed", error="La finalización no escribió el mockup elegido.", finished=drafts._now())
            return
    elif outcome.get("status") != "running_or_pending":
        entry.update(status="failed", error=str(outcome.get("summary") or "No se pudo finalizar el contrato."),
                     finished=drafts._now())
        return
    # Reuse the canonical contract validation and history writer without recursing into exploration settlement.
    phase = entry.pop("phase")
    try:
        drafts._settle(rdir, ref, entry)
    finally:
        entry["phase"] = phase
    if entry.get("status") == "ready":
        for f in entry.get("feedback", []):
            if (f.get("id") or f["when"]) in entry.get("feedback_batch", []):
                f["consumed"] = entry["delegation"]
