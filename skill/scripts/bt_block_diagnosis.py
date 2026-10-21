"""Why a run stopped, in words the owner can act on: what failed, where it comes from, how to fix it, which option.

A decision request names a reason code («identity_unverified») that is often not the cause: REQ-027 T16 was «identity
unverified» because its start was refused by a clash between two earlier tasks, and REQ-020 T1 was «attempts exhausted»
because a plan check ran `git` in a sandbox without git metadata. `explain` reads the run's own evidence (start
rejections, the M6 failure notes, every attempt's failure, closures by hand) and matches known causes; each one says
the origin, the steps and the option to pick, and may add an option that fixes it in one move (rework the task that
must be redone). A cause it does not know falls back to the guidance of the reason code. `bt_block_agent` asks a cheap
model to read the same evidence (`bundle`) when the rules are not enough. Nothing here changes the run.
"""
from __future__ import annotations

import re

# kind -> (label shown on the chip, colour token of the web theme)
KINDS = {
    "conflict": ("Conflicto entre tareas", "warn"),
    "plan": ("Defecto del plan", "lav"),
    "environment": ("Entorno", "info"),
    "dependency": ("Dependencias", "info"),
    "code": ("Código", "bad"),
    "quota": ("Cuota del agente", "warn"),
    "cancelled": ("Cancelado", "muted"),
    "verifier": ("Verificador", "info"),
    "manual": ("Comprobación manual", "lav"),
    "integrity": ("Integridad", "bad"),
    "unknown": ("Sin identificar", "muted"),
}
CONFLICT = re.compile(r"INTEGRATION_CONFLICT:\s*(?P<left>[\w.+-]+) vs (?P<right>[\w.-]+) for (?P<task>[\w.-]+):\s*(?P<files>.*)")
ENV_VAR = re.compile(r"\b([A-Z][A-Z0-9]*_[A-Z0-9_]{2,})\b[^\n]{0,40}?\b(?:is not set|not set|is missing|missing|"
                     r"undefined|is required|required)\b|(?:missing|undefined|required|falta)[^\n]{0,30}?\b([A-Z][A-Z0-9]*_[A-Z0-9_]{2,})\b")
MODULE = re.compile(r"Cannot find (?:module|package) ['\"](?P<name>[^'\"]+)['\"]|No module named ['\"]?(?P<py>[\w.]+)")
AUDIT_GATE = re.compile(r"audit gate: \d+ open blocking finding\(s\): (?P<findings>[^|]+)")
CONNECTION = re.compile(r"ECONNREFUSED\s*(?P<addr>[\w.:\[\]-]+)?|connection refused|could not connect to server", re.I)


def _text(*parts: str) -> str:
    return "\n".join(p for p in parts if p)


def _diag(kind: str, headline: str, origin: str, steps: list[str], option: str, note: str = "",
          confidence: str = "alta") -> dict:
    label, tone = KINDS[kind]
    return {"kind": kind, "label": label, "tone": tone, "headline": headline, "origin": origin, "steps": steps,
            "option": option, "note": note, "confidence": confidence, "source": "reglas"}


def _offered(request: dict, option: str, fallback: str) -> str:
    return option if option in {o["id"] for o in request.get("options", [])} else fallback


def _redone(doc: dict, task: str) -> bool:
    """Was the task's accepted result replaced by a redo (two or more accepted attempts)?"""
    attempts = doc.get("tasks", {}).get(task, {}).get("attempts", [])
    return sum(doc.get("attempts", {}).get(a, {}).get("state") == "accepted" for a in attempts) >= 2


def conflict_target(doc: dict, plan, members: list[str]) -> str:
    """Which task of a clash must be redone: the one built on an earlier result of another member that was redone
    since. Without that evidence, the right-hand side (the work merged last)."""
    for task in members:
        try:
            ancestors = set(plan.ancestors(task)) if plan is not None else set()
        except Exception:  # noqa: BLE001 - an unknown id: no evidence from it
            ancestors = set()
        if any(other in ancestors and _redone(doc, other) for other in members if other != task):
            return task
    return members[-1]


