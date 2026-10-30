"""Auditor port: milestone audits in the durable runtime (REQ-030 item 4), with the legacy gate's own rules.

An accepted `kind: audit` task is judged by its findings ledger(s) at the audited snapshot, exactly as the legacy quality
port does it: `bt_audit_gate.evaluate_many` (open critical/high findings block; a missing or malformed ledger is a
problem of the audit itself) and, with `gates.audit_read_only`, `stray_changes` (an audit may change only the files it
declares). Blocking findings are not sent back one task at a time: `bt_remediation`'s grouping puts findings that name
the same task or overlapping paths together (at most `MAX_PER_TASK` per repair), and each group becomes ONE coordinated
repair — a new round of the first task the group names, whose brief lists every finding of the group with the probes
that reproduce them (the named tasks' own verification commands). The run workflow then runs the audit again.

The judgement is a pure function of the snapshot, the frozen plan and the operator's policy, and it runs inside one
DBOS step, so a recovered run replays the same repairs.
"""
from __future__ import annotations

import json
import subprocess
from collections.abc import Callable, Mapping
from pathlib import Path

from bt_contracts.execution import RunRef

from ..legacy import Plan, TaskSpec, audit_gate, audit_policy, remediation_groups

REPAIR_PREFIX = "REMEDIATION"            # what the brief of a coordinated repair starts with


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-C", str(repo), *args], capture_output=True,
                          check=False)


class AuditGate:
    def __init__(self, repositories_for: Callable[[str], Mapping[str, Path] | Callable[[str], Path | None]]):
        self.repositories_for = repositories_for

    def _repo(self, run: RunRef, role: str) -> Path:
        repos = self.repositories_for(run.project)
        found = repos(role) if callable(repos) else repos.get(role)
        if not found:
            raise RuntimeError(f"REPOSITORY_UNKNOWN: {role}")
        return Path(found)

    def judge(self, run: RunRef, plan: Plan, task: TaskSpec, snapshot_sha: str, *, base_sha: str = "") -> dict:
        """{"audit": False} for any other task; otherwise {ok, problems, blocking, repairs, remediate, rounds}."""
        if task.meta.get("kind") != "audit":
            return {"audit": False}
        policy = audit_policy()
        ledgers = [p for p in task.expected_paths if isinstance(p, str) and p.endswith(audit_gate.LEDGER_SUFFIX)]
        base = {"audit": True, "remediate": policy.remediate, "rounds": policy.remediation_rounds,
                "ledgers": ledgers, "blocking": [], "repairs": []}
        if not ledgers:
            if policy.ledger_required:                   # a plan defect: running the audit again cannot fix it
                return {**base, "ok": False, "structural": True,
                        "problems": [f"an audit task must declare at least one *{audit_gate.LEDGER_SUFFIX} file"]}
            return {**base, "ok": True, "problems": [], "skipped": "no ledger declared"}
        repo = self._repo(run, task.repository)
        raw = []
        for path in ledgers:
            shown = _git(repo, "show", f"{snapshot_sha}:{path}")
            raw.append(shown.stdout if shown.returncode == 0 else None)
        gate = audit_gate.evaluate_many(raw, [t.id for t in plan.tasks], task.id, policy)
        problems = list(gate.problems)
        if policy.read_only and not problems:
            # the audit's own changes: from the commit its attempt started from (an audit that changed nothing has
            # that commit as its snapshot, and the snapshot's parent would show someone else's work)
            changed = _git(repo, "diff", "--name-only", base_sha or f"{snapshot_sha}^1", snapshot_sha)
            stray = audit_gate.stray_changes(changed.stdout.decode().splitlines(), task.expected_paths) \
                if changed.returncode == 0 else ()
            if stray:
                problems.append(audit_gate.scope_problem(stray))
        blocking = [_plain(item) for item in gate.blocking]
        # a blocking finding that names only this audit is a gap in the audit's own coverage (pictures REQ-021 r27 T2.7
        # F8: «T2.7 must be rerun», its capture harness failed on one route): no other task can repair it, so it is a
        # problem of the audit, which runs again told what to complete, within the same rounds (D-234)
        own = coverage_findings(raw, [t.id for t in plan.tasks], task.id, policy) if not gate.problems else set()
        coverage = [item for item in blocking if not item.get("tasks") and item["id"] in own]
        problems += [_coverage_problem(task.id, item) for item in coverage]
        out = {**base, "ok": gate.ok and not problems, "problems": problems[:20], "blocking": blocking,
               "summary": gate.summary()}
        if coverage:
            out["coverage"] = [item["id"] for item in coverage]
        if blocking and not problems:
            out["repairs"] = repairs(plan, task.id, blocking)
        return out


