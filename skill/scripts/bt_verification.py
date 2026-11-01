"""Per-subplan verification: the owner's checkpoint after each subplan is built.

The run never stops at the end of a subplan, but a plan with subplans is not finished until the owner has tried and
approved every one of them, each on its own:

- the Planner writes `## Pruebas` in SPEC.md (columns Subplan, Where, How, Expect): where the subplan can be tried
  (local, production, an external place) and what to look for. A subplan cannot be confirmed in planning without a row;
  an internal one says `none` and why;
- when the engine publishes a subplan version (an immutable commit of the integrated tree at that subplan's boundary,
  mirrored in `RUN.projection.json` under `subplans`), the subplan is *to test*; the owner opens exactly that commit in a
  throwaway worktree outside the repositories, tries it, and approves or rejects it;
- a decision is pinned to the version and commit it saw: a newer published version makes it *outdated*;
- `gate()` lists what still blocks closing the requirement (the review merge refuses while it is not empty).

State is `<req>/.verification/decisions.json`. Only runs whose projection carries `subplans` (written by this code)
are gated, so runs started before this feature are untouched. Standard library only.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import contextlib
import re
import sqlite3
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

import bt_planning_activity as activity
from bt_planning_flow import _cells, _scope

DIR = ".verification"
FILE = "decisions.json"
PROJECTION = "RUN.projection.json"
SHA = re.compile(r"[0-9a-f]{40}")
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,40}")
NONE_WORDS = {"none", "ninguna", "ninguno", "sin prueba manual", "no aplica", "n/a"}
STATES_ES = {"waiting": "se está construyendo", "to_test": "por probar", "approved": "aprobado", "rejected": "rechazado",
             "outdated": "cambió tras tu decisión"}
KINDS_ES = {"local": "En local", "production": "En producción", "external": "Fuera de tus servidores", "none": "Sin prueba manual"}


def _now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


# ------------------------------------------------------------------ SPEC ## Pruebas

def _kind(where: str) -> str:
    low = where.lower().strip("*` ")
    if low in NONE_WORDS or low.startswith(("ninguna", "none", "sin prueba")):
        return "none"
    if low.startswith("local"):
        return "local"
    if low.startswith(("prod", "producción", "produccion")):
        return "production"
    return "external"


def tests(rdir: Path, name: str = "SPEC.md") -> list[dict]:
    """Rows of every SPEC.md `## Pruebas` (or `## Testing`) table: subplans ([] = every subplan), kind, where, how, expect.
    `name` reads another rendering of the SPEC (SPEC.es.md, whose steps the owner reads in Spanish)."""
    try:
        text = (Path(rdir) / name).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return []
    out = []
    for section in re.finditer(r"(?ms)^##\s+(?:Pruebas|Testing|Manual testing)\b[^\n]*\n(.*?)(?=^#{1,2}\s|\Z)", text):
        for table in re.findall(r"(?m)(?:^[ \t]*\|.*\n?)+", section.group(1)):
            lines = table.strip().splitlines()
            if len(lines) < 3 or not all(set(c) <= set("-: ") and c for c in _cells(lines[1])):
                continue
            head = [c.lower().strip("*` ") for c in _cells(lines[0])]

            def index(*names: str, head=head) -> int | None:
                return next((i for name in names for i, label in enumerate(head) if label.startswith(name)), None)
            cols = {"subplan": index("subplan"), "where": index("where", "dónde", "donde"), "how": index("how", "cómo", "como"),
                    "expect": index("expect", "qué", "que debes", "esperado", "resultado")}
            if cols["subplan"] is None or cols["where"] is None:
                continue
            for line in lines[2:]:
                row = _cells(line)
                get = lambda i, row=row: row[i] if i is not None and i < len(row) else ""
                if not get(cols["where"]):
                    continue
                out.append({"subplans": _scope(get(cols["subplan"])), "kind": _kind(get(cols["where"])),
                            "where": get(cols["where"]), "how": get(cols["how"]), "expect": get(cols["expect"])})
    return out


def tests_for(rdir: Path, sp: str, rows: list[dict] | None = None) -> list[dict]:
    rows = tests(rdir) if rows is None else rows
    return [r for r in rows if not r["subplans"] or sp in r["subplans"]]


# The pages a test row names: full local URLs and bare paths such as /3d or /proyectos (owner, 2026-10-29: «necesito que
# salgan la url y las urls específicas que hay que probar»). Navigation through menus stays in «Cómo».
_FULL_URL = re.compile(r"https?://(?:localhost|127\.0\.0\.1)(?::\d+)?(/[^\s`)|,;»\"']*)?")
_BARE_PATH = re.compile(r"(?<![\w/.:@-])(/[a-z0-9][a-z0-9_\-]*(?:/[a-z0-9_\-\[\]]+)*)(?![\w.@/])")


def test_paths(rows: list[dict]) -> list[str]:
    found: list[str] = []
    for r in rows:
        text = f"{r.get('how') or ''} {r.get('expect') or ''}"
        rest = _FULL_URL.sub(lambda m: found.append((m.group(1) or "/").rstrip(".")) or " ", text)
        found += [m.group(1) for m in _BARE_PATH.finditer(rest)]
    return list(dict.fromkeys(found))


def missing(rdir: Path, sp: str, rows: list[dict] | None = None) -> bool:
    """True when no row of `## Pruebas` names `sp` itself (a row for `all` only supplements) or the only row says `none`
    without a reason in its How cell."""
    rows = tests(rdir) if rows is None else rows
    return not any(sp in r["subplans"] and (r["kind"] != "none" or r["how"].strip()) for r in rows)


# ------------------------------------------------------------------ ledger and run facts

def _load(rdir: Path) -> dict:
    try:
        data = json.loads((Path(rdir) / DIR / FILE).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    if not isinstance(data.get("subplans"), dict):
        data["subplans"] = {}
    if not isinstance(data.get("seen"), dict):
        data["seen"] = {}
    data["schema_version"] = 1
    return data


@contextmanager
def _locked(rdir: Path):
    folder = Path(rdir) / DIR
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / f".{FILE}.lock").open("a+b") as handle:
        try:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        except (ImportError, OSError):
            pass
        data = _load(rdir)
        yield data
        fd, tmp = tempfile.mkstemp(prefix=f".{FILE}.", dir=folder)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(data, stream, ensure_ascii=False, indent=1, sort_keys=True)
                stream.write("\n")
            os.replace(tmp, folder / FILE)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)


def _plan(rdir: Path) -> dict:
    try:
        data = json.loads((Path(rdir) / "PLAN.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def published(rdir: Path) -> dict[str, dict]:
    """The engine's published subplan versions from the run projection; `None`-like `{}` when there is no projection."""
    return {f["id"]: f for f in projection_subplans(rdir) if f.get("status") == "published"
            and isinstance(f.get("version"), int) and not isinstance(f.get("version"), bool) and f["version"] > 0
            and isinstance(f.get("commit"), str) and SHA.fullmatch(f["commit"])}


