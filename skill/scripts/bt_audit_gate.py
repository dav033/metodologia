"""Audit gate: an audit task passes only when its findings ledger has no open blocking finding.

A `kind: audit` task declares one `*.findings.json` among its files. The auditor writes the human report and this
machine-readable ledger beside it:

    {"schema": "audit-findings/1", "findings": [
        {"id": "F1", "severity": "critical|high|medium|low", "status": "open|fixed|accepted",
         "summary": "...", "tasks": ["T13"],                       # plan tasks whose result is wrong
         "evidence": "..." (required when fixed), "accepted_by": "owner", "reason": "..." (required when accepted)}]}

The gate reads the ledger, never the prose. Whether the report says «PARTIAL, release blocked» is irrelevant: a
critical/high/medium finding still `open` (the default `gates.audit_blocking`) rejects the task, a ledger that is missing or malformed rejects it, and the tasks the
findings name are sent back for rework by the Scheduler (`SchedulerCore.reject_and_rework`). Only the owner can accept a
risk; an auditor cannot waive its own finding. Standard library only; ledger evaluation is pure, and the provenance
helpers read git trees without changing the repository (the caller reads evidence files).
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from dataclasses import dataclass

from bt_audit_evidence import DIGEST, evidence_gate, evidence_outputs, evidence_paths, tree_digest

LEDGER_SUFFIX = ".findings.json"
SCHEMA = "audit-findings/1"
SEVERITIES = ("critical", "high", "medium", "low")
BLOCKING_SEVERITIES = ("critical", "high", "medium")   # default (D-233): a confirmed defect is repaired, not left open;
#                                                       `bt_config` `gates.audit_blocking` overrides it
STATUSES = ("open", "fixed", "accepted")
REWORK_SCOPES = ("named", "downstream")
MAX_BYTES = 1 << 20
MAX_FINDINGS = 200
MAX_TEXT = 600
SEMANTIC_FINGERPRINT = re.compile(r"^[0-9a-f]{64}$")

def evidence_help(rdir, task_id: str) -> str:
    """Where an auditor keeps its screenshots, logs and other evidence: outside the repository, in the requirement's
    evidence folder. Inside the repository an audit writes only its report and ledger; a visual audit that saved its
    captures next to its report was rejected for files it did not declare and audited again (pictures REQ-021 T2.7,
    then T5.5 with 16 captures, 2026-10-29)."""
    folder = Path(rdir) / "evidence" / task_id
    return (f"Inside the repository write only the report and the ledger. Keep screenshots, captures, logs and any other "
            f"evidence OUTSIDE it, in `{folder}` (create it), and cite them in the report by that path; any other file "
            "you leave in the repository makes the audit be rejected and run again.")


def ledger_help(path: str | None = None) -> str:
    """The instruction an auditor reads: where to write the ledger (its declared path) and in which format."""
    return LEDGER_HELP.replace(f"`<report>{LEDGER_SUFFIX}`", f"`{path}`" if path else f"`<report>{LEDGER_SUFFIX}`", 1)


LEDGER_HELP = (
    f"Besides the report, write the findings ledger `<report>{LEDGER_SUFFIX}` (JSON, schema `{SCHEMA}`): "
    '{"schema": "audit-findings/1", "findings": [{"id": "F1", "severity": "critical|high|medium|low", '
    '"status": "open|fixed|accepted", "summary": "...", "tasks": ["<plan task id whose result is wrong>"], '
    '"evidence": "required when fixed", "accepted_by": "owner", "reason": "required when accepted", '
    '"semantic_fingerprint": "optional lowercase sha256"}]}. '
    "semantic_fingerprint is sha256 of compact JSON [contract_id, failure_mechanism, trigger, affected_frontier] "
    "after Unicode NFKC normalization, case-folding and whitespace collapse; a frontier array is sorted and unique. "
    "List every finding you confirm. A critical or high finding left `open` rejects this audit and sends the tasks it "
    "names back to be redone. An audit is read-only: change only your report and this ledger, never source, tests or "
    "configuration (a change outside them rejects the audit). Use `fixed` only for a finding you re-checked and found "
    "already fixed in the audited tree, with the command and result as `evidence`, and never mark `accepted` "
    "yourself: only the owner accepts a risk. Another independent auditor may review the same scope: confirm and "
    "record your own findings and never assume the other one covers anything."
)


@dataclass(frozen=True)
class Policy:
    """What the gate enforces. Built from the owner's configuration (`policy_from`), never inferred from a plan."""
    blocking: tuple[str, ...] = BLOCKING_SEVERITIES   # open findings of these severities reject the audit
    ledger_required: bool = True                      # an audit without a declared ledger: reject (True) or skip
    read_only: bool = True                            # an audit may change only the files it declares (report, ledger)
    rework_scope: str = "named"                       # what a rejection sends back: "named" (+ the checks over it) | "downstream"
    remediate: bool = True                            # blocking findings become new tasks on the integrated tree (REQ-028)
    remediation_rounds: int = 2                       # rounds one audit gets before the named tasks are sent back instead


