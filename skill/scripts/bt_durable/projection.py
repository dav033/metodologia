"""The panels' read model of one durable run (REQ-030 M7): derived only from DBOS, rebuildable at any time.

`build` reads the run's workflows (statuses, inputs, outputs) and the `summary`/`state`/`decision` events from the DBOS
system database, through a DBOSClient (operator CLI) or the launched DBOS class (engine), and returns one JSON
document; `write` stores it atomically (0600 file, 0700 directories) where the stdlib panels read it
(`bt_durable_panel.path`). It is a projection, not a second source of truth: no workflow reads it, a missing or
damaged file is rebuilt from DBOS, and every remote command is checked against a fresh build before it is sent.

The previous file is read only to carry the monotonic `sequence`: it grows by one whenever the derived content
changes, and a rebuild without a previous file starts from the current time in milliseconds, so a sequence is never
reused. `status_seq`, `tasks[].seq` and `decisions[].seq` record the sequence at which that subject last changed.
"""
from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import re
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import bt_durable_panel as panel
from bt_contracts.execution import RunRef

RUN, TASK, AGENT, VERIFY, INTEGRATE = "bt.run", "bt.task", "bt.agent", "bt.verify", "bt.integrate"
LIVE = ("PENDING", "ENQUEUED", "DELAYED")
FAILED = ("ERROR", "MAX_RECOVERY_ATTEMPTS_EXCEEDED")
HISTORY = 10
_KEY = re.compile(r"[^A-Za-z0-9._-]+")
_ATTEMPT = re.compile(r"^(?P<task>.+)-a(?P<number>\d+)-[0-9a-f]{8}$")
_SKIP = ("sequence", "status_seq", "seq", "projected_at")


# ----------------------------------------------------------------------------------------------------- build
def build(source, run: RunRef, plan=None) -> dict[str, Any]:
    """The projection content of `run` (without sequences). `source` has DBOS's `list_workflows` and `get_event`;
    `plan` is the run's validated Plan when available (it tells queued from pending work)."""
    run_wid = f"bt:{run.run_id}"
    rows = source.list_workflows(workflow_id_prefix=run_wid, load_input=False, load_output=True)
    # the run's current incarnation: `bt:<run>`, or `bt:<run>@N` after `bt-durable reopen` forked it
    incarnations = [r for r in rows if r.workflow_id == run_wid or (r.workflow_id.startswith(run_wid + "@")
                                                                     and r.workflow_id.rsplit("@", 1)[1].isdigit())]
    run_row = max(incarnations, key=lambda r: int(r.workflow_id.rsplit("@", 1)[1]) if "@" in r.workflow_id else 1,
                  default=None)
    summary = _event(source, run_row.workflow_id, "summary") if run_row else None
    summary = summary if isinstance(summary, dict) else {}
    summary_tasks = summary.get("tasks") if isinstance(summary.get("tasks"), dict) else {}
    summary_results = summary.get("results") if isinstance(summary.get("results"), dict) else {}
    rounds: dict[str, list] = {}
    for row in rows:
        if row.name == TASK and row.workflow_id.startswith(run_wid + ":"):
            task_id, _, k = row.workflow_id[len(run_wid) + 1:].rpartition(":k")
            if task_id and k.isdigit():
                rounds.setdefault(task_id, []).append((int(k), row))
    attempts = _attempts(source, run)
    order = [t.id for t in plan.tasks] if plan is not None else []
    order += sorted((set(summary_tasks) | set(rounds) | set(attempts)) - set(order))
    tasks, decisions = [], []
    for task_id in order:
        task, decision = _task(source, task_id, rounds.get(task_id, []), summary_tasks.get(task_id),
                               attempts.get(task_id, []))
        _audit_hold(task, summary_tasks.get(task_id), summary_results.get(task_id))
        tasks.append(task)
        if decision:
            decisions.append(decision)
    if plan is not None:
        _queue(plan, tasks, summary_tasks)
    status = _run_status(run_row, summary)
    counts: dict[str, int] = {}
    for task in tasks:
        counts[task["state"]] = counts.get(task["state"], 0) + 1
    return {"schema": panel.SCHEMA, "projection": True, "authority": panel.AUTHORITY, "project": run.project,
            "req": run.req, "run_id": run.run_id, "workflow_id": run_row.workflow_id if run_row else run_wid,
            "plan_ref": {"plan_id": run.plan_id, "revision": run.revision, "sha256": run.plan_sha256},
            "workflow_status": run_row.status if run_row else None, "status": status,
            "paused": summary.get("status") == "paused", "counts": counts, "tasks": tasks, "decisions": decisions}


