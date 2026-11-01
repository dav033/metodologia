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
        # M6's aggregate BLOCKED_ENV also covers an interrupted engine. Only a pure interruption can be
        # reverified without an agent; mixed/manual/authorization issues keep their existing guards.
        if reason in {"BLOCKED_ENV", "ENGINE_INTERRUPTED"} and codes == {"ENGINE_INTERRUPTED"}:
            return _report(FailureClass.VERIFICATION, "ENGINE_INTERRUPTED",
                           "the engine interrupted verification before a complete verdict was persisted",
                           [*ev, Evidence(kind="verify_issue", ref=verify.result_ref, excerpt="ENGINE_INTERRUPTED")])
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


# a `ui: true` task's contract on the base it would start from (bt_design_approval.check_tree state), D-262
DESIGN_CONTRACT_CODES = {"missing": "DESIGN_CONTRACT_MISSING", "unapproved": "DESIGN_CONTRACT_UNAPPROVED",
                         "hash-mismatch": "DESIGN_CONTRACT_HASH_MISMATCH"}


def design_contract(gate: dict) -> FailureReport:
    """The contract gate refused the start: an environment fact for the owner, never an agent attempt. pictures
    REQ-021 r32 T2.57 ran five agents on a base without its approved v2 contract (D-262)."""
    state = str(gate.get("state") or "unapproved")
    code = str(gate.get("code") or DESIGN_CONTRACT_CODES.get(state, "DESIGN_CONTRACT_UNAPPROVED"))
    path = str(gate.get("path") or "the UI contract")
    why = {"missing": f"{path} is missing from the base the attempt would start from (the design task "
                      f"{gate.get('design_task') or ''} has not delivered it to this line)",
           "hash-mismatch": f"{path} in the base differs from the approved SHA-256 (base {gate.get('sha256') or 'none'})",
           }.get(state, f"{path} is not approved by the owner")
    if gate.get("detail"):
        why += f" ({gate['detail']})"
    return _report(FailureClass.ENVIRONMENT, code, f"{code}: {why}"[:500],
                   [Evidence(kind="design_contract", ref=path[:200], excerpt=f"state={state}")], basis=f"{code} {path}")


AGENT_ENV_UNREACHABLE = "AGENT_ENV_UNREACHABLE"
_SOURCES = {"agent_env_file": "agent env file {file} stale or its tunnel/service down",
            "verifier": "set by the verifier too: tunnel/service down for the checks as well",
            "verifier_inherited": "inherited by the verifier too: tunnel/service down for the checks as well",
            "inherited": "from the engine's environment: tunnel/service down"}


def agent_env_unreachable(probe: dict) -> FailureReport:
    """A network resource of the attempt's test environment did not answer before the start (D-265): an environment
    fact for the owner, never an agent attempt. pictures REQ-021 r32 T3.91 spent a5..a7 on a database port nothing
    listened on. Names the key, host:port, database and where the value comes from; never the value."""
    found = [item for item in probe.get("unreachable") or () if isinstance(item, dict)]
    parts = [f"{item.get('key')} -> {item.get('resource')} {item.get('error')} ("
             + _SOURCES.get(str(item.get("source")), _SOURCES["inherited"]).format(file=probe.get("env_file") or "")
             + ")" for item in found]
    summary = (f"{AGENT_ENV_UNREACHABLE}: " + ("; ".join(parts) or "a test resource did not answer")
               + ". No agent started, no attempt used: fix the file or start the tunnel/service, then retry (probes again).")
    divergent = [item for item in probe.get("divergent") or () if isinstance(item, dict)]
    if divergent:
        summary += (" Agent env file differs from the verifier on "
                    + "; ".join(f"{item.get('key')} (agent: {item.get('agent')}; verifier: {item.get('verifier')})"
                                for item in divergent[:10]) + "; agents get the verifier's value.")
    return _report(FailureClass.ENVIRONMENT, AGENT_ENV_UNREACHABLE, summary[:500],
                   [Evidence(kind="agent_env", ref=str(item.get("key"))[:200], excerpt=str(item.get("resource"))[:200])
                    for item in found[:10]],
                   basis=f"{AGENT_ENV_UNREACHABLE} " + " ".join(sorted(str(item.get("key")) for item in found)))


NO_CHANGE = "AGENT_NO_CHANGE"


def unchanged(snapshot, agent) -> bool:
    """The agent ended normally and its attempt left the tree exactly as it was given (snapshot == its base)."""
    return (snapshot is not None and agent is not None and agent.status == "completed" and bool(snapshot.snapshot_sha)
            and (snapshot.snapshot_sha == snapshot.base_sha or not snapshot.changed_paths))


