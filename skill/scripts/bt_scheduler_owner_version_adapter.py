"""Owner-facing forwarding for M1's public subplan-version recovery operations."""
from __future__ import annotations


def version_facts(scheduler, *, include_stale: bool = False):
    return scheduler.subplan_version_facts(include_stale=include_stale)


def record_stale_version(scheduler, subplan_id: str, version: int, commit: str, manifest_sha256: str) -> None:
    scheduler.record_stale_subplan_version(subplan_id, version, commit, manifest_sha256)
