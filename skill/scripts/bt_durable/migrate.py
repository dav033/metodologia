"""Bridge from legacy Scheduler runs to the durable runtime (REQ-030 M8).

Nothing here writes to a legacy store or to a DBOS table: the legacy run is read (SQLite read-only), its progress is
re-proved from evidence, and the durable run starts with that proof as INPUT (`inherited`) — no fabricated
checkpoints. A task is inherited only when its accepted attempt has an M6 PASS result for the same task, the snapshot
commit still exists, and the task's specification did not change since that verdict. Anything less is reconciled
(the snapshot is re-verified before it counts) or redone.

Ownership: `RUN.owner.json` in the requirement folder names the one backend that may mutate the run. Migration
refuses while a legacy owner process or a live legacy attempt exists, and applying it twice is a no-op.
"""
from __future__ import annotations

import glob
import hashlib
import json
import shutil
import sqlite3
import subprocess
import time
from pathlib import Path
from typing import Literal

import bt_run_owner
from bt_contracts.execution import (
    Backend,
    LegacyProgress,
    LegacyTask,
    OwnerRecord,
    RunRef,
)
from pydantic import BaseModel, ConfigDict, Field

LIVE_ATTEMPTS = frozenset({"reserved", "dispatched", "running", "verifying", "uncertain"})
SCHEMA = "bt-durable.migration/1"


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class TaskInventory(_Model):
    task_id: str
    legacy_state: str
    verdict: Literal["inherit", "reconcile", "redo"]
    reason: str
    attempt: str | None = None
    evidence: str | None = None
    snapshot_sha: str | None = None
    base_sha: str | None = None
    manifest_path: str | None = None
    diagnosis: str = ""


class Inventory(_Model):
    schema_version: str = SCHEMA
    project: str
    req: str
    plan_id: str
    revision: int
    plan_sha256: str
    plan_path: str
    owner_pids: list[int] = Field(default_factory=list)
    live_attempts: list[str] = Field(default_factory=list)
    tasks: list[TaskInventory]
    digest: str = ""

    @property
    def blockers(self) -> list[str]:
        out = []
        if self.owner_pids:
            out.append(f"a legacy owner is running (pid {', '.join(map(str, self.owner_pids))}): stop it with a hold first")
        if self.live_attempts:
            out.append(f"legacy attempts are still live: {', '.join(self.live_attempts)}")
        return out


def _ro(db: Path) -> dict:
    conn = sqlite3.connect(f"{db.resolve().as_uri()}?mode=ro", uri=True, timeout=5)
    try:
        return json.loads(conn.execute("SELECT doc FROM state WHERE id = 1").fetchone()[0])
    finally:
        conn.close()


def _m6_result(state_dir: Path, project: str, req: str, evidence: str) -> dict | None:
    if not evidence or not evidence.startswith("m6://result/"):
        return None
    digest = evidence.removeprefix("m6://result/")
    for path in sorted(glob.glob(str(state_dir / "scheduler" / f"{project}-{req}-*-modules" / "m6-quality.sqlite3"))):
        conn = sqlite3.connect(f"{Path(path).resolve().as_uri()}?mode=ro", uri=True, timeout=5)
        try:
            row = conn.execute("SELECT content FROM artifacts WHERE digest = ?", (digest,)).fetchone()
        finally:
            conn.close()
        if row:
            data = bytes(row[0])
            if hashlib.sha256(data).hexdigest() != digest:
                return None                                   # tampered or corrupt evidence never counts
            return json.loads(data)
    return None


def passed(evidence: dict) -> bool:
    """PASS from an M6 verify result (`status`) or an evidence manifest (no status field: every criterion and every
    check must say pass, and the manifest's reason code must be PASS). Anything less is not inherited."""
    if "status" in evidence:
        return evidence.get("status") == "PASS"
    criteria = evidence.get("criteria") or []
    checks = evidence.get("checks") or []
    return (evidence.get("reason_code") == "PASS" and bool(criteria) and all(c.get("status") == "pass" for c in criteria)
            and all(c.get("status") == "pass" for c in checks))


def _manifest(state_dir: Path, project: str, req: str, attempt: str) -> Path | None:
    hits = sorted(glob.glob(str(state_dir / "executor" / f"{project}-{req}-r*" / "attempts" / f"{attempt}-*"
                                / "handoff" / "manifest.json")))
    return Path(hits[-1]) if hits else None


def _last_snapshot(state_dir: Path, project: str, req: str, attempts: list[str]):
    """(attempt, manifest, snapshot, base) of the newest attempt whose captured snapshot still exists, or None."""
    for attempt in reversed(attempts):
        manifest = _manifest(state_dir, project, req, attempt)
        if manifest is None:
            continue
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        snapshot, base = data.get("snapshot_sha"), data.get("base_sha")
        if data.get("status") == "captured" and snapshot and base and snapshot != base \
                and _commit_exists(data.get("repository", ""), snapshot):
            return attempt, manifest, snapshot, base
    return None