def no_change(failure: FailureReport, agent, verify) -> FailureReport:
    """A failed verification of an attempt that changed nothing is not an implementation failure to retry: the agent
    stopped on purpose and its final message says why. pictures REQ-021 r32 T2.57: five attempts refused a base without
    the approved contract and changed nothing, each judged CHECK_FAILED and retried, and healing answered three
    decisions with a note about an npm script the agent never got to (D-262). An environment fact for the owner, with
    the agent's own reason; the signature is stable across such attempts (code + failing checks), so a repeat is seen."""
    said = " ".join((agent.text if agent is not None else "").split())
    quote = said[-700:] if said else "(no final message)"
    failing = ", ".join(verify.failing_checks[:5]) if verify is not None else ""
    evidence = [Evidence(kind="agent_report", excerpt=(agent.text if agent is not None else "")[-2000:]),
                Evidence(kind="no_change", excerpt="the attempt changed nothing: its snapshot is the tree it started from"),
                *failure.evidence[:2]]
    note = ("Your previous attempt changed nothing and ended with: «" + quote + "». The checks then failed on the "
            "unchanged tree.\n\n" + failure.agent_note)
    return _report(FailureClass.ENVIRONMENT, NO_CHANGE,
                   f"the attempt changed nothing and the agent said: «{quote[-400:]}»"
                   + (f" (failing checks on the unchanged tree: {failing})" if failing else ""),
                   evidence, note=note, basis=f"{NO_CHANGE} {failing}")


# a V8 heap-limit abort (the process stopped itself at Node's heap cap) versus the sandbox killing it for memory
_V8_HEAP = re.compile(r"Ineffective mark-compacts near heap limit|Reached heap limit|heap limit Allocation failed|"
                      r"JavaScript heap out of memory")
_SANDBOX_KILL = re.compile(r"^\s*Killed\s*$|SIGKILL|\bsignal 9\b|oom[-_ ]kill|\bexit(?: code)?[ =:]*137\b|memory\.events",
                           re.MULTILINE | re.IGNORECASE)
HEAP_LIMIT = "CHECK_HEAP_LIMIT"
HEAP_LIMIT_PLAN = "CHECK_HEAP_LIMIT_PLAN"


def heap_abort(out: str) -> str:
    """The line showing a Node heap-limit abort, when the output shows one and no sandbox memory kill; '' otherwise."""
    text = str(out or "")
    match = _V8_HEAP.search(text)
    if match is None or _SANDBOX_KILL.search(text):
        return ""
    start = text.rfind("\n", 0, match.start()) + 1
    end = text.find("\n", match.end())
    return text[start:end if end >= 0 else len(text)].strip()[:200]


def own_check(failing: Sequence[str], *, known_paths: Sequence[str] = (), own: Sequence[str] = ()) -> str:
    """The first failing check this task created: its command is one the plan marks `created_by` this task (`own`), or
    it runs a file of the task's expected paths. '' when none is."""
    import fnmatch
    own_set = {" ".join(str(c).split()) for c in own}
    for command in failing:
        normal = " ".join(str(command).split())
        if normal in own_set or any(o and o in normal for o in own_set):
            return command
        for token in normal.split():
            token = token.strip("'\"").removeprefix("./")
            if "/" in token and any(fnmatch.fnmatchcase(token, pattern) for pattern in known_paths):
                return command
    return ""


def heap_limit(failure: FailureReport, verify, *, own: str, relaxed: bool) -> FailureReport | None:
    """A Node heap-limit abort in a check is not a sandbox memory kill: a larger sandbox (the relaxed re-verification)
    cannot raise a heap cap that a harness's child process sets for itself. pictures REQ-021 r32 T3.91 a1: the
    harness the task wrote ran `next build` with an explicit environment without NODE_OPTIONS; it aborted at ~2 GB,
    the relaxed re-verification aborted the same way and the owner was asked, the agent never told (D-262).
    In a check this task created (`own`): an implementation failure with a concrete note, retried normally. In
    another check, after the relaxed re-verification (which does raise the heap of a Node process that inherits
    NODE_OPTIONS) aborted again: a plan/check problem for the owner. None: not a heap abort (a genuine sandbox kill)
    or the relaxed re-verification is still to be tried."""
    out = verify.digest if verify is not None else ""
    line = heap_abort(out)
    if not line:
        return None
    lines = Evidence(kind="output_line", ref=verify.result_ref if verify is not None else "", excerpt=out[:2000])
    if own:
        note = (f"A process in your check `{own[:300]}` hit Node's heap cap ({line}). It is not the sandbox's memory: "
                "the child processes your harness spawns receive only the environment the harness gives them. Pass an "
                "explicit, bounded NODE_OPTIONS (for example --max-old-space-size=4096) in the environment of the child "
                "that ran out (e.g. the `next build` it starts). Do not change product code or the check commands for "
                "this.\n\nDecisive lines:\n\n" + out)
        return _report(FailureClass.IMPLEMENTATION, HEAP_LIMIT,
                       f"a process in this task's own check hit Node's heap limit: {line}", [*failure.evidence[:1], lines],
                       note=note, basis=f"{HEAP_LIMIT} {own}")
    if not relaxed:
        return None
    return _report(FailureClass.CONTRACT, HEAP_LIMIT_PLAN,
                   f"a check hit Node's heap limit again with a larger heap ({line}): a process it starts caps its own "
                   "heap (an explicit environment without NODE_OPTIONS); the check or the plan must set it",
                   [*failure.evidence[:1], lines], basis=f"{HEAP_LIMIT_PLAN} {', '.join(verify.failing_checks[:3])}")
