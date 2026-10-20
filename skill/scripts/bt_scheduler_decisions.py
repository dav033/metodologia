"""Decision requests: what a run asks its owner when it cannot go on alone.

A blocked task or an open verifier review used to be a bare reason code («m5:timeout_repeated»). A request says what
happened, with the evidence, offers closed options that name their consequence and recommends one. It is derived from the
run's own state (nothing to keep in sync); only the answers are stored, as an append-only file next to the run.

Unskippable requests are the ones nobody may answer on the owner's behalf (a human override of the verifier, an
integrity anomaly, a reason this module does not know). No request is ever answered by a timeout: waiting is the safe state.
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

import bt_scheduler_adapter as adapter
import bt_scheduler_ops as ops

ANSWERS = "RUN.decisions.jsonl"
NOTES = "RUN.notes"
NOTIFIED = "RUN.decisions.notified.json"

RETRY = {"id": "retry", "label": "Reintentar",
         "consequence": "Un intento nuevo, que sigue desde el último snapshot si existe. Gasta un intento."}
RETRY_NOTE = {"id": "retry_with_note", "label": "Reintentar con una indicación tuya",
              "consequence": "Como reintentar, y tu nota entra en el prompt del agente. Exige --reason."}
REVISE = {"id": "revise", "label": "Pasar el run a la última revisión del plan",
          "consequence": "Cancela los intentos vivos y rebasa; las tareas cuya definición cambió se rehacen."}
STOP = {"id": "stop", "label": "Detener el run",
        "consequence": "Para el scheduler y el vigilante hasta que lo reanudes. Nada más se ejecuta."}
PASS = {"id": "review_pass", "label": "Aprobar a mano (anula al verificador)",
        "consequence": "La tarea se acepta sin que las comprobaciones lo hayan probado. Queda tu nombre y tu razón. Exige --reason."}
FAIL = {"id": "review_fail", "label": "Rechazar",
        "consequence": "La tarea se rechaza y el sistema decide si reintenta. Exige --reason."}

# reason code -> (what happened, unskippable, recommended option)
REASONS = {
    "attempts_exhausted": ("Se agotaron los intentos y ninguno pasó la verificación.", False, "retry"),
    "timeout_repeated": ("El agente superó dos veces el límite de tiempo.", False, "retry"),
    "same_cause_limit": ("Los intentos fallaron una y otra vez por la misma causa.", False, "retry_with_note"),
    "decision_limit": ("La recuperación automática ya decidió demasiadas veces sobre esta tarea.", False, "retry_with_note"),
    "permanent_or_unknown_cause": ("El fallo no es de los que se reintentan solos.", False, "retry_with_note"),
    "handoff_missing": ("El intento terminó sin un snapshot del trabajo que sirva para continuar.", False, "retry"),
    "transience_unconfirmed": ("No se pudo confirmar que el fallo fuera pasajero.", False, "retry"),
    "quota_reset_unknown": ("Se agotó la cuota y no se sabe cuándo se renueva.", False, "retry"),
    "wait_limit": ("Ya esperó el máximo de veces a que se renueve algo.", False, "retry"),
    "wait_window_exceeded": ("La espera necesaria supera la ventana permitida.", False, "retry"),
    "elapsed_limit": ("Pasó demasiado tiempo desde el primer fallo.", False, "retry"),
    "rework_limit": ("La auditoría rechazó esta tarea otra vez, pero alguna de las tareas que señala ya fue devuelta el máximo de veces permitido (gates.max_reworks) y el sistema no las reabre solo. Lo normal es que los hallazgos se conviertan en tareas de remediación sin preguntarte; esto aparece cuando una auditoría ya agotó sus rondas (gates.remediation_rounds) o sus hallazgos no se pudieron convertir. Reintentar sirve para que la auditoría mire de nuevo el árbol actual; con una indicación puedes decirle qué priorizar.", False, "retry_with_note"),
    "manual_cancel": ("Alguien canceló el intento.", False, "retry"),
    "stale_or_cancelled": ("El intento quedó cancelado u obsoleto.", False, "retry"),
    # integrity anomalies: the evidence itself cannot be trusted, so a person looks first
    "identity_unverified": ("No se pudo comprobar qué proceso produjo el resultado.", True, "retry"),
    "execution_unsettled": ("El executor no confirma si el agente terminó.", True, "retry"),
    "evidence_from_future": ("La evidencia lleva una fecha posterior a ahora.", True, "retry"),
    "evidence_stale": ("La evidencia del fallo es demasiado vieja para decidir con ella.", True, "retry"),
    "evidence_insufficient": ("No hay evidencia suficiente del fallo.", True, "retry"),
    "cause_state_mismatch": ("La causa del fallo y el estado del executor no cuadran.", True, "retry"),
    "verification_evidence_missing": ("La verificación rechazó el intento sin dejar su evidencia.", True, "retry"),
}


def answers_path(rdir: Path) -> Path:
    return Path(rdir) / ANSWERS


def notes_path(rdir: Path, task: str) -> Path:
    return Path(rdir) / NOTES / f"{task}.md"


def operator_notes(rdir: Path, task: str) -> str:
    """The owner's indications for a task, to go into its next prompt."""
    try:
        text = notes_path(rdir, task).read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    return f"Indications from the owner for this task (they come first):\n{text}" if text else ""


