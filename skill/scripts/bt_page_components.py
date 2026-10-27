"""`/components`: the Designer's component kits for the owner to browse. Pure functions: kit data in, HTML out.

The main page shows the REAL libraries (shadcn/ui on Base UI, Animate UI, Bencho, React Bits) from `real/manifest.json`
merged with the last workspace build; `/components/kit` shows the plain-HTML fallback kit. The page is the trusted shell
(dashboard CSP, no inline script); every preview is a sandboxed frame (`/components/live/<id>`, `/components/frame/<id>`,
references), so the components' CSS never meets the dashboard's and real media queries apply to the width switch. Text
comes only from the skill's files and the built workspace and is always escaped."""
from __future__ import annotations

from html import escape as e

import bt_kit
from bt_pages import layout

SOURCE = dict(bt_kit.SOURCES)
STATUS = {"done": "hecho", "gap": "brecha"}
TYPE = {"base": "base", "capability": "capacidad", "new-capability": "capacidad nueva", "variant": "variante",
        "presentation": "presentación"}

FRAME_CSS = """body { min-height: 0; }
.kit-frame { display: flex; flex-direction: column; gap: calc(var(--spacing) * 10); padding: calc(var(--spacing) * 6); }
.kit-example { display: flex; flex-direction: column; gap: calc(var(--spacing) * 3); min-width: 0; }
.kit-example-title { color: var(--muted-foreground); font-size: var(--text-xs); font-weight: 500; }
@media (max-width: 640px) { .kit-frame { padding: calc(var(--spacing) * 4); gap: calc(var(--spacing) * 8); } }"""

# tells the gallery how tall the frame is (sandboxed: only postMessage crosses); kit.js applies theme/motion messages
FRAME_JS = """(function () {
  function size() { try { parent.postMessage({ kit: 'height', h: document.documentElement.scrollHeight }, '*'); } catch (e) {} }
  if (window.ResizeObserver) new ResizeObserver(size).observe(document.body);
  window.addEventListener('load', size); new MutationObserver(size).observe(document.documentElement, { attributes: true });
  size();
})();"""


def _seg(kind: str, label: str, options: tuple[tuple[str, str], ...], current: str) -> str:
    buttons = "".join(f'<button type="button" data-set="{kind}" data-value="{v}" aria-pressed="{str(v == current).lower()}">{t}</button>'
                      for v, t in options)
    return f'<div class="cg-seg" role="group" aria-label="{label}"><span class="cg-seg-label" aria-hidden="true">{label}</span>{buttons}</div>'


def _toolbar(extra: str = "", motion_toggle: bool = False) -> str:
    rm = ('<button type="button" class="cg-toggle" data-toggle="reduced" aria-pressed="false">Movimiento reducido</button>'
          if motion_toggle else "")
    return f"""<div class="cg-toolbar" role="toolbar" aria-label="Vista previa">
<label class="cg-search"><span class="sr-only">Buscar componentes</span><input type="search" id="cg-q" placeholder="Buscar: botón, tabla, fondo, contador…" autocomplete="off"></label>
{_seg("theme", "Tema", (("light", "Claro"), ("dark", "Oscuro")), "light")}
{_seg("motion", "Movimiento", (("subtle", "Sutil"), ("natural", "Natural"), ("expressive", "Expresivo")), "natural")}
{_seg("width", "Ancho", (("390", "Móvil"), ("768", "Tableta"), ("full", "Escritorio")), "full")}
{rm}{extra}
</div>"""


# ---------------------------------------------------------------- real libraries (main page)
def _demo_source(row: dict) -> str:
    path = bt_kit.REAL / row["demo"]
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _enh(rows: list[dict]) -> str:
    if not rows:
        return ""
    items = "".join(f'<li><span>{e(x["name"])}</span><span class="cg-status s-{e(x["status"])}">{e(STATUS[x["status"]])}</span>'
                    f'<span class="cg-dim">{e(x["how"] or x["reason"])}</span></li>' for x in rows)
    return (f'<div class="cg-enh"><p class="cg-enh-title"><span class="cg-src cg-src-animate-ui">Animate UI</span> '
            f'Mejora de movimiento</p><ul>{items}</ul></div>')


