"""The module's own value types: everything that crosses its boundary is a small frozen dataclass of JSON values.

M1's `StartOrder`/`Ack`/`ExecutionStatus`/`Event` classes are owned by the core; the adapter translates, so this package
imports nothing of it and keeps working whatever version of the core contract it is plugged into.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .errors import ExecutorError

# --- attempt states (ledger) ---------------------------------------------------------------------------------------
QUEUED, PREPARING, RUNNING, SETTLING = "queued", "preparing", "running", "settling"
FINISHED, FAILED, CANCELLED, REJECTED = "finished", "failed", "cancelled", "rejected"
LIVE = (QUEUED, PREPARING, RUNNING, SETTLING)
TERMINAL = (FINISHED, FAILED, CANCELLED, REJECTED)
STATES = LIVE + TERMINAL
TRANSITIONS: dict[str, frozenset[str]] = {
    QUEUED: frozenset({PREPARING, SETTLING}),
    PREPARING: frozenset({RUNNING, SETTLING}),
    RUNNING: frozenset({SETTLING}),
    SETTLING: frozenset({FINISHED, FAILED, CANCELLED}),
    FINISHED: frozenset(), FAILED: frozenset(), CANCELLED: frozenset(), REJECTED: frozenset(),
}

# --- cause classes (facts, never decisions) ------------------------------------------------------------------------
CLEAN = "clean"
QUOTA, CONNECTION, AGENT_ERROR, TIMEOUT = "quota_exhausted", "connection_lost", "agent_error", "timeout"
KILLED, INCOMPLETE, START_FAILED, LOST = "killed", "incomplete_output", "start_failed", "lost"
ARTIFACT, CANCEL_CAUSE = "artifact_error", "cancelled"
CAUSES = (CLEAN, QUOTA, CONNECTION, AGENT_ERROR, TIMEOUT, KILLED, INCOMPLETE, START_FAILED, LOST, ARTIFACT, CANCEL_CAUSE)

# --- technical event kinds (names match the core's; a separate vocabulary on purpose) ----------------------------
EV_STARTED, EV_FINISHED, EV_FAILED = "execution_started", "execution_finished", "execution_failed"
EV_CANCELLED, EV_HEARTBEAT = "execution_cancelled", "heartbeat"
EVENT_KINDS = (EV_STARTED, EV_FINISHED, EV_FAILED, EV_CANCELLED, EV_HEARTBEAT)

RECEIPT_STATUSES = ("accepted", "duplicate", "rejected")
STATUS_STATES = ("queued", "preparing", "running", "settling", "finished", "failed", "cancelled", "not_found")

_TEXT = re.compile(r"^[^\x00]{1,300}$")
EFFORTS = frozenset({"low", "medium", "high", "xhigh", "max", "minimal", "none"})


def _text(value: object, name: str, *, empty: bool = False) -> str:
    if not isinstance(value, str) or (not empty and not value.strip()) or not _TEXT.match(value or "x"):
        raise ExecutorError("ORDER_INVALID", f"{name} must be a non-empty text without NUL (max 300)")
    return value


def _int(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ExecutorError("ORDER_INVALID", f"{name} must be an integer")
    return value


def _optional_epoch(value: object, name: str) -> float | None:
    if value is None:
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ExecutorError("ROUTE_INVALID", f"{name} must be a finite epoch")
    try:
        result = float(value)
    except OverflowError as exc:
        raise ExecutorError("ROUTE_INVALID", f"{name} must be a finite epoch") from exc
    if not math.isfinite(result) or result < 0:
        raise ExecutorError("ROUTE_INVALID", f"{name} must be a finite epoch")
    return result


@dataclass(frozen=True)
class Route:
    """What M2 selected, resolved to launchable parts. The executor never fills a missing part with a default."""
    provider: str
    model: str
    profile: str = ""          # account profile id; "" = the ambient account of that provider
    effort: str = ""
    reference: str = ""        # the opaque reference the order carried (kept for audit)
    account_ref: str = ""      # the account identity the selector evaluated (re-checked at launch when present)
    single_use: bool = False   # a selector's reference may start ONE attempt, ever (replay/slot-bypass guard)
    quota_valid_until: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"provider": self.provider, "model": self.model, "profile": self.profile, "effort": self.effort,
                "reference": self.reference, "account_ref": self.account_ref, "single_use": self.single_use,
                "quota_valid_until": self.quota_valid_until}

    @classmethod
    def from_dict(cls, data: Any) -> Route:
        if not isinstance(data, Mapping):
            raise ExecutorError("ROUTE_INVALID", "route must be an object")
        provider = _text(data.get("provider"), "route.provider")
        model = _text(data.get("model"), "route.model")
        profile = _text(data.get("profile", ""), "route.profile", empty=True)
        effort = _text(data.get("effort", ""), "route.effort", empty=True)
        valid_until = _optional_epoch(data.get("quota_valid_until"), "route quota_valid_until")
        return cls(provider, model, profile, effort, str(data.get("reference", "")),
                   str(data.get("account_ref", ""))[:200], bool(data.get("single_use", False)),
                   valid_until)


@dataclass(frozen=True)
class StartRequest:
    """One authorised order (M1) enriched with approved plan identity and its repository role."""
    idempotency_key: str
    plan_id: str
    revision: int
    task_id: str
    attempt_id: str
    token: int
    executor: str                      # the M2 route reference, opaque here
    repository: str                    # a role the WorkspaceManager can resolve
    project: str = ""
    base_ref: str = "HEAD"
    timeout_seconds: float | None = None
    acceptance_criteria: tuple[str, ...] = ()
    verification: tuple[Mapping[str, Any], ...] = ()
    plan_sha256: str = ""

    def validate(self) -> StartRequest:
        for name in ("idempotency_key", "plan_id", "task_id", "attempt_id", "executor", "repository", "base_ref"):
            _text(getattr(self, name), name)
        _text(self.project, "project", empty=True)
        _int(self.revision, "revision")
        _int(self.token, "token")
        if not isinstance(self.plan_sha256, str) or (self.plan_sha256 and not re.fullmatch(r"[0-9a-f]{64}", self.plan_sha256)):
            raise ExecutorError("ORDER_INVALID", "plan_sha256 must be a lowercase SHA256 digest when present")
        if self.timeout_seconds is not None and (isinstance(self.timeout_seconds, bool)
                                                 or not isinstance(self.timeout_seconds, (int, float))
                                                 or not math.isfinite(self.timeout_seconds)
                                                 or self.timeout_seconds <= 0):
            raise ExecutorError("ORDER_INVALID", "timeout_seconds must be a positive number")
        if not all(isinstance(c, str) for c in self.acceptance_criteria):
            raise ExecutorError("ORDER_INVALID", "acceptance_criteria must be texts")
        if not all(isinstance(v, Mapping) for v in self.verification):
            raise ExecutorError("ORDER_INVALID", "verification must be objects")
        return self

    def to_dict(self) -> dict[str, Any]:
        return {"idempotency_key": self.idempotency_key, "plan_id": self.plan_id, "revision": self.revision,
                "task_id": self.task_id, "attempt_id": self.attempt_id, "token": self.token,
                "executor": self.executor, "repository": self.repository, "project": self.project,
                "base_ref": self.base_ref, "timeout_seconds": self.timeout_seconds,
                "acceptance_criteria": list(self.acceptance_criteria),
                "verification": [dict(v) for v in self.verification], "plan_sha256": self.plan_sha256}

    def matches_record(self, record: object) -> bool:
        """Match a durable order, allowing only the pre-hash schema on an idempotent replay."""
        if not isinstance(record, Mapping):
            return False
        expected = self.to_dict()
        if "plan_sha256" not in record:
            expected.pop("plan_sha256")
        return dict(record) == expected

    @classmethod
    def from_dict(cls, data: Any) -> StartRequest:
        if not isinstance(data, Mapping):
            raise ExecutorError("ORDER_INVALID", "order must be an object")
        try:
            return cls(idempotency_key=data["idempotency_key"], plan_id=data["plan_id"], revision=data["revision"],
                       task_id=data["task_id"], attempt_id=data["attempt_id"], token=data["token"],
                       executor=data["executor"], repository=data["repository"], project=data.get("project", ""),
                       base_ref=data.get("base_ref", "HEAD"), timeout_seconds=data.get("timeout_seconds"),
                       acceptance_criteria=tuple(data.get("acceptance_criteria", ())),
                       verification=tuple(data.get("verification", ())), plan_sha256=data.get("plan_sha256", "")).validate()
        except KeyError as missing:
            raise ExecutorError("ORDER_INVALID", f"missing field {missing.args[0]}") from None
        except TypeError as bad:
            raise ExecutorError("ORDER_INVALID", str(bad)) from None


@dataclass(frozen=True)
class Receipt:
    status: str                        # accepted | duplicate | rejected
    code: str = ""                     # stable error code when rejected
    detail: str = ""
    attempt_id: str = ""

    def __post_init__(self) -> None:
        if self.status not in RECEIPT_STATUSES:
            raise ValueError(f"bad receipt status {self.status!r}")


@dataclass(frozen=True)
class AttemptStatus:
    state: str                         # one of STATUS_STATES
    detail: str = ""
    cause: str = ""
    handoff: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.state not in STATUS_STATES:
            raise ValueError(f"bad status state {self.state!r}")


@dataclass(frozen=True)
class TechnicalEvent:
    """A fact about one attempt. `event_id` is deterministic (`<attempt>:<kind>`), so redelivery is idempotent."""
    event_id: str
    kind: str
    plan_id: str
    revision: int
    task_id: str
    attempt_id: str
    token: int
    occurred_at: str
    payload: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"event_id": self.event_id, "kind": self.kind, "plan_id": self.plan_id, "revision": self.revision,
                "task_id": self.task_id, "attempt_id": self.attempt_id, "token": self.token,
                "occurred_at": self.occurred_at, "payload": dict(self.payload)}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> TechnicalEvent:
        return cls(data["event_id"], data["kind"], data["plan_id"], data["revision"], data["task_id"],
                   data["attempt_id"], data["token"], data["occurred_at"], dict(data.get("payload", {})))


@dataclass(frozen=True)
class Brief:
    """What the agent is asked to do, built from the frozen plan's task (BriefSource port)."""
    title: str
    objective: str = ""
    acceptance_criteria: tuple[str, ...] = ()
    verification: tuple[str, ...] = ()         # human-readable commands/checks
    expected_paths: tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class Workspace:
    """An isolated checkout for one attempt (WorkspaceManager port)."""
    path: str
    branch: str
    base_sha: str
    repo: str                                  # the repository the worktree hangs from
    journal: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "branch": self.branch, "base_sha": self.base_sha, "repo": self.repo,
                "journal": self.journal}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Workspace:
        return cls(data["path"], data["branch"], data["base_sha"], data["repo"], data.get("journal", ""))


@dataclass(frozen=True)
class Launch:
    """How to run one agent (AgentDriver.prepare). `env_set` may hold secrets: never persisted, never logged."""
    argv: tuple[str, ...] = field(repr=False)
    stdin: str | None = field(default=None, repr=False)
    env_remove: tuple[str, ...] = ()
    env_set: tuple[tuple[str, str], ...] = field(default=(), repr=False)

    def redacted(self) -> dict[str, Any]:
        return {"argv0": self.argv[0].rsplit("/", 1)[-1] if self.argv else "", "argc": len(self.argv),
                "stdin_bytes": len((self.stdin or "").encode()), "env_removed": list(self.env_remove),
                "env_set": [k for k, _ in self.env_set]}


@dataclass(frozen=True)
class Classification:
    """The provider-aware reading of a finished process (AgentDriver.classify). Facts the provider reported."""
    status: str                        # completed | failed | limit | partial | timeout | cancelled
    reset_epoch: int | None = None     # None = unknown, never a guess
    terminal_event: bool = False
    text: str = ""
    usage: Mapping[str, Any] | None = None
    cost_usd: float | None = None
