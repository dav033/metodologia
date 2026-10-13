"""Agent telemetry page: per agent/profile/model attempts, outcomes and token coverage, from .state/events."""
from __future__ import annotations

from html import escape as e

import bt_events
import bt_profiles
from bt_pages import layout

OUTCOME_CLASS = {"done": "done", "verified": "done", "claimed": "review", "partial": "review"}


def _fmt(value) -> str:
    return "—" if value is None else f"{value:,}".replace(",", ".")


def _rate(done: int, attempts: int) -> str:
    return f"{100 * done // attempts} %" if attempts else "—"


def metrics_page() -> str:
    rows = bt_events.read_all()
    groups = bt_events.summary(rows)
    work = {p: s.get("work_only") for p, s in bt_profiles.load().items()}
    table = "".join(
        f'<tr><td>{e(str(g["agent"]))}</td><td>{e(str(g["profile"] or "—"))}'
        f'{" <span class=badge>work</span>" if work.get(g["profile"]) else ""}</td><td>{e(str(g["model"] or "—"))}</td>'
        f'<td>{g["attempts"]}</td><td>{g["done"]}</td><td>{g["failed"]}</td><td>{g["other"]}</td>'
        f'<td>{_rate(g["done"], g["attempts"])}</td><td>{_fmt(g["seconds"])}</td>'
        f'<td>{_fmt(g["tokens_measured"]) if g["measured"] else "—"}</td>'
        f'<td>{int(100 * g["coverage"])} %</td></tr>' for g in groups)
    recent = "".join(
        f'<tr><td>{e(r.get("ts", "")[:16].replace("T", " "))}</td><td>{e(str(r.get("project")))}</td>'
        f'<td>{e(str(r.get("task")))}</td><td>{e(str(r.get("agent")))}/{e(str(r.get("profile") or "—"))}</td>'
        f'<td><span class="badge {OUTCOME_CLASS.get(r.get("result"), "")}">{e(str(r.get("result")))}</span></td>'
        f'<td>{_fmt(r.get("seconds"))} s</td></tr>' for r in reversed(rows[-30:]))
    body = f"""<h1>Métricas de agentes</h1>
<p class="muted">Cada fila agrupa intentos de maratón y delegaciones. Un dato que el proveedor no informó queda en «—»,
nunca en 0; los tokens solo cuentan intentos con medición (columna cobertura). No son un saldo de suscripción.</p>
{('<div style="overflow-x:auto"><table class="matrix"><tr><th>Agente</th><th>Perfil</th><th>Modelo</th><th>Intentos</th>'
  '<th>Hechos</th><th>Fallidos</th><th>Otros</th><th>Tasa</th><th>Segundos</th><th>Tokens medidos</th>'
  '<th>Cobertura</th></tr>' + table + '</table></div>') if groups else
 '<p class="muted">Aún no hay intentos registrados. Aparecerán al correr una maratón o <code>delegate</code>.</p>'}
<div class="card"><strong>Cómo leerlo</strong><ul class="plain">
<li>La tasa compara tareas distintas: un modelo fuerte suele recibir las más difíciles. No es un ranking.</li>
<li>Con pocos intentos no hay evidencia suficiente para concluir que un modelo supera a otro.</li>
<li>«Hechos» incluye <code>verified</code> (comprobado por el supervisor); <code>claimed</code> es solo la palabra del agente.</li></ul></div>
<h2>Últimos intentos</h2>
{('<div style="overflow-x:auto"><table class="matrix"><tr><th>Cuándo</th><th>Proyecto</th><th>Tarea</th>'
  '<th>Agente/perfil</th><th>Resultado</th><th>Duración</th></tr>' + recent + '</table></div>') if rows else ''}"""
    return layout("Métricas de agentes", body, [("proyectos", "/"), ("métricas", "/metrics")])