def _conflict(request: dict, doc: dict, plan, match: re.Match, req: str) -> tuple[dict, list[dict]]:
    left, right, files = match["left"].split("+"), match["right"], match["files"].strip(" ,…")
    members = [*left, right]
    target = conflict_target(doc, plan, members)
    others = " y ".join(m for m in members if m != target)
    task = request["task"]
    origin = (f"{task} no puede arrancar: para darle su base hay que combinar el trabajo de {' + '.join(left)} con el "
              f"de {right}, y los dos cambiaron las mismas líneas ({files}). {target} se construyó sobre un resultado "
              f"anterior de {others}, que después se rehízo; ni combinándolos sobre ese resultado anterior se resuelve.")
    option = {"id": "rework_conflict", "target": target,
              "label": f"Rehacer {target} sobre el trabajo actual",
              "consequence": f"{target} vuelve a hacerse encima del resultado vigente de {others}; {task} espera a "
                             f"que termine y arranca sobre la base combinada. No gasta intentos de {task}."}
    steps = [f"Pulsa «{option['label']}»: el sistema devuelve {target} (solo esa tarea) para rehacerla.",
             f"Cuando {target} se acepte, {task} arranca sola sobre la base combinada.",
             f"Por terminal: `scheduler-op {req} rework {target} --only --reason \"conflicto con {others}\"`."]
    return _diag("conflict", f"Conflicto de código entre {' + '.join(left)} y {right}", origin, steps,
                 "rework_conflict"), [option]


def lineage_between(doc: dict, plan, audit: str, named: list[str]) -> list[str]:
    """The accepted tasks that sit between the named ones and the audit: they hold the OLD version of what the named
    tasks change, and the audit reads the tree they build. A fix that does not reach them never reaches the audit
    (REQ-027: T8a was redone for F41/F42 and T18 found the same two again, because T9 -> T16 -> T17 kept the old file)."""
    if plan is None:
        return []
    try:
        before_audit = set(plan.ancestors(audit))
        found = {m for n in named for m in plan.descendants(n)} & before_audit
    except Exception:  # noqa: BLE001 - an unknown id: no lineage evidence
        return []
    done = {t for t, rec in (doc.get("tasks") or {}).items() if rec.get("state") == "completed"}
    order = [spec.id for spec in getattr(plan, "tasks", ())]
    return [t for t in order if t in found and t in done and t not in named and t != audit]


def _findings(request: dict, match: re.Match, refused: dict, req: str, lineage: list[str] | None = None
              ) -> tuple[dict, list[dict]]:
    task, named = request["task"], [str(t) for t in refused.get("named") or []]
    lineage = [t for t in lineage or [] if t not in named]
    found = match["findings"].strip()
    why = refused.get("why", "")
    option = []
    steps = ["Lee los hallazgos en el informe de la auditoría (el log del último intento) y escribe cada uno, con "
             f"su evidencia, en `RUN.notes/<tarea>.audit.md` de la tarea que señala: es lo que el agente leerá."]
    if named:
        everything = [*named, *lineage]
        targets = ",".join(everything)
        extra = (f" También se rehacen {', '.join(lineage)}: están entre esas tareas y la auditoría y conservan la versión "
                 "vieja, así que sin ellas el arreglo no llegaría al árbol que se audita." if lineage else "")
        option = [{"id": "rework_findings", "target": targets, "label": f"Devolver {', '.join(everything)} para que los arreglen",
                   "consequence": f"{', '.join(everything)} se rehacen (solo ellas) con las notas de la auditoría; {task} "
                                  "vuelve a auditar cuando terminen. Es lo que el sistema haría si no hubiera llegado "
                                  "a su límite de devoluciones. Exige escribir los hallazgos: llegan a cada tarea como nota."
                                  + extra}]
        steps += [f"Pulsa «{option[0]['label']}».",
                  f"Por terminal: `scheduler-op {req} rework {targets} --only --reason \"hallazgos {found}\"`."]
    else:
        steps += ["Reintenta con una indicación que diga qué hallazgos revisar primero."]
    origin = (f"La auditoría {task} sigue encontrando hallazgos bloqueantes abiertos ({found}) en el árbol actual. "
              f"Normalmente el sistema convierte los hallazgos en tareas de remediación o devuelve las tareas que "
              f"señalan, pero ya usó sus rondas" + (f" ({why})" if why else "") + ", así que espera tu decisión. "
              "Reintentar la auditoría sin arreglar nada volverá a dar los mismos hallazgos.")
    return _diag("code", f"La auditoría sigue encontrando {found}", origin, steps,
                 "rework_findings" if named else "retry_with_note"), option


