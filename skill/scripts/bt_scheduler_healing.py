"""Self-healing of a Scheduler run: bounded, idempotent, recorded and reversible (REQ-030 step 5, the core of REQ-029).

A run stops on a handful of causes that repeat from night to night (a clash of two parallel tasks, a transient start
failure, a plan check that cannot work, a regression one task's rework introduced in another's tests, a criterion the verifier
cannot map to a check). Until now each one waited for a person, and the person did the same minimal repair every time.
`cycle()` is what the watchdog runs over the open stops:

1. DIAGNOSE with evidence: the last real error, the verifier's notes, the attempt history, the plan and who owns which files
   (`bt_healing_classify`: a closed taxonomy, nothing unplaced is guessed at);
2. REPAIR with the smallest safe move of that class: retry, retry with a note that cites the evidence, redo the task that
   clashed, give a check the exact text of its criterion, or insert a repair task BEFORE a task that can only execute and
   record (`repair_task`);
3. RECORD every decision in `RUN.healing.json` (the case, what was done, when) and in `RUN.interventions.jsonl`
   (`bt_interventions`: class, evidence, repair, result, minutes lost) for the evolution analysis.

Guarantees:

- **Idempotent**: a case is its signature (task, class, decisive error with the volatile parts removed); a restart or a second
  watcher never repeats a repair that was already applied.
- **Bounded**: `healing.max_per_task` actions per task, `healing.max_actions` per run, at most `PER_CYCLE` per cycle. A case
  whose signature comes back after its repair is `exhausted`: the same strategy is never run twice on unchanged evidence, and
  the card stays for the owner with the reason.
- **Honest**: it never touches attempt counters to hide a failure (it only uses the owner's own moves: reopen, rework,
  revise) and every automatic answer is written by `scheduler` in the decisions log, like an owner's.
- **Stoppable and reversible**: `RUN.healing.off` (or `scheduler-op REQ heal stop`) switches it off at once;
  `scheduler-op REQ heal revert CASE` undoes a plan revision it made.
"""
from __future__ import annotations

import copy
import json
import os
import re
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import bt_healing_classify as classify_mod
import bt_interventions

FILE = "RUN.healing.json"
OFF = "RUN.healing.off"
PER_CYCLE = 2
MAX_CASES = 200                 # cases kept in RUN.healing.json (an agent chooses the error text, hence the signatures)
MAX_HISTORY = 10
SETTLE = {"transient": 45.0, "quota": 900.0}      # seconds a stop must have been open before it is answered
REPEATS = {"integration_defect": 3, "transient": 2, "quota": 2}   # times one signature may be repaired (default 1)
REVISING = ("regression", "plan_defect", "criterion_unmapped")    # classes whose repair changes the plan: capped per task
MAX_NOTE = 1500
MODEL_OPTIONS = ("retry", "retry_with_note")      # what a model's diagnosis may do on its own: both are the owner's own, reversible moves
MIN_MODEL_NOTE = 20


# ------------------------------------------------------------------------------------------------ settings and state
def _config(key: str, default):
    import bt_config

    try:
        return bt_config.get(f"healing.{key}", default)
    except (KeyError, TypeError):
        return default


def enabled(rdir: Path | str) -> bool:
    return _config("enabled", True) is True and not (Path(rdir) / OFF).exists()


def limits() -> dict[str, int]:
    def number(key: str, default: int) -> int:
        value = _config(key, default)
        return value if isinstance(value, int) and not isinstance(value, bool) and value >= 1 else default

    return {"per_task": number("max_per_task", 2), "actions": number("max_actions", 40)}


