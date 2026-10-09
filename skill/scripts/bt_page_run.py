"""Marathon tab of a requirement: live view of RUN.json (progress, heartbeat, tasks, log) and pause/resume/stop.

Reads RUN.json directly (plain JSON, tolerant of a half-written file) and writes the controls through
bt_runstate.update (locked read-modify-write), so a button never clobbers what the supervisor saved meanwhile.
"""
from __future__ import annotations

import socket
from html import escape as e

from bt_core import *  # noqa: F403
from bt_pages import badge, purl

ACTIVE = ("running", "waiting", "paused")
CONTROLS = {"pause": "pause", "stop": "stop", "resume": None}
STALE_EXTRA_MIN = 10


def run_file(rdir: Path) -> Path:
    return rdir / "RUN.json"


def load_run(rdir: Path) -> dict | None:
    try:
        data = json.loads(run_file(rdir).read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def progress(run: dict) -> tuple[int, int]:
    tasks = run.get("tasks") or []
    return sum(1 for t in tasks if t.get("status") == "done"), len(tasks)


def age_minutes(iso: str | None) -> float | None:
    if not iso:
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


def is_stale(run: dict) -> bool:
    """An active (running/waiting/paused) marathon whose heartbeat is older than one session timeout plus a margin:
    the supervisor is gone. Waits and pauses heartbeat too, so they are checked the same way."""
    if run.get("status") not in ACTIVE:
        return False
    limit = ((run.get("limits") or {}).get("session_timeout_min") or 60) + STALE_EXTRA_MIN
    age = age_minutes((run.get("heartbeat") or {}).get("at"))
    return age is None or age > limit


def active_runs(pdir: Path) -> list[dict]:
    """Marathons of a project that are running, waiting or paused (for the dashboard)."""
    out = []
    for f in sorted(pdir.glob("requirements/REQ-*/RUN.json")):
        run = load_run(f.parent)
        if run and run.get("status") in ACTIVE:
            done, total = progress(run)
            out.append({"req": run.get("req") or req_id(f.parent), "status": run["status"], "done": done,
                        "total": total, "age": age_minutes((run.get("heartbeat") or {}).get("at")),
                        "stale": is_stale(run)})
    return out


def apply_control(rdir: Path, action: str) -> str:
    """Write the pause/resume/stop request into RUN.json (the supervisor honors it between sessions)."""
    if action not in CONTROLS:
        raise SystemExit(f"Acción desconocida: {action}")
    if load_run(rdir) is None:
        raise SystemExit("Este requerimiento no tiene RUN.json (no se lanzó en modo maratón).")
    import bt_runstate  # locked read-modify-write: never overwrites what the supervisor saved meanwhile
    run = bt_runstate.update(rdir, lambda s: s.update(control=CONTROLS[action]))
    status = run.get("status")
    if action == "resume":
        if status in ("stopped", "blocked", "done"):
            return (f"Control limpiado, pero la maratón está '{status}': no hay supervisor corriendo. "
                    f"Relánzala con bitacora.py run {run.get('req', '')} --resume.")
        return "Maratón reanudada: el supervisor continúa en su próximo ciclo."
    where = "al terminar la sesión en curso" if status == "running" else "en su próximo ciclo"
    return f"Orden '{action}' enviada: el supervisor la aplica {where}."


def _task_rows(run: dict) -> str:
    cur = (run.get("heartbeat") or {}).get("task")
    rows = []
    for t in run.get("tasks") or []:
        err = (t.get("last_error") or "")[:80]
        pid = t.get("pending_id")
        rows.append(
            f'<tr{" class=current" if t.get("id") == cur and run.get("status") == "running" else ""}>'
            f'<td>{e(str(t.get("id", "")))}</td><td>{e(str(t.get("title", "")))}</td><td>{e(str(t.get("repo") or "—"))}</td>'
            f'<td>{badge(str(t.get("status", "todo")))}</td><td>{t.get("attempts", 0)}</td>'
            f'<td class="muted">{e(err)}</td><td>{e(pid) if pid else ""}</td></tr>')
    return ('<table><tr><th>ID</th><th>Tarea</th><th>Repo</th><th>Estado</th><th>Intentos</th>'
            f'<th>Último error</th><th>Pendiente</th></tr>{"".join(rows)}</table>')


def _log_rows(run: dict) -> str:
    rows = []
    for x in reversed((run.get("log") or [])[-30:]):
        rows.append(f'<tr><td>{e(str(x.get("at", ""))[:19].replace("T", " "))}</td><td>#{e(str(x.get("session", "")))}</td>'
                    f'<td>{e(str(x.get("task", "")))}</td><td>{badge(str(x.get("result", "")))}</td>'
                    f'<td>{e(str(x.get("seconds", "")))}s</td><td>{e(str(x.get("summary", "")))}</td></tr>')
    return ('<table><tr><th>Hora</th><th>Sesión</th><th>Tarea</th><th>Resultado</th><th>Duración</th>'
            f'<th>Resumen</th></tr>{"".join(rows)}</table>') if rows else '<p class="muted">Sin sesiones todavía.</p>'


def run_panel(project: str, rid: str, rdir: Path, token: str) -> str:
    run = load_run(rdir)
    if run is None:
        return '<p class="muted">Este requerimiento no se lanzó en modo maratón.</p>'
    done, total = progress(run)
    hb = run.get("heartbeat") or {}
    age = age_minutes(hb.get("at"))
    status = str(run.get("status", "?"))
    kpis = [f'<span class="kpi">estado {badge(status)}</span>',
            f'<span class="kpi">progreso {done}/{total}</span>',
            f'<span class="kpi">agente {e(str(run.get("agent", "")))} · {e(str(run.get("model", "")))}'
            f'{" · ultracode" if run.get("ultracode") else ""}</span>',
            f'<span class="kpi">sesión #{e(str(hb.get("session", "—")))} · tarea {e(str(hb.get("task") or "—"))}</span>',
            f'<span class="kpi">latido {fmt_age(age)}</span>']
    if run.get("waiting_until"):
        kpis.append(f'<span class="kpi">espera hasta {e(str(run["waiting_until"])[:16].replace("T", " "))}</span>')
    if run.get("control"):
        kpis.append(f'<span class="kpi">orden pendiente: {e(str(run["control"]))}</span>')
    notes = ""
    if is_stale(run):
        mins = ((run.get("limits") or {}).get("session_timeout_min") or 60) + STALE_EXTRA_MIN
        notes += (f'<div class="notice warn">El latido tiene más de {mins} min: el supervisor parece detenido '
                  f'(¿reinicio o ventana cerrada?). Relánzalo con <code>bitacora.py --project {e(project)} run '
                  f'{e(rid)} --resume</code>.</div>')
    if hb.get("machine") and hb["machine"] != socket.gethostname():
        notes += f'<div class="notice warn">Esta maratón corre en otra máquina: {e(str(hb["machine"]))}.</div>'
    if hb.get("state"):
        notes += f'<p class="muted">{e(str(hb["state"]))}</p>'
    bar = f'<progress max="{max(total, 1)}" value="{done}" style="width:100%"></progress>'
    act = purl(project, "req", rid, "run")

    def btn(action: str, label: str, cls: str = "secondary") -> str:
        return (f'<form method="post" action="{act}" style="display:inline">'
                f'<input type="hidden" name="token" value="{e(token)}"><input type="hidden" name="action" value="{action}">'
                f'<button class="{cls}" type="submit">{label}</button></form>')
    controls = (f'<div class="actions">{btn("pause", "Pausar")}{btn("resume", "Reanudar", "")}{btn("stop", "Detener")}'
                f'{btn("monitor", "Abrir monitor remoto")}</div>'
                f'<p class="muted">Monitor remoto: sesión «{e(project)} {e(rid)} maratón» en claude.ai/code o la app de '
                f'Claude (Remote Control) — pregúntale cómo va, o pídele pausar/reanudar/detener.</p>')
    return (f'<div class="kpis">{"".join(kpis)}</div>{bar}{notes}{controls}<h2>Tareas</h2>{_task_rows(run)}'
            f'<h2>Últimas sesiones</h2>{_log_rows(run)}')