def durable_versions(rdir: Path) -> list[dict] | None:
    """The subplan versions the durable runtime published, as projection rows; None when the run is not the durable
    runtime's. They live in its composition stores (`<root>/.state/durable/composition/<project>-<REQ>-r<N>-<role>.db`,
    one per approved revision), never in RUN.projection.json, which only the legacy Scheduler writes: without this, a
    durable run's subplans stayed «se está construyendo» forever and a stage queued behind one never ran (pictures
    REQ-021, 2026-10-29). A version is a change of the subplan's commit over time, so a stage join re-publishing the
    same tree keeps the owner's decision."""
    rdir = Path(rdir)
    try:
        import bt_run_owner
        if bt_run_owner.backend(rdir) != "dbos" or rdir.parent.name != "requirements":
            return None
    except Exception:  # noqa: BLE001 - an unreadable owner record is not a durable run
        return None
    store = rdir.parent.parent.parent / ".state" / "durable" / "composition"
    seen: dict[str, list[tuple[str, str]]] = {}
    for db in store.glob(f"{rdir.parent.parent.name}-{_req(rdir)}-r*-*.db"):
        try:
            with contextlib.closing(sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=2.0)) as conn:
                rows = conn.execute("SELECT subplan_id, body FROM versions").fetchall()
        except sqlite3.Error:
            continue
        for sid, body in rows:
            try:
                item = json.loads(body)
            except ValueError:
                continue
            if isinstance(item.get("commit"), str) and SHA.fullmatch(item["commit"]):
                seen.setdefault(str(sid), []).append((str(item.get("published_at") or ""), item["commit"]))
    lines = _lines(rdir)
    for sid, (tip, repo) in _built(rdir, lines).items():
        last = max(seen.get(sid, []), default=("", ""))[1]
        if tip != last and not (last and _tree(repo, last) == _tree(repo, tip)):
            seen.setdefault(sid, []).append(("~", tip))           # after every stored publication
    out = []
    for sid, items in sorted(seen.items()):
        commits: list[str] = []
        for _at, commit in sorted(items):
            if not commits or commits[-1] != commit:
                commits.append(commit)
        out.append({"id": sid, "status": "published", "version": len(commits), "commit": commits[-1]})
    import bt_verification_tree
    return bt_verification_tree.folded(out, lines)


