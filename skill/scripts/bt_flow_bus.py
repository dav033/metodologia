"""The flow bus: every message between the Planner and the Scheduler modules, read from their own stores.

The modules keep durable, ordered records; this bus tails them read-only and normalises each record to a `FlowEvent`.
Unknown records remain visible. Provider-level M3 → M4 details stay quiet and fold into one digest per attempt.
Missing, locked or foreign stores are skipped; the bus never writes or creates a file.

    collect(rdir, project, cursors=None) -> (events, cursors)
    snapshot(rdir, project) -> events
"""
from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path
from typing import Any, Callable

import bt_run_stores
import bt_scheduler_adapter as scheduler_

VERSION = 1
PARTIES = ("planner", "M1", "M2", "M3", "M4", "M5", "M6", "web", "owner")
LIMIT = 2000                                    # rows per store per cycle: bounded work, the cursor catches up
STORES = ("m1", "m2", "m3", "m4", "m4i", "m5", "m6", "heal", "cyc")


# What each module's database holds and what the bus does with it. A table nobody classified here fails
# `test_flow_contract`: a new module table is either a message source (add a tailer) or bookkeeping (say why).
# `diagnostic_cycles` (REQ-029) is created by the methodology adapter beside the M5 store, not by the package: _cycle_events reads it.
COVERED_TABLES = {"m1": {"audit"}, "m2": {"decision_records"}, "m3": {"events"},
                  "m4": {"normalized_events", "incidents"}, "m5": {"decisions"}, "m6": {"requests"}}
IGNORED_TABLES = {
    "state": "M1's state document: the audit table is its message log",
    "verification_retries": "M6 record of an operator retry of a verification; the request row keeps the verdict",
    "check_pass_cache": "M6 cache of passing checks per tree (REQ-030): a performance record, no message",
    "check_stats": "M6 last duration of each check (REQ-030): input to ordering, no message",
    "precious": "integrity probe of the store, no message",
    "learning_snapshots": "M2 learning input, read by M2 itself",
    "batch_decisions": "M2 batch cache; each task decision is already in decision_records",
    "attempts": "M3 attempt ledger: its events table carries the messages",
    "meta": "key/value bookkeeping", "route_refs": "M3 executor-reference index",
    "capacity_padding": "M4 storage reservation", "daily_metric_aggregates": "M4 derived aggregate",
    "daily_metric_aggregates_v2": "M4 derived aggregate", "incident_evidence_refs": "M4 incident evidence index",
    "m1_outbox": "M4 delivery queue to M1: the delivery shows as M1's incident_observed",
    "m4_extension_meta": "schema bookkeeping", "m4_retention_health": "M4 housekeeping",
    "metric_samples": "M4 derived samples of the stream events already emitted",
    "recovery_cases": "M5 normalized case inputs; durable decisions are the flow source",
    "recovery_events": "M5 internal transition history; the final decision is the flow source",
    "recovery_leases": "M5 short-lived worker leases; operational bookkeeping, not a user-visible flow event",
    "application_checkpoints": "M5 idempotency checkpoints for application; the associated decision is the flow source",
    "schema_meta": "schema bookkeeping", "size_fixture": "M4 test fixture table", "source_cursors": "M4 read positions",
    "store_limits": "M4 configuration", "stream_gaps": "M4 loss accounting (surfaces as incidents)",
    "unrelated": "test fixture table", "artifacts": "M6 evidence blobs, referenced by the verdict",
    "outbox": "M6 delivery queue to M1: the delivery shows as M1's dispatch_ack", "reviews": "M6 human-review queue",
}

# ---------------------------------------------------------------- helpers
def _ro(path: Path | None) -> sqlite3.Connection | None:
    if path is None or not Path(path).exists():
        return None
    try:
        conn = sqlite3.connect(f"{Path(path).resolve().as_uri()}?mode=ro", uri=True, timeout=0.2)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error:
        return None


def _rows(path: Path | None, sql: str, args: tuple = ()) -> list[sqlite3.Row]:
    conn = _ro(path)
    if conn is None:
        return []
    try:
        return conn.execute(sql, args).fetchall()
    except sqlite3.Error:
        return []
    finally:
        conn.close()


