"""Read-only rendered owner status for UI design contracts in plan views."""
from __future__ import annotations

from html import escape


def approval_label(state: str) -> str:
    return {"approved": "aprobado", "changes-requested": "cambios solicitados"}.get(state, "pendiente")


def index_chips(row: dict) -> str:
    return "".join(f'<span class="chip">{escape(item["contract"])} · aprobación '
                   f'{escape(approval_label((item.get("approval") or {}).get("status", "pending")))}</span>'
                   for item in row.get("design_subplans", []))


def plan_panel(subplans: list[dict]) -> str:
    if not subplans:
        return ""
    parts = ['<section class="ms"><h2>Contratos de diseño</h2>']
    for item in subplans:
        approval = (item.get("approval") or {}).get("status", "pending")
        parts.append(f'<p><strong>{escape(str(item.get("subplan_id") or ""))}</strong> · '
                     f'<code>{escape(str(item.get("contract") or ""))}</code> · '
                     f'aprobación {escape(approval_label(str(approval)))} · diseño {escape(str(item.get("design_state") or ""))}</p>')
    parts.append('</section>')
    return "".join(parts)