def load(rdir: Path | str) -> dict[str, Any]:
    try:
        data = json.loads((Path(rdir) / FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    if not isinstance(data.get("cases"), dict):
        data["cases"] = {}
    data["cases"] = {k: v for k, v in data["cases"].items() if isinstance(k, str) and isinstance(v, dict)}
    for entry in data["cases"].values():
        entry["applied"] = entry["applied"] if isinstance(entry.get("applied"), int) else 0
        entry["history"] = [h for h in entry.get("history", []) if isinstance(h, dict)][-MAX_HISTORY:] \
            if isinstance(entry.get("history"), list) else []
    if not isinstance(data.get("actions"), int) or isinstance(data["actions"], bool):
        data["actions"] = 0
    return data


def save(rdir: Path | str, data: dict[str, Any]) -> None:
    path = Path(rdir) / FILE
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def stop(rdir: Path | str) -> str:
    (Path(rdir) / OFF).write_text("self-healing stopped by the owner\n", encoding="utf-8")
    return "self-healing is off for this run (`scheduler-op REQ heal start` switches it on)"


def start(rdir: Path | str) -> str:
    (Path(rdir) / OFF).unlink(missing_ok=True)
    return "self-healing is on for this run"


def status(rdir: Path | str) -> dict[str, Any]:
    data = load(rdir)
    return {"enabled": enabled(rdir), "actions": data["actions"], "limits": limits(),
            "cases": {sig: {k: entry.get(k) for k in ("id", "task", "class", "status", "repair", "applied", "revision", "evidence")}
                      for sig, entry in data["cases"].items()}}


# ------------------------------------------------------------------------------------------------ the cycle
def cycle(project: str, req: str, rdir: Path | str, *, requests: list[dict] | None = None,
          answer: Callable[..., list[str]] | None = None, revise: Callable[[str], list[str]] | None = None,
          now: Callable[[], float] = time.time, log: Callable[[str], None] = lambda text: None,
          notify: Callable[[str, str], None] | None = None) -> int:
    """Look at the open stops and apply the smallest safe repair to at most `PER_CYCLE` of them. Returns how many it did."""
    rdir = Path(rdir)
    if not enabled(rdir):
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
    revise = revise or (lambda reason: _revise(project, req, rdir, reason))
    state, bound = load(rdir), limits()
    done = 0
    for task_id, attempt_id, detail, times in stuck_verifications(rdir, doc):
        if attempt_id in state.setdefault("stuck", []):
            continue
        state["stuck"] = [*state["stuck"], attempt_id][-50:]
        bt_interventions.record(rdir, kind="plan_defect", source="auto", task=task_id,
                                evidence=f"{attempt_id} waits in verifying: the verifier refused its order {times} times ({detail})",
                                repair="none: the owner is told (a plan revision or a fix of the order generator is needed)",
                                result="failed", run=f"{project}-{req}")
        log(f"healing {task_id}: {attempt_id} is stuck in verifying, the verifier refuses its order ({detail}, {times} times)")
        if notify:
            notify(f"Bitácora · {task_id}", f"La verificación de {task_id} ({attempt_id}) no avanza: el verificador rechaza su orden "
                                           f"({detail}) y se reenvía cada pocos minutos. Hace falta una revisión del plan o un arreglo.")
        save(rdir, state)
    for request in found:
        if done >= PER_CYCLE or state["actions"] >= bound["actions"]:
            break
        try:
            context = decisions._context(rdir, doc, request)
        except Exception:  # noqa: BLE001 - without its context a stop is not diagnosed
            continue
        case = classify_mod.classify(request, verify=context.get("verify", ""), failures=context.get("failures", ()),
                                     plan=plan, doc=doc)
        if case is None and model_enabled() and model_eligible(request):
            case = classify_mod.unplaced(request, verify=context.get("verify", ""), failures=context.get("failures", ()))
        if case is None or _too_fresh(case, request, doc, now()):
            continue
        if case.signature not in state["cases"] and len(state["cases"]) >= MAX_CASES:
            continue                                   # a flood of distinct error texts cannot grow the record without bound
        entry = state["cases"].setdefault(case.signature, {
            "id": case.signature, "task": case.task, "class": case.kind, "status": "open", "applied": 0,
            "evidence": list(case.evidence), "first_at": round(now(), 3), "history": []})
        task_actions = sum(e["applied"] for e in state["cases"].values()
                           if e["task"] == case.task and e["class"] in REVISING)
        if entry["status"] in ("exhausted", "reverted", "unrepairable"):
            continue
        if ops.on_hold(rdir):                      # an operator's stop landed since the cycle began: it wins, nothing more is done
            break
        if entry["applied"] >= REPEATS.get(case.kind, 1) or (case.kind in REVISING and task_actions >= bound["per_task"]):
            _give_up(rdir, state, entry, case, request, doc, now(), notify, log,
                     "the same failure came back after its repair" if entry["applied"] else
                     f"{case.task} already had {task_actions} automatic plan repairs")
            continue
        outcome = _repair(project, req, rdir, request, case, context, plan, doc, answer, revise)
        if outcome["repair"] == "none" and model_enabled() and model_eligible(request):
            outcome = model_repair(project, req, rdir, request, case, answer)
            if outcome["repair"] == "wait":            # the diagnosis is not there yet: ask again next cycle, nothing is recorded
                continue
        entry["history"] = [*entry["history"], {"at": round(now(), 3), "repair": outcome["repair"],
                                                "result": outcome["result"]}][-MAX_HISTORY:]
        if outcome["repair"] == "none":
            entry["status"] = "unrepairable"           # terminal: the card stays for a person and the case is not looked at again
            continue
        state["actions"] += 1
        done += 1
        entry.update(applied=entry["applied"] + 1, repair=outcome["repair"], at=round(now(), 3),
                     status="applied" if outcome["result"] == "fixed" else "failed", **outcome.get("track", {}))
        bt_interventions.record(rdir, kind=case.kind, source="auto", task=case.task, evidence=case.describe(),
                                repair=outcome["repair"], result=outcome["result"], minutes_lost=_minutes(request, doc, now()),
                                run=f"{project}-{req}", case=case.signature)
        log(f"healing {case.task} [{case.kind}] {outcome['repair']}: {outcome['result']}")
        save(rdir, state)
    save(rdir, state)
    return done


STUCK_VERIFY_REJECTIONS = 3        # the verifier refusing the same order this many times is not going to change its mind


def verify_rejections(rdir: Path, attempt_id: str) -> list[str]:
    """The details of every `dispatch_rejected` of kind `verify` the run's audit log holds for one attempt (oldest first)."""
    import sqlite3

    import bt_scheduler_adapter as adapter

    try:
        conn = sqlite3.connect(f"file:{adapter.run_db_path(Path(rdir))}?mode=ro", uri=True, timeout=2)
        try:
            rows = conn.execute("SELECT detail FROM audit WHERE kind = 'dispatch_rejected' AND attempt_id = ? ORDER BY seq",
                                (attempt_id,)).fetchall()
        finally:
            conn.close()
    except sqlite3.Error:
        return []
    out = []
    for (raw,) in rows:
        try:
            row = json.loads(raw)
        except (TypeError, ValueError):
            continue
        if isinstance(row, dict) and row.get("kind") == "verify":
            out.append(str(row.get("detail") or ""))
    return out


def stuck_verifications(rdir: Path, doc: dict, rejections=None) -> list[tuple[str, str, str, int]]:
    """(task, attempt, detail, times) of the attempts that wait in `verifying` because the verifier keeps refusing the order itself
    (ORDER_INVALID, ORDER_DIFFERS_FROM_APPROVED_PLAN...). The core re-sends the order at every lease expiry, forever: REQ-020's T14.1a
    spent 100+ minutes that way, silently. Seeing it is the first thing; the owner or a plan revision fixes the order."""
    rejections = rejections or verify_rejections
    found = []
    for attempt_id, att in (doc.get("attempts") or {}).items():
        if att.get("state") != "verifying":
            continue
        details = rejections(rdir, attempt_id)
        if len(details) >= STUCK_VERIFY_REJECTIONS and len(set(details[-STUCK_VERIFY_REJECTIONS:])) == 1:
            found.append((att.get("task_id", ""), attempt_id, details[-1], len(details)))
    return found


def model_enabled() -> bool:
    return _config("model_diagnosis", False) is True


def model_eligible(request: dict) -> bool:
    """Only a task stop the owner could answer with a plain retry: never an owner-only decision and never a review (a verdict on
    the work is not a model's to give)."""
    return request.get("source") == "task" and request.get("unskippable") is not True


def model_repair(project: str, req: str, rdir: Path, request: dict, case, answer) -> dict[str, Any]:
    """REQ-029 R3/R4 as a last resort. The diagnosing model (`bt_block_agent`, config `diagnosis.*`) has read the same evidence the
    owner would and picked an offered option; its JSON was validated by `bt_block_agent.parse`. It is acted on only when that option
    is one of `MODEL_OPTIONS`, is offered, the model is not unsure, and a note says something. The model never authorises scope,
    commands or state: it chooses between two moves of the owner's. One try per signature (`REPEATS`), then the owner decides."""
    import bt_block_agent

    options = _options(request)
    agent = request.get("agent")
    if agent is None:
        try:
            import bt_config

            if not bt_config.get("diagnosis.auto"):
                return {"repair": "none", "result": "pending"}      # nobody asks the model: the card stays for a person
            bt_block_agent.spawn(project, req, Path(rdir), request["id"])
        except Exception:  # noqa: BLE001 - no model to ask: the card stays for a person
            return {"repair": "none", "result": "pending"}
        return {"repair": "wait", "result": "pending"}
    if agent.get("state") == "running":
        return {"repair": "wait", "result": "pending"}
    option, note = agent.get("option"), str(agent.get("note") or "").strip()
    if agent.get("state") != "done" or option not in MODEL_OPTIONS or option not in options or agent.get("confidence") == "baja":
        return {"repair": "none", "result": "pending"}
    if option == "retry_with_note" and len(note) < MIN_MODEL_NOTE:
        option = "retry"
    reason = (f"{note}\n\n" if option == "retry_with_note" else "") + \
        f"automatic (model diagnosis, {agent.get('kind', 'unknown')}, confidence {agent.get('confidence', '?')}): {str(agent.get('headline') or '')[:200]}"
    try:
        answer(request["id"], option, reason[:MAX_NOTE])
    except Exception as error:  # noqa: BLE001 - a failed move leaves the card for a person
        return {"repair": f"model diagnosis: {type(error).__name__}: {str(error)[:200]}", "result": "failed"}
    return {"repair": f"{option} chosen by the diagnosing model ({agent.get('model', '?')}): {str(agent.get('headline') or '')[:120]}",
            "result": "fixed"}


def _too_fresh(case: classify_mod.Case, request: dict, doc: dict, now: float) -> bool:
    settle = SETTLE.get(case.kind, 0.0)
    attempt = doc.get("attempts", {}).get(request.get("attempt", ""), {})
    stamp = attempt.get("updated_at") or attempt.get("created_at") or 0.0
    return bool(settle and stamp and now - float(stamp) < settle)


def _minutes(request: dict, doc: dict, now: float) -> float | None:
    attempt = doc.get("attempts", {}).get(request.get("attempt", ""), {})
    stamp = attempt.get("updated_at")
    return max(0.0, (now - float(stamp)) / 60) if stamp else None


def _give_up(rdir, state, entry, case, request, doc, now, notify, log, why: str) -> None:
    entry["status"] = "exhausted"
    entry["why"] = why
    bt_interventions.record(rdir, kind=case.kind, source="auto", task=case.task, evidence=case.describe(),
                            repair=f"none: {why}", result="failed", minutes_lost=_minutes(request, doc, now), case=case.signature)
    log(f"healing {case.task} [{case.kind}] gave up: {why}")
    if notify:
        notify(f"Bitácora · {case.task}", f"La autocuración no pudo arreglar {case.task} ({case.kind}): {why}. Decide tú.")
    save(rdir, state)


# ------------------------------------------------------------------------------------------------ repairs
def _options(request: dict) -> set[str]:
    return {o["id"] for o in request.get("options") or ()}


def _repair(project, req, rdir, request, case, context, plan, doc, answer, revise) -> dict[str, Any]:
    """The smallest safe move for this class; {"repair": "none"} when there is none."""
    options, request_id, kind = _options(request), request["id"], case.kind
    cite = "; ".join(case.evidence[:2])
    try:
        if kind in ("transient", "quota"):
            option = "review_fail" if request.get("source") == "review" else "retry"
            if option in options:
                answer(request_id, option, f"automatic ({kind}): {cite}")
                return {"repair": f"retry ({kind})", "result": "fixed"}
        elif kind == "integration_defect":
            diagnosis = request.get("diagnosis") or {}
            if diagnosis.get("option") == "rework_conflict" and diagnosis.get("confidence") == "alta" and "rework_conflict" in options:
                answer(request_id, "rework_conflict", "automatic: " + str(diagnosis.get("headline") or "integration clash"))
                return {"repair": "redo the task built on the stale result", "result": "fixed"}
        elif kind == "environment":
            if _workspace_full(rdir, case) and "retry" in options:
                import bt_config

                now = bt_config.get("verifier.max_workspace_mb", 2048)
                bigger = min(int(now) * 2, WORKSPACE_CAP_MB) if isinstance(now, int) else 4096
                if bigger > now:
                    bt_config.set_value("verifier.max_workspace_mb", bigger)
                    answer(request_id, "retry", f"automatic: the verifier workspace was full; max_workspace_mb {now} -> {bigger}")
                    return {"repair": f"verifier.max_workspace_mb {now} -> {bigger}, retry", "result": "fixed"}
            note = (request.get("diagnosis") or {}).get("note")
            if note and "retry_with_note" in options:
                answer(request_id, "retry_with_note", f"{note}\n\nEvidence the system found: {cite}")
                return {"repair": "retry with a note that cites the evidence", "result": "fixed"}
        elif kind == "criterion_unmapped":
            return _fix_mapping(project, req, rdir, request, case, plan, answer, revise)
        elif kind == "regression" and "audit gate:" in context.get("verify", "") + str(request.get("error")):
            import bt_remediation

            if "retry" in options and bt_remediation.grant_round(rdir, request["task"]):
                answer(request_id, "retry", "automatic: one more remediation round for the audit instead of sending accepted tasks back")
                return {"repair": "one more remediation round, then the audit looks again", "result": "fixed"}
        elif kind in ("regression", "plan_defect"):
            return repair_task(project, req, rdir, request, case, context, plan, revise)
    except Exception as error:  # noqa: BLE001 - a repair that fails leaves the card for a person
        return {"repair": f"{kind}: {type(error).__name__}: {str(error)[:200]}", "result": "failed"}
    return {"repair": "none", "result": "pending"}


WORKSPACE_CAP_MB = 8192


def _workspace_full(rdir: Path, case) -> bool:
    """ENOSPC while the HOST has room: the verifier's private workspace (a tmpfs) is the one that is full, and that is a
    setting, not the owner's disk. A really full disk is never "repaired" (nothing of the owner's is deleted)."""
    import shutil

    if not any("ENOSPC" in e or "No space left" in e or "space" in e for e in case.evidence):
        return False
    try:
        return shutil.disk_usage(rdir).free > 5 << 30
    except OSError:
        return False


def _fix_mapping(project, req, rdir, request, case, plan, answer, revise) -> dict[str, Any]:
    """A verifier that cannot map evidence to a criterion: when every criterion already passed and only an extra check is
    unmapped, accept (all the proof is there); when exactly one check's purpose is the criterion's text with other
    spelling, give the check the criterion's exact text in a new plan revision."""
    evidence = [str(e) for e in request.get("evidence") or ()]
    criteria = [e for e in evidence if e.startswith("criterio ")]
    issues = {e.split(":", 1)[0] for e in evidence if e[:1].isupper() and ":" in e and "_" in e.split(":", 1)[0]}
    if criteria and all(e.startswith("criterio PASS") for e in criteria) and issues <= {"CHECK_UNMAPPED"} \
            and not any(" → fail" in e or " → unknown" in e for e in evidence) and "review_pass" in _options(request):
        answer(request["id"], "review_pass", f"automatic: all {len(criteria)} criteria PASS and every command check passed; "
                                             "only an extra check names no criterion (CHECK_UNMAPPED)")
        return {"repair": "accept: every criterion proved, only an extra check unmapped", "result": "fixed"}
    checks = [e for e in evidence if " → " in e and not e.startswith("criterio ")]
    if (len(criteria) == 1 and criteria[0].startswith("criterio UNKNOWN") and issues <= {"CRITERION_UNVERIFIABLE", "CHECK_UNMAPPED"}
            and checks and all(e.endswith("→ pass") or "→ pass (" in e for e in checks) and "review_pass" in _options(request)):
        answer(request["id"], "review_pass", f"automatic: the task's single criterion has no check with its exact text, but all {len(checks)} "
                                             "command checks passed and none is left over for another criterion (mapping by elimination)")
        return {"repair": "accept by elimination: one criterion, every command check passed", "result": "fixed"}
    if plan is None:
        return {"repair": "none", "result": "pending"}
    latest = _latest_plan(rdir)
    revised = remap_purposes(latest, request["task"]) if latest else None
    if revised is None:
        return {"repair": "none", "result": "pending"}
    _freeze(rdir, revised, "healing")
    lines = revise(f"healing: give the checks of {request['task']} the exact text of their criteria")
    return {"repair": f"plan r{revised['revision']}: checks of {request['task']} renamed to their criteria", "result": "fixed",
            "track": {"revision": revised["revision"], "lines": lines[-2:]}}


def remap_purposes(plan: dict, task_id: str) -> dict | None:
    """A copy of `plan` where each command check of `task_id` whose purpose matches no criterion gets the text of the one
    unmatched criterion it spells differently (same words, other case/punctuation/spacing). None when nothing changes or any
    pairing is not unique."""
    import difflib
    import re

    task = next((t for t in plan.get("tasks", []) if t.get("id") == task_id), None)
    if task is None:
        return None
    criteria = list(task.get("acceptance_criteria") or ())
    loose = lambda s: re.sub(r"[\W_]+", " ", s.lower()).strip()  # noqa: E731
    unmatched_criteria = [c for c in criteria if not any(v.get("purpose") == c for v in task.get("verification", ()))]
    unmatched_checks = [v for v in task.get("verification", ()) if v.get("purpose") not in criteria and v.get("type") == "command"]
    if not unmatched_criteria or not unmatched_checks:
        return None
    pairs = {}
    for check in unmatched_checks:
        scored = sorted(((difflib.SequenceMatcher(None, loose(check.get("purpose", "")), loose(c)).ratio(), c)
                         for c in unmatched_criteria), reverse=True)
        if scored[0][0] < 0.75 or (len(scored) > 1 and scored[1][0] >= scored[0][0] - 0.05):
            return None
        pairs[id(check)] = scored[0][1]
    if len(set(pairs.values())) != len(pairs):
        return None
    revised = copy.deepcopy(plan)
    target = next(t for t in revised["tasks"] if t["id"] == task_id)
    originals = {id(c): c for c in unmatched_checks}
    for index, check in enumerate(target["verification"]):
        for key, original in originals.items():
            if check == original:
                target["verification"][index] = {**check, "purpose": pairs[key]}
    revised["revision"] = int(plan.get("revision") or 0) + 1
    return revised


def repair_task(project, req, rdir, request, case, context, plan, revise) -> dict[str, Any]:
    """A task that can only execute and record cannot fix the code its checks run over, and a regression is not the
    blocked task's to fix: insert a REPAIR task before it, built from the evidence, and revise the run onto the new plan."""
    import bt_plan_adapter

    latest = _latest_plan(rdir)
    if latest is None:
        return {"repair": "none", "result": "pending"}
    built = build_fix_revision(latest, request["task"], case, context)
    if built is None:
        return {"repair": "none", "result": "pending"}
    revised, new_id, restored = built
    errors = bt_plan_adapter.plan_errors(revised)
    if errors:
        return {"repair": f"revision invalid: {errors[0][:160]}", "result": "failed"}
    _freeze(rdir, revised, "healing")
    track = {"revision": revised["revision"], "task_added": new_id, "after_restored": restored, "target": request["task"]}
    try:
        lines = revise(f"healing: {new_id} repairs what blocks {request['task']} ({case.kind})")
    except Exception as error:  # noqa: BLE001 - the revision is frozen but not applied: keep what `revert` needs to undo it
        return {"repair": f"plan r{revised['revision']} frozen but not applied: {type(error).__name__}: {str(error)[:160]}",
                "result": "failed", "track": track}
    return {"repair": f"plan r{revised['revision']}: repair task {new_id} before {request['task']}", "result": "fixed",
            "track": {**track, "lines": lines[-2:]}}


_SIGNAL = re.compile(r"FAIL|ERROR|Error|error|Expected|Assertion|!==|not ok|✖|✗|Cannot|cannot|Traceback|Exception")


def excerpt(text: str, limit: int = 700) -> str:
    """What failed, for the objective of a repair task: the commands that RAN and failed (a numeric exit code; a check that never ran
    says `None` and is not this task's to fix) with the few lines that say why. A real note carries pages of server logs; the planner
    refuses an objective that repeats the same words, and an agent does not need the logs to know what to fix."""
    blocks = re.split(r"(?m)^(?=\$ )", str(text or ""))
    out: list[str] = []
    for block in blocks:
        head, _, body = block.partition("\n")
        code = re.match(r"exit code (-?\d+)\b", body.lstrip())
        if not head.startswith("$ ") or not code or code.group(1) == "0":
            continue
        lines = [line.strip()[:160] for line in body.splitlines()[1:]
                 if _SIGNAL.search(line) and not line.lstrip().startswith(("{", "npm notice"))]
        out.append(head[:200] + f"\nexit code {code.group(1)}" + ("".join("\n" + line for line in dict.fromkeys(lines[:6]))))
    return "\n".join(out)[:limit] or str(text or "")[:min(limit, 400)]


def build_fix_revision(plan: dict, task_id: str, case: classify_mod.Case, context: dict) -> tuple[dict, str, list[str]] | None:
    """(revised plan, new task id, the target's previous `after`) or None when the evidence cannot make a sound task."""
    import bt_remediation

    by_id = {t["id"]: t for t in plan.get("tasks", []) if isinstance(t, dict) and isinstance(t.get("id"), str)}
    target = by_id.get(task_id)
    if target is None:
        return None
    owners = [o for o in case.owners if o in by_id]
    named = owners or [task_id]
    failure = excerpt(context.get("verify") or next((f for f in reversed(context.get("failures") or ()) if f), ""))
    summary = (f"{task_id} cannot pass its checks: " + (f"tests of {', '.join(owners)} fail ({', '.join(case.failing[:4])})"
                                                        if owners else f"it only runs and records, and {', '.join(case.failing[:4]) or 'its checks'} fail"))
    finding = {"id": "H1", "severity": "high", "summary": summary[:300], "tasks": named,
               "evidence": "the failing command and its output, quoted once in the objective above", "status": "open"}
    chunk = [finding]
    new_id = bt_remediation._next_ids(set(by_id), task_id, 1)[0]
    spec_ref = str(plan.get("spec_ref") or "SPEC.md").split(":")[-1]
    # the owners' own checks (all of them, not only the first) plus the blocked task's own, stated by this repair
    own_commands = [[{"command": v["value"]} for name in named for v in by_id[name].get("verification", ())
                     if v.get("type") == "command" and v.get("value")]]
    fix = bt_remediation._task(new_id, target, chunk, by_id, list(target.get("after") or ()), 1, spec_ref, plan,
                               commands=own_commands if own_commands[0] else None)
    if fix is None:
        return None
    own = [v for v in target.get("verification", ()) if v.get("type") == "command"]
    for number, check in enumerate(own, 1):
        purpose = f"{task_id}'s own check {number} passes: {check['value'][:140]}"
        fix["acceptance_criteria"].append(purpose)
        fix["verification"].append({**check, "purpose": purpose, "category": check.get("category") or "functional"})
    fix["title"] = f"Repair what blocks {task_id}"[:120]
    fix["objective"] = (f"{summary}. Fix the PRODUCTION code so the failing checks pass; do not edit or delete the failing "
                        f"tests unless the test itself is the defect, and say which one was. Evidence from the last "
                        f"verification:\n{failure}\n" + fix["objective"].split("\n", 1)[-1])[:6000]
    fix["kind"] = "implement"
    revised = copy.deepcopy(plan)
    revised["revision"] = int(plan.get("revision") or 0) + 1
    restored = list(target.get("after") or ())
    for task in revised["tasks"]:
        if task["id"] == task_id:
            task["after"] = list(dict.fromkeys([*restored, new_id]))
    revised["tasks"] = [*revised["tasks"], fix]
    return revised, new_id, restored


def revert(project: str, req: str, rdir: Path | str, case_id: str, *,
           revise: Callable[[str], list[str]] | None = None) -> list[str]:
    """Undo a plan revision the healing made: drop the repair task, restore the `after` it changed, freeze that as the next
    revision and move the run onto it. The case becomes `reverted` and is never applied again."""
    import bt_plan_adapter

    rdir = Path(rdir)
    state = load(rdir)
    entry = state["cases"].get(case_id)
    if entry is None or not entry.get("task_added"):
        raise ValueError(f"case {case_id} made no plan revision to revert (see `scheduler-op REQ heal status`)")
    if entry.get("status") == "reverted":
        return [f"case {case_id} was already reverted"]
    latest = _latest_plan(rdir)
    if latest is None:
        raise ValueError("no frozen plan to revert on")
    added = entry["task_added"]
    by_id = {t["id"]: t for t in latest.get("tasks", []) if isinstance(t, dict)}
    if added not in by_id or not re.fullmatch(r"T[0-9]+\.[0-9]+[a-z]?", str(added)):
        raise ValueError(f"{added} is not a repair task of the current plan: nothing to revert")
    if by_id[added].get("recovery_task") is not True and "Repair what blocks" not in str(by_id[added].get("title", "")) \
            and "Remediate" not in str(by_id[added].get("title", "")):
        raise ValueError(f"{added} was not made by the self-healing: refusing to remove it")
    if _is_accepted(rdir, added):
        raise ValueError(f"{added} is already accepted: its work stays; reopen the plan by hand if it must go")
    revised = copy.deepcopy(latest)
    revised["tasks"] = [t for t in revised["tasks"] if t["id"] != added]
    for task in revised["tasks"]:                  # only the repair task leaves the prerequisites: every other edge stays as it is now
        if added in (task.get("after") or ()):
            task["after"] = [a for a in task["after"] if a != added]
    revised["revision"] = int(latest.get("revision") or 0) + 1
    errors = bt_plan_adapter.plan_errors(revised)
    if errors:
        raise ValueError(f"the reverted plan is not valid: {errors[0][:200]}")
    _freeze(rdir, revised, "healing-revert")
    lines = (revise or (lambda why: _revise(project, req, rdir, why)))(f"healing revert of case {case_id}")
    entry["status"] = "reverted"
    save(rdir, state)
    bt_interventions.record(rdir, kind=entry["class"], source="manual", task=entry["task"], evidence=f"revert of case {case_id}",
                            repair=f"plan r{revised['revision']} without {entry['task_added']}", result="fixed", case=case_id)
    return [f"plan r{revised['revision']}: {entry['task_added']} removed, {entry.get('target')} back to its previous prerequisites",
            *lines]


def _is_accepted(rdir: Path, task_id: str) -> bool:
    """True when the run already accepted `task_id` (the state is read from the run's own database)."""
    try:
        import bt_scheduler_decisions

        return bt_scheduler_decisions._state(Path(rdir)).get("tasks", {}).get(task_id, {}).get("state") == "completed"
    except Exception:  # noqa: BLE001 - no readable run, nothing accepted
        return False


def _latest_plan(rdir: Path):
    import bt_plan_adapter

    return bt_plan_adapter.latest_plan(rdir)


def _freeze(rdir: Path, plan: dict, source: str):
    import bt_plan_adapter

    return bt_plan_adapter.freeze_revision(rdir, plan, source)


def _revise(project: str, req: str, rdir: Path, reason: str) -> list[str]:
    import bt_scheduler_ops as ops

    return ops.apply(project, req, rdir, "revise", "", reason)