def _json(text: Any) -> dict[str, Any]:
    try:
        value = json.loads(text) if isinstance(text, (str, bytes)) else text
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


def _epoch(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value) if value > 0 else None
    try:
        return dt.datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _iso(epoch: float) -> str:
    return dt.datetime.fromtimestamp(epoch, dt.UTC).isoformat(timespec="milliseconds")


def event(run: str, store: str, ident: int, at: float, frm: str, to: str, kind: str, summary: str, *,
          task: str = "", attempt: str = "", from_part: str = "", to_part: str = "", data: dict | None = None
          ) -> dict[str, Any]:
    out = {"v": VERSION, "seq": f"{store}:{ident}", "ord": f"{at:018.6f}:{store}:{ident:010d}", "at": _iso(at),
           "at_epoch": at, "run": run, "task": task or None, "attempt": attempt or None, "from": frm, "to": to,
           "kind": kind, "summary": summary, "ref": {"store": store, "id": ident}}
    if from_part:
        out["from_part"] = from_part
    if to_part:
        out["to_part"] = to_part
    if data:
        out["data"] = data
    return out


# ---------------------------------------------------------------- M1 audit
class Ctx:
    """What the M1 rules may need besides the row: a route label for an executor reference."""

    def __init__(self, ledger: Path | None, run: str):
        self.ledger, self.run = ledger, run
        self.terminal_at: dict[str, float] = {}      # attempt id -> when M1 saw it end (to time M5 decisions)
        self._routes: dict[str, str] = {}

    def route(self, reference: str) -> str:
        if reference not in self._routes:
            label = ""
            if self.ledger is not None and reference:
                try:
                    raw = scheduler_.resolve_m2_route(self.ledger, reference)
                except Exception:
                    raw = None
                if raw:
                    label = " · ".join(x for x in (f'{raw.get("provider")}/{raw.get("model")}', raw.get("profile"),
                                                   raw.get("effort")) if x)
            self._routes[reference] = label
        return self._routes[reference]


class _Safe(dict):
    """A detail the record did not carry shows as "?" in the summary instead of failing the whole event."""

    def __missing__(self, key: str) -> str:
        return "?"


def _m1(kind: str, frm: str, to: str, label: str, **extra: Any) -> Callable:
    def rule(ctx: Ctx, row: sqlite3.Row, d: dict) -> tuple:
        text = label.format_map(_Safe({**d, "task": row["task_id"], "attempt": row["attempt_id"]})) if "{" in label else label
        return frm, to, kind, text, extra
    return rule


def _reserved(ctx: Ctx, row: sqlite3.Row, d: dict) -> tuple:
    route = ctx.route(str(d.get("executor") or ""))
    return "M1", "M2", "reserved", f"Reserva {row['task_id']} intento {row['attempt_id']}" + (f" · {route}" if route else ""), {}


def _incident_observed(ctx: Ctx, row: sqlite3.Row, d: dict) -> tuple:
    return "M4", "M1", "incident", f"M4 informa un incidente ({d.get('detector_id') or '?'}) en {row['attempt_id']}", \
        {"severity": d.get("severity"), "detector": d.get("detector_id")}


def _dispatch_intent(ctx: Ctx, row: sqlite3.Row, d: dict) -> tuple:
    if d.get("kind") == "verify":
        return "M1", "M6", "verify_order", f"Pide verificar {row['attempt_id']}", {}
    if d.get("kind") == "cancel":
        return "M1", "M3", "cancel_order", f"Cancela {row['attempt_id']}", {}
    return "M1", "M3", "start_order", f"Inicia {row['task_id']} ({row['attempt_id']})", {}


def _dispatch_delivered(ctx: Ctx, row: sqlite3.Row, d: dict) -> tuple:
    to = "M6" if d.get("kind") == "verify" else "M3"
    return to, "M1", "dispatch_ack", f"{to} acepta la orden {d.get('kind') or ''}".strip(), {}


