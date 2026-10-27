"""The heavier views of the Plan tab: a subplan's design panel, the design review and the bilingual plan document.

Pure functions of the context built by `bt_page_planning.fragment` (project, requirement, options, translation cache,
subplans and their draft rows); they return HTML blocks marked with `data-k` for the live swap.
"""
from __future__ import annotations

import re
from html import escape as e

import bt_agent_models as models
import bt_design_drafts as drafts
import bt_planning_activity as activity
import bt_role_policy as role_policy
import bt_translate as tr
from bt_page_planning import REASONS, SEND, link, state_of, text
from bt_pages import inline, md, purl, read

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
    if (row.get("continuation_choice") or row.get("chosen") and row.get("phase") == "finalise") and row["status"] not in ("ready", "approved"):
        note = ("El Designer está finalizando el diseño elegido." if row["status"] in drafts.ACTIVE
                else "La revisión del diseño elegido está pendiente de finalizarse.")
        return f'<div class="pp-frame pending{" tall" if tall else ""}"><span>{e(note)}</span></div>'
    if drafts.revision_file(ctx["rdir"], ref, rev or None, ".html").is_file():
        src = _mock_src(ctx, ref, rev)
        return (f'<div class="pp-frame{" tall" if tall else ""}"><iframe src="{src}" title="Mockup {e(ref)}" '
                'loading="lazy" sandbox="allow-scripts"></iframe></div>')
    busy = row["status"] in drafts.ACTIVE
    note = "Aún no hay mockup: el progreso del Designer está arriba." if busy else "Todavía no hay mockup."
    bar = '<span class="pp-progress" aria-hidden="true"><span></span></span>' if busy else ""
    return f'<div class="pp-frame pending{" tall" if tall else ""}">{bar}<span>{e(note)}</span></div>'


def _designer_progress(ctx: dict, row: dict) -> str:
    """What the Designer is really doing: its state, the files it has written so far and its latest steps, so «preparando el
    borrador» is never the same message whether it works, thinks, or died."""
    import time

    import bt_agent_health as health
    now = time.time()
    state = health.one(row.get("delegation") or "", now)
    redo = row.get("reason") == "plan changed"
    if state is None:
        head, tone = "Registrando el resultado del Designer…", "work"
    elif state["state"] == "working":
        head = f"Designer trabajando · lleva {health.ago(state.get('age', 0)).replace('hace ', '')} · última señal {health.ago(state['since'])}"
        tone = "work"
    elif state["state"] == "quiet":
        head, tone = f"Designer sin señales {health.ago(state['since'])}: puede estar pensando o atascado", "wait"
    else:
        head = f"El Designer {health.STATE_ES.get(state['state'], state['state'])} {health.ago(state['since'])}: {state['detail']}"
        tone = "bad"
    files = []
    md, html = drafts.paths(ctx["rdir"], row["ref"])
    for label, path in (("Contrato", md), ("Contrato en español", md.with_name(md.stem + ".es.md")), ("Mockup", html)):
        if path.is_file():
            stamp = time.strftime("%H:%M", time.localtime(path.stat().st_mtime))
            files.append(f'<li class="done">✓ {e(label)} <span class="pp-meta">{path.stat().st_size // 1024} KB · {stamp}</span></li>')
        else:
            files.append(f'<li>○ {e(label)} <span class="pp-meta">aún no</span></li>')
    steps = health.activity(row.get("delegation") or "", 5) if state else []
    log = ("<ol class='pp-dsteps'>" + "".join(f"<li>{e(s)}</li>" for s in steps) + "</ol>") if steps else ""
    why = ("Actualizando el diseño elegido con el cambio del plan." if row.get("status") == "amending" else
           "Preparando el diseño de nuevo porque el subplan cambió." if redo else "Primer borrador.")
    return (f'<div class="pp-dprog"><p class="pp-dhead"><span class="pp-ag-dot {"work" if tone == "work" else "wait" if tone == "wait" else "bad"}"></span>'
            f'{e(head)}</p><p class="pp-meta">{why} Escrito hasta ahora:</p><ul class="pp-dfiles">{"".join(files)}</ul>'
            f'{("<p class=pp-meta>Últimos pasos (el más reciente primero):</p>" + log) if log else ""}</div>')


