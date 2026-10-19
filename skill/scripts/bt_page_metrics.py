"""Agent telemetry page: attempts, outcomes, usage coverage, and account availability."""
from __future__ import annotations

from html import escape as e

import bt_agents
import bt_events
import bt_scheduler_rows
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


def _model_cell(g) -> str:
    """The model name as a link to its statistics (and effort when the row has one)."""
    import bt_page_attempts
    if not g.get("agent") or not g.get("model"):
        return _value(g.get("model"))
    return bt_page_attempts.model_chip(g["agent"], g["model"], None)


def _main_rows(groups, work_profiles, source_rows) -> str:
    rendered = []
    for g in groups:
        profile = _value(g.get("profile"))
        work = ' <span class="badge">work</span>' if g.get("profile") in work_profiles else ""
        rate = DASH if g.get("success_rate") is None else f'{g["success_rate"]:.0%}'
        coverage = DASH if g.get("coverage") is None else f'{g["coverage"]:.0%}'
        rendered.append(f"<tr><td>{_value(g.get('agent'))}</td><td>{profile}{work}</td><td>{_model_cell(g)}</td>"
                    f"<td>{_effort(g)}</td><td>{g['attempts']}</td><td>{g['done']}</td><td>{g['failed']}</td>"
                    f"<td>{g['other']}</td><td>{rate}</td><td>{_rate(g.get('verified_task_success_rate'))}</td><td>{_number(_avg_seconds(g, source_rows, ('agent', 'profile', 'model', 'effort')))}</td>"
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
        f"<td>{_rate(g.get('success_rate'))}</td><td>{_rate(g.get('verified_task_success_rate'))}</td>"
        f"<td>{_number(_avg_seconds(g, rows, ('kind', 'agent', 'model', 'effort')))}</td>"
        f"<td>{_number(g.get('audited') or None)}</td><td>{_number(g.get('findings'))}</td>"
        f"<td>{_value(g.get('findings_per_audited_task'))}</td><td>{_number(g.get('high_findings'))}</td>"
        f"<td>{g.get('rework_attempts', 0)}</td><td>{_rate(g.get('rework_rate'))}</td>"
        f"<td>{_number(g.get('tokens_per_clean_task'))}</td></tr>" for g in groups)


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


def _complexity_rows(groups) -> str:
    return "".join(
        f"<tr><td>{_value(g.get('kind'))}</td><td>{_value(g.get('complexity'))}</td><td>{_value(g.get('agent'))}</td>"
        f"<td>{_value(g.get('model'))}</td><td>{_effort(g)}</td><td>{g['attempts']}</td><td>{g['done']}</td>"
        f"<td>{g['failed']}</td><td>{_rate(g.get('success_rate'))}</td><td>{_number(g.get('avg_seconds'))}</td>"
        f"<td>{_number(g.get('tokens_per_done'))}</td></tr>" for g in groups)


def _reason_rows(groups) -> str:
    def cell(items) -> str:
        return "<br>".join(e(i[:240]) for i in items) or DASH
    return "".join(
        f"<tr><td>{_value(g.get('kind'))}</td><td>{_value(g.get('complexity'))}</td>"
        f"<td>{_value(g.get('agent'))} · {_value(g.get('model'))} · {_effort(g)}</td><td>{g['attempts']}</td>"
        f"<td>{e(', '.join(f'{k}: {v}' for k, v in sorted(g['outcomes'].items())))}</td>"
        f"<td>{cell(g['failed_because'])}</td><td>{cell(g['worked_because'])}</td></tr>" for g in groups)


def _attempt_cards(rows, count: int = 8) -> str:
    """Each recent attempt as a key/value table: what it was, who ran it, what it cost, how and why it ended."""
    cards = []
    for r in reversed(rows[-count:]):
        pairs = "".join(f"<tr><th style=\"text-align:left;white-space:nowrap\">{e(k)}</th><td>{e(v)}</td></tr>"
                        for k, v in bt_events.key_values(r))
        cls = OUTCOME_CLASS.get(r.get("result"), "")
        cards.append(f'<details class="card"><summary><span class="badge {cls}">{_value(r.get("result"))}</span> '
                     f'{_value(r.get("task"))} · {_value(r.get("agent"))} {_value(r.get("model"))} · '
                     f'{_value(r.get("kind"))} · {_number(r.get("seconds"))} s</summary>'
                     f'<table class="matrix">{pairs}</table></details>')
    return "".join(cards)


