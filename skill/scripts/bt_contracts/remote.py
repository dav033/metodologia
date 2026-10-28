"""Canonical remote-control contracts: laptop listener, gateway and phone (REQ-027, REQ-030 M1).

One dialect on the wire: camelCase, the names the phone and the gateway read. The gateway -> laptop ledger body is
the one snake_case contract (`LedgerCommand`); it is internal to the tunnel and documented as such. The stdlib
producers (`bt_remote_*`, the gateway, the Telegram bot) never import this module; tests validate what they emit.

Alias window (documented in remote/docs/contract.md): runs keep `status` next to the canonical `state` for gateways
deployed before this contract, and the gateway accepts a retry `route.route_id` next to the canonical
`route.routeId` from phones built before it. Both are removed in v2.
"""
from __future__ import annotations

from typing import Annotated, Any, Literal

from bt_scheduler_core.states import AttemptState, RunStatus, TaskState
from pydantic import Field, RootModel

from bt_contracts._base import NonEmpty, SnakeWireModel, Timestamp, WireModel

SCHEMA_VERSION = 1
API_PREFIX = "/api/remote/v1"
STREAM_PATH = f"{API_PREFIX}/stream"
STREAM_EVENT = "event"          # SSE `event:` name of one feed event; its `id:` is the gateway's epoch:sequence
STREAM_RESYNC = "resync"        # SSE `event:` name of a full GatewaySnapshot after a gap the backlog cannot fill

IDEMPOTENCY_KEY_MIN, IDEMPOTENCY_KEY_MAX = 16, 120   # phone and Telegram envelopes (the ledger caps at 120 too)
LEDGER_KEY_MIN = 8                                   # the laptop ledger still replays older 8-character keys
KEY_PATTERN = r"^[A-Za-z0-9._:-]+$"
REQ_PATTERN = r"^REQ-[0-9]{3,}$"
LEDGER_TARGET_PATTERN = r"^[^/]+/REQ-[0-9]+$"

M1_RUN_STATUSES = tuple(item.value for item in RunStatus)
M1_TASK_STATES = tuple(item.value for item in TaskState)
M1_ATTEMPT_STATES = tuple(item.value for item in AttemptState)
# The snapshot speaks the plan-status vocabulary (bt_planstatus): M1 `active` is `running`, `recovering` is `rejected`.
SNAPSHOT_TASK_STATES = ("pending", "ready", "running", "verifying", "rejected", "completed", "blocked", "cancelled")
REOPENABLE_TASK_STATES = ("blocked", "rejected")
REOPENABLE_RUN_STATUSES = ("blocked",)
EVENT_TYPES = ("attempt.failed", "attempt.blocked", "run.finished", "round.waiting", "plan.waiting",
               "quota.exhausted", "attempt.stalled", "laptop.offline", "command.updated")
COMMAND_TYPES = ("pause", "resume", "cancel-attempt", "reopen", "retry", "revise", "approve", "launch",
                 "answer-decision", "answer-round", "cancel-plan", "delete-plan", "edit-brief", "note")
CHALLENGED_COMMANDS = ("revise", "approve", "launch", "cancel-plan", "delete-plan", "edit-brief")

AttemptStateName = Literal[M1_ATTEMPT_STATES]  # type: ignore[valid-type]
SnapshotTaskState = Literal[SNAPSHOT_TASK_STATES]  # type: ignore[valid-type]
EventType = Literal[EVENT_TYPES]  # type: ignore[valid-type]
CommandType = Literal[COMMAND_TYPES]  # type: ignore[valid-type]
Project = Annotated[str, Field(min_length=1, max_length=80)]
ReqId = Annotated[str, Field(pattern=REQ_PATTERN)]
TaskId = Annotated[str, Field(min_length=1, max_length=120)]
OpaqueId = Annotated[str, Field(min_length=1, max_length=120)]
IdempotencyKey = Annotated[str, Field(min_length=IDEMPOTENCY_KEY_MIN, max_length=IDEMPOTENCY_KEY_MAX,
                                      pattern=KEY_PATTERN)]
Reason = Annotated[str, Field(max_length=2000)]


# ---- snapshot (GET /snapshot on the laptop; the gateway adds its liveness fields) ----

class Attempt(WireModel):
    """One attempt as the snapshot shows it (`bt_live_api._attempt`, camelCased by `bt_remote_snapshot`)."""
    id: str | None
    number: int | None
    state: AttemptStateName | None
    provider: str | None
    model: str | None
    effort: str | None
    account: str | None
    started_at: Timestamp | None
    ended_at: Timestamp | None
    duration_s: float | None
    live: bool | None
    verdict: str | None
    failure: str | None
    last_activity_at: Timestamp | None