def _composer(ctx: dict, row: dict, placeholder: str) -> str:
    base = purl(ctx["project"], "req", ctx["rid"])
    selected = row.get("chosen") or row.get("continuation_choice")
    direction = (f'<input type="hidden" name="direction" value="{e(selected)}">' if selected else
                 '<label>Sobre la dirección <select name="direction"><option value="">Todas</option>' +
                 ''.join(f'<option value="{d["id"]}">{d["id"].upper()} · {e(d.get("name") or d["id"])}</option>'
                         for d in row.get("directions", [])) + '</select></label>' if row.get("directions") else '')
    return (f'<form method="post" class="pp-composer" action="{base}/design-feedback">'
            f'<input type="hidden" name="token" value="{e(ctx["token"])}"><input type="hidden" name="contract" '
            f'value="{e(row["ref"])}"><input type="hidden" name="lang" value="{e(ctx["opts"]["lang"])}">'
            f'<input type="hidden" name="anchor" value="{e(row["id"])}">{direction}<div class="pp-input">'
            f'<textarea name="comments" aria-label="Comentario para el Designer" placeholder="{e(placeholder)}">'
            f'</textarea><button type="submit" class="pp-send" aria-label="Enviar al Designer">{SEND}</button></div>'
            f'<div class="pp-composer-foot"><span class="pp-meta">También puedes decirlo en la conversación: el '
            f'Planner se lo pasa al Designer.</span><button type="submit" class="text" formaction="{base}/design-draft"'
            ' name="force" value="1">Rehacer diseño</button></div></form>')


def _notices(ctx: dict, row: dict) -> str:
    from bt_page_design_amend import banner
    out = [banner(ctx, row)]
    if row["status"] in drafts.ACTIVE:
        out.append(f'<p class="pp-note warn">El Designer está trabajando ({e(REASONS.get(row.get("reason"), "en curso"))}).</p>')
    if row["stale"] and not row.get("amend"):
        out.append('<p class="pp-note warn">El subplan cambió en la conversación y aún no elegiste una dirección: el '
                   "Designer preparará direcciones nuevas cuando el plan deje de cambiar.</p>")
    if row.get("error"):
        out.append(f'<p class="pp-note bad">{e(row["error"])}</p>')
    return "".join(out)


