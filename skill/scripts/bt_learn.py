"""Record evidence-backed project and owner learnings for future bitácora sessions."""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

from bt_core import ROOT
import bt_lock

SCOPES = ("project", "owner", "skill")
KINDS = ("preference", "convention", "pitfall", "tooling", "decision")
STATUSES = ("candidate", "confirmed", "rejected")
_SECRET_PATTERNS = tuple(re.compile(pattern, re.IGNORECASE) for pattern in (
    r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
    r"\bAKIA[0-9A-Z]{16}\b",
    r"\bgh[pousr]_[A-Za-z0-9]{20,}\b",
    r"\bsk-[A-Za-z0-9_-]{20,}\b",
    r"\bxox[baprs]-[A-Za-z0-9-]+",
    r"\b(?:password|passwd|secret|token|api[_-]?key)\s*[:=]\s*\S{6,}",
    r"\b[0-9a-fA-F]{41,}\b",  # longer than a git SHA-1, which is legitimate evidence
))
_BLOB = re.compile(r"[A-Za-z0-9+=_-]{40,}")  # no '/': a long file path is not a secret


class LearnError(SystemExit):
    """Invalid learning input or storage operation."""


def _now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="microseconds")


def _file(project: str | None, scope: str) -> Path:
    if scope == "project":
        if not project or not project.strip() or Path(project).name != project or project in (".", ".."):
            raise LearnError("A valid project is required for project learnings")
        return ROOT / project / "learnings.json"
    return ROOT / "learnings.json"


def _read(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"schema": 1, "items": []}
    except (OSError, ValueError) as exc:
        raise LearnError(f"Could not read learnings: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema") != 1 or not isinstance(data.get("items"), list):
        raise LearnError(f"Invalid learnings file: {path}")
    return data


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8", newline="\n")
    tmp.replace(path)


def _save(path: Path, data: dict) -> None:
    _atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def _blob(value: str) -> bool:
    """A long opaque token mixing upper case, lower case and digits (base64-like)."""
    return any(any(c.isupper() for c in m) and any(c.islower() for c in m) and any(c.isdigit() for c in m)
               for m in _BLOB.findall(value))


def _secret(*values: str) -> bool:
    return any(pattern.search(value) for value in values for pattern in _SECRET_PATTERNS) or \
        any(_blob(value) for value in values)


def _normalize(text: str) -> str:
    return " ".join("".join(ch.lower() if ch.isalnum() else " " for ch in text).split())


def _similar(left: str, right: str) -> bool:
    a, b = set(_normalize(left).split()), set(_normalize(right).split())
    return bool(a and b) and len(a & b) / len(a | b) >= 0.8


GLOBAL_PREFIX = "LG"  # owner/skill learnings live in one root file; their ids never collide with a project's L-NNN


def scope_of_id(item_id: str, default: str = "project") -> str | None:
    """`LG-…` ids are global (owner or skill: None = look in the root file), anything else is the project's."""
    return None if str(item_id).upper().startswith(GLOBAL_PREFIX + "-") else default


def _next_id(items: list[dict], prefix: str = "L") -> str:
    numbers = [int(match.group(1)) for item in items
               if (match := re.fullmatch(r"LG?-(\d+)", str(item.get("id", ""))))]
    return f"{prefix}-{max(numbers, default=0) + 1:03d}"


def _copy(item: dict, **extra) -> dict:
    return {**item, "evidence": [dict(row) for row in item.get("evidence", [])], **extra}


def add(project: str | None, text: str, evidence: str, source: str = "", scope: str = "project",
        kind: str = "convention", promote_after: int = 3) -> dict:
    """Add an observation, or attach it to a matching learning in the same scope."""
    if scope not in SCOPES:
        raise LearnError(f"Unknown scope '{scope}'")
    if kind not in KINDS:
        raise LearnError(f"Unknown kind '{kind}'")
    if not isinstance(text, str) or not isinstance(evidence, str) or not isinstance(source, str):
        raise LearnError("Text, evidence, and source must be text")
    clean_text = " ".join(text.split())
    clean_evidence = " ".join(evidence.split())
    clean_source = " ".join(source.split())
    if not 12 <= len(clean_text) <= 400:
        raise LearnError("Learning text must be 12..400 characters after whitespace collapse")
    if not clean_evidence:
        raise LearnError("Evidence is required")
    if not isinstance(promote_after, int) or isinstance(promote_after, bool) or promote_after < 1:
        raise LearnError("promote_after must be a positive integer")
    if _secret(clean_text, clean_evidence, clean_source):
        raise LearnError("Possible secret detected; nothing was stored")
    path = _file(project, scope)
    with bt_lock.central_lock("learn"):
        data = _read(path)
        now = _now()
        found = next((item for item in data["items"] if item.get("scope") == scope and
                      (_normalize(item.get("text", "")) == _normalize(clean_text) or
                       _similar(item.get("text", ""), clean_text))), None)
        if found is not None:
            if found.get("status") == "rejected":
                return _copy(found, ignored=True, created=False)
            same_source = any(row.get("source", "") == clean_source for row in found.get("evidence", []))
            if not same_source:
                found.setdefault("evidence", []).append({"at": now, "source": clean_source, "note": clean_evidence})
                found["sightings"] = int(found.get("sightings", 0)) + 1
                if found.get("status") == "candidate" and found["sightings"] >= promote_after:
                    found["status"], found["promoted_by"] = "confirmed", "sightings"
            found["updated"] = now
            _save(path, data)
            render_md(project if scope == "project" else None)
            return _copy(found, created=False)
        item = {"id": _next_id(data["items"], "L" if scope == "project" else GLOBAL_PREFIX), "scope": scope, "kind": kind, "text": clean_text,
                "status": "candidate", "sightings": 1,
                "evidence": [{"at": now, "source": clean_source, "note": clean_evidence}],
                "created": now, "updated": now, "promoted_by": None}
        data["items"].append(item)
        _save(path, data)
        render_md(project if scope == "project" else None)
        return _copy(item, created=True)


