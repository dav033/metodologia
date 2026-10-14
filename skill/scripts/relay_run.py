#!/usr/bin/env python3
"""relay_run: parent launcher of an interactive agent (quota relay, primary path).

    relay_run.py <profile> -- <agent argv...>

Runs the agent as a CHILD in the foreground (it inherits the terminal) and, when it exits, checks for a successor the
relay prepared (<state>/relay/next-<this pid>.json, owner-only, fresh, not cancelled, consumed atomically). If there is
one it runs the successor argv (a list, never a shell string) in the same terminal; otherwise it exits with the child's
exit code. Nothing is ever typed into a terminal. Standard library only: a failure here would block the agent.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(os.environ.get("BITACORA_ROOT", Path.home() / "bitacora"))
STATE = ROOT / ".state"
FRESH_SECONDS = 900
DEFAULT_MAX_CHAIN = 3
ENV_KEYS = re.compile(r"^(CLAUDE_CONFIG_DIR|CODEX_HOME)$")  # only the account selectors may be overlaid
WRAPPER_VAR = "METODOLOGIA_RELAY_WRAPPER"


def relay_dir() -> Path:
    return STATE / "relay"


def max_chain() -> int:
    try:
        value = json.loads((STATE / "config.json").read_text(encoding="utf-8"))["relay"]["max_chain"]
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            return value
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return DEFAULT_MAX_CHAIN


def exit_code(returncode: int | None) -> int:
    if returncode is None:
        return 1
    return 128 - returncode if returncode < 0 else returncode


def take_next(wrapper_pid: int, now: float | None = None) -> dict | None:
    """The successor spec waiting for this wrapper, consumed atomically; None when absent, stale, cancelled,
    foreign or malformed (a bad file is discarded, never half-trusted)."""
    now = time.time() if now is None else now
    path = relay_dir() / f"next-{wrapper_pid}.json"
    taken = path.with_name(path.name + ".consumed")
    try:
        os.rename(path, taken)  # atomic: a second reader (or a second exit) finds nothing
    except OSError:
        return None
    try:
        fd = os.open(taken, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))  # a symlink is refused, not followed
        with os.fdopen(fd, "r", encoding="utf-8") as fh:
            st = os.fstat(fh.fileno())  # the inode actually read
            if st.st_uid != os.getuid() or st.st_mode & 0o077:
                return None
            spec = json.loads(fh.read())
        argv, cwd = spec.get("argv"), spec.get("cwd")
        if not (isinstance(argv, list) and argv and all(isinstance(a, str) and a for a in argv)
                and isinstance(cwd, str) and isinstance(spec.get("created"), (int, float))):
            return None
        if now - spec["created"] > FRESH_SECONDS or spec["created"] > now + 60:
            return None
        stem = spec.get("stem")
        if isinstance(stem, str) and (relay_dir() / "cancelled" / stem).exists():
            return None
        if any("\0" in a for a in argv) or "\0" in cwd or any(
                "\0" in str(v) for v in (spec.get("env") or {}).values()):
            return None
        if not os.path.isabs(argv[0]) or not os.access(argv[0], os.X_OK) or not os.path.isdir(cwd):
            return None
        spec["env"] = {k: v for k, v in (spec.get("env") or {}).items() if ENV_KEYS.match(k) and isinstance(v, str)}
        spec["unset"] = [k for k in (spec.get("unset") or []) if isinstance(k, str) and ENV_KEYS.match(k)]
        return spec
    except (OSError, ValueError, AttributeError, TypeError):
        return None
    finally:
        try:
            taken.unlink()
        except OSError:
            pass


def forward(child, sig: int, same_foreground: bool) -> None:
    """Pass a signal to the child. A terminal-generated SIGINT already reaches the child (same foreground process
    group): forwarding it again would count as a double Ctrl-C."""
    if sig == signal.SIGINT and same_foreground:
        return
    try:
        child.send_signal(sig)
    except (OSError, ProcessLookupError):
        pass


def _same_foreground() -> bool:
    try:
        return os.tcgetpgrp(0) == os.getpgrp()
    except OSError:
        return False


def _install(holder: list) -> None:
    def handler(sig, _frame):
        if holder:
            forward(holder[0], sig, _same_foreground())
    for name in ("SIGINT", "SIGTERM", "SIGHUP", "SIGWINCH"):
        if hasattr(signal, name):
            signal.signal(getattr(signal, name), handler)


def _save_tty():
    try:
        import termios
        return termios, termios.tcgetattr(0)
    except Exception:
        return None, None


def _restore_tty(termios, saved) -> None:
    if saved is not None:
        try:
            termios.tcsetattr(0, termios.TCSADRAIN, saved)
        except Exception:
            pass


def run(profile: str, argv: list[str], popen=subprocess.Popen, environ: dict | None = None, now=time.time,
        err=sys.stderr, install_signals: bool = True) -> int:
    env = dict(os.environ if environ is None else environ)
    env[WRAPPER_VAR] = str(os.getpid())
    env["METODOLOGIA_RELAY_PROFILE"] = profile
    holder: list = []
    if install_signals:
        _install(holder)
    termios, saved = _save_tty()
    chain, cwd, last_code = 0, None, 1
    while True:
        try:
            child = popen(argv, env=env, cwd=cwd)
        except (OSError, ValueError) as exc:  # a successor that cannot start must not take the launcher down
            print(f"\033[2mrelevo de cuota: no se pudo iniciar {argv[0]} ({type(exc).__name__}); salgo\033[0m", file=err)
            return last_code
        holder[:] = [child]
        try:
            child.wait()
        finally:
            holder.clear()
            _restore_tty(termios, saved)
        code = last_code = exit_code(child.returncode)
        spec = take_next(os.getpid(), now())
        if spec is None:
            return code
        if chain >= max_chain():
            print(f"\033[2mrelevo de cuota: tope de {max_chain()} relevos encadenados alcanzado; no continúo\033[0m",
                  file=err)
            return code
        chain += 1
        for key in spec["unset"]:
            env.pop(key, None)
        env.update(spec["env"])
        env["METODOLOGIA_RELAY_PROFILE"] = spec.get("profile") or profile
        argv, cwd, profile = spec["argv"], spec["cwd"], env["METODOLOGIA_RELAY_PROFILE"]
        print(f"\033[2mrelevo de cuota: continúa {profile} ({chain}/{max_chain()})\033[0m", file=err)


def main() -> int:
    args = sys.argv[1:]
    if len(args) < 3 or args[1] != "--":
        print("usage: relay_run.py <profile> -- <agent argv...>", file=sys.stderr)
        return 2
    if not shutil.which(args[2]) and not os.path.exists(args[2]):
        print(f"relay_run: '{args[2]}' not found", file=sys.stderr)
        return 127
    return run(args[0], args[2:])


if __name__ == "__main__":
    sys.exit(main())
