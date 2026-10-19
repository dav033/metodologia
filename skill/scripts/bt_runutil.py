"""Run helpers shared by delegation and the Scheduler: console status line, notifications, autostart, heartbeat, sleep inhibitor."""
from __future__ import annotations

import subprocess

from bt_core import *  # noqa: F403
import bt_platform as host
import bt_runstate as rs


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
