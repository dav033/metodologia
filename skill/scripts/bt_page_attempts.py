"""HTML pieces for attempts: model chips that link to their statistics, durations, tokens, the per-task attempts table.

Pure functions (data in, HTML out) shared by the plan detail, `/now` and the metrics pages. Anything an attempt did not
report is shown as "—" or "no informado", never as 0.
"""
from __future__ import annotations

from html import escape as e
from urllib.parse import quote


def model_href(provider: str | None, model: str | None, effort: str | None = None) -> str | None:
    if not provider or not model:
        return None
    parts = ["/metrics/model", quote(provider, safe=""), quote(model, safe="")]
    if effort:
        parts.append(quote(effort, safe=""))
    return "/".join(parts)


def model_chip(provider: str | None, model: str | None, effort: str | None = None) -> str:
    """`sonnet · high`, linked to the statistics of that model (and effort); a plain dash when the model is unknown."""
    if not model:
        return '<span class="muted">—</span>'
    label = e(model) + (f' · {e(effort)}' if effort else "")
    href = model_href(provider, model, effort)
    return f'<a class="mchip" href="{e(href)}">{label}</a>' if href else f'<span class="mchip">{label}</span>'


def fmt_duration(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    s = int(seconds)
    if s < 60:
        return f"{s} s"
    if s < 3600:
        return f"{s // 60} min {s % 60:02d} s"
    return f"{s // 3600} h {(s % 3600) // 60:02d} min"


def fmt_count(value: int | None) -> str:
    if value is None:
        return "—"
    return f"{value / 1000:.1f}k" if value >= 10_000 else f"{value:,}".replace(",", ".")


def tokens_html(tokens: dict | None) -> str:
    """`46.3k` total, or `↑12k ↓3k` when only the parts are known; `no informado` when the provider reported none."""
    if not tokens:
        return '<span class="muted">no informado</span>'
    if tokens.get("total") is not None:
        title = f'entrada {fmt_count(tokens.get("input"))} · salida {fmt_count(tokens.get("output"))}'
        return f'<span title="{e(title)}">{fmt_count(tokens["total"])}</span>'
    parts = [f'{sym}{fmt_count(tokens[k])}' for sym, k in (("↑", "input"), ("↓", "output")) if tokens.get(k) is not None]
    return f'<span title="el proveedor no informó el total">{" ".join(parts)}</span>'


def _time(iso: str | None) -> str:
    return e(iso[11:19]) if iso and len(iso) >= 19 else "—"


def attempt_row(a: dict) -> str:
    state = a.get("state") or "—"
    cls = "ok" if state == "accepted" else "bad" if state in ("rejected", "failed") else "info" if a.get("live") else ""
    cause = f' title="{e(a["failure"])}"' if a.get("failure") else ""
    return (f'<tr id="a-{e(str(a.get("id")))}" data-k="a-{e(str(a.get("id")))}"><td>#{e(str(a.get("number") or "?"))}</td>'
            f'<td><span class="st {cls}"{cause}><i class="dot {cls}"></i>{e(state)}</span></td>'
            f'<td>{model_chip(a.get("provider"), a.get("model_requested"), a.get("effort"))}'
            f'{"" if not a.get("model_reported") or a["model_reported"] == a.get("model_requested") else " <span class=muted>(" + e(a["model_reported"]) + ")</span>"}</td>'
            f'<td>{e(a.get("account") or "—")}</td><td>{_time(a.get("started_at"))}</td>'
            f'<td><span data-v>{fmt_duration(a.get("duration_s"))}</span></td><td><span data-v>{tokens_html(a.get("tokens"))}</span></td>'
            f'<td>{"—" if a.get("cost_usd") is None else "$%.2f" % a["cost_usd"]}</td>'
            f'<td class="muted">{e(a.get("failure") or "")}</td></tr>')


def attempts_table(history: list[dict]) -> str:
    if not history:
        return ""
    head = ("<tr><th>n</th><th>estado</th><th>modelo</th><th>cuenta</th><th>inicio</th><th>duración</th>"
            "<th>tokens</th><th>coste</th><th>causa</th></tr>")
    return (f'<details class="attd"{" open" if any(a.get("live") for a in history) else ""}>'
            f'<summary>Intentos ({len(history)})</summary><div class="tscroll"><table class="att">{head}'
            f'{"".join(attempt_row(a) for a in history)}</table></div></details>')


def assigned_line(route: dict | None) -> str:
    """The route M2 assigned from the start (before any attempt), with its status and why."""
    if not route or not route.get("model_requested"):
        return ""
    status = {"recommended": "recomendada", "assigned": "asignada", "unavailable": "sin ruta"}.get(route["status"], "")
    why = route.get("selection_reason") or route.get("reason")
    return (f'<span><b>asignado</b> {model_chip(route.get("provider"), route["model_requested"], route.get("effort"))}'
            f' · {e(route.get("account") or "—")}{" · " + status if status else ""}'
            f'{" — <span class=why>" + e(why.replace(";", ", ").replace("_", " ")) + "</span>" if why else ""}</span>')
