"""Consecutive probe tracking for the laptop connection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import time


class LaptopStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"


@dataclass(frozen=True)
class LivenessTransition:
    previous: LaptopStatus
    current: LaptopStatus


class LivenessMonitor:
    def __init__(self, failures_before_offline: int = 3):
        if failures_before_offline < 1:
            raise ValueError("failures_before_offline must be positive")
        self.failures_before_offline = failures_before_offline
        self.status = LaptopStatus.ONLINE
        self.consecutive_failures = 0
        self.offline_since: float | None = None

    def record_success(self) -> LivenessTransition | None:
        self.consecutive_failures = 0
        if self.status is LaptopStatus.OFFLINE:
            previous = self.status
            self.status = LaptopStatus.ONLINE
            self.offline_since = None
            return LivenessTransition(previous, self.status)
        return None

    def record_failure(self) -> LivenessTransition | None:
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.failures_before_offline and self.status is LaptopStatus.ONLINE:
            previous = self.status
            self.status = LaptopStatus.OFFLINE
            self.offline_since = time.monotonic()
            return LivenessTransition(previous, self.status)
        return None