def _event(source, workflow_id: str, key: str) -> Any:
    return source.get_event(workflow_id, key, timeout_seconds=0)


def _run_status(row, summary: dict) -> str:
    if row is None:
        return "unknown"
    if row.status in LIVE:
        return "paused" if summary.get("status") == "paused" else "running"
    if row.status == "CANCELLED":
        return "cancelled"
    if row.status in FAILED:
        return "failed"
    final = summary.get("status") or (row.output.get("status") if isinstance(row.output, dict) else None)
    return "completed" if final == "completed" else "blocked"


def _task(source, task_id: str, rounds: list, summary_state: str | None, attempts: list) -> tuple[dict, dict | None]:
    """One task: its latest round's workflow decides; the run summary covers inherited and not-started tasks."""
    task: dict[str, Any] = {"id": task_id, "state": "pending", "round": None, "workflow_id": None,
                            "workflow_status": None, "durable_state": None, "attempt": None, "until": None,
                            "decision_id": None, "outcome": None, "limit_hit": None, "attempts": 0}
    decision = None
    if rounds:
        k, row = max(rounds, key=lambda item: item[0])
        task.update(round=k, workflow_id=row.workflow_id, workflow_status=row.status)
        if row.status in LIVE:
            event = _event(source, row.workflow_id, "state")
            event = event if isinstance(event, dict) else {}
            durable = event.get("state") or ("queued" if row.status != "PENDING" else "routing")
            task.update(durable_state=durable, attempt=event.get("attempt"), until=event.get("until"))
            task["state"] = {"routing": "queued", "queued": "queued", "waiting_quota": "waiting_quota",
                             "running": "running", "recovering": "recovering", "reconciling": "verifying",
                             "needs_decision": "needs_decision", "completed": "completed",
                             "inherited": "completed", "blocked": "blocked",
                             "cancelled": "cancelled"}.get(durable, "running")
            if durable == "needs_decision":
                request = _event(source, row.workflow_id, "decision")
                if isinstance(request, dict) and request.get("request_id"):
                    decision = _decision(task_id, k, row.workflow_id, request, task["attempt"] or
                                         (attempts[-1]["id"] if attempts else None))
                    task.update(decision_id=decision["id"], limit_hit=decision["limit_hit"] or None)
        elif row.status == "SUCCESS":
            output = row.output if isinstance(row.output, dict) else {}
            task["outcome"] = output.get("status")
            closed = output.get("decision") if isinstance(output.get("decision"), dict) else {}
            task["limit_hit"] = closed.get("limit_hit") or None
            task["state"] = {"completed": "completed", "inherited": "completed", "blocked": "blocked",
                             "cancelled": "cancelled"}.get(output.get("status"), "blocked")
        elif row.status == "CANCELLED":
            task["state"] = "cancelled"
        else:
            task["state"] = "failed"
    elif summary_state in ("inherited", "completed"):
        task.update(state="completed", outcome=summary_state)
    elif summary_state in ("blocked", "cancelled"):
        task.update(state=summary_state, outcome=summary_state)
    if task["state"] == "running" and attempts and attempts[-1]["state"] in ("verifying", "reserved"):
        task["state"] = "verifying" if attempts[-1]["state"] == "verifying" else "queued"
    task["attempts"] = len(attempts)
    # attempt numbers are (round - 1) * 100 + n: what the current round spent of its budget
    task["round_attempts"] = sum(1 for a in attempts if task["round"] and (a["number"] - 1) // 100 + 1 == task["round"]
                                 and a["number"] % 100 != 99)
    task["history"] = attempts[-HISTORY:]
    return task, decision


