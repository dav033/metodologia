"""Everything about one subplan the owner must not miss, in one place: where it is in its flow, what waits for the owner,
what blocks it and who resolves it, which agent works on it now, the decisions already taken and what changed.

Read-only. Built from the same sources the Plan tab already reads (planning flow, Designer drafts, rounds, the run's
status, subplan verification and the planning activity log), once per page fragment for every subplan (`statuses`).
"""
from __future__ import annotations

import re
from pathlib import Path

import bt_design_drafts as drafts
import bt_planning_activity as activity
import bt_rounds as rounds
import bt_verification as verification

STEPS = (("define", "Definir"), ("design", "Diseñar"), ("confirm", "Confirmar"), ("run", "Ejecutar"),
         ("verify", "Probar"), ("done", "Aprobado"))
QUIET = {"Traducción"}                     # activity that never needs the owner's attention
_PREFIX = re.compile(r"^\s*((?:SP-\d+\s*(?:[/,y]|and)?\s*)+):")
_STUCK = {"needs_decision", "rejected", "blocked", "failed"}
_PLANNER = ("todavía no tiene tareas", "hay tareas sin criterios", "falta cómo probarlo", "no se podrá ejecutar")


def _question_subplans(question: dict, coverage: str) -> set[str]:
    """Subplans a round question is about: its «SP-n:» prefix, else the round's coverage when it names exactly one."""
    head = _PREFIX.match(str(question.get("text") or ""))
    if head:
        return set(re.findall(r"SP-\d+", head.group(1)))
    named = set(re.findall(r"SP-\d+", coverage or ""))
    return named if len(named) == 1 else set()


def _rounds(rdir: Path) -> tuple[dict | None, list[dict]]:
    """(open round, answered rounds oldest first)."""
    if not rounds.rounds_dir(rdir).exists():
        return None, []
    open_round, answered = None, []
    for f in rounds.list_rounds(rdir):
        try:
            data = rounds.load(f)
        except (OSError, ValueError):
            continue
        if data.get("status") == "answered":
            answered.append(data)
        elif data.get("status") == "open":
            open_round = data
    return open_round, answered


def _answer(question: dict, answer: dict) -> str:
    choice = answer.get("choice")
    label = next((o.get("label") for o in question.get("options") or [] if o.get("key") == choice), None)
    text = f"{choice}) {label}" if label else str(answer.get("text") or choice or "")
    return text + (f" · nota: {answer['note']}" if answer.get("note") else "")


def _tasks_by_id(run: dict | None) -> dict[str, dict]:
    return {t["id"]: t for m in (run or {}).get("milestones") or [] for t in m.get("tasks") or [] if t.get("id")}


def _gates(rdir: Path) -> dict[str, list[str]]:
    """gate task id -> subplans it composes."""
    plan = drafts._plan(rdir)
    return {g["task"]: list(g.get("subplans") or []) for g in plan.get("composition_gates") or []
            if isinstance(g, dict) and isinstance(g.get("task"), str)}


def _design(row: dict | None, has_tasks: bool, you: list, blockers: list, working: list, decisions: list) -> str:
    """Design facts of a UI subplan; returns the step state: done, now or todo."""
    if row is None:
        return "skip"
    status, ready = row["status"], [d for d in row.get("directions") or [] if d.get("status") == "ready"]
    chosen = next((d for d in row.get("directions") or [] if d.get("id") == row.get("chosen")), None)
    if chosen:
        decisions.append({"when": row.get("started") or "", "text": f"Elegiste la dirección {str(chosen['id']).upper()}"
                          f" · {chosen.get('name') or ''}".rstrip(" ·")})
    if status in drafts.ACTIVE:
        what = ("actualiza el diseño elegido con el cambio del plan" if status == "amending" else
                f"termina la dirección {str(row.get('chosen')).upper()}" if row.get("phase") == "finalise" and row.get("chosen")
                else "prepara 3 direcciones para que elijas" if row.get("phase") == "explore" else "trabaja en el diseño")
        working.append({"who": "Designer", "text": what, "since": row.get("started") or ""})
    for q in row.get("questions") or []:
        you.append({"kind": "design", "text": f"El Designer pregunta: {q}", "action": "Responder", "view": "design"})
    if row.get("pending_feedback") and status not in drafts.ACTIVE:
        n = row["pending_feedback"]
        blockers.append({"who": "Designer", "text": f"{n} comentario{'s' if n != 1 else ''} sin aplicar al diseño todavía"})
    if row.get("amend") and status not in drafts.ACTIVE:
        you.append({"kind": "design", "text": "El plan cambió después del diseño elegido: actualízalo",
                    "action": "Actualizar diseño", "view": "design"})
        return "now"
    if status == "choosing" and not row.get("chosen"):
        you.append({"kind": "design", "text": f"Elegir una de las {len(ready)} direcciones de diseño",
                    "action": "Comparar", "view": "design"})
        return "now"
    if status == "failed":
        you.append({"kind": "design", "text": "El Designer falló en su último intento: pide rehacer el diseño",
                    "action": "Rehacer diseño", "view": "design"})
        return "now"
    if row["stale"]:
        blockers.append({"who": "Designer", "text": "El diseño quedó desactualizado: el Designer prepara uno nuevo"})
        return "now"
    if status in ("ready", "approved"):
        return "done"
    if status == "none" and not has_tasks:
        return "todo"                          # the Designer starts once the subplan has tasks (D-146)
    if status == "none":
        blockers.append({"who": "Designer", "text": "El diseño aún no empezó: arranca solo ahora que el subplan tiene tareas"})
    return "now"


