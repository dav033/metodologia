"""Which agent sessions are working right now, and on what (planning a requirement, building, idle).

The Scheduler's own stores only know about runs. A plan is written by an agent session long before any run exists, so
this is the other half of "what is happening": the `hook relay` events every session already sends (UserPromptSubmit,
PostToolUse, Stop) are noted in `<root>/.state/presence/<session>.json`, and edits to a requirement's SPEC / PLAN /
rounds are also appended to `events.jsonl` so `/flow` can show the Planeación module talking.

Observer only: it never decides anything and never stores prompt text. Standard library only.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

IDLE_AFTER_S = 15 * 60        # a "working" session with no event for this long is shown as quiet
FORGET_AFTER_S = 6 * 3600     # and one with none for this long is not listed at all
MAX_EVENTS = 2000
_REQ_FILE = re.compile(r"/requirements/(REQ-\d+)[^/]*/(SPEC\.md|PLAN\.md|PLAN\.json|PLAN\.amendments\.jsonl|rounds/|"
                       r"PLAN-REVIEW|plan-revisions/)")
_STAGE = {"SPEC.md": "especificación", "PLAN.md": "plan", "PLAN.json": "plan", "PLAN.amendments.jsonl": "enmienda",
          "rounds/": "entrevista", "PLAN-REVIEW": "revisión del plan", "plan-revisions/": "congelado del plan"}


def _dir(root: Path) -> Path:
    return Path(root) / ".state" / "presence"


def _safe(sid: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9._-]{4,80}", sid or ""))


def _write(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def planning_target(file_path: str) -> dict[str, str] | None:
    """`{req, stage}` when the path is one of a requirement's planning documents, else None."""
    found = _REQ_FILE.search(file_path.replace("\\", "/"))
    if not found:
        return None
    return {"req": found.group(1), "stage": _STAGE.get(found.group(2), "plan")}


_PLAN_CMD = re.compile(r"(plan-json\s+(?:init|check|freeze|report|amend)|planner\s+invoke|\bgo\b|\bhandoff\b)")


def _planned_req(payload: dict) -> str | None:
    """The REQ a Bash command works on when it is one of the planning commands (init, check, planner invoke, go…)."""
    tool_input = payload.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str) or "bitacora" not in command or not _PLAN_CMD.search(command):
        return None
    found = re.search(r"\bREQ-\d+\b", command)
    if not found:
        return None
    named = re.search(r"--project[ =]([A-Za-z0-9._-]+)", command)
    return f"{named.group(1)}:{found.group(0)}" if named else found.group(0)


def _path_project(file_path: str) -> str:
    found = re.search(r"/([A-Za-z0-9._-]+)/requirements/REQ-\d+", file_path.replace("\\", "/"))
    return found.group(1) if found else ""


def _file_of(payload: dict) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("file_path", "path", "notebook_path"):
            if isinstance(tool_input.get(key), str):
                return tool_input[key]
    return ""


def record(root: Path, payload: dict, project: str | None, agent: str = "", now: float | None = None) -> None:
    """Note one hook event. Raises nothing the caller must handle beyond OSError."""
    sid = str(payload.get("session_id") or "")
    if not _safe(sid):
        return
    now = time.time() if now is None else now
    event = payload.get("hook_event_name") or "UserPromptSubmit"
    path = _dir(root) / f"{sid}.json"
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        doc = {}
    if not isinstance(doc, dict):
        doc = {}
    if event == "SessionEnd":
        path.unlink(missing_ok=True)
        path.with_name(f"{sid}.gate.json").unlink(missing_ok=True)
        return
    state = "idle" if event == "Stop" else "working"
    if state == "working" and doc.get("state") != "working":
        doc["since"] = now
    doc.update({"session": sid, "project": project or doc.get("project") or "", "state": state, "agent": agent or
                doc.get("agent") or "", "cwd": str(payload.get("cwd") or doc.get("cwd") or ""), "last_event_at": now})
    if event == "UserPromptSubmit":
        doc.pop("activity", None)
    tool = payload.get("tool_name")
    if isinstance(tool, str) and event == "PostToolUse":
        doc["last_tool"] = tool
        target = planning_target(_file_of(payload))
        asked = _planned_req(payload) if tool == "Bash" else None
        if asked:
            doc["planned"] = sorted({*(doc.get("planned") or []), asked})
        if target:
            owner = _path_project(_file_of(payload))     # the project of the file, not of the session: a session bound to one
            entry = f"{owner}:{target['req']}" if owner else target["req"]            # project can plan another's requirement
            doc["planned"] = sorted({*(doc.get("planned") or []), entry})
            doc["activity"] = {"kind": "planning", **target, "at": now}
            _append_event(root, {"at": now, "session": sid, "project": doc["project"], "req": target["req"],
                                 "stage": target["stage"]})
        elif _file_of(payload) and tool in ("Edit", "Write", "MultiEdit"):
            doc["activity"] = {"kind": "building", "at": now}
    _write(path, doc)


def planned_reqs(root: Path, sid: str) -> list[str]:
    """REQs this session wrote planning documents for, or ran planning commands on."""
    if not _safe(sid):
        return []
    try:
        doc = json.loads((_dir(root) / f"{sid}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    planned = doc.get("planned") if isinstance(doc, dict) else None
    return [r for r in planned if isinstance(r, str)] if isinstance(planned, list) else []


def _append_event(root: Path, event: dict) -> None:
    log = _dir(root) / "events.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    if log.stat().st_size > 400_000:                 # keep the tail: this is a live view, not an archive
        lines = log.read_text(encoding="utf-8").splitlines()[-MAX_EVENTS // 2:]
        log.write_text("\n".join(lines) + "\n", encoding="utf-8")


def sessions(root: Path, now: float | None = None) -> list[dict[str, Any]]:
    """Sessions seen recently, working ones first. `quiet` marks a working session that stopped sending events."""
    now = time.time() if now is None else now
    out = []
    try:
        files = sorted(_dir(root).glob("*.json"))
    except OSError:
        return []
    for path in files:
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(doc, dict) or not isinstance(doc.get("last_event_at"), (int, float)):
            continue
        age = now - doc["last_event_at"]
        if age > FORGET_AFTER_S:
            continue
        working = doc.get("state") == "working"
        act = doc.get("activity") if isinstance(doc.get("activity"), dict) else {}
        out.append({"session": str(doc.get("session") or path.stem)[:8], "project": doc.get("project") or "",
                    "agent": doc.get("agent") or "", "state": "working" if working else "idle",
                    "quiet": working and age > IDLE_AFTER_S, "since": doc.get("since") if working else None,
                    "last_event_at": doc["last_event_at"], "last_tool": doc.get("last_tool"),
                    "activity": act.get("kind"), "req": act.get("req"), "stage": act.get("stage")})
    out.sort(key=lambda s: (s["state"] != "working", -s["last_event_at"]))
    return out


def planning_events(root: Path, after: int = 0, limit: int = 500) -> list[dict[str, Any]]:
    """Planning edits after line number `after` (1-based), each with its line number as `id`."""
    log = _dir(root) / "events.jsonl"
    out = []
    try:
        with log.open("r", encoding="utf-8") as handle:
            for n, line in enumerate(handle, 1):
                if n <= after:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if isinstance(row, dict) and isinstance(row.get("at"), (int, float)):
                    out.append({**row, "id": n})
                if len(out) >= limit:
                    break
    except OSError:
        return []
    return out
