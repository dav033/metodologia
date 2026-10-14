"""The only place where the methodology touches the planner module (`bt_planner`).

Dependency direction: methodology -> this adapter -> bt_planner. The module knows nothing about the methodology; the
methodology-specific meaning (which PLAN.md status words mean "approved", how a requirement folder maps to a plan id,
what to do on a launch) lives here. No other file may import `bt_planner` (test_plan_integration enforces it).
"""
from __future__ import annotations

from pathlib import Path

import bt_planner as planner
from bt_planner import cli as planner_cli

# What the methodology calls an approved plan; the module itself only has a default for these words.
APPROVED_STATES = ("approved", "launched", "done", "merged")


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
    import re
    import shlex
    import shutil
    import subprocess

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
            try:
                words = shlex.split(value)
            except ValueError:
                return None
            while words and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]):
                words = words[1:]
            if not words:
                return None
            first = words[0]
            if first in ("cd", "export", "source", "set", "test", "[", "exec", "time"):
                return True
            if "/" in first:
                base = roots.get(repository)
                return (base / first).exists() if base else None
            return shutil.which(first) is not None
        if kind == "precedent":
            req = re.fullmatch(r"REQ-([0-9]+)(?:/(T[0-9]+(?:\.[0-9]+)?[a-z]?))?(?:#.*)?", value)
            if req:
                return requirement(req.group(1), req.group(2))
            ident = re.fullmatch(r"([DP])-([0-9]+)", value)
            if ident:
                names = {"D": "DECISIONS.md", "P": "PENDING.md"}[ident.group(1)]
                return re.search(rf"\b{ident.group(1)}-{ident.group(2)}\b", text_of(project_dir / names)) is not None
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


def run_cli(action: str, rdir: Path, *, force: bool = False, as_json: bool = False, emit=print) -> int:
    """Back the `bitacora.py plan-json <action> REQ-NNN` command."""
    return planner_cli.run(action, rdir, plan_id=plan_id(rdir), force=force, as_json=as_json,
                           approved_states=APPROVED_STATES, repo_roots=repo_roots(rdir), ref_exists=ref_verifier(rdir),
                           emit=emit)


def handoff_problems(rdir: Path, limit: int = 5) -> list[str]:
    """Reasons `handoff` must refuse the plan because its (opt-in) PLAN.json is invalid; [] for legacy plans."""
    if not (Path(rdir) / planner.PLAN_JSON).exists():
        return []
    errors = planner.check(rdir, plan_id=plan_id(rdir), repo_roots=repo_roots(rdir),
                           ref_exists=ref_verifier(rdir)).errors
    out = [f"PLAN.json: {e}" for e in errors[:limit]]
    if len(errors) > limit:
        out.append(f"PLAN.json: {len(errors) - limit} more error(s); run `bitacora.py plan-json check {plan_id(rdir)}`")
    return out


def launch_problem(rdir: Path, *, freeze: bool = True, forced: bool = False) -> str | None:
    """The gate every launch path passes (standard, foreground, web, handoff, and a new run itself): None when the
    plan may run, otherwise one line saying why not. The plan must be valid, consistent with PLAN.md and exactly the
    approved (frozen) revision. A launch never creates the approval record: a plan that was never frozen is refused
    (`PLAN_NOT_FROZEN`); only an explicit `forced` launch is taken as the owner's approval and frozen (`freeze` False
    verifies without writing). A legacy plan (no PLAN.json, nothing frozen) always passes."""
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


def freeze_on_launch(rdir: Path, *, dry_run: bool = False, forced: bool = False) -> None:
    """Standard/web launch: refuse (SystemExit with the cause) unless the run would execute exactly the approved,
    frozen revision. A dry run verifies and writes nothing."""
    problem = launch_problem(rdir, freeze=not dry_run, forced=forced)
    if problem:
        raise SystemExit(problem)


def resume_problem(rdir: Path, state: dict) -> str | None:
    """A RESUMED run keeps its RUN.json untouched but must not go on executing content nobody approved: when the run
    carries a `plan_ref` or the plan has frozen revisions, PLAN.json must still exist, be valid and be the latest
    approved revision. File evidence is not re-verified (the run's own work may have moved those files and this machine may hold no
    checkouts; it was verified at approval and launch). Runs of plans without the contract are never gated."""
    if not (state.get("plan_ref") or planner.list_revisions(rdir) or (Path(rdir) / planner.PLAN_JSON).exists()):
        return None
    if not state.get("plan_ref") and not planner.list_revisions(rdir):
        return None  # a contract plan that was never frozen: nothing approved to compare with
    try:
        planner.bind_approved(rdir, plan_id(rdir), APPROVED_STATES, repo_roots=None, freeze=False, forced=True,
                              verify_files=False)  # evidence files may legitimately have moved while the run worked
    except planner.PlanContractError as exc:
        more = f" (+{len(exc.issues) - 5} more)" if len(exc.issues) > 5 else ""
        return (f"{exc.code}: this run cannot resume on PLAN.json: " + "; ".join(exc.issues[:5]) + more +
                f" (bitacora.py plan-json check {plan_id(rdir)})")
    except Exception as exc:  # noqa: BLE001 - fail closed
        return (f"PLAN_CHECK_FAILED: PLAN.json could not be checked ({type(exc).__name__}); "
                f"run `bitacora.py plan-json check {plan_id(rdir)}`")
    return None


def publishable_problem(rdir: Path) -> str | None:
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
        return None
    more = f" (+{len(report.errors) - 5} more)" if len(report.errors) > 5 else ""
    return ("PLAN_INVALID: the plan cannot be approved while PLAN.json has errors: " + "; ".join(report.errors[:5]) +
            more + f" (bitacora.py plan-json check {plan_id(rdir)})")


def freeze_approved(rdir: Path) -> None:
    """Called right after PLAN.md became `approved`: the approved PLAN.json is frozen at that moment, so what the
    owner approved is what any later launch is compared against. No PLAN.json -> nothing to do."""
    try:
        planner.freeze_if_present(rdir, plan_id(rdir), APPROVED_STATES, repo_roots(rdir), verify_files=True,
                                  ref_exists=ref_verifier(rdir))
    except planner.PlanContractError as exc:
        raise SystemExit(f"{exc.code}: approved PLAN.json could not be frozen: " + "; ".join(exc.issues[:5])) from exc


def run_state_fields(rdir: Path) -> dict:
    """Fields a NEW run state records about its plan: `plan_ref`, or `plan_ref_error` when the store is damaged."""
    return planner.run_reference(rdir)
