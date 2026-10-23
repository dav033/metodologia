"""Run the bounded stop-diagnosis and repair cycle; repairs and state helpers belong to healing."""
from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path

import bt_scheduler_healing as healing


def cycle(project: str, req: str, rdir: Path | str, *, requests: list[dict] | None = None,
          answer: Callable[..., list[str]] | None = None, revise: Callable[[str], list[str]] | None = None,
          now: Callable[[], float] = time.time, log: Callable[[str], None] = lambda text: None,
          notify: Callable[[str, str], None] | None = None) -> int:
    """Look at the open stops and apply the smallest safe repair to at most `PER_CYCLE` of them. Returns how many it did."""
    rdir = Path(rdir)
    if not healing.enabled(rdir):
        return 0
    import bt_scheduler_decisions as decisions
    import bt_scheduler_ops as ops

    if ops.on_hold(rdir):               # an operator's move is in progress (REQ-029 F15: nothing is frozen under a hold)
        return 0

    try:
        found = requests if requests is not None else decisions.open_requests(rdir)
        doc, plan = decisions._state(rdir), decisions._plan(rdir)
    except Exception:  # noqa: BLE001 - a run without readable state has nothing to heal
        return 0
    answer = answer or (lambda request_id, option, reason: decisions.answer(project, req, rdir, request_id, option, reason, "scheduler"))
    revise = revise or (lambda reason: healing._revise(project, req, rdir, reason))
    state, bound = healing.load(rdir), healing.limits()
    from bitacora_platform import healing_analyst as bt_healing_analyst

    doc, found = bt_healing_analyst.stop_tasks(project, req, rdir, doc, found, state,
                                             enabled=lambda: healing.enabled(rdir), save=lambda: healing.save(rdir, state), log=log)
    done = 0
    for task_id, attempt_id, detail, times in healing.stuck_verifications(rdir, doc):
        if attempt_id in state.setdefault("stuck", []):
            continue
        state["stuck"] = [*state["stuck"], attempt_id][-50:]
        healing.bt_interventions.record(rdir, kind="plan_defect", source="auto", task=task_id,
                                evidence=f"{attempt_id} waits in verifying: the verifier refused its order {times} times ({detail})",
                                repair="none: the owner is told (a plan revision or a fix of the order generator is needed)",
                                result="failed", run=f"{project}-{req}")
        log(f"healing {task_id}: {attempt_id} is stuck in verifying, the verifier refuses its order ({detail}, {times} times)")
        if notify:
            notify(f"Bitácora · {task_id}", f"La verificación de {task_id} ({attempt_id}) no avanza: el verificador rechaza su orden "
                                           f"({detail}) y se reenvía cada pocos minutos. Hace falta una revisión del plan o un arreglo.")
        healing.save(rdir, state)
    for port, detail, times in healing.looping_ports(rdir):
        key = f"{port}:{detail}"[:160]
        if key in state.setdefault("looping", []):
            continue
        state["looping"] = [*state["looping"], key][-50:]
        healing.bt_interventions.record(rdir, kind="plan_defect", source="auto", task="",
                                evidence=f"the owner repeats the same {port} error {times} times in a row ({detail})",
                                repair="none: the owner is told (a plan revision or a fix of the port is needed)",
                                result="failed", run=f"{project}-{req}")
        log(f"healing: the owner loops on a {port} error, {times} times ({detail})")
        if notify:
            notify(f"Bitácora · {req}", f"El scheduler repite el mismo error de {port} ({detail}) y no avanza. Hace falta revisar el plan.")
        healing.save(rdir, state)
    for request in found:
        if done >= healing.PER_CYCLE or state["actions"] >= bound["actions"]:
            break
        try:
            context = decisions._context(rdir, doc, request)
        except Exception:  # noqa: BLE001 - without its context a stop is not diagnosed
            continue
        case = healing.analyst_case(rdir, request) if str(request.get("reason", "")).split(":", 1)[0] == bt_healing_analyst.REASON else None
        case = case or healing.classify_mod.classify(request, verify=context.get("verify", ""), failures=context.get("failures", ()),
                                            plan=plan, doc=doc)
        analysis = healing.analyst_case(rdir, request) if case is None else None
        if analysis is not None:
            case = analysis
        if case is not None:
            # a repair built from the rules' reading alone is blind to what the analyst found (REQ-020 T14.3a: a generic repair, and the
            # live check failed the same way): whatever places the stop, the finished analysis rides along in the repair's objective
            text = healing._analysis_text(rdir, request["task"])
            if text:
                context = {**context, "analysis": text}
        if case is None and (healing.model_enabled() or healing.autonomous_enabled()) and healing.model_eligible(request):
            case = healing.classify_mod.unplaced(request, verify=context.get("verify", ""), failures=context.get("failures", ()))
        if case is None or healing._too_fresh(case, request, doc, now()):
            continue
        if case.signature not in state["cases"] and len(state["cases"]) >= healing.MAX_CASES:
            continue                                   # a flood of distinct error texts cannot grow the record without bound
        entry = state["cases"].setdefault(case.signature, {
            "id": case.signature, "task": case.task, "class": case.kind, "status": "open", "applied": 0,
            "evidence": list(case.evidence), "first_at": round(now(), 3), "history": []})
        task_actions = sum(e["applied"] for e in state["cases"].values()
                           if e["task"] == case.task and e["class"] in healing.REVISING)
        if entry["status"] in ("exhausted", "reverted", "unrepairable"):
            continue
        if not healing.enabled(rdir) or ops.on_hold(rdir):  # an operator's stop landed since the cycle began: it wins
            break
        if entry["applied"] >= healing.REPEATS.get(case.kind, 1) or (case.kind in healing.REVISING and task_actions >= bound["per_task"]):
            healing._give_up(rdir, state, entry, case, request, doc, now(), notify, log,
                     "the same failure came back after its repair" if entry["applied"] else
                     f"{case.task} already had {task_actions} automatic plan repairs")
            continue
        outcome = healing._repair(project, req, rdir, request, case, context, plan, doc, answer, revise)
        if outcome.get("blocker"):
            entry.update(status="unrepairable", blocker=outcome["blocker"], repair=outcome["repair"])
            healing.save(rdir, state)
            log(f"healing {case.task}: no retry ({outcome['blocker']}); apply a real repair revision first")
            continue
        if outcome["repair"] == "none" and healing.model_enabled() and healing.model_eligible(request):
            outcome = healing.model_repair(project, req, rdir, request, case, answer)
            if outcome["repair"] == "wait":            # the diagnosis is not there yet: ask again next cycle, nothing is recorded
                continue
        if outcome["repair"] == "none" and case.kind == "unknown" and healing.autonomous_enabled() and healing.model_eligible(request):
            outcome = healing.autonomous_repair(rdir, request, case, answer)
        entry["history"] = [*entry["history"], {"at": round(now(), 3), "repair": outcome["repair"],
                                                "result": outcome["result"]}][-healing.MAX_HISTORY:]
        if outcome["repair"] == "none":
            entry["status"] = "unrepairable"           # terminal: the card stays for a person and the case is not looked at again
            continue
        if outcome["result"] == "failed" and str(outcome["repair"]).startswith("revision invalid") and entry.get("invalid", 0) < healing.INVALID_TRIES:
            # a revision the planner REFUSED changed nothing: it is not a repair that failed to help, so it must not spend the case (REQ-020
            # T15: the first repair died on the planner lint, the case was marked exhausted, and the task idled all night for a person)
            entry["invalid"] = entry.get("invalid", 0) + 1
            healing.save(rdir, state)
            log(f"healing {case.task} [{case.kind}] {outcome['repair']}: will be tried again")
            continue
        state["actions"] += 1
        done += 1
        entry.update(applied=entry["applied"] + 1, repair=outcome["repair"], at=round(now(), 3),
                     status="applied" if outcome["result"] == "fixed" else "failed", **outcome.get("track", {}))
        healing.bt_interventions.record(rdir, kind=case.kind, source="auto", task=case.task, evidence=case.describe(),
                                repair=outcome["repair"], result=outcome["result"], minutes_lost=healing._minutes(request, doc, now()),
                                run=f"{project}-{req}", case=case.signature)
        log(f"healing {case.task} [{case.kind}] {outcome['repair']}: {outcome['result']}")
        healing.save(rdir, state)
    healing.save(rdir, state)
    return done
