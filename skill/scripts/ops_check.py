"""Host operational checks (Linux, needs tmux and systemd --user): headless job survives its launcher, process-tree
cleanup on timeout, sleep inhibitor lifecycle, loopback-only dashboard, systemd autostart unit. Uses a throwaway root.
Run by hand: python ops_check.py"""
import json, os, shutil, signal, subprocess, sys, tempfile, time
from pathlib import Path
SC = str(__import__("pathlib").Path(__file__).resolve().parent)
sys.path.insert(0, SC)
res = []
def ok(name, cond, detail=""):
    res.append((name, bool(cond), detail)); print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail else ""), flush=True)
def sh(cmd, **kw):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60, **kw)

tmp = Path(tempfile.mkdtemp(prefix="ops-"))
env = {**os.environ, "BITACORA_ROOT": str(tmp / "bitacora")}

# 0. host facts
lg = sh("loginctl show-user $USER -p Linger").stdout.strip()
ok("0a linger habilitado (servicios sobreviven sin sesión)", lg.endswith("yes"), lg)
ok("0b tmux y systemd-run disponibles", shutil.which("tmux") and shutil.which("systemd-run"))
sus = sh("systemctl status sleep.target 2>&1 | head -3").stdout.splitlines()[:2]
print("   sleep.target:", " | ".join(sus))

# 1. headless launch survives the launcher process (the 'SSH drop')
import bt_platform as host
script = tmp / "job.sh"
script.write_text("#!/bin/bash\necho $$ > " + str(tmp / "jobpid") + "\nfor i in $(seq 1 60); do date +%s > " + str(tmp / "beat") + "; sleep 1; done\n"); script.chmod(0o755)
launcher = f'''
import os, sys
sys.path.insert(0, {SC!r}); os.environ.pop("DISPLAY", None); os.environ.pop("WAYLAND_DISPLAY", None)
import bt_platform as host; from pathlib import Path
print(host.open_terminal(Path({str(tmp)!r}), Path({str(script)!r}), "ops check job"))
'''
r = subprocess.run([sys.executable, "-c", launcher], capture_output=True, text=True, env={k: v for k, v in os.environ.items() if k not in ("DISPLAY", "WAYLAND_DISPLAY")})
ok("1a lanzador headless abre sesión tmux", r.returncode == 0, (r.stdout + r.stderr).strip()[:120])
time.sleep(2)
t0 = (tmp / "beat").read_text().strip() if (tmp / "beat").exists() else ""
time.sleep(3)
t1 = (tmp / "beat").read_text().strip() if (tmp / "beat").exists() else ""
ok("1b el job sigue vivo tras terminar el proceso lanzador (latido avanza)", t0 and t1 and t1 > t0, f"{t0}->{t1}")
ok("1c la sesión es adjuntable", "ops-check-job" in sh("tmux ls").stdout, sh("tmux ls").stdout.strip()[:80])
sh("tmux kill-session -t ops-check-job")
time.sleep(1)
def alive(pid):
    try:
        os.kill(int(pid), 0); return True
    except (OSError, ValueError):
        return False
jobpid = (tmp / "jobpid").read_text().strip() if (tmp / "jobpid").exists() else ""
ok("1d al matar la sesión no queda el proceso del job", jobpid != "" and not alive(jobpid), f"pid {jobpid}")

# 2. process tree cleanup on timeout (delegation through the real code path)
wd = tmp / "repo"; wd.mkdir(); subprocess.run(["git", "init", "-q"], cwd=wd)
stub = tmp / "tree.py"
stub.write_text("import subprocess, time, os\na = subprocess.Popen(['sleep','300'])\nb = subprocess.Popen(['sh','-c','sleep 300 & wait'])\nopen(%r, 'w').write(' '.join(map(str, [a.pid, b.pid])))\ntime.sleep(300)\n" % str(tmp / "kids"))
cmd = [sys.executable, f"{SC}/bitacora.py", "--project", "ops", "delegate", "start", "tree test", "--agent", "claude",
       "--workdir", str(wd), "--timeout", "0.05", "--agent-cmd", f'"{sys.executable}" "{stub}"']
(tmp / "bitacora" / "ops").mkdir(parents=True)
r = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=120)
try:
    status = json.loads(r.stdout)["status"]
except Exception:
    status = (r.stdout + r.stderr)[-200:]
ok("2a delegación con árbol de procesos termina en timeout", status == "timeout", str(status))
time.sleep(1)
kids = (tmp / "kids").read_text().split() if (tmp / "kids").exists() else []
left = [k for k in kids if alive(k)]
ok("2b no quedan descendientes tras el timeout", kids and not left, f"hijos {kids}, vivos {left}")
for k in left:
    try: os.kill(int(k), signal.SIGKILL)
    except OSError: pass

# 3. keep_awake holds a sleep inhibitor and releases it with the process
holder = subprocess.Popen([sys.executable, "-c", f"import sys; sys.path.insert(0, {SC!r}); import bt_runutil, time; bt_runutil.keep_awake(); time.sleep(8)"],
                          env=env)
time.sleep(3)
inh = sh("systemd-inhibit --list --no-pager 2>&1").stdout
ok("3a keep_awake registra un inhibidor 'metodologia'", "metodologia" in inh, "")
holder.wait(timeout=20); time.sleep(2)
inh2 = sh("systemd-inhibit --list --no-pager 2>&1").stdout
ok("3b el inhibidor se libera al salir el proceso", "marathon running" not in inh2, "")

# 4. dashboard binds to loopback only
port = "8791"
srv = subprocess.Popen([sys.executable, f"{SC}/bitacora.py", "serve", "--port", port], env={**env, "BITACORA_PORT": port},
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(3)
ss = sh(f"ss -ltn 'sport = :{port}'").stdout
ok("4a el dashboard escucha solo en 127.0.0.1", f"127.0.0.1:{port}" in ss and "0.0.0.0" not in ss and "[::]" not in ss, ss.strip().splitlines()[-1] if ss.strip() else "no escucha")
srv.terminate(); srv.wait(timeout=10)

# 5. autostart unit: install, verify enabled, remove, verify gone
import bt_autostart
from pathlib import Path as P
root = tmp / "bitacora"; (root / ".state").mkdir(exist_ok=True)
p = bt_autostart.install("ops", "REQ-999", root, P(SC) / "bitacora.py")
en = sh(f"systemctl --user is-enabled {p.name}").stdout.strip()
ok("5a unit systemd de usuario instalada y habilitada", p.exists() and en == "enabled", f"{p.name}: {en}")
bt_autostart.remove("ops", "REQ-999")
ok("5b la unit se elimina limpiamente", not p.exists() and "No such" not in sh("systemctl --user daemon-reload").stderr,
   sh(f"systemctl --user is-enabled {p.name} 2>&1").stdout.strip())

shutil.rmtree(tmp, ignore_errors=True)
fails = [n for n, c, _ in res if not c]
print(f"\n{len(res) - len(fails)}/{len(res)} OK" + (f"; FALLAN: {fails}" if fails else ""))
