"""Real PTY harness and controlled subprocess fixtures for lifecycle tests."""
from __future__ import annotations

import json
import os
import pty
import select
import signal
import sys
import tempfile
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
CHILD = '''
import json, os, signal, sys, termios, time, uuid
package = json.load(sys.stdin)
fd = os.open('/dev/tty', os.O_RDWR)
attrs = termios.tcgetattr(fd)
attrs[3] &= ~termios.ECHO
termios.tcsetattr(fd, termios.TCSANOW, attrs)
row = dict(pid=os.getpid(), ppid=os.getppid(), sid=os.getsid(0), pgid=os.getpgrp(),
           foreground=os.tcgetpgrp(fd), tty=os.ttyname(fd), session_id=str(uuid.uuid4()),
           instance=os.environ['BITACORA_ORCHESTRATOR_INSTANCE'], package=package)
with open(os.environ['ROWS'], 'a') as out:
    out.write(json.dumps(row) + '\\n')
if package.get('overflow'):
    print('x' * 10000, flush=True)
elif package.get('hang'):
    signal.signal(signal.SIGINT, lambda *_: sys.exit(130))
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    while True: time.sleep(.05)
else:
    print(json.dumps(dict(session_id=row['session_id'])), flush=True)
'''


class ForegroundHarness:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.child = self.base / 'child.py'
        self.child.write_text(CHILD)
        self.rows = self.base / 'rows.jsonl'

    def start(self, source: str):
        pid, fd = pty.fork()
        if pid == 0:
            os.environ.update(PYTHONPATH=str(SCRIPTS), ROWS=str(self.rows), CHILD=str(self.child))
            os.execv(sys.executable, [sys.executable, '-c', source])
        self.addCleanup(os.close, fd)
        return pid, fd

    def finish(self, pid: int, fd: int, timeout: float = 8) -> tuple[int, str]:
        deadline, output = time.monotonic() + timeout, b''
        while time.monotonic() < deadline:
            if select.select([fd], [], [], .05)[0]:
                try:
                    output += os.read(fd, 65536)
                except OSError:
                    pass
            done, status = os.waitpid(pid, os.WNOHANG)
            if done:
                return os.waitstatus_to_exitcode(status), output.decode(errors='replace')
        os.kill(pid, signal.SIGKILL)
        os.waitpid(pid, 0)
        self.fail('foreground process failed to exit: ' + output.decode(errors='replace'))

    def wait_rows(self, count: int):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if self.rows.exists():
                rows = self.rows.read_text().splitlines()
                if len(rows) >= count:
                    return [json.loads(row) for row in rows]
            time.sleep(.02)
        self.fail('child did not report its terminal identity')

    def source(self, package: dict, repeat: int = 1, timeout: float = 3):
        return f'''
import json, os, sys, termios
from pathlib import Path
import bt_orchestration_terminal as t
before=termios.tcgetattr(0)
for i in range({repeat}):
    result=t.run_child([sys.executable,os.environ['CHILD']], {package!r}, Path.cwd(),
                       dict(os.environ), timeout={timeout}, output_bytes=1024)
    print('RESULT',json.dumps(result),flush=True)
assert termios.tcgetattr(0)==before, 'termios not restored'
assert os.tcgetpgrp(0)==os.getpgrp(), 'supervisor foreground was not restored'
print('RESTORED',flush=True)
'''
