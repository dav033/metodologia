"""Pure progress assessment from explicit, evidence-backed occurrence relations."""
from __future__ import annotations

from .diagnostic_contracts import ProgressSnapshot, RecoveryProgress
from .validation import require


def assess_progress(previous: ProgressSnapshot, current: ProgressSnapshot) -> RecoveryProgress:
    require(type(previous) is ProgressSnapshot and type(current) is ProgressSnapshot)
    old = {item.occurrence_id: item for item in previous.occurrences}
    new = {item.occurrence_id: item for item in current.occurrences}
    require(len(old) == len(previous.occurrences) and len(new) == len(current.occurrences))
    relations = {item.current_occurrence: item.previous_occurrence for item in current.relations}
    require(len(relations) == len(current.relations))
    require(all(source in old and target in new for target, source in relations.items()))

    persisted: list[str] = []
    fixed: list[str] = []
    added: list[str] = []
    regressed: list[str] = []
    uncertain: list[str] = []
    matched_previous: set[str] = set()
    for occurrence_id, occurrence in new.items():
        if not occurrence.evidence_refs:
            uncertain.append(occurrence_id)
            continue
        previous_id = relations.get(occurrence_id)
        if previous_id is None:
            (fixed if occurrence.state == "fixed" else added).append(occurrence_id)
            continue
        matched_previous.add(previous_id)
        prior = old[previous_id]
        if prior.state == "fixed" and occurrence.state == "open":
            regressed.append(occurrence_id)
        elif occurrence.state == "fixed":
            fixed.append(occurrence_id)
        else:
            persisted.append(occurrence_id)

    for occurrence_id, occurrence in old.items():
        if occurrence.state == "open" and occurrence_id not in matched_previous:
            uncertain.append(occurrence_id)

    blocked = tuple(sorted(check.check_id for check in current.prerequisite_checks if check.status == "blocked"))
    return RecoveryProgress(tuple(sorted(persisted)), tuple(sorted(fixed)), tuple(sorted(added)),
                            tuple(sorted(regressed)), tuple(sorted(set(uncertain))), blocked)
