"""The «Ejecución» tab of a subplan in the Plan tab: what the run did and what it waits for, with the owner's hands on it.

Everything the run-management page (`/plans/<project>/<REQ>`) shows is here, filtered to one subplan and answerable without
leaving the Plan tab: its tasks (state, route, attempts), the decisions its tasks wait on (retry, retry with a note, stop...),
retry of one task, sending accepted tasks back, the diagnostic recovery and the self-healing of the run, and the way to its
checkpoint («Probar»). The cards and rows are the ones of `bt_page_plans`; the forms post to the same `/plans/...` endpoints
with `back`, so the answer returns to this view. Pure functions: HTML out.
"""
from __future__ import annotations

import re
from html import escape as e
from urllib.parse import quote, urlencode

from bt_page_solver import card as solver_card

TOKEN = re.compile(r'(<input type="hidden" name="token" value="[^"]*">)')


def _status(ctx: dict) -> dict | None:
    """The run status of the plan, once per fragment; None when the plan has no readable run."""
    if "run_status" not in ctx:
        try:
            import bt_plans_api as api
            from bt_core import ROOT
            ctx["run_status"] = api.exec_status(ROOT, ctx["project"], ctx["rid"])
        except Exception:  # noqa: BLE001 - the Plan tab must render even when the run cannot be read
            ctx["run_status"] = None
    return ctx["run_status"]


def counts(ctx: dict) -> dict[str, tuple[int, int]]:
    """subplan id -> (completed tasks, tasks) of the run; empty without a run."""
    status = _status(ctx)
    out: dict[str, list[int]] = {}
    for milestone in (status or {}).get("milestones") or []:
        for task in milestone.get("tasks") or []:
            sid = task.get("subplan_id")
            if sid:
                done, total = out.setdefault(sid, [0, 0])
                out[sid] = [done + (task.get("state") == "completed"), total + 1]
    return {k: (v[0], v[1]) for k, v in out.items()}


def tab_label(ctx: dict, sid: str) -> str:
    done, total = counts(ctx).get(sid, (0, 0))
    return f"Ejecución · {done}/{total}" if total else "Ejecución"


def chip(ctx: dict, sid: str) -> str:
    """The run's state of a subplan for the subplan list: «ejecución 8/8 ✓», «ejecución 3/8», or "" before it ran."""
    done, total = counts(ctx).get(sid, (0, 0))
    if not total or not done and not _live(ctx, sid):
        return ""
    return f"ejecución {done}/{total}" + (" ✓" if done == total else "")


def _live(ctx: dict, sid: str) -> bool:
    status = _status(ctx) or {}
    return any(t.get("subplan_id") == sid and (t.get("attempt") or {}).get("live")
               for m in status.get("milestones") or [] for t in m.get("tasks") or [])


def _back(html: str, back: str) -> str:
    """Make every form of the piece return to this view."""
    return TOKEN.sub(lambda m: m.group(1) + f'<input type="hidden" name="back" value="{e(back)}">', html)


def panel(ctx: dict, sub: dict) -> str:
    import bt_page_plans as plans
    from bt_page_planning import link

    status = _status(ctx)
    if status is None:
        return '<p class="pp-empty">Este plan todavía no tiene una ejecución que mostrar.</p>'
    project, rid, sid = ctx["project"], ctx["rid"], sub["id"]
    base = f"/plans/{quote(project)}/{quote(rid)}"
    back = link(project, rid, ctx["opts"], view="run", sp=sid)
    token = ctx["token"]
    tasks = [t for m in status["milestones"] for t in m["tasks"] if t.get("subplan_id") == sid]
    if not tasks:
        return '<p class="pp-empty">Este subplan todavía no está en la ejecución: se incorpora al aprobar su etapa («Ejecutar subplan»).</p>'
    ids = {t["id"] for t in tasks}
    done = sum(1 for t in tasks if t["state"] == "completed")
    live = [t for t in tasks if (t.get("attempt") or {}).get("live")]
    mine = [d for d in status.get("decisions") or [] if d.get("task") in ids]
    elsewhere = len(status.get("decisions") or []) - len(mine)
    head = (f'<div class="pl pp-run"><div class="phead"><div class="tl"><span class="pill">{e(plans._run_status_es(status["run"]["status"]))}</span>'
            f'<span class="chip">{done}/{len(tasks)} tareas completadas</span>'
            f'{f"""<span class="chip">{len(live)} en curso</span>""" if live else ""}</div>{plans.bar(done, len(tasks))}</div>')
    asks = _back(plans._decisions({**status, "decisions": mine, "open_rounds": []}, base, token), back) if mine else \
        '<p class="muted">Ninguna decisión te espera en este subplan.</p>'
    other = (f'<p class="muted">Hay {elsewhere} decisión(es) en otros subplanes: ábrelos o míralas en '
             f'<a href="{e(base)}#asks">la página de ejecución</a>.</p>') if elsewhere else ""
    by_id = {r["task"]: r for r in mine if r.get("task")}
    rows = "".join(_row(plans, t, by_id, base, token, back) for t in tasks)
    return (head + asks + other + f'<h2>Tareas</h2>{rows}' + _rework(tasks, base, token, back) + _run_tools(ctx, status, base, token, back)
            + _tests(ctx, sub) + "</div>")


