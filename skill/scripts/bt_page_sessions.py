"""The «Sesión» tab of a subplan: work on it WITH an agent in a window of its own (data in `bt_subplan_sessions`).

Pure functions: HTML out, no writes. The actions post to `/p/<project>/req/<REQ>/session-start|session-finish`.
"""
from __future__ import annotations

from html import escape as e
from pathlib import Path

import bt_subplan_sessions as sessions
from bt_pages import purl

STATUS_ES = {"running": "En marcha", "finished": "Terminada", "closed": "Cerrada sin terminar"}


def tab_label(rdir: Path, sid: str) -> str:
    live = sessions.active(rdir, sid)
    return "Sesión · en marcha" if live else ("Sesión ✓" if sessions.sessions(rdir, sid) else "Sesión")


def _form(ctx: dict, action: str, label: str, sid: str, *, picker: bool = False, cls: str = "", mode: str = "") -> str:
    models = ""
    if picker:
        options = "".join(f'<option value="{k}"{" selected" if k == sessions.DEFAULT_MODEL else ""}>{e(v[2])}</option>'
                          for k, v in sessions.MODELS.items())
        models = f'<label class="pp-vlabel">Agente <select name="model">{options}</select></label>'
    return (f'<form method="post" action="{purl(ctx["project"], "req", ctx["rid"], action)}" class="pp-vform">'
            f'<input type="hidden" name="token" value="{e(ctx["token"])}"><input type="hidden" name="anchor" value="{e(sid)}">'
            f'{f"<input type=hidden name=mode value={mode}>" if mode else ""}'
            f'{models}<button type="submit" class="{e(cls)}">{e(label)}</button></form>')


def _card(item: dict) -> str:
    rows = [("Rama", f'<code>{e(item["branch"])}</code>'), ("Copia de trabajo", f'<code>{e(item["worktree"])}</code>'),
            ("Agente", e(item.get("agent", ""))), ("Desde", f'<code>{e(item["base"])}</code> · {e(item["base_sha"][:10])}'),
            ("Commits en la rama", str(item.get("commits", item["ahead"]))),
            ("Archivos sin commit", str(item.get("uncommitted", item["dirty"])))]
    if item["status"] == "running":
        rows.append(("Agente", "en marcha: escríbele desde el cuadro «Hablar con el agente» de arriba" if item["window"] else "ya no está en marcha: puedes terminar la sesión o abrir otra"))
    body = "".join(f"<div><span class=\"pp-vlabel\">{e(k)}</span><p>{v}</p></div>" for k, v in rows)
    state = STATUS_ES.get(item["status"], item["status"]) + (" · ejecución autónoma" if item.get("mode") == "auto" else " · con el usuario")
    return (f'<article class="pp-vwhere {"local" if item["status"] == "running" else "none"}"><header>'
            f'<strong>{e(state)}</strong><span class="pp-meta">{e(item["started_at"][:16].replace("T", " "))}</span></header>'
            f'{body}</article>')


def panel(ctx: dict, s: dict) -> str:
    rdir, sid = ctx["rdir"], s["id"]
    history = [sessions.info(x) for x in sessions.sessions(rdir, sid)]
    live = next((x for x in history if x["status"] == "running"), None)
    intro = ('<p class="pp-vintro">Construye este subplan ya, sin esperar a que todo el plan esté aprobado. Un agente trabaja en una '
             'copia aparte del código (rama propia, partiendo de <code>origin/main</code>); no publica, no fusiona ni despliega '
             'nada. El resultado es una rama que tú revisas y que el Planner usa al armar las tareas finales.</p>')
    note = ('<p class="pp-meta">Esta sesión no es el Scheduler: el resultado es una rama que el Planner usa al definir las '
            'tareas. Para que el subplan lo construya el Scheduler (auditorías, verificación, estado durable), confírmalo y '
            'pulsa «Ejecutar subplan».</p>')
    if live and live["exists"]:
        who = "La sesión está abierta"
        actions = (f'<div class="pp-vactions"><p>{who}. Mira su pantalla o escríbele desde la barra de arriba.</p><div class="pp-vbuttons">'
                   f'{_form(ctx, "session-finish", "Terminar y registrar la rama", sid, cls="pp-approve")}</div>'
                   f'<p class="pp-meta">Al terminar se registra la rama y su último commit; la copia no se borra.</p></div>')
    else:
        hands = _form(ctx, "session-start", "Trabajar contigo, paso a paso", sid, picker=True, cls="outline", mode="hands")
        actions = (f'<div class="pp-vactions"><div class="pp-vbuttons wide">{hands}</div>{note}</div>')
    cards = "".join(_card(x) for x in reversed(history))
    return f'<section class="pp-verify">{intro}{actions}{("<h3>Ejecuciones y sesiones de este subplan</h3>" + cards) if cards else ""}</section>'
