"""Parallel crash check: two sessions on different repos, SIGKILL the supervisor mid-batch, resume, and verify both
orphaned sessions were ended, nothing was repeated beyond the interrupted tasks and no event is duplicated.
Throwaway root, stub agent. Run by hand: python ops_parallel_check.py"""
import json, os, shutil, signal, subprocess, sys, tempfile, time
from pathlib import Path
SC = str(Path(__file__).resolve().parent)
tmp = Path(tempfile.mkdtemp(prefix="pcrash-"))
root = tmp / "bitacora"; sd = tmp / "stub"; sd.mkdir()
os.environ["BITACORA_ROOT"] = str(root)
sys.path.insert(0, SC)
import bt_core
pdir, _ = bt_core.ensure_project("pcrash")
rdir = pdir / "requirements" / "REQ-001-demo"; rdir.mkdir(parents=True)
(rdir / "SPEC.md").write_text("---\nstatus: approved\n---\n# Demo\n")
(rdir / "PLAN.md").write_text("---\nstatus: approved\n---\n# Plan\n\n## Tasks\n- [ ] T1 — front · repo: frontend\n"
                              "- [ ] T2 — back · repo: backend\n- [ ] T3 — join · after: T1, T2\n")
stub = tmp / "stub.py"
stub.write_text('''
import os, pathlib, subprocess, sys, time
d = pathlib.Path(os.environ["STUB_DIR"]); task = os.environ["BITACORA_TASK"]
c = d / ("count-" + task); n = int(c.read_text()) if c.exists() else 0; c.write_text(str(n + 1))
open(d / "order.log", "a").write(f"{task}:{n}\\n")
if task in ("T1", "T2") and n == 0 and os.environ.get("CRASH") == "1":
    (d / ("started-" + task)).write_text(str(os.getpid())); time.sleep(600)
if task == "FINAL":
    pathlib.Path(os.environ["STUB_RDIR"], "REPORT.md").write_text("# report\\n"); sys.exit(0)
subprocess.run([sys.executable, os.environ["STUB_SCRIPT"], "--project", "pcrash", "task", "done", os.environ["BITACORA_RUN"], task, "--evidence", "stub " + task], check=True)
''')
env = {**os.environ, "STUB_DIR": str(sd), "STUB_RDIR": str(rdir), "STUB_SCRIPT": f"{SC}/bitacora.py",
       "BITACORA_RUN_GRACE_SEC": "1", "BITACORA_RUN_BACKOFF_SEC": "1"}
cmd = [sys.executable, f"{SC}/bitacora.py", "--project", "pcrash", "run", "REQ-001", "--agent", "claude",
       "--agent-cmd", f'"{sys.executable}" "{stub}"', "--no-autostart", "--workers", "2"]
p = subprocess.Popen(cmd, env={**env, "CRASH": "1"}, stdout=open(tmp / "s1.log", "wb"), stderr=subprocess.STDOUT,
                     start_new_session=True)
for _ in range(120):
    if (sd / "started-T1").exists() and (sd / "started-T2").exists(): break
    time.sleep(0.5)
pids = [int((sd / f"started-{t}").read_text()) for t in ("T1", "T2") if (sd / f"started-{t}").exists()]
print("sesiones paralelas en curso:", pids, flush=True)
tracked = json.loads((rdir / "RUN.json").read_text())["heartbeat"].get("session_pids")
os.killpg(p.pid, signal.SIGKILL); p.wait(); time.sleep(1)
def alive(pid):
    try: os.kill(pid, 0); return open(f"/proc/{pid}/stat").read().rsplit(")", 1)[-1].split()[0] != "Z"
    except OSError: return False
orph = [pid for pid in pids if alive(pid)]
print("huérfanos tras el corte:", orph, "| pids registrados:", tracked, flush=True)
r = subprocess.run(cmd + ["--resume"], env=env, stdout=open(tmp / "s2.log", "wb"), stderr=subprocess.STDOUT, timeout=240)
st = json.loads((rdir / "RUN.json").read_text())
order = (sd / "order.log").read_text().split()
left = [pid for pid in pids if alive(pid)]
ev = []
for f in (root / ".state" / "events").glob("attempts-*.jsonl"):
    ev += [json.loads(l) for l in f.read_text().splitlines()]
ids = [e["event_id"] for e in ev]
print("orden:", order, "| estado:", st["status"], {t["id"]: t["status"] for t in st["tasks"]})
checks = {
  "ambas sesiones corrían a la vez": len(pids) == 2,
  "el corte las dejó huérfanas": len(orph) == 2,
  "los dos pids estaban registrados": sorted((tracked or {}).values()) == sorted(pids),
  "al reanudar no queda ninguna viva": not left,
  "termina en done": r.returncode == 0 and st["status"] == "done",
  "T1 y T2 se reintentan una vez": order.count("T1:1") == 1 and order.count("T2:1") == 1 and "T1:2" not in order,
  "T3 y FINAL una sola vez": order.count("T3:0") == 1 and order.count("FINAL:0") == 1,
  "sin eventos duplicados": len(ids) == len(set(ids)),
}
for k, v in checks.items(): print(("PASS " if v else "FAIL ") + k)
for pid in left:
    try: os.kill(pid, signal.SIGKILL)
    except OSError: pass
shutil.rmtree(tmp, ignore_errors=True)
print("\nRESULT", "OK" if all(checks.values()) else "FALLA")
