"""The failure analyst (P-138, owner rule D-115): a task that failed MORE THAN TWICE goes to a model that reads all the context, names the
cause and the way out, and does NOT carry it out. Its answer goes into the next attempt's prompt, after the history it was built from.

Why: a retry sees the last failure and the list of earlier ones, and still repeats itself (REQ-027 T15: 13 attempts; REQ-020 T14a: five
rejections of a command that could not work). A reader who is not in the middle of the task sees the pattern.

- `due(rdir, task, doc)`: the task has `FAILURES_BEFORE` + 1 failed attempts and nothing newer than the last analysis explains them
  (a new analysis only after `REANALYZE_AFTER` further failures: one that did not help is not repeated on every attempt);
- `analyze(...)`: one model call through the diagnosis profile (`diagnosis.*`: the same read-only sandbox, no tools that write), JSON
  `{cause, solution, confidence}`, stored in `RUN.notes/<task>.analysis.json`;
- `prompt(rdir, task)`: what the next attempt reads. Marked as an opinion: the agent checks it against the code instead of obeying it;
- `cycle(...)`: the watcher's turn; starts at most one background analysis per task (`scheduler-op REQ analyze TASK`).
Config: `analyst.auto` (default on). It never changes state: no revision, no retry, no verdict.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

FAILURES_BEFORE = 2
REANALYZE_AFTER = 2
MAX_CONTEXT = 14000
NOTES = "RUN.notes"

PROMPT = """You are the failure analyst of a software scheduler. One task has failed {failures} attempts. You can only read: you change nothing and
run nothing. Read everything below and answer with ONE JSON object and nothing else:
{{"cause": "the root cause in at most 4 sentences, naming the file, command or assumption that is wrong",
  "solution": "what the next attempt must do differently, in at most 5 short numbered steps",
  "not_the_task": true|false, "confidence": "alta"|"media"|"baja"}}
`not_the_task` is true when the cause is outside what the task may change (the plan, the environment, a missing credential, another task's
work): then say so in `cause` and say who must act in `solution`. Do not repeat an approach the history says already failed.

{bundle}
"""


def path(rdir: Path | str, task: str) -> Path:
    return Path(rdir) / NOTES / f"{task}.analysis.json"


def load(rdir: Path | str, task: str) -> dict[str, Any]:
    try:
        data = json.loads(path(rdir, task).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _save(rdir: Path | str, task: str, data: dict[str, Any]) -> None:
    target = path(rdir, task)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".tmp")
    tmp.write_text(json.dumps({"task": task, **data}, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def failures(rdir: Path | str, task: str, doc: dict) -> int:
    import bt_attempt_history

    return sum(1 for h in bt_attempt_history.entries(Path(rdir), task, doc) if h["outcome"] != "accepted")


def enabled() -> bool:
    try:
        import bt_config

        return bt_config.get("analyst.auto", True) is True
    except Exception:  # noqa: BLE001 - without a readable config the analyst stays off
        return False


def due(rdir: Path | str, task: str, doc: dict) -> int:
    """The failure count that deserves an analysis now, or 0."""
    count = failures(rdir, task, doc)
    if count <= FAILURES_BEFORE:
        return 0
    last = load(rdir, task)
    if last.get("state") == "running" and time.time() - float(last.get("started", 0)) < 1800:
        return 0
    return count if count >= int(last.get("failures", 0) or 0) + (REANALYZE_AFTER if last.get("state") else 1) else 0


def _spec(plan: Any, task: str) -> dict[str, Any]:
    """The task of the approved plan as plain data. The plan is the scheduler's `Plan` (TaskSpec objects); a dict is accepted too."""
    if plan is None:
        return {}
    if isinstance(plan, dict):
        found = next((t for t in plan.get("tasks", []) if isinstance(t, dict) and t.get("id") == task), None)
        return {k: found[k] for k in ("id", "title", "objective", "acceptance_criteria", "expected_paths", "verification", "after")
                if found and found.get(k)}
    try:
        spec = plan.task(task)
    except Exception:  # noqa: BLE001 - a task the plan does not know is analysed without its text
        return {}
    meta = getattr(spec, "meta", {}) or {}
    data = {"id": spec.id, "title": meta.get("title"), "objective": meta.get("objective"), "acceptance_criteria": spec.acceptance_criteria,
            "expected_paths": spec.expected_paths, "verification": spec.verification, "after": spec.after}
    return {k: v for k, v in data.items() if v}


