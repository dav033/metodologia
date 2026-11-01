"""Self-healing of a durable run's decisions (D-167: REQ-029 R3/R4 in the durable runtime).

The legacy Scheduler answered a stop the owner could answer with a plain retry by asking a diagnosing model
(`bt_scheduler_healing.model_repair`, config `healing.model_diagnosis`). The durable runtime that took the runs over
(REQ-030) only opened the decision and waited for a person: pictures REQ-021, 2026-10-29, T4.2, T7.4 and T93 each
waited for the operator. Here the engine's maintenance pass does it for durable runs. An open decision gets a diagnosis
from the same agent (`bt_block_agent`, config `diagnosis.*`), in a background thread; on a later pass its validated
choice, `retry` or `retry_with_note` only, is sent as the answer to that exact round, once per failure signature and
task, within `healing.max_per_task` and `healing.max_actions`. A diagnosis that blames the plan goes to the run's
Planner with its evidence, and the decision stays for a person: changing the plan is not a model's call. Everything
happens outside the workflows: the order of steps in bt.run/bt.task is unchanged.

Every decision healing leaves for a person (limit reached, diagnosis failed, unsure or unoffered choice, the plan
blamed, no retry offered) and every failure signature that comes back after its retry is handed once to `escalate`:
the Solucionador (`bt_durable.solver`, REQ-031), the next rung.
"""
from __future__ import annotations

import json
import logging
import re
import threading
import time
from collections.abc import Callable, Iterable
from pathlib import Path

from bt_contracts.execution import RunRef

LOG = logging.getLogger("bt_durable.healing")
STATE = "RUN.durable-healing.json"           # RUN.healing.json is the legacy Scheduler's
MODEL_OPTIONS = ("retry", "retry_with_note")     # the owner's own reversible moves; never stop, reverify or a route
MIN_NOTE = 20
OPTIONS = {"retry": "a new attempt of the task from its last snapshot",
           "retry_with_note": "a new attempt with your note first in its prompt",
           "retry_other_route": "a new attempt on another model or account",
           "reverify": "verify the same snapshot again (only after its manual checks were attested)",
           "stop": "stop the task"}
# decisions about the environment itself: a new agent run does not fix them, the owner does (D-265)
OWNER_ENV_CODES = frozenset({"AGENT_ENV_UNREACHABLE"})
# the agent's final message says a check could not be run, or why (pictures REQ-021 r32 T3.91 a5..a7: «la URL de prueba
# apunta al puerto 55965, que rechazó la conexión … el smoke real de navegador queda pendiente»), D-265
_NOT_RUN = re.compile(
    r"connection refused|ECONNREFUSED|refused (?:the |a )?connection|could ?n[o']t (?:run|connect|reach|start)|"
    r"cannot (?:run|connect|reach)|can't (?:run|connect|reach)|unable to (?:run|connect|reach)|"
    r"did ?n[o']t (?:run|execute)|(?:was|were|has|have) ?n[o']t (?:been )?(?:run|executed)\b|(?:remains?|left|still) pending|"
    r"rechaz[óoa]\w* (?:la )?conexi[óo]n|conexi[óo]n rechazada|no (?:se )?(?:pud[oe]|puedo|pudimos) (?:ejecutar|correr|"
    r"conectar|lanzar|arrancar)|no (?:ejecut[ée]|corr[ií]|lanc[ée])\b|no se (?:ejecut[óo]|corri[óo])|"
    r"(?<!no )(?:queda|quedan|qued[óo]|quedaron|sigue|siguen)\s+(?:\w+\s+){0,2}pendientes?\b", re.IGNORECASE)
_running: set[str] = set()
_lock = threading.Lock()


def enabled() -> bool:
    import bt_config
    return all(bt_config.get(key) is True for key in ("healing.enabled", "healing.model_diagnosis", "diagnosis.auto"))


def _limit(name: str, default: int) -> int:
    import bt_config
    value = bt_config.get(f"healing.{name}", default)
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else default


def runs(root: Path) -> Iterable[tuple[Path, RunRef]]:
    for path in sorted(Path(root).glob("*/requirements/*/RUN.durable-run.json")):
        try:
            yield path.parent, RunRef.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue


def load(rdir: Path) -> dict:
    try:
        data = json.loads((Path(rdir) / STATE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    return data if isinstance(data, dict) else {}


def save(rdir: Path, data: dict) -> None:
    target = Path(rdir) / STATE
    tmp = target.with_name(f".{target.name}.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    tmp.replace(target)


def round_of(item: dict) -> int | None:
    found = re.search(r":k(\d+)$", str(item.get("workflow_id") or ""))
    return int(found.group(1)) if found else None


def attempt_facts(client, decision: dict) -> dict:
    """The decided attempt as it ended (`verify_attempt` of the request): whether it changed anything and the agent's
    final message. pictures REQ-021 r32 T2.57: the diagnosis saw only the failing check and told three retries to add an
    npm script, while every attempt had changed nothing and its agent had said why it stopped (D-262). {} when the
    request names no attempt of this runtime or its output cannot be read."""
    key = str(decision.get("verify_attempt") or "")
    reader = getattr(client, "attempt_output", None)
    if not key or reader is None:
        return {}
    try:
        output = reader(key)
    except Exception as error:  # noqa: BLE001 - evidence only: the diagnosis goes on without it
        LOG.warning("healing: attempt %s unreadable: %s", key, type(error).__name__)
        return {}
    snapshot = output.get("snapshot") if isinstance(output.get("snapshot"), dict) else {}
    agent = output.get("agent") if isinstance(output.get("agent"), dict) else {}
    if not snapshot and not agent:
        return {}
    changed = list(snapshot.get("changed_paths") or ())
    unchanged = bool(snapshot.get("snapshot_sha")) and (snapshot.get("snapshot_sha") == snapshot.get("base_sha")
                                                        or not changed)
    message = str(agent.get("text") or "")
    return {"attempt": key, "unchanged": unchanged, "changed": len(changed), "agent_status": agent.get("status"),
            "agent_message": message[-1500:], "checks_not_run": checks_not_run(message)}


def checks_not_run(message: str) -> bool:
    """The agent's final message says it could not run a check (a refused connection, «no ejecuté», «queda pendiente»):
    the failing checks were never reproduced by the agent, so a code guess does not answer them (D-265)."""
    return bool(_NOT_RUN.search(message or ""))


def evidence(run: RunRef, rdir: Path, task_id: str, decision: dict, round_no: int | None,
             facts: dict | None = None) -> str:
    """What a person answering the decision would read: the failure, the task, its dependencies and its attempts, and
    (`facts`, `attempt_facts`) what the decided attempt changed and its agent's final message."""
    try:
        plan = json.loads(Path(run.plan_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        plan = {}
    task = next((t for t in plan.get("tasks") or [] if isinstance(t, dict) and t.get("id") == task_id), {})
    failure = decision.get("failure") or {}
    offered = [o for o in decision.get("options") or () if o in OPTIONS]
    lines = [f"Run {run.run_id}, task {task_id}: {task.get('title') or ''}",
             f"Subplan: {task.get('subplan_id') or '-'}; depends on: {', '.join(task.get('after') or []) or 'nothing'}",
             f"Objective: {task.get('objective') or ''}",
             "Acceptance criteria:", *[f"- {c}" for c in task.get("acceptance_criteria") or []],
             "Checks:", *[f"- {c.get('value')} ({c.get('category', '')}; requires {', '.join(c.get('requires') or []) or '-'})"
                          for c in task.get("verification") or [] if isinstance(c, dict)],
             f"Decision {decision.get('request_id')} (round k{round_no}): {decision.get('reason')}; limit {decision.get('limit_hit') or '-'}",
             f"Failure: {failure.get('failure_class')} {failure.get('code')}: {failure.get('summary')}",
             "Offered options in this runtime:", *[f"- {o}: {OPTIONS[o]}" for o in offered],
             "Failure evidence:", *[str(e.get("excerpt") or "")[:2500] for e in failure.get("evidence") or [] if isinstance(e, dict)]]
    if facts and facts.get("checks_not_run"):
        lines.insert(0, "THE AGENT SAYS IT COULD NOT RUN ITS CHECKS (its final message is below): the failing checks "
                        "were not reproduced by the agent, most likely because of its environment (a refused "
                        "connection, a missing service). This is an environment question for the operator, not a "
                        "code defect to guess at.")
    if facts:
        lines += [f"Decided attempt {facts.get('attempt')}: " + (
                      "it changed NOTHING (its snapshot is the tree it started from): the failing checks ran on the "
                      "unchanged tree, so they say nothing about the agent's code; read why the agent stopped"
                      if facts.get("unchanged") else f"it changed {facts.get('changed')} file(s)"),
                  (f"The agent's final message ({facts.get('agent_status') or '?'}): "
                   f"{facts.get('agent_message') or '(none)'}")]
    history = Path(rdir) / "RUN.notes" / f"{task_id}.history.jsonl"
    try:
        rows = [json.loads(line) for line in history.read_text(encoding="utf-8").splitlines() if line.strip()][-4:]
    except (OSError, ValueError):
        rows = []
    if rows:
        lines += ["Earlier attempts (oldest first):"] + [f"- {r.get('attempt', '')} {r.get('kind', '')}: "
                                                         f"{str(r.get('text') or '')[:1200]}" for r in rows]
    return "\n".join(str(line) for line in lines)


def heal(root: Path, client, *, diagnose: Callable | None = None, notify: Callable | None = None,
         start: Callable[[Callable[[], object]], None] | None = None,
         escalate: Callable[[dict], object] | None = None) -> list[str]:
    """One maintenance pass over every durable run's open decisions. Returns what it did (for the engine log).
    `escalate(trigger)` receives, once per decision round, what this pass leaves for a person (`solver.trigger`)."""
    if not enabled():
        return []
    import bt_block_agent
    diagnose = diagnose or bt_block_agent.diagnose
    start = start or (lambda job: threading.Thread(target=job, daemon=True, name="bt-healing").start())
    escalate = escalate or (lambda trigger: None)
    if notify is None:
        import bt_agent_terminal
        notify = bt_agent_terminal.notify_planner
    said: list[str] = []
    for rdir, run in runs(root):
        try:
            status = client.status(run)
        except Exception as error:  # noqa: BLE001 - a run that cannot be read is tried on the next pass
            LOG.warning("healing: %s status failed: %s", run.run_id, error)
            continue
        state = load(rdir)
        before = json.dumps(state, sort_keys=True)
        for task_id, item in sorted((status.get("tasks") or {}).items()):
            decision = (item or {}).get("decision")
            if isinstance(decision, dict) and decision.get("request_id"):
                said += _one(run, rdir, state, task_id, item, decision, client, diagnose, notify, start, escalate)
        if json.dumps(state, sort_keys=True) != before:
            save(rdir, state)
    return said


def _left(run, task_id, decision, round_no, key, kind, reason) -> dict:
    return {"kind": kind, "key": key, "run_id": run.run_id, "task_id": task_id,
            "request_id": decision["request_id"], "round": round_no, "reason": reason[:400]}


def _one(run, rdir, state, task_id, item, decision, client, diagnose, notify, start, escalate) -> list[str]:
    import bt_block_agent
    import bt_planning_activity as activity
    offered = [o for o in decision.get("options") or () if o in OPTIONS]
    round_no = round_of(item)
    key = f"{run.run_id}:{task_id}:{decision['request_id']}@k{round_no}"
    if key in state.setdefault("seen", []):
        return []
    if not set(MODEL_OPTIONS) & set(offered):
        state["seen"].append(key)
        escalate(_left(run, task_id, decision, round_no, key, "decision",
                       f"no retry is offered ({', '.join(offered) or 'no option'}): {decision.get('reason') or ''}"))
        return [f"{key}: no retry offered, left to the owner"]
    signature = str((decision.get("failure") or {}).get("signature") or decision.get("reason") or "")
    entry = state.setdefault("tasks", {}).setdefault(task_id, {"signatures": {}})
    if signature in entry["signatures"]:
        state["seen"].append(key)
        escalate(_left(run, task_id, decision, round_no, key, "repeat",
                       f"the failure healing already answered came back ({signature[:80]}): {decision.get('reason') or ''}"))
        return [f"{key}: the same failure again, left to the owner"]
    facts = attempt_facts(client, decision)
    code = str((decision.get("failure") or {}).get("code") or "")
    if code in OWNER_ENV_CODES or facts.get("checks_not_run"):
        # an unreachable test resource, or an agent that could not run its checks: another run of an agent answers
        # nothing (pictures REQ-021 r32 T3.91: healing guessed a locator and floor hit-testing), D-265
        state["seen"].append(key)
        why = (f"the environment stopped the start ({code})" if code in OWNER_ENV_CODES else
               "the agent says it could not run its checks: " + str(facts.get("agent_message") or "")[-200:])
        activity.record(rdir, "Autocuración", f"{task_id}: {decision['request_id']} queda para ti: "
                        + ("un recurso de prueba no responde" if code in OWNER_ENV_CODES else
                           "el agente no pudo ejecutar sus checks (entorno)"), kind="flow")
        escalate(_left(run, task_id, decision, round_no, key, "decision",
                       f"{why}; {decision.get('reason') or ''}"))
        return [f"{key}: environment, left to the owner"]
    again = [record for record in entry["signatures"].values() if record.get("option") and record.get("unchanged")
             and record.get("code") == code and record.get("round") == round_no]
    if facts.get("unchanged") and again:
        # its last answer was followed by the same failure and again an attempt that changed nothing: another retry with
        # a note would loop (pictures REQ-021 r32 T2.57 d1..d3, D-262); the operator and the Solucionador decide
        state["seen"].append(key)
        activity.record(rdir, "Autocuración", f"{task_id}: tras mi respuesta anterior el intento volvió a no cambiar "
                        f"nada; {decision['request_id']} queda para ti", kind="flow")
        escalate(_left(run, task_id, decision, round_no, key, "repeat",
                       f"healing's answer {again[-1].get('request', '')} was followed by the same failure ({code}) and "
                       f"again an attempt that changed nothing; the agent said: {facts.get('agent_message', '')[-200:]}"))
        return [f"{key}: no change again after healing's answer, left to the owner"]
    if len(entry["signatures"]) >= _limit("max_per_task", 2) or int(state.get("actions", 0)) >= _limit("max_actions", 40):
        state["seen"].append(key)
        activity.record(rdir, "Autocuración", f"{task_id}: {decision['request_id']} queda para ti (límite de "
                        "reparaciones automáticas alcanzado)", kind="flow")
        escalate(_left(run, task_id, decision, round_no, key, "decision", "healing's repair limit is reached"))
        return [f"{key}: limit reached"]
    found = bt_block_agent.cached(rdir, key)
    if found is None:
        with _lock:
            if key in _running:
                return []
            _running.add(key)
        request = {"id": key, "options": [{"id": o} for o in offered], "recommended": "retry"}
        text = evidence(run, rdir, task_id, decision, round_no, facts)

        def job() -> None:
            try:
                diagnose(run.project, rdir, request, text)
            finally:
                with _lock:
                    _running.discard(key)
        start(job)
        return [f"{key}: diagnosing"]
    if found.get("state") == "running":
        return []
    state["seen"].append(key)
    if found.get("state") != "done":
        activity.record(rdir, "Autocuración", f"{task_id}: no se pudo diagnosticar {decision['request_id']} "
                        f"({str(found.get('error') or '')[:120]}); queda para ti", kind="flow")
        escalate(_left(run, task_id, decision, round_no, key, "decision",
                       f"the diagnosis failed: {str(found.get('error') or '')[:200]}"))
        return [f"{key}: diagnosis failed"]
    headline = str(found.get("headline") or "")[:160]
    if found.get("kind") == "plan":
        steps = " ".join(f"{n}. {s}" for n, s in enumerate(found.get("steps") or [], 1))
        notify(run.project, run.req, f"Self-healing diagnosis of {task_id} ({decision['request_id']}, {run.run_id}) "
               f"blames the plan: {headline}. {found.get('origin') or ''} Steps: {steps} Revise the plan (type the "
               "missing dependency or fix the check), validate it and tell the owner which subplans need "
               "re-confirmation. The decision stays open for the owner.")
        entry["signatures"][signature] = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "planner": key}
        activity.record(rdir, "Autocuración", f"{task_id}: el diagnóstico culpa al plan ({headline}); se lo pasé al "
                        f"Planner y {decision['request_id']} queda para ti", kind="flow")
        escalate(_left(run, task_id, decision, round_no, key, "decision",
                       f"the diagnosis blames the plan and healing told the Planner: {headline}"))
        return [f"{key}: sent to the Planner"]
    option, note = found.get("option"), str(found.get("note") or "").strip()
    if option not in MODEL_OPTIONS or option not in offered or found.get("confidence") == "baja":
        activity.record(rdir, "Autocuración", f"{task_id}: el diagnóstico no basta para decidir solo "
                        f"({option or '-'}, confianza {found.get('confidence') or '?'}); {decision['request_id']} queda "
                        "para ti", kind="flow")
        escalate(_left(run, task_id, decision, round_no, key, "decision",
                       f"the diagnosis is not enough to answer alone (option {option or '-'}, confidence "
                       f"{found.get('confidence') or '?'}): {headline}"))
        return [f"{key}: left to the owner"]
    if option == "retry_with_note" and len(note) < MIN_NOTE:
        option, note = "retry", ""
    from bt_contracts.owner import OwnerAnswer
    try:
        client.answer(run, task_id, OwnerAnswer(request_id=decision["request_id"], action=option,
                                                note=note if option == "retry_with_note" else "", by="healing"),
                      round_no=round_no)
    except Exception as error:  # noqa: BLE001 - a round that moved on, or a refused answer: the card stays for a person
        return [f"{key}: answer refused ({type(error).__name__}: {str(error)[:160]})"]
    entry["signatures"][signature] = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "option": option, "request": key,
                                      "code": code, "round": round_no, "unchanged": bool(facts.get("unchanged"))}
    state["actions"] = int(state.get("actions", 0)) + 1
    activity.record(rdir, "Autocuración", f"{task_id}: {option} automático ({found.get('label') or found.get('kind')}): "
                    f"{headline}", kind="flow")
    return [f"{key}: {option}"]


__all__ = ["attempt_facts", "enabled", "evidence", "heal", "load", "round_of", "runs"]
