from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import bt_scheduler_core as m1
import bt_scheduler_executor as m3
import bt_scheduler_executor_adapter as m3_adapter
import bt_scheduler_integrator as m3_integrator
from bt_scheduler_quality.policy import QualityPolicy
from bt_scheduler_quality.store import QualityStore
from bt_scheduler_quality_adapter import QualityVerificationPort

SCRIPTS = Path(__file__).resolve().parents[1]
PROVIDER = """from pathlib import Path
import subprocess
import sys

task_id = sys.argv[1]
fixtures = {
    "T1": ("alpha.txt", "alpha\\n", "verify_t1.py", 'from pathlib import Path\\nassert Path("alpha.txt").read_text().strip() == "alpha"\\n'),
    "T2": ("beta.txt", "beta\\n", "verify_t2.py", 'from pathlib import Path\\nassert Path("beta.txt").read_text().strip() == "beta"\\n'),
    "T3": ("joined.txt", "joined\\n", "verify_t3.py", 'from pathlib import Path\\nassert Path("alpha.txt").read_text().strip() == "alpha"\\nassert Path("beta.txt").read_text().strip() == "beta"\\nraise AssertionError("intentional integration regression")\\n'),
    "T4": ("contract.txt", "contract-v1\\n", "verify_t4.py", 'from pathlib import Path\\nassert Path("contract.txt").read_text().strip() == "contract-v1"\\n'),
    "T5": ("contract.txt", "contract-v2\\n", "verify_t5.py", 'from pathlib import Path\\nassert Path("contract.txt").read_text().strip() == "contract-v2"\\n'),
}
tracked_path, tracked_content, verification_path, verification = fixtures[task_id]
Path(tracked_path).write_text(tracked_content, encoding="utf-8")
Path(verification_path).write_text(verification, encoding="utf-8")
if task_id == "T3":
    Path("report.json").write_text('{"status":"ready"}', encoding="utf-8")
subprocess.run(["git", "add", "--", tracked_path], check=True, capture_output=True)
subprocess.run(["git", "-c", "user.name=M6 fake provider", "-c", "user.email=m6@example.invalid",
                "-c", "core.hooksPath=/dev/null", "commit", "-m", "fake provider change"],
               check=True, capture_output=True)
print("fake local provider finished")
"""


class LocalResolver:
    def resolve(self, request):
        return m3.Route("local-test", request.task_id, reference=request.executor)


class LocalDriver:
    def __init__(self, provider_path: Path):
        self.provider_path = provider_path

    def prepare(self, route, prompt, workspace, timeout_seconds):
        return m3.Launch(argv=(sys.executable, str(self.provider_path), route.model))

    def classify(self, route, raw, returncode, *, timed_out=False, cancelled=False):
        if timed_out:
            return m3.Classification("timeout", terminal_event=True, text=raw[-200:])
        if cancelled:
            return m3.Classification("cancelled", terminal_event=True, text=raw[-200:])
        status = "completed" if returncode == 0 else "failed"
        return m3.Classification(status, terminal_event=True, text=raw[-200:])