def policy_from(get) -> Policy:
    """`get(key, default)` is `bt_config.get`; invalid values fall back to the defaults."""
    severities = get("gates.audit_blocking", list(BLOCKING_SEVERITIES))
    ok = isinstance(severities, list) and severities and all(item in SEVERITIES for item in severities)
    required = get("gates.audit_ledger_required", True)
    read_only = get("gates.audit_read_only", True)
    scope = get("gates.rework_scope", "named")
    remediate = get("gates.audit_remediation", True)
    rounds = get("gates.remediation_rounds", 2)
    return Policy(tuple(severities) if ok else BLOCKING_SEVERITIES, required if isinstance(required, bool) else True,
                  read_only if isinstance(read_only, bool) else True, scope if scope in REWORK_SCOPES else "named",
                  remediate if isinstance(remediate, bool) else True,
                  rounds if isinstance(rounds, int) and not isinstance(rounds, bool) and rounds >= 0 else 2)


@dataclass(frozen=True)
class Gate:
    ok: bool
    problems: tuple[str, ...]      # the ledger is unusable (nothing can be sent back; the auditor must fix it)
    blocking: tuple[dict, ...]     # open blocking findings: {id, severity, summary, tasks, evidence}
    rework: tuple[str, ...]        # plan tasks named by blocking findings, in first-seen order

    def summary(self) -> str:
        if self.ok:
            return "audit gate: no open blocking finding"
        if self.problems:
            return "audit gate: rejected: " + "; ".join(self.problems[:5])
        ids = ", ".join(f"{f['id']} ({f['severity']})" for f in self.blocking[:12])
        return f"audit gate: {len(self.blocking)} open blocking finding(s): {ids}"

    def digest(self) -> str:
        body = json.dumps([self.ok, self.problems, self.blocking, self.rework], sort_keys=True)
        return hashlib.sha256(body.encode()).hexdigest()[:16]


def stray_changes(changed, declared) -> tuple[str, ...]:
    """The changed paths an audit may not touch: everything outside the files it declares (its report and ledger). An
    audit reports; the tasks it names are sent back to be redone. One that patches source itself hides the builder's
    defect from the router and, run beside a second auditor, hands every later task a merge conflict between the two."""
    allowed = {p.strip("/") for p in declared if isinstance(p, str)}
    return tuple(sorted(p for p in changed if isinstance(p, str) and p.strip("/") not in allowed))


def scope_problem(stray) -> str:
    shown = ", ".join(stray[:5]) + (f" and {len(stray) - 5} more" if len(stray) > 5 else "")
    return (f"the audit changed {len(stray)} file(s) it did not declare: {shown}. An audit only writes its report and "
            "ledger; leave the source as it is and record each defect as an open finding naming the task that owns it")


def ledger_path(expected_paths) -> str | None:
    """The one ledger an audit task declares among its files, or None when it declares none or several."""
    found = [p for p in expected_paths if isinstance(p, str) and p.endswith(LEDGER_SUFFIX)]
    return found[0] if len(found) == 1 else None


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _tasks(item: dict):
    return item.get("tasks", item.get("taskReferences", []))