def audit_notes_path(rdir: Path, task: str) -> Path:
    return Path(rdir) / NOTES / f"{task}.audit.md"


def write_audit_notes(rdir: Path, task: str, text: str) -> None:
    """What the independent audit found wrong with a task, written by the system when it sends the task back."""
    path = audit_notes_path(rdir, task)
    if not text.strip():                                # the task passed: what it was told no longer applies
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def verify_notes_path(rdir: Path, task: str) -> Path:
    return Path(rdir) / NOTES / f"{task}.verify.md"


def write_verify_notes(rdir: Path, task: str, text: str) -> None:
    """Why the independent verification rejected the last attempt (empty text clears it once the task passes)."""
    path = verify_notes_path(rdir, task)
    if not text.strip():
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def verify_notes(rdir: Path, task: str) -> str:
    """The failing checks of the previous attempt, to go into the next prompt: a retry that cannot see why it failed
    repeats the failure (REQ-027 T17 failed three times on the same sandbox error)."""
    try:
        return verify_notes_path(rdir, task).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def audit_notes(rdir: Path, task: str) -> str:
    """The system's audit indications for a task, to go into its next prompt."""
    try:
        text = audit_notes_path(rdir, task).read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    return f"Indications from the independent audit for this task (they come first):\n{text}" if text else ""


def _answered(rdir: Path) -> set[str]:
    found = set()
    try:
        for line in answers_path(rdir).read_text(encoding="utf-8").splitlines():
            try:
                found.add(json.loads(line)["request"])
            except (ValueError, KeyError, TypeError):
                continue
    except OSError:
        pass
    return found


def _ro(path: Path):
    conn = sqlite3.connect(f"{Path(path).resolve().as_uri()}?mode=ro", uri=True, timeout=2)
    conn.row_factory = sqlite3.Row
    return conn


def _state(rdir: Path) -> dict:
    conn = _ro(adapter.run_db_path(rdir))
    try:
        return json.loads(conn.execute("SELECT doc FROM state WHERE id = 1").fetchone()[0])
    finally:
        conn.close()


def reason_code(reason: str) -> str:
    text = (reason or "").strip()
    for prefix in ("m5:", "m5_"):
        if text.startswith(prefix):
            return text[len(prefix):]
    return text


def _newer_revision(rdir: Path, current: int) -> bool:
    try:
        return adapter.approved_plan(rdir).revision > current
    except Exception:  # noqa: BLE001 - no frozen plan to move to
        return False