def _entry(row: dict, enh: list[dict]) -> str:
    cid, src = row["id"], row["source"]
    sources = src + (" animate-ui" if enh else "")
    words = " ".join([row["name"], cid, row["category"], src, SOURCE[src], row["description"], STATUS[row["status"]],
                      " ".join(x["name"] for x in enh)]).lower()
    head = (f'<header class="cg-comp-head"><div class="cg-comp-title"><h3>{e(row["name"])}</h3>'
            f'<span class="cg-src cg-src-{e(src)}">{e(SOURCE[src])}</span>'
            f'<span class="cg-prio" title="Prioridad del inventario de david-ui ({e(row["raw_priority"])})">{e(row["priority"])}</span>'
            f'<span class="cg-type">{e(TYPE.get(row["type"], row["type"]))}</span>'
            f'<span class="cg-status s-{e(row["status"])}">{e(STATUS[row["status"]])}</span></div>'
            f'<p>{e(row["description"])}</p></header>')
    meta = (f'<dl class="cg-meta"><div><dt>En el contrato</dt><dd><code>{e(row["contract"])} · variant=… · state=…</code></dd></div>'
            f'<div><dt>Versión · licencia</dt><dd>{e(row["version"])} · {e(row["licence"])}</dd></div></dl>')
    code = _demo_source(row)
    snippet = (f'<details class="cg-code"><summary>Import y JSX</summary><div class="cg-snippet"><div class="cg-snippet-head">'
               f'<span>{e(row["import"].splitlines()[0])}</span><button type="button" class="cg-copy" data-copy="snip-{e(cid)}">Copiar</button></div>'
               f'<pre><code id="snip-{e(cid)}">{e(code or row["import"])}</code></pre></div></details>')
    if row.get("built"):
        stage = (f'<div class="cg-stage"><iframe class="cg-frame" title="{e(row["name"])}: vista previa" '
                 f'src="/components/live/{e(cid)}?theme=light&amp;motion=natural" loading="lazy" sandbox="allow-scripts"></iframe></div>')
        if row["status"] == "gap":
            stage += f'<p class="cg-gap-note"><strong>Brecha del contrato:</strong> {e(row["reason"])}</p>'
    else:
        stage = f'<p class="cg-gap-note"><strong>Brecha:</strong> {e(row["reason"])}</p>'
    return (f'<article class="cg-comp" id="c-{e(cid)}" data-source="{e(sources)}" data-category="{e(row["category"])}" '
            f'data-priority="{e(row["priority"])}" data-status="{e(row["status"])}" data-search="{e(words)}">'
            f'{head}{meta}{stage}{snippet}{_enh(enh)}</article>')


def _filters(rows: list[dict], enh: list[dict], cats: list[dict]) -> str:
    def chip(value: str, label: str, n: int, extra: str = "") -> str:
        return (f'<button type="button" class="cg-chip" data-filter="source" data-value="{value}" aria-pressed="{str(value == "").lower()}">'
                f'{e(label)}<span class="cg-count">{n}{extra}</span></button>')
    chips = chip("", "Todas", len(rows)) + "".join(
        chip(sid, label, sum(r["source"] == sid for r in rows), f" + {len(enh)}" if sid == "animate-ui" else "")
        for sid, label in bt_kit.SOURCES)

    def select(kind: str, label: str, options: list[tuple[str, str]]) -> str:
        opts = "".join(f'<option value="{e(v)}">{e(t)}</option>' for v, t in [("", "Todas")] + options)
        return f'<label class="cg-select"><span>{label}</span><select data-filter="{kind}">{opts}</select></label>'
    return (f'<div class="cg-filters" role="group" aria-label="Filtros"><div class="cg-chips" role="group" aria-label="Fuente">{chips}</div>'
            f'{select("category", "Categoría", [(c["id"], c["title"]) for c in cats])}'
            f'{select("priority", "Prioridad", [("P1", "P1"), ("P2", "P2")])}'
            f'{select("status", "Estado", list(STATUS.items()))}</div>')


