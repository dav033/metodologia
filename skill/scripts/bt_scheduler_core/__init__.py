"""bt_scheduler_core: the deterministic core (M1) of the Scheduler.

Loads an approved PLAN.json, resolves its task DAG, runs the task/attempt state machine on a transactional store,
reserves capacity and resources atomically, dispatches through ports and reconciles after restarts. It contains no AI:
nothing that calls, configures or names a model or a provider, and no semantic reasoning. Standard library only; imports nothing outside this
package (enforced by tests/test_boundaries.py). Public API below; see README.md.
"""
from .config import Config
from .contracts import (
                        CONTRACT_VERSION,
                        Ack,
                        Assignment,
                        AssignmentPort,
                        AssignmentRequest,
                        CancelOrder,
                        Event,
                        EventPort,
                        ExecutionPort,
                        ExecutionStatus,
                        PortNotReady,
                        FailureContext,
                        IngestResult,
                        PlanRoutingPort,
                        PlanRoutingRequest,
                        PlannedRoute,
                        ROUTING_CONTRACT_VERSION,
                        RecoveryPort,
                        RecoveryProposal,
                        StartOrder,
                        TaskView,
                        Verdict,
                        VerificationPort,
                        VerifyOrder,
)
from .errors import CODES, SchedulerError
from .model import AuditEntry, RunState
from .plan import Plan, TaskSpec, load_plan, load_plan_file
from .repository import InMemoryRepository, StateRepository, Transaction
from .reservation import ClaimResult
from .scheduler import Ports, SchedulerCore, StepReport
from .rebase import RebaseReport, content_fingerprint, fingerprint, plan_rebase, rebase_run
from .simulators import FakeExecutor, FakeVerifier, FifoAssignment, ScriptedRecovery
from .sqlite_repository import SqliteRepository
from .states import AttemptState, EventKind, RunStatus, TaskState
from .views import Snapshot

__all__ = [
    "RebaseReport", "content_fingerprint", "fingerprint", "plan_rebase", "rebase_run",
    "CODES", "CONTRACT_VERSION", "Ack", "Assignment", "AssignmentPort", "AssignmentRequest", "AttemptState",
    "AuditEntry", "CancelOrder", "ClaimResult", "Config", "Event", "EventKind", "EventPort", "ExecutionPort",
    "ExecutionStatus", "PortNotReady", "FailureContext", "FakeExecutor", "FakeVerifier", "FifoAssignment", "InMemoryRepository",
    "IngestResult", "Plan", "PlanRoutingPort", "PlanRoutingRequest", "PlannedRoute", "Ports", "RecoveryPort",
    "RecoveryProposal", "ROUTING_CONTRACT_VERSION", "RunState", "RunStatus", "SchedulerCore",
    "SchedulerError", "ScriptedRecovery", "Snapshot", "SqliteRepository", "StartOrder", "StateRepository",
    "StepReport", "TaskSpec", "TaskState", "TaskView", "Transaction", "Verdict", "VerificationPort", "VerifyOrder",
    "load_plan", "load_plan_file"]
