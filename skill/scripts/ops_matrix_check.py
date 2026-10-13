#!/usr/bin/env python3
"""Operational check with REAL agents: every account can run every model of its provider, and every provider can
delegate to the other one (a Claude session using Codex as its subagent and the reverse).

It spends a little real quota (a dozen one-line tasks). Nothing is written outside a throwaway directory, except the
telemetry rows and delegation records of the real bitácora. A work-only account is exercised inside a project marked
work, with a task that changes nothing. Usage: ops_matrix_check.py [--project NAME] [--skip-cross] [--only PROFILE]
Exit status 0 only when every cell passed or was a usage limit (reported as such, not as a failure).
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import bt_agents  # noqa: E402
import bt_profiles  # noqa: E402
import bt_workspace as ws  # noqa: E402
from bt_core import ROOT  # noqa: E402

CLI = [sys.executable, str(SCRIPTS / "bitacora.py")]


def delegate(project: str, task: str, workdir: Path, profile: str, model: str, effort: str | None, verify: str | None,
             timeout_min: int = 8) -> dict:
    cmd = [*CLI, "--project", project, "delegate", "start", task, "--profile", profile, "--model", model,
           "--workdir", str(workdir), "--timeout", str(timeout_min), "--kind", "research"]
    if effort:
        cmd += ["--effort", effort]
    if verify:
        cmd += ["--verify", verify]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_min * 60 + 120)
    try:
        return json.loads(res.stdout)
    except ValueError:
        return {"status": "error", "summary": (res.stdout + res.stderr).strip()[-300:]}


def work_project() -> tuple[str, Path] | None:
    for d in sorted(p for p in ROOT.iterdir() if (p / "project.json").exists()):
        if bt_profiles.is_work_project(d.name):
            wd = ws.workdir(ROOT, d.name)
            if wd and wd.is_dir():
                return d.name, wd
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="metodologia")
    ap.add_argument("--skip-cross", action="store_true")
    ap.add_argument("--only", help="a single profile id")
    a = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="ops-matrix-"))
    subprocess.run(["git", "init", "-q", str(tmp)], check=True)
    profiles = bt_profiles.load()
    accounts = [p for p in bt_agents.pool_for(a.project) if not a.only or p == a.only]
    work = [p for p, s in profiles.items() if s.get("work_only") and (not a.only or p == a.only)]
    cells = []
    for pid in accounts:
        provider = profiles[pid]["provider"]
        for model, spec in bt_agents.MODELS.items():
            if spec["provider"] != provider:
                continue
            effort = next((e for m, e in bt_agents.LADDER[provider] if m == model), None)
            name = f"{pid}-{model}".replace(".", "_")
            cells.append((f"{pid} · {model}", a.project, f"Create a file named {name}.txt in the working directory "
                          f"containing exactly the word ok. Nothing else.", tmp, pid, model,
                          "low" if provider == "codex" else effort and "low", f"test -f {name}.txt"))
    wp = work_project()
    for pid in work:  # gated account: only inside a work project, and with a task that changes nothing
        if not wp:
            print(f"SKIP {pid}: no project is marked work on this machine")
            continue
        model = bt_agents.LADDER[profiles[pid]["provider"]][0][0]
        cells.append((f"{pid} · {model} (work project {wp[0]})", wp[0], "Do not read or modify any file. Just write "
                      "the required report with status done and summary 'ok'.", wp[1], pid, model, None, None))
    if not a.skip_cross and not a.only:
        claude = next((p for p in accounts if profiles[p]["provider"] == "claude"), None)
        for codex in [p for p in accounts if profiles[p]["provider"] == "codex"]:
            if not claude:
                break
            inner = (f'{CLI[0]} "{CLI[1]}" --project {a.project} delegate start "Create a file named '
                     f'{{name}}.txt in the working directory containing exactly the word ok." --profile {{to}} '
                     f'--model {{model}} --effort low --workdir "{tmp}" --verify "test -f {{name}}.txt"')
            for src, dst, model in ((claude, codex, "gpt-6-luna"), (codex, claude, "haiku")):
                name = f"cross-{src}-to-{dst}"
                cmd = inner.format(name=name, to=dst, model=model).replace(" --effort low", "" if dst == claude else " --effort low")
                src_model = bt_agents.LADDER[profiles[src]["provider"]][0][0]
                cells.append((f"{src} delegates to {dst} · {model}", a.project,
                              "You must NOT create the file yourself. Run exactly this shell command, wait for it to "
                              f"finish and report its `status` field in your summary: {cmd}", tmp, src, src_model,
                              "low" if profiles[src]["provider"] == "codex" else None, f"test -f {name}.txt"))
    print(f"{len(cells)} cells, scratch dir {tmp}", flush=True)

    def run(cell):
        label, project, task, workdir, pid, model, effort, verify = cell
        out = delegate(project, task, workdir, pid, model, effort, verify)
        return label, out

    failed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for label, out in pool.map(run, cells):
            status = out.get("status")
            ok = status in ("verified", "claimed")
            limit = status == "usage_limit"
            failed += not (ok or limit)
            mark = "PASS" if ok else "LIMIT" if limit else "FAIL"
            print(f"{mark:5} {label}: {status} ({out.get('seconds', '?')}s) {'' if ok else str(out.get('summary'))[:200]}",
                  flush=True)
    print("RESULT:", "all cells passed" if not failed else f"{failed} cell(s) failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
