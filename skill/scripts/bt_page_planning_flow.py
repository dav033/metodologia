"""Plan tab blocks of the collaborative planning flow (bt_planning_flow, D-130).

The phase stepper (Requisitos · Esqueleto · Subplanes n/m · Aprobación), the interview and skeleton views, a subplan's
flow actions (Definir ahora / Confirmar subplan) and its inputs. Pure functions of the context built by
`bt_page_planning.fragment`, which carries the flow state in `ctx["flow"]`.
"""
from __future__ import annotations

from html import escape as e

import bt_design_drafts as drafts
import bt_planning_flow as flow
from bt_page_planning import link, plural, state_of, text
from bt_pages import purl

STEPS = (("interview", "Requisitos"), ("outline", "Esqueleto"), ("subplans", "Subplanes"), ("ready", "Aprobación"))
STATE_ES = {"pending": "pendiente", "defining": "definiendo ahora", "confirmed": "confirmado",
            "changed": "cambió tras confirmarlo"}
DOT = {"pending": "none", "defining": "drafting", "confirmed": "ready", "changed": "changed"}
HINT = {"interview": "El Planner hace en la conversación solo las preguntas iniciales y las más importantes.",
        "outline": "Revisa hitos y subplanes; pide cambios en la conversación y confirma el esqueleto.",
        "ready": "Todos los subplanes están confirmados: aprueba el plan para lanzarlo."}


def _form(ctx: dict, action: str, label: str, *, sp: str = "", cls: str = "", disabled: bool = False) -> str:
    return (f'<form method="post" action="{purl(ctx["project"], "req", ctx["rid"], action)}" class="pp-inline">'
            f'<input type="hidden" name="token" value="{e(ctx["token"])}"><input type="hidden" name="lang" '
            f'value="{e(ctx["opts"]["lang"])}"><input type="hidden" name="anchor" value="{e(sp)}">'
            f'<button type="submit"{f" class={cls}" if cls else ""}{" disabled" if disabled else ""}>{e(label)}'
            "</button></form>")


def steps(ctx: dict) -> str:
    st, status = ctx["flow"], ctx["status"]
    current = len(STEPS) if status in ("approved", "launched", "in-progress", "done") else \
        [k for k, _ in STEPS].index(st["phase"])
    items = []
    for i, (key, name) in enumerate(STEPS):
        label = f"{name} {st['confirmed']}/{st['total']}" if key == "subplans" and st["total"] else name
        cls = "done" if i < current else "on" if i == current else ""
        items.append(f'<li class="{cls}"{" aria-current=step" if cls == "on" else ""}><span class="n">'
                     f'{"✓" if cls == "done" else i + 1}</span>{e(label)}</li>')
    focus = st["focus"]
    hint = (f"Definiendo {focus}: comportamiento, diseño, entradas y tareas. Confírmalo cuando esté completo."
            if st["phase"] == "subplans" and focus else HINT.get(st["phase"], ""))
    return (f'<div class="pp-steps" data-k="steps"><ol aria-label="Fases de la planificación">{"".join(items)}</ol>'
            f'<span class="pp-meta">{e(hint)}</span></div>')


def interview(ctx: dict) -> str:
    p, r = ctx["project"], ctx["rid"]
    general = [row for row in ctx["flow"]["inputs"] if not row["subplan"]]
    return (f'<section class="pp-phase" data-k="interview"><h2>Preguntas iniciales</h2><p>El Planner pregunta en la '
            'conversación solo lo que define todo el plan: objetivo, alcance, decisiones grandes y las entradas que '
            'afectan a todos los subplanes. El resto se pregunta al definir cada subplan.</p><p>Cuando escriba el '
            'esqueleto de hitos y subplanes, aparecerá aquí para que lo revises.</p><p class="pp-links">'
            f'<a href="{purl(p, "req", r)}?tab=rounds">Rondas de preguntas</a> · <a href="{purl(p, "req", r)}?tab=spec">'
            f'Spec</a></p>{_inputs_table(general, "Entradas generales")}</section>')


