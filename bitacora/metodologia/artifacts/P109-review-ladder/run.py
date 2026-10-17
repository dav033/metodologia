"""Reproduce the owner-authorized, synthetic, three-provider review comparison.

No production edits. Prompts exclude the predeclared oracle; raw CLI streams and
private reasoning are never persisted. Each invocation has a bounded deadline.
"""
from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent
SCRIPTS = Path.home() / "dev/metodologia/skill/scripts"
sys.path.insert(0, str(SCRIPTS))
import bt_agy
import bt_profiles
import bt_quota_live

ROUTES = [("codex-2", "codex", "gpt-6.1-sol"),
          ("claude-work", "claude", "sonnet"),
          ("antigravity", "antigravity", "gemini-3.8-flash-high")]
INSTRUCTION = """Review the supplied implementation PLAN against its REQUIREMENTS and stated baseline.
This is a self-contained review: do not call tools, browse, inspect local files, or execute code.
All needed facts are in the input. Baseline guarantees explicitly stated as correct may be trusted.
Find actionable correctness, security, dependency or verification defects. Do not invent missing requirements,
restate valid baseline protections as defects, or report style preferences. Deduplicate root causes.
Return ONLY JSON, no markdown fence, at most 8 findings and 900 words:
{"verdict":"acceptable|needs_changes","findings":[{"task":"Tn","severity":"critical|high|medium|low",
"issue":"precise defect","evidence":"exact supplied fact","failure_scenario":"concrete consequence",
"fix":"minimal correction"}],"uncertainties":["only if material facts are missing"]}.
Use English for the JSON content. A plan with a material defect must be needs_changes.

INPUT:\n"""


def save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def quota(profile, provider):
    if provider != "antigravity":
        return bt_quota_live.read_row(profile, provider, timeout=20)
    try:
        windows = bt_agy.read_usage(timeout=30)
        return {"profile": profile, "status": "ok", "observed_at": time.time(), "windows": windows}
    except Exception as exc:
        return {"profile": profile, "status": type(exc).__name__, "observed_at": time.time(), "windows": {}}


def numeric_fields(value):
    if not isinstance(value, dict):
        return {}
    return {k: (numeric_fields(v) if isinstance(v, dict) else v)
            for k, v in value.items() if isinstance(v, (int, float, dict)) and not isinstance(v, bool)}


def extract(provider, stdout):
    events = []
    for line in stdout.splitlines():
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if isinstance(obj, dict):
            events.append(obj)
    response, usage, observed_models, tool_events = "", {}, set(), 0
    for e in events:
        if provider == "codex":
            if e.get("type") == "turn.completed":
                usage = numeric_fields(e.get("usage"))
            item = e.get("item", {})
            if isinstance(item, dict) and e.get("type") == "item.completed":
                if item.get("type") == "agent_message":
                    response = item.get("text", "")
                elif item.get("type") in ("command_execution", "mcp_tool_call", "web_search"):
                    tool_events += 1
        elif provider == "claude":
            if e.get("type") == "result":
                response = e.get("result", "")
                usage = numeric_fields(e.get("usage"))
            message = e.get("message", {})
            if isinstance(message, dict):
                if isinstance(message.get("model"), str):
                    observed_models.add(message["model"])
                tool_events += sum(b.get("type") == "tool_use" for b in message.get("content", []) if isinstance(b, dict))
        elif provider == "antigravity":
            if e.get("event") == "result":
                result = e.get("result", {})
                response = result.get("response", "")
                usage = numeric_fields(result.get("usage"))
                for key in ("model", "modelId", "model_id"):
                    if isinstance(result.get(key), str):
                        observed_models.add(result[key])
            if e.get("event") in ("tool_call", "tool_use", "tool_execution"):
                tool_events += 1
            for key in ("model", "modelId", "model_id"):
                if isinstance(e.get(key), str):
                    observed_models.add(e[key])
    clean = response.strip()
    if clean.startswith("```"):
        clean = "\n".join(clean.splitlines()[1:-1])
    try:
        answer = json.loads(clean)
        valid = isinstance(answer, dict) and answer.get("verdict") in ("acceptable", "needs_changes") and isinstance(answer.get("findings"), list) and len(answer["findings"]) <= 8
        for finding in answer.get("findings", []):
            valid = valid and isinstance(finding, dict) and all(isinstance(finding.get(k), str) for k in ("task", "severity", "issue", "evidence", "failure_scenario", "fix"))
    except (ValueError, AttributeError):
        answer, valid = None, False
    return {"answer": answer, "response_text": response, "format_valid": bool(valid),
            "usage_reported": usage, "observed_models": sorted(observed_models), "observed_tool_events": tool_events}


