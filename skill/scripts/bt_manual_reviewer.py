"""The manual reviewer (P-165): a model judges the manual criteria that are written as prose, from evidence the ENGINE gathers.

A plan may declare a manual check such as «inspect gh repository visibility and the pushed commit» or «review docs/consumption.md». The
verifier's sandbox has no network identity and runs only commands, and the coordinator runs only commands the plan spells out, so such a
task waited for a person even when every command check passed and the fact was one `gh` call away (david-ui REQ-001 T1: 15 minutes).

1. the model, which has no tools, lists the read-only commands that would show whether the criterion holds;
2. THE ENGINE vets each one against an allowlist (no shell, no writes, no network mutation) and runs it: `git`/`gh` in the task's
   repository, file readers in the snapshot of the attempt being verified; everything printed is redacted of the repository's env values;
3. the model judges the outputs: `pass` is attested (the same receipt a person would leave, `by=manual-reviewer-auto`), `fail` goes to
   the attempt's verification note where the agent and the healing read it, `unsure` — a phone, a look at the product, too little
   evidence — stays for a person.
It never changes a plan, never answers a decision, and every verdict is recorded as an intervention. Config: `reviewer.auto` (default on).
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

STATE = "RUN.reviewer.json"
MAX_COMMANDS = 8
OUTPUT_CHARS = 3000
TIMEOUT = 60
FILE_TOOLS = {"ls", "cat", "head", "tail", "wc", "grep", "stat", "test", "diff"}
GIT_SUBCOMMANDS = {"log", "show", "status", "diff", "ls-remote", "ls-files", "rev-parse", "branch", "remote", "cat-file", "rev-list",
                   "describe", "tag", "config"}
GH_GROUPS = {"repo": {"view", "list"}, "pr": {"view", "list", "checks", "diff", "status"}, "run": {"view", "list"},
             "release": {"view", "list"}, "issue": {"view", "list"}, "api": None}
WRITING_FLAGS = {"-X", "--method", "-f", "-F", "--field", "--raw-field", "--input", "-d", "--delete", "--edit", "-i"}
LIST_FLAGS = {"-a", "-r", "-l", "--list", "-v", "-vv", "--show-current", "--all", "--remotes"}
UNSAFE_GIT_FLAGS = {"--output", "-o", "--exec-path", "--upload-pack", "-c", "--ext-diff", "--textconv"}

PLAN_PROMPT = """You review a manual acceptance criterion of a software task. You have no tools: say which READ-ONLY commands would show
whether it holds, and the engine will run them. Allowed: `git` (log, show, status, diff, ls-remote, ls-files, rev-parse, branch, remote,
cat-file, rev-list), `gh` (repo view, pr view, run view, release view, api GET only), and file readers (ls, cat, head, tail, wc, grep, stat,
test, diff) on relative paths of the task's snapshot or absolute paths under the listed roots. One command per item, no pipes, no shell
syntax, at most {limit}. If the criterion needs a human body or eyes (a phone, how a screen looks or feels) answer with an empty list.
Answer with ONE JSON object: {{"commands": ["..."], "why": "one sentence"}}

TASK: {task}
CRITERION (manual check): {purpose}
HOW TO CHECK: {value}
EXPECTED: {expected}
REPOSITORY (cwd of git/gh): {repository}
ROOTS you may read by absolute path: {roots}
"""

JUDGE_PROMPT = """You review a manual acceptance criterion of a software task from command outputs the engine collected. Judge ONLY from them.
`pass` needs outputs that prove every part of the criterion; anything missing, ambiguous, failed to run, or needing a human body or eyes
is `unsure`; `fail` needs outputs that show it does NOT hold. Answer with ONE JSON object and nothing else:
{{"verdict": "pass"|"fail"|"unsure", "confidence": "alta"|"media"|"baja", "evidence": "at most 5 sentences quoting the outputs that decide"}}

TASK: {task}
CRITERION: {purpose}
EXPECTED: {expected}

