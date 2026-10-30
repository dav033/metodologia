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
    return re.sub(r'(https?://[^\s<)]*[^\s<).,;:!?])', r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>', out)


def _form(ctx: dict, action: str, label: str, sp: str, *, cls: str = "", note: bool = False, danger: bool = False,
          blank: bool = False, path: bool = False, login: bool = False) -> str:
    field = ('<textarea name="comments" rows="3" required placeholder="Qué falló o qué esperabas ver"></textarea>' if note else "")
    target = ' target="_blank" rel="noopener"' if blank else ""
    page = '<input type="hidden" name="path" value="/">' if path else ""     # the page the new tab lands on (D-200)
    page += '<input type="hidden" name="login" value="1">' if login else ""   # start it as in production (D-202)
    return (f'<form method="post" action="{purl(ctx["project"], "req", ctx["rid"], action)}" class="pp-vform{" note" if note else ""}"{target}>'
            f'<input type="hidden" name="token" value="{e(ctx["token"])}"><input type="hidden" name="anchor" value="{e(sp)}">'
            f'{page}{field}<button type="submit" class="{e(cls)}{" danger" if danger else ""}">{e(label)}</button></form>')


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
        items = "".join(f'<li><a href="{e(origin.group(0) + p)}" target="_blank" rel="noopener">{e(origin.group(0) + p)} ↗</a></li>'
                        for p in paths)
        lead = "La versión está en marcha. Páginas que hay que probar (se abren sin reiniciarla):"
    else:
        items = "".join(f"<li><code>{e(p)}</code></li>" for p in paths)
        lead = "Páginas que hay que probar; se vuelven enlaces cuando la versión está en marcha:"
    return f'<div class="pp-vurls"><span class="pp-vlabel">URLs a probar</span><p class="pp-meta">{lead}</p><ul>{items}</ul></div>'


_SAID = {"ready": ("ok", "En marcha: responde."), "preparing": ("warn", "Arrancando…"),
         "failed": ("bad", "Falló al arrancar."), "stopped": ("none", "Detenida.")}


def _servers(ctx: dict, row: dict, paths: list[str]) -> str:
    """Where to try the version: its URL and the pages its test names, every one a plain link to the real address. A click
    on a link opens that page; when the version is not running (or failed) the click first stops everything of the
    version and starts it clean from its commit, and the new tab lands on that same page once every server answers.
    «Reiniciar desde cero» forces the clean restart. Owner, 2026-10-30: «en vez del botón de probar debe darme el link a
    la URL donde probarlo y que me abra la URL en el navegador… y las URLs específicas de la solución» (D-200)."""
    import bt_verify_servers as servers
    if servers.recipe(ctx["root"], ctx["project"], ctx["rdir"]) is None:
        return ""
    now = _running(ctx, row)
    plan = servers.planned(ctx["root"], ctx["project"], ctx["rdir"], row["id"])
    url = now.get("url") if now["state"] in ("ready", "preparing") and now.get("url") else plan["url"]
    ports = now.get("ports") if now["state"] in ("ready", "preparing") and now.get("ports") else plan["ports"]
    ctx["_url"] = url
    form_id = f"vstart-{row['id']}"
    start = _form(ctx, "verify-run", "Reiniciar desde cero", row["id"], cls="secondary", blank=True, path=True).replace(
        "<form ", f'<form id="{e(form_id)}" ', 1)
    stop = _form(ctx, "verify-stop", "Detener servidores", row["id"], cls="secondary") if now["state"] in ("ready", "preparing") else ""
    data = servers.recipe(ctx["root"], ctx["project"], ctx["rdir"])
    signed = ""
    if servers.has_local_auth(data):                  # D-202: enter already signed in; «con login» for accounts and roles
        running = now["state"] in ("ready", "preparing")
        with_login = running and now.get("login", True)
        signed = ('<p class="pp-meta"><strong>' + ("Con login: entra con una cuenta de prueba." if with_login else
                  "Sin login: entras ya como administrador local.") + "</strong> " +
                  ("Para probar con una cuenta o un rol concretos usa «Reiniciar con login»." if not with_login else
                   "«Reiniciar sin login» vuelve a entrar ya autenticado.") + "</p>")
        other = (_form(ctx, "verify-run", "Reiniciar sin login", row["id"], cls="secondary", blank=True, path=True)
                 if with_login else
                 _form(ctx, "verify-run", "Reiniciar con login (roles)", row["id"], cls="secondary", blank=True, path=True,
                       login=True))
        stop = other + stop
    cls, said = _SAID.get(now["state"], _SAID["stopped"])
    if now["state"] == "failed" and now.get("step"):
        said += " " + now["step"]
    origin = (re.match(r"https?://[^/]+", url or "") or [""])[0]
    pages = ["/"] + [p for p in paths if p != "/"]
    web = (re.search(r":(\d+)", url or "") or [None, ""])[1]
    links = link_items(origin, web, pages, form_id)
    session = servers.session_name(ctx["project"], ctx["rdir"], row["id"], row["version"])
    port_list = ", ".join(f"{n} {p}" for n, p in (ports or {}).items())
    remote = remote_help(web)
    how = ("Está en marcha: cada enlace se abre directamente." if now["state"] == "ready" else
           "Al abrir un enlace detengo todo lo de esta versión (sesión <code>" + e(session) + "</code> y sus procesos; nunca los "
           "de otra versión ni otros servicios), la arranco desde cero en el commit <code>" + e(str(row["commit"])[:10]) +
           "</code> (" + e(port_list) + ") y la pestaña nueva llega a esa página cuando responde.")
    return (f'<div class="pp-vtry" data-state="{e(now["state"])}"><span class="pp-vlabel">Dónde probarlo</span>'
            f'<ul class="pp-vlinks">{links}</ul><p class="pp-vstatus {cls}" role="status">{e(said)}</p>'
            f'<p class="pp-meta">{how}</p>{signed}<div class="pp-vtry-row">{start}{stop}</div>{remote}</div>')


def tunnel_command(port: str) -> str:
    """The SSH bridge from the owner's own computer to this machine's port, through AdvIn's reverse tunnel (the way the
    owner reaches the panel); `BITACORA_TUNNEL_TARGET` in the panel's environment changes the destination."""
    import os
    target = os.environ.get("BITACORA_TUNNEL_TARGET") or DEFAULT_TUNNEL_TARGET
    return f"ssh -N -L {port}:127.0.0.1:{port} {target}"


DEFAULT_TUNNEL_TARGET = "-J root@185.147.157.25 -p 2222 david@127.0.0.1"


def opener_url(port: str, page: str) -> str:
    """`bitacora://open/?port=…&path=…`: the Windows opener (assets/bitacora-opener.ps1) bridges the port over SSH when it
    is not open yet and opens http://localhost:<port><page> in that computer's browser."""
    return f"bitacora://open/?port={quote(str(port))}&path={quote(page, safe='/')}"


def link_items(origin: str, port: str, pages: list[str], form_id: str) -> str:
    """One row per page: the plain link (this machine, or a computer whose bridge is open), «en mi computador» (the
    opener: bridge and browser on the owner's computer) and the bridge command to copy. Owner, 2026-10-30, working from
    a Windows computer through an SSH tunnel: «al lado de cada link salga el comando para hacer el puente por ssh… y que
    se mande el comando en el computador que estoy usando» (D-201)."""
    if not origin:
        return ""
    command = tunnel_command(port) if port else ""
    rows = []
    for p in pages:
        mine = (f' <a class="pp-vwin" href="{e(opener_url(port, p))}" data-vstart="{e(form_id)}" data-path="{e(p)}" '
                f'title="Abre el puente SSH (si falta) y la página en el computador que estás usando">en mi computador ↗</a>'
                f' <button type="button" class="pp-vcopy secondary" data-copy="{e(command)}" title="{e(command)}">copiar puente</button>'
                if port else "")
        rows.append(f'<li><a class="pp-vurl" href="{e(origin + p)}" target="_blank" rel="noopener" data-vstart="{e(form_id)}"'
                    f' data-path="{e(p)}">{e(origin + p)}</a>{mine}</li>')
    return "".join(rows)


def remote_help(port: str) -> str:
    """The bridge for every link of the version, and the one-time opener for Windows."""
    if not port:
        return ""
    return (f'<div class="pp-vremote"><span class="pp-vlabel">Desde otro computador</span><p class="pp-meta">Puente SSH '
            f'(en una terminal de ese computador): <code>{e(tunnel_command(port))}</code></p><p class="pp-meta">«en mi '
            f'computador ↗» lo hace solo en Windows: instala una vez el abridor (<a href="/static/bitacora-opener.ps1" '
            f'download>bitacora-opener.ps1</a>; en PowerShell: <code>powershell -ExecutionPolicy Bypass -File '
            f'bitacora-opener.ps1</code>). Desde entonces el enlace abre el puente (si falta) y la página en tu navegador.</p>'
            f'</div>')


def _guide(ctx: dict, row: dict, url: str) -> str:
    """«Cómo probarlo»: the steps of `bt_verify_guide`, each with what to do and what to see."""
    import bt_verify_guide as guides
    import bt_verify_servers as servers
    copy = verification.workdir(ctx["root"], ctx["project"], verification._req(ctx["rdir"]), row["id"], row["version"]) \
        if ctx.get("root") and row.get("version") else None
    g = guides.guide(ctx.get("root") or Path("."), ctx["project"], ctx["rdir"], row["id"], url=url, copy=copy,
                     recipe=servers.recipe(ctx["root"], ctx["project"], ctx["rdir"]) if ctx.get("root") else None)
    if not g["steps"]:
        return ""
    parts = ['<div class="pp-vguide"><h3>Cómo probarlo</h3>']
    if g["before"] or g["done"]:
        items = "".join(f"<li>{_text(b)}</li>" for b in g["before"]) + "".join(f"<li>{_text(d)}</li>" for d in g["done"])
        parts.append(f'<div><span class="pp-vlabel">Antes</span><ul>{items}</ul></div>')
    if g["dev"]:
        parts.append('<p class="pp-meta">Donde el plan dice <code>npm run dev</code>: no hace falta, «Probar» ya arranca '
                     'los servidores de esta versión.</p>')
    if g["accounts"]:
        who = ", ".join(f"<code>{e(a)}</code>" for a in g["accounts"])
        parts.append(f'<p><span class="pp-vlabel">Cuentas</span>{who}' +
                     (f' — {_text(g["password"])}' if g["password"] else "") + "</p>")
    steps = "".join(f'<li><p>{_text(s["do"])}</p>' + (f'<p class="pp-vexpect"><strong>Debes ver:</strong> {_text(s["expect"])}</p>'
                                                         if s["expect"] else "") + "</li>" for s in g["steps"])
    parts.append(f'<ol class="pp-vsteps">{steps}</ol>')
    if g["more"]:
        parts.append(f'<p class="pp-meta">Y {g["more"]} pasos más en el plan (abajo, «Texto del plan»).</p>')
    if g["expect"]:
        parts.append('<div><span class="pp-vlabel">Qué debes ver</span><ul>' +
                     "".join(f"<li>{_text(x)}</li>" for x in g["expect"]) + "</ul></div>")
    if g["commands"]:
        parts.append(f'<p class="pp-meta">Para los comandos, abre una terminal con el entorno de esta versión: '
                     f'<code>{e(g["commands"])}</code></p>')
    if g["design"]:
        ref = e(g["design"]["ref"])
        link = (f'<a href="{purl(ctx["project"], "doc", *g["design"]["doc"].split("/"))}" target="_blank" rel="noopener">{ref}</a>'
                if g["design"]["doc"] else f"<code>{ref}</code>")
        parts.append(f'<p class="pp-meta">Compara lo que ves con el diseño aprobado: {link}.</p>')
    parts.append(f'<p class="pp-meta">Pasos tomados de <code>{e(g["source"])}</code>.</p></div>')
    return "".join(parts)


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
    run = ctx.get("_try", "")
    buttons = (_form(ctx, "verify-open", "Abrir esta versión en local", sid) if not opened and not run else "") + \
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
    paths = test_paths(rows)
    ctx["_try"] = run = _servers(ctx, row, paths) if ctx.get("root") else ""
    guide = _guide(ctx, row, ctx.get("_url", ""))
    if guide and all(r["kind"] == "local" for r in rows):            # the guide says it; the plan's text stays one click away
        where = f'<details class="pp-vplan"><summary>Texto del plan</summary>{where}</details>'
    else:
        where = f"<h3>Dónde probarlo</h3>{where}"
    return f'<section class="pp-verify">{head}{run}{guide}{"" if run else _urls(ctx, row, paths)}{where}{_actions(ctx, row)}</section>'


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
