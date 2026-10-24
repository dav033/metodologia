"""Deterministic M6 verification orchestration; it never mutates M1 or M3 state."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Callable
from typing import Any

from .contracts import QualityError, VerifyRequest
from .criteria import CheckResult, CriterionResult, evaluate_criteria, overall_status
from .evidence import build_evidence, sha256_bytes, validate_result_contract
from . import reuse
from .authority import VerificationAuthority
from .check_runner import CheckExecutor
from .policy import CheckSpec, QualityPolicy, compile_verification
from .review import ReviewerPort, validate_reviewer_evidence
from .runner import CommandOutcome, SandboxRunner
from .snapshot import SHA_LENGTHS, SnapshotResolver, SnapshotSource
from .store import QualityStore

_ISSUE_DETAILS = {
    "HANDOFF_MISSING": "M3 did not provide a valid captured handoff.",
    "SNAPSHOT_INVALID": "The captured snapshot could not be safely verified.",
    "CHECK_UNSUPPORTED": "The approved command is outside the supported verification policy.",
    "CHECK_PRODUCTION_ACTION": "This verification requests an external deployment or migration and needs operator review.",
    "CHECK_TIMEOUT": "The command exceeded its wall-clock limit.",
    "OUTPUT_LIMIT": "The command exceeded its captured output limit.",
    "SANDBOX_UNAVAILABLE": "The required operating-system sandbox could not be established.",
    "CHECK_UNAVAILABLE": "A declared external resource or trusted authorization is unavailable.",
    "POLICY_ENTRY_MISSING_AUTHORIZATION": "The matching external policy entry is missing its authorization field.",
    "CHECK_MANUAL": "This verification requires an explicit operator review.",
    "RUNNER_BUSY": "The configured verification concurrency limit is full.",
    "ENGINE_INTERRUPTED": "M6 stopped before persisting a complete result; commands were not rerun.",
    "ENGINE_FAILURE": "M6 could not complete verification safely.",
    "REVIEW_REQUIRED": "Operator policy requires a separate review, but none is available.",
    "REVIEW_UNAVAILABLE": "The configured independent reviewer did not return evidence.",
    "REVIEW_INVALID": "The independent review evidence is invalid or does not match this request.",
    "REVIEW_NOT_INDEPENDENT": "The reviewer identity matches an author of the verification checks.",
    "REVIEW_REJECTED": "The independent reviewer rejected the verification result.",
    "CHECK_UNMAPPED": "A verification check does not map exactly to an acceptance criterion.",
    "CRITERION_UNVERIFIABLE": "No verification check maps exactly to this acceptance criterion.",
    "CRITERION_AMBIGUOUS": "More than one verification check maps to this acceptance criterion.",
    "CRITERION_MANUAL": "This acceptance criterion has only manual evidence.",
    "CHECK_UNKNOWN": "The check did not produce a determinate result.",
    "CHECK_DEFERRED": "An expensive check was not run because a cheaper one failed first.",
}


@dataclass(frozen=True)
class _ExecutionEvidence:
    specs: tuple[CheckSpec, ...]
    outcomes: dict[str, CommandOutcome]
    base_sha: str | None
    snapshot_sha: str | None
    issue_codes: tuple[str, ...]
    manifest_context: dict[str, Any]


class QualityEngine:
    def __init__(
        self,
        policy: QualityPolicy,
        store: QualityStore,
        *,
        runner: SandboxRunner | None = None,
        resolver: SnapshotResolver | None = None,
        reviewer: ReviewerPort | None = None,
        attestations: Callable[[VerifyRequest, CheckSpec], str | None] | None = None,
        own_outputs: Callable[[VerifyRequest], tuple[str, ...]] | None = None,
        verification_authority: VerificationAuthority | None = None,
    ):
        """`attestations(order, spec)` -> the digest of a valid receipt the coordinator left for that manual check, or None
        (a receipt is minted and verified outside this package; M6 only learns whether one holds)."""
        self.attestations = attestations
        self.own_outputs = own_outputs          # order -> the report files its task writes (they do not change what a check proves)
        self.policy = policy
        self.store = store
        self.runner = runner or SandboxRunner(policy)
        self.check_executor = CheckExecutor(policy, store, self.runner, verification_authority)
        self.resolver = resolver or SnapshotResolver(policy)
        self.reviewer = reviewer

    def verify(
        self, raw_order: object, source: SnapshotSource | None
    ) -> dict[str, Any]:
        order = (
            raw_order
            if isinstance(raw_order, VerifyRequest)
            else VerifyRequest.from_mapping(raw_order)
        )
        state, existing = self.store.reserve(
            order, max_pending=self.policy.max_pending_requests
        )
        if state == "existing":
            if existing is None:
                raise QualityError("STORE_FAILURE", "completed request has no result")
            return existing
        if state != "new" or not self.store.claim_work(order.idempotency_key):
            raise QualityError(
                "REQUEST_IN_PROGRESS", "the same request already has an active verifier"
            )
        return self.process_reserved(order, source)

    def process_reserved(
        self, order: VerifyRequest, source: SnapshotSource | None
    ) -> dict[str, Any]:
        """Run one request whose durable queue entry is already claimed by a worker."""
        execution = self._execute_order(order, source, time.monotonic())
        checks, artifact_bodies = _build_check_results(
            execution.specs, execution.outcomes
        )
        receipts: dict[str, str] = {}

        def attested(spec: CheckSpec) -> bool:
            receipt = self.attestations(order, spec) if self.attestations else None
            if receipt:
                receipts[spec.id] = receipt
            return bool(receipt)

        criteria = evaluate_criteria(order, checks, mixed=self.policy.mixed_evidence, attested=attested)
        mapped = {
            item.spec.purpose
            for item in checks
            if item.spec.purpose in order.acceptance_criteria
        }
        issue_codes = list(execution.issue_codes)
        issue_codes.extend(item.issue_code for item in criteria if item.issue_code)
        if _has_unmapped_check(checks, order, criteria):
            issue_codes.append("CHECK_UNMAPPED")
        unique_codes = tuple(dict.fromkeys(issue_codes))
        issues = _issue_documents(unique_codes)
        status = overall_status(criteria, checks, has_issues=bool(issues))
        status, unique_codes, issues, review_manifest = self._apply_review(
            order, criteria, checks, status, unique_codes
        )
        result, result_bytes, manifest_bytes, _ = build_evidence(
            order,
            self.policy,
            base_sha=execution.base_sha,
            snapshot_sha=execution.snapshot_sha,
            checks=checks,
            criteria=criteria,
            status=status,
            issues=issues,
            tree_digest=execution.manifest_context.get("tree_digest", execution.snapshot_sha),
            check_tree_digests=execution.manifest_context.get("check_tree_digests"),
            environment_fingerprint=execution.manifest_context.get("environment_fingerprint"),
            extra_manifest={
                **execution.manifest_context,
                "mapped_criteria": sorted(mapped),
                **({"attestations": dict(sorted(receipts.items()))} if receipts else {}),
                **({"independent_review": review_manifest} if review_manifest else {}),
            },
        )
        validate_result_contract(result)
        self.store.finish(order, result, result_bytes, manifest_bytes, artifact_bodies)
        return result

    def _execute_order(
        self,
        order: VerifyRequest,
        source: SnapshotSource | None,
        started: float,
    ) -> _ExecutionEvidence:
        if source is not None and not isinstance(source, SnapshotSource):
            source = None
        specs = _raw_specs(order)
        base_sha = (
            source.base_sha if source and _valid_commit(source.base_sha) else None
        )
        snapshot_sha = (
            source.snapshot_sha
            if source and _valid_commit(source.snapshot_sha)
            else None
        )
        if source is None:
            return _ExecutionEvidence(
                specs,
                {spec.id: _unknown("HANDOFF_MISSING") for spec in specs},
                base_sha,
                snapshot_sha,
                ("HANDOFF_MISSING",),
                {"source": "unavailable"},
            )
        try:
            return self._execute_snapshot(order, source, started)
        except QualityError as error:
            code = error.code
            return _ExecutionEvidence(
                specs,
                {spec.id: _unknown(code) for spec in specs},
                base_sha if _valid_commit(base_sha) else None,
                snapshot_sha if _valid_commit(snapshot_sha) else None,
                (code,),
                {"source": "rejected", "source_issue": code},
            )

    def _execute_snapshot(
        self,
        order: VerifyRequest,
        source: SnapshotSource,
        started: float,
    ) -> _ExecutionEvidence:
        with self.resolver.materialize(source) as snapshot:
            specs = compile_verification(order, snapshot.directory, self.policy)
            ignore = tuple(self.own_outputs(order)) if self.own_outputs and self.policy.cache_ignores_outputs else ()
            pruned: dict[tuple[str, ...], str | None] = {}

            def tree_for(spec: CheckSpec) -> str | None:
                # a check that names a report file reads it: that file stays in ITS key
                skip = tuple(path for path in ignore if path not in spec.command)
                if skip not in pruned:
                    pruned[skip] = reuse.tree_id(source.repository, snapshot.snapshot_sha, skip)
                return pruned[skip]

            check_tree_digests: dict[str, str | None] = {}

            def check_tree(spec: CheckSpec) -> str | None:
                value = tree_for(spec)
                check_tree_digests[spec.id] = value or snapshot.snapshot_sha
                return value

            outcomes, issue_codes = self.check_executor.run(
                specs, snapshot.directory, started, source.worktree, source.repository,
                tree=None if ignore else reuse.tree_id(source.repository, snapshot.snapshot_sha),
                tree_for=check_tree if ignore else None,
                order=order,
            )
            full_tree = reuse.tree_id(source.repository, snapshot.snapshot_sha)
            if not ignore:
                check_tree_digests.update({spec.id: full_tree or snapshot.snapshot_sha for spec in specs})
            return _ExecutionEvidence(
                specs,
                outcomes,
                snapshot.base_sha,
                snapshot.snapshot_sha,
                tuple(issue_codes),
                {
                    "source": "m3-handoff",
                    "manifest_sha256": snapshot.manifest_sha256,
                    "archive_sha256": snapshot.archive_sha256,
                    "uncompressed_bytes": snapshot.uncompressed_bytes,
                    "file_count": snapshot.file_count,
                    "tree_digest": full_tree or snapshot.snapshot_sha,
                    "check_tree_digests": check_tree_digests,
                    "environment_fingerprint": reuse.bound_environment_fingerprint(
                        self.policy, order.contract_identities, order.environment_fingerprint
                    ),
                },
            )

    def _apply_review(
        self,
        order: VerifyRequest,
        criteria: tuple[CriterionResult, ...],
        checks: tuple[CheckResult, ...],
        status: str,
        unique_codes: tuple[str, ...],
    ) -> tuple[str, tuple[str, ...], tuple[dict[str, str], ...], dict[str, Any] | None]:
        if not self.policy.require_independent_review:
            return status, unique_codes, _issue_documents(unique_codes), None
        review_manifest, review_issue = self._request_review(
            order, criteria, checks, status
        )
        if review_issue:
            unique_codes = tuple(dict.fromkeys((*unique_codes, review_issue)))
            if review_issue == "REVIEW_REJECTED":
                status = "FAIL"
            elif (
                review_issue
                in {
                    "REVIEW_REQUIRED",
                    "REVIEW_UNAVAILABLE",
                    "REVIEW_INVALID",
                    "REVIEW_NOT_INDEPENDENT",
                }
                and status != "FAIL"
            ):
                status = "NEEDS_REVIEW"
        return status, unique_codes, _issue_documents(unique_codes), review_manifest

    def _request_review(
        self,
        order: VerifyRequest,
        criteria: tuple[CriterionResult, ...],
        checks: tuple[CheckResult, ...],
        status: str,
    ) -> tuple[dict[str, Any] | None, str | None]:
        if self.reviewer is None:
            return None, "REVIEW_REQUIRED"
        review_input = {
            "input_hash": order.input_hash,
            "status": status,
            "criteria": [item.to_dict() for item in criteria],
            "checks": [
                {
                    "id": item.spec.id,
                    "status": item.outcome.status,
                    "exit_code": item.outcome.exit_code,
                    "stdout_ref": item.stdout_ref,
                    "stderr_ref": item.stderr_ref,
                }
                for item in checks
            ],
        }
        try:
            review = validate_reviewer_evidence(
                self.reviewer.review(order, review_input),
                order,
                self.policy.secret_values,
            )
        except QualityError as error:
            return None, error.code
        # Custom reviewer ports may raise provider-specific exceptions.
        except Exception:  # noqa: BLE001
            return None, "REVIEW_UNAVAILABLE"
        if not review.approved:
            return review.to_dict(), "REVIEW_REJECTED"
        return review.to_dict(), None

    def finish_unavailable(self, order: VerifyRequest, code: str) -> dict[str, Any]:
        if code not in _ISSUE_DETAILS:
            code = "ENGINE_FAILURE"
        specs = _raw_specs(order)
        checks_list: list[CheckResult] = []
        artifact_bodies: dict[str, bytes] = {}
        for spec in specs:
            outcome = _unknown(code)
            stdout_digest, stderr_digest = (
                sha256_bytes(outcome.stdout),
                sha256_bytes(outcome.stderr),
            )
            artifact_bodies[stdout_digest] = outcome.stdout
            artifact_bodies[stderr_digest] = outcome.stderr
            checks_list.append(
                CheckResult(
                    spec,
                    outcome,
                    f"m6://artifact/{stdout_digest}",
                    f"m6://artifact/{stderr_digest}",
                )
            )
        checks = tuple(checks_list)
        criteria = evaluate_criteria(order, checks)
        issues = (
            {
                "code": code,
                "detail": _ISSUE_DETAILS.get(
                    code, "M6 could not complete verification safely."
                ),
            },
        )
        result, result_bytes, manifest_bytes, _ = build_evidence(
            order,
            self.policy,
            base_sha=None,
            snapshot_sha=None,
            checks=checks,
            criteria=criteria,
            status="NEEDS_REVIEW",
            issues=issues,
            environment_fingerprint=reuse.bound_environment_fingerprint(
                self.policy, order.contract_identities, order.environment_fingerprint
            ),
            extra_manifest={"source": "unavailable", "checks_replayed": False},
        )
        validate_result_contract(result)
        self.store.finish(order, result, result_bytes, manifest_bytes, artifact_bodies)
        return result

    def recover_interrupted(self) -> tuple[str, ...]:
        """Convert durable in-flight requests into review items without replaying any check."""
        recovered: list[str] = []
        for key, raw_order in self.store.pending_requests():
            order = VerifyRequest.from_mapping(raw_order)
            specs = _raw_specs(order)
            artifact_bodies: dict[str, bytes] = {}
            checks_list: list[CheckResult] = []
            for spec in specs:
                outcome = _unknown("ENGINE_INTERRUPTED")
                stdout_digest, stderr_digest = (
                    sha256_bytes(outcome.stdout),
                    sha256_bytes(outcome.stderr),
                )
                artifact_bodies[stdout_digest] = outcome.stdout
                artifact_bodies[stderr_digest] = outcome.stderr
                checks_list.append(
                    CheckResult(
                        spec,
                        outcome,
                        f"m6://artifact/{stdout_digest}",
                        f"m6://artifact/{stderr_digest}",
                    )
                )
            checks = tuple(checks_list)
            criteria = evaluate_criteria(order, checks)
            issues = (
                {
                    "code": "ENGINE_INTERRUPTED",
                    "detail": _ISSUE_DETAILS["ENGINE_INTERRUPTED"],
                },
            )
            result, result_bytes, manifest_bytes, _ = build_evidence(
                order,
                self.policy,
                base_sha=None,
                snapshot_sha=None,
                checks=checks,
                criteria=criteria,
                status="NEEDS_REVIEW",
                issues=issues,
                environment_fingerprint=reuse.bound_environment_fingerprint(
                    self.policy, order.contract_identities, order.environment_fingerprint
                ),
                extra_manifest={
                    "source": "interrupted",
                    "request_key": key,
                    "commands_replayed": False,
                },
            )
            validate_result_contract(result)
            self.store.finish(
                order, result, result_bytes, manifest_bytes, artifact_bodies
            )
            recovered.append(key)
        return tuple(recovered)


def _build_check_results(
    specs: tuple[CheckSpec, ...], outcomes: dict[str, CommandOutcome]
) -> tuple[tuple[CheckResult, ...], dict[str, bytes]]:
    artifact_bodies: dict[str, bytes] = {}
    results: list[CheckResult] = []
    for spec in specs:
        outcome = outcomes[spec.id]
        stdout_digest, stderr_digest = (
            sha256_bytes(outcome.stdout),
            sha256_bytes(outcome.stderr),
        )
        artifact_bodies[stdout_digest] = outcome.stdout
        artifact_bodies[stderr_digest] = outcome.stderr
        results.append(
            CheckResult(
                spec,
                outcome,
                f"m6://artifact/{stdout_digest}",
                f"m6://artifact/{stderr_digest}",
            )
        )
    return tuple(results), artifact_bodies


def _has_unmapped_check(
    checks: tuple[CheckResult, ...], order: VerifyRequest, criteria: tuple[CriterionResult, ...]
) -> bool:
    """A check whose purpose names no criterion needs review, except a supplementary COMMAND check (a baseline such as the
    project's own test script) when every criterion already has exactly one clean check of its own: criteria are still
    proven one by one, and `overall_status` still requires every command, supplementary ones too, to pass."""
    unmapped = [item for item in checks if item.spec.purpose not in order.acceptance_criteria]
    if not unmapped:
        return False
    return any(item.spec.kind != "command" for item in unmapped) or any(item.issue_code for item in criteria)


def _issue_documents(codes: tuple[str, ...]) -> tuple[dict[str, str], ...]:
    return tuple(
        {
            "code": code,
            "detail": _ISSUE_DETAILS.get(code, "Verification evidence needs review."),
        }
        for code in codes
    )


def _raw_specs(order: VerifyRequest) -> tuple[CheckSpec, ...]:
    return tuple(
        CheckSpec(
            f"CHECK-{index:03d}",
            item.kind,
            item.value,
            (),
            ".",
            item.purpose,
            item.expected,
        )
        for index, item in enumerate(order.verification, start=1)
    )


def _unknown(code: str) -> CommandOutcome:
    return CommandOutcome("unknown", None, 0, b"", b"", code, False)


def _valid_commit(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) in SHA_LENGTHS
        and all(char in "0123456789abcdef" for char in value)
    )
