"""Upgrade audit declarations and add independent cross-checks in working plans."""
from __future__ import annotations

import copy
import re
from collections.abc import Callable
from pathlib import Path

from . import contract as pc
from . import quality
from . import revisions as rev

PLAN_MD = "PLAN.md"
PLAN_JSON = "PLAN.json"


def _next_id(taken: set[str], base: str) -> str:
    """`T18` -> `T18b` (the next free letter); a task that already ends in a letter gets the next free number."""
    if re.fullmatch(r"T[0-9]+(?:\.[0-9]+)?", base):
        for letter in "bcdefghijklmnopqrstuvwxyz":
            if base + letter not in taken:
                return base + letter
    top = max((int(m.group(1)) for t in taken if (m := re.match(r"T([0-9]+)", t))), default=0)
    return f"T{top + 1}"


def _cross_check_of(task: dict, new_id: str) -> dict:
    """A copy of an audit task that reviews the same scope independently, with its own report and ledger."""
    clone = copy.deepcopy(task)
    paths = [p for p in task.get("expected_paths", []) if isinstance(p, str)]
    old_report = next((p for p in paths if p.endswith(".md")), None)
    stem = (old_report[:-3] if old_report else next((p[: -len(quality.LEDGER_SUFFIX)] for p in paths
                                                      if p.endswith(quality.LEDGER_SUFFIX)), f"{task['id'].lower()}"))
    new_stem = f"{stem}-crosscheck"
    clone["id"] = new_id
    # Each reviewer writes separate evidence, so inherited exclusive claims would
    # needlessly serialize independent passes over the same product.
    clone["shared_resources"] = []
    clone["title"] = f"Cross-check audit of {task['id']}: {task.get('title', '')}"[:200]
    clone["objective"] = (f"An independent second audit of the scope of {task['id']}. Do not read its report or ledger "
                          "first: confirm findings yourself and record every one in your own ledger.")
    clone["expected_paths"] = ([f"{new_stem}.md"] if old_report else []) + [f"{new_stem}{quality.LEDGER_SUFFIX}"]
    if old_report:
        for item in clone.get("verification", []):
            if isinstance(item, dict) and isinstance(item.get("value"), str):
                item["value"] = item["value"].replace(old_report, f"{new_stem}.md")
    clone["estimate_rationale"] = (f"Cross-check of {task['id']}: a bounded independent pass over the same scope; "
                                   + str(task.get("estimate_rationale", "")))[:400]
    return clone


def retrofit_audit(directory: Path, cross_check: bool, read_plan: Callable) -> list[str]:
    """Bring a plan written before the audit gate in line, as a new working revision: each `kind: audit` task that does
    not list exactly one findings ledger gets `<its first .md report>` with the ledger suffix (else `<task>.findings.json`
    in its first directory), in PLAN.json and on its PLAN.md line. Nothing else changes and nothing is frozen: review the
    diff, then `freeze`. It never invents an end-to-end test; if the plan lacks one `check` still says so. Returns what
    it changed (empty when the plan already complies)."""
    directory = Path(directory)
    plan, report = read_plan(directory)
    if not isinstance(plan, dict) or not isinstance(plan.get("tasks"), list):
        raise pc.PlanContractError("PLAN_INVALID", report.errors or ["PLAN.json is missing or unreadable"])
    last = rev.latest(directory)
    changed: list[str] = []
    md_path = directory / PLAN_MD
    md_text = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    for task in plan["tasks"]:
        if not isinstance(task, dict) or task.get("kind") != "audit":
            continue
        paths = task.get("expected_paths") if isinstance(task.get("expected_paths"), list) else []
        if sum(1 for p in paths if isinstance(p, str) and p.endswith(quality.LEDGER_SUFFIX)) == 1:
            continue
        report_md = next((p for p in paths if isinstance(p, str) and p.endswith(".md")), None)
        if report_md:
            ledger = report_md[:-3] + quality.LEDGER_SUFFIX
        else:
            first_dir = next((p.rsplit("/", 1)[0] + "/" for p in paths if isinstance(p, str) and "/" in p), "")
            ledger = f"{first_dir}{str(task.get('id')).lower()}{quality.LEDGER_SUFFIX}"
        task["expected_paths"] = [p for p in paths if not (isinstance(p, str) and p.endswith(quality.LEDGER_SUFFIX))] + [ledger]
        line = re.compile(rf"^(- \[.\] {re.escape(str(task.get('id')))} .*?· files: )([^·\n]*?)(\s*(?:·|$))", re.M)
        md_text, count = line.subn(lambda m: f"{m.group(1)}{m.group(2).rstrip()}, {ledger}{m.group(3)}", md_text, count=1)
        changed.append(f"{task['id']}: declares {ledger}" + ("" if count else " (PLAN.md line has no `files:`; add it by hand)"))
    audits = [t for t in plan["tasks"] if isinstance(t, dict) and t.get("kind") == "audit"]
    if cross_check and len(audits) == 1:
        original = audits[0]
        taken = {t.get("id") for t in plan["tasks"] if isinstance(t, dict)}
        new_id = _next_id({i for i in taken if isinstance(i, str)}, original["id"])
        clone = _cross_check_of(original, new_id)
        plan["tasks"].insert(plan["tasks"].index(original) + 1, clone)
        for task in plan["tasks"]:                       # whatever waited for the audit waits for its cross-check too
            if isinstance(task, dict) and original["id"] in task.get("after", []) and task is not clone:
                task["after"] = [*task["after"], new_id]
                md_text = re.sub(rf"^(- \[.\] {re.escape(str(task['id']))} .*?after: [^·\n]*?\b{re.escape(original['id'])})(?=[,\s·]|$)",
                                 lambda m: f"{m.group(1)}, {new_id}", md_text, count=1, flags=re.M)
        line = re.search(rf"^(- \[.\] {re.escape(original['id'])} .*)$", md_text, re.M)
        if line:
            row = line.group(1).replace(f"{original['id']} —", f"{new_id} —", 1)
            row = re.sub(r"(?<=— )(.*?)(?= ·)", lambda m: f"Cross-check audit of {original['id']}: {m.group(1)}", row, count=1)
            row = re.sub(r"files: [^·\n]*", "files: " + ", ".join(clone["expected_paths"]) + " ", row, count=1)
            row = re.sub(r"verify: `[^`]*`", f"verify: `{clone['verification'][0]['value']}`", row, count=1) \
                if clone.get("verification") else row
            md_text = md_text[:line.end()] + "\n" + row + md_text[line.end():]
        else:
            changed.append(f"{new_id}: PLAN.md has no line for {original['id']}; add the cross-check line by hand")
        changed.append(f"{new_id}: cross-check audit of {original['id']} ({', '.join(clone['expected_paths'])})")
    if changed:
        plan["revision"] = (last["revision"] + 1) if last else plan.get("revision", 1)
        (directory / PLAN_JSON).write_text(pc.dumps(plan), encoding="utf-8")
        if md_text:
            md_path.write_text(md_text, encoding="utf-8")
    return changed