class ActiveTask(WireModel):
    id: str
    title: str | None
    state: SnapshotTaskState
    attempt: Attempt | None


class SnapshotTask(WireModel):
    id: str
    title: str | None
    state: SnapshotTaskState
    active_attempt: Attempt | None
    review_attempt: Attempt | None = Field(description="Latest failed or rejected attempt, for the failure review.")
    history: list[Attempt]


class SnapshotRun(WireModel):
    id: str = Field(description="project/REQ-NNN")
    project: Project
    req: ReqId
    state: str = Field(description="M1 run status (running, paused, completed, blocked, cancelled) for Scheduler "
                                   "runs; legacy runs report their own status, or idle/running when they have none.")
    status: str | None = Field(description="Deprecated alias window of `state` for older gateways; removed in v2.")
    title: str | None
    active: bool | None
    revision: int | None
    updated_at: Timestamp | None
    active_attempt: Attempt | None
    active_task: ActiveTask | None
    last_activity_at: Timestamp | None
    tasks: list[SnapshotTask]


class PlanTask(WireModel):
    id: str | None
    title: str | None
    state: str
    revision: int | None
    updated_at: Timestamp | None
    acceptance_criteria: list[str]


class SnapshotPlan(WireModel):
    id: str
    project: Project
    req: ReqId
    state: str
    revision: int | None
    updated_at: Timestamp | None
    tasks: list[PlanTask]
    acceptance_criteria: list[str]


class RoundOption(WireModel):
    key: str
    label: str


class RoundQuestion(WireModel):
    id: str
    text: str
    type: Literal["choice", "open"]
    options: list[RoundOption] | None = None
    recommended: str | None = None
    why: str | None = None
    suggested: str | None = None


class SnapshotRound(WireModel):
    project: Project
    req: ReqId
    round: int = Field(ge=1)
    id: str | None = None
    title: str | None = None
    intro: str | None = None
    coverage: str | None = None
    status: str
    revision: int | None = None
    questions: list[RoundQuestion]


class DecisionOption(WireModel):
    id: NonEmpty
    label: str
    consequence: str


class DecisionRequest(WireModel):
    """An open Scheduler decision, projected to plain text: no rendered HTML and no form prefill."""
    id: NonEmpty
    project: Project
    req: ReqId
    task: str | None
    attempt: str | None
    source: str | None
    title: str
    what: str
    needs: str | None
    reason: str | None
    evidence: list[str]
    options: list[DecisionOption] = Field(min_length=1)
    recommended: str | None
    unskippable: bool


class RemoteSnapshot(WireModel):
    schema_version: Literal[1]
    generated_at: Timestamp
    cursor: NonEmpty
    runs: list[SnapshotRun]
    plans: list[SnapshotPlan]
    rounds: list[SnapshotRound]
    decision_requests: list[DecisionRequest]


class LaptopLiveness(WireModel):
    online: bool


class GatewaySnapshot(RemoteSnapshot):
    """What the phone reads from the gateway: the cached laptop snapshot flattened with the gateway's liveness."""
    laptop: LaptopLiveness
    online: bool
    cached_at: float | None
    last_event_id: str = Field(description="epoch:sequence of the last fanned-out event, for SSE resume.")


# ---- feed events (GET /events on the laptop, SSE `event` frames from the gateway) ----

class EventSubject(WireModel):
    kind: Literal["run", "attempt", "task", "plan", "round"]
    project: Project
    req: ReqId
    task_id: TaskId | None = None
    attempt_id: OpaqueId | None = None
    round_id: OpaqueId | None = None


class SystemSubject(WireModel):
    kind: Literal["system"]


class RemoteEvent(WireModel):
    schema_version: Literal[1]
    id: Annotated[str, Field(min_length=1, max_length=160)]
    cursor: Annotated[str, Field(min_length=1, max_length=256)]
    type: EventType
    occurred_at: Timestamp = Field(description="RFC 3339 UTC; legacy naive laptop times are read as laptop-local.")
    target: Annotated[EventSubject | SystemSubject, Field(discriminator="kind")]
    data: dict[str, Any]
    dedupe_key: Annotated[str, Field(min_length=1, max_length=256)]


class EventsPage(WireModel):
    events: list[RemoteEvent]
    next_cursor: str
    has_more: bool


# ---- read models served through the gateway's allow-list ----

class QuotaWindow(WireModel):
    window: NonEmpty = Field(description="Window name as the provider reports it, e.g. five_hour, seven_day.")
    used_percent: float
    resets_at: Timestamp | None