def _attempt_transition(ctx: Ctx, row: sqlite3.Row, d: dict) -> tuple:
    new = str(d.get("to") or "")
    if new in ("accepted", "rejected", "failed", "cancelled"):
        ctx.terminal_at[row["attempt_id"]] = float(row["at"])
    frm = "M6" if new in ("accepted", "rejected") or d.get("verifier") else \
        "M3" if d.get("source") == "executor" or new in ("running", "verifying", "dispatched") else "M1"
    cause = f" ({d['cause']})" if d.get("cause") else ""
    return frm, "M1", "state_change", f"{row['attempt_id']}: {d.get('from', '?')} → {new}{cause}", {"state": new}


def _task_transition(ctx: Ctx, row: sqlite3.Row, d: dict) -> tuple:
    src = "M5" if d.get("decision") else "M1"
    note = f" · {d['decision']}" if d.get("decision") else ""
    return src, "M1", "task_state", f"{row['task_id']}: {d.get('from', '?')} → {d.get('to', '?')}{note}", {"state": d.get("to")}


_COMPOSITION_STATES = (("candidate", "candidata"), ("published", "publicada"), ("rejected", "rechazada"))
M1_RULES: dict[str, Callable] = {
    "run_created": _m1("run_created", "owner", "M1", "Ejecución creada ({tasks} tareas)"),
    "plan_routes_received": _m1("route_map", "M2", "M1", "M2 entrega el mapa de rutas del plan"),
    "reserved": _reserved,
    "reservation_released": _m1("reservation_released", "M1", "M2", "Se libera la reserva de {attempt}"),
    "reservation_refused": _m1("reservation_refused", "M2", "M1", "M2 no puede reservar {task}"),
    "dispatch_intent": _dispatch_intent,
    "dispatch_delivered": _dispatch_delivered,
    "dispatch_rejected": _m1("dispatch_rejected", "M3", "M1", "La orden de {attempt} fue rechazada"),
    "dispatch_voided": _m1("dispatch_voided", "M1", "M3", "Orden anulada para {attempt}"),
    "attempt_transition": _attempt_transition,
    "task_transition": _task_transition,
    "incident_observed": _incident_observed,
    "recovery_wait": _m1("recovery", "M5", "M1", "M5 pide esperar antes de reintentar {task}"),
    "recovery_refused": _m1("recovery", "M5", "M1", "M1 rechaza la recomendación de M5 para {task}"),
    "lease_expired": _m1("lease_expired", "M1", "M3", "Venció el permiso de {attempt}"),
    "reconciled": _m1("reconciled", "M3", "M1", "Se reconcilia {attempt} con el ejecutor"),
    "reconcile_redeliver": _m1("reconcile_redeliver", "M1", "M3", "Se reenvía la orden de {attempt}"),
    "delivery_abandoned": _m1("delivery_abandoned", "M1", "M3", "Se abandona la entrega de {attempt}"),
    "outbox_pruned": _m1("housekeeping", "M1", "M1", "Se poda la bandeja de salida"),
    "port_invalid": _m1("port_invalid", "M2", "M1", "Un puerto devolvió algo inválido"),
    "port_error": _m1("port_error", "M2", "M1", "Un puerto falló ({port})"),
    "message_rejected": _m1("message_rejected", "M3", "M1", "M1 rechazó un mensaje de {attempt}"),
    "observation_ignored": _m1("observation_ignored", "M4", "M1", "M1 ignora una observación de {attempt}"),
    "attempt_resolved_manually": _m1("manual_resolution", "owner", "M1", "El dueño resuelve {attempt}"),
    "run_paused": _m1("run_paused", "owner", "M1", "Ejecución en pausa"),
    "run_resumed": _m1("run_resumed", "owner", "M1", "Ejecución reanudada"),
    "run_resumed_by_process": _m1("run_resumed", "owner", "M1", "Ejecución reanudada por el proceso"),
    "run_cancel_requested": _m1("run_cancelled", "owner", "M1", "Cancelación solicitada"),
    "amendment_applied": _m1("amendment", "planner", "M1", "Enmienda aplicada a {task}"),
    "rework_requested": _m1("rework", "M6", "M1", "La auditoría devuelve trabajo aceptado: se rehacen {tasks}"),
    "rework_withdrawn": _m1("rework_withdrawn", "owner", "M1", "El dueño retira el rework: {tasks} vuelven a su resultado aceptado"),
    "rework_refused": _m1("rework_refused", "M6", "M1", "No se pudo devolver el trabajo tras la auditoría ({why})"),
    "audit_gate_skipped": _m1("audit_gate", "M6", "M1", "Auditoría de {task} sin ledger: el gate se omite (configurado)"),
    "run_rebased": _m1("run_rebased", "planner", "M1", "La ejecución pasa a la revisión nueva"),
    "revision_barrier": _m1("revision_barrier", "planner", "M1", "Se bloquean nuevas reservas para aplicar la revisión {operation_key}"),
    "revision_applied": _m1("revision_applied", "planner", "M1", "La revisión {to_rev} se aplicó conservando el trabajo no afectado"),
    "subplan_version_published": _m1("subplan_version", "M6", "M1", "{subplan_id} publica la versión {version}"),
    **{f"composition_{s}": _m1("composition", "M6", "M1", f"Composición {{composition_id}}: {es}") for s, es in _COMPOSITION_STATES},
    "demonstrated_frontier_applied": _m1("recovery_frontier", "M5", "M1", "M1 aplica la frontera explícita de M5"),
    "needs_review_held": _m1("needs_review", "M6", "M1", "M1 conserva la revisión M6 de {attempt}"),
    "needs_review_waiting": _m1("needs_review_wait", "M5", "M1", "M5 mantiene en espera {attempt}"),
    "needs_review_resumed": _m1("needs_review_resume", "M5", "M1", "M5 reanuda la verificación de {attempt}"),
    "needs_review_blocked": _m1("needs_review_block", "M5", "M1", "M5 bloquea la revisión no resuelta de {attempt}"),
    "needs_review_retry_exhausted": _m1("needs_review_block", "M6", "M1", "M1 bloquea {attempt}: reintento M6 agotado"),
    "needs_review_resolved": _m1("needs_review_resolved", "M6", "M1", "M6 entrega el veredicto de {attempt}"),
}


