"""Exact-match mapping from approved verification purposes to acceptance criteria."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .contracts import VerifyRequest
from .policy import CheckSpec
from .runner import CommandOutcome

Status = Literal["pass", "fail", "unknown"]


@dataclass(frozen=True)
class CheckResult:
    spec: CheckSpec
    outcome: CommandOutcome
    stdout_ref: str
    stderr_ref: str


@dataclass(frozen=True)
class CriterionResult:
    criterion: str
    status: Status
    evidence: tuple[str, ...]
    issue_code: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "criterion": self.criterion,
            "status": self.status,
            "evidence": list(self.evidence),
        }


def evaluate_criteria(
    order: VerifyRequest, checks: tuple[CheckResult, ...]
) -> tuple[CriterionResult, ...]:
    results: list[CriterionResult] = []
    for criterion in order.acceptance_criteria:
        matches = [item for item in checks if item.spec.purpose == criterion]
        if not matches:
            results.append(
                CriterionResult(criterion, "unknown", (), "CRITERION_UNVERIFIABLE")
            )
        elif len(matches) != 1:
            results.append(
                CriterionResult(
                    criterion,
                    "unknown",
                    tuple(item.spec.id for item in matches),
                    "CRITERION_AMBIGUOUS",
                )
            )
        else:
            match = matches[0]
            if match.spec.kind == "manual":
                results.append(
                    CriterionResult(
                        criterion, "unknown", (match.spec.id,), "CRITERION_MANUAL"
                    )
                )
            elif match.outcome.status == "unknown":
                results.append(
                    CriterionResult(
                        criterion,
                        "unknown",
                        (match.spec.id,),
                        match.outcome.issue_code or "CHECK_UNKNOWN",
                    )
                )
            else:
                results.append(
                    CriterionResult(criterion, match.outcome.status, (match.spec.id,))
                )
    return tuple(results)


def overall_status(
    criteria: tuple[CriterionResult, ...],
    checks: tuple[CheckResult, ...],
    *,
    has_issues: bool = False,
) -> Literal["PASS", "FAIL", "NEEDS_REVIEW"]:
    if any(item.status == "fail" for item in criteria) or any(
        item.spec.kind == "command" and item.outcome.status == "fail" for item in checks
    ):
        return "FAIL"
    if (
        not has_issues
        and criteria
        and all(item.status == "pass" for item in criteria)
        and all(
            item.outcome.status == "pass"
            for item in checks
            if item.spec.kind == "command"
        )
    ):
        return "PASS"
    return "NEEDS_REVIEW"