def metrics_page() -> str:
    rows = sorted(bt_events.read_all() + bt_scheduler_rows.rows(), key=lambda r: r.get("ts") or "")
    catalog = bt_agents.catalog()
    work_profiles = {a["profile"] for a in catalog["accounts"] if a.get("work_only")}
    groups = bt_events.summary(rows, ("agent", "profile", "model", "effort"))
    defects = bt_events.read_defects()
    kinds = bt_events.summary(rows, ("kind", "agent", "model", "effort"), defects)
    sized = bt_events.summary(rows, ("kind", "complexity", "agent", "model", "effort"))
    why = bt_events.reasons(rows)
    advice = "".join(f"<li>{e(text)}</li>" for text in bt_events.advice(rows, defects=defects))
    body = f"""<div class="head"><div><p class="eyebrow">suscripciones y modelos</p><h1>Métricas de agentes</h1></div></div>
<p class="muted">Cada fila agrupa intentos de maratón, delegaciones e intentos del Scheduler (derivados de su estado, solo lectura). Un dato que el proveedor no informó queda en «—»,
nunca en 0; los tokens solo cuentan intentos con medición (columna cobertura). No son un saldo de suscripción.
«Tasa por sesión» cuenta una sesión parcial como un intento fallido; «Tasa verificada por tarea» (la que usa el router)
cuenta cada tarea con su veredicto y excluye pérdidas del proveedor, omitidas y no verificadas.</p>
<h2>Qué dicen los datos</h2><div class="card"><ul class="plain">{advice}</ul></div>
<h2>Por agente, modelo y esfuerzo</h2>
{_table(["Agente", "Perfil", "Modelo", "Esfuerzo", "Intentos", "Hechos", "Fallidos", "Otros", "Tasa por sesión", "Tasa verificada por tarea", "Seg. medio", "Tokens medidos", "Tokens/hecho", "Coste USD informado", "Cobertura"], _main_rows(groups, work_profiles, rows)) if groups else '<p class="muted">Aún no hay intentos registrados.</p>'}
<h2>Por tipo de trabajo</h2>
{_table(["Tipo", "Agente", "Modelo", "Esfuerzo", "Intentos", "Hechos", "Fallidos", "Tasa por sesión", "Tasa verificada por tarea", "Seg. medio", "Auditadas", "Hallazgos", "Hallazgos/tarea", "Altos", "Retrabajo", "Tasa retrabajo", "Tokens/tarea limpia"], _kind_rows(kinds, rows)) if kinds else '<p class="muted">Aún no hay intentos registrados.</p>'}
<p class="muted">Calidad: los hallazgos vienen solo de auditorías independientes que los informaron (<code>task done --findings</code>); sin dato queda «—». Muestras pequeñas; los tokens de Claude excluyen caché y Codex no informa coste.</p>
<h2>Por tipo y complejidad</h2>
<p class="muted">Complejidad S/M/L: la declarada en el plan (<code>complexity: M</code>) o, si falta, inferida (se indica en cada intento).</p>
{_table(["Tipo", "Complejidad", "Agente", "Modelo", "Esfuerzo", "Intentos", "Hechos", "Fallidos", "Tasa por sesión", "Seg. medio", "Tokens/hecho"], _complexity_rows(sized)) if sized else '<p class="muted">Aún no hay intentos registrados.</p>'}
<h2>Por qué falló y por qué salió bien</h2>
{_table(["Tipo", "Complejidad", "Agente · modelo · esfuerzo", "Intentos", "Cómo terminaron", "Falló porque", "Funcionó porque"], _reason_rows(why)) if why else '<p class="muted">Aún no hay intentos registrados.</p>'}
<h2>Intentos recientes, clave por clave</h2>
{_attempt_cards(rows) if rows else '<p class="muted">Aún no hay intentos registrados.</p>'}
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
