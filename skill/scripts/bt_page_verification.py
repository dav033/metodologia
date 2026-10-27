"""The owner's checkpoint after each subplan, as web pieces (data in `bt_verification`).

- `panel`: the «Probar» tab of a subplan in the Plan tab: where to try it (local, production, elsewhere), what to look
  for, and, once the engine has published a version, the actions (open that exact version locally, approve, reject) with
  the revert command and the subplans that depend on it;
- `run_card`: every subplan's state on the run page and on the plan detail, linking to each «Probar» tab;
- `chip`: «por probar N» for the Plan tab bar.

Pure functions: HTML out, no writes. The actions post to `/p/<project>/req/<REQ>/verify-*` (see `bt_server`).
"""
from __future__ import annotations

from html import escape as e
from pathlib import Path
from urllib.parse import quote, urlencode

import bt_verification as verification
from bt_pages import inline, purl

PILL = {"waiting": "none", "to_test": "warn", "approved": "ok", "rejected": "bad", "outdated": "warn"}
KIND_ICON = {"local": "⌂", "production": "◎", "external": "↗", "none": "–"}


def _link(rid_url: str, sp: str) -> str:
    return rid_url + "?" + urlencode({"tab": "plan", "mode": "subplans", "view": "verify", "sp": sp})


def _state_pill(state: str) -> str:
    return f'<span class="pp-vstate {PILL.get(state, "none")}">{e(verification.STATES_ES.get(state, state))}</span>'