def status(ctx: dict, s: dict, shared: dict) -> dict:
    """The control status of subplan `s` (one of `ctx['subplans']`)."""
    sid = s["id"]
    you: list[dict] = []
    blockers: list[dict] = []
    working: list[dict] = []
    decisions: list[dict] = []
    row = ctx["rows"].get(s["ref"]) if s["ref"] else None
    flow = (ctx.get("flow") or {}).get("subplans", {}).get(sid) if ctx.get("flow") else None
    problems = list((flow or {}).get("problems") or [])

    open_round, answered = shared["rounds"]
    if open_round:
        mine = [q for q in open_round.get("questions") or []
                if sid in _question_subplans(q, open_round.get("coverage", ""))]
        if mine:
            you.append({"kind": "round", "text": f"Responder {len(mine)} pregunta{'s' if len(mine) != 1 else ''} de la "
                        f"ronda {open_round.get('round')}", "action": "Responder", "view": "asks"})
    for data in answered:
        for q in data.get("questions") or []:
            if sid in _question_subplans(q, data.get("coverage", "")) and (a := (data.get("answers") or {}).get(q.get("id"))):
                decisions.append({"when": data.get("answered_at") or data.get("created_at") or "",
                                  "text": f"Ronda {data.get('round')}: {_PREFIX.sub('', str(q.get('text'))).strip()} → "
                                          f"{_answer(q, a)}"})

    design_step = _design(row, bool(s["tasks"]), you, blockers, working, decisions)

    pending_inputs = [r["item"] for r in shared["inputs"].get(sid, []) if r["pending"]]
    if pending_inputs:
        you.append({"kind": "input", "text": "Dar " + (f"la entrada «{pending_inputs[0]}»" if len(pending_inputs) == 1 else
                    f"{len(pending_inputs)} entradas: " + ", ".join(pending_inputs[:3])), "action": "Ver entradas",
                    "view": "inputs"})
    planner = [p for p in problems if p.startswith(_PLANNER)]
    for p in planner:
        blockers.append({"who": "Planner", "text": p[:1].upper() + p[1:]})
    defined = bool(s["tasks"]) and not planner and not pending_inputs

    state = (flow or {}).get("state")
    if state == "confirmed":
        where = {"web": " en la web", "conversation": " en la conversación"}.get((flow or {}).get("via"), "")
        decisions.append({"when": (flow or {}).get("confirmed_at") or "", "text": f"Confirmaste el subplan{where}"})
    confirm_step = "done" if state == "confirmed" or flow is None else "todo"
    if flow is not None and state != "confirmed" and defined and design_step in ("done", "skip"):
        confirm_step = "now"
        if not problems:
            you.append({"kind": "confirm", "text": "Volver a confirmarlo: cambió después de confirmarlo" if state == "changed"
                        else "Revisar y confirmar el subplan", "action": "confirm", "view": ""})

    tasks = shared["tasks"]
    own = [t for t in tasks.values() if t.get("subplan_id") == sid]
    staged = sid in shared["held"] or (flow is None and any(t.get("attempts") for t in own))
    executing = staged                                        # before that, waiting on other work is not news
    if flow is not None and state == "confirmed" and not staged and s["tasks"]:
        you.append({"kind": "run", "text": "Mandarlo a ejecutar: aprobarlo como etapa", "action": "run", "view": ""})
    waits: dict[str, list[str]] = {}
    for t in own:
        attempt = t.get("attempt") or {}
        if attempt.get("live"):
            working.append({"who": "Ejecución", "text": f"{t['id']} · {t.get('title') or ''} (intento "
                             f"{attempt.get('number') or t.get('attempts') or 1})", "since": attempt.get("started_at") or ""})
        elif t.get("state") in _STUCK and t["id"] not in shared["decided"]:
            blockers.append({"who": "Ejecución", "text": f"{t['id']} quedó {t.get('state')}: {t.get('title') or ''}"})
        if executing and t.get("state") in ("pending", "ready"):
            for dep in t.get("after") or []:
                other = tasks.get(dep)
                if other and other.get("subplan_id") != sid and other.get("state") in _STUCK:
                    waits.setdefault(dep, []).append(t["id"])
    for dep, ids in waits.items():
        why = "necesita tu decisión" if dep in shared["decided"] else f"quedó {tasks[dep].get('state')}"
        blockers.append({"who": "Tú" if dep in shared["decided"] else "Ejecución",
                         "text": f"{', '.join(ids)} {'espera' if len(ids) == 1 else 'esperan'} a {dep}"
                                 f"{' (puerta de composición)' if dep in shared['gates'] else ''}, que {why}"})
    for d in shared["decisions"]:
        task = tasks.get(d.get("task")) or {}
        if task.get("subplan_id") == sid or sid in shared["gates"].get(d.get("task"), []):
            you.append({"kind": "decision", "text": f"Decidir cómo sigue {d.get('task')}: "
                                                    f"{d.get('error') or d.get('what') or d.get('title') or ''}",
                        "action": "Decidir", "view": "run" if task.get("subplan_id") == sid else "req-run"})
    done_tasks = sum(1 for t in own if t.get("state") == "completed")
    run_step = ("done" if own and done_tasks == len(own) else "now" if staged or state == "confirmed" else "todo")

    verified = shared["verified"].get(sid) or {}
    vstate = verified.get("state")
    if vstate in ("to_test", "outdated"):
        you.append({"kind": "verify", "text": f"Probar la versión {verified.get('version')} y aprobarla o rechazarla",
                    "action": "Probar", "view": "verify"})
    elif vstate == "rejected":
        blockers.append({"who": "Ejecución", "text": f"Rechazaste la versión {verified.get('version')}: espera una corrección"})
    if verified.get("decision", {}).get("decision") in ("approved", "rejected"):
        dec = verified["decision"]
        decisions.append({"when": dec.get("at") or "", "text": ("Aprobaste" if dec["decision"] == "approved" else "Rechazaste")
                          + f" la versión {dec.get('version')}" + (f" · {dec['note']}" if dec.get("note") else "")})
    verify_step = "done" if vstate == "approved" else "now" if vstate in ("to_test", "outdated", "rejected") else "todo"

    states = {"define": "done" if defined else "now", "design": design_step, "confirm": confirm_step, "run": run_step,
              "verify": verify_step, "done": "done" if vstate == "approved" else "todo"}
    steps = [{"key": k, "label": label, "state": states[k]} for k, label in STEPS]
    current = next((st for st in steps if st["state"] == "now"), None) or \
        next((st for st in steps if st["state"] == "todo"), steps[-1])
    news = [ev for ev in shared["events"] if ev.get("sp") == sid and ev.get("who") not in QUIET]
    decisions += [{"when": ev.get("at") or "", "text": "Le pediste al Designer: " + str(ev.get("text") or "")}
                  for ev in news if ev.get("kind") == "feedback"]   # choices, confirmations and verdicts come from their sources
    return {"id": sid, "steps": steps, "current": current["key"], "you": you, "blockers": blockers, "working": working,
            "decisions": sorted(decisions, key=lambda d: d["when"], reverse=True), "news": news[:12],
            "latest": news[0].get("at", "") if news else "", "tasks": {"done": done_tasks, "total": len(own)}}


