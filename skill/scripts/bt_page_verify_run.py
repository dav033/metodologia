"""The tab «Probar» opens: it shows the version restarting step by step and then goes to the version's own URL.

`page` is plain HTML whose script (verify-run.js) polls `status_json` (the same URL with `format=json`) every two seconds
and replaces itself with the version's URL as soon as every server answers. A failure stays on screen with the step that
failed and its log tail, and «Reintentar» restarts it clean. Pure functions: HTML and JSON out.
"""
from __future__ import annotations

import json
import re
from html import escape as e
from pathlib import Path

import bt_verify_servers as servers
from bt_pages import layout, purl


def status_json(root: Path, project: str, rdir: Path, sid: str) -> str:
    return json.dumps(servers.status(root, project, rdir, sid), ensure_ascii=False)


def page(root: Path, project: str, rid: str, rdir: Path, sid: str, token: str = "", path: str = "/") -> str:
    now = servers.status(root, project, rdir, sid)
    path = path if re.fullmatch(r"/[A-Za-z0-9_\-./\[\]]{0,200}", path or "") and "//" not in path else "/"
    back = (f"/plans/{e(project)}/{e(rid)}" if re.fullmatch(r"T\d+(?:\.\d+)*", sid or "") else
            purl(project, "req", rid) + f"?tab=plan&mode=subplans&view=verify&sp={e(sid)}")
    retry = (f'<form method="post" action="{purl(project, "req", rid, "verify-run")}" id="vrun-retry" class="pp-vform"'
             f'{"" if now["state"] == "failed" else " hidden"}><input type="hidden" name="token" value="{e(token)}">'
             f'<input type="hidden" name="anchor" value="{e(sid)}"><input type="hidden" name="path" value="{e(path)}"><button type="submit" class="pp-approve">Reintentar desde cero'
             f'</button></form>' if token else "")
    url = now.get("url") or ""
    body = (f'<section class="pp-vrun" data-sp="{e(sid)}" data-path="{e(path)}"><h1>Probar {e(sid)}</h1>'
            f'<p class="pp-vrun-url"><span class="pp-vlabel">Dirección</span><code id="vrun-url">{e(url) or "…"}</code></p>'
            f'<p id="vrun-state" class="pp-vstatus {_cls(now)}" role="status">{e(_said(now))}</p>'
            f'<p id="vrun-step" class="pp-meta">{e(now.get("step") or "")}</p>'
            f'<ul id="vrun-servers">{_rows(now)}</ul><pre id="vrun-log"{"" if now.get("log") else " hidden"}>{e(now.get("log") or "")}</pre>'
            f'{retry}<p class="pp-meta">Esta pestaña se abrirá sola en <code>{e(path)}</code> cuando todos los servidores respondan. '
            f'<a href="{back}">Volver</a></p></section>'
            '<script src="/static/verify-run.js"></script>')
    return layout(f"Probar {sid}", body)


def _cls(now: dict) -> str:
    return {"ready": "ok", "failed": "bad", "preparing": "warn"}.get(now["state"], "none")


def _said(now: dict) -> str:
    return {"ready": "Lista: abriendo la versión…", "preparing": "Arrancando la versión desde cero…",
            "failed": "No pude arrancar la versión."}.get(now["state"], "Los servidores no están en marcha.")


def _rows(now: dict) -> str:
    ports = now.get("ports") or {}
    return "".join(f"<li>{e(n)} (puerto {e(str(ports.get(n, '?')))}): {'responde' if ok else 'arrancando…'}</li>"
                   for n, ok in (now.get("servers") or {}).items())
