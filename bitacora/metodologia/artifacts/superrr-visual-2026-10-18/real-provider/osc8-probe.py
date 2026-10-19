import os, pty, sys, time, select, re
cmd = sys.argv[1:]
env = dict(os.environ, TERM="xterm-kitty", TERM_PROGRAM="kitty", COLORTERM="truecolor")
pid, fd = pty.fork()
if pid == 0:
    os.execvpe(cmd[0], cmd, env)
import fcntl, termios, struct
fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 40, 140, 0, 0))
buf = b""; sent = False; t0 = time.time()
prompt = b"Reply with exactly this one line and nothing else: see [REQ-005](http://127.0.0.1:8765/go/metodologia/REQ-005) and REQ-006 and http://127.0.0.1:8765/go/P-013\r"
while time.time() - t0 < 100:
    r, _, _ = select.select([fd], [], [], 0.5)
    if r:
        try: d = os.read(fd, 65536)
        except OSError: break
        buf += d
        if b"\x1b[6n" in d: os.write(fd, b"\x1b[1;1R")
    if not sent and time.time() - t0 > 12:
        os.write(fd, prompt[:-1]); time.sleep(1); os.write(fd, b"\r"); sent = True
    if sent and time.time() - t0 > 80: break
try: os.write(fd, b"\x03\x03")
except OSError: pass
time.sleep(1)
open(sys.argv[0] + ".out", "wb").write(buf)
print("bytes", len(buf), "OSC8:", len(re.findall(rb"\x1b\]8;", buf)))
for m in re.findall(rb"\x1b\]8;[^\x07\x1b]*(?:\x07|\x1b\\)", buf)[:6]: print(m)
txt = re.sub(rb"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07\x1b]*(\x07|\x1b\\)", b"", buf)
print(txt[-400:].decode("utf8","replace"))
