"""«¿Qué está haciendo el agente?» for the Plan tab: the planning session's state and last steps, from the presence feed.

A web confirmation never reaches an idle agent, and a subplan marked «Definir ahora» only means it is the focus, not
that anyone is working on it. This strip says what the agent is really doing (or that it is waiting, and for how long),
so the owner is not left guessing. Pure function: HTML out; times are rounded so the live block does not churn.
"""
from __future__ import annotations

import time
from html import escape as e
from pathlib import Path

import bt_agent_terminal as terminal
import bt_presence as presence
import bt_subplan_sessions as sessions
from bt_pages import purl

IDLE_HINT_S = 120
SCREEN_LINES = 30


def _ago(seconds: float) -> str:
    seconds = max(0, int(seconds))
    if seconds < 60:
        return "hace menos de 1 min"                     # coarse on purpose: a label that changes every few seconds makes the live block churn
    minutes = seconds // 60
    return f"hace {minutes} min" if minutes < 90 else f"hace {minutes // 60} h"


def planning_sessions(root: Path, project: str, req: str, now: float | None = None, rdir: Path | None = None) -> list[dict]:
    """Sessions planning this requirement. When the Planner's own conversation is known (`.planning/planner.json`) only it
    counts: another agent that merely ran a `planning` command on the requirement (this very tool, a reviewer) is not it."""
    found = [s for s in presence.sessions(root, now)
             if s["req"] == req and s["req_project"] == project and s["activity"] == "planning"]
    known = str((terminal._record(rdir).get("session_id") if rdir else "") or "")[:8]
    return ([s for s in found if s["session"] == known] if known else found)[:2]


def _pop(label: str, body: str, cls: str = "") -> str:
    """A small menu button whose panel floats over the page instead of pushing it down."""
    return f'<details class="pp-pop-menu {cls}"><summary>{e(label)}</summary><div class="pp-pop-body">{body}</div></details>'


def _open_round(ctx: dict) -> int:
    import bt_rounds
    current = bt_rounds.open_round(ctx["rdir"]) if bt_rounds.rounds_dir(ctx["rdir"]).exists() else None
    return int(bt_rounds.load(current).get("round") or 0) if current else 0


def strip(ctx: dict, now: float | None = None) -> str:
    """One slim line: who, what it is doing, and menus for its steps, its screen and restarting it."""
    now = time.time() if now is None else now
    req = ctx["rid"]
    found = planning_sessions(ctx["root"], ctx["project"], req, now, ctx.get("rdir"))
    focus = (ctx.get("flow") or {}).get("focus") or ""
    reachable = any(item["kind"] == "planner" for item in terminals(ctx))
    asking = _open_round(ctx)
    menus = ""
    steps: list[dict] = []
    if not found and reachable:
        tone, text = "wait", "Planner abierto desde la web · todavía sin señales (arrancando o leyendo el plan)"
    elif not found:
        tone, text = "off", "Ningún agente está planificando ahora mismo"
        menus = _pop("Abrir un Planner", open_planner(ctx), "end")
    else:
        s = found[0]
        age = now - s["last_event_at"]
        steps = s["steps"][:8]
        if s["state"] == "working" and not s["quiet"]:
            tone, text = "work", f'Planner · Trabajando{" · " + steps[0]["text"] if steps else ""}'
        elif s["state"] == "working":
            tone, text = "wait", f"Planner · Sin señales {_ago(age)} (puede estar pensando o atascado)"
        else:
            tone, text = "idle", f"Planner · Esperando · inactivo {_ago(age)}"
            if asking:
                text += f" · espera tus respuestas de la ronda {asking}"
            elif age > IDLE_HINT_S:
                text += (f" · no sabe qué haces en la web: escríbele" if reachable else " · escríbele en su ventana")
    if steps:
        items = "".join(f'<li><time>{e(_ago(now - x["at"]))}</time> {e(x["text"])}</li>' for x in steps)
        menus += _pop(f"Pasos ({len(steps)})", f'<ol class="pp-ag-steps-list">{items}</ol>')
    for item in terminals(ctx):
        shown = terminal.screen(item["name"], SCREEN_LINES) or "(la pantalla está vacía)"
        menus += _pop(f"Pantalla de {item['label']}" if len(terminals(ctx)) > 1 else "Pantalla", f'<pre class="pp-term">{e(shown)}</pre>')
    if reachable:
        menus += _pop("Reiniciar", open_planner(ctx), "end")
    return (f'<section class="pp-agent" data-k="agent" aria-label="Estado del agente"><span class="pp-ag-dot {tone}"></span>'
            f'<span class="pp-ag-text">{e(text)}</span><span class="pp-ag-menus">{menus}</span>{_health(ctx)}</section>')


