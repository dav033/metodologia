"""Full flow check (P-002) with a REAL Claude agent, so it spends subscription quota (a few haiku sessions):
project + two repos -> requirement -> question round answered through the web form -> plan approved through the web
(which launches the marathon in a tmux session) -> supervised run to done -> files, PLAN ticks, REPORT.md, telemetry,
bitácora commits and removal of the login-resume entry. Throwaway root; run by hand: python ops_e2e_check.py
Needs: claude logged in, tmux, a free local port 8796."""
import json, os, shutil, subprocess, sys, tempfile, time, urllib.parse, urllib.request
from pathlib import Path
SC = str(Path(__file__).resolve().parent)
tmp = Path(tempfile.mkdtemp(prefix="p002-"))
root = tmp / "bitacora"; fe = tmp / "frontend"; be = tmp / "backend"
for r in (fe, be):
    r.mkdir(); subprocess.run(["git", "init", "-q"], cwd=r)
    subprocess.run(["git", "-c", "user.email=a@b.c", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "init"], cwd=r)
PORT = "8796"
env = {**os.environ, "BITACORA_ROOT": str(root), "BITACORA_PORT": PORT, "BITACORA_TERMINAL": "tmux"}
def cli(*a, **kw):
    return subprocess.run([sys.executable, f"{SC}/bitacora.py", *a], env=env, capture_output=True, text=True, timeout=120, **kw)
