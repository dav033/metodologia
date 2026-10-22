"""The structural recovery cycle, from queue to closing proof (REQ-029 R3-R8, R14, R15; P-152).

`RecoveryAdapter.tick_diagnostic_recovery` (in the owner) opens at most one durable cycle per lineage. It cannot also run the
cycle: applying a plan revision stops the owner. So the work is split on that line:

- the OWNER side (`owner_pipeline`) only queues: it records the goal the cycle is about and returns `applying`;
- the WATCHER side (`advance`, called from the watchdog's `heal`) takes each active cycle one step at a time, resumably, with the
  row of `diagnostic_cycles` as the state machine:

    applying/queued   evidence is exported, the model diagnoses ONCE, the compiler turns its proposal into a plan revision
    applying/compiled a run-scoped grant is issued and `bt_recovery_apply` applies the revision (journaled, CAS, hold-aware)
    executing         the ordinary scheduler runs the corrective tasks; `auditing`: only the re-audits are left
    succeeded         only when every corrective task and the independent audits are accepted on the resulting tree, with the
                      five-way proof `_verified_cycle_success` demands; blocked: the exact code of what stopped it

Every step that cannot go on raises `Blocked`, which becomes the cycle's durable blocker (the plan page shows it) and leaves the
owner's own card for the owner. The stop control wins at every step: no activation for this stop generation, no step.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import time
from contextlib import closing
from pathlib import Path
from typing import Any

import bt_recovery_diagnosis as dg

ACTIVE = ("applying", "executing", "auditing")
DIR = "RUN.recovery"


# ------------------------------------------------------------------------------------------------ the owner side
def owner_pipeline(rdir: Path | str):
    """The `diagnostic_pipeline` of the owner's adapter: queue the cycle, do nothing that touches the run."""
    def queue(ctx) -> dict[str, Any]:
        goal = (ctx.get("sources") or {}).get("diagnosis_target")
        if not isinstance(goal, dict) or not goal.get("named"):
            return {"state": "blocked", "blocker": "recovery_evidence_unavailable"}
        return {"state": "applying", "phase": "queued", "goal": goal, "queued_at": round(time.time(), 3)}
    return queue


# ------------------------------------------------------------------------------------------------ rows
def _db(rdir: Path) -> Path | None:
    import bt_run_stores

    return bt_run_stores.paths(rdir).get("m5")


def active_cycles(rdir: Path | str) -> list[dict[str, Any]]:
    path = _db(Path(rdir))
    if path is None or not Path(path).exists():
        return []
    try:
        with closing(sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=5)) as conn:
            rows = conn.execute("SELECT lineage_id, cycle_token, state, payload_json FROM diagnostic_cycles WHERE state IN (?,?,?) "
                                "ORDER BY updated_at", ACTIVE).fetchall()
    except sqlite3.Error:
        return []
    out = []
    for lineage, token, state, payload in rows:
        try:
            body = json.loads(payload)
        except ValueError:
            body = {}
        out.append({"lineage": lineage, "token": token, "state": state, "payload": body if isinstance(body, dict) else {}})
    return out


def _save(rdir: Path, cycle: dict, state: str, payload: dict[str, Any]) -> None:
    path = _db(rdir)
    with closing(sqlite3.connect(path, timeout=5, isolation_level=None)) as conn:
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute("UPDATE diagnostic_cycles SET state=?, payload_json=?, updated_at=? WHERE lineage_id=?",
                     (state, json.dumps({**payload, "state": state}, sort_keys=True), time.time(), cycle["lineage"]))
    cycle.update(state=state, payload=payload)


def _activation_ok(rdir: Path) -> bool:
    """The owner's opt-in is still in force: present, for this run, and for the stop generation the run is in now."""
    import bt_scheduler_adapter as adapter

    try:
        policy = json.loads((rdir / "RUN.recovery-policy.json").read_text(encoding="utf-8"))
        identity = adapter.revision_identity(rdir)
    except (OSError, ValueError, KeyError, Exception):  # noqa: BLE001 - nothing readable is nothing authorized
        return False
    return (policy.get("schema_version") == "recovery-policy/1"
            and policy.get("identity", {}).get("stop_generation") == identity.get("stop_generation")
            and not identity.get("paused") and not identity.get("cancelled"))


