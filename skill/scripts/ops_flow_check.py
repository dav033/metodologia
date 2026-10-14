#!/usr/bin/env python3
"""Whole automatic flow with REAL agents (spends a little quota on the default Claude and Codex accounts):
requirement -> plan in two milestones -> `handoff` approves by itself and starts the supervisor in the background
(tmux) -> one fresh session per milestone on the routed account -> an independent audit of each milestone by the
other provider -> final review -> done. Also proves that a confirmed learning reaches every session and shapes the
result, and that telemetry records agent, model, effort and kind.

Throwaway bitácora root and repo; nothing of the real bitácora is touched. Run by hand: python ops_flow_check.py --live
Needs: claude and codex logged in (default accounts), tmux.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--live", action="store_true", help="explicitly start real provider sessions and spend quota")
if not parser.parse_args().live:
    parser.error("real provider sessions require --live; use --help to inspect the checker")

SC = str(Path(__file__).resolve().parent)
tmp = Path(tempfile.mkdtemp(prefix="flow-"))
root, app = tmp / "bitacora", tmp / "app"
env = {**os.environ, "BITACORA_ROOT": str(root), "BITACORA_PORT": "8795", "BITACORA_TERMINAL": "tmux"}
for key in ("BITACORA_PROJECT", "BITACORA_RUN", "BITACORA_TASK", "BITACORA_SESSION", "BITACORA_KIND"):
    env.pop(key, None)
P = "flow"
res: dict[str, bool] = {}


def cli(*a, timeout=180):
    return subprocess.run([sys.executable, f"{SC}/bitacora.py", *a], env=env, capture_output=True, text=True,
                          timeout=timeout)


def step(name, ok, detail=""):
    res[name] = bool(ok)
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""), flush=True)
    return ok


def note(name, detail):
    print(f"INFO {name} — {detail}", flush=True)


try:
    app.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=app)
    subprocess.run(["git", "-c", "user.email=a@b.c", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "init"],
                   cwd=app)
    root.mkdir()
    (root / P).mkdir()
    cli("--project", P, "workspace", "add", "app", str(app))
    cli("--project", P, "req", "new", "Small calculator module")
    rdir = next((root / P / "requirements").glob("REQ-001-*"))
    (rdir / "SPEC.md").write_text(
        "---\nstatus: approved\n---\n# Small calculator module\n\n## Requirements\n"
        "- R1: `calc.py` exposes `add(a, b)` returning the sum.\n- R2: `calc.py` exposes `mul(a, b)` returning the product.\n"
        "- R3: unit tests in `test_calc.py` cover both functions (run with `python3 -m unittest -q`).\n"
        "- R4: `README.md` documents both functions with one usage example each.\n\n## Out of scope\nAnything else.\n")
    (rdir / "PLAN.md").write_text(
        "---\nstatus: draft\n---\n# Plan — REQ-001 Small calculator module\n\n## Tasks\n\n"
        "### M1 — Addition with its test\n"
        "- [ ] T1 — Create calc.py with add(a, b) and commit it · repo: app · covers: R1 · verify: `python3 -c \"import calc; assert calc.add(2, 3) == 5\"`\n"
        "- [ ] T2 — Create test_calc.py with unittest cases for add and commit it · repo: app · after: T1 · covers: R3 · verify: `python3 -m unittest -q`\n\n"
        "### M2 — Multiplication, test and documentation\n"
        "- [ ] T3 — Add mul(a, b) to calc.py with its unittest cases and commit · repo: app · after: T2 · covers: R2, R3 · verify: `python3 -c \"import calc; assert calc.mul(4, 3) == 12\" && python3 -m unittest -q`\n"
        "- [ ] T4 — Write README.md documenting add and mul with one example each and commit · repo: app · after: T3 · kind: docs · covers: R4 · verify: `grep -q mul README.md && grep -q add README.md`\n\n"
        "## Verification\n`python3 -m unittest -q` passes in the app repo.\n")
    # a preference the owner already confirmed: every later session must receive it and honour it
    r = cli("learn", "add", "Every Python function carries type hints on its parameters and its return value",
            "--scope", "owner", "--kind", "preference", "--evidence", "stated by the owner", "--source", "setup")
    lid = (r.stdout.split() or ["?"])[0]
    r2 = cli("learn", "confirm", lid)
    step("owner preference stored and confirmed", r.returncode == 0 and "confirmed" in r2.stdout, r2.stdout.strip()[:90])

    # Antigravity is a machine-local account: when this machine has it signed in, register it in the throwaway root so
    # the run exercises the default-auditor path (D-004). Without it the check still runs on Claude and Codex.
    agy_token = Path.home() / ".gemini" / "antigravity-cli" / "antigravity-oauth-token"
    with_agy = agy_token.exists() and shutil.which("agy") is not None
    if with_agy:
        pr = cli("profiles", "add", "antigravity", "--provider", "antigravity")
        step("antigravity profile registered for the run", pr.returncode == 0, pr.stdout.strip()[-60:])
    r = cli("--project", P, "handoff", "REQ-001", "--dry-run")
    dry = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
    step("dry run: plan is valid and needs no approval", dry.get("decision") == "would_launch",
         f"reasons={dry.get('reasons')} problems={dry.get('problems')} pool={dry.get('pool')}")
    r = cli("--project", P, "handoff", "REQ-001")
    ho = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
    step("handoff approved by itself and launched in the background", ho.get("decision") == "launched" and r.returncode == 0,
         f"{ho.get('opened', r.stderr.strip()[-200:])}")
    sessions = subprocess.run(["tmux", "list-sessions", "-F", "#{session_name}"], capture_output=True, text=True).stdout
    step("supervisor is a detached tmux session (no window)", "flow-REQ-001" in sessions, sessions.strip().replace("\n", ", "))

    state, deadline = None, time.time() + 75 * 60
    seen = 0
    while time.time() < deadline:
        f = rdir / "RUN.json"
        if f.exists():
            try:
                state = json.loads(f.read_text())
            except ValueError:
                state = None
            if state and len(state.get("log", [])) != seen:
                seen = len(state["log"])
                last = state["log"][-1]
                print(f"  .. S{last['session']} {last['task']} {last['result']} "
                      f"[{last.get('profile') or last.get('agent')} {last.get('model')} {last.get('effort')}] {last['seconds']}s",
                      flush=True)
            if state and state["status"] in ("done", "blocked", "stopped"):
                break
        time.sleep(10)
    st = state or {}
    tasks = {t["id"]: t["status"] for t in st.get("tasks", [])}
    step("run reached done", st.get("status") == "done", f"status={st.get('status')} sessions={st.get('sessions')} {tasks}")
    step("pool has both providers", len({p for p in st.get("pool", [])}) >= 2, str(st.get("pool")))
    step("audit tasks were created and done", tasks.get("M1-audit") == "done" and tasks.get("M2-audit") == "done")

    ev = []
    for fl in (root / ".state" / "events").glob("attempts-*.jsonl"):
        ev += [json.loads(line) for line in fl.read_text().splitlines()]
    ev.sort(key=lambda e: e["session"])
    for e in ev:
        note("session", f"S{e['session']} {e['task']} kind={e.get('kind')} tier={e.get('tier')} {e.get('agent')}/"
                        f"{e.get('profile')} {e.get('model')} effort={e.get('effort')} -> {e['result']} {e['seconds']}s "
                        f"tokens={e['usage'].get('total_tokens') or e['usage'].get('output_tokens')}")
    builds = [e for e in ev if e["task"] in ("M1", "M2")]
    audits = [e for e in ev if e["task"].endswith("-audit")]
    step("each milestone ran as ONE session carrying its tasks",
         any(e["task"] == "M1" and e.get("tasks") == ["T1", "T2"] for e in ev)
         and any(e["task"] == "M2" and set(e.get("tasks") or []) >= {"T3", "T4"} for e in ev),
         str([(e["task"], e.get("tasks")) for e in builds]))
    by_ms = {e["task"]: e["agent"] for e in builds if e["result"] == "done"}
    crossed = [(a["task"], a["agent"], by_ms.get(a["task"].split("-")[0])) for a in audits if a["result"] == "done"]
    limited = {e["agent"] for e in ev if e["result"] in ("usage_limit", "limit_streak")}
    step("every audit ran on another provider than its builder, or that provider had hit its usage limit",
         bool(crossed) and all(aud != built or bool(limited - {built}) for _, aud, built in crossed),
         f"{crossed} usage-limited: {sorted(limited)}")
    if limited:
        quota = json.loads((root / ".state" / "quota.json").read_text()) if (root / ".state" / "quota.json").exists() else {}
        step("a usage limit put the account on cooldown and the run continued on another one without waiting",
             bool(quota) and not st.get("waiting_until"), str({k: time.strftime('%m-%d %H:%M', time.localtime(v['until'])) for k, v in quota.items()}))
    if with_agy:
        done_audits = [a for a in audits if a["result"] == "done"]
        step("every audit ran on Antigravity (Gemini 3.8 Flash low) as the default auditor",
             bool(done_audits) and all(a["agent"] == "antigravity" and a["model"] == "gemini-3.8-flash-low"
                                       for a in done_audits),
             str([(a["task"], a["agent"], a["model"], a["effort"], a["seconds"]) for a in audits]))
    step("audits ran one tier above the builders", all((a.get("tier") or 0) >= 1 for a in audits),
         str([(a["task"], a.get("tier"), a.get("model"), a.get("effort")) for a in audits]))
    step("telemetry rows carry agent, profile, model, effort, kind and measured usage",
         bool(ev) and all(e.get("agent") and e.get("model") and e.get("kind") for e in ev)
         and all(e["usage"]["quality"] != "unknown" for e in ev if e["result"] == "done"),
         f"{len(ev)} rows")
    m = cli("metrics", "--by", "kind,agent,model,effort")
    groups = json.loads(m.stdout) if m.stdout.strip().startswith("[") else []
    step("metrics groups by kind, agent, model and effort", len(groups) >= 2 and all("success_rate" in g for g in groups),
         str([(g["kind"], g["agent"], g["model"], g["effort"], g["attempts"], g["success_rate"]) for g in groups]))

    prompts = sorted((root / ".state" / "runs" / f"{P}-REQ-001").glob("prompt-*.txt"))
    texts = [p.read_text() for p in prompts]
    step("every session started from a fresh prompt with the learned preference and the agent catalog",
         bool(texts) and all("type hints" in t for t in texts if "FINAL" not in t.splitlines()[0])
         and all("Agents available" in t for t in texts if "FINAL" not in t.splitlines()[0]), f"{len(texts)} prompts")
    step("prompts carry references, not the conversation (each under 12 kB)", all(len(t) < 12000 for t in texts),
         str([len(t) for t in texts]))
    code = (app / "calc.py").read_text() if (app / "calc.py").exists() else ""
    step("code honours the learned owner preference (type hints)", "->" in code and "def add(" in code and "def mul(" in code,
         code.replace("\n", " | ")[:200])
    ut = subprocess.run([sys.executable, "-m", "unittest", "-q"], cwd=app, capture_output=True, text=True)
    step("tests written by the agents pass", ut.returncode == 0 and "Ran 0" not in ut.stderr, ut.stderr.strip()[-80:])
    step("documentation written", (app / "README.md").exists() and "mul" in (app / "README.md").read_text())
    step("audit reports written", (rdir / "AUDIT-M1.md").exists() and (rdir / "AUDIT-M2.md").exists(),
         str(sorted(p.name for p in rdir.glob("AUDIT-*.md"))))
    plan = (rdir / "PLAN.md").read_text()
    step("PLAN.md ticked and closed", all(f"[x] T{i}" in plan for i in (1, 2, 3, 4)) and "status: done" in plan)
    step("REPORT.md written by the final session", (rdir / "REPORT.md").exists())
    log = subprocess.run(["git", "-C", str(app), "log", "--oneline", "--all"], capture_output=True, text=True).stdout
    step("work committed in the repo, nothing pushed", len(log.splitlines()) >= 3, f"{len(log.splitlines())} commits")
    learned = cli("--project", P, "learn", "list").stdout.strip()
    note("learnings after the run (candidates proposed by the agents, if any)", learned.replace("\n", " || ")[:600] or "none")
    decisions = (root / P / "DECISIONS.md").read_text() if (root / P / "DECISIONS.md").exists() else ""
    note("decisions recorded", str(decisions.count("\n## D-")))
    unit = Path.home() / f".config/systemd/user/metodologia-run-{P}-REQ-001.service"
    step("autostart entry removed after done", not unit.exists())
finally:
    out = subprocess.run(["tmux", "list-sessions", "-F", "#{session_name}"], capture_output=True, text=True).stdout.split()
    for s in out:
        if s.startswith("flow-REQ-001"):
            subprocess.run(["tmux", "kill-session", "-t", s])
    unit = Path.home() / f".config/systemd/user/metodologia-run-{P}-REQ-001.service"
    if unit.exists():
        subprocess.run(["systemctl", "--user", "disable", unit.name], capture_output=True)
        unit.unlink()
        subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
    keep = os.environ.get("FLOW_KEEP")
    if keep:
        print("kept:", tmp)
    else:
        shutil.rmtree(tmp, ignore_errors=True)
print("\nRESULT", "OK" if res and all(res.values()) else "FAIL: " + ", ".join(k for k, v in res.items() if not v), flush=True)
sys.exit(0 if res and all(res.values()) else 1)