COMMANDS AND OUTPUTS:
{outputs}
"""


def enabled() -> bool:
    try:
        import bt_config

        return bt_config.get("reviewer.auto", True) is True
    except Exception:  # noqa: BLE001 - without a readable config the reviewer stays off
        return False


# ------------------------------------------------------------------------------------------------------------ vetting
def _inside(value: str, roots: list[Path], cwd: Path) -> bool:
    if value.startswith("-"):
        return True
    path = Path(value)
    resolved = (path if path.is_absolute() else cwd / path).resolve()
    return any(resolved == root or root in resolved.parents for root in roots)


def vet(command: str, roots: list[Path], snapshot: Path, repository: Path) -> tuple[list[str], Path] | None:
    """(argv, cwd) when `command` is one the reviewer may run, else None. No shell: the text is split, never interpreted."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None
    if not tokens or any(ch in command for ch in "|;&`$<>\n") or len(tokens) > 40:
        return None
    tool, rest = tokens[0], tokens[1:]
    if tool in FILE_TOOLS:
        if not all(_inside(t, roots, snapshot) for t in rest if not t.startswith("-")):
            return None
        return tokens, snapshot
    if tool == "git":
        sub = rest[0] if rest else ""
        if sub not in GIT_SUBCOMMANDS or any(t in UNSAFE_GIT_FLAGS or t.startswith("--output") for t in rest):
            return None
        if sub in ("branch", "tag") and not all(t in LIST_FLAGS for t in rest[1:]):
            return None
        if sub == "remote" and rest[1:] not in ([], ["-v"]) and not (len(rest) == 3 and rest[1] in ("show", "get-url")):
            return None
        if sub == "config" and not (len(rest) >= 2 and rest[1] in ("--get", "--list", "-l")):
            return None
        return tokens, repository
    if tool == "gh":
        if len(rest) < 2 or rest[0] not in GH_GROUPS or any(t in WRITING_FLAGS for t in rest):
            return None
        allowed = GH_GROUPS[rest[0]]
        if allowed is not None and rest[1] not in allowed:
            return None
        if rest[0] == "api" and any(t.upper() in ("POST", "PUT", "PATCH", "DELETE") for t in rest):
            return None
        return tokens, repository
    return None


# ------------------------------------------------------------------------------------------------------------ running
def run_command(argv: list[str], cwd: Path, secrets: list[str]) -> dict[str, Any]:
    try:
        done = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True, timeout=TIMEOUT, stdin=subprocess.DEVNULL,
                              env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GH_PROMPT_DISABLED": "1", "GIT_OPTIONAL_LOCKS": "0"})
        text, code = (done.stdout or "") + (done.stderr or ""), done.returncode
    except (OSError, subprocess.SubprocessError) as error:
        text, code = f"{type(error).__name__}: {error}", -1
    for secret in secrets:
        text = text.replace(secret, "[redacted]")
    return {"exit_code": code, "output": text[-OUTPUT_CHARS:]}


def _env_secrets(repository: Path) -> list[str]:
    import bt_coordinator

    env_file = repository / ".env.local"
    return bt_coordinator.env_secrets(env_file) if env_file.is_file() else []


def _extract(repository: Path, snapshot: str, work: Path) -> None:
    archive = subprocess.run(["git", "-C", str(repository), "archive", snapshot], capture_output=True, timeout=120, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(work)], input=archive, capture_output=True, timeout=120, check=True)


# ------------------------------------------------------------------------------------------------------------ the model
def ask(project: str, prompt: str, *, runner: Callable[..., Any] = subprocess.run, config: dict | None = None) -> str:
    """One model call through the diagnosis profile (no tools): the text it answers."""
    import bt_block_agent
    import bt_profiles

    config = config or bt_block_agent.settings()
    pid, model, effort = config["profile"], config["model"], config["effort"]
    spec = bt_profiles.get(pid)
    provider = spec["provider"]
    bt_profiles.authorize(pid, project)
    env = bt_profiles.session_env(pid, provider, None, project)
    with tempfile.TemporaryDirectory(prefix="bt-reviewer-") as work:
        out = Path(work) / "answer.txt"
        done = runner(bt_block_agent.argv(provider, spec.get("bin") or provider, model, effort, out), input=prompt, text=True,
                      capture_output=True, cwd=work, env=env, timeout=int(config["timeout_seconds"]))
        text = out.read_text(encoding="utf-8") if out.is_file() else (done.stdout or "")
    if done.returncode:
        raise ValueError(f"{provider} exited with {done.returncode}: {(done.stderr or done.stdout or '')[-300:]}")
    return text


def _json(text: str) -> dict[str, Any]:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("the answer has no JSON")
    data = json.loads(text[start:end + 1])
    if not isinstance(data, dict):
        raise ValueError("the answer is not an object")
    return data


def judge(task: str, check: dict, results: list[dict], ask_model: Callable[[str], str]) -> dict[str, Any]:
    outputs = "\n\n".join(f"$ {r['command']}\n(exit {r['exit_code']})\n{r['output']}" for r in results) or "(no command could be run)"
    data = _json(ask_model(JUDGE_PROMPT.format(task=task, purpose=check["purpose"], expected=check["expected"], outputs=outputs)))
    verdict = data.get("verdict") if data.get("verdict") in ("pass", "fail", "unsure") else "unsure"
    confidence = data.get("confidence") if data.get("confidence") in ("alta", "media", "baja") else "baja"
    if verdict != "unsure" and confidence == "baja":
        verdict = "unsure"                          # a verdict the reviewer itself doubts is not a verdict
    return {"verdict": verdict, "confidence": confidence, "evidence": str(data.get("evidence") or "").strip()[:900]}


