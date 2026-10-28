"""Read-only M6 verification log for one failed Scheduler attempt."""
from __future__ import annotations

import hashlib
import html
import json
import re
import sqlite3
from pathlib import Path
from typing import Any
from urllib.parse import quote

import bt_planstatus
import bt_plans_api
import bt_run_stores
from bt_pages import layout
from bt_scheduler_monitor_adapter import redact_evidence

_RESULT = re.compile(r"^m6://result/([0-9a-f]{64})$")
_ARTIFACT = re.compile(r"^m6://artifact/([0-9a-f]{64})$")
_MAX_OUTPUT_BYTES = 4096
_MAX_LINES = 200
_MAX_INPUT_BYTES = 64 * 1024


class ReviewError(Exception):
    """A safe, user-facing failure review error."""


def _artifact(conn: sqlite3.Connection, reference: str, pattern: re.Pattern[str]) -> bytes:
    match = pattern.fullmatch(reference) if isinstance(reference, str) else None
    if not match:
        raise ReviewError("La referencia de evidencia no es válida.")
    row = conn.execute("SELECT content FROM artifacts WHERE digest=?", (match.group(1),)).fetchone()
    if not row:
        raise ReviewError("El artefacto ya no está disponible en el store de esta ejecución.")
    content = bytes(row[0])
    if hashlib.sha256(content).hexdigest() != match.group(1):
        raise ReviewError("El hash del artefacto no coincide; se ocultó la salida.")
    return content


def _tail(content: bytes) -> tuple[str, bool]:
    """Return a redacted tail, bounded to 200 lines and 4 KiB."""
    truncated_bytes = len(content) > _MAX_INPUT_BYTES
    bounded = content[-_MAX_INPUT_BYTES:] if truncated_bytes else content
    lines = bounded.splitlines()[-_MAX_LINES:]
    raw = b"\n".join(lines)
    safe = redact_evidence(raw, max_bytes=_MAX_OUTPUT_BYTES)
    if safe.withheld:
        return "La salida se ocultó porque no se pudo decodificar o excede el límite seguro.", True
    text = safe.excerpt or "(sin salida)"
    truncated = truncated_bytes or len(raw) > _MAX_OUTPUT_BYTES or len(bounded.splitlines()) > _MAX_LINES
    if len(raw) > _MAX_OUTPUT_BYTES:
        text = text.encode("utf-8")[-_MAX_OUTPUT_BYTES:].decode("utf-8", "ignore")
    return text, truncated


def _manifest_v1(manifest: dict[str, Any]) -> dict[str, Any]:
    return {key: manifest.get(key) for key in ("request", "checks", "criteria", "issues")}


# One reader per published M6 manifest version (bt_scheduler_quality.evidence.MANIFEST_VERSION is the newest).
# 1.1 only adds fields this page does not show (reason_code, tree digests, argv), so it reads like 1.
_MANIFEST_READERS = {"m6.evidence-manifest/1": _manifest_v1, "m6.evidence-manifest/1.1": _manifest_v1}


def read_manifest(manifest: Any) -> dict[str, Any] | None:
    """The fields this page uses from a known manifest version; None for an unknown or malformed one."""
    reader = _MANIFEST_READERS.get(manifest.get("schema_version")) if isinstance(manifest, dict) else None
    return reader(manifest) if reader else None


