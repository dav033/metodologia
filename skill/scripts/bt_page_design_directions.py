"""Owner-facing direction comparison, shared by the plan panel and design review."""
from __future__ import annotations

from html import escape as e

from bt_design_directions import choosable
from bt_pages import purl

LABELS = {"concept": "Concepto", "layout": "Composición", "navigation": "Navegación", "typography": "Tipografía",
          "density": "Densidad y forma", "components": "Componentes", "colour": "Color", "motion": "Movimiento"}


def panel(ctx: dict, row: dict) -> str:
    directions = row.get("directions") or []
    if not directions or row.get("chosen") or row.get("continuation_choice"):
        return ""
    base = purl(ctx["project"], "req", ctx["rid"])
    comparison = row.get("comparison") or {}
    status = "Comparación pendiente"
    if comparison:
        passed = "Evidencia de la dirección: comprobada" if len(directions) == 1 else "Direcciones distintas: comprobado"
        status = passed if comparison.get("ok") else str(comparison.get("error") or "Comparación fallida")
        usable = [d["id"].upper() for d in directions if d["status"] == "ready" and choosable(row["ref"], row, d)]
        if not comparison.get("ok") and usable and row["status"] == "choosing":
            status = f"Puedes elegir {', '.join(usable)}. Las demás no se pueden elegir todavía: {status}"
    cards = []
    switches = '<button type="button" data-direction-show="all" aria-pressed="true">Comparar todas</button>' if len(directions) > 1 else ''
    for d in directions:
        key = d["id"]
        name = d.get("name") or f"Dirección {key.upper()}"
        if len(directions) > 1:
            switches += f'<button type="button" data-direction-show="{key}" aria-pressed="false">{key.upper()} · {e(name)}</button>'
        src = f'{base}/mockup?contract={row["ref"]}&direction={key}&rev={d["revision"]}'
        table = "".join(f'<tr><th scope="row">{label}</th><td>{e(str(d.get("axes", {}).get(axis, "Pendiente")))}</td></tr>'
                        for axis, label in LABELS.items())
        can_choose = (d["status"] == "ready" and row["status"] == "choosing" and choosable(row["ref"], row, d))
        form = (f'<form method="post" action="{base}/design-choose"><input type="hidden" name="token" value="{e(ctx["token"])}">'
                f'<input type="hidden" name="contract" value="{e(row["ref"])}"><input type="hidden" name="direction" value="{key}">'
                f'<input type="hidden" name="anchor" value="{e(row["id"])}"><button type="submit">Elegir esta dirección</button></form>') if can_choose else ""
        iterate = _iterate(ctx, row, d, base)
        preview = (f'<a href="{e(src)}" target="_blank" rel="noopener">Abrir dirección {key.upper()} a pantalla completa</a>'
                   f'<div class="pp-frame"><iframe title="{e(name)}" src="{e(src)}" loading="lazy" sandbox="allow-scripts"></iframe></div>') if d["status"] == "ready" else f'<p>{e(d.get("error") or d["status"])}</p>'
        cards.append(f'<section class="pp-direction" data-direction-card="{key}"><h4>{key.upper()} · {e(name)}'
                     f'{" · Elegida" if row.get("chosen") == key else ""}</h4>{form}{preview}'      # the button sits under the title, not below an 800px mockup
                     f'<details><summary>Ejes de la dirección</summary><table>{table}</table></details>{iterate}</section>')
    pairs = comparison.get("pairs") or comparison.get("report", {}).get("pairs") or []
    detail = "".join(f'<li>{e(p["a"])} / {e(p["b"])}: similitud de composición {p["layout_similarity"]:.0%} · '
                     f'{"pasa" if p["ok"] else "demasiado similares"}</li>' for p in pairs)
    heading = "Compara y elige una dirección" if len(directions) > 1 else "Revisa y elige el diseño"
    controls = (f'<div class="pp-seg" role="group" aria-label="Dirección visible">{switches}</div>'
                '<p>Las alternativas conservan el mismo comportamiento. Compara composición, navegación y movimiento.</p>') if switches else ''
    return (f'<section class="pp-directions"><h3>{heading}</h3><p role="status">{e(status)}</p>'
            f'{controls}<div class="pp-direction-grid">{"".join(cards)}</div><ul>{detail}</ul></section>')


def _iterate(ctx: dict, row: dict, d: dict, base: str) -> str:
    """Revise this one direction with the owner's comments; disabled while a Designer is working."""
    key, busy = d["id"], row["status"] in ("queued", "drafting")
    iterable = d["status"] == "ready" and (row["status"] == "choosing" or
                                          (row["status"] == "ready" and row.get("chosen") == key))
    if not (iterable or busy and d.get("name")):
        return ""
    off = " disabled" if busy else ""
    return (f'<form method="post" class="pp-iterate" action="{base}/design-iterate">'
            f'<input type="hidden" name="token" value="{e(ctx["token"])}"><input type="hidden" name="contract" value="{e(row["ref"])}">'
            f'<input type="hidden" name="direction" value="{key}"><input type="hidden" name="anchor" value="{e(row["id"])}">'
            f'<label>Qué cambiar en la dirección {key.upper()}<textarea name="comments" required{off} '
            f'placeholder="Ej.: más redondeada y moderna; conserva la composición y el movimiento"></textarea></label>'
            f'<button type="submit"{off}>Iterar esta dirección</button>'
            f'{"<p class=pp-meta>El Designer está trabajando; espera a que termine para iterar.</p>" if busy else ""}</form>')