def _blocked(doc: dict, rdir: Path) -> list[dict]:
    out = []
    for task, rec in doc.get("tasks", {}).items():
        if rec.get("state") != "blocked":
            continue
        code = reason_code(rec.get("reason", ""))
        known = REASONS.get(code)
        what, unskippable, recommended = known if known else (
            f"La tarea está bloqueada por una razón que el sistema no reconoce: «{rec.get('reason', '')[:200]}».", True, "retry_with_note")
        attempts = rec.get("attempts", [])
        last = doc.get("attempts", {}).get(attempts[-1], {}) if attempts else {}
        options = [RETRY, RETRY_NOTE]
        if _newer_revision(rdir, int(doc.get("revision", 0))):
            options.append(REVISE)
        options.append(STOP)
        out.append({
            "id": f"{task}:{len(attempts)}", "source": "task", "task": task, "attempt": last.get("id", ""),
            "title": f"{task} bloqueada: {code or 'sin razón'}", "what": what, "reason": rec.get("reason", ""),
            "evidence": [e for e in (f"intentos: {len(attempts)}", f"último fallo: {last.get('failure')}" if last.get("failure") else "",
                                     f"evidencia: {last.get('evidence')}" if last.get("evidence") else "") if e],
            "options": options, "recommended": recommended, "unskippable": unskippable})
    return out


def _reviews(rdir: Path, doc: dict) -> list[dict]:
    import bt_run_stores

    path = bt_run_stores.paths(rdir).get("m6")
    if path is None or not Path(path).exists():
        return []
    out = []
    conn = _ro(path)
    try:
        rows = conn.execute("SELECT r.request_key, q.request_json, q.result_json FROM reviews r JOIN requests q "
                            "ON q.idempotency_key = r.request_key WHERE r.state = 'open'").fetchall()
    except sqlite3.Error:
        return []
    finally:
        conn.close()
    for row in rows:
        try:
            request, result = json.loads(row["request_json"]), json.loads(row["result_json"] or "{}")
        except ValueError:
            continue
        checks = [f"{c.get('command', '?')[:90]} → {c.get('status')}" + (f" ({c['issue_code']})" if c.get("issue_code") else "")
                  for c in result.get("checks", [])]
        issues = [f"{i.get('code')}: {i.get('detail')}" for i in result.get("issues", [])]
        if doc.get("attempts", {}).get(request.get("attempt_id"), {}).get("state") not in ("verifying", "uncertain"):
            continue          # the attempt moved on (cancelled, rebased away): nobody is waiting for this review
        out.append({
            "id": row["request_key"], "source": "review", "task": request.get("task_id", ""),
            "attempt": request.get("attempt_id", ""), "title": f"{request.get('task_id', '?')}: el verificador pide una persona",
            "what": "Las comprobaciones no pudieron dar un veredicto y el verificador espera que decida una persona.",
            "reason": "needs_review", "evidence": issues + checks, "options": [FAIL, PASS, STOP],
            "recommended": "review_fail", "unskippable": True})
    return out


def open_requests(rdir: Path) -> list[dict]:
    """Every question the run is waiting on, derived from its state. Answered ones are left out."""
    rdir = Path(rdir)
    done = _answered(rdir)
    doc = _state(rdir)
    found = _blocked(doc, rdir) + _reviews(rdir, doc)
    return [r for r in found if r["id"] not in done]


def _record(rdir: Path, request: dict, option: str, by: str, reason: str, result: list[str]) -> None:
    line = {"request": request["id"], "task": request["task"], "option": option, "by": by, "reason": reason,
            "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "result": result}
    with answers_path(rdir).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(line, ensure_ascii=False) + "\n")


