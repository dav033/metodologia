"""«Probar esto» on a decision card that waits for the owner's manual evidence (MANUAL_EVIDENCE_REQUIRED/CRITERION_MANUAL).

Owner, 2026-10-30, on pictures REQ-021 T10.5: «this asks me to confirm something, but it should open a button that sends
me to test that something directly». The card gets the snapshot's real URL with «Probar esto ↗» (the same clean restart
as a subplan version: `bt_verify_servers` with the decision's attempt snapshot), the manual check as steps
(`bt_verify_guide.manual`) and the two answers: «Funciona» seals the owner's evidence as the attestation receipt
(`bt-durable attest … --by owner`, which re-verifies that very snapshot) and «No funciona» answers `retry_with_note`
with what failed. Pure functions: HTML out.
"""
from __future__ import annotations

import re

from html import escape as e
from pathlib import Path
from urllib.parse import quote

from bt_pages import inline


def _hidden(token: str, **fields: str) -> str:
    return f'<input type="hidden" name="token" value="{e(token)}">' + "".join(
        f'<input type="hidden" name="{e(k)}" value="{e(v)}">' for k, v in fields.items())


def block(root: Path, project: str, req: str, rdir: Path, decision: dict, base: str, token: str) -> str:
    """The «Probar esto» block of one decision card; empty when the decision is not a manual-evidence one or its
    snapshot cannot be found (the card keeps its usual options)."""
    import bt_verify_guide as guides
    import bt_verify_servers as servers
    manual = decision.get("manual")
    if not manual:
        return ""
    task = manual["task"]
    data = servers.recipe(root, project, rdir)
    target = servers.task_target(root, project, rdir, task) if data else None
    if target is None:
        why = ("el proyecto no tiene receta de servidores de prueba" if data is None else
               f"no encuentro el snapshot del intento {manual['attempt']}")
        return f'<p class="muted">«Probar esto» no está disponible: {e(why)}.</p>'
    now = servers.status(root, project, rdir, task)
    plan = servers.planned(root, project, rdir, task)
    url = now.get("url") if now["state"] in ("ready", "preparing") and now.get("url") else plan["url"]
    guide = guides.manual(root, project, rdir, task, url=url, recipe=data, attempt=target["attempt"], commit=target["commit"])
    form_id = f"vstart-{task}"
    start = (f'<form id="{e(form_id)}" method="post" action="/p/{quote(project)}/req/{quote(req)}/verify-run" target="_blank" '
             f'rel="noopener" class="pp-vform">{_hidden(token, anchor=task, path="/")}<button type="submit" class="secondary">'
             f'Reiniciar desde cero</button></form>')
    import bt_page_verification as verify_page          # the pages its steps name, each a link like the version's own (D-200)
    origin = (re.match(r"https?://[^/]+", url or "") or [""])[0]
    pages = ["/"] + [p for p in verify_page.test_paths([{"how": " ".join(s["do"] for s in guide["steps"]),
                                                          "expect": " ".join(s["expect"] or "" for s in guide["steps"])}])
                     if p != "/"]
    port = (re.search(r":(\d+)", url or "") or [None, ""])[1]
    login = servers.auto_login(data)                 # D-211: the card's links sign in too, as the account the check needs
    who_first = (guide["accounts"] or [""])[0] if login else ""
    go = (f"/p/{quote(project)}/req/{quote(req)}/verify-go?sp={quote(task)}&t={quote(token)}"
          + (f"&account={quote(who_first)}" if who_first else "")) if login else ""
    links = verify_page.link_items(origin, port, pages, form_id, go)
    said = {"ready": ("ok", "En marcha: responde."), "preparing": ("warn", "Arrancando…"),
            "failed": ("bad", "Falló al arrancar. " + str(now.get("step") or ""))}.get(now["state"], ("none", "Detenido."))
    steps = "".join(f'<li><p>{inline(s["do"])}</p>' + (f'<p class="pp-vexpect"><strong>Debes ver:</strong> {inline(s["expect"])}</p>'
                                                  if s["expect"] else "") + "</li>" for s in guide["steps"])
    who = ""
    if guide["accounts"]:
        who = ('<p><span class="pp-vlabel">Cuentas</span>' + ", ".join(f"<code>{e(a)}</code>" for a in guide["accounts"]) +
               (f" — {inline(guide['password'])}" if guide["password"] else "") + "</p>")
    named = (f'<p><span class="pp-vlabel">Proveedor configurado</span><code>{e(guide["provider"])}</code> '
             f'(de <code>{e(str(data.get("env_file") or ""))}</code>)</p>' if guide["provider"] else "")
    works = (f'<form method="post" action="{base}/attest" class="opt dx-works">'
             f'{_hidden(token, request=manual["request_id"], task=task)}'
             f'<label class="pp-vlabel" for="ev-{e(task)}">Qué comprobaste (queda como evidencia firmada; sin secretos)</label>'
             f'<textarea id="ev-{e(task)}" name="evidence" required rows="3">{e(guide["prefill"])}</textarea>'
             f'<button type="submit" class="primary">Funciona</button>'
             f'<p class="muted">Guarda tu observación como recibo del propietario y vuelve a verificar este mismo intento.</p></form>')
    broken = (f'<form method="post" action="{base}/decide" class="opt dx-broken">'
              f'{_hidden(token, request=decision["id"], option="retry_with_note")}'
              f'<textarea name="reason" required rows="2" placeholder="Qué falló: qué hiciste y qué viste" '
              f'aria-label="Qué falló"></textarea><button type="submit">No funciona</button>'
              f'<p class="muted">Un intento nuevo de {e(task)} que recibe tu nota.</p></form>')
    picker = verify_page.account_picker({**login, "default": who_first or login.get("default")}, task) if login else ""
    return (f'<div class="pp-vtry dx-manual" data-state="{e(now["state"])}"><span class="pp-vlabel">Probar esto: dónde</span>'
            f'{picker}<ul class="pp-vlinks">{links}</ul>'
            f'<p class="pp-vstatus {said[0]}" role="status">{e(said[1])}</p>'
            f'<p class="muted">Es el intento <code>{e(target["version"])}</code> de {e(task)} (commit '
            f'<code>{e(target["commit"][:10])}</code>), el mismo que se vuelve a verificar con tu respuesta. Si no está en '
            f'marcha, al abrir un enlace lo arranco desde cero y la pestaña llega a esa página cuando responde.</p>'
            f'<div class="pp-vtry-row">{start}</div>{verify_page.remote_help(port)}{who}{named}<ol class="pp-vsteps">{steps}</ol>'
            f'<div class="dx-manual-answers">{works}{broken}</div></div><script src="/static/verify-run.js"></script>')
