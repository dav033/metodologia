"""A small run on disk with the shapes of the real stores, for the structural recovery tests (REQ-029 P-152/P-153).

Layout is the bitácora's (`<root>/<project>/requirements/REQ-001-x`, stores under `<root>/.state`), the M1 document, the M6 store,
the executor ledger and its manifests have the columns and keys the real ones have (checked against a real run of REQ-029), the
repository is a real git repository, and the plan is frozen through the planner. Nothing here runs a scheduler: tests set the state
the run would be in (`set_state`) and the pipeline reads it the way it reads a real one.
"""
from __future__ import annotations

import json
import sqlite3
import subprocess
from contextlib import closing
from pathlib import Path

import bt_plan_adapter
import bt_run_stores
import bt_scheduler_adapter as adapter

RUNTIME = "a" * 32
M5_SCHEMA = ("CREATE TABLE IF NOT EXISTS diagnostic_cycles (lineage_id TEXT PRIMARY KEY, cycle_token TEXT NOT NULL UNIQUE, "
             "state TEXT NOT NULL, identity_json TEXT NOT NULL, payload_json TEXT NOT NULL, updated_at REAL NOT NULL)")


def plan_for_tests() -> dict:
    from test_recovery_compiler import RecoveryCompilerTests

    case = RecoveryCompilerTests("test_web_coverage_includes_typecheck_and_build")
    case.setUp()
    return case.plan


class RecoveryRun:
    def __init__(self, root: Path, project: str = "demo", req: str = "REQ-001-x", plan: dict | None = None):
        self.root = Path(root)
        self.rdir = self.root / project / "requirements" / req
        self.rdir.mkdir(parents=True)
        self.project = project
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.commits: dict[str, str] = {}
        self.plan = plan or plan_for_tests()
        self.frozen = bt_plan_adapter.freeze_revision(self.rdir, self.plan, "approval")
        self.db = adapter.run_db_path(self.rdir)
        self.db.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute("CREATE TABLE state (id INTEGER PRIMARY KEY, doc TEXT NOT NULL)")
            conn.commit()
        bt_run_stores.runtime_marker(self.db).write_text(json.dumps({"runtime_id": RUNTIME}))
        stores = bt_run_stores.module_stores(self.db, RUNTIME)
        stores["m5"].parent.mkdir(parents=True, exist_ok=True)
        stores["m5"].parent.chmod(0o700)
        with closing(sqlite3.connect(stores["m5"])) as conn:
            conn.execute(M5_SCHEMA)
            conn.commit()
        from bt_scheduler_quality.store import QualityStore

        QualityStore(stores["m6"]).close()
        self.executor = self.root / ".state" / "executor" / f"{project}-REQ-001-r1-x"
        self.executor.mkdir(parents=True)
        with closing(sqlite3.connect(self.executor / "ledger.db")) as conn:
            conn.execute("CREATE TABLE attempts (attempt_id TEXT PRIMARY KEY, dirname TEXT NOT NULL)")
            conn.commit()

    # ---- git
    def git(self, *args: str) -> str:
        done = subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=T", "-c", "user.email=t@t", *args],
                              capture_output=True, text=True, check=True)
        return done.stdout.strip()

    def commit(self, name: str, files: dict[str, str]) -> str:
        for path, text in files.items():
            target = self.repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
            self.git("add", path)
        self.git("commit", "-q", "--allow-empty", "-m", name)
        self.commits[name] = self.git("rev-parse", "HEAD")
        return self.commits[name]

    # ---- the records of one attempt
    def attempt(self, attempt_id: str, task_id: str, *, base: str, snapshot: str, verdict: dict | None = None,
                revision: int = 1, token: int = 1) -> None:
        dirname = f"{attempt_id}-0123456789abcdef"
        handoff = self.executor / "attempts" / dirname / "handoff"
        handoff.mkdir(parents=True)
        (handoff / "manifest.json").write_text(json.dumps({
            "schema": 1, "status": "captured", "attempt_id": attempt_id, "repository": str(self.repo), "base_sha": base,
            "snapshot_sha": snapshot, "handoff_mode": "snapshot"}))
        with closing(sqlite3.connect(self.executor / "ledger.db")) as conn:
            conn.execute("INSERT OR REPLACE INTO attempts VALUES (?, ?)", (attempt_id, dirname))
            conn.commit()
        if verdict is not None:
            request = {"plan_id": self.plan["plan_id"], "revision": revision, "task_id": task_id, "attempt_id": attempt_id,
                       "token": token, "idempotency_key": f"verify:{task_id}:{attempt_id}"}
            with closing(sqlite3.connect(bt_run_stores.paths(self.rdir)["m6"])) as conn:
                conn.execute("INSERT OR REPLACE INTO requests(idempotency_key, input_hash, request_json, state, result_json, "
                             "result_hash, created_at, updated_at) VALUES (?, ?, ?, 'complete', ?, 'h', 't', 't')",
                             (request["idempotency_key"], "i", json.dumps(request), json.dumps(verdict)))
                conn.commit()

    def set_state(self, tasks: dict, attempts: dict, *, plan_sha256: str | None = None, revision: int = 1) -> None:
        doc = {"plan_id": self.plan["plan_id"], "revision": revision, "plan_sha256": plan_sha256 or self.frozen["sha256"],
               "tasks": tasks, "attempts": attempts}
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute("INSERT OR REPLACE INTO state(id, doc) VALUES (1, ?)", (json.dumps(doc),))
            conn.commit()


def conflict_plan() -> dict:
    """Two UNORDERED tasks that both own `web` (the planner allows it when each names the other as its coupling), a consumer that
    needs both, and an audit after it: the plan in which two accepted results can clash on the same file."""
    import copy

    import bt_plan_adapter

    plan = plan_for_tests()
    first = plan["tasks"][0]
    second = copy.deepcopy(first)
    second.update({"id": "T5", "title": "Implement the second page behavior", "coupling": "high",
                   "objective": "Implement the second page behavior in the same page file",
                   "acceptance_criteria": ["The second page behavior holds"]})
    first["coupling"] = "high"
    first["classification_evidence"]["coupling"]["evidence"] = ["spec:SPEC.md", "task:T5"]
    second["classification_evidence"]["coupling"]["evidence"] = ["spec:SPEC.md", "task:T1"]
    for check in second["verification"]:
        check["purpose"] += " (second behavior)"
    plan["tasks"].insert(1, second)
    for task in plan["tasks"]:
        if task["id"] == "T3":
            task["after"] = ["T1", "T5"]
    errors = bt_plan_adapter.plan_errors(plan)
    assert not errors, errors
    return plan
