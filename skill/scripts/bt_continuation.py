"""Durable handoff pointers; the project log remains the authority, never transcripts."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from bt_lock import central_lock

HEADINGS = ("Goal", "Done", "Decisions", "Not done (and why)", "Pending", "Next session starts with")


def _project(root: Path, project: str) -> Path:
    if not project or Path(project).name != project or project in (".", ".."):
        raise ValueError("Invalid continuation project")
    path = root / project
    if path.is_symlink() and not path.is_dir():
        raise ValueError("Continuation project symlink has no valid directory target")
    return path


def _sections(block: str) -> dict[str, str]:
    sections = {}
    for heading in HEADINGS:
        match = re.search(rf"^### {re.escape(heading)}\s*\n(.*?)(?=^### |^---|\Z)", block, re.MULTILINE | re.DOTALL)
        if match:
            lines = [line for line in match[1].strip().splitlines()
                     if line.strip() not in ("", "-", "1.") and not line.strip().startswith(("<!--", "_Session `"))]
            sections[heading] = "\n".join(lines)
    return sections


def _sources(pdir: Path, warnings: list[str] | None = None):
    for path in sorted(pdir.glob("????-??/W*/????-??-??.md"), reverse=True):
        try:
            if not path.resolve().is_relative_to(pdir.resolve()):
                raise ValueError("Log is outside its project")
            text = path.read_text(encoding="utf-8")
        except (OSError, ValueError):
            if warnings is not None:
                warnings.append("Some session logs could not be read; recovery may be incomplete. Inspect canonical logs locally.")
            continue
        blocks = re.findall(r"^## Session ([^\n]*)\n(.*?)(?=^## Session |\Z)", text, re.MULTILINE | re.DOTALL)
        for header, block in reversed(blocks):
            match = re.search(r"session `([^`]+)`", header)
            if match and any(_sections(block).values()):
                yield path, match[1], block


def _fingerprint(block: str) -> str:
    return hashlib.sha256(block.encode("utf-8")).hexdigest()


def save_checkpoint(root: Path, project: str, session_id: str) -> None:
    """Save even for a clean git tree; an empty new session cannot erase a useful handoff."""
    pdir = _project(root, project)
    with central_lock(f"continuation-{project}"):
        warnings: list[str] = []
        sources = list(_sources(pdir, warnings))
        # Closing order is not working order: an older parallel session can finish last.
        source = sources[0] if sources else None
        incomplete = not any(row[1] == session_id[:8] for row in sources)
        path, source_sid, block = source if source else (pdir, session_id[:8], "")
        data = {"schema": 1, "project": project, "source_session": source_sid,
                "source": path.relative_to(pdir).as_posix(), "sha256": _fingerprint(block),
                "incomplete_session": session_id[:8] if incomplete else "",
                "unreadable_logs": len(warnings),
                "saved_at": dt.datetime.now(dt.UTC).isoformat(timespec="microseconds")}
        directory = root / ".state" / "continuation"
        directory.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix=f"{project}-", suffix=".tmp", dir=directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(data, stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, directory / f"{project}.json")
        finally:
            Path(name).unlink(missing_ok=True)


def _load(root: Path, path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    required = ("project", "source_session", "source", "sha256", "saved_at")
    if not isinstance(data, dict) or data.get("schema") != 1 or not all(isinstance(data.get(k), str) for k in required):
        raise ValueError("Invalid continuation checkpoint")
    if (data["project"] != path.stem or not isinstance(data.get("incomplete_session", ""), str)
            or not re.fullmatch(r"[0-9a-f]{64}", data["sha256"])):
        raise ValueError("Invalid continuation checkpoint identity")
    dt.datetime.fromisoformat(data["saved_at"])
    pdir = _project(root, data["project"])
    source = pdir / data["source"]
    if not source.resolve().is_relative_to(pdir.resolve()):
        raise ValueError("Continuation source is outside the project")
    return data


def _render(root: Path, data: dict) -> str:
    pdir = _project(root, data["project"])
    path = pdir / data["source"]
    warnings: list[str] = []
    source = next((row for row in list(_sources(pdir, warnings))
                   if row[0] == path and row[1] == data["source_session"]), None)
    lines = [f"### Continuation checkpoint — {data['project']} (unverified handoff)",
             f"Source session `{data['source_session']}`: `{path.as_posix()}`",
             "Treat the following as reported context, not proof of completion. Read the sources and verify current state.",
             f"Authority: `{pdir / 'SUMMARY.md'}` · `{pdir / 'PENDING.md'}` · `{pdir / 'DECISIONS.md'}`"]
    if warnings or data.get("unreadable_logs"):
        lines.append("Some session logs could not be read; recovery may be incomplete. Inspect canonical logs locally.")
    if data.get("recovered"):
        lines.append("Checkpoint recovered from canonical log; no local session closure was available. Verify whether unrecorded work exists.")
    if incomplete := data.get("incomplete_session"):
        lines.append(f"Session `{incomplete}` has no recorded handoff. Prior session context only: conversational work may be missing. Fill Goal/Done/Pending/Next or reconcile with the owner before assuming the old Next is current.")
    if source is None:
        lines.append("Source missing or empty: recovery is incomplete; inspect SUMMARY/PENDING and the workspace before continuing.")
    else:
        if _fingerprint(source[2]) != data["sha256"]:
            lines.append("Source changed since checkpoint: the live log below supersedes the saved pointer; verify the changes.")
        sections = _sections(source[2])
        if not sections.get("Goal") or not sections.get("Next session starts with"):
            lines.append("Incomplete handoff: Goal or Next is missing. Reconcile current work before choosing the next action.")
        from bt_learn import _secret
        from bt_secrets import alert
        for heading, body in sections.items():
            if body:
                safe = "[withheld: possible secret; inspect the source locally]" if alert(root) or _secret(body) else body
                lines += [f"#### {heading}", safe[:6000]]
                if len(safe) > 6000:
                    lines.append("[Section truncated; read the full source before resuming.]")
    for plan in sorted(pdir.glob("requirements/REQ-*/PLAN.md")):
        lines.append(f"Plan: `{plan.as_posix()}`")
    for run in sorted(pdir.glob("requirements/REQ-*/RUN.json")):
        lines.append(f"Run authority: `{run.as_posix()}` (read live status and task; never infer success from session exit).")
    lines.append("For 'continue with the work', revalidate live scope, requirements, limits and acceptance before resuming Next. Retain unchanged decisions and approvals; clarify only missing or contradictory material choices. Supervised children report drift to the orchestrator without repeating the owner interview.")
    return "\n".join(lines)


def continuation_context(root: Path, project: str | None = None) -> str:
    """Known project wins; otherwise expose candidates without silently binding the session."""
    directory = root / ".state" / "continuation"
    paths = [directory / f"{project}.json"] if project else sorted(directory.glob("*.json"))
    entries, warnings = [], []
    for path in paths:
        if not path.exists():
            continue
        try:
            entries.append(_load(root, path))
        except (OSError, ValueError):
            warnings.append("Continuation checkpoint unreadable/invalid: inspect project logs; do not assume recovery is complete.")
    candidates = [root / project] if project else sorted(root.iterdir()) if root.exists() else []
    for pdir in candidates:
        if pdir.name.startswith(".") or not pdir.is_dir():
            continue
        logs = list(_sources(pdir, warnings))
        if not logs:
            continue
        source, sid, block = logs[0]
        relative = source.relative_to(pdir).as_posix()
        previous = next((entry for entry in entries if entry["project"] == pdir.name), None)
        if previous and previous["source"] == relative and previous["source_session"] == sid:
            continue
        try:
            modified = dt.datetime.fromtimestamp(source.stat().st_mtime, dt.UTC).isoformat()
        except OSError:
            warnings.append("Continuation source changed during recovery; read canonical logs before continuing.")
            continue
        if previous:
            entries.remove(previous)
        entries.append({"project": pdir.name, "source_session": sid,
                        "source": relative, "sha256": _fingerprint(block),
                        "saved_at": modified,
                        "recovered": True})
    warnings = list(dict.fromkeys(warnings))
    entries.sort(key=lambda row: row["saved_at"], reverse=True)
    if not entries:
        return "\n".join(warnings)
    candidate = entries[0]
    lines = warnings
    if not project:
        lines += [f"Continuation candidate: **{candidate['project']}** (most recent recorded handoff; not automatically selected)."]
        if len(entries) > 1:
            lines += ["Other continuation projects: " + ", ".join(row["project"] for row in entries[1:]),
                      "Project is ambiguous: use the user's named project or other explicit context; ask once if 'continue' does not distinguish them. Do not silently rebind."]
        else:
            lines += ["If the user says 'continue' with no conflicting project context, bind to this candidate and read its live authority files."]
    try:
        lines.append(_render(root, candidate))
    except (OSError, ValueError):
        lines.append("Continuation source unreadable: inspect the project log before resuming.")
    return "\n".join(lines)