def _m1_events(run: str, path: Path | None, after: int, ctx: Ctx) -> list[dict]:
    return audit_events(run, _rows(path, "SELECT seq, at, kind, task_id, attempt_id, detail FROM audit WHERE seq > ? "
                                         "ORDER BY seq LIMIT ?", (after, LIMIT)), ctx)


def audit_events(run: str, rows: list, ctx: Ctx) -> list[dict]:
    """FlowEvents of M1 audit rows (sqlite rows or dicts with the same keys): also how a simulated run is mapped."""
    out = []
    for row in rows:
        d = _json(row["detail"])
        rule = M1_RULES.get(row["kind"])
        if rule is None:
            frm, to, kind, text, extra = "M1", "M1", "unknown", f"Registro de M1 sin regla: {row['kind']}", {}
        else:
            try:
                frm, to, kind, text, extra = rule(ctx, row, d)
            except Exception:
                frm, to, kind, text, extra = "M1", "M1", "unknown", f"Registro de M1 ilegible: {row['kind']}", {}
        out.append(event(run, "m1", row["seq"], float(row["at"]), frm, to, kind, text, task=row["task_id"],
                         attempt=row["attempt_id"], data={"audit": row["kind"], **extra}))
    return out


# ---------------------------------------------------------------- the other modules
def _m2_events(run: str, path: Path | None, after: int) -> list[dict]:
    out = []
    for row in _rows(path, "SELECT seq, task_id, record_json FROM decision_records WHERE seq > ? ORDER BY seq LIMIT ?",
                     (after, LIMIT)):
        d = _json(row["record_json"])
        selected = d.get("selected")
        selected = selected if isinstance(selected, dict) else {}
        route = f'{selected.get("provider", "?")}/{selected.get("model", "?")}' if selected else "sin ruta"
        label = " · ".join(x for x in (route, selected.get("profile"), selected.get("effort")) if x)
        at = _epoch(d.get("created_at")) or 0.0
        out.append(event(run, "m2", row["seq"], at, "M2", "M1", "assignment", f"Asigna {row['task_id']} → {label}",
                         task=row["task_id"], data={"status": d.get("status"), "factors": d.get("factor_codes")}))
    return out