def _change(project: str | None, item_id: str, status: str, scope: str, reason: str = "") -> dict:
    if scope not in SCOPES:
        raise LearnError(f"Unknown scope '{scope}'")
    path = _file(project, scope)
    with bt_lock.central_lock("learn"):
        data = _read(path)
        item = next((row for row in data["items"] if row.get("id") == item_id and
                     (row.get("scope") == scope or (scope != "project" and row.get("scope") in ("owner", "skill")))),
                    None)
        if item is None:
            raise LearnError(f"Unknown learning id '{item_id}'")
        item["status"], item["updated"] = status, _now()
        if status == "confirmed":
            item["promoted_by"] = "owner"
        elif reason.strip():
            item.setdefault("evidence", []).append({"at": item["updated"], "source": "owner rejection",
                                                     "note": " ".join(reason.split())})
        _save(path, data)
        render_md(project if scope == "project" else None)
        return _copy(item)


def confirm(project: str | None, item_id: str, scope: str = "project") -> dict:
    return _change(project, item_id, "confirmed", scope)


def reject(project: str | None, item_id: str, scope: str = "project", reason: str = "") -> dict:
    return _change(project, item_id, "rejected", scope, reason)


def listing(project: str | None, scope: str | None = None, status: str | None = None) -> list[dict]:
    if scope is not None and scope not in SCOPES:
        raise LearnError(f"Unknown scope '{scope}'")
    if status is not None and status not in STATUSES:
        raise LearnError(f"Unknown status '{status}'")
    items = []
    for selected in ((scope,) if scope else ("owner", "skill", "project")):
        if selected == "project" and project is None:
            continue
        items.extend(row for row in _read(_file(project, selected))["items"] if row.get("scope") == selected)
    return [_copy(item) for item in items if (scope is None or item.get("scope") == scope) and
            (status is None or item.get("status") == status)]


def brief(project: str | None, max_items: int = 12) -> str:
    if not isinstance(max_items, int) or isinstance(max_items, bool) or max_items < 0:
        raise LearnError("max_items must be a non-negative integer")
    all_items = listing(project)
    confirmed = [item for item in all_items if item.get("status") == "confirmed"]
    # Keep global learnings ahead of project learnings and newest first within each scope.
    confirmed = [item for selected in ("owner", "skill", "project")
                 for item in sorted((row for row in confirmed if row["scope"] == selected),
                                    key=lambda row: row.get("updated", ""), reverse=True)]
    candidates = sum(item.get("status") == "candidate" for item in all_items)
    if not confirmed and not candidates:
        return ""
    lines = ["### Learned so far"] if confirmed else []
    for item in confirmed[:max_items]:
        lines.append(f"- [{item['id']} · {item['kind']}] {item['text']}")
    if len(confirmed) > max_items:
        lines.append(f"(+{len(confirmed) - max_items} more: bitacora.py learn list)")
    if candidates:
        lines.append(f"Candidates awaiting confirmation: {candidates}")
    return "\n".join(lines)


def render_md(project: str | None) -> Path:
    """Regenerate the human-readable learning index for a project or global scopes."""
    path = (ROOT / project if project else ROOT) / "LEARNINGS.md"
    items = listing(project, scope="project" if project else None)
    lines = ["# Learnings", ""]
    for status, title in (("confirmed", "Confirmed"), ("candidate", "Candidates"), ("rejected", "Rejected")):
        lines.extend((f"## {title}", ""))
        selected = [item for item in items if item.get("status") == status]
        if not selected:
            lines.extend(("_None._", ""))
        for item in selected:
            lines.append(f"- **{item['id']} · {item['kind']}** {item['text']}")
            for row in item.get("evidence", []):
                lines.append(f"  - {row.get('at', '')} · {row.get('source', '')}: {row.get('note', '')}")
            lines.append("")
    with bt_lock.central_lock("learn"):
        _atomic_write(path, "\n".join(lines).rstrip() + "\n")
    return path
