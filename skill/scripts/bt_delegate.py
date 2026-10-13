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


def create(project: str, task: str, profile: str | None, agent: str | None, workdir: Path, allow: list[str],
           verify: str | None, timeout_min: int, model: str | None, effort: str | None) -> dict:
    """Validate and write TASK.json. The permission gate runs here, before any prompt with code exists."""
    if profile:
        bt_profiles.authorize(profile, project)
        agent = bt_profiles.require_launchable(profile)
        ok, why = bt_profiles.gate_cwd(profile, workdir)  # the folder must belong to a work project too
        if not ok:
            raise SystemExit(why)
    if agent not in ("claude", "codex", "antigravity"):
        raise SystemExit("Pass --profile ID or --agent claude|codex|antigravity")
    workdir = Path(workdir).expanduser().resolve()
    if not workdir.is_dir():
        raise SystemExit(f"Working directory does not exist: {workdir}")
    did = new_id()
    order = {"id": did, "project": project, "profile": profile, "agent": agent, "task": task.strip(),
             "workdir": str(workdir), "allow": allow, "verify": verify, "timeout_min": timeout_min,
             "model": model, "effort": effort, "created": dt.datetime.now().astimezone().isoformat(timespec="seconds")}
    d = path_of(did)
    d.mkdir(parents=True, exist_ok=True)
    (d / "TASK.json").write_text(json.dumps(order, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return order


def _prompt(order: dict, result: Path) -> str:
    allow = f"- You may only modify: {', '.join(order['allow'])}\n" if order["allow"] else ""
    verify = (f"- This will be checked independently by running: `{order['verify']}`. Make it pass.\n"
              if order.get("verify") else "")
    return PROMPT.format(project=order["project"], task=order["task"], workdir=order["workdir"], allow=allow,
                         verify=verify, result=result.as_posix(), id=order["id"])


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


def execute(did: str, agent_cmd: str | None = None) -> dict:
    """Run the delegation to completion (blocking) and write RESULT.json + OUTCOME.json. Returns summary()."""
    d = path_of(did)
    order = json.loads((d / "TASK.json").read_text(encoding="utf-8"))
    workdir = Path(order["workdir"])
    result_file, log_file, prompt_file = d / "RESULT.json", d / "session.log", d / "prompt.txt"
    bt_profiles.authorize(order.get("profile"), order["project"])  # again: nothing runs on a stale permission
    prompt = _prompt(order, result_file)
    prompt_file.write_text(prompt, encoding="utf-8")
    state = {"agent": order["agent"], "model": order.get("model"), "req": did, "profile": order.get("profile")}
    before = set(_git_changed(workdir) or [])
    env = {**os.environ, **bt_profiles.env_of(order.get("profile")), "BITACORA_PROJECT": order["project"],
           "BITACORA_DELEGATION": did}
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
            "model": order.get("model"), "effort": order.get("effort")}
    changed_all = _git_changed(workdir)
    changed = sorted(set(changed_all) - before) if changed_all is not None else None
    verify = _verify(order["verify"], workdir) if order.get("verify") and not base.get("status") else None
    claimed = bool(report and report["status"] == "done")
    if base.get("status"):
        status = base["status"]
    elif timed_out:
        status = "timeout"
    elif settle.detect_limit(info) is not None and not report:
        status = "usage_limit"
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
    outcome = {"id": order["id"], "status": status, "claimed_done": claimed, "verified": (
        None if verify is None else verify["exit"] == 0), "rc": rc, "seconds": seconds,
        "summary": (report or {}).get("summary") or base.get("error") or settle.parse_output(text)["text"][:SUMMARY_MAX],
        "changed_files": changed if changed is not None else (report or {}).get("changed_files", []),
        "outside_allowed": _outside(changed or [], order.get("allow") or []),
        "followups": (report or {}).get("followups", []), "verify": verify,
        "result_file": (d / "RESULT.json").as_posix() if report else None, "log": (d / "session.log").as_posix()}
    (d / "OUTCOME.json").write_text(json.dumps(outcome, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    bt_events.record_attempt(order["project"], {"agent": order["agent"], "req": order["id"],
                                                "profile": order.get("profile")},
                             order["id"], 1, info, status)
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
        return json.loads(outcome.read_text(encoding="utf-8"))
    if (d / "TASK.json").exists():
        return {"id": did, "status": "running_or_pending", "log": (d / "session.log").as_posix()}
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
