"""Evidence-based failure classification (REQ-030 M5): one taxonomy for everything an attempt can end with.

Rules are ordered and explicit; each one names the evidence it used, so the class of a failure can be audited. The
decisive output lines come from the same extractor the agent's verification note uses, so what the classifier
saw is what the next attempt is told. Nothing here guesses a quota reset or bypasses a permission: those become
`quota` with an unknown reset, or `permission`, and the policy decides what is allowed.
"""
from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from dataclasses import dataclass, field

from bitacora_platform import failure_lines
from bt_contracts.execution import (
    AgentReport,
    ProcessRecord,
    VerifyOutcome,
    VerifyStatus,
)
from bt_contracts.failure import Evidence, FailureClass, FailureReport

_ENV_MISSING = re.compile(r"\b(?:Set|Missing|missing|requires?|undefined env(?:ironment)? var(?:iable)?)\s+`?([A-Z][A-Z0-9_]{2,})`?")
_CONN = re.compile(r"ECONNRESET|ECONNREFUSED|ETIMEDOUT|EAI_AGAIN|socket hang up|stream disconnected|overloaded|"
                   r"\b(?:502|503|504|529)\b|Service Unavailable|Bad Gateway|rate.?limit", re.IGNORECASE)
_AUTH = re.compile(r"\b401\b|\b403\b|unauthori[sz]ed|authentication (?:failed|required)|not logged in|invalid api key|"
                   r"login required|permission denied by policy", re.IGNORECASE)
_VOLATILE = re.compile(r"0x[0-9a-f]+|\b[0-9a-f]{12,}\b|\d+(?:\.\d+)?(?:ms|s)?\b|/tmp/[^\s'\"]+|:\d+:\d+")

# M6 reason/issue codes that are not a verdict on the code
_TRANSIENT_VERIFY = frozenset({"SANDBOX_UNAVAILABLE", "RUNNER_BUSY", "STORE_FAILURE"})
_MANUAL_VERIFY = frozenset({"CHECK_MANUAL", "CRITERION_UNMAPPED", "CRITERION_AMBIGUOUS", "CRITERION_MANUAL"})
# what a coordinator receipt can settle (bt_scheduler_quality.recovery.ATTESTABLE): only manual evidence is missing
_ATTESTABLE = frozenset({"CRITERION_MANUAL", "CHECK_MANUAL", "CHECK_UNMAPPED"})
MANUAL_EVIDENCE = "MANUAL_EVIDENCE_REQUIRED"
_ENV_VERIFY = frozenset({"BLOCKED_EXTERNAL", "BLOCKED_ENV", "CHECK_UNAVAILABLE", "OUTPUT_LIMIT"})
_PERMISSION_VERIFY = frozenset({"POLICY_ENTRY_MISSING_AUTHORIZATION", "AUTHORIZATION_DENIED", "OPERATOR_REVIEW"})
_INTERNAL_VERIFY = frozenset({"SNAPSHOT_INVALID", "UNCLASSIFIED_INTERNAL"})
_PERMISSION_START = frozenset({"POLICY_DENIED", "AUTH_FAILED"})
_CONTRACT_START = frozenset({"ORDER_INVALID", "ROUTE_INVALID", "CONTRACT_INVALID", "PLAN_INVALID"})


@dataclass(frozen=True)
class AttemptFacts:
    """What the runtime observed about one attempt; every field is optional because an attempt can end anywhere."""
    start_error: str = ""                    # "CODE: detail" from preparing/launching
    process: ProcessRecord | None = None
    agent: AgentReport | None = None
    verify: VerifyOutcome | None = None
    failing_output: str = ""                 # decisive excerpt of the failing checks (stderr first)
    integration_conflict: str = ""
    internal_error: str = ""                 # an unexpected exception inside the runtime
    declared_requires: Sequence[str] = field(default_factory=tuple)
    known_paths: Sequence[str] = field(default_factory=tuple)   # the task's expected paths: names of its own sources


