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
import re
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


def _form(ctx: dict, action: str, label: str, sp: str, *, cls: str = "", note: bool = False, danger: bool = False,
          blank: bool = False) -> str:
    field = ('<textarea name="comments" rows="3" required placeholder="Qué falló o qué esperabas ver"></textarea>' if note else "")
    target = ' target="_blank" rel="noopener"' if blank else ""
    return (f'<form method="post" action="{purl(ctx["project"], "req", ctx["rid"], action)}" class="pp-vform{" note" if note else ""}"{target}>'
            f'<input type="hidden" name="token" value="{e(ctx["token"])}"><input type="hidden" name="anchor" value="{e(sp)}">'
            f'{field}<button type="submit" class="{e(cls)}{" danger" if danger else ""}">{e(label)}</button></form>')


def _running(ctx: dict, row: dict) -> dict:
    """The version's test servers, asked once per page (they are probed over HTTP)."""
    import bt_verify_servers as servers
    cache = ctx.setdefault("_verify_servers", {})
    if row["id"] not in cache:
        cache[row["id"]] = servers.status(ctx["root"], ctx["project"], ctx["rdir"], row["id"])
    return cache[row["id"]]


# The pages a test row names: full local URLs and bare paths such as /3d or /proyectos (owner, 2026-10-29: «necesito que
# salgan la url y las urls específicas que hay que probar»). Navigation through menus stays in «Cómo».
_FULL_URL = re.compile(r"https?://(?:localhost|127\.0\.0\.1)(?::\d+)?(/[^\s`)|,;»\"']*)?")
_BARE_PATH = re.compile(r"(?<![\w/.:@-])(/[a-z0-9][a-z0-9_\-]*(?:/[a-z0-9_\-\[\]]+)*)(?![\w.@/])")


def test_paths(rows: list[dict]) -> list[str]:
    found: list[str] = []
    for r in rows:
        text = f"{r.get('how') or ''} {r.get('expect') or ''}"
        rest = _FULL_URL.sub(lambda m: found.append((m.group(1) or "/").rstrip(".")) or " ", text)
        found += [m.group(1) for m in _BARE_PATH.finditer(rest)]
    return list(dict.fromkeys(found))


def _urls(ctx: dict, row: dict, paths: list[str]) -> str:
    if not paths:
        return ""
    now = _running(ctx, row) if ctx.get("root") and row["state"] != "waiting" else {"state": "stopped", "url": ""}
    origin = re.match(r"https?://[^/]+", now.get("url") or "")
    if now["state"] == "ready" and origin:
        port = origin.group(0).rsplit(":", 1)[-1]
        items = "".join(f'<li><a href="{e(origin.group(0) + p)}" target="_blank" rel="noopener" data-vport="{e(port)}" '
                        f'data-vpath="{e(p)}" data-vsuffix=" ↗">{e(origin.group(0) + p)} ↗</a></li>' for p in paths)
        lead = (f"La versión está en marcha (puerto {e(port)}); los enlaces pasan por el panel, así que funcionan también "
                f"por el túnel SSH. Páginas que hay que probar:")
    else:
        items = "".join(f"<li><code>{e(p)}</code></li>" for p in paths)
        lead = "Páginas que hay que probar; se vuelven enlaces cuando la versión está en marcha («Probar esta versión»):"
    return f'<div class="pp-vurls"><span class="pp-vlabel">URLs a probar</span><p class="pp-meta">{lead}</p><ul>{items}</ul></div>'


def _servers(ctx: dict, row: dict) -> str:
    """«Probar esta versión»: start its test servers and open it in a new tab; while they run, the link and «Detener»."""
    import bt_verify_servers as servers
    if servers.recipe(ctx["root"], ctx["project"]) is None:
        return ""
    now = _running(ctx, row)
    if now["state"] == "stopped":
        return _form(ctx, "verify-run", "Probar esta versión ↗", row["id"], cls="pp-approve", blank=True)
    found = re.match(r"https?://[^/:]+:(\d+)(/.*)?$", now.get("url") or "")
    link = (f'<a class="pp-vopen" href="{e(now["url"])}" target="_blank" rel="noopener" data-vport="{found.group(1)}" '
            f'data-vpath="{e(found.group(2) or "/")}" data-vprefix="Abrir " data-vsuffix=" ↗">Abrir {e(now["url"])} ↗</a>'
            if now["state"] == "ready" and found else
            f'<a class="pp-vopen" href="{purl(ctx["project"], "req", ctx["rid"], "verify-run")}?sp={e(row["id"])}" '
            f'target="_blank" rel="noopener">Preparando… ↗</a>')
    return link + _form(ctx, "verify-stop", "Detener servidores", row["id"])


def _where(rows: list[dict]) -> str:
    if not rows:
        return ('<div class="pp-vmissing"><strong>Falta «cómo probarlo»</strong><p class="pp-meta">El Planner debe escribir una '
                'fila para este subplan en <code>## Pruebas</code> del SPEC: dónde se prueba, cómo y qué deberías ver. '
                'Sin ella el subplan no se puede confirmar.</p></div>')
    cards = []
    for r in rows:
        place = f'<span class="pp-meta">{e(r["where"])}</span>' if r["kind"] == "external" else ""
        ports = sorted({int(port) for port in re.findall(
            r'(?<![\w.-])https?://(?:localhost|127\.0\.0\.1):([0-9]{1,5})(?![0-9])',
            f'{r["how"]} {r["expect"]}') if 1 <= int(port) <= 65535}) if r["kind"] == "local" else []
        access = ""
        if ports:
            labels = ", ".join(str(port) for port in ports)
            example = ports[0]
            access = (f'<p class="pp-vpath"><strong>Puerto indicado para la prueba: {labels}.</strong> '
                      f'Abrir la copia no inicia la aplicación; sigue las instrucciones de abajo. '
                      f'Si te conectas desde otro computador, crea un túnel SSH '
                      f'<code>ssh -L {example}:127.0.0.1:{example} usuario@servidor</code> '
                      f'y abre <code>http://localhost:{example}</code> en tu navegador.</p>')
        how = f'<div><span class="pp-vlabel">Cómo</span><p>{_text(r["how"])}</p></div>' if r["how"] else ""
        expect = f'<div><span class="pp-vlabel">Qué debes ver</span><p>{_text(r["expect"])}</p></div>' if r["expect"] else ""
        cards.append(f'<article class="pp-vwhere {e(r["kind"])}"><header><span class="pp-vicon" aria-hidden="true">'
                     f'{KIND_ICON[r["kind"]]}</span><strong>{e(verification.KINDS_ES[r["kind"]])}</strong>{place}</header>'
                     f'{access}{how}{expect}</article>')
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
    run = _servers(ctx, row) if root and row["state"] != "waiting" else ""
    buttons = run + (_form(ctx, "verify-open", "Abrir esta versión en local", sid) if not opened and not run else "") + \
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
    rows = verification.tests_for(rdir, s["id"])
    where = _where(rows)
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
    return f'<section class="pp-verify">{head}<h3>Dónde probarlo</h3>{where}{_urls(ctx, row, test_paths(rows))}{_actions(ctx, row)}</section>'


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
