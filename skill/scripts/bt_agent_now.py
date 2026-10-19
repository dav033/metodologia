"""What an agent is doing at this moment, read from the end of its attempt log. Read-only, never the M4 store.

M4 keeps only a tool's name and a digest of its arguments; the attempt directory keeps the agent's own words
(`output.log`, and `output.tail` with the newest bytes once the log's head is full). This module reads the newest part
and answers, per live attempt: the action in progress (tool and its command/file), the agent's last sentence and its
last finished steps. Two log shapes exist: Claude's `stream-json` lines and Codex's text blocks (`exec`, `codex`,
`apply patch`). Anything unreadable just yields less, never an error.

    now(rdir, project, attempts) -> {attempt_id: {"current", "said", "steps", "updated_at"}}
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import bt_run_stores

TAIL_BYTES = 262_144          # the newest part of the log is enough to know the last few actions
WHAT_CHARS = 220              # a command or a path, cut to two lines on screen
SAID_CHARS = 400
STEPS = 3
_CODEX_HEADERS = ("exec", "codex", "thinking", "apply patch", "user")
_CODEX_DONE = re.compile(r"^\s*(succeeded|exited (-?\d+)) in [\d.]+m?s:?\s*$")


def attempt_dir(rdir: Path, project: str, attempt_id: str) -> Path | None:
    """`.state/executor/<project>-<REQ>-r<rev>-*/attempts/<attempt>-*`, the newest if a revision repeated the id."""
    state = bt_run_stores.paths(Path(rdir))["m1"].parent.parent
    req = "-".join(Path(rdir).name.split("-")[:2]) if Path(rdir).name.startswith("REQ-") else Path(rdir).name
    found = [p for p in (state / "executor").glob(f"{project}-{req}-*/attempts/{attempt_id}-*") if p.is_dir()]
    return max(found, key=lambda p: p.stat().st_mtime) if found else None


def _tail(adir: Path) -> tuple[str, float]:
    log, tail = adir / "output.log", adir / "output.tail"
    candidates = [p for p in (tail, log) if p.exists()]
    if not candidates:
        return "", 0.0
    newest = max(candidates, key=lambda p: p.stat().st_mtime)
    source = tail if tail.exists() and tail.stat().st_mtime >= log.stat().st_mtime - 1 else log
    with source.open("rb") as handle:
        size = handle.seek(0, 2)
        handle.seek(max(0, size - TAIL_BYTES))
        data = handle.read()
    text = data.decode("utf-8", errors="replace")
    if size > TAIL_BYTES:                     # the first line was cut in the middle
        text = text.split("\n", 1)[-1]
    return text, newest.stat().st_mtime


_WORKTREE = re.compile(r"/\S*?/worktrees/[^/\s;&|'\"]+/?")
_CD = re.compile(r"^(cd\s+\S+\s*(&&|;)\s*)+")


def _cut(text: Any, limit: int) -> str:
    """One line, paths relative to the attempt's worktree (the long prefix says nothing), at most `limit` chars."""
    flat = _WORKTREE.sub("", _CD.sub("", " ".join(str(text or "").split())))
    return flat if len(flat) <= limit else flat[: limit - 1] + "…"


def _claude_what(name: str, args: Any) -> str:
    if not isinstance(args, dict):
        return ""
    for key in ("command", "file_path", "path", "pattern", "url", "query", "description", "prompt", "notebook_path"):
        if args.get(key):
            return _cut(args[key], WHAT_CHARS)
    return ""


def _claude(text: str) -> dict[str, Any]:
    open_tools: dict[str, dict[str, Any]] = {}
    steps: list[dict[str, Any]] = []
    said = None
    for line in text.splitlines():
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        message = event.get("message") if isinstance(event.get("message"), dict) else {}
        content = message.get("content") if isinstance(message.get("content"), list) else []
        if event.get("type") == "assistant":
            for part in content:
                if not isinstance(part, dict):
                    continue
                if part.get("type") == "tool_use":
                    open_tools[str(part.get("id"))] = {"tool": str(part.get("name") or "?"),
                                                       "what": _claude_what(str(part.get("name")), part.get("input"))}
                elif part.get("type") == "text" and str(part.get("text") or "").strip():
                    said = _cut(part["text"], SAID_CHARS)
        elif event.get("type") == "user":
            for part in content:
                if isinstance(part, dict) and part.get("type") == "tool_result":
                    done = open_tools.pop(str(part.get("tool_use_id")), None)
                    if done:
                        steps.append({**done, "ok": not part.get("is_error")})
    current = list(open_tools.values())[-1] if open_tools else None
    return {"current": current, "said": said, "steps": steps[-STEPS:]}


def _codex_command(line: str) -> str:
    command = re.sub(r"\s+in /\S+\s*$", "", line.strip())
    wrapped = re.match(r"^\S*bash -lc (['\"])(.*)\1$", command)
    return _cut(wrapped.group(2) if wrapped else command, WHAT_CHARS)


def _codex(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    steps: list[dict[str, Any]] = []
    current = None
    said = None
    i = 0
    while i < len(lines):
        head = lines[i].strip()
        if head == "exec" and i + 1 < len(lines):
            if current:
                steps.append({**current, "ok": None})
            current = {"tool": "exec", "what": _codex_command(lines[i + 1])}
            i += 2
            continue
        done = _CODEX_DONE.match(lines[i])
        if done and current:
            steps.append({**current, "ok": done.group(1) == "succeeded"})
            current = None
        elif head == "codex":
            words = []
            j = i + 1
            while j < len(lines) and lines[j].strip() not in _CODEX_HEADERS and len(" ".join(words)) < SAID_CHARS:
                words.append(lines[j])
                j += 1
            if words:
                said = _cut(" ".join(words), SAID_CHARS)
            i = j
            continue
        elif head == "apply patch":
            files = []
            for ln in lines[i + 1:i + 40]:
                if ln.startswith("diff --git") or ln.strip() in _CODEX_HEADERS:
                    break
                if ln.startswith("/"):
                    files.append(ln.strip())
            steps.append({"tool": "apply patch", "what": _cut(", ".join(files) or "cambios de archivos", WHAT_CHARS),
                          "ok": True})
        i += 1
    return {"current": current, "said": said, "steps": steps[-STEPS:]}


def read(adir: Path) -> dict[str, Any]:
    text, updated = _tail(adir)
    shape = _claude if any(line.startswith('{"type"') for line in text.splitlines()[:200]) else _codex
    return {**shape(text), "updated_at": updated or None}


def now(rdir: Path, project: str, attempts: list[str]) -> dict[str, dict[str, Any]]:
    out = {}
    for attempt_id in attempts:
        try:
            adir = attempt_dir(rdir, project, attempt_id)
            if adir is not None:
                out[attempt_id] = read(adir)
        except OSError:
            continue
    return out
