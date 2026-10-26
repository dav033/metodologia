"""The heavier views of the Plan tab: a subplan's design panel, the design review and the bilingual plan document.

Pure functions of the context built by `bt_page_planning.fragment` (project, requirement, options, translation cache,
subplans and their draft rows); they return HTML blocks marked with `data-k` for the live swap.
"""
from __future__ import annotations

import re
from html import escape as e

import bt_design_drafts as drafts
import bt_planning_activity as activity
import bt_translate as tr
from bt_page_planning import REASONS, SEND, link, state_of, text
from bt_pages import md, purl, read

WIDTHS = (("390", "Móvil"), ("768", "Tableta"), ("", "Escritorio"))


def _mock_src(ctx: dict, ref: str, rev: int = 0) -> str:
    html = drafts.revision_file(ctx["rdir"], ref, rev or None, ".html")
    version = int(html.stat().st_mtime) if html.is_file() else 0
    return (f'{purl(ctx["project"], "req", ctx["rid"], "mockup")}?contract={e(ref)}&amp;v={version}'
            + (f"&amp;rev={rev}" if rev else ""))


def _widths() -> str:
    return ('<div class="pp-seg sm" role="group" aria-label="Ancho del mockup">' + "".join(
        f'<button type="button" data-width="{w}"{" class=on aria-pressed=true" if not w else " aria-pressed=false"}>'
        f"{label}</button>" for w, label in WIDTHS) + "</div>")


def _frame(ctx: dict, row: dict, rev: int = 0, tall: bool = False) -> str:
    ref = row["ref"]
    if drafts.revision_file(ctx["rdir"], ref, rev or None, ".html").is_file():
        src = _mock_src(ctx, ref, rev)
        return (f'<div class="pp-frame{" tall" if tall else ""}"><iframe src="{src}" title="Mockup {e(ref)}" '
                'loading="lazy" sandbox="allow-scripts"></iframe></div>')
    busy = row["status"] in drafts.ACTIVE
    note = ("El subplan cambió en la conversación; rehaciendo el diseño…" if row.get("reason") == "plan changed"
            else "El Designer está preparando el primer borrador…") if busy else "Todavía no hay mockup."
    bar = '<span class="pp-progress" aria-hidden="true"><span></span></span>' if busy else ""
    return f'<div class="pp-frame pending{" tall" if tall else ""}">{bar}<span>{e(note)}</span></div>'


def _composer(ctx: dict, row: dict, placeholder: str) -> str:
    base = purl(ctx["project"], "req", ctx["rid"])
    return (f'<form method="post" class="pp-composer" action="{base}/design-feedback">'
            f'<input type="hidden" name="token" value="{e(ctx["token"])}"><input type="hidden" name="contract" '
            f'value="{e(row["ref"])}"><input type="hidden" name="lang" value="{e(ctx["opts"]["lang"])}">'
            f'<input type="hidden" name="anchor" value="{e(row["id"])}"><div class="pp-input">'
            f'<textarea name="comments" aria-label="Comentario para el Designer" placeholder="{e(placeholder)}">'
            f'</textarea><button type="submit" class="pp-send" aria-label="Enviar al Designer">{SEND}</button></div>'
            f'<div class="pp-composer-foot"><span class="pp-meta">También puedes decirlo en la conversación: el '
            f'Planner se lo pasa al Designer.</span><button type="submit" class="text" formaction="{base}/design-draft"'
            ' name="force" value="1">Rehacer diseño</button></div></form>')


def _notices(row: dict) -> str:
    out = []
    if row["status"] in drafts.ACTIVE:
        out.append(f'<p class="pp-note warn">El Designer está trabajando ({e(REASONS.get(row.get("reason"), "en curso"))}).</p>')
    if row["stale"]:
        out.append('<p class="pp-note warn">El subplan cambió en la conversación; el diseño se rehará cuando el plan '
                   "deje de cambiar.</p>")
    if row.get("error"):
        out.append(f'<p class="pp-note bad">{e(row["error"])}</p>')
    return "".join(out)


def design_panel(ctx: dict, s: dict, row: dict) -> str:
    opts, p, r = ctx["opts"], ctx["project"], ctx["rid"]
    rev = int(row.get("revision") or 0)
    questions = "".join(f'<li><span class="grow">{e(q)}</span><button type="button" class="outline sm" '
                        f'data-reply="{e(q)}">Responder</button></li>' for q in row.get("questions") or [])
    asked = (f'<div class="pp-questions"><strong>Preguntas del Designer · {len(row["questions"])}</strong>'
             f'<ul>{questions}</ul></div>' if questions else "")
    history = "".join(f'<li><span class="pp-meta">{e(f["when"][11:16])}</span> {e(f["text"])}'
                      f'{"" if f.get("consumed") else " <em>(pendiente)</em>"}</li>' for f in row.get("feedback") or [])
    past = (f'<details class="pp-history"><summary>Tus comentarios ({len(row.get("feedback") or [])})</summary>'
            f"<ul>{history}</ul></details>" if history else "")
    review = link(p, r, opts, mode="review", sp=s["id"], rev=0)
    composer = _composer(ctx, row, "Ej.: cuadrícula a 4 columnas y filtros en una sola barra") \
        if row["status"] != "approved" else '<p class="pp-meta">Aprobado con el plan: los cambios van en una versión nueva.</p>'
    return (f'<div class="pp-design"><section class="pp-mock"><div class="pp-mock-bar"><code>{e(row["ref"])}</code>'
            f'<span class="pp-meta">{f"· borrador {rev}" if rev else "· sin borrador"}</span>{_widths()}</div>'
            f'{_frame(ctx, row)}<div class="pp-mock-foot"><span class="pp-meta">El mockup trae sus propios selectores '
            f'de vista y estado.</span><a href="{e(review)}" data-nav>Abrir revisión →</a></div></section>'
            f'<div class="pp-side">{_notices(row)}{asked}{composer}'
            f"{past}</div></div>")


