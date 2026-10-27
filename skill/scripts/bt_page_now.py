"""`/now` and the global "Ahora" bar: every attempt alive at this moment, in every project.

Pure functions (data in, HTML out). `items` are `bt_live_api.now_items`. Durations and "hace N s" are server-rendered
once and then ticked by `assets/live.js` from the `data-since` / `data-ago` timestamps, so they keep moving between
events. A silent stream is shown grey as "sin actividad", never as dead: M4 owns that judgement.
"""
from __future__ import annotations

from html import escape as e
from urllib.parse import quote

import bt_page_attempts as attempts_
from bt_pages import layout

QUIET_AFTER_S = 60


def task_href(item: dict) -> str:
    return f'/plans/{quote(item["project"])}/{quote(item["req_id"])}#t-{quote(str(item["task"]))}'


def _since(a: dict) -> str:
    return (f'<span data-since="{e(a["started_at"])}">{attempts_.fmt_duration(a.get("duration_s"))}</span>'
            if a.get("started_at") else attempts_.fmt_duration(a.get("duration_s")))


def _ago(a: dict) -> str:
    stamp = a.get("last_activity_at")
    return f'<span data-ago="{e(stamp)}">—</span>' if stamp else "—"


def _quiet(a: dict) -> bool:
    return not a.get("last_activity_at")


def _doing(s: dict) -> str:
    if s["activity"] == "planning" and s.get("req"):
        return f'planificando {e(s["req"])} · {e(s.get("stage") or "plan")}'
    if s["activity"] == "building":
        return "implementando"
    return "trabajando" if s["state"] == "working" else "en espera"


def _agent_name(s: dict) -> str:
    return e(s.get("agent") or "agente")


def agent_card(s: dict) -> str:
    working = s["state"] == "working"
    quiet = " quiet" if (s.get("quiet") or not working) else ""
    where = e(s["project"] or "sin proyecto")
    owner = s.get("req_project") or s["project"]
    if s["activity"] == "planning" and s.get("req") and owner:
        where = f'<a href="/go/{quote(owner)}/{quote(s["req"])}">{e(owner)} · {e(s["req"])}</a>'
    since = (f'<span data-since="{_iso(s["since"])}">—</span>' if working and s.get("since") else "")
    return (f'<article class="ncard agent{quiet}" data-k="s-{e(s["session"])}">'
            f'<div class="nstate"><i class="dot {"info live" if working and not s.get("quiet") else ""}"></i>'
            f'{_doing(s)} {since}</div><div><div class="nwhere">{_agent_name(s)} · sesión {e(s["session"])}</div>'
            f'<div class="ntitle">{where}</div></div>'
            f'<div class="ntok"><span>{e(s.get("last_tool") or "—")}</span>'
            f'<span>actividad <span data-ago="{_iso(s["last_event_at"])}">—</span></span></div>'
            f'{steps_html(s.get("steps") or [])}</article>')


def steps_html(steps: list[dict]) -> str:
    """What the session did lately, newest first; the first line is what it is doing right now."""
    if not steps:
        return ""
    rows = "".join(f'<li><span class="nago" data-ago="{_iso(x["at"])}">—</span><span>{e(x["text"])}</span></li>'
                   for x in steps)
    return f'<ol class="nsteps" aria-label="últimos pasos">{rows}</ol>'


def _iso(epoch: float) -> str:
    import datetime as dt
    return dt.datetime.fromtimestamp(epoch, dt.timezone.utc).isoformat().replace("+00:00", "Z")


def agents_html(agents: list[dict]) -> str:
    live = [s for s in agents if s["state"] == "working"]
    if not live:
        return '<p class="muted nempty">Ningún agente está trabajando ahora mismo.</p>'
    return "".join(agent_card(s) for s in live)