def design_panel(ctx: dict, s: dict, row: dict) -> str:
    from bt_page_design_directions import panel as directions_panel
    opts, p, r = ctx["opts"], ctx["project"], ctx["rid"]
    rev = int(row.get("revision") or 0)
    base = purl(p, "req", r)
    questions = "".join(f'<li><span class="grow">{e(q)}</span><details><summary>Responder</summary>'
                        f'<form method="post" action="{base}/design-answer">'
                        f'<input type="hidden" name="token" value="{e(ctx["token"])}">'
                        f'<input type="hidden" name="contract" value="{e(row["ref"])}">'
                        f'<input type="hidden" name="anchor" value="{e(row["id"])}">'
                        f'<input type="hidden" name="lang" value="{e(opts["lang"])}">'
                        f'<input type="hidden" name="question" value="{e(q)}">'
                        '<label>Tu respuesta<textarea name="comments" required></textarea></label>'
                        '<button type="submit">Enviar respuesta</button></form></details></li>'
                        for q in row.get("questions") or [])
    asked = (f'<div class="pp-questions"><strong>Preguntas del Designer · {len(row["questions"])}</strong>'
             f'<ul>{questions}</ul></div>' if questions else "")
    history = "".join(f'<li><span class="pp-meta">{e(f["when"][11:16])}</span> {e(f["text"])}'
                      f'{"" if f.get("consumed") else " <em>(pendiente)</em>"}</li>' for f in row.get("feedback") or [])
    past = (f'<details class="pp-history"><summary>Tus comentarios ({len(row.get("feedback") or [])})</summary>'
            f"<ul>{history}</ul></details>" if history else "")
    review = link(p, r, opts, mode="review", sp=s["id"], rev=0)
    composer = _composer(ctx, row, "Ej.: cuadrícula a 4 columnas y filtros en una sola barra") \
        if row["status"] != "approved" and drafts.planning(ctx["rdir"]) else \
        '<p class="pp-meta">El plan ya no está en planificación: los cambios van en una versión nueva del contrato.</p>'
    progress = _designer_progress(ctx, row) if row["status"] in drafts.ACTIVE else ""
    if row.get("directions") and not (row.get("chosen") or row.get("continuation_choice")):
        return (directions_panel(ctx, row) + f'<div class="pp-side">{progress}{_notices(ctx, row)}'
                f'{asked}{composer}{past}</div>')
    return (directions_panel(ctx, row) + f'<div class="pp-design"><section class="pp-mock">{progress}<div class="pp-mock-bar"><code>{e(row["ref"])}</code>'
            f'<span class="pp-meta">{f"· borrador {rev}" if rev else "· sin borrador"}</span>{_widths()}</div>'
            f'{_frame(ctx, row)}<div class="pp-mock-foot"><span class="pp-meta">El mockup trae sus propios selectores '
            f'de vista y estado.</span><a href="{e(review)}" data-nav>Abrir revisión →</a></div></section>'
            f'<div class="pp-side">{_notices(ctx, row)}{asked}{composer}'
            f"{past}</div></div>")


LEVEL = {"low": "baja", "medium": "media", "high": "alta", "extreme": "extrema"}
LEVEL_M = {"low": "bajo", "medium": "medio", "high": "alto", "extreme": "extremo"}
TONE = {"low": "ok", "medium": "mid", "high": "warn", "extreme": "bad"}
TONE_INVERSE = {"low": "warn", "medium": "mid", "high": "ok", "extreme": "ok"}      # confidence: low is the worry
SCOPE = {"small_change": "cambio pequeño", "large_change": "cambio grande", "full_feature": "funcionalidad completa"}


def _level(value: object, feminine: bool = True) -> str:
    return (LEVEL if feminine else LEVEL_M).get(str(value), str(value or "").replace("_", " "))


def _duration(minutes: object) -> str:
    if not isinstance(minutes, (int, float)) or isinstance(minutes, bool) or minutes <= 0:
        return ""
    total = round(minutes)
    return f"~{total} min" if total < 60 else f"~{total // 60} h" + (f" {total % 60:02d} min" if total % 60 else "")


def _signal(label: str, value: object, tone: str, feminine: bool = False) -> str:
    if not value:
        return ""
    return f'<div><dt>{label}</dt><dd class="lv {tone}">{e(_level(value, feminine))}</dd></div>'


ROLE_ES = {"implementer": "Implementador", "runner": "Ejecutor de pruebas", "reviewer": "Revisor",
           "researcher": "Investigador", "designer": "Diseñador", "explorer": "Explorador", "planner": "Planificador",
           "antagonist": "Antagonista"}
PROVIDER_ES = {"claude": "Claude Code", "codex": "Codex", "antigravity": "Antigravity"}
EFFORT_ES = {"low": "bajo", "medium": "medio", "high": "alto", "xhigh": "muy alto"}


