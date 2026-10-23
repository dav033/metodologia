"""The only place where the methodology touches the planner module (`bt_planner`).

Dependency direction: methodology -> this adapter -> bt_planner. The module knows nothing about the methodology; the
methodology-specific meaning (which PLAN.md status words mean "approved", how a requirement folder maps to a plan id,
what to do on a launch) lives here. No other file may import `bt_planner` (test_plan_integration enforces it).
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import bt_planner as planner
from bt_plan_adapter_evidence import verify_command
from bt_planner import cli as planner_cli
from bt_planner import contract as planner_contract
from bt_planner import quality as planner_quality
from bt_planner import revisions as planner_revisions

# What the methodology calls an approved plan; the module itself only has a default for these words.
APPROVED_STATES = ("approved", "launched", "done", "merged")
PLAN_SCHEMA_CONSUMER_GATE_SINCE = (1, 2, 0)
_SCHEMA_VERSION_RE = re.compile(r"([0-9]+)\.([0-9]+)\.([0-9]+)")


def _schema_version(plan_path: Path) -> tuple[str, tuple[int, int, int]] | None:
    """Read only the version marker; the Planner contract validates the whole document at every action gate."""
    try:
        plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError, RecursionError):
        return None
    if not isinstance(plan, dict):
        return None
    value = plan.get("schema_version")
    match = _SCHEMA_VERSION_RE.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        return None
    try:
        version = tuple(int(match.group(index)) for index in (1, 2, 3))
    except ValueError:
        return None
    return value, version


def plan_schema_version(plan_path: Path) -> str | None:
    """Return a syntactically valid version marker; the Planner owns full contract validation."""
    version = _schema_version(plan_path)
    return version[0] if version is not None else None


def validate_candidate(plan: object) -> tuple[str, ...]:
    """Validate an in-memory plan revision through the Planner contract without filesystem effects."""
    report = planner.validate(plan)
    return tuple(report.errors)

def second_auditor_required(plan: object) -> bool:
    """Expose the owner cross-check gate to pure plan transformations."""
    if not isinstance(plan, dict) or not isinstance(plan.get("schema_version"), str):
        return False
    match = _SCHEMA_VERSION_RE.fullmatch(plan["schema_version"])
    if match is None or tuple(int(match.group(index)) for index in (1, 2, 3)) < PLAN_SCHEMA_CONSUMER_GATE_SINCE:
        return False
    import bt_config
    return bool(bt_config.get("gates.second_auditor", True))


def plan_schema_version_details(plan_path: Path) -> tuple[str, tuple[int, int, int]] | None:
    """Return the syntactically valid version and parsed components for downstream compatibility checks."""
    return _schema_version(plan_path)


def second_auditor_problem(plan_path: Path) -> str | None:
    """Owner policy `gates.second_auditor` (default on): a plan with an audit needs an independent cross-check audit, so
    one auditor's omissions cannot decide the outcome. Schema 1.2.0 plans only; the planner only warns, the policy is
    configuration, so it lives here."""
    version = _schema_version(plan_path)
    if version is None or version[1] < PLAN_SCHEMA_CONSUMER_GATE_SINCE:
        return None
    try:
        import bt_config
        if not bt_config.get("gates.second_auditor", True):
            return None
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    tasks = plan.get("tasks") if isinstance(plan, dict) else None
    audits = [t.get("id") for t in tasks if isinstance(t, dict) and t.get("kind") == "audit"] if isinstance(tasks, list) else []
    if len(audits) == 1:
        return (f"SECOND_AUDITOR_MISSING: {audits[0]} is the only audit; gates.second_auditor is on, so add an independent "
                "cross-check audit task (own report and findings ledger) — `plan-json retrofit-audit REQ --cross-check` "
                "adds it — or turn the policy off with `bitacora.py config set gates.second_auditor false`")
    return None


def plan_consumer_problem(rdir: Path, *, compatibility_report: dict[str, object] | None = None,
                          plan_path: Path | None = None) -> str | None:
    """The consumer gate (capability report) and the owner's gate policies for the plan."""
    return _consumer_problem(rdir, compatibility_report=compatibility_report, plan_path=plan_path) or \
        second_auditor_problem(plan_path or (Path(rdir) / planner.PLAN_JSON))


