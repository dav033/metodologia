"""M6 structural integration gate delivery helpers."""
from __future__ import annotations

from collections.abc import Callable


class EvidenceUnavailable(RuntimeError):
    """The structural verdict cannot be safely delivered without complete evidence."""


def integration_problem(source_reader: Callable, task_id: str, attempt_id: str,
                        integration_check: Callable | None, unresolved_check: Callable | None,
                        revert_check: Callable | None = None) -> str:
    if integration_check is None and unresolved_check is None and revert_check is None:
        return ""
    try:
        source = source_reader()
        if not source:
            raise EvidenceUnavailable("evidence_unavailable: M3 snapshot manifest is missing")
        left = unresolved_check(task_id, source.snapshot_sha) if unresolved_check else ()
        if left:
            return "merge conflict markers left in: " + ", ".join(left[:6])
        back = revert_check(task_id, source.snapshot_sha, base=source.base_sha) if revert_check else ()
        if back:
            return "files changed back to an older version than the base they started from: " + ", ".join(back[:6])
        return integration_check(task_id, attempt_id, source.snapshot_sha) if integration_check else ""
    except EvidenceUnavailable:
        raise
    except Exception as error:  # noqa: BLE001 - structural evidence failure cannot be converted to an empty conflict
        raise EvidenceUnavailable("evidence_unavailable: integration evidence could not be recomputed") from None


def task_ids_in_clash(clash: str, task_id: str) -> tuple[str, ...]:
    pair = clash.split(" for ", 1)[0]
    sides = pair.split(" vs ", 1)
    return tuple(dict.fromkeys(part for side in sides for part in side.split("+") if part != task_id))


def refusal_detail(core, clash: str, task_id: str) -> str:
    named = task_ids_in_clash(clash, task_id)
    known = {spec.id for spec in core.plan.tasks}
    detail = core.rework_problem(named, (), cascade=False) if named and set(named) <= known else ""
    return detail or "rework refused: task set is not eligible for ordinary give-way"


def publish_or_raise(publisher: Callable | None, order, clash: str, refusal: str, detail: str) -> str | None:
    if publisher is None:
        return None
    try:
        reference = publisher(order, clash, refusal, detail)
    except Exception as error:  # noqa: BLE001 - sink failure makes an automatic verdict unsafe
        raise EvidenceUnavailable(f"evidence_unavailable: integration conflict publication failed ({type(error).__name__})") from None
    if not isinstance(reference, str) or not reference:
        raise EvidenceUnavailable("evidence_unavailable: integration conflict publication returned no reference")
    return reference


def start_rejection_detail(error) -> str:
    """Preserve IntegrationError's old code/detail while making missing publication explicit at M1."""
    prefix = "evidence_unavailable: " if getattr(error, "conflict_data", None) and error.conflict_data.get(
        "evidence_unavailable") else ""
    reference = error.conflict_data.get("evidence_ref") if getattr(error, "conflict_data", None) else None
    evidence = f" | conflict evidence: {reference}" if isinstance(reference, str) and reference else ""
    return f"{prefix}{error.code}: {error.detail}{evidence}"[:300]
