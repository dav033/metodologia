"""The model-authored half of the structural recovery (REQ-029 R3/R4/R8/R12, P-152): who may diagnose, what the model reads, and
what comes back as a validated revision.

Nothing here runs a run. It takes a target (an exhausted audit stop), exports and collects its evidence (`bt_recovery_export`,
`bt_recovery_evidence`), shows the model a bounded view of it, parses the answer as UNTRUSTED data and hands it to the compiler
(`bt_recovery_compiler`), which is the only thing that can turn it into a plan revision. A failure at any step is a
`Blocked(code, detail)`: one diagnosis per cycle, the exact blocker is recorded, the owner decides.

The model view is not the evidence. The full record is megabytes (the snapshot ledger alone lists every file of the tree), so the model
reads the failing checks, the audit's findings, the plan tasks involved and the digests it must cite; the compiler binds to the full
record by those digests.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

EXHAUSTED = ("rework_limit", "rework_impact")
MAX_OWNERS = 8                       # the cycle's corrective-task allowance (R14); a wider finding set is the owner's call
NARRATIVE_BYTES = 60 * 1024
PLAN_TASK_BYTES = 120 * 1024
CHECKS_BYTES = 80 * 1024

PROMPT = """You are the Planner role diagnosing why an automated run's independent audit keeps rejecting the same work.
You have NO tools and NO connectors: use only the evidence below. Do not run or suggest running anything on your own: the commands
you write are text that a later, separately authorized step validates and runs in a sandbox. Do not answer any owner decision.
Reply with ONE JSON object and nothing else (schema recovery-proposal/1):

{{"schema_version": "recovery-proposal/1",
  "confidence": "confirmed" | "reported",          // confirmed = the evidence shows it; reported = the evidence says it; never guess
  "causal_history": "what the previous corrections changed, which findings persisted, were fixed, appeared or regressed",
  "evidence_refs": ["m6:<sha256>", ...],            // copy from `refs` below the ones you relied on, nothing else
  "actions": [
    {{"type": "correct_tasks", "owner_task_id": "T4", "task_ids": ["T4"],
      "replacements": [{{"id": "T4", "objective": "…new objective that fixes the cause…", "acceptance_criteria": ["every old one, plus new"],
                        "verification": [ every existing check unchanged, plus new {{"type": "command", "value": "python3 -m unittest tests.test_x",
                                         "purpose": "…", "category": "regression", "created_by": "T4"}} ]}}]}},
    {{"type": "repair_verification", "owner_task_id": "T4", "task_ids": ["T4"],
      "verification": [{{"type": "command", "value": "…", "purpose": "…", "category": "regression", "created_by": "T4"}}]}},
    {{"type": "refresh_integrated_audit", "owner_task_id": "<the audit task>", "after": ["T4"]}} ],
  "symptom_oracle": {{"symptom": "one sentence: the observable failure", "red_command": "a command that FAILS on the broken source",
                     "command": "the same behaviour as a command that PASSES once corrected"}} }}

Rules the validator enforces (a proposal that breaks one is refused whole, and you get no second try):
- only these three action types; every task id must exist in the plan below; `task_ids` must stay inside `owner_task_id`'s paths;
- a replacement keeps the task's kind, repository, milestone, `covers`, `expected_paths`, `shared_resources` and every existing
  acceptance criterion and verification check unchanged; it may only add criteria and checks;
- every NEW check is `{{"type": "command", ...}}` with a `purpose` (the criterion it proves, in its words), a `category` (one of static,
  functional, integration, regression, product: the plan is refused without it) and `created_by` = the task id it belongs to, one argv: no pipes, `;`, `&&`, `||`,
  redirections, backticks or `$(`; never `sh -c`, `python -c`, `rm`, `sudo`; audits cannot be replaced;
- name an action for EVERY task that owns a changed path listed in `changed_paths`; at most {limit} tasks in total;
- `symptom_oracle` is mandatory and falsifiable: `red_command` must reproduce the failure and `command` must prove the fix.
If the evidence cannot support a diagnosis, set "confidence" to "unknown" and "actions" to []: that is an honest answer.

Request identity: {identity}