def _models_popover(t: dict, pill_class: str) -> str:
    """The complexity pill as a disclosure: the owner policy's models for this task. Read-only information; the real
    route is chosen by the Scheduler at run time from each account's quota."""
    cx, role = t.get("complexity"), role_policy.role_for_task(t.get("kind"))
    choices = role_policy.options(role, cx) if role else []
    rows = "".join(
        f'<li class="{"first" if n == 1 else ""}"><i class="pv {e(prov)}" aria-hidden="true"></i><span class="pm">'
        f'<b>{e(models.MODELS.get(m, {}).get("label", m))}</b><span>{e(PROVIDER_ES.get(prov, prov))} · esfuerzo '
        f'{e(EFFORT_ES.get(eff, eff))}</span></span><em>{"Preferido" if n == 1 else "Alternativa"}</em></li>'
        for n, (prov, m, eff) in enumerate(choices, 1))
    if not role:
        body, foot = '<p class="pp-meta">Esta tarea no tiene un rol fijo: el Scheduler usa el enrutado general.</p>', ""
    else:
        stable = choices == role_policy.options(role)
        foot = ("La complejidad no cambia la preferencia de este rol. " if stable else
                "La complejidad alta prefiere la opción de más capacidad. ") + "Al ejecutar, el Scheduler elige según la cuota."
        body = f"<ol>{rows}</ol>"
    return (f'<details class="pp-cxpop"><summary class="pp-cx {pill_class}">Complejidad {e(_level(cx))}'
            f'<i aria-hidden="true">▾</i></summary><div class="pp-pop"><header><span>Modelos recomendados</span>'
            f'<strong>{e(ROLE_ES.get(role, "Sin rol fijo"))}</strong></header>{body}'
            f'{f"<footer>{foot}</footer>" if foot else ""}</div></details>')


def tasks_panel(ctx: dict, s: dict) -> str:
    """The subplan's tasks as cards: title first, complexity (what routes the agent) as the one highlighted fact, then
    risk, coupling, confidence and scope as small labelled values, then time, dependencies and criteria, then the task's
    full detail."""
    interfaces = [i for i in drafts._plan(ctx["rdir"]).get("interfaces") or [] if isinstance(i, dict)] \
        if ctx.get("rdir") else []
    cards = []
    for t in s["tasks"]:
        cx = t.get("complexity")
        pill = _models_popover(t, TONE.get(str(cx), "mid")) if cx else ""
        scope = t.get("scope")
        signals = "".join((
            _signal("Riesgo", t.get("risk"), TONE.get(str(t.get("risk")), "mid")),
            _signal("Acoplamiento", t.get("coupling"), TONE.get(str(t.get("coupling")), "mid")),
            _signal("Confianza", t.get("confidence"), TONE_INVERSE.get(str(t.get("confidence")), "mid"), True),
            f'<div><dt>Alcance</dt><dd class="lv">{e(SCOPE.get(str(scope), str(scope).replace("_", " ")))}</dd></div>'
            if scope else ""))
        after = [a for a in t.get("after") or [] if isinstance(a, str)]
        criteria = [c for c in t.get("acceptance_criteria") or [] if isinstance(c, str)]
        foot = " · ".join(x for x in (
            _duration(t.get("estimated_minutes")), f"después de {', '.join(after)}" if after else "",
            f'{len(criteria)} criterio{"" if len(criteria) == 1 else "s"}') if x)
        cards.append(
            f'<article class="pp-task" id="t-{e(t.get("id", ""))}"><header><span class="pp-id">{e(t.get("id", ""))}</span>'
            f'<span class="pp-kind">{e(t.get("kind") or "")}{" · UI" if t.get("ui") is True else ""}</span>{pill}</header>'
            f'<h3>{text(ctx, t.get("title") or "")}</h3>'
            f'{f"<dl class=pp-sig>{signals}</dl>" if signals else ""}<p class="pp-meta">{e(foot)}</p>'
            f'{_task_detail(ctx, t, interfaces)}</article>')
    return '<div class="pp-tasks">' + "".join(cards) + "</div>"


EVIDENCE_ES = {"complexity": "Complejidad", "scope": "Alcance", "duration": "Duración", "risk": "Riesgo",
               "coupling": "Acoplamiento", "confidence": "Confianza"}


