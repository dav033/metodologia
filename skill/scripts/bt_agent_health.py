"""Which agents are working, which are quiet and which died: so the owner sees trouble instead of waiting on a corpse.

Two kinds of agent are covered, both started by the methodology:
- background delegations (a Designer, an implementer…): `.state/delegations/<id>/` has TASK.json, CLAIMED (the pid of the
  process running it), session.log (it grows while the agent works) and OUTCOME.json once it is over;
- agents in a tmux session (`bt_agent_terminal`): the Planner and the hands-on subplan sessions.

`agents()` lists them with a state; `problems()` is the subset that needs a look. Read-only, never raises.
"""
from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any

import bt_agent_terminal as terminal

QUIET_S = 15 * 60          # a delegation whose log did not grow for this long is «sin señales» (a Codex agent may think for minutes)
NEVER_STARTED_S = 5 * 60   # TASK.json written but nobody claimed it
FAILED_SHOWN_S = 2 * 3600  # a failed delegation stays visible this long unless a newer one replaced it
STALE_S = 24 * 3600        # nothing older than this is reported (an abandoned run from last week is not today's problem)
LOOKBACK = 40              # newest delegations inspected

STATE_ES = {"working": "trabajando", "quiet": "sin señales", "died": "murió", "exited": "terminó o se cerró",
            "failed": "falló", "never_started": "no llegó a arrancar"}
BAD = {"died", "exited", "failed", "never_started"}