Evidence ({count} sections, in order):
{sections}
"""


CONFLICT_PROMPT = """You are the Planner role judging an integration clash that an automated run could not settle by redoing one task over the
other. Two accepted tasks each changed the same files; a third task needs both. You have NO tools and NO connectors: use only the
evidence below. Do not run anything: the commands you write are validated and run later in a sandbox. Do not answer any owner decision.
Reply with ONE JSON object and nothing else (schema recovery-proposal/1):

{{"schema_version": "recovery-proposal/1",
  "confidence": "confirmed" | "reported",
  "causal_history": "why the two results overlap and what each is trying to do",
  "semantic_conflict": false,                        // true ONLY when the two requirements cannot both hold: then say which below
  "incompatible_requirements": [],                   // texts of the requirements that exclude each other (only when semantic_conflict)
  "evidence_refs": ["m6:<sha256>", ...],             // copy from `refs` below the ones you relied on
  "symptom_oracle": {{"symptom": "one sentence: the behaviour that needs BOTH sides",
                     "path": "one of the clashing files this check exercises",
                     "red_command": "a command that FAILS on an accepted side alone (it lacks the other side's behaviour)",
                     "command": "the same behaviour as a command that PASSES once both requirements hold"}}}}

Rules (a proposal that breaks one is refused whole and you get no second try):
- commands: one argv, no pipes, `;`, `&&`, `||`, redirections, backticks or `$(`; never `sh -c`, `python -c`, `rm`, `sudo`; they must
  already exist in the repository at the accepted sides or be runnable from it (an existing test file, a module call);
- `red_command` is executed on each accepted side: if it does not FAIL like a test fails (exit non-zero) on one of them, the cycle stops;
- "semantic_conflict" is a product judgement: set it only when satisfying one requirement necessarily breaks the other.
If the evidence cannot support a judgement, set "confidence" to "unknown": that is an honest answer.

Request identity: {identity}

