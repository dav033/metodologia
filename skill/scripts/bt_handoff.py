"""Automatic hand-off: from a written plan to a running, supervised execution without a second conversation.

`assess` reads PLAN.md (and SPEC.md) and answers two questions. Is the plan runnable (problems: no tasks, unknown or
circular dependencies, an unknown repo role)? Does it need the owner's approval first (reasons: too many milestones or
tasks, an architecture-level or high-risk task, or text that names an irreversible, external, financial or
security-sensitive action)? `handoff` then either approves the plan itself and starts the marathon in the background
with the account pool, or puts the plan in review and says exactly why. A plan the owner already approved is launched
whatever the reasons. Thresholds: bt_config (approval.*). Rules: references/requirements.md, "Automatic hand-off".
"""
from __future__ import annotations

import re

import bt_config
import bt_rounds as rounds
import bt_runstate as rs
from bt_core import *  # noqa: F403
from bt_core import _front

# Conservative on purpose: a false positive costs one approval click, a false negative an unattended risky action.
RISK_WORDS = (
    ("irreversible data change", r"\b(drop\s+(table|database|schema|column)|truncate\s+table|delete\s+from|rm\s+-rf|"
                                 r"wipe|purge|destroy|irreversibl\w*\s+(change|migration|action|operation|step)\w*|"
                                 r"data\s+migration|backfill)\b"),
    ("production or deploy", r"\b(prod(uction)?\b|deploy\w*|release\s+to|publish\w*|go[- ]live|rollout)"),
    ("git history or remote", r"\b(force[- ]push|git\s+push|push\s+to\s+(main|master|origin)|rewrite\s+history|"
                              r"merge\s+(in)?to\s+(main|master))\b"),
    ("money", r"\b(payment\w*|billing|invoice\s+customers|charge\w*|refund\w*|stripe|paypal|payout\w*)\b"),
    # an ACTION on credentials or access rules; merely naming them ("never store secrets") is not a reason
    ("credentials or access", r"\b((rotat|chang|creat|stor|expos|shar|grant|revok|updat|modif|generat)\w*\s+"
                              r"(the\s+|a\s+|an\s+|new\s+|production\s+|user\s+)?(credential\w*|secret\w*|"
                              r"api[_ -]?key\w*|password\w*|permission\w*|access\s+token\w*)|"
                              r"(auth(entication|orization)|access\s+control|oauth)\s+(flow|system|logic|layer|"
                              r"change\w*|rule\w*|middleware|provider))\b"),
    ("external communication", r"\b(send\s+(e-?mail|sms|message)\w*|notify\s+(users|customers)|webhook\s+to|"
                               r"post\s+to\s+(slack|twitter|x)\b)"),
)


def _cycle(tasks: list[dict]) -> list[str]:
    graph = {t["id"]: [a for a in t["after"]] for t in tasks}
    state: dict[str, int] = {}

    def visit(node: str, path: list[str]) -> list[str]:
        if state.get(node) == 1:
            return path[path.index(node):] + [node]
        if state.get(node) == 2 or node not in graph:
            return []
        state[node] = 1
        for nxt in graph[node]:
            found = visit(nxt, path + [node])
            if found:
                return found
        state[node] = 2
        return []

    for tid in graph:
        found = visit(tid, [])
        if found:
            return found
    return []


_NEGATION = re.compile(r"\b(never|do not|don't|does not|doesn't|must not|mustn't|shall not|won't|will not|"
                       r"without|no|not|out of scope:?|excluded?:?|refuses? to)\s+(\w+\s+){0,3}$", re.I)
# A verify command runs through the shell, unattended, with the supervisor's own permissions: anything in it that
# writes, deletes, escalates or reaches the network must be seen by the owner first.
VERIFY_RISK = re.compile(r"(^|[\s;&|(`$])(sudo|rm|rmdir|mv|dd|chmod|chown|kill|pkill|curl|wget|ssh|scp|rsync|nc|"
                         r"docker|kubectl|psql|mysql|mongo\w*|redis-cli|git\s+(push|reset|clean|checkout|rebase)|"
                         r"npm\s+publish|eval|source)(\s|$)|\|\s*(ba|z|fi)?sh\b|>\s*[/~]|>>\s*[/~]")


def _negated(text: str, start: int) -> bool:
    """The risky phrase is the object of a stated limit in ITS OWN clause ("never push", "out of scope: payments").
    A negation elsewhere on the line ("Deploy billing change; no tests") does not excuse it."""
    clause = re.split(r"[.;:!?\n]|\s+-\s+|\s+—\s+", text[max(0, start - 80):start])[-1]
    before = text[max(0, start - 80):start]
    tail = before[len(before) - len(clause) - 14:]  # keep "out of scope:" attached to what follows its colon
    return bool(_NEGATION.search(clause) or re.search(r"(out of scope|excluded?)\s*:\s*(\w+[\s,]+){0,6}$", tail, re.I))


def _risky_text(text: str) -> list[str]:
    text = re.sub(r"<!--.*?-->", "", text or "", flags=re.S)
    found = []
    for label, pattern in RISK_WORDS:
        for m in re.finditer(pattern, text, re.I):
            if not _negated(text, m.start()):
                found.append(f"{label}: the text mentions \"{m.group(0).strip()}\"")
                break
    return found