def _read(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _req_of(order: dict) -> tuple[str, str]:
    """(project, REQ-NNN) a delegation works on, when its workdir or task names one."""
    found = re.search(r"REQ-\d+", f"{order.get('workdir', '')} {order.get('task', '')}")
    return str(order.get("project") or ""), found.group(0) if found else ""


def _label(order: dict) -> str:
    role = order.get("role") or order.get("kind") or "agente"
    who = {"designer": "Designer", "implementer": "Implementador", "planner": "Planner", "reviewer": "Revisor",
           "runner": "Runner", "researcher": "Investigador", "explorer": "Explorador", "antagonist": "Antagonista"}.get(role, role)
    sp = re.search(r"subplan (SP-\d+)", str(order.get("task") or ""))
    return f"{who}{' ' + sp.group(1) if sp else ''}"


def delegations(now: float | None = None) -> list[dict[str, Any]]:
    import bt_delegate
    from bt_runutil import pid_alive
    now = time.time() if now is None else now
    out, seen_ok = [], set()
    try:
        dirs = sorted(bt_delegate.DIR.glob("D-*"), reverse=True)[:LOOKBACK]
    except OSError:
        return []
    for d in dirs:
        order, outcome = _read(d / "TASK.json"), _read(d / "OUTCOME.json")
        if not order:
            continue
        project, req = _req_of(order)
        key = (str(order.get("task") or "")[:60], project)
        base = {"id": d.name, "kind": "delegation", "who": _label(order), "project": project, "req": req,
                "model": f"{order.get('profile') or ''} {order.get('model') or ''}".strip()}
        try:
            log_at = (d / "session.log").stat().st_mtime
        except OSError:
            log_at = 0.0
        created = order.get("created") or ""
        try:
            import datetime as dt
            started = dt.datetime.fromisoformat(created).timestamp() if created else log_at
        except ValueError:
            started = log_at
        if outcome:
            ended = (d / "OUTCOME.json").stat().st_mtime
            if outcome.get("status") in ("failed", "timeout") and now - ended < FAILED_SHOWN_S and key not in seen_ok:
                out.append({**base, "state": "failed", "since": now - ended,
                            "detail": str(outcome.get("summary") or outcome.get("status") or "")[:160]})
            else:
                seen_ok.add(key)             # a newer delegation of the same task finished: older failures no longer matter
            continue
        try:
            owner = int((d / "CLAIMED").read_text().strip() or 0)
        except (OSError, ValueError):
            owner = 0
        if now - (log_at or started) > STALE_S:
            continue
        if not owner:
            if now - started > NEVER_STARTED_S and key not in seen_ok:
                out.append({**base, "state": "never_started", "since": now - started, "detail": "nadie tomó la tarea"})
            continue
        if not pid_alive(owner):
            if key in seen_ok:
                continue                     # a newer run of the same task replaced it
            out.append({**base, "state": "died", "since": now - (log_at or started),
                        "detail": "su proceso desapareció sin dejar resultado (por ejemplo, al reiniciar un servicio)"})
            continue
        idle = now - (log_at or started)
        seen_ok.add(key)                     # this one is alive: older runs of the same task are history
        out.append({**base, "state": "quiet" if idle > QUIET_S else "working", "since": idle, "age": now - started,
                    "detail": f"última señal hace {int(idle // 60)} min" if idle >= 90 else "activo"})
    return out


def tmux_agents(now: float | None = None) -> list[dict[str, Any]]:
    """Agents in the methodology's tmux server: alive when their pane still has a `claude` or `codex` child."""
    try:
        rows = terminal._run("list-panes", "-a", "-F", "#{session_name}\t#{pane_pid}").stdout.splitlines()
    except (RuntimeError, OSError, subprocess.SubprocessError):
        return []
    out = []
    for row in rows:
        name, _, pid = row.partition("\t")
        if not name.startswith("bit-") or not pid.isdigit():
            continue
        try:
            kids = subprocess.run(["ps", "--ppid", pid, "-o", "args="], capture_output=True, text=True, timeout=5).stdout
        except (OSError, subprocess.SubprocessError):
            continue
        alive = bool(re.search(r"\b(claude|codex)\b", kids))
        project = name.split("-")[1] if name.count("-") >= 2 else ""
        found = re.search(r"REQ-\d+", name)
        req = found.group(0) if found else ""
        role = "Planner" if name.endswith("-planner") else "Sesión con el usuario" if "-hands-" in name or "-auto-" in name else "Agente"
        out.append({"id": name, "kind": "tmux", "who": role, "project": project, "req": req,
                    "state": "working" if alive else "exited", "since": 0.0,
                    "detail": "" if alive else "el agente ya no corre; la terminal quedó abierta sin él"})
    return out


def agents(now: float | None = None) -> list[dict[str, Any]]:
    try:
        return delegations(now) + tmux_agents(now)
    except Exception:  # noqa: BLE001 - health must never break the page it decorates
        return []


def problems(now: float | None = None, req: str = "", project: str = "") -> list[dict[str, Any]]:
    rows = [a for a in agents(now) if a["state"] in BAD or a["state"] == "quiet"]
    if req:
        rows = [a for a in rows if a["req"] == req and (not project or a["project"] == project)]
    rows.sort(key=lambda a: (a["state"] not in BAD, a["since"]))
    return rows


def active_for(req: str, project: str, now: float | None = None) -> list[dict[str, Any]]:
    """Delegations working on this requirement right now (a Designer, for instance), for the Plan tab."""
    return [a for a in delegations(now) if a["req"] == req and a["project"] == project and a["state"] in ("working", "quiet")]


def ago(seconds: float) -> str:
    seconds = max(0, int(seconds))
    if seconds < 60:
        return "hace menos de 1 min"
    minutes = seconds // 60
    return f"hace {minutes} min" if minutes < 90 else f"hace {minutes // 60} h"


# ------------------------------------------------------------------ what a delegation is doing right now

def _short(text: str, limit: int = 130) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _command_summary(cmd: str) -> str:
    """«cat > x.html <<…» → «Escribe x.html»; «sed -n … file» → «Lee file»; anything else: the command, shortened."""
    body = re.sub(r"^(/usr/bin/)?bash -lc ['\"]?", "", cmd.strip())
    script = re.match(r"(node|python3?|bash|sh)\s+<<", body)
    if script:
        return f"Ejecuta un script ({script.group(1)})"
    wrote = re.match(r"cat\s*>+\s*(\S+)", body)
    if wrote:
        return "Escribe " + Path(wrote.group(1)).name
    read = re.match(r"(?:sed -n\s+\S+|cat|head(?: -n \d+)?|tail(?: -n \d+)?|rg|grep(?: -[a-zA-Z]+)*)\s+.*?([\w./@-]+\.\w{1,5})", body)
    if read:
        return "Lee " + Path(read.group(1)).name
    return "Ejecuta " + _short(body, 90)


def activity(did: str, limit: int = 6, tail_bytes: int = 400_000) -> list[str]:
    """The last things a delegation did, newest first, from its log: Codex narration, commands and patches, or the
    tool calls of a Claude stream. Best effort: an unreadable or unknown log gives an empty list."""
    import bt_delegate
    try:
        log = bt_delegate.path_of(did) / "session.log"
        size = log.stat().st_size
        with log.open("rb") as stream:
            stream.seek(max(0, size - tail_bytes))
            lines = stream.read().decode("utf-8", errors="replace").splitlines()
    except (OSError, SystemExit):
        return []
    out: list[str] = []
    i = len(lines) - 1
    while i >= 0 and len(out) < limit:
        line = lines[i]
        if line.startswith("{"):                                   # Claude stream-json
            try:
                event = json.loads(line)
            except ValueError:
                i -= 1
                continue
            for block in reversed(((event.get("message") or {}).get("content") or []) if event.get("type") == "assistant" else []):
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    inp = block.get("input") or {}
                    target = inp.get("file_path") or inp.get("command") or inp.get("pattern") or ""
                    out.append(f"{block.get('name')}: {_short(str(target), 100)}")
                elif isinstance(block, dict) and block.get("type") == "text" and block.get("text", "").strip():
                    out.append(_short(block["text"]))
        elif line == "codex" and i + 1 < len(lines) and lines[i + 1].strip():
            out.append(_short(lines[i + 1]))
        elif line == "exec" and i + 1 < len(lines):
            out.append(_command_summary(lines[i + 1]))
        elif line == "apply patch":
            target = next((x for x in lines[i + 1:i + 6] if x.startswith("/")), "")
            out.append("Edita " + Path(target).name if target else "Aplica un parche")
        i -= 1
    return out[:limit]


def one(did: str, now: float | None = None) -> dict[str, Any] | None:
    return next((a for a in delegations(now) if a["id"] == did), None)
