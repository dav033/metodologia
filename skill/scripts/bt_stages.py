"""«Ejecutar subplan» (D-134): the Scheduler runs approved subplans while the rest of the plan is still being planned.

A stage is a frozen revision holding the subplans the owner approved so far (the planner's `stages` module). Running a
subplan here means: every subplan of the next stage is confirmed by the owner in the collaborative flow and unchanged
since (tasks, inputs, `## Pruebas` rows and design draft are in the confirmation digest), its UI drafts are pinned, the
stage passes the publication gate and is frozen as revision N+1, and then THE Scheduler runs it: a new run when there
is none, otherwise the existing run joins it at its next quiet point (dispatch paused, rebase keeping accepted work,
resume; `bt_scheduler_run.join`). PLAN.md `status` is not touched: the plan stays in planning until its final approval
(the stage that holds everything).

A stage that would hold a single audit gets its independent cross-check first (`gates.second_auditor`): the click adds
`<audit>b` to the plan and keeps the confirmations that held, instead of refusing.

Pressing the button is the owner's approval of the stage; `bitacora.py stage run` is honor-system like
`planning confirm` (an agent runs it only when the owner said so). Refusals carry a stable code.
"""
from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path

import bt_planning_activity as activity
import bt_planning_flow as flow


class StageError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code, self.message = code, message


DURABLE_REFUSAL = ("Este plan corre en el runtime durable, que todavía no suma etapas nuevas a un run en marcha: "
                   "no se aprobó ninguna etapa. Las tareas de este subplan quedan para cuando exista esa unión.")


def durable_owner(rdir: Path) -> bool:
    """The run belongs to the durable runtime (`RUN.owner.json` backend dbos), which cannot join a later stage yet."""
    import bt_run_owner
    try:
        return bt_run_owner.backend(rdir) == "dbos"
    except bt_run_owner.OwnerConflict:
        return False


def _req(rdir: Path) -> str:
    return "-".join(Path(rdir).name.split("-")[:2])


def approved(rdir: Path) -> list[str]:
    """Subplans of the latest approved stage (fail closed: an unreadable store raises StageError)."""
    import bt_plan_adapter
    try:
        return bt_plan_adapter.stage_subplans(rdir)
    except Exception as exc:
        raise StageError(getattr(exc, "code", "PLAN_REVISIONS_UNREADABLE"), str(exc)) from exc


def eligibility(rdir: Path, subplans: list[str]) -> list[str]:
    """Why these subplans cannot form a stage yet (empty when they can): the requirement follows the collaborative
    flow, the skeleton is confirmed, each subplan is confirmed and unchanged since, and no plan-wide input is pending."""
    if not flow.active(rdir):
        return [("el requerimiento no está en la planificación conjunta (bitacora.py planning start): no hay "
                 "confirmación de subplanes que aprobar por etapas")]
    st = flow.state(rdir)
    if st["editing"]:
        return ["PLAN.json se está editando (no se puede leer); inténtalo en unos segundos"]
    if not st["outline"]:
        return ["falta confirmar el esqueleto de hitos y subplanes"]
    out = []
    for sid in subplans:
        item = st["subplans"].get(sid)
        if item is None:
            out.append(f"{sid}: no está en el plan")
        elif item["state"] == "changed":
            out.append(f"{sid}: cambió después de confirmarlo; vuelve a confirmarlo")
        elif item["state"] != "confirmed":
            out.append(f"{sid}: sin confirmar" + (f" (falta: {'; '.join(item['problems'][:3])})" if item["problems"] else ""))
    pending = [r["item"] for r in st["inputs"] if r["pending"] and not r["subplans"]]
    if pending:
        out.append("faltan entradas generales: " + ", ".join(pending[:4]))
    return out


def _ui_refs(plan: dict, subplans: list[str]) -> list[str]:
    return [f"{sp['ui'].get('contract')}@v{sp['ui'].get('version')}" for sp in plan.get("subplans") or []
            if isinstance(sp, dict) and sp.get("id") in subplans and isinstance(sp.get("ui"), dict)]


