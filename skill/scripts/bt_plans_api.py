"""Plans view backend: lookups, JSON payloads, cancel / delete / restore actions and the SSE stream.

Plans are read-only for the user: nothing here edits PLAN.json. `delete` MOVES plan artifacts into a recoverable trash
folder (never unlinks them); `cancel` goes through the scheduler core when it owns the run, else flips the PLAN.md
front-matter status. Every path is resolved and checked to stay inside the (symlink-resolved) bitácora root.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import select
import shutil
import socket
import threading
import time
from pathlib import Path
from typing import Any

import bt_lock
import bt_planstatus as ps
import bt_scheduler_adapter as scheduler_
from bt_core import find_req, req_id, set_front

TRASH_DIR = ".trash"  # per project, under the bitácora root: change here to change the retention policy
PLAN_ARTIFACTS = ("PLAN.md", "PLAN.json", "plan-revisions", "HANDOFF.md", "RUN.json", scheduler_.PROJECTION)
MANIFEST, RESTORED = "TRASH.json", "RESTORED.json"
MAX_SSE_CLIENTS = 20
KEEPALIVE_SEC = 15
_REQ = re.compile(r"^REQ-\d+$")
RUN_FINISHED = ("done", "completed", "cancelled", "failed")
_slots = threading.BoundedSemaphore(MAX_SSE_CLIENTS)


class PlanError(Exception):
    """A refused request; the message is shown to the user as the flash text."""


def _root(root: Path) -> Path:
    return Path(root).resolve()


def project_dir(root: Path, project: str) -> Path:
    root = _root(root)
    path = (root / project).resolve()
    if not project or project.startswith(".") or path.parent != root or not path.is_dir():
        raise PlanError("Proyecto no encontrado.")
    return path


def req_dir(root: Path, project: str, req: str) -> Path:
    pdir = project_dir(root, project)
    if not _REQ.match(req.upper()):
        raise PlanError("Requerimiento no válido.")
    try:
        rdir = find_req(pdir, req).resolve()
    except SystemExit as exc:
        raise PlanError("Requerimiento no encontrado.") from exc
    if rdir.parent != (pdir / "requirements").resolve():
        raise PlanError("Requerimiento fuera de la bitácora.")
    return rdir


def status_of(root: Path, project: str, req: str) -> dict[str, Any]:
    rdir = req_dir(root, project, req)
    status = ps.plan_status(project, rdir)
    status["run_action"] = run_action(project, req, rdir)
    status["decisions"] = open_decisions(rdir)
    status["open_rounds"] = open_rounds(rdir)
    status["healing"] = healing_state(rdir)
    return status


def healing_state(rdir: Path) -> dict[str, Any] | None:
    """The self-healing of the run for its page (REQ-029 R7 / REQ-030): on/off, budget, every case with what was done, and the
    last interventions. None for a plan that never ran; the page must render when the files cannot be read."""
    if not (rdir / scheduler_.PROJECTION).is_file():
        return None
    try:
        import bt_interventions
        import bt_scheduler_healing as healing
        state = healing.status(rdir)
        recent = list(bt_interventions.read(rdir))[-8:]
        state["recent"] = [{k: row.get(k) for k in ("at", "class", "source", "task", "repair", "result", "minutes_lost")}
                           for row in reversed(recent)]
        return state
    except Exception:  # noqa: BLE001 - an unreadable record is not a reason to hide the plan
        return None


def heal_control(root: Path, project: str, req: str, action: str, case: str = "") -> str:
    """The owner's hand on the self-healing from the page: stop, start or revert one case (same moves as
    `scheduler-op REQ heal`). Raises PlanError for anything else."""
    import bt_scheduler_healing as healing
    rdir = req_dir(root, project, req)
    try:
        if action == "stop":
            return healing.stop(rdir)
        if action == "start":
            return healing.start(rdir)
        if action == "revert" and case:
            return " · ".join(healing.revert(project, req, rdir, case))
    except ValueError as exc:
        raise PlanError(str(exc)) from exc
    raise PlanError("Acción de autocuración desconocida.")


def open_decisions(rdir: Path) -> list[dict[str, Any]]:
    """What the run asks its owner now (D-020); a plan without a readable scheduler run asks nothing."""
    if not (rdir / scheduler_.PROJECTION).is_file():
        return []
    try:
        import bt_page_diagnosis
        import bt_scheduler_decisions
        requests = bt_scheduler_decisions.open_requests(rdir)
    except Exception:  # noqa: BLE001 - the plan page must render even when the run state cannot be read
        return []
    for r in requests:          # /flow shows the same panel as the plan page and adds its own forms
        r["diagnosis_html"] = bt_page_diagnosis.html(r)
        r["note_prefill"] = bt_page_diagnosis.note_for(r)
    return requests


def open_rounds(rdir: Path) -> list[int]:
    import bt_rounds
    out = []
    for f in bt_rounds.list_rounds(rdir):
        try:
            data = bt_rounds.load(f)
        except (OSError, ValueError):
            continue
        if data.get("status") == "open":
            out.append(int(data.get("round") or 0))
    return out


def decide(root: Path, project: str, req: str, request_id: str, option: str, reason: str, by: str = "web") -> str:
    """Answer one decision request from the plan page; the request must still be open and offer that option."""
    import bt_scheduler_decisions
    rdir = req_dir(root, project, req)
    try:
        lines = bt_scheduler_decisions.answer(project, req, rdir, request_id, option, reason, by=by)
    except ValueError as exc:
        raise PlanError(f"No se aplicó: {exc}. Recarga la página: la petición pudo cambiar.") from exc
    except scheduler_.core.SchedulerError as exc:
        raise PlanError(str(exc)) from exc
    return f"Decisión {request_id} → {option}: " + "; ".join(lines)


def diagnose(root: Path, project: str, req: str, request_id: str) -> str:
    """Ask the diagnosing agent (again) about one open request; it answers in the background."""
    import bt_block_agent
    rdir = req_dir(root, project, req)
    if request_id not in {r["id"] for r in open_decisions(rdir)}:
        raise PlanError(f"No hay una decisión abierta {request_id}. Recarga la página.")
    if (bt_block_agent.cached(rdir, request_id) or {}).get("state") == "running":
        return f"El agente ya está diagnosticando {request_id}."
    bt_block_agent.forget(rdir, request_id)
    if not bt_block_agent.spawn(project, req, rdir, request_id):
        raise PlanError("No se pudo lanzar el agente de diagnóstico.")
    return f"El agente está diagnosticando {request_id}; el resultado aparece en la tarjeta en un minuto o dos."


# ---------------------------------------------------------------- trash

def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _files(path: Path) -> list[Path]:
    return [p for p in sorted(path.rglob("*")) if p.is_file()] if path.is_dir() else [path]


def _stamp() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")


def trash_entries(root: Path, project: str) -> list[dict[str, Any]]:
    tdir = project_dir(root, project) / TRASH_DIR
    out = []
    for entry in sorted(tdir.iterdir(), reverse=True) if tdir.is_dir() else []:
        try:
            data = json.loads((entry / MANIFEST).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        out.append({"name": entry.name, "req_id": data.get("req_id"), "deleted_at": data.get("deleted_at"),
                    "reason": data.get("reason"), "files": len(data.get("files") or [])})
    return out


def all_trash(root: Path) -> dict[str, list[dict[str, Any]]]:
    found = {}
    for pdir in sorted(_root(root).iterdir()):
        if pdir.is_dir() and not pdir.name.startswith("."):
            entries = trash_entries(root, pdir.name)
            if entries:
                found[pdir.name] = entries
    return found


def delete_plan(root: Path, project: str, req: str, confirm: str, by: str = "web", reason: str = "") -> str:
    rdir = req_dir(root, project, req)
    status = ps.plan_status(project, rdir)
    rid = status["req_id"]
    if confirm.strip().upper() != rid:
        raise PlanError(f"Para borrar escribe el id del requerimiento ({rid}).")
    if status["run"]["active"] and status["plan"]["status"] != "cancelled":
        raise PlanError("La ejecución sigue activa: cancela el plan antes de borrarlo.")
    present = [name for name in PLAN_ARTIFACTS if (rdir / name).exists()]
    if not present:
        raise PlanError("No hay artefactos de plan que mover.")
    root = _root(root)
    base = project_dir(root, project) / TRASH_DIR
    base.mkdir(exist_ok=True)
    suffix, target = 0, base / f"{rid}-{_stamp()}"
    while True:
        try:
            target.mkdir()
            break
        except FileExistsError:
            suffix += 1
            target = base / f"{rid}-{_stamp()}-{suffix}"
    files = [{"path": p.relative_to(rdir).as_posix(), "original": str(p), "sha256": _sha(p)}
             for name in present for p in _files(rdir / name)]
    manifest = {"req_id": rid, "project": project, "req_dir": rdir.relative_to(root).as_posix(),
                "deleted_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"), "by": by, "reason": reason,
                "artifacts": present, "files": files}
    (target / MANIFEST).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    with bt_lock.central_lock("plans"):
        for name in present:
            shutil.move(str(rdir / name), str(target / name))
    return f"Plan {rid} movido a la papelera ({target.name})."


def restore_plan(root: Path, project: str, entry: str) -> str:
    root = _root(root)
    tdir = (project_dir(root, project) / TRASH_DIR).resolve()
    folder = (tdir / entry).resolve()
    if not entry or folder.parent != tdir or not (folder / MANIFEST).is_file():
        raise PlanError("Entrada de papelera no encontrada.")
    manifest = json.loads((folder / MANIFEST).read_text(encoding="utf-8"))
    rdir = (root / manifest["req_dir"]).resolve()
    if rdir.parent != (project_dir(root, project) / "requirements").resolve() or not rdir.is_dir():
        raise PlanError("El requerimiento de destino ya no existe.")
    names = [n for n in manifest["artifacts"] if n in PLAN_ARTIFACTS]
    clash = [n for n in names if (rdir / n).exists()]
    if clash:
        raise PlanError("No se restaura: ya existe " + ", ".join(clash) + " en el requerimiento.")
    with bt_lock.central_lock("plans"):
        for name in names:
            shutil.move(str(folder / name), str(rdir / name))
        (folder / MANIFEST).rename(folder / RESTORED)
    return f"Plan {manifest['req_id']} restaurado."


# ---------------------------------------------------------------- cancel

def cancel_plan(root: Path, project: str, req: str, confirm: str, by: str = "web") -> str:
    rdir = req_dir(root, project, req)
    status = ps.plan_status(project, rdir)
    rid = status["req_id"]
    if confirm.strip().upper() != rid:
        raise PlanError(f"Para cancelar escribe el id del requerimiento ({rid}).")
    if status["plan"]["status"] == "cancelled":
        raise PlanError("El plan ya estaba cancelado.")
    authority = status["run"]["authority"]
    note = ""
    if authority == "scheduler":
        try:
            scheduler_.apply_control(rdir, "stop", by=by)
        except SystemExit as exc:
            raise PlanError(str(exc)) from exc
        note = " El scheduler cancelló la ejecución; es irreversible."
    elif authority == "legacy" and status["run"]["active"]:
        note = " La ejecución heredada (RUN.json) no tiene supervisor: solo se canceló el plan."
    plan_md = rdir / "PLAN.md"
    if plan_md.is_file():
        with bt_lock.central_lock("plans"):
            set_front(plan_md, "status", "cancelled")
    return f"Plan {rid} cancelado.{note}"


# ---------------------------------------------------------------- JSON + stream

# ---------------------------------------------------------------- run from the plan page

def run_action(project: str, req: str, rdir: Path) -> dict[str, str] | None:
    """What the plan page's run button does now: approve and launch, launch, resume a held run, or nothing."""
    import bt_scheduler_ops as ops
    from bt_core import _front
    status = _front(rdir / "PLAN.md", "status") if (rdir / "PLAN.md").is_file() else ""
    if status == "review":
        return {"action": "approve", "label": "Aprobar y ejecutar"}
    projection = rdir / scheduler_.PROJECTION      # only a scheduler run can be resumed; RUN.json runs have no owner
    if status == "approved" and not projection.is_file() and not (rdir / "RUN.json").is_file():
        return {"action": "launch", "label": "Ejecutar"}
    if status in ("launched", "in-progress") and projection.is_file():
        try:
            run = json.loads(projection.read_text(encoding="utf-8")).get("status")
        except (OSError, ValueError):
            run = None
        if run in RUN_FINISHED:
            return None
        if ops.on_hold(rdir) or (not ops.owner_pids(project, req) and not ops.watching(rdir)):
            return {"action": "resume", "label": "Reanudar ejecución"}
    return None