def _heading(ctx: dict, key: str, body: str) -> str:
    """A section heading in the chosen language (its translation's first line once the section is translated)."""
    if ctx["opts"]["lang"] == "en":
        return e(key)
    es, missing = tr.render(ctx["rdir"], body)
    shown = es.strip().splitlines()[0].lstrip("#").strip() if not missing and es.strip() else key
    if ctx["opts"]["lang"] == "both" and shown != key:
        return f'{e(shown)} <span class="pp-meta" lang="en">· {e(key)}</span>'
    return e(shown)


def _sections(markdown: str) -> list[tuple[str, str]]:
    return [(k, v) for k, v in activity.headings(markdown) if k != "·"]


def _criteria(markdown: str) -> list[list[str]]:
    rows = []
    for line in markdown.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and re.fullmatch(r"UI-AC-\d+", cells[0]):
            rows.append(cells[:4])
    return rows


def review(ctx: dict) -> str:
    opts, p, r = ctx["opts"], ctx["project"], ctx["rid"]
    s = next(item for item in ctx["subplans"] if item["id"] == opts["sp"])
    row = ctx["rows"].get(s["ref"]) if s["ref"] else None
    back = link(p, r, opts, mode="subplans", rev=0)
    if row is None:
        return (f'<section class="pp-review" data-k="review-{e(s["id"])}"><a href="{e(back)}" data-nav>← Volver</a>'
                '<p class="pp-empty">Este subplan no tiene interfaz: no hay diseño que revisar.</p></section>')
    latest = int(row.get("revision") or 0)
    rev = opts["rev"] if 0 < opts["rev"] <= latest else latest
    versions = "".join(f'<a href="{e(link(p, r, opts, rev=n))}" data-nav{" class=on aria-current=true" if n == rev else ""}>'
                       f"v{n}</a>" for n in range(1, latest + 1))
    current = read(drafts.revision_file(ctx["rdir"], row["ref"], rev or None, ".md"))
    previous = dict(_sections(read(drafts.revision_file(ctx["rdir"], row["ref"], rev - 1, ".md")))) if rev > 1 else {}
    outline = []
    for i, (key, body) in enumerate(_sections(current)):
        moved = bool(previous) and previous.get(key) != body
        shown = tr.render(ctx["rdir"], body)[0] if opts["lang"] != "en" else body
        outline.append(f'<details class="pp-sec-item{" changed" if moved else ""}"><summary><span>{_heading(ctx, key, body)}</span>'
                       f'{"<em>cambió</em>" if moved else ""}</summary>{md(f"rv-{i}", shown)}</details>')
    criteria = "".join(f'<li><span class="pp-id">{e(c[0])}</span> <span class="pp-meta">{e(c[1])} · {e(c[2])}</span>'
                       f"<br>{e(c[3])}</li>" for c in _criteria(current))
    thread = [(f["when"], "Tú", f["text"], True) for f in row.get("feedback") or []]
    thread += [(h["at"], f"Designer · borrador {h['rev']}", h.get("summary") or "", False) for h in row.get("history") or []]
    thread += [(ev["at"], ev["who"], ev["text"] + (f" ({ev['diff']})" if ev.get("diff") else ""), False)
               for ev in activity.events(ctx["rdir"], 60) if ev.get("sp") == s["id"] and ev.get("who") == "Planner"]
    messages = "".join(f'<div class="pp-msg{" mine" if mine else ""}"><span class="pp-meta">{e(who)} · '
                       f'{e(when[11:16])}</span>{e(body)}</div>' for when, who, body, mine in sorted(thread))
    cls, label = state_of(row)
    composer = _composer(ctx, row, "Pedir un cambio sobre este ancho o estado…") if row["status"] != "approved" else ""
    return (f'<section class="pp-review" data-k="review-{e(s["id"])}-{rev}"><header class="pp-rhead">'
            f'<a href="{e(back)}" data-nav class="pp-back" aria-label="Volver a los subplanes">←</a>'
            f'<code>{e(s["id"])} · {e(row["ref"])}</code><h2>{text(ctx, s["title"])}</h2>'
            f'{f"<nav class=pp-seg aria-label=Borrador>{versions}</nav>" if versions else ""}'
            f'<span class="pp-state {e(cls)}">{e(label)}</span></header><div class="pp-rgrid"><div class="pp-rmain">'
            f'<div class="pp-mock-bar">{_widths()}<span class="pp-meta">Mockup con datos ficticios</span></div>'
            f'{_frame(ctx, row, rev, tall=True)}</div><aside class="pp-rside">'
            '<input type="radio" name="pp-rt" id="pp-rt-c" checked><label for="pp-rt-c">Contrato</label>'
            '<input type="radio" name="pp-rt" id="pp-rt-k"><label for="pp-rt-k">Criterios</label>'
            '<input type="radio" name="pp-rt" id="pp-rt-m"><label for="pp-rt-m">Comentarios</label>'
            f'<div class="pp-rpanel c"><p class="pp-meta">{len(outline)} secciones · {len(_criteria(current))} criterios '
            f'visuales{" · comparado con v" + str(rev - 1) if previous else ""}</p>{"".join(outline)}</div>'
            f'<div class="pp-rpanel k"><ul class="pp-ac">{criteria or "<li class=pp-meta>Sin tabla de criterios.</li>"}'
            f'</ul></div><div class="pp-rpanel m">{messages or "<p class=pp-meta>Sin comentarios todavía.</p>"}</div>'
            f"{composer}</aside></div></section>")


