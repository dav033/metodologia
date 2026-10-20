"""Requirements-v1 gate. Public API: record, check, require_ready, entry_context.

record(rdir, review) persists a reviewed scope/requirements/limits/acceptance snapshot,
approval evidence, unresolved decisions and source fingerprints in REQUIREMENTS.json.
check returns {status: ready|needs_revalidation|legacy, reasons, snapshot}; snapshot
is validated schema-v1 data, or None. Consumers must call require_ready before effects.
Legacy plans opt in with PLAN frontmatter execution_contract: requirements-v1;
an existing snapshot also activates enforcement. No function grants plan approval.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from bt_lock import central_lock

CONTRACT = "requirements-v1"
FIELDS = ("goal", "scope", "requirements", "limits", "acceptance", "approval")
MAX_BYTES = 65536
_PLAN_STATUS_BLOCK = re.compile(
    r"(?m)^<!-- bitacora:status:begin -->[ \t]*\r?\n.*?^<!-- bitacora:status:end -->[ \t]*(?:\r?\n|$)",
    re.DOTALL,
)


def _validate(data: object, stored: bool = False) -> dict:
    if not isinstance(data, dict):
        raise TypeError("Requirements review must be an object")
    for key in FIELDS:
        if not isinstance(data.get(key), str) or not data[key].strip() or len(data[key]) > 8000:
            raise ValueError(f"Requirements review needs bounded nonempty {key}")
    for key in ("evidence", "unresolved"):
        values = data.get(key)
        if (not isinstance(values, list) or len(values) > 32
                or any(not isinstance(value, str) or not value.strip() or len(value) > 1000 for value in values)):
            raise ValueError(f"Invalid requirements {key}")
    if not data["evidence"]:
        raise ValueError("Requirements review needs source evidence")
    if stored:
        if type(data.get("schema")) is not int or data["schema"] != 1:
            raise ValueError("Unsupported requirements schema")
        fingerprints = data.get("fingerprints")
        if (not isinstance(fingerprints, dict) or not {"SPEC.md", "PLAN.md"} <= fingerprints.keys()
                or any(not isinstance(k, str) or not isinstance(v, str) or not re.fullmatch(r"[0-9a-f]{64}", v)
                       for k, v in fingerprints.items())):
            raise ValueError("Invalid requirements fingerprints")
        expected = {"SPEC.md", "PLAN.md", *data["evidence"]}
        if not expected <= fingerprints.keys() or set(fingerprints) - expected - {"../../DECISIONS.md"}:
            raise ValueError("Requirements evidence/fingerprints mismatch")
        if not isinstance(data.get("reviewed_at"), str):
            raise ValueError("Missing requirements review timestamp")
        dt.datetime.fromisoformat(data["reviewed_at"])
    return data


def _source(rdir: Path, name: str) -> str:
    path = rdir / name
    authority = rdir.parent.parent if rdir.parent.name == "requirements" else rdir
    if Path(name).is_absolute() or not path.resolve().is_relative_to(authority.resolve()):
        raise ValueError("Requirements evidence must stay within the project directory")
    if path.name == "REQUIREMENTS.json":
        raise ValueError("Requirements snapshot cannot be its own evidence")
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("Requirements evidence exceeds 65536 bytes")
    text = path.read_text(encoding="utf-8")
    canonical = path.resolve()
    if canonical in ((rdir / "PLAN.md").resolve(), (rdir / "SPEC.md").resolve()):
        front = re.match(r"\A---[ \t]*\n(.*?)\n---(?:\n|$)", text, re.DOTALL)
        if front:
            normalized = re.sub(r"^status:.*$", "status: <operational>", front[1], flags=re.MULTILINE)
            text = text[:front.start(1)] + normalized + text[front.end(1):]
    if canonical == (rdir / "PLAN.md").resolve():
        # The Scheduler refreshes this generated read-model block as task states change.
        text = _PLAN_STATUS_BLOCK.sub("", text)
        # Operational progress does not change approved scope or task contracts.
        text = re.sub(r"^## Progress log\s*\n(.*?)(?=^## |\Z)",
                      lambda match: "\n".join(line for line in match[1].splitlines()
                                               if re.match(r"\s*- \[[ xX]\]", line)),
                      text, flags=re.MULTILINE | re.DOTALL)
        text = re.sub(r"(?m)^(\s*- )\[[ xX]\]", r"\1[ ]", text)
    return text


def _fingerprints(rdir: Path, names: list[str]) -> dict[str, str]:
    names = list(names)
    decisions = rdir.parent.parent / "DECISIONS.md"
    if rdir.parent.name == "requirements" and decisions.exists():
        names.append("../../DECISIONS.md")
    result = {}
    for name in sorted({"SPEC.md", "PLAN.md", *names}):
        path = rdir / name
        if name == "../../DECISIONS.md" and path.resolve() == decisions.resolve():
            # Central decisions are authority inputs, not prompt evidence. Hash them
            # incrementally so a large decision log stays bounded in memory.
            with path.open("rb") as source:
                digest = hashlib.file_digest(source, "sha256").hexdigest()
        else:
            digest = hashlib.sha256(_source(rdir, name).encode()).hexdigest()
        result[name] = digest
    return result


def _contract(rdir: Path) -> str:
    plan = rdir / "PLAN.md"
    text = plan.read_text(encoding="utf-8") if plan.exists() else ""
    front = re.match(r"\A---[ \t]*\n(.*?)\n---(?:\n|$)", text, re.DOTALL)
    if not front:
        if re.search(r"(?m)^\s*execution_contract\b", text):
            raise ValueError("Malformed requirements contract frontmatter")
        return ""
    lines = [line for line in front[1].splitlines()
             if re.match(r"\s*(?:execution_contract|['\"]execution_contract['\"])\s*:", line)]
    if not lines:
        if re.search(r"(?m)^\s*execution_contract\b", front[1]):
            raise ValueError("Malformed requirements execution contract")
        return ""
    if len(lines) != 1:
        raise ValueError("Duplicate requirements execution contract")
    value = lines[0].split(":", 1)[1].strip()
    match = re.fullmatch(r"(?:'([^']*)'|\"([^\"]*)\"|([A-Za-z0-9_-]+))(?:\s+#.*)?", value)
    if not match:
        raise ValueError("Malformed requirements execution contract")
    contract = next(part for part in match.groups() if part is not None)
    if not contract:
        raise ValueError("Empty requirements execution contract")
    return contract



def record(rdir: Path, review: object) -> dict:
    """Record explicit reviewed facts; unresolved items persist but block execution.

    Required review fields: goal, scope, requirements, limits, acceptance, approval (nonempty
    strings <=8000 chars), evidence (1..32 relative source paths), unresolved (0..32
    decision/contradiction descriptions). List entries are nonempty, <=1000 chars.
    PLAN/SPEC are always fingerprinted. Review does not modify PLAN's approval status.
    """
    data = _validate(review)
    contract = _contract(rdir)
    if contract and contract != CONTRACT:
        raise ValueError("Unsupported requirements execution contract")
    with central_lock("requirements-" + hashlib.sha256(str(rdir.resolve()).encode()).hexdigest()[:16]):
        snapshot = {key: data[key] for key in (*FIELDS, "evidence", "unresolved")}
        snapshot.update(schema=1, reviewed_at=dt.datetime.now(dt.UTC).isoformat(),
                        fingerprints=_fingerprints(rdir, data["evidence"]))
        payload = json.dumps(snapshot, ensure_ascii=False, indent=2)
        if len(payload.encode()) > MAX_BYTES:
            raise ValueError("Requirements snapshot exceeds 65536 bytes")
        fd, name = tempfile.mkstemp(prefix=".requirements-", suffix=".tmp", dir=rdir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(payload + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, rdir / "REQUIREMENTS.json")
        finally:
            Path(name).unlink(missing_ok=True)
    return snapshot


def check(rdir: Path) -> dict:
    """Reread authority every time; invalid/missing/drifted evidence fails closed."""
    snapshot = None
    try:
        contract = _contract(rdir)
        path = rdir / "REQUIREMENTS.json"
        if contract and contract != CONTRACT:
            raise ValueError("Unsupported requirements execution contract")
        if not contract and not path.exists():
            return {"status": "legacy", "reasons": [], "snapshot": None}
        if not path.exists():
            raise ValueError("Requirements review missing")
        if path.stat().st_size > MAX_BYTES:
            raise ValueError("Requirements snapshot exceeds 65536 bytes")
        snapshot = _validate(json.loads(path.read_text(encoding="utf-8")), stored=True)
        current = _fingerprints(rdir, list(snapshot["fingerprints"]))
        changed = [name for name, digest in current.items() if snapshot["fingerprints"].get(name) != digest]
        reasons = (["Requirements authority changed: " + ", ".join(changed)] if changed else [])
        if snapshot["unresolved"]:
            reasons.append("Unresolved requirements decisions/contradictions; inspect REQUIREMENTS.json")
        return {"status": "needs_revalidation" if reasons else "ready", "reasons": reasons, "snapshot": snapshot}
    except (OSError, ValueError, TypeError, UnicodeError) as exc:
        return {"status": "needs_revalidation", "reasons": [f"Invalid requirements authority: {type(exc).__name__}"],
                "snapshot": None}


def require_ready(rdir: Path) -> dict:
    """Legacy is allowed during bootstrap; --force never bypasses new-mode validation."""
    result = check(rdir)
    if result["status"] == "needs_revalidation":
        raise SystemExit("REQUIREMENTS_REVALIDATION_REQUIRED: " + "; ".join(result["reasons"]))
    return result


def entry_context(root: Path, project: str | None) -> str:
    """Entry/continue diagnostic only: supervised children verify, never reinterview."""
    projects = [root / project] if project else [p for p in root.iterdir() if p.is_dir()] if root.exists() else []
    lines = []
    child = bool(os.environ.get("BITACORA_RUN") and os.environ.get("BITACORA_TASK"))
    for pdir in projects:
        for plan in sorted(pdir.glob("requirements/REQ-*/PLAN.md")):
            result = check(plan.parent)
            if result["status"] == "legacy":
                continue
            lines.append(f"Requirements gate `{plan.parent}`: {result['status']}.")
            lines.extend(result["reasons"])
    if lines:
        lines.append("Supervised child: use approved scope; report drift to the orchestrator; do not interview the owner."
                     if child else "Revalidate only missing or contradictory decisions; retain unchanged approval.")
    return "\n".join(lines)
