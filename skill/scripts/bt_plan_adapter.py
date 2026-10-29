"""Methodology → adapter → `bt_planner`; sole importer boundary is enforced by test_plan_integration."""
from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable
from pathlib import Path

import bt_planner as planner
from bt_plan_adapter_evidence import verify_command
from bitacora_platform.plan_command_checks import ignore_resolver
from bt_planner import cli as planner_cli
from bt_planner import command_checks as planner_command_checks
from bt_planner import contract as planner_contract
from bt_planner import quality as planner_quality
from bt_planner import revisions as planner_revisions

from bt_plan_consumers import (
    PLAN_SCHEMA_CONSUMER_GATE_SINCE,
    _SCHEMA_VERSION_RE,
    _schema_version,
    plan_schema_version,
    second_auditor_required,
    plan_schema_version_details,
    second_auditor_problem,
    second_auditor_lines,
    plan_consumer_problem,
    _consumer_problem,
    _schema_version_value,
    _compat_consumer_supported,
    plan_id,
)


# What the methodology calls an approved plan; the module itself only has a default for these words.
APPROVED_STATES = ("approved", "launched", "done", "merged")
LEDGER_COMMAND = "bitacora.py audit-ledger check"


def validate_candidate(plan: object) -> tuple[str, ...]:
    """Validate an in-memory plan revision through the Planner contract without filesystem effects."""
    report = planner.validate(plan)
    return tuple(report.errors)

def validate_owner_composition(subplans, gates, tasks) -> tuple[str, ...]:
    return planner.validate_owner_composition(subplans, gates, tasks)  # Planner rules over the owner's plan view

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
    original_emit = emit
    emit = lambda text: original_emit(text.replace("the engine's `audit-ledger check`", "`bitacora.py audit-ledger check`"))
    if action == "compat":
        messages: list[str] = []
        code = planner_cli.run(action, rdir, plan_id=plan_id(rdir), force=force, as_json=as_json,
                               approved_states=APPROVED_STATES, repo_roots=repo_roots(rdir),
                               ignored_path=ignore_resolver(repo_roots(rdir)), ref_exists=ref_verifier(rdir), emit=messages.append)
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
        report["consumer_supported"] = _compat_consumer_supported(rdir, compatibility_report)
        emit(json.dumps(report, indent=1, ensure_ascii=False))
        return 0
    if action in {"freeze", "bind"}:
        problem = publishable_problem(rdir, compatibility_report=compatibility_report, allow_unmapped=force) if action == "freeze" else \
            plan_consumer_problem(rdir, compatibility_report=compatibility_report)
        if problem:
            emit(problem)
            return 2
    return planner_cli.run(action, rdir, plan_id=plan_id(rdir), force=force, as_json=as_json,
                           approved_states=APPROVED_STATES, repo_roots=repo_roots(rdir), ignored_path=ignore_resolver(repo_roots(rdir)), ref_exists=ref_verifier(rdir),
                           cross_check=cross_check, ledger_command=LEDGER_COMMAND, emit=emit)


def handoff_problems(rdir: Path, limit: int = 5, *,
                     compatibility_report: dict[str, object] | None = None) -> list[str]:
    """Reasons `handoff` must refuse the plan because its (opt-in) PLAN.json is invalid; [] for legacy plans."""
    if not (Path(rdir) / planner.PLAN_JSON).exists():
        return []
    errors = planner.check(rdir, plan_id=plan_id(rdir), repo_roots=repo_roots(rdir),
                           ignored_path=ignore_resolver(repo_roots(rdir)), ref_exists=ref_verifier(rdir),
                           ledger_command=LEDGER_COMMAND, strict_publication=not _unchanged_frozen(rdir)).errors
    out = [f"PLAN.json: {e}" for e in errors[:limit]]
    if len(errors) > limit:
        out.append(f"PLAN.json: {len(errors) - limit} more error(s); run `bitacora.py plan-json check {plan_id(rdir)}`")
    if not errors and (problem := plan_consumer_problem(rdir, compatibility_report=compatibility_report)):
        out.append(f"PLAN.json: {problem}")
    return out


def _unchanged_frozen(rdir: Path) -> bool:
    try:
        last = planner_revisions.latest(rdir)
        plan = planner_contract.load(Path(rdir) / planner.PLAN_JSON)
        return bool(last and plan.get("revision") == last["revision"]
                    and planner_revisions.sha256(planner_contract.dumps(plan)) == last["sha256"])
    except (planner.PlanContractError, OSError, ValueError):
        return False