def _text(value: str) -> str:
    """Cell text: code spans and bare URLs become clickable; everything else is escaped."""
    import re
    out = inline(value)
    return re.sub(r'(https?://[^\s<)]+)', r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>', out)


def _form(ctx: dict, action: str, label: str, sp: str, *, cls: str = "", note: bool = False, danger: bool = False) -> str:
    field = ('<textarea name="comments" rows="3" required placeholder="Qué falló o qué esperabas ver"></textarea>' if note else "")
    return (f'<form method="post" action="{purl(ctx["project"], "req", ctx["rid"], action)}" class="pp-vform{" note" if note else ""}">'
            f'<input type="hidden" name="token" value="{e(ctx["token"])}"><input type="hidden" name="anchor" value="{e(sp)}">'
            f'{field}<button type="submit" class="{e(cls)}{" danger" if danger else ""}">{e(label)}</button></form>')


def _where(rows: list[dict]) -> str:
    if not rows:
        return ('<div class="pp-vmissing"><strong>Falta «cómo probarlo»</strong><p class="pp-meta">El Planner debe escribir una '
                'fila para este subplan en <code>## Pruebas</code> del SPEC: dónde se prueba, cómo y qué deberías ver. '
                'Sin ella el subplan no se puede confirmar.</p></div>')
    cards = []
    for r in rows:
        place = f'<span class="pp-meta">{e(r["where"])}</span>' if r["kind"] == "external" else ""
        how = f'<div><span class="pp-vlabel">Cómo</span><p>{_text(r["how"])}</p></div>' if r["how"] else ""
        expect = f'<div><span class="pp-vlabel">Qué debes ver</span><p>{_text(r["expect"])}</p></div>' if r["expect"] else ""
        cards.append(f'<article class="pp-vwhere {e(r["kind"])}"><header><span class="pp-vicon" aria-hidden="true">'
                     f'{KIND_ICON[r["kind"]]}</span><strong>{e(verification.KINDS_ES[r["kind"]])}</strong>{place}</header>'
                     f'{how}{expect}</article>')
    return '<div class="pp-vwheres">' + "".join(cards) + "</div>"


def _actions(ctx: dict, row: dict) -> str:
    sid, root, rdir = row["id"], ctx.get("root"), ctx["rdir"]
    dec = row["decision"] or {}
    note = (f'<p class="pp-meta">Tu nota: «{e(dec.get("note") or "")}»</p>'
            if row["state"] == "rejected" and dec.get("note") else "")
    opened = ""
    try:
        target = verification.workdir(root, ctx["project"], verification._req(rdir), sid, row["version"]) if root else None
    except Exception:  # noqa: BLE001 - a missing home directory must not break the page
        target = None
    if target is not None and target.exists():
        opened = (f'<p class="pp-vpath">Abierta en <code>{e(str(target))}</code></p>' + _form(ctx, "verify-close", "Cerrar la copia", sid))
    buttons = (_form(ctx, "verify-open", "Abrir esta versión en local", sid) if not opened else "") + \
        _form(ctx, "verify-approve", "Aprobar" if row["state"] != "approved" else "Aprobado ✓", sid, cls="pp-approve") + \
        f'<details class="pp-vreject"><summary>Rechazar…</summary>{_form(ctx, "verify-reject", "Rechazar con esta nota", sid, note=True, danger=True)}</details>'
    command = verification.revert_command(root, ctx["project"], rdir, sid) if root else ""
    deps = verification.dependents(rdir, sid)
    undo = (f'<p>Esta versión empieza en un commit propio, así que se puede deshacer solo ese tramo:</p>'
            f'<pre><code>{e(command)}</code></pre>' if command else
            '<p class="pp-meta">No encuentro el tramo de este subplan en el repo.</p>')
    warn = (f'<p class="pp-vwarn">Ojo: {e(", ".join(deps))} se construye sobre este subplan; deshacerlo solo dejaría el '
            f'resto sin base. Revierte también esos o apruébalo.</p>' if deps else "")
    revert = (f'<details class="pp-vrevert"><summary>Cómo deshacer este subplan</summary>{undo}{warn}'
              f'<p class="pp-meta">Solo se muestra el comando: la web nunca revierte ni toca <code>main</code>.</p></details>')
    return f'<div class="pp-vactions">{note}{opened}<div class="pp-vbuttons">{buttons}</div>{revert}</div>'


def panel(ctx: dict, s: dict) -> str:
    rdir = ctx["rdir"]
    st = verification.state(rdir)
    row = next((r for r in st["subplans"] if r["id"] == s["id"]), None)
    where = _where(verification.tests_for(rdir, s["id"]))
    if not st["applies"] or row is None:
        head = ('<p class="pp-vintro">Cuando este subplan termine de construirse, aquí podrás abrir esa versión, probarla y '
                'aprobarla o rechazarla. El plan no se da por terminado hasta que apruebes todos los subplanes.</p>')
        return f'<section class="pp-verify">{head}<h3>Dónde probarlo</h3>{where}</section>'
    if row["state"] == "waiting":
        head = f'<p class="pp-vintro">{_state_pill("waiting")} Todavía no hay una versión de este subplan para probar.</p>'
        return f'<section class="pp-verify">{head}<h3>Dónde probarlo</h3>{where}</section>'
    stale = ('<p class="pp-vwarn">El motor publicó una versión nueva después de tu decisión: vuelve a probarla.</p>'
             if row["state"] == "outdated" else "")
    head = (f'<p class="pp-vintro">{_state_pill(row["state"])} Versión {e(str(row["version"]))} · commit '
            f'<code>{e(str(row["commit"])[:10])}</code>. Es el árbol integrado exactamente al terminar este subplan.</p>{stale}')
    return f'<section class="pp-verify">{head}<h3>Dónde probarlo</h3>{where}{_actions(ctx, row)}</section>'


def tab_label(rdir: Path) -> str:
    st = verification.state(rdir)
    if not st["applies"]:
        return "Probar"
    left = st["total"] - st["approved"]
    return f"Probar · {st['approved']}/{st['total']}" if left else "Probar ✓"


def chip(rdir: Path) -> str:
    st = verification.state(rdir)
    if not st["applies"]:
        return ""
    waiting = st["counts"]["to_test"] + st["counts"]["outdated"] + st["counts"]["rejected"]
    cls = "warn" if waiting else "ok" if st["approved"] == st["total"] else ""
    text = f"por probar {waiting}" if waiting else f"aprobados {st['approved']}/{st['total']}"
    return f'<span class="pp-chip {cls}">{e(text)}</span>'


def run_card(project: str, rid: str, rdir: Path) -> str:
    """Every subplan with its state and a link to its «Probar» tab (empty when the run does not report subplans)."""
    st = verification.state(rdir)
    if not st["applies"]:
        return ""
    base = purl(project, "req", rid)
    rows = "".join(
        f'<a class="pp-vrow" href="{e(_link(base, r["id"]))}"><span class="pp-id">{e(r["id"])}</span>'
        f'<span class="grow">{e(r["title"])}</span>{_state_pill(r["state"])}</a>' for r in st["subplans"])
    closed = st["approved"] == st["total"]
    lead = ("Todos los subplanes están aprobados: ya puedes fusionar en Revisar." if closed else
            f"El plan no está terminado hasta que pruebes y apruebes cada subplan ({st['approved']}/{st['total']}).")
    return (f'<section class="pp-vcard" aria-label="Verificación por subplan"><header><h3>Verificación por subplan</h3>'
            f'<p class="pp-meta">{e(lead)}</p></header>{rows}</section>')
