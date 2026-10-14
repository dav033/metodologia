"""StateRepository: the only persistence contract of the core, plus the in-memory implementation.

One transaction = one atomic change of the run state and its audit rows (all or nothing). Implementations must
serialise writers (one authority per run). The core never calls a port while a transaction is open.
"""
from __future__ import annotations

import json
import threading
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from typing import Any, Protocol

from .model import AuditEntry, RunState


class Transaction:
    """What the engine sees inside a transaction: the state (or None for an empty store) and the audit trail."""

    def __init__(self, state: RunState | None, *, readonly: bool = False):
        self.state = state
        self.readonly = readonly
        self.entries: list[AuditEntry] = []

    def audit(self, kind: str, /, *, at: float, task_id: str = "", attempt_id: str = "", **detail: Any) -> None:
        if self.readonly:
            raise RuntimeError("audit inside a read-only transaction")
        if self.state is None:
            raise RuntimeError("audit before the run state exists")
        self.entries.append(AuditEntry(self.state.next("audit"), at, kind, self.state.plan_id, task_id, attempt_id,
                                       json.loads(json.dumps(detail, default=str))))


class StateRepository(Protocol):
    def transaction(self) -> AbstractContextManager[Transaction]:
        """Exclusive read-modify-write; commits on normal exit, rolls back on any exception."""
    def read_transaction(self) -> AbstractContextManager[Transaction]:
        """Consistent snapshot for looking, never for changing: takes no writer lock and commits nothing.
        Optional: a repository without it is read through `transaction()`."""
    def audit_log(self, since: int = 0) -> list[AuditEntry]:
        """Entries with seq > since, oldest first."""


class InMemoryRepository:
    """Thread-safe store that keeps the state as JSON text, so it behaves like a durable one (and proves
    serialisability). `before_commit` lets tests inject a failure at the commit point."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._doc: str | None = None
        self._audit: list[AuditEntry] = []
        self.before_commit: Callable[[], None] | None = None
        self.commits = 0

    @contextmanager
    def transaction(self) -> Iterator[Transaction]:
        with self._lock:
            tx = Transaction(RunState.from_dict(json.loads(self._doc)) if self._doc is not None else None)
            yield tx
            if self.before_commit:
                self.before_commit()
            if tx.state is not None:
                self._doc = json.dumps(tx.state.to_dict(), sort_keys=True)   # an unchanged document is the same text
            self._audit.extend(tx.entries)
            self.commits += 1

    @contextmanager
    def read_transaction(self) -> Iterator[Transaction]:
        with self._lock:
            yield Transaction(RunState.from_dict(json.loads(self._doc)) if self._doc is not None else None, readonly=True)

    def audit_log(self, since: int = 0) -> list[AuditEntry]:
        with self._lock:
            return [e for e in self._audit if e.seq > since]