def _consumer_problem(rdir: Path, *, compatibility_report: dict[str, object] | None = None,
                      plan_path: Path | None = None) -> str | None:
    """Evaluate a caller-supplied capability report without importing downstream consumers here."""
    version = _schema_version(plan_path or (Path(rdir) / planner.PLAN_JSON))
    if version is None or version[1] < PLAN_SCHEMA_CONSUMER_GATE_SINCE:
        return None
    compatibility = compatibility_report if isinstance(compatibility_report, dict) else {}
    if compatibility.get("required_schema_version") == version[0] and compatibility.get("supported") is True:
        return None
    consumers = compatibility.get("consumers")
    consumers = consumers if isinstance(consumers, dict) else {}
    unavailable = []
    if compatibility.get("required_schema_version") != version[0]:
        reported = compatibility.get("required_schema_version")
        unavailable.append(f"capability report (schema {reported if isinstance(reported, str) else 'unknown'})")
    for name in ("M1", "M2", "M6"):
        consumer = consumers.get(name)
        status = consumer.get("status") if isinstance(consumer, dict) else "unknown"
        if status != "supported":
            unavailable.append(f"{name} ({status if isinstance(status, str) else 'unknown'})")
    planner_status = compatibility.get("planner")
    planner_status = planner_status.get("status") if isinstance(planner_status, dict) else "unknown"
    if not isinstance(planner_status, str) or planner_status != "supported":
        unavailable.insert(0, f"Planner ({planner_status if isinstance(planner_status, str) else 'unknown'})")
    return (f"PLAN_CONSUMER_INCOMPATIBLE: PLAN.json schema {version[0]} requires compatible M1/M2/M6 consumers; "
            f"unsupported or unknown: {', '.join(unavailable)}. Check `bitacora.py plan-json compat "
            f"{plan_id(rdir)}` before approval or execution")


def plan_id(rdir: Path) -> str:
    """`REQ-009-some-slug` -> `REQ-009` (the methodology's requirement id)."""
    return "-".join(Path(rdir).name.split("-")[:2])


def repo_roots(rdir: Path) -> dict[str, Path] | None:
    """{repository role: checkout} of the project that owns this requirement folder, so the planner can verify that the
    `file:` evidence of a classification really exists. None when the workspace cannot be resolved (never guessed)."""
    try:
        import bt_core as core
        project = Path(rdir).resolve().parent.parent.name
        roots = {role: Path(path) for role, path in core.ws.repos(core.ROOT, project).items()}
    except Exception:  # noqa: BLE001 - an unresolvable workspace only means evidence is reported as unverified
        return None
    # a registered repository that is not cloned on this machine yet cannot disprove anything: leave it unresolved
    return {role: path for role, path in roots.items() if path.is_dir()} or None