def signature(failure_class: FailureClass, code: str, lines: str) -> str:
    """Stable across reruns: numbers, hashes, temp paths and positions are erased before hashing."""
    normal = _VOLATILE.sub("#", " ".join(lines.split()))[:4000]
    return hashlib.sha256(f"{failure_class}|{code}|{normal}".encode()).hexdigest()[:16]


def _report(cls: FailureClass, code: str, summary: str, evidence: list[Evidence], note: str = "",
            basis: str = "") -> FailureReport:
    return FailureReport(failure_class=cls, code=code, summary=summary[:500],
                         signature=signature(cls, code, basis or summary), evidence=tuple(evidence),
                         agent_note=note[:6000])


def classify(facts: AttemptFacts) -> FailureReport | None:
    """None when the attempt succeeded (verified PASS and nothing else went wrong)."""
    out = facts.failing_output or (facts.verify.digest if facts.verify else "")
    if facts.internal_error:
        return _report(FailureClass.INTERNAL, "RUNTIME_ERROR", f"runtime defect: {facts.internal_error}",
                       [Evidence(kind="exception", excerpt=facts.internal_error[:2000])])
    if facts.start_error:
        code = facts.start_error.split(":", 1)[0].strip() or "START_FAILED"
        ev = [Evidence(kind="start_error", excerpt=facts.start_error[:2000])]
        if code in _PERMISSION_START or _AUTH.search(facts.start_error):
            return _report(FailureClass.PERMISSION, code, f"start refused: {facts.start_error}", ev)
        if code in _CONTRACT_START:
            return _report(FailureClass.CONTRACT, code, f"invalid order or plan data: {facts.start_error}", ev)
        if code in {"WORKSPACE_ERROR", "BASE_UNRESOLVED", "REPOSITORY_UNKNOWN"}:
            return _report(FailureClass.INTERNAL, code, f"could not prepare the workspace: {facts.start_error}", ev)
        return _report(FailureClass.TRANSIENT, code, f"could not start the agent: {facts.start_error}", ev)
    process, agent, verify = facts.process, facts.agent, facts.verify
    if agent and agent.status == "limit":
        return _report(FailureClass.QUOTA, "ROUTE_LIMIT", "the provider reported a usage limit",
                       [Evidence(kind="agent_report", excerpt=agent.text[:500])],
                       basis=f"limit {agent.reset_epoch or 'unknown'}")
    if agent and _AUTH.search(agent.text) and agent.status != "completed":
        return _report(FailureClass.PERMISSION, "PROVIDER_AUTH", "the provider refused the account",
                       [Evidence(kind="agent_report", excerpt=agent.text[:500])])
    if process and process.oom_killed:
        return _report(FailureClass.ENVIRONMENT, "AGENT_OOM", "the agent process was killed by its memory limit",
                       [Evidence(kind="cgroup", ref=process.unit or "", excerpt=f"result={process.result}")])
    if process and process.result == "timeout" or (agent and agent.status == "timeout"):
        return _report(FailureClass.TRANSIENT, "AGENT_TIMEOUT", "the agent ran out of its time limit",
                       [Evidence(kind="exit_record", ref=(process.unit or "") if process else "",
                                 excerpt=f"result={process.result if process else 'timeout'}")])
    if agent and agent.status in {"failed", "partial"} and _CONN.search(agent.text) and verify is None:
        return _report(FailureClass.TRANSIENT, "PROVIDER_CONNECTION", "the provider connection failed",
                       [Evidence(kind="agent_report", excerpt=agent.text[:500])])
    if facts.integration_conflict:
        return _report(FailureClass.INTEGRATION, "INTEGRATION_CONFLICT", facts.integration_conflict,
                       [Evidence(kind="integration", excerpt=facts.integration_conflict[:2000])],
                       note=("Your result conflicts with work accepted since you started: " + facts.integration_conflict))
    if verify is None:
        if agent and agent.status in {"failed", "partial", "cancelled"}:
            return _report(FailureClass.TRANSIENT, f"AGENT_{agent.status.upper()}",
                           f"the agent ended {agent.status} before verification",
                           [Evidence(kind="agent_report", excerpt=agent.text[:500])])
        return _report(FailureClass.INTERNAL, "NO_VERDICT", "the attempt ended without a verification verdict", [])
    return _classify_verdict(verify, out, facts)


