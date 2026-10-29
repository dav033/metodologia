"""The tab «Probar esta versión» opens: it waits for the version's test servers and then goes to the version itself.

`page` is plain HTML whose script polls `status_json` (the same URL with `format=json`) every two seconds and replaces
itself with the version's URL as soon as every server answers. Pure functions: HTML and JSON out.
"""
from __future__ import annotations

import json
from html import escape as e
from pathlib import Path

import bt_verify_servers as servers
from bt_pages import layout, purl


def status_json(root: Path, project: str, rdir: Path, sid: str) -> str:
    return json.dumps(servers.status(root, project, rdir, sid), ensure_ascii=False)


def page(root: Path, project: str, rid: str, rdir: Path, sid: str) -> str:
    now = servers.status(root, project, rdir, sid)
    back = purl(project, "req", rid) + f"?tab=plan&mode=subplans&view=verify&sp={e(sid)}"
    body = (f'<section class="pp-vrun" data-sp="{e(sid)}"><h1>Probar {e(sid)}</h1>'
            f'<p id="vrun-state" role="status">{_said(now)}</p>'
            f'<ul id="vrun-servers">{_rows(now)}</ul><pre id="vrun-log">{e(now.get("log") or "")}</pre>'
            f'<p class="pp-meta">Esta pestaña se abrirá sola en la versión cuando todos los servidores respondan. '
            f'<a href="{back}">Volver a «Probar»</a></p></section>'
            '<script src="/static/verify-run.js"></script>')
    return layout(f"Probar {sid}", body)


def _said(now: dict) -> str:
    return {"ready": "Lista: abriendo la versión…", "preparing": "Preparando la versión…",
            "failed": "Un servidor se detuvo al arrancar; abajo está su salida."}.get(
        now["state"], "Los servidores no están en marcha.")


def _rows(now: dict) -> str:
    return "".join(f"<li>{e(n)}: {'responde' if ok else 'arrancando…'}</li>" for n, ok in (now.get("servers") or {}).items())
