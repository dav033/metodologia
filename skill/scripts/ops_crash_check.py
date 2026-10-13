"""Crash check: SIGKILL a marathon supervisor mid-task, resume, and verify no repeated work, no duplicate events and
no orphaned agent session. Uses a throwaway root and a stub agent. Run by hand: python ops_crash_check.py"""
import json, os, signal, subprocess, sys, tempfile, time, shutil
from pathlib import Path
SC = str(__import__("pathlib").Path(__file__).resolve().parent)
tmp = Path(tempfile.mkdtemp(prefix="crash-"))
root = tmp / "bitacora"; sd = tmp / "stub"; sd.mkdir()
os.environ["BITACORA_ROOT"] = str(root)
sys.path.insert(0, SC)
import bt_core
pdir, _ = bt_core.ensure_project("crash")
rdir = pdir / "requirements" / "REQ-001-demo"; rdir.mkdir(parents=True)
(rdir / "SPEC.md").write_text("---\nstatus: approved\n---\n# Demo\n")
(rdir / "PLAN.md").write_text("---\nstatus: approved\n---\n# Plan\n\n## Tasks\n- [ ] T1 — first\n- [ ] T2 — second · after: T1\n- [ ] T3 — third · after: T2\n")
stub = tmp / "stub.py"
stub.write_text('''
import os, pathlib, subprocess, sys, time
d = pathlib.Path(os.environ["STUB_DIR"]); task = os.environ["BITACORA_TASK"]
c = d / ("count-" + task); n = int(c.read_text()) if c.exists() else 0; c.write_text(str(n + 1))
open(d / "order.log", "a").write(f"{task}:{n}\\n")
if task == "T2" and n == 0 and os.environ.get("CRASH") == "1":
    (d / "t2-started").write_text("1"); time.sleep(600)
if task == "FINAL":
    pathlib.Path(os.environ["STUB_RDIR"], "REPORT.md").write_text("# report\\n"); sys.exit(0)
subprocess.run([sys.executable, os.environ["STUB_SCRIPT"], "--project", "crash", "task", "done", os.environ["BITACORA_RUN"], task, "--evidence", "stub " + task], check=True)
''')
env = {**os.environ, "STUB_DIR": str(sd), "STUB_RDIR": str(rdir), "STUB_SCRIPT": f"{SC}/bitacora.py",
       "BITACORA_RUN_GRACE_SEC": "1", "BITACORA_RUN_BACKOFF_SEC": "1"}
cmd = [sys.executable, f"{SC}/bitacora.py", "--project", "crash", "run", "REQ-001", "--agent", "claude",
       "--agent-cmd", f'"{sys.executable}" "{stub}"', "--no-autostart"]
out = open(tmp / "sup1.log", "wb")
p = subprocess.Popen(cmd, env={**env, "CRASH": "1"}, stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
for _ in range(120):
    if (sd / "t2-started").exists(): break
    time.sleep(0.5)
print("T2 en curso:", (sd / "t2-started").exists(), flush=True)
os.killpg(p.pid, signal.SIGKILL)          # corte brusco: supervisor + sesión, sin limpieza
p.wait(); time.sleep(1)
st = json.loads((rdir / "RUN.json").read_text())
print("tras el corte:", {t["id"]: t["status"] for t in st["tasks"]}, "| status", st["status"], "| sessions", st["sessions"], flush=True)

out2 = open(tmp / "sup2.log", "wb")
r = subprocess.run(cmd + ["--resume"], env=env, stdout=out2, stderr=subprocess.STDOUT, timeout=240)
st = json.loads((rdir / "RUN.json").read_text())
order = (sd / "order.log").read_text().split()
print("tras reanudar: rc", r.returncode, "| status", st["status"], "|", {t["id"]: (t["status"], t.get("attempts")) for t in st["tasks"]}, "| sessions", st["sessions"])
print("orden de ejecución:", order)
ev = []
for f in (root / ".state" / "events").glob("attempts-*.jsonl"):
    ev += [json.loads(l) for l in f.read_text().splitlines()]
ids = [e["event_id"] for e in ev]
print("eventos:", [(e["task"], e["session"], e["result"]) for e in ev], "| duplicados:", len(ids) - len(set(ids)))
checks = {
  "reanuda y termina": r.returncode == 0 and st["status"] == "done",
  "T1 no se repite": order.count("T1:0") == 1 and not any(o.startswith("T1:1") for o in order),
  "T2 se reintenta tras el corte": "T2:1" in order,
  "todas las tareas hechas": all(t["status"] == "done" for t in st["tasks"]),
  "REPORT.md generado": (rdir / "REPORT.md").exists(),
  "sin eventos duplicados": len(ids) == len(set(ids)),
  "sin procesos huérfanos del stub": not subprocess.run(["bash", "-c", f"ps -eo args | grep -F '{stub}' | grep -v grep"], capture_output=True, text=True).stdout.strip(),
}
for k, v in checks.items(): print(("PASS " if v else "FAIL ") + k)
shutil.rmtree(tmp, ignore_errors=True)
print("\nRESULT", "OK" if all(checks.values()) else "FALLA")
