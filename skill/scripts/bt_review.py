"""Review & merge gate: what the executor changed in each workspace repo, and merging it as one unit.

The executor works on the same feature branch in every repo it touches (`feature_branch(rdir)`). Merging is
local (`--no-ff` into the repo's default branch); pushing happens only when the user presses the
"merge and publish" button — that click is the authorization.
"""
from __future__ import annotations

import subprocess

from bt_core import *  # noqa: F403


def feature_branch(rdir: Path) -> str:
    return f"feat/{rdir.name.lower()}"[:60]


def _git(repo: Path, *args: str, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, timeout=timeout,
                          encoding="utf-8", errors="replace")


def default_branch(repo: Path) -> str:
    head = _git(repo, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD").stdout.strip()
    if head:
        return head.split("/", 1)[-1]
    for name in ("main", "master"):
        if _git(repo, "rev-parse", "--verify", "--quiet", name).returncode == 0:
            return name
    return "main"


def repo_state(repo: Path, branch: str) -> dict:
    """Branch existence, commits ahead of the default branch, diff stat, dirtiness."""
    if not (repo / ".git").exists():
        return {"exists": False, "note": "not cloned on this machine"}
    base = default_branch(repo)
    if _git(repo, "rev-parse", "--verify", "--quiet", branch).returncode != 0:
        return {"exists": True, "branch": None, "base": base}
    commits = _git(repo, "log", "--format=%h %ad %s", "--date=short", f"{base}..{branch}").stdout.strip().splitlines()
    stat = _git(repo, "diff", "--stat", f"{base}...{branch}").stdout.strip().splitlines()
    dirty = [l for l in _git(repo, "status", "--porcelain").stdout.splitlines() if not l.startswith("??")]
    merged = _git(repo, "merge-base", "--is-ancestor", branch, base).returncode == 0
    return {"exists": True, "branch": branch, "base": base, "commits": commits, "stat": stat[-25:],
            "dirty": dirty, "merged": merged}


def review_state(project: str, rdir: Path) -> dict[str, dict]:
    branch = feature_branch(rdir)
    return {role: repo_state(path, branch) for role, path in ws.repos(ROOT, project, discover=False).items()}


def stage_gap(rdir: Path) -> str:
    """Why the approved plan is not the whole draft yet ('' when it is, or when the requirement has no PLAN.json);
    fail closed: a store or draft that cannot be read is a gap."""
    import bt_plan_adapter
    if not (Path(rdir) / "PLAN.json").exists():
        try:
            if bt_plan_adapter.stage_subplans(rdir) or bt_plan_adapter.latest_plan(rdir) is not None:
                return "PLAN_MISSING: falta PLAN.json de un plan aprobado"
        except Exception as exc:  # noqa: BLE001 - missing draft cannot bypass a damaged approval store
            return f"no pude leer las revisiones aprobadas ({type(exc).__name__})"
        return ""
    try:
        summary, draft = bt_plan_adapter.stage_summary(rdir), bt_plan_adapter.draft_subplans(rdir)
        held = bt_plan_adapter.stage_subplans(rdir)
    except Exception as exc:  # noqa: BLE001 - fail closed
        return f"no pude leer las revisiones aprobadas ({type(exc).__name__})"
    if draft is None:
        return "PLAN.json no se puede leer; reintenta en unos segundos"
    missing = [sid for sid in draft if sid not in held]
    if missing or (summary["stages"] and not summary["complete"]):
        return ("la última etapa aprobada no contiene todo el plan" +
                (f" (faltan {', '.join(missing[:8])})" if missing else "") + "; apruébalo completo antes de fusionar")
    import bt_scheduler_adapter
    if problem := bt_plan_adapter.launch_problem(
            rdir, forced=True, compatibility_report=bt_scheduler_adapter.plan_compatibility_report(rdir)):
        return problem
    try:
        latest = bt_plan_adapter.revisions(rdir)[-1]
        identity = bt_scheduler_adapter.run_identity(rdir)
        if identity is None or (identity["revision"], identity["plan_sha256"]) != (latest["revision"], latest["sha256"]):
            return f"la etapa r{latest['revision']} todavía no está ejecutada en este run"
        import bt_scheduler_ops
        states = bt_scheduler_ops.status(rdir.parent.parent.name, bt_plan_adapter.plan_id(rdir), rdir)["task_states"]
        plan = bt_plan_adapter.latest_plan(rdir)
        pending = [t["id"] for t in plan["tasks"] if states.get(t["id"]) != "completed"]
        if pending:
            return "faltan tareas de la etapa aprobada por terminar: " + ", ".join(pending[:8])
    except Exception as exc:  # noqa: BLE001 - stale or unreadable runtime state cannot authorize a merge
        return f"no pude comprobar la ejecución de la etapa ({type(exc).__name__})"
    return ""


def merge(project: str, rdir: Path, push: bool) -> list[str]:
    """Merge the feature branch into the default branch of every repo that has it. All-or-nothing pre-checks:
    nothing is merged if any repo is dirty."""
    import bt_verification
    if (waiting := bt_verification.gate(rdir)):          # every subplan must be tried and approved before the work is merged
        return ["No fusioné nada: faltan subplanes por aprobar tras probarlos (" + "; ".join(waiting[:6]) +
                "). Pruébalos y apruébalos en Plan → Probar."]
    if (short := stage_gap(rdir)):                       # D-134: only the stage holding the whole plan can be closed
        return [f"No fusioné nada: STAGE_INCOMPLETE: {short}"]
    branch = feature_branch(rdir)
    targets = {r: (p, s) for r, (p, s) in
               {role: (path, repo_state(path, branch)) for role, path in ws.repos(ROOT, project).items()}.items()
               if s.get("branch") and not s.get("merged")}
    if not targets:
        return ["Nada que fusionar: ningún repo tiene la rama " + branch + " pendiente."]
    dirty = [r for r, (_, s) in targets.items() if s["dirty"]]
    if dirty:
        return [f"No fusioné nada: hay cambios sin commit en {', '.join(dirty)}. Haz commit o stash y vuelve a intentar."]
    out = []
    req = req_id(rdir)
    for role, (path, st) in targets.items():
        current = _git(path, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        if _git(path, "checkout", "-q", st["base"]).returncode != 0:
            out.append(f"{role}: no pude cambiar a {st['base']}")
            continue
        res = _git(path, "merge", "--no-ff", "-m", f"merge: {req} ({branch})", branch)
        if res.returncode != 0:
            _git(path, "merge", "--abort")
            _git(path, "checkout", "-q", current)
            out.append(f"{role}: conflicto al fusionar — dejé el repo como estaba ({current})")
            continue
        line = f"{role}: fusionada {branch} → {st['base']} ({len(st['commits'])} commits)"
        if push:
            p = _git(path, "push", "-q", "origin", st["base"], timeout=120)
            line += " · push OK" if p.returncode == 0 else f" · push FALLÓ: {(p.stderr or '').strip()[:150]}"
        out.append(line)
    return out
