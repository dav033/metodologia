"""The Solucionador's brief and prompt (REQ-031): everything an operator would read first, in the order the role prompt
(`agents/solver.md`) asks for it. Split from `solver.py`, which decides when a session starts."""
from __future__ import annotations

import json
from pathlib import Path

from . import healing


def _recent_logs(project_dir: Path, count: int = 2) -> list[Path]:
    return sorted(Path(project_dir).glob("20*/W*/20*.md"))[-count:]


GATE_EVENTS = ("gate_compose_failed", "gate_composed", "gate_recompose", "subplan_lines_unavailable",
               "subplan_line_conflict")


def gate_trail(telemetry: Path | None, run_id: str, limit: int = 12) -> list[str]:
    """The run's last composition-gate and subplan-line events from the engine's telemetry: a composition that fails
    leaves only these (`gate_compose_failed`: the gate, the turn, the error), while the run waits for nothing visible."""
    rows = []
    try:
        with open(telemetry, encoding="utf-8") as stream:
            for line in stream:
                if run_id not in line or not any(event in line for event in GATE_EVENTS):
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if row.get("run_id") == run_id and row.get("event") in GATE_EVENTS:
                    rows.append(row)
    except (OSError, TypeError):
        return []
    out = []
    for row in rows[-limit:]:
        what = {k: row[k] for k in ("gate", "turn", "state", "candidate_id", "reason", "role", "previous") if k in row}
        out.append(f"- {row['event']}: {json.dumps(what, ensure_ascii=False, default=str)[:700]}")
    return out


