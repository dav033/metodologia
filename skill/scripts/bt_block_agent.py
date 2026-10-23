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
from bt_prompt_context import compact, instruction

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


CONCISE_PROMPT = """Diagnose this stopped run from evidence only. Tell the owner what failed, its origin and the next action.
Guard codes are symptoms, not necessarily causes. Prefer a concrete rule-based diagnosis unless evidence contradicts it.
Preserve commands, paths, numbers, negations and decisive errors. Avoid repeated explanations.

""" + PROMPT[PROMPT.index("How the system works"):]


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
        prompt = instruction(PROMPT, CONCISE_PROMPT).format(kinds=", ".join(rules.KINDS), options=options, bundle=compact(evidence))
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


# --- recovery diagnosis: Planner-role, read-only, structured transport (REQ-029 T3) ------------------------------------
# Separate from the owner-card advice above: no `diagnosis.*` profile/model defaults, no fallback to card JSON. The
# transport returns UNTRUSTED bytes; only the M5 adapter parses `recovery-proposal/1`.

RECOVERY_DIR = "RECOVERY.diagnoses"        # lives in `store`, never in the target run
SECTION_BYTES = 32 * 1024
EVIDENCE_BYTES = 512 * 1024
RECOVERY_PROMPT = """You are the Planner role diagnosing why an automated run's task repeatedly failed audit.
You have NO tools and NO connectors: use only the evidence below. Do not run or suggest running anything on your own;
suggested commands are text for a later, separately authorized step. Do not answer any owner decision.
Reply with ONE JSON object and nothing else (schema recovery-proposal/1) covering: the causal history of the failure,
a check against the integrated tree (or state that integrated-tree evidence is unavailable), references to the evidence
sections you relied on, supported actions from retry, wait, block, rework_findings, ordered prerequisites, the expected
outcome, and falsifiable checks that would prove or refute your diagnosis.
Cite only evidence that is present; say so when the evidence cannot support a claim.

Request identity: {identity}

Evidence ({count} sections, in order):
{sections}
"""
ROUTE_KEYS = ("provider", "profile", "model", "authorized_by")


def _sections(evidence: dict) -> list[str] | None:
    """Full evidence as ordered bounded sections, or None when the bound cannot hold it (never truncated)."""
    blob = json.dumps(evidence, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    if len(blob.encode("utf-8")) > EVIDENCE_BYTES:
        return None
    pieces: list[str] = []
    piece: list[str] = []
    piece_bytes = 0
    for character in blob:
        char_bytes = len(character.encode("utf-8"))
        if piece and piece_bytes + char_bytes > SECTION_BYTES:
            pieces.append("".join(piece))
            piece = []
            piece_bytes = 0
        piece.append(character)
        piece_bytes += char_bytes
    pieces.append("".join(piece))
    return [f"## retained evidence [{n}/{len(pieces)}]\n{piece}" for n, piece in enumerate(pieces, 1)]


def _blocked(outcome: str, blocker: str, provenance: dict, raw: bytes = b"") -> dict:
    return {"outcome": outcome, "blocker": blocker, "raw": raw, "provenance": provenance}


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"invalid JSON constant: {value}")