def _m3_events(run: str, path: Path | None, after: int) -> list[dict]:
    out = []
    for row in _rows(path, "SELECT seq, attempt_id, kind, body, created FROM events WHERE seq > ? ORDER BY seq LIMIT ?",
                     (after, LIMIT)):
        task = _json(row["body"]).get("task_id") or ""
        kind = {"execution_started": "execution_started", "execution_finished": "execution_finished"}.get(
            row["kind"], "executor_event")
        e = event(run, "m3", row["seq"], float(row["created"]), "M3", "M1", kind,
                  f"M3: {row['kind']} de {row['attempt_id']}", task=task, attempt=row["attempt_id"],
                  from_part="M3.shim", data={"executor_event": row["kind"]})
        e["seq"] = f"m3:{Path(path).parent.name}:{row['seq']}"     # each plan revision has its own ledger from seq 1
        out.append(e)
    return out


def _m4_events(run: str, path: Path | None, after: int) -> list[dict]:
    out = []
    for row in _rows(path, "SELECT rowid AS id, body FROM normalized_events WHERE rowid > ? ORDER BY rowid LIMIT ?",
                     (after, LIMIT)):
        d = _json(row["body"])
        payload = d.get("payload") if isinstance(d.get("payload"), dict) else {}
        at = _epoch(d.get("received_at")) or _epoch(d.get("source_occurred_at")) or 0.0
        tokens = None
        if d.get("event_type") == "usage_reported" and isinstance(payload.get("value"), (int, float)):
            tokens = {"metric": payload.get("metric_name"), "value": payload["value"]}
        text = (f'{payload.get("metric_name")}: {payload.get("value")}' if tokens else str(d.get("event_type")))
        cause = {"cause": payload.get("cause")} if d.get("event_type") == "stream_gap" and payload.get("cause") else {}
        out.append(event(run, "m4", row["id"], at, "M3", "M4", "stream", f"Flujo del proveedor · {text}",
                         task=d.get("task_id") or "", attempt=d.get("attempt_id") or "", to_part="M4.stream",
                         data={"event_type": d.get("event_type"), "provider": d.get("provider"),
                               "model": d.get("model"), **cause, **({"tokens": tokens} if tokens else {})}))
    return out


def _m4_incidents(run: str, path: Path | None, after: int) -> list[dict]:
    out = []
    for row in _rows(path, "SELECT rowid AS id, body FROM incidents WHERE rowid > ? ORDER BY rowid LIMIT ?",
                     (after, LIMIT)):
        d = _json(row["body"])
        at = _epoch(d.get("first_seen_at")) or 0.0
        out.append(event(run, "m4i", row["id"], at, "M4", "M4", "incident_detected",
                         f'M4 detecta {d.get("type") or d.get("detector_id")} ({d.get("severity")})',
                         task=d.get("task_id") or "", attempt=d.get("attempt_id") or "", from_part="M4.detectors",
                         to_part="M4.outbox", data={"severity": d.get("severity"), "detector": d.get("detector_id")}))
    return out


def _heal_events(run: str, rdir: Path, after: int) -> list[dict]:
    """Every intervention on the run (REQ-030: `RUN.interventions.jsonl`), automatic ones from the scheduler's own recovery and
    manual ones from the owner, as feed events. The id is the line number, so the cursor resumes where it stopped."""
    import bt_interventions

    out = []
    rows = list(bt_interventions.read(rdir))           # a damaged line is skipped, so ids count the readable rows
    for number, row in enumerate(rows, 1):
        if number <= after:
            continue
        auto = row.get("source") == "auto"
        at = float(row.get("at") or 0.0)
        result = {"fixed": "resuelto", "failed": "no resuelto", "pending": "pendiente"}.get(row.get("result"), "")
        who = "recuperación automática" if auto else "el dueño"
        text = f'{who}: {row.get("class")} · {str(row.get("repair") or "")[:120]}{" · " + result if result else ""}'
        out.append(event(run, "heal", number, at, "M5" if auto else "owner", "M1", "recovery_intervention", text,
                         task=row.get("task") or "", from_part="M5.recovery" if auto else "",
                         data={"class": row.get("class"), "source": row.get("source"), "result": row.get("result"),
                               "minutes_lost": row.get("minutes_lost"), "case": row.get("case")}))
    return out


CYCLE_TEXT = {"diagnosing": "diagnostica", "applying": "prepara correcciones", "executing": "ejecuta correcciones",
              "auditing": "reaudita", "succeeded": "resuelto", "blocked": "bloqueado", "escalated": "necesita al dueño"}