def launch_problem(rdir: Path, *, forced: bool = False,
                   compatibility_report: dict[str, object] | None = None) -> str | None:
    """The gate every launch and join passes (standard, foreground, web, handoff, a stage): None when the latest approved
    stage may run, otherwise one line saying why not. The draft projected onto that stage must be exactly it (D-134):
    edits to approved scope are refused, edits elsewhere are the planners' draft. A launch never creates an approval
    record (`PLAN_NOT_FROZEN`). `forced` skips the PLAN.md status check: a stage runs while the plan is still planned."""
    if problem := plan_consumer_problem(rdir, compatibility_report=compatibility_report):
        return problem
    try:
        planner.bind_approved(rdir, plan_id(rdir), APPROVED_STATES, forced=forced)
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
    frozen revision. Nothing is written (a launch never freezes); `dry_run` is accepted for the callers' symmetry."""
    problem = launch_problem(rdir, forced=forced, compatibility_report=compatibility_report)
    if problem:
        raise SystemExit(problem)


def resume_problem(rdir: Path, state: dict, *, compatibility_report: dict[str, object] | None = None) -> str | None:
    """A RESUMED run executes the revision it is bound to (D-134: a newer approved stage joins it at a quiet point), so
    resuming only needs that revision to be one the owner approved: the run's `plan_ref` names a frozen revision of this
    requirement with the same hash. The draft is not judged here."""
    if problem := plan_consumer_problem(rdir, compatibility_report=compatibility_report):
        return problem
    raw_ref = state.get("plan_ref") if isinstance(state, dict) else None
    ref = raw_ref if isinstance(raw_ref, dict) else None
    try:
        frozen = planner.list_revisions(rdir)
    except planner.PlanContractError as exc:
        return f"{exc.code}: this run cannot resume: " + "; ".join(exc.issues[:5])
    except Exception as exc:  # noqa: BLE001 - fail closed
        return (f"PLAN_CHECK_FAILED: the revision store could not be read ({type(exc).__name__}); "
                f"run `bitacora.py plan-json check {plan_id(rdir)}`")
    if not (ref or frozen):
        return None
    if not ref:
        return ("PLAN_REF_MISSING: this run has no plan_ref for an approved revision; "
                "start a new run so its approved plan identity and hash are recorded")
    if ref.get("plan_id") != plan_id(rdir):
        return (f"PLAN_REF_MISMATCH: the run's plan_ref names {ref.get('plan_id')!r}, but this requirement is "
                f"{plan_id(rdir)}")
    entry = next((item for item in frozen if item["revision"] == ref.get("revision")), None)
    if entry is None or ref.get("sha256") != entry["sha256"]:
        return (f"PLAN_REF_MISMATCH: the run's plan_ref (revision {ref.get('revision')}) is not an approved revision "
                "with that hash; the run state or the revision store was altered")
    try:
        planner.load_revision(rdir, entry["revision"])        # the bytes the run executes are the approved ones
    except planner.PlanContractError as exc:
        return f"{exc.code}: this run cannot resume: " + "; ".join(exc.issues[:5])
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



def host_path_lines(plan: dict, frozen: tuple[dict, dict] | None) -> str | None:
    """Approval gate: a new or changed sandbox check that names a host path fails on every attempt
    (`command_checks.host_paths`). A check frozen exactly so was approved before this gate and is not re-gated."""
    kept = {(t.get("id"), c.get("value")) for t in (frozen[1].get("tasks") or [] if frozen else [])
            if isinstance(t, dict) for c in t.get("verification") or [] if isinstance(c, dict)}
    lines = [f"{c['task_id']}.verification[{c['verification_index']}] «{c['path']}»"
             for c in planner_command_checks.host_paths(plan) if (c["task_id"], c["value"]) not in kept]
    if not lines:
        return None
    more = f" (+{len(lines) - 4} more)" if len(lines) > 4 else ""
    return ("PLAN_CHECK_HOST_PATH: the verifier runs checks in a sandbox holding only a copy of the repository, so these "
            "would fail on every attempt: " + "; ".join(lines[:4]) + more + "; use a repository path, or pin the content "
            "(e.g. its sha256 with `node -e`)")


def host_path_problem(rdir: Path) -> str | None:
    try:
        plan = planner.load(Path(rdir) / planner.PLAN_JSON)
        found = planner.stages.latest(rdir)
    except Exception:  # noqa: BLE001 - an unreadable plan or store is the validity check's to report
        return None
    return host_path_lines(plan, found)