_SAFE_REF = re.compile(r"[^A-Za-z0-9._-]+")


def _tree(repo: Path, commit: str) -> str:
    return _git(repo, "rev-parse", "-q", "--verify", f"{commit}^{{tree}}").stdout.strip()


def _lines(rdir: Path) -> dict:
    """The current durable run's plan, task states and subplan line tips (`refs/bt/subplan/...`, the commit the composer
    itself publishes): {"plan", "states", "tips": {sid: (tip, repo, role)}, "project", "req", "revision"}; {} when the
    run cannot be read."""
    root = rdir.parent.parent.parent
    try:
        run = json.loads((rdir / "RUN.owner.json").read_text(encoding="utf-8")).get("run_id") or ""
        project, req, revision = run.split(":")[0], run.split(":")[1], int(run.rsplit(":r", 1)[1])
        plan = json.loads((rdir / "plan-revisions" / f"PLAN.r{revision}.json").read_text(encoding="utf-8"))
        projected = json.loads((root / ".state" / "durable" / "projections" / project / f"{req}-r{revision}.json")
                               .read_text(encoding="utf-8"))
    except (OSError, ValueError, IndexError, AttributeError):
        return {}
    states = {t.get("id"): t.get("state") for t in projected.get("tasks") or () if isinstance(t, dict)}
    try:
        import bt_workspace as ws
        repos = ws.repos(root, project, discover=False)
    except Exception:  # noqa: BLE001 - no workspace record: nothing to read the lines from
        return {}
    tips = {}
    for sid in {str(t["subplan_id"]) for t in plan.get("tasks") or () if isinstance(t, dict) and t.get("subplan_id")}:
        role = str(next(t for t in plan["tasks"] if isinstance(t, dict) and t.get("subplan_id") == sid)
                   .get("repository") or "default")
        repo = repos.get(role)
        if not repo or not Path(repo).exists():
            continue
        ref = f"refs/bt/subplan/{_SAFE_REF.sub('-', project)}/{req}/r{revision}/{_SAFE_REF.sub('-', role)}/{_SAFE_REF.sub('-', sid)}"
        tip = _git(Path(repo), "rev-parse", "-q", "--verify", f"{ref}^{{commit}}").stdout.strip()
        if SHA.fullmatch(tip):
            tips[sid] = (tip, Path(repo), role)
    return {"plan": plan, "states": states, "tips": tips, "project": project, "req": req, "revision": revision,
            "resolutions": root / ".state" / "durable" / "composition" / "resolutions"}


def _built(rdir: Path, lines: dict | None = None) -> dict[str, tuple[str, Path]]:
    """Subplans of the current durable run whose every task is accepted, with their subplan line's tip: the tree the
    owner tries. The composer publishes a subplan's version only when a composition gate folds it, and a gate can sit
    behind unrelated work: pictures REQ-021 SP-11/SP-12 were complete on 2026-10-30 but stayed «se está construyendo»
    because CG-11/CG-12 waited on SP-10 and the owner's manual check, while SP-13 waited on the owner approving SP-12
    (D-243). The tip is the same commit the composer would publish (`refs/bt/subplan/...`)."""
    lines = _lines(rdir) if lines is None else lines
    if not lines:
        return {}
    states, out = lines["states"], {}
    for sid, (tip, repo, _role) in lines["tips"].items():
        tasks = [t for t in lines["plan"].get("tasks") or () if isinstance(t, dict) and t.get("subplan_id") == sid]
        if tasks and all(states.get(t.get("id")) in ("completed", "inherited") for t in tasks):
            out[sid] = (tip, repo)
    return out