Evidence ({count} sections, in order):
{sections}
"""


class Blocked(Exception):
    """The cycle cannot go on: `code` is the durable, exact reason shown on the plan page."""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code, self.detail = code, detail[:300]


def route(project: str) -> dict[str, Any] | None:
    """The Planner-role route: the diagnosing profile and model (`diagnosis.*`), only when its profile may run this project. The
    authorization reference names the check that was made; None when there is nothing authorized to ask."""
    import bt_block_agent
    import bt_profiles

    config = bt_block_agent.settings()
    profile, model = config.get("profile"), config.get("model")
    if not isinstance(profile, str) or not profile or not isinstance(model, str) or not model:
        return None
    try:
        provider = bt_profiles.get(profile)["provider"]
        bt_profiles.authorize(profile, project)
    except (bt_profiles.ProfileError, KeyError, ValueError):
        return None
    ref = f"profile:{profile}@{project}"
    return {"role": "planner", "verified": True, "provider": provider, "profile": profile, "model": model,
            "effort": config.get("effort") or None, "authorized_by": ref, "authorization_ref": ref, "decision_ref": ref}


def target(rdir: Path, requests: list[dict]) -> dict[str, Any] | None:
    """The exhausted audit stop the cycle is about, with the tasks its findings name (the owners to correct)."""
    import bt_scheduler_decisions as decisions

    for request in requests:
        code = decisions.reason_code(str(request.get("reason") or ""))
        if code not in EXHAUSTED or request.get("source") != "task" or not request.get("attempt"):
            continue
        named: list[str] = []
        for option in request.get("options") or ():
            if option.get("id") == "rework_findings":
                named = [name for name in str(option.get("target") or "").split(",") if name]
        return {"kind": "audit", "request": request["id"], "task": request["task"], "attempt": request["attempt"], "reason": code,
                "named": named}
    return conflict_target(rdir, requests)


def conflict_target(rdir: Path, requests: list[dict]) -> dict[str, Any] | None:
    """A task stopped by an integration clash the ordinary redo gave up on: the two accepted tasks and ALL the paths (recorded
    when the clash happened, never clipped)."""
    import bt_recovery_lineage as lineage

    for request in requests:
        if request.get("source") != "task" or not request.get("task"):
            continue
        text = " ".join(str(request.get(key) or "") for key in ("error", "reason", "what")) + " ".join(
            str(e) for e in request.get("evidence") or ())
        if "INTEGRATION_CONFLICT" not in text and (request.get("diagnosis") or {}).get("kind") != "conflict":
            continue
        row = lineage.latest_conflict(rdir, request["task"])
        if row is None:
            continue
        return {"kind": "conflict", "request": request["id"], "task": request["task"], "attempt": request.get("attempt") or "",
                "reason": "integration_conflict", "named": [row["left"], row["right"]], "left": row["left"], "right": row["right"],
                "files": sorted(set(row["files"]))}
    return None


def _git(repo: str, *args: str) -> str:
    done = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, timeout=60, check=False)
    if done.returncode:
        raise Blocked("evidence_unavailable", f"git {args[0]}: {(done.stderr or done.stdout).strip()[:120]}")
    return done.stdout


def changed_paths(rdir: Path, named: list[str]) -> list[str]:
    """What the named tasks changed: the paths between each accepted attempt's base and snapshot (the manifest lists are clipped,
    git is not). A path another task also changed is listed once."""
    import bt_recovery_export as export
    import bt_scheduler_decisions as decisions

    doc = decisions._state(rdir)
    found: list[str] = []
    for task_id in named:
        rec = (doc.get("tasks") or {}).get(task_id) or {}
        attempts = rec.get("attempts") or []
        accepted = next((a for a in reversed(attempts) if (doc.get("attempts") or {}).get(a, {}).get("state") == "accepted"), None)
        if accepted is None:
            continue
        manifest = json.loads(export._manifest_path(rdir, accepted).read_text(encoding="utf-8"))
        base, snapshot, repo = manifest.get("base_sha"), manifest.get("snapshot_sha"), manifest.get("repository")
        if not (base and snapshot and repo):
            raise Blocked("evidence_unavailable", f"the manifest of {accepted} lacks its base, snapshot or repository")
        for line in _git(repo, "diff", "--name-only", "--no-renames", base, snapshot).splitlines():
            if line and line not in found:
                found.append(line)
    return found


def _clip(value: Any, limit: int) -> Any:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value if len(text.encode("utf-8")) <= limit else {"clipped": True, "bytes": len(text.encode("utf-8")),
                                                                "head": text[:limit // 4]}


def model_view(rdir: Path, evidence: dict, goal: dict, paths: list[str]) -> dict[str, Any]:
    """The bounded document the model reads. The digests in `refs` are what its answer may cite."""
    import bt_scheduler_decisions as decisions

    sources = evidence["sources"]
    refs = {name: f"{name}:{sources[name]['sha256']}" for name in ("m1", "plan", "m6", "remediation", "m3_manifest")}
    plan = sources["plan"]["document"]
    involved = {goal["task"], *goal["named"]}
    tasks = [t for t in plan.get("tasks", []) if isinstance(t, dict) and t.get("id") in involved]
    request = next((r for r in decisions.open_requests(rdir) if r["id"] == goal["request"]), None)
    narrative = decisions.evidence(rdir, request)[:NARRATIVE_BYTES] if request else ""
    m6 = sources["m6"]["document"]
    view = {"diagnosable": True, "evidence_sha256": hashlib.sha256(json.dumps(
                {k: v["sha256"] for k, v in sources.items()}, sort_keys=True).encode()).hexdigest(),
            "identity": evidence["identity"], "refs": refs, "stop": {k: goal[k] for k in ("request", "task", "attempt", "reason")},
            "tasks_named_by_the_findings": goal["named"], "changed_paths": paths,
            "plan_tasks_involved": _clip(tasks, PLAN_TASK_BYTES),
            "verdict_of_the_failed_attempt": {"status": m6["result"].get("status"), "issues": m6["result"].get("issues"),
                                             "checks": _clip(m6.get("checks"), CHECKS_BYTES)},
            "what_the_owner_would_read": narrative,
            "prior_remediation": _clip(sources["remediation"]["document"].get("events"), 30 * 1024)}
    return view


def parse(raw: bytes) -> dict[str, Any]:
    """The model's answer as data. Anything but one JSON object with the schema is a refusal, never a repair of the text."""
    try:
        proposal = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as error:
        raise Blocked("proposal_invalid", f"not JSON: {error}") from error
    if not isinstance(proposal, dict) or proposal.get("schema_version") != "recovery-proposal/1":
        raise Blocked("proposal_invalid", "not a recovery-proposal/1 object")
    if proposal.get("confidence") not in ("confirmed", "reported") or not proposal.get("actions"):
        raise Blocked("diagnosis_inconclusive", f"the model's confidence is {proposal.get('confidence')!r}")
    if not isinstance(proposal.get("actions"), list) or len(proposal["actions"]) > MAX_OWNERS * 3:
        raise Blocked("proposal_invalid", "too many actions")
    return proposal


