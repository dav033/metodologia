"""Answering and reviewing from the Plan tab: the Planner's open question round, and its notes and past rounds.

The rounds tab of the requirement page stays, but the owner works in a subplan's view, so the open round shows up here
with the same form (it brings him back to this view) and the history sits in a tab. The open round is a block of its own
whose HTML only changes when the round does, so the live refresh never swaps it while the owner is filling it in.
"""
from __future__ import annotations

from html import escape as e

import bt_planning_notes as notes
import bt_rounds as rounds


def _clip(text: str, limit: int = 240) -> tuple[str, str]:
    """(first part, rest) so a long paragraph can open on demand; it breaks at a sentence or clause, never mid-word."""
    text = (text or "").strip()
    if len(text) <= limit:
        return text, ""
    cut = max((text.rfind(mark, 0, limit) + 1 for mark in (". ", "; ", ": ")), default=0)
    if cut < 80:
        cut = text.rfind(" ", 0, limit)
        cut = cut if cut > 40 else limit
        return text[:cut].rstrip() + "…", text[cut:].strip()
    return text[:cut].strip(), text[cut:].strip()


def _options(q: dict, qid: str) -> str:
    out = []
    for opt in q["options"]:
        rec = opt["key"] == q.get("recommended")
        out.append(f'<label class="pp-opt{" rec" if rec else ""}"><input type="radio" name="{qid}" value="{e(opt["key"])}"'
                   f'{" checked" if rec else ""}><span class="pp-opt-key">{e(opt["key"])}</span>'
                   f'<span class="pp-opt-label">{e(opt["label"])}</span>'
                   f'{"<span class=pp-opt-rec>Recomendada</span>" if rec else ""}</label>')
    return f'<div class="pp-opts">{"".join(out)}</div>'


def _question(i: int, q: dict) -> str:
    qid = e(q["id"])
    head, rest = _clip(q["text"])
    more = f'<details class="pp-ask-more"><summary>Ver el resto</summary><p>{e(rest)}</p></details>' if rest else ""
    why = f'<p class="pp-ask-why">{e(q["why"])}</p>' if q.get("why") else ""
    if q["type"] == "choice":
        body = (_options(q, qid) + f'<details class="pp-ask-note"><summary>Añadir un comentario</summary>'
                f'<input type="text" name="{qid}__note" placeholder="Comentario (opcional)" '
                f'aria-label="Comentario a la pregunta {i}"></details>')
    else:
        hint = '<span class="pp-ask-hint">Sugerencia precargada: cámbiala si no te convence.</span>' if q.get("suggested") else ""
        body = (f'<textarea name="{qid}" rows="4" aria-label="Respuesta a la pregunta {i}">{e(q.get("suggested", ""))}</textarea>{hint}')
    return (f'<fieldset class="pp-ask-q"><legend><span class="pp-ask-n">{i}</span></legend>'
            f'<div class="pp-ask-text"><strong>{e(head)}</strong>{more}{why}</div>{body}</fieldset>')


def asks(ctx: dict) -> str:
    rdir = ctx["rdir"]
    import bt_page_planning as planning
    opts = ctx.get("opts") or {}
    current = rounds.open_round(rdir) if rounds.rounds_dir(rdir).exists() else None
    if current is None:
        if opts.get("view") != "asks":
            return '<div data-k="asks" hidden></div>'
        sp = opts.get("sp") or ""
        back = f'<a data-nav href="{e(planning.link(ctx["project"], ctx["rid"], opts, view="design"))}">Volver al subplan {e(sp)}</a>' if sp else ""
        past = f'<a data-nav href="{e(planning.link(ctx["project"], ctx["rid"], opts, view="notes"))}">Ver las rondas respondidas y las notas</a>'
        return (f'<section class="pp-asks pp-asks-empty" data-k="asks" aria-label="Preguntas del Planner"><h3>No hay preguntas abiertas</h3>'
                f'<p class="pp-meta">El Planner no tiene nada pendiente de ti ahora mismo. Si acabas de responder, ya lo está leyendo.</p>'
                f'<p>{past} · {back}</p></section>')
    from bt_pages import purl
    data = rounds.load(current)
    back_link = (f'<a class="pp-asks-back" data-nav href="{e(planning.link(ctx["project"], ctx["rid"], opts, view="design"))}">'
                 f'← Volver al subplan {e(opts.get("sp") or "")}</a>') if opts.get("sp") else ""
    sp = e((ctx.get("opts") or {}).get("sp") or "")
    head, rest = _clip(data.get("intro", ""), 200)
    intro = (f'<p class="pp-ask-intro">{e(head)}</p>' + (f'<details class="pp-ask-more"><summary>Leer el contexto completo</summary>'
                                                         f'<p>{e(rest)}</p></details>' if rest else "")) if head else ""
    questions = "".join(_question(i, q) for i, q in enumerate(data["questions"], 1))
    count = len(data["questions"])
    return (f'<section class="pp-asks" data-k="asks" aria-label="Preguntas del Planner"><header class="pp-asks-head">'
            f'{back_link}<span class="pp-asks-chip">Ronda {e(str(data.get("round")))} · {count} {"pregunta" if count == 1 else "preguntas"}</span>'
            f'<h3>{e(data.get("title", ""))}</h3><p class="pp-meta">El Planner te pregunta. Las respuestas recomendadas vienen '
            f'marcadas: cambia solo lo que no te convenza.</p>{intro}</header>'
            f'<form method="post" action="{purl(ctx["project"], "req", ctx["rid"], "answer")}" class="pp-asks-form">'
            f'<input type="hidden" name="token" value="{e(ctx["token"])}"><input type="hidden" name="round" value="{e(current.name)}">'
            f'<input type="hidden" name="back" value="plan"><input type="hidden" name="back_sp" value="{sp}">'
            f'{questions}<div class="pp-asks-bar"><span class="pp-meta">Al enviar, el Planner recibe el aviso y sigue.</span>'
            f'<button type="submit">Enviar respuestas</button></div></form></section>')


def tab_label(ctx: dict) -> str:
    rows = notes.notes(ctx["rdir"])
    done = sum(1 for f in rounds.list_rounds(ctx["rdir"]) if rounds.load(f).get("status") == "answered") \
        if rounds.rounds_dir(ctx["rdir"]).exists() else 0
    return f"Notas y rondas · {len(rows)}/{done}"


def panel(ctx: dict) -> str:
    rdir = ctx["rdir"]
    rows = notes.notes(rdir)
    if rows:
        items = "".join(f'<li><time>{e(r["at"][11:16])}</time> <strong>{e(r["kind"])}</strong> {e(r["text"])}</li>'
                        for r in reversed(rows[-60:]))
        saved = f'<h3>Notas del Planner</h3><ol class="pp-notes">{items}</ol>'
    else:
        saved = ('<h3>Notas del Planner</h3><p class="pp-empty">Todavía no ha guardado notas. Son lo que aprende y decide, '
                 'con su motivo, para que otra sesión pueda continuar sin perder nada.</p>')
    history = []
    for f in (reversed(rounds.list_rounds(rdir)) if rounds.rounds_dir(rdir).exists() else []):
        data = rounds.load(f)
        if data.get("status") != "answered":
            continue
        history.append(f'<details><summary><strong>Ronda {e(str(data.get("round")))} — {e(data.get("title", ""))}</strong></summary>'
                       f'<p>{e(rounds.format_answers(data)).replace(chr(10), "<br>")}</p></details>')
    past = ("<h3>Rondas respondidas</h3>" + "".join(history)) if history else ""
    return f'<section class="pp-verify">{saved}{past}</section>'
