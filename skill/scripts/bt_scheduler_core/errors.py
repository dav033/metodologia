"""Stable error type of the module: a `code` for programs, `issues` for people."""
from __future__ import annotations


class SchedulerError(ValueError):
    """Something cannot be done; `code` is stable (see README §Errors), `issues` are actionable lines."""

    def __init__(self, code: str, issues: list[str] | str):
        self.code = code
        self.issues = [issues] if isinstance(issues, str) else list(issues)
        super().__init__(f"{code}: " + "; ".join(self.issues[:5]) + (" …" if len(self.issues) > 5 else ""))


CODES = (
    "PLAN_UNREADABLE",         # cannot read / decode / parse the plan text
    "PLAN_NOT_APPROVED",       # no approved hash given, or the plan's hash differs from it
    "PLAN_INVALID",            # structurally wrong: ids, references, cycles, types
    "PLAN_SCHEMA_UNSUPPORTED",  # major version this core does not understand
    "PLAN_MISMATCH",           # plan_id / revision differ from the expected or the persisted run
    "STATE_UNREADABLE",        # persisted state cannot be decoded
    "STATE_MISSING",           # operation needs an initialised run (or an existing database)
    "STATE_UNAVAILABLE",       # the store cannot be opened, is locked or failed
    "ILLEGAL_TRANSITION",      # internal guard: a transition the tables do not allow
    "CONFIG_INVALID",          # configuration value out of range
    "UNKNOWN_TASK",            # task id not in the plan
    "UNKNOWN_ATTEMPT",         # attempt id not in the run
    "NOT_ALLOWED",             # operation refused by the current state (e.g. reopen a task that is not blocked)
    "CONTRACT_VIOLATION",      # a message that does not satisfy the versioned contract
    "ROUTING_UNAVAILABLE",     # M2 did not produce the required initial route map
    "ROUTING_INVALID",         # M2 returned an incomplete or malformed initial route map
)
