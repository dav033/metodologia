"""Freshness policy for external research claims."""
from __future__ import annotations

from datetime import date


FRESHNESS_DAYS = {
    "price": 7,
    "package_version": 30,
    "api_behavior": 90,
    "changelog": 90,
    "security_advisory": 7,
    "license": 365,
    "docs": 180,
    "other": 90,
}


def claim_status(kind: str, retrieved_dates: list[str], *, disputed: bool = False,
                 invalidated: bool = False, as_of: date | None = None) -> str:
    """Classify a claim using its newest verifiable retrieval date."""
    if disputed:
        return "disputed"
    if not retrieved_dates:
        return "unverified"
    newest = max(date.fromisoformat(value) for value in retrieved_dates)
    current = as_of or date.today()
    if invalidated or (current - newest).days > FRESHNESS_DAYS[kind]:
        return "stale"
    return "fresh"
