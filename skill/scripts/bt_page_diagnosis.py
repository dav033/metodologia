"""The diagnosis panel of a decision card: what failed, its origin, how to fix it, the option to pick.

One renderer for the plan page (server side) and /flow (which receives it as `diagnosis_html` in the plan status API
and adds its own forms). The rules' diagnosis (`bt_block_diagnosis`) shows at once; the agent's (`bt_block_agent`) when
it arrives, with a button to ask for it or ask again. Technical detail stays folded underneath.
"""
from __future__ import annotations

import re
from html import escape

ICONS = {"conflict": "⇄", "plan": "▤", "environment": "⚙", "dependency": "⧉", "code": "‹›", "quota": "◔",
         "cancelled": "⊘", "verifier": "◎", "manual": "✋", "integrity": "⚠", "unknown": "?"}
CODE = re.compile(r"`([^`]+)`")


def _rich(text: str) -> str:
    """Escaped text where `code` spans become <code>."""
    return CODE.sub(lambda m: f"<code>{m.group(1)}</code>", escape(text or ""))


def _label(request: dict, option: str) -> str:
    return next((o["label"] for o in request.get("options") or [] if o["id"] == option), option)


def panel(request: dict, d: dict, title: str) -> str:
    steps = "".join(f"<li>{_rich(s)}</li>" for s in d.get("steps") or [])
    pick = (f'<p class="dx-pick">Elige: <b>{escape(_label(request, d["option"]))}</b>'
            + (f' — con esta indicación ya escrita abajo' if d.get("note") else "") + "</p>") if d.get("option") else ""
    return (f'<div class="dx dx-{escape(d.get("tone", "muted"))}"><div class="dx-top">'
            f'<span class="dx-chip"><span aria-hidden="true">{ICONS.get(d.get("kind"), "?")}</span> {escape(d.get("label", ""))}</span>'
            f'<span class="dx-src">{escape(title)} · confianza {escape(d.get("confidence", ""))}</span></div>'
            f'<p class="dx-head">{_rich(d.get("headline", ""))}</p>'
            f'<div class="dx-sec"><span class="dx-k">De dónde viene</span><p>{_rich(d.get("origin", ""))}</p></div>'
            f'<div class="dx-sec"><span class="dx-k">Cómo solucionarlo</span><ol>{steps}</ol></div>{pick}</div>')


def ask_button(request: dict, again: bool = False) -> str:
    """A button the page wires to «diagnose this request» (data-diagnose)."""
    label = "Pedir otra vez al agente" if again else "Pedir diagnóstico al agente"
    return f'<button type="button" class="dx-ask" data-diagnose="{escape(request["id"])}">{label}</button>'


def agent_state(request: dict, ask: str) -> str:
    """The agent's line under the main panel: working, failed (and why) or the button to ask."""
    a = request.get("agent") or {}
    if a.get("state") == "running":
        model = f" ({escape(a['model'])})" if a.get("model") else ""
        return f'<p class="dx-agent dx-running"><i class="dx-spin" aria-hidden="true"></i> El agente{model} está leyendo la evidencia…</p>'
    if a.get("state") == "failed":
        return f'<p class="dx-agent">El agente no pudo diagnosticar: {escape(a.get("error", ""))[:300]} {ask}</p>'
    if a.get("state") == "done":
        return f'<p class="dx-agent">{ask}</p>'
    return f'<p class="dx-agent">¿No te queda claro? {ask}</p>'


def _fallback(request: dict) -> dict | None:
    """A request without a diagnosis (an older payload) still shows what it needs and what can be done."""
    if not request.get("what"):
        return None
    return {"kind": "unknown", "label": "Sin identificar", "tone": "muted", "headline": request["what"],
            "origin": request.get("needs", ""), "steps": list(request.get("you_can") or []),
            "option": request.get("recommended", ""), "confidence": "baja"}


def html(request: dict, ask: str | None = None) -> str:
    """The whole panel; `ask` replaces the default data-diagnose button (the plan page posts a form instead)."""
    rule, agent = request.get("diagnosis") or _fallback(request), request.get("agent") or {}
    done = agent if agent.get("state") == "done" else None
    if ask is None:
        ask = ask_button(request, again=bool(done))
    parts = []
    if done and (not rule or rule.get("confidence") != "alta"):
        parts.append(panel(request, done, f"diagnóstico del agente · {done.get('model', '')}"))
        if rule:
            parts.append(f'<details class="dx-more"><summary>Lo que dicen las reglas</summary>{panel(request, rule, "reglas")}</details>')
    else:
        if rule:
            parts.append(panel(request, rule, "diagnóstico automático"))
        if done:
            parts.append(f'<details class="dx-more"><summary>Segunda opinión del agente ({escape(done.get("model", ""))})</summary>'
                         f'{panel(request, done, "agente")}</details>')
    parts.append(agent_state(request, ask))
    detail = []
    if request.get("error"):
        detail.append(f'<pre class="dx-err">{escape(request["error"])}</pre>')
    if request.get("evidence"):
        detail.append("<ul>" + "".join(f"<li>{escape(x)}</li>" for x in request["evidence"][:8]) + "</ul>")
    if detail:
        parts.append(f'<details class="dx-more"><summary>Error técnico y evidencia</summary>{"".join(detail)}</details>')
    return "".join(parts)


def note_for(request: dict) -> str:
    """The indication to prefill in the retry_with_note box: the agent's when it gave one, else the rules'."""
    for d in (request.get("agent") or {}, request.get("diagnosis") or {}):
        if d.get("state", "done") == "done" and d.get("option") == "retry_with_note" and d.get("note"):
            return d["note"]
    return ""


def headline(request: dict) -> str:
    agent = request.get("agent") or {}
    d = agent if agent.get("state") == "done" else request.get("diagnosis") or {}
    return d.get("headline", "")

