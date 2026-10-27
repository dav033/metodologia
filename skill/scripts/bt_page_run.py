"""Run tab of a requirement: authority-specific status view and pause/resume/stop controls.

Legacy runs (RUN.json written by the retired supervisor) are shown read-only. Scheduler runs read RUN.projection.json
and send controls to M1.
"""
from __future__ import annotations

import math
from html import escape as e

import bt_page_attempts as attempts_
import bt_runtier as tier_
import bt_scheduler_adapter as scheduler_
from bt_core import *  # noqa: F403
from bt_pages import badge, purl

ACTIVE = ("running", "waiting", "paused")
CONTROLS = {"pause": "pause", "stop": "stop", "resume": None}
STALE_EXTRA_MIN = 10
SCHEDULER_STALE_MIN = scheduler_.SCHEDULER_STALE_MINUTES


def run_file(rdir: Path) -> Path:
    return rdir / "RUN.json"


def load_run(rdir: Path) -> dict | None:
    if scheduler_.scheduler_authority(rdir):
        return scheduler_.read_projection(rdir)
    try:
        data = json.loads(run_file(rdir).read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def scheduler_authority(rdir: Path) -> bool:
    return scheduler_.scheduler_authority(rdir)


def has_run(rdir: Path) -> bool:
    return scheduler_authority(rdir) or run_file(rdir).is_file()


def progress(run: dict) -> tuple[int, int]:
    tasks = run.get("tasks") or []
    return sum(1 for t in tasks if t.get("status") == "done"), len(tasks)


def age_minutes(iso: str | None) -> float | None:
    if not isinstance(iso, str) or not iso:
        return None
    try:
        at = dt.datetime.fromisoformat(iso)
        now = dt.datetime.now(at.tzinfo) if at.tzinfo else dt.datetime.now()
        return max(0.0, (now - at).total_seconds() / 60)
    except ValueError:
        return None


def fmt_age(minutes: float | None) -> str:
    if minutes is None:
        return "sin latido"
    if minutes < 1:
        return "hace segundos"
    if minutes < 90:
        return f"hace {int(minutes)} min"
    if minutes < 48 * 60:
        return f"hace {minutes / 60:.1f} h"
    return f"hace {minutes / 1440:.1f} d"


def _format_quota_epoch(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return "sin dato"
    try:
        timestamp = float(value)
        if not math.isfinite(timestamp):
            return "sin dato"
        at = dt.datetime.fromtimestamp(timestamp, tz=dt.UTC)
    except (OverflowError, OSError, ValueError):
        return "sin dato"
    return at.strftime("%Y-%m-%d %H:%M:%S UTC")


def is_stale(run: dict) -> bool:
    """An active (running/waiting/paused) marathon whose heartbeat is older than one session timeout plus a margin:
    the supervisor is gone. Waits and pauses heartbeat too, so they are checked the same way."""
    if run.get("status") not in ACTIVE:
        return False
    limit = ((run.get("limits") or {}).get("session_timeout_min") or 60) + STALE_EXTRA_MIN
    age = age_minutes((run.get("heartbeat") or {}).get("at"))
    return age is None or age > limit


def active_runs(pdir: Path) -> list[dict]:
    """Active legacy and Scheduler runs of a project, each read from its authority."""
    out = []
    for rdir in sorted(path for path in (pdir / "requirements").glob("REQ-*") if path.is_dir()):
        run = load_run(rdir)
        is_scheduler = scheduler_authority(rdir)
        if run is None and is_scheduler:
            out.append({"req": req_id(rdir), "status": "desconocido", "done": 0, "total": 0,
                        "age": None, "stale": True, "authority": "scheduler"})
            continue
        if run and run.get("status") in ACTIVE:
            done, total = progress(run)
            is_scheduler = run.get("authority") == scheduler_.AUTHORITY
            stale = scheduler_is_stale(run) if is_scheduler else is_stale(run)
            out.append({"req": run.get("req") or req_id(rdir), "status": run["status"], "done": done,
                        "total": total, "age": age_minutes((run.get("heartbeat") or {}).get("at")),
                        "stale": stale, "authority": "scheduler" if is_scheduler else "legacy"})
    return out


def scheduler_is_stale(run: dict) -> bool:
    return scheduler_.projection_is_stale(run)


def apply_control(rdir: Path, action: str) -> str:
    """Route a run control through its authority, preserving legacy state and Scheduler ownership."""
    if action not in CONTROLS:
        raise SystemExit(f"Acción desconocida: {action}")
    if scheduler_authority(rdir):
        scheduler_.apply_control(rdir, action, by="web")
        return {"pause": "Ejecución Scheduler pausada.", "resume": "Ejecución Scheduler reanudada.",
                "stop": "Cancelación enviada a M1."}[action]
    raise SystemExit("Ejecución heredada (RUN.json): su supervisor fue retirado y ya no admite controles. "
                     "Los planes nuevos corren con el Scheduler (bitacora.py launch).")


def _tier_cell(run: dict, t: dict) -> str:
    tier = tier_.tier_of(t)
    if run.get("pool"):  # the router decides per session: show who ran it last, or that it is still open
        last = t.get("last_route") or {}
        who = (f'{last.get("profile") or last.get("agent")} · {tier_.label(last.get("model"), last.get("effort"))}'
               if last else "según cuota y resultados")
        return f'{e(who)} <span class="muted">(nivel {tier})</span>'
    return f'{e(tier_.label(*tier_.model_for(run, tier)))} <span class="muted">(nivel {tier})</span>'


def _task_rows(run: dict) -> str:
    cur = (run.get("heartbeat") or {}).get("task")
    rows = []
    for t in run.get("tasks") or []:
        err = (t.get("last_error") or "")[:80]
        pid = t.get("pending_id")
        rows.append(
            f'<tr{" class=current" if t.get("id") == cur and run.get("status") == "running" else ""}>'
            f'<td>{e(str(t.get("id", "")))}</td><td>{e(str(t.get("milestone") or "—"))}</td>'
            f'<td>{e(str(t.get("title", "")))} <span class="muted">{e(str(t.get("kind") or ""))}</span></td>'
            f'<td>{e(str(t.get("repo") or "—"))}</td>'
            f'<td>{badge(str(t.get("status", "todo")))}</td><td>{_tier_cell(run, t)}</td><td>{t.get("attempts", 0)}</td>'
            f'<td class="muted">{e(err)}</td><td>{e(pid) if pid else ""}</td></tr>')
    return ('<table><tr><th>ID</th><th>Hito</th><th>Tarea</th><th>Repo</th><th>Estado</th><th>Modelo</th><th>Intentos</th>'
            f'<th>Último error</th><th>Pendiente</th></tr>{"".join(rows)}</table>')


def _log_rows(run: dict) -> str:
    rows = []
    for x in reversed((run.get("log") or [])[-30:]):
        model = attempts_.model_chip(x.get("agent"), x.get("model"), x.get("effort")) if x.get("model") else "—"
        if x.get("profile") or x.get("agent"):
            model = f'{e(str(x.get("profile") or x.get("agent")))} · {model}'
        rows.append(f'<tr><td>{e(str(x.get("at", ""))[:19].replace("T", " "))}</td><td>#{e(str(x.get("session", "")))}</td>'
                    f'<td>{e(str(x.get("task", "")))}</td><td>{model}</td><td>{badge(str(x.get("result", "")))}</td>'
                    f'<td>{e(str(x.get("seconds", "")))}s</td><td>{e(str(x.get("summary", "")))}</td></tr>')
    return ('<table><tr><th>Hora</th><th>Sesión</th><th>Tarea</th><th>Agente · modelo</th><th>Resultado</th><th>Duración</th>'
            f'<th>Resumen</th></tr>{"".join(rows)}</table>') if rows else '<p class="muted">Sin sesiones todavía.</p>'


def run_panel(project: str, rid: str, rdir: Path, token: str) -> str:
    run = load_run(rdir)
    if run is None:
        if scheduler_authority(rdir):
            command = f"bitacora.py --project {project} scheduler-run {rid} --resume"
            return (f'<div class="notice warn">La proyección Scheduler no disponible. La base M1 se conserva. '
                    f'Reconstruye la vista con <code>{e(command)}</code>.</div>')
        return '<p class="muted">Este requerimiento no tiene ejecución registrada.</p>'
    if run.get("authority") == scheduler_.AUTHORITY:
        import bt_page_verification
        return bt_page_verification.run_card(project, rid, rdir) + _scheduler_run_panel(project, rid, run, token)
    done, total = progress(run)
    hb = run.get("heartbeat") or {}
    age = age_minutes(hb.get("at"))
    status = str(run.get("status", "?"))
    kpis = [f'<span class="kpi">estado {badge(status)}</span>',
            f'<span class="kpi">progreso {done}/{total}</span>',
            f'<span class="kpi">{"agentes " + e(", ".join(run["pool"])) if run.get("pool") else "agente " + e(str(run.get("agent", ""))) + " · " + e(str(run.get("model", "")))}'
            f'{" · ultracode" if run.get("ultracode") else ""}</span>',
            f'<span class="kpi">sesión #{e(str(hb.get("session", "—")))} · tarea {e(str(hb.get("task") or "—"))}</span>',
            f'<span class="kpi">latido {fmt_age(age)}</span>']
    if run.get("waiting_until"):
        kpis.append(f'<span class="kpi">espera hasta {e(str(run["waiting_until"])[:16].replace("T", " "))}</span>')
    if run.get("control"):
        kpis.append(f'<span class="kpi">orden pendiente: {e(str(run["control"]))}</span>')
    notes = '<div class="notice warn">Ejecución heredada (RUN.json): solo lectura; su supervisor fue retirado.</div>'
    if hb.get("state"):
        notes += f'<p class="muted">{e(str(hb["state"]))}</p>'
    bar = f'<progress max="{max(total, 1)}" value="{done}" style="width:100%"></progress>'
    return (f'<div class="kpis">{"".join(kpis)}</div>{bar}{notes}<h2>Tareas</h2>{_task_rows(run)}'
            f'<h2>Últimas sesiones</h2>{_log_rows(run)}')


def _stage_kpi(run: dict) -> str:
    """D-134: the subplans this run holds and how many the plan still has outside it."""
    stage = run.get("stage") if isinstance(run.get("stage"), dict) else None
    if not stage:
        return ""
    held = ", ".join(str(x) for x in stage.get("subplans") or [])
    outside = len(stage.get("outside") or [])
    text = f"etapa {held}" + (f" · faltan {outside} subplanes" if outside else " · plan completo")
    if stage.get("joining"):
        text += f" · se une r{stage['joining']}"
    return f'<span class="kpi" title="Subplanes aprobados que ejecuta el Scheduler">{e(text)}</span>'


def _scheduler_run_panel(project: str, rid: str, run: dict, token: str) -> str:
    done, total = progress(run)
    hb = run.get("heartbeat") or {}
    age = age_minutes(hb.get("at"))
    status = str(run.get("status", "?"))
    stale = scheduler_is_stale(run)
    plan = run.get("plan_ref") or {}
    kpis = (f'<span class="kpi">autoridad Scheduler M1</span><span class="kpi">estado {badge(status)}</span>'
            f'<span class="kpi">progreso {done}/{total}</span><span class="kpi">latido {fmt_age(age)}</span>'
            f'<span class="kpi">plan r{e(str(plan.get("revision", "?")))}</span>' + _stage_kpi(run))
    notes = ""
    if stale:
        command = f"bitacora.py --project {project} scheduler-run {rid} --resume"
        notes = (f'<div class="notice warn">El latido Scheduler supera {SCHEDULER_STALE_MIN} min; '
                 f'el proceso puede haberse detenido. Reanuda con <code>{e(command)}</code>.</div>')
    rows = []
    for task in run.get("tasks", []):
        if not isinstance(task, dict):
            continue
        model = str(task.get("model") or "")
        model_cell = None
        if model:
            model_label = " · ".join(part for part in (str(task.get("provider") or ""),
                                                        str(task.get("profile") or ""), model) if part)
            if task.get("effort"):
                model_label += f' ({task["effort"]})'
            prefix = " · ".join(part for part in (str(task.get("provider") or ""), str(task.get("profile") or "")) if part)
            model_cell = (f'{e(prefix + " · " if prefix else "")}'
                          f'{attempts_.model_chip(task.get("provider"), model, task.get("effort") or None)}')
            route_status = {"recommended": "planificado", "assigned": "revalidado al iniciar"}.get(
                str(task.get("route_status", "")), "")
            if route_status:
                model_label += f" · {route_status}"
                model_cell += f" · {e(route_status)}"
        else:
            model_label = {"unavailable": "Sin ruta elegible", "unplanned": "Pendiente"}.get(
                str(task.get("route_status", "")), "—")
            route_reason = str(task.get("route_reason") or "")
            if route_reason:
                model_label += f" · motivo: {route_reason}"
        quota_state = str(task.get("quota_state") or "")
        account = str(task.get("account_ref") or "")
        route_details = []
        if account:
            route_details.append(f"cuenta {account}")
        if quota_state:
            quota_text = f"cuota {quota_state}"
            observed = str(task.get("quota_observed_at") or "")
            valid_until = str(task.get("quota_valid_until") or "")
            used = str(task.get("quota_used_percent") or "")
            if observed:
                quota_text += f" · observada {_format_quota_epoch(observed)}"
            if valid_until:
                quota_text += f" · válida hasta {_format_quota_epoch(valid_until)}"
            if used:
                quota_text += f" · uso {used}%"
            route_details.append(quota_text)
        quota_reason = str(task.get("quota_reason") or "")
        if quota_reason:
            route_details.append(f"evidencia {quota_reason}")
        selection_reason = str(task.get("selection_reason") or "")
        if selection_reason:
            route_details.append(f"selección {selection_reason}")
        route_detail = "<br>".join(e(value) for value in route_details) or "—"
        rows.append(
            f'<tr><td>{e(str(task.get("id", "")))}</td><td>{e(str(task.get("milestone") or "—"))}</td>'
            f'<td>{e(str(task.get("title", "")))}</td><td>{e(str(task.get("complexity") or "—"))}</td>'
            f'<td>{model_cell if model_cell is not None else e(model_label)}</td><td>{route_detail}</td>'
            f'<td>{badge(str(task.get("scheduler_state", task.get("status", "?"))))}</td>'
            f'<td>{e(str(task.get("attempts", 0)))}</td></tr>')
    table = (f'<table><tr><th>ID</th><th>Hito</th><th>Tarea</th><th>Complejidad</th><th>Modelo M2</th>'
             f'<th>Cuenta y evidencia de cuota</th><th>Estado M1</th><th>Intentos</th></tr>{"".join(rows)}</table>'
             if rows else '<p class="muted">El plan no tiene tareas en la proyección.</p>')
    controls = ""
    if status in ACTIVE:
        action_url = purl(project, "req", rid, "run")

        def btn(action: str, label: str) -> str:
            return (f'<form method="post" action="{action_url}" style="display:inline">'
                    f'<input type="hidden" name="token" value="{e(token)}">'
                    f'<input type="hidden" name="action" value="{action}">'
                    f'<button type="submit">{label}</button></form>')

        controls = f'<div class="actions">{btn("pause", "Pausar")}{btn("resume", "Reanudar")}' \
                   f'{btn("stop", "Detener")}</div>'
    return (f'<div class="kpis">{kpis}</div><progress max="{max(total, 1)}" value="{done}" '
            f'style="width:100%"></progress>{notes}{controls}<h2>Tareas</h2>{table}')
