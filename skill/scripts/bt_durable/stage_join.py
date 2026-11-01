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
- A join that would redo accepted work (its task changed in the new stage) needs `confirm`, as the legacy join does,
  except for the tasks of a subplan the OWNER reconfirmed after the current run's stage when the stage holding that
  confirmation is in the join and holds the task as joined (D-275, the owner's choice «Reconfirmar = confirmar»).
  `confirm` is True (everything) or the exact tasks the owner saw (`--confirm-tasks`, the panel's «Confirmar y unir»):
  anything else redone is refused again. The join result, its telemetry and the requirement's activity say who
  confirmed each redone task («confirmado al reconfirmar SP-14 a las 19:55»).
- The engine joins a frozen stage the durable run is behind on its own (`behind`, in its drain pass), once, while no
  refusal is recorded for that revision: a stage is frozen only by the owner's approval (or D-241's standing rule).
- It happens at a quiet point: with live attempts the current run is paused and `RUN.join.json` records the request;
  the engine completes it once they end (`drain`).
- Then the current run's workflows are cancelled, `RUN.owner.json` and `RUN.durable-run.json` move to the new run by
  compare-and-swap, and the new run starts. Open owner decisions of the current run end with it (the reconciled task
  asks again if it must).
- A refused join leaves `RUN.join.refused.json` (when, target revision, code, message, who asked) until a later join of
  the requirement is not refused: the panel shows why a frozen stage is still waiting to join (D-272).
- `RUN.join.json` is written BEFORE the cancel, whatever started the join, and removed only once the run pointer moved:
  a join cut between the cancel and the new run's start (the CLI or the web service killed, an engine restart) left the
  run cancelled with nothing to finish it, and no rung noticed (the Solucionador watches runs in ERROR and PENDING tasks).
  The engine's `drain` completes it from the marker. Joins of one requirement are serialised by `RUN.join.lock`: the
  CLI waits for it, the drain skips a requirement whose lock is held (audit of REQ-030, 2026-10-29).
"""
from __future__ import annotations

import contextlib
import datetime as dt
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
REFUSED = "RUN.join.refused.json"
FINGERPRINT = ("objective", "acceptance_criteria", "verification", "expected_paths", "after", "repository")


class JoinRefused(RuntimeError):
    def __init__(self, code: str, message: str, *, tasks: list[str] | None = None):
        super().__init__(f"{code}: {message}")
        self.code, self.message, self.tasks = code, message, list(tasks or ())


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


def note_refusal(rdir: Path, revision: int, code: str, message: str, *, by: str, tasks: list[str] | None = None) -> None:
    """Record the last refused join of the requirement (read by the panel, `bt_verification_correction`; D-272). `tasks`:
    the redone tasks still waiting for the owner's confirmation (JOIN_NEEDS_CONFIRM, D-275)."""
    target = Path(rdir) / REFUSED
    tmp = target.with_name(f".{REFUSED}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps({"at": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "revision": revision,
                               "code": code, "message": message[:500], "by": by, "tasks": list(tasks or ())},
                              indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def last_refusal(rdir: Path) -> dict | None:
    """The last refused join (`note_refusal`), or None when there is none or it is unreadable."""
    try:
        data = json.loads((Path(rdir) / REFUSED).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


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
    """The task's progress from one captured handoff, or None. An accepted task (`integrated`) whose snapshot IS its
    base is inherited as it is: the attempt changed nothing because its work was already in the base it started from,
    which is a legitimate acceptance (pictures REQ-021 T2.3 in r32, D-272). The join refused it as JOIN_MATERIAL_MISSING
    and the confirmed SP-14 could never reach the run. The commit must still exist; the worktree need not (D-266)."""
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    sha, base, repo = snapshot or data.get("snapshot_sha"), data.get("base_sha"), data.get("repository", "")
    if data.get("status") != "captured" or not sha or not base or not _commit_exists(repo, sha):
        return None
    if sha == base and not integrated:     # nothing of its own to verify again or continue from: the task runs
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


def _hhmm(stamp: str) -> str:
    try:
        return dt.datetime.fromisoformat(stamp).strftime("%H:%M")
    except ValueError:
        return stamp


def reconfirmed(rdir: Path, old: RunRef, new: RunRef, redone: list[str]) -> dict[str, dict]:
    """Redone task -> {"subplan", "at", "via", "stage", "text"} for each task the owner's reconfirmation of its subplan
    confirms (D-275): confirmed after the current run's stage was frozen, held by a stage in the join, and the task as
    that stage holds it is the task as it joins (a later change was never confirmed). Unreadable facts confirm nothing."""
    import bt_stage_confirmations as confirmations
    new_doc = json.loads(Path(new.plan_path).read_text(encoding="utf-8"))
    subplan = {t.get("id"): t.get("subplan_id") or "" for t in new_doc.get("tasks", ())}
    found = confirmations.owner_reconfirmations(rdir, {subplan.get(t) for t in redone if subplan.get(t)},
                                            after=old.revision, upto=new.revision)
    out: dict[str, dict] = {}
    docs: dict[int, dict] = {}
    for tid in redone:
        hit = found.get(subplan.get(tid) or "")
        if not hit:
            continue
        if hit["stage"] != new.revision:
            if hit["stage"] not in docs:
                try:
                    import bt_plan_adapter
                    docs[hit["stage"]] = bt_plan_adapter.planner_revisions.load_revision(rdir, hit["stage"])
                except Exception:  # noqa: BLE001 - the holding stage unreadable: not confirmed
                    docs[hit["stage"]] = {}
            if not fingerprint(docs[hit["stage"]], tid) or fingerprint(docs[hit["stage"]], tid) != fingerprint(new_doc, tid):
                continue
        out[tid] = {**hit, "subplan": subplan[tid],
                    "text": f"confirmado al reconfirmar {subplan[tid]} a las {_hhmm(hit['at'])}"}
    return out


def _confirmations(rdir: Path, old: RunRef, new: RunRef, redone: list[str], confirm, confirm_by: str) -> tuple[dict, list]:
    """(task -> who confirmed it, the redone tasks nobody confirmed) for `confirm` True | False | the confirmed tasks."""
    try:
        covered = reconfirmed(rdir, old, new, redone) if redone else {}
    except (OSError, ValueError):
        covered = {}
    explicit = set(redone) if confirm is True else set(confirm or ()) if not isinstance(confirm, bool) else set()
    said = {t: covered[t]["text"] for t in redone if t in covered}
    who = "ti" if confirm_by == "owner" else confirm_by
    said.update({t: f"confirmado por {who}" for t in redone if t not in said and t in explicit})
    return said, [t for t in redone if t not in said]


def _note_activity(rdir: Path, new: RunRef, said: dict[str, str]) -> None:
    """One activity line per way of confirming, so the owner sees why accepted work runs again (D-275)."""
    if not said:
        return
    import bt_planning_activity as activity
    groups: dict[str, list[str]] = {}
    for tid, text in said.items():
        groups.setdefault(text, []).append(tid)
    for text, tids in groups.items():
        sp = text.split("reconfirmar ", 1)[1].split(" ", 1)[0] if "reconfirmar " in text else ""
        activity.record(rdir, "Ejecución", f"Etapa r{new.revision} unida: se rehacen {', '.join(tids)} ({text})",
                        kind="flow", sp=sp)


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


def join(client, rdir: Path, *, state_dir: Path, new: RunRef, repositories, settings=None,
         confirm: bool | list[str] = False, dry_run: bool = False, by: str = "bt-durable join", emit=None,
         wait: bool = True) -> dict:
    """Join the frozen stage `new` into the run the durable runtime owns in `rdir` (see the module docstring).
    `settings`: the new run's; by default the current run's own (the run continues). `confirm`: True, or the redone
    tasks the owner confirmed. `emit`: telemetry. `wait=False` raises JoinBusy when another join holds its lock."""
    if dry_run:
        return _join(client, rdir, state_dir=state_dir, new=new, repositories=repositories, settings=settings,
                     confirm=confirm, dry_run=True, by=by, emit=emit)
    with locked(rdir, wait=wait):
        try:
            outcome = _join(client, rdir, state_dir=state_dir, new=new, repositories=repositories, settings=settings,
                            confirm=confirm, dry_run=False, by=by, emit=emit)
        except JoinRefused as refused:
            note_refusal(rdir, new.revision, refused.code, refused.message, by=by, tasks=refused.tasks)
            raise
        (Path(rdir) / REFUSED).unlink(missing_ok=True)          # this join was not refused: the old reason is gone
        return outcome


def _join(client, rdir: Path, *, state_dir: Path, new: RunRef, repositories, settings, confirm, dry_run: bool,
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
        from .settings import Settings, configured
        settings = configured(Settings.model_validate(args[1]) if len(args) > 1 else None)   # live knobs (D-239)
    report = plan(state_dir=state_dir, old=old, new=new, status=status, inherited=inherited)
    # the owner's pause carries over; the pause this join itself sent while it waited for live attempts does not
    try:
        pending = json.loads((Path(rdir) / PENDING).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pending = None
    paused = bool(pending.get("owner_paused")) if isinstance(pending, dict) else \
        (status.get("summary") or {}).get("status") == "paused"
    earlier = {k: v for k, v in pending.items() if k != "error"} if isinstance(pending, dict) else {}
    confirm_by = str(earlier.get("confirm_by") or by)       # who asked for the confirmed join, not the engine finishing it
    said, unconfirmed = _confirmations(rdir, old, new, report["redone"], confirm, confirm_by)
    if unconfirmed and not dry_run:
        raise JoinRefused("JOIN_NEEDS_CONFIRM", "the new stage changes accepted tasks, which would run again: "
                          + ", ".join(unconfirmed) + (f" (already confirmed: {', '.join(said)})" if said else ""),
                          tasks=unconfirmed)
    counts = {v: sum(1 for t in report["tasks"] if t["verdict"] == v) for v in ("inherit", "reconcile", "redo")}
    if dry_run:
        return {"status": "dry_run", "from": old.run_id, "to": new.run_id, "counts": counts, "live": report["live"],
                "paused": paused,
                "redone": report["redone"], "confirmed": said, "needs_confirm": unconfirmed,
                "tasks": {t["task_id"]: f"{t['verdict']} (was {t['previous'] or 'not started'})" for t in report["tasks"]}}
    request = {**earlier, "run": new.model_dump(mode="json"), "by": by,
               "confirm": confirm if isinstance(confirm, bool) else sorted(confirm),
               "settings": settings.model_dump(mode="json"), "owner_paused": paused}
    if confirm:
        request["confirm_by"] = confirm_by
    request.setdefault("since", time.time())
    if report["live"]:
        client.command(old, "pause", request_id=f"join-r{new.revision}-pause", by="stage join")
        _write_pending(rdir, {**request, "stage": "waiting"})
        emit("stage_join_waiting", run_id=old.run_id, to=new.run_id, live=report["live"])
        return {"status": "waiting", "run_id": old.run_id, "live": report["live"], "counts": counts, "confirmed": said}
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
         paused=paused, confirmed=said)
    _note_activity(rdir, new, said)
    return {"status": "joined", "from": old.run_id, "to": new.run_id, "workflow": workflow, "counts": counts,
            "paused": paused, "confirmed": said,
            "reconcile": [t["task_id"] for t in report["tasks"] if t["verdict"] == "reconcile"],
            "cancelled": cancelled, "lines": copied}


def behind(root: Path) -> list[tuple[Path, int]]:
    """Requirements under `root` whose durable run is behind their latest frozen STAGE (a manifest entry with stage pins)
    with no pending join and no refusal recorded for that revision or a later one: (rdir, latest revision). Cheap: two
    small JSON reads per durable requirement."""
    out = []
    for pointer in sorted(Path(root).glob("*/requirements/*/RUN.durable-run.json")):
        rdir = pointer.parent
        if (rdir / PENDING).exists():
            continue
        try:
            running = json.loads(pointer.read_text(encoding="utf-8")).get("revision")
            entries = json.loads((rdir / "plan-revisions" / "MANIFEST.json").read_text(encoding="utf-8"))["revisions"]
            if bt_run_owner.backend(rdir) != "dbos":
                continue
        except Exception:  # noqa: BLE001, S112 - an unreadable requirement is not joined behind anyone's back
            continue
        last = max((e for e in entries if isinstance(e, dict) and isinstance(e.get("revision"), int)),
                   key=lambda e: e["revision"], default=None)
        if not last or not isinstance(last.get("stage"), dict) or not isinstance(running, int):
            continue
        refused = last_refusal(rdir) or {}
        if last["revision"] > running and not (isinstance(refused.get("revision"), int)
                                              and refused["revision"] >= last["revision"]):
            out.append((rdir, last["revision"]))
    return out


def drain(root: Path, client, *, state_dir: Path, repositories_for, emit=None, prepare=None) -> list[dict]:
    """The engine's pass over pending joins (`RUN.join.json` under `root`): each is tried again and completes once its
    run is quiet. A refusal is written into the file, which is then left alone (the owner sees why, and asks again).
    With `prepare(rdir, project, req) -> RunRef` (the CLI's frozen-plan check) it also joins the stages the durable runs
    are behind (`behind`, D-275); a refusal is recorded and that revision is not tried again."""
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
                            settings=settings, confirm=request.get("confirm") or False, by="engine stage join",
                            emit=emit, wait=False))
        except JoinBusy:
            out.append({"status": "busy", "rdir": str(rdir)})             # its own process is joining it right now
        except JoinRefused as refused:
            marker.write_text(json.dumps({**request, "error": f"{refused.code}: {refused.message}"}, indent=1) + "\n",
                              encoding="utf-8")
            out.append({"status": "refused", "code": refused.code, "message": refused.message})
    for rdir, revision in (behind(root) if prepare else ()):
        project, req = rdir.parent.parent.name, "-".join(rdir.name.split("-")[:2])
        try:
            new = prepare(rdir, project, req)
        except SystemExit as refused:                       # the frozen plan breaks its contract: say so, once
            note_refusal(rdir, revision, "PLAN_PREFLIGHT", str(refused), by="engine stage join")
            out.append({"status": "refused", "code": "PLAN_PREFLIGHT", "message": str(refused)})
            continue
        try:
            outcome = join(client, rdir, state_dir=state_dir, new=new, repositories=repositories_for(project),
                           by="engine stage join", emit=emit, wait=False)
            out.append({**outcome, "automatic": True})
        except JoinBusy:
            out.append({"status": "busy", "rdir": str(rdir)})
        except JoinRefused as refused:                     # recorded by `join`: the panel shows it, no retry
            out.append({"status": "refused", "code": refused.code, "message": refused.message, "automatic": True})
        except Exception as error:  # noqa: BLE001 - e.g. the system database briefly away: tried again next pass
            out.append({"status": "error", "rdir": str(rdir), "error": f"{type(error).__name__}: {error}"[:300]})
    return out
