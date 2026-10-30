#!/usr/bin/env python3
"""Bitácora core: dates, project resolution, templates, file creation, IDs, INDEX.md.

Creates and locates the per-project documentation tree, hands out IDs, keeps INDEX.md
in sync, and implements the Claude Code hooks (SessionStart / Stop / SessionEnd).
The agent writes the content; this script never invents prose.

Layout (root = $BITACORA_ROOT or ~/bitacora):
  <root>/<project>/
    SUMMARY.md ARCHITECTURE.md DECISIONS.md PENDING.md INDEX.md
    requirements/REQ-001-<slug>/SPEC.md, PLAN.md
    2026-10/MONTH.md
    2026-10/W2/WEEK.md
    2026-10/W2/2026-10-08.md          (one file per day, one section per session)

Weeks are week-of-month, Monday-based: W1 is the (possibly partial) week containing day 1.
"""
from __future__ import annotations

import bt_nowindow  # noqa: F401  (no console windows on Windows)

import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import bt_workspace as ws

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

from bt_resources import resource_root  # noqa: E402


SKILL_DIR = resource_root()
PYTHON = Path(sys.executable).as_posix()  # generated commands name the interpreter, never a bare `python`
SCRIPT = Path(__file__).resolve().parent / "bitacora.py"
TEMPLATES = SKILL_DIR / "templates"
ROOT = Path(os.environ.get("BITACORA_ROOT", Path.home() / "bitacora"))
STATE = ROOT / ".state"
CENTRAL = ["SUMMARY.md", "ARCHITECTURE.md", "DECISIONS.md", "PENDING.md", "TOOLS.md", "INDEX.md"]
MUTATING_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
CHAT_TURNS_BEFORE_NUDGE = 12  # assistant turns with no logging before a pure-conversation session gets nudged


# ---------------------------------------------------------------- dates

def today() -> dt.date:
    return dt.date.today()


def week_of_month(d: dt.date) -> int:
    first = d.replace(day=1)
    return (d.day + first.weekday() - 1) // 7 + 1


def day_paths(project_dir: Path, d: dt.date) -> dict:
    month_dir = project_dir / f"{d:%Y-%m}"
    week_dir = month_dir / f"W{week_of_month(d)}"
    return {
        "month_dir": month_dir,
        "month": month_dir / "MONTH.md",
        "week_dir": week_dir,
        "week": week_dir / "WEEK.md",
        "day": week_dir / f"{d:%Y-%m-%d}.md",
    }


# ---------------------------------------------------------------- project resolution

def slugify(text: str, maxlen: int = 40) -> str:
    text = text.lower()
    for a, b in zip("áéíóúüñ", "aeiouun"):
        text = text.replace(a, b)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:maxlen].rstrip("-") or "item"