def git_facts(roots: dict[str, Path], ref: str = "HEAD"):
    """(exists, read) callbacks over the repositories at `ref`, for bt_planner.preflight (which reads no repository)."""
    import subprocess

    def exists(role: str, path: str) -> bool | None:
        repo = roots.get(role)
        if repo is None:
            return None
        if path == ".":
            return True
        done = subprocess.run(["git", "cat-file", "-e", f"{ref}:{path}"], cwd=str(repo), capture_output=True, check=False)
        return done.returncode == 0

    def read(role: str, path: str) -> bytes | None:
        repo = roots.get(role)
        if repo is None:
            return None
        done = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=str(repo), capture_output=True, check=False)
        return done.stdout if done.returncode == 0 else None

    return exists, read


def preflight_check(plan: dict, roots: dict[str, Path], *, env_available=None, strict: bool = False, ref: str = "HEAD"):
    """bt_planner.preflight over real repositories (the planner's one door, like every other planner call)."""
    from bt_planner import preflight
    exists, read = git_facts(roots, ref)
    return preflight.check(plan, exists=exists, read=read, env_available=env_available, strict=strict, base=ref)


def preflight_problem(rdir: Path) -> str | None:
    """REQ-030 M6: structural defects a run would hit before any agent could fix them (bt_planner.preflight)."""
    import bt_config
    if not bt_config.get("planner.preflight", True):
        return None
    roots = repo_roots(rdir)
    if roots is None:
        return None                                   # an unresolvable workspace proves nothing either way
    try:
        import bt_verifier_env
        from bt_scheduler_verification_authority import owner_verification_authority
        plan = json.loads((Path(rdir) / planner.PLAN_JSON).read_text(encoding="utf-8"))
        project = Path(rdir).resolve().parent.parent.name
        environment, _ = bt_verifier_env.for_run(project, rdir)
        names = {name for name, _ in environment}
        authority = owner_verification_authority(rdir, project)
        report = preflight_check(plan, roots,
                                 env_available=lambda name: name in names or authority.resource_available(name))
    except Exception:  # noqa: BLE001 - the pre-flight never blocks on its own failure; the planner check already ran
        return None
    if report.ok:
        return None
    more = f" (+{len(report.errors) - 4} more)" if len(report.errors) > 4 else ""
    return "PLAN_PREFLIGHT: " + "; ".join(report.errors[:4]) + more + " (planner.preflight=false skips this gate)"


def publishable_problem(rdir: Path, *, compatibility_report: dict[str, object] | None = None,
                        allow_unmapped: bool = False) -> str | None:
    """Approval gate: a PLAN.json that is invalid, or contradicts PLAN.md, cannot be approved. None for legacy plans."""
    if not (Path(rdir) / planner.PLAN_JSON).exists():
        return None
    if problem := plan_consumer_problem(rdir, compatibility_report=compatibility_report):
        return problem
    try:
        report = planner.check(rdir, plan_id=plan_id(rdir), repo_roots=repo_roots(rdir), verify_files=True,
                               ignored_path=ignore_resolver(repo_roots(rdir)), ref_exists=ref_verifier(rdir),
                               ledger_command=LEDGER_COMMAND)
    except Exception as exc:  # noqa: BLE001 - fail closed
        return (f"PLAN_CHECK_FAILED: the plan cannot be approved, PLAN.json could not be checked "
                f"({type(exc).__name__}); run `bitacora.py plan-json check {plan_id(rdir)}`")
    if report.ok:
        return preflight_problem(rdir) or host_path_problem(rdir) or (None if allow_unmapped else mapping_problem(rdir))
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
                                  ignored_path=ignore_resolver(repo_roots(rdir)), ref_exists=ref_verifier(rdir),
                                  ledger_command=LEDGER_COMMAND)
    except planner.PlanContractError as exc:
        raise SystemExit(f"{exc.code}: approved PLAN.json could not be frozen: " + "; ".join(exc.issues[:5])) from exc