def _status(item: dict):
    return "fixed" if item.get("status") == "closed" else item.get("status")


def _finding_problems(item: object, index: int) -> list[str]:
    where = f"findings[{index}]"
    if not isinstance(item, dict):
        return [f"{where}: not an object"]
    out = []
    if not _text(item.get("id")) or len(_text(item.get("id"))) > 40:
        out.append(f"{where}.id: missing or longer than 40")
    if item.get("severity") not in (*SEVERITIES, "info"):
        out.append(f"{where}.severity: one of {', '.join(SEVERITIES)}")
    if _status(item) not in STATUSES:
        out.append(f"{where}.status: one of {', '.join(STATUSES)}")
    if not _text(item.get("summary")):
        out.append(f"{where}.summary: missing")
    if "semantic_fingerprint" in item and (
        not isinstance(item["semantic_fingerprint"], str)
        or not SEMANTIC_FINGERPRINT.fullmatch(item["semantic_fingerprint"])
    ):
        out.append(f"{where}.semantic_fingerprint: expected 64 lowercase hexadecimal characters")
    tasks = _tasks(item)
    if not isinstance(tasks, list) or not all(isinstance(t, str) and t.strip() for t in tasks):
        out.append(f"{where}.tasks: a list of plan task ids")
    if _status(item) == "fixed" and not _text(item.get("evidence")):
        out.append(f"{where}: `fixed` needs `evidence`")
    if item.get("status") == "accepted" and not (item.get("accepted_by") == "owner" and _text(item.get("reason"))):
        out.append(f"{where}: `accepted` needs accepted_by `owner` and a `reason` (an auditor cannot waive a finding)")
    return out


def validate_ledger(data: object) -> list[str]:
    """Validate the ledger contract without judging open findings or requiring a plan."""
    if not isinstance(data, dict) or data.get("schema") != SCHEMA or not isinstance(data.get("findings"), list):
        return [f"the ledger must be an object with schema `{SCHEMA}` and a `findings` list"]
    findings = data["findings"]
    if len(findings) > MAX_FINDINGS:
        return [f"more than {MAX_FINDINGS} findings"]
    problems: list[str] = []
    if "tree_digest" in data and (not isinstance(data["tree_digest"], str) or not DIGEST.fullmatch(data["tree_digest"])):
        problems.append("tree_digest: expected sha256:<64 lowercase hex>")
    try:
        evidence_paths(data, {})
    except ValueError as error:
        problems.append(str(error))
    ids: set[str] = set()
    for index, item in enumerate(findings):
        problems += _finding_problems(item, index)
        if isinstance(item, dict):
            fid = _text(item.get("id"))
            if fid in ids:
                problems.append(f"findings[{index}].id: duplicate {fid!r}")
            ids.add(fid)
    return problems


def evaluate(raw: bytes | str | None, plan_task_ids, audit_task_id: str, policy: Policy = Policy()) -> Gate:
    """Judge a ledger. `raw` None means the file is absent from the audited snapshot."""
    if raw is None:
        return Gate(False, ("the findings ledger is missing from the audited snapshot",), (), ())
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    if len(raw) > MAX_BYTES:
        return Gate(False, (f"the findings ledger is larger than {MAX_BYTES} bytes",), (), ())
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return Gate(False, ("the findings ledger is not valid UTF-8 JSON",), (), ())
    problems = validate_ledger(data)
    if problems:
        return Gate(False, tuple(problems[:20]), (), ())
    findings = data["findings"]
    known = set(plan_task_ids)
    blocking, rework = [], []
    by_fingerprint: dict[str, int] = {}
    for item in findings:
        if item["severity"] in policy.blocking and item["status"] == "open":
            tasks = [t.strip() for t in _tasks(item) if t.strip() in known and t.strip() != audit_task_id]
            record = _blocking_record(item, tasks)
            fingerprint = record.get("semantic_fingerprint")
            if fingerprint and fingerprint in by_fingerprint:
                _merge_blocking(blocking[by_fingerprint[fingerprint]], record)
            else:
                if fingerprint:
                    by_fingerprint[fingerprint] = len(blocking)
                blocking.append(record)
            rework += [t for t in tasks if t not in rework]
    return Gate(not blocking, (), tuple(blocking), tuple(rework))


