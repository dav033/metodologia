"""Comparable benchmark of the two runtimes (REQ-030 item 10): one frozen plan, one agent process, one set of injected
failures, run once by the legacy Scheduler owner and once by the durable runtime.

What is identical on both sides: the plan bytes, the starting repository tree and its checks, the agent process (the fake
`claude` of the durable lab, `fake_providers/durable_agent.py`, launched through `bt_driver`'s real claude invocation and
read by its real parser), the M6 sandbox verifier and its policy, and the injected failures:

  T1 ok         plain task
  T2 fixlater   a real implementation failure, fixed by a retry that continues from its own snapshot
  T3 heap       the check fails like a Node build out of heap unless the verifier raises the heap (environment, not code)
  T4 quotaonce  the first launch hits the provider's usage limit (reset in 3 s)
  T5 ok         depends on T1
  T6 neverfix   never fixed: the runtime must stop and ask the owner within its budget

What differs is only the runtime: the legacy owner runs in process with its real M1/M3/M5/M6 stores (as in
`test_scheduler_owner_e2e_subplans`); the durable engine runs as its own process on DBOS (SQLite). The owner is a script:
when a runtime asks for a decision on T6 the answer is "stop" (the same answer on both sides), so both runs end.

  uv run python skill/scripts/tests/bench_runtimes.py run <out-dir>     # both runtimes, each in a fresh process
  uv run python skill/scripts/tests/bench_runtimes.py compare <out-dir> # the comparison table from the two JSON files

Observed numbers come only from the runtimes' own records and the agent launch log; see `compare` for the definitions.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
sys.path[:0] = [str(SCRIPTS), str(HERE)]

import durable_support as lab_support

TASKS = (("T1", "ok", lab_support.CHECK_GOOD, ()), ("T2", "fixlater", lab_support.CHECK_GOOD, ()),
         ("T3", "ok", lab_support.CHECK_HEAP, ()), ("T4", "quotaonce", lab_support.CHECK_GOOD, ()),
         ("T5", "ok", lab_support.CHECK_GOOD, ("T1",)), ("T6", "neverfix", lab_support.CHECK_GOOD, ()))
INJECTED = {"T2": "implementation", "T3": "environment", "T4": "quota", "T6": "unfixable"}
# launches no runtime can avoid: one per task, plus T2's wrong first try and T4's refused first start
UNAVOIDABLE = {"T1": 1, "T2": 2, "T3": 1, "T4": 2, "T5": 1}
TOKENS_PER_LAUNCH = 120          # what the fake agent reports per run (100 input + 20 output)


def plan() -> dict:
    """A strict 1.2.0 plan (the legacy planner's publication rules), read unchanged by both runtimes."""
    import bt_plan_adapter
    import owner_e2e_support as support
    tasks = []
    for task_id, scenario, check, after in TASKS:
        item = support.plan_task(task_id, f"{task_id} SCENARIO:{scenario} bench task", subplan=None,
                                 kind="implement", after=after)
        criterion = f"{task_id} leaves the good output"
        # one declared path per task (the planner's overlap rule); the fake agent also rewrites the shared out.txt with
        # the same content in every task, which both integration lines merge cleanly
        item.update(acceptance_criteria=[criterion], expected_paths=[f"{task_id}.task"],
                    verification=[{"type": "command", "value": check, "purpose": criterion, "category": "functional"}])
        tasks.append(item)
    data = {"schema_version": "1.2.0", "plan_id": "REQ-900", "spec_ref": "SPEC.md", "revision": 1,
            "milestones": [{"id": "M1", "title": "Bench", "acceptance_criteria": ["every bench task is verified"]}],
            "requirements": ["R4"], "tasks": tasks}
    report = bt_plan_adapter.planner.validate(data, strict_publication=True)
    if report.errors:
        raise SystemExit("invalid bench plan: " + "; ".join(report.errors))
    return data


class BenchDriver:
    """The one agent driver both runtimes use: the fake `claude` through bt_driver's claude invocation and parser."""

    def __init__(self, wrapper: Path):
        self.wrapper = str(wrapper)

    def prepare(self, route, prompt, workspace, timeout_seconds):
        import bt_driver
        from bt_scheduler_executor_adapter import m3
        invocation = bt_driver.driver_for("claude", self.wrapper).invocation(
            prompt, Path(workspace.path), route.model, route.effort or None, int(timeout_seconds), structured=True)
        return m3.Launch(argv=invocation.argv, stdin=invocation.stdin)

    def classify(self, route, raw, returncode, *, timed_out=False, cancelled=False):
        import bt_driver
        from bt_scheduler_executor_adapter import m3
        out = bt_driver.driver_for("claude").normalize(raw, returncode, timed_out=timed_out, cancelled=cancelled)
        return m3.Classification(out.status, out.reset_epoch, out.terminal_event, out.text, out.usage, out.cost_usd)


def _launches(path: Path) -> list[dict]:
    try:
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    except OSError:
        return []


# ------------------------------------------------------------------------------------------------------------ legacy
def run_legacy(root: Path) -> dict:
    """The legacy owner in this process, patched only where its own owner e2e patches it (no autostart, no
    notifications, the routes M2 may choose, the repository registry, short sleeps) — plus the shared agent driver."""
    from types import SimpleNamespace
    from unittest.mock import patch

    lab = lab_support.Lab(root / "lab", backend="pgroup")        # only for its repository, checks and fake claude
    os.environ.update(BITACORA_ROOT=str(root / "bitacora"), FAKE_COUNT=str(lab.count))
    import bt_config
    import bt_scheduler_adapter as scheduler_adapter
    import bt_scheduler_run as scheduler_run
    import owner_e2e_support as support
    import scheduler_chain_support as chain

    rdir = root / "bitacora" / "proj" / "requirements" / "REQ-900-bench"
    rdir.mkdir(parents=True)
    support.freeze_plan(rdir, plan())
    real_sleep = time.sleep
    clock = SimpleNamespace(sleep=lambda seconds: real_sleep(min(seconds, 0.5)), monotonic=time.monotonic,
                            time=time.time)

    class M2(chain.M2Port):
        def close(self):
            pass

    started = time.time()
    with patch.object(bt_config, "STATE", root / "bitacora" / ".state"), \
            patch.object(scheduler_run.bt_core, "ROOT", root / "bitacora"), \
            patch("bt_requirements_gate.require_ready"), \
            patch("bt_workspace.repos", return_value={"app": lab.repo}), \
            patch.object(scheduler_adapter, "DecisionAssignmentPort",
                         side_effect=lambda project, ledger, *, laya_root: M2(ledger, lambda _t: [("claude", "sonnet", "claude", "low")])), \
            patch("bt_scheduler_executor_wiring.api.MethodologyDriver", return_value=BenchDriver(lab.bin / "claude")), \
            patch.object(scheduler_run, "time", clock), \
            patch.object(scheduler_run, "_remove_autostart"), patch.object(scheduler_run, "_install_autostart"), \
            patch.object(scheduler_run.bt_notify, "notify"):
        # the owner returns when nothing more can run without a person (stalled) or everything is done
        code = scheduler_run.run("proj", "REQ-900", rdir, resume=False, no_autostart=True, max_steps=2400)
    ended = time.time()
    doc = _legacy_doc(rdir)
    attempts = list(doc.get("attempts", {}).values())
    accepted_at = {a["task_id"]: a["updated_at"] for a in attempts if a["state"] == "accepted"}
    first_failure = {}
    for a in sorted(attempts, key=lambda item: item["created_at"]):
        if a["state"] not in ("accepted",) and a["task_id"] not in first_failure:
            first_failure[a["task_id"]] = a["updated_at"]
    # what the run left for a person is the owner intervention; the durable side answers the same request "stop"
    waiting = [t for t, rec in doc["tasks"].items() if rec["state"] not in ("completed", "cancelled")]
    return {"runtime": "legacy", "wall_seconds": round(ended - started, 1), "exit_code": code,
            "launches": _launches(lab.count),
            "task_states": {t: rec["state"] for t, rec in doc["tasks"].items()},
            "task_reasons": {t: rec.get("reason", "")[:300] for t, rec in doc["tasks"].items() if rec.get("reason")},
            "attempts": [{k: a.get(k) for k in ("task_id", "number", "state", "failure", "budget_consumed",
                                                 "created_at", "updated_at")} for a in attempts],
            "owner_decisions": [{"task": t, "state": doc["tasks"][t]["state"]} for t in waiting],
            "recovery_seconds": {t: round(accepted_at[t] - first_failure[t], 1) for t in first_failure
                                 if t in accepted_at and accepted_at[t] >= first_failure[t]}}


def _legacy_doc(rdir: Path) -> dict:
    import sqlite3

    import bt_scheduler_adapter as scheduler_adapter
    conn = sqlite3.connect(f"{scheduler_adapter.run_db_path(rdir).resolve().as_uri()}?mode=ro", uri=True)
    try:
        return json.loads(conn.execute("SELECT doc FROM state WHERE id = 1").fetchone()[0])
    finally:
        conn.close()


# ----------------------------------------------------------------------------------------------------------- durable
def serve(config_path: str) -> None:
    data = json.loads(Path(config_path).read_text())
    lab = lab_support.Lab(Path(data["root"]), backend=data["backend"])
    from bt_contracts.execution import Route
    from bt_durable.adapters.runtime import SupervisorRuntime
    from bt_durable.service import operator_verifier, wire
    from bt_durable.service import serve as serve_engine
    cfg = lab.engine_config()
    runtime = SupervisorRuntime(lab.state / "supervisor", backend=lab.backend, unit_prefix=lab.unit_prefix)
    ports = wire(cfg, repositories_for=lambda project: {"app": lab.repo},
                 driver_for=lambda project: BenchDriver(lab.bin / "claude"),
                 routes=[Route(provider="claude", model="sonnet")], runtime=runtime,
                 verifier=operator_verifier(lab.state / "m6-quality.sqlite3"))
    serve_engine(cfg, ports, reap_seconds=2.0)


def run_durable(root: Path) -> dict:
    from bt_contracts.execution import RunRef
    from bt_contracts.owner import OwnerAnswer
    from bt_durable.client import Client
    from bt_durable.settings import Settings

    systemd = subprocess.run(["systemctl", "--user", "is-system-running"], capture_output=True, text=True,
                             check=False).stdout.strip() in ("running", "degraded")
    lab = lab_support.Lab(root / "lab", backend="systemd" if systemd else "pgroup")
    text = json.dumps(plan(), indent=2, sort_keys=True) + "\n"
    folder = lab.rdir / "plan-revisions"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "PLAN.r1.json").write_text(text)
    import hashlib
    run = RunRef(project="proj", req="REQ-900", plan_id="REQ-900", revision=1,
                 plan_sha256=hashlib.sha256(text.encode()).hexdigest(), plan_path=folder / "PLAN.r1.json")
    config = lab.write_config()
    log = open(lab.root / "engine.log", "ab")  # noqa: SIM115 - handed to the engine process
    engine = subprocess.Popen([sys.executable, str(Path(__file__)), "serve", str(config)],
                              env={**os.environ, **lab.env()}, stdout=log, stderr=subprocess.STDOUT,
                              start_new_session=True)
    client = None
    try:
        lab_support.wait_until(lambda: (lab.state / "dbos.sqlite3").exists() or engine.poll() is not None, 60)
        time.sleep(1.0)
        client = Client(lab.database_url)
        started = time.time()
        client.start(run, Settings(max_parallel=2, poll_seconds=0.5, run_poll_seconds=5, owner_wait_seconds=5))
        answered = []
        deadline = time.time() + 1800
        while time.time() < deadline:
            status = client.status(run)
            if status["workflow_status"] in ("SUCCESS", "ERROR"):
                break
            for task_id, item in status["tasks"].items():
                decision = item.get("decision")
                if decision and decision["request_id"] not in answered:
                    answered.append(decision["request_id"])
                    client.answer(run, task_id, OwnerAnswer(request_id=decision["request_id"], action="stop",
                                                            by="bench-owner"))
            time.sleep(0.5)
        ended = time.time()
        status = client.status(run)
    finally:
        if client is not None:
            client.close()
        if engine.poll() is None:
            engine.send_signal(signal.SIGTERM)
            try:
                engine.wait(30)
            except subprocess.TimeoutExpired:
                engine.kill()
        for verb in ("stop", "reset-failed"):
            subprocess.run(["systemctl", "--user", verb, f"{lab.unit_prefix}*"], capture_output=True, check=False)
    rows = [json.loads(line) for line in (lab.state / "telemetry.jsonl").read_text().splitlines()]
    settled = {r["task_id"]: r["ts"] for r in rows if r.get("event") == "task_settled" and r.get("status") == "completed"}
    first_failure = {}
    for r in rows:
        if r.get("event") == "recovery_decision" and r["task_id"] not in first_failure:
            first_failure[r["task_id"]] = r["ts"]
    return {"runtime": "durable", "wall_seconds": round(ended - started, 1), "launches": _launches(lab.count),
            "task_states": (status.get("summary") or {}).get("tasks", {}),
            "recovery_decisions": [{k: r.get(k) for k in ("task_id", "action", "code", "failure_class", "limit_hit")}
                                   for r in rows if r.get("event") == "recovery_decision"],
            "owner_decisions": [{"request": request, "answer": "stop"} for request in answered],
            "recovery_seconds": {t: round(settled[t] - first_failure[t], 1) for t in first_failure if t in settled}}


