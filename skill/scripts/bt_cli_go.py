"""`bitacora go REQ-NNN`: from a written plan to a running execution with one command.

SPEC.md + PLAN.md  ->  PLAN.json skeleton (`plan-json init`)  ->  the Planner agent classifies every task with
evidence and checks it  ->  `plan-json check`  ->  `handoff` (approves when no risk reasons hold it back, then starts
the Scheduler in the background, where M2 picks model/account per task).

Every step is the existing CLI command, run as a child process; nothing here re-implements them. The only decision this
adds is *when to stop*: an invalid plan after the agent's attempts, or a hand-off that needs the owner's approval
(risk reasons), is reported and left alone.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import bt_workspace as ws
from bt_core import SCRIPT, find_req, req_id

ATTEMPTS = 2                  # classification rounds the Planner gets before the plan is reported as not ready
PLANNER_TIMEOUT = 1800


def add_parser(sub) -> None:
    p = sub.add_parser("go", help="classify the plan with the Planner agent, approve when safe and run it", allow_abbrev=False)
    p.add_argument("req", help="REQ-NNN")
    p.add_argument("--dry-run", action="store_true", help="do the planning steps but only say what the hand-off would do")
    p.add_argument("--no-ai", action="store_true", help="never call the Planner agent: stop if PLAN.json is incomplete")
    p.add_argument("--timeout", type=int, default=PLANNER_TIMEOUT, help="seconds the Planner agent may take per round")


def _cli(project: str, *args: str, stdin: str | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), "--project", project, *args], input=stdin, text=True,
                          capture_output=True, cwd=cwd)


def _say(message: str) -> None:
    print(message, flush=True)


def prompt_for(project: str, rid: str, problems: str) -> str:
    return (
        f"Classify the plan of requirement {rid} (project {project}) so it satisfies the PLAN.json contract.\n"
        f"SPEC.md and PLAN.md already exist and are approved as the scope: do not change what will be built. "
        f"Fill PLAN.json (create it with `bitacora.py --project {project} plan-json init {rid}` only if it is missing): "
        "every task needs the full classification (complexity, scope, risk, coupling, confidence, estimate) with typed "
        "evidence from files you actually opened, `covers`, `kind` and verification the project can run. "
        "Keep PLAN.md and PLAN.json in agreement. Never approve, freeze, hand off, launch or implement anything.\n"
        f"Finish by running `bitacora.py --project {project} plan-json check {rid}` and report its real result.\n\n"
        f"Current `plan-json check` output:\n{problems.strip()[:6000] or '(PLAN.json not created yet)'}\n")


def _repo_args(root: Path, project: str) -> tuple[list[str], Path | None]:
    repos = ws.repos(root, project, discover=False)
    args = [f"--repo={role}={path}" for role, path in repos.items()]
    first = next(iter(repos.values()), None)
    return args, first if first and first.is_dir() else None


def run(root: Path, project: str, req: str, dry_run: bool = False, no_ai: bool = False,
        timeout: int = PLANNER_TIMEOUT) -> int:
    rdir = find_req(root / project, req)
    rid = req_id(rdir)
    for name in ("SPEC.md", "PLAN.md"):
        if not (rdir / name).exists():
            _say(f"{rid}: falta {name}; `go` parte de una especificación y un plan ya escritos.")
            return 2
    if not (rdir / "PLAN.json").exists():
        _say(f"{rid}: creando el esqueleto de PLAN.json…")
        made = _cli(project, "plan-json", "init", rid)
        if made.returncode:
            _say(made.stdout + made.stderr)
            return 2
    check = _cli(project, "plan-json", "check", rid)
    rounds = 0
    while check.returncode and not no_ai and rounds < ATTEMPTS:
        rounds += 1
        _say(f"{rid}: el Planner clasifica las tareas (ronda {rounds}/{ATTEMPTS}; el router elige modelo y cuenta)…")
        repo_args, cwd = _repo_args(root, project)
        agent = _cli(project, "planner", "invoke", "--req", rid, "--timeout", str(timeout), *repo_args,
                     stdin=prompt_for(project, rid, check.stdout + check.stderr), cwd=cwd)
        if agent.returncode:
            _say(f"{rid}: el Planner falló (código {agent.returncode}):\n{(agent.stderr or agent.stdout)[-1500:]}")
        check = _cli(project, "plan-json", "check", rid)
    if check.returncode:
        _say(f"{rid}: el plan todavía no cumple el contrato; no se lanza nada.\n{(check.stdout + check.stderr)[-3000:]}")
        _say(f"Corrígelo y repite: bitacora --project {project} go {rid}")
        return 2
    _say(f"{rid}: PLAN.json válido. {'Simulando' if dry_run else 'Aprobando y lanzando'} el hand-off…")
    import bt_handoff
    result = bt_handoff.handoff(project, rid, dry_run)
    print(json.dumps(result, indent=1, ensure_ascii=False))
    decision = result["decision"]
    if decision in ("launched", "would_launch", "already_running", "done", "prepared", "would_prepare"):
        if decision == "launched":
            _say(f"Listo: {rid} corre en segundo plano. Míralo en http://127.0.0.1:8765/plans/{project}/{rid} "
                 f"o con: bitacora --project {project} watch {rid}")
        return 0
    if decision == "needs_approval":
        _say(f"{rid}: el plan tiene motivos de riesgo y espera tu aprobación (arriba). Apruébalo en la web o con "
             f"`bitacora --project {project} plan approve {rid}` y luego `bitacora --project {project} go {rid}`.")
        return 3
    return 2