def _commit_exists(repo: str, sha: str) -> bool:
    if not repo or not sha:
        return False
    done = subprocess.run(["git", "cat-file", "-e", f"{sha}^{{commit}}"], cwd=repo, capture_output=True, check=False)
    return done.returncode == 0


def _task_fingerprint(plan_doc: dict, task_id: str) -> str:
    task = next((t for t in plan_doc.get("tasks", ()) if t.get("id") == task_id), None)
    if task is None:
        return ""
    keep = {k: task.get(k) for k in ("objective", "acceptance_criteria", "verification", "expected_paths", "after",
                                     "repository")}
    return hashlib.sha256(json.dumps(keep, sort_keys=True).encode()).hexdigest()


def inventory(*, state_dir: Path, rdir: Path, project: str, req: str, owner_pids: list[int] | None = None) -> Inventory:
    doc = _ro(state_dir / "scheduler" / f"{project}-{req}.db")
    revision = int(doc["revision"])
    plan_path = rdir / "plan-revisions" / f"PLAN.r{revision}.json"
    plan_bytes = plan_path.read_bytes()
    if hashlib.sha256(plan_bytes).hexdigest() != doc["plan_sha256"]:
        raise RuntimeError(f"PLAN_CHANGED: {plan_path.name} does not match the run's approved hash")
    plan_doc = json.loads(plan_bytes)
    live = sorted(a for a, rec in doc.get("attempts", {}).items() if rec.get("state") in LIVE_ATTEMPTS)
    tasks: list[TaskInventory] = []
    for task_id, rec in sorted(doc.get("tasks", {}).items()):
        state = rec.get("state", "pending")
        accepted = next((a for a in reversed(rec.get("attempts", []))
                         if doc["attempts"].get(a, {}).get("state") == "accepted"), None)
        diagnosis = str(rec.get("reason") or "")[:500]
        if state != "completed" or accepted is None:
            continued = _last_snapshot(state_dir, project, req, rec.get("attempts", []))
            if continued is not None:                    # keep the partial work: verify it, then continue from it
                attempt, manifest, snapshot, base = continued
                tasks.append(TaskInventory(task_id=task_id, legacy_state=state, verdict="reconcile", attempt=attempt,
                                           snapshot_sha=snapshot, base_sha=base, manifest_path=str(manifest),
                                           diagnosis=diagnosis,
                                           reason=f"not completed: continue from the last legacy snapshot ({attempt})"))
                continue
            tasks.append(TaskInventory(task_id=task_id, legacy_state=state, verdict="redo", diagnosis=diagnosis,
                                       reason="not completed under the legacy runtime" if state != "completed"
                                       else "completed without an accepted attempt"))
            continue
        evidence = doc["attempts"][accepted].get("evidence") or ""
        result = _m6_result(state_dir, project, req, evidence)
        manifest = _manifest(state_dir, project, req, accepted)
        repo = json.loads(manifest.read_text()).get("repository", "") if manifest else ""
        snapshot = (result or {}).get("input", {}).get("snapshot_sha")
        base = (result or {}).get("input", {}).get("base_sha")
        common = {"task_id": task_id, "legacy_state": state, "attempt": accepted, "evidence": evidence or None,
                  "snapshot_sha": snapshot, "base_sha": base, "manifest_path": str(manifest) if manifest else None}
        if result is None:
            tasks.append(TaskInventory(**common, verdict="redo", reason="the M6 evidence is missing or fails its hash"))
            continue
        verified_rev = int(result.get("request", {}).get("revision") or 0)
        same_task = result.get("request", {}).get("task_id") == task_id
        spec_same = verified_rev == revision or (
            (rdir / "plan-revisions" / f"PLAN.r{verified_rev}.json").is_file() and _task_fingerprint(
                json.loads((rdir / "plan-revisions" / f"PLAN.r{verified_rev}.json").read_text()), task_id)
            == _task_fingerprint(plan_doc, task_id))
        if passed(result) and same_task and spec_same and _commit_exists(repo, snapshot or ""):
            tasks.append(TaskInventory(**common, verdict="inherit", reason=f"M6 PASS r{verified_rev}, snapshot present"))
        elif snapshot and _commit_exists(repo, snapshot) and manifest is not None:
            tasks.append(TaskInventory(**common, verdict="reconcile",
                                       reason="evidence is not a PASS for this exact task specification: re-verify"))
        else:
            tasks.append(TaskInventory(**common, verdict="redo", reason="the snapshot commit is gone"))
    inv = Inventory(project=project, req=req, plan_id=doc["plan_id"], revision=revision,
                    plan_sha256=doc["plan_sha256"], plan_path=str(plan_path), owner_pids=list(owner_pids or []),
                    live_attempts=live, tasks=tasks)
    body = inv.model_dump(mode="json", exclude={"digest", "owner_pids"})
    return inv.model_copy(update={"digest": hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()})


