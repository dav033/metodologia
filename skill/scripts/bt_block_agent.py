"""A cheap model reads why a run stopped and writes the diagnosis for the owner (config `diagnosis.*`).

The rules of `bt_block_diagnosis` know the causes seen so far; an agent reads the same evidence bundle for the rest and
says, in plain Spanish, what failed, where it comes from, the steps to fix it and which offered option to pick. One
answer per decision request, cached in `RUN.diagnoses/<request>.json` (a new attempt is a new request, so a stale answer
never shows on a new stop). The watchdog asks for it in the background when a request appears; the owner can ask again
from the panel. The agent runs without tools that write and its answer is advice: only an owner's choice changes the run.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import bt_block_diagnosis as rules

DIR = "RUN.diagnoses"
RUNNING_SECONDS = 600            # a «diagnosing…» marker older than this belongs to a process that died
FIELDS = ("headline", "origin", "steps", "option", "note", "kind", "confidence")

PROMPT = """You diagnose why an automated software run stopped and tell its owner how to fix it.
The owner is not reading logs: answer so that a person understands in ten seconds what failed, where it comes from
and what to press. Read only the evidence below; do not invent files, commands or causes it does not support.
The reason code (e.g. identity_unverified, attempts_exhausted) is only the system's last guard that tripped and is
often NOT the cause: the cause is in the attempt failures, the verification failure and the error text. A rule-based
guess, when present, was matched on that same evidence; when it names a concrete error, trust it unless the evidence
contradicts it, and explain it in your own words.

How the system works (use it to give instructions that are right):
- Each task runs as attempts of a coding agent; an independent verifier then runs the plan's verification commands in
  a sandbox: a clean copy of the final files WITHOUT .git, node_modules mounted read-only, an empty environment plus
  the variables of the owner's verifier env file (config verifier.env_file, e.g. ~/.config/metodologia/verifier-<project>.env).
  A command check is one argv: no |, ;, $, backticks or && chains; only a leading `cd <dir> &&` and leading `NAME=value`
  assignments. One refused command makes the verifier skip every check of the task.
- The plan's authority is PLAN.json next to the run. Changing a check, a criterion or a task is a new revision: raise
  "revision" by 1, run `bitacora.py --project <project> plan-json freeze <REQ>`, then pick the option `revise`.
- `retry_with_note`: your note is put first in the next attempt's prompt. `retry`: same task again, from its last snapshot.
- `rework_conflict`: redo the named task on top of the current work of the tasks it clashes with.
- Terminal: `bitacora.py --project <project> scheduler-op <REQ> status|decisions|decide <id> <option> --reason "…"`.
Prefer an option that moves the run forward; pick `stop` only when every other option would repeat the failure.

Answer with ONE JSON object and nothing else, written in Spanish (neutral, plain, no jargon unless quoted from the
evidence), with exactly these keys:
- "headline": one sentence, at most 90 characters: what failed.
- "origin": two or three sentences: where the failure comes from (the code, the plan, the environment, the system,
  another task), citing the decisive error text or file.
- "kind": one of {kinds}.
- "steps": 2 to 4 short imperative steps that fix it, in order; name exact commands or files from the evidence.
- "option": the id of the offered option to pick now, one of: {options}.
- "note": if the option is retry_with_note, the indication for the next attempt, in English, concrete; else "".
- "confidence": "alta", "media" or "baja".

