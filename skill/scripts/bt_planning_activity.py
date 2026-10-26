"""What changed while a requirement is being planned: an append-only event log and a snapshot of the plan.

The conversation edits SPEC/PLAN files directly, so nobody announces a change; `observe()` compares PLAN.json and
PLAN.md with the last snapshot (`.planning/snapshot.json`) and logs what moved: new, removed or changed subplans
(outcome, criteria, tasks) and PLAN.md sections. The Designer, the owner's feedback and the translator log their own
events. The web Plan tab shows the log as "lo que cambió en la conversación" and marks changed sections.
"""
from __future__ import annotations

import datetime as dt
import difflib
import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path

DIR = ".planning"
LOG = "activity.jsonl"
SNAPSHOT = "snapshot.json"
KEEP = 400          # events kept in the log
RECENT_SEC = 2 * 3600


def _now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def record(rdir: Path, who: str, text: str, *, kind: str = "plan", sp: str = "", diff: str = "") -> None:
    """Append one event; never raises (logging must not break the action it describes)."""
    try:
        target = Path(rdir) / DIR / LOG
        target.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps({"at": _now(), "who": who, "kind": kind, "sp": sp, "text": text[:400], "diff": diff[:300]},
                          ensure_ascii=False)
        with target.open("a", encoding="utf-8") as stream:
            stream.write(line + "\n")
        if target.stat().st_size > KEEP * 600:
            lines = target.read_text(encoding="utf-8").splitlines()[-KEEP:]
            target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError:
        pass


def events(rdir: Path, limit: int = 30) -> list[dict]:
    """Newest first."""
    try:
        lines = (Path(rdir) / DIR / LOG).read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out = []
    for line in reversed(lines):
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if isinstance(item, dict):
            out.append(item)
        if len(out) >= limit:
            break
    return out


def headings(text: str) -> list[tuple[str, str]]:
    """(key, section text) for PLAN.md: the preamble and every `##`/`###` section, keyed by its heading line."""
    body = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.DOTALL)
    out: list[tuple[str, str]] = []
    for part in re.split(r"(?m)^(?=#{2,3} )", body):
        if not part.strip():
            continue
        first = part.splitlines()[0]
        key = first.lstrip("#").strip() if first.startswith("#") and not first.startswith("# ") else "·"
        while key in dict(out):
            key += "·"
        out.append((key, part))
    return out


def _subplan_view(rdir: Path) -> dict[str, dict]:
    import bt_design_drafts as drafts
    return {s["id"]: {"title": s["title"], "outcome": s["outcome"], "digest": s["digest"],
                      "criteria": [c for c in s["criteria"] if isinstance(c, str)],
                      "tasks": [t.get("title") or "" for t in s["tasks"]]} for s in drafts.subplans(rdir)}


@contextmanager
def _locked(rdir: Path):
    target = Path(rdir) / DIR / ".lock"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a+b") as handle:
        try:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        except (ImportError, OSError):
            pass
        yield


def snapshot(rdir: Path) -> dict:
    try:
        data = json.loads((Path(rdir) / DIR / SNAPSHOT).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _save(rdir: Path, data: dict) -> None:
    target = Path(rdir) / DIR / SNAPSHOT
    fd, tmp = tempfile.mkstemp(prefix=".snapshot.", dir=target.parent)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False)
    os.replace(tmp, target)


def _stamp(rdir: Path) -> list[float]:
    return [(Path(rdir) / name).stat().st_mtime if (Path(rdir) / name).is_file() else 0.0
            for name in ("PLAN.md", "PLAN.json")]


def observe(rdir: Path) -> int:
    """Log what changed in PLAN.json/PLAN.md since the last look; returns the number of events written."""
    stamp = _stamp(rdir)
    if snapshot(rdir).get("stamp") == stamp:
        return 0
    with _locked(rdir):
        old = snapshot(rdir)
        if old.get("stamp") == stamp:
            return 0
        plan = Path(rdir) / "PLAN.md"
        text = plan.read_text(encoding="utf-8") if plan.is_file() else ""
        subplans, sections = _subplan_view(rdir), dict(headings(text))
        before = old.get("sections") or {}
        now, merged = _now(), {}
        for key, body in sections.items():
            prior = before.get(key) or {}
            sha = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
            if prior.get("sha") == sha:
                merged[key] = prior
            else:
                merged[key] = {"sha": sha, "text": body, "prev": prior.get("text", ""), "changed": now if old else ""}
        written = 0
        if old:  # the first look is the baseline: nothing "changed" yet
            written += _log_subplans(rdir, old.get("subplans") or {}, subplans)
            moved = [k for k in sections if merged[k].get("changed") == now and k != "·"]
            if moved:
                record(rdir, "Planner", "PLAN.md: " + ", ".join(f"«{k}»" for k in moved[:3]) +
                       (f" y {len(moved) - 3} más" if len(moved) > 3 else "") + " cambió", kind="doc")
                written += 1
        _save(rdir, {"stamp": stamp, "subplans": subplans, "sections": merged})
        return written


def _log_subplans(rdir: Path, old: dict, new: dict) -> int:
    count = 0
    for sid, item in new.items():
        prior = old.get(sid)
        if prior is None:
            record(rdir, "Planner", f"Nuevo subplan {sid}: {item['title']}", sp=sid)
        elif prior.get("digest") != item["digest"]:
            added = [c for c in item["criteria"] if c not in prior.get("criteria", [])]
            gone = [c for c in prior.get("criteria", []) if c not in item["criteria"]]
            tasks = [t for t in item["tasks"] if t not in prior.get("tasks", [])]
            parts = (["resultado"] if item["outcome"] != prior.get("outcome") else []) + \
                    (["criterios"] if added or gone else []) + (["tareas"] if tasks or
                                                                 len(item["tasks"]) != len(prior.get("tasks", [])) else [])
            diff = (f"+ {added[0]}" if added else f"− {gone[0]}" if gone else f"+ tarea: {tasks[0]}" if tasks else
                    f"+ {item['outcome']}" if "resultado" in parts else "")
            record(rdir, "Planner", f"Actualizó {sid}" + (f" ({', '.join(parts)})" if parts else ""), sp=sid, diff=diff)
        else:
            continue
        count += 1
    for sid in old:
        if sid not in new:
            record(rdir, "Planner", f"Quitó el subplan {sid}", sp=sid)
            count += 1
    return count


def changed_sections(rdir: Path, *, now: float | None = None) -> dict[str, dict]:
    """PLAN.md sections changed in the last couple of hours: heading → {changed, prev, text}."""
    now = dt.datetime.now(dt.UTC).timestamp() if now is None else now
    out = {}
    for key, item in (snapshot(rdir).get("sections") or {}).items():
        try:
            at = dt.datetime.fromisoformat(item.get("changed") or "").timestamp()
        except ValueError:
            continue
        if now - at <= RECENT_SEC:
            out[key] = item
    return out


def line_diff(prev: str, text: str, limit: int = 40) -> list[tuple[str, str]]:
    """(sign, line) pairs of a changed section: '+' added, '-' removed, ' ' kept (context trimmed)."""
    out = []
    for line in difflib.ndiff(prev.splitlines(), text.splitlines()):
        sign, body = line[:1], line[2:]
        if sign in "+- " and body.strip():
            out.append((sign, body))
    changed = [i for i, (sign, _) in enumerate(out) if sign != " "]
    if not changed:
        return []
    keep = {j for i in changed for j in range(i - 1, i + 2)}
    return [item for i, item in enumerate(out) if i in keep][:limit]