def run_plan(root: Path, project: str, req: str, expected: str, by: str = "web") -> str:
    """Run the plan from its page. `expected` is the action the page showed: a stale page never does something else."""
    rdir = req_dir(root, project, req)
    act = run_action(project, req, rdir)
    if not act:
        raise PlanError("Este plan ya se está ejecutando o no se puede ejecutar en su estado actual.")
    if act["action"] != expected:
        raise PlanError("El estado del plan cambió; revisa la página antes de volver a pulsar.")
    if act["action"] == "resume":
        import bt_scheduler_ops as ops
        return f"Ejecución reanudada: {ops.resume(project, req, rdir)}."
    if act["action"] == "approve":
        import bt_rounds
        bt_rounds.plan_decide(rdir, True, "", by)
    from bt_launch import launch
    try:
        info = launch(project, req, background=True)
    except SystemExit as exc:
        raise PlanError(str(exc)) from exc
    return ("Plan aprobado y lanzado" if act["action"] == "approve" else "Plan lanzado") + f" en {info['workdir']}."


def plans_payload(root: Path, filt: str = "all") -> list[dict[str, Any]]:
    rows = ps.list_plans(_root(root))
    return [r for r in rows if r["active"]] if filt == "active" else rows


FINGERPRINT_TTL = 0.5        # one stat sweep over every run serves all live clients for this long
FRAME_TTL = 1.5              # one parse + render of the plans serves every client watching the same view
_shared_lock = threading.Lock()
_shared: dict[Any, tuple[float, Any]] = {}