def _audit_hold(task: dict, summary_state: str | None, result: Any) -> None:
    """A milestone audit (REQ-030 item 4) ends its round completed, but the run holds it while its blocking findings
    are repaired (`remediating`) or once its remediation rounds ran out (`blocked`): the run decides, not the round."""
    if task["state"] != "completed" or summary_state not in ("remediating", "blocked"):
        return
    reason = result.get("audit") if isinstance(result, dict) else None
    task.update(state="recovering" if summary_state == "remediating" else "blocked", durable_state=summary_state,
                outcome=summary_state, audit=str(reason)[:1000] if reason else None)


def _decision(task_id: str, k: int, workflow_id: str, request: dict, attempt: str | None) -> dict:
    failure = request.get("failure") if isinstance(request.get("failure"), dict) else {}
    keep = ("failure_class", "code", "summary", "agent_note")
    return {"id": f"{request['request_id']}@k{k}", "request_id": request["request_id"], "task_id": task_id,
            "round": k, "workflow_id": workflow_id, "attempt": attempt, "reason": str(request.get("reason") or "")[:1000],
            "limit_hit": request.get("limit_hit"),
            "failure": {name: str(failure[name])[:2000] for name in keep if failure.get(name) is not None},
            "options": [o for o in request.get("options") or [] if isinstance(o, str)],
            "verify_attempt": str(request.get("verify_attempt") or "") or None}   # the snapshot a receipt binds to


def _queue(plan, tasks: list[dict], summary_tasks: dict) -> None:
    """Not-started tasks whose dependencies are done are queued (waiting for a slot, a resource or a resume)."""
    done = {t["id"] for t in tasks if t["state"] == "completed"} | \
        {tid for tid, state in summary_tasks.items() if state in ("completed", "inherited")}
    after = {spec.id: tuple(spec.after) for spec in plan.tasks}
    for task in tasks:
        if task["state"] == "pending" and task["round"] is None and set(after.get(task["id"], ())) <= done:
            task["state"] = "queued"


# -------------------------------------------------------------------------------------------------- attempts
def _attempts(source, run: RunRef) -> dict[str, list[dict]]:
    """Each attempt from its agent / verify / integrate workflows (`bt:<attempt key>:<kind>`), grouped by task."""
    prefix = "bt:" + _KEY.sub("-", f"{run.project}-{run.req}-r{run.revision}-")
    by_key: dict[str, dict[str, Any]] = {}
    for row in source.list_workflows(workflow_id_prefix=prefix, load_input=True, load_output=True):
        key = row.workflow_id[3:].partition(":")[0]
        slot = by_key.setdefault(key, {"verify": []})
        if row.name == AGENT:
            slot["agent"] = row
        elif row.name == VERIFY:
            slot["verify"].append(row)
        elif row.name == INTEGRATE and ("integrate" not in slot or
                                       (row.created_at or 0) > (slot["integrate"].created_at or 0)):
            slot["integrate"] = row
    out: dict[str, list[dict]] = {}
    for key, slot in by_key.items():
        identity = _identity(key, slot)
        if identity is None:
            continue
        out.setdefault(identity[0], []).append(_attempt(key, identity[1], slot))
    for items in out.values():
        items.sort(key=lambda item: (item["started_at"] or 0, item["number"]))
    return out


