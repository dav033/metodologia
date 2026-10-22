"""The facts of an integration CONFLICT, read from the run's official records, and the convergence work compiled from them
(REQ-029 R11/R12/R13, P-152).

Two accepted tasks A and B each changed the same paths and a consumer C needs both: the merge that feeds C conflicts. Ordinary
recovery redoes B on top of A with markers (`rework_conflict`); this module is for when that was exhausted. It does NOT guess:

- `gather` derives every fact deterministically: the accepted attempts and their snapshots, the owners the frozen plan gives each
  path, whether A and B are ordered, what each side changed, who consumes both. Anything that does not hold (a side is not the
  accepted one any more, a side changed a path it does not own, the sides are ordered, the clash is not between two tasks) is a
  `Blocked` with its own code: that is not the defect this repair is for, and the ordinary paths or the owner take it.
- the model contributes only the judgement the records cannot give: whether the two requirements are compatible, and the symptom
  oracle that tells the combined behaviour from the broken one. The red step of that oracle is RUN, in the verifier sandbox, on an
  accepted side, and must fail as a test fails (`bt_recovery_oracle`).
- `convergence_work` hands the facts to `bt_recovery_convergence.plan_conflict_convergence`, which is where nothing can be weakened:
  the owners' own frozen checks are copied, both acceptance contracts are kept, one designated writer owns the paths, and both
  accepted snapshots are preserved as its start.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import bt_recovery_convergence as conv
import bt_recovery_diagnosis as dg

DIFF_BYTES = 30 * 1024
ACTIONS = ("converge_owned_paths", "inherit_additive_checks")
MARKER_CHECK = "awk '/^" + "[\\x3c\\x3e]" * 7 + " /{{exit 1}}' {path}"        # exit 1 when the file holds a marker line, 0 when it is clean


def conflict_rows(rdir: Path) -> list[dict]:
    """Every recorded clash, oldest first (`bt_interventions.record_conflict`: all its paths, never clipped)."""
    rows = []
    try:
        for line in (Path(rdir) / "RUN.conflicts.jsonl").read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict) and row.get("task") and row.get("files"):
                rows.append(row)
    except OSError:
        pass
    return rows


def latest_conflict(rdir: Path, task: str) -> dict | None:
    return next((row for row in reversed(conflict_rows(rdir)) if row.get("task") == task), None)


def _git(repo: str, *args: str) -> str:
    done = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, timeout=60, check=False)
    if done.returncode:
        raise dg.Blocked("evidence_unavailable", f"git {args[0]}: {(done.stderr or done.stdout).strip()[:120]}")
    return done.stdout.strip()


def _covers(prefixes: list[str], path: str) -> bool:
    return any(path == p or path.startswith(p.rstrip("/") + "/") for p in prefixes if isinstance(p, str))


def _reaches(tasks: dict[str, dict], start: str, goal: str) -> bool:
    seen, stack = set(), [start]
    while stack:
        current = stack.pop()
        if current == goal:
            return True
        if current in seen or current not in tasks:
            continue
        seen.add(current)
        stack.extend(tasks[current].get("after") or [])
    return False


def gather(rdir: Path, project: str, row: dict) -> dict[str, Any]:
    """Every deterministic fact of the clash in `row`, or `Blocked`."""
    import bt_plan_adapter
    import bt_recovery_export as export
    import bt_scheduler_decisions as decisions

    left, right, consumer = str(row.get("left") or ""), str(row.get("right") or ""), str(row["task"])
    if not re.fullmatch(r"T[0-9]+(?:\.[0-9]+)?[a-z]?", left) or not re.fullmatch(r"T[0-9]+(?:\.[0-9]+)?[a-z]?", right) or left == right:
        raise dg.Blocked("conflict_sides_not_two_tasks", f"{left!r} vs {right!r}: more than two results were already merged")
    files = sorted({str(f) for f in row["files"]})
    doc = decisions._state(rdir)
    revision = doc.get("revision")
    plan = next((bt_plan_adapter.planner_revisions.load_revision(rdir, r["revision"]) for r in bt_plan_adapter.revisions(rdir)
                 if r.get("revision") == revision), None)
    if plan is None:
        raise dg.Blocked("evidence_unavailable", f"the frozen plan r{revision} is not on disk")
    tasks = {t["id"]: t for t in plan["tasks"] if isinstance(t, dict)}
    for name in (left, right, consumer):
        if name not in tasks:
            raise dg.Blocked("lineage_stale", f"{name} is not a task of the plan the run is on (r{revision})")
    accepted: dict[str, str] = {}
    for name, rec in (doc.get("tasks") or {}).items():
        if rec.get("state") == "completed":
            attempt = next((a for a in reversed(rec.get("attempts") or []) if (doc.get("attempts") or {}).get(a, {}).get("state") == "accepted"), None)
            if attempt:
                accepted[name] = attempt
    for name in (left, right):
        if name not in accepted:
            raise dg.Blocked("lineage_stale", f"{name} is not accepted: ordinary redo handles a clash with work that is not current")
    if _reaches(tasks, left, right) or _reaches(tasks, right, left):
        raise dg.Blocked("sides_are_ordered", f"{left} and {right} are ordered by the plan: a clash between them is a stale result, not shared ownership")
    owners = {}
    for name in (left, right):
        paths = tasks[name].get("expected_paths") or []
        outside = [f for f in files if not _covers(paths, f)]
        if outside:
            raise dg.Blocked("scope_escape", f"{name} does not declare {', '.join(outside[:3])}: the owner decides who owns it")
        criteria = [c for c in tasks[name].get("acceptance_criteria") or [] if isinstance(c, str) and c.strip()]
        owners[name] = {"paths": sorted(p for p in paths if isinstance(p, str)), "requirements": criteria}
    sides = []
    for name in (left, right):
        attempt = accepted[name]
        manifest_path = export._manifest_path(rdir, attempt)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        repo, base, snapshot = manifest.get("repository"), manifest.get("base_sha"), manifest.get("snapshot_sha")
        if not (repo and base and snapshot):
            raise dg.Blocked("evidence_unavailable", f"the manifest of {attempt} lacks its base, snapshot or repository")
        delta = [p for p in _git(repo, "diff", "--name-only", "--no-renames", base, snapshot).splitlines() if p]
        sides.append({"role": "accepted", "task_id": name, "attempt_id": attempt, "base_sha": base, "snapshot_sha": snapshot,
                      "tree_sha": _git(repo, "rev-parse", f"{snapshot}^{{tree}}"), "repository": repo, "manifest": manifest,
                      "delta": sorted(delta)})
    if sides[0]["repository"] != sides[1]["repository"]:
        raise dg.Blocked("conflict_across_repositories", "the two results are in different repositories")
    consumers = sorted(name for name, task in tasks.items() if name not in (left, right) and set(task.get("after") or []) & {left, right}
                       and (doc.get("tasks") or {}).get(name, {}).get("state") != "completed")
    if consumer not in consumers:
        raise dg.Blocked("lineage_stale", f"{consumer} no longer waits for {left} and {right}")
    return {"rdir": str(rdir), "project": project, "plan": plan, "revision": revision, "plan_sha256": doc.get("plan_sha256"),
            "tasks": tasks, "accepted": accepted, "consumer": consumer, "left": left, "right": right, "files": files,
            "owners": owners, "sides": sides, "consumers": consumers, "repository": sides[0]["repository"],
            "repository_role": tasks[consumer].get("repository") or "repo"}


def view(facts: dict) -> dict[str, Any]:
    """What the model reads to judge the clash and write the oracle: the two tasks, their requirements and what each changed."""
    def side(index: int) -> dict:
        s, name = facts["sides"][index], facts["sides"][index]["task_id"]
        task = facts["tasks"][name]
        diff = _git(s["repository"], "diff", "--no-color", "--no-renames", s["base_sha"], s["snapshot_sha"], "--", *facts["files"][:20])
        return {"task": name, "title": task.get("title"), "objective": task.get("objective"), "requirements": facts["owners"][name]["requirements"],
                "checks": task.get("verification"), "changed_paths": s["delta"][:200],
                "diff_of_the_clashing_files": diff[:DIFF_BYTES] + ("\n[clipped]" if len(diff) > DIFF_BYTES else "")}
    first = facts["sides"][0]
    names = [n for n in _git(first["repository"], "ls-tree", "-r", "--name-only", first["snapshot_sha"]).splitlines()
             if re.search(r"(^|/)(tests?|spec|__tests__)(/|$)|test_|_test\.|\.test\.|\.spec\.", n)][:60]
    sample = {}
    for name in names[:6]:                                   # what an oracle command can run: the tests that already exist
        body = subprocess.run(["git", "-C", first["repository"], "show", f"{first['snapshot_sha']}:{name}"], capture_output=True, text=True,
                              timeout=30, check=False).stdout
        sample[name] = body[:3000]
    return {"clash": {"consumer": facts["consumer"], "paths": facts["files"]}, "sides": [side(0), side(1)],
            "existing_test_files": names, "test_file_contents": sample,
            "consumer": {"id": facts["consumer"], "title": facts["tasks"][facts["consumer"]].get("title")}}


def _digest(value: object) -> str:
    return conv._digest(value)


def _checks(facts: dict) -> list[dict]:
    out = []
    for name in sorted({facts["left"], facts["right"]}):
        for check in facts["tasks"][name].get("verification") or []:
            if conv._command(check):
                out.append({**copy.deepcopy(check), "owner_task_id": name})
    return out


def red_provenance(facts: dict, oracle: dict, policy) -> dict:
    """Run the oracle's red command on each accepted side; it must fail like a test on at least one of them (the side lacking the
    other's requirement). The provenance names that side's attempt and the digest of its tree."""
    import bt_recovery_oracle as runner

    last = None
    for side in facts["sides"]:
        try:
            outcome = runner.run(side["repository"], side["snapshot_sha"], oracle["red_command"], policy)
        except runner.OracleError as error:
            raise dg.Blocked("oracle_unusable", str(error)[:200]) from error
        last = outcome
        if outcome["status"] == "fail" and outcome["kind"] == "symptom":
            return {"captured_attempt_id": side["attempt_id"], "failure_kind": "symptom",
                    "source_digest": hashlib.sha256(side["tree_sha"].encode()).hexdigest(),
                    "command_digest": _digest(oracle["red_command"]), "exit_code": outcome["exit_code"]}
    raise dg.Blocked("oracle_not_red", f"the red command did not fail on either accepted side ({(last or {}).get('status')}, "
                     f"exit {(last or {}).get('exit_code')}): it proves nothing about the clash")


def convergence_work(facts: dict, oracle: dict, semantic: dict, policy) -> dict[str, Any]:
    """`convergence-work/1` for this clash, validated by `plan_conflict_convergence`."""
    provenance = red_provenance(facts, oracle, policy)
    plan = {**facts["plan"], "sha256": facts["plan_sha256"]}
    left, right, consumer = facts["left"], facts["right"], facts["consumer"]
    accepted_map = dict(sorted(facts["accepted"].items()))
    manifests = {s["task_id"]: s["manifest"] for s in facts["sides"]}
    base_side = facts["sides"][0]
    merge_base = _git(facts["repository"], "merge-base", facts["sides"][0]["snapshot_sha"], facts["sides"][1]["snapshot_sha"])
    evidence = sorted({_digest(accepted_map), *(_digest(m) for m in manifests.values()), _digest({"plan": facts["plan_sha256"]}),
                       _digest({"clash": facts["files"], "consumer": consumer, "left": left, "right": right})})
    sides = [{"ordinal": i, "role": "accepted", "task_id": s["task_id"], "attempt_id": s["attempt_id"],
              "base_digest": hashlib.sha256(s["base_sha"].encode()).hexdigest(),
              "snapshot_digest": hashlib.sha256(s["snapshot_sha"].encode()).hexdigest(),
              "tree_digest": hashlib.sha256(s["tree_sha"].encode()).hexdigest()} for i, s in enumerate(facts["sides"])]
    run_id, plan_id, revision = f"{facts['project']}:{Path(facts['rdir']).name}", facts["plan"]["plan_id"], facts["revision"]
    start_attempt = f"{consumer}-start"
    observation = {"schema_version": "conflict-observation/1", "source_type": "start", "run_id": run_id, "plan_id": plan_id,
                   "revision": revision, "plan_sha256": facts["plan_sha256"], "task_id": consumer, "attempt_id": start_attempt,
                   "token": "start", "consumer_id": consumer, "repository_id": facts["repository_role"], "paths": facts["files"],
                   "sides": sides, "original_merge_base": hashlib.sha256(merge_base.encode()).hexdigest(), "carry_ancestry": [],
                   "evidence_digests": evidence, "ordinary_rework_refusal": "overlap_requires_structural_recovery",
                   "ordinary_rework_refusal_detail": f"{left} and {right} both own {', '.join(facts['files'][:4])}: redoing one on "
                                                     f"the other did not settle it"}
    incompatible = [str(x).strip() for x in semantic.get("incompatible_requirements") or [] if str(x).strip()]
    lineage = {"schema_version": "conflict-lineage-facts/1", "status": "current", "evidence_complete": True,
               "semantic_conflict": bool(semantic.get("semantic_conflict")) and bool(incompatible),
               "incompatible_requirements": incompatible if semantic.get("semantic_conflict") else [],
               "ownership_or_order_defect": True, "demonstrated_future_defect": False, "aliases": []}
    plan_facts = {"schema_version": "conflict-plan-facts/1", "source_type": "start", "run_id": run_id, "plan_id": plan_id,
                  "revision": revision, "plan_sha256": facts["plan_sha256"], "task_id": consumer, "attempt_id": start_attempt,
                  "token": "start", "consumer_id": consumer, "repository_id": facts["repository_role"],
                  "approved_start_paths": facts["files"], "approved_integration_paths": facts["files"],
                  "authority_status": "authorized"}
    edges = [{"consumer_id": name, "source_task_id": side} for name in facts["consumers"] for side in (left, right)
             if side in (facts["tasks"][name].get("after") or [])]
    receipt = {"schema_version": "conflict-lineage-receipt/1", "source_digests": evidence, "affected_consumers": facts["consumers"],
               "obsolete_edges": edges}
    receipt["sha256"] = _digest({k: v for k, v in receipt.items() if k != "sha256"})
    numbers = [int(m.group(1)) for t in facts["tasks"] if (m := re.fullmatch(r"T([0-9]+)", t))]
    new_id = f"T{max(numbers, default=0) + 1}"
    checks = _checks(facts)
    strategy = conv.ConflictStrategy(source_digests=tuple(evidence), accepted_map_digest=_digest(accepted_map),
                                path_digests=tuple(sorted({_digest(p) for p in facts["files"]})),
                                check_digests=tuple(sorted({_digest(c) for c in checks})), actions=ACTIONS,
                                action_edges=((ACTIONS[0], ACTIONS[1]),)).to_dict()
    # `owners` lists the CONCRETE files each side owns (declared prefixes applied to what it changed and to the clashing files):
    # a delta file outside its declared scope is then not owned, and the convergence refuses it
    owned = {}
    for side in facts["sides"]:
        declared = facts["owners"][side["task_id"]]
        owned[side["task_id"]] = {"paths": sorted({f for f in [*facts["files"], *side["delta"]] if _covers(declared["paths"], f)}),
                                  "requirements": declared["requirements"]}
    envelope = {"observation": observation, "plan_facts": plan_facts, "lineage_facts": lineage, "owners": owned,
                "current_base": {facts["repository_role"]: {"task_id": left, "accepted_attempt_id": base_side["attempt_id"],
                                                             "snapshot_sha": base_side["snapshot_sha"],
                                                             "accepted_map_digest": _digest(accepted_map),
                                                             "m3_manifest": base_side["manifest"]}},
                "accepted_map": accepted_map,
                "sources": [{k: s[k] for k in ("role", "task_id", "attempt_id", "base_sha", "snapshot_sha", "tree_sha")}
                            for s in facts["sides"]],
                "delta_paths": {s["attempt_id"]: s["delta"] for s in facts["sides"]},
                "symptom_oracle": {"path": oracle["path"], "command": oracle["command"], "red_command": oracle["red_command"],
                                   "red_on_conflict": True, "green_on_result": True, "owner_task_id": left,
                                   "red_provenance": provenance},
                "marker_check": {"type": "command", "value": MARKER_CHECK.format(path=facts["files"][0]),
                                 "created_by": new_id, "purpose": "No unresolved conflict markers"},
                "convergence_task_id": new_id, "nonconflicting_predecessor_closure": _closure(facts),
                "marker_paths": facts["files"], "affected_consumers": facts["consumers"], "lineage_receipt": receipt}
    try:
        work = conv.plan_conflict_convergence(plan, envelope, strategy)
    except conv.ConvergenceError as error:
        raise dg.Blocked("convergence_refused", str(error)[:240]) from error
    task = work["convergence_task"]
    # `git diff --check` cannot run in the verifier (no .git) and its category is not one the planner knows: the per-file marker check
    # below is the integrity check that can
    task["verification"] = [c for c in task["verification"] if c.get("value") != "git diff --check"]
    for path in facts["files"][1:]:                        # one marker check per conflicted file (the grep lists a file only when clean)
        task["verification"].append({"type": "command", "value": MARKER_CHECK.format(path=path), "created_by": task["id"],
                                     "purpose": "No unresolved conflict markers", "category": "integration"})
    owner = facts["tasks"][left]                           # the planner never defaults a classification: the writer inherits its owner's
    for key in ("complexity", "scope", "estimated_minutes", "risk", "confidence", "shared_resources"):
        task.setdefault(key, copy.deepcopy(owner.get(key)))
    task.setdefault("estimate_rationale", f"Converges {left} and {right} over {', '.join(facts['files'][:3])}: {owner.get('estimate_rationale', '')}"[:400])
    evidence = copy.deepcopy(owner.get("classification_evidence") or {})
    evidence["coupling"] = {"justification": f"It combines the accepted results of {left} and {right}, which both own these paths.",
                            "evidence": ["spec:SPEC.md", f"task:{left}", f"task:{right}"]}
    task.setdefault("classification_evidence", evidence)
    task["coupling"] = "high"
    task["objective"] += (f" The working tree starts as a merge in progress: {left}'s accepted result with {right}'s accepted work "
                          f"merged over it, and {', '.join(facts['files'][:6])} hold git conflict markers. Resolve them so both "
                          f"requirements hold, keep every other file as it is, and leave no marker.")
    return work


def _closure(facts: dict) -> list[str]:
    """The minimum frozen closure of the consumers' OTHER prerequisites (what `plan_conflict_convergence` demands to the letter)."""
    affected = {facts["left"], facts["right"]}
    found: set[str] = set()
    pending = [d for name in facts["consumers"] for d in facts["tasks"][name].get("after") or [] if d not in affected]
    while pending:
        name = pending.pop()
        if name in found:
            continue
        if name in affected or name not in facts["tasks"]:
            raise dg.Blocked("lineage_stale", f"{name} is both a prerequisite of the consumers and tied to one of the sides")
        found.add(name)
        pending.extend(facts["tasks"][name].get("after") or [])
    return sorted(found)


def synthesized_proposal(facts: dict, oracle: dict, refs: list[str]) -> dict[str, Any]:
    """The `recovery-proposal/1` the compiler wants beside the convergence work: it names both owners (no change to their text) and
    carries the oracle. The actions are not the model's: the convergence itself is."""
    return {"schema_version": "recovery-proposal/1", "confidence": "confirmed", "evidence_refs": refs,
            "actions": [{"type": "repair_verification", "owner_task_id": name, "task_ids": [name], "verification": []}
                        for name in (facts["left"], facts["right"])],
            "symptom_oracle": {"symptom": oracle["symptom"], "red_command": oracle["red_command"], "command": oracle["command"]}}