def _shared_value(key: Any, build, ttl: float) -> Any:
    """`build()` at most once per `ttl` for a key, however many SSE clients ask. Clients wait on the lock instead of each
    parsing every plan, so N open tabs cost the same as one. An exception is not cached."""
    with _shared_lock:
        hit = _shared.get(key)
        if hit and time.monotonic() - hit[0] < ttl:
            return hit[1]
        value = build()
        stamp = time.monotonic()
        for stale in [k for k, (at, _) in _shared.items() if stamp - at > 60]:
            del _shared[stale]                     # frames are keyed by fingerprint: drop the old ones
        _shared[key] = (stamp, value)
        return value


def _changed_frame(root: Path, plan: tuple[str, str] | None, filt: str) -> bytes:
    from bt_page_plans import detail_fragment, index_fragment
    rows = plans_payload(root)
    shown = [r for r in rows if r["active"]] if filt == "active" else rows
    frame = _event("plans", {"plans": rows, "html": index_fragment(shown, filt)})
    if plan:
        try:
            status = status_of(root, *plan)
            frame += _event("plan", {"status": status, "html": detail_fragment(status)})
        except PlanError:
            pass
    return frame


def stream(handler, root: Path, plan: tuple[str, str] | None, filt: str, sleep_tick: float = 0.25) -> None:
    """Serve one SSE client until it disconnects. Events: `plans` on any plan change, `plan` for the watched one."""
    base = _root(root)
    if not _slots.acquire(blocking=False):
        return handler.send("Demasiados clientes en vivo", 503, "text/plain")
    try:
        handler.send_response(200)
        for key, value in (("Content-Type", "text/event-stream; charset=utf-8"), ("Cache-Control", "no-store"),
                           ("X-Accel-Buffering", "no"), ("Connection", "close")):
            handler.send_header(key, value)
        handler.end_headers()
        handler.close_connection = True
        out = handler.wfile
        out.write(b"retry: 3000\n: connected\n\n")
        out.flush()

        def fingerprint() -> str:
            return _shared_value(("fingerprint", base), lambda: ps.fingerprint(base), FINGERPRINT_TTL)

        seen, last_beat = fingerprint(), time.monotonic()
        last_frame = 0.0
        while True:
            readable, _, _ = select.select([handler.connection], [], [], sleep_tick)
            if readable and not handler.connection.recv(1, socket.MSG_PEEK):
                return  # client closed
            now = fingerprint()
            if now != seen and time.monotonic() - last_frame >= FRAME_TTL:   # a busy run is coalesced, never dropped
                seen = now
                out.write(_shared_value(("frame", base, plan, filt, now), lambda: _changed_frame(root, plan, filt), FRAME_TTL))
                out.flush()
                last_frame = time.monotonic()
                last_beat = time.monotonic()
            elif time.monotonic() - last_beat >= KEEPALIVE_SEC:
                out.write(b": keepalive\n\n")
                out.flush()
                last_beat = time.monotonic()
    except (BrokenPipeError, ConnectionResetError, OSError, ValueError):
        return
    finally:
        _slots.release()


def _event(name: str, data: dict) -> bytes:
    return f"event: {name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n".encode()
