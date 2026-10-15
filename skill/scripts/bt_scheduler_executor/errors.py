"""The module's single error type with stable codes."""
from __future__ import annotations

CODES = (
    "ORDER_INVALID",         # the order does not satisfy the contract (types, empty ids, bad numbers)
    "FOREIGN_RUN",           # an order of another plan/revision reached this executor's root
    "ROUTE_UNRESOLVABLE",    # the route reference is unknown, stale or malformed: never replaced by a default
    "ROUTE_INVALID",         # resolved, but provider/model/profile/effort are not launchable together
    "POLICY_DENIED",         # profile/project policy refused the launch
    "REPOSITORY_UNKNOWN",    # the order's repository is not known to the workspace manager
    "BASE_UNRESOLVED",       # the base ref does not name a commit
    "QUEUE_FULL",            # more orders than the bounded queue holds
    "KEY_CONFLICT",          # an attempt id or idempotency key reused with different content
    "TOKEN_MISMATCH",        # a fenced operation carried another token
    "UNKNOWN_ATTEMPT",
    "WORKSPACE_ERROR",       # worktree allocation or snapshot failed
    "ARTIFACT_ERROR",        # the artefact directory cannot be written
    "START_FAILED",          # the provider process could not be started
    "LEDGER_ERROR",          # the durable store is unusable
    "CONFIG_INVALID",
    "PLATFORM_UNSUPPORTED",
    "ROOT_BUSY",             # another live executor already serves this root (one supervisor per root)
    "PORT_ERROR",            # a port raised something that is not an ExecutorError
)


class ExecutorError(Exception):
    def __init__(self, code: str, detail: object = ""):
        if code not in CODES:
            raise ValueError(f"unknown error code {code!r}")
        self.code = code
        self.detail = detail if isinstance(detail, str) else "; ".join(map(str, detail))
        super().__init__(f"{code}: {self.detail}" if self.detail else code)
