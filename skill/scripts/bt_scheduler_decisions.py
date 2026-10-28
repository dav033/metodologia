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
    "rework_impact": ("La auditoría rechazó esta tarea y pide devolver más tareas ya aceptadas de las que el sistema rehace sin tu permiso (gates.rework_confirm_over). Lo normal es que los hallazgos se conviertan en tareas de remediación sin tocar lo aceptado; esto aparece cuando una auditoría agotó sus rondas o sus hallazgos no se pudieron convertir. Reintentar hace que la auditoría mire de nuevo el árbol actual; si de verdad quieres rehacer ese trabajo aceptado, hazlo tú con `scheduler-op REQ rework <tareas> --confirm` viendo el coste estimado.", False, "retry_with_note"),
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


# What each kind of stop needs from the owner and what the owner can do about it. The error itself is read from the run.
_TRANSIENT = ("No es un fallo del código: la tarea espera tu decisión de volver a intentarlo.",
              ["Reintenta: casi siempre basta.",
               "Si el motivo es la cuota de un agente, mira `globalusage` y reintenta cuando se renueve."])
_CODE = ("Decidir cómo seguir: leer el error de abajo y reintentar, con una indicación tuya o cambiando el plan.",
         ["Si el error es del entorno (una variable que falta, un servicio caído, dependencias, un permiso), arréglalo y reintenta.",
          "Si es del código, reintenta con una indicación (`retry_with_note`) que diga qué cambiar.",
          "Si el plan está mal planteado, corrígelo (nueva revisión) y pasa el run a ella (`revise`)."])
_INTEGRITY = ("Que una persona mire primero: la evidencia del intento no es fiable y nadie responde por ti.",
              ["Mira el estado del run con `scheduler-op status` y el trabajo del intento antes de decidir.",
               "Si no hay nada raro, reintenta."])
GUIDE = {
    "attempts_exhausted": _CODE, "timeout_repeated": _CODE, "same_cause_limit": _CODE, "decision_limit": _CODE,
    "permanent_or_unknown_cause": _CODE,
    "rework_impact": ("Decidir si la auditoría vuelve a mirar el árbol actual o si pagas el coste de rehacer trabajo aceptado.",
                      ["Reintenta para que la auditoría revise el árbol de ahora (la remediación ya está integrada).",
                       "Si quieres rehacer las tareas aceptadas, `scheduler-op REQ rework <tareas> --confirm` te dice antes cuántas son y cuántos minutos cuestan."]),
    "rework_limit": ("Decidir si la auditoría vuelve a mirar el árbol actual, con una indicación tuya si quieres.",
                     ["Reintenta para que la auditoría revise el árbol de ahora (los arreglos previos ya están integrados).",
                      "Con `retry_with_note` dile qué hallazgos priorizar."]),
}
for _code in ("handoff_missing", "transience_unconfirmed", "quota_reset_unknown", "wait_limit", "wait_window_exceeded",
              "elapsed_limit", "manual_cancel", "stale_or_cancelled"):
    GUIDE[_code] = _TRANSIENT
for _code in ("identity_unverified", "execution_unsettled", "evidence_from_future", "evidence_stale", "evidence_insufficient",
              "cause_state_mismatch", "verification_evidence_missing"):
    GUIDE[_code] = _INTEGRITY
UNKNOWN_GUIDE = ("Mirar el motivo de abajo: el sistema no lo reconoce y no sabe cómo seguir solo.",
                 ["Reintenta con una indicación tuya si sabes qué pasó.", "Si no, detén el run y revisa el intento."])
INFRA_ISSUES = ("SANDBOX_UNAVAILABLE", "RUNNER_BUSY", "CHECK_TIMEOUT")
MAX_ERROR = 1500


def _clip(text: str, limit: int = MAX_ERROR) -> str:
    text = (text or "").strip()
    return text if len(text) <= limit else text[:limit].rstrip() + " …"


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


