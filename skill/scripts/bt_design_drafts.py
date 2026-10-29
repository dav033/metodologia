"""Planning-time design drafts: the Designer works on each UI subplan while the owner and the Planner talk.

Drafts live in the requirement folder, never in a project repository: `design/<contract>@v<N>.md` (the contract) and
`design/<contract>@v<N>.html` (a static mockup), with their state in `design/drafts.json`. A plan change reaching the
UI brief amends an owner-chosen design (bt_design_amend); directions are regenerated only before a choice or on request. Approving the plan approves every ready draft
(bt_design_approval pins its SHA-256), and the execution-time `design` task copies it byte for byte into the
repository, so the M3 gate finds the approved blob and UI work does not pause.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import tempfile
import time
from contextlib import contextmanager, suppress
from pathlib import Path

DIR = "design"
FILE = "drafts.json"
TIMEOUT_MIN = 40
DEBOUNCE_SEC = 45          # a subplan still being edited in the conversation is not redesigned on every keystroke
STALE_GRACE_SEC = 15 * 60  # a delegation that never wrote its outcome is declared failed after its timeout plus this
QUEUED_TTL_SEC = 10 * 60  # a draft queued by a process that died before starting the Designer
FAIL_BACKOFF_SEC = 10 * 60  # a failed draft is not retried by `sync` sooner (no account, usage limits)
MAX_AUTO_RUNS = 8         # redesigns `sync` may start per contract on its own; explicit requests are not capped
MAX_FAILURES = 3          # consecutive failures after which only an explicit request starts the Designer again
MIN_SECTIONS = 10         # a contract has twelve `##` sections; fewer means the Designer did not finish it
PLANNING = ("draft", "clarifying", "ready", "planned", "review", "changes-requested", "?")
SKILL_ROOT = Path(__file__).resolve().parent.parent
KIT = SKILL_ROOT / "agents/designer/skills/david-ui-kit/kit"   # the Designer's david-ui stand-in kit (D-135)
ACTIVE = ("queued", "drafting", "amending")
DEFAULT_DIRECTIONS = 3
_REF = re.compile(r"[a-z0-9][a-z0-9-]{0,63}@v[1-9][0-9]{0,5}\Z")


def _now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def _plan(rdir: Path) -> dict:
    try:
        data = json.loads((Path(rdir) / "PLAN.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return {}  # a PLAN.json mid-edit in the conversation is simply not visible yet
    return data if isinstance(data, dict) else {}


def subplans(rdir: Path) -> list[dict]:
    """Every subplan of PLAN.json with its tasks; `ref` is set for UI subplans (`<contract>@v<N>`)."""
    plan = _plan(rdir)
    tasks = [t for t in plan.get("tasks") or [] if isinstance(t, dict)]
    out = []
    for item in plan.get("subplans") or []:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        own = [t for t in tasks if t.get("subplan_id") == item["id"]]
        ui = item.get("ui") if isinstance(item.get("ui"), dict) else None
        ref = (f"{ui['contract']}@v{ui['version']}" if ui and isinstance(ui.get("contract"), str)
               and type(ui.get("version")) is int else None)
        ref = ref if ref and _REF.match(ref) else None  # the ref names files: never a path outside design/
        row = {"id": item["id"], "title": item.get("title") or "", "outcome": item.get("outcome") or "",
               "covers": item.get("covers") or [], "criteria": item.get("acceptance_criteria") or [],
               "ui": ui, "ref": ref, "tasks": own, "digest": _digest(item, own),
               "ui_brief": item.get("ui_brief") if isinstance(item.get("ui_brief"), dict) else None}
        row["ui_digest"] = __import__("bt_design_ui_brief").digest(rdir, row) if ref else None
        out.append(row)
    return out


def behind(entry: dict, row: dict) -> bool:
    """The draft was built from another UI brief than the current one; entries recorded before `ui_digest` existed
    compare the whole-subplan `digest` as they always did."""
    if entry.get("ui_digest"):
        return entry["ui_digest"] != row.get("ui_digest")
    return entry.get("digest") != row.get("digest")


def _digest(subplan: dict, tasks: list[dict]) -> str:
    """What the Designer depends on: the subplan and the user-facing parts of its tasks."""
    keep = ("id", "title", "objective", "kind", "ui", "acceptance_criteria")
    payload = {"subplan": subplan, "tasks": [{k: t.get(k) for k in keep} for t in tasks]}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def paths(rdir: Path, ref: str) -> tuple[Path, Path]:
    base = Path(rdir) / DIR
    return base / f"{ref}.md", base / f"{ref}.html"


def active(rdir: Path) -> bool:
    """Planning-time design is on for this requirement once a draft was ever requested."""
    return (Path(rdir) / DIR / FILE).is_file()


def _load(rdir: Path) -> dict:
    try:
        data = json.loads((Path(rdir) / DIR / FILE).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        data = {}
    if not isinstance(data, dict) or not isinstance(data.get("drafts"), dict):
        data = {"schema_version": 1, "drafts": {}}
    return data


def states(rdir: Path) -> dict[str, str]:
    """ref → draft status as last recorded; read-only (no settling, no lock), for status pages."""
    return {ref: str(entry.get("status") or "none") for ref, entry in _load(rdir)["drafts"].items()
            if isinstance(entry, dict)}


def _save(rdir: Path, data: dict) -> None:
    target = Path(rdir) / DIR / FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{FILE}.", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=1, sort_keys=True)
            stream.write("\n")
        os.replace(tmp, target)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


@contextmanager
def _locked(rdir: Path):
    """One read-modify-write of drafts.json at a time (web threads, CLI and the HQ session share it)."""
    target = Path(rdir) / DIR / f".{FILE}.lock"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a+b") as handle:
        try:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        except (ImportError, OSError):
            pass
        data = _load(rdir)
        before = json.dumps(data, sort_keys=True)
        yield data
        if before != json.dumps(data, sort_keys=True) or not (Path(rdir) / DIR / FILE).is_file():
            _save(rdir, data)  # a page poll that only reads must not rewrite the file


def _sha(file: Path) -> str | None:
    try:
        return hashlib.sha256(file.read_bytes()).hexdigest()
    except OSError:
        return None


def _age(stamp: str | None) -> float:
    try:
        return time.time() - dt.datetime.fromisoformat(stamp).timestamp() if stamp else 0.0
    except ValueError:
        return 0.0


def _settle(rdir: Path, ref: str, entry: dict) -> None:
    """Fold a finished delegation into its draft entry (lazy: called whenever drafts are read)."""
    if entry.get("status") == "amending":
        import bt_design_amend
        return bt_design_amend.settle(rdir, ref, entry)
    if entry.get("phase"):
        import bt_design_directions
        return bt_design_directions.settle(rdir, ref, entry)
    import bt_delegate
    did = entry.get("delegation")
    if entry.get("status") == "queued" and _age(entry.get("queued")) > QUEUED_TTL_SEC:
        entry.update({"status": "failed", "error": "the Designer never started", "finished": _now()})
        return
    if entry.get("status") != "drafting" or not did:
        return
    try:
        outcome = bt_delegate.summary(did)
    except SystemExit:
        outcome = {"status": "failed", "summary": "delegation record is missing"}
    except (OSError, ValueError):  # OUTCOME.json being written right now: settle on the next read
        return
    if outcome.get("status") == "running_or_pending":
        started = dt.datetime.fromisoformat(entry.get("started") or _now()).timestamp()
        if time.time() - started < TIMEOUT_MIN * 60 + STALE_GRACE_SEC:
            return
        outcome = {"status": "failed", "summary": "the Designer session ended without a result"}
    report = {}
    if outcome.get("result_file"):
        try:
            report = json.loads(Path(outcome["result_file"]).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError):
            report = {}
    md, html = paths(rdir, ref)
    # a redesign must rewrite the contract: an untouched previous draft is not this session's result
    written = md.is_file() and md.stat().st_size > 0 and _sha(md) != entry.get("before")
    if written and sum(1 for line in md.read_text(encoding="utf-8", errors="replace").splitlines()
                       if line.startswith("## ")) < MIN_SECTIONS:
        written, outcome = False, {**outcome, "status": "incomplete",
                                   "summary": f"the contract has fewer than {MIN_SECTIONS} sections"}
    entry["finished"] = _now()
    entry["summary"] = str(outcome.get("summary") or "")[:600]
    entry["questions"] = [line.strip()[2:].strip() for line in str(report.get("notes") or "").splitlines()
                          if line.strip().upper().startswith("Q:")]
    if outcome.get("status") in ("claimed", "verified", "partial", "blocked") and written:
        entry["status"] = "ready"
        entry["sha256"] = _sha(md)
        entry["mockup"] = html.is_file()
        entry["error"] = ""  # `partial` here usually means "draft, not approved yet": that is the planning state
        entry["report"] = outcome.get("status")
        entry["revision"] = int(entry.get("revision") or 0) + 1
        entry["failures"] = 0
        _archive(rdir, ref, entry["revision"])
        entry.setdefault("history", []).append({"rev": entry["revision"], "at": entry["finished"],
                                                "summary": entry["summary"]})
        _event(rdir, "Designer", f"{ref} · borrador {entry['revision']} listo", entry)
    else:
        entry["status"] = "failed"
        entry["failures"] = int(entry.get("failures") or 0) + 1
        entry["error"] = f"{outcome.get('status')}: {entry['summary'] or 'the contract was not written'}"[:600]
        for item in entry.get("feedback", []):  # the owner's comments were not applied: they stay pending
            if item.get("consumed") == did:
                item.pop("consumed")
        _event(rdir, "Designer", f"{ref} · el diseño falló: {entry['error'][:120]}", entry)


def _event(rdir: Path, who: str, text: str, entry: dict, kind: str = "design") -> None:
    import bt_planning_activity
    bt_planning_activity.record(rdir, who, text, kind=kind, sp=entry.get("subplan_id") or "")


def _archive(rdir: Path, ref: str, rev: int) -> None:
    """Keep each finished revision (`design/history/<ref>/r<N>.md|.html`) so the owner can compare versions."""
    target = Path(rdir) / DIR / "history" / ref
    target.mkdir(parents=True, exist_ok=True)
    for source, suffix in zip(paths(rdir, ref), (".md", ".html"), strict=True):
        if source.is_file():
            (target / f"r{rev}{suffix}").write_bytes(source.read_bytes())


def revision_file(rdir: Path, ref: str, rev: int | None, suffix: str) -> Path:
    """The draft file of revision `rev` (the current one when `rev` is None or the latest)."""
    if rev:
        archived = Path(rdir) / DIR / "history" / ref / f"r{int(rev)}{suffix}"
        if archived.is_file():
            return archived
    return paths(rdir, ref)[0 if suffix == ".md" else 1]


def rows(rdir: Path) -> list[dict]:
    """UI subplans joined with their draft state; settles finished Designer sessions on the way."""
    if not active(rdir):
        return [{**s, "status": "none", "stale": False, "feedback": [], "pending_feedback": 0}
                for s in subplans(rdir) if s["ref"]]
    with _locked(rdir) as data:
        return _rows(rdir, data)


def _rows(rdir: Path, data: dict) -> list[dict]:
    """`rows` over drafts.json already loaded under the lock."""
    ui = [s for s in subplans(rdir) if s["ref"]]
    for ref, entry in data["drafts"].items():
        _settle(rdir, ref, entry)
    drafts = json.loads(json.dumps(data["drafts"]))
    import bt_design_amend
    out = []
    for s in ui:
        entry = drafts.get(s["ref"], {})
        feedback = entry.get("feedback") or []
        late = bool(entry) and behind(entry, s)
        out.append({**s, **{k: v for k, v in entry.items() if k not in ("feedback", "digest", "ui_digest", "amend")},
                    "status": entry.get("status", "none"), "feedback": feedback,
                    "pending_feedback": sum(1 for f in feedback if not f.get("consumed")),
                    "stale": entry.get("status") in ("ready", "approved", "choosing") and late,
                    "amend": bt_design_amend.mode(rdir, s["ref"], entry) if late else None})
    return out


def _brief(project: str, rdir: Path, row: dict, feedback: list[dict], *, fresh: bool = False,
           behavior: Path | None = None) -> str:
    from bt_design_brief import _brief as build
    return build(project, rdir, row, feedback, fresh=fresh, behavior=behavior)


def launch(project: str, rdir: Path, ref: str, reason: str, *, fresh: bool = False) -> dict:
    """Start one Designer session in the background for `ref`; the caller holds no lock."""
    import bt_delegate
    row = next((r for r in subplans(rdir) if r["ref"] == ref), None)
    if row is None:
        raise SystemExit(f"{ref} is not a UI subplan contract of {Path(rdir).name}")
    with _locked(rdir) as data:
        entry = data["drafts"].setdefault(ref, {"feedback": []})
        if entry.get("status") in ACTIVE or entry.get("status") == "approved":
            return entry
        pending = [f for f in entry.get("feedback", []) if not f.get("consumed")]
        entry.update({"status": "queued", "subplan_id": row["id"], "reason": reason, "error": "", "queued": _now(),
                      "before": _sha(paths(rdir, ref)[0])})
    order = None
    try:
        order = bt_delegate.create(project, _brief(project, rdir, row, pending, fresh=fresh), None, None, Path(rdir), [], None,
                                   TIMEOUT_MIN, None, None, kind="design", role="designer")
        bt_delegate.start_background(order["id"])
    except (SystemExit, Exception) as exc:  # noqa: BLE001 - no account, usage limits: shown, retried after a backoff
        with _locked(rdir) as data:
            data["drafts"][ref].update({"status": "failed", "error": str(exc)[:600] or type(exc).__name__,
                                        "finished": _now(), "delegation": (order or {}).get("id")})
            return data["drafts"][ref]
    with _locked(rdir) as data:
        entry = data["drafts"][ref]
        for item in entry.get("feedback", []):
            if not item.get("consumed") and item in pending:
                item["consumed"] = order["id"]
        entry.update({"status": "drafting", "delegation": order["id"], "digest": row["digest"],
                      "ui_digest": row["ui_digest"], "started": _now(),
                      "agent": order.get("agent"), "model": order.get("model")})
        if reason == "plan changed":
            entry["auto_runs"] = int(entry.get("auto_runs") or 0) + 1
        _event(rdir, "Designer", f"Empezó {ref}" + {"feedback": " con tus comentarios", "focus": " (subplan en foco)",
                                                    "plan changed": " porque el subplan cambió"}.get(reason, ""), entry)
        return entry


def request(project: str, rdir: Path, refs: list[str] | None = None, *, force: bool = False,
            reason: str = "requested", fresh: bool = False, directions: int | None = None) -> list[str]:
    """Draft the named UI subplans (all of them by default) that need it; returns the refs started."""
    started = []
    directions = DEFAULT_DIRECTIONS if directions is None else directions
    if type(directions) is not int or not 1 <= directions <= 3:
        raise SystemExit("El número de direcciones debe estar entre 1 y 3.")
    if not planning(rdir):
        return started
    for row in rows(rdir) if active(rdir) else [{**s, "status": "none", "stale": False, "pending_feedback": 0}
                                                    for s in subplans(rdir) if s["ref"]]:
        if refs and row["ref"] not in refs:
            continue
        if row["status"] in ACTIVE or row["status"] == "approved":
            continue  # one Designer batch per subplan; different subplans are designed in parallel (owner, 2026-10-29)
        due = force or fresh or row["status"] in ("none", "failed") or row["stale"] or row["pending_feedback"]
        if due and reason != "plan changed" and row.get("failures"):
            with _locked(rdir) as data:  # an explicit request is the owner's retry: the failure count starts over
                data["drafts"].get(row["ref"], {})["failures"] = 0
        if due and not fresh and row.get("amend"):
            import bt_design_amend  # chosen work is extended with the plan delta, never regenerated
            with suppress(SystemExit):
                bt_design_amend.start(project, rdir, row["ref"], "", reason, auto=reason == "plan changed")
                started.append(row["ref"])
            continue
        if due:
            import bt_design_directions
            # A deliberate redo releases the previous choice; revision files remain untouched.
            if row["status"] == "choosing":
                with _locked(rdir) as data:
                    data["drafts"][row["ref"]]["status"] = "failed"
            result = bt_design_directions.start(project, rdir, row["ref"], reason, fresh, directions)
        if due and result.get("status") == "drafting":
            started.append(row["ref"])
    known = {s["ref"] for s in subplans(rdir) if s["ref"]}
    if not active(rdir) and known and (not refs or set(refs) & known):
        with _locked(rdir):
            pass  # an explicit request with nothing to start still turns planning-time design on
    return started


def add_feedback(project: str, rdir: Path, ref: str, text: str, via: str, *, direction: str | None = None) -> str:
    from bt_design_iterate import add_feedback as add
    return add(project, rdir, ref, text, via, direction=direction)


def sync(project: str, rdir: Path, *, now: float | None = None) -> list[str]:
    """Follow planning changes and owner feedback."""
    from bt_design_follow import sync as follow
    return follow(project, rdir, now=now)


def planning(rdir: Path) -> bool:
    """The plan is still being discussed (not approved, launched or finished): drafts may change."""
    from bt_core import _front
    return _front(Path(rdir) / "PLAN.md", "status") in PLANNING


def readiness(rdir: Path) -> list[str]:
    """Why the plan cannot be approved yet (empty when planning-time design is off or every draft is ready)."""
    return _problems(rows(rdir)) if active(rdir) else []


def _problems(rows_: list[dict]) -> list[str]:
    problems = []
    for row in rows_:
        label = f"{row['id']} ({row['ref']})"
        if row["status"] == "approved":
            continue
        if row.get("continuation_choice"):
            if row["status"] in ACTIVE:
                problems.append(f"{label}: el Designer sigue trabajando")
            elif row["status"] == "choosing":
                problems.append(f"{label}: la revisión del diseño elegido está pendiente de finalizarse")
            else:
                problems.append(f"{label}: no se pudo finalizar la revisión ({row.get('error') or row['status']})")
            continue
        if row.get("directions") and not row.get("chosen"):
            problems.append(f"{label}: elige una dirección de diseño antes de confirmar o aprobar")
            continue
        if row["status"] in ACTIVE:
            problems.append(f"{label}: el Designer sigue trabajando")
        elif row["status"] != "ready":
            problems.append(f"{label}: no hay un diseño listo ({row.get('error') or row['status']})")
        elif row.get("amend"):
            problems.append(f"{label}: el plan cambió después del diseño; actualízalo con «Actualizar diseño»")
        elif row["stale"]:
            problems.append(f"{label}: el subplan cambió después del diseño; hay que rehacerlo")
        elif row["pending_feedback"]:
            problems.append(f"{label}: hay comentarios sin aplicar")
    return problems


def pin_for_plan(rdir: Path, refs: list[str] | None = None) -> list[str]:
    """Approve the planning drafts with the plan, atomically with respect to the Designer: under the drafts lock,
    refuse unless every draft is ready and unchanged, then pin each one (SHA-256, `via: plan`). Called before the
    plan (or a stage, D-134: `refs` = the stage's UI contracts) is approved, so a refusal leaves nothing half-approved."""
    import bt_design_approval as approval
    if not active(rdir):
        return []
    with _locked(rdir) as data:
        current = [r for r in _rows(rdir, data) if refs is None or r["ref"] in refs]
        problems = _problems(current)
        ready, prior = [r for r in current if r["status"] == "ready"], approval.approvals(rdir)
        blobs = {}
        for row in ready:
            blob = paths(rdir, row["ref"])[0].read_bytes()
            digest = hashlib.sha256(blob).hexdigest()
            earlier = prior.get(row["ref"]) if isinstance(prior.get(row["ref"]), dict) else {}
            if digest != row.get("sha256"):
                problems.append(f"{row['ref']}: el contrato cambió después de quedar listo")
            elif earlier.get("status") == "approved" and earlier.get("sha256") != digest:
                problems.append(f"{row['ref']}: ya hay otra versión aprobada; usa una versión nueva del contrato")
            blobs[row["ref"]] = blob
        if problems:
            raise SystemExit("Los diseños de planificación no están listos: " + "; ".join(problems))
        for ref, blob in blobs.items():
            frozen = Path(rdir) / DIR / "history" / ref / "approved.md"  # the run copies this, never the live draft
            frozen.parent.mkdir(parents=True, exist_ok=True)
            frozen.write_bytes(blob)
            if paths(rdir, ref)[1].is_file():
                frozen.with_suffix(".html").write_bytes(paths(rdir, ref)[1].read_bytes())
            approval.approve_planning_draft(rdir, ref, blob, frozen.as_posix())
            data["drafts"][ref].update({"status": "approved", "approved": _now()})
        return list(blobs)


def execution_notes(rdir: Path, ref: str) -> str:
    """Brief lines for the run: where the plan-approved draft and its mockup are (empty when there is none)."""
    import bt_design_approval as approval
    record = approval.approvals(rdir).get(ref) if (Path(rdir) / approval.FILE).exists() else None
    frozen = Path(rdir) / DIR / "history" / ref / "approved.md"
    html = frozen.with_suffix(".html")
    if not isinstance(record, dict) or record.get("via") != "plan" or not frozen.is_file() or \
            hashlib.sha256(frozen.read_bytes()).hexdigest() != record.get("sha256"):
        return ""
    return f"Planning draft: {frozen.as_posix()}" + (f"\nPlanning mockup: {html.as_posix()}" if html.is_file() else "")


def follow_project(root: Path, project: str) -> list[str]:
    """Stop-hook nudge: for every requirement still being planned with planning-time design on, log what the
    conversation changed, redesign settled subplans and keep the translation current (also with no web page open)."""
    import bt_planning_activity
    import bt_planning_flow
    import bt_translate
    from bt_core import _front
    touched = []
    for rdir in sorted((Path(root) / project / "requirements").glob("REQ-*")):
        if not (active(rdir) or bt_planning_flow.active(rdir)) or _front(rdir / "PLAN.md", "status") in ("approved", "launched", "in-progress", "done",
                                                                       "merged"):
            continue
        try:
            bt_planning_activity.observe(rdir)
            touched += sync(project, rdir)
            bt_translate.ensure(project, rdir)
        except (SystemExit, Exception):  # noqa: BLE001, S112 - a hook never fails the session on background work
            continue
    return touched