def flow_frame(ctx: dict, sub: dict) -> str:
    """The Flow page of this subplan (scope `subplan:P/REQ/SP`, D-150) while its «Ejecución» is open: the module map,
    the messages and each task's route, live. Above the plan's three columns at full width (inside the centre column
    it was cramped, and under a long task list it was buried), collapsible; its own block, whose HTML depends only on
    the subplan, so the Plan tab's refresh never reloads it. planning-live.js sizes the frame to the Flow's height and
    remembers whether the owner left it open."""
    if not counts(ctx).get(sub["id"]):
        return ""
    scope = f'subplan:{ctx["project"]}/{ctx["rid"]}/{sub["id"]}'
    src = "/flow?" + urlencode({"scope": scope, "embed": "1"})
    return (f'<details class="pp-flowtop" data-k="flowtop-{e(sub["id"])}" open><summary><span class="pp-flowtop-title">'
            f'Flujo de {e(sub["id"])}</span><span class="pp-meta">Mensajes entre módulos y recorrido de cada tarea, en '
            f'vivo</span><a class="pp-flowtop-open" href="{e("/flow?" + urlencode({"scope": scope}))}" target="_blank" '
            f'rel="noopener">Abrir en su página ↗</a></summary><div class="pp-flowtop-body"><iframe class="pp-flowtop-frame" '
            f'src="{e(src)}" title="Flujo de {e(sub["id"])}"></iframe></div></details>')


def _row(plans, task: dict, asks: dict, base: str, token: str, back: str) -> str:
    """One line per task (id, title, attempts, state, a one-click retry when it is stuck); the full detail the run page
    shows — objective, criteria, checks, attempts — opens in a modal, so fifteen tasks no longer run to thousands of
    pixels (pictures REQ-021 SP-3)."""
    tid = str(task["id"])
    stuck = task["state"] in ("blocked", "rejected", "cancelled") or tid in asks
    retry = (f'<form method="post" action="{base}/retry-task" class="pp-inline">'
             f'<input type="hidden" name="token" value="{e(token)}"><input type="hidden" name="back" value="{e(back)}">'
             f'<input type="hidden" name="task" value="{e(tid)}">'
             f'<button type="submit" class="outline sm">Reintentar</button></form>') if stuck else ""
    live = '<i class="dot info live" title="trabajando"></i>' if (task.get("attempt") or {}).get("live") else ""
    dialog = f"tdlg-{tid}"
    return (f'<div class="pp-trow"><button type="button" class="pp-trow-open" data-open="{e(dialog)}" aria-haspopup="dialog"'
            f' title="Ver el detalle de {e(tid)}"><span class="tid">{e(tid)}</span><span class="pp-trow-title">'
            f'{plans.inline(task["title"])}</span></button>{live}'
            f'<span class="chip">{task["attempts"]} intento{"s" if task["attempts"] != 1 else ""}</span>'
            f'{plans.state_badge(task["state"])}{retry}</div>'
            f'<dialog id="{e(dialog)}" class="pp-tdialog" aria-labelledby="{e(dialog)}-h"><header>'
            f'<h3 id="{e(dialog)}-h">{e(tid)} · {plans.inline(task["title"])}</h3>'
            f'<button type="button" class="outline sm" data-close aria-label="Cerrar">✕</button></header>'
            f'{plans._task(task, asks)}</dialog>')


def _rework(tasks: list[dict], base: str, token: str, back: str) -> str:
    """Send accepted tasks back, only them. Past the ceiling the owner confirms the cost; the page says so before."""
    done = [t for t in tasks if t["state"] == "completed"]
    if not done:
        return ""
    boxes = "".join(f'<label class="chip"><input type="checkbox" name="tasks" value="{e(t["id"])}"> {e(t["id"])}</label> '
                    for t in done)
    return (f'<details class="dx-more"><summary>Devolver tareas aceptadas para rehacerlas</summary>'
            f'<form method="post" action="{base}/rework" class="opt"><input type="hidden" name="token" value="{e(token)}">'
            f'<input type="hidden" name="back" value="{e(back)}">'
            f'<p class="muted">Solo se rehacen las que marques; lo que depende de ellas conserva su resultado aceptado. '
            f'Es el último recurso: antes mira si hay una ronda de remediación o la recuperación diagnóstica de abajo.</p>'
            f'<p>{boxes}</p>'
            f'<textarea name="reason" required placeholder="Qué hay que corregir (la tarea lo lee en su siguiente intento)" '
            f'aria-label="Motivo"></textarea>'
            f'<label><input type="checkbox" name="confirm_cost" value="1"> Confirmo el coste si son más de las que el sistema '
            f'rehace sin preguntar (3)</label>'
            f'<p><button type="submit" class="danger">Devolver las marcadas</button></p></form></details>')


def _run_tools(ctx: dict, status: dict, base: str, token: str, back: str) -> str:
    """Diagnostic recovery and self-healing of the run (they act on the whole run, not on one subplan)."""
    import bt_page_plans as plans
    pieces = plans._recovery(status, base, token) + plans._healing(status, base, token) + solver_card(status.get("solver"))
    if not pieces:
        return ""
    recovery = status.get("recovery") or {}
    opens = " open" if recovery.get("preview_digest") and not recovery.get("active") and status.get("decisions") else ""
    return (f'<details class="dx-more"{opens}><summary>Gestión del run: recuperación diagnóstica, autocuración y '
            f'Solucionador</summary>'
            f'<p class="muted">Actúan sobre todo el run, no solo sobre este subplan.</p>{_back(pieces, back)}</details>')


def _tests(ctx: dict, sub: dict) -> str:
    from bt_page_planning import link

    href = link(ctx["project"], ctx["rid"], ctx["opts"], view="verify", sp=sub["id"])
    try:
        import bt_page_verification as verify
        label = verify.tab_label(ctx["rdir"])
    except Exception:  # noqa: BLE001
        label = "Probar"
    return (f'<h2>Pruebas</h2><p>La comprobación de este subplan (qué probar, dónde y qué debes ver, y aprobar o rechazar su '
            f'versión) está en <a data-nav href="{e(href)}">{e(label)}</a>.</p>')