def stage_problem(rdir: Path, subplans: list[str], *, compatibility_report: dict[str, object] | None = None,
                  allow_unmapped: bool = False, draft: dict | None = None) -> str | None:
    """Publication gate of the next stage (D-134) without writing: the engine supports the plan, the projection passes
    `check_stage` and, under `planner.require_mapped_checks`, every check maps to a criterion."""
    if problem := plan_consumer_problem(rdir, compatibility_report=compatibility_report):
        return problem
    try:
        projection, draft = _next_stage(rdir, subplans, draft=draft)
        report = planner.check_stage(rdir, projection, draft, plan_id(rdir), repo_roots(rdir), True,
                                     ref_verifier(rdir), ignore_resolver(repo_roots(rdir)), LEDGER_COMMAND)
    except planner.PlanContractError as exc:
        return f"{exc.code}: " + "; ".join(exc.issues[:5]) + (f" (+{len(exc.issues) - 5} more)" if len(exc.issues) > 5 else "")
    except Exception as exc:  # noqa: BLE001 - fail closed
        return f"PLAN_CHECK_FAILED: the stage could not be checked ({type(exc).__name__})"
    if not report.ok:
        more = f" (+{len(report.errors) - 5} more)" if len(report.errors) > 5 else ""
        return "PLAN_INVALID: the stage cannot be approved: " + "; ".join(report.errors[:5]) + more
    if (problem := second_auditor_lines(projection)):       # what the run would refuse, refused at approval
        return problem
    if (problem := host_path_lines(projection, planner.stages.latest(rdir))):     # what the sandbox can never run
        return problem
    return None if allow_unmapped else _mapping_lines(projection, plan_id(rdir))


def stage_readiness(rdir: Path, *, compatibility_report: dict[str, object] | None = None) -> list[dict]:
    """Deterministic structure check of the whole plan, stage by stage: for every subplan in plan order (after the approved
    stage), would the stage that adds it and everything before it be approved? `stage_problem` is the gate the owner meets when
    he presses «Ejecutar subplan»; running it for every future stage tells the Planner, while it writes, what that button will
    refuse (REQ-021 SP-3: evidence citing a later subplan's task, a composition gate that also composes subplans not yet staged).
    A subplan with no tasks is not defined yet: it ends the chain (what follows depends on it) and is reported as such.
    Returns [{subplan, tasks, ok, problem, depends_on_unfinished}] in plan order."""
    draft, report = planner.sync.read_plan(rdir)
    if not isinstance(draft, dict):
        raise planner.PlanContractError("PLAN_INVALID", report.errors or ["PLAN.json: top level must be an object"])
    found = planner.stages.latest(rdir)
    approved = planner.stages.subplans_in(found[1]) if found else []
    counts: dict[str, int] = {}
    for task in draft.get("tasks") or []:
        if isinstance(task, dict) and isinstance(task.get("subplan_id"), str):
            counts[task["subplan_id"]] = counts.get(task["subplan_id"], 0) + 1
    out, chain, blocked_by = [], [], ""
    for sub in draft.get("subplans") or []:
        sid = sub.get("id") if isinstance(sub, dict) else None
        if not isinstance(sid, str) or sid in approved:
            continue
        item = {"subplan": sid, "tasks": counts.get(sid, 0), "ok": False, "problem": "", "depends_on_unfinished": ""}
        if not item["tasks"]:
            item["problem"] = "sin tareas: todavía no está definido"
            blocked_by = blocked_by or sid
        elif blocked_by:
            item["problem"] = f"no se puede comprobar: depende de {blocked_by}, que aún no está definido"
            item["depends_on_unfinished"] = blocked_by
        else:
            chain.append(sid)
            problem = stage_problem(rdir, list(chain), compatibility_report=compatibility_report, draft=draft)
            item["ok"], item["problem"] = problem is None, problem or ""
        out.append(item)
    return out


def _next_stage(rdir: Path, subplans: list[str], *, draft: dict | None = None) -> tuple[dict, dict]:
    """(projection, draft), including unchanged approvals so publication is always revalidated."""
    if draft is None:
        draft, report = planner.sync.read_plan(rdir)
    if not isinstance(draft, dict):
        raise planner.PlanContractError("PLAN_INVALID", report.errors or ["PLAN.json: top level must be an object"])
    found = planner.stages.latest(rdir)
    previous = planner.stages.subplans_in(found[1]) if found else []
    projection = planner.stages.project(draft, [*previous, *subplans])
    revision = (found[0]["revision"] + 1) if found else 1
    if (found and planner_contract.dumps({**projection, "revision": found[0]["revision"]}) == planner_contract.dumps(found[1])
            and found[0].get("stage") == planner.stages.approval_pins(rdir, draft, projection)):
        revision = found[0]["revision"]
    return {**projection, "revision": revision}, draft