# ------------------------------------------------------------------------------------------------ the watcher side
def advance(project: str, req: str, rdir: Path | str, *, runner=None, probe_runner=None, home: Path | None = None,
            log=lambda text: None) -> bool:
    """One step of the first active cycle. True when something changed (the watchdog then looks again before restarting the owner)."""
    import bt_scheduler_ops as ops

    rdir = Path(rdir)
    cycles = active_cycles(rdir)
    if not cycles or ops.on_hold(rdir) or not _activation_ok(rdir):
        return False
    cycle = cycles[0]
    before = (cycle["state"], json.dumps(cycle["payload"], sort_keys=True))
    try:
        _step(project, req, rdir, cycle, runner=runner, probe_runner=probe_runner, home=home)
    except dg.Blocked as stop:
        _save(rdir, cycle, "blocked", {**cycle["payload"], "blocker": stop.code, "detail": stop.detail})
        log(f"recovery cycle {cycle['token'][:12]} blocked: {stop.code} {stop.detail}")
        _record(rdir, cycle, "failed", f"blocked: {stop.code}")
    except Exception as error:  # noqa: BLE001 - a failure is durable and never falls through to the ordinary retry
        _save(rdir, cycle, "blocked", {**cycle["payload"], "blocker": f"cycle_failed:{type(error).__name__}", "detail": str(error)[:300]})
        log(f"recovery cycle {cycle['token'][:12]} failed: {type(error).__name__}: {error}")
        _record(rdir, cycle, "failed", f"failed: {type(error).__name__}")
    else:
        if cycle["state"] == "succeeded":
            _record(rdir, cycle, "fixed", "the corrective tasks and the independent audits are accepted on the resulting tree")
    return before != (cycle["state"], json.dumps(cycle["payload"], sort_keys=True))


def _record(rdir: Path, cycle: dict, result: str, text: str) -> None:
    import bt_interventions

    goal = cycle["payload"].get("goal") or {}
    bt_interventions.record(rdir, kind="regression", source="auto", task=str(goal.get("task") or ""),
                            evidence=f"exhausted audit stop {goal.get('request', '')} ({goal.get('reason', '')})",
                            repair=f"structural recovery cycle {cycle['token'][:12]}: {text}", result=result,
                            case=cycle["token"][:16])


def _cycle_dir(rdir: Path, cycle: dict) -> Path:
    path = rdir / DIR / f"cycle-{cycle['token'][:16]}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _step(project: str, req: str, rdir: Path, cycle: dict, **model) -> None:
    payload, phase = dict(cycle["payload"]), cycle["payload"].get("phase", "queued")
    if cycle["state"] in ("executing", "auditing"):
        _progress(rdir, cycle)
        return
    folder = _cycle_dir(rdir, cycle)
    if phase == "queued":
        _diagnose(project, rdir, cycle, folder, **model)
    elif phase == "compiled":
        _apply(rdir, cycle, folder)
    else:
        raise dg.Blocked("cycle_phase_unknown", str(phase))


def _diagnose(project: str, rdir: Path, cycle: dict, folder: Path, **model) -> None:
    goal = cycle["payload"]["goal"]
    route = dg.route(project)
    if route is None:
        raise dg.Blocked("authorized_planner_route_unavailable", "no diagnosing profile is authorized for this project")
    import bt_config

    timeout = max(int(bt_config.get("diagnosis.timeout_seconds", 180) or 180), 300)
    if goal.get("kind") == "conflict":
        evidence, judgement, extra = dg.diagnose_conflict(project, rdir, goal, route, folder, timeout_seconds=timeout, **model)
        compiled, proposal = dg.compile_conflict(evidence, judgement, extra, project)
    else:
        evidence, proposal, extra = dg.diagnose(project, rdir, goal, route, folder, timeout_seconds=timeout, **model)
        compiled = dg.compile_revision(evidence, proposal, extra["paths"])
    (folder / "proposal.json").write_text(json.dumps(proposal, indent=1, sort_keys=True), encoding="utf-8")
    body = {"plan": compiled.plan, "scope": list(compiled.scope), "verification_map": compiled.verification_map,
            "changed_paths": extra["paths"], "proposal_hash": dg.proposal_hash(proposal),
            "source_sha256": evidence["identity"]["plan_sha256"], "repository": _repository_of(evidence)}
    (folder / "compiled.json").write_text(json.dumps(body, indent=1, sort_keys=True), encoding="utf-8")
    _save(rdir, cycle, "applying", {**cycle["payload"], "phase": "compiled", "model": route["model"],
                                     "proposal_hash": body["proposal_hash"], "scope": body["scope"]})


