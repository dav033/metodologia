"""Stage readiness as a standing gate: the plan is checked as it changes, and a subplan whose stage would be refused cannot be confirmed.

`bt_plan_adapter.stage_readiness` walks every next stage with the same gate as «Ejecutar subplan» (3-4 s for REQ-021). Here its
result is cached by the content of the plan files, so the panel and `planning status` read it for free until something changes,
and `bt_planning_flow.problems` turns a refused stage into a reason the owner sees BEFORE confirming (REQ-021 SP-3: the owner
confirmed, pressed «Ejecutar» and met three plan errors nobody had run the gate for). Errors a later stage only inherits from an
earlier one are reported once, on the subplan that introduces them.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

CACHE = ".planning/readiness.json"
# Errors that depend on where the check runs (no repository registered or cloned here), not on how the plan is structured
ENVIRONMENT = ("could not be verified against a repository", "no repository roots available")


def _key(rdir: Path) -> str:
    h = hashlib.sha256()
    for name in ("PLAN.json", "PLAN.md", "SPEC.md"):
        try:
            h.update((Path(rdir) / name).read_bytes())
        except OSError:
            h.update(b"-")
    try:
        import bt_plan_adapter as adapter
        found = adapter.planner.stages.latest(rdir)
        h.update(str(found[0].get("revision") if found else 0).encode())
    except Exception:  # noqa: BLE001 - an unreadable stage store only widens the key
        h.update(b"?")
    return h.hexdigest()


def _errors(problem: str) -> list[str]:
    """The stage errors of a refusal, without the plan-header ones (`plan.schema_version: missing`…): a plan still being started has
    no header yet, and that is the plan check's business, not a reason to refuse a subplan's confirmation."""
    body = problem.split("cannot be approved: ", 1)[-1] if "cannot be approved: " in problem else problem.split(": ", 1)[-1]
    body = re.sub(r"[^;(]*(?:" + "|".join(re.escape(m) for m in ENVIRONMENT) + r")[^(;]*(?:\([^)]*\))?", "", body)
    return [part.strip() for part in body.split("; ") if part.strip() and not part.strip().startswith("plan.")]


def _subplan_plan(rdir: Path) -> bool:
    try:
        plan = json.loads((Path(rdir) / "PLAN.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    version = str(plan.get("schema_version") or "") if isinstance(plan, dict) else ""
    try:
        return tuple(int(x) for x in version.split(".")[:2]) >= (1, 3) and bool(plan.get("subplans"))
    except ValueError:
        return False


def rows(rdir: Path, *, refresh: bool = False) -> list[dict]:
    """The readiness rows of every next stage, from cache while the plan files are unchanged. [] when it cannot be computed."""
    if not _subplan_plan(rdir):
        return []                                      # stages exist only for schema 1.3 plans with subplans
    path = Path(rdir) / CACHE
    key = _key(rdir)
    if not refresh:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("key") == key and isinstance(data.get("rows"), list):
                return data["rows"]
        except (OSError, ValueError):
            pass
    try:
        import bt_plan_adapter as adapter
        import bt_scheduler_adapter
        found = adapter.stage_readiness(rdir, compatibility_report=bt_scheduler_adapter.plan_compatibility_report(rdir))
    except Exception:  # noqa: BLE001 - a plan that cannot be walked is the plan check's business, never the page's
        return []
    seen: set[str] = set()
    for row in found:
        row["errors"] = [] if row["ok"] or not row["tasks"] or row["depends_on_unfinished"] else _errors(row["problem"])
        row["new_errors"] = [e for e in row["errors"] if e not in seen]
        seen |= set(row["errors"])
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"key": key, "rows": found}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    except OSError:
        pass
    return found


def problem_for(rdir: Path, subplan: str) -> str:
    """Why the stage that adds `subplan` would be refused, in words for the owner; "" when it would be approved or cannot be judged."""
    for row in rows(rdir):
        if row["subplan"] != subplan or row["ok"] or not row["tasks"] or row["depends_on_unfinished"]:
            continue
        if row.get("new_errors"):
            return "no se podrá ejecutar, el plan falla: " + "; ".join(row["new_errors"][:3])
        if row.get("errors"):
            return "no se podrá ejecutar: arrastra un fallo de un subplan anterior"
    return ""