def _gaps(rows: list[dict], enh: list[dict], gaps: list[dict]) -> str:
    def item(name: str, badge: str, cls: str, reason: str) -> str:
        return f'<li><strong>{e(name)}</strong> <span class="{cls}">{e(badge)}</span><p>{e(reason)}</p></li>'
    entries = "".join(item(r["name"], SOURCE[r["source"]], f'cg-src cg-src-{e(r["source"])}', r["reason"])
                      for r in rows if r["status"] == "gap")
    mejoras = "".join(item(f'{x["base"]}: {x["name"]}', "Animate UI", "cg-src cg-src-animate-ui", x["reason"])
                      for x in enh if x["status"] == "gap")
    outside = "".join(item(g["name"], g["kind"], "cg-type", g["reason"]) for g in gaps)
    none = '<p class="cg-dim">Ninguna: las {} entradas están instaladas y se ven en vivo.</p>'.format(len(rows))
    return (f'<section class="cg-cat cg-gaps" id="brechas"><h2>Brechas</h2>'
            f'<h3>Entradas del inventario</h3>{"<ul class=cg-gap-list>" + entries + "</ul>" if entries else none}'
            f'<h3>Mejoras de Animate UI</h3><ul class="cg-gap-list">{mejoras}</ul>'
            f'<h3>Fuera del inventario</h3><ul class="cg-gap-list">{outside}</ul></section>')


def components_page() -> str:
    data = bt_kit.real_manifest()
    rows, enh, ws = data["entries"], data["enhancements"], data["workspace"]
    enh_of = {r["id"]: [x for x in enh if x["base"] == r["id"]] for r in rows}
    by_cat = {c["id"]: [r for r in rows if r["category"] == c["id"]] for c in data["categories"]}

    def index_entry(c: dict) -> str:
        links = "".join(f'<li><a href="#c-{e(r["id"])}" data-comp-link="{e(r["id"])}">{e(r["name"])}</a></li>' for r in by_cat[c["id"]])
        return (f'<li><a href="#cat-{e(c["id"])}" data-cat-link="{e(c["id"])}">{e(c["title"])}'
                f'<span class="cg-count">{len(by_cat[c["id"]])}</span></a><ul>{links}</ul></li>')
    index = "".join(index_entry(c) for c in data["categories"] if by_cat[c["id"]])
    cats = "".join(f'<section class="cg-cat" id="cat-{e(c["id"])}" data-cat="{e(c["id"])}"><h2>{e(c["title"])}</h2>'
                   f'{"".join(_entry(r, enh_of[r["id"]]) for r in by_cat[c["id"]])}</section>'
                   for c in data["categories"] if by_cat[c["id"]])
    refs = "".join(
        f'<article class="cg-ref" id="r-{e(r["id"])}"><header class="cg-ref-head"><div><h3>{e(r["title"])}</h3><p>{e(r["description"])}</p></div>'
        + (f'<a class="cg-open" href="/components/ref/{e(r["id"])}" target="_blank" rel="noopener" data-ref-link>Abrir a pantalla completa</a></header>'
           f'<div class="cg-stage cg-stage-ref"><iframe class="cg-frame cg-frame-ref" title="Pantalla de referencia: {e(r["title"])}" '
           f'src="/components/ref/{e(r["id"])}" loading="lazy" sandbox="allow-scripts"></iframe></div>' if r["built"] else
           '</header><p class="cg-gap-note">Aún no construida: <code>bitacora.py components build</code>.</p>')
        + '</article>' for r in data["references"])
    done = sum(r["status"] == "done" for r in rows)
    per = " · ".join(f'{label} {sum(r["source"] == sid and r["status"] == "done" for r in rows)}/{sum(r["source"] == sid for r in rows)}'
                     for sid, label in bt_kit.SOURCES)
    enh_done = sum(x["status"] == "done" for x in enh)
    if not ws["installed"]:
        notice = ('<p class="cg-notice">El workspace de librerías no está instalado en esta máquina: ejecuta '
                  '<code>bitacora.py components install</code> (descarga de los instaladores oficiales; luego todo funciona sin red).</p>')
    elif not ws["built"]:
        notice = '<p class="cg-notice">Workspace instalado pero sin construir: <code>bitacora.py components build</code>.</p>'
    else:
        notice = ""
    body = f"""<link rel="stylesheet" href="/static/kit-gallery.css">
<div class="cg" id="cg">
<div class="head cg-head"><div><p class="eyebrow">Kit del Designer · librerías reales</p><h1>Componentes</h1>
<p class="cg-lede">Las {len(rows)} entradas del inventario de david-ui instaladas desde sus fuentes oficiales y renderizadas en vivo:
{done} cubren el contrato del inventario ({e(per)}); {enh_done} de {len(enh)} mejoras de Animate UI aplicadas. Son los mismos componentes con los que el
Designer arma sus mockups. <a href="/components/kit">Kit de respaldo en HTML</a>.</p>{notice}</div></div>
{_toolbar(_filters(rows, enh, data["categories"]), motion_toggle=True)}
<div class="cg-layout">
<nav class="cg-index" aria-label="Categorías"><ul>{index}<li><a href="#brechas">Brechas</a></li>
<li><a href="#referencias">Pantallas de referencia<span class="cg-count">{len(data["references"])}</span></a></li></ul></nav>
<div class="cg-main">
<p class="cg-none" id="cg-none" hidden>Ninguna entrada coincide con la búsqueda o los filtros.</p>
{cats}
{_gaps(rows, enh, data.get("gaps", []))}
<section class="cg-cat cg-refs" id="referencias"><h2>Pantallas de referencia</h2>
<p class="cg-lede">Mockups completos construidos con los componentes reales y el builder del Designer: un HTML autocontenido cada uno,
con los mismos selectores de vista, estado, diálogo y tema que usa la página del plan.</p>
{refs}</section>
</div></div></div>
<script src="/static/kit-gallery.js"></script>"""
    return layout("Componentes", body, [("Componentes", "/components")])