def run_ref(inv: Inventory) -> RunRef:
    return RunRef(project=inv.project, req=inv.req, plan_id=inv.plan_id, revision=inv.revision,
                  plan_sha256=inv.plan_sha256, plan_path=Path(inv.plan_path))


def legacy_progress(inv: Inventory) -> LegacyProgress:
    """What the durable run starts from: inherited and reconcilable tasks with their legacy snapshot material."""
    out = []
    for t in inv.tasks:
        if t.verdict not in ("inherit", "reconcile") or not (t.snapshot_sha and t.base_sha and t.manifest_path):
            continue
        manifest = json.loads(Path(t.manifest_path).read_text(encoding="utf-8"))
        worktree = manifest.get("worktree")
        out.append(LegacyTask(task_id=t.task_id, verdict=t.verdict, snapshot_sha=t.snapshot_sha, base_sha=t.base_sha,
                              repository=Path(manifest["repository"]), attempt_dir=Path(t.manifest_path).parent.parent,
                              manifest_path=Path(t.manifest_path),
                              worktree=Path(worktree) if worktree and Path(worktree).is_dir() else None,
                              provenance=f"legacy {t.attempt} {t.evidence or ''}"[:500]))
    return LegacyProgress(inventory_digest=inv.digest, tasks=tuple(out))


def inherited(inv: Inventory) -> dict[str, str]:
    return {t.task_id: f"legacy {t.attempt} {t.evidence}" for t in inv.tasks if t.verdict == "inherit"}


def diff(inv: Inventory, rdir: Path) -> dict:
    """The dry-run report: what the migration would do, and what already is."""
    current = bt_run_owner.read(rdir)
    counts: dict[str, int] = {}
    for t in inv.tasks:
        counts[t.verdict] = counts.get(t.verdict, 0) + 1
    return {"run_id": run_ref(inv).run_id, "inventory_digest": inv.digest, "current_owner": current,
            "would_own": "dbos", "blockers": inv.blockers, "counts": counts,
            "tasks": [t.model_dump(mode="json", include={"task_id", "legacy_state", "verdict", "reason"}) for t in inv.tasks]}


def backup(state_dir: Path, rdir: Path, inv: Inventory, dest: Path) -> Path:
    """A consistent copy of the legacy stores and run files, with a checksum list, before ownership moves."""
    target = dest / f"{inv.project}-{inv.req}-r{inv.revision}-{inv.digest[:12]}"
    if (target / "SHA256SUMS").is_file():
        return target                                         # idempotent: the same inventory was backed up already
    target.mkdir(parents=True, exist_ok=True)
    sums = []
    sources = [state_dir / "scheduler" / f"{inv.project}-{inv.req}.db",
               *map(Path, glob.glob(str(state_dir / "scheduler" / f"{inv.project}-{inv.req}-*-modules" / "*.sqlite3")))]
    for src in sources:
        if not src.is_file():
            continue
        out = target / (src.parent.name + "__" + src.name if src.parent.name.endswith("-modules") else src.name)
        conn = sqlite3.connect(f"{src.resolve().as_uri()}?mode=ro", uri=True, timeout=10)
        try:
            with sqlite3.connect(out) as copy:
                conn.backup(copy)                             # an online, consistent snapshot of a WAL database
        finally:
            conn.close()
        sums.append(f"{hashlib.sha256(out.read_bytes()).hexdigest()}  {out.name}")
    for name in ("RUN.decisions.jsonl", "RUN.interventions.jsonl", "RUN.healing.json", "RUN.projection.json"):
        if (rdir / name).is_file():
            shutil.copy2(rdir / name, target / name)
            sums.append(f"{hashlib.sha256((target / name).read_bytes()).hexdigest()}  {name}")
    (target / "inventory.json").write_text(inv.model_dump_json(indent=1), encoding="utf-8")
    (target / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")
    return target


def claim(rdir: Path, inv: Inventory, *, by: str) -> OwnerRecord:
    """Move ownership to the durable backend. Refuses with blockers; a repeat with the same inventory is a no-op."""
    if inv.blockers:
        raise RuntimeError("MIGRATION_BLOCKED: " + "; ".join(inv.blockers))
    current = bt_run_owner.read(rdir)
    run = run_ref(inv)
    if current and current.get("backend") == Backend.DBOS and current.get("run_id") == run.run_id:
        return OwnerRecord.model_validate(current)
    record = OwnerRecord(run_id=run.run_id, backend=Backend.DBOS, workflow_id=f"bt:{run.run_id}", since=time.time(),
                         by=by, migrated_from=f"legacy@{inv.digest[:12]}")
    bt_run_owner.write(rdir, record.model_dump(mode="json"), expect=current)
    return record


def release(rdir: Path, *, by: str) -> dict:
    """Rollback of ownership: the legacy store was never written, so handing the run back is only the owner record
    (the caller cancels the durable workflows and terminates their units first)."""
    current = bt_run_owner.read(rdir)
    record = {**(current or {}), "backend": "legacy", "since": time.time(), "by": by, "workflow_id": None}
    bt_run_owner.write(rdir, record, expect=current)
    return record
