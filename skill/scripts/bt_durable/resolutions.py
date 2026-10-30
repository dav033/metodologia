"""Open composition resolution requests as Solucionador triggers (REQ-031, live finding of 2026-10-29 19:55).

The composer and the line integrator settle a text conflict they cannot merge by rule with a recorded resolution
(D-160, D-164): when none exists they write `<state>/composition/resolutions/<key>.json` (path, the three blob ids,
the three commits) and `<key>.diff3`, and wait for someone to write `<key>.resolved`, the file's final content. Nobody
did: on pictures REQ-021 three requests sat open for up to 3 h while T95 kept failing with INTEGRATION_CONFLICT and
healing kept answering `retry_with_note`, which no retry can fix. A request older than `solver.resolution_after_seconds`
becomes a `resolution` trigger for the run whose task conflicts: the run whose open decision names the conflict's path
or one of its commits, else the run whose rejected composition gate conflicted on that path (its last `gate_composed`
event in the engine's telemetry: a gate the composer rejects leaves no decision to name it — pictures REQ-021 r25, CG-9,
2026-10-30 04:38, D-193), else the one run with an open INTEGRATION_CONFLICT decision (with several such runs and no
match the request waits: guessing could resolve a file for the wrong project).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

CONFLICT = "INTEGRATION_CONFLICT"
DIFF3_BYTES = 20000


def open_requests(folder: Path, now: float, after_seconds: int) -> list[dict]:
    """Requests without `.resolved` whose `.json` is older than `after_seconds`."""
    found = []
    for context in sorted(Path(folder).glob("*.json")):
        key = context.stem
        resolved = context.with_name(f"{key}.resolved")
        try:
            if resolved.exists() or now - context.stat().st_mtime < after_seconds:
                continue
            data = json.loads(context.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(data, dict) and data.get("path"):
            found.append({"key": key, "path": str(data["path"]), "blobs": data.get("blobs") or {},
                          "commits": data.get("commits") or {}, "json": str(context),
                          "diff3": str(context.with_name(f"{key}.diff3")), "resolved": str(resolved),
                          "since": context.stat().st_mtime})
    return found


def _decision_text(task: dict) -> str:
    decision = task.get("decision") if isinstance(task.get("decision"), dict) else {}
    failure = decision.get("failure") if isinstance(decision.get("failure"), dict) else {}
    pieces = [str(decision.get("reason") or ""), str(failure.get("code") or ""), str(failure.get("summary") or ""),
              str(failure.get("agent_note") or "")]
    pieces += [str(e.get("excerpt") or "") for e in failure.get("evidence") or [] if isinstance(e, dict)]
    return "\n".join(pieces)


def rejected_paths(telemetry: Path | None, statuses: dict[str, dict]) -> dict[str, dict[str, str]]:
    """{run id: {path: gate}} for the gates each run's summary rejects now, from each gate's last rejected
    `gate_composed` event (its per-member conflict paths)."""
    wanted = {run_id: set((((status or {}).get("summary") or {}).get("gates") or {}).get("rejected") or {})
              for run_id, status in statuses.items()}
    wanted = {run_id: gates for run_id, gates in wanted.items() if gates}
    if not wanted or telemetry is None:
        return {}
    last: dict[tuple[str, str], dict] = {}
    try:
        with open(telemetry, encoding="utf-8") as stream:
            for line in stream:
                if '"gate_composed"' not in line or '"rejected"' not in line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                run_id, gate = row.get("run_id"), row.get("gate")
                if row.get("event") == "gate_composed" and row.get("state") == "rejected" \
                        and gate in wanted.get(run_id, ()) and isinstance(row.get("conflicts"), dict):
                    last[(run_id, gate)] = row["conflicts"]
    except OSError:
        return {}
    out: dict[str, dict[str, str]] = {}
    for (run_id, gate), conflicts in sorted(last.items()):
        for paths in conflicts.values():
            for path in paths if isinstance(paths, list) else ():
                out.setdefault(run_id, {})[str(path)] = gate
    return out


def target(request: dict, statuses: dict[str, dict],
           rejected: dict[str, dict[str, str]] | None = None) -> tuple[str, str] | None:
    """(run id, task id) the request belongs to, or None when it cannot be told; a rejected gate's conflict is given
    as (run id, gate id)."""
    commits = [c for c in (request.get("commits") or {}).values() if isinstance(c, str) and len(c) >= 12]
    named, conflicting = [], []
    for run_id, status in sorted(statuses.items()):
        for task_id, task in sorted((status.get("tasks") or {}).items()):
            text = _decision_text(task or {})
            if not text.strip():
                continue
            if request["path"] in text or any(c[:12] in text for c in commits):
                named.append((run_id, task_id))
            elif CONFLICT in text:
                conflicting.append((run_id, task_id))
    if named:
        return named[0]
    gates = sorted((run_id, paths[request["path"]]) for run_id, paths in (rejected or {}).items()
                   if request["path"] in paths)
    if len({run_id for run_id, _ in gates}) == 1:
        return gates[0]
    runs = {run_id for run_id, _ in conflicting}
    return conflicting[0] if len(runs) == 1 else None


def triggers(folder: Path, statuses: dict[str, dict], now: float, after_seconds: int,
             telemetry: Path | None = None) -> list[dict]:
    from .solver import round_of, trigger
    out = []
    requests = open_requests(folder, now, after_seconds)
    rejected = rejected_paths(telemetry, statuses) if requests else {}
    for request in requests:
        found = target(request, statuses, rejected)
        if found is None:
            continue
        run_id, task_id = found
        task = (statuses[run_id].get("tasks") or {}).get(task_id) or {}
        decision = task.get("decision") if isinstance(task.get("decision"), dict) else {}
        item = trigger("resolution", f"{run_id}:resolution:{request['key']}", run_id, task_id=task_id,
                       request_id=str(decision.get("request_id") or ""), round_no=round_of(task),
                       reason=f"the conflict in {request['path']} waits for a recorded resolution since "
                              f"{time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(request['since']))}; no retry "
                              "can settle it")
        item["resolution"] = request
        out.append(item)
    return out


def brief(item: dict) -> list[str]:
    """The brief's section for a resolution trigger: the request, its diff3 and what to do with it."""
    request = item.get("resolution") or {}
    try:
        diff3 = Path(request["diff3"]).read_text(encoding="utf-8", errors="replace")[:DIFF3_BYTES]
    except (KeyError, OSError):
        diff3 = "(the .diff3 file could not be read)"
    blobs = request.get("blobs") or {}
    return ["", f"## Resolution request {request.get('key')} ({request.get('path')})", "",
            f"- request: `{request.get('json')}`; diff3: `{request.get('diff3')}`",
            f"- blobs: base `{blobs.get('base')}`, ours `{blobs.get('ours')}`, theirs `{blobs.get('theirs')}` "
            "(`git cat-file -p <blob>` in the project's repository)",
            f"- commits: {json.dumps(request.get('commits') or {})}",
            f"- write the final content to: `{request.get('resolved')}`",
            "- the final content keeps BOTH sides' intent: never drop either side's change; when they truly exclude "
            "each other, ask the owner. Then answer the task's open decision with `retry` (or `reverify` when the "
            "same snapshot only needs to be integrated again).",
            "", "```diff3", diff3, "```"]
