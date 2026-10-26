"""Planning-time design drafts: the Designer works on each UI subplan while the owner and the Planner talk.

Drafts live in the requirement folder, never in a project repository: `design/<contract>@v<N>.md` (the contract) and
`design/<contract>@v<N>.html` (a static mockup), with their state in `design/drafts.json`. A draft is redone when
its subplan changes, when the owner leaves feedback, or on request. Approving the plan approves every ready draft
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
from contextlib import contextmanager
from pathlib import Path

DIR = "design"
FILE = "drafts.json"
TIMEOUT_MIN = 40
DEBOUNCE_SEC = 45          # a subplan still being edited in the conversation is not redesigned on every keystroke
STALE_GRACE_SEC = 15 * 60  # a delegation that never wrote its outcome is declared failed after its timeout plus this
QUEUED_TTL_SEC = 10 * 60  # a draft queued by a process that died before starting the Designer
FAIL_BACKOFF_SEC = 10 * 60  # a failed draft is not retried by `sync` sooner (no account, usage limits)
MAX_AUTO_RUNS = 8         # redesigns `sync` may start per contract on its own; explicit requests are not capped
ACTIVE = ("queued", "drafting")
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
        out.append({"id": item["id"], "title": item.get("title") or "", "outcome": item.get("outcome") or "",
                    "covers": item.get("covers") or [], "criteria": item.get("acceptance_criteria") or [],
                    "ui": ui, "ref": ref, "tasks": own, "digest": _digest(item, own)})
    return out


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
        _archive(rdir, ref, entry["revision"])
        entry.setdefault("history", []).append({"rev": entry["revision"], "at": entry["finished"],
                                                "summary": entry["summary"]})
        _event(rdir, "Designer", f"{ref} · borrador {entry['revision']} listo", entry)
    else:
        entry["status"] = "failed"
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
    out = []
    for s in ui:
        entry = drafts.get(s["ref"], {})
        feedback = entry.get("feedback") or []
        out.append({**s, **{k: v for k, v in entry.items() if k not in ("feedback", "digest")},
                    "status": entry.get("status", "none"), "feedback": feedback,
                    "pending_feedback": sum(1 for f in feedback if not f.get("consumed")),
                    "stale": entry.get("status") == "ready" and entry.get("digest") != s["digest"]})
    return out


def _brief(project: str, rdir: Path, row: dict, feedback: list[dict]) -> str:
    import bt_workspace
    from bt_core import ROOT
    md, html = paths(rdir, row["ref"])
    repos = "\n".join(f"  - {role}: {path}" for role, path in bt_workspace.repos(ROOT, project, discover=False).items()
                      if Path(path).exists()) or "  - (none cloned on this machine)"
    previous = ("A previous draft exists at those paths: revise it, keeping everything the feedback and the plan "
                "changes do not touch." if md.is_file() else "There is no previous draft.")
    asks = "\n".join(f"  - ({f['when'][:16]}) {f['text']}" for f in feedback) or "  - none"
    return f"""Planning-time UI/UX design for subplan {row['id']} — {row['title']}.

The owner and the Planner are still discussing this plan. Design the best version for the plan as it stands now;
record open decisions as questions in the contract instead of stopping. This draft becomes the approved contract
`{row['ref']}` when the owner approves the plan.

Read: {Path(rdir) / 'SPEC.md'}, {Path(rdir) / 'PLAN.md'} and {Path(rdir) / 'PLAN.json'} (subplan {row['id']}, its
tasks and the requirement ids it covers). Project repositories, read-only, for the existing design system, tokens
and components:
{repos}

Write exactly these two files and nothing else (no SPEC, PLAN, repository or other bitácora file):
1. {md} — the contract `{row['ref']}` with status `draft`, following the ui-ux-contract-authoring skill (all twelve
   sections, visual acceptance criteria table included).
2. {html} — a self-contained static mockup of that contract: inline CSS and JS only, no network request, no external
   font or image (use CSS or data: URIs), realistic mock data, every view of the subplan, a visible switch for each
   declared state (loading, empty, error, …) and layouts that reflow at the contract's breakpoints. Reuse the
   project's design tokens when the repository has them. Show a small "Mockup" label so nobody takes it for the
   product.

{previous}
Owner feedback to address (oldest first):
{asks}