def diagnose_recovery(project: str, evidence: dict, request_identity: dict, route: dict, *, store: Path,
                      timeout_seconds: int, runner=None, probe_runner=None, home: Path | None = None,
                      prompt: str | None = None) -> dict:
    """One persisted, read-only Planner diagnostic per cycle. Returns {outcome, blocker, raw, provenance}.

    `route` comes from the caller's M2 role policy: {role: "planner", verified: True, provider, profile, model,
    effort?, authorized_by}. outcome is "ok" (raw = untrusted model bytes that are at least valid JSON) or one of
    unauthorized_route, evidence_incomplete, unsupported_diagnostic_sandbox, unavailable, timeout, invalid_json,
    already_invoked. Nothing is retried and nothing is written outside `store`.
    """
    import bt_planner_runtime as runtime
    import bt_profiles

    cycle = hashlib.sha256(json.dumps(request_identity, sort_keys=True, default=str).encode()).hexdigest()[:24]
    target = Path(store) / RECOVERY_DIR / f"{cycle}.json"
    provenance = {"cycle": cycle, "request_identity": request_identity,
                  "evidence_sha256": evidence.get("evidence_sha256") if isinstance(evidence, dict) else None,
                  "route": {k: route.get(k) for k in (*ROUTE_KEYS, "role", "effort", "verified")} if isinstance(route, dict) else None,
                  "authorization_status": "pending"}

    def finish(result: dict) -> dict:
        record = {"outcome": result["outcome"], "blocker": result["blocker"], "provenance": provenance,
                  "raw_sha256": hashlib.sha256(result["raw"]).hexdigest(), "raw_bytes": len(result["raw"]),
                  "raw": result["raw"].decode("utf-8", "replace"), "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
        tmp = target.with_suffix(".tmp")
        try:
            tmp.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
            tmp.replace(target)
        except OSError as exc:
            return _blocked("unavailable", f"diagnostic result could not be persisted: {exc}"[:400], provenance,
                            result["raw"])
        return {**result, "provenance": provenance}

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8") as claim:
            claim.write(json.dumps({"outcome": "running", "provenance": provenance}, ensure_ascii=False))
    except FileExistsError:
        return _blocked("already_invoked", "this cycle already used its single diagnostic invocation", provenance)
    except OSError as exc:
        return _blocked("unavailable", f"could not reserve diagnostic cycle: {exc}"[:400], provenance)
    if (not isinstance(route, dict) or route.get("role") != "planner" or route.get("verified") is not True
            or any(not isinstance(route.get(k), str) or not route[k].strip() for k in ROUTE_KEYS)):
        provenance["authorization_status"] = "rejected"
        return finish(_blocked("unauthorized_route", "route is not a verified, authorized Planner-role route", provenance))
    if not isinstance(evidence, dict) or evidence.get("diagnosable") is not True or evidence.get("missing_sources"):
        return finish(_blocked("evidence_incomplete", "retained evidence is incomplete or not diagnosable", provenance))
    try:
        bt_profiles.authorize(route["profile"], project)
    except (bt_profiles.ProfileError, KeyError, ValueError) as exc:
        provenance["authorization_status"] = "rejected"
        return finish(_blocked("unauthorized_route", f"profile is not authorized for this project: {exc}"[:400], provenance))
    provenance["authorization_status"] = "authorized"
    try:
        sections = _sections(evidence)
    except (TypeError, ValueError, OverflowError):
        sections = None
    if sections is None:
        return finish(_blocked("evidence_incomplete", f"evidence exceeds {EVIDENCE_BYTES} bytes; not truncated", provenance))
    prompt = (prompt or RECOVERY_PROMPT).format(identity=json.dumps(request_identity, sort_keys=True, default=str),
                                                count=len(sections), sections="\n\n".join(sections))
    try:
        with tempfile.TemporaryDirectory(prefix="bt-recovery-diagnosis-") as work:
            result = runtime.invoke_diagnostic(
                runtime.PlannerRequest(project=project, provider=route["provider"], profile=route["profile"],
                                       model=route["model"], prompt=prompt, cwd=Path(work), effort=route.get("effort"),
                                       timeout_seconds=timeout_seconds),
                Path(work), runner=runner, probe_runner=probe_runner, home=home)
    except runtime.UnsupportedDiagnosticSandbox as exc:
        return finish(_blocked("unsupported_diagnostic_sandbox", str(exc)[:400], provenance))
    except runtime.PlannerRuntimeError as exc:
        text = str(exc)
        return finish(_blocked("timeout" if "timed out" in text else "unavailable", text[:400], provenance))
    if result.returncode:
        return finish(_blocked("unavailable", f"planner exited with status {result.returncode}: "
                                                f"{' '.join((result.stderr or '').split())[-240:]}", provenance))
    if len(result.stdout) > runtime.MAX_DIAGNOSTIC_OUTPUT_BYTES:
        return finish(_blocked("invalid_json", "diagnostic output exceeds the bound", provenance))
    try:
        parsed = json.loads(result.stdout.decode("utf-8"), parse_constant=_reject_json_constant)
        if not isinstance(parsed, dict):
            raise ValueError("not an object")
    except ValueError:
        return finish(_blocked("invalid_json", "diagnostic output is not a JSON object", provenance, result.stdout))
    return finish({"outcome": "ok", "blocker": None, "raw": result.stdout, "provenance": provenance})
