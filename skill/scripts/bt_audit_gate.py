"""Audit gate: an audit task passes only when its findings ledger has no open blocking finding.

A `kind: audit` task declares one `*.findings.json` among its files. The auditor writes the human report and this
machine-readable ledger beside it:

    {"schema": "audit-findings/1", "findings": [
        {"id": "F1", "severity": "critical|high|medium|low", "status": "open|fixed|accepted",
         "summary": "...", "tasks": ["T13"],                       # plan tasks whose result is wrong
         "evidence": "..." (required when fixed), "accepted_by": "owner", "reason": "..." (required when accepted)}]}

The gate reads the ledger, never the prose. Whether the report says «PARTIAL, release blocked» is irrelevant: a
critical/high finding still `open` rejects the task, a ledger that is missing or malformed rejects it, and the tasks the
findings name are sent back for rework by the Scheduler (`SchedulerCore.reject_and_rework`). Only the owner can accept a
risk; an auditor cannot waive its own finding. Standard library only; no I/O (the caller reads the file).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

LEDGER_SUFFIX = ".findings.json"
SCHEMA = "audit-findings/1"
SEVERITIES = ("critical", "high", "medium", "low")
BLOCKING_SEVERITIES = ("critical", "high")     # the default policy; `bt_config` `gates.audit_blocking` overrides it
STATUSES = ("open", "fixed", "accepted")
MAX_BYTES = 1 << 20
MAX_FINDINGS = 200
MAX_TEXT = 600

def ledger_help(path: str | None = None) -> str:
    """The instruction an auditor reads: where to write the ledger (its declared path) and in which format."""
    return LEDGER_HELP.replace(f"`<report>{LEDGER_SUFFIX}`", f"`{path}`" if path else f"`<report>{LEDGER_SUFFIX}`", 1)


LEDGER_HELP = (
    f"Besides the report, write the findings ledger `<report>{LEDGER_SUFFIX}` (JSON, schema `{SCHEMA}`): "
    '{"schema": "audit-findings/1", "findings": [{"id": "F1", "severity": "critical|high|medium|low", '
    '"status": "open|fixed|accepted", "summary": "...", "tasks": ["<plan task id whose result is wrong>"], '
    '"evidence": "required when fixed", "accepted_by": "owner", "reason": "required when accepted"}]}. '
    "List every finding you confirm. A critical or high finding left `open` rejects this audit and sends the tasks it "
    "names back to be redone; use `fixed` only when your own change AND a regression test prove it, and never mark "
    "`accepted` yourself: only the owner accepts a risk."
)


@dataclass(frozen=True)
class Policy:
    """What the gate enforces. Built from the owner's configuration (`policy_from`), never inferred from a plan."""
    blocking: tuple[str, ...] = BLOCKING_SEVERITIES   # open findings of these severities reject the audit
    ledger_required: bool = True                      # an audit without a declared ledger: reject (True) or skip


def policy_from(get) -> Policy:
    """`get(key, default)` is `bt_config.get`; invalid values fall back to the defaults."""
    severities = get("gates.audit_blocking", list(BLOCKING_SEVERITIES))
    ok = isinstance(severities, list) and severities and all(item in SEVERITIES for item in severities)
    required = get("gates.audit_ledger_required", True)
    return Policy(tuple(severities) if ok else BLOCKING_SEVERITIES, required if isinstance(required, bool) else True)


@dataclass(frozen=True)
class Gate:
    ok: bool
    problems: tuple[str, ...]      # the ledger is unusable (nothing can be sent back; the auditor must fix it)
    blocking: tuple[dict, ...]     # open critical/high findings: {id, severity, summary, tasks}
    rework: tuple[str, ...]        # plan tasks named by blocking findings, in first-seen order

    def summary(self) -> str:
        if self.ok:
            return "audit gate: no open blocking finding"
        if self.problems:
            return "audit gate: ledger unusable: " + "; ".join(self.problems[:5])
        ids = ", ".join(f"{f['id']} ({f['severity']})" for f in self.blocking[:12])
        return f"audit gate: {len(self.blocking)} open blocking finding(s): {ids}"

    def digest(self) -> str:
        body = json.dumps([self.ok, self.problems, self.blocking, self.rework], sort_keys=True)
        return hashlib.sha256(body.encode()).hexdigest()[:16]