def answer(project: str, req: str, rdir: Path, request_id: str, option: str, reason: str = "",
           by: str = "owner") -> list[str]:
    """Carry out one option of one open request. Raises ValueError for anything that is not offered."""
    rdir = Path(rdir)
    request = next((r for r in open_requests(rdir) if r["id"] == request_id), None)
    if request is None:
        raise ValueError(f"no open request {request_id}")
    if option not in {o["id"] for o in request["options"]}:
        raise ValueError(f"{option} is not offered for {request_id}: " + ", ".join(o["id"] for o in request["options"]))
    needs_reason = option in {"retry_with_note", "review_pass", "review_fail"}
    if needs_reason and not reason.strip():
        raise ValueError(f"{option} needs --reason")
    task = request["task"]
    if option == "retry":
        result = ops.apply(project, req, rdir, "reopen", task, reason or f"decision {request_id}: retry")
    elif option == "retry_with_note":
        path = notes_path(rdir, task)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(reason.strip() + "\n", encoding="utf-8")
        result = [f"{task}: note saved"] + ops.apply(project, req, rdir, "reopen", task, f"decision {request_id}: retry with a note")
    elif option == "revise":
        result = ops.apply(project, req, rdir, "revise", "", reason or f"decision {request_id}: revise")
    elif option == "stop":
        ops.hold_path(rdir).write_text(json.dumps({"why": f"decision {request_id}: stop"}) + "\n", encoding="utf-8")
        result = [f"owner stopped: {ops.stop_owner(project, req)}; held"]
    else:
        result = _resolve_review(project, req, rdir, request, "PASS" if option == "review_pass" else "FAIL", by, reason)
    _record(rdir, request, option, by, reason, result)
    if option != "stop":
        result.append(ops.resume(project, req, rdir))
    return result


def _resolve_review(project: str, req: str, rdir: Path, request: dict, verdict: str, by: str, reason: str) -> list[str]:
    import bt_run_stores
    from bt_scheduler_quality.store import QualityStore

    with ops.hold(rdir, f"review {request['id']}: {verdict}"):
        stopped = ops.stop_owner(project, req)
        store = QualityStore(bt_run_stores.paths(rdir)["m6"])
        try:
            store.resolve_review(request["id"], by, verdict, reason)
        finally:
            close = getattr(store, "close", None)
            if callable(close):
                close()
    return [f"owner stopped: {stopped}", f"review {request['id']}: {verdict} by {by}; the owner delivers it on restart"]


def announce(project: str, req: str, rdir: Path, notify=None) -> list[str]:
    """Notify once per new open request; returns the ids announced. Best effort: a run without state announces nothing."""
    if notify is None:
        import bt_notify
        notify = bt_notify.notify
    try:
        requests = open_requests(rdir)
    except Exception:  # noqa: BLE001 - the watchdog must never fail because of a notification
        return []
    path = Path(rdir) / NOTIFIED
    try:
        seen = set(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError):
        seen = set()
    fresh = [r for r in requests if r["id"] not in seen]
    for request in fresh:
        flag = " (nadie puede responder por ti)" if request["unskippable"] else ""
        notify(f"Bitácora · {req}", f"{request['title']}{flag}. Responde con: scheduler-op {req} decisions")
    if fresh:
        try:
            path.write_text(json.dumps(sorted(seen | {r["id"] for r in fresh})), encoding="utf-8")
        except OSError:
            pass
    return [r["id"] for r in fresh]


def render(requests: list[dict], req: str) -> str:
    if not requests:
        return "Ninguna decisión pendiente."
    blocks = []
    for r in requests:
        lines = [f"{r['id']}  {r['title']}" + ("   [nadie puede responder por ti]" if r["unskippable"] else ""),
                 f"  Qué pasó: {r['what']}"]
        lines += [f"  · {e}" for e in r["evidence"][:8]]
        for o in r["options"]:
            star = " (recomendada)" if o["id"] == r["recommended"] else ""
            lines.append(f"  - {o['id']}{star}: {o['label']}. {o['consequence']}")
        lines.append(f"  Responder: scheduler-op {req} decide {r['id']} <opción> [--reason \"…\"]")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)