def _strs(value: object) -> list[str]:
    return [x for x in value or [] if isinstance(x, str) and x.strip()] if isinstance(value, list) else []


def _task_detail(ctx: dict, t: dict, interfaces: list[dict]) -> str:
    """Everything PLAN.json says about a task, which is all the executor receives: objective, acceptance criteria,
    verification, files, interfaces and facts, with the classification evidence folded below. Folded by default so
    the cards stay scannable; the live swap keeps a card the owner opened open."""
    parts = [f'<p class="pp-tobj">{text(ctx, t["objective"])}</p>'] if isinstance(t.get("objective"), str) else []
    criteria = _strs(t.get("acceptance_criteria"))
    if criteria:
        parts.append("<h4>Criterios de aceptación</h4><ol class=pp-criteria>"
                     + "".join(f"<li>{text(ctx, c)}</li>" for c in criteria) + "</ol>")
    checks = [c for c in t.get("verification") or [] if isinstance(c, dict)]
    if checks:
        rows = []
        for c in checks:
            tags = " · ".join(e(str(x)) for x in (c.get("category"), c.get("environment"),
                                                  f'la crea {c["created_by"]}' if c.get("created_by") else "",
                                                  f'requiere {", ".join(_strs(c.get("requires")))}'
                                                  if _strs(c.get("requires")) else "") if x)
            value = (f'<code>{e(str(c.get("value") or ""))}</code>' if c.get("type") == "command"
                     else f'<span class="pp-manual">Manual</span> {text(ctx, str(c.get("value") or ""))}')
            expected = (f'<span class="pp-meta">Esperado: {text(ctx, c["expected"])}</span>'
                        if isinstance(c.get("expected"), str) else "")
            rows.append(f'<li>{value}<span>{text(ctx, str(c.get("purpose") or ""))}</span>{expected}'
                        f'{f"<span class=pp-meta>{tags}</span>" if tags else ""}</li>')
        parts.append(f'<h4>Verificación</h4><ul class="pp-checks">{"".join(rows)}</ul>')
    paths = _strs(t.get("expected_paths"))
    if paths:
        parts.append("<h4>Archivos</h4><ul class=pp-paths>" + "".join(f"<li><code>{e(p)}</code></li>" for p in paths)
                     + "</ul>")
    tid = t.get("id")
    links = []
    for i in interfaces:
        roles = [label for label, hit in (("produce", i.get("producer_task") == tid),
                                          ("consume", tid in _strs(i.get("consumer_tasks"))),
                                          ("integra", i.get("integration_task") == tid)) if hit]
        if roles:
            links.append(f'<li><b>{e(str(i.get("id") or ""))}</b> {text(ctx, str(i.get("title") or ""))} '
                         f'<span class="pp-meta">· {e(", ".join(roles))}</span></li>')
    if links:
        parts.append(f"<h4>Interfaces</h4><ul class=pp-paths>{''.join(links)}</ul>")
    facts = [(label, ", ".join(_strs(t.get(key))) if isinstance(t.get(key), list) else t.get(key))
             for label, key in (("Repositorio", "repository"), ("Hito", "milestone_id"), ("Cubre", "covers"),
                                ("Recursos compartidos", "shared_resources"))]
    facts = "".join(f"<div><dt>{label}</dt><dd>{e(str(v))}</dd></div>" for label, v in facts if v)
    if facts:
        parts.append(f"<dl class=pp-facts>{facts}</dl>")
    if isinstance(t.get("estimate_rationale"), str):
        parts.append(f'<p class="pp-meta"><b>Estimación:</b> {text(ctx, t["estimate_rationale"])}</p>')
    evidence = t.get("classification_evidence") if isinstance(t.get("classification_evidence"), dict) else {}
    why = "".join(
        f'<div><dt>{e(EVIDENCE_ES.get(k, k))}</dt><dd>{text(ctx, str(v.get("justification") or ""))}'
        + "".join(f"<code>{e(x)}</code>" for x in _strs(v.get("evidence"))) + "</dd></div>"
        for k, v in evidence.items() if isinstance(v, dict))
    if why:
        parts.append(f'<details class="pp-why"><summary>Por qué esta clasificación</summary><dl>{why}</dl></details>')
    return (f'<details class="pp-tdet"><summary>Ver detalle de la tarea</summary><div>{"".join(parts)}</div></details>'
            if parts else "")


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
        if len(cells) >= 4 and re.fullmatch(r"(?:UI-)?AC-\d+", cells[0]):
            rows.append(cells[:4])
    return rows


