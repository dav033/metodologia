"""Quota relay, relaunch: type the successor's command into the SAME terminal pane once the old agent is gone.

Multiplexers (detected from the calling session's environment): zellij, tmux, kitty with remote control. With none
of them nothing is typed: the owner gets the exact command and a desktop notification.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import time
from pathlib import Path

import bt_profiles
import bt_relay as relay
import bt_relay_proc as proc

WAIT_MAX = 600           # seconds to wait for the turn to end / the agent to leave
SETTLE = 1.0             # seconds after the old client is gone before typing
EXIT_WAIT = 20           # seconds granted after each signal
POLL = 1.0
PROMPT = ("Continúa el trabajo anterior: lee {path} y sigue desde 'Next'. No repitas lo ya hecho; "
          "verifica el estado con git status.")


class Refused(Exception):
    """The relaunch must not happen; the message is for the log and the owner."""


def notify(title: str, message: str) -> None:
    try:
        import bt_notify
        bt_notify.notify(title, message)
    except Exception:
        pass


KITTY_HELP = ("kitty remote control is off. Add these two lines to kitty.conf and restart kitty: "
              "`allow_remote_control yes` and `listen_on unix:/tmp/kitty`")


def detect_mux(environ: dict) -> dict | None:
    import bt_relay_client
    return bt_relay_client.mux_from_env(environ)


def _json_of(argv: list[str], env: dict, runner) -> object:
    try:
        done = runner(argv, capture_output=True, text=True, timeout=10, env=env)
    except (OSError, subprocess.SubprocessError) as exc:
        raise Refused(f"{argv[0]} failed ({type(exc).__name__})" + (f". {KITTY_HELP}" if argv[0] == "kitty" else "")) from exc
    if done.returncode != 0:
        raise Refused(f"{' '.join(argv[:3])} failed" + (f". {KITTY_HELP}" if argv[0] == "kitty" else ""))
    return done.stdout


def _walk(node):
    yield node
    if isinstance(node, dict):
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk(value)


def preflight(kind: str, target: str, env: dict, pid: int, runner=subprocess.run) -> None:
    """Before the old client is closed: the multiplexer can be driven, the pane EXISTS and (where the multiplexer
    says so) it belongs to the client that will be closed. Anything unproven raises Refused (manual fallback)."""
    if not shutil.which(kind):
        raise Refused(f"'{kind}' is not on PATH: nothing could be typed")
    family = set(proc.ancestors(pid))
    if kind == "tmux":
        out = _json_of(["tmux", "display", "-p", "-t", target, "#{pane_pid}"], env, runner).strip()
        if not out.isdigit() or int(out) not in family:
            raise Refused(f"tmux pane {target} is not proven to belong to the client (pane pid {out or '?'})")
    elif kind == "kitty":
        try:
            data = json.loads(_json_of(["kitty", "@", "ls"], env, runner))
        except ValueError as exc:
            raise Refused("kitty @ ls returned unreadable output") from exc
        windows = [w for w in _walk(data) if isinstance(w, dict) and str(w.get("id")) == str(target)
                   and ("foreground_processes" in w or "pid" in w)]
        if len(windows) != 1:
            raise Refused(f"kitty window {target} was not found exactly once")
        w = windows[0]
        owners = {p.get("pid") for p in w.get("foreground_processes") or [] if isinstance(p, dict)} | {w.get("pid")}
        if not owners & family:
            raise Refused(f"kitty window {target} is not proven to belong to the client")
    elif kind == "zellij":
        try:
            data = json.loads(_json_of(["zellij", "action", "list-panes", "--json"], env, runner))
        except ValueError as exc:
            raise Refused("zellij list-panes returned unreadable output") from exc
        number = target.split("_", 1)[-1]
        panes = [d for d in _walk(data) if isinstance(d, dict) and str(d.get("id")) in (number, target)
                 and not d.get("is_plugin")]
        if not panes:
            raise Refused(f"zellij pane {target} was not found (ownership is proven only by the client's environment)")


def send_steps(kind: str, target: str, text: str) -> list[tuple[list[str], str | None]]:
    """[(argv, stdin)] that type `text` into the pane and press Enter."""
    if kind == "zellij":
        return [(["zellij", "action", "write-chars", "--pane-id", target, text], None),
                (["zellij", "action", "write", "--pane-id", target, "13"], None)]
    if kind == "tmux":
        return [(["tmux", "send-keys", "-t", target, "-l", text], None),
                (["tmux", "send-keys", "-t", target, "Enter"], None)]
    if kind == "kitty":  # --stdin sends the text as is; an argument would have its backslashes interpreted
        match = f"id:{target}"
        return [(["kitty", "@", "send-text", "--match", match, "--stdin"], text),
                (["kitty", "@", "send-text", "--match", match, "\\r"], None)]
    raise Refused(f"unknown multiplexer '{kind}'")


def quote(value: str) -> str:
    """Single-quoted word valid in bash AND fish: fish gives backslash meaning inside single quotes, so a value that
    holds one (or a control character) is refused instead of being typed wrongly."""
    if "\\" in value or re.search(r"[\x00-\x1f\x7f]", value):
        raise Refused(f"cannot type {value!r} safely into fish and bash")
    return shlex.quote(value)


def successor_spec(profile: str, cwd: str, handoff: Path, strict: bool = False) -> dict:
    """What starts the successor: argv list (binary, prompt), the account selectors to set and unset, the cwd. `strict`
    (wrapper path, which runs the list itself) requires an absolute, executable binary."""
    spec = bt_profiles.get(profile)
    name = spec.get("bin") or spec["provider"]
    binary = shutil.which(name)
    if strict and not (binary and os.path.isabs(binary) and os.access(binary, os.X_OK)):
        raise Refused(f"the successor binary '{name}' cannot be resolved")
    if strict and not Path(cwd).is_dir():
        raise Refused(f"successor cwd {cwd} does not exist")
    own = bt_profiles.env_of(profile)
    unset = [key for keys in bt_profiles.ACCOUNT_VARS.values() for key in keys if key not in own]
    return {"argv": [binary or name, PROMPT.format(path=handoff)], "env": own, "unset": unset, "cwd": cwd,
            "profile": profile}


def successor_command(profile: str, cwd: str, handoff: Path) -> str:
    """`cd 'cwd' && env [-u OTHER] K='v' <bin> '<prompt>'`: the typed (secondary/manual) form, one line."""
    spec = successor_spec(profile, cwd, handoff)
    parts = ["env"] + [f"-u {key}" for key in spec["unset"]]
    parts += [f"{key}={quote(value)}" for key, value in spec["env"].items()]
    parts += [quote(word) for word in spec["argv"]]
    return f"cd {quote(cwd)} && {' '.join(parts)}"


def run_steps(steps, runner=subprocess.run, env: dict | None = None) -> None:
    for argv, stdin in steps:
        done = runner(argv, input=stdin, text=True, capture_output=True, timeout=10, env=env)
        if done.returncode != 0:
            raise Refused(f"{argv[0]} failed ({done.returncode}): {(done.stderr or '').strip()[:200]}"
                          + (f" ({KITTY_HELP})" if argv[0] == "kitty" else ""))


def cancelled(stem: str) -> bool:
    return (relay.relay_dir() / "cancelled" / stem).exists()


def cancel() -> str:
    pending = relay.load_json(relay.relay_dir() / "pending.json", {})
    if not pending.get("stem") or (relay.relay_dir() / "launched" / pending["stem"]).exists():
        return "No hay un relevo pendiente."
    relay.write_private(relay.relay_dir() / "cancelled" / pending["stem"], "")
    relay.log(f"cancelled {pending['stem']}")
    relay.record_event("cancelled", handoff=pending.get("handoff"))
    return f"Relevo cancelado ({pending['stem']})."


def claim(stem: str, session: str = "unknown") -> bool:
    """Atomic once-only markers: False when this handoff, or any handoff of this session, was already relaunched, so
    two successors can never be typed for the same session."""
    directory = relay.relay_dir() / "launched"
    relay.private_dir(directory)
    names = [stem] + ([f"session-{session}"] if session != "unknown" else [])
    made = []
    for name in names:
        try:
            os.close(os.open(directory / name, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600))
            made.append(name)
        except FileExistsError:
            for done in made:
                (directory / done).unlink(missing_ok=True)
            return False
    return True


def release(stem: str, session: str) -> None:
    """Undo claim() when nothing was typed or relaunched, so a later attempt is not blocked."""
    for name in (stem, f"session-{session}"):
        (relay.relay_dir() / "launched" / name).unlink(missing_ok=True)


def wait_turn_end(handoff: Path, session: str, sleep=time.sleep, clock=time.monotonic) -> None:
    """Block until the Stop hook reports the end of the turn AFTER the handoff was written (marker newer than the
    file). There is no other signal: without the Stop hook the relay never closes anything by itself."""
    deadline = clock() + WAIT_MAX
    marker = relay.relay_dir() / f"turn-ended-{session}"
    while clock() < deadline:
        if cancelled(handoff.stem):
            raise Refused("cancelled")
        try:
            if handoff.exists() and marker.stat().st_mtime > handoff.stat().st_mtime:
                return
        except OSError:
            pass
        sleep(POLL)
    raise Refused("no end-of-turn marker arrived (is the Stop hook installed?)")


def stop_agent(pid: int, start: int, exit_current: bool, kill=None, sleep=time.sleep, clock=time.monotonic) -> None:
    """End the verified agent (only when the owner allows it) and wait until it is gone."""
    kill = kill or os.kill
    if proc.alive(pid, start) and exit_current:
        if not proc.same_agent(pid, start):
            raise Refused(f"pid {pid} is not the agent recorded at handoff: not signalling it")
        import signal
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                kill(pid, sig)
            except ProcessLookupError:
                break  # already gone: carry on to the launch
            end = clock() + EXIT_WAIT
            while proc.alive(pid, start) and clock() < end:
                sleep(POLL)
            if not proc.alive(pid, start):
                break
    end = clock() + (EXIT_WAIT if exit_current else WAIT_MAX)
    while proc.alive(pid, start) and clock() < end:
        sleep(POLL)
    if proc.alive(pid, start):
        raise Refused(f"the agent (pid {pid}) is still running: nothing is typed into its pane")


def manual(command: str, why: str, handoff: Path) -> None:
    relay.log(f"manual relaunch needed: {why}. Command: {command}")
    relay.record_event("manual", reason=why, handoff=str(handoff))
    notify("Relevo de cuota: hace falta tu acción", f"{why}. Ejecuta: {command}")
    print(f"{why}. Run in the pane of your choice:\n{command}")


def run_wrapper(handoff: Path, to: str, cwd: str, session: str, pid: int, start: int, wrapper: tuple[int, int],
                exit_current: bool, sleep=time.sleep) -> str:
    """Primary path: write the successor for the parent relay_run.py FIRST, wait for the turn to end, then end the client
    (which the wrapper owns); the wrapper starts the successor in the same terminal. Nothing is typed anywhere.
    Raises Refused before the client is touched; a leftover next file is removed on any failure."""
    import bt_relay_client
    spec = successor_spec(to, cwd, handoff, strict=True)
    if not bt_relay_client.verify_wrapper(pid, start, wrapper[0], wrapper[1]):
        raise Refused("the client is not proven to be the child of the relay wrapper")
    path = relay.relay_dir() / f"next-{wrapper[0]}.json"
    claimed = False
    try:
        wait_turn_end(handoff, session, sleep=sleep)
        if not bt_relay_client.verify_wrapper(pid, start, wrapper[0], wrapper[1]):
            raise Refused("the wrapper proof no longer holds")
        if cancelled(handoff.stem):
            raise Refused("cancelled")
        if not claim(handoff.stem, session):  # only the claimant ever writes or removes the next file
            return "skipped"
        claimed = True
        # written only after the turn ended and the once-only claim: a voluntary exit earlier relays nothing
        relay.write_private(path, json.dumps({**spec, "stem": handoff.stem, "created": time.time(), "client": pid}))
        stop_agent(pid, start, exit_current, sleep=sleep)
        relay.log(f"relay handed to wrapper {wrapper[0]}: {to} ({handoff.stem})")
        relay.record_event("launched", profile_to=to, mux="wrapper", handoff=str(handoff))
        return "wrapper"
    except BaseException:
        path.unlink(missing_ok=True)
        if claimed:
            release(handoff.stem, session)
        raise


def run(handoff: Path, to: str, cwd: str, session: str, mux: str | None, target: str | None, pid: int | None,
        start: int | None, exit_current: bool, runner=subprocess.run, sleep=time.sleep,
        mux_env: dict | None = None, wrapper: tuple[int, int] | None = None) -> str:
    """The detached helper. Returns 'launched' | 'manual' | 'skipped' | 'cancelled' | 'failed'. Whatever goes wrong
    ends in the manual fallback (log, notification, exact command); the old client is only closed after the
    successor command, the multiplexer binary and the pane were validated."""
    if (relay.relay_dir() / "launched" / handoff.stem).exists():
        relay.log(f"skip {handoff.stem}: already relaunched")
        return "skipped"
    if not relay.valid_session(session):
        relay.log(f"refused {handoff.stem}: invalid session id")
        return "failed"
    if relay.supervised() or not relay.settings()["enabled"]:
        relay.log(f"skip {handoff.stem}: relay disabled or supervised session")
        return "skipped"
    try:
        command = successor_command(to, cwd, handoff)
    except (Refused, SystemExit, OSError) as exc:
        relay.log(f"refused {handoff.stem}: {exc}")
        notify("Relevo de cuota: no se pudo preparar", f"{exc}. Handoff: {handoff}")
        return "failed"
    if wrapper and pid is not None and start is not None:
        try:
            return run_wrapper(handoff, to, cwd, session, pid, start, wrapper, exit_current, sleep)
        except Refused as exc:
            if str(exc) == "cancelled":
                relay.record_event("cancelled", handoff=str(handoff))
                relay.log(f"cancelled {handoff.stem}")
                return "cancelled"
            relay.log(f"wrapper path failed ({exc}); trying the multiplexer")
            relay.record_event("wrapper_failed", reason=str(exc), handoff=str(handoff))
    try:
        if not mux or not target:
            manual(command, "No detecté zellij, tmux ni kitty en la sesión", handoff)
            return "manual"
        if pid is None or start is None:
            raise Refused("the terminal client was not verified: nothing is closed or typed")
        if not Path(cwd).is_dir():
            raise Refused(f"successor cwd {cwd} does not exist")
        env = {**os.environ, **(mux_env or {})}
        preflight(mux, target, env, pid, runner)
        wait_turn_end(handoff, session, sleep=sleep)
        stop_agent(pid, start, exit_current, sleep=sleep)
        if proc.alive(pid, start):
            raise Refused(f"the agent (pid {pid}) is still running: nothing is typed into its pane")
        if cancelled(handoff.stem):
            raise Refused("cancelled")
        if not claim(handoff.stem, session):
            relay.log(f"skip {handoff.stem}: already relaunched")
            return "skipped"
        sleep(SETTLE)
        run_steps(send_steps(mux, target, command), runner, env)
        relay.log(f"launched {to} in {mux} {target}: {handoff.stem}")
        relay.record_event("launched", profile_to=to, mux=mux, handoff=str(handoff))
        return "launched"
    except Exception as exc:
        if isinstance(exc, Refused) and str(exc) == "cancelled":
            relay.record_event("cancelled", handoff=str(handoff))
            relay.log(f"cancelled {handoff.stem}")
            return "cancelled"
        relay.log(f"failed {handoff.stem}: {type(exc).__name__}: {exc}")
        relay.record_event("failed", reason=f"{type(exc).__name__}: {exc}", handoff=str(handoff))
        manual(command, str(exc) or type(exc).__name__, handoff)
        return "failed"