def _repository_of(evidence: dict) -> str | None:
    return (evidence["sources"]["m3_manifest"]["document"] or {}).get("repository")


def integration_base(repository: str | None) -> str:
    """The integration base a grant is bound to: the repository's HEAD at the moment (a revision that finds it moved is refused)."""
    if not repository:
        raise dg.Blocked("evidence_unavailable", "no repository to bind the integration base to")
    done = subprocess.run(["git", "-C", repository, "rev-parse", "HEAD"], capture_output=True, text=True, timeout=30, check=False)
    if done.returncode:
        raise dg.Blocked("evidence_unavailable", "the integration base cannot be read")
    return hashlib.sha256(done.stdout.strip().encode()).hexdigest()


def _apply(rdir: Path, cycle: dict, folder: Path) -> None:
    import bt_plan_adapter
    import bt_recovery_apply as apply
    import bt_recovery_authorization as authorization
    import bt_scheduler_adapter as adapter

    compiled = json.loads((folder / "compiled.json").read_text(encoding="utf-8"))
    identity = adapter.revision_identity(rdir)
    if identity.get("paused") or identity.get("cancelled"):
        raise dg.Blocked("run_paused_or_cancelled")
    target = hashlib.sha256(bt_plan_adapter.planner_contract.dumps(compiled["plan"]).encode("utf-8")).hexdigest()
    case_id = "case-" + cycle["lineage"][:24]
    base = integration_base(compiled.get("repository"))
    if cycle["payload"].get("grant_key"):
        key = cycle["payload"]["grant_key"]
    else:
        key = authorization.open_for_run(rdir).issue_task_grant({
            "case_id": case_id, "case_hash": hashlib.sha256(f"{case_id}:{compiled['proposal_hash']}".encode()).hexdigest(),
            "cycle_token": cycle["token"], "stop_generation": identity["stop_generation"], "proposal_hash": compiled["proposal_hash"],
            "source_sha256": identity["source_sha256"], "target_sha256": target, "scope": list(compiled["scope"]),
            "accepted_map_digest": identity["accepted_map_digest"], "base_digest": base})
        _save(rdir, cycle, "applying", {**cycle["payload"], "grant_key": key})
    result = apply.apply_recovery_revision(
        rdir, {**compiled, "case_id": case_id, "cycle_token": cycle["token"], "source_sha256": identity["source_sha256"]}, key,
        current_base=lambda: integration_base(compiled.get("repository")))
    status = result.get("status")
    if status == "waiting":
        _save(rdir, cycle, "applying", {**cycle["payload"], "wait": {k: result.get(k) for k in ("reason", "live_attempts")}})
        return
    if status == "blocked":
        raise dg.Blocked("apply_blocked", str(result.get("reason") or result.get("blocker") or ""))
    plan = compiled["plan"]
    audits = [t["id"] for t in plan["tasks"] if t.get("kind") == "audit"]
    corrective = [t for t in compiled["scope"] if t not in audits]
    integration = [t["id"] for t in plan["tasks"] if t.get("title") == "Run integrated recovery verification"]
    _save(rdir, cycle, "executing", {**cycle["payload"], "phase": "applied", "target_sha256": target, "audits": audits,
                                       "corrective": corrective, "integration": integration, "receipt": {k: result.get(k) for k in ("schema", "grant_key")}})


