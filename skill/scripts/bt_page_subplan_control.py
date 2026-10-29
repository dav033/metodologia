"""The subplan's control block on the Plan tab: its flow, what waits for the owner (with the action at hand), what blocks it
and who resolves it, which agent works on it now, what changed (marked new since the owner's last visit by the browser)
and the decisions already taken. Data: `bt_subplan_status`."""
from __future__ import annotations

import datetime as dt
import time
from html import escape as e

import bt_subplan_status as status_model
from bt_pages import purl

WHO = {"Planner": "planner", "Designer": "designer", "Tú": "you", "Ejecución": "run"}
NOW_PREFIX = {"you": "Te toca", "working": "Trabajando", "blockers": "Falta"}
DEFAULT = {"define": "El Planner define sus tareas, criterios y pruebas.", "design": "Diseño en marcha.",
           "confirm": "Listo para que lo revises y lo confirmes.", "run": "Confirmado.",
           "verify": "Construido: pruébalo y apruébalo.", "done": "Aprobado: no falta nada en este subplan."}
STEP_ES = {"done": "hecho", "now": "en curso", "todo": "pendiente", "skip": "no aplica"}


def _ago(stamp: str) -> str:
    try:
        seconds = time.time() - dt.datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp()
    except (AttributeError, ValueError):
        return ""
    minutes = int(max(seconds, 0) // 60)
    if minutes < 1:
        return "ahora"
    if minutes < 60:
        return f"hace {minutes} min"
    hours = minutes // 60
    return f"hace {hours} h" if hours < 48 else f"hace {hours // 24} días"


def _time(stamp: str) -> str:
    ago = _ago(stamp)
    return f'<time datetime="{e(stamp)}">{e(ago)}</time>' if ago else ""


def _clip(text: str, limit: int = 220) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def _href(ctx: dict, sid: str, view: str) -> str:
    import bt_page_planning as planning
    if view == "req-run":
        return f'{purl(ctx["project"], "req", ctx["rid"])}?tab=run'
    return planning.link(ctx["project"], ctx["rid"], ctx["opts"], view=view, sp=sid, mode="subplans")


def _action(ctx: dict, s: dict, item: dict, run_form: str) -> str:
    if item["action"] == "confirm":
        import bt_page_planning_flow as flow_view
        return flow_view._form(ctx, "planning-confirm", "Confirmar y ejecutar", sp=s["id"],
                               title="Lo confirma y lo manda al Scheduler: se ejecuta ya, o queda en cola hasta que los "
                                     "subplanes que necesita se ejecuten y los apruebes en «Probar»")
    if item["action"] == "run":
        return run_form
    nav = "" if item["view"] == "req-run" else " data-nav"
    return f'<a class="sc-go" href="{e(_href(ctx, s["id"], item["view"]))}"{nav}>{e(item["action"])} →</a>'


def _card(kind: str, title: str, rows: list[str], empty: str) -> str:
    count = f'<span class="sc-n">{len(rows)}</span>' if rows else ""
    body = f'<ul>{"".join(rows)}</ul>' if rows else f'<p class="sc-empty">{e(empty)}</p>'
    return f'<section class="sc-card {kind}{" has" if rows else ""}"><h3>{e(title)}{count}</h3>{body}</section>'


def _top(ctx: dict, s: dict) -> tuple[str, str]:
    """(buttons for the header, the «Ejecutar subplan» form when it belongs in «Te toca a ti»)."""
    flow = ctx.get("flow")
    if not flow or flow["phase"] in ("interview", "outline") or \
            ctx.get("status") in ("approved", "launched", "in-progress", "done"):
        return "", ""
    import bt_page_planning_flow as flow_view
    item = flow["subplans"].get(s["id"]) or {"state": "pending"}
    pill = f'<span class="pp-state {e(flow_view.DOT[item["state"]])}">{e(flow_view.STATE_ES[item["state"]])}</span>'
    focus = (flow_view._form(ctx, "planning-focus", "Definir ahora", sp=s["id"], cls="outline")
             if item["state"] != "confirmed" and s["id"] != flow["focus"] else "")
    run = flow_view._run_button(ctx, s)
    if "stage-run" in run:
        return pill + focus, run
    return pill + focus + run, ""


def block(ctx: dict, s: dict) -> str:
    st = status_model.statuses(ctx)[s["id"]]
    buttons, run_form = _top(ctx, s)
    steps = "".join(f'<li class="{"na" if x["state"] == "skip" else e(x["state"])}"{" aria-current=step" if x["key"] == st["current"] else ""}>'
                    f'<span class="sc-dot" aria-hidden="true"></span>{e(x["label"])}'
                    f'<span class="sr"> ({STEP_ES[x["state"]]})</span></li>' for x in st["steps"])
    you = [f'<li><span class="sc-what">{e(_clip(i["text"]))}</span>{_action(ctx, s, i, run_form)}</li>' for i in st["you"]]
    blockers = [f'<li><span class="sc-who {WHO.get(b["who"], "run")}">{e(b["who"])}</span>'
                f'<span class="sc-what">{e(_clip(b["text"]))}</span></li>' for b in st["blockers"]]
    working = [f'<li><span class="sc-pulse" aria-hidden="true"></span><span class="sc-what"><strong>{e(w["who"])}</strong> '
               f'{e(_clip(w["text"]))}</span>{_time(w.get("since") or "")}</li>' for w in st["working"]]
    kind, first = next(((k, st[k][0]) for k in ("you", "working", "blockers") if st[k]), (None, None))
    if first is None:
        now = DEFAULT[st["current"]]
        if st["current"] == "run" and st["tasks"]["total"]:
            now = f'Ejecución: {st["tasks"]["done"]} de {st["tasks"]["total"]} tareas hechas.'
    else:
        text = first["text"] if kind != "working" else f'{first["who"]} {first["text"]}'
        now = f"{NOW_PREFIX[kind]}: {_clip(text, 160)}"
    news = "".join(f'<li data-at="{e(ev.get("at") or "")}">{_time(ev.get("at") or "")}'
                   f'<span class="sc-who {WHO.get(str(ev.get("who") or "").split(" ")[0], "run")}">{e(ev.get("who") or "")}'
                   f'</span><span class="sc-what">{e(_clip(ev.get("text") or "", 180))}</span></li>' for ev in st["news"][:6])
    decisions = "".join(f'<li>{_time(d["when"])}<span class="sc-what">{e(_clip(d["text"], 260))}</span></li>'
                        for d in st["decisions"])
    more = ('<div class="sc-more"><section class="sc-news" aria-label="Novedades del subplan"><h3>Novedades '
            '<span class="sc-new" data-sc-newcount hidden></span></h3>'
            + (f'<ol>{news}</ol>' if news else '<p class="sc-empty">Todavía no hay movimiento en este subplan.</p>') +
            f'</section><details class="sc-dec"><summary>Decisiones tomadas ({len(st["decisions"])})</summary>'
            + (f'<ol>{decisions}</ol>' if decisions else '<p class="sc-empty">Aún no hay decisiones registradas.</p>') +
            "</details></div>")
    return (f'<section class="sc" aria-label="Estado de {e(s["id"])}" data-k="control-{e(s["id"])}" '
            f'data-sc-sp="{e(s["id"])}" data-sc-latest="{e(st["latest"])}">'
            f'<div class="sc-top"><ol class="sc-steps" aria-label="Flujo del subplan">{steps}</ol>'
            f'<div class="sc-actions">{buttons}</div></div>'
            f'<p class="sc-now" role="status">{e(now)}</p><div class="sc-cols">'
            + _card("you", "Te toca a ti", you, "Nada pendiente de ti en este subplan.")
            + _card("stop", "Falta para avanzar", blockers, "Nada lo frena ahora.")
            + _card("work", "Trabajando ahora", working, "Ningún agente trabaja en él en este momento.")
            + f"</div>{more}</section>")


def badge(ctx: dict, sid: str) -> str:
    """For the subplan list: how many things wait for the owner, and the newest change for the «nuevo» mark."""
    st = status_model.statuses(ctx).get(sid)
    if not st:
        return ""
    count = len(st["you"])
    mine = (f'<span class="sc-badge" title="{count} cosa{"s" if count != 1 else ""} te toca{"n" if count != 1 else ""} '
            f'en este subplan">{count}</span>') if count else ""
    return mine + f'<span class="sc-fresh" data-sc-latest="{e(st["latest"])}" data-sc-sp="{e(sid)}" hidden>nuevo</span>'
