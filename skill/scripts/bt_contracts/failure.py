"""Failure taxonomy and recovery decisions (REQ-030 M5).

One closed set of classes replaces the ten classification sites of the legacy runtime. A class is assigned only from
evidence (exit records, cgroup events, verifier reason codes, decisive output lines); the evidence travels with the
report so a reviewer, the owner or a later diagnosis can check why a failure was routed the way it was.
"""
from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class _Closed(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class FailureClass(StrEnum):
    TRANSIENT = "transient_infrastructure"   # provider stream dropped, connection reset, sandbox busy
    ENVIRONMENT = "environment"              # OOM in a sandbox, missing tool, missing declared env var, disk full
    CONTRACT = "contract"                    # producer/consumer shape mismatch, invalid order or plan data
    VERIFICATION = "verification"            # the check itself cannot decide: manual, unmapped, flaky, timeout
    IMPLEMENTATION = "implementation"        # the agent's code fails a real check
    INTEGRATION = "integration"              # the result conflicts with accepted work
    QUOTA = "quota"                          # route has no capacity now
    PERMISSION = "permission"                # authentication, authorization, policy denial: never auto-bypassed
    PRODUCT_DECISION = "product_decision"    # the plan or the owner must decide
    INTERNAL = "internal"                    # a defect of the runtime itself


class Evidence(_Closed):
    kind: str = Field(min_length=1, max_length=40)        # exit_record | cgroup | verify_reason | output_line | ...
    ref: str = Field(default="", max_length=300)          # m6://..., file path, unit name
    excerpt: str = Field(default="", max_length=2000)


class FailureReport(_Closed):
    failure_class: FailureClass
    code: str = Field(min_length=1, max_length=80)        # stable machine code, e.g. NODE_HEAP_OOM, CHECK_FAILED
    summary: str = Field(min_length=1, max_length=500)
    signature: str = Field(min_length=8, max_length=64)   # hash of the normalized decisive evidence
    evidence: tuple[Evidence, ...] = ()
    agent_note: str = Field(default="", max_length=6000)  # what the next attempt is told (decisive lines first)


class RecoveryAction(StrEnum):
    RETRY = "retry"                          # same task, fresh attempt from the last snapshot
    RETRY_OTHER_ROUTE = "retry_other_route"  # same task on another allowed route
    WAIT = "wait"                            # durable wait until not_before, then retry
    REPAIR_ENVIRONMENT = "repair_environment"  # bounded environment repair, then retry without a model change
    REMEDIATE = "remediate"                  # a coordinated repair task with the reproducing probes
    RECONCILE_INTEGRATION = "reconcile_integration"
    ESCALATE = "escalate"                    # the owner decides; the workflow waits durably for the answer
    STOP = "stop"                            # nothing safe left to try; the task is blocked with its evidence


class Budget(_Closed):
    """Anti-loop limits of one task. Every limit is checked before an attempt is started."""
    max_attempts: int = Field(default=4, ge=1, le=50)
    max_same_signature: int = Field(default=2, ge=1, le=20)
    max_elapsed_seconds: int = Field(default=6 * 3600, ge=60)
    max_tokens: int | None = Field(default=8_000_000, ge=1)
    max_route_changes: int = Field(default=2, ge=0, le=10)
    max_environment_repairs: int = Field(default=1, ge=0, le=5)
    max_consecutive_regressions: int = Field(default=2, ge=1, le=10)
    max_waits: int = Field(default=6, ge=0, le=100)


class Spent(_Closed):
    """What one task has consumed so far (derived from its attempt outcomes, never edited by hand)."""
    attempts: int = 0
    elapsed_seconds: float = 0.0
    tokens: int = 0
    route_changes: int = 0
    environment_repairs: int = 0
    waits: int = 0
    signatures: dict[str, int] = Field(default_factory=dict)
    consecutive_regressions: int = 0


class RecoveryDecision(_Closed):
    action: RecoveryAction
    reason: str = Field(min_length=1, max_length=500)
    failure: FailureReport | None = None
    not_before: float | None = None
    note_for_agent: str = Field(default="", max_length=6000)
    spent: Spent = Field(default_factory=Spent)
    limit_hit: str = Field(default="", max_length=80)
