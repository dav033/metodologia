#!/usr/bin/env python3
"""Verify plans written by planner sessions that had no context (independent-evidence/REQ-90N-*/): they were authored
by fresh agents from the methodology documents alone, not by the implementer of the planner.

For each plan folder: publication gate with `file:`/`command:`/`precedent:` evidence verified against the real
checkouts, quality summary, a corruption battery (each must be refused with the cause) and the approval -> freeze ->
launch gate -> drift lifecycle in a throwaway copy. Writes VERIFICATION.json next to this file; exit 1 on any failure.
"""
from __future__ import annotations

import copy
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path.home() / "dev" / "metodologia" / "skill" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import bt_plan_adapter as adapter  # noqa: E402
import bt_rounds  # noqa: E402

planner = adapter.planner
HERE = Path(__file__).resolve().parent
ROOTS = {"trainingapp": Path.home() / "dev/trainingapp", "maros-nest": Path.home() / "dev/maros/maros-nest",
         "maros-next": Path.home() / "dev/maros/maros-next", "pictures": Path.home() / "dev/pictures"}


def verify(folder: Path) -> dict:
    steps: list[tuple[str, bool, str]] = []

    def step(label: str, ok: bool, detail: str = "") -> None:
        steps.append((label, bool(ok), detail))
        print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f" — {detail[:200]}" if detail and not ok else ""))

    plan_id = re.match(r"(REQ-[0-9]+)", folder.name).group(1)
    plan = json.loads((folder / "PLAN.json").read_text())
    roles = {t["repository"] for t in plan["tasks"]}
    roots = {r: ROOTS[r] for r in roles if r in ROOTS}
    step(f"repositories resolve on this machine ({sorted(roles)})", set(roots) == roles, f"unresolved {roles - set(roots)}")
    work = Path(tempfile.mkdtemp(prefix="indep-")) / folder.name
    shutil.copytree(folder, work)
    adapter.repo_roots = lambda rdir: roots  # the project's registered workspace
    verifier = adapter.ref_verifier(work)
    report = planner.check(work, plan_id=plan_id, repo_roots=roots, verify_files=True, ref_exists=verifier)
    step("publication gate with file/command/precedent evidence verified", report.ok, "; ".join(report.errors[:3]))
    analysis = planner.quality.analyze(plan)
    step("no unordered task collisions, no redundant edges", not analysis["unordered_conflicts"]
         and not analysis["redundant_edges"])
    step("schema 1.1.0 with evidence on every task", plan["schema_version"] == "1.1.0"
         and len(analysis["with_evidence"]) == analysis["tasks"])
    step("uncertain work is kept as confidence low (or the plan has none)",
         True if not analysis["low_confidence"] else all(
             any(r.startswith("assumption:") or r.startswith("spec:") or r.startswith("task:") or r.startswith("file:")
                 for e in t["classification_evidence"].values() for r in e["evidence"])
             for t in plan["tasks"] if t["confidence"] == "low"))
    paths_missing = []
    for t in plan["tasks"]:
        for p in t["expected_paths"]:
            static = re.split(r"[*?\[]", p)[0].rstrip("/")
            if static and not (roots[t["repository"]] / static).exists() and not (folder / static).exists() and not re.search(
                    r"\b(add|create|write|new|build|implement|introduce|define|document|record|extract|write)\b",
                    " ".join([t["title"], t["objective"], *t["acceptance_criteria"]]), re.I) \
                    and not any(v.get("created_by") == t["id"] for v in t["verification"]) \
                    and p not in " ".join([t["title"], t["objective"], *t["acceptance_criteria"],
                                           *[v["value"] for v in t["verification"]]]):  # named as the task's own output
                paths_missing.append(f"{t['id']}:{p}")
    step("planned paths exist or are created by the task that lists them", not paths_missing, ", ".join(paths_missing))

    first = plan["tasks"][0]
    dependent = next((t for t in plan["tasks"] if t["after"]), None)
    md = (work / "PLAN.md").read_text()

    def refused(label: str, mutated: dict, needle: str, text: str | None = None) -> None:
        (work / "PLAN.json").write_text(planner.dumps(mutated))
        (work / "PLAN.md").write_text(text or md)
        errors = "\n".join(planner.check(work, plan_id=plan_id, repo_roots=roots, verify_files=True,
                                         ref_exists=verifier).errors)
        step(f"refused: {label}", needle in errors, f"{needle!r} not in {errors[:200] or 'NO ERROR'}")

    m = copy.deepcopy(plan)
    refused("task id twice in PLAN.md", m, f"{first['id']}: defined 2 times in PLAN.md",
            md + f"- [ ] {first['id']} — Again · repo: {first['repository']}\n")
    m = copy.deepcopy(plan); m["tasks"].append(copy.deepcopy(m["tasks"][0]))
    refused("task id twice in PLAN.json", m, f"{first['id']}: duplicate task id")
    m = copy.deepcopy(plan); m["tasks"][0]["title"] = "Something else entirely"
    refused("title contradiction", m, f"{first['id']}.title")
    other = next((r for r in ROOTS if r not in roles), "elsewhere")
    m = copy.deepcopy(plan); m["tasks"][0]["repository"] = other
    refused("repository contradiction", m, f"{first['id']}.repository")
    if dependent:
        m = copy.deepcopy(plan)
        next(t for t in m["tasks"] if t["id"] == dependent["id"])["after"] = []
        refused("dependency contradiction", m, f"{dependent['id']}.after")
    m = copy.deepcopy(plan); del m["tasks"][0]["classification_evidence"]["risk"]
    refused("risk without evidence", m, f"{first['id']}.classification_evidence.risk")
    m = copy.deepcopy(plan)
    m["tasks"][0]["classification_evidence"]["scope"]["evidence"] = ["file:src/does/not/exist.py"]
    refused("fabricated file evidence", m, "does not exist in repository")
    m = copy.deepcopy(plan)
    m["tasks"][0]["classification_evidence"]["duration"]["evidence"] = ["precedent:REQ-999/T1"]
    refused("fabricated precedent", m, "precedent 'REQ-999/T1' does not exist")
    m = copy.deepcopy(plan)
    m["tasks"][0]["classification_evidence"]["complexity"]["justification"] = "TBD"
    refused("placeholder justification", m, "complexity.justification")
    m = copy.deepcopy(plan); m["tasks"][0]["model_hint"] = "opus"
    refused("scheduling key", m, f"{first['id']}.model_hint")
    m = copy.deepcopy(plan); m["tasks"][0]["estimate_rationale"] = "safe to run in parallel with everything"
    refused("parallel-safety promise", m, "promises parallel safety")

    # lifecycle in the throwaway copy
    (work / "PLAN.json").write_text(planner.dumps(plan))
    (work / "PLAN.md").write_text(re.sub(r"^status: .*$", "status: review", md, count=1, flags=re.M))
    status = bt_rounds.plan_decide(work, True, "", "independent-verification")
    frozen = planner.load_revision(work, 1)
    step("approval freezes exactly the approved bytes", status == "approved"
         and planner.dumps(frozen) == planner.dumps(plan))
    step("launch gate passes for the approved revision", adapter.launch_problem(work, freeze=False) is None)
    edited = copy.deepcopy(plan); edited["revision"] = 2; edited["tasks"][0]["estimated_minutes"] += 5
    (work / "PLAN.json").write_text(planner.dumps(edited))
    problem = adapter.launch_problem(work, freeze=True) or ""
    step("an unapproved edit is PLAN_DRIFT and nothing is frozen", "PLAN_DRIFT" in problem
         and [r["revision"] for r in planner.list_revisions(work)] == [1])
    shutil.rmtree(work.parent, ignore_errors=True)
    return {"plan": folder.name, "ok": all(s[1] for s in steps), "tasks": analysis["tasks"],
            "critical_path": analysis["critical_path"], "low_confidence": analysis["low_confidence"],
            "warnings": report.warnings, "steps": [{"step": a, "ok": b, "detail": c} for a, b, c in steps]}


def main() -> int:
    results = []
    for folder in sorted(HERE.glob("REQ-90*-*/")):
        if not (folder / "PLAN.json").exists():
            results.append({"plan": folder.name, "ok": False, "steps": [], "note": "no PLAN.json (planner did not finish)"})
            print(f"\n== {folder.name}: no PLAN.json")
            continue
        print(f"\n== {folder.name}")
        results.append(verify(folder))
    (HERE / "VERIFICATION.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    done = [r for r in results if r["steps"]]
    print(f"\n{sum(1 for r in done if r['ok'])}/{len(done)} independent plans verified")
    return 0 if done and all(r["ok"] for r in done) else 1


if __name__ == "__main__":
    sys.exit(main())
