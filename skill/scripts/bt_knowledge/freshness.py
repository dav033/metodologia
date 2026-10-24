"""Freshness policy for external research claims."""
from __future__ import annotations

from datetime import date, datetime


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
                 invalidated: bool = False, invalidated_at: str | None = None,
                 as_of: date | None = None) -> str:
    """Classify a claim using its newest verifiable retrieval date."""
    if disputed:
        return "disputed"
    current = as_of or date.today()
    verified_dates = [date.fromisoformat(value) for value in retrieved_dates
                      if date.fromisoformat(value) <= current]
    if not verified_dates:
        return "unverified"
    newest = max(verified_dates)
    # Evidence dates are local calendar days; compare the UTC invalidation timestamp on the same clock.
    invalidation_date = datetime.fromisoformat(invalidated_at).astimezone().date() if invalidated_at else None
    if (invalidated and (invalidation_date is None or newest <= invalidation_date)) or (
            current - newest).days > FRESHNESS_DAYS[kind]:
        return "stale"
    return "fresh"
