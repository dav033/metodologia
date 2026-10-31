"""Notices for the dedicated Planner that count as delivered only when it can act on them (pictures REQ-021, 2026-10-30).

16:25 the operator's `tell-planner` printed «Enviado al Planner.» while the Planner's Codex account answered the
request with «■ You've hit your usage limit … try again at 4:32 PM»; nobody was told and the request was lost.
`bt_agent_terminal.send` now says when a wall answers a message (and answers Codex's harmless model-switch modal);
here the Planner leaves that account for one with quota (the way `start_planner` starts any Planner, conversation
included), or, when no account has quota, the notice is held in the plan (`bt_agent_wall.HELD`) and the engine's
maintenance pass sends it again when the reset time shown passes (`deliver_held`).
"""
from __future__ import annotations

import re
import time
from pathlib import Path

import bt_agent_terminal as terminal
import bt_agent_wall as wall

WEB_NOTICE = "[Automatic notice from the web, not typed by the owner] "
HOLD_MINUTES = 30                                     # when a wall does not say when it ends: try again this often


def _rdir(project: str, req: str) -> Path | None:
    from bt_core import ROOT
    return next(iter(sorted((Path(ROOT) / project / "requirements").glob(f"{req}-*"))), None)


def tell(project: str, req: str, notice: str, *, retry: bool = False) -> tuple[str, str]:
    """Deliver `notice` to the running Planner so it can act on it. Returns (state, Spanish text): sent | moved (its
    account ran out: started on another one with quota, conversation and notice included) | held (no account has quota,
    or it waits on the owner: kept and sent again on its own, `deliver_held`) | absent (no Planner runs) | failed.
    A wall already on the screen counts unless its reset time has passed; `retry` (a held notice whose time came) types
    anyway and judges only what answers it."""
    name = terminal.name_for(project, req, "planner")
    if not terminal.exists(name):
        return "absent", f"No hay un Planner en marcha para {project} {req}."
    shown = terminal.screen(name, 20)
    if wall.OWNER_PROMPT.search(shown):
        return _wait_owner(project, req, name, notice)
    hit, until = wall.limited(shown)
    if hit and not retry:
        return after_wall(project, req, notice, until)
    said = terminal.send(name, notice)
    state = getattr(said, "state", "sent" if said == "Enviado." else "error")
    if state == "sent":
        if rdir := _rdir(project, req):
            wall.drop(rdir, [notice])
        extra = "".join(f" ({a})" for a in getattr(said, "answered", ()))
        return "sent", "Enviado al Planner." + extra
    if state == "limited":
        return after_wall(project, req, notice, getattr(said, "until", None))
    if state == "owner":
        return _wait_owner(project, req, name, notice)
    if state == "blocked":
        return _held(project, req, notice, time.time() + 10 * 60, "blocked", f"No le escribí al Planner: {said} "
                     f"Mira su ventana (`tmux -L {terminal.socket()} attach -t {name}`); lo reintento solo")
    return "failed", f"No pude escribirle al Planner de {project} {req}: {said}"


def after_wall(project: str, req: str, notice: str, until: float | None) -> tuple[str, str]:
    """The Planner's account ran out with `notice` undelivered: start it on another account with quota
    (`bt_agent_terminal.start_planner`: its conversation, the notices held for it and this one go along); when none has
    quota, hold it until the reset the wall showed (or the first account the router frees), `HOLD_MINUTES` when neither
    is known."""
    rdir = _rdir(project, req)
    if rdir is None:
        return "failed", f"No encuentro el plan {project} {req}."
    record = terminal._record(rdir)
    avoid = record.get("codex_home", "") if record.get("provider") == "codex" else record.get("config_dir", "")
    route = terminal.planner_route(project, avoid)
    if route.get("exhausted") or route.get("home", "") == avoid:
        frees = float(route["until"]) if route.get("until") else None
        due = min(t for t in (until, frees) if t) if (until or frees) else time.time() + HOLD_MINUTES * 60
        return _held(project, req, notice, max(due, time.time() + 60), "quota",
                     f"El Planner de {req} se quedó sin cuota y ninguna otra cuenta tiene")
    pending = [n["text"] for n in wall.held(rdir) if n["text"] != notice]
    terminal.kill(terminal.name_for(project, req, "planner"))
    ok, message = terminal.start_planner(Path(rdir).parents[2], project, rdir, avoid=avoid, route=route,
                                         message="\n\n".join([*pending, notice]))
    if not ok:
        return _held(project, req, notice, time.time() + 5 * 60, "start",
                     f"El Planner de {req} se quedó sin cuota y no pude abrirlo en otra cuenta ({message})")
    wall.drop(rdir, [*pending, notice])
    _feed(rdir, "El Planner se quedó sin cuota: lo pasé a otra cuenta con los avisos que no había leído")
    return "moved", f"El Planner se quedó sin cuota: lo pasé a otra cuenta con el mensaje. {message}"