def outline(ctx: dict) -> str:
    plan = drafts._plan(ctx["rdir"])
    milestones = [m for m in plan.get("milestones") or [] if isinstance(m, dict)]
    owner = {s.get("id"): s.get("milestone_id") for s in plan.get("subplans") or [] if isinstance(s, dict)}
    known = {m.get("id") for m in milestones}
    columns = []
    for m in milestones + ([{"id": None, "title": "Sin hito"}]
                           if any(owner.get(s["id"]) not in known for s in ctx["subplans"]) else []):
        mine = [s for s in ctx["subplans"] if (owner.get(s["id"]) == m.get("id")) or
                (m.get("id") is None and owner.get(s["id"]) not in known)]
        cards = "".join(_card(ctx, s) for s in mine) or '<p class="pp-meta">Sin subplanes.</p>'
        columns.append(f'<section class="pp-ms"><header><span class="pp-id">{e(str(m.get("id") or "—"))}</span>'
                       f'<strong>{text(ctx, str(m.get("title") or ""))}</strong></header>{cards}</section>')
    confirmed = bool(ctx["flow"]["outline"])
    foot = ('<p class="pp-meta">Esqueleto confirmado. Cambiarlo sigue siendo posible en la conversación.</p>'
            if confirmed else
            '<div class="pp-board-foot"><span class="pp-meta">¿Falta, sobra o cambia algo? Dilo en la conversación: '
            'el tablero se actualiza solo.</span>' + _form(ctx, "planning-outline", "Confirmar esqueleto") + "</div>")
    ui = sum(1 for s in ctx["subplans"] if s["ref"])
    return (f'<section class="pp-board" data-k="outline"><header class="pp-board-head"><h2>Esqueleto del plan</h2>'
            f'<span class="pp-meta">{plural(len(milestones), "hito", "hitos")} · '
            f'{plural(len(ctx["subplans"]), "subplan", "subplanes")} · {ui} con interfaz</span></header>'
            f'<div class="pp-cols-ms">{"".join(columns)}</div>{foot}</section>')


def _card(ctx: dict, s: dict) -> str:
    chips = f'<span class="pp-chip info">UI · {e(s["ref"])}</span>' if s["ref"] else '<span class="pp-chip">sin interfaz</span>'
    if s["tasks"]:
        chips += f'<span class="pp-chip">{plural(len(s["tasks"]), "tarea", "tareas")}</span>'
    href = link(ctx["project"], ctx["rid"], ctx["opts"], sp=s["id"], mode="subplans")
    return (f'<a class="pp-card" href="{e(href)}" data-nav><span class="pp-id">{e(s["id"])}</span><strong>'
            f'{text(ctx, s["title"])}</strong><span class="pp-meta">{text(ctx, s["outcome"])}</span>'
            f'<span class="pp-chips">{chips}</span></a>')


def label(ctx: dict, sid: str) -> tuple[str, str]:
    """(dot class, label) of a subplan's flow state."""
    item = ctx["flow"]["subplans"].get(sid) or {"state": "pending"}
    return DOT[item["state"]], STATE_ES[item["state"]]


def actions(ctx: dict, s: dict) -> str:
    """The subplan's place in the flow and what the owner can do with it."""
    st = ctx["flow"]
    if st["phase"] in ("interview", "outline") or ctx["status"] in ("approved", "launched", "in-progress", "done"):
        return ""
    item = st["subplans"].get(s["id"]) or {"state": "pending", "problems": []}
    state, missing = item["state"], item["problems"]
    buttons = []
    if state != "confirmed" and s["id"] != st["focus"]:
        buttons.append(_form(ctx, "planning-focus", "Definir ahora", sp=s["id"], cls="outline"))
    if state != "confirmed":
        buttons.append(_form(ctx, "planning-confirm", "Confirmar subplan", sp=s["id"], disabled=bool(missing)))
    run = _run_button(ctx, s)
    note = ""
    if state == "confirmed":
        where = " en la conversación" if item.get("via") == "conversation" else " en la web" if item.get("via") else ""
        note = (f'Confirmado{where} {e((item.get("confirmed_at") or "")[:16].replace("T", " "))}. Si cambia, '
                "vuelve a pedir confirmación.")
    elif missing:
        note = "Para confirmarlo falta: " + e("; ".join(missing)) + "."
        import bt_page_planning as planning
        asked = planning._asking(ctx["rdir"])
        if asked and any(m.startswith("faltan entradas") for m in missing):          # the answer is one click away
            note += (f' <a data-nav href="{e(link(ctx["project"], ctx["rid"], ctx["opts"], view="asks"))}">'
                     f'Responde {asked} pregunta{"s" if asked != 1 else ""} abierta{"s" if asked != 1 else ""}</a>.')
    else:
        note = "Todo listo: revisa diseño, tareas, criterios y entradas, y confírmalo."
    return (f'<div class="pp-flow {e(state)}"><span class="pp-state {e(DOT[state])}">{e(STATE_ES[state])}</span>'
            f'<span class="pp-meta grow">{note}</span>{run}{"".join(buttons)}</div>')


