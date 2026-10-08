#!/usr/bin/env python3
"""Eval runner for the `metodologia` skill.

Runs each case in evals/cases/*.json as a real `claude -p` session (your normal ~/.claude config: CLAUDE.md import,
skill, hooks) inside a throwaway fixture repo, with the bitácora redirected to a throwaway root
(BITACORA_ROOT) and the web UI on a throwaway port (BITACORA_PORT=8798). Then grades transcript + files.

  python evals/run.py                          # all cases, sonnet, cap USD 5
  python evals/run.py --case a-* --case e-*    # some cases
  python evals/run.py --model opus --cap 10    # fidelity run with the model you really use
  python evals/run.py --list
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fixtures  # noqa: E402
from graders import grade  # noqa: E402

PORT = "8798"
REAL_BITACORA = HERE.parent / "bitacora"
FIXTURE_NAMES = re.compile(r"tienda-web|pedidos-api|metodologia-evals")
# Safety net on top of the redirected env: the agent may never edit the real skill/bitácora/config, nor push.
DENY = ["Edit(~/metodologia/**)", "Write(~/metodologia/**)", "Edit(~/bitacora/**)", "Write(~/bitacora/**)",
        "Edit(~/.claude/**)", "Write(~/.claude/**)", "Bash(git push:*)", "PowerShell(git push*)"]

def claude_bin() -> str:
    exe = shutil.which("claude") or shutil.which("claude.exe") or shutil.which("claude.cmd")
    if not exe:
        sys.exit("claude CLI not found on PATH")
    return exe


def git_bash() -> str | None:
    """Claude Code runs command hooks with Git Bash; a user-scope Git install isn't always found from a nested
    shell, and then hooks fall back to PowerShell and the bitácora hooks fail. Point at it explicitly."""
    if os.environ.get("CLAUDE_CODE_GIT_BASH_PATH"):
        return os.environ["CLAUDE_CODE_GIT_BASH_PATH"]
    git = shutil.which("git")
    cands = [Path(git).resolve().parent.parent / "bin" / "bash.exe"] if git else []
    cands += [Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "bin" / "bash.exe",
              Path.home() / "AppData" / "Local" / "Programs" / "Git" / "bin" / "bash.exe"]
    return next((str(c) for c in cands if c.exists()), None)


def child_env(bt_root: Path) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("BITACORA_", "CLAUDE_CODE_SESSION",
                                                                     "CLAUDE_CODE_MESSAGING", "CLAUDECODE"))}
    env.pop("SHELL", None)
    env.update(BITACORA_ROOT=str(bt_root), BITACORA_PORT=PORT)
    gb = git_bash() if os.name == "nt" else None
    if gb:
        env["CLAUDE_CODE_GIT_BASH_PATH"] = gb
    return env


def parse_stream(text: str) -> dict:
    turn = {"texts": [], "final": "", "tools": [], "cost": 0.0, "session_id": None, "error": None, "num_turns": 0}
    for line in text.splitlines():
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("session_id"):
            turn["session_id"] = e["session_id"]
        if e.get("type") == "assistant":
            for c in (e.get("message") or {}).get("content") or []:
                if c.get("type") == "text" and c.get("text", "").strip():
                    turn["texts"].append(c["text"])
                elif c.get("type") == "tool_use":
                    turn["tools"].append({"name": c.get("name", ""), "input": c.get("input") or {}})
        elif e.get("type") == "result":
            turn["final"] = e.get("result") or (turn["texts"][-1] if turn["texts"] else "")
            turn["cost"] = float(e.get("total_cost_usd") or 0)
            turn["num_turns"] = e.get("num_turns", 0)
            if e.get("is_error") or e.get("subtype") != "success":
                turn["error"] = e.get("subtype")
    if not turn["final"] and turn["texts"]:
        turn["final"] = turn["texts"][-1]
    return turn


def run_turn(prompt: str, cwd: Path, env: dict, case: dict, model: str, resume: str | None, log: Path) -> dict:
    cmd = [claude_bin(), "-p", prompt, "--output-format", "stream-json", "--verbose", "--model", model,
           "--permission-mode", "bypassPermissions", "--strict-mcp-config",
           "--max-turns", str(case.get("max_turns", 25)), "--max-budget-usd", str(case.get("budget_usd", 0.6)),
           "--disallowedTools", *DENY]
    if resume:
        cmd += ["--resume", resume]
    t0 = time.time()
    try:
        res = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8",
                             errors="replace", timeout=case.get("timeout_s", 900), stdin=subprocess.DEVNULL)
        out = res.stdout
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
    with log.open("a", encoding="utf-8") as fh:
        fh.write(out)
    turn = parse_stream(out)
    turn["seconds"] = round(time.time() - t0, 1)
    if not turn["session_id"]:
        turn["error"] = turn["error"] or "no result (timeout or crash)"
    return turn


def make_judge(run_dir: Path, judge_model: str, costs: list):
    jdir = run_dir / "_judge"
    jdir.mkdir(exist_ok=True)
    env = child_env(jdir / "bitacora")

    def judge(criteria: str, content: str) -> tuple[bool, str]:
        prompt = ("You are a strict grader. Read the CRITERIA and the CONTENT (output of an AI coding agent, "
                  "mostly in Spanish). Reply with exactly one line: `PASS: <reason>` or `FAIL: <reason>` "
                  f"(reason ≤ 25 words).\n\nCRITERIA:\n{criteria}\n\nCONTENT:\n<<<\n{content}\n>>>")
        cmd = [claude_bin(), "-p", "--model", judge_model, "--output-format", "json", "--tools", "",
               "--setting-sources", "project", "--strict-mcp-config", "--no-session-persistence", "--max-turns", "1"]
        try:
            res = subprocess.run(cmd, input=prompt, cwd=jdir, env=env, capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", timeout=180)
            data = json.loads(res.stdout)
        except Exception as e:
            return False, f"judge error: {e}"
        costs.append(float(data.get("total_cost_usd") or 0))
        out = (data.get("result") or "").strip()
        m = re.search(r"\b(PASS|FAIL)\b:?\s*(.*)", out)
        return (bool(m) and m.group(1) == "PASS"), (m.group(2)[:200] if m else out[:200])
    return judge


def leaks(since: float) -> list[str]:
    """Files in the REAL bitácora touched during the run that mention a fixture project — must be empty."""
    found = []
    for p in REAL_BITACORA.rglob("*"):
        if p.is_file() and ".git" not in p.parts and p.stat().st_mtime >= since:
            try:
                if FIXTURE_NAMES.search(p.read_text(encoding="utf-8", errors="ignore")):
                    found.append(str(p))
            except OSError:
                pass
    return found


def run_case(case: dict, run_dir: Path, args, judge) -> dict:
    name = case["name"]
    cdir = run_dir / name
    work, bt_root, project = fixtures.build(case["fixture"], cdir, tools=case.get("tools_md", False))
    env = child_env(bt_root)
    is_repo = project is not None
    base = fixtures.git(work, "rev-parse", "HEAD") if is_repo else ""
    turns, resume, t0 = [], None, time.time()
    for prompt in case["turns"]:
        turn = run_turn(prompt, work, env, case, args.model, resume, cdir / "transcript.jsonl")
        turns.append(turn)
        resume = turn["session_id"]
        if not resume:
            break
    out = grade_case(case, turns, cdir, work, bt_root, project, base, judge)
    out["seconds"] = round(time.time() - t0, 1)
    return out


def grade_case(case: dict, turns: list, cdir: Path, work: Path, bt_root: Path, project: str | None, base: str,
               judge) -> dict:
    ctx = {"turns": turns, "repo": str(work), "bt": str(bt_root / project) if project else None,
           "bt_root": str(bt_root), "base_sha": base, "remote": str(cdir / f"{project}.git") if project else "",
           "judge": judge}
    results = []
    for g in case["graders"]:
        ok, detail = grade(g, ctx)
        results.append({"name": g.get("name", g["type"]), "passed": ok, "detail": detail})
    score = sum(r["passed"] for r in results) / len(results)
    return {"name": case["name"], "score": round(score, 2), "passed": score == 1.0, "graders": results,
            "cost": round(sum(t["cost"] for t in turns), 4), "seconds": 0,
            "turn_errors": [t["error"] for t in turns if t["error"]], "workdir": str(work),
            "final": turns[-1]["final"][:1500] if turns else ""}


def regrade(run_dir: Path, cases: list[dict], judge) -> list[dict]:
    """Re-score a kept run (--keep) with the current graders: no agent calls, only judge calls."""
    out = []
    for case in cases:
        cdir = run_dir / case["name"]
        log = cdir / "transcript.jsonl"
        if not log.exists():
            continue
        chunks, cur = [], []
        for line in log.read_text(encoding="utf-8").splitlines():
            cur.append(line)
            try:
                is_result = json.loads(line).get("type") == "result"
            except Exception:
                is_result = False
            if is_result:
                chunks.append(cur)
                cur = []
        turns = [parse_stream(chr(10).join(c)) for c in chunks]
        _, project = fixtures.FIXTURES.get(case["fixture"], (None, None))
        work = cdir / project if project else cdir / "scratch"
        base = fixtures.git(work, "rev-list", "--max-parents=0", "HEAD") if project else ""
        out.append(grade_case(case, turns, cdir, work, cdir / "bitacora", project, base, judge))
    return out


def kill_port(port: str) -> None:
    """Stop a bitácora web server an eval session may have started on the throwaway port."""
    if os.name != "nt":
        return
    out = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, encoding="oem", errors="replace").stdout or ""
    for pid in {ln.split()[-1] for ln in out.splitlines() if f":{port} " in ln and "LISTENING" in ln}:
        subprocess.run(["taskkill", "/PID", pid, "/F", "/T"], capture_output=True)


def load_cases(patterns: list[str] | None) -> list[dict]:
    cases = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((HERE / "cases").glob("*.json"))]
    if patterns:
        cases = [c for c in cases if any(fnmatch.fnmatch(c["name"], pat) for pat in patterns)]
    return cases


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--case", action="append", help="glob on case name (repeatable)")
    ap.add_argument("--model", default="sonnet", help="model for the agent under test (default: sonnet)")
    ap.add_argument("--judge-model", default="haiku")
    ap.add_argument("--cap", type=float, default=5.0, help="hard cost cap in USD (cases not started past it)")
    ap.add_argument("-j", "--concurrency", type=int, default=3)
    ap.add_argument("--keep", action="store_true", help="keep the fixture dirs in %%TEMP%%")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--regrade", metavar="RUN_DIR", help="re-score a run kept with --keep, without re-running it")
    args = ap.parse_args()

    cases = load_cases(args.case)
    if args.list or not cases:
        for c in cases:
            print(f"{c['name']:28} {c.get('description', '')}")
        return
    if args.regrade:
        costs: list[float] = []
        for r in regrade(Path(args.regrade), cases, make_judge(Path(args.regrade), args.judge_model, costs)):
            fails = [f"{g['name']} ({g['detail']})" for g in r["graders"] if not g["passed"]]
            print(f"{'PASS' if r['passed'] else 'FAIL'} {r['name']:26} score {r['score']}"
                  f"{' · failed: ' + '; '.join(fails) if fails else ''}")
        return
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = Path(tempfile.gettempdir()) / "metodologia-evals" / f"run-{stamp}"
    run_dir.mkdir(parents=True)
    judge_costs: list[float] = []
    judge = make_judge(run_dir, args.judge_model, judge_costs)
    started, t0 = time.time(), time.time()
    print(f"run dir: {run_dir}\nmodel: {args.model} · judge: {args.judge_model} · cap: ${args.cap}\n")

    # Cost cap: a case starts only if (spent so far + worst-case budget of running cases + its own) fits the cap.
    results, queue, running, spent = [], list(cases), {}, 0.0
    budget = lambda c: c.get("budget_usd", 0.6) * len(c["turns"])  # noqa: E731
    with cf.ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as pool:
        while queue or running:
            while queue and len(running) < args.concurrency and \
                    spent + sum(judge_costs) + sum(budget(c) for c in running.values()) + budget(queue[0]) <= args.cap:
                c = queue.pop(0)
                running[pool.submit(run_case, c, run_dir, args, judge)] = c
            if not running:
                for c in queue:
                    results.append({"name": c["name"], "score": None, "passed": False, "skipped": "cost cap",
                                    "graders": [], "cost": 0, "seconds": 0})
                    print(f"SKIP {c['name']:26} (cost cap)")
                break
            done, _ = cf.wait(running, return_when=cf.FIRST_COMPLETED)
            fut = next(iter(done))
            case = running.pop(fut)
            try:
                r = fut.result()
            except Exception as e:
                r = {"name": case["name"], "score": 0, "passed": False, "graders": [], "cost": 0, "seconds": 0,
                     "turn_errors": [f"runner error: {e}"]}
            spent += r["cost"]
            results.append(r)
            mark = "PASS" if r["passed"] else "FAIL"
            fails = [g["name"] for g in r["graders"] if not g["passed"]]
            print(f"{mark} {r['name']:26} score {r['score']} · ${r['cost']:.2f} · {r['seconds']}s"
                  f"{' · failed: ' + ', '.join(fails) if fails else ''}", flush=True)
    kill_port(PORT)
    leaked = leaks(started)
    order = {c["name"]: i for i, c in enumerate(cases)}
    results.sort(key=lambda r: order.get(r["name"], 99))
    total = sum(r["cost"] for r in results) + sum(judge_costs)
    summary = {"model": args.model, "judge_model": args.judge_model, "run_dir": str(run_dir),
               "cost_usd": round(total, 3), "judge_cost_usd": round(sum(judge_costs), 3),
               "seconds": round(time.time() - t0), "leaks_into_real_bitacora": leaked, "cases": results}
    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    (out_dir / f"{stamp}.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    passed = sum(r["passed"] for r in results)
    print(f"\n{passed}/{len(results)} cases passed · ${total:.2f} · {summary['seconds']}s · "
          f"results: evals/results/{stamp}.json")
    if leaked:
        print("!! LEAK: the real bitácora was touched:", *leaked, sep="\n   ")
    if not args.keep:
        shutil.rmtree(run_dir, ignore_errors=True) if passed == len(results) else None
    sys.exit(0 if passed == len(results) and not leaked else 1)


if __name__ == "__main__":
    main()