def semantic_fingerprint(contract_id: str, failure_mechanism: str, trigger: str,
                         affected_frontier: str | list[str] | tuple[str, ...]) -> str:
    """Hash NFKC, case-folded, whitespace-collapsed JSON fields; frontier lists are sorted and unique."""
    def normalize(value: str) -> str:
        return " ".join(unicodedata.normalize("NFKC", value).casefold().split())

    frontier = affected_frontier if isinstance(affected_frontier, (list, tuple)) else [affected_frontier]
    canonical = [normalize(contract_id), normalize(failure_mechanism), normalize(trigger),
                 sorted({normalize(value) for value in frontier})]
    body = json.dumps(canonical, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def evaluate_many(raw_ledgers, plan_task_ids, audit_task_id: str, policy: Policy = Policy()) -> Gate:
    """Combine independent audit ledgers; only matching explicit fingerprints merge."""
    gates = [evaluate(raw, plan_task_ids, audit_task_id, policy) for raw in raw_ledgers]
    problems = tuple(problem for gate in gates for problem in gate.problems)
    if problems:
        return Gate(False, problems[:20], (), ())
    blocking: list[dict] = []
    by_fingerprint: dict[str, int] = {}
    rework: list[str] = []
    for gate in gates:
        for record in gate.blocking:
            fingerprint = record.get("semantic_fingerprint")
            if fingerprint and fingerprint in by_fingerprint:
                _merge_blocking(blocking[by_fingerprint[fingerprint]], record)
            else:
                if fingerprint:
                    by_fingerprint[fingerprint] = len(blocking)
                blocking.append(dict(record))
            rework.extend(task for task in record["tasks"] if task not in rework)
    return Gate(not blocking, (), tuple(blocking), tuple(rework))


def _blocking_record(item: dict, tasks: list[str]) -> dict:
    evidence_refs = item.get("evidence_refs", [])
    if not isinstance(evidence_refs, list) or not all(isinstance(value, str) for value in evidence_refs):
        evidence_refs = []
    record = {"id": _text(item["id"]), "severity": item["severity"],
              "summary": _text(item["summary"])[:MAX_TEXT], "tasks": tasks,
              "evidence": _text(item.get("evidence"))[:MAX_TEXT],
              "evidence_entries": ((_text(item.get("evidence"))[:MAX_TEXT],) if _text(item.get("evidence")) else ()),
              "evidence_refs": tuple(dict.fromkeys(evidence_refs))}
    if "semantic_fingerprint" in item:
        record["semantic_fingerprint"] = item["semantic_fingerprint"]
    return record


def _merge_blocking(target: dict, other: dict) -> None:
    target["tasks"] = list(dict.fromkeys((*target["tasks"], *other["tasks"])))
    target["evidence_entries"] = tuple(dict.fromkeys((*target.get("evidence_entries", ()), *other.get("evidence_entries", ()))))
    target["evidence_refs"] = tuple(dict.fromkeys((*target.get("evidence_refs", ()), *other.get("evidence_refs", ()))))
    if not target.get("evidence") and other.get("evidence"):
        target["evidence"] = other["evidence"]


def note_for(gate: Gate, task_id: str, audit_task_id: str) -> str:
    """What a task sent back for rework must read in its next prompt: the findings that name it, or why it was reset."""
    own = [f for f in gate.blocking if task_id in f["tasks"]]
    if own:
        lines = [f"- {f['id']} ({f['severity']}): {f['summary']}"
                 + (f"\n  Evidence from the audit: {f['evidence']}" if f.get("evidence") else "") for f in own]
        return (f"The independent audit {audit_task_id} rejected the accepted result of this task. Fix these confirmed "
                "findings and prove each one with a test that exercises the real entry point, not only the module in "
                "isolation:\n" + "\n".join(lines))
    return (f"A task this one depends on was sent back by the independent audit {audit_task_id}. Redo your work on top "
            "of its new result and check it still holds end to end.")
