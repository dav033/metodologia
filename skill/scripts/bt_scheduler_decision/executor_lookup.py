"""Read-only resolution of persisted M2 executor references."""
from __future__ import annotations

import sqlite3
from collections.abc import Callable
from pathlib import Path

from .contracts import DecisionRecord, RouteBinding, RouteSummary
from .identity import parse_executor_reference
from .ledger_errors import DecisionLedgerError

ConnectionFactory = Callable[[bool], sqlite3.Connection]
RecordDecoder = Callable[[str], DecisionRecord]


def resolve_executor_binding(connection_factory: ConnectionFactory, decode_record: RecordDecoder,
                             reference: str) -> RouteBinding | None:
    """Resolve the selected route and the plan/task the persisted decision belongs to."""
    parsed = parse_executor_reference(reference)
    if parsed is None:
        return None
    decision_id, route_id = parsed
    try:
        connection = connection_factory(True)
    except sqlite3.Error as exc:
        raise DecisionLedgerError("ledger_unavailable") from exc
    try:
        row = connection.execute("SELECT seq, record_json FROM decision_records WHERE decision_id = ?",
                                 (decision_id,)).fetchone()
        if row is None:
            return None
        record = decode_record(row[1])
        if record.selected is None or record.selected.route_id != route_id:
            return None
        later = connection.execute(
            "SELECT decision_id FROM decision_records WHERE plan_id = ? AND task_id = ? AND seq > ? "
            "ORDER BY seq DESC LIMIT 1", (record.plan_id, record.task_id, row[0]),
        ).fetchone()
    except sqlite3.Error as exc:
        raise DecisionLedgerError("ledger_unavailable") from exc
    finally:
        connection.close()
    return RouteBinding(record.selected, record.decision_id, record.plan_id, record.revision, record.plan_sha256,
                        record.task_id, record.created_at, later[0] if later else None)


def resolve_executor_reference(connection_factory: ConnectionFactory, decode_record: RecordDecoder,
                               reference: str) -> RouteSummary | None:
    """Resolve only the selected route; unknown, malformed, excluded and alternative refs return `None`."""
    parsed = parse_executor_reference(reference)
    if parsed is None:
        return None
    decision_id, route_id = parsed
    try:
        connection = connection_factory(True)
    except sqlite3.Error as exc:
        raise DecisionLedgerError("ledger_unavailable") from exc
    try:
        row = connection.execute("SELECT record_json FROM decision_records WHERE decision_id = ?",
                                 (decision_id,)).fetchone()
    except sqlite3.Error as exc:
        raise DecisionLedgerError("ledger_unavailable") from exc
    finally:
        connection.close()
    if row is None:
        return None
    record = decode_record(row[0])
    if record.selected is None or record.selected.route_id != route_id:
        return None
    return record.selected


def resolve_executor_binding_path(path: str | Path, reference: str) -> RouteBinding | None:
    """Resolve a binding through an existing ledger without creating or changing the database."""
    from .recorder import DecisionLedger

    return DecisionLedger(path, create=False).resolve_executor_binding(reference)


def resolve_executor_reference_path(path: str | Path, reference: str) -> RouteSummary | None:
    """Resolve a route through an existing ledger without creating or changing the database."""
    from .recorder import DecisionLedger

    return DecisionLedger(path, create=False).resolve_executor_reference(reference)
