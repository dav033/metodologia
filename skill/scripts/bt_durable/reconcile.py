"""Subplan lines keep up with the subplans they build on (D-297; pictures REQ-021 r39: «no pude combinar este subplan con la
versión actual de SP-2», and «lo que quiero que hagas es que algo así no vuelva a pasar»).

A subplan's line holds its members and their frozen-plan ancestors, so a repair a later stage adds to an earlier subplan
never reaches it, and when it is an ancestor and conflicts it is left out «for the gates that compose both» (D-172, D-289).
Those gates are far away: SP-2's r27 and r32 repairs lay outside SP-5..SP-12 for days while CG-10..CG-12 waited on SP-10 and
the owner, and the owner was offered trees without them (D-246 said so, and nobody was asked to do anything about it).

Once per engine pass, before the Solucionador looks for work (`solver.Solver.run_pass`), `sweep` folds every subplan line,
in plan order, with the current lines of the subplans it builds on (`bt_verification_tree.fold`, the composer's rules):

- it folds and the tree changes: the line takes that commit by compare-and-swap, the same commit «Probar» already offered, so
  the version and the owner's decision on it stand. An earlier subplan never moves for a later one: its approval is safe.
- a conflict git and the rules leave: nothing moves (a line takes all its predecessors or none), the existing resolution
  requests are opened and bound to this run, and `resolutions.triggers` gives them to the Solucionador, which writes
  `<key>.resolved`. The next pass goes on from there. Subplans holding the same versions of a file share one request.
- a line moved or a pending subplan cleared: the run is told (`recheck_gates`), so its gates judge the new versions.

Lines are moved, not only the tried tree, so there is one resolution of each clash: the gates compose what the owner tried
and no later attempt starts from a line without the repair. While a member of a gate is not reconciled the composer does not
compose it (`PENDING`): it would ask an agent to settle the same clash a second time, against other merge bases.

`view` is what the panel says about it, from the record under `<state>/reconcile/` and the Solucionador's triggers.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import time
from collections.abc import Callable
from pathlib import Path

LOG = logging.getLogger("bt_durable.reconcile")
PENDING = "RECONCILE_PENDING"
WORKING = frozenset({"running", "queued"})
ESCALATED = frozenset({"limit", "gave_up", "asked_owner", "failed"})


def enabled() -> bool:
    """It runs where the Solucionador it hands conflicts to runs (`solver.enabled`, without importing it for the panel)."""
    import bt_config
    return (bt_config.get("solver.reconcile", True) is True and bt_config.get("solver.enabled") is True
            and all(bt_config.get(key) is True for key in ("healing.enabled", "healing.model_diagnosis", "diagnosis.auto")))


def _path(root: Path, project: str, req: str) -> Path:
    return Path(root) / ".state" / "durable" / "reconcile" / f"{project}-{req}.json"


def load(root: Path, project: str, req: str) -> dict:
    """{"subplans": {sid: what it waits for}, "moved": {sid: [each move of its line]}, "dirty": the run was not told yet}."""
    try:
        data = json.loads(_path(root, project, req).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    data = data if isinstance(data, dict) else {}
    data["subplans"] = data.get("subplans") if isinstance(data.get("subplans"), dict) else {}
    data["moved"] = data.get("moved") if isinstance(data.get("moved"), dict) else {}
    return data


def _save(root: Path, project: str, req: str, data: dict) -> None:
    target = _path(root, project, req)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def history(rdir: Path) -> dict[str, list[dict]]:
    """Sid -> the moves of its line. `bt_verification.durable_versions` counts the tips the owner was offered before a move,
    so a version number never goes back when a line takes its fold (the tip itself was never published)."""
    rdir = Path(rdir)
    root, project = rdir.parent.parent.parent, rdir.parent.parent.name
    return load(root, project, "-".join(rdir.name.split("-")[:2]))["moved"]


def _iso(now: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now))


def _record_activity(rdir: Path, text: str) -> None:
    import bt_planning_activity
    bt_planning_activity.record(rdir, "Combinación", text, kind="flow")


def sweep(root: Path, rdir: Path, run, *, client=None, record: Callable | None = None, emit: Callable | None = None,
          now: Callable[[], float] = time.time) -> dict:
    """One pass over one run: {"moved": [sids], "pending": {sid: entry}, "bound": {request key: {"run_id", "subplan", "with"}}}.
    Idempotent: with nothing new it makes no commit and no ref moves (`fold` is memoized by tips and resolutions)."""
    rdir, root = Path(rdir), Path(root)
    out: dict = {"moved": [], "pending": {}, "bound": {}}
    if (rdir / "RUN.join.json").exists():                # a stage join is copying these lines: the next pass, on the new ones
        return out
    import bt_verification as verification
    import bt_verification_tree as tree
    lines = verification._lines(rdir)
    if not lines or lines.get("revision") != run.revision:
        return out
    record = record or _record_activity
    data = load(root, run.project, run.req)
    built = verification._built(rdir, lines)
    tips = dict(lines["tips"])
    pending: dict[str, dict] = {}
    for sid in [s.get("id") for s in lines["plan"].get("subplans") or () if isinstance(s, dict)]:
        if sid not in tips:
            continue
        tip, repo, role = tips[sid]
        preds = [(p, tips[p][0]) for p in tree.predecessors(lines["plan"], sid) if p in tips and tips[p][2] == role]
        if not preds:
            continue
        waits = next((p for p, _ in preds if p in pending), "")
        if waits:                                        # it would ask to settle what its predecessor is about to change, and
            pending[sid] = {**pending[waits], "with": waits, "waits": True, "tip": tip}   # move twice: pictures SP-6 x SP-5
            pending[sid].update(files=[], missing=[], keys=[])
            continue
        done = tree.fold(repo, tip, preds, tree.try_ref(lines, role, sid), lines.get("resolutions"), request=True)
        conflict = done["conflict"]
        if conflict:
            before = data["subplans"].get(sid) or {}
            pending[sid] = {"with": conflict["with"], "files": conflict.get("files") or [],
                            "missing": conflict.get("missing") or [], "keys": conflict.get("keys") or [],
                            "error": conflict.get("error") or "", "tip": tip,
                            "since": before.get("since") if before.get("with") == conflict["with"] else _iso(now())}
            for key in pending[sid]["keys"]:
                out["bound"].setdefault(key, {"run_id": run.run_id, "subplan": sid, "with": conflict["with"]})
            continue
        new = done["commit"]
        if new == tip:
            continue
        ref = (f"refs/bt/subplan/{tree._SAFE_REF.sub('-', run.project)}/{run.req}/r{run.revision}/"
               f"{tree._SAFE_REF.sub('-', role)}/{tree._SAFE_REF.sub('-', sid)}")
        moved = subprocess.run(["git", "-C", str(repo), "update-ref", ref, new, tip], capture_output=True, text=True, check=False)
        if moved.returncode:                             # an integration moved it first: the next pass folds the new tip
            LOG.info("reconcile: %s moved while folding: %s", ref, moved.stderr.strip()[:200])
            continue
        tips[sid] = (new, repo, role)
        data["moved"].setdefault(sid, []).append({"from": tip, "to": new, "at": _iso(now()), "offered": sid in built})
        out["moved"].append(sid)
        if emit:
            emit("subplan_reconciled", run_id=run.run_id, subplan=sid, previous=tip, commit=new,
                 includes=list(done.get("includes") or ()))
        record(rdir, f"{sid}: su línea ya incluye la versión actual de {', '.join(p for p, _ in preds)}")
    cleared = set(data["subplans"]) - set(pending)
    if pending != data["subplans"] or out["moved"]:
        data["dirty"] = bool(data.get("dirty") or out["moved"] or cleared)
        data["subplans"], data["run_id"], data["at"] = pending, run.run_id, _iso(now())
        _save(root, run.project, run.req, data)
    if data.get("dirty") and client is not None:
        digest = hashlib.sha256(json.dumps(sorted((s, t[0]) for s, t in tips.items())).encode()).hexdigest()[:24]
        try:
            client.command(run, "recheck_gates", request_id=f"reconcile-{digest}", by="reconcile")
        except Exception as error:  # noqa: BLE001 - e.g. the system database briefly away: told on the next pass
            LOG.warning("reconcile: %s not told: %s", run.run_id, error)
        else:
            data["dirty"] = False
            _save(root, run.project, run.req, data)
    out["pending"] = pending
    return out


def wanted(rdir: Path, status: dict) -> bool:
    """Not a finished plan: a run that completed with every subplan approved (or none to approve) has nothing to keep up
    with, and an old requirement must not start sessions."""
    if ((status.get("summary") or {}).get("status")) != "completed":
        return True
    import bt_verification as verification
    state = verification.state(rdir)
    return bool(state["applies"]) and state["approved"] != state["total"]


def problems(run, pending: dict[str, dict]) -> list[dict]:
    """A subplan that cannot be combined and has no request to answer (git failed, the rules did not apply): nothing else
    would ever look at it, so it goes to the Solucionador as it is."""
    from .solver_triggers import trigger
    out = []
    for sid, entry in pending.items():
        if entry.get("keys") or entry.get("waits"):
            continue
        basis = json.dumps([sid, entry.get("with"), entry.get("error"), entry.get("files")], sort_keys=True)
        item = trigger("reconcile", f"{run.run_id}:reconcile:{hashlib.sha256(basis.encode()).hexdigest()[:16]}", run.run_id,
                       reason=f"{sid} builds on {entry.get('with')} and cannot be combined with its current line, and there "
                              f"is no resolution request to answer: {entry.get('error') or entry.get('files')}")
        item["subplan"] = f"{sid}×{entry.get('with')}"
        out.append(item)
    return out


def view(rdir: Path, sid: str) -> dict:
    """What the panel says about a subplan whose tree lacks a predecessor: {"state": working | queued | escalated | off |
    unattended | building, "session", "since", "question"}. Facts only: a trigger's status, never a guess."""
    rdir = Path(rdir)
    root, project = rdir.parent.parent.parent, rdir.parent.parent.name
    entries = load(root, project, "-".join(rdir.name.split("-")[:2]))["subplans"]
    entry = entries.get(sid)
    if not enabled():
        return {"state": "off"}
    if entry is None:
        return {"state": "unattended"}
    while entry.get("waits") and entries.get(entry.get("with")):    # what it waits for is what the panel can tell about
        sid, entry = entry["with"], entries[entry["with"]]
    try:
        state = json.loads((rdir / "RUN.solver" / "state.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    wanted = {f":resolution:{key}" for key in entry.get("keys") or ()}
    found = [t for name, t in (state.get("triggers") or {}).items() if isinstance(t, dict) and
             (any(name.endswith(end) for end in wanted) or
              (not wanted and t.get("kind") == "reconcile" and str(t.get("subplan") or "").startswith(f"{sid}×")))]
    statuses = {str(t.get("status")) for t in found}
    out = {"since": entry.get("since") or ""}
    if statuses & WORKING:
        session = next((t.get("session") for t in found if t.get("status") in WORKING and t.get("session")), "")
        started = next((s.get("started_at") for s in state.get("sessions") or () if s.get("id") == session), "")
        return {**out, "state": "working", "session": session, "since": started or out["since"]}
    if statuses & ESCALATED:
        question = next((s.get("question") or s.get("summary") or "" for s in reversed(state.get("sessions") or ())
                         if s.get("status") in ESCALATED), "")
        return {**out, "state": "escalated", "question": str(question)[:300]}
    return {**out, "state": "queued"}