def _approval_snapshot(rdir: Path, subplans: list[str]) -> tuple[dict, Callable[[], None]]:
    """Freeze the plan object checked by eligibility; reject changing approval inputs before publication."""
    import bt_design_drafts as drafts
    import bt_plan_adapter

    try:
        raw = (rdir / "PLAN.json").read_bytes()
        plan = bt_plan_adapter.planner.loads(raw.decode("utf-8"))
        if not isinstance(plan, dict):
            raise TypeError("PLAN.json must be an object")
        paths = [rdir / "PLAN.md", rdir / "SPEC.md", rdir / flow.DIR / flow.FILE]
        spec = (rdir / str(plan.get("spec_ref") or "SPEC.md")).resolve()
        if not spec.is_relative_to(rdir.resolve()):
            raise ValueError("SPEC must be inside the requirement")
        paths.append(spec)
        for ref in _ui_refs(plan, subplans):
            if not drafts._REF.fullmatch(ref):
                raise ValueError("invalid design reference")
            paths.extend(drafts.paths(rdir, ref))

        def digest(path: Path) -> str | None:
            return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None

        expected = {path: digest(path) for path in paths}
        expected[rdir / "PLAN.json"] = hashlib.sha256(raw).hexdigest()
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        raise StageError("STAGE_APPROVAL_CHANGED", f"no pude capturar los documentos de aprobación: {exc}") from exc

    def unchanged() -> None:
        try:
            changed = any(digest(path) != value for path, value in expected.items())
        except OSError:
            changed = True
        if changed:
            raise StageError("STAGE_APPROVAL_CHANGED", "los documentos cambiaron durante la aprobación; confirma "
                             "el subplan actualizado y vuelve a intentarlo")

    return plan, unchanged


def _add_second_auditor(rdir: Path, stage: list[str], add: list[str]) -> list[str]:
    """The owner's click also settles `gates.second_auditor`: when the stage would hold a single audit, add its
    independent cross-check (`<audit>b`, own report and ledger, after it; whatever waited for the audit waits for both)
    and keep the confirmations that held before this mechanical edit. Anything else wrong is left to the gates below,
    which refuse with their own reason. Returns what changed in the plan."""
    import bt_plan_adapter
    from bt_plan_consumers import second_auditor_lines
    if eligibility(rdir, stage):
        return []
    try:
        projection, _ = bt_plan_adapter._next_stage(rdir, add)
    except Exception:  # noqa: BLE001 - the publication gate reports it
        return []
    if not second_auditor_lines(projection):
        return []
    audit = next(t["id"] for t in projection["tasks"] if isinstance(t, dict) and t.get("kind") == "audit")
    confirmed = [sid for sid, item in flow.state(rdir)["subplans"].items() if item["state"] == "confirmed"]
    changed = bt_plan_adapter.planner.sync.retrofit_audit(rdir, cross_check=True, target=audit)
    flow.keep_confirmed(rdir, confirmed, f"auto cross-check of {audit}")
    added = next((c.split(":")[0] for c in changed if "cross-check audit of" in c), "")
    activity.record(rdir, "Plan", f"Se añadió {added}, auditoría cruzada de {audit}: la etapa tenía una sola auditoría "
                    "y la regla del segundo auditor pide dos", kind="flow", sp=add[0] if add else "")
    return changed


def freeze(project: str, rdir: Path, add: list[str]) -> dict:
    """Approve the next stage (the approved subplans plus `add`) and freeze it; returns the manifest entry."""
    import bt_design_drafts as drafts
    import bt_plan_adapter
    import bt_scheduler_adapter
    from bt_requirements_gate import PLANNING_FILES, require_ready

    stage = list(dict.fromkeys([*approved(rdir), *add]))
    _add_second_auditor(rdir, stage, add)
    snapshot, unchanged = _approval_snapshot(rdir, stage)
    if (missing := eligibility(rdir, stage)):
        raise StageError("STAGE_SUBPLAN_UNCONFIRMED", "; ".join(missing))
    unchanged()
    try:
        require_ready(rdir, waive=PLANNING_FILES)
    except SystemExit as exc:
        raise StageError("REQUIREMENTS_REVALIDATION_REQUIRED", str(exc)) from exc
    report = bt_scheduler_adapter.plan_compatibility_report(rdir)
    if (problem := bt_plan_adapter.stage_problem(rdir, add, compatibility_report=report, draft=snapshot)):
        code, _, text = problem.partition(":")
        raise StageError(code.strip(), text.strip())
    try:
        unchanged()
        drafts.pin_for_plan(rdir, refs=_ui_refs(snapshot, stage))      # the stage's designs are approved with it
    except SystemExit as exc:
        raise StageError("STAGE_DESIGN_NOT_READY", str(exc)) from exc
    try:
        return bt_plan_adapter.freeze_stage(rdir, add, compatibility_report=report, draft=snapshot,
                                            before_freeze=unchanged)
    except bt_plan_adapter.planner.PlanContractError as exc:
        raise StageError(exc.code, "; ".join(exc.issues[:5])) from exc