def verify_html(verify: list[dict]) -> str:
    """Subplans finished and waiting for the owner to try them, one card per requirement."""
    if not verify:
        return '<p class="muted nempty">No hay subplanes esperando que los pruebes.</p>'
    cards = []
    for v in verify:
        href = (f'/p/{quote(v["project"])}/req/{quote(v["req"])}?tab=plan&mode=subplans&view=verify&sp='
                f'{quote(v["subplans"][0])}')
        cards.append(f'<article class="ncard verify" data-k="v-{e(v["project"])}-{e(v["req"])}"><div class="nstate">'
                     f'<i class="dot warn"></i>por probar</div><div><div class="nwhere">{e(v["project"])} · {e(v["req"])}</div>'
                     f'<a class="ntitle" href="{e(href)}">{e(", ".join(v["subplans"]))}</a></div>'
                     f'<div class="ntok"><span>aprobados {v["approved"]}/{v["total"]}</span>'
                     f'<a href="{e(href)}">Probar →</a></div></article>')
    return "".join(cards)


def health_html(health: list[dict]) -> str:
    """Agents that died, went quiet or failed, one card each, worst first."""
    import bt_agent_health as h
    if not health:
        return '<p class="muted nempty">Todos los agentes que lanzó la metodología responden.</p>'
    cards = []
    for a in health:
        bad = a["state"] in h.BAD
        where = f'{a["project"]} · {a["req"]}'.strip(" ·") or a["id"]
        href = f'/p/{quote(a["project"])}/req/{quote(a["req"])}?tab=plan' if a["project"] and a["req"] else "/now"
        cards.append(f'<article class="ncard health" data-k="h-{e(a["id"])}"><div class="nstate"><i class="dot {"bad" if bad else "warn"}"></i>'
                     f'{e(h.STATE_ES[a["state"]])}</div><div><div class="nwhere">{e(where)}</div>'
                     f'<a class="ntitle" href="{e(href)}">{e(a["who"])}</a><p class="muted">{e(a["detail"])}</p></div>'
                     f'<div class="ntok"><span>{e(h.ago(a["since"]))}</span><span>{e(a.get("model", ""))}</span></div></article>')
    return "".join(cards)


def bar_html(items: list[dict], agents: list[dict] = (), verify: list[dict] = (), health: list[dict] = ()) -> str:
    """The strip under the header: one chip per live attempt or working agent; empty string when nothing runs."""
    working = [s for s in agents if s["state"] == "working" and not s.get("quiet")]
    if not items and not working and not verify and not health:
        return ""
    chips = "".join(
        f'<a class="nchip" href="{e(task_href(i))}" title="{e(i["task_title"] or "")}">'
        f'<i class="dot info live"></i>{e(i["req_id"])} {e(str(i["task"]))} · '
        f'{e(i["attempt"].get("model_requested") or "—")} · {_since(i["attempt"])}</a>' for i in items[:6])
    chips += "".join(
        f'<a class="nchip" href="/now" title="sesión {e(s["session"])}"><i class="dot info live"></i>'
        f'{_agent_name(s)} · {e(s["project"] or "?")} · {_doing(s)}</a>' for s in working[:4])
    chips += "".join(
        f'<a class="nchip" href="/p/{quote(v["project"])}/req/{quote(v["req"])}?tab=plan&mode=subplans&view=verify&sp='
        f'{quote(v["subplans"][0])}" title="Subplanes terminados que esperan tu prueba"><i class="dot warn"></i>'
        f'{e(v["req"])} · {e(", ".join(v["subplans"][:3]))} por probar</a>' for v in list(verify)[:3])
    chips = "".join(
        f'<a class="nchip" href="/now" title="{e(a["detail"])}"><i class="dot {"bad" if a["state"] in ("died", "exited", "failed", "never_started") else "warn"}"></i>'
        f'⚠ {e(a["who"])} {e({"died": "murió", "exited": "se cerró", "failed": "falló", "never_started": "no arrancó", "quiet": "sin señales"}[a["state"]])}</a>'
        for a in list(health)[:3]) + chips
    total = len(items) + len(working) + len(verify) + len(health)
    more = f'<span class="muted">+{len(items) - 6}</span>' if len(items) > 6 else ""
    return (f'<b class="nlabel">Ahora <sl-badge variant="primary" pill pulse>{total}</sl-badge></b>{chips}{more}'
            f'<a class="nall" href="/now">Ver todo →</a>')