def explain(request: dict, doc: dict, *, repeats: int = 0, **evidence) -> tuple[dict, list[dict]]:
    """(diagnosis, extra options) for one open request; `repeats`: how many of the last attempts failed the same way
    (bt_attempt_history). A known cause that keeps coming back says so: the owner sees it is not a one-off."""
    diagnosis, extra = _match(request, doc, repeats=repeats, **evidence)
    if repeats >= 2 and not diagnosis["headline"].startswith("Los últimos"):
        diagnosis["origin"] += f" Ya van {repeats} intentos seguidos con este mismo fallo: reintentar igual no lo arregla."
    return diagnosis, extra


def _match(request: dict, doc: dict, *, plan=None, verify: str = "", failures: list[str] | None = None,
           closed: str = "", refused: dict | None = None, repeats: int = 0, req: str = "REQ") -> tuple[dict, list[dict]]:
    """(diagnosis, extra options) for one open request. `failures` are the task's attempts' failures, oldest first."""
    failures = [f for f in (failures or []) if f]
    last = failures[-1] if failures else ""
    text = _text(verify, last, request.get("error", ""))
    task, code = request.get("task", "?"), request.get("reason", "")
    revise = _offered(request, "revise", "retry_with_note")
    if request.get("source") == "review":
        bad = _unsupported(plan, task) if "CHECK_UNSUPPORTED" in "\n".join(request.get("evidence") or []) else []
        if bad:
            listed = "; ".join(f"«{cmd[:120]}» ({why})" for cmd, why in bad)
            return _diag("plan", "El verificador no acepta un comando del plan",
                         f"El verificador compila todos los comandos de la tarea juntos y rechazó {listed}. Con uno "
                         "rechazado no corre ninguno: la tarea no se juzgó, el trabajo puede estar bien.",
                         ["Corrige ese comando en PLAN.json (un solo comando por verificación, sin |, ;, $ ni &&; "
                          "solo se admite un cd <carpeta> && al principio), sube la revisión y congélala con "
                          f"`bitacora.py plan-json freeze {req}`.",
                          "Rechaza esta revisión con la razón y pasa el run a la revisión nueva."], "review_fail"), []
        return _review(request), []
    match = CONFLICT.search(last) or CONFLICT.search(request.get("error", ""))
    if match:
        return _conflict(request, doc, plan, match, req)
    gate = AUDIT_GATE.search(last)
    if gate and code.endswith("rework_limit"):
        return _findings(request, gate, refused or {}, req,
                         lineage_between(doc, plan, request["task"], [str(t) for t in (refused or {}).get("named") or []]))
    if "not a git repository" in text:
        return _diag("plan", "Una comprobación del plan usa git y el verificador no tiene git",
                     "El verificador corre las comprobaciones en una copia limpia de los archivos, sin la carpeta .git. "
                     "Un comando de verificación del plan llama a git, así que falla siempre, haga lo que haga el agente: "
                     "el código no es el problema.",
                     ["Corrige el plan: quita esa comprobación o conviértela en manual (type: manual) en PLAN.json, "
                      "con la revisión subida en 1.",
                      f"Congela la revisión: `bitacora.py plan-json freeze {req}`.",
                      "Elige «Pasar el run a la última revisión del plan»."], revise), []
    if "EROFS" in text or "read-only file system" in text.lower():
        return _diag("environment", "La prueba intenta escribir en una carpeta de solo lectura",
                     "En el verificador node_modules (y las dependencias instaladas) están montadas de solo lectura. "
                     "La tarea instala o modifica dependencias durante la prueba (npm ci / npm install), y eso falla "
                     "antes de que corra ninguna prueba.",
                     ["Reintenta con la indicación propuesta: que la prueba no instale dependencias si ya están.",
                      "Revisa que el comando de verificación no ejecute npm ci/install."], "retry_with_note",
                     note="The verification sandbox mounts node_modules read-only, so installing dependencies inside a "
                          "check fails with EROFS before any test runs. Do not install dependencies in tests or "
                          "verification commands; use the installed ones and run the checks again before finishing."), []
    module = MODULE.search(text)
    if module:
        name = module["name"] or module["py"]
        return _diag("dependency", f"Falta la dependencia {name}",
                     f"Una comprobación no encuentra el módulo «{name}». O no está declarado en package.json / el "
                     "lockfile de la tarea, o el verificador no lo tiene instalado.",
                     [f"Reintenta con la indicación propuesta para que el agente declare {name} en package.json y el "
                      "lockfile.",
                      "Si ya está declarado, el problema es la instalación del verificador: revisa que el repositorio "
                      "tenga sus dependencias instaladas y reintenta."], "retry_with_note",
                     note=f"The checks fail with a missing module '{name}'. Declare it in package.json and the lockfile "
                          "(do not rely on a globally installed copy) and run every verification command again."), []
    var = ENV_VAR.search(text)
    if var:
        name = var.group(1) or var.group(2)
        project = request.get("project") or "<proyecto>"
        return _diag("environment", f"Falta la variable de entorno {name}",
                     f"Las comprobaciones corren sin tus variables de entorno. «{name}» no llega al verificador, así que "
                     "la prueba no puede conectarse o se niega a correr.",
                     [f"Añade {name} al archivo de variables del verificador (`~/.config/metodologia/verifier-{project}.env`, "
                      "config `verifier.env_file`).",
                      "Si el valor es secreto se redacta en los logs; no lo pongas en el repositorio.",
                      "Después pulsa «Reintentar»."], "retry"), []
    conn = CONNECTION.search(text)
    if conn:
        where = conn["addr"] or "un servicio local"
        return _diag("environment", f"Un servicio no responde ({where})",
                     f"Una comprobación intenta conectarse a {where} y nadie contesta: la base de datos o el servicio "
                     "no está levantado en esta máquina.",
                     [f"Levanta el servicio (por ejemplo `docker compose up -d` en el repositorio) y comprueba {where}.",
                      "Después pulsa «Reintentar»."], "retry"), []
    if re.search(r"usage limit|rate.?limit|quota|429", text, re.I) or code.startswith("quota"):
        return _diag("quota", "El agente se quedó sin cuota",
                     "La cuenta que ejecutaba la tarea llegó a su límite de uso. No es un fallo del código.",
                     ["Mira la cuota con `globalusage`.", "Reintenta cuando se renueve (el sistema elige otra cuenta si "
                      "hay una libre)."], "retry"), []
    if closed or code in ("manual_cancel", "stale_or_cancelled"):
        who = closed or "alguien (o el sistema al reorganizar el run)"
        return _diag("cancelled", "El intento se canceló",
                     f"El último intento no falló: lo cerró {who}. No hay nada que arreglar en el código.",
                     ["Pulsa «Reintentar» si la tarea debe seguir."], "retry"), []
    same = repeats or (len(failures) if len(failures) >= 2 and len(set(failures[-3:])) == 1 and verify else 0)
    if same >= 2:
        return _diag("code", f"Los últimos {same} intentos fallaron exactamente igual",
                     f"Los últimos {same} intentos terminaron con el mismo error: reintentar sin cambiar nada lo "
                     "repetirá. Lee el error y decide si es del código (indicación al agente), del entorno (arréglalo "
                     "tú) o del plan (revisión). El agente ya ve el historial de intentos y este aviso.",
                     ["Si el error apunta al código, reintenta con una indicación que diga qué cambiar.",
                      "Si apunta a una comprobación imposible, corrige el plan y pasa el run a la revisión nueva.",
                      "Pide el diagnóstico del agente si no está claro."], "retry_with_note", confidence="media"), []
    if verify:
        return _diag("code", "La verificación rechazó el trabajo",
                     "Las comprobaciones independientes fallaron. El error de abajo dice cuál; el agente ya lo verá en "
                     "su próximo intento.",
                     ["Si el error tiene sentido como fallo del código, reintenta.",
                      "Si es del entorno o del plan, corrígelo antes de reintentar."], "retry", confidence="media"), []
    return _diag("unknown", request.get("what") or "La tarea se detuvo",
                 "Las reglas no reconocen la causa a partir de la evidencia del run.",
                 list(request.get("you_can") or []) + ["Pide el diagnóstico del agente."],
                 request.get("recommended", "retry"), confidence="baja"), []


