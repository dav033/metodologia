"""Explicit operating limits. Nothing here is inferred from a plan: an estimate is never a timeout."""
from __future__ import annotations

import math
from dataclasses import dataclass

from .errors import ExecutorError

MIB = 1024 * 1024


@dataclass(frozen=True)
class Config:
    max_running: int = 2              # attempts preparing or running at once (M1 owns global capacity; this is a safety ceiling)
    max_queued: int = 64              # accepted but not yet started; beyond it `start` answers QUEUE_FULL
    timeout_seconds: float = 1800.0   # default wall-clock limit of one agent process (an order may carry its own)
    max_timeout_seconds: float = 86400.0
    grace_seconds: float = 10.0       # SIGTERM -> SIGKILL
    heartbeat_seconds: float = 30.0   # liveness hint rate per running attempt; never proof of anything
    poll_seconds: float = 0.5
    output_head_bytes: int = 8 * MIB  # kept from the start of the output
    output_tail_bytes: int = 256 * 1024   # kept from the end of the output (quota/errors live there)
    classify_head_bytes: int = 64 * 1024  # the part of the head given to the classifier when output was dropped
    patch_max_bytes: int = 16 * MIB   # a larger patch is not written (the snapshot ref still holds the work)
    log_tail_bytes: int = 64 * 1024   # tail copied into the handoff
    max_event_backlog: int = 10_000   # undelivered terminal events kept before `start` refuses new work
    deliver_batch: int = 100
    spawn_wait_seconds: float = 10.0  # how long `start` of a shim waits for its identity record
    handoff_tries: int = 3            # attempts to capture the handoff before stating that it failed
    handoff_retry_seconds: float = 0.5
    settle_retry_seconds: float = 5.0  # a settle that failed is retried this slowly
    spare_interactive: bool = True    # the worktree sweep leaves processes with a controlling terminal that are not the agent's live descendants

    def validate(self) -> Config:
        positive = ("max_running", "max_queued", "timeout_seconds", "max_timeout_seconds", "grace_seconds",
                    "heartbeat_seconds", "poll_seconds", "output_head_bytes", "output_tail_bytes",
                    "classify_head_bytes", "patch_max_bytes", "log_tail_bytes", "max_event_backlog", "deliver_batch",
                    "spawn_wait_seconds", "settle_retry_seconds", "handoff_tries", "handoff_retry_seconds")
        bad = [n for n in positive if not isinstance(getattr(self, n), (int, float)) or isinstance(getattr(self, n), bool)
               or not math.isfinite(getattr(self, n)) or getattr(self, n) <= 0]
        if bad:
            raise ExecutorError("CONFIG_INVALID", f"must be positive numbers: {', '.join(bad)}")
        if self.timeout_seconds > self.max_timeout_seconds:
            raise ExecutorError("CONFIG_INVALID", "timeout_seconds exceeds max_timeout_seconds")
        return self