class M6RealM3IntegrationTests(unittest.TestCase):
    def test_real_m3_handoffs_run_m6_checks_and_keep_m1_m5_authority(self):
        with tempfile.TemporaryDirectory(prefix="m6-real-m3-") as temporary:
            root = Path(temporary)
            repository = root / "repository"
            repository.mkdir()
            _git(repository, "init", "-q", "-b", "main")
            (repository / "README.md").write_text("base\n", encoding="utf-8")
            _git(repository, "add", "README.md")
            _git(
                repository,
                "-c",
                "user.name=fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-q",
                "-m",
                "base",
            )
            base_head = _git(repository, "rev-parse", "HEAD")
            base_branch = _git(repository, "branch", "--show-current")
            base_status = _git(repository, "status", "--porcelain")
            index_path = repository / ".git" / "index"
            base_index = hashlib.sha256(index_path.read_bytes()).hexdigest()

            tasks = [
                _task("T1", "alpha is valid", tracked_path="alpha.txt"),
                _task("T2", "beta is valid", tracked_path="beta.txt"),
                _task(
                    "T3",
                    "joined integration is valid",
                    after=("T1", "T2"),
                    tracked_path="joined.txt",
                ),
                _task(
                    "T4",
                    "contract v1 is valid",
                    tracked_path="contract.txt",
                    shared_resources=("public-api-contract",),
                ),
                _task(
                    "T5",
                    "contract v2 is valid",
                    tracked_path="contract.txt",
                    shared_resources=("public-api-contract",),
                ),
                _task(
                    "T6",
                    "contracts can be combined",
                    after=("T4", "T5"),
                    tracked_path="joined-contract.txt",
                ),
            ]
            plan_text = json.dumps(
                {
                    "schema_version": "1.0.0",
                    "plan_id": "PLAN-M6-REAL-M3",
                    "revision": 1,
                    "tasks": tasks,
                }
            )
            plan = m1.load_plan(
                plan_text,
                approved_sha256=hashlib.sha256(plan_text.encode()).hexdigest(),
            )
            recovery = m1.ScriptedRecovery(
                {
                    "T3": m1.RecoveryProposal(
                        "block", "regression is not safe to retry"
                    ),
                    "T6": m1.RecoveryProposal(
                        "block", "contract collision needs an operator"
                    ),
                }
            )

            provider_path = root / "fake_local_provider.py"
            provider_path.write_text(PROVIDER, encoding="utf-8")
            executor_root = root / "m3"
            sink = m3_adapter.CoreEventSink()
            executor = m3.AgentExecutor(
                executor_root,
                resolver=LocalResolver(),
                briefs=m3_adapter.PlanBriefs(plan),
                driver=LocalDriver(provider_path),
                workspaces=m3.GitWorkspaces(executor_root / "ws", {"repo": repository}),
                sink=sink,
                config=m3.Config(
                    max_running=4,
                    poll_seconds=0.03,
                    heartbeat_seconds=3600,
                    grace_seconds=1,
                    timeout_seconds=10,
                ),
                autostart=False,
            )
            execution = m3_adapter.CoreExecutionPort(
                executor, plan, project="m6-test", default_repository="repo"
            )
            core = m1.SchedulerCore(
                plan,
                m1.InMemoryRepository(),
                ports=m1.Ports(execution=execution, recovery=recovery),
                config=m1.Config(max_parallel_tasks=4, max_attempts=1),
            )
            sink.bind(core)
            predecessor_integrator = m3_integrator.PredecessorIntegrator(
                fallback="HEAD"
            )
            predecessor_integrator.bind(
                plan=plan,
                accepted=lambda: {
                    task_id: view["attempt"]
                    for task_id, view in core.snapshot().tasks.items()
                    if view.get("state") == "completed" and view.get("attempt")
                },
                snapshot_of=lambda attempt_id: (
                    (executor.describe(attempt_id) or {})
                    .get("handoff", {})
                    .get("snapshot_sha")
                ),
                repo_of=lambda role: repository if role == "repo" else None,
                default_repository="repo",
                identity="PLAN-M6-REAL-M3-r1",
            )
            execution.base_ref = predecessor_integrator.base_ref

            store = QualityStore(root / "quality" / "m6.sqlite3")
            verifier = QualityVerificationPort(
                core, executor, store, QualityPolicy(), lambda order: repository
            )
            core.ports.verification = verifier
            try:
                core.start()
                executor.start_loop()
                verifier.start()
                expected = {
                    "T1": "completed",
                    "T2": "completed",
                    "T3": "blocked",
                    "T4": "completed",
                    "T5": "completed",
                    "T6": "blocked",
                }
                deadline = time.monotonic() + 45
                while time.monotonic() < deadline:
                    core.step()
                    states = {
                        task_id: task_view["state"]
                        for task_id, task_view in core.snapshot().tasks.items()
                    }
                    if states == expected:
                        break
                    if states["T1"] == "blocked" and states["T2"] == "blocked":
                        break
                    time.sleep(0.02)
                rejected_attempts = {
                    attempt_id: executor.describe(attempt_id)
                    for attempt_id in executor.ledger.all_ids()
                }
                self.assertEqual(
                    states,
                    expected,
                    f"M1 audit={[(e.kind, e.task_id, e.detail) for e in core.audit_log()[-12:]]!r}; "
                    f"M3 attempts={[(key, value['state'], value.get('rejection')) for key, value in rejected_attempts.items()]!r}",
                )

                snapshot = core.snapshot()
                attempt_ids = {
                    task_id: row["attempt"]
                    for task_id, row in snapshot.tasks.items()
                    if row.get("attempt")
                }
                results = {}
                for task_id in ("T1", "T2", "T3", "T4", "T5"):
                    request_key = _verify_key(core, attempt_ids[task_id])
                    results[task_id] = store.get_result(request_key)
                self.assertFalse(
                    {
                        task: _verify_key(core, attempt_ids[task])
                        for task, result in results.items()
                        if result is None
                    },
                    f"missing M6 results; metrics={store.metrics()!r}",
                )
                self.assertEqual(
                    {task: result["status"] for task, result in results.items()},
                    {
                        "T1": "PASS",
                        "T2": "PASS",
                        "T3": "FAIL",
                        "T4": "PASS",
                        "T5": "PASS",
                    },
                )
                self.assertEqual(
                    results["T3"]["input"]["base_sha"],
                    executor.describe(attempt_ids["T3"])["handoff"]["base_sha"],
                )
                t3_snapshot = executor.describe(attempt_ids["T3"])["handoff"][
                    "snapshot_sha"
                ]
                self.assertEqual(
                    _git(repository, "show", f"{t3_snapshot}:report.json"),
                    '{"status":"ready"}',
                )
                self.assertEqual(
                    _git(
                        repository,
                        "show",
                        f"{results['T3']['input']['base_sha']}:alpha.txt",
                    ),
                    "alpha",
                )
                self.assertEqual(
                    _git(
                        repository,
                        "show",
                        f"{results['T3']['input']['base_sha']}:beta.txt",
                    ),
                    "beta",
                )
                self.assertIn(
                    "verification_rejected", {item.cause for item in recovery.calls}
                )
                self.assertIn(
                    "execution_failed", {item.cause for item in recovery.calls}
                )
                self.assertTrue(
                    any(
                        "INTEGRATION_CONFLICT" in item.detail for item in recovery.calls
                    )
                )

                handoff = executor.describe(attempt_ids["T1"])["handoff"]
                self.assertEqual(handoff["status"], "captured")
                self.assertTrue(handoff["dirty"])
                self.assertGreater(handoff["untracked_count"], 0)
                cli = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "bt_scheduler_executor",
                        "show",
                        "--root",
                        str(executor_root),
                        attempt_ids["T1"],
                        "--json",
                    ],
                    cwd=root,
                    env={**os.environ, "PYTHONPATH": str(SCRIPTS)},
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                self.assertEqual(cli.returncode, 0, cli.stderr)
                self.assertEqual(
                    json.loads(cli.stdout)["handoff"]["status"], "captured"
                )
                self.assertTrue(executor.wait_idle(10))
                self.assertEqual(_git(repository, "rev-parse", "HEAD"), base_head)
                self.assertEqual(
                    _git(repository, "branch", "--show-current"), base_branch
                )
                self.assertEqual(_git(repository, "status", "--porcelain"), base_status)
                self.assertEqual(
                    hashlib.sha256(index_path.read_bytes()).hexdigest(), base_index
                )
            finally:
                verifier.close()
                executor.close(wait=True)
                store.close()


def _task(
    task_id: str, criterion: str, *, after=(), tracked_path: str, shared_resources=()
) -> dict[str, object]:
    verification_path = f"verify_{task_id.lower()}.py"
    return {
        "id": task_id,
        "milestone_id": "M1",
        "after": list(after),
        "repository": "repo",
        "shared_resources": list(shared_resources),
        "expected_paths": [tracked_path, verification_path],
        "acceptance_criteria": [criterion],
        "verification": [
            {
                "type": "command",
                "value": f"python3 {verification_path}",
                "purpose": criterion,
            }
        ],
    }


def _verify_key(core: m1.SchedulerCore, attempt_id: str) -> str:
    return f"{core.plan.plan_id}:r{core.plan.revision}:{attempt_id}:verify"


def _git(repository: Path, *args: str) -> str:
    result = subprocess.run(
        [
            "git",
            "-c",
            "user.name=fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "-c",
            "core.hooksPath=/dev/null",
            *args,
        ],
        cwd=repository,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if result.returncode:
        raise AssertionError(f"git {args!r} failed: {result.stderr}")
    return result.stdout.strip()


if __name__ == "__main__":
    unittest.main()