def _risky_verify(tasks: list[dict]) -> list[str]:
    out = []
    for t in tasks:
        m = VERIFY_RISK.search(t.get("verify") or "")
        if m:
            out.append(f"{t['id']} verify command does more than check (`{m.group(0).strip()}`): it runs unattended "
                       "through the shell")
    return out


def assess(project: str, rdir: Path) -> dict:
    """{ok, problems, reasons, auto, tasks, milestones}: problems make the plan unrunnable; reasons require the
    owner's approval; `auto` = it may start with no one asked."""
    plan, spec = rdir / "PLAN.md", rdir / "SPEC.md"
    tasks = rs.parse_plan(plan)
    stones = rs.milestones(plan)
    problems, reasons = [], []
    if not plan.exists():
        problems.append("there is no PLAN.md")
    elif not tasks:
        problems.append("PLAN.md has no task lines (`- [ ] T1 — title · repo: role · verify: `cmd``)")
    ids = [t["id"] for t in tasks]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(f"task id {dup} appears more than once")
    for t in tasks:
        for dep in t["after"]:
            if dep not in ids:
                problems.append(f"{t['id']} depends on {dep}, which is not in the plan")
    loop = _cycle(tasks)
    if loop:
        problems.append("circular dependency: " + " -> ".join(loop))
    roles = ws.repos(ROOT, project)
    for t in tasks:
        if t["repo"] and t["repo"] not in roles:
            problems.append(f"{t['id']} names repo role '{t['repo']}', not registered (have: {', '.join(roles) or 'none'})")
    if not roles:
        problems.append(f"no repository is registered for '{project}' (bitacora.py --project {project} workspace add <role> <path>)")
    pending = [t for t in tasks if not t["done"]]
    max_m, max_t = bt_config.get("approval.max_milestones", 8), bt_config.get("approval.max_tasks", 40)
    if len(stones) > max_m:
        reasons.append(f"{len(stones)} milestones (more than {max_m})")
    if len(pending) > max_t:
        reasons.append(f"{len(pending)} pending tasks (more than {max_t})")
    for t in pending:
        if t["level"] == "architecture":
            reasons.append(f"{t['id']} is an architecture-level task")
        if t.get("risk") in ("high", "critical"):
            reasons.append(f"{t['id']} is marked risk: {t['risk']}")
    reasons += _risky_verify(pending)
    unverified = [t["id"] for t in pending if not t["verify"]]
    if pending and len(unverified) == len(pending):
        reasons.append("no task has a machine-runnable verify: nothing would check the work independently")
    for source in (plan, spec):
        try:
            reasons += [f"{source.name}: {r}" for r in _risky_text(source.read_text(encoding="utf-8"))]
        except OSError:
            pass
    if not bt_config.get("approval.auto", True):
        reasons.append("automatic approval is turned off (config approval.auto)")
    return {"ok": not problems, "problems": problems, "reasons": reasons, "auto": not problems and not reasons,
            "tasks": len(tasks), "pending": len(pending), "milestones": [m["id"] for m in stones],
            "unverified": unverified}


def handoff(project: str, req: str, dry_run: bool = False, pool: str | None = None, model: str | None = None,
            profile: str | None = None) -> dict:
    """Approve-and-launch when the plan is safe to start unattended, otherwise leave it in review with the reasons.
    Returns {decision: launched | needs_approval | invalid | already_running, ...}."""
    rdir = find_req(ROOT / project, req)
    rid = req_id(rdir)
    plan = rdir / "PLAN.md"
    report = assess(project, rdir)
    status = _front(plan, "status") if plan.exists() else None
    out = {"project": project, "req": rid, "plan_status": status, **report}
    if not report["ok"]:
        return {**out, "decision": "invalid", "next": "fix the plan problems, then run handoff again"}
    if status in ("launched", "done"):
        return {**out, "decision": "already_running" if status == "launched" else "done",
                "next": f"bitacora.py --project {project} run-control {rid} pause|resume|stop"}
    approved = status == "approved"
    if report["reasons"] and not approved:
        if not dry_run:
            rounds.plan_review(rdir)
            with plan.open("a", encoding="utf-8") as fh:
                fh.write(f"- {dt.datetime.now():%Y-%m-%d %H:%M} hand-off held for approval: "
                         + "; ".join(report["reasons"])[:600] + "\n")
            from bt_vcs import commit
            commit(ROOT, f"{project}: {rid} hand-off needs approval")
        return {**out, "decision": "needs_approval",
                "next": f"owner approves (web, or: bitacora.py --project {project} plan approve {rid}), then handoff again"}
    display = bt_config.get("executor.display", "background")
    mode_pool = pool or ("auto" if bt_config.get("routing.mode", "auto") == "auto" else None)
    if dry_run:
        return {**out, "decision": "would_launch", "pool": mode_pool, "display": display}
    if not approved:
        rounds.plan_decide(rdir, True, "no approval reasons found by the automatic hand-off", "handoff")
    from bt_launch import launch
    extra = {"profile": profile} if profile else {}
    result = launch(project, rid, mode="marathon", model=model or "haiku", pool=mode_pool,
                    background=display == "background", **extra)
    return {**out, "decision": "launched", "pool": mode_pool, "display": display, "opened": result["opened"],
            "handoff": result["handoff"],
            "next": f"watch: bitacora.py web · control: bitacora.py --project {project} run-control {rid} pause|resume|stop"}