class QuotaAccount(WireModel):
    account: str | None = Field(description="The bitácora profile that owns the subscription.")
    provider: str | None
    status: str | None
    observed_at: Timestamp | None
    windows: list[QuotaWindow]


class QuotasResponse(WireModel):
    accounts: list[QuotaAccount] = Field(min_length=1)
    checked_at: Timestamp


class RouteOption(WireModel):
    route_id: NonEmpty
    provider: str
    model: str
    profile: str
    available: bool = Field(description="The single rule bt_route_pins.usable also applies to pinned retries.")
    quota_status: str | None


class RoutesResponse(WireModel):
    routes: list[RouteOption]


class ReviewVerification(WireModel):
    command: str | None
    output: str


class ReviewDiff(WireModel):
    stat: str | None
    files: list[str]


class FailureReview(WireModel):
    attempt_id: NonEmpty
    cause: str
    verification: ReviewVerification
    diff: ReviewDiff
    log_tail: str


class CommandHistoryItem(WireModel):
    id: NonEmpty
    command: CommandType
    target: str
    origin: Literal["web", "telegram"]
    submitted_at: Timestamp
    finished_at: Timestamp | None
    result: str


class CommandHistoryResponse(WireModel):
    commands: list[CommandHistoryItem]
    next_cursor: str


class Problem(WireModel):
    code: NonEmpty
    message: str
    details: dict[str, Any] | None = None


# ---- commands: phone/Telegram -> gateway (POST /commands) ----

class _TargetBase(WireModel):
    project: Project
    req: ReqId


class RunTarget(_TargetBase):
    kind: Literal["run"]
    task_id: TaskId | None = Field(default=None, description="The task a run-level decision is about, if any.")


class TaskTarget(_TargetBase):
    kind: Literal["task"]
    task_id: TaskId


class AttemptTarget(_TargetBase):
    kind: Literal["attempt"]
    attempt_id: OpaqueId
    task_id: TaskId | None = None


class PlanTarget(_TargetBase):
    kind: Literal["plan"]


class RoundTarget(_TargetBase):
    kind: Literal["round"]
    round_id: OpaqueId


class Precondition(WireModel):
    state: Annotated[str, Field(min_length=1, max_length=80)]
    revision: Annotated[int, Field(ge=0)] | None = None
    updated_at: str | None = None


class Confirmation(WireModel):
    challenge_id: Annotated[str, Field(min_length=1, max_length=128)] = Field(
        description="Opaque, one-use id returned by POST /challenges for this exact target.")
    typed_req: ReqId


class RouteSelector(WireModel):
    route_id: NonEmpty
    provider: str | None = None
    model: str | None = None
    account: str | None = None


class _Command(WireModel):
    schema_version: Literal[1]
    idempotency_key: IdempotencyKey
    precondition: Precondition
    reason: Reason | None = None


class PauseCommand(_Command):
    type: Literal["pause"]
    target: RunTarget


class ResumeCommand(_Command):
    type: Literal["resume"]
    target: RunTarget


class CancelAttemptCommand(_Command):
    type: Literal["cancel-attempt"]
    target: AttemptTarget
    reason: Annotated[str, Field(min_length=1, max_length=2000)]


class ReopenCommand(_Command):
    type: Literal["reopen"]
    target: TaskTarget = Field(description="Reopen always names the task; the precondition is that task's state.")


class RetryCommand(_Command):
    type: Literal["retry"]
    target: TaskTarget
    route: RouteSelector | None = None


class _Confirmed(_Command):
    confirmation: Confirmation


class ReviseCommand(_Confirmed):
    type: Literal["revise"]
    target: RunTarget


class ApproveCommand(_Confirmed):
    type: Literal["approve"]
    target: PlanTarget


class LaunchCommand(_Confirmed):
    type: Literal["launch"]
    target: PlanTarget


class CancelPlanCommand(_Confirmed):
    type: Literal["cancel-plan"]
    target: PlanTarget


class DeletePlanCommand(_Confirmed):
    type: Literal["delete-plan"]
    target: PlanTarget


class AnswerDecisionCommand(_Command):
    type: Literal["answer-decision"]
    target: RunTarget
    request_id: NonEmpty
    option: NonEmpty


class AnswerRoundCommand(_Command):
    type: Literal["answer-round"]
    target: RoundTarget
    round: int = Field(ge=1)
    answers: dict[str, Any] = Field(min_length=1, max_length=50)


class EditBriefCommand(_Confirmed):
    type: Literal["edit-brief"]
    target: TaskTarget
    field: Literal["brief", "objective", "criteria", "acceptance_criteria"]
    value: Annotated[str, Field(min_length=1, max_length=20000)] | list[NonEmpty]