def _start_owner(project: str, req: str, rdir: Path) -> bool:
    """Start (or keep) the unattended owner: the watchdog spawns `scheduler-run` (new run or `--resume`)."""
    import bt_scheduler_ops as ops
    return ops.ensure_watch(project, req, rdir)


def start_or_join(project: str, rdir: Path, *, start: Callable[[str, str, Path], bool] | None = None) -> str:
    """Make the Scheduler run the latest approved stage: a new run, an immediate join of an idle run, or a join at the
    running owner's next quiet point. Never cancels a live attempt."""
    import bt_plan_adapter
    import bt_scheduler_adapter as sa
    import bt_scheduler_ops as ops
    import bt_scheduler_run

    req = _req(rdir)
    if durable_owner(rdir):
        raise StageError("DURABLE_OWNER", DURABLE_REFUSAL)
    start = start or _start_owner
    authority = sa.authority(rdir)
    if authority == "legacy":
        raise StageError("AUTHORITY_CONFLICT", f"{req} has a legacy RUN.json run; the Scheduler does not take it over")
    if (problem := bt_plan_adapter.launch_problem(rdir, forced=True,
                                                  compatibility_report=sa.plan_compatibility_report(rdir))):
        code, _, text = problem.partition(":")
        raise StageError(code.strip(), text.strip())
    if authority != sa.AUTHORITY:
        start(project, req, rdir)
        return "El Scheduler empezó la ejecución."
    if ops.owner_pids(project, req):
        return "La ejecución en curso la incorpora en cuanto terminen los intentos que están corriendo."
    try:
        moved = bt_scheduler_run.join(rdir)
    except sa.core.SchedulerError as exc:
        start(project, req, rdir)
        if exc.code == "JOIN_NEEDS_CONFIRM":
            return (f"Aprobada, pero unirla rehace tareas ya aceptadas: {exc}. Confírmalo con "
                    f"`bitacora.py scheduler-op {req} revise --confirm`.")
        return "La ejecución la incorpora cuando terminen los intentos que siguen vivos."
    start(project, req, rdir)
    return f"La ejecución se unió a la etapa ({moved})." if moved else "La ejecución sigue con la etapa aprobada."


def run(project: str, rdir: Path, add: list[str], *, by: str = "owner", via: str = "web",
        start: Callable[[str, str, Path], bool] | None = None) -> str:
    """«Ejecutar subplan»: approve the stage with `add`, then have the Scheduler run it. Raises StageError."""
    if durable_owner(rdir):          # refused before anything is frozen: the legacy Scheduler may not take a durable run
        raise StageError("DURABLE_OWNER", DURABLE_REFUSAL)
    entry = freeze(project, rdir, add)
    message = start_or_join(project, rdir, start=start)
    stage = entry.get("stage") or {}
    held = ", ".join(stage.get("subplans") or approved(rdir))
    pending = len(stage.get("pending_subplans") or [])
    who = "Tú" if by == "owner" else by
    activity.record(rdir, who, f"Ejecutar {', '.join(add) or 'etapa'}: etapa r{entry['revision']} aprobada ({held})"
                    + (f", faltan {pending} subplanes" if pending else ""), kind="flow", sp=add[0] if add else "")
    return (f"Etapa r{entry['revision']} aprobada con {held}" + (f"; faltan {pending} subplanes por definir. " if pending
                                                                  else ". ") + message)


def info(rdir: Path) -> dict:
    """For pages: approved stages, the subplans the latest one holds and the draft subplans still outside."""
    import bt_plan_adapter
    summary = bt_plan_adapter.stage_summary(rdir)
    held = summary["stages"][-1]["subplans"] if summary["stages"] else []
    draft = bt_plan_adapter.draft_subplans(rdir)
    return {**summary, "held": held, "outside": [s for s in draft or [] if s not in held],
            "revision": summary["stages"][-1]["revision"] if summary["stages"] else None}