def bundle(rdir: Path, task: str, doc: dict, plan: dict | None) -> str:
    import bt_attempt_history
    import bt_scheduler_decisions as decisions

    parts = []
    spec = _spec(plan, task)
    if spec:
        parts.append("THE TASK (from the approved plan):\n" + json.dumps(spec, ensure_ascii=False, indent=1, default=str)[:5000])
    for label, text in (("HISTORY OF THE ATTEMPTS", bt_attempt_history.prompt(rdir, task, doc)),
                        ("LAST VERIFICATION NOTE", decisions.verify_notes(rdir, task)),
                        ("AUDIT NOTES", decisions.audit_notes(rdir, task)),
                        ("OWNER'S NOTES", decisions.operator_notes(rdir, task))):
        if text:
            parts.append(f"{label}:\n{text}")
    return "\n\n".join(parts)[:MAX_CONTEXT]


def parse(text: str) -> dict[str, Any]:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("the answer has no JSON")
    data = json.loads(text[start:end + 1])
    cause, solution = str((data or {}).get("cause") or "").strip(), str((data or {}).get("solution") or "").strip()
    if not cause or not solution:
        raise ValueError("the answer lacks the cause or the solution")
    return {"cause": cause[:1200], "solution": solution[:1500], "not_the_task": data.get("not_the_task") is True,
            "confidence": data.get("confidence") if data.get("confidence") in ("alta", "media", "baja") else "media"}


def analyze(project: str, rdir: Path, task: str, *, runner: Callable[..., Any] = subprocess.run, config: dict | None = None,
            doc: dict | None = None, plan: dict | None = None) -> dict[str, Any]:
    """Ask the configured model and store its analysis (or the failure, also stored so it is not asked again at once)."""
    import bt_block_agent
    import bt_profiles
    import bt_scheduler_decisions as decisions

    rdir = Path(rdir)
    doc = doc if doc is not None else decisions._state(rdir)
    plan = plan if plan is not None else decisions._plan(rdir)
    count = failures(rdir, task, doc)
    config = config or bt_block_agent.settings()
    pid, model, effort = config["profile"], config["model"], config["effort"]
    started = time.time()
    _save(rdir, task, {"state": "running", "failures": count, "started": started})
    try:
        spec = bt_profiles.get(pid)
        provider = spec["provider"]
        bt_profiles.authorize(pid, project)
        env = bt_profiles.session_env(pid, provider, None, project)
        prompt = PROMPT.format(failures=count, bundle=bundle(rdir, task, doc, plan))
        with tempfile.TemporaryDirectory(prefix="bt-analyst-") as work:
            out = Path(work) / "answer.txt"
            done = runner(bt_block_agent.argv(provider, spec.get("bin") or provider, model, effort, out), input=prompt, text=True,
                          capture_output=True, cwd=work, env=env, timeout=int(config["timeout_seconds"]))
            text = out.read_text(encoding="utf-8") if out.is_file() else (done.stdout or "")
        if done.returncode:
            raise ValueError(f"{provider} exited with {done.returncode}: {(done.stderr or done.stdout or '')[-300:]}")
        result = {"state": "done", **parse(text)}
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired, SystemExit) as exc:
        result = {"state": "failed", "error": str(exc)[:400]}
    result.update({"failures": count, "model": model, "profile": pid, "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "seconds": round(time.time() - started, 1)})
    _save(rdir, task, result)
    return result


def prompt(rdir: Path | str, task: str) -> str:
    """The analyst's section of a retry's prompt ('' until there is an analysis that finished)."""
    data = load(rdir, task)
    if data.get("state") != "done":
        return ""
    who = "the task's own scope" if not data.get("not_the_task") else "OUTSIDE what this task may change"
    return (f"Independent failure analysis (after {data.get('failures')} failed attempts; confidence {data.get('confidence')}; the cause lies in "
            f"{who}). It is an opinion of a reader who ran nothing: check it against the code and the failures above before you follow it.\n"
            f"Cause: {data.get('cause')}\nWhat to do differently: {data.get('solution')}")


def spawn(project: str, req: str, task: str) -> bool:
    script = Path(__file__).resolve().parent / "bitacora.py"
    try:
        subprocess.Popen([sys.executable, str(script), "--project", project, "scheduler-op", req, "analyze", task],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    except OSError:
        return False
    return True


def cycle(project: str, req: str, rdir: Path | str, *, log: Callable[[str], None] = lambda text: None,
          starter: Callable[[str, str, str], bool] = spawn) -> int:
    """The watcher's turn: one background analysis for each task that needs one. How many were started."""
    if not enabled():
        return 0
    import bt_scheduler_decisions as decisions

    rdir = Path(rdir)
    try:
        doc = decisions._state(rdir)
    except Exception:  # noqa: BLE001 - a run without readable state has nothing to analyse
        return 0
    started = 0
    for task, record in (doc.get("tasks") or {}).items():
        if not isinstance(record, dict) or record.get("state") == "completed" or not due(rdir, task, doc):
            continue
        _save(rdir, task, {"state": "running", "failures": failures(rdir, task, doc), "started": time.time()})   # before the start: never twice
        if starter(project, req, task):
            started += 1
            log(f"analyst: {task} failed {failures(rdir, task, doc)} times: analysis started")
    return started