def _unsupported(plan, task: str) -> list[tuple[str, str]]:
    """(command, why) for each command verification of the task that M6's parser refuses."""
    import tempfile
    from pathlib import Path

    from bt_scheduler_quality.policy import _parse_command

    try:
        items = [v["value"] for v in plan.task(task).verification if v.get("type") == "command"]
    except Exception:  # noqa: BLE001 - no plan, no task: nothing to point at
        return []
    out = []
    with tempfile.TemporaryDirectory() as root:
        for item in items:
            try:
                _parse_command(item, Path(root), True)
            except Exception as exc:  # noqa: BLE001 - QualityError carries the reason
                why = getattr(exc, "detail", str(exc))
                if "relative executable" not in why or "=" in item.split()[0]:
                    out.append((item, why))
    return out


def _review(request: dict) -> dict:
    evidence = request.get("evidence") or []
    text = "\n".join(evidence)
    criteria = [line for line in evidence if line.startswith("criterio ")]
    issues = {line.split(":", 1)[0] for line in evidence if line[:1].isupper() and ":" in line and "_" in line.split(":", 1)[0]}
    if criteria and all(line.startswith("criterio PASS") for line in criteria) and issues <= {"CHECK_UNMAPPED"} \
            and not any(" → fail" in line or " → unknown" in line for line in evidence):
        return _diag("verifier", "Todo pasó: un check extra no corresponde a ningún criterio",
                     f"Los {len(criteria)} criterios de aceptación pasaron y todos los checks salieron bien. El "
                     "verificador solo se detiene porque un check (normalmente el genérico, como `npm run …:test`) "
                     "tiene un propósito que no coincide literalmente con ningún criterio (CHECK_UNMAPPED). No es un "
                     "fallo de la tarea.",
                     ["Pulsa «Aprobar a mano» con la razón «todos los criterios PASS; solo CHECK_UNMAPPED».",
                      "Para que no vuelva a pasar, en la próxima revisión del plan da a ese check el mismo propósito "
                      "que un criterio, o quítalo."], "review_pass")
    if any(code in text for code in ("SANDBOX_UNAVAILABLE", "RUNNER_BUSY", "CHECK_TIMEOUT")):
        return _diag("verifier", "El verificador no pudo comprobar nada",
                     "El entorno de comprobación falló (sandbox, ocupado o tiempo agotado). La tarea no fue juzgada.",
                     ["Pulsa «Rechazar» con la razón: el sistema reintenta en un entorno sano.",
                      "No apruebes a mano: nada se comprobó."], "review_fail")
    if "Comprobar a mano" in text:
        return _diag("manual", "Hay una comprobación que solo puede hacer una persona",
                     "El plan marcó criterios como manuales (por ejemplo en el teléfono o en producción).",
                     ["Haz la comprobación descrita en la evidencia.",
                      "Si se cumple, «Aprobar a mano» con lo que viste; si no, «Rechazar» diciendo qué falló."],
                     "review_pass", confidence="media")
    return _diag("verifier", "Las comprobaciones no dieron veredicto",
                 "El verificador terminó sin poder decir si la tarea cumple.",
                 ["Si los checks fallaron por el entorno, rechaza para reintentar.",
                  "Aprueba a mano solo si tú comprobaste lo que ellos no pudieron."], "review_fail", confidence="media")