def _identity(key: str, slot: dict) -> tuple[str, int] | None:
    for row in [slot.get("agent"), *slot["verify"]]:
        args = (getattr(row, "input", None) or {}).get("args") if row is not None else None
        if args and isinstance(args[0], dict) and args[0].get("task_id"):
            return str(args[0]["task_id"]), int(args[0].get("number") or 0)
    match = _ATTEMPT.match(key)
    return (match["task"], int(match["number"])) if match else None


def _attempt(key: str, number: int, slot: dict) -> dict[str, Any]:
    agent, integrate = slot.get("agent"), slot.get("integrate")
    verifies = sorted(slot["verify"], key=lambda r: r.created_at or 0)
    verify = verifies[-1] if verifies else None
    rows = [r for r in (agent, *verifies, integrate) if r is not None]
    route: dict = {}
    if agent is not None:
        args = (agent.input or {}).get("args") or ()
        route = args[1] if len(args) > 1 and isinstance(args[1], dict) else {}
    output = agent.output if agent is not None and isinstance(agent.output, dict) else {}
    verdict = verify.output if verify is not None and isinstance(verify.output, dict) else {}
    merged = integrate.output if integrate is not None and isinstance(integrate.output, dict) else {}
    failure = None
    if integrate is not None and integrate.status in LIVE:
        state = "verifying"
    elif merged.get("ref") and not merged.get("conflict") and not merged.get("internal_error"):
        state = "accepted"
    elif verify is not None and verify.status in LIVE:
        state = "verifying"
    elif agent is not None and agent.status == "ENQUEUED":
        state = "reserved"
    elif agent is not None and agent.status in LIVE:
        state = "running"
    elif any(r.status == "CANCELLED" for r in rows):
        state = "cancelled"
    elif verdict.get("status") == "FAIL":
        state, failure = "rejected", verdict.get("reason_code")
    elif merged.get("conflict"):
        state, failure = "rejected", "INTEGRATION_CONFLICT"
    elif verify is None and agent is not None and agent.status == "SUCCESS" and not _ended(output):
        state = "verifying"                                  # the snapshot is being handed to verification
    else:
        state = "failed"
        failure = (verdict.get("reason_code") or output.get("start_error") or output.get("internal_error")
                   or (output.get("agent") or {}).get("status") or (rows[-1].status if rows else None))
    started = min((r.created_at for r in rows if r.created_at), default=None)
    updated = max((r.updated_at for r in rows if r.updated_at), default=None)
    live = state in ("running", "verifying", "reserved")
    ended = None if live else updated
    return {"id": key, "number": number, "state": state, "provider": route.get("provider"),
            "model": route.get("model"), "profile": route.get("profile") or None, "effort": route.get("effort") or None,
            "started_at": started / 1000 if started else None, "ended_at": ended / 1000 if ended else None,
            "updated_at": updated / 1000 if updated else None, "live": live,
            "duration_s": round((ended - started) / 1000, 1) if ended and started else None,
            "verdict": verdict.get("status"), "failure": str(failure)[:200] if failure else None}


def _ended(output: dict) -> bool:
    """An agent result that will not be verified: refused start, internal error, or cut short (limit/timeout)."""
    agent = output.get("agent") if isinstance(output.get("agent"), dict) else {}
    return bool(output.get("start_error") or output.get("internal_error")
                or agent.get("status") in ("limit", "timeout", "cancelled") or not output.get("snapshot"))


# ----------------------------------------------------------------------------------------------- sequences
def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(_strip(value), sort_keys=True, default=str).encode()).hexdigest()


def _strip(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _strip(v) for k, v in value.items() if k not in _SKIP}
    if isinstance(value, list):
        return [_strip(v) for v in value]
    return value