def coverage_findings(raw_ledgers, plan_task_ids, audit_id: str, policy) -> set[str]:
    """Ids of the open blocking findings whose tasks name this audit and no other task of the plan (`bt_audit_gate`
    drops the audit's own id from a finding's tasks, so such a finding reaches the gate with no task at all)."""
    known = set(plan_task_ids) - {audit_id}
    out: set[str] = set()
    for raw in raw_ledgers:
        try:
            data = json.loads(raw.decode("utf-8") if isinstance(raw, bytes) else raw or "null")
        except (UnicodeDecodeError, ValueError):
            continue
        for item in (data.get("findings") or ()) if isinstance(data, dict) else ():
            if not isinstance(item, dict) or item.get("severity") not in policy.blocking or item.get("status") != "open":
                continue
            names = {str(name).strip() for name in item.get("tasks", item.get("taskReferences")) or ()}
            if audit_id in names and not names & known:
                out.add(str(item.get("id") or "").strip())
    return out


def _coverage_problem(audit_id: str, finding: Mapping) -> str:
    evidence = f" Its evidence: {finding['evidence']}" if finding.get("evidence") else ""
    return (f"finding {finding['id']} ({finding['severity']}) names only this audit ({audit_id}): it is a gap in the "
            "audit's own coverage, not a defect another task can repair. Complete what it says is missing in this run "
            f"and record its real status: {finding['summary']}{evidence}")[:1500]


def _plain(record: Mapping) -> dict:
    return {key: list(value) if isinstance(value, tuple) else value for key, value in record.items()}


def repairs(plan: Plan, audit_id: str, blocking: list[dict]) -> list[dict]:
    """The coordinated repairs of `blocking`, in order: [{owner, findings, note}]. A finding that names no task of the
    plan has no owner: it yields {owner: "", findings, note} and the run asks the owner instead of guessing."""
    order = [t.id for t in plan.tasks]
    tasks = {t.id: {"expected_paths": list(t.expected_paths)} for t in plan.tasks}
    out = []
    for chain in remediation_groups(list(blocking), tasks):
        for chunk in chain:
            named = sorted({name for finding in chunk for name in finding.get("tasks") or () if name in tasks},
                           key=order.index)
            owner = named[0] if named else ""
            probes = list(dict.fromkeys(str(check.get("value")) for name in named
                                        for check in plan.task(name).verification
                                        if check.get("type") == "command" and check.get("value")))
            out.append({"owner": owner, "findings": [finding["id"] for finding in chunk], "named": named,
                        "note": _note(audit_id, chunk, named, probes)})
    return out


def _note(audit_id: str, chunk: list[dict], named: list[str], probes: list[str]) -> str:
    lines = [(f"{REPAIR_PREFIX}. The independent audit {audit_id} confirmed these related defects in accepted work "
             f"({', '.join(named) or 'no plan task named'}). Fix ALL of them in this one change, on the integrated tree "
             "you start from (it holds the audited work and the audit's report). Do not weaken, skip or remove any "
             "check; prove each fix with a test that exercises the real entry point.")]
    if probes:
        lines.append("Probes that reproduce them (run each before and after your change):")
        lines += [f"- `{probe}`" for probe in probes]
    lines.append("Findings:")
    for finding in chunk:
        evidence = f"\n  Evidence from the audit: {finding['evidence']}" if finding.get("evidence") else ""
        lines.append(f"- {finding['id']} ({finding['severity']}): {finding['summary']}{evidence}")
    return "\n".join(lines)[:6000]
