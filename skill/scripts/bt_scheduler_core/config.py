"""Explicit operating limits. Nothing here is inferred from the plan (an estimate is never a timeout)."""
from __future__ import annotations

from dataclasses import dataclass

from .errors import SchedulerError


@dataclass(frozen=True)
class Config:
    max_parallel_tasks: int = 1          # global cap on tasks with a live attempt
    max_attempts: int = 1                # attempts per task and budget; 1 = never retry unless the owner raises it
    lease_seconds: float = 300.0         # a lease that lapses triggers reconciliation, never a presumption of death
    reconcile_seconds: float = 60.0      # longest an idle loop sleeps before it re-checks leases and holds
    repository_isolation: str = "shared"  # "shared": same-repo tasks may overlap; "exclusive": one per repository
    unknown_surface: str = "serialize"   # task with no repository/paths/resources: "serialize" (global lock) | "allow"
    exclusive_scopes: tuple[str, ...] = ()  # plan `scope` values that run alone in their repository (the only
    #                                        classification the core ever reads, and only when the operator names it)
    max_recovery_wait: float = 3600.0    # cap on a recovery proposal's `wait`
    max_recovery_waits: int = 3          # a recovery module may ask to wait this many times per task, then the task blocks
    max_deliveries: int = 5              # an order whose delivery keeps failing is abandoned (attempt becomes uncertain)
    require_independent_verifier: bool = True  # the verdict's verifier must differ from the attempt's executor label

    def __post_init__(self):
        problems = []
        if not (isinstance(self.max_parallel_tasks, int) and not isinstance(self.max_parallel_tasks, bool)
                and self.max_parallel_tasks >= 1):
            problems.append("max_parallel_tasks must be an integer >= 1")
        if not (isinstance(self.max_attempts, int) and not isinstance(self.max_attempts, bool) and self.max_attempts >= 1):
            problems.append("max_attempts must be an integer >= 1")
        for name in ("max_recovery_waits", "max_deliveries"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                problems.append(f"{name} must be an integer >= 1")
        for name in ("lease_seconds", "reconcile_seconds", "max_recovery_wait"):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
                problems.append(f"{name} must be a number > 0")
        if self.repository_isolation not in ("shared", "exclusive"):
            problems.append("repository_isolation must be 'shared' or 'exclusive'")
        if not (isinstance(self.exclusive_scopes, tuple) and all(isinstance(s, str) and s for s in self.exclusive_scopes)):
            problems.append("exclusive_scopes must be a tuple of non-empty strings")
        if self.unknown_surface not in ("serialize", "allow"):
            problems.append("unknown_surface must be 'serialize' or 'allow'")
        if problems:
            raise SchedulerError("CONFIG_INVALID", problems)
