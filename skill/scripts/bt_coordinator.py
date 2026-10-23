"""The coordinator step: run the live commands a plan leaves to "the coordinator", and attest them (P-157).

A plan may declare a manual check as «Coordinator runs `npx tsx … --live` with .env.local». The verifier cannot run it (its sandbox has no
credentials and no network identity), so the task waits in review for a person to run it and `scheduler-op REQ attest`. When the owner has
AUTHORIZED a project (`coordinator.projects`), this module is that person:

1. only when every manual check of the task is such a runnable command (a phone, a review of the product or any other human step is not,
   and the task then stays for its owner) and the verifier's only doubt is manual evidence (an open review it can requeue);
2. it runs the commands on the SNAPSHOT of the attempt being verified (`git archive`, no `.git`), with that project's `.env.local` copied
   in and its `node_modules` hard-linked, so the evidence is about the work that is verified, not about whatever the checkout holds today;
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


def extra_files(project: str) -> dict[str, str]:
    """`coordinator.files.<project>`: {path inside the tree: file on this machine} for fixtures a live command needs and the repository
    does not carry (a recorded voice for the voice check). Relative destinations only: nothing is written outside the tree."""
    import bt_config

    configured = bt_config.get("coordinator.files", {})
    files = configured.get(project, {}) if isinstance(configured, dict) else {}
    return {str(dest): str(src) for dest, src in files.items()
            if isinstance(files, dict) and not Path(str(dest)).is_absolute() and ".." not in Path(str(dest)).parts}


def command_env(project: str, command: str) -> dict[str, str]:
    """`coordinator.env_files.<project>` = {"<text in the command>": [env files of this machine]}: the variables of those files go into the
    PROCESS environment of the commands that contain the text (a process variable wins over `.env.local` for dotenv and Next). REQ-020's
    deployed check (`--deployed`) needs the published origin and the passwords of the deployed services; the local live check keeps the
    checkout's own test credentials."""
    import bt_config

    configured = bt_config.get("coordinator.env_files", {})
    rules = configured.get(project, {}) if isinstance(configured, dict) else {}
    env: dict[str, str] = {}
    for needle, files in (rules.items() if isinstance(rules, dict) else ()):
        if needle in command and isinstance(files, list):
            for path in files:
                env.update(parse_env(Path(str(path)).expanduser()))
    return env


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                values[key.strip()] = value.strip().strip("'\"")
    except OSError:
        pass
    return values


def prepare(repository: Path, snapshot: str, work: Path, env_file: Path, files: dict[str, str] | None = None) -> Path:
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
    for dest, source in (files or {}).items():
        target = root / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    modules = repository / "node_modules"
    if modules.is_dir() and not (root / "node_modules").exists():
        # A hard-linked copy, not a symlink: Next/Turbopack refuses a node_modules that points out of the project root. The links share
        # the files with the checkout (no space, seconds); a different filesystem falls back to the symlink.
        linked = subprocess.run(["cp", "-al", str(modules), str(root / "node_modules")], capture_output=True, timeout=600, check=False)
        if linked.returncode:
            shutil.rmtree(root / "node_modules", ignore_errors=True)
            (root / "node_modules").symlink_to(modules)
    return root


def run_one(command: str, root: Path, timeout: int, secrets: list[str], extra_env: dict[str, str] | None = None) -> dict[str, Any]:
    started = time.monotonic()
    try:
        done = subprocess.run(shlex.split(command), cwd=root, capture_output=True, text=True, timeout=timeout, check=False,
                              env={**os.environ, "CI": "1", **(extra_env or {})})
        code, text = done.returncode, (done.stdout or "") + (done.stderr or "")
    except subprocess.TimeoutExpired as error:
        code, text = -1, f"timed out after {timeout} s\n" + str(error.stdout or "")[-2000:]
    except OSError as error:
        code, text = -2, f"could not start: {error}"
    lines = [line for line in redact(text, secrets).splitlines() if line.strip()]
    return {"command": command, "exit_code": code, "seconds": round(time.monotonic() - started, 1), "tail": lines[-TAIL_LINES:],
            "full": lines[-400:]}


def _keep_failure(rdir: Path, task: str, attempt: str, result: dict, number: int) -> None:
    """The failed run's output (already redacted) beside the task's notes: the verification note keeps only its last lines."""
    try:
        target = Path(rdir) / "RUN.notes" / f"{task}.live-{attempt}.{number}.log"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"$ {result['command']}\nexit code {result['exit_code']} after {result['seconds']} s\n" + "\n".join(result.get("full") or result["tail"]) + "\n",
                          encoding="utf-8")
    except OSError:
        pass


def _evidence(attempt: str, snapshot: str, results: list[dict]) -> str:
    parts = [f"Coordinator ran {len(results)} live command(s) on the snapshot {snapshot[:12]} of {attempt} with the project's .env.local "
             "(values redacted):"]
    for result in results:
        parts.append(f"`{result['command'][:160]}` exit {result['exit_code']} in {result['seconds']} s"
                     + (f" (run {result['run']} of {result['of']})" if result.get("run", 1) > 1 else "") + "; last lines: "
                     + " | ".join(line[:120] for line in result["tail"][-4:]))
    return "\n".join(parts)[:3800]


REVIEW_WAIT_TRIES = 12
REVIEW_WAIT_SECONDS = 15.0