def _cycle_events(run: str, path: Path | None, after: int) -> list[dict]:
    """The durable diagnostic-recovery cycles (REQ-029 R7). The cursor is the update time in milliseconds, so a cycle that
    moves to another state is reported again."""
    out = []
    for row in _rows(path, "SELECT lineage_id, cycle_token, state, payload_json, updated_at, "
                     "CAST(updated_at * 1000 AS INTEGER) AS ms FROM diagnostic_cycles "
                     "WHERE CAST(updated_at * 1000 AS INTEGER) > ? ORDER BY updated_at LIMIT ?", (after, LIMIT)):
        why = _json(row["payload_json"]).get("blocker") or ""
        if isinstance(why, dict):
            why = why.get("code") or ""
        out.append(event(run, "cyc", row["ms"], float(row["updated_at"] or 0.0), "M5", "M1", "recovery_cycle",
                         f'Recuperación diagnóstica: {CYCLE_TEXT.get(row["state"], row["state"])}{" · " + str(why)[:120] if why else ""}',
                         from_part="M5.recovery", data={"state": row["state"], "lineage": str(row["lineage_id"])[:16],
                                                        "cycle": str(row["cycle_token"])[:16], "blocker": why or None}))
    return out


def _m5_events(run: str, path: Path | None, after: int, ctx: Ctx) -> list[dict]:
    out = []
    for row in _rows(path, "SELECT seq, task_id, attempt_id, cause, action FROM decisions WHERE seq > ? ORDER BY seq "
                           "LIMIT ?", (after, LIMIT)):
        at = ctx.terminal_at.get(row["attempt_id"], 0.0) + 0.001      # M5 stores no clock: it answers M1's failure
        out.append(event(run, "m5", row["seq"], at, "M5", "M1", "recommendation",
                         f'M5 recomienda {row["action"]} para {row["task_id"]} ({row["cause"]})',
                         task=row["task_id"], attempt=row["attempt_id"], data={"action": row["action"]}))
    return out


def _m6_events(run: str, path: Path | None, after: int) -> list[dict]:
    out = []
    for row in _rows(path, "SELECT rowid AS id, request_json, result_json, state, updated_at FROM requests "
                           "WHERE rowid > ? ORDER BY rowid LIMIT ?", (after, LIMIT)):
        if row["state"] in ("queued", "running"):   # rows are updated in place: stop here so the cursor never passes
            break                                   # a request whose verdict has not been written yet
        req, res = _json(row["request_json"]), _json(row["result_json"])
        status = res.get("status") or row["state"]
        out.append(event(run, "m6", row["id"], _epoch(row["updated_at"]) or 0.0, "M6", "M1", "verdict",
                         f'M6: veredicto {status} para {req.get("attempt_id")}', task=req.get("task_id") or "",
                         attempt=req.get("attempt_id") or "", from_part="M6.runner", data={"status": status}))
    return out


# ---------------------------------------------------------------- public API
def _terminal_times(path: Path | None, attempts: set[str]) -> dict[str, float]:
    """attempt id -> when M1 saw it end, for just the attempts M5 is answering (not bounded by the per-cycle window)."""
    out: dict[str, float] = {}
    if not attempts:
        return out
    marks = ",".join("?" * len(attempts))
    for row in _rows(path, f"SELECT attempt_id, at, detail FROM audit WHERE kind = 'attempt_transition' "
                           f"AND attempt_id IN ({marks}) ORDER BY seq", tuple(sorted(attempts))):
        if _json(row["detail"]).get("to") in ("accepted", "rejected", "failed", "cancelled"):
            out[row["attempt_id"]] = float(row["at"])
    return out


def _ledger_of(rdir: Path) -> Path | None:
    return bt_run_stores.paths(rdir).get("m2")


def _m3_ledger(rdir: Path, project: str) -> Path | None:
    """The M3 ledger of the run's current executor directory: `.state/executor/<project>-<REQ>-r<rev>-*/ledger.db`."""
    paths = bt_run_stores.paths(rdir)
    state = paths["m1"].parent.parent
    req = rdir.name.split("-")[0] + "-" + rdir.name.split("-")[1] if rdir.name.startswith("REQ-") else rdir.name
    found = sorted((state / "executor").glob(f"{project}-{req}-*/ledger.db"), key=lambda p: p.stat().st_mtime)
    return found[-1] if found else None


