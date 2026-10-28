"""Collaborative planning (D-130): the owner, the Planner and the Designer build the plan together, in four phases.

- `interview`: no subplan yet. The Planner asks only the initial, most important questions (goal, scope, the
  decisions and inputs that shape the whole plan).
- `outline`: PLAN.json has the skeleton (milestones and subplans: title, outcome, UI or not; tasks optional). The owner
  confirms it on the web Plan tab or in the conversation.
- `subplans`: one subplan at a time is in focus. Owner and Planner define its behavior, design, inputs (credentials,
  locations, accounts) and tasks while the Designer drafts its UI; the owner confirms it and the focus moves on.
- `ready`: every subplan is confirmed and unchanged since; plan approval only checks that, pins the designs and launches.

State lives in `.planning/flow.json`; a requirement follows this flow once `start()` created it. Inputs come from the
`## Inputs` table of SPEC.md (columns Item, Subplan, Where, Who, Status; an empty Subplan or `all` is plan-wide). A
confirmation records a digest of the subplan, its tasks, its inputs, its `## Pruebas` rows (where to try it once it is
built, see `bt_verification`) and its draft: any later change reopens it.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path

import bt_design_drafts as drafts
import bt_planning_activity as activity

DIR = ".planning"
FILE = "flow.json"
PHASES = ("interview", "outline", "subplans", "ready")
RESOLVED = {"available", "location given", "provided", "resolved", "n/a", "not needed", "disponible", "ubicación dada"}


def _now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def active(rdir: Path) -> bool:
    return (Path(rdir) / DIR / FILE).is_file()


def _load(rdir: Path) -> dict:
    try:
        data = json.loads((Path(rdir) / DIR / FILE).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        data = {}
    if not isinstance(data, dict) or not isinstance(data.get("subplans"), dict):
        data = {"schema_version": 1, "outline": None, "focus": "", "subplans": {}}
    return data


@contextmanager
def _locked(rdir: Path):
    target = Path(rdir) / DIR / f".{FILE}.lock"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a+b") as handle:
        try:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        except (ImportError, OSError):
            pass
        data = _load(rdir)
        yield data
        fd, tmp = tempfile.mkstemp(prefix=f".{FILE}.", dir=target.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(data, stream, ensure_ascii=False, indent=1, sort_keys=True)
                stream.write("\n")
            os.replace(tmp, Path(rdir) / DIR / FILE)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


def start(rdir: Path) -> bool:
    """Put the requirement on the collaborative flow; False when it already was."""
    if active(rdir):
        return False
    with _locked(rdir):
        pass
    activity.record(rdir, "Planner", "Planificación conjunta: primero las preguntas iniciales", kind="flow")
    return True


# ------------------------------------------------------------------ inputs (SPEC ## Inputs)

def inputs(rdir: Path) -> list[dict]:
    """Rows of every SPEC.md `## Inputs…` table: item, subplans ([] = plan-wide), where, who, status, pending.
    Each table reads its own header; a table without an Item column is not an inputs table. Only locations are ever
    written there, never secret values."""
    try:
        text = (Path(rdir) / "SPEC.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return []
    out = []
    for section in re.finditer(r"(?ms)^##\s+Inputs\b[^\n]*\n(.*?)(?=^#{1,2}\s|\Z)", text):
        for table in re.findall(r"(?m)(?:^[ \t]*\|.*\n?)+", section.group(1)):
            out += _table(table.strip().splitlines())
    return out


def _cells(line: str) -> list[str]:
    body = line.strip()
    body = body.removeprefix("|")
    body = body[:-1] if body.endswith("|") and not body.endswith("\\|") else body
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", body)]


def _table(lines: list[str]) -> list[dict]:
    if len(lines) < 2 or not all(set(c) <= set("-: ") and c for c in _cells(lines[1])):
        return []
    head = [c.lower().strip("*` ") for c in _cells(lines[0])]

    def index(*names: str) -> int | None:
        return next((i for name in names for i, label in enumerate(head) if label.startswith(name)), None)
    item, status = index("item", "input"), index("status", "estado")
    if item is None:
        return []
    cols = {"subplan": index("subplan"), "where": index("where", "location", "dónde"),
            "who": index("who", "supplier", "supplied", "quién")}
    rows = []
    for line in lines[2:]:
        row = _cells(line)
        get = lambda i, row=row: row[i] if i is not None and i < len(row) else ""
        if not get(item):
            continue
        value = get(status) if status is not None else ""
        rows.append({"item": get(item), "subplans": _scope(get(cols["subplan"])), "where": get(cols["where"]),
                     "who": get(cols["who"]), "status": value or ("sin columna Status" if status is None else ""),
                     "pending": not _resolved(value)})
        rows[-1]["subplan"] = ", ".join(rows[-1]["subplans"])
    return rows


def _scope(cell: str) -> list[str]:
    """`SP-1, sp-2 / SP3` → ['SP-1', 'SP-2', 'SP-3']; empty, `all`, `todos` or a dash → plan-wide ([])."""
    parts = [p for p in re.split(r"[,;/\s]+", cell.strip("` ")) if p]
    if not parts or all(p.lower() in ("all", "todos", "-", "—") for p in parts):
        return []
    return [f"SP-{m.group(1)}" if (m := re.fullmatch(r"(?i)sp-?(\d+)", p)) else p for p in parts]


def _resolved(status: str) -> bool:
    """A closed set; `deferred` counts only with its fallback written after a colon."""
    head, _, rest = status.lower().strip("*` ").partition(":")
    head = head.strip()
    return head in RESOLVED or (head == "deferred" and bool(rest.strip()))


def inputs_for(rdir: Path, sp: str, rows: list[dict] | None = None) -> list[dict]:
    rows = inputs(rdir) if rows is None else rows
    return [row for row in rows if not row["subplans"] or sp in row["subplans"]]


# ------------------------------------------------------------------ state

def _plan_order(rdir: Path) -> list[dict]:
    return drafts.subplans(rdir)


def _digest(rdir: Path, plan: dict, sp: dict, rows: list[dict]) -> str:
    """What the owner confirmed: the subplan with all its tasks, the inputs naming it and its design draft (contract
    and mockup content, not their status: approval pins them unchanged). Plan-wide inputs gate approval instead."""
    item = next((s for s in plan.get("subplans") or [] if isinstance(s, dict) and s.get("id") == sp["id"]), {})
    mockup = drafts.paths(rdir, sp["ref"])[1] if sp["ref"] else None
    import bt_verification
    payload = {"subplan": item, "tasks": sp["tasks"], "inputs": [r for r in rows if sp["id"] in r["subplans"]],
               "design": _draft_sha(rdir, sp["ref"]),
               "mockup": hashlib.sha256(mockup.read_bytes()).hexdigest() if mockup and mockup.is_file() else None}
    if (tests := bt_verification.tests_for(rdir, sp["id"])):   # absent when there are none: earlier confirmations keep their digest
        payload["tests"] = tests
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def _draft_sha(rdir: Path, ref: str | None) -> str | None:
    if not ref:
        return None
    md = drafts.paths(rdir, ref)[0]
    try:
        return hashlib.sha256(md.read_bytes()).hexdigest()
    except OSError:
        return None


def problems(rdir: Path, sp: dict, design_rows: dict | None = None, input_rows: list[dict] | None = None) -> list[str]:
    """Why subplan `sp` cannot be confirmed yet."""
    out = []
    if not sp["tasks"]:
        out.append("todavía no tiene tareas")
    elif any(not (t.get("acceptance_criteria") or []) for t in sp["tasks"]):
        out.append("hay tareas sin criterios de aceptación")
    import bt_verification
    if bt_verification.missing(rdir, sp["id"]):
        out.append("falta cómo probarlo: una fila para este subplan en SPEC `## Pruebas` (dónde, cómo y qué debes ver)")
    if sp["tasks"]:
        try:
            import bt_stage_readiness
            if (refused := bt_stage_readiness.problem_for(rdir, sp["id"])):
                out.append(refused)
        except Exception:  # noqa: BLE001 - the readiness walk never breaks the page
            pass
    pending = [r["item"] for r in inputs_for(rdir, sp["id"], input_rows) if r["pending"]]
    if pending:
        out.append("faltan entradas: " + ", ".join(pending[:4]) + (f" y {len(pending) - 4} más" if len(pending) > 4 else ""))
    if sp["ref"]:
        design_rows = {r["ref"]: r for r in drafts.rows(rdir)} if design_rows is None else design_rows
        row = design_rows.get(sp["ref"])
        if row is None or row["status"] == "none":
            out.append("el Designer todavía no empezó su diseño (empieza cuando el subplan está en foco)")
        elif row.get("amend") and row["status"] not in drafts.ACTIVE:
            out.append("el plan cambió después del diseño elegido: actualízalo con lo que ya está («Actualizar diseño»)")
        elif row["stale"] and row["status"] not in drafts.ACTIVE:
            out.append("el diseño quedó desactualizado y aún no hay dirección elegida: el Designer prepara direcciones "
                       "nuevas con el subplan en foco")
        else:
            out += [p.split(": ", 1)[-1] for p in drafts._problems([row])]
    return out


def _editing(rdir: Path, plan: dict) -> bool:
    """PLAN.json exists but does not parse: the conversation is writing it right now."""
    return not plan and (Path(rdir) / "PLAN.json").is_file()


def _done(data: dict, rdir: Path, plan: dict, subplans: list[dict], rows: list[dict]) -> set[str]:
    """Subplans confirmed and unchanged since."""
    return {sp["id"] for sp in subplans if (data["subplans"].get(sp["id"]) or {}).get("digest") ==
            _digest(rdir, plan, sp, rows)}


def _focus(data: dict, subplans: list[dict], done: set[str]) -> str:
    """The stored focus while it still needs work; otherwise the first subplan pending or reopened, in plan order."""
    ids = [sp["id"] for sp in subplans]
    if data.get("focus") in ids and data["focus"] not in done:
        return data["focus"]
    return next((sid for sid in ids if sid not in done), "")


def state(rdir: Path, subplans: list[dict] | None = None, design_rows: dict | None = None) -> dict:
    """Phase, focus and per-subplan state (`pending`, `defining`, `confirmed`, `changed`) with what is missing."""
    data, plan = _load(rdir), drafts._plan(rdir)
    subplans = _plan_order(rdir) if subplans is None else subplans
    input_rows = inputs(rdir)
    known = {sp["id"] for sp in subplans}
    unknown = sorted({sid for row in input_rows for sid in row["subplans"] if sid not in known})
    if _editing(rdir, plan):  # keep the phase the owner was in instead of flipping to the interview view
        phase = "subplans" if data.get("outline") else "outline"
        return {"active": active(rdir), "phase": phase, "focus": data.get("focus") or "", "subplans": {},
                "confirmed": 0, "total": 0, "outline": data.get("outline"), "inputs": input_rows,
                "unknown": unknown, "editing": True}
    done = _done(data, rdir, plan, subplans, input_rows) if data.get("outline") else set()
    if design_rows is None and any(sp["ref"] and sp["id"] not in done for sp in subplans):
        design_rows = {row["ref"]: row for row in drafts.rows(rdir)}
    focus = _focus(data, subplans, done) if data.get("outline") else ""
    per = {}
    for sp in subplans:
        record = data["subplans"].get(sp["id"]) or {}
        if record.get("digest"):
            st = "confirmed" if sp["id"] in done else "changed"
        else:
            st = "defining" if focus == sp["id"] else "pending"
        per[sp["id"]] = {"state": st, "confirmed_at": record.get("at", ""), "via": record.get("via", ""),
                         "problems": problems(rdir, sp, design_rows, input_rows) if st != "confirmed" else []}
    if not subplans:
        phase = "interview"
    elif not data.get("outline"):
        phase = "outline"
    elif all(v["state"] == "confirmed" for v in per.values()):
        phase = "ready"
    else:
        phase = "subplans"
    return {"active": active(rdir), "phase": phase, "focus": focus, "subplans": per, "confirmed": len(done),
            "total": len(per), "outline": data.get("outline"), "inputs": input_rows, "unknown": unknown,
            "editing": False}


def keep_confirmed(rdir: Path, sids: list[str], note: str) -> list[str]:
    """Re-pin the confirmation of `sids` after a mechanical edit the owner's own action made (a stage's automatic
    cross-check audit), so it does not undo them. The caller passes only subplans that were confirmed and unchanged
    right before that edit. Returns the re-pinned ids."""
    plan, subplans, rows = drafts._plan(rdir), _plan_order(rdir), inputs(rdir)
    by_id = {sp["id"]: sp for sp in subplans}
    kept = []
    with _locked(rdir) as data:
        for sid in sids:
            record = data["subplans"].get(sid)
            if record and sid in by_id:
                record.update(digest=_digest(rdir, plan, by_id[sid], rows), repinned=f"{_now()} {note}")
                kept.append(sid)
    return kept


def approval_problems(rdir: Path, snapshot: dict | None = None) -> list[str]:
    """Why the plan cannot be approved under this flow (empty when the flow is off or every subplan is confirmed)."""
    if not active(rdir):
        return []
    st = snapshot if snapshot is not None else state(rdir)
    if st["editing"]:
        return ["PLAN.json se está editando (no se puede leer)"]
    if st["phase"] == "interview":
        return ["todavía no hay esqueleto de hitos y subplanes"]
    if st["phase"] == "outline":
        return ["falta confirmar el esqueleto"]
    out = []
    for sid, item in st["subplans"].items():
        if item["state"] == "changed":
            out.append(f"{sid}: cambió después de confirmarlo")
        elif item["state"] != "confirmed":
            out.append(f"{sid}: sin confirmar")
    pending = [r["item"] for r in st["inputs"] if r["pending"] and not r["subplans"]]
    if pending:
        out.append("faltan entradas generales: " + ", ".join(pending[:4]))
    if st["unknown"]:
        out.append("hay entradas para subplanes que no existen: " + ", ".join(st["unknown"]))
    return out


def design_scope(rdir: Path) -> set[str] | None:
    """UI contracts the Designer may work on by itself: only the subplan in focus under this flow (a reopened one
    becomes the focus when nothing else is); None = all."""
    if not active(rdir):
        return None
    data, plan = _load(rdir), drafts._plan(rdir)
    if not data.get("outline") or _editing(rdir, plan):
        return set()
    subplans = _plan_order(rdir)
    focus = _focus(data, subplans, _done(data, rdir, plan, subplans, inputs(rdir)))
    return {sp["ref"] for sp in subplans if sp["id"] == focus and sp["ref"]}


# ------------------------------------------------------------------ actions

def _next(subplans: list[dict], done: set[str], after: str = "") -> str:
    """The next subplan to define: the first not confirmed (or reopened) after `after` in plan order, wrapping."""
    ids = [sp["id"] for sp in subplans]
    start_at = ids.index(after) + 1 if after in ids else 0
    return next((sid for sid in ids[start_at:] + ids[:start_at] if sid not in done and sid != after), "")


def _design(project: str, rdir: Path, sid: str) -> str:
    ref = next((sp["ref"] for sp in _plan_order(rdir) if sp["id"] == sid and sp["ref"]), None)
    if not ref:
        return ""
    started = drafts.request(project, rdir, [ref], reason="focus")
    return f" El Designer empezó {ref}." if started else ""


def _guard(rdir: Path) -> str:
    if not active(rdir):
        return "Este requerimiento no está en la planificación conjunta (bitacora.py planning start)."
    if not drafts.planning(rdir):
        return "El plan ya no está en planificación."
    if _editing(rdir, drafts._plan(rdir)):
        return "PLAN.json se está editando; inténtalo en unos segundos."
    return ""


def confirm_outline(project: str, rdir: Path, by: str = "owner", via: str = "web") -> str:
    if (refused := _guard(rdir)):
        return refused
    subplans = _plan_order(rdir)
    if not subplans:
        return "Todavía no hay subplanes en el plan: el esqueleto aparece cuando el Planner lo escribe."
    with _locked(rdir) as data:
        if data.get("outline"):
            return "El esqueleto ya estaba confirmado."
        data["outline"] = {"at": _now(), "by": by, "via": via, "subplans": [sp["id"] for sp in subplans]}
        data["focus"] = _focus(data, subplans, set())
        focus = data["focus"]
    activity.record(rdir, "Tú", f"Confirmaste el esqueleto ({len(subplans)} subplanes); empezamos por {focus}",
                    kind="flow", sp=focus)
    return f"Esqueleto confirmado. Ahora se define {focus}." + _design(project, rdir, focus)


def focus(project: str, rdir: Path, sid: str, by: str = "owner") -> str:
    if (refused := _guard(rdir)):
        return refused
    subplans = _plan_order(rdir)
    if sid not in {sp["id"] for sp in subplans}:
        return f"{sid or 'Ese subplan'} no está en el plan."
    with _locked(rdir) as data:
        if not data.get("outline"):
            return "Primero hay que confirmar el esqueleto."
        if data.get("focus") == sid:
            return f"Ya se está definiendo {sid}."
        data["focus"] = sid
    activity.record(rdir, "Tú" if by == "owner" else "Planner", f"Ahora se define {sid}", kind="flow", sp=sid)
    return f"Ahora se define {sid}." + _design(project, rdir, sid)


def confirm(project: str, rdir: Path, sid: str, by: str = "owner", via: str = "web") -> str:
    if (refused := _guard(rdir)):
        return refused
    plan, subplans, rows = drafts._plan(rdir), _plan_order(rdir), inputs(rdir)
    sp = next((s for s in subplans if s["id"] == sid), None)
    if sp is None:
        return f"{sid or 'Ese subplan'} no está en el plan."
    missing = problems(rdir, sp, None, rows)
    if missing:
        return f"{sid} no se puede confirmar todavía: " + "; ".join(missing) + "."
    with _locked(rdir) as data:
        if not data.get("outline"):
            return "Primero hay que confirmar el esqueleto."
        data["subplans"][sid] = {"at": _now(), "by": by, "via": via, "digest": _digest(rdir, plan, sp, rows)}
        nxt = _next(subplans, _done(data, rdir, plan, subplans, rows), after=sid)
        data["focus"] = nxt
    where = "en la web" if via == "web" else "en la conversación"
    activity.record(rdir, "Tú", f"Confirmaste {sid} {where}" + (f"; sigue {nxt}" if nxt else "; todos listos"),
                    kind="flow", sp=sid)
    if not nxt and state(rdir)["phase"] == "ready":
        from bt_core import set_front
        set_front(Path(rdir) / "PLAN.md", "status", "review")  # every subplan confirmed: the plan awaits approval
        return f"{sid} confirmado. Todos los subplanes están confirmados: el plan queda listo para aprobar."
    if not nxt:
        return f"{sid} confirmado."
    return f"{sid} confirmado. Ahora se define {nxt}." + _design(project, rdir, nxt)