def projection_subplans(rdir: Path) -> list[dict]:
    durable = durable_versions(rdir)
    if durable is not None:
        return durable
    try:
        data = json.loads((Path(rdir) / PROJECTION).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return []
    rows = data.get("subplans") if isinstance(data, dict) else None
    return [r for r in rows if isinstance(r, dict) and isinstance(r.get("id"), str)] if isinstance(rows, list) else []


def _enrolled(rdir: Path) -> bool:
    """The requirement was planned for verification: it follows the collaborative flow or its SPEC has `## Pruebas` rows.
    Runs planned before this feature are never gated, even when resumed under new code."""
    return (Path(rdir) / ".planning" / "flow.json").is_file() or bool(tests(rdir)) or bool(_load(rdir).get("gated"))


def _reports_subplans(rdir: Path) -> bool:
    if durable_versions(rdir) is not None:
        return True
    try:
        data = json.loads((Path(rdir) / PROJECTION).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return False
    return isinstance(data, dict) and "subplans" in data


def applies(rdir: Path) -> bool:
    """The requirement is enrolled and its run reports subplans (or did once: the flag survives a projection written
    without them or a PLAN.json caught mid-edit, so the gate never fails open)."""
    return _enrolled(rdir) and (bool(_load(rdir).get("gated")) or _reports_subplans(rdir)) and \
        bool(_plan(rdir).get("subplans") or _load(rdir).get("gated"))


def state(rdir: Path) -> dict:
    """Per subplan: `waiting` (not published yet), `to_test`, `approved`, `rejected` or `outdated`, with the version."""
    plan, ledger, facts = _plan(rdir), _load(rdir)["subplans"], published(rdir)
    rows = []
    for item in plan.get("subplans") or []:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            continue
        sid, fact, dec = item["id"], facts.get(item["id"]), ledger.get(item["id"]) or {}
        if not fact:
            st = "waiting"
        elif (dec.get("version"), dec.get("commit")) == (fact.get("version"), fact.get("commit")) and \
                dec.get("decision") in ("approved", "rejected"):
            st = dec["decision"]
        elif dec:
            st = "outdated"
        else:
            st = "to_test"
        rows.append({"id": sid, "title": item.get("title") or sid, "milestone_id": item.get("milestone_id"),
                     "state": st, "version": (fact or {}).get("version"), "commit": (fact or {}).get("commit"),
                     "decision": dec, "ui": bool(item.get("ui")),
                     # a newer version after a rejection: «por probar» again, with what the owner rejected last time
                     "retest": st == "outdated" and dec.get("decision") == "rejected",
                     "solver": solver_reply(rdir, sid, dec) if dec.get("decision") == "rejected" else {},
                     "includes": (fact or {}).get("includes") or [],
                     "fold_conflict": (fact or {}).get("fold_conflict") or {}})
    counts = {k: sum(1 for r in rows if r["state"] == k) for k in STATES_ES}
    return {"applies": applies(rdir), "subplans": rows, "counts": counts, "approved": counts["approved"], "total": len(rows)}


SOLVER_ES = {"pending": "pasó al Solucionador", "queued": "pasó al Solucionador", "running": "el Solucionador lo está "
             "reproduciendo en esa versión", "fixed": "el Solucionador confirmó el fallo y pidió la reparación",
             "answered": "el Solucionador respondió", "asked_owner": "el Solucionador te pregunta algo",
             "gave_up": "el Solucionador no pudo resolverlo", "limit": "el Solucionador ya lo intentó varias veces; queda "
             "para ti", "stale": "", "failed": "el Solucionador no pudo arrancar",
             "resolved": "se resolvió por otra vía; el Solucionador se cerró"}


def rejection_key(sid: str, dec: dict) -> str:
    """The Solucionador's trigger key of one rejection: the subplan, the version and commit it saw, and the note. With
    attached images their digests join the note (in any order), so the same note with other images is a new rejection;
    without images the key is the one it always was (D-258)."""
    import hashlib

    import bt_rejection_images as images
    seed = " ".join(str(dec.get("note") or "").split())
    if images.digests(dec):
        seed += "\n" + "\n".join(images.digests(dec))
    note = hashlib.sha256(seed.encode()).hexdigest()[:12]
    return f"owner_rejected:{sid}:v{dec.get('version')}:{str(dec.get('commit') or '')[:12]}:{note}"


def solver_reply(rdir: Path, sid: str, dec: dict) -> dict:
    """What the Solucionador did with this rejection ({status, text, summary, question}), read from its state
    (`RUN.solver/state.json`, bt_durable.solver); {} when it never got it (no durable run, or it is off)."""
    try:
        data = json.loads((Path(rdir) / "RUN.solver" / "state.json").read_text(encoding="utf-8"))
        item = (data.get("triggers") or {}).get(rejection_key(sid, dec)) or {}
        if not isinstance(item, dict) or not item.get("status"):
            return {}
        session = next((x for x in data.get("sessions") or [] if isinstance(x, dict) and x.get("id") == item.get("session")
                        and x.get("status") != "running"), {})
    except (OSError, UnicodeError, ValueError, AttributeError):
        return {}
    status = str(item["status"])
    return {"status": status, "text": SOLVER_ES.get(status, status), "summary": str(session.get("summary") or ""),
            "question": str(session.get("question") or "")}


def gate(rdir: Path) -> list[str]:
    """What still stops the requirement from being closed; empty when there is nothing to verify or all is approved."""
    st = state(rdir)
    if not st["applies"]:
        return []
    if not st["subplans"]:
        return ["no puedo leer los subplanes del plan; reintenta en unos segundos"]
    return [f"{r['id']}: {STATES_ES[r['state']]}" for r in st["subplans"] if r["state"] != "approved"]


# ------------------------------------------------------------------ decisions

def approval_over_rejection(rdir: Path, sid: str) -> str:
    """Why approving `sid` now needs an explicit confirmation, or "": the owner rejected this very version (D-255).

    An approval closes that rejection's pending items and drains the stages queued behind the subplan, so a stray click
    on «Aprobar» (pictures REQ-021 SP-2 v2, 2026-10-31 13:04, half an hour after its rejection) silently undid it."""
    row = next((r for r in state(rdir)["subplans"] if r["id"] == sid), None)
    if not row or row["state"] != "rejected":
        return ""
    note = str((row.get("decision") or {}).get("note") or "").strip()
    return (f"{sid} versión {row['version']} tiene tu rechazo" + (f" («{note[:120]}»)" if note else "") +
            ". No la aprobé: si ya no aplica, marca «Ya no aplica mi rechazo de esta versión» y aprueba otra vez.")


def decide(project: str, rdir: Path, sid: str, decision: str, note: str = "", by: str = "owner", via: str = "web",
           attachments: list | None = None) -> str:
    """Record the owner's decision on the subplan's current version. A rejection may carry images (D-258):
    `attachments` holds `(client name, bytes)` pairs (the web form) or file paths (the CLI); they are checked by their
    bytes and stored under `<rdir>/evidence/owner-rejected/<SP>-v<N>/` before anything is recorded, and a refusal
    records nothing.

    A rejection is idempotent: the same version and commit, the same note (whitespace aside) and the same images as the
    subplan's standing rejection is the same rejection sent twice (a double click or a resubmitted form: pictures REQ-021
    SP-3 v3, 2026-10-31 15:40:59 and 15:41:03, opened P-212 and P-213). Nothing is rewritten and no second P-item is
    opened; the answer names the existing one. Another note or other images is a new rejection."""
    if decision not in ("approved", "rejected"):
        return "La decisión debe ser aprobar o rechazar."
    if decision == "rejected" and not note.strip():
        return "Para rechazar escribe qué falló."
    row = next((r for r in state(rdir)["subplans"] if r["id"] == sid), None)
    if row is None:
        return f"{sid or 'Ese subplan'} no está en el plan."
    if row["state"] == "waiting":
        return f"{sid} todavía se está construyendo: aún no hay una versión que probar."
    import bt_rejection_images as images
    accepted: list[dict] = []
    if decision == "rejected" and attachments:
        try:
            accepted = images.accept([a if isinstance(a, tuple) else images.from_paths([a])[0] for a in attachments])
        except images.Refused as exc:
            return str(exc)
    stored: list[dict] = []
    with _locked(rdir) as data:                 # the check and the write under one lock: two submits race here
        current = data["subplans"].get(sid) or {}
        if decision == "rejected" and _same_rejection(current, row, note, accepted):
            return _repeated(sid, current)
        try:
            stored = images.store(rdir, sid, row["version"], accepted)
        except images.Refused as exc:
            return str(exc)
        # P-items of rejections no approval has answered yet travel with the subplan's latest decision
        carried = [p for p in current.get("open_pending") or [] if isinstance(p, str)]
        data["subplans"][sid] = {"decision": decision, "version": row["version"], "commit": row["commit"], "by": by,
                                 "via": via, "at": _now(), "note": note.strip()[:1000],
                                 "open_pending": [] if decision == "approved" else carried}
        if stored:
            data["subplans"][sid]["attachments"] = stored
    verb = "Aprobaste" if decision == "approved" else "Rechazaste"
    activity.record(rdir, "Tú", f"{verb} {sid} (versión {row['version']})" + (f": {note.strip()[:120]}" if note.strip() else "")
                    + (f" ({len(stored)} {'imagen' if len(stored) == 1 else 'imágenes'})" if stored else ""),
                    kind="verify", sp=sid)
    left = gate(rdir)
    if decision == "approved":
        for pid in carried:                      # the owner's rejections are answered by this approval
            _close_pending(rdir, pid, f"the owner approved {sid} v{row['version']}")
        try:                                     # stages queued behind this subplan run now (bt_stage_queue)
            import bt_stage_queue
            ran = bt_stage_queue.drain(project, rdir)
        except Exception:  # noqa: BLE001 - the owner's approval stands; the queue says why it could not run
            ran = []
        return f"{sid} aprobado." + (" Todos los subplanes están aprobados: ya se puede fusionar en Revisar." if not left else
                                     f" Faltan {len(left)} por aprobar.") + "".join(f" {m}" for m in ran)
    pid = _open_pending(rdir, sid, row["version"], note.strip(), images.project_relative(rdir, {"attachments": stored}))
    if pid:                                      # the owner-visible record, linked from the Solucionador's trigger
        with _locked(rdir) as data:
            if (data["subplans"].get(sid) or {}).get("note") == note.strip()[:1000]:
                data["subplans"][sid]["pending"] = pid
                data["subplans"][sid]["open_pending"] = [*data["subplans"][sid].get("open_pending", []), pid]
    who = ("; se lo paso al Solucionador: lo reproduce en esta versión y, si confirma el fallo, pide la reparación "
           "al Planner. Cuando se publique la versión nueva te aparecerá aquí «por probar» con tu nota"
           if _solver_takes(rdir) else "; el requisito sigue por verificar")
    saved = (f"Tu nota y {'la imagen quedaron guardadas' if len(stored) == 1 else f'las {len(stored)} imágenes quedaron guardadas'}"
             if stored else "Tu nota quedó guardada")
    return f"{sid} rechazado. {saved}" + (f" y abrí el pendiente {pid}" if pid else "") + who + "."


def _same_rejection(current: dict, row: dict, note: str, accepted: list[dict]) -> bool:
    """`current` is already this rejection: same version and commit, note and image digests (in any order)."""
    import bt_rejection_images as images
    return (current.get("decision") == "rejected" and (current.get("version"), current.get("commit")) ==
            (row["version"], row["commit"]) and " ".join(str(current.get("note") or "").split()) ==
            " ".join(note.strip()[:1000].split()) and images.digests(current) == sorted(a["sha256"] for a in accepted))


def _repeated(sid: str, current: dict) -> str:
    pid = current.get("pending")
    return (f"{sid} ya estaba rechazado con esta misma nota" + (" e imágenes" if current.get("attachments") else "") +
            (f": sigue abierto el pendiente {pid}" if pid else "") + ". No abrí otro.")


def _solver_takes(rdir: Path) -> bool:
    """A rejection reaches the Solucionador: the requirement runs on the durable runtime and the Solucionador is on."""
    try:
        if durable_versions(rdir) is None or not (Path(rdir) / "RUN.durable-run.json").is_file():
            return False
        import bt_config
        return all(bt_config.get(k) is True for k in ("solver.enabled", "healing.enabled", "healing.model_diagnosis",
                                                       "diagnosis.auto"))
    except Exception:  # noqa: BLE001 - the message is a courtesy; the decision stands
        return False


def _open_pending(rdir: Path, sid: str, version: object, note: str, images: list[str] | None = None) -> str:
    """File the rejection in the project's PENDING.md so it is not lost; empty when there is no such file."""
    try:
        pdir = Path(rdir).resolve().parents[1]
        target = pdir / "PENDING.md"
        text = target.read_text(encoding="utf-8")
        if "## Open\n" not in text:
            return ""
        import bt_pending
        from bt_core import next_id
        pid = next_id(pdir, "P")
        item = (f"- {pid} · The owner rejected {sid} v{version} of {_req(rdir)} after trying it: "
                f"{' '.join(note.split())[:400]}"
                + ("".join(f" [imagen {i}]({p})" for i, p in enumerate(images or [], 1)) if images else "")
                + f" · urgency: high · complexity: M · added {dt.date.today().isoformat()} · "
                f"per-subplan verification\n")
        target.write_text(text.replace("## Open\n", "## Open\n" + item, 1), encoding="utf-8")
        bt_pending.sort_file(pdir)
        return pid
    except Exception:  # noqa: BLE001 - the decision itself is already recorded
        return ""


def _close_pending(rdir: Path, pid: str, why: str) -> bool:
    """Close a rejection's P-item (bt_pending moves a CLOSED item to «Recently closed»); False when it is not open."""
    try:
        pdir = Path(rdir).resolve().parents[1]
        target = pdir / "PENDING.md"
        text = target.read_text(encoding="utf-8")
        found = re.search(rf"(?m)^- {re.escape(pid)} · (?!CLOSED)", text)
        if not found:
            return False
        import bt_pending
        target.write_text(text[:found.end()] + f"CLOSED {dt.date.today().isoformat()}: {why} · " + text[found.end():],
                          encoding="utf-8")
        bt_pending.sort_file(pdir)
        return True
    except Exception:  # noqa: BLE001 - the decision itself is already recorded
        return False


# ------------------------------------------------------------------ trying a version on its own

def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=120, env=env, check=False)


def _req(rdir: Path) -> str:
    found = re.match(r"REQ-\d+", Path(rdir).name)
    return found.group(0) if found else Path(rdir).name


def _repo_with(root: Path, project: str, commit: str) -> Path | None:
    import bt_workspace as ws
    for path in ws.repos(root, project).values():
        if _git(Path(path), "cat-file", "-e", f"{commit}^{{commit}}").returncode == 0:
            return Path(path)
    return None


def workdir(root: Path, project: str, req: str, sid: str, version: int | str) -> Path:
    base = Path(os.environ.get("BITACORA_VERIFY_DIR") or Path.home() / ".local" / "share" / "bitacora-verify")
    return base / project / req / f"{sid}-v{version}"


def open_local(root: Path, project: str, rdir: Path, sid: str) -> tuple[Path | None, str]:
    """A detached worktree of exactly the commit the engine published for `sid`, outside every repository."""
    row = next((r for r in state(rdir)["subplans"] if r["id"] == sid), None)
    if row is None or not row["commit"] or not SHA.fullmatch(str(row["commit"])) or not SAFE_ID.fullmatch(sid):
        return None, f"{sid or 'Ese subplan'} todavía no tiene una versión publicada que abrir."
    repo = _repo_with(root, project, row["commit"])
    if repo is None:
        return None, "No encuentro el commit de esa versión en los repos del proyecto."
    target = workdir(root, project, _req(rdir), sid, row["version"])
    if target.exists():
        head = _git(target, "rev-parse", "HEAD").stdout.strip()
        return (target, f"Ya estaba abierto en {target}.") if head == row["commit"] else \
            (None, f"{target} existe pero no está en el commit publicado; ciérralo primero.")
    target.parent.mkdir(parents=True, exist_ok=True)
    _git(repo, "worktree", "prune")                      # a copy deleted by hand must not block opening it again
    done = _git(repo, "worktree", "add", "--detach", str(target), row["commit"])
    if done.returncode != 0:
        return None, "No pude abrir la versión: " + (done.stderr or "").strip()[:200]
    return target, f"Versión {row['version']} de {sid} abierta en {target}."


def close_local(root: Path, project: str, rdir: Path, sid: str) -> str:
    row = next((r for r in state(rdir)["subplans"] if r["id"] == sid), None)
    if row is None or not row["commit"]:
        return f"{sid or 'Ese subplan'} no tiene versión abierta."
    repo = _repo_with(root, project, row["commit"])
    target = workdir(root, project, _req(rdir), sid, row["version"])
    if repo is None or not target.exists():
        return "No había nada abierto."
    done = _git(repo, "worktree", "remove", str(target))        # no --force: edits made while trying it are never discarded
    if done.returncode == 0:
        return "Cerrado."
    return ("La copia tiene cambios sin guardar o archivos nuevos: revísalos y bórrala a mano si no los quieres "
            f"({target}). Git dijo: " + (done.stderr or "").strip()[:160])


def dependents(rdir: Path, sid: str) -> list[str]:
    """Other subplans that build on `sid`: a task that comes after one of its tasks, or one that consumes a contract it
    produces. Reverting `sid` alone is not sound while any of them is accepted."""
    plan = _plan(rdir)
    mine = {t["id"] for t in plan.get("tasks") or [] if isinstance(t, dict) and t.get("subplan_id") == sid}
    produced = {f"{p.get('contract')}@{p.get('version')}" for s in plan.get("subplans") or [] if isinstance(s, dict)
                and s.get("id") == sid for p in s.get("produces") or [] if isinstance(p, dict)}
    out = set()
    for t in plan.get("tasks") or []:
        if isinstance(t, dict) and t.get("subplan_id") not in (None, sid) and mine & set(t.get("after") or []):
            out.add(t["subplan_id"])
    for s in plan.get("subplans") or []:
        if isinstance(s, dict) and s.get("id") != sid:
            consumed = {f"{c.get('contract')}@{c.get('version')}" for c in s.get("consumes") or [] if isinstance(c, dict)}
            if consumed & produced:
                out.add(s["id"])
    return sorted(out, key=lambda x: (len(x), x))


def _line_base(repo: Path, commit: str) -> str | None:
    """The commit this subplan's own line started from: the `-base` ref next to the line ref that points at `commit`."""
    refs = _git(repo, "for-each-ref", "--format=%(refname) %(objectname)", "refs/m3/line/").stdout.splitlines()
    for line in refs:
        name, _, oid = line.partition(" ")
        if oid == commit and not name.endswith("-base"):
            base = _git(repo, "rev-parse", "--verify", "--quiet", f"{name}-base^{{commit}}")
            if base.returncode == 0:
                return base.stdout.strip()
    return None


def revert_command(root: Path, project: str, rdir: Path, sid: str) -> str:
    """The command that would undo this subplan version's own changes; empty when its base cannot be found. It only
    prints: nothing is reverted by the web or the CLI."""
    row = next((r for r in state(rdir)["subplans"] if r["id"] == sid), None)
    if row is None or not row["commit"]:
        return ""
    repo = _repo_with(root, project, row["commit"])
    base = _line_base(repo, row["commit"]) if repo else None
    return f"git -C {repo} revert --no-commit {base}..{row['commit']}" if repo and base else ""


# ------------------------------------------------------------------ projection hook

def on_projection(rdir: Path) -> list[str]:
    """Called after the run projection is written: enrol the run, and tell the owner once per newly published subplan
    version. Never raises. Returns the subplan ids announced."""
    try:
        if not _enrolled(rdir) or not _reports_subplans(rdir):
            return []
        facts, ledger = published(rdir), _load(rdir)
        fresh = sorted(sid for sid, fact in facts.items() if ledger["seen"].get(sid) != f"{fact['version']}:{fact['commit']}")
        if ledger.get("gated") and not fresh:
            return []                                    # nothing changed: no write, no churn in the bitácora
        announced = []
        before = {sid: dec for sid, dec in ledger["subplans"].items() if isinstance(dec, dict)
                  and dec.get("decision") == "rejected" and dec.get("version") != (facts.get(sid) or {}).get("version")}
        if fresh:
            import bt_runutil
            again = "".join(f" {sid}: rechazaste la versión {before[sid].get('version')} («"
                            f"{' '.join(str(before[sid].get('note') or '').split())[:120]}»); comprueba eso en esta."
                            for sid in fresh if sid in before)
            bt_runutil.notify("Subplan listo para probar", f"{Path(rdir).parent.parent.name} · {_req(rdir)}: "
                              + ", ".join(fresh) + ". Ábrelo en la pestaña Plan → Probar." + again)
            announced = fresh
        with _locked(rdir) as data:
            data["gated"] = True
            for sid in announced:
                data["seen"][sid] = f"{facts[sid]['version']}:{facts[sid]['commit']}"
        for sid in announced:
            if sid in before:
                note = " ".join(str(before[sid].get("note") or "").split())[:160]
                text = (f"{sid} versión {facts[sid]['version']} está lista para probar de nuevo: rechazaste la versión "
                        f"{before[sid].get('version')} («{note}»)")
            else:
                text = f"{sid} terminó y está listo para probar"
            activity.record(rdir, "Scheduler", text, kind="verify", sp=sid)
        return announced
    except Exception:  # noqa: BLE001 - observing a run must never break it
        return []
