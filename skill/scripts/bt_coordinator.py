"""The coordinator step: run the live commands a plan leaves to "the coordinator", and attest them (P-157).

A plan may declare a manual check as «Coordinator runs `npx tsx … --live` with .env.local». The verifier cannot run it (its sandbox has no
credentials and no network identity), so the task waits in review for a person to run it and `scheduler-op REQ attest`. When the owner has
AUTHORIZED a project (`coordinator.projects`), this module is that person:

1. only when every manual check of the task is such a runnable command (a phone, a review of the product or any other human step is not,
   and the task then stays for its owner) and the verifier's only doubt is manual evidence (an open review it can requeue);
2. it runs the commands on the SNAPSHOT of the attempt being verified (`git archive`, no `.git`), with that project's `.env.local` copied
   in and its `node_modules` linked, so the evidence is about the work that is verified, not about whatever the checkout holds today;
3. everything printed is redacted of every value of that env file before it is kept anywhere;
4. exit code 0 for all of them: one attestation, bound to the attempt (`bt_attestation`), then the review is requeued; otherwise nothing is
   attested and what failed goes to the attempt's verification note, where the agent and the self-healing read it (a real defect is then a
   repair task like any other).

It never touches a project the owner did not name, and it records every run as an intervention.
"""
from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
import json
from typing import Any, Callable

SNIPPET = re.compile(r"`([^`]+)`")
RUNNERS = ("npx", "npm", "node", "tsx", "pnpm", "yarn", "python3", "python")
MIN_SECRET = 6
TAIL_LINES = 14


def authorized(project: str) -> bool:
    import bt_config

    projects = bt_config.get("coordinator.projects", [])
    return isinstance(projects, list) and project in projects


def commands_of(value: str) -> list[str]:
    """The commands inside the backticks of a manual check. A later snippet that starts with `--` is the SAME command with that flag
    changed («`… --milestone M1` and then `--milestone M2`»)."""
    out: list[str] = []
    for snippet in SNIPPET.findall(value or ""):
        snippet = snippet.strip()
        try:
            tokens = shlex.split(snippet)
        except ValueError:
            continue
        if not tokens:
            continue
        if tokens[0].startswith("--") and out:
            base = shlex.split(out[0])
            if tokens[0] in base:
                at = base.index(tokens[0])
                out.append(shlex.join(base[:at] + tokens + base[at + len(tokens):]))
            else:
                out.append(shlex.join(base + tokens))
        elif Path(tokens[0]).name in RUNNERS:
            out.append(shlex.join(tokens))
    return out


def env_secrets(env_file: Path) -> list[str]:
    """Every value of an env file long enough to be a secret (they are removed from anything the coordinator keeps)."""
    secrets: list[str] = []
    try:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            value = line.split("=", 1)[1].strip().strip("'\"")
            if len(value) >= MIN_SECRET:
                secrets.append(value)
    except OSError:
        pass
    return sorted(set(secrets), key=len, reverse=True)


def redact(text: str, secrets: list[str]) -> str:
    for secret in secrets:
        text = text.replace(secret, "***")
    return text


def prepare(repository: Path, snapshot: str, work: Path, env_file: Path) -> Path:
    """The attempt's snapshot as a plain tree with the project's env file and node_modules (nothing of the checkout is touched)."""
    root = work / "tree"
    root.mkdir()
    archive = subprocess.run(["git", "-C", str(repository), "archive", "--format=tar", snapshot], capture_output=True, timeout=300, check=False)
    if archive.returncode:
        raise RuntimeError(f"git archive {snapshot[:12]}: {archive.stderr.decode('utf-8', 'replace')[:160]}")
    unpacked = subprocess.run(["tar", "-x", "-C", str(root)], input=archive.stdout, capture_output=True, timeout=300, check=False)
    if unpacked.returncode:
        raise RuntimeError(f"tar: {unpacked.stderr.decode('utf-8', 'replace')[:160]}")
    shutil.copyfile(env_file, root / ".env.local")
    os.chmod(root / ".env.local", 0o600)
    modules = repository / "node_modules"
    if modules.is_dir() and not (root / "node_modules").exists():
        (root / "node_modules").symlink_to(modules)
    return root


def run_one(command: str, root: Path, timeout: int, secrets: list[str]) -> dict[str, Any]:
    started = time.monotonic()
    try:
        done = subprocess.run(shlex.split(command), cwd=root, capture_output=True, text=True, timeout=timeout, check=False,
                              env={**os.environ, "CI": "1"})
        code, text = done.returncode, (done.stdout or "") + (done.stderr or "")
    except subprocess.TimeoutExpired as error:
        code, text = -1, f"timed out after {timeout} s\n" + str(error.stdout or "")[-2000:]
    except OSError as error:
        code, text = -2, f"could not start: {error}"
    lines = [line for line in redact(text, secrets).splitlines() if line.strip()]
    return {"command": command, "exit_code": code, "seconds": round(time.monotonic() - started, 1), "tail": lines[-TAIL_LINES:]}


