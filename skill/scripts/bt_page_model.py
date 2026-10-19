"""`/metrics/model/<provider>/<model>[/<effort>]`: what one model (optionally at one effort) has done, across the
marathon, delegations and Scheduler attempts. Pure functions; rows are `bt_events` schema-2 rows."""
from __future__ import annotations

import statistics
from html import escape as e
from urllib.parse import quote

import bt_events
import bt_page_attempts as attempts_
import bt_scheduler_rows
from bt_pages import layout

DASH = "—"
DONE = ("done", "verified")


def select(rows: list[dict], provider: str, model: str, effort: str | None) -> list[dict]:
    return [r for r in rows if r.get("agent") == provider and r.get("model") == model
            and (effort is None or r.get("effort") == effort)]


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(q * (len(ordered) - 1)))]


def _rate(value) -> str:
    return DASH if value is None else f"{value:.0%}"


def _num(value) -> str:
    return DASH if value is None else e(f"{value:,}".replace(",", "."))


def _secs(value) -> str:
    return DASH if value is None else attempts_.fmt_duration(value)


def facts(rows: list[dict]) -> dict:
    """Headline numbers of the selected rows. Anything with no sample is None, never 0."""
    seconds = [r["seconds"] for r in rows if isinstance(r.get("seconds"), (int, float))]
    group = (bt_events.summary(rows, ("agent", "model")) or [{}])[0]
    return {"attempts": len(rows), "done": sum(r.get("result") in DONE for r in rows),
            "failed": group.get("failed"), "success_rate": group.get("success_rate"),
            "verified_rate": group.get("verified_task_success_rate"),
            "p50": percentile(seconds, 0.5), "p90": percentile(seconds, 0.9),
            "mean": round(statistics.fmean(seconds), 1) if seconds else None,
            "tokens_per_done": group.get("tokens_per_done"), "tokens": group.get("tokens_measured") or None,
            "coverage": group.get("coverage"), "cost": group.get("cost_usd_reported"),
            "efforts": sorted({str(r.get("effort")) for r in rows if r.get("effort")})}


def _task_link(r: dict) -> str:
    label = f'{e(str(r.get("req") or "?"))} · {e(str(r.get("task") or "?"))}'
    if r.get("project") and r.get("req") and r.get("task"):
        return (f'<a href="/plans/{quote(str(r["project"]))}/{quote(str(r["req"]))}#t-{quote(str(r["task"]))}">'
                f'{label}</a>')
    return label


def _breakdown(rows: list[dict]) -> str:
    groups = bt_events.summary(rows, ("kind", "complexity"))
    body = "".join(
        f'<tr><td>{e(str(g["kind"]))}</td><td>{e(str(g.get("complexity") or DASH))}</td><td>{g["attempts"]}</td>'
        f'<td>{g["done"]}</td><td>{g["failed"]}</td><td>{_rate(g.get("success_rate"))}</td>'
        f'<td>{_secs(g.get("avg_seconds"))}</td><td>{_num(g.get("tokens_per_done"))}</td></tr>' for g in groups)
    return (f'<div class="tscroll"><table class="matrix"><tr><th>tipo</th><th>complejidad</th><th>intentos</th>'
            f'<th>hechos</th><th>fallidos</th><th>tasa</th><th>seg. medio</th><th>tokens/hecho</th></tr>{body}'
            f'</table></div>')


def _recent(rows: list[dict], count: int = 20) -> str:
    body = "".join(
        f'<tr><td>{e(str(r.get("ts") or DASH)[:19].replace("T", " "))}</td><td>{_task_link(r)}</td>'
        f'<td>{e(str(r.get("effort") or DASH))}</td><td>{e(str(r.get("result")))}</td><td>{_secs(r.get("seconds"))}</td>'
        f'<td>{e(str(r.get("origin") or "maratón"))}</td></tr>' for r in reversed(rows[-count:]))
    return (f'<div class="tscroll"><table class="matrix"><tr><th>cuándo</th><th>tarea</th><th>esfuerzo</th>'
            f'<th>resultado</th><th>duración</th><th>origen</th></tr>{body}</table></div>')


def _kpi(label: str, value: str, note: str = "") -> str:
    return (f'<div class="mstat"><div class="muted">{e(label)}</div><div class="kv">{value}</div>'
            f'<div class="muted">{note}</div></div>')


def model_page(provider: str, model: str, effort: str | None, rows: list[dict]) -> str:
    chosen = select(rows, provider, model, effort)
    title = f"{model}" + (f" · {effort}" if effort else "")
    head = (f'<div class="head"><div><p class="eyebrow">modelo · {e(provider)}</p><h1>{e(title)}</h1></div></div>')
    if not chosen:
        return layout(f"{title} · modelo", head + '<p class="muted">Aún no hay intentos de este modelo'
                      + (" con ese esfuerzo" if effort else "") + '.</p>',
                      [("Métricas", "/metrics"), (title, "")])
    f = facts(chosen)
    all_efforts = sorted({str(r.get("effort")) for r in select(rows, provider, model, None) if r.get("effort")})
    other = [x for x in all_efforts if x != effort]
    efforts = ("Otros esfuerzos: " + " · ".join(
        f'<a href="/metrics/model/{quote(provider, safe="")}/{quote(model, safe="")}/{quote(x, safe="")}">{e(x)}</a>'
        for x in other)) if other and effort else (
        "Por esfuerzo: " + " · ".join(
            f'<a href="/metrics/model/{quote(provider, safe="")}/{quote(model, safe="")}/{quote(x, safe="")}">{e(x)}</a>'
            for x in all_efforts) if all_efforts else "")
    kpis = "".join((
        _kpi("Intentos", str(f["attempts"]), f'{f["done"]} hechos'),
        _kpi("Tasa verificada", _rate(f["verified_rate"]), "por tarea, sin pérdidas del proveedor"),
        _kpi("Duración p50 / p90", f'{_secs(f["p50"])} / {_secs(f["p90"])}', f'media {_secs(f["mean"])}'),
        _kpi("Tokens por tarea hecha", _num(f["tokens_per_done"]), f'cobertura {_rate(f["coverage"])}'),
        _kpi("Coste informado (USD)", DASH if f["cost"] is None else f'{f["cost"]:.2f}', "solo si el proveedor lo informó")))
    body = (f'{head}<p class="muted">{efforts}</p><div class="mstats">{kpis}</div>'
            f'<h2>Por tipo y complejidad</h2>{_breakdown(chosen)}'
            f'<h2>Últimos {min(20, len(chosen))} intentos</h2>{_recent(chosen)}'
            f'<p class="muted">Un dato que el proveedor no informó queda en «—», nunca en 0. Los tokens de Claude '
            f'excluyen caché; los de Codex la incluyen: no se suman entre proveedores.</p>')
    return layout(f"{title} · modelo", body, [("Métricas", "/metrics"), (title, "")])


def all_rows() -> list[dict]:
    return sorted(bt_events.read_all() + bt_scheduler_rows.rows(), key=lambda r: r.get("ts") or "")