def _classify_verdict(verify: VerifyOutcome, out: str, facts: AttemptFacts) -> FailureReport | None:
    reason = verify.reason_code or "UNCLASSIFIED"
    ev = [Evidence(kind="verify_reason", ref=verify.result_ref, excerpt=reason)]
    if verify.status == VerifyStatus.PASS:
        return None
    if verify.status == VerifyStatus.STALE:
        return _report(FailureClass.INTERNAL, "VERIFY_STALE", "the verification belongs to a replaced attempt", ev)
    if reason in _PERMISSION_VERIFY:
        return _report(FailureClass.PERMISSION, reason, "a check needs an authorization the operator has not given", ev)
    if verify.status == VerifyStatus.NEEDS_REVIEW:
        codes = set(verify.issue_codes) or {reason}
        if "CRITERION_MANUAL" in codes and codes <= _ATTESTABLE:
            # not a failure of the code and not opaque: the owner (or coordinator) attests the named manual checks
            # with `bt-durable attest`, and the same snapshot is verified again without an agent run
            checks = "; ".join(verify.manual_checks) or "the task's manual checks"
            return _report(FailureClass.PRODUCT_DECISION, MANUAL_EVIDENCE,
                           f"manual evidence is missing for: {checks}"[:500],
                           [*ev, *(Evidence(kind="manual_check", excerpt=check[:2000]) for check in verify.manual_checks[:5])])
        if reason in _TRANSIENT_VERIFY:
            return _report(FailureClass.TRANSIENT, reason, "the verifier could not run the checks", ev)
        if reason in _MANUAL_VERIFY:
            return _report(FailureClass.PRODUCT_DECISION, reason, "a criterion needs a human check or a plan fix", ev)
        if reason == "CHECK_TIMEOUT":
            return _report(FailureClass.VERIFICATION, reason, "a check exceeded the verifier's time limit", ev)
        if reason == "FLAKY_SUSPECTED":
            return _report(FailureClass.VERIFICATION, reason, "a check passed and failed on the same tree", ev)
        if reason in _ENV_VERIFY:
            return _report(FailureClass.ENVIRONMENT, reason, "a declared resource or tool is missing", ev)
        if reason in _INTERNAL_VERIFY:
            return _report(FailureClass.INTERNAL, reason, "the verifier rejected its own inputs", ev)
        return _report(FailureClass.VERIFICATION, reason, "the verifier could not decide", ev)
    lines = Evidence(kind="output_line", ref=verify.result_ref, excerpt=out[:2000])
    limit, shown = failure_lines.resource_limit(out)       # the same reading the agent's note uses
    if limit:
        code = "VERIFIER_OOM" if limit == "memory" else "VERIFIER_PROCESS_LIMIT"
        return _report(FailureClass.ENVIRONMENT, code,
                       f"a check hit the verifier sandbox's {limit} limit (not a code defect): {shown}", [*ev, lines],
                       basis=code)
    missing = _ENV_MISSING.search(out)
    if missing and missing.group(1) in set(facts.declared_requires):
        return _report(FailureClass.ENVIRONMENT, "ENV_MISSING",
                       f"the check did not receive the declared variable {missing.group(1)}", [*ev, lines],
                       basis=missing.group(1))
    packages = [name for name, kind in failure_lines.missing_modules(out, facts.known_paths) if kind == "package"]
    if packages:
        return _report(FailureClass.ENVIRONMENT, "DEPENDENCY_MISSING",
                       f"the package {packages[0]} is not installed where the check runs", [*ev, lines],
                       basis=packages[0])
    note = ("The independent verification of your previous attempt failed. Decisive lines:\n\n" + out) if out else ""
    return _report(FailureClass.IMPLEMENTATION, "CHECK_FAILED",
                   "checks failed: " + ", ".join(verify.failing_checks[:5]) if verify.failing_checks else "checks failed",
                   [*ev, lines], note=note, basis=out or reason)
