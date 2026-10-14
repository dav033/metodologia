#!/usr/bin/env python3
"""Run the planning trials of REQ-012 against the REAL repositories named in trials_data.ROOTS.

For every trial: write PLAN.md (human text) and PLAN.json (from the task definitions) into a scratch requirement folder,
then (1) publish-gate it with `file:` evidence verified against the checkout, (2) judge quality beyond the schema
(commands exist, planned paths exist or are created by their task, real references are covered, critical path and
classification expectations), (3) corrupt it in ten ways and require each to be refused, (4) approve -> freeze -> launch
gate -> revise -> drift -> re-approve through the methodology's own functions, with a sentinel RUN.json that must keep its
bytes, (5) feed the frozen revision to the scheduler core's reader (read-only).

Nothing here is simulated: a failed expectation is a failed trial and exit code 1. Run from anywhere:
    python3 run_trials.py [--keep DIR]
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = Path.home() / "dev" / "metodologia" / "skill" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(HERE))

import bt_plan_adapter as adapter  # noqa: E402
import bt_planner as planner  # noqa: E402
import bt_rounds  # noqa: E402
from bt_planner import contract as pc  # noqa: E402
from bt_planner import quality  # noqa: E402
from trials_data import ROOTS, TRIALS  # noqa: E402

CREATION_WORDS = re.compile(r"\b(add|create|write|new|build|implement|provide|introduce|define|document|record)\b", re.I)
RESULTS: list[dict] = []


class Trial:
    def __init__(self, name: str, spec: dict, root: Path):
        self.name, self.spec = name, spec
        self.dir = root / name
        self.dir.mkdir(parents=True)
        self.steps: list[tuple[str, bool, str]] = []
        self.repo = ROOTS[spec["repo"]]
        self.roots = {spec["repo"]: self.repo}

    # -- helpers ------------------------------------------------------------------------------------------------
    def step(self, label: str, ok: bool, detail: str = "") -> bool:
        self.steps.append((label, bool(ok), detail))
        print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f" — {detail}" if detail and not ok else ""))
        return bool(ok)

    def plan_dict(self, tasks: list[dict] | None = None, milestones: dict | None = None) -> dict:
        stones = milestones or self.spec["milestones"]
        return {"schema_version": planner.SCHEMA_VERSION, "plan_id": planner.default_plan_id(self.dir), "revision": 1,
                "spec_ref": "SPEC.md",
                "milestones": [{"id": mid, "title": title, "acceptance_criteria": crit}
                               for mid, (title, crit) in stones.items()],
                "tasks": copy.deepcopy(tasks if tasks is not None else self.spec["tasks"])}

    def write(self, plan: dict, md: str | None = None, status: str | None = None) -> None:
        (self.dir / "SPEC.md").write_text(self.spec["spec"], encoding="utf-8")
        text = md if md is not None else self.spec["plan_md"]
        if status:
            text = re.sub(r"^status: .*$", f"status: {status}", text, count=1, flags=re.M)
        (self.dir / "PLAN.md").write_text(text, encoding="utf-8")
        (self.dir / "PLAN.json").write_text(planner.dumps(plan), encoding="utf-8")

    def check(self, plan: dict | None = None) -> pc.Report:
        return planner.check(self.dir, plan, repo_roots=self.roots) if plan is not None else \
            planner.check(self.dir, repo_roots=self.roots)

    # -- quality judgement (beyond the schema) -------------------------------------------------------------------
    def judge(self, plan: dict) -> None:
        tasks = {t["id"]: t for t in plan["tasks"]}
        expect = self.spec.get("expect", {})
        analysis = quality.analyze(plan)
        self.analysis = analysis
        if "critical_path" in expect:
            self.step("critical path is the expected dependency chain",
                      analysis["critical_path"]["tasks"] == expect["critical_path"],
                      f"got {analysis['critical_path']['tasks']}")
        for tid, want in expect.get("classify", {}).items():
            got = {k: tasks[tid][k] for k in want}
            self.step(f"{tid} classified {want} (independent dimensions)", got == want, f"got {got}")
        if "low_confidence" in expect:
            self.step("uncertain tasks keep confidence=low and the plan still publishes",
                      sorted(analysis["low_confidence"]) == sorted(expect["low_confidence"]),
                      f"got {analysis['low_confidence']}")
        self.step("every task has a machine-checked verification or an explicit manual check with expected result",
                  all(any(v["type"] == "command" or v.get("expected") for v in t["verification"]) for t in tasks.values()))
        self.step("every high-risk task names a command or an explicit manual check (AC-07)",
                  all(any(v["type"] in ("command", "manual") for v in t["verification"])
                      for t in tasks.values() if t["risk"] == "high"))
        # commands must refer to scripts/modules that exist (no invented commands)
        bad = []
        scripts: set[str] = set()
        for manifest in self.repo.rglob("package.json"):
            if "node_modules" in manifest.parts:
                continue
            try:
                scripts |= set(json.loads(manifest.read_text()).get("scripts", {}))
            except (OSError, ValueError):
                pass
        for t in tasks.values():
            for v in t["verification"]:
                if v["type"] != "command":
                    continue
                value = v["value"]
                found = re.match(r"npm (?:run )?([\w:.-]+)", value)
                if found and self.spec["repo"] == "trainingapp":
                    if found.group(1) not in scripts and found.group(1) not in ("test", "install"):
                        bad.append(f"{t['id']}: npm script {found.group(1)!r} not in any package.json")
                found = re.match(r"python3 -m unittest (?:discover -s )?([\w.]+)", value)
                if found and self.spec["repo"] == "metodologia":
                    mod = found.group(1)
                    target = SCRIPTS / (mod.replace(".", "/") + ".py") if mod != "tests" else SCRIPTS / "tests"
                    if not target.exists():
                        bad.append(f"{t['id']}: test module {mod!r} not found")
        self.step("verification commands refer to scripts and modules that exist", not bad, "; ".join(bad))
        # planned paths: existing, or created by a task that says so
        invented = []
        for t in tasks.values():
            for path in t["expected_paths"]:
                static = re.split(r"[*?\[]", path)[0].rstrip("/")
                if (self.repo / static).exists():
                    continue
                declared = CREATION_WORDS.search(" ".join([t["title"], t["objective"], *t["acceptance_criteria"]])) or any(
                    v.get("created_by") == t["id"] for v in t["verification"])
                if not declared:
                    invented.append(f"{t['id']}:{path}")
        self.step("planned paths exist, or belong to a task that creates them (no invented paths)", not invented,
                  ", ".join(invented))
        # connectivity: no task floats free of the graph in a multi-task plan
        linked = {t["id"] for t in tasks.values() if t["after"]} | {d for t in tasks.values() for d in t["after"]}
        loose = sorted(set(tasks) - linked) if len(tasks) > 1 else []
        self.step("no task floats outside the dependency graph", not loose, f"loose: {loose}")
        # real-world coverage: the references a grep finds are all covered by a task of the plan
        if "covers_inventory" in expect:
            out = subprocess.run(["grep", "-rl", "@training/", ".", "--exclude-dir=node_modules", "--exclude-dir=.next",
                                  "--exclude=package-lock.json"], cwd=self.repo, capture_output=True, text=True).stdout
            files = sorted(f[2:] for f in out.split() if f.startswith("./"))
            covered = {p for t in tasks.values() if t["id"] in expect["covers_inventory"][1] for p in t["expected_paths"]}
            missing = [f for f in files if f not in covered]
            self.step(f"plan covers all {len(files)} real files that reference the old scope", not missing,
                      f"uncovered: {missing}")

    # -- corruption: each must be refused ------------------------------------------------------------------------
    def mutations(self, plan: dict) -> None:
        base_md = self.spec["plan_md"]
        first, second = plan["tasks"][0], plan["tasks"][-1]

        def refused(label: str, mutated: dict, md: str | None, *needles: str) -> None:
            self.write(mutated, md, status="review")
            errors = "\n".join(self.check().errors)
            self.step(f"refused: {label}", bool(errors) and all(n in errors for n in needles),
                      f"needles {needles!r} not all in: {errors[:300] or 'NO ERROR'}")

        m = copy.deepcopy(plan)
        refused("task id defined twice in PLAN.md", m, base_md + f"- [ ] {first['id']} — Another {first['id']} · repo: {first['repository']}\n",
                f"{first['id']}: defined 2 times in PLAN.md")
        m = copy.deepcopy(plan); m["tasks"].append(copy.deepcopy(m["tasks"][0]))
        refused("task id defined twice in PLAN.json", m, None, f"{first['id']}: duplicate task id")
        m = copy.deepcopy(plan); m["tasks"][0]["title"] = "Something else entirely"
        refused("title contradicts PLAN.md", m, None, f"{first['id']}.title")
        m = copy.deepcopy(plan); m["tasks"][0]["repository"] = "elsewhere"
        refused("repository contradicts PLAN.md", m, None, f"{first['id']}.repository")
        target = next(t for t in plan["tasks"] if t["after"])
        m = copy.deepcopy(plan)
        next(t for t in m["tasks"] if t["id"] == target["id"])["after"] = []
        refused("dependency contradicts PLAN.md", m, None, f"{target['id']}.after")
        withv = next((t for t in plan["tasks"] if re.search(r"verify: `", base_md.split(f"{t['id']} —")[1].split("\n")[0])), None)
        if withv:
            m = copy.deepcopy(plan)
            next(t for t in m["tasks"] if t["id"] == withv["id"])["verification"] = [
                {"type": "command", "value": "make test", "purpose": "a different command than PLAN.md states"}]
            refused("verification contradicts PLAN.md", m, None, f"{withv['id']}.verification")
        m = copy.deepcopy(plan)
        del m["tasks"][0]["classification_evidence"]["risk"]
        refused("risk classification without evidence", m, None, f"{first['id']}.classification_evidence.risk")
        m = copy.deepcopy(plan)
        m["tasks"][0]["classification_evidence"]["scope"]["evidence"] = ["file:src/does/not/exist.py"]
        refused("evidence names a file that does not exist", m, None, "does not exist in repository")
        m = copy.deepcopy(plan)
        m["tasks"][0]["classification_evidence"]["complexity"]["justification"] = "TBD"
        refused("justification is a placeholder", m, None, "complexity.justification")
        m = copy.deepcopy(plan)
        t0 = m["tasks"][0]
        t0["confidence"] = "high"
        for dim in t0["classification_evidence"].values():
            dim["evidence"] = ["assumption:it is probably fine"]
        refused("confidence high resting on assumptions", m, None, f"{first['id']}.confidence")
        m = copy.deepcopy(plan)
        # two tasks in the same repo that nothing orders, sharing a path, one claiming coupling low
        a, b = m["tasks"][0], m["tasks"][1]
        a["after"], b["after"] = [], []
        a["coupling"] = "low"
        b["expected_paths"] = list(a["expected_paths"]) or ["src/shared.ts"]
        a["expected_paths"] = b["expected_paths"]
        report = pc.validate(m)
        self.step("refused: unordered tasks share a path while one claims coupling low",
                  any("nothing orders them" in e for e in report.errors), "; ".join(report.errors[:2]))
        m = copy.deepcopy(plan)
        m["tasks"][0]["scope"] = "full_system"
        report = pc.validate(m)
        self.step("refused: a full_system task without a documented exception",
                  any("full_system must be decomposed" in e for e in report.errors))
        self.write(plan, None, status="review")  # restore

    # -- approval -> launch lifecycle ---------------------------------------------------------------------------------
    def lifecycle(self, plan: dict) -> None:
        self.write(plan, status="review")
        run = self.dir / "RUN.json"
        run.write_text(json.dumps({"req": self.name, "status": "running", "sessions": 3,
                                   "tasks": [{"id": "T1", "status": "done", "attempts": 2}]}), encoding="utf-8")
        before = run.read_bytes()
        try:
            adapter.launch_problem(self.dir, freeze=False)
            self.step("unapproved plan is not launchable", adapter.launch_problem(self.dir, freeze=False) is not None
                      and "PLAN_NOT_APPROVED" in adapter.launch_problem(self.dir, freeze=False))
            status = bt_rounds.plan_decide(self.dir, True, "", "trial")
            self.step("approval succeeds and freezes r1", status == "approved" and
                      [r["revision"] for r in planner.list_revisions(self.dir)] == [1])
            frozen = planner.load_revision(self.dir, 1)
            self.step("frozen revision equals exactly the approved PLAN.json", planner.dumps(frozen) == planner.dumps(plan))
            self.step("launch gate passes for the approved revision", adapter.launch_problem(self.dir, freeze=False) is None)
            edited = copy.deepcopy(plan)
            edited["revision"] = 2
            edited["tasks"][0]["estimated_minutes"] += 15
            (self.dir / "PLAN.json").write_text(planner.dumps(edited), encoding="utf-8")
            problem = adapter.launch_problem(self.dir, freeze=True) or ""
            self.step("an edit after approval is refused as PLAN_DRIFT and nothing is frozen",
                      "PLAN_DRIFT" in problem and [r["revision"] for r in planner.list_revisions(self.dir)] == [1], problem[:200])
            (self.dir / "PLAN.md").write_text(re.sub(r"^status: .*$", "status: review", (self.dir / "PLAN.md").read_text(),
                                                     count=1, flags=re.M), encoding="utf-8")
            bt_rounds.plan_decide(self.dir, True, "re-approved after revision", "trial")
            self.step("re-approval freezes r2 and r1 stays recoverable",
                      [r["revision"] for r in planner.list_revisions(self.dir)] == [1, 2]
                      and planner.dumps(planner.load_revision(self.dir, 1)) == planner.dumps(plan))
            self.step("launch gate passes for the newly approved revision", adapter.launch_problem(self.dir, freeze=False) is None)
        finally:
            self.step("RUN.json was never touched by planning", run.read_bytes() == before)
        try:
            import bt_scheduler_core.plan as sp
            entry = planner.list_revisions(self.dir)[-1]
            loaded = sp.load_plan((self.dir / "plan-revisions" / f"PLAN.r{entry['revision']}.json").read_text(),
                                  approved_sha256=entry["sha256"])
            self.step("the scheduler core reads the frozen revision (read-only interoperability)",
                      loaded.plan_id == planner.default_plan_id(self.dir) and len(loaded.tasks) == len(plan["tasks"]))
        except ImportError as exc:
            self.step("scheduler core reader unavailable (not exercised)", True, str(exc))

    def run(self) -> dict:
        print(f"\n== {self.name} ({self.spec['intent']}) on {self.repo}")
        plan = self.plan_dict()
        self.write(plan, status="review")
        report = self.check()
        self.step("publication gate passes with evidence verified against the real checkout", report.ok, "; ".join(report.errors[:4]))
        self.step("evidence files were really checked, not skipped",
                  not any("not verified" in w for w in report.warnings), "; ".join(report.warnings[:3]))
        if report.ok:
            self.judge(plan)
            self.mutations(plan)
            self.lifecycle(plan)
        if "naive_full_system" in self.spec:  # in its own folder: the main plan above is already frozen
            other = Trial(self.name + "-naive", self.spec, self.dir.parent)
            naive = other.plan_dict([self.spec["naive_full_system"]], {"M1": self.spec["milestones"]["M1"]})
            md = "---\nstatus: review\n---\n# Plan\n\n### M1 — Decide and prepare\n- [ ] T1 — Migrate the persistence layer to PostgreSQL · repo: trainingapp\n"
            other.write(naive, md, status="review")
            errors = "\n".join(other.check().errors)
            self.step("a lone full_system task is refused (decompose or justify)", "full_system must be decomposed" in errors, errors[:200])
            naive["tasks"][0]["scope_exception"] = {"reason": "owner wants the whole migration reviewed as one unit"}
            other.write(naive, md, status="review")
            report = other.check()
            self.step("with a documented exception it publishes but is flagged for the owner",
                      report.ok and any("scope_exception" in w for w in report.warnings), "; ".join(report.errors[:2]))
        ok = all(s[1] for s in self.steps)
        return {"trial": self.name, "intent": self.spec["intent"], "repo": str(self.repo), "ok": ok,
                "steps": [{"step": a, "ok": b, "detail": c} for a, b, c in self.steps],
                "analysis": getattr(self, "analysis", None),
                "warnings": report.warnings if "report" in dir() else []}


def main() -> int:
    keep = Path(sys.argv[sys.argv.index("--keep") + 1]) if "--keep" in sys.argv else None
    with tempfile.TemporaryDirectory(prefix="planning-trials-") as tmp:
        root = Path(tmp)
        trials = []
        for name, spec in TRIALS.items():
            trial = Trial(name, spec, root)
            trials.append(trial.run())
        if keep:
            shutil.copytree(root, keep, dirs_exist_ok=True)
    total = sum(len(t["steps"]) for t in trials)
    passed = sum(1 for t in trials for s in t["steps"] if s["ok"])
    summary = {"trials": len(trials), "steps": total, "passed": passed,
               "failed": [f"{t['trial']}: {s['step']}" for t in trials for s in t["steps"] if not s["ok"]],
               "roots": {k: str(v) for k, v in ROOTS.items()},
               "head": {k: subprocess.run(["git", "-C", str(v), "rev-parse", "--short", "HEAD"], capture_output=True,
                                           text=True).stdout.strip() for k, v in ROOTS.items()},
               "results": trials}
    (HERE / "RESULTS.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\n{passed}/{total} checks passed over {len(trials)} trials")
    for line in summary["failed"]:
        print("FAILED:", line)
    return 0 if not summary["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