def append_audit_notes(rdir: Path, task: str, text: str) -> None:
    """Add the owner's words to what the system already wrote from the audit's findings (never replace the findings)."""
    text = text.strip()
    if not text:
        return
    path = audit_notes_path(rdir, task)
    try:
        existing = path.read_text(encoding="utf-8").strip()
    except OSError:
        existing = ""
    if text in existing:
        return
    write_audit_notes(rdir, task, f"{existing}\n\nOwner's note:\n{text}" if existing else text)


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


def automatic_answers(rdir: Path, task: str, option: str) -> int:
    """How many times the scheduler itself (not a person) already answered `option` for `task`."""
    count = 0
    try:
        for line in answers_path(rdir).read_text(encoding="utf-8").splitlines():
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if entry.get("by") == "scheduler" and entry.get("task") == task and entry.get("option") == option:
                count += 1
    except OSError:
        pass
    return count


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


def _manual_closure(rdir: Path, attempt_id: str) -> str:
    """Who ended the attempt by hand and why («cancelled by operator: wrong base»), or ''."""
    import bt_attempt_facts
    import bt_run_stores

    if not attempt_id:
        return ""
    try:
        m1 = bt_run_stores.paths(rdir).get("m1")
    except Exception:  # noqa: BLE001 - explaining a stop never stops the explanation
        return ""
    return bt_attempt_facts.resolution_text(bt_attempt_facts.manual_resolutions(m1).get(attempt_id))


def _start_rejected(code: str):
    """The scheduler refused to start the attempt (`start rejected: <CODE>`) or the verifier refused its order (`verify rejected: <CODE>`): its
    own evidence, not an integrity anomaly, so it is not an owner-only decision and the self-healing may answer it."""
    for prefix, what in (("start_rejected_", "arrancar el intento"), ("verify_rejected_", "aceptar la orden de verificación")):
        if code.startswith(prefix):
            return (f"El scheduler no pudo {what}: {code[len(prefix):].upper()}. La evidencia es del propio sistema (no un fallo de "
                    "integridad), y el error de abajo dice qué choca o qué falta; el trabajo terminado se conserva.", False, "retry")
    return None