def _evidence(attempt: str, snapshot: str, results: list[dict]) -> str:
    parts = [f"Coordinator ran {len(results)} live command(s) on the snapshot {snapshot[:12]} of {attempt} with the project's .env.local "
             "(values redacted):"]
    for result in results:
        parts.append(f"`{result['command'][:160]}` exit {result['exit_code']} in {result['seconds']} s; last lines: "
                     + " | ".join(line[:120] for line in result["tail"][-4:]))
    return "\n".join(parts)[:3800]


def attest_task(project: str, req: str, rdir: Path, task: str, *, runner: Callable[..., dict] | None = None,
                timeout: int | None = None) -> list[str]:
    """Run the manual live checks of `task` for the attempt its verifier is waiting on, and attest them when they all pass."""
    import bt_attestation
    import bt_config
    import bt_interventions
    import bt_recovery_export as export
    import bt_run_stores
    import bt_scheduler_decisions as decisions
    import bt_scheduler_ops as ops
    from bt_scheduler_quality.store import QualityStore

    if not authorized(project):
        raise ops.core.SchedulerError("NOT_ALLOWED", f"the owner has not authorized the coordinator for {project} (config coordinator.projects)")
    plan = ops.bound_plan(rdir)
    checks = bt_attestation.manual_checks(plan, task)
    commands: list[str] = []
    for check in checks:
        found = commands_of(check["value"])
        if not found:
            return [f"{task}: «{check['purpose'][:70]}» is not a command the coordinator can run: it stays for its owner"]
        commands += [c for c in found if c not in commands]
    if not commands:
        return [f"{task} has no manual check"]
    store = QualityStore(bt_run_stores.paths(rdir)["m6"])
    try:
        attempts = store.open_review_attempts(task)
    finally:
        store.close()
    if len(attempts) != 1:
        return [f"{task}: no single verification is waiting for evidence ({len(attempts)} found)"]
    attempt = attempts[0]
    manifest = export._manifest_path(rdir, attempt)
    body = json.loads(manifest.read_text(encoding="utf-8"))
    repository, snapshot = Path(str(body.get("repository"))), str(body.get("snapshot_sha"))
    env_file = repository / ".env.local"
    if not env_file.is_file():
        return [f"{task}: {env_file} does not exist: the coordinator has no credentials to run with"]
    secrets = env_secrets(env_file)
    limit = timeout or int(bt_config.get("coordinator.command_seconds", 1800))
    run = runner or run_one
    results: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="bt-coordinator-") as work:
        root = prepare(repository, snapshot, Path(work), env_file)
        for command in commands:
            result = run(command, root, limit, secrets)
            results.append(result)
            if result["exit_code"] != 0:
                break                                           # nothing is attested over a failure: the next ones prove nothing
    stamp = f"{project}-{req}"
    if all(r["exit_code"] == 0 for r in results) and len(results) == len(commands):
        evidence = _evidence(attempt, snapshot, results)
        lines = ops.attest(project, req, rdir, task, "", evidence, by="coordinator-auto")
        bt_interventions.record(rdir, kind="criterion_unmapped", source="auto", task=task, evidence=f"manual live checks of {attempt}",
                                repair=f"the coordinator ran {len(results)} command(s) and attested them", result="fixed", run=stamp)
        return [f"{task}@{attempt}: {len(results)} live command(s) passed", *lines]
    failed = next(r for r in results if r["exit_code"] != 0)
    decisions.write_verify_notes(rdir, task, "The coordinator ran the live check and it FAILED, so nothing was attested:\n\n$ "
                                 f"{failed['command']}\nexit code {failed['exit_code']}\n" + "\n".join(failed["tail"]))
    bt_interventions.record(rdir, kind="regression", source="auto", task=task, evidence=_evidence(attempt, snapshot, results)[:600],
                            repair="none: the live check failed, the note carries it", result="failed", run=stamp)
    return [f"{task}@{attempt}: `{failed['command'][:100]}` exited {failed['exit_code']}; not attested, the failure is in the verification note"]


STATE = "RUN.coordinator.json"


def cycle(project: str, req: str, rdir: Path, *, log: Callable[[str], None] = lambda text: None,
          runner: Callable[..., dict] | None = None) -> bool:
    """The watchdog's turn: every open REVIEW of an authorized project gets ONE coordinator attempt (a failed run is not retried over the same
    verification: its note feeds the next attempt). True when a live run happened."""
    if not authorized(project):
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
    except Exception:  # noqa: BLE001 - a run without readable state has nothing to coordinate
        return False
    ran = False
    for request in requests:
        key = str(request.get("id"))
        if request.get("source") != "review" or key in done or ops.on_hold(rdir):
            continue
        done.append(key)
        path.write_text(json.dumps({"done": done[-200:]}), encoding="utf-8")        # before running: a crash never repeats a live run
        try:
            lines = attest_task(project, req, rdir, request["task"], runner=runner)
        except Exception as error:  # noqa: BLE001 - the coordinator is an extra: its failure leaves the review for a person
            log(f"coordinator {request['task']}: {type(error).__name__}: {str(error)[:200]}")
            continue
        for line in lines:
            log(f"coordinator: {line}")
        ran = ran or any("live command" in line for line in lines)
        try:
            ops.resume(project, req, rdir)
        except Exception:  # noqa: BLE001 - the watcher restarts the owner anyway
            pass
    return ran
