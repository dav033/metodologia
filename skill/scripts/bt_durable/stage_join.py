"""A later stage joins a plan the durable runtime runs (D-134 for durable runs, D-149).

«Ejecutar subplan» freezes a new plan revision (the approved stage). A durable run is bound to one frozen revision
(`RunRef`: lines, attempt keys and compositions are named after it), so the stage does not change the running workflow:
the run of the new revision CONTINUES the current one.

- Its lines start where the current run's lines are: every `refs/bt/line/…/r<old>/…` and `refs/bt/subplan/…/r<old>/…` is
  copied to `r<new>` (create-only), so accepted work, and anything an operator committed on a line, is kept as it is.
- A task accepted in the current run whose specification did not change is inherited without running anything
  (`LegacyTask.integrated`: its snapshot is already in the copied lines). A task with a captured snapshot that was not
  accepted (stopped, waiting for the owner) is reconciled: its snapshot is verified again first and, if that fails, the
  next attempt continues from it with the failure as its note. Everything else runs.
- A join that would redo accepted work (its task changed in the new stage) needs `confirm`, as the legacy join does.
- It happens at a quiet point: with live attempts the current run is paused and `RUN.join.json` records the request;
  the engine completes it once they end (`drain`).
- Then the current run's workflows are cancelled, `RUN.owner.json` and `RUN.durable-run.json` move to the new run by
  compare-and-swap, and the new run starts. Open owner decisions of the current run end with it (the reconciled task
  asks again if it must).
- `RUN.join.json` is written BEFORE the cancel, whatever started the join, and removed only once the run pointer moved:
  a join cut between the cancel and the new run's start (the CLI or the web service killed, an engine restart) left the
  run cancelled with nothing to finish it, and no rung noticed (the Solucionador watches runs in ERROR and PENDING tasks).
  The engine's `drain` completes it from the marker. Joins of one requirement are serialised by `RUN.join.lock`: the
  CLI waits for it, the drain skips a requirement whose lock is held (audit of REQ-030, 2026-10-29).
"""
from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import bt_run_owner
from bt_contracts.execution import (
    Backend,
    LegacyProgress,
    LegacyTask,
    OwnerRecord,
    RunRef,
)

LIVE = frozenset({"queued", "running", "verifying", "recovering", "waiting_quota"})
DONE = frozenset({"completed", "inherited"})
PENDING = "RUN.join.json"
LOCK = "RUN.join.lock"
FINGERPRINT = ("objective", "acceptance_criteria", "verification", "expected_paths", "after", "repository")


class JoinRefused(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code, self.message = code, message


class JoinBusy(RuntimeError):
    """Another process is joining a stage of this requirement right now."""


@contextlib.contextmanager
def locked(rdir: Path, *, wait: bool = True) -> Iterator[None]:
    """One join of a requirement at a time (CLI, web and the engine's drain). `wait=False` raises JoinBusy instead."""
    with open(Path(rdir) / LOCK, "a+") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | (0 if wait else fcntl.LOCK_NB))
        except BlockingIOError:
            raise JoinBusy(str(rdir)) from None
        yield