def _blocked(doc: dict, rdir: Path) -> list[dict]:
    out = []
    for task, rec in doc.get("tasks", {}).items():
        if rec.get("state") != "blocked":
            continue
        code = reason_code(rec.get("reason", ""))
        known = REASONS.get(code) or _start_rejected(code)
        what, unskippable, recommended = known if known else (
            f"La tarea está bloqueada por una razón que el sistema no reconoce: «{rec.get('reason', '')[:200]}».", True, "retry_with_note")
        attempts = rec.get("attempts", [])
        last = doc.get("attempts", {}).get(attempts[-1], {}) if attempts else {}
        options = [RETRY, RETRY_NOTE]
        if _newer_revision(rdir, int(doc.get("revision", 0))):
            options.append(REVISE)
        options.append(STOP)
        needs, you_can = known and (GUIDE.get(code) or _TRANSIENT) or UNKNOWN_GUIDE
        closed = _manual_closure(rdir, last.get("id", ""))
        error = _clip("\n".join(x for x in (verify_notes(rdir, task), f"Cerrado a mano: {closed}" if closed else "",
                                              f"Último fallo: {last.get('failure')}" if last.get("failure") else "",
                                              f"Motivo del bloqueo: {rec.get('reason', '')}" if not known else "") if x))
        out.append({
            "needs": needs, "you_can": list(you_can), "error": error,
            "id": f"{task}:{len(attempts)}" + (f":{rec['reason']}" if rec.get("reason", "").startswith("analyst_not_the_task:") else ""), "source": "task", "task": task, "attempt": last.get("id", ""),
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
        checks = [(f"Comprobar a mano: {c.get('command', '?')[:300]}" if c.get("issue_code") == "CHECK_MANUAL" else
                   f"{c.get('command', '?')[:90]} → {c.get('status')}" + (f" ({c['issue_code']})" if c.get("issue_code") else ""))
                  for c in result.get("checks", [])]
        issues = [f"{i.get('code')}: {i.get('detail')}" for i in result.get("issues", [])]
        criteria = [f"criterio {str(c.get('status', '?')).upper()}: {str(c.get('criterion', ''))[:160]}"
                    for c in result.get("criteria", [])]
        if doc.get("attempts", {}).get(request.get("attempt_id"), {}).get("state") not in ("verifying", "uncertain"):
            continue          # the attempt moved on (cancelled, rebased away): nobody is waiting for this review
        codes = {c.get("issue_code") for c in result.get("checks", [])} | {i.get("code") for i in result.get("issues", [])}
        if codes & set(INFRA_ISSUES):
            needs = "Rechazar para que la tarea se reintente: el verificador no pudo comprobar nada, no es un fallo de la tarea."
            you_can = ["Rechaza (`review_fail`) con la razón; el sistema reintenta en un entorno sano.",
                       "No apruebes a mano: nada se comprobó."]
        elif "CHECK_MANUAL" in codes:
            needs = "Comprobar a mano lo que dicen los criterios manuales y responder si se cumple."
            you_can = ["Haz la comprobación descrita abajo (por ejemplo en el teléfono) y aprueba (`review_pass`, con tu razón) si se cumple.",
                       "Si no se cumple, rechaza (`review_fail`) y di qué falló."]
        else:
            needs = "Decidir si los checks que no dieron veredicto bastan para aceptar la tarea."
            you_can = ["Mira los checks de abajo: si fallaron por el entorno, rechaza para reintentar.",
                       "Aprueba a mano solo si tú mismo comprobaste lo que ellos no pudieron."]
        out.append({
            "needs": needs, "you_can": you_can, "error": _clip("\n".join(issues)),
            "id": row["request_key"], "source": "review", "task": request.get("task_id", ""),
            "attempt": request.get("attempt_id", ""), "title": f"{request.get('task_id', '?')}: el verificador pide una persona",
            "what": "Las comprobaciones no pudieron dar un veredicto y el verificador espera que decida una persona.",
            "reason": "needs_review", "evidence": issues + criteria + checks, "options": [STOP] if rdir.parent.parent.name == "pictures" and request.get("plan_id") == "REQ-021" and request.get("task_id") == "T3.2" else [FAIL, PASS, STOP],
            "recommended": "review_fail", "unskippable": True})
    return out


def _plan(rdir: Path):
    try:
        return adapter.approved_plan(rdir)
    except Exception:  # noqa: BLE001 - without the plan a diagnosis just knows less
        return None


def _context(rdir: Path, doc: dict, request: dict) -> dict:
    """The evidence the rules and the agent read for one request."""
    import bt_attempt_history

    attempts = doc.get("tasks", {}).get(request["task"], {}).get("attempts", [])
    task = request["source"] == "task"
    history = bt_attempt_history.entries(rdir, request["task"], doc)
    return {"verify": verify_notes(rdir, request["task"]),
            "failures": [doc.get("attempts", {}).get(a, {}).get("failure", "") for a in attempts],
            "repeats": bt_attempt_history.repeats(history),
            "closed": _manual_closure(rdir, request.get("attempt", "")) if task else "",
            "refused": _refused_rework(rdir, request.get("attempt", "")) if task else {}}


def _refused_rework(rdir: Path, attempt_id: str) -> dict:
    """{named, why} when the audit gate could not send the tasks of an audit's findings back (M1 `rework_refused`)."""
    import bt_run_stores

    try:
        m1 = bt_run_stores.paths(rdir).get("m1")
        if not attempt_id or m1 is None or not Path(m1).exists():
            return {}
        conn = _ro(m1)
        try:
            row = conn.execute("SELECT detail FROM audit WHERE kind = 'rework_refused' AND attempt_id = ? "
                               "ORDER BY seq DESC LIMIT 1", (attempt_id,)).fetchone()
        finally:
            conn.close()
        body = json.loads(row[0]) if row else {}
    except (sqlite3.Error, OSError, ValueError, TypeError):
        return {}
    return body if isinstance(body, dict) else {}


def _explain(rdir: Path, doc: dict, request: dict, plan) -> dict:
    """Attach what failed, its origin and the steps (`diagnosis`), an option that fixes it in one move when there is
    one, and the agent's diagnosis when one was asked (`agent`)."""
    import bt_block_agent
    import bt_block_diagnosis

    request["project"], request["req"] = Path(rdir).parent.parent.name, _req_of(rdir)
    try:
        diagnosis, extra = bt_block_diagnosis.explain(request, doc, plan=plan, req=_req_of(rdir), **_context(rdir, doc, request))
    except Exception:  # noqa: BLE001 - explaining a stop never stops the card
        diagnosis, extra = None, []
    if extra:
        stop = [o for o in request["options"] if o["id"] == "stop"]
        request["options"] = [o for o in request["options"] if o["id"] != "stop"] + extra + stop
    if diagnosis and diagnosis["confidence"] == "alta" and diagnosis["option"] in {o["id"] for o in request["options"]}:
        request["recommended"] = diagnosis["option"]
        # the reason code's generic guidance («look first, the evidence is not reliable») would contradict a known cause
        if request.get("source") == "task":
            request["needs"] = f"{diagnosis['headline']}. Elegir la opción recomendada ({diagnosis['option']}) o la que prefieras."
    request["diagnosis"] = diagnosis
    request["agent"] = bt_block_agent.cached(rdir, request["id"])
    return request


def _req_of(rdir: Path) -> str:
    return "-".join(Path(rdir).name.split("-")[:2])


def open_requests(rdir: Path) -> list[dict]:
    """Every question the run is waiting on, derived from its state, each with its diagnosis. Answered ones are left out."""
    rdir = Path(rdir)
    done = _answered(rdir)
    doc = _state(rdir)
    found = [r for r in _blocked(doc, rdir) + _reviews(rdir, doc) if r["id"] not in done]
    plan = _plan(rdir) if found else None
    return [_explain(rdir, doc, r, plan) for r in found]


def evidence(rdir: Path, request: dict) -> str:
    """What the diagnosing agent reads for one request (bt_block_diagnosis.bundle)."""
    import bt_block_diagnosis

    rdir = Path(rdir)
    doc = _state(rdir)
    answered = []
    try:
        for line in answers_path(rdir).read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row.get("task") == request["task"]:
                answered.append(row)
    except (OSError, ValueError):
        pass
    ctx = _context(rdir, doc, request)
    import bt_attempt_history

    history = bt_attempt_history.prompt(rdir, request["task"], doc)
    return bt_block_diagnosis.bundle(request, plan=_plan(rdir), verify=ctx["verify"],
                                     failures=[history] if history else ctx["failures"],
                                     notes=operator_notes(rdir, request["task"]), audit=audit_notes(rdir, request["task"]),
                                     answered=answered, rule=request.get("diagnosis"))


def _record(rdir: Path, request: dict, option: str, by: str, reason: str, result: list[str]) -> None:
    line = {"request": request["id"], "task": request["task"], "option": option, "by": by, "reason": reason,
            "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "result": result}
    if by != "scheduler":          # what the scheduler answers itself is recorded by the healing cycle, with its class
        import bt_healing_classify
        import bt_interventions

        bt_interventions.record(rdir, kind=bt_healing_classify.class_of_diagnosis(request.get("diagnosis")), source="manual",
                                task=request["task"], evidence=str(request.get("title") or request.get("what") or ""),
                                repair=f"{option}: {reason[:300]}", result="fixed", request=request["id"])
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
    needs_reason = option in {"retry_with_note", "review_pass", "review_fail", "rework_findings"}
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
    elif option in ("rework_conflict", "rework_findings"):
        target = next(o["target"] for o in request["options"] if o["id"] == option)
        if option == "rework_findings":                 # the findings the owner wrote reach each task's next prompt
            for name in target.split(","):
                append_audit_notes(rdir, name, f"The independent audit {task} still finds, in the current tree:\n{reason.strip()}")
        result = ops.apply(project, req, rdir, "rework", target, reason or f"decision {request_id}: redo {target} on the "
                           f"current work it clashed with", only=True)
        if task in ops.status(project, req, rdir)["blocked_tasks"]:
            result += ops.apply(project, req, rdir, "reopen", task, f"decision {request_id}: waits for {target}")
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
        store = _open_store(QualityStore, bt_run_stores.paths(rdir)["m6"])
        try:
            store.resolve_review(request["id"], by, verdict, reason)
        finally:
            close = getattr(store, "close", None)
            if callable(close):
                close()
    return [f"owner stopped: {stopped}", f"review {request['id']}: {verdict} by {by}; the owner delivers it on restart"]


def _open_store(cls, path, wait: float = 15.0):
    """The M6 store once the stopped owner's last process lets go of it (a verifier child can outlive it a moment)."""
    deadline = time.monotonic() + wait
    while True:
        try:
            return cls(path)
        except Exception as exc:  # noqa: BLE001 - QualityError; only STORE_IN_USE is worth waiting for
            if getattr(exc, "code", "") != "STORE_IN_USE" or time.monotonic() > deadline:
                raise
            time.sleep(0.5)


def auto_diagnoser(project: str, req: str, rdir: Path):
    """What the watchdog passes to `announce`: start the diagnosing agent per new request (config `diagnosis.auto`)."""
    import bt_block_agent
    import bt_config
    if not bt_config.get("diagnosis.auto"):
        return None
    return lambda request: bt_block_agent.spawn(project, req, Path(rdir), request["id"])


def announce(project: str, req: str, rdir: Path, notify=None, diagnose=None) -> list[str]:
    """Notify once per new open request and hand it to `diagnose` (see auto_diagnoser); returns the ids announced.
    Best effort: a run without state announces nothing."""
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
        what = (request.get("diagnosis") or {}).get("headline") or request["needs"]
        notify(f"Bitácora · {req}", f"{request['title']}{flag}. {what}. Detalle y opciones: scheduler-op {req} decisions")
        if diagnose:
            try:
                diagnose(request)
            except Exception:  # noqa: BLE001 - the watchdog must never fail because of a diagnosis
                pass
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
                 f"  Qué pasó: {r['what']}", f"  Qué necesita de ti: {r['needs']}"]
        if r.get("error"):
            lines += ["  Error:"] + [f"    {x}" for x in r["error"].splitlines()[:14]]
        lines += [f"  · {e}" for e in r["evidence"][:8]]
        rule, agent = r.get("diagnosis"), r.get("agent") or {}
        d = agent if agent.get("state") == "done" and (rule or {}).get("confidence") != "alta" else rule  # as the panel
        if d:
            lines += [f"  Diagnóstico ({d.get('source', 'reglas')}): [{d['label']}] {d['headline']}", f"    Origen: {d['origin']}"]
            lines += [f"    {n}. {x}" for n, x in enumerate(d["steps"], 1)]
        else:
            lines += ["  Qué puedes hacer:"] + [f"    - {x}" for x in r["you_can"]]
        for o in r["options"]:
            star = " (recomendada)" if o["id"] == r["recommended"] else ""
            lines.append(f"  - {o['id']}{star}: {o['label']}. {o['consequence']}")
        lines.append(f"  Responder: scheduler-op {req} decide {r['id']} <opción> [--reason \"…\"]")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)