def diagnose(project: str, rdir: Path, goal: dict, route_: dict, cycle_dir: Path, *, runner=None, probe_runner=None,
             home: Path | None = None, timeout_seconds: int = 300) -> tuple[dict, dict, dict]:
    """(evidence, proposal, paths) for one target, or raises Blocked. One model invocation per cycle (the transport enforces it)."""
    import bt_block_agent
    import bt_recovery_evidence as evidence_mod
    import bt_recovery_export as export

    if not goal["named"]:
        raise Blocked("findings_unnamed", "the audit's stop names no task to correct")
    if len(goal["named"]) > MAX_OWNERS:
        raise Blocked("findings_too_broad", f"the findings span {len(goal['named'])} tasks; a cycle corrects at most {MAX_OWNERS}")
    try:
        audit, attempt = export.export(rdir, goal["task"], goal["attempt"])
    except export.ExportError as error:
        raise Blocked("evidence_unavailable", str(error)) from error
    evidence = evidence_mod.collect_recovery_evidence(rdir, audit, attempt)
    if evidence.get("diagnosable") is not True:
        raise Blocked("evidence_unavailable", "; ".join(evidence.get("validation_problems") or ["not diagnosable"]))
    paths = changed_paths(rdir, goal["named"])
    if not paths:
        raise Blocked("evidence_unavailable", "the named tasks changed no path")
    view = model_view(rdir, evidence, goal, paths)
    answer = bt_block_agent.diagnose_recovery(
        project, view, {"run": rdir.name, "request": goal["request"], "attempt": goal["attempt"], "evidence": view["evidence_sha256"]},
        route_, store=cycle_dir, timeout_seconds=timeout_seconds, runner=runner, probe_runner=probe_runner, home=home,
        prompt=PROMPT.replace("{limit}", str(MAX_OWNERS)))
    if answer["outcome"] != "ok":
        raise Blocked(f"diagnosis_{answer['outcome']}", str(answer.get("blocker") or ""))
    return evidence, parse(answer["raw"]), {"paths": paths, "view": view}


def parse_conflict(raw: bytes) -> dict[str, Any]:
    """The model's judgement and oracle, as data: the shape is checked, the command safety is the compiler's job."""
    try:
        body = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as error:
        raise Blocked("proposal_invalid", f"not JSON: {error}") from error
    if not isinstance(body, dict) or body.get("schema_version") != "recovery-proposal/1":
        raise Blocked("proposal_invalid", "not a recovery-proposal/1 object")
    if body.get("confidence") not in ("confirmed", "reported"):
        raise Blocked("diagnosis_inconclusive", f"the model's confidence is {body.get('confidence')!r}")
    oracle = body.get("symptom_oracle")
    if not isinstance(oracle, dict) or any(not isinstance(oracle.get(k), str) or not oracle[k].strip()
                                           for k in ("symptom", "path", "red_command", "command")):
        raise Blocked("proposal_invalid", "the symptom oracle is incomplete")
    refs = body.get("evidence_refs")
    if not isinstance(refs, list) or any(not isinstance(r, str) for r in refs):
        raise Blocked("proposal_invalid", "evidence_refs must be a list of references")
    incompatible = body.get("incompatible_requirements") or []
    if not isinstance(incompatible, list) or any(not isinstance(x, str) for x in incompatible):
        raise Blocked("proposal_invalid", "incompatible_requirements must be a list of texts")
    if body.get("semantic_conflict") is True:
        raise Blocked("incompatible_requirements", "; ".join(x.strip() for x in incompatible if x.strip())[:240] or
                      "the model judges the two requirements incompatible")
    return {"oracle": {k: oracle[k].strip() for k in ("symptom", "path", "red_command", "command")}, "refs": refs,
            "semantic": {"semantic_conflict": False, "incompatible_requirements": []}}


