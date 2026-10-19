"""Quota relay, core: settings, state, telemetry and the `hook relay` entry point.

When an interactive session's own 5 h window is nearly spent, the hook tells the agent to write a handoff
(bt_relay_handoff) and stop; a helper (bt_relay_launch) then starts the successor in the same terminal pane.
Never active inside marathon/delegated sessions (the supervisor handles limits there) and a no-op unless
`relay.enabled` is true. Everything here fails open: a hook problem must never disturb the session.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path

try:
    import fcntl
except ImportError:  # Windows: no advisory locks, single-writer assumption
    fcntl = None

from bt_core import PYTHON, SCRIPT, STATE

QUOTA_TTL = 120          # seconds a reading of the current profile stays valid
READ_DEADLINE = 6.0      # a prompt is never held longer than this by the probe
REWARN_SECONDS = 600
FAIL_TTL = 60            # a failed/empty reading is remembered this long so a slow network costs one wait, not one per tool call
URGENT_PERCENT = 99
SUPERVISED_VARS = ("BITACORA_RUN", "BITACORA_TASK", "BITACORA_SESSION", "BITACORA_DELEGATION")


def relay_dir():
    return STATE / "relay"


def settings() -> dict:
    import bt_config
    return {"enabled": bt_config.get("relay.enabled", False),
            "threshold": bt_config.get("relay.threshold_percent", 92),
            "exit_current": bt_config.get("relay.exit_current", True),
            "auto": bt_config.get("relay.auto", True)}


def supervised(environ: dict | None = None) -> bool:
    """Marathon and delegated sessions run under a supervisor that already handles usage limits."""
    environ = os.environ if environ is None else environ
    return any(environ.get(k) for k in SUPERVISED_VARS)


SESSION_ID = re.compile(r"^[\w.-]+$")


def valid_session(value) -> bool:
    return isinstance(value, str) and bool(SESSION_ID.match(value)) and value not in (".", "..")


def private_dir(path) -> None:
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        st = path.stat()
        if st.st_uid == os.getuid() and st.st_mode & 0o077:
            path.chmod(0o700)
    except (OSError, AttributeError):
        pass


def write_private(path, text: str, mode: str = "w") -> None:
    """Write with owner-only permissions (handoffs and state may hold summaries of private work)."""
    private_dir(path.parent)
    if mode != "a":  # a pre-created file or symlink is replaced, never written through
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
    flags = os.O_WRONLY | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags | (os.O_APPEND if mode == "a" else os.O_EXCL), 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)


def log(message: str) -> None:
    try:
        write_private(relay_dir() / "relay.log",
                      f"{dt.datetime.now().astimezone().isoformat(timespec='seconds')} {message}\n", "a")
    except OSError:
        pass


def record_event(kind: str, **fields) -> None:
    """Append one row to events/relay-YYYY-MM.jsonl. Never raises."""
    try:
        now = dt.datetime.now().astimezone()
        path = STATE / "events" / f"relay-{now:%Y-%m}.jsonl"
        write_private(path, json.dumps({"ts": now.isoformat(timespec="seconds"), "kind": kind, **fields},
                                       ensure_ascii=False) + "\n", "a")
    except Exception as exc:
        print(f"[relay] event not recorded: {type(exc).__name__}: {exc}", file=sys.stderr)


def load_json(path, default):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, type(default)) else default
    except (OSError, ValueError):
        return default


def save_json(path, data) -> None:
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    write_private(tmp, json.dumps(data, indent=1) + "\n")
    tmp.replace(path)


@contextmanager
def locked(path):
    private_dir(path.parent)
    with os.fdopen(os.open(path.with_name(path.name + ".lock"), os.O_WRONLY | os.O_CREAT, 0o600), "w") as fh:
        if fcntl:
            fcntl.flock(fh, fcntl.LOCK_EX)
        yield


def update_json(path, mutate, default=None) -> dict:
    """Read-modify-write under a lock, so concurrent hooks and helpers never lose each other's updates."""
    with locked(path):
        data = load_json(path, {} if default is None else default)
        mutate(data)
        save_json(path, data)
        return data


def five_hour(row: dict | None) -> tuple[float, float | None] | None:
    """(used percent, reset epoch) of a REAL reading; an error status (HTTP 429 included) is unknown, never a percentage."""
    if not row:
        return None
    window = (row.get("windows") or {}).get("five_hour")
    if row.get("status") == "ok" and isinstance(window, dict) and isinstance(window.get("used_percent"), (int, float)):
        return float(window["used_percent"]), window.get("resets_at")
    return None