def review(ctx: dict) -> str:
    from bt_page_design_directions import panel as directions_panel
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
    composer = (_composer(ctx, row, "Pedir un cambio sobre este ancho o estado…")
                if row["status"] != "approved" and drafts.planning(ctx["rdir"]) else "")
    preview = ('' if row.get("directions") and not (row.get("chosen") or row.get("continuation_choice")) else
               f'<div class="pp-rmain"><div class="pp-mock-bar">{_widths()}'
               f'<span class="pp-meta">Mockup con datos ficticios</span></div>{_frame(ctx, row, rev, tall=True)}</div>')
    return (f'<section class="pp-review" data-k="review-{e(s["id"])}-{rev}"><header class="pp-rhead">'
            f'<a href="{e(back)}" data-nav class="pp-back" aria-label="Volver a los subplanes">←</a>'
            f'<code>{e(s["id"])} · {e(row["ref"])}</code><h2>{text(ctx, s["title"])}</h2>'
            f'{f"<nav class=pp-seg aria-label=Borrador>{versions}</nav>" if versions else ""}'
            f'<span class="pp-state {e(cls)}">{e(label)}</span>'
            '<button type="button" class="pp-dbtn" data-pp-full title="Ver el mockup como lo vería un usuario">'
            f'⛶ Pantalla completa</button></header>{directions_panel(ctx, row)}<div class="pp-rgrid">{preview}<aside class="pp-rside">'
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
        columns = _columns(ctx, section.split("\n", 1)[1] if section.startswith("#") and "\n" in section else section,
                           f"pp-d{i}")
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
    """The EN lines that changed (+/−). Two translations of a section differ in wording everywhere, so the Spanish
    side shows the current translation of the changed section instead of a line diff."""
    def clean(body: str) -> str:
        return inline(re.sub(r"^(#{1,6}\s+|[-*]\s+|\d+\.\s+)", "", body.strip()))
    en = "".join(f'<p class="{"add" if sign == "+" else "del" if sign == "-" else "ctx"}">'
                 f'{"+ " if sign == "+" else "− " if sign == "-" else ""}{clean(body)}</p>'
                 for sign, body in activity.line_diff(moved["prev"], moved["text"]) if clean(body))
    if ctx["opts"]["lang"] == "en":
        return f'<div class="pp-diffbox">{en}</div>'
    es, missing = tr.render(ctx["rdir"], moved["text"])
    added = [clean(line) for sign, line in activity.line_diff(moved["prev"], moved["text"]) if sign == "+"]
    current = ('<p class="ctx"><span class="pp-chip info">traduciendo…</span> la versión en español aparece al terminar.</p>'
               if missing else f'<p class="ctx">{len(added)} línea{"s" if len(added) != 1 else ""} nueva'
               f'{"s" if len(added) != 1 else ""} en el original; así queda la sección:</p>' + "".join(
                   f'<p class="now">{clean(line)}</p>' for line in es.splitlines()[1:] if clean(line)))
    if ctx["opts"]["lang"] == "es":
        return f'<div class="pp-diffbox">{current}</div>'
    return f'<div class="pp-cols pp-diffbox"><div lang="en">{en}</div><div lang="es">{current}</div></div>'
