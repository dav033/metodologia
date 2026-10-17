"""Read-only Linux process identity observation and corroboration."""
from __future__ import annotations

from pathlib import Path

from .contracts import ProcessIdentity


def read_linux_process_identity(pid: int, proc_root: Path = Path("/proc")) -> ProcessIdentity | None:
    """Read boot ID and kernel start ticks; unreadable or incomplete proc data stays unknown."""
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        raise ValueError("pid must be a positive integer")
    try:
        stat = (proc_root / str(pid) / "stat").read_text(encoding="ascii")
        boot_id = (proc_root / "sys/kernel/random/boot_id").read_text(encoding="ascii").strip()
    except (OSError, UnicodeError):
        return None
    close = stat.rfind(")")
    if close < 0 or not boot_id:
        return None
    fields = stat[close + 1:].split()
    # Fields after comm start at proc field 3; starttime is proc field 22.
    if len(fields) < 20:
        return None
    if fields[0].upper() in ("Z", "X"):
        return None
    try:
        start_ticks = int(fields[19])
    except ValueError:
        return None
    if start_ticks < 0:
        return None
    return ProcessIdentity("linux", boot_id, pid, start_ticks)


def corroborate_process_identity(expected: ProcessIdentity | None,
                                 observed: ProcessIdentity | None) -> str:
    """Compare only known identity components; never treat a PID alone as confirmation."""
    if expected is None or observed is None:
        return "unknown"
    if expected.pid is None or observed.pid is None:
        return "unknown"
    if expected.pid != observed.pid:
        return "disagreement"
    if expected.platform != observed.platform:
        return "disagreement"
    if expected.host_boot_id is not None and observed.host_boot_id is not None \
            and expected.host_boot_id != observed.host_boot_id:
        return "pid_reuse"
    if expected.start_ticks is not None and observed.start_ticks is not None \
            and expected.start_ticks != observed.start_ticks:
        return "pid_reuse"
    if expected.host_boot_id is None or observed.host_boot_id is None \
            or expected.start_ticks is None or observed.start_ticks is None:
        return "unknown"
    return "match"


__all__ = ["corroborate_process_identity", "read_linux_process_identity"]