def sequence(content: dict, previous: dict | None, now: float) -> dict:
    """Stamp `content` with the projection sequence and each subject's last-change sequence."""
    prev_seq = previous.get("sequence") if isinstance(previous, dict) and type(previous.get("sequence")) is int else None
    if prev_seq is not None and previous.get("digest") == digest(content):
        return previous                                           # nothing changed: same document, same sequence
    seq = prev_seq + 1 if prev_seq is not None else int(now * 1000)
    old = previous if prev_seq is not None else {}
    out = {**content, "sequence": seq, "projected_at": now, "digest": digest(content)}
    same_status = (old.get("status"), old.get("workflow_status")) == (content["status"], content["workflow_status"])
    out["status_seq"] = old.get("status_seq", seq) if same_status else seq
    out["tasks"] = _stamp(content["tasks"], old.get("tasks"), seq)
    out["decisions"] = _stamp(content["decisions"], old.get("decisions"), seq)
    return out


def _stamp(items: list[dict], previous: Any, seq: int) -> list[dict]:
    """A task keeps its `seq` while its control-relevant view (state, round, decision, outcome) is unchanged."""
    before = {p.get("id"): p for p in previous or [] if isinstance(p, dict)}
    out = []
    for item in items:
        old = before.get(item["id"])
        same = old is not None and _control(old) == _control(item) and type(old.get("seq")) is int
        out.append({**item, "seq": old["seq"] if same else seq})
    return out


def _control(item: dict) -> tuple:
    return tuple(item.get(k) for k in ("state", "round", "decision_id", "outcome", "request_id", "workflow_status"))


# ----------------------------------------------------------------------------------------------------- store
def requirement_dir(run: RunRef) -> Path:
    return Path(run.plan_path).parent.parent                     # <req dir>/plan-revisions/PLAN.rN.json


def target(run: RunRef) -> Path:
    return panel.path(requirement_dir(run), run.run_id)


