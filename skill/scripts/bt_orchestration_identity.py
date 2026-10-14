"""Foreground identities are separate from native worker session PID bookkeeping."""
from __future__ import annotations

import os
import signal
import socket
from pathlib import Path

import bt_runstate as rs
from bt_orchestration_actions import ActionError


def track(rdir: Path, project: str, state: dict, pid: int | None, instance: str | None) -> None:
    identity = None
    if pid is not None:
        identity = {'pid': pid, 'pgid': os.getpgid(pid), 'sid': os.getsid(pid), 'instance': instance,
                        'start': Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[19],
                        'machine': socket.gethostname(), 'project': project, 'req': state['req']}
    rs.update(rdir, lambda current: current.update(foreground_child=identity))


def recover(rdir: Path, project: str, state: dict) -> None:
    identity = state.get('foreground_child')
    if identity is None:
        return
    if (not isinstance(identity, dict) or identity.get('machine') != socket.gethostname()
            or identity.get('project') != project or identity.get('req') != state['req']
            or type(identity.get('pid')) is not int or identity['pid'] <= 1
            or identity.get('pgid') != identity['pid'] or identity['pid'] == os.getpid()):
        raise ActionError('UNVERIFIED_FOREGROUND_ORPHAN: inspect process on the recorded machine')
    pid = identity['pid']
    stat_path = Path(f'/proc/{pid}/stat')
    if not stat_path.exists():
        try:
            os.killpg(pid, 0)
        except ProcessLookupError:
            track(rdir, project, state, None, None)
            return
        raise ActionError('UNVERIFIED_FOREGROUND_GROUP: leader absent; no unrelated group signalled')
    if not hasattr(os, 'pidfd_open') or not hasattr(signal, 'pidfd_send_signal'):
        raise ActionError('FOREGROUND_ORPHAN_REQUIRES_MANUAL_RECOVERY: pidfd unavailable')
    descriptors: dict[int, int] = {}
    expected = [f'BITACORA_PROJECT={project}', f'BITACORA_RUN={state["req"]}',
                f'BITACORA_ORCHESTRATOR_INSTANCE={identity.get("instance")}']
    try:
        for _ in range(3):
            added = False
            for entry in Path('/proc').iterdir():
                if not entry.name.isdigit() or int(entry.name) in descriptors:
                    continue
                candidate = int(entry.name)
                try:
                    fd = os.pidfd_open(candidate)
                except ProcessLookupError:
                    continue
                try:
                    fields = (entry / 'stat').read_text().rsplit(')', 1)[1].split()
                    if int(fields[2]) != pid:
                        continue
                    env = (entry / 'environ').read_bytes().split(b'\0')
                    if (int(fields[3]) != identity['sid'] or any(value.encode() not in env for value in expected)
                            or (candidate == pid and fields[19] != identity.get('start'))):
                        raise ActionError('UNVERIFIED_FOREGROUND_ORPHAN: no numeric process group signalled')
                    if len(descriptors) >= 128:
                        raise ActionError('FOREGROUND_ORPHAN_PROCESS_CAP')
                    signal.pidfd_send_signal(fd, signal.SIGSTOP)
                    descriptors[candidate], fd, added = fd, None, True
                except (FileNotFoundError, ProcessLookupError):
                    continue
                finally:
                    if fd is not None:
                        os.close(fd)
            if not added:
                break
        else:
            raise ActionError('FOREGROUND_ORPHAN_UNSTABLE_TREE: manual recovery required')
        for fd in descriptors.values():
            try:
                signal.pidfd_send_signal(fd, signal.SIGKILL)
            except ProcessLookupError:
                pass
        track(rdir, project, state, None, None)
    finally:
        for fd in descriptors.values():
            try:
                signal.pidfd_send_signal(fd, signal.SIGCONT)
            except ProcessLookupError:
                pass
            os.close(fd)
