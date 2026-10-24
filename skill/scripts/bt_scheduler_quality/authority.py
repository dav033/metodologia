"""Trusted operator decisions for declared external verification resources."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class VerificationAuthority:
    """Host-owned probes; plan content can request decisions but cannot supply them."""

    resource_available: Callable[[str], bool] | None = None
    authorize_environment: Callable[[str, str | None], bool | str] | None = None