def document(ctx: dict) -> str:
    opts, p, r, rdir = ctx["opts"], ctx["project"], ctx["rid"], ctx["rdir"]
    sections = _sections(read(rdir / "PLAN.md"))
    changed = activity.changed_sections(rdir)
    lang = opts["lang"]
    toggle = link(p, r, opts, only=not opts["only"])
    nav, body = [], []
    for i, (key, section) in enumerate(sections):
        moved = changed.get(key)
        title = _heading(ctx, key, section)
        nav.append(f'<a href="#pp-sec-{i}"{" class=changed" if moved else ""}>{title}'
                   f'{"<em>cambió</em>" if moved else ""}</a>')
        if opts["only"] and not moved:
            body.append(f'<section class="pp-sec folded" id="pp-sec-{i}"><span>{title} · sin cambios</span></section>')
            continue
        head = (f'<header>{title}' + (f'<span>· cambió a las {e(moved["changed"][11:16])} desde la conversación</span>'
                                       if moved else "") + "</header>")
        diff = _diff(ctx, moved) if moved and moved.get("prev") else ""
        columns = _columns(ctx, section, f"pp-d{i}")
        full = f"<details><summary>Sección completa</summary>{columns}</details>" if diff else columns
        body.append(f'<section class="pp-sec{" changed" if moved else ""}" id="pp-sec-{i}">{head}{diff}{full}</section>')
    labels = ('<div class="pp-cols-head"><span>Original · EN</span><span>Traducción · ES</span></div>'
              if lang == "both" else "")
    return (f'<section class="pp-doc" data-k="doc-{lang}-{int(opts["only"])}"><div class="pp-doc-bar">'
            f'<a href="{e(toggle)}" data-nav class="pp-toggle{" on" if opts["only"] else ""}" role="switch" '
            f'aria-checked="{str(opts["only"]).lower()}">Solo lo que cambió</a><span class="pp-meta">Secciones con '
            f'cambios en las últimas 2 h: {len(changed)}</span></div><div class="pp-docgrid"><nav class="pp-toc" '
            f'aria-label="Secciones del plan">{"".join(nav)}</nav><div class="pp-doc-main">{labels}{"".join(body)}'
            "</div></div></section>")


def _columns(ctx: dict, section: str, block: str) -> str:
    lang = ctx["opts"]["lang"]
    if lang == "en":
        return md(block + "-en", section)
    es, missing = tr.render(ctx["rdir"], section)
    note = '<span class="pp-chip info">traduciendo…</span>' if missing else ""
    if lang == "es":
        return note + md(block + "-es", es)
    return (f'<div class="pp-cols"><div lang="en">{md(block + "-en", section)}</div>'
            f'<div lang="es">{note}{md(block + "-es", es)}</div></div>')


def _diff(ctx: dict, moved: dict) -> str:
    def lines(prev: str, new: str) -> str:
        return "".join(f'<p class="{"add" if sign == "+" else "del" if sign == "-" else "ctx"}">'
                       f'{"+ " if sign == "+" else "− " if sign == "-" else ""}{e(body)}</p>'
                       for sign, body in activity.line_diff(prev, new))
    en = lines(moved["prev"], moved["text"])
    if ctx["opts"]["lang"] == "en":
        return f'<div class="pp-diffbox">{en}</div>'
    (old_es, old_missing), (new_es, new_missing) = tr.render(ctx["rdir"], moved["prev"]), tr.render(ctx["rdir"], moved["text"])
    es = (lines(old_es, new_es) if not old_missing and not new_missing else
          '<p class="ctx"><span class="pp-chip info">traduciendo…</span> la diferencia en español aparece al terminar.</p>')
    if ctx["opts"]["lang"] == "es":
        return f'<div class="pp-diffbox">{es}</div>'
    return f'<div class="pp-cols pp-diffbox"><div lang="en">{en}</div><div lang="es">{es}</div></div>'