def _git(cwd: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=5)
    except Exception:
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def _load_bindings() -> dict:
    try:
        return json.loads((STATE / "sessions.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_bindings(data: dict) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    # keep the file small: last 200 sessions
    items = list(data.items())[-200:]
    (STATE / "sessions.json").write_text(json.dumps(dict(items), indent=1), encoding="utf-8")


def register_repo(project: str, repo: Path, role: str | None = None) -> str:
    """Add a repo to the project's workspace (project.json + reverse index). Returns its role."""
    return ws.add_repo(ROOT, project, repo, role)


def project_meta(project: str) -> dict:
    return ws.meta(ROOT, project)


def hq_project(cwd: Path) -> str | None:
    """Inside the bitácora root (the HQ): ROOT/<project>/... -> project; ROOT itself -> None."""
    try:
        rel = Path(cwd).resolve().relative_to(ROOT.resolve())
    except ValueError:
        return None
    return rel.parts[0] if rel.parts and not rel.parts[0].startswith(".") else None


def in_hq(cwd: Path) -> bool:
    try:
        Path(cwd).resolve().relative_to(ROOT.resolve())
        return True
    except ValueError:
        return False


def resolve_project(cwd: Path, session_id: str | None = None, explicit: str | None = None) -> str | None:
    """explicit > $BITACORA_PROJECT (set by the launcher) > session binding > HQ folder > .bitacora marker >
    workspace repo > git repo name > None."""
    if explicit:
        return slugify(explicit, 60)
    if os.environ.get("BITACORA_PROJECT"):
        return slugify(os.environ["BITACORA_PROJECT"], 60)
    if session_id:
        bound = _load_bindings().get(session_id)
        if bound:
            return bound
    if in_hq(cwd):
        return hq_project(cwd)
    in_workspace = ws.project_for_path(ROOT, cwd)
    if in_workspace:
        return in_workspace
    for p in [cwd, *cwd.parents]:
        marker = p / ".bitacora"
        if marker.is_file():
            name = marker.read_text(encoding="utf-8").strip()
            if name:
                return slugify(name, 60)
        if p == Path.home():
            break
    top = _git(cwd, "rev-parse", "--show-toplevel")
    if top:
        url = _git(cwd, "remote", "get-url", "origin")
        if url:
            name = re.sub(r"\.git$", "", url.rstrip("/").split("/")[-1].split(":")[-1])
            if name:
                return slugify(name, 60)
        return slugify(Path(top).name, 60)
    return None


# ---------------------------------------------------------------- templates / creation

def render(name: str, **kw) -> str:
    text = (TEMPLATES / name).read_text(encoding="utf-8")
    for k, v in kw.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text


def ensure_project(project: str) -> tuple[Path, bool]:
    from bt_vcs import ensure_repo
    ensure_repo(ROOT)
    pdir = ROOT / project
    created = not pdir.exists()
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / "requirements").mkdir(exist_ok=True)
    (pdir / "artifacts").mkdir(exist_ok=True)
    for f in CENTRAL:
        target = pdir / f
        if not target.exists() and f != "INDEX.md":
            target.write_text(render(f, project=project, date=today().isoformat()), encoding="utf-8")
    shared_tools = ROOT / "TOOLS.md"  # infrastructure shared by several projects
    if not shared_tools.exists():
        shared_tools.write_text(render("TOOLS.md", project="Shared (all projects)"), encoding="utf-8")
    if created or not (pdir / "INDEX.md").exists():
        write_index(pdir)
    return pdir, created


def ensure_glossary(pdir: Path) -> Path:
    """GLOSSARY.md is created on demand (the first time a term is settled), never empty for every project."""
    target = pdir / "GLOSSARY.md"
    if not target.exists():
        target.write_text(render("GLOSSARY.md", project=pdir.name, date=today().isoformat()), encoding="utf-8")
    return target


def ensure_day(pdir: Path, d: dt.date) -> dict:
    p = day_paths(pdir, d)
    p["week_dir"].mkdir(parents=True, exist_ok=True)
    if not p["month"].exists():
        p["month"].write_text(render("MONTH.md", project=pdir.name, month=f"{d:%Y-%m}"), encoding="utf-8")
    if not p["week"].exists():
        monday = d - dt.timedelta(days=d.weekday())
        start = max(monday, d.replace(day=1))
        end_month = (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1) - dt.timedelta(days=1)
        end = min(monday + dt.timedelta(days=6), end_month)
        p["week"].write_text(
            render("WEEK.md", project=pdir.name, week=f"{d:%Y-%m} W{week_of_month(d)}",
                   start=start.isoformat(), end=end.isoformat()),
            encoding="utf-8")
    if not p["day"].exists():
        p["day"].write_text(f"# {d.isoformat()} — {pdir.name}\n", encoding="utf-8")
    return p


def session_header(session_id: str, cwd: Path) -> str:
    now = dt.datetime.now().strftime("%H:%M")
    branch = _git(cwd, "rev-parse", "--abbrev-ref", "HEAD")
    commit = _git(cwd, "rev-parse", "--short", "HEAD")
    meta = f"session `{session_id[:8]}`"
    if branch:
        meta += f" · branch `{branch}` · start commit `{commit}`"
    return f"\n---\n\n## Session {now} · {meta}\n\n" + render("SESSION.md")


def ensure_session_block(pdir: Path, session_id: str, cwd: Path) -> Path:
    p = ensure_day(pdir, today())
    text = p["day"].read_text(encoding="utf-8")
    if session_id and f"`{session_id[:8]}`" not in text:
        with p["day"].open("a", encoding="utf-8") as fh:
            fh.write(session_header(session_id, cwd))
    return p["day"]


# ---------------------------------------------------------------- IDs

ID_PATTERNS = {
    # only real entries count: "## D-001 — ..." headings and "P-001 · ..." lines (optionally bulleted/struck)
    "D": ("DECISIONS.md", r"^##\s+D-(\d{3,})\b"),
    "P": ("PENDING.md", r"^\s*(?:[-*]\s+)?(?:~~)?P-(\d{3,})\b"),
}


RESERVED = ".ids-reserved.json"     # numbers handed out with `id --reserve` before their entry is written (D-209)


def next_id(pdir: Path, kind: str, *, reserve: str = "") -> str:
    """The next free ID of `kind`. With `reserve` (who/what takes it) the number is recorded in `<project>/.ids-reserved
    .json` under a lock, so a second caller gets the one after it even before the first writes its entry: on
    2026-10-29/30 five sessions and agents picked the same D-NNN from DECISIONS.md and collided four times (D-209)."""
    pdir = Path(pdir)
    if not reserve:
        return _next_id(pdir, kind)
    pdir.mkdir(parents=True, exist_ok=True)
    with open(pdir / f"{RESERVED}.lock", "a+") as lock:
        try:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX)
        except ImportError:                          # Windows: one machine, one caller at a time is assumed
            pass
        found = _next_id(pdir, kind)
        ledger = _reservations(pdir)
        ledger.setdefault(found.split("-")[0], []).append(
            {"id": found, "by": reserve[:200], "at": time.strftime("%Y-%m-%dT%H:%M:%S")})
        tmp = pdir / f".{RESERVED}.tmp"
        tmp.write_text(json.dumps(ledger, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        tmp.replace(pdir / RESERVED)
        return found


def _reservations(pdir: Path) -> dict:
    try:
        data = json.loads((Path(pdir) / RESERVED).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _next_id(pdir: Path, kind: str) -> str:
    found = _next_written_id(pdir, kind)
    prefix, number = found.rsplit("-", 1)
    reserved = [int(item["id"].rsplit("-", 1)[1]) for item in _reservations(pdir).get(prefix, [])
                if isinstance(item, dict) and str(item.get("id", "")).startswith(f"{prefix}-")
                and str(item["id"]).rsplit("-", 1)[1].isdigit()]
    width = len(number)
    return f"{prefix}-{max([int(number) - 1, *reserved]) + 1:0{width}d}"


def _next_written_id(pdir: Path, kind: str) -> str:
    from bt_vcs import pull
    pull(ROOT)  # another machine may have taken the next number
    kind = kind.upper()
    if kind == "REQ":
        nums = [int(m.group(1)) for x in (pdir / "requirements").glob("REQ-*")
                if (m := re.match(r"REQ-(\d+)", x.name))]
        return f"REQ-{max(nums, default=0) + 1:03d}"
    if kind == "P":
        # highest number ever written in the project's own log, not only the open list: closed items may be pruned
        # from PENDING.md, and reusing a number would merge two items in the trace graph
        logs = [pdir / "PENDING.md", *pdir.glob("20*/**/*.md"), *(pdir / "requirements").glob("**/*.md")]
        nums = [int(n) for f in logs if f.is_file()
                for n in re.findall(r"\bP-(\d{3,})\b", f.read_text(encoding="utf-8", errors="ignore"))]
        return f"P-{max(nums, default=0) + 1:03d}"
    fname, pat = ID_PATTERNS[kind]
    f = pdir / fname
    text = re.sub(r"<!--.*?-->", "", f.read_text(encoding="utf-8"), flags=re.S) if f.exists() else ""
    nums = [int(n) for n in re.findall(pat, text, re.M)]
    return f"{kind}-{max(nums, default=0) + 1:03d}"


# ---------------------------------------------------------------- index

def _first_heading(f: Path) -> str:
    try:
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    except Exception:
        pass
    return f.stem


def _front(f: Path, key: str) -> str:
    try:
        m = re.search(rf"^{key}:\s*(.+)$", f.read_text(encoding="utf-8"), re.M)
        return m.group(1).strip() if m else "?"
    except Exception:
        return "?"


def tool_names(f: Path) -> list[str]:
    """`### name` blocks of a TOOLS.md, ignoring the commented example."""
    try:
        text = re.sub(r"<!--.*?-->", "", f.read_text(encoding="utf-8"), flags=re.S)
    except Exception:
        return []
    return re.findall(r"^### (.+)$", text, re.M)


def set_front(f: Path, key: str, value: str) -> None:
    """Set a `key: value` line in the file's front matter (first --- block)."""
    text = f.read_text(encoding="utf-8")
    new, n = re.subn(rf"^{key}:.*$", f"{key}: {value}", text, count=1, flags=re.M)
    if not n:
        new = re.sub(r"^---\n", f"---\n{key}: {value}\n", text, count=1)
    f.write_text(new, encoding="utf-8")


def find_req(pdir: Path, req: str) -> Path:
    matches = sorted((pdir / "requirements").glob(f"{req.upper()}-*"))
    if not matches:
        raise SystemExit(f"{req} not found in {pdir / 'requirements'}")
    return matches[0]


def req_id(rdir: Path) -> str:
    return "-".join(rdir.name.split("-")[:2])


def write_index(pdir: Path) -> Path:
    """Regenerate the project's INDEX.md (navigation map). Implemented in bt_index."""
    from bt_index import project_index
    return project_index(pdir)


def write_global_index() -> Path:
    """Regenerate ~/bitacora/INDEX.md: every project at a glance. Implemented in bt_index."""
    from bt_index import global_index
    return global_index()