def diagnose_conflict(project: str, rdir: Path, goal: dict, route_: dict, cycle_dir: Path, *, runner=None, probe_runner=None,
                      home: Path | None = None, timeout_seconds: int = 300) -> tuple[dict, dict, dict]:
    """(evidence, judgement, extra) for an integration clash: the facts are derived, the model judges and writes the oracle."""
    import bt_block_agent
    import bt_recovery_evidence as evidence_mod
    import bt_recovery_export as export
    import bt_recovery_lineage as lineage

    row = lineage.latest_conflict(rdir, goal["task"])
    if row is None:
        raise Blocked("evidence_unavailable", "the clash was not recorded with its paths")
    facts = lineage.gather(rdir, project, row)
    side = facts["sides"][0]
    try:
        audit, attempt = export.export(rdir, side["task_id"], side["attempt_id"], accepted=True)
    except export.ExportError as error:
        raise Blocked("evidence_unavailable", str(error)) from error
    evidence = evidence_mod.collect_recovery_evidence(rdir, audit, attempt, states=("accepted",))
    if evidence.get("diagnosable") is not True:
        raise Blocked("evidence_unavailable", "; ".join(evidence.get("validation_problems") or ["not diagnosable"]))
    shown = lineage.view(facts)
    shown.update({"diagnosable": True, "refs": {n: f"{n}:{evidence['sources'][n]['sha256']}"
                                                for n in ("m1", "plan", "m6", "remediation", "m3_manifest")},
                  "evidence_sha256": hashlib.sha256(json.dumps({k: v["sha256"] for k, v in evidence["sources"].items()},
                                                               sort_keys=True).encode()).hexdigest()})
    answer = bt_block_agent.diagnose_recovery(
        project, shown, {"run": rdir.name, "request": goal["request"], "clash": goal["files"][:8], "evidence": shown["evidence_sha256"]},
        route_, store=cycle_dir, timeout_seconds=timeout_seconds, runner=runner, probe_runner=probe_runner, home=home,
        prompt=CONFLICT_PROMPT)
    if answer["outcome"] != "ok":
        raise Blocked(f"diagnosis_{answer['outcome']}", str(answer.get("blocker") or ""))
    judgement = parse_conflict(answer["raw"])
    if judgement["oracle"]["path"] not in facts["files"]:
        raise Blocked("proposal_invalid", "the oracle's path is not one of the clashing files")
    return evidence, judgement, {"paths": facts["files"], "facts": facts, "view": shown}


def compile_conflict(evidence: dict, judgement: dict, extra: dict, project: str):
    """The plan revision with the convergence writer, or Blocked: the oracle is run red on an accepted side first."""
    import bt_recovery_compiler as compiler
    import bt_recovery_compiler_verification as cv
    import bt_recovery_lineage as lineage
    import bt_recovery_oracle as runner

    facts = extra["facts"]
    work = lineage.convergence_work(facts, judgement["oracle"], judgement["semantic"], runner.policy_for(project))
    proposal = lineage.synthesized_proposal(facts, judgement["oracle"], judgement["refs"])
    plan = evidence["sources"]["plan"]["document"]
    try:
        compiled = compiler.compile_recovery_revision(plan, {**evidence, "changed_paths": list(extra["paths"])}, proposal,
                                                       convergence=work)
    except cv.RecoveryCompilationError as error:
        raise Blocked("proposal_rejected", f"{error.code}: {error.reason}") from error
    return compiled, proposal


def compile_revision(evidence: dict, proposal: dict, paths: list[str]):
    """The validated plan revision, or Blocked with the compiler's own code. Only this turns a model's text into a plan."""
    import bt_recovery_compiler as compiler
    import bt_recovery_compiler_verification as cv

    plan = evidence["sources"]["plan"]["document"]
    try:
        return compiler.compile_recovery_revision(plan, {**evidence, "changed_paths": list(paths)}, proposal)
    except cv.RecoveryCompilationError as error:
        raise Blocked("proposal_rejected", f"{error.code}: {error.reason}") from error


_ID = re.compile(r"[A-Za-z0-9._:@-]{1,128}")


def proposal_hash(proposal: dict) -> str:
    return hashlib.sha256(json.dumps(proposal, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
