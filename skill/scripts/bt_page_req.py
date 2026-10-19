"""Requirement page: spec, plan (with the approval form), question rounds (with the answer form), handoff."""
from __future__ import annotations

import re
from html import escape as e

import bt_rounds as rounds
from bt_core import *  # noqa: F403
from bt_core import _first_heading, _front
from bt_page_run import ACTIVE, has_run, load_run, run_panel
from bt_pages import badge, layout, md, purl, read

REQ_TABS = [("rounds", "Preguntas"), ("spec", "Spec"), ("plan", "Plan"), ("trace", "Trazabilidad"), ("review", "Revisar"), ("handoff", "Handoff")]


def req_page(project: str, req: str, tab: str, token: str, notice: str = "") -> str:
    rdir = find_req(ROOT / project, req)
    rid = req_id(rdir)
    spec, plan = rdir / "SPEC.md", rdir / "PLAN.md"
    plan_status = _front(plan, "status") if plan.exists() else None
    open_round = rounds.open_round(rdir) if rounds.rounds_dir(rdir).exists() else None
    run = load_run(rdir)
    run_available = has_run(rdir)
    live = bool(run) and run.get("status") in ACTIVE
    if not tab:
        tab = "rounds" if open_round else ("plan" if plan_status == "review" else
                                           ("run" if live or (run_available and run is None) else
                                            ("review" if plan_status in ("done", "launched") else "spec")))
    tab_list = REQ_TABS + ([("run", "Ejecución")] if run_available else [])
    tabs = "".join(
        f'<a class="{"on" if k == tab else ""}" href="{purl(project, "req", rid)}?tab={k}">{v}'
        f'{" ●" if (k == "rounds" and open_round) or (k == "plan" and plan_status == "review") or (k == "run" and live) else ""}</a>'
        for k, v in tab_list)
    if tab == "run":
        content = run_panel(project, rid, rdir, token)
    elif tab == "rounds":
        content = rounds_panel(project, rid, rdir, token)
    elif tab == "plan":
        content = plan_panel(project, rid, plan, plan_status, token) if plan.exists() else \
            '<p class="muted">Todavía no hay plan.</p>'
    elif tab == "review":
        from bt_page_review import review_panel
        content = review_panel(project, rid, rdir, token)
    elif tab == "trace":
        from bt_page_graph import coverage_panel
        content = coverage_panel(project, rid)
    elif tab == "handoff":
        h = rdir / "HANDOFF.md"
        content = md("doc", read(h)) if h.exists() else '<p class="muted">Aún no se lanzó un ejecutor.</p>'
    else:
        content = md("doc", read(spec))
    note = f'<div class="notice">{e(notice)}</div>' if notice else ""
    title = re.sub(r"^REQ-\d+\s*[—–:-]\s*", "", _first_heading(spec)) or rid
    head = (f'<div class="head"><div><p class="eyebrow">{e(project)} · {e(rid)}</p><h1>{e(title)}</h1>'
            f'<div class="kpis"><span class="kpi">spec {badge(_front(spec, "status"))}</span>'
            f'{"<span class=kpi>plan " + badge(plan_status) + "</span>" if plan_status else ""}</div></div></div>')
    body = f'{head}{note}<div class="tabs">{tabs}</div><div class="panel">{content}</div>'
    return layout(rid, body, [(project, purl(project)), (rid, purl(project, "req", rid))])


def rounds_panel(project: str, rid: str, rdir: Path, token: str) -> str:
    files = rounds.list_rounds(rdir) if rounds.rounds_dir(rdir).exists() else []
    if not files:
        return '<p class="muted">Sin rondas de preguntas todavía.</p>'
    parts = []
    for f in reversed(files):
        data = rounds.load(f)
        title = f'Ronda {data.get("round")} — {e(data.get("title", ""))}'
        if data.get("status") == "open":
            parts.append(f"<h2>{title} {badge('open')}</h2>" + round_form(project, rid, f, data, token))
        else:
            answered = e(rounds.format_answers(data)).replace("\n", "<br>")
            parts.append(f'<details><summary><strong>{title}</strong> {badge("answered")}</summary>'
                         f'<p style="font-size:14px">{answered}</p></details>')
    return "".join(parts)


def round_form(project: str, rid: str, f: Path, data: dict, token: str) -> str:
    qs = []
    intro = f'<p>{e(data["intro"])}</p>' if data.get("intro") else ""
    cov = f'<p class="muted">Cobertura: {e(str(data["coverage"]))}</p>' if data.get("coverage") else ""
    for i, q in enumerate(data["questions"], 1):
        qid = e(q["id"])
        why = f'<p class="why">{e(q["why"])}</p>' if q.get("why") else ""
        if q["type"] == "choice":
            opts = "".join(
                f'<label class="opt"><input type="radio" name="{qid}" value="{e(o["key"])}"'
                f'{" checked" if o["key"] == q.get("recommended") else ""}> <span><strong>{e(o["key"])})</strong> '
                f'{e(o["label"])}{"<span class=rec>recomendada</span>" if o["key"] == q.get("recommended") else ""}'
                f'</span></label>' for o in q["options"])
            field = (f'{opts}<input type="text" name="{qid}__note" placeholder="Comentario (opcional)" '
                     f'style="margin-top:6px">')
        else:
            field = f'<textarea name="{qid}">{e(q.get("suggested", ""))}</textarea>'
        qs.append(f'<div class="question"><strong>{i}. {e(q["text"])}</strong>{why}<div style="margin-top:8px">'
                  f'{field}</div></div>')
    return (f'{intro}{cov}<form class="q" method="post" action="{purl(project, "req", rid, "answer")}">'
            f'<input type="hidden" name="token" value="{e(token)}"><input type="hidden" name="round" value="{e(f.name)}">'
            f'{"".join(qs)}<div class="actions"><button type="submit">Enviar respuestas</button>'
            f'<span class="muted">Las recomendadas vienen marcadas; cambia solo lo que no te convenza.</span></div></form>')


def plan_panel(project: str, rid: str, plan: Path, status: str | None, token: str) -> str:
    form = ""
    if status == "review":
        form = f"""<form class="q" method="post" action="{purl(project, 'req', rid, 'plan')}" style="margin-top:20px">
<input type="hidden" name="token" value="{e(token)}">
<div class="question"><strong>Comentarios</strong> <span class="muted">(opcional; obligatorio si pides cambios)</span>
<textarea name="comments"></textarea>
</div>
<div class="actions"><button type="submit" name="decision" value="approve">Aprobar y lanzar Scheduler</button>
<button class="secondary" type="submit" name="decision" value="changes">Pedir cambios</button></div></form>"""
    elif status in ("approved", "launched", "in-progress", "done"):
        form = f'<div class="notice">Plan {e(status)}.</div>'
    return md("doc", read(plan)) + form