def bundle(request: dict, *, plan=None, verify: str = "", failures: list[str] | None = None, notes: str = "",
           audit: str = "", answered: list[dict] | None = None, rule: dict | None = None, limit: int = 9000) -> str:
    """The evidence an agent reads to diagnose the stop: plain text, bounded."""
    task = None
    if plan is not None:
        try:
            task = plan.task(request["task"])
        except Exception:  # noqa: BLE001 - a review of a task outside this revision
            task = None
    lines = [f"Project: {request.get('project', '')} · requirement: {request.get('req', '')}",
             f"Request: {request['id']} — {request.get('title', '')}", f"Reason code: {request.get('reason', '')}",
             f"What the system says: {request.get('what', '')}"]
    if task is not None:
        meta = getattr(task, "meta", {}) or {}
        lines += [f"Task: {task.id} — {meta.get('title', '')}", f"Objective: {meta.get('objective', '')}",
                  f"Prerequisites: {', '.join(task.after) or 'none'}", "Acceptance criteria:",
                  *[f"- {c}" for c in task.acceptance_criteria],
                  "Verification commands:", *[f"- [{v.get('type', '')}] {v.get('value', '')}" for v in task.verification]]
    lines += ["Options offered: " + ", ".join(o["id"] for o in request.get("options", []))]
    if failures:
        lines += ["Attempt failures (oldest first):", *[f"- {f[:400]}" for f in failures[-6:]]]
    for title, body in (("Last verification failure", verify), ("Owner notes in force", notes),
                        ("Audit notes", audit), ("Error shown on the card", request.get("error", ""))):
        if body:
            lines += [f"{title}:", body[:2500]]
    if answered:
        lines += ["Earlier owner decisions for this task:",
                  *[f"- {a.get('request')} {a.get('option')}: {str(a.get('reason', ''))[:300]}" for a in answered[-4:]]]
    if rule:
        lines += [f"Rule-based guess: {rule['label']} — {rule['headline']}. {rule['origin']}",
                  "Its steps: " + " / ".join(rule["steps"]) + f" (option: {rule['option']})"]
    text = "\n".join(lines)
    return text if len(text) <= limit else text[:limit] + "\n…(clipped)"