def run_one(case, route, effort="high", variant=None):
    profile, provider, model = route
    variant = variant or profile
    path = ROOT / f"{case['id']}-{variant}.json"
    if path.exists():
        print(f"SKIP existing {path.name}", flush=True)
        return
    prompt = INSTRUCTION + case["input"]
    before = quota(profile, provider)
    if any(w.get("used_percent", 0) >= 100 for name, w in before.get("windows", {}).items()
           if name in ("five_hour", "seven_day")):
        save(path, {"status": "quota_exhausted", "before": before})
        print(f"BLOCKED {case['id']} {profile} quota", flush=True)
        return
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDECODE", "CLAUDE_CONFIG_DIR", "CODEX_HOME")}
    env.update(bt_profiles.env_of(profile))
    if provider == "codex":
        args = ["codex", "exec", "--ignore-user-config", "--ignore-rules", "--ephemeral", "--skip-git-repo-check",
                "--sandbox", "read-only", "--model", model, "-c", f'model_reasoning_effort="{effort}"', "--json", "-"]
        stdin = prompt
    elif provider == "claude":
        args = ["claude", "--print", "--model", model, "--effort", effort, "--safe-mode", "--restricted",
                "--tools", "", "--no-session-persistence", "--permission-mode", "plan", "--output-format", "stream-json", "--verbose"]
        stdin = prompt
    else:
        args = ["agy", "--model", model, "--mode", "plan", "--disable-slash-commands", "--output-format", "stream-json",
                "--print-timeout", "300s", "--print=" + prompt]
        stdin = None
    record = {"case": case["id"], "profile": profile, "provider": provider, "requested_model": model,
              "requested_effort": effort, "variant": variant, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
              "prompt_characters": len(prompt), "quota_before": before, "started_at": time.time()}
    print(f"START {case['id']} {profile}", flush=True)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="p109-review-ladder-") as cwd:
        try:
            proc = subprocess.run(args, input=stdin, text=True, capture_output=True, cwd=cwd, env=env, timeout=330)
            record.update(extract(provider, proc.stdout))
            record.update(exit_code=proc.returncode, status="completed" if proc.returncode == 0 else "cli_error")
            if proc.returncode != 0:
                record["error_excerpt"] = proc.stderr[-1200:]
        except subprocess.TimeoutExpired:
            record.update(status="timeout", exit_code=None)
    record["elapsed_seconds"] = round(time.monotonic() - started, 3)
    record["quota_after"] = quota(profile, provider)
    save(path, record)
    print(f"DONE {case['id']} {profile} {record['status']} {record['elapsed_seconds']}s format={record.get('format_valid')} usage={record.get('usage_reported')}", flush=True)


if __name__ == "__main__":
    cases = json.loads((ROOT / "cases.json").read_text())
    save(ROOT / "protocol.json", {"schema_version": 1, "scope": "synthetic reviewer pilot, outside REQ-024 formal benchmark",
         "cases": len(cases), "planned_calls": 15, "findings_limit": 8, "word_limit": 900,
         "oracle_sha256": hashlib.sha256((ROOT / "cases.json").read_bytes()).hexdigest(),
         "instruction": INSTRUCTION, "routes": ROUTES, "repetitions": 1,
         "score_rule": "Manually map each finding to predeclared defects, deduplicate; report recall, false positives, precision and F1. Any extra supported issue is adjudicated separately, never automatically called false positive.",
         "limitations": ["One run per cell; no statistical superiority claim", "Synthetic plan reviews, no repository exploration or code execution", "Provider contexts/tokenizers differ", "Quota is coarse account-level telemetry and may lag or include concurrent account use"]})
    for case in cases:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(lambda route: run_one(case, route), ROUTES))
        print(f"CASE COMPLETE {case['id']}", flush=True)