@contextlib.contextmanager
def locked(path: Path) -> Iterator[None]:
    """One projector at a time per run: read DBOS, compare with the previous file and write, in that order."""
    _private_dirs(path.parent)
    fd = os.open(path.with_name(f".{path.name}.lock"), os.O_CREAT | os.O_RDWR | os.O_CLOEXEC, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def _private_dirs(folder: Path) -> None:
    """Create the missing directories 0700, like the rest of `<root>/.state` (existing ones keep their mode)."""
    missing = []
    probe = folder
    while not probe.exists():
        missing.append(probe)
        probe = probe.parent
    for item in reversed(missing):
        item.mkdir(mode=0o700, exist_ok=True)
        item.chmod(0o700)


def previous(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) and data.get("schema") == panel.SCHEMA else None


def write(path: Path, document: dict) -> None:
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    fd = os.open(tmp, os.O_CREAT | os.O_TRUNC | os.O_WRONLY | os.O_CLOEXEC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(json.dumps(document, indent=1, sort_keys=True, ensure_ascii=False, default=str) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)


def project(source, run: RunRef, plan=None, *, now: float | None = None) -> dict:
    """Rebuild, sequence and store the projection of `run`; returns the stored document."""
    if not requirement_dir(run).is_dir():
        raise FileNotFoundError(f"{run.run_id}: its requirement folder is gone; nothing to project into")
    path = target(run)
    with locked(path):
        content = build(source, run, plan)
        before = previous(path)
        document = sequence(content, before, time.time() if now is None else now)
        if document is not before:
            write(path, document)
        return document


def load_plan(run: RunRef):
    """The run's validated plan from its frozen file, or None when it cannot be read (queued is then not told)."""
    from .legacy import load_plan as load
    try:
        return load(Path(run.plan_path).read_text(encoding="utf-8"), approved_sha256=run.plan_sha256,
                    plan_id=run.plan_id, revision=run.revision)
    except Exception:  # noqa: BLE001 - the projection still shows every started task
        return None


def _announce(run: RunRef) -> None:
    """Tell the owner when a subplan version the composer published is ready to test in «Probar» (the legacy Scheduler
    does it after writing its projection); never fails the pass."""
    try:
        import bt_verification
        bt_verification.on_projection(requirement_dir(run))
    except Exception:  # noqa: BLE001 - observing a run must never break it
        pass


def _current_run_id(rdir: Path) -> str:
    """The run the requirement points at now (`RUN.durable-run.json`), or "" when it cannot be read."""
    try:
        return RunRef.model_validate_json((Path(rdir) / "RUN.durable-run.json").read_text(encoding="utf-8")).run_id
    except (OSError, ValueError):
        return ""


def _announce_blocked(source, workflow_id: str, run: RunRef, plan) -> None:
    """A run that settled blocked because composition gates were rejected tells the owner once what stopped it and what
    to press (pictures REQ-021 r19 settled blocked with CG-3, CG-5 and CG-6 rejected and no decision to answer). Only for
    the requirement's current run: every engine start projects each settled run once more, and r19's and r24's old
    rejections were announced again at each restart of 2026-10-30 while r25 ran with every gate composed (D-192). Never
    fails the pass."""
    try:
        summary = _event(source, workflow_id, "summary") or {}
        rejected = dict(sorted(((summary.get("gates") or {}).get("rejected") or {}).items()))
        if not rejected:
            return
        rdir = requirement_dir(run)
        if _current_run_id(rdir) not in ("", run.run_id):
            return                       # an earlier run of the requirement: what stopped it is history (D-192)
        marker = rdir / "RUN.blocked-notice.json"
        key = {"run_id": run.run_id, "rejected": rejected}
        try:
            if json.loads(marker.read_text(encoding="utf-8")) == key:
                return
        except (OSError, ValueError):
            pass
        tasks = {gate.id: gate.task for gate in (getattr(plan, "composition_gates", None) or ())}
        folder = Path(os.environ.get("BITACORA_ROOT") or Path.home() / "bitacora") / ".state" / "durable" / "composition" / "resolutions"
        pending = sorted(p.with_suffix(".diff3").name for p in folder.glob("*.json") if not p.with_suffix(".resolved").exists())
        gates = ", ".join(f"{g} ({tasks.get(g, '?')})" for g in rejected)
        text = (f"El run se detuvo: la composición de {gates} tiene conflictos de texto entre subplanes. "
                + (f"Cada conflicto está en {folder}: {', '.join(pending[:4])}; escribe el contenido final del archivo en el "
                   f".resolved de la misma clave y pulsa «Reintentar» en la tarea de la puerta." if pending else
                   "Pulsa «Reintentar» en la tarea de la puerta para componerla otra vez."))
        import bt_planning_activity as activity
        import bt_runutil
        activity.record(rdir, "Motor", text[:600], kind="flow")
        bt_runutil.notify("El run se detuvo", text[:300])
        marker.write_text(json.dumps(key, sort_keys=True) + "\n", encoding="utf-8")
    except Exception:  # noqa: BLE001 - observing a run must never break it
        pass


class EngineProjector:
    """The engine's periodic refresh: live runs every pass, a finished run once more after it settles."""

    def __init__(self, source):
        self.source = source
        self._plans: dict[str, Any] = {}
        self._settled: dict[str, str] = {}

    def refresh(self) -> list[str]:
        written = []
        for row in self.source.list_workflows(name=RUN, load_input=True, load_output=False):
            if row.status not in LIVE and self._settled.get(row.workflow_id) == row.status:
                continue
            args = (row.input or {}).get("args") or ()
            try:
                run = RunRef.model_validate(args[0])
            except (IndexError, ValueError):
                continue
            if not requirement_dir(run).is_dir():
                self._settled[row.workflow_id] = row.status
                continue
            if run.run_id not in self._plans:
                self._plans[run.run_id] = load_plan(run)
            document = project(self.source, run, self._plans[run.run_id])
            _announce(run)
            if document.get("status") == "blocked":
                _announce_blocked(self.source, row.workflow_id, run, self._plans[run.run_id])
            if row.status not in LIVE:
                self._settled[row.workflow_id] = row.status
            written.append(run.run_id)
        return written