def _mapping_lines(plan: dict, req: str) -> str | None:
    import bt_config

    if bt_config.get("planner.require_mapped_checks", False) is not True:
        return None
    lines = [f"{c['task_id']}.verification[{c['verification_index']}] «{str(c['purpose'])[:60]}»" for c in planner_quality.unmapped_checks(plan)]
    lines += [f"{c['task_id']}: criterion «{str(c['criterion'])[:60]}» has no check with its exact text"
              for c in planner_quality.criteria_without_command(plan) if c["reason"] in ("purpose_not_found", "whitespace_mismatch")]
    if not lines:
        return None
    more = f" (+{len(lines) - 4} more)" if len(lines) > 4 else ""
    return ("PLAN_CHECKS_UNMAPPED: the verifier maps evidence to criteria by exact text, so these would stop the run for a person: "
            + "; ".join(lines[:4]) + more + f" (bitacora.py plan-json check {req} lists them; `purpose` = the criterion's text)")


def freeze_stage(rdir: Path, subplans: list[str], *, compatibility_report: dict[str, object] | None = None,
                 draft: dict | None = None, before_freeze: Callable[[], None] | None = None) -> dict:
    """Approve the next stage: the subplans already approved plus `subplans` (D-134). Raises PlanContractError."""
    if problem := stage_problem(rdir, subplans, compatibility_report=compatibility_report, draft=draft):
        raise planner.PlanContractError(problem.split(":", 1)[0], [problem.split(":", 1)[-1].strip()])
    return planner.freeze_stage(rdir, subplans, plan_id(rdir), repo_roots(rdir), True, ref_verifier(rdir),
                                ignore_resolver(repo_roots(rdir)), LEDGER_COMMAND, draft=draft, before_freeze=before_freeze)


def stage_summary(rdir: Path) -> dict:
    """Approved stages for people (pages, CLI); empty when nothing is frozen or the store cannot be read."""
    try:
        return planner.stages.summary(rdir)
    except (planner.PlanContractError, OSError, ValueError):
        return {"stages": [], "complete": False}


def stage_subplans(rdir: Path, revision: int | None = None) -> list[str]:
    """Subplans of a frozen revision (the latest by default); [] when none. Raises on store damage (fail closed)."""
    if revision is None:
        found = planner.stages.latest(rdir)
        return planner.stages.subplans_in(found[1]) if found else []
    return planner.stages.subplans_in(planner_revisions.load_revision(rdir, revision))


def draft_subplans(rdir: Path) -> list[str] | None:
    """Subplans the working draft declares; None when PLAN.json cannot be read."""
    draft, _ = planner.sync.read_plan(rdir)
    return planner.stages.declared_subplans(draft) if isinstance(draft, dict) else None


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


def plan_errors(plan: dict, *, roots: dict[str, Path] | None = None) -> list[str]:
    """The contract errors of a plan ([] when it is valid), including the limits the scheduler enforces when it dispatches: a plan
    the owner cannot route used to freeze fine and then stall the run in a loop (REQ-020 T14.5a had 42 checks)."""
    errors = list(planner_contract.validate(plan, ignored_path=ignore_resolver(roots)).errors)
    for task in plan.get("tasks", ()) if isinstance(plan, dict) else ():
        count = len(task.get("verification") or ()) if isinstance(task, dict) else 0
        if count > DECISION_MAX_CHECKS:
            errors.append(f"{task.get('id')}: {count} verification checks; the scheduler routes at most {DECISION_MAX_CHECKS} per task")
    return errors


def freeze_revision(rdir: Path, plan: dict, source: str) -> dict:
    """Freeze a revision the scheduler made itself (healing, remediation, recovery) from the latest one, and carry it
    into the working draft (`stages.splice`) so the draft never contradicts what runs while the rest of it is still
    being planned. Without a draft the revision becomes it; nothing is frozen when an existing draft cannot be read (it
    may be being written): the caller retries."""
    path = Path(rdir) / planner.PLAN_JSON
    draft, report = planner.sync.read_plan(rdir) if path.exists() else (None, None)
    if path.exists() and not isinstance(draft, dict):
        raise planner.PlanContractError("PLAN_INVALID", report.errors or ["PLAN.json is not an object"])
    base = latest_plan(rdir)
    spliced = planner.stages.splice(draft, base, plan) if base and draft is not None else plan
    frozen = planner_revisions.freeze(rdir, plan, source, ledger_command=LEDGER_COMMAND)
    tmp = path.with_name(f".{path.name}.splice.tmp")
    tmp.write_text(planner_contract.dumps(spliced), encoding="utf-8")
    tmp.replace(path)
    return frozen


def paths_overlap(a: str, b: str) -> bool:
    return planner_quality.paths_overlap(a, b)