class NoteCommand(_Command):
    type: Literal["note"]
    target: RunTarget
    note: Annotated[str, Field(min_length=1, max_length=4000)]


RemoteCommandVariant = Annotated[PauseCommand | ResumeCommand | CancelAttemptCommand | ReopenCommand | RetryCommand | ReviseCommand | ApproveCommand | LaunchCommand | AnswerDecisionCommand | AnswerRoundCommand | CancelPlanCommand | DeletePlanCommand | EditBriefCommand | NoteCommand, Field(discriminator="type")]


class RemoteCommand(RootModel[RemoteCommandVariant]):
    """A command the phone or the Telegram bot posts to the gateway. Every variant is idempotent and guarded."""


class ChallengeRequest(WireModel):
    target: Annotated[str, Field(pattern=LEDGER_TARGET_PATTERN)] | PlanTarget | RunTarget | TaskTarget
    typed_req: ReqId


class CommandResult(WireModel):
    """What the gateway answers the phone; gateway-only refusals carry just a code."""
    status: str | None = None
    code: str | None = None
    message: str | None = None
    replayed: bool | None = None
    stored: bool | None = None
    idempotency_key: str | None = None
    outcome: Any = None


# ---- gateway -> laptop ledger body (snake_case, internal to the tunnel) ----

class LedgerParams(SnakeWireModel):
    task: TaskId | None = None
    attempt: OpaqueId | None = None
    route: Annotated[str, Field(min_length=1, max_length=200)] | None = None
    model: Annotated[str, Field(min_length=1, max_length=200)] | None = None
    account: Annotated[str, Field(min_length=1, max_length=200)] | None = None
    reason: Reason | None = None
    request_id: NonEmpty | None = None
    option: NonEmpty | None = None
    round: Annotated[int, Field(ge=1)] | None = None
    answers: dict[str, Any] | None = None
    field: str | None = None
    value: str | list[str] | None = None
    note: str | None = None


class LedgerPrecondition(SnakeWireModel):
    state: str | None = None
    revision: int | None = None
    updated_at: str | None = Field(default=None, alias="updatedAt")


class LedgerConfirmation(SnakeWireModel):
    challenge_id: NonEmpty
    typed_req: str


class LedgerCommand(SnakeWireModel):
    idempotency_key: Annotated[str, Field(min_length=LEDGER_KEY_MIN, max_length=IDEMPOTENCY_KEY_MAX)]
    command: CommandType
    target: Annotated[str, Field(pattern=LEDGER_TARGET_PATTERN)]
    origin: Literal["web", "telegram"]
    params: LedgerParams
    precondition: LedgerPrecondition
    confirmation: LedgerConfirmation | None = None


# Exported in this order to remote/contract/*.schema.json (file name -> model) and to the phone's TypeScript.
SCHEMA_FILES: dict[str, type] = {
    "snapshot.schema.json": RemoteSnapshot,
    "gateway-snapshot.schema.json": GatewaySnapshot,
    "event.schema.json": RemoteEvent,
    "events-page.schema.json": EventsPage,
    "command.schema.json": RemoteCommand,
    "command-result.schema.json": CommandResult,
    "challenge.schema.json": ChallengeRequest,
    "ledger-command.schema.json": LedgerCommand,
    "quotas.schema.json": QuotasResponse,
    "routes.schema.json": RoutesResponse,
    "review.schema.json": FailureReview,
    "command-history.schema.json": CommandHistoryResponse,
    "error.schema.json": Problem,
}

# Runtime constants the phone imports from the generated module, so its checks follow the contract.
TS_CONSTANTS: dict[str, object] = {
    "SCHEMA_VERSION": SCHEMA_VERSION,
    "STREAM": {"path": STREAM_PATH, "event": STREAM_EVENT, "resync": STREAM_RESYNC},
    "M1_RUN_STATUSES": list(M1_RUN_STATUSES),
    "SNAPSHOT_TASK_STATES": list(SNAPSHOT_TASK_STATES),
    "REOPENABLE_TASK_STATES": list(REOPENABLE_TASK_STATES),
    "REOPENABLE_RUN_STATUSES": list(REOPENABLE_RUN_STATUSES),
    "EVENT_TYPES": list(EVENT_TYPES),
    "COMMAND_TYPES": list(COMMAND_TYPES),
    "CHALLENGED_COMMANDS": list(CHALLENGED_COMMANDS),
    "IDEMPOTENCY_KEY": {"min": IDEMPOTENCY_KEY_MIN, "max": IDEMPOTENCY_KEY_MAX, "pattern": KEY_PATTERN},
}