def _held(project: str, req: str, notice: str, due: float, why: str, said: str) -> tuple[str, str]:
    rdir = _rdir(project, req)
    if rdir is None:
        return "failed", f"{said}; no encuentro el plan para guardar el mensaje."
    wall.hold(rdir, notice, due, why)
    text = f"{said}: guardé el mensaje y se lo reenvío solo a las {wall.clock(due)}."
    _feed(rdir, text)
    return "held", text


def _wait_owner(project: str, req: str, name: str, notice: str) -> tuple[str, str]:
    """The Planner waits on a question only the owner answers: he is told once; the notice is held and tried again."""
    rdir = _rdir(project, req)
    if rdir is None or not any(n.get("why") == "owner" for n in wall.held(rdir)):
        terminal._ask_owner(project, req, name)
    if rdir is not None:
        wall.hold(rdir, notice, time.time() + 10 * 60, "owner")
    return "held", (f"El Planner de {req} espera que aceptes el modo Bypass Permissions en su cuenta (`tmux -L "
                    f"{terminal.socket()} attach -t {name}`); guardé el mensaje y se lo reenvío cuando pueda leerlo.")


def _feed(rdir: Path, text: str) -> None:
    try:
        import bt_planning_activity as activity
        activity.record(rdir, "Planner", text, kind="flow")
    except Exception:  # noqa: BLE001, S110 - the plan's feed is best effort; the caller reports the same text
        pass


def deliver_held(root: Path, now: float | None = None) -> list[str]:
    """Send again the notices held for a Planner whose time came (the engine's maintenance pass, every 30 s). A Planner
    that is not running is started with them; a plan no longer being planned, or a notice older than
    `bt_agent_wall.HELD_FOR_DAYS`, is dropped and said so in its feed. Returns what it did."""
    from bt_core import _front
    now = time.time() if now is None else now
    said: list[str] = []
    for path in sorted(Path(root).glob("*/requirements/REQ-*/" + wall.HELD)):
        rdir, project = path.parents[1], path.parents[3].name
        req = re.match(r"REQ-\d+", rdir.name)
        notices = wall.held(rdir)
        if not req or not notices:
            continue
        old = [n["text"] for n in notices if now - float(n.get("since") or now) > wall.HELD_FOR_DAYS * 86400]
        if _front(rdir / "PLAN.md", "status") in terminal._DONE or old:
            gone = [n["text"] for n in notices] if _front(rdir / "PLAN.md", "status") in terminal._DONE else old
            wall.drop(rdir, gone)
            _feed(rdir, f"Descarté {len(gone)} aviso(s) que el Planner nunca pudo leer (el plan ya no se planifica o "
                        f"pasaron {wall.HELD_FOR_DAYS} días)")
            said.append(f"{project}/{req.group(0)}: dropped {len(gone)} held notice(s)")
            notices = wall.held(rdir)
        if not notices or min(float(n.get("due") or 0) for n in notices) > now:
            continue
        if not terminal.exists(terminal.name_for(project, req.group(0), "planner")):
            texts = [n["text"] for n in notices]
            ok, _ = terminal.start_planner(Path(root), project, rdir, message="\n\n".join(texts))
            if ok:
                wall.drop(rdir, texts)
            said.append(f"{project}/{req.group(0)}: {'started with' if ok else 'could not start for'} "
                        f"{len(texts)} held notice(s)")
            continue
        for notice in notices:                         # in order; the first that cannot be read stops the rest
            state, _ = tell(project, req.group(0), notice["text"], retry=True)
            said.append(f"{project}/{req.group(0)}: held notice {state}")
            if state != "sent":
                break
    return said