Evidence:
{bundle}
"""


def path(rdir: Path, request_id: str) -> Path:
    safe = re.sub(r"[^\w.-]+", "_", request_id)[:80] + "-" + hashlib.sha256(request_id.encode()).hexdigest()[:8]
    return Path(rdir) / DIR / f"{safe}.json"


def cached(rdir: Path, request_id: str) -> dict | None:
    """The stored diagnosis, a `{"state": "running"}` marker while one is being written, or None."""
    try:
        data = json.loads(path(rdir, request_id).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or data.get("request") != request_id:
        return None
    if data.get("state") == "running" and time.time() - float(data.get("started", 0)) > RUNNING_SECONDS:
        return {"state": "failed", "request": request_id, "error": "el diagnóstico no terminó"}
    return data


def _write(rdir: Path, request_id: str, data: dict) -> None:
    target = path(rdir, request_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".tmp")
    tmp.write_text(json.dumps({"request": request_id, **data}, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(target)


def settings() -> dict:
    import bt_config
    return {key: bt_config.get(f"diagnosis.{key}") for key in ("auto", "profile", "model", "effort", "timeout_seconds")}


def argv(provider: str, binary: str, model: str, effort: str, out: Path) -> list[str]:
    if provider == "claude":
        cmd = [binary, "-p", "--model", model, "--output-format", "text",
               "--disallowedTools", "Bash,Edit,Write,NotebookEdit,WebFetch,WebSearch"]
        return cmd + (["--effort", effort] if effort else [])
    if provider == "codex":
        return [binary, "exec", "--model", model, "--config", f"model_reasoning_effort={effort or 'medium'}",
                "--sandbox", "read-only", "--skip-git-repo-check", "--output-last-message", str(out), "-"]
    raise ValueError(f"diagnosis does not drive {provider}")


def parse(text: str, request: dict) -> dict:
    """The model's JSON, checked: known kind, an offered option, 1-4 steps. Raises ValueError otherwise."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("la respuesta no trae JSON")
    data = json.loads(text[start:end + 1])
    if not isinstance(data, dict):
        raise ValueError("la respuesta no es un objeto")
    offered = [o["id"] for o in request.get("options", [])]
    kind = data.get("kind") if data.get("kind") in rules.KINDS else "unknown"
    steps = [str(s).strip() for s in data.get("steps") or [] if str(s).strip()][:4]
    if not str(data.get("headline") or "").strip() or not steps:
        raise ValueError("faltan el titular o los pasos")
    option = data.get("option") if data.get("option") in offered else request.get("recommended", "")
    label, tone = rules.KINDS[kind]
    return {"kind": kind, "label": label, "tone": tone, "headline": str(data["headline"]).strip()[:160],
            "origin": str(data.get("origin") or "").strip()[:900], "steps": [s[:400] for s in steps],
            "option": option, "note": str(data.get("note") or "").strip()[:2000] if option == "retry_with_note" else "",
            "confidence": data.get("confidence") if data.get("confidence") in ("alta", "media", "baja") else "media"}


def diagnose(project: str, rdir: Path, request: dict, evidence: str, *, runner=subprocess.run,
             config: dict | None = None) -> dict:
    """Ask the configured model; store and return its diagnosis (or the failure, also stored)."""
    import bt_profiles

    config = config or settings()
    pid, model, effort = config["profile"], config["model"], config["effort"]
    started = time.time()
    _write(rdir, request["id"], {"state": "running", "started": started, "model": model, "profile": pid})
    try:
        spec = bt_profiles.get(pid)
        provider = spec["provider"]
        bt_profiles.authorize(pid, project)
        env = bt_profiles.session_env(pid, provider, None, project)
        options = ", ".join(o["id"] for o in request.get("options", []))
        prompt = PROMPT.format(kinds=", ".join(rules.KINDS), options=options, bundle=evidence)
        with tempfile.TemporaryDirectory(prefix="bt-diagnosis-") as work:
            out = Path(work) / "answer.txt"
            done = runner(argv(provider, spec.get("bin") or provider, model, effort, out), input=prompt, text=True,
                          capture_output=True, cwd=work, env=env, timeout=int(config["timeout_seconds"]))
            text = out.read_text(encoding="utf-8") if out.is_file() else (done.stdout or "")
        if done.returncode:
            raise ValueError(f"{provider} salió con {done.returncode}: {(done.stderr or done.stdout or '')[-300:]}")
        result = {"state": "done", **parse(text, request)}
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired, SystemExit) as exc:
        result = {"state": "failed", "error": str(exc)[:400]}
    result.update({"source": f"agente · {model}", "model": model, "profile": pid, "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "seconds": round(time.time() - started, 1)})
    _write(rdir, request["id"], result)
    return result


def spawn(project: str, req: str, rdir: Path, request_id: str) -> bool:
    """Start a background diagnosis of one request unless one is stored or running. True when started."""
    now = cached(rdir, request_id)
    if now and now.get("state") in ("done", "running"):
        return False
    _write(rdir, request_id, {"state": "running", "started": time.time()})
    script = Path(__file__).resolve().parent / "bitacora.py"
    try:
        subprocess.Popen([sys.executable, str(script), "--project", project, "scheduler-op", req, "diagnose", request_id],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
    except OSError:
        path(rdir, request_id).unlink(missing_ok=True)
        return False
    return True


def forget(rdir: Path, request_id: str) -> None:
    """Drop the stored answer so the next ask runs the agent again."""
    path(rdir, request_id).unlink(missing_ok=True)
