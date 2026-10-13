"""Agent telemetry page: attempts, outcomes, usage coverage, and account availability."""
from __future__ import annotations

from html import escape as e

import bt_agents
import bt_events
from bt_pages import layout

OUTCOME_CLASS = {"done": "done", "verified": "done", "claimed": "review", "partial": "review"}
DASH = "—"


def _value(value) -> str:
    return DASH if value is None else e(str(value))


def _number(value) -> str:
    return DASH if value is None else e(f"{value:,}".replace(",", "."))


def _table(headers, rows_html: str) -> str:
    head = "".join(f"<th>{e(header)}</th>" for header in headers)
    return f'<div style="overflow-x:auto"><table class="matrix"><tr>{head}</tr>{rows_html}</table></div>'


def _effort(row) -> str:
    return _value(row.get("effort"))


def _avg_seconds(group, rows, keys) -> int | None:
    values = [r["seconds"] for r in rows if all(
        (r.get(key) or "implement") == group.get(key) if key == "kind" else r.get(key) == group.get(key)
        for key in keys) and r.get("seconds") is not None]
    return round(sum(values) / len(values)) if values else None


def _main_rows(groups, work_profiles, source_rows) -> str:
    rendered = []
    for g in groups:
        profile = _value(g.get("profile"))
        work = ' <span class="badge">work</span>' if g.get("profile") in work_profiles else ""
        rate = DASH if g.get("success_rate") is None else f'{g["success_rate"]:.0%}'
        coverage = DASH if g.get("coverage") is None else f'{g["coverage"]:.0%}'
        rendered.append(f"<tr><td>{_value(g.get('agent'))}</td><td>{profile}{work}</td><td>{_value(g.get('model'))}</td>"
                    f"<td>{_effort(g)}</td><td>{g['attempts']}</td><td>{g['done']}</td><td>{g['failed']}</td>"
                    f"<td>{g['other']}</td><td>{rate}</td><td>{_number(_avg_seconds(g, source_rows, ('agent', 'profile', 'model', 'effort')))}</td>"
                    f"<td>{_number(g.get('tokens_measured') if g.get('measured') else None)}</td>"
                    f"<td>{_number(g.get('tokens_per_done'))}</td><td>{_value(g.get('cost_usd_reported'))}</td>"
                    f"<td>{coverage}</td></tr>")
    return "".join(rendered)


def _rate(value) -> str:
    return DASH if value is None else f"{value:.0%}"


def _kind_rows(groups, rows) -> str:
    return "".join(
        f"<tr><td>{_value(g.get('kind'))}</td><td>{_value(g.get('agent'))}</td><td>{_value(g.get('model'))}</td>"
        f"<td>{_effort(g)}</td><td>{g['attempts']}</td><td>{g['done']}</td><td>{g['failed']}</td>"
        f"<td>{_rate(g.get('success_rate'))}</td>"
        f"<td>{_number(_avg_seconds(g, rows, ('kind', 'agent', 'model', 'effort')))}</td></tr>" for g in groups)


def _account_rows(accounts) -> str:
    return "".join(
        f"<tr><td>{_value(a.get('profile'))}</td><td>{_value(a.get('provider'))}</td>"
        f"<td>{'Sí' if a.get('work_only') else 'No'}</td>"
        f"<td>{'Sí' if a.get('installed') else 'No'}</td><td>{_value(a.get('cooling_until'))}</td></tr>"
        for a in accounts)


def _ladder_rows(ladder) -> str:
    rows = []
    for provider, tiers in ladder.items():
        by_tier = {item.get("tier"): item for item in tiers}
        cells = []
        for tier in range(3):
            item = by_tier.get(tier)
            cells.append(_value(f"{item.get('model') or DASH} · {item.get('effort') or DASH}") if item else DASH)
        rows.append(f"<tr><td>{_value(provider)}</td>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")
    return "".join(rows)


def _recent_rows(rows) -> str:
    out = []
    for r in reversed(rows[-30:]):
        result = r.get("result")
        cls = OUTCOME_CLASS.get(result, "")
        when = str(r.get("ts") or "")[:16].replace("T", " ")
        out.append(f"<tr><td>{e(when)}</td><td>{_value(r.get('project'))}</td><td>{_value(r.get('task'))}</td>"
                   f"<td>{_value(r.get('agent'))}/{_value(r.get('profile'))}</td>"
                   f"<td>{_value(r.get('model'))} · {_effort(r)}</td><td>{_value(r.get('kind'))}</td>"
                   f"<td><span class=\"badge {cls}\">{_value(result)}</span></td>"
                   f"<td>{_number(r.get('seconds'))} s</td></tr>")
    return "".join(out)


def metrics_page() -> str:
    rows = bt_events.read_all()
    catalog = bt_agents.catalog()
    work_profiles = {a["profile"] for a in catalog["accounts"] if a.get("work_only")}
    groups = bt_events.summary(rows, ("agent", "profile", "model", "effort"))
    kinds = bt_events.summary(rows, ("kind", "agent", "model", "effort"))
    advice = "".join(f"<li>{e(text)}</li>" for text in bt_events.advice(rows))
    body = f"""<h1>Métricas de agentes</h1>
<p class="muted">Cada fila agrupa intentos de maratón y delegaciones. Un dato que el proveedor no informó queda en «—»,
nunca en 0; los tokens solo cuentan intentos con medición (columna cobertura). No son un saldo de suscripción.</p>
<h2>Qué dicen los datos</h2><div class="card"><ul class="plain">{advice}</ul></div>
<h2>Por agente, modelo y esfuerzo</h2>
{_table(["Agente", "Perfil", "Modelo", "Esfuerzo", "Intentos", "Hechos", "Fallidos", "Otros", "Tasa", "Seg. medio", "Tokens medidos", "Tokens/hecho", "Coste USD informado", "Cobertura"], _main_rows(groups, work_profiles, rows)) if groups else '<p class="muted">Aún no hay intentos registrados.</p>'}
<h2>Por tipo de trabajo</h2>
{_table(["Tipo", "Agente", "Modelo", "Esfuerzo", "Intentos", "Hechos", "Fallidos", "Tasa", "Seg. medio"], _kind_rows(kinds, rows)) if kinds else '<p class="muted">Aún no hay intentos registrados.</p>'}
<h2>Cuentas y cuotas</h2>
{_table(["Perfil", "Proveedor", "Solo trabajo", "CLI instalado", "En espera hasta"], _account_rows(catalog["accounts"]))}
<h3>Escalera de modelos</h3>
{_table(["Proveedor", "Tier 0", "Tier 1", "Tier 2"], _ladder_rows(catalog["ladder"]))}
<div class="card"><strong>Cómo leerlo</strong><ul class="plain">
<li>La tasa compara tareas distintas: un modelo fuerte suele recibir las más difíciles. No es un ranking.</li>
<li>Con pocos intentos no hay evidencia suficiente para concluir que un modelo supera a otro.</li>
<li>«Hechos» incluye <code>verified</code> (comprobado por el supervisor); <code>claimed</code> es solo la palabra del agente.</li></ul></div>
<h2>Últimos intentos</h2>
{_table(["Cuándo", "Proyecto", "Tarea", "Agente/perfil", "Modelo·esfuerzo", "Tipo", "Resultado", "Duración"], _recent_rows(rows)) if rows else ''}"""
    return layout("Métricas de agentes", body, [("proyectos", "/"), ("métricas", "/metrics")])