def _review_attempts(ops, rdir: Path, task: str, sleep: Callable[[float], None] = time.sleep) -> tuple[str, ...]:
    """The attempts waiting for `task`'s evidence; while there are none, wait: a live run takes ~25 min and the owner can be restarting
    (an engine reload) just when it ends, which made REQ-020's T14a lose a whole run («no verification waiting for evidence»)."""
    attempts = ops.review_attempts(rdir, task)
    for _ in range(REVIEW_WAIT_TRIES):
        if attempts:
            break
        sleep(REVIEW_WAIT_SECONDS)
        attempts = ops.review_attempts(rdir, task)
    return attempts


def attest_task(project: str, req: str, rdir: Path, task: str, *, runner: Callable[..., dict] | None = None,
                timeout: int | None = None) -> list[str]:
    """Run the manual live checks of `task` for the attempt its verifier is waiting on, and attest them when they all pass."""
    import bt_attestation
    import bt_config
    import bt_interventions
    import bt_recovery_export as export
    import bt_scheduler_decisions as decisions
    import bt_scheduler_ops as ops

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
    attempts = _review_attempts(ops, rdir, task)
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
    for needle_files in (bt_config.get("coordinator.env_files", {}) or {}).get(project, {}).values():
        for extra in needle_files if isinstance(needle_files, list) else ():
            secrets += env_secrets(Path(str(extra)).expanduser())
    limit = timeout or int(bt_config.get("coordinator.command_seconds", 1800))
    run = runner or run_one
    scratch = Path.home() / ".cache" / "bt-coordinator"         # on the checkout's filesystem (not /tmp) so node_modules can be hard-linked
    scratch.mkdir(parents=True, exist_ok=True)
    tries = 1 + max(0, int(bt_config.get("coordinator.retries", 1) or 0))
    done: dict[str, dict] = {}                                  # a command shared by two checks runs once
    outcome: list[tuple[int, dict, list[dict]]] = []            # (1-based number of the check, the check, the results of its commands)
    with tempfile.TemporaryDirectory(prefix="run-", dir=scratch) as work:
        root = prepare(repository, snapshot, Path(work), env_file, extra_files(project))
        for number, check in enumerate(checks, 1):
            results: list[dict] = []
            for command in commands_of(check["value"]):
                if command not in done:
                    # A live check drives real services (a model, a database) and shares the machine with the scheduler's own gates: REQ-020's M2
                    # failed five times in the watcher and passed five times run by hand on the same snapshot. One more run costs minutes; the
                    # evidence keeps how many runs it took, and every failed run's full output is kept for the diagnosis.
                    for turn in range(1, tries + 1):
                        result = run(command, root, limit, secrets, command_env(project, command)) if runner is None \
                            else run(command, root, limit, secrets)
                        result["run"], result["of"] = turn, tries
                        if result["exit_code"] != 0:
                            _keep_failure(rdir, task, attempt, result, turn)
                        if result["exit_code"] == 0 or result["exit_code"] < 0:
                            break                               # passed, or could not run at all (a timeout is not retried)
                    done[command] = result
                results.append(done[command])
                if done[command]["exit_code"] != 0:
                    break                                       # the rest of THIS check proves nothing; the other checks still run
            outcome.append((number, check, results))
    stamp = f"{project}-{req}"
    lines: list[str] = []
    _review_attempts(ops, rdir, task)             # the owner may be restarting right now (an engine reload): attest once the review is visible
    passed = [(n, c, r) for n, c, r in outcome if r and all(x["exit_code"] == 0 for x in r) and len(r) == len(commands_of(c["value"]))]
    failed_checks = [(n, c, r) for n, c, r in outcome if (n, c, r) not in passed]
    for number, check, results in passed:
        evidence = _evidence(attempt, snapshot, results)
        # one receipt per check (its 1-based number): what passed stays attested when another check of the task cannot
        lines += ops.attest(project, req, rdir, task, str(number), evidence, by="coordinator-auto")
        bt_interventions.record(rdir, kind="criterion_unmapped", source="auto", task=task, evidence=f"manual live check {number} of {attempt}",
                                repair=f"the coordinator ran {len(results)} command(s) and attested check {number}", result="fixed", run=stamp)
    if not failed_checks:
        return [f"{task}@{attempt}: {sum(len(r) for _, _, r in passed)} live command(s) passed", *lines]
    every = [x for _, _, r in outcome for x in r]
    failed = next(x for _, _, r in failed_checks for x in r if x["exit_code"] != 0)
    left = ", ".join(str(n) for n, _, _ in failed_checks)
    decisions.write_verify_notes(rdir, task, "The coordinator ran the live check and it FAILED, so nothing was attested"
                                 + (f" for manual check {left}" if passed else "") + ":\n\n$ "
                                 f"{failed['command']}\nexit code {failed['exit_code']}\n" + "\n".join(failed["tail"]))
    bt_interventions.record(rdir, kind="regression", source="auto", task=task, evidence=_evidence(attempt, snapshot, every)[:600],
                            repair="none: the live check failed, the note carries it", result="failed", run=stamp)
    return [*lines, f"{task}@{attempt}: `{failed['command'][:100]}` exited {failed['exit_code']}; not attested "
            f"{'(manual check ' + left + ')' if passed else ''}, the failure is in the verification note"]


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