def _read_review(root: Path, query: dict[str, str]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    project, req, task_id, attempt_id, reference = (query.get(k, "") for k in ("project", "req", "task", "attempt", "ref"))
    match = _RESULT.fullmatch(reference)
    if not match or not task_id or not attempt_id:
        raise ReviewError("Faltan datos válidos para abrir el log de este intento.")
    rdir = bt_plans_api.req_dir(root, project, req)
    status = bt_planstatus.plan_status(project, rdir)
    if status["run"].get("authority") != "scheduler":
        raise ReviewError("La revisión solo está disponible para ejecuciones del Scheduler.")
    task = next((t for milestone in status["milestones"] for t in milestone["tasks"] if t["id"] == task_id), None)
    if task is None:
        raise ReviewError("La tarea no pertenece a esta ejecución.")
    attempt = next((a for a in task.get("history", []) if a.get("id") == attempt_id), None)
    if attempt is None or attempt.get("state") not in ("rejected", "failed"):
        raise ReviewError("El intento no corresponde a un fallo registrado de esta tarea.")
    stores = bt_run_stores.paths(rdir)
    db_path = stores.get("m6")
    if not db_path or not Path(db_path).is_file():
        raise ReviewError("El store M6 de esta ejecución no está disponible.")
    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(f"{Path(db_path).resolve().as_uri()}?mode=ro", uri=True, timeout=2)
        manifest_bytes = _artifact(conn, reference, _RESULT)
        if len(manifest_bytes) > 256 * 1024:
            raise ReviewError("El manifiesto excede el límite de lectura.")
        manifest = read_manifest(json.loads(manifest_bytes))
        request = manifest.get("request") if manifest else None
        if not isinstance(request, dict) or any((request.get("plan_id") != status["plan"]["plan_id"],
                                                  request.get("task_id") != task_id,
                                                  request.get("attempt_id") != attempt_id,
                                                  request.get("revision") != status["plan"]["revision"])):
            raise ReviewError("El manifiesto no corresponde al requerimiento, tarea e intento seleccionados.")
        checks = manifest.get("checks")
        if not isinstance(checks, list):
            raise ReviewError("El manifiesto no contiene registros de verificación.")
        rows = []
        for item in checks[:20]:
            if not isinstance(item, dict):
                continue
            outputs = {}
            for name in ("stdout", "stderr"):
                ref = item.get(f"{name}_ref")
                try:
                    outputs[name], outputs[f"{name}_truncated"] = _tail(_artifact(conn, ref, _ARTIFACT))
                except ReviewError as exc:
                    outputs[name], outputs[f"{name}_truncated"] = str(exc), True
            rows.append({"id": str(item.get("id") or "Verificación"),
                         "command": str(item.get("command") or "Comando no disponible"),
                         "status": str(item.get("status") or "desconocido"),
                         "exit_code": item.get("exit_code") if isinstance(item.get("exit_code"), int) else None,
                         "issue_code": item.get("issue_code") if isinstance(item.get("issue_code"), str) else None,
                         **outputs})
        criteria = manifest.get("criteria") if isinstance(manifest.get("criteria"), list) else []
        return {"project": project, "req": req, "task": task_id, "attempt": attempt_id,
                "reference": reference, "state": str(attempt.get("state") or "rejected"),
                "criteria": [c for c in criteria[:20] if isinstance(c, dict)],
                "issues": [i for i in (manifest.get("issues") or [])[:20] if isinstance(i, dict)]}, rows
    except (sqlite3.Error, json.JSONDecodeError, UnicodeDecodeError):
        raise ReviewError("No se pudo leer el manifiesto M6 de forma segura.") from None
    finally:
        if conn is not None:
            conn.close()


def review_page(root: Path, query: dict[str, str]) -> str:
    try:
        report, checks = _read_review(root, query)
    except (ReviewError, bt_plans_api.PlanError) as exc:
        body = f'<div class="fl-review"><p role="alert">{html.escape(str(exc))}</p><p><a href="/flow">Volver a Flujo</a></p></div>'
        return layout("Log de fallo", body, [("Flujo", "/flow")])
    criteria = "".join('<li><b>' + html.escape(str(item.get("status", "—"))) + '</b> · ' +
                       html.escape(str(item.get("criterion", "Criterio"))) + '</li>' for item in report["criteria"])
    issues = "".join('<li><b>' + html.escape(str(item.get("code", "Fallo"))) + '</b> · ' +
                     html.escape(str(item.get("detail", ""))) + '</li>' for item in report["issues"])
    check_html = []
    for check in checks:
        exit_code = "—" if check["exit_code"] is None else html.escape(str(check["exit_code"]))
        output_html = "".join('<details open><summary>' + title + (" · cola truncada" if check[f"{key}_truncated"] else "") +
                              '</summary><pre>' + html.escape(check[key]) + '</pre></details>'
                              for key, title in (("stdout", "stdout"), ("stderr", "stderr")))
        check_html.append('<article class="fl-review-check"><h3>' + html.escape(check["id"]) + ' · ' +
                          html.escape(check["status"]) + ' · código ' + exit_code + '</h3><code>' +
                          html.escape(check["command"]) + '</code>' +
                          (('<p>' + html.escape(check["issue_code"]) + '</p>') if check["issue_code"] else "") + output_html + '</article>')
    run_scope = quote(f'run:{report["project"]}/{report["req"]}', safe="")
    body = ('<div class="fl-review"><p class="eyebrow">M6 · evidencia de verificación</p><h1>Log del fallo · ' +
            html.escape(report["task"]) + '</h1><p>Intento <code>' + html.escape(report["attempt"]) +
            '</code> · ' + html.escape(report["state"]) + '</p><p class="fl-review-ref">Evidencia <code>' +
            html.escape(report["reference"]) + '</code></p>' +
            ('<section><h2>Criterios</h2><ul>' + criteria + '</ul></section>' if criteria else "") +
            ('<section><h2>Problemas reportados</h2><ul>' + issues + '</ul></section>' if issues else "") +
            '<section><h2>Comandos y salida</h2>' + ''.join(check_html) + '</section>' +
            '<p><a href="/flow?scope=' + html.escape(run_scope) + '">Volver a la ejecución</a></p></div>')
    return layout(f'Log de fallo · {report["task"]}', body, [("Flujo", "/flow")])
