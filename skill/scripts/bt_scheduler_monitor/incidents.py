"""In-memory deterministic incident lifecycle; persistence is owned by the store."""
from __future__ import annotations

from collections import deque
from dataclasses import replace
from datetime import datetime

from .contracts import Incident

MAX_LIFECYCLE_INCIDENTS = 10_000
MAX_LIFECYCLE_EVIDENCE = 256
MAX_RECENT_EVIDENCE = 256

# A later observation must demonstrate the detector-specific recovery condition.
_RESOLUTION_EVIDENCE = {
    "missed_heartbeat": frozenset(("matching_heartbeat",)),
    "silent_but_alive": frozenset(("new_output", "process_terminal")),
    "repetitive_activity": frozenset(("distinct_activity", "window_expired")),
    "oversized_output": frozenset(("valid_frame_resynchronized",)),
    "provider_stream_silence": frozenset(("valid_parser_event", "source_terminal")),
    "pid_reuse": frozenset(("m3_identity_reconciled",)),
    "stale_post_cancel": frozenset(("late_stream_drained", "m3_stream_closed")),
    "source_disagreement": frozenset(("newer_consistent_snapshot",)),
    "stream_gap": frozenset(("cursor_resumed",)),
    "unexpected_exit": frozenset(("corrected_m3_terminal", "reconciled_m3_terminal")),
    "quota_explicit": frozenset(("new_authorized_execution", "m3_terminal_complete")),
    "quota_probable": frozenset(("later_non_quota_terminal",)),
    "auth_failure": frozenset(("new_authorized_execution",)),
    "connection_error": frozenset(("heartbeat_recovered", "stream_recovered", "m3_terminal")),
    "timeout": frozenset(("m3_terminal",)),
}


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)


class IncidentLifecycle:
    """Deduplicate by stable incident ID and resolve only on matching evidence."""

    def __init__(self) -> None:
        self._incidents: dict[str, Incident] = {}
        self._recent_evidence: dict[str, tuple[deque[str], set[str]]] = {}

    def observe(self, incident: Incident) -> Incident:
        if not isinstance(incident, Incident) or incident.resolution_state != "open":
            raise ValueError("only open Incident observations can be recorded")
        current = self._incidents.get(incident.incident_id)
        if current is None:
            if len(self._incidents) >= MAX_LIFECYCLE_INCIDENTS:
                raise OverflowError("incident lifecycle capacity reached")
            self._incidents[incident.incident_id] = incident
            recent = deque(dict.fromkeys(incident.evidence_refs[-MAX_RECENT_EVIDENCE:]))
            self._recent_evidence[incident.incident_id] = (recent, set(recent))
            return incident
        if current.resolution_state == "resolved":
            raise ValueError("resolved incident IDs cannot be reopened; use a new dedupe window key")
        if (current.run_id, current.task_id, current.attempt_id, current.execution_id,
                current.detector_id, current.type) != (incident.run_id, incident.task_id, incident.attempt_id,
                                                       incident.execution_id, incident.detector_id, incident.type):
            raise ValueError("incident ID collision across identities or detectors")
        if _time(incident.last_seen_at) < _time(current.last_seen_at):
            raise ValueError("incident observations must be chronological")
        recent, seen = self._recent_evidence[incident.incident_id]
        external_refs = set(current.evidence_refs)
        new_refs = tuple(dict.fromkeys(ref for ref in incident.evidence_refs
                                       if ref not in seen and ref not in external_refs))
        if not new_refs:
            return current
        for ref in new_refs:
            if len(recent) >= MAX_RECENT_EVIDENCE:
                seen.remove(recent.popleft())
            recent.append(ref)
            seen.add(ref)
        available = MAX_LIFECYCLE_EVIDENCE - len(current.evidence_refs)
        refs = tuple(dict.fromkeys((*current.evidence_refs, *new_refs[:available])))
        updated = replace(current, last_seen_at=incident.last_seen_at,
                          occurrence_count=min(2**31 - 1,
                                              current.occurrence_count + incident.occurrence_count),
                          evidence_refs=refs)
        self._incidents[incident.incident_id] = updated
        return updated

    def resolve(self, incident_id: str, resolved_at: str, evidence: str) -> Incident:
        current = self._incidents.get(incident_id)
        if current is None:
            raise KeyError(incident_id)
        if current.resolution_state == "resolved":
            return current
        if evidence not in _RESOLUTION_EVIDENCE.get(current.detector_id, frozenset()):
            raise ValueError("resolution evidence does not match detector recovery condition")
        if _time(resolved_at) < _time(current.last_seen_at):
            raise ValueError("resolution must follow the latest observation")
        updated = replace(current, resolution_state="resolved", resolved_at=resolved_at)
        self._incidents[incident_id] = updated
        return updated

    def get(self, incident_id: str) -> Incident | None:
        return self._incidents.get(incident_id)

    def snapshot(self) -> tuple[Incident, ...]:
        return tuple(sorted(self._incidents.values(), key=lambda item: (item.first_seen_at, item.incident_id)))


__all__ = ["IncidentLifecycle", "MAX_LIFECYCLE_EVIDENCE", "MAX_LIFECYCLE_INCIDENTS"]
