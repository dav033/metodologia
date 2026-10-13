"""Marathon supervisor helpers: console status line, notifications, autostart, bitácora commit, heartbeat, waits."""
from __future__ import annotations

import shutil
import subprocess
import time

from bt_core import *  # noqa: F403
import bt_platform as host
import bt_runstate as rs

POLL = 30


def say(state: dict | None, text: str) -> None:
    prog = "{}/{}".format(*rs.progress(state)) if state else "-"
    print(f"[{dt.datetime.now():%m-%d %H:%M:%S}] {prog} {text}", flush=True)


def notify(title: str, message: str) -> None:
    try:
        import bt_notify
        bt_notify.notify(title, message)
    except Exception:
        pass


def autostart(action: str, project: str, req: str) -> None:
    try:
        import bt_notify
        (bt_notify.install_autostart if action == "install" else bt_notify.remove_autostart)(project, req)
    except Exception as exc:
        print(f"[run] autostart {action} failed: {exc}", file=sys.stderr)


def commit_bitacora(project: str, message: str) -> None:
    try:
        from bt_vcs import commit
        commit(ROOT, f"{project}: {message}")
    except Exception as exc:
        print(f"[run] bitacora commit failed: {exc}", file=sys.stderr)


def pid_alive(pid: int) -> bool:
    if os.name == "nt":
        import ctypes
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, int(pid))
        if not handle:
            return False
        code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(handle)
        return code.value == 259
    try:
        os.kill(int(pid), 0)
        return True
    except PermissionError:
        return True  # exists, owned by another user
    except OSError:
        return False


_inhibitor: "subprocess.Popen | None" = None


def keep_awake() -> None:
    """Stop the machine from sleeping while the supervisor runs (best effort, never raises)."""
    global _inhibitor
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
        except Exception:
            pass
    elif _inhibitor is None:
        argv = host.sleep_inhibitor_argv(sys.platform, os.getpid())
        if argv:
            try:
                _inhibitor = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                              stderr=subprocess.DEVNULL, start_new_session=True)
            except OSError:
                pass




def beat(rdir: Path, **fields) -> dict:
    return rs.update(rdir, lambda s: rs.heartbeat(s, **fields))


def set_fields(rdir: Path, **fields) -> dict:
    return rs.update(rdir, lambda s: s.update(fields))


def backoff_override() -> float | None:
    """BITACORA_RUN_BACKOFF_SEC: tiny usage-limit backoff for tests (seconds)."""
    try:
        return float(os.environ["BITACORA_RUN_BACKOFF_SEC"])
    except (KeyError, ValueError):
        return None


def wait_or_control(rdir: Path, seconds: float | None, label: str, ignore: str | None = None) -> str | None:
    """Sleep in short slices, heartbeating; returns early with the control value if the user sets one.
    seconds=None waits until the control changes (a pause waits for `ignore`='pause' to go away)."""
    end = time.time() + seconds if seconds is not None else None
    poll = min(POLL, 1) if backoff_override() is not None else POLL
    while end is None or time.time() < end:
        beat(rdir, state=label)
        control = (rs.load(rdir) or {}).get("control")
        if control and control != ignore:
            return control
        if ignore and not control:
            return None
        time.sleep(poll if end is None else min(poll, max(0.2, end - time.time())))
    return None