def quota_for(profile: str, now: float | None = None, reader=None) -> dict | None:
    """The profile's reading, cached QUOTA_TTL seconds (FAIL_TTL for a failed or empty one), taken within READ_DEADLINE.
    None on any failure."""
    now = time.time() if now is None else now
    path = relay_dir() / "quota-cache.json"
    hit = load_json(path, {}).get(profile)
    if isinstance(hit, dict) and now - float(hit.get("at") or 0) < (QUOTA_TTL if five_hour(hit.get("row")) else FAIL_TTL):
        return hit.get("row")
    if reader is None:
        import bt_profiles
        import bt_quota_live
        spec = bt_profiles.load().get(profile) or {}
        provider = spec.get("provider")
        if provider not in ("claude", "codex"):
            return None
        reader = lambda: bt_quota_live.read_row(profile, provider, timeout=READ_DEADLINE - 1)  # noqa: E731
    box: list = []
    failures: list[str] = []

    def read_quota():
        try:
            box.append(reader())
        except Exception:  # noqa: BLE001 -- optional quota readers fail open with a stable, observable error code
            failures.append("READER_FAILED")

    worker = threading.Thread(target=read_quota, daemon=True)
    worker.start()
    worker.join(READ_DEADLINE)
    row = box[0] if box else None
    error = failures[0] if failures else "READ_TIMEOUT" if worker.is_alive() else None
    if error:
        log(f"quota read failed: {error}")
    try:
        update_json(path, lambda cache: cache.__setitem__(profile, {"at": now, "row": row, "error": error}))
    except OSError:
        pass
    return row


def _message(percent: float, reset: float | None, command: str) -> str:
    when = dt.datetime.fromtimestamp(reset).strftime("%H:%M") if reset else "hora desconocida"
    urgent = percent >= URGENT_PERCENT
    lead = ("URGENTE: la cuota de 5 h de esta cuenta está agotada o a punto de agotarse"
            if urgent else "Aviso del relevo de cuota: la ventana de 5 h de esta cuenta casi se agota")
    return (f"[relevo de cuota] {lead} ({percent:.0f}% usado, se renueva a las {when}). "
            "Termina SOLO el paso atómico en curso" + (" ahora mismo" if urgent else "") +
            ", no hagas commits riesgosos ni empieces nada nuevo. Luego ejecuta este comando pasando por stdin un "
            "resumen en inglés con: qué está hecho, qué sigue (bajo el encabezado 'Next'), archivos tocados, comandos "
            f"verificados y preguntas abiertas:\n{command}\n"
            "Cuando el comando responda, no hagas nada más: termina tu turno. Otra cuenta continuará en este mismo panel. "
            "Avisa al usuario en una sola línea (en español) de que se hace el relevo.")


AUTO_TAIL_BYTES = 200_000
AUTO_QUOTE_CHARS = 1500