def _write_pending(rdir: Path, request: dict) -> None:
    target = Path(rdir) / PENDING
    tmp = target.with_name(f".{PENDING}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(request, indent=1) + "\n", encoding="utf-8")
    with open(tmp, "rb") as stream:
        os.fsync(stream.fileno())
    os.replace(tmp, target)


def fingerprint(plan_doc: dict, task_id: str) -> str:
    task = next((t for t in plan_doc.get("tasks", ()) if t.get("id") == task_id), None)
    if task is None:
        return ""
    return hashlib.sha256(json.dumps({k: task.get(k) for k in FINGERPRINT}, sort_keys=True).encode()).hexdigest()


def _manifests(state_dir: Path, run: RunRef, task_id: str) -> list[Path]:
    """The captured handoffs of `task_id`'s attempts in `run`, newest attempt first."""
    folder = state_dir / "attempts-root" / "attempts"
    stem = f"{run.project}-{run.req}-r{run.revision}-{task_id}-a"
    hits = [p / "handoff" / "manifest.json" for p in folder.glob(f"{stem}*") if (p / "handoff" / "manifest.json").is_file()]

    def number(path: Path) -> int:
        tail = path.parent.parent.name[len(stem):].split("-", 1)[0]
        return int(tail) if tail.isdigit() else 0
    return sorted(hits, key=number, reverse=True)


def _commit_exists(repo: str, sha: str) -> bool:
    return bool(repo and sha) and subprocess.run(["git", "cat-file", "-e", f"{sha}^{{commit}}"], cwd=repo,
                                                 capture_output=True, check=False).returncode == 0


def _from_manifest(manifest: Path, task_id: str, verdict: str, provenance: str, *, snapshot: str = "",
                   integrated: bool = False) -> LegacyTask | None:
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    sha, base, repo = snapshot or data.get("snapshot_sha"), data.get("base_sha"), data.get("repository", "")
    if data.get("status") != "captured" or not sha or not base or sha == base or not _commit_exists(repo, sha):
        return None
    worktree = data.get("worktree")
    return LegacyTask(task_id=task_id, verdict=verdict, snapshot_sha=sha, base_sha=base, repository=Path(repo),
                      attempt_dir=manifest.parent.parent, manifest_path=manifest,
                      worktree=Path(worktree) if worktree and Path(worktree).is_dir() else None,
                      provenance=provenance[:500], integrated=integrated)


def plan(*, state_dir: Path, old: RunRef, new: RunRef, status: dict, inherited: LegacyProgress) -> dict:
    """What the join would do: per task of the new stage inherit | reconcile | redo, the live attempts and the accepted
    work it would redo. `status` is `Client.status(old)`; `inherited` the current run's own starting progress."""
    old_doc = json.loads(Path(old.plan_path).read_text(encoding="utf-8"))
    new_doc = json.loads(Path(new.plan_path).read_text(encoding="utf-8"))
    summary = status.get("summary") or {}
    states, results = summary.get("tasks") or {}, summary.get("results") or {}
    started = {t.task_id: t for t in inherited.tasks}          # what the current run itself started from
    live = sorted(t for t, row in (status.get("tasks") or {}).items()
                  if row.get("workflow_status") == "PENDING" and ((row.get("state") or {}).get("state") in LIVE))
    tasks, redone = [], []
    for item in new_doc.get("tasks", ()):
        tid = item["id"]
        same = bool(fingerprint(old_doc, tid)) and fingerprint(old_doc, tid) == fingerprint(new_doc, tid)
        result = results.get(tid) or {}
        if states.get(tid) in DONE and not same:
            redone.append(tid)
        entry = None
        if states.get(tid) in DONE and same:
            snapshot = result.get("snapshot_sha") or (started[tid].snapshot_sha if tid in started else "")
            provenance = (started[tid].provenance if states[tid] == "inherited" and tid in started else
                          f"durable {old.run_id} {result.get('verdict_ref') or ''}".strip())
            if tid in started and started[tid].snapshot_sha == snapshot:   # accepted on the material it started from
                entry = started[tid].model_copy(update={"verdict": "inherit", "integrated": True,
                                                        "provenance": provenance[:500]})
            else:                                              # accepted on an attempt of the current run
                entry = next((e for m in _manifests(state_dir, old, tid)
                              if (e := _from_manifest(m, tid, "inherit", provenance, snapshot=snapshot, integrated=True))),
                             None)
            if entry is None:                                  # never redo accepted work silently: refuse instead
                raise JoinRefused("JOIN_MATERIAL_MISSING", f"{tid} was accepted in {old.run_id} but its snapshot "
                                  f"({snapshot or 'none'}) has no captured handoff to continue from")
        elif tid in states and same:                           # started, not accepted: continue from its last snapshot
            entry = next((e for m in _manifests(state_dir, old, tid)
                          if (e := _from_manifest(m, tid, "reconcile", f"durable {old.run_id} {states[tid]}"))), None)
        tasks.append({"task_id": tid, "verdict": entry.verdict if entry else "redo", "previous": states.get(tid, ""),
                      "item": entry})
    return {"tasks": tasks, "live": live, "redone": redone}


def progress(report: dict, *, paused: bool = False) -> LegacyProgress:
    items = tuple(t["item"] for t in report["tasks"] if t["item"] is not None)
    digest = hashlib.sha256(json.dumps([i.model_dump(mode="json") for i in items], sort_keys=True,
                                       default=str).encode()).hexdigest()
    return LegacyProgress(inventory_digest=digest, tasks=items, paused=paused)


def copy_lines(repositories, roles, old: RunRef, new: RunRef) -> list[str]:
    """Copy the current run's run lines, base pins and subplan lines to the new revision (create-only, idempotent).
    `repositories`: role -> checkout (a mapping or the engine's resolver)."""
    from .adapters.integration import _SAFE
    project = _SAFE.sub("-", old.project)
    copied = []
    resolve = repositories if callable(repositories) else repositories.get
    found = {role: resolve(role) for role in roles}
    if missing := sorted(role for role, path in found.items() if path is None):
        raise JoinRefused("REPOSITORY_UNKNOWN", ", ".join(missing))
    for repo in sorted({Path(p) for p in found.values()}):
        prefixes = [f"refs/bt/line/{project}/{old.req}/r{old.revision}/", f"refs/bt/subplan/{project}/{old.req}/r{old.revision}/"]
        listed = subprocess.run(["git", "for-each-ref", "--format=%(refname) %(objectname)", *prefixes], cwd=repo,
                                capture_output=True, text=True, check=True).stdout.split("\n")
        for line in filter(None, listed):
            ref, sha = line.split()
            target = ref.replace(f"/{old.req}/r{old.revision}/", f"/{new.req}/r{new.revision}/", 1)
            current = subprocess.run(["git", "rev-parse", "-q", "--verify", target], cwd=repo, capture_output=True,
                                     text=True, check=False).stdout.strip()
            if current == sha:
                continue
            if current:
                raise JoinRefused("JOIN_LINES_EXIST", f"{target} already exists at another commit in {repo}")
            subprocess.run(["git", "update-ref", target, sha, ""], cwd=repo, capture_output=True, text=True, check=True)
            copied.append(f"{repo.name}:{target}")
    return copied


def join(client, rdir: Path, *, state_dir: Path, new: RunRef, repositories, settings=None, confirm: bool = False,
         dry_run: bool = False, by: str = "bt-durable join", emit=None, wait: bool = True) -> dict:
    """Join the frozen stage `new` into the run the durable runtime owns in `rdir` (see the module docstring).
    `settings`: the new run's; by default the current run's own (the run continues). `emit`: telemetry. `wait=False`
    raises JoinBusy when another join of the requirement holds its lock."""
    if dry_run:
        return _join(client, rdir, state_dir=state_dir, new=new, repositories=repositories, settings=settings,
                     confirm=confirm, dry_run=True, by=by, emit=emit)
    with locked(rdir, wait=wait):
        return _join(client, rdir, state_dir=state_dir, new=new, repositories=repositories, settings=settings,
                     confirm=confirm, dry_run=False, by=by, emit=emit)


def _join(client, rdir: Path, *, state_dir: Path, new: RunRef, repositories, settings, confirm: bool, dry_run: bool,
          by: str, emit) -> dict:
    emit = emit or (lambda event, **fields: None)
    owner = bt_run_owner.read(rdir)
    if not owner or owner.get("backend") != "dbos":
        raise JoinRefused("NOT_DURABLE", "the run is not owned by the durable runtime")
    old = RunRef.model_validate_json((Path(rdir) / "RUN.durable-run.json").read_text(encoding="utf-8"))
    if new.revision <= old.revision:
        (Path(rdir) / PENDING).unlink(missing_ok=True)
        return {"status": "current", "run_id": old.run_id}
    status = client.status(old)
    rows = client.client.list_workflows(workflow_ids=[f"bt:{old.run_id}"], load_input=True, load_output=False)
    args = ((rows[0].input or {}).get("args") or ()) if rows else ()
    inherited = LegacyProgress.model_validate(args[2]) if len(args) > 2 else LegacyProgress()
    if settings is None:
        from .settings import Settings
        settings = Settings.model_validate(args[1]) if len(args) > 1 else Settings()
    report = plan(state_dir=state_dir, old=old, new=new, status=status, inherited=inherited)
    # the owner's pause carries over; the pause this join itself sent while it waited for live attempts does not
    try:
        pending = json.loads((Path(rdir) / PENDING).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pending = None
    paused = bool(pending.get("owner_paused")) if isinstance(pending, dict) else \
        (status.get("summary") or {}).get("status") == "paused"
    if report["redone"] and not confirm and not dry_run:
        raise JoinRefused("JOIN_NEEDS_CONFIRM", "the new stage changes accepted tasks, which would run again: "
                          + ", ".join(report["redone"]))
    counts = {v: sum(1 for t in report["tasks"] if t["verdict"] == v) for v in ("inherit", "reconcile", "redo")}
    if dry_run:
        return {"status": "dry_run", "from": old.run_id, "to": new.run_id, "counts": counts, "live": report["live"],
                "paused": paused,
                "redone": report["redone"],
                "tasks": {t["task_id"]: f"{t['verdict']} (was {t['previous'] or 'not started'})" for t in report["tasks"]}}
    earlier = {k: v for k, v in pending.items() if k != "error"} if isinstance(pending, dict) else {}
    request = {**earlier, "run": new.model_dump(mode="json"), "by": by,
               "confirm": confirm, "settings": settings.model_dump(mode="json"), "owner_paused": paused}
    request.setdefault("since", time.time())
    if report["live"]:
        client.command(old, "pause", request_id=f"join-r{new.revision}-pause", by="stage join")
        _write_pending(rdir, {**request, "stage": "waiting"})
        emit("stage_join_waiting", run_id=old.run_id, to=new.run_id, live=report["live"])
        return {"status": "waiting", "run_id": old.run_id, "live": report["live"], "counts": counts}
    roles = {t.get("repository") or "default" for t in json.loads(Path(new.plan_path).read_text())["tasks"]}
    copied = copy_lines(repositories, roles, old, new)
    # from the cancel on, the old run is gone: the marker lets the engine finish what an interrupted join started
    _write_pending(rdir, {**request, "stage": "moving"})
    cancelled = client.cancel(old)
    record = OwnerRecord(run_id=new.run_id, backend=Backend.DBOS, workflow_id=f"bt:{new.run_id}", since=time.time(),
                         by=by, migrated_from=f"durable {old.run_id}")
    bt_run_owner.write(rdir, record.model_dump(mode="json"), expect=owner)
    workflow = client.start(new, settings, progress(report, paused=paused))
    # the run pointer moves last: a join interrupted before this point is finished by asking for it again
    (Path(rdir) / "RUN.durable-run.json").write_text(new.model_dump_json(indent=1), encoding="utf-8")
    (Path(rdir) / PENDING).unlink(missing_ok=True)
    emit("stage_joined", run_id=old.run_id, to=new.run_id, counts=counts, lines=len(copied), cancelled=len(cancelled),
         paused=paused)
    return {"status": "joined", "from": old.run_id, "to": new.run_id, "workflow": workflow, "counts": counts,
            "paused": paused,
            "reconcile": [t["task_id"] for t in report["tasks"] if t["verdict"] == "reconcile"],
            "cancelled": cancelled, "lines": copied}


def drain(root: Path, client, *, state_dir: Path, repositories_for, emit=None) -> list[dict]:
    """The engine's pass over pending joins (`RUN.join.json` under `root`): each is tried again and completes once its
    run is quiet. A refusal is written into the file, which is then left alone (the owner sees why, and asks again)."""
    out = []
    for marker in sorted(Path(root).glob(f"*/requirements/*/{PENDING}")):
        try:
            request = json.loads(marker.read_text(encoding="utf-8"))
            new = RunRef.model_validate(request["run"])
        except (OSError, ValueError, KeyError):
            continue
        if request.get("error"):
            continue
        rdir, project = marker.parent, marker.parent.parent.parent.name
        try:
            from .settings import Settings
            settings = Settings.model_validate(request["settings"]) if request.get("settings") else None
            out.append(join(client, rdir, state_dir=state_dir, new=new, repositories=repositories_for(project),
                            settings=settings, confirm=bool(request.get("confirm")), by="engine stage join", emit=emit,
                            wait=False))
        except JoinBusy:
            out.append({"status": "busy", "rdir": str(rdir)})             # its own process is joining it right now
        except JoinRefused as refused:
            marker.write_text(json.dumps({**request, "error": f"{refused.code}: {refused.message}"}, indent=1) + "\n",
                              encoding="utf-8")
            out.append({"status": "refused", "code": refused.code, "message": refused.message})
    return out
