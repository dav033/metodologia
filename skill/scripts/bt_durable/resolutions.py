"""Open composition resolution requests as Solucionador triggers (REQ-031, live finding of 2026-10-29 19:55).

The composer and the line integrator settle a text conflict they cannot merge by rule with a recorded resolution
(D-160, D-164): when none exists they write `<state>/composition/resolutions/<key>.json` (path, the three blob ids,
the three commits) and `<key>.diff3`, and wait for someone to write `<key>.resolved`, the file's final content. Nobody
did: on pictures REQ-021 three requests sat open for up to 3 h while T95 kept failing with INTEGRATION_CONFLICT and
healing kept answering `retry_with_note`, which no retry can fix. A request older than `solver.resolution_after_seconds`
becomes a `resolution` trigger for the run whose task conflicts: the run whose open decision names the conflict's path
or one of its commits, else the one run with an open INTEGRATION_CONFLICT decision (with several such runs and no
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


def target(request: dict, statuses: dict[str, dict]) -> tuple[str, str] | None:
    """(run id, task id) the request belongs to, or None when it cannot be told."""
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
    runs = {run_id for run_id, _ in conflicting}
    return conflicting[0] if len(runs) == 1 else None


def triggers(folder: Path, statuses: dict[str, dict], now: float, after_seconds: int) -> list[dict]:
    from .solver import round_of, trigger
    out = []
    for request in open_requests(folder, now, after_seconds):
        found = target(request, statuses)
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