# ----------------------------------------------------------------------------------------------------------- compare
def summarize(result: dict) -> dict:
    per_task: dict[str, int] = {}
    for launch in result["launches"]:
        per_task[launch.get("task") or "?"] = per_task.get(launch.get("task") or "?", 0) + 1
    redundant = {t: per_task.get(t, 0) - need for t, need in UNAVOIDABLE.items() if per_task.get(t, 0) > need}
    return {"runtime": result["runtime"], "agent_launches": len(result["launches"]), "launches_per_task": per_task,
            "redundant_launches": redundant, "redundant_total": sum(redundant.values()),
            "launches_before_owner_asked_T6": per_task.get("T6", 0),
            "owner_interventions": len(result["owner_decisions"]),
            "tokens": len(result["launches"]) * TOKENS_PER_LAUNCH,
            "recovery_seconds": result.get("recovery_seconds", {}),
            "completed": sorted(t for t, s in result["task_states"].items() if s in ("completed", "inherited")),
            "not_completed": {t: s for t, s in result["task_states"].items() if s not in ("completed", "inherited")},
            "wall_seconds": result["wall_seconds"]}


def compare(out: Path) -> dict:
    sides = {name: summarize(json.loads((out / f"{name}.json").read_text())) for name in ("legacy", "durable")}
    return {"plan": [t[0] + " " + t[1] for t in TASKS], "injected": INJECTED, "unavoidable_launches": UNAVOIDABLE,
            "tokens_per_launch": TOKENS_PER_LAUNCH, **sides}


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] in ("legacy", "durable"):
        root = Path(argv[1])
        result = run_legacy(root) if argv[0] == "legacy" else run_durable(root)
        (root / f"{argv[0]}.json").write_text(json.dumps(result, indent=1, default=str))
        return 0
    if len(argv) == 2 and argv[0] == "serve":
        serve(argv[1])
        return 0
    if len(argv) == 2 and argv[0] in ("run", "compare"):
        out = Path(argv[1])
        if argv[0] == "run":
            out.mkdir(parents=True, exist_ok=True)
            for side in ("legacy", "durable"):
                root = out / side
                shutil.rmtree(root, ignore_errors=True)
                root.mkdir()
                with open(out / f"{side}.log", "w") as log:
                    subprocess.run([sys.executable, str(Path(__file__)), side, str(root)], stdout=log,
                                   stderr=subprocess.STDOUT, check=False, timeout=3600)
                shutil.copy(root / f"{side}.json", out / f"{side}.json")
        print(json.dumps(compare(out), indent=1))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
