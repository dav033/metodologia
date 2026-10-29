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
import re
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


def tests(rdir: Path) -> list[dict]:
    """Rows of every SPEC.md `## Pruebas` (or `## Testing`) table: subplans ([] = every subplan), kind, where, how, expect."""
    try:
        text = (Path(rdir) / "SPEC.md").read_text(encoding="utf-8")
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
                    "expect": index("expect", "qué", "que debes", "esperado")}
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


def projection_subplans(rdir: Path) -> list[dict]:
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
                     "decision": dec, "ui": bool(item.get("ui"))})
    counts = {k: sum(1 for r in rows if r["state"] == k) for k in STATES_ES}
    return {"applies": applies(rdir), "subplans": rows, "counts": counts, "approved": counts["approved"], "total": len(rows)}


def gate(rdir: Path) -> list[str]:
    """What still stops the requirement from being closed; empty when there is nothing to verify or all is approved."""
    st = state(rdir)
    if not st["applies"]:
        return []
    if not st["subplans"]:
        return ["no puedo leer los subplanes del plan; reintenta en unos segundos"]
    return [f"{r['id']}: {STATES_ES[r['state']]}" for r in st["subplans"] if r["state"] != "approved"]


# ------------------------------------------------------------------ decisions

def decide(project: str, rdir: Path, sid: str, decision: str, note: str = "", by: str = "owner", via: str = "web") -> str:
    if decision not in ("approved", "rejected"):
        return "La decisión debe ser aprobar o rechazar."
    if decision == "rejected" and not note.strip():
        return "Para rechazar escribe qué falló."
    row = next((r for r in state(rdir)["subplans"] if r["id"] == sid), None)
    if row is None:
        return f"{sid or 'Ese subplan'} no está en el plan."
    if row["state"] == "waiting":
        return f"{sid} todavía se está construyendo: aún no hay una versión que probar."
    with _locked(rdir) as data:
        data["subplans"][sid] = {"decision": decision, "version": row["version"], "commit": row["commit"], "by": by,
                                 "via": via, "at": _now(), "note": note.strip()[:1000]}
    verb = "Aprobaste" if decision == "approved" else "Rechazaste"
    activity.record(rdir, "Tú", f"{verb} {sid} (versión {row['version']})" + (f": {note.strip()[:120]}" if note.strip() else ""),
                    kind="verify", sp=sid)
    left = gate(rdir)
    if decision == "approved":
        try:                                     # stages queued behind this subplan run now (bt_stage_queue)
            import bt_stage_queue
            ran = bt_stage_queue.drain(project, rdir)
        except Exception:  # noqa: BLE001 - the owner's approval stands; the queue says why it could not run
            ran = []
        return f"{sid} aprobado." + (" Todos los subplanes están aprobados: ya se puede fusionar en Revisar." if not left else
                                     f" Faltan {len(left)} por aprobar.") + "".join(f" {m}" for m in ran)
    pid = _open_pending(rdir, sid, row["version"], note.strip())
    return f"{sid} rechazado. Tu nota quedó guardada" + (f" y abrí el pendiente {pid}" if pid else "") + \
        "; el requisito sigue por verificar."


def _open_pending(rdir: Path, sid: str, version: object, note: str) -> str:
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
                f"{' '.join(note.split())[:400]} · urgency: high · complexity: M · added {dt.date.today().isoformat()} · "
                f"per-subplan verification\n")
        target.write_text(text.replace("## Open\n", "## Open\n" + item, 1), encoding="utf-8")
        bt_pending.sort_file(pdir)
        return pid
    except Exception:  # noqa: BLE001 - the decision itself is already recorded
        return ""


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
        if fresh:
            import bt_runutil
            bt_runutil.notify("Subplan listo para probar", f"{Path(rdir).parent.parent.name} · {_req(rdir)}: "
                              + ", ".join(fresh) + ". Ábrelo en la pestaña Plan → Probar.")
            announced = fresh
        with _locked(rdir) as data:
            data["gated"] = True
            for sid in announced:
                data["seen"][sid] = f"{facts[sid]['version']}:{facts[sid]['commit']}"
        for sid in announced:
            activity.record(rdir, "Scheduler", f"{sid} terminó y está listo para probar", kind="verify", sp=sid)
        return announced
    except Exception:  # noqa: BLE001 - observing a run must never break it
        return []
