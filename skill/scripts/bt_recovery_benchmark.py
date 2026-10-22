"""Versioned benchmark of the recovery of a run: twelve stops of the real REQ-020 / REQ-029 night, measured (REQ-030 step 6).

Each scenario of `tests/fixtures/recovery-scenarios-v1.json` is a stop the night really had (the evidence strings are the ones
the run produced), the human move it took and how long the run waited for it (from the run's audit trail and decisions log).
`run()` puts the CURRENT code on the same stops with no model and no provider: it classifies the stop
(`bt_healing_classify`), asks the healing for its repair (`bt_scheduler_healing`) with the plan and the answers stubbed, and
reports per scenario whether the class is the expected one, whether the system would act without a person, and the minutes
until it acts (the stop's settle time + one poll) instead of the minutes until a human did.

Totals: `human_interventions` and `minutes_to_recovery` (lower is better) and `classified` (higher is better). The results of
every version are kept in `tests/fixtures/recovery-benchmark-results.json`; `regressions(previous, current)` is what stops a
change from making recovery worse than the version before it.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import bt_healing_classify as taxonomy
import bt_scheduler_healing as healing

FIXTURES = Path(__file__).resolve().parent / "tests" / "fixtures"
SCENARIOS = FIXTURES / "recovery-scenarios-v1.json"
RESULTS = FIXTURES / "recovery-benchmark-results.json"
POLL_SECONDS = 30.0


def load(path: Path = SCENARIOS) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _plan(tasks: list[dict]):
    specs = tuple(SimpleNamespace(id=t["id"], expected_paths=tuple(t.get("expected_paths", ())), after=(),
                                  meta={"kind": t.get("kind", "implement")}) for t in tasks)
    return SimpleNamespace(tasks=specs, task=lambda tid: next(s for s in specs if s.id == tid)) if specs else None


def _attempt(scenario: dict, now: float) -> dict[str, Any]:
    """What the current code does for one recorded stop."""
    request, context, doc = scenario["request"], scenario["context"], scenario["doc"]
    plan = _plan(scenario.get("plan_tasks", []))
    case = taxonomy.classify(request, verify=context.get("verify", ""), failures=context.get("failures", ()), plan=plan, doc=doc)
    if case is None:
        return {"class": None, "auto": False, "repair": "none", "wait": None}
    answers: list[tuple] = []
    plan_json, frozen = scenario.get("plan_json"), []
    import bt_config
    import bt_remediation

    original = (healing._latest_plan, healing._freeze, bt_config.set_value, bt_remediation.grant_round)
    bt_config.set_value = lambda key, value: None                     # the benchmark never writes the machine's settings
    bt_remediation.grant_round = lambda rdir, audit, limit=1: True
    healing._latest_plan = lambda rdir: plan_json
    healing._freeze = lambda rdir, plan_, source: frozen.append(plan_) or plan_
    try:
        outcome = healing._repair("bench", "REQ-0", Path("."), request, case, context, plan, doc,
                                  lambda *args: answers.append(args) or ["ok"], lambda why: ["rebased"])
    finally:
        healing._latest_plan, healing._freeze, bt_config.set_value, bt_remediation.grant_round = original
    auto = outcome["repair"] != "none" and outcome["result"] == "fixed"
    wait = healing.SETTLE.get(case.kind, 0.0) + POLL_SECONDS if auto else None
    return {"class": case.kind, "auto": auto, "repair": outcome["repair"], "wait": wait}


def _files_lost() -> dict[str, Any]:
    """The REQ-020 T14 stop on a real repository: the integrated tree lost two sibling files; the invariant restores them."""
    import bt_integration_invariant as invariant
    from bt_scheduler_integrator import _git

    root = Path(tempfile.mkdtemp(prefix="recovery-bench-"))
    try:
        repo = root / "repo"
        repo.mkdir()
        run = lambda *a, **k: subprocess.run(["git", "-c", "user.name=B", "-c", "user.email=b@b", *a], cwd=repo, check=True,  # noqa: E731
                                              capture_output=True, text=True, **k).stdout.strip()
        run("init", "-q")
        (repo / "README.md").write_text("x\n")
        run("add", ".")
        run("commit", "-qm", "base")
        head = run("rev-parse", "HEAD")

        def snap(parent, files):
            for name, text in files.items():
                (repo / name).parent.mkdir(parents=True, exist_ok=True)
                (repo / name).write_text(text)
            run("add", "-A")
            tree = run("write-tree")
            run("reset", "-q", "--hard", head)
            run("clean", "-fdq")
            return run("commit-tree", tree, "-p", parent, "-m", "snap")

        s12 = snap(head, {"src/directions.ts": "d\n"})
        other = snap(head, {"src/packages.ts": "p\n"})
        s13 = run("commit-tree", run("rev-parse", f"{other}^{{tree}}"), "-p", s12, "-m", "snap")   # on s12, tree without directions.ts
        items = [invariant.Item("T12", head, s12), invariant.Item("T13", s12, s13)]
        report = invariant.check(_git, repo, s13, items)
        fixed = invariant.restore(_git, repo, s13, items, report) if not report.ok else s13
        ok = bool(fixed) and invariant.check(_git, repo, fixed, items).ok
        return {"class": "integration_defect", "auto": ok, "repair": "restored" if ok else "none", "wait": 0.0}
    finally:
        shutil.rmtree(root, ignore_errors=True)


def run(path: Path = SCENARIOS) -> dict[str, Any]:
    data = load(path)
    rows = []
    for scenario in data["scenarios"]:
        got = _files_lost() if scenario.get("kind") == "files_lost" else _attempt(scenario, data["now"])
        night = scenario["night"]
        expect = scenario["expect"]
        minutes_after = got["wait"] / 60 if got["auto"] and got["wait"] is not None else night["minutes"]
        rows.append({"id": scenario["id"], "title": scenario["title"], "class": got["class"], "class_ok": got["class"] == expect["class"],
                     "auto": got["auto"], "auto_ok": got["auto"] == expect["auto"] and (not got["auto"] or got["repair"].startswith(expect["repair"])),
                     "repair": got["repair"], "human_before": night["human"], "human_after": 0 if got["auto"] else 1,
                     "minutes_before": night["minutes"], "minutes_after": round(minutes_after, 2)})
    return {"scenarios": rows, "totals": {
        "human_interventions": sum(r["human_after"] for r in rows),
        "human_interventions_night": sum(r["human_before"] for r in rows),
        "minutes_to_recovery": round(sum(r["minutes_after"] for r in rows), 1),
        "minutes_to_recovery_night": round(sum(r["minutes_before"] for r in rows), 1),
        "classified": sum(1 for r in rows if r["class"] is not None),
        "as_expected": sum(1 for r in rows if r["class_ok"] and r["auto_ok"]), "scenarios": len(rows)}}


def regressions(previous: dict[str, Any], current: dict[str, Any]) -> list[str]:
    """What got worse from `previous` totals to `current` totals (empty = nothing did)."""
    worse = []
    for key in ("human_interventions", "minutes_to_recovery"):
        if current[key] > previous[key]:
            worse.append(f"{key}: {previous[key]} -> {current[key]}")
    for key in ("classified", "as_expected"):
        if current[key] < previous[key]:
            worse.append(f"{key}: {previous[key]} -> {current[key]}")
    return worse


def history(path: Path = RESULTS) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"versions": {}}


if __name__ == "__main__":
    print(json.dumps(run()["totals"], indent=1))