def is_quiet(e: dict[str, Any]) -> bool:
    """Provider-level detail: the raw stream (thousands per attempt) and incidents M4 itself rates as info only."""
    if e["kind"] == "stream":
        return True
    return e["kind"] in ("incident", "incident_detected") and (e.get("data") or {}).get("severity") == "info"


def sources(rdir: Path, project: str) -> dict[str, tuple[str, int]]:
    """Which file each cursor points into (path, inode): a new revision's M3 ledger or a recreated store starts its
    sequence again, so a reader that kept the old cursor must rewind that one."""
    paths = bt_run_stores.paths(Path(rdir))
    files = {name: paths.get(name) for name in ("m1", "m2", "m4", "m5", "m6")}
    files["m3"] = _m3_ledger(Path(rdir), project)
    out = {}
    for name, path in files.items():
        try:
            out[name] = (str(path), Path(path).stat().st_ino) if path else ("", 0)
        except OSError:
            out[name] = (str(path), 0)
    out["m4i"] = out["m4"]
    out["cyc"] = out["m5"]
    interventions = Path(rdir) / "RUN.interventions.jsonl"
    try:
        out["heal"] = (str(interventions), interventions.stat().st_ino)
    except OSError:
        out["heal"] = (str(interventions), 0)
    return out


def collect(rdir: Path, project: str, cursors: dict[str, int] | None = None) -> tuple[list[dict], dict[str, int]]:
    """New events of one run after `cursors`, causally ordered, and the advanced cursors."""
    rdir = Path(rdir)
    cur = {name: int((cursors or {}).get(name, 0)) for name in STORES}
    paths = bt_run_stores.paths(rdir)
    run = f"{project}/{rdir.name.split('-')[0]}-{rdir.name.split('-')[1]}" if rdir.name.startswith("REQ-") else f"{project}/{rdir.name}"
    ctx = Ctx(paths.get("m2"), run)
    # M5 is timed from M1's terminal transitions, so M1 is always replayed from the start into the context
    m5_pending = {r["attempt_id"] for r in _rows(paths.get("m5"), "SELECT attempt_id FROM decisions WHERE seq > ? "
                                                  "LIMIT ?", (cur["m5"], LIMIT))}
    if m5_pending:                       # M5 stores no clock: time it from M1's terminal transitions of its attempts
        ctx.terminal_at.update(_terminal_times(paths["m1"], m5_pending))
    seen_m1 = _m1_events(run, paths["m1"], cur["m1"], ctx) if paths["m1"].exists() else []
    events = {
        "m1": [e for e in seen_m1 if e["ref"]["id"] > cur["m1"]],
        "m2": _m2_events(run, paths.get("m2"), cur["m2"]),
        "m3": _m3_events(run, _m3_ledger(rdir, project), cur["m3"]),
        "m4": _m4_events(run, paths.get("m4"), cur["m4"]),
        "m4i": _m4_incidents(run, paths.get("m4"), cur["m4i"]),
        "m5": _m5_events(run, paths.get("m5"), cur["m5"], ctx),
        "m6": _m6_events(run, paths.get("m6"), cur["m6"]),
        "heal": _heal_events(run, rdir, cur["heal"]),
        "cyc": _cycle_events(run, paths.get("m5"), cur["cyc"]),
    }
    merged = []
    for name, items in events.items():
        if items:
            cur[name] = max(cur[name], max(e["ref"]["id"] for e in items))
        merged.extend(items)
    for e in merged:
        if is_quiet(e):
            e["quiet"] = True
    merged.sort(key=lambda e: e["ord"])
    return merged, cur


def simulated(run: str, audit: list[dict]) -> list[dict]:
    """Events of a simulated run (`bt_scheduler_adapter.simulate_audit` rows), in causal order."""
    events = audit_events(run, audit, Ctx(None, run))
    events.sort(key=lambda e: e["ord"])
    return events


def snapshot(rdir: Path, project: str) -> list[dict]:
    return collect(rdir, project, None)[0]