def _health(ctx: dict) -> str:
    """Designers and other delegations working on this requirement, and anything that died or went quiet."""
    import bt_agent_health as health
    rows = health.agents()
    mine = [a for a in rows if a["req"] == ctx["rid"] and a["project"] == ctx["project"] and a["kind"] == "delegation"]
    out = []
    for a in mine:
        if a["state"] in ("working", "quiet"):
            out.append((a["state"], f'{a["who"]} · {health.STATE_ES[a["state"]]} · {a["detail"]}'))
        elif a["state"] in health.BAD:
            out.append(("bad", f'{a["who"]} · {health.STATE_ES[a["state"]]} {health.ago(a["since"])}: {a["detail"]}'))
    if not out:
        return ""
    items = "".join(f'<span class="pp-ag-health {e(tone)}"><span class="pp-ag-dot {"work" if tone == "working" else "wait" if tone == "quiet" else "bad"}"></span>{e(text)}</span>'
                    for tone, text in out)
    return f'<span class="pp-ag-healthrow">{items}</span>'


def terminals(ctx: dict) -> list[dict]:
    """Agents running in a tmux session the web can read and type into: the Planner and the selected subplan's session."""
    found = []
    name = terminal.name_for(ctx["project"], ctx["rid"], "planner")
    if terminal.exists(name):
        found.append({"label": "Planner", "name": name, "kind": "planner", "anchor": ""})
    sid = (ctx.get("opts") or {}).get("sp") or ""
    live = sessions.active(ctx["rdir"], sid) if sid else None
    if live and terminal.exists(live.get("tmux") or ""):
        found.append({"label": f"Sesión con el usuario · {sid}", "name": live["tmux"], "kind": "session", "anchor": sid})
    return found


def _form(ctx: dict, action: str, label: str, fields: str = "", cls: str = "") -> str:
    return (f'<form method="post" action="{purl(ctx["project"], "req", ctx["rid"], action)}" class="pp-vform">'
            f'<input type="hidden" name="token" value="{e(ctx["token"])}">{fields}'
            f'<button type="submit" class="{e(cls)}">{e(label)}</button></form>')


def screens(ctx: dict) -> str:
    """What each web-reachable agent shows right now (inside the live strip: it changes every few seconds)."""
    out = []
    for item in terminals(ctx):
        text = terminal.screen(item["name"], SCREEN_LINES) or "(la pantalla está vacía)"
        out.append(f'<details class="pp-ag-screen"><summary>Pantalla de {e(item["label"])}</summary>'
                   f'<pre class="pp-term">{e(text)}</pre></details>')
    return "".join(out)


def open_planner(ctx: dict) -> str:
    """Offer to start a Planner the web can talk to when none is running, or to restart the running one."""
    if any(item["kind"] == "planner" for item in terminals(ctx)):
        return ('<p class="pp-meta">¿Se atascó o quieres una sesión fresca? Se reabre sobre la misma conversación y sus notas: '
                'no pierde nada.</p>' + _form(ctx, "agent-restart", "Reiniciar el Planner"))
    return ('<p class="pp-meta">Este plan no tiene un Planner con el que puedas hablar desde la web. '
            'Si ya hubo uno, retoma su conversación anterior y sus notas. Si hay otro abierto en una ventana, ciérralo antes: dos Planners a la vez se pisan.</p>'
            + _form(ctx, "agent-start", "Abrir un Planner para este plan", cls="pp-approve"))


def say(ctx: dict) -> str:
    """The text box, one line tall until focused. A separate block from the live strip on purpose: its HTML only changes
    when an agent appears or goes away, so the page never swaps it while the owner is typing."""
    items = terminals(ctx)
    if not items:
        return '<div data-k="agent-say" hidden></div>'
    forms = []
    for item in items:
        fields = (f'<input type="hidden" name="kind" value="{e(item["kind"])}"><input type="hidden" name="anchor" '
                  f'value="{e(item["anchor"])}"><textarea name="text" rows="1" maxlength="{terminal.MAX_SAY}" required '
                  f'placeholder="Escríbele al {e(item["label"])}…" title="Llega como si lo escribieras en su ventana" '
                  f'aria-label="Mensaje para {e(item["label"])}"></textarea>')
        forms.append(_form(ctx, "agent-say", "Enviar", fields))
    return f'<section class="pp-agent-say" data-k="agent-say" aria-label="Hablar con el agente">{"".join(forms)}</section>'