def ledger_path(expected_paths) -> str | None:
    """The one ledger an audit task declares among its files, or None when it declares none or several."""
    found = [p for p in expected_paths if isinstance(p, str) and p.endswith(LEDGER_SUFFIX)]
    return found[0] if len(found) == 1 else None


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _finding_problems(item: object, index: int) -> list[str]:
    where = f"findings[{index}]"
    if not isinstance(item, dict):
        return [f"{where}: not an object"]
    out = []
    if not _text(item.get("id")) or len(_text(item.get("id"))) > 40:
        out.append(f"{where}.id: missing or longer than 40")
    if item.get("severity") not in SEVERITIES:
        out.append(f"{where}.severity: one of {', '.join(SEVERITIES)}")
    if item.get("status") not in STATUSES:
        out.append(f"{where}.status: one of {', '.join(STATUSES)}")
    if not _text(item.get("summary")):
        out.append(f"{where}.summary: missing")
    tasks = item.get("tasks", [])
    if not isinstance(tasks, list) or not all(isinstance(t, str) and t.strip() for t in tasks):
        out.append(f"{where}.tasks: a list of plan task ids")
    if item.get("status") == "fixed" and not _text(item.get("evidence")):
        out.append(f"{where}: `fixed` needs `evidence`")
    if item.get("status") == "accepted" and not (item.get("accepted_by") == "owner" and _text(item.get("reason"))):
        out.append(f"{where}: `accepted` needs accepted_by `owner` and a `reason` (an auditor cannot waive a finding)")
    return out


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
    if not isinstance(data, dict) or data.get("schema") != SCHEMA or not isinstance(data.get("findings"), list):
        return Gate(False, (f"the ledger must be an object with schema `{SCHEMA}` and a `findings` list",), (), ())
    findings = data["findings"]
    if len(findings) > MAX_FINDINGS:
        return Gate(False, (f"more than {MAX_FINDINGS} findings",), (), ())
    problems: list[str] = []
    ids: set[str] = set()
    for index, item in enumerate(findings):
        problems += _finding_problems(item, index)
        if isinstance(item, dict):
            fid = _text(item.get("id"))
            if fid in ids:
                problems.append(f"findings[{index}].id: duplicate {fid!r}")
            ids.add(fid)
    if problems:
        return Gate(False, tuple(problems[:20]), (), ())
    known = set(plan_task_ids)
    blocking, rework = [], []
    for item in findings:
        if item["severity"] in policy.blocking and item["status"] == "open":
            tasks = [t.strip() for t in item.get("tasks", []) if t.strip() in known and t.strip() != audit_task_id]
            blocking.append({"id": _text(item["id"]), "severity": item["severity"],
                             "summary": _text(item["summary"])[:MAX_TEXT], "tasks": tasks})
            rework += [t for t in tasks if t not in rework]
    return Gate(not blocking, (), tuple(blocking), tuple(rework))


def note_for(gate: Gate, task_id: str, audit_task_id: str) -> str:
    """What a task sent back for rework must read in its next prompt: the findings that name it, or why it was reset."""
    own = [f for f in gate.blocking if task_id in f["tasks"]]
    if own:
        lines = [f"- {f['id']} ({f['severity']}): {f['summary']}" for f in own]
        return (f"The independent audit {audit_task_id} rejected the accepted result of this task. Fix these confirmed "
                "findings and prove each one with a test that exercises the real entry point, not only the module in "
                "isolation:\n" + "\n".join(lines))
    return (f"A task this one depends on was sent back by the independent audit {audit_task_id}. Redo your work on top "
            "of its new result and check it still holds end to end.")
