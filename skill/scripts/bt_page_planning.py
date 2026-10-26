"""Plan tab of a requirement while it is being planned: the plan in English, Spanish or both, every subplan, and the
Designer's draft for each UI subplan (mockup, contract, open questions and an owner feedback form).

The tab is one live region: `planning-live.js` polls `fragment()` and swaps only the blocks (`data-k`) that changed,
so what the owner and the Planner change in the conversation appears without a reload and without losing a comment
being typed. Each poll also lets the Designer and the translator follow those changes (`follow`, throttled).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import re
import threading
import time
from html import escape as e
from pathlib import Path

import bt_design_drafts as drafts
import bt_translate as tr
from bt_core import _front
from bt_pages import md, purl, read

LANGS = (("en", "EN"), ("es", "ES"), ("both", "EN + ES"))
STATES = {"none": "sin diseño", "queued": "diseño en cola", "drafting": "diseñando…", "ready": "diseño listo",
          "failed": "error de diseño", "approved": "diseño aprobado con el plan"}
REASONS = {"requested": "pedido desde la conversación", "web": "pedido desde la web",
           "feedback": "aplicando tus comentarios", "plan changed": "el subplan cambió"}
_FOLLOW_SEC = 10
_followed: dict[str, float] = {}
_follow_lock = threading.Lock()


def default_lang(rdir: Path) -> str:
    return "es" if (Path(rdir) / "PLAN.es.md").is_file() else "en"


def follow(project: str, rdir: Path) -> None:
    """Let the Designer and the translator catch up with the conversation, at most every few seconds per requirement."""
    key = str(rdir)
    with _follow_lock:
        if time.time() - _followed.get(key, 0) < _FOLLOW_SEC:
            return
        _followed[key] = time.time()

    def run():
        try:
            drafts.sync(project, rdir)
            tr.ensure(project, rdir)
        except (SystemExit, Exception):  # noqa: BLE001, S110 - a page poll never fails on background work
            pass
    threading.Thread(target=run, daemon=True).start()


def plan_tab(project: str, rid: str, rdir: Path, status: str | None, token: str, lang: str) -> str:
    lang = lang if lang in dict(LANGS) else default_lang(rdir)
    api = purl(project, "req", rid, "planning") + f"?lang={lang}"
    return (f'<div class="planning" id="planning" data-api="{e(api)}" aria-live="polite">'
            f'{fragment(project, rid, rdir, status, token, lang)}</div>'
            '<script src="/static/planning-live.js"></script>')


def fragment(project: str, rid: str, rdir: Path, status: str | None, token: str, lang: str) -> str:
    plan = Path(rdir) / "PLAN.md"
    cache = tr.load_cache(rdir) if lang != "en" else {}
    subplans = drafts.subplans(rdir)
    rows = {row["ref"]: row for row in drafts.rows(rdir)}
    parts = [_bar(project, rid, rdir, lang, rows)]
    if subplans:
        parts.append(f'<h2 class="pl-h">Subplanes <span class="muted">({len(subplans)})</span></h2>')
        if rows and not drafts.active(rdir) and status not in ("approved", "launched", "in-progress", "done"):
            parts.append(f'<div class="block" data-k="design-start"><form method="post" class="pl-start" '
                         f'action="{purl(project, "req", rid, "design-draft")}"><input type="hidden" name="token" '
                         f'value="{e(token)}"><input type="hidden" name="lang" value="{e(lang)}"><p>Hay {len(rows)} '
                         'subplanes con interfaz. El Designer puede diseñarlos en paralelo mientras sigues planeando.</p>'
                         '<button type="submit">Iniciar diseños</button></form></div>')
        parts += [_subplan(project, rid, rdir, s, rows.get(s["ref"]), cache, lang, token) for s in subplans]
    parts.append(_document(rdir, plan, lang))
    parts.append(_approval(project, rid, rdir, status, token, lang))
    return "".join(_stamp(part) for part in parts)


def _stamp(block: str) -> str:
    """Give a live block the digest of its HTML (`data-h`): the page swaps only blocks whose digest changed."""
    digest = hashlib.sha256(block.encode("utf-8")).hexdigest()[:12]
    return re.sub(r'data-k="([^"]*)"', lambda m: f'{m.group(0)} data-h="{digest}"', block, count=1)


def _bar(project: str, rid: str, rdir: Path, lang: str, rows: dict) -> str:
    links = "".join(f'<a href="{purl(project, "req", rid)}?tab=plan&amp;lang={k}"'
                    f'{" class=on aria-current=true" if k == lang else ""}>{label}</a>' for k, label in LANGS)
    chips = []
    sources = [f for f in (Path(rdir) / "PLAN.md", Path(rdir) / "PLAN.json", Path(rdir) / "SPEC.md") if f.is_file()]
    if sources:
        changed = dt.datetime.fromtimestamp(max(f.stat().st_mtime for f in sources), dt.UTC).astimezone()
        chips.append(f'<span class="kpi">plan modificado {changed:%H:%M:%S}</span>')
    if lang != "en":
        state = tr.status(rdir)
        chips.append('<span class="kpi warn">traduciendo…</span>' if state["running"] else
                     f'<span class="kpi warn">{state["pending"]} secciones sin traducir</span>' if state["pending"] else
                     '<span class="kpi ok">traducción al día</span>')
    if rows:
        ready = sum(1 for r in rows.values() if r["status"] in ("ready", "approved") and not r["stale"])
        busy = sum(1 for r in rows.values() if r["status"] in drafts.ACTIVE)
        chips.append(f'<span class="kpi">diseños {ready}/{len(rows)} listos</span>')
        if busy:
            chips.append(f'<span class="kpi info">Designer trabajando en {busy}</span>')
    return (f'<div class="pl-bar block" data-k="bar"><nav class="pl-lang" aria-label="Idioma del plan">{links}</nav>'
            f'<div class="kpis">{"".join(chips)}<span class="kpi live" id="pl-live">● en vivo</span></div></div>')


def _text(cache: dict, text: str, lang: str) -> str:
    """Escaped text in the chosen language; in EN + ES the original follows in muted type."""
    if lang == "en" or not text:
        return e(text)
    es = tr.phrase(cache, text)
    if lang == "both" and es != text:
        return f'{e(es)}<span class="pl-orig" lang="en">{e(text)}</span>'
    return e(es)


def _subplan(project: str, rid: str, rdir: Path, s: dict, row: dict | None, cache: dict, lang: str, token: str) -> str:
    tasks = "".join(f'<li><code>{e(t.get("id", ""))}</code> {_text(cache, t.get("title") or "", lang)}'
                    f' <span class="muted">· {e(t.get("kind") or "")}{" · UI" if t.get("ui") is True else ""}</span></li>'
                    for t in s["tasks"])
    criteria = "".join(f"<li>{_text(cache, c, lang)}</li>" for c in s["criteria"] if isinstance(c, str))
    covers = f' · cubre {e(", ".join(map(str, s["covers"])))}' if s["covers"] else ""
    chip = ""
    if row:
        label = "diseño desactualizado" if row["stale"] else STATES.get(row["status"], row["status"])
        chip = f'<span class="pl-state {e(row["status"])}{" stale" if row["stale"] else ""}">{e(label)}</span>'
    body = (f'<header><span class="pl-id">{e(s["id"])}</span><h3>{_text(cache, s["title"], lang)}</h3>'
            f'{"<span class=pl-ui>UI</span>" if s["ref"] else ""}{chip}</header>'
            f'<p class="pl-outcome">{_text(cache, s["outcome"], lang)}</p>'
            f'<details class="pl-tasks"><summary>{len(s["tasks"])} tareas{covers}</summary>'
            f'<ul>{tasks}</ul>{"<p class=muted>Criterios de aceptación</p><ul>" + criteria + "</ul>" if criteria else ""}'
            f'</details>')
    if row:
        body += _design(project, rid, rdir, row, lang, token)
    return f'<section class="pl-sub card block" data-k="sp-{e(s["id"])}" id="{e(s["id"])}">{body}</section>'


def _design(project: str, rid: str, rdir: Path, row: dict, lang: str, token: str) -> str:
    ref = row["ref"]
    md_file, html_file = drafts.paths(rdir, ref)
    bits = [f'<div class="pl-design"><p class="pl-dhead">Diseño <code>{e(ref)}</code>']
    if row.get("revision"):
        bits.append(f' · versión de borrador {int(row["revision"])}')
    if row.get("model"):
        bits.append(f' · <span class="muted">{e(str(row.get("agent") or ""))} {e(str(row["model"]))}</span>')
    bits.append("</p>")
    if row["status"] in drafts.ACTIVE:
        bits.append('<p class="notice warn">El Designer está trabajando en este diseño' +
                    (f' ({e(REASONS.get(row["reason"], row["reason"]))})' if row.get("reason") else "") + '.</p>')
    if row["stale"]:
        bits.append('<p class="notice warn">El subplan cambió en la conversación; el diseño se rehará en cuanto el plan '
                    'deje de cambiar.</p>')
    if row.get("error"):
        bits.append(f'<p class="notice bad">{e(row["error"])}</p>')
    if row.get("questions"):
        items = "".join(f"<li>{e(q)}</li>" for q in row["questions"])
        bits.append(f'<div class="pl-questions"><strong>Preguntas del Designer</strong><ul>{items}</ul></div>')
    if html_file.is_file():
        src = f'{purl(project, "req", rid, "mockup")}?contract={e(ref)}&amp;v={int(html_file.stat().st_mtime)}'
        bits.append(f'<div class="pl-mock"><iframe src="{src}" title="Mockup {e(ref)}" loading="lazy" '
                    f'sandbox="allow-scripts"></iframe><a href="{src}" target="_blank" rel="noopener">Abrir mockup '
                    'en otra pestaña →</a></div>')
    elif row["status"] in drafts.ACTIVE:
        bits.append('<div class="pl-mock pending" aria-hidden="true"><span>Mockup en preparación…</span></div>')
    if md_file.is_file():
        bits.append(f'<details class="pl-contract"><summary>Contrato de diseño</summary>'
                    f'{_document_body(rdir, read(md_file), lang, "c-" + re.sub(r"[^a-z0-9-]", "-", ref.lower()))}</details>')
    if row.get("feedback"):
        items = "".join(f'<li><span class="muted">{e(f["when"][11:16])}</span> {e(f["text"])}'
                        f'{"" if f.get("consumed") else " <em>(pendiente)</em>"}</li>' for f in row["feedback"])
        bits.append(f'<details class="pl-feedback"><summary>Tus comentarios ({len(row["feedback"])})</summary>'
                    f'<ul>{items}</ul></details>')
    if row["status"] != "approved":
        base = purl(project, "req", rid)
        bits.append(f'<form method="post" class="q pl-form" action="{base}/design-feedback">'
                    f'<input type="hidden" name="token" value="{e(token)}"><input type="hidden" name="contract" '
                    f'value="{e(ref)}"><input type="hidden" name="lang" value="{e(lang)}"><input type="hidden" '
                    f'name="anchor" value="{e(row["id"])}"><label for="fb-{e(row["id"])}"><strong>Pedir cambios al diseño</strong></label>'
                    f'<textarea id="fb-{e(row["id"])}" name="comments" placeholder="Qué debe cambiar, qué falta, qué '
                    'no te convence…"></textarea><div class="actions"><button type="submit">Enviar al Designer</button>'
                    f'<button class="secondary" type="submit" formaction="{base}/design-draft" name="contract" '
                    f'value="{e(ref)}">Rehacer diseño</button></div></form>')
    bits.append("</div>")
    return "".join(bits)


def _document_body(rdir: Path, text: str, lang: str, block: str) -> str:
    if lang == "en":
        return md(block, text)
    es, missing = tr.render(rdir, text)
    note = (f'<p class="notice warn">{missing} secciones aún en inglés; la traducción se está actualizando.</p>'
            if missing else "")
    if lang == "es":
        return note + md(block + "-es", es)
    return (f'{note}<div class="pl-bilingual"><div><p class="eyebrow">Original · EN</p>{md(block + "-en", text)}</div>'
            f'<div lang="es"><p class="eyebrow">Traducción · ES</p>{md(block + "-es", es)}</div></div>')


def _document(rdir: Path, plan: Path, lang: str) -> str:
    return (f'<section class="block pl-doc" data-k="doc"><h2 class="pl-h">Plan completo</h2>'
            f'{_document_body(rdir, read(plan), lang, "plan-doc")}</section>')


def _approval(project: str, rid: str, rdir: Path, status: str | None, token: str, lang: str) -> str:
    if status in ("approved", "launched", "in-progress", "done"):
        return f'<div class="block notice" data-k="approve">Plan {e(status)}.</div>'
    if status != "review":
        return ('<div class="block notice" data-k="approve">El plan sigue en conversación; el botón de aprobación '
                'aparece cuando el Planner lo deja en revisión.</div>')
    waiting = drafts.readiness(rdir)
    blocked = "".join(f"<li>{e(w)}</li>" for w in waiting)
    note = (f'<div class="notice"><strong>Antes de aprobar:</strong><ul>{blocked}</ul></div>' if waiting else
            '<p class="muted">Aprobar el plan aprueba también sus diseños listos (contratos v1 con su SHA-256).</p>'
            if drafts.active(rdir) else "")
    return (f'<form class="q block pl-approve" data-k="approve" method="post" '
            f'action="{purl(project, "req", rid, "plan")}"><input type="hidden" name="token" value="{e(token)}">'
            f'<h2 class="pl-h">Aprobación</h2>{note}<div class="question"><strong>Comentarios</strong> <span '
            'class="muted">(opcional; obligatorio si pides cambios)</span><textarea name="comments" '
            'aria-label="Comentarios"></textarea></div><div class="actions">'
            f'<button type="submit" name="decision" value="approve"{" disabled" if waiting else ""}>'
            'Aprobar y lanzar Scheduler</button><button class="secondary" type="submit" name="decision" '
            'value="changes">Pedir cambios</button></div></form>')


def plan_status(rdir: Path) -> str | None:
    plan = Path(rdir) / "PLAN.md"
    return _front(plan, "status") if plan.exists() else None