def card_html(i: dict) -> str:
    a = i["attempt"]
    state = "verificando" if i["state"] == "verifying" else "trabajando"
    quiet = " quiet" if _quiet(a) else ""
    pct = round(100 * i["progress"]["done"] / i["progress"]["total"]) if i["progress"]["total"] else 0
    return (
        f'<article class="ncard{quiet}" data-k="n-{e(i["project"])}-{e(i["req_id"])}-{e(str(i["task"]))}">'
        f'<div class="nstate"><i class="dot {"info live" if not quiet else ""}"></i>{state} · {_since(a)}</div>'
        f'<div><div class="nwhere">{e(i["project"])} · {e(i["req_id"])} · {e(str(i["task"]))}</div>'
        f'<a class="ntitle" href="{e(task_href(i))}">{e(i["task_title"] or i["task"])}</a></div>'
        f'<div class="nchips">{attempts_.model_chip(a.get("provider"), a.get("model_requested"), a.get("effort"))}'
        f'<span class="chip">{e(a.get("account") or "—")}</span><span class="chip">intento {e(str(a.get("number") or "?"))}</span></div>'
        f'<div><div class="ntok"><span>{attempts_.tokens_html(a.get("tokens"))} tokens</span>'
        f'<span>{"actividad " if not quiet else "sin actividad registrada · "}{_ago(a)}</span></div>'
        f'<sl-progress-bar value="{pct}" aria-label="avance del plan"></sl-progress-bar></div>'
        f'<div class="nplan">plan {i["progress"]["done"]}/{i["progress"]["total"]} tareas{_stage(i)}</div></article>')


def _stage(i: dict) -> str:
    """' · etapa SP-1 · faltan 12 subplanes' while the plan runs in stages (D-134)."""
    stage = i.get("stage") if isinstance(i.get("stage"), dict) else None
    if not stage or stage.get("complete"):
        return ""
    return e(f' · etapa {", ".join(str(x) for x in stage.get("subplans") or [])} · faltan {len(stage.get("outside") or [])} subplanes')


def cards_html(items: list[dict]) -> str:
    if not items:
        return '<p class="muted nempty">Nada se está ejecutando ahora mismo.</p>'
    return "".join(card_html(i) for i in items)


def fragments(items: list[dict], agents: list[dict] = (), verify: list[dict] = (), health: list[dict] = ()) -> dict[str, str]:
    return {"bar": bar_html(items, agents, verify, health), "health": health_html(list(health)), "cards": cards_html(items), "agents": agents_html(list(agents)),
            "verify": verify_html(list(verify))}


def now_page(items: list[dict], agents: list[dict] = (), verify: list[dict] = (), health: list[dict] = ()) -> str:
    body = (f'<div class="head"><div><p class="eyebrow">en vivo</p><h1>Ahora</h1></div></div>'
            f'<p class="muted">Cada tarjeta es un intento vivo del Scheduler, de todos los proyectos. Los tokens y el '
            f'tiempo se actualizan solos; «sin actividad» no significa caído: lo decide el monitor.</p>'
            f'<h2 class="nsec">Salud de los agentes</h2>'
            f'<p class="muted">Agentes que lanzó la metodología y murieron, no dan señales o fallaron.</p>'
            f'<div class="ngrid" id="now-health">{health_html(list(health))}</div>'
            f'<h2 class="nsec">Agentes en sesión</h2>'
            f'<p class="muted">Quién está trabajando ahora, incluso si todavía no hay un plan que ejecutar '
            f'(entrevista, especificación, plan).</p><div class="ngrid" id="now-agents">{agents_html(list(agents))}</div>'
            f'<h2 class="nsec">Subplanes por probar</h2>'
            f'<p class="muted">Terminados por el Scheduler: el plan no se cierra hasta que pruebes y apruebes cada uno.</p>'
            f'<div class="ngrid" id="now-verify">{verify_html(list(verify))}</div>'
            f'<h2 class="nsec">Intentos del Scheduler</h2>'
            f'<div class="ngrid" id="now-cards">{cards_html(items)}</div>')
    return layout("Ahora", body, [("Ahora", "/now")])