def stage_info(ctx: dict) -> dict:
    """The approved stages (D-134), computed once per fragment."""
    if "stages" not in ctx:
        import bt_stages
        ctx["stages"] = bt_stages.info(ctx["rdir"])
    return ctx["stages"]


def _run_button(ctx: dict, s: dict) -> str:
    """«Ejecutar subplan» next to the confirmation (D-134): the Scheduler runs this confirmed subplan as part of the
    approved stage while the rest of the plan is still being defined; once it is in a stage, a link to the run."""
    import bt_subplan_sessions as sessions
    import bt_page_planning as planning
    live = sessions.active(ctx["rdir"], s["id"])
    if live:
        return (f'<a class="pp-chip info" data-nav href="{e(planning.link(ctx["project"], ctx["rid"], ctx["opts"], view="session"))}">'
                "Sesión abierta → ver</a>")
    info = stage_info(ctx)
    if s["id"] in info["held"]:
        return (f'<a class="pp-chip ok" href="{e(purl(ctx["project"], "req", ctx["rid"]))}?tab=run" '
                f'title="El Scheduler la ejecuta en la etapa r{info["revision"]}">En ejecución · etapa r{info["revision"]} → ver</a>')
    item = ctx["flow"]["subplans"].get(s["id"]) or {}
    if item.get("state") != "confirmed" or not s.get("tasks"):
        return ""
    return (f'<form method="post" action="{purl(ctx["project"], "req", ctx["rid"], "stage-run")}" class="pp-inline">'
            f'<input type="hidden" name="token" value="{e(ctx["token"])}"><input type="hidden" name="anchor" value="{e(s["id"])}">'
            f'<input type="hidden" name="lang" value="{e(ctx["opts"]["lang"])}"><button type="submit" class="outline" '
            'title="Aprueba este subplan como etapa y el Scheduler lo ejecuta (auditorías, verificación, estado durable) '
            'mientras sigues definiendo el resto">Ejecutar subplan</button></form>')


def inputs_panel(ctx: dict, s: dict) -> str:
    rows = sorted(flow.inputs_for(ctx["rdir"], s["id"], ctx["flow"]["inputs"]),  # this subplan's own first
                  key=lambda row: (not row["subplans"], not row["pending"]))
    if not rows:
        return ('<p class="pp-empty">No hay entradas registradas para este subplan. Las credenciales, rutas, hosts y '
                'cuentas que necesite van en la tabla <code>## Inputs</code> del SPEC, con su columna Subplan; nunca '
                "el valor de un secreto, solo dónde vive.</p>")
    return _inputs_table(rows, "")


def _inputs_table(rows: list[dict], title: str) -> str:
    if not rows:
        return ""
    body = "".join(f'<div class="pp-row"><span class="grow"><strong>{e(r["item"])}</strong><span class="pp-meta block">'
                   f'{e(r["where"] or "—")}{" · " + e(r["who"]) if r["who"] else ""}'
                   f'{" · todo el plan" if not r["subplan"] else ""}</span></span><span class="pp-chip '
                   f'{"warn" if r["pending"] else "ok"}">{e(r["status"] or "pendiente")}</span></div>' for r in rows)
    head = f"<h3>{e(title)}</h3>" if title else ""
    return f'{head}<div class="pp-rows">{body}</div>'


def check_rows(ctx: dict) -> list[str]:
    """Approval dialog rows under the flow: each subplan's confirmation and design."""
    out = []
    for s in ctx["subplans"]:
        dot, name = label(ctx, s["id"])
        row = ctx["rows"].get(s["ref"]) if s["ref"] else None
        design = f' · {s["ref"]} · {state_of(row)[1]}' if row else " · sin interfaz"
        mark = "✓" if dot == "ready" else "!" if dot == "changed" else "–"
        out.append(f'<div class="pp-check"><span class="pp-mark {"ready" if dot == "ready" else "none"}" '
                   f'aria-hidden="true">{mark}</span><span class="pp-id">{e(s["id"])}</span><span class="grow">'
                   f'{text(ctx, s["title"])}<span class="pp-meta block">{e(name + design)}</span></span></div>')
    return out
