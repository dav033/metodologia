"""The Solucionador's card on the run page and in a subplan's «Ejecución» tab (REQ-031 US-6): which session works on
which task and why, since when, how to watch it, and what the last ones did. Pure function: HTML out; every text comes
from run files, so everything is escaped."""
from __future__ import annotations

from html import escape as e

OUTCOME_ES = {"running": "trabajando", "fixed": "arreglado", "answered": "respondida", "asked_owner": "te pregunta",
              "gave_up": "no pudo"}
KIND_ES = {"decision": "decisión que la autocuración no resolvió", "repeat": "el mismo fallo volvió",
           "stuck": "tarea sin avance", "error": "run en error",
           "resolution": "conflicto de composición sin resolver"}


def card(state: dict | None, socket: str | None = None) -> str:
    if not state:
        return ""
    if socket is None:
        import bt_agent_terminal
        socket = bt_agent_terminal.socket()
    out = ['<h2 id="solver">Solucionador</h2><div class="ask">']
    active = state.get("active")
    if active:
        out.append(f'<p><span class="pill">{e(OUTCOME_ES["running"])}</span> <b>{e(str(active.get("task") or "run"))}</b>'
                   f' · {e(KIND_ES.get(str(active.get("kind")), str(active.get("kind"))))} · desde '
                   f'{e(str(active.get("started_at") or "")[11:16])} · {e(str(active.get("provider") or ""))} '
                   f'{e(str(active.get("model") or ""))}</p><p class="muted">{e(str(active.get("reason") or ""))}</p>'
                   f'<p class="muted">Míralo trabajar: <code>tmux -L {e(socket)} attach -t {e(str(active.get("name")))}'
                   f'</code> (sal con Ctrl-b d)</p>')
    else:
        out.append('<p class="muted">Ningún Solucionador trabaja ahora en este run.</p>')
    items = []
    for s in state.get("recent") or []:
        report = f' · <a href="{e(s["report_url"])}">informe</a>' if s.get("report_url") else ""
        question = f'<br><b>Pregunta:</b> {e(str(s["question"]))}' if s.get("question") else ""
        items.append(f'<li><span class="pill">{e(OUTCOME_ES.get(str(s.get("status")), str(s.get("status"))))}</span> '
                     f'<b>{e(str(s.get("task") or "run"))}</b> · {e(str(s.get("ended_at") or s.get("started_at") or "")[:16])}'
                     f' · {e(str(s.get("summary") or ""))}{report}{question}</li>')
    if items:
        out.append(f'<details{" open" if not active else ""}><summary>Últimas sesiones</summary><ul>{"".join(items)}</ul>'
                   '</details>')
    if state.get("waiting"):
        out.append(f'<p class="muted">{e(str(state["waiting"]))} aviso(s) esperan su turno.</p>')
    if state.get("left"):
        out.append(f'<p class="muted">{e(str(state["left"]))} caso(s) quedaron para ti: el Solucionador agotó sus '
                   'intentos en esa tarea.</p>')
    return "".join(out) + "</div>"
