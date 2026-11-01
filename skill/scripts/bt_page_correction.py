"""A rejected subplan version waiting for its correction, as web pieces (data in `bt_verification_correction`, D-268).

Owner, 2026-10-31, about pictures REQ-021 SP-14: «en el panel debe aparecer como rechazada en espera de iteración o algo
así». Wherever a subplan's state shows, the rejection is the primary label: «Rechazada v2 · rediseñando».

- `badge`: the label in the panel's rejected style, the owner's note on hover;
- `strip`: the label, the correction's phases (done, current, next), and the note with a link to its P-item.

Pure functions: HTML out, no writes.
"""
from __future__ import annotations

from html import escape as e
from urllib.parse import quote

STATE_ES = {"done": "hecho", "now": "en curso", "todo": "pendiente"}


def _hover(c: dict) -> str:
    note = " ".join(c.get("note", "").split())
    return (f"Tu nota: «{note}»" if note else "Rechazaste esta versión") + (f" · {c['pending']}" if c.get("pending") else "")


def badge(c: dict, cls: str = "pp-state rejected") -> str:
    return f'<span class="{e(cls)}" title="{e(_hover(c))}">{e(c["label"])}</span>'


def pending_link(project: str, c: dict) -> str:
    pid = c.get("pending") or ""
    return f'<a href="/go/{quote(project)}/{quote(pid)}">Ver {e(pid)} →</a>' if pid else ""


def strip(project: str, c: dict, *, note: bool = True) -> str:
    """The correction at a glance; `note=False` where the owner's note is already on the page («Probar»)."""
    steps = "".join(f'<li class="{e(s["state"])}"{" aria-current=step" if s["state"] == "now" else ""}>{e(s["label"])}'
                    f'<span class="sr"> ({STATE_ES[s["state"]]})</span></li>' for s in c["steps"])
    detail = f'<span class="pp-meta">{e(c["detail"])}</span>' if c.get("detail") else ""
    said = ""
    if note and (c.get("note") or c.get("pending")):
        summary = "Tu nota del rechazo" + (f" · {c['pending']}" if c.get("pending") else "")
        said = (f'<details class="pp-rejnote"><summary>{e(summary)}</summary>'
                + (f'<p>«{e(c["note"])}»</p>' if c.get("note") else "") + f"{pending_link(project, c)}</details>")
    return (f'<div class="pp-rej" role="status" aria-label="Corrección de la versión {e(str(c["version"]))}">'
            f'<div class="pp-rej-head">{badge(c)}{detail}{"" if note else pending_link(project, c)}</div>'
            f'<ol class="pp-rejsteps" aria-label="Pasos de la corrección">{steps}</ol>{said}</div>')
