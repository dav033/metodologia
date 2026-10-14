"""Delegate ONE task to a headless agent session and get back a compact, independently checked result.

For the Agile track and for ad-hoc work: no PLAN.md, no RUN.json, no supervisor loop. A delegation lives under
<root>/.state/delegations/<id>/ with TASK.json (the order), prompt.txt, session.log (full output, never returned to
the caller) and RESULT.json (the agent's report). The caller only receives `summary()`: status, a short summary,
changed files and the verify outcome. "The agent said it finished" is never a success by itself: with --verify the
command's exit status decides, without it the status stays `claimed` (unverified).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

import bt_agents
import bt_events
import bt_platform as host
import bt_profiles
import bt_runprompt as rp
import bt_runsettle as settle
from bt_core import ROOT, SCRIPT, STATE
from bt_runsession import kill_tree

DIR = STATE / "delegations"
SUMMARY_MAX = 400
RESULT_KEYS = ("task_id", "status", "summary", "evidence", "changed_files", "test_result", "notes", "followups")
VERIFY_TIMEOUT_SEC = 900

PROMPT = """You are executing ONE delegated task for project `{project}`. Work only on this task.

## Task
{task}

## Constraints
- Working directory: {workdir}
{allow}- Do not run `git push`, do not merge, do not delete files outside the task, do not read or print secrets.
- Do not commit unless the task explicitly asks for it.
{verify}
## Report (required)
When finished, write a JSON file at `{result}` with exactly these keys:
{{"task_id": "{id}", "status": "done" | "partial" | "blocked", "summary": "<=3 sentences",
 "evidence": "what you ran and saw", "changed_files": ["relative/paths"], "test_result": "pass|fail|not_run + detail",
 "notes": "", "followups": ["anything out of scope you noticed"]}}
