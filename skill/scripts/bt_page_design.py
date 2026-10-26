"""Read-only rendered owner status for UI design contracts in plan views."""
from __future__ import annotations

from html import escape


def approval_label(state: str) -> str:
    return {"approved": "aprobado", "changes-requested": "cambios solicitados"}.get(state, "pendiente")


def index_chips(row: dict, href: str = "") -> str:
    """One compact pill per plan row (approved/total designs); the contracts and their state go in the tooltip."""
    items = row.get("design_subplans", [])
    if not items:
        return ""
    states = [str((item.get("approval") or {}).get("status", "pending")) for item in items]
    tip = "\n".join(f'{item.get("contract")} · aprobación {approval_label(state)}' for item, state in zip(items, states))
    tone = " ok" if all(state == "approved" for state in states) else ""
    tag = f'a href="{escape(href)}"' if href else "span"
    return (f'<{tag} class="pill design-pill{tone}" title="{escape(tip)}">diseños '
            f'{states.count("approved")}/{len(items)}</{tag.split()[0]}>')


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