def _tail_messages(transcript: str | None) -> tuple[str, str]:
    """(last user text, last assistant text) from the tail of a Claude transcript, bounded. ('', '') when unreadable."""
    try:
        path = Path(transcript or "")
        if not path.is_file():
            return "", ""
        with path.open("rb") as stream:
            start = max(0, path.stat().st_size - AUTO_TAIL_BYTES)
            stream.seek(start)
            lines = stream.read().decode("utf-8", errors="replace").splitlines()
            if start:
                lines = lines[1:]  # the first line of a tail read is usually cut in half
    except OSError:
        return "", ""
    user = assistant = ""
    for line in lines:
        try:
            item = json.loads(line)
        except ValueError:
            continue
        message = item.get("message") if isinstance(item, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, list):
            text = " ".join(c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text")
        else:
            text = content if isinstance(content, str) else ""
        text = text.strip()
        if not text:
            continue
        if item.get("type") == "user" and not text.startswith(("<", "[Request interrupted")):
            user = text
        elif item.get("type") == "assistant":
            assistant = text
    return user[-AUTO_QUOTE_CHARS:], assistant[-AUTO_QUOTE_CHARS:]


def _auto_handoff(payload: dict, sid: str, environ: dict, cfg: dict, now: float, reader=None) -> str:
    """End of turn, quota at or above the threshold and the agent did not hand off by itself: write the handoff from
    what the hook can see (last request, last answer, git state) and let the same launcher machinery run the
    successor. The summary says it was generated, so the successor re-reads the repo state before acting."""
    import bt_quota_live
    profile = bt_quota_live.current_profile(environ)
    if not profile:
        return ""
    found = five_hour(quota_for(profile, now, reader))
    if not found or found[0] < cfg["threshold"]:
        return ""
    percent, reset = found
    user, assistant = _tail_messages(payload.get("transcript_path"))
    cwd = payload.get("cwd") or os.getcwd()
    summary = (f"Relevo AUTOMÁTICO al {percent:.0f}% de la ventana de 5 h (el agente no escribió resumen). Lo que sigue "
               "sale de los últimos mensajes y del estado de git: nada se verificó.\n\n"
               f"Último pedido del usuario:\n{user or '(no disponible)'}\n\n"
               f"Última respuesta del agente:\n{assistant or '(no disponible)'}\n\n"
               "Next: revisa `git status` y los últimos commits, confirma con el usuario si el último pedido quedó "
               "completo y continúa solo desde lo que falte.")
    import bt_relay_handoff
    message = bt_relay_handoff.handoff(summary, sid, None, cwd, environ)
    write_private(relay_dir() / f"turn-ended-{sid}", "")  # this hook IS the end of the turn
    record_event("auto", session=sid, profile=profile, percent=percent)
    return json.dumps({"systemMessage": f"Relevo automático al {percent:.0f}%: {message}"}, ensure_ascii=False)


def evaluate(payload: dict, environ: dict | None = None, now: float | None = None, reader=None) -> str:
    """The hook's stdout ('' for nothing to say). Raises nothing the caller must handle: see hook_main."""
    environ = os.environ if environ is None else environ
    now = time.time() if now is None else now
    cfg = settings()
    if not cfg["enabled"] or supervised(environ):
        return ""
    sid = str(payload.get("session_id") or "unknown")
    if not valid_session(sid):
        return ""
    event = payload.get("hook_event_name") or "UserPromptSubmit"
    state_path = relay_dir() / "warned.json"
    state = load_json(state_path, {})
    entry = state.get(sid) if isinstance(state.get(sid), dict) else {}
    if event == "Stop":
        if entry.get("handoff"):
            write_private(relay_dir() / f"turn-ended-{sid}", "")
            return ""
        if cfg.get("auto", True):
            return _auto_handoff(payload, sid, environ, cfg, now, reader)
        return ""
    if entry.get("handoff") or now - float(entry.get("at") or 0) < REWARN_SECONDS:
        return ""
    import bt_quota_live
    profile = bt_quota_live.current_profile(environ)
    if not profile:
        return ""
    found = five_hour(quota_for(profile, now, reader))
    if not found or found[0] < cfg["threshold"]:
        return ""
    percent, reset = found
    fresh = []

    def mark(data: dict) -> None:
        current = data.get(sid) if isinstance(data.get(sid), dict) else {}
        if current.get("handoff") or now - float(current.get("at") or 0) < REWARN_SECONDS:
            return  # another hook of this session warned first
        for key in [k for k, v in data.items() if not isinstance(v, dict) or now - float(v.get("at") or 0) >= 86400]:
            del data[key]
        data[sid] = {**current, "at": now, "profile": profile, "percent": percent,
                     "cwd": payload.get("cwd") or os.getcwd()}
        fresh.append(True)
    update_json(state_path, mark)
    if not fresh:
        return ""
    record_event("warned", session=sid, profile=profile, percent=percent, event=event)
    command = f"\"{PYTHON}\" \"{SCRIPT}\" relay handoff --session {sid} <<'EOF'\n<resumen>\nEOF"
    return json.dumps({"hookSpecificOutput": {"hookEventName": event,
                                               "additionalContext": _message(percent, reset, command)}},
                      ensure_ascii=False)


def _note_presence(payload: object) -> None:
    """Tell the web view this session is working / idle (independent of the relay settings; never raises)."""
    try:
        if not isinstance(payload, dict):
            return
        import bt_core
        import bt_presence
        cwd = Path(payload.get("cwd") or os.getcwd())
        project = bt_core.resolve_project(cwd, str(payload.get("session_id") or "") or None)
        agent = "codex" if "CODEX_HOME" in os.environ or "codex" in str(os.environ.get("_", "")) else "claude"
        bt_presence.record(bt_core.ROOT, payload, project, agent)
    except Exception as exc:
        log(f"presence error: {type(exc).__name__}: {exc}")


def hook_main(stdin_text: str) -> None:
    """`bitacora.py hook relay`: fail open, exit status 0 and silent on any error."""
    try:
        payload = json.loads(stdin_text) if stdin_text.strip() else {}
        _note_presence(payload)
        out = evaluate(payload if isinstance(payload, dict) else {})
        if out:
            print(out)
    except Exception as exc:
        log(f"hook error: {type(exc).__name__}: {exc}")