def _held(ctx: dict) -> set[str]:
    """Subplans of the latest approved stage (D-134): the ones sent to execution."""
    try:
        import bt_page_planning_flow as flow_view
        return set(flow_view.stage_info(ctx)["held"])
    except Exception:  # noqa: BLE001 - a stage that cannot be read only hides the «send to run» hint
        return set()


def statuses(ctx: dict) -> dict[str, dict]:
    """Every subplan's status, computed once per fragment (cached in ctx)."""
    if "subplan_status" in ctx:
        return ctx["subplan_status"]
    rdir = ctx["rdir"]
    import bt_page_planning_run as run_view
    run = run_view._status(ctx)
    try:
        import bt_planning_flow
        input_rows = (ctx.get("flow") or {}).get("inputs")
        inputs = {s["id"]: bt_planning_flow.inputs_for(rdir, s["id"], input_rows) for s in ctx["subplans"]} \
            if ctx.get("flow") else {}
    except (OSError, ValueError):
        inputs = {}
    decisions = [d for d in (run or {}).get("decisions") or [] if isinstance(d, dict)]
    ver = verification.state(rdir) if verification.applies(rdir) else {"subplans": []}
    shared = {"rounds": _rounds(rdir), "inputs": inputs, "run": run, "tasks": _tasks_by_id(run), "gates": _gates(rdir),
              "decisions": decisions, "decided": {d.get("task") for d in decisions}, "held": _held(ctx),
              "verified": {r["id"]: r for r in ver["subplans"]}, "events": activity.events(rdir, 300)}
    ctx["subplan_status"] = {s["id"]: status(ctx, s, shared) for s in ctx["subplans"]}
    return ctx["subplan_status"]