def _gate_tasks(run) -> dict[str, str]:
    """Composition gate -> its gate task, from the frozen plan the run executes."""
    try:
        plan = json.loads(Path(run.plan_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {str(g.get("id")): str(g.get("task")) for g in plan.get("composition_gates") or () if isinstance(g, dict)}


def brief(run, rdir: Path, session: dict, items: list[dict], status: dict, *, telemetry: Path | None = None) -> str:
    """Everything an operator would read first, in the order the prompt asks for it."""
    import bt_block_agent
    rdir = Path(rdir)
    root = rdir.parent.parent.parent                     # <root>/<project>/requirements/<REQ-dir>
    scripts = Path(__file__).resolve().parent.parent
    tasks = status.get("tasks") or {}
    lines = [f"# Solucionador {session['id']} — {run.project} {run.req} (run {run.run_id})", "",
             f"Started {session['started_at']} by the durable engine's maintenance pass.", "", "## Triggers", ""]
    lines += [f"- `{i['key']}` — {i['kind']}{' · ' + i['task_id'] if i.get('task_id') else ''}: {i['reason']}"
              for i in items]
    from . import resolutions
    for item in items:
        if item["kind"] == "resolution":
            lines += resolutions.brief(item)
    for item in items:
        task = tasks.get(item.get("task_id") or "") or {}
        decision = task.get("decision") if isinstance(task.get("decision"), dict) else None
        if not item.get("task_id"):
            continue
        lines += ["", f"## {item['task_id']}", "", f"Workflow `{task.get('workflow_id')}` "
                  f"({task.get('workflow_status')}); state: `{json.dumps(task.get('state'), default=str)}`"]
        if decision:
            lines += ["", "```", healing.evidence(run, rdir, item["task_id"], decision, healing.round_of(task)), "```"]
            found = bt_block_agent.cached(rdir, item["key"]) if item["kind"] in ("decision", "repeat") else None
            if found:
                lines += ["", "Diagnosis (bt_block_agent, read-only, may be wrong):", "```json",
                          json.dumps(found, ensure_ascii=False, indent=1)[:4000], "```"]
        history = rdir / "RUN.notes" / f"{item['task_id']}.history.jsonl"
        lines += ["", f"Attempt history: `{history}`" + ("" if history.is_file() else " (none yet)")]
    open_tasks = [f"- {t}: {(v or {}).get('workflow_status')} {json.dumps((v or {}).get('state'), default=str)[:160]}"
                  for t, v in sorted(tasks.items()) if (v or {}).get("workflow_status") != "SUCCESS"]
    summary = status.get("summary") if isinstance(status.get("summary"), dict) else {}
    lines += ["", "## Run status", "", f"Run workflow `{status.get('workflow_id')}`: {status.get('workflow_status')}; "
              f"summary status {summary.get('status')}. Full status: `{Path(session['dir']) / 'status.json'}`.", "",
              *(open_tasks[:40] or ["- every task workflow ended"])]
    gates = summary.get("gates") if isinstance(summary.get("gates"), dict) else {}
    trail = gate_trail(telemetry, run.run_id)
    if gates or trail:
        lines += ["", "## Composition gates", "",
                  (f"Composed: `{json.dumps(gates.get('composed') or {}, ensure_ascii=False)}`; rejected: "
                   f"`{json.dumps(gates.get('rejected') or {}, ensure_ascii=False)[:1500]}`. A composition that fails "
                   "is tried again on later turns of the run loop (`COMPOSE_TURNS`) before the gate counts as "
                   "rejected; the owner's `retry-task` of the gate task composes it again."), "",
                  *(["Last gate and line events (telemetry):", *trail] if trail else [])]
        tasks_of = _gate_tasks(run)
        for gate in sorted(gates.get("rejected") or {}):
            lines += ["", (f"Known case (agents/solver.md): gate {gate} is rejected. Fix the origin of its reason above "
                           "(the composer, a merge rule, the environment or the plan), integrate the fix, then "
                           f"`uv run --project ~/dev/metodologia bt-durable retry-task {run.project} {run.req} "
                           f"{tasks_of.get(gate, '<gate task>')}`: it reopens the ended run and composes {gate} again.")]
    logs = _recent_logs(root / run.project) + _recent_logs(root / "metodologia")
    lines += ["", "## Files", "",
              f"- requirement: `{rdir}` (SPEC.md, PLAN.md, PLAN.json, SPEC.es.md)",
              f"- the frozen plan this run executes: `{run.plan_path}`",
              f"- project decisions: `{root / run.project / 'DECISIONS.md'}`",
              f"- metodologia decisions: `{root / 'metodologia' / 'DECISIONS.md'}`",
              *[f"- day log: `{p}`" for p in logs],
              f"- diagnoses: `{rdir / 'RUN.diagnoses'}`; healing: `{rdir / healing.STATE}`; activity: "
              f"`{rdir / '.planning' / 'activity.jsonl'}`; telemetry and attempts: `{root / '.state' / 'durable'}`",
              "", "## Commands", "",
              f"- run status: `uv run --project ~/dev/metodologia bt-durable status {run.project} {run.req}`",
              "- engine journal: `journalctl --user -u bt-durable.service --since -3h --no-pager -o cat`",
              f"- answer a decision: `uv run --project ~/dev/metodologia bt-durable answer {run.project} {run.req} <task> "
              "<request>@k<round> <action> --note \"...\" --by solver`",
              f"- the run's Planner: `python3 {scripts / 'bt_agent_terminal.py'} tell-planner {run.project} {run.req} "
              "\"<change request>\"`",
              f"- integrate a metodologia fix: `python3 ~/dev/metodologia/skill/scripts/bt_integrate.py --branch "
              f"solver/{session['id']} --worktree {session['cwd']}/wt --title \"<what> (D-NNN)\" --session "
              f"{session['id']} --trailer \"<your attribution line>\"` (`--dry-run` first; `--help` for the steps)",
              "", "## Your session", "",
              f"- session folder (REPORT.md, result.json, NOTES.md, inbox.jsonl): `{session['dir']}`",
              f"- working folder (your worktree goes in `{session['cwd']}/wt`): `{session['cwd']}`",
              f"- trigger keys for result.json `handled`: {', '.join(i['key'] for i in items)}",
              "- keep NOTES.md current (what you found, what you changed, what is next): you may be restarted on "
              "another account and must be able to continue from your files."]
    return "\n".join(str(line) for line in lines) + "\n"


def prompt(folder: Path) -> str:
    """The versioned role prompt (`agents/solver.md`) plus where this session's brief is."""
    from bt_resources import resource_root
    text = (resource_root() / "agents" / "solver.md").read_text(encoding="utf-8")
    body = text.split("\n---\n", 1)[1].strip() if text.startswith("---\n") else text
    return (f"{body}\n\n## This session\n\nYour brief: `{Path(folder) / 'BRIEF.md'}`. Read it now, then "
            "`triggers.json` next to it, and start.\n")