Keep the summary short; full logs stay in the session. If you cannot finish, say so with status "blocked".
"""


def new_id() -> str:
    return f"D-{dt.datetime.now():%Y%m%d-%H%M%S}-{secrets.token_hex(2)}"


def path_of(did: str) -> Path:
    if not did or "/" in did or "\\" in did or did.startswith("."):
        raise SystemExit(f"Invalid delegation id: {did!r}")
    return DIR / did


def auto_route(project: str, kind: str, tier: int | None, avoid: set | None = None) -> dict:
    """The router's choice for a delegation nobody pinned to an account: every account allowed for the project is a
    candidate, usage limits and measured results decide (bt_agents.route)."""
    pool = bt_agents.pool_for(project, bt_agents._config("routing.pool", []) or None)
    if not pool:
        raise SystemExit(f"No account may run '{project}'. Check: bitacora.py agents")
    tier = bt_agents.start_tier(None, kind) if tier is None else tier
    try:
        return bt_agents.route(project, {"pool": pool}, tier, kind, avoid)
    except bt_agents.NoRoute as exc:
        raise SystemExit(f"Every account is waiting for a usage-limit reset (earliest "
                         f"{dt.datetime.fromtimestamp(exc.until):%Y-%m-%d %H:%M}). Nothing was sent.") from exc


def create(project: str, task: str, profile: str | None, agent: str | None, workdir: Path, allow: list[str],
           verify: str | None, timeout_min: int, model: str | None, effort: str | None,
           kind: str | None = None, tier: int | None = None, complexity: str | None = None,
           wait_quota: bool = False) -> dict:
    """Validate and write TASK.json. The permission gate runs here, before any prompt with code exists. With neither
    --profile nor --agent the router picks account, model and effort for the task's kind and tier."""
    kind = kind if kind in bt_agents.KINDS else bt_agents.infer_kind(task[:200])
    routed = None
    if not profile and not agent:
        own = os.environ.get("BITACORA_KIND")  # an audit delegated from a builder session goes to another provider
        avoid = {bt_profiles.ambient_provider()} if kind == "audit" and own != "audit" else None
        routed = auto_route(project, kind, tier, avoid - {None} if avoid else None)
        profile, model, effort = routed["profile"], model or routed["model"], effort or routed["effort"]
    if profile:
        bt_profiles.authorize(profile, project)
        agent = bt_profiles.require_launchable(profile)
        ok, why = bt_profiles.gate_cwd(profile, workdir)  # the folder must belong to a work project too
        if not ok:
            raise SystemExit(why)
        if tier is not None and not model:
            model, effort = bt_agents.model_for(agent, tier, None, kind)[0], effort or bt_agents.model_for(agent, tier, None, kind)[1]
    elif agent in bt_profiles.LAUNCHABLE:
        bt_profiles.authorize_ambient(agent, project, workdir)  # the inherited account may be a work-only one
    if agent not in bt_profiles.LAUNCHABLE:
        raise SystemExit(f"Pass --profile ID, --agent {'|'.join(bt_profiles.LAUNCHABLE)}, or neither to let the router choose")
    if kind == "audit":
        tier = bt_agents.start_tier(None, kind) if tier is None else tier
        default_model, default_effort = bt_agents.model_for(agent, tier, kind=kind)
        model = model or default_model
        effort = effort or default_effort
    if agent == "codex" and model and not effort:  # an account's config default may not suit this model
        effort = "medium"
    workdir = Path(workdir).expanduser().resolve()
    if not workdir.is_dir():
        raise SystemExit(f"Working directory does not exist: {workdir}")
    did = new_id()
    order = {"id": did, "project": project, "profile": profile, "agent": agent, "task": task.strip(),
             "workdir": str(workdir), "allow": allow, "verify": verify, "timeout_min": timeout_min,
             "model": model, "effort": effort, "kind": kind, "tier": tier if tier is not None else (routed or {}).get("tier"),
             "routed": (routed or {}).get("why"), "auto": bool(routed),
             "complexity": complexity if complexity in ("S", "M", "L") else None, "wait_quota": bool(wait_quota),
             "created": dt.datetime.now().astimezone().isoformat(timespec="seconds")}
    d = path_of(did)
    d.mkdir(parents=True, exist_ok=True)
    (d / "TASK.json").write_text(json.dumps(order, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return order


def _prompt(order: dict, result: Path) -> str:
    allow = f"- You may only modify: {', '.join(order['allow'])}\n" if order["allow"] else ""
    verify = (f"- This will be checked independently by running: `{order['verify']}`. Make it pass.\n"
              if order.get("verify") else "")
    prompt = PROMPT.format(project=order["project"], task=order["task"], workdir=order["workdir"], allow=allow,
                           verify=verify, result=result.as_posix(), id=order["id"])
    previous = str(order.get("previous_attempt") or "")[:600]
    return prompt + (f"\n## Previous attempt\n{previous}\n" if previous else "")


def _git_changed(workdir: Path) -> list[str] | None:
    try:
        res = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=workdir,
                             capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if res.returncode != 0:
        return None
    return sorted(line[3:].split(" -> ")[-1].strip('"') for line in res.stdout.splitlines() if len(line) > 3)


def _outside(changed: list[str], allow: list[str]) -> list[str]:
    if not allow:
        return []
    prefixes = [a.rstrip("/").replace("\\", "/") for a in allow]
    return [c for c in changed if not any(c == p or c.startswith(p + "/") for p in prefixes)]


def _read_result(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    out = {k: data.get(k) for k in RESULT_KEYS}
    out["summary"] = str(out.get("summary") or "")[:SUMMARY_MAX]
    out["status"] = out["status"] if out["status"] in ("done", "partial", "blocked") else None
    for key in ("changed_files", "followups"):
        out[key] = [str(x) for x in out[key]][:50] if isinstance(out[key], list) else []
    return out


def _verify(command: str, workdir: Path) -> dict:
    start = time.time()
    try:
        res = subprocess.run(command, cwd=workdir, shell=True, capture_output=True, text=True,
                             timeout=VERIFY_TIMEOUT_SEC, encoding="utf-8", errors="replace")
        return {"command": command, "exit": res.returncode, "seconds": int(time.time() - start),
                "tail": (res.stdout + res.stderr).strip()[-600:]}
    except subprocess.TimeoutExpired:
        return {"command": command, "exit": None, "seconds": VERIFY_TIMEOUT_SEC, "tail": "verify timed out"}


MAX_REROUTES = 4
QUOTA_WAIT_CAP_SEC = 12 * 3600      # one nap; availability is re-checked after each
MAX_QUOTA_WAIT_SEC = 8 * 24 * 3600  # weekly limits exist: give up only after more than a week


def execute(did: str, agent_cmd: str | None = None) -> dict:
    """Run the delegation to completion (blocking) and write RESULT.json + OUTCOME.json. Returns summary().
    A usage limit does not end a delegation the router placed: it is sent again to another account; when every
    account is cooling down it waits for the earliest reset if the order asked for it (--wait-quota), otherwise the
    outcome says when to retry."""
    d = path_of(did)
    order = json.loads((d / "TASK.json").read_text(encoding="utf-8"))
    _claim(d, did)
    outcome, tried = {}, []
    for attempt in range(1, MAX_REROUTES + 2):
        order["attempt"] = attempt
        outcome = _attempt(d, order, agent_cmd)
        tried.append(f"{order.get('profile') or order['agent']}:{outcome['status']}")
        if outcome["status"] != "usage_limit" or not (order.get("auto") or order.get("wait_quota")):
            break
        nxt = _next_route(order)
        if nxt is None:
            break
        order.update(profile=nxt["profile"], agent=nxt["agent"], model=nxt["model"], effort=nxt["effort"],
                     routed=nxt.get("why"))
    if len(tried) > 1:
        outcome["rerouted"] = tried
        (d / "TASK.json").write_text(json.dumps(order, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        (d / "OUTCOME.json").write_text(json.dumps(outcome, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return outcome


def _claim(d: Path, did: str) -> None:
    """One execution per delegation id. The claim records its pid: a claim whose process died before writing an
    outcome (a crash, a refused permission) can be taken over instead of blocking the id forever."""
    claim = d / "CLAIMED"
    for _ in range(2):
        try:
            fd = os.open(claim, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return
        except FileExistsError:
            from bt_runutil import pid_alive
            try:
                owner = int(claim.read_text().strip() or 0)
            except (OSError, ValueError):
                owner = 0
            if (d / "OUTCOME.json").exists() or (owner and owner != os.getpid() and pid_alive(owner)):
                raise SystemExit(f"Delegation {did} was already started; read it with: delegate status {did}") from None
            claim.unlink(missing_ok=True)  # stale: its process is gone and left no outcome
    raise SystemExit(f"Delegation {did} could not be claimed")


def _wait_for(until: float) -> None:
    override = os.environ.get("BITACORA_RUN_BACKOFF_SEC")
    time.sleep(float(override) if override else min(max(until - time.time(), 0) + 30, QUOTA_WAIT_CAP_SEC))


def _next_route(order: dict) -> dict | None:
    """Where a delegation that hit a usage limit runs next. One the router placed goes to another account; one pinned
    to an account or provider can only wait for that same account. Waiting happens only with --wait-quota, in bounded
    naps that re-check availability, for at most MAX_QUOTA_WAIT_SEC. None = give up now (the outcome carries
    retry_after)."""
    deadline = time.time() + MAX_QUOTA_WAIT_SEC
    same = {"profile": order.get("profile"), "agent": order["agent"], "model": order.get("model"),
            "effort": order.get("effort"), "why": "same account after its usage-limit reset"}
    tier = order.get("tier") if order.get("tier") is not None else bt_agents.start_tier(None, order.get("kind"))
    while True:
        if order.get("auto"):
            pool = bt_agents.pool_for(order["project"], bt_agents._config("routing.pool", []) or None)
            routes, soonest = bt_agents.candidates(order["project"], pool, tier, order.get("kind") or "implement")
            if routes:
                return routes[0]
        else:
            soonest = bt_agents.cooling_until(order.get("profile"), order["agent"])
            if not soonest:
                return same
        if not (order.get("wait_quota") and soonest) or time.time() >= deadline:
            return None
        _wait_for(soonest)


def _attempt(d: Path, order: dict, agent_cmd: str | None) -> dict:
    did = order["id"]
    workdir = Path(order["workdir"])
    result_file, log_file, prompt_file = d / "RESULT.json", d / "session.log", d / "prompt.txt"
    if order.get("profile"):  # again: nothing runs on a stale permission
        bt_profiles.authorize(order["profile"], order["project"])
    else:  # the order was written under one environment and may be executed under another
        bt_profiles.authorize_ambient(order["agent"], order["project"], order["workdir"])
    prompt = _prompt(order, result_file)
    prompt_file.write_text(prompt, encoding="utf-8")
    state = {"agent": order["agent"], "model": order.get("model"), "req": did, "profile": order.get("profile")}
    before = set(_git_changed(workdir) or [])
    env = {**bt_profiles.session_env(order.get("profile"), order["agent"], None, order["project"]),
           "BITACORA_PROJECT": order["project"],
           "BITACORA_DELEGATION": did, "BITACORA_KIND": order.get("kind") or "implement"}
    for key in ("BITACORA_RUN", "BITACORA_TASK", "BITACORA_SESSION"):  # a helper must not report as its parent's task
        env.pop(key, None)
    if agent_cmd:  # tests: command template with {prompt_file} {workdir} {result} {id}
        argv, stdin_text, shell = agent_cmd.format_map({"prompt_file": prompt_file.as_posix(),
                                                        "workdir": workdir.as_posix(), "result": result_file.as_posix(),
                                                        "id": did}), None, True
    else:
        argv, stdin_text = rp.agent_argv(state, workdir, prompt, order.get("model"), order.get("effort"))
        shell = False
    start, timed_out, rc = time.time(), False, None
    with log_file.open("wb", buffering=0) as out:
        try:
            proc = subprocess.Popen(argv, cwd=str(workdir), env=env, shell=shell, stdout=out,
                                    stderr=subprocess.STDOUT,
                                    stdin=subprocess.PIPE if stdin_text else subprocess.DEVNULL,
                                    **host.detached_options())
        except FileNotFoundError as exc:
            return _finish(d, order, {"status": "agent_error", "error": f"agent executable not found: {exc}"},
                           None, None, 0, False, None, before)
        try:
            proc.communicate(input=stdin_text.encode("utf-8") if stdin_text else None,
                             timeout=max(0.05, float(order["timeout_min"])) * 60)
        except subprocess.TimeoutExpired:
            timed_out = True
            kill_tree(proc)
        rc = proc.returncode
    return _finish(d, order, {}, rc, _read_result(result_file), int(time.time() - start), timed_out, log_file, before)


def _finish(d: Path, order: dict, base: dict, rc, report: dict | None, seconds: int, timed_out: bool,
            log_file: Path | None, before: set) -> dict:
    workdir = Path(order["workdir"])
    text = log_file.read_bytes().decode("utf-8", errors="replace") if log_file and log_file.exists() else ""
    info = {"rc": rc, "text": text, "seconds": seconds, "timed_out": timed_out, "stopped": False,
            "model": order.get("model"), "effort": order.get("effort"), "agent": order["agent"],
            "profile": order.get("profile"), "kind": order.get("kind"), "tier": order.get("tier")}
    changed_all = _git_changed(workdir)
    changed = sorted(set(changed_all) - before) if changed_all is not None else None
    verify = _verify(order["verify"], workdir) if order.get("verify") and not base.get("status") else None
    claimed = bool(report and report["status"] == "done")
    if base.get("status"):
        status = base["status"]
    elif timed_out:
        status = "timeout"
    elif settle.detect_limit(info) is not None and not report:
        status = "usage_limit"  # the router skips this account until it resets
        bt_agents.quota_mark(order.get("profile"), order["agent"], settle.detect_limit(info) or 0,
                             settle.limit_line(text[-4000:]), order.get("model"))
    elif verify is not None:
        status = "verified" if verify["exit"] == 0 else "verify_failed"
    elif report and report["status"] == "blocked":
        status = "blocked"
    elif claimed:
        status = "claimed"  # done by the agent's word only: no independent check was requested
    elif report:
        status = "partial"
    else:
        status = "failed"
    outcome = {"id": order["id"], "status": status, "agent": order["agent"], "profile": order.get("profile"),
               "model": order.get("model"), "effort": order.get("effort"), "kind": order.get("kind"),
               "claimed_done": claimed, "verified": (
        None if verify is None else verify["exit"] == 0), "rc": rc, "seconds": seconds,
        "summary": (report or {}).get("summary") or base.get("error") or settle.parse_output(text)["text"][:SUMMARY_MAX],
        "changed_files": changed if changed is not None else (report or {}).get("changed_files", []),
        "outside_allowed": _outside(changed or [], order.get("allow") or []),
        "followups": (report or {}).get("followups", []), "verify": verify,
        "result_file": (d / "RESULT.json").as_posix() if report else None, "log": (d / "session.log").as_posix()}
    (d / "OUTCOME.json").write_text(json.dumps(outcome, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    limit = settle.detect_limit(info) if status == "usage_limit" else None
    if status == "usage_limit":
        until = bt_agents.cooling_until(order.get("profile"), order["agent"])
        outcome["retry_after"] = dt.datetime.fromtimestamp(until).isoformat(timespec="minutes") if until else None
        (d / "OUTCOME.json").write_text(json.dumps(outcome, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    why = (f"verify `{verify['command']}` exit {verify['exit']}: {verify['tail'][-200:]}" if verify else
           settle.limit_line(text[-4000:]) if limit is not None else outcome["summary"])
    detail = {"complexity": order.get("complexity") or "S",
              "complexity_source": "declared" if order.get("complexity") else "inferred",
              "attempt": order.get("attempt", 1), "milestone": None, "titles": [order["task"][:90]],
              "outcome": bt_events.outcome_of(status, why), "why": " ".join(str(why).split())[:700]}
    bt_events.record_attempt(order["project"], {"agent": order["agent"], "req": order["id"],
                                                "profile": order.get("profile")},
                             order["id"], order.get("attempt", 1), info, status, detail)
    return outcome


def start_background(did: str) -> int:
    """Run `delegate exec` detached from this process; returns the child pid."""
    cmd = [sys.executable, str(SCRIPT), "--project", json.loads((path_of(did) / "TASK.json").read_text())["project"],
           "delegate", "exec", did]
    log = (path_of(did) / "supervisor.log").open("ab")
    proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=log, stderr=log, close_fds=True,
                            env={**os.environ, "BITACORA_ROOT": str(ROOT)}, **host.detached_options())
    return proc.pid


def summary(did: str) -> dict:
    d = path_of(did)
    outcome = d / "OUTCOME.json"
    if outcome.exists():
        result = json.loads(outcome.read_text(encoding="utf-8"))
        try:
            order = json.loads((d / "TASK.json").read_text(encoding="utf-8"))
            from bt_driver import driver_for
            raw = (d / "session.log").read_text(encoding="utf-8", errors="replace")
            contract = driver_for(order["agent"]).normalize(raw, result.get("rc"),
                                                             timed_out=result.get("status") == "timeout")
            result["contract"] = {"v": contract.version, "status": contract.status,
                                  "terminal": contract.terminal_event}
        except Exception:
            result["contract"] = None
        return result
    if (d / "TASK.json").exists():
        return {"id": did, "status": "running_or_pending", "log": (d / "session.log").as_posix(),
                "contract": None}
    raise SystemExit(f"Unknown delegation: {did}")


def listing(limit: int = 20) -> list[dict]:
    rows = []
    for d in sorted(DIR.glob("D-*"), reverse=True)[:limit]:
        try:
            order = json.loads((d / "TASK.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        s = summary(d.name)
        rows.append({"id": d.name, "project": order["project"], "profile": order.get("profile"),
                     "agent": order["agent"], "status": s["status"], "task": order["task"][:80]})
    return rows