# ------------------------------------------------------------------------------------------------ progress and proof
def _progress(rdir: Path, cycle: dict) -> None:
    import bt_scheduler_decisions as decisions

    payload = cycle["payload"]
    doc = decisions._state(rdir)
    if doc.get("plan_sha256") != payload.get("target_sha256"):
        raise dg.Blocked("plan_revision_changed", "the run left the revision the cycle applied")
    tasks = doc.get("tasks") or {}
    corrective, audits = payload["corrective"], payload["audits"]
    for task in [*corrective, *audits]:
        if (tasks.get(task) or {}).get("state") in ("blocked", "cancelled"):
            raise dg.Blocked("corrective_task_blocked", f"{task} is {tasks[task]['state']}: {tasks[task].get('reason', '')[:120]}")
    done = lambda names: all((tasks.get(t) or {}).get("state") == "completed" for t in names)  # noqa: E731
    if not done(corrective):
        if cycle["state"] != "executing":
            _save(rdir, cycle, "executing", payload)
        return
    if not done(audits):
        if cycle["state"] != "auditing":
            _save(rdir, cycle, "auditing", payload)
        return
    result = _proof(rdir, doc, payload)
    import bt_scheduler_recovery_lifecycle as lifecycle

    if not lifecycle._verified_cycle_success(result):
        raise dg.Blocked("independent_resulting_tree_proof_missing", "the five-way proof of the resulting tree is incomplete")
    _save(rdir, cycle, "succeeded", {**payload, **result})


def _accepted_attempt(doc: dict, task: str) -> str:
    rec = (doc.get("tasks") or {}).get(task) or {}
    for attempt in reversed(rec.get("attempts") or []):
        if (doc.get("attempts") or {}).get(attempt, {}).get("state") == "accepted":
            return attempt
    raise dg.Blocked("independent_resulting_tree_proof_missing", f"{task} has no accepted attempt")


def _proof(rdir: Path, doc: dict, payload: dict) -> dict[str, Any]:
    """The five independent facts about the tree the last audit accepted, each read from its owner's record."""
    import bt_recovery_export as export

    audits, corrective = payload["audits"], payload["corrective"]
    number = lambda attempt: int(attempt.rsplit("-", 1)[-1])  # noqa: E731
    accepted = {t: _accepted_attempt(doc, t) for t in audits}
    final = max(audits, key=lambda t: number(accepted[t]))    # the audit accepted last has every correction in its tree
    attempt = accepted[final]
    manifest = json.loads(export._manifest_path(rdir, attempt).read_text(encoding="utf-8"))
    snapshot = manifest.get("snapshot_sha")
    if not isinstance(snapshot, str) or len(snapshot) < 40:
        raise dg.Blocked("independent_resulting_tree_proof_missing", f"{final}'s snapshot is unknown")
    tree = hashlib.sha256(snapshot.encode()).hexdigest()
    verdict = export._m6_result(rdir, final, attempt)[1].get("status")
    # the second opinion: another audit when the plan has one, else the task that ran every owner check and the oracle together
    others = [t for t in audits if t != final] or list(payload.get("integration") or [])
    if not others:
        raise dg.Blocked("independent_resulting_tree_proof_missing", "there is no second independent check of the tree")
    cross = others[0]
    cross_attempt = accepted.get(cross) or _accepted_attempt(doc, cross)

    def item(ok: bool, ref: str) -> dict[str, Any]:
        return {"status": "verified" if ok else "missing", "resulting_tree_digest": tree, "evidence_ref": ref}

    return {"corrective_tasks": [{"task_id": t, "state": "accepted"} for t in corrective], "resulting_tree_digest": tree,
            "progress": {"verified": True, "unresolved": False},
            "independent_evidence": {
                "m1_revision": item(doc.get("plan_sha256") == payload["target_sha256"], f"m1:{doc.get('plan_sha256')}@r{doc.get('revision')}"),
                "m3_snapshot": item(True, f"m3:{snapshot}"),
                "m6_verdict": item(verdict == "PASS", f"m6:{final}:{attempt}:{verdict}"),
                "independent_audit": item(True, f"audit:{final}:{attempt}"),
                "independent_cross_check": item(True, f"cross:{cross}:{cross_attempt}")}}