def ref_verifier(rdir: Path):
    """`command:` and `precedent:` evidence must point at something that exists in this workspace: an executable or a
    path for a command; a requirement (and task), decision, pending item or commit for a precedent. True/False when
    it can tell, None when it cannot (a URL, an unresolved repository)."""
    roots = repo_roots(rdir) or {}
    try:
        import bt_core as core
        bitacora_root = Path(core.ROOT)
    except Exception:  # noqa: BLE001
        bitacora_root = Path(rdir).resolve().parent.parent.parent
    project_dir = Path(rdir).resolve().parent.parent

    def text_of(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            return ""

    def requirement(number: str, task: str | None) -> bool:
        found = [p for base in {bitacora_root, project_dir.parent} for p in Path(base).glob(f"*/requirements/REQ-{number}-*")]
        found += list(project_dir.glob(f"requirements/REQ-{number}-*"))
        if not found:
            return False
        if not task:
            return True
        return any(re.search(rf"\b{re.escape(task)}\b", text_of(p / "PLAN.md")) for p in found)

    def check(kind: str, value: str, repository: str) -> bool | None:
        if kind == "command":
            return verify_command(value, roots.get(repository))
        if kind == "precedent":
            req = re.fullmatch(r"REQ-([0-9]+)(?:/(T[0-9]+(?:\.[0-9]+)?[a-z]?))?(?:#.*)?", value)
            if req:
                return requirement(req.group(1), req.group(2))
            ident = re.fullmatch(r"([DP])-([0-9]+)", value)
            if ident:
                names = {"D": "DECISIONS.md", "P": "PENDING.md"}[ident.group(1)]
                return re.search(rf"\b{ident.group(1)}-{ident.group(2)}\b", text_of(project_dir / names)) is not None
            family = re.fullmatch(r"([A-Za-z][A-Za-z0-9_.-]*?)-[0-9]+(?:[/#].*)?", value)
            if family and family.group(1) not in ("REQ", "D", "P", "PLAN", "SCH", "PR", "ISSUE"):
                return False  # an id of a family this workspace does not keep: cannot be a precedent here
            commit = re.fullmatch(r"(?:commit )?([0-9a-f]{7,40})", value)
            if commit:
                if not roots:
                    return None
                for base in roots.values():
                    done = subprocess.run(["git", "-C", str(base), "cat-file", "-e", commit.group(1) + "^{commit}"],
                                          capture_output=True, timeout=10, check=False)
                    if done.returncode == 0:
                        return True
                return False
        return None

    return check


def run_cli(action: str, rdir: Path, *, force: bool = False, as_json: bool = False, emit=print,
            compatibility_report: dict[str, object] | None = None, cross_check: bool = False) -> int:
    """Back the `bitacora.py plan-json <action> REQ-NNN` command."""
    if action == "compat":
        messages: list[str] = []
        code = planner_cli.run(action, rdir, plan_id=plan_id(rdir), force=force, as_json=as_json,
                               approved_states=APPROVED_STATES, repo_roots=repo_roots(rdir),
                               ref_exists=ref_verifier(rdir), emit=messages.append)
        if code:
            for message in messages:
                emit(message)
            return code
        try:
            report = json.loads("\n".join(messages))
        except (TypeError, ValueError):
            emit("PLAN_COMPATIBILITY_REPORT_FAILED: the Planner returned an unreadable compatibility report")
            return 2
        if not isinstance(report, dict):
            emit("PLAN_COMPATIBILITY_REPORT_FAILED: the Planner returned an invalid compatibility report")
            return 2
        if compatibility_report is not None:
            report["downstream_compatibility"] = compatibility_report
        emit(json.dumps(report, indent=1, ensure_ascii=False))
        return 0
    if action in {"freeze", "bind"}:
        problem = publishable_problem(rdir, compatibility_report=compatibility_report, allow_unmapped=force) if action == "freeze" else \
            plan_consumer_problem(rdir, compatibility_report=compatibility_report)
        if problem:
            emit(problem)
            return 2
    return planner_cli.run(action, rdir, plan_id=plan_id(rdir), force=force, as_json=as_json,
                           approved_states=APPROVED_STATES, repo_roots=repo_roots(rdir), ref_exists=ref_verifier(rdir),
                           cross_check=cross_check, emit=emit)


def handoff_problems(rdir: Path, limit: int = 5, *,
                     compatibility_report: dict[str, object] | None = None) -> list[str]:
    """Reasons `handoff` must refuse the plan because its (opt-in) PLAN.json is invalid; [] for legacy plans."""
    if not (Path(rdir) / planner.PLAN_JSON).exists():
        return []
    errors = planner.check(rdir, plan_id=plan_id(rdir), repo_roots=repo_roots(rdir),
                           ref_exists=ref_verifier(rdir)).errors
    out = [f"PLAN.json: {e}" for e in errors[:limit]]
    if len(errors) > limit:
        out.append(f"PLAN.json: {len(errors) - limit} more error(s); run `bitacora.py plan-json check {plan_id(rdir)}`")
    if not errors and (problem := plan_consumer_problem(rdir, compatibility_report=compatibility_report)):
        out.append(f"PLAN.json: {problem}")
    return out


def launch_problem(rdir: Path, *, freeze: bool = True, forced: bool = False,
                   compatibility_report: dict[str, object] | None = None) -> str | None:
    """The gate every launch path passes (standard, foreground, web, handoff, and a new run itself): None when the
    plan may run, otherwise one line saying why not. The plan must be valid, consistent with PLAN.md and exactly the
    approved (frozen) revision. A launch never creates the approval record: a plan that was never frozen is refused
    (`PLAN_NOT_FROZEN`); only an explicit `forced` launch is taken as the owner's approval and frozen (`freeze` False
    verifies without writing). A legacy plan (no PLAN.json, nothing frozen) always passes."""
    if problem := plan_consumer_problem(rdir, compatibility_report=compatibility_report):
        return problem
    try:
        planner.bind_approved(rdir, plan_id(rdir), APPROVED_STATES, repo_roots=repo_roots(rdir), freeze=freeze,
                              forced=forced, verify_files=True, ref_exists=ref_verifier(rdir))
    except planner.PlanContractError as exc:
        more = f" (+{len(exc.issues) - 5} more)" if len(exc.issues) > 5 else ""
        return (f"{exc.code}: PLAN.json cannot be launched: " + "; ".join(exc.issues[:5]) + more +
                f" (bitacora.py plan-json check {plan_id(rdir)})")
    except Exception as exc:  # noqa: BLE001 - the gate fails closed: an unexpected error never lets a plan through
        return (f"PLAN_CHECK_FAILED: PLAN.json could not be checked ({type(exc).__name__}); "
                f"run `bitacora.py plan-json check {plan_id(rdir)}`")
    return None


def freeze_on_launch(rdir: Path, *, dry_run: bool = False, forced: bool = False,
                     compatibility_report: dict[str, object] | None = None) -> None:
    """Standard/web launch: refuse (SystemExit with the cause) unless the run would execute exactly the approved,
    frozen revision. A dry run verifies and writes nothing."""
    problem = launch_problem(rdir, freeze=not dry_run, forced=forced,
                             compatibility_report=compatibility_report)
    if problem:
        raise SystemExit(problem)


def resume_problem(rdir: Path, state: dict, *,
                   compatibility_report: dict[str, object] | None = None) -> str | None:
    """A RESUMED run must not go on executing content nobody approved. When the run carries a `plan_ref` (or the plan
    has frozen revisions): PLAN.json must still exist, be valid and be the latest approved revision, the PLAN.md prose
    must be the approved one, and the run's own `plan_ref` must point at that same revision (a run started under r1
    while r2 was approved keeps r1's verification commands: start a new run instead). The gate never writes RUN.json.
    File evidence is not re-verified (the run's own work may have moved those files). Plans without the contract are
    never gated."""
    if problem := plan_consumer_problem(rdir, compatibility_report=compatibility_report):
        return problem
    raw_ref = state.get("plan_ref") if isinstance(state, dict) else None
    ref = raw_ref if isinstance(raw_ref, dict) else None
    try:
        frozen = planner.list_revisions(rdir)
        if not (ref or frozen):
            return None
        if frozen and not ref:
            return ("PLAN_REF_MISSING: this run has no plan_ref for the approved revision; "
                    "start a new run so its approved plan identity and hash are recorded")
        entry = planner.bind_approved(rdir, plan_id(rdir), APPROVED_STATES, repo_roots=None, freeze=False,
                                      forced=True, verify_files=False)
    except planner.PlanContractError as exc:
        more = f" (+{len(exc.issues) - 5} more)" if len(exc.issues) > 5 else ""
        return (f"{exc.code}: this run cannot resume on PLAN.json: " + "; ".join(exc.issues[:5]) + more +
                f" (bitacora.py plan-json check {plan_id(rdir)})")
    except Exception as exc:  # noqa: BLE001 - fail closed
        return (f"PLAN_CHECK_FAILED: PLAN.json could not be checked ({type(exc).__name__}); "
                f"run `bitacora.py plan-json check {plan_id(rdir)}`")
    if ref and entry:
        if ref.get("plan_id") != plan_id(rdir):
            return (f"PLAN_REF_MISMATCH: the run's plan_ref names {ref.get('plan_id')!r}, but this requirement is "
                    f"{plan_id(rdir)}")
        revision = ref.get("revision")
        if not (isinstance(revision, int) and not isinstance(revision, bool)) or revision != entry["revision"]:
            return (f"PLAN_REF_STALE: this run was started under revision {ref.get('revision')} but revision "
                    f"{entry['revision']} is the approved one; resuming would keep running the old plan values. "
                    "Start a new run for the approved revision")
        if not isinstance(ref.get("sha256"), str) or ref["sha256"] != entry["sha256"]:
            return (f"PLAN_REF_MISMATCH: the run's plan_ref hash does not match approved revision "
                    f"{entry['revision']}; the run state or the revision store was altered")
    return None


def mapping_problem(rdir: Path) -> str | None:
    """Approval gate (config `planner.require_mapped_checks`, off by default): a check whose purpose is not the exact text of a
    criterion of its task, or a criterion no check carries, makes the verifier stop for a person on every attempt (CHECK_UNMAPPED /
    CRITERION_UNVERIFIABLE: the two most frequent stops of four real runs). New approvals must not carry them; plans already
    frozen are never re-gated (revisions made by the scheduler itself do not pass here)."""
    import bt_config

    if bt_config.get("planner.require_mapped_checks", False) is not True:
        return None
    try:
        plan = planner.load(Path(rdir) / planner.PLAN_JSON)
    except Exception:  # noqa: BLE001 - an unreadable plan is the validity check's to report
        return None
    lines = [f"{c['task_id']}.verification[{c['verification_index']}] «{str(c['purpose'])[:60]}»" for c in planner_quality.unmapped_checks(plan)]
    lines += [f"{c['task_id']}: criterion «{str(c['criterion'])[:60]}» has no check with its exact text"
              for c in planner_quality.criteria_without_command(plan) if c["reason"] in ("purpose_not_found", "whitespace_mismatch")]
    if not lines:
        return None
    more = f" (+{len(lines) - 4} more)" if len(lines) > 4 else ""
    return ("PLAN_CHECKS_UNMAPPED: the verifier maps evidence to criteria by exact text, so these would stop the run for a person: "
            + "; ".join(lines[:4]) + more + f" (bitacora.py plan-json check {plan_id(rdir)} lists them; `purpose` = the criterion's text; "
            "pass --force to approve anyway, or set planner.require_mapped_checks=false)")


def publishable_problem(rdir: Path, *, compatibility_report: dict[str, object] | None = None,
                        allow_unmapped: bool = False) -> str | None:
    """Approval gate: a PLAN.json that is invalid, or contradicts PLAN.md, cannot be approved. None for legacy plans."""
    if not (Path(rdir) / planner.PLAN_JSON).exists():
        return None
    try:
        report = planner.check(rdir, plan_id=plan_id(rdir), repo_roots=repo_roots(rdir), verify_files=True,
                               ref_exists=ref_verifier(rdir))
    except Exception as exc:  # noqa: BLE001 - fail closed
        return (f"PLAN_CHECK_FAILED: the plan cannot be approved, PLAN.json could not be checked "
                f"({type(exc).__name__}); run `bitacora.py plan-json check {plan_id(rdir)}`")
    if report.ok:
        return (None if allow_unmapped else mapping_problem(rdir)) or plan_consumer_problem(rdir, compatibility_report=compatibility_report)
    more = f" (+{len(report.errors) - 5} more)" if len(report.errors) > 5 else ""
    return ("PLAN_INVALID: the plan cannot be approved while PLAN.json has errors: " + "; ".join(report.errors[:5]) +
            more + f" (bitacora.py plan-json check {plan_id(rdir)})")


def freeze_approved(rdir: Path, *, compatibility_report: dict[str, object] | None = None) -> None:
    """Called right after PLAN.md became `approved`: the approved PLAN.json is frozen at that moment, so what the
    owner approved is what any later launch is compared against. No PLAN.json -> nothing to do."""
    if problem := publishable_problem(rdir, compatibility_report=compatibility_report):
        raise SystemExit(problem)
    try:
        planner.freeze_if_present(rdir, plan_id(rdir), APPROVED_STATES, repo_roots(rdir), verify_files=True,
                                  ref_exists=ref_verifier(rdir))
    except planner.PlanContractError as exc:
        raise SystemExit(f"{exc.code}: approved PLAN.json could not be frozen: " + "; ".join(exc.issues[:5])) from exc


def run_state_fields(rdir: Path) -> dict:
    """Fields a NEW run state records about its plan: `plan_ref`, or `plan_ref_error` when the store is damaged."""
    return planner.run_reference(rdir)


# ---- classification amendments (the plan's estimate changing while it runs; scope still needs a new revision)
def amend(rdir: Path, task: str, field: str, to: object, *, reason: str, evidence: list[str] | None = None, by: str,
          proposed_by: str) -> dict:
    """Append one amendment to the requirement's `PLAN.amendments.jsonl` (planner rules: an agent may only raise a
    level, with evidence). Raises `planner.PlanContractError` (stable `.code`) when refused."""
    return planner.amendments.append(rdir, task, field, to, reason=reason, evidence=evidence, by=by,
                                     proposed_by=proposed_by)


def amendments(rdir: Path) -> list[dict]:
    return planner.amendments.read(rdir)


def effective_overrides(rdir: Path) -> dict[str, dict[str, object]]:
    """{task id: {field: value in force}} for the classification fields an amendment changed; {} when none (or when the
    plan or the file cannot be read: the plan's own classification stays in force)."""
    try:
        records = planner.amendments.read(rdir)
        if not records:
            return {}
        last = planner.latest(rdir)
        plan = planner.load_revision(rdir, last["revision"]) if last else planner.load(Path(rdir) / planner.PLAN_JSON)
        in_force = planner.amendments.effective(plan, records)
    except (planner.PlanContractError, OSError, ValueError):
        return {}
    own = {t["id"]: t for t in plan.get("tasks", []) if isinstance(t, dict) and "id" in t}
    return {tid: {f: v for f, v in fields.items() if v != own.get(tid, {}).get(f)}
            for tid, fields in in_force.items() if any(v != own.get(tid, {}).get(f) for f, v in fields.items())}


def revisions(rdir: Path) -> list[dict]:
    """The frozen revisions of a plan, oldest first: [{revision, sha256, frozen_at, ...}]; [] when none or unreadable."""
    try:
        return planner.list_revisions(rdir)
    except (planner.PlanContractError, OSError, ValueError):
        return []


# ---- what plan growth at run time (bt_remediation) needs from the planner: the module is imported only here
def latest_plan(rdir: Path) -> dict | None:
    """The latest frozen revision of the requirement's plan, or None when nothing was frozen."""
    last = planner_revisions.latest(rdir)
    return planner_revisions.load_revision(rdir, last["revision"]) if last else None


DECISION_MAX_CHECKS = 32      # the scheduler's decision engine refuses a task with more checks (bt_scheduler_decision.validation)


def plan_errors(plan: dict) -> list[str]:
    """The contract errors of a plan ([] when it is valid), including the limits the scheduler enforces when it dispatches: a plan
    the owner cannot route used to freeze fine and then stall the run in a loop (REQ-020 T14.5a had 42 checks)."""
    errors = list(planner_contract.validate(plan).errors)
    for task in plan.get("tasks", ()) if isinstance(plan, dict) else ():
        count = len(task.get("verification") or ()) if isinstance(task, dict) else 0
        if count > DECISION_MAX_CHECKS:
            errors.append(f"{task.get('id')}: {count} verification checks; the scheduler routes at most {DECISION_MAX_CHECKS} per task")
    return errors


def freeze_revision(rdir: Path, plan: dict, source: str) -> dict:
    """Freeze `plan` as the next revision and write it as the working PLAN.json."""
    frozen = planner_revisions.freeze(rdir, plan, source)
    (Path(rdir) / planner.PLAN_JSON).write_text(planner_contract.dumps(plan), encoding="utf-8")
    return frozen


def paths_overlap(a: str, b: str) -> bool:
    return planner_quality.paths_overlap(a, b)
