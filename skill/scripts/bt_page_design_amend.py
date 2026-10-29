"""Plan-tab banner for a chosen design the plan has overtaken: what changed and «Actualizar diseño»."""
from __future__ import annotations

from html import escape as e

import bt_design_drafts as drafts
from bt_pages import purl

KIND = {"added": "Añadido", "removed": "Quitado", "changed": "Cambiado"}


def banner(ctx: dict, row: dict) -> str:
    """Empty unless the entry has chosen work behind the plan and its own Designer is idle; other subplans' Designers
    never block it (they work in parallel)."""
    if not row.get("amend") or row["status"] in drafts.ACTIVE:
        return ""
    import bt_design_amend
    try:
        change = bt_design_amend.delta(ctx["project"], ctx["rdir"], row, row)
    except (OSError, KeyError, TypeError, ValueError):
        change = {"changes": [], "previous_path": None}
    changes = change["changes"]
    items = "".join(f'<li><span class="pp-meta">{e(c["section"])} · {KIND[c["kind"]]}:</span> '
                    + (f'<del>{e(c["before"])}</del> → {e(c["after"])}' if c["kind"] == "changed" else
                       e(c["after"] or c["before"])) + "</li>" for c in changes)
    summary = (f'<details class="pp-amend-diff"><summary>Qué cambió en el plan ({len(changes)})</summary>'
               f'<ul>{items}</ul></details>' if changes else
               ('<p class="pp-meta">No hay diferencias que resumir; el Designer comparará los dos briefs.</p>'
                if change["previous_path"] else
                '<p class="pp-meta">No hay un brief anterior registrado: el Designer revisará el contrato completo.</p>'))
    base = purl(ctx["project"], "req", ctx["rid"])
    failed = ('<p class="pp-meta">El intento anterior falló; el diseño elegido sigue intacto.</p>'
              if row["status"] == "failed" else "")
    return (f'<section class="pp-note warn pp-amend" role="status"><p><strong>El plan cambió: actualizar el diseño con '
            f'lo que ya está</strong></p><p class="pp-meta">Se conserva la dirección elegida; el Designer aplica solo '
            f'el cambio del plan y deja una revisión nueva.</p>{failed}{summary}'
            f'<form method="post" action="{base}/design-amend"><input type="hidden" name="token" value="{e(ctx["token"])}">'
            f'<input type="hidden" name="contract" value="{e(row["ref"])}"><input type="hidden" name="anchor" '
            f'value="{e(row["id"])}"><input type="hidden" name="lang" value="{e(ctx["opts"]["lang"])}">'
            f'<label>Indicaciones para el Designer (opcional)<textarea name="comments"></textarea></label>'
            f'<button type="submit">Actualizar diseño</button></form></section>')