In your report put one line per open question for the owner in "notes", each starting with "Q:".
"""


def launch(project: str, rdir: Path, ref: str, reason: str) -> dict:
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
        order = bt_delegate.create(project, _brief(project, rdir, row, pending), None, None, Path(rdir), [], None,
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
        entry.update({"status": "drafting", "delegation": order["id"], "digest": row["digest"], "started": _now(),
                      "agent": order.get("agent"), "model": order.get("model")})
        if reason == "plan changed":
            entry["auto_runs"] = int(entry.get("auto_runs") or 0) + 1
        _event(rdir, "Designer", f"Empezó {ref}" + {"feedback": " con tus comentarios",
                                                    "plan changed": " porque el subplan cambió"}.get(reason, ""), entry)
        return entry


def request(project: str, rdir: Path, refs: list[str] | None = None, *, force: bool = False,
            reason: str = "requested") -> list[str]:
    """Draft the named UI subplans (all of them by default) that need it; returns the refs started."""
    started = []
    for row in rows(rdir) if active(rdir) else [{**s, "status": "none", "stale": False, "pending_feedback": 0}
                                                    for s in subplans(rdir) if s["ref"]]:
        if refs and row["ref"] not in refs:
            continue
        if row["status"] in ACTIVE or row["status"] == "approved":
            continue
        due = force or row["status"] == "none" or row["stale"] or row["pending_feedback"]
        if due and launch(project, rdir, row["ref"], reason).get("status") == "drafting":
            started.append(row["ref"])
    known = {s["ref"] for s in subplans(rdir) if s["ref"]}
    if not active(rdir) and known and (not refs or set(refs) & known):
        with _locked(rdir):
            pass  # an explicit request with nothing to start still turns planning-time design on
    return started


def add_feedback(project: str, rdir: Path, ref: str, text: str, via: str) -> str:
    text = " ".join(text.split())
    if not text:
        return "Escribe qué debe cambiar en el diseño."
    if ref not in {s["ref"] for s in subplans(rdir) if s["ref"]}:
        return f"{ref or 'Ese contrato'} no es un subplan con interfaz de este plan."
    with _locked(rdir) as data:
        entry = data["drafts"].setdefault(ref, {"feedback": [], "status": "none"})
        _settle(rdir, ref, entry)
        if entry.get("status") == "approved":
            return f"{ref} ya fue aprobado con el plan; los cambios van en una versión nueva del contrato."
        entry.setdefault("feedback", []).append({"when": _now(), "text": text[:4000], "via": via})
        _event(rdir, "Tú → Designer", f"{ref}: {text[:200]}", entry, kind="feedback")
        busy = entry.get("status") in ACTIVE
    if busy:
        return f"Comentario guardado. El Designer lo tomará al terminar la versión en curso de {ref}."
    started = request(project, rdir, [ref], reason="feedback")
    return (f"Comentario enviado al Designer; rediseñando {ref}." if started else
            f"Comentario guardado para {ref}; no se pudo iniciar el Designer (revisa el estado).")


def sync(project: str, rdir: Path, *, now: float | None = None) -> list[str]:
    """Follow the conversation: draft new UI subplans, pending feedback, and subplans that changed and settled."""
    if not active(rdir):
        return []
    now = time.time() if now is None else now
    try:
        settled = now - (Path(rdir) / "PLAN.json").stat().st_mtime >= DEBOUNCE_SEC
    except OSError:
        return []
    due = []
    for r in rows(rdir):
        if r["status"] in ACTIVE or r["status"] == "approved":
            continue
        if r["status"] == "failed" and _age(r.get("finished")) < FAIL_BACKOFF_SEC:
            continue  # do not relaunch a failing Designer on every page poll
        changed = settled and (r["status"] == "none" or r["stale"]) and int(r.get("auto_runs") or 0) < MAX_AUTO_RUNS
        if r["pending_feedback"] or changed:
            due.append(r["ref"])
    return request(project, rdir, due, reason="plan changed") if due else []


def readiness(rdir: Path) -> list[str]:
    """Why the plan cannot be approved yet (empty when planning-time design is off or every draft is ready)."""
    return _problems(rows(rdir)) if active(rdir) else []


def _problems(rows_: list[dict]) -> list[str]:
    problems = []
    for row in rows_:
        label = f"{row['id']} ({row['ref']})"
        if row["status"] == "approved":
            continue
        if row["status"] in ACTIVE:
            problems.append(f"{label}: el Designer sigue trabajando")
        elif row["status"] != "ready":
            problems.append(f"{label}: no hay un diseño listo ({row.get('error') or row['status']})")
        elif row["stale"]:
            problems.append(f"{label}: el subplan cambió después del diseño; se está rehaciendo")
        elif row["pending_feedback"]:
            problems.append(f"{label}: hay comentarios sin aplicar")
    return problems


def pin_for_plan(rdir: Path) -> list[str]:
    """Approve every planning draft with the plan, atomically with respect to the Designer: under the drafts lock,
    refuse unless every draft is ready and unchanged, then pin each one (SHA-256, `via: plan`). Called before the
    plan is marked approved, so a refusal leaves the plan in review and nothing half-approved."""
    import bt_design_approval as approval
    if not active(rdir):
        return []
    with _locked(rdir) as data:
        current = _rows(rdir, data)
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
            approval.approve_planning_draft(rdir, ref, blob, paths(rdir, ref)[0].as_posix())
            data["drafts"][ref].update({"status": "approved", "approved": _now()})
        return list(blobs)


def execution_notes(rdir: Path, ref: str) -> str:
    """Brief lines for the run: where the plan-approved draft and its mockup are (empty when there is none)."""
    import bt_design_approval as approval
    record = approval.approvals(rdir).get(ref) if (Path(rdir) / approval.FILE).exists() else None
    md, html = paths(rdir, ref)
    if not isinstance(record, dict) or record.get("via") != "plan" or not md.is_file():
        return ""
    return f"Planning draft: {md.as_posix()}" + (f"\nPlanning mockup: {html.as_posix()}" if html.is_file() else "")