def step(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""), flush=True); return ok
res = {}
try:
    # --- HQ: project, workspace, requirement, spec
    root.mkdir(); (root / "p002").mkdir()
    for role, p in (("frontend", fe), ("backend", be)):
        cli("--project", "p002", "workspace", "add", role, str(p))
    r = cli("--project", "p002", "req", "new", "Two small files")
    res["req new"] = step("req new", r.returncode == 0, r.stdout.strip()[:100])
    rdir = next((root / "p002" / "requirements").glob("REQ-001-*"))
    (rdir / "SPEC.md").write_text("---\nstatus: approved\n---\n# Two small files\n\n## R1\nThe frontend repo has front.txt containing the word hola.\n"
                                  "## R2\nThe backend repo has back.txt containing the word mundo.\n")
    # --- a question round answered from the web form
    round_file = tmp / "round.json"
    round_file.write_text(json.dumps({"title": "Content", "intro": "check", "coverage": "1/1", "questions": [
        {"id": "q1", "text": "Which words go in the files?", "type": "choice",
         "options": [{"key": "a", "label": "hola / mundo"}, {"key": "b", "label": "foo / bar"}], "recommended": "a", "why": "spec"}]}))
    r = cli("--project", "p002", "round", "new", "REQ-001", "--file", str(round_file))
    res["round new"] = step("round new", r.returncode == 0, r.stdout.strip()[-80:])
    # --- plan in review
    (rdir / "PLAN.md").write_text("---\nstatus: draft\n---\n# Plan\n\n## Tasks\n"
        "- [ ] T1 — In the frontend repo create front.txt containing exactly the word hola, then commit it · repo: frontend · covers: R1 · verify: `grep -q hola front.txt`\n"
        "- [ ] T2 — In the backend repo create back.txt containing exactly the word mundo, then commit it · repo: backend · covers: R2 · verify: `grep -q mundo back.txt`\n")
    r = cli("--project", "p002", "plan", "review", "REQ-001")
    res["plan review"] = step("plan review", r.returncode == 0, r.stdout.strip()[-80:])
    # --- web server: answer the round, approve the plan (launches the marathon)
    srv = subprocess.Popen([sys.executable, f"{SC}/bitacora.py", "serve", "--port", PORT], env=env,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)
    token = (root / ".state" / "server-token").read_text().strip()
    base = f"http://127.0.0.1:{PORT}/p/p002/req/REQ-001"
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k): return None
    opener = urllib.request.build_opener(NoRedirect)
    def post(action, **form):
        data = urllib.parse.urlencode({"token": token, **form}).encode()
        try:
            resp = opener.open(urllib.request.Request(f"{base}/{action}", data=data), timeout=60)
            return resp.status, ""
        except urllib.error.HTTPError as e:
            return e.code, urllib.parse.unquote(e.headers.get("Location", ""))
    code, loc = post("answer", round="round-01.json", q1="a", q1__note="")
    res["answer"] = step("answer the round from the web form", code == 303 or code == 302, f"{code} {loc[-90:]}")
    ans = json.loads((rdir / "rounds" / "round-01.json").read_text())
    res["answer saved"] = step("answer persisted", ans["status"] == "answered" and ans["answered_via"] == "web")
    code, loc = post("plan", decision="approve", mode="marathon", agent="claude")
    res["approve"] = step("approve plan on the web launches the marathon", code in (302, 303) and "lanzada" in loc.lower(), f"{code} {loc[-160:]}")
    # --- the marathon runs by itself in tmux
    state = None
    deadline = time.time() + 1500
    while time.time() < deadline:
        f = rdir / "RUN.json"
        if f.exists():
            try: state = json.loads(f.read_text())
            except ValueError: state = None
            if state and state["status"] in ("done", "blocked", "stopped"):
                break
        time.sleep(10)
    st = state or {}
    res["done"] = step("marathon reached done", st.get("status") == "done", f"status={st.get('status')} sessions={st.get('sessions')} tasks={ {t['id']: t['status'] for t in st.get('tasks', [])} }")
    res["files"] = step("files exist with the right content",
                        (fe / "front.txt").exists() and "hola" in (fe / "front.txt").read_text()
                        and (be / "back.txt").exists() and "mundo" in (be / "back.txt").read_text())
    plan = (rdir / "PLAN.md").read_text()
    res["plan"] = step("PLAN.md ticked and closed", "[x] T1" in plan and "[x] T2" in plan and "status: done" in plan)
    res["report"] = step("REPORT.md written", (rdir / "REPORT.md").exists())
    ev = []
    for fl in (root / ".state" / "events").glob("attempts-*.jsonl"):
        ev += [json.loads(l) for l in fl.read_text().splitlines()]
    res["telemetry"] = step("telemetry recorded with measured tokens", len(ev) >= 3 and all(e["usage"]["quality"] != "unknown" for e in ev),
                            str([(e["task"], e["result"], e["usage"].get("output_tokens"), e["model"]) for e in ev]))
    log = subprocess.run(["git", "-C", str(root), "log", "--oneline"], capture_output=True, text=True).stdout.splitlines()
    res["bitacora git"] = step("bitácora commits for the run", any("marathon" in l for l in log), f"{len(log)} commits")
    day = list(root.glob("p002/20*/**/*.md"))
    res["day log"] = step("day log written", bool(day), str([d.name for d in day][:3]))
    unit = Path.home() / ".config/systemd/user/metodologia-run-p002-REQ-001.service"
    res["autostart"] = step("autostart entry removed after done", not unit.exists())
    print("log:", [(e["session"], e["task"], e["result"], e.get("model"), e.get("effort")) for e in st.get("log", [])], flush=True)
finally:
    try: srv.terminate()
    except Exception: pass
    out = subprocess.run(["tmux", "list-sessions", "-F", "#{session_name}"], capture_output=True, text=True).stdout.split()
    for s in out:
        if "p002" in s: subprocess.run(["tmux", "kill-session", "-t", s])
    unit = Path.home() / ".config/systemd/user/metodologia-run-p002-REQ-001.service"
    if unit.exists():
        subprocess.run(["systemctl", "--user", "disable", unit.name], capture_output=True); unit.unlink()
        subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
    shutil.rmtree(tmp, ignore_errors=True)
print("\nRESULT", "OK" if res and all(res.values()) else "FALLA", flush=True)