# ------------------------------------------------------------------------------------------------------------ the task
def review_task(project: str, req: str, rdir: Path, task: str, *, ask_model: Callable[[str], str] | None = None,
                run: Callable[..., dict] = run_command) -> list[str]:
    """Judge every manual check of `task` for the attempt its verifier waits on. Lines for the log."""
    import bt_attestation
    import bt_interventions
    import bt_recovery_export as export
    import bt_scheduler_decisions as decisions
    import bt_scheduler_ops as ops

    plan = ops.bound_plan(rdir)
    checks = bt_attestation.manual_checks(plan, task)
    if not checks:
        return [f"{task} has no manual check"]
    attempts = ops.review_attempts(rdir, task)
    if len(attempts) != 1:
        return [f"{task}: no single verification is waiting for evidence ({len(attempts)} found)"]
    attempt = attempts[0]
    body = json.loads(export._manifest_path(rdir, attempt).read_text(encoding="utf-8"))
    repository, snapshot_sha = Path(str(body.get("repository"))), str(body.get("snapshot_sha"))
    ask_model = ask_model or (lambda prompt: ask(project, prompt))
    home = Path.home()
    lines: list[str] = []
    with tempfile.TemporaryDirectory(prefix="review-", dir=home / ".cache") as directory:
        work = Path(directory)
        _extract(repository, snapshot_sha, work)
        roots = [work.resolve(), repository.resolve(), (home / "dev" / "cerebro").resolve(), (home / "bitacora" / project).resolve()]
        secrets = _env_secrets(repository)
        for number, check in enumerate(checks, 1):
            asked = _json(ask_model(PLAN_PROMPT.format(
                limit=MAX_COMMANDS, task=task, purpose=check["purpose"], value=check["value"], expected=check["expected"],
                repository=repository, roots=", ".join(str(r) for r in roots[1:]))))
            results: list[dict] = []
            for command in [str(c) for c in asked.get("commands") or []][:MAX_COMMANDS]:
                vetted = vet(command, roots, work, repository)
                if vetted is None:
                    results.append({"command": command, "exit_code": -2, "output": "refused: not a read-only command the reviewer may run"})
                    continue
                results.append({"command": command, **run(vetted[0], vetted[1], secrets)})
            if not any(r["exit_code"] == 0 for r in results):
                lines.append(f"{task}: «{check['purpose'][:70]}» has no evidence the reviewer can gather: it stays for its owner")
                continue
            verdict = judge(task, check, results, ask_model)
            stamp = f"{project}-{req}"
            evidence = f"{verdict['evidence']} [reviewer: {len(results)} command(s) on {attempt}, confidence {verdict['confidence']}]"
            if verdict["verdict"] == "pass":
                lines += ops.attest(project, req, rdir, task, str(number), evidence, by="manual-reviewer-auto")
                bt_interventions.record(rdir, kind="criterion_unmapped", source="auto", task=task, evidence=evidence[:600],
                                        repair=f"the manual reviewer attested check {number} of {attempt}", result="fixed", run=stamp)
            elif verdict["verdict"] == "fail":
                decisions.write_verify_notes(rdir, task, f"The manual reviewer checked «{check['purpose']}» and it does NOT hold:\n\n"
                                             + verdict["evidence"] + "\n\n" + "\n".join(f"$ {r['command']}\n{r['output'][-400:]}" for r in results))
                bt_interventions.record(rdir, kind="regression", source="auto", task=task, evidence=evidence[:600],
                                        repair="none: the criterion does not hold, the note carries it", result="failed", run=stamp)
                lines.append(f"{task}@{attempt}: «{check['purpose'][:70]}» does not hold; the note carries it")
            else:
                lines.append(f"{task}@{attempt}: the reviewer is unsure about «{check['purpose'][:70]}»: it stays for its owner")
    return lines


def cycle(project: str, req: str, rdir: Path, *, log: Callable[[str], None] = lambda text: None,
          ask_model: Callable[[str], str] | None = None, run: Callable[..., dict] = run_command) -> bool:
    """The watcher's turn: every open REVIEW whose manual evidence nothing else supplied gets ONE reviewer pass. True when a review was
    attested (the owner is then resumed)."""
    if not enabled():
        return False
    import bt_scheduler_decisions as decisions
    import bt_scheduler_ops as ops

    path = Path(rdir) / STATE
    try:
        done = list(json.loads(path.read_text(encoding="utf-8")).get("done", []))
    except (OSError, ValueError):
        done = []
    try:
        requests = decisions.open_requests(rdir)
    except Exception:  # noqa: BLE001 - a run without readable state has nothing to review
        return False
    attested = False
    for request in requests:
        key = str(request.get("id"))
        if request.get("source") != "review" or key in done or ops.on_hold(rdir):
            continue
        done.append(key)
        path.write_text(json.dumps({"done": done[-200:], "at": time.time()}), encoding="utf-8")   # before running: a crash never repeats a pass
        try:
            lines = review_task(project, req, rdir, request["task"], ask_model=ask_model, run=run)
        except Exception as error:  # noqa: BLE001 - an extra: its failure leaves the review for a person
            log(f"reviewer {request['task']}: {type(error).__name__}: {str(error)[:200]}")
            continue
        for line in lines:
            log(f"reviewer: {line}")
        if any(line.startswith("attested ") for line in lines):
            attested = True
            try:
                ops.resume(project, req, rdir)
            except Exception:  # noqa: BLE001 - the watcher restarts the owner anyway
                pass
    return attested
