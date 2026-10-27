"""Briefing for a session that takes over a collaborative plan: `bitacora.py planning resume REQ-NNN`.

The flow's state is all files (SPEC, rounds, `.planning/flow.json`, activity log), so a fresh session can continue;
what it lacks is a single place that says where things stand and what to do next. This renders that, read-only.
"""
from __future__ import annotations

from pathlib import Path

import bt_planning_activity as activity
import bt_planning_flow as flow
import bt_planning_notes as notes
import bt_rounds as rounds
import bt_subplan_sessions as subplan_sessions
import bt_verification as verification


def next_action(project: str, rdir: Path, st: dict, open_round: Path | None) -> str:
    req = verification._req(rdir)
    if not st["active"]:
        return f"Collaborative planning is not on: run `bitacora.py --project {project} planning start {req}`."
    if open_round is not None:
        return (f"Round {rounds.load(open_round).get('round')} is open: the owner has not answered. Wait for it "
                f"(`round wait {req}`); do not guess the answers.")
    if st["editing"]:
        return "The plan is being edited (draft). Finish the edit, then re-read this briefing."
    phase = st["phase"]
    if phase == "interview":
        return ("No skeleton yet and no round is open: read the answered rounds, then either ask the remaining "
                "plan-wide questions (`round new`) or draft the skeleton of milestones and subplans in the plan.")
    if phase == "outline":
        return ("The skeleton exists but the owner has not confirmed it: tell them to confirm it in the Plan tab "
                "(`planning outline-confirm` only to relay their explicit words).")
    if phase == "ready":
        return "Every subplan is confirmed: validate the plan (`plan-json check`) and tell the owner it is ready to approve."
    focus = st["focus"]
    todo = (st["subplans"].get(focus) or {}).get("problems") or []
    tail = ("; missing: " + "; ".join(todo)) if todo else ""
    return f"Define the focus subplan {focus} with the owner (behavior, design, inputs, tasks, `## Pruebas` row){tail}."


def briefing(project: str, rdir: Path) -> str:
    st = flow.state(rdir)
    files = rounds.list_rounds(rdir)
    open_round = rounds.open_round(rdir)
    out = [f"# Resume {verification._req(rdir)} (project {project})", f"Plan dir: {rdir}",
           f"Flow: {'on' if st['active'] else 'off'} · phase {st['phase'] or '-'} · focus {st['focus'] or '-'} · "
           f"confirmed {st['confirmed']}/{st['total']}"]
    if st["subplans"]:
        out.append("Subplans: " + ", ".join(f"{k}:{v['state']}" for k, v in st["subplans"].items()))
    missing = [sid for sid in st["subplans"] if not verification.tests_for(rdir, sid)]
    if missing:
        out.append("Without a `## Pruebas` row (the owner cannot confirm them): " + ", ".join(missing))
    pending = [row["item"] for row in st["inputs"] if row["pending"]]
    if pending:
        out.append("Inputs still pending: " + "; ".join(pending))
    hands_on = [subplan_sessions.info(s) for s in subplan_sessions.sessions(rdir)]
    if hands_on:
        out.append("Hands-on sessions with the owner (build the subplan's tasks around these branches, do not redo them): "
                   + "; ".join(f"{s['subplan']} {s['status']} on {s['branch']} ({s.get('commits', s['ahead'])} commits)"
                               for s in hands_on))
    out.append(f"Rounds: {len(files)} ({'round ' + str(rounds.load(open_round).get('round')) + ' OPEN' if open_round else 'none open'})")
    answered = [f for f in files if rounds.load(f).get("status") == "answered"]
    if answered:
        out += ["", "Latest answered round (the owner's words, not yours):", rounds.format_answers(rounds.load(answered[-1]))]
    recent = [e for e in activity.events(rdir, 30) if e.get("kind") != "translate"][-8:]
    if recent:
        out += ["", "Recent activity:"] + [f"- {e.get('at', '')[11:19]} {e.get('who')}: {e.get('text', '')[:140]}" for e in recent]
    remembered = notes.render(rdir)
    if remembered:
        out += [""] + remembered
    out += ["", "Read first: SPEC.md (owner decisions are in its Clarifications) and the project DECISIONS.md. "
            "The notes above are what the previous session saved; re-read the code you need and keep saving notes (`planning note`).",
            "", "NEXT: " + next_action(project, rdir, st, open_round)]
    return "\n".join(out)