# ---------------------------------------------------------------- fallback kit (plain HTML)
def frame_doc(cid: str, theme: str | None, motion: str | None) -> str | None:
    """A standalone page with the fallback kit and one component's examples, or None for an unknown id."""
    row = bt_kit.component(cid)
    if row is None:
        return None
    sections = "".join(f'<section class="kit-example" id="ex-{e(x["id"])}"><h2 class="kit-example-title">{e(x["title"])}</h2>'
                       f'<div class="kit-example-body">{x["html"]}</div></section>' for x in row["examples"])
    return (f'<!doctype html><html lang="es" data-theme="{bt_kit.theme(theme)}" data-motion="{bt_kit.motion(motion)}"><head>'
            f'<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{e(row["name"])}</title><style>{bt_kit.css()}</style><style>{FRAME_CSS}</style></head>'
            f'<body><main class="kit-frame">{sections}</main><script>{bt_kit.js()}</script><script>{FRAME_JS}</script></body></html>')


def kit_page() -> str:
    data = bt_kit.manifest()
    rows = data["components"]
    by_cat = {c["id"]: [r for r in rows if r["category"] == c["id"]] for c in data["categories"]}

    def comp(row: dict) -> str:
        cid = row["id"]
        snippets = "".join(
            f'<div class="cg-snippet"><div class="cg-snippet-head"><span>{e(x["title"])}</span>'
            f'<button type="button" class="cg-copy" data-copy="snip-{e(cid)}-{e(x["id"])}">Copiar</button></div>'
            f'<pre><code id="snip-{e(cid)}-{e(x["id"])}">{e(x["html"])}</code></pre></div>' for x in row["examples"])
        states = "".join(f"<li>{e(st)}</li>" for st in row["states"])
        words = " ".join([row["name"], cid, row["category"], row["description"], " ".join(row["states"])]).lower()
        return f"""<article class="cg-comp" id="c-{e(cid)}" data-search="{e(words)}">
<header class="cg-comp-head"><div class="cg-comp-title"><h3>{e(row["name"])}</h3><span class="cg-prio">{e(row["priority"])}</span></div>
<p>{e(row["description"])}</p></header>
<dl class="cg-meta"><div><dt>En el contrato</dt><dd><code>{e(row["contract"]).replace("|", "|<wbr>")}</code></dd></div>
<div><dt>Estados</dt><dd><ul class="cg-states">{states}</ul></dd></div></dl>
<div class="cg-stage"><iframe class="cg-frame" title="{e(row["name"])}: vista previa" src="/components/frame/{e(cid)}?theme=light&amp;motion=natural" loading="lazy" sandbox="allow-scripts"></iframe></div>
<details class="cg-code"><summary>HTML · {len(row["examples"])} ejemplos</summary>{snippets}</details>
</article>"""
    cats = "".join(f'<section class="cg-cat" id="cat-{e(c["id"])}" data-cat="{e(c["id"])}"><h2>{e(c["title"])}</h2>'
                   f'{"".join(comp(r) for r in by_cat[c["id"]])}</section>' for c in data["categories"] if by_cat[c["id"]])
    refs = "".join(
        f'<article class="cg-ref" id="r-{e(r["id"])}"><header class="cg-ref-head"><div><h3>{e(r["title"])}</h3><p>{e(r["description"])}</p></div>'
        f'<a class="cg-open" href="/components/kitref/{e(r["id"])}" target="_blank" rel="noopener" data-ref-link>Abrir a pantalla completa</a></header>'
        f'<div class="cg-stage cg-stage-ref"><iframe class="cg-frame cg-frame-ref" title="Pantalla de referencia: {e(r["title"])}" '
        f'src="/components/kitref/{e(r["id"])}?theme=light" loading="lazy" sandbox="allow-scripts"></iframe></div></article>'
        for r in data["references"])
    body = f"""<link rel="stylesheet" href="/static/kit-gallery.css">
<div class="cg" id="cg">
<div class="head cg-head"><div><p class="eyebrow">Kit del Designer · respaldo</p><h1>Kit de respaldo (HTML)</h1>
<p class="cg-lede">{len(rows)} componentes con anatomía de shadcn escritos en HTML/CSS simple. El Designer solo lo usa cuando no puede
ejecutar el builder de las librerías reales. <a href="/components">Volver a los componentes reales</a>.</p></div></div>
{_toolbar()}
<div class="cg-main">
<p class="cg-none" id="cg-none" hidden>Ningún componente coincide con la búsqueda.</p>
{cats}
<section class="cg-cat cg-refs" id="referencias"><h2>Pantallas de referencia</h2>{refs}</section>
</div></div>
<script src="/static/kit-gallery.js"></script>"""
    return layout("Kit de respaldo", body, [("Componentes", "/components"), ("Kit de respaldo", "/components/kit")])


def route(rest: list[str], q: dict) -> tuple[int, str | bytes, str, bool]:
    """(status, body, content type, sandbox) for `/components/...`. Previews are served sandboxed; ids resolve
    through a manifest only."""
    html = "text/html; charset=utf-8"
    if not rest:
        return 200, components_page(), html, False
    if rest == ["kit"]:
        return 200, kit_page(), html, False
    if len(rest) == 2 and rest[0] == "live":
        doc = bt_kit.live_doc(rest[1], q.get("theme"), q.get("motion"), q.get("rm"))
        if doc is not None:
            return 200, doc, html, True
    if len(rest) == 2 and rest[0] == "ref":
        path = bt_kit.real_reference(rest[1])
        if path:
            return 200, path.read_bytes(), html, True
    if len(rest) == 2 and rest[0] == "frame":
        doc = frame_doc(rest[1], q.get("theme"), q.get("motion"))
        if doc is not None:
            return 200, doc, html, True
    if len(rest) == 2 and rest[0] == "kitref":
        found = bt_kit.reference(rest[1])
        if found and found[1].is_file():
            return 200, found[1].read_bytes(), html, True
    return 404, "Not found", "text/plain", False
