"""D-266 (2026-10-31 ~18:45: / and /home at 100 %, pictures REQ-021 r32 T3.91 a9 «No space left on device»): the
engine's scratch. ~480 attempt worktrees of runs r15..r32 (each with node_modules and a Next build) were never removed
after their capture. Now an attempt's worktree is removed once its snapshot ref is written and nothing needs the
checkout (its round ended, or a later attempt of the round exists); a running, held, busy, uncaptured or unknown attempt
is kept. Before an agent starts or a check runs, a scratch filesystem below `execution.min_free_gb` stops with the
environment decision DISK_LOW instead of an attempt that dies with ENOSPC.

    PYTHONPATH=skill/scripts:skill/scripts/tests uv run python -m unittest test_durable_scratch
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import durable_support as lab_support
import test_durable_upgrade as upgrade
from bt_contracts.execution import AttemptRef, Prepared, RunRef, Snapshot, VerifyStatus
from bt_contracts.failure import Budget, FailureClass, RecoveryAction, Spent
from bt_durable import healing, scratch
from bt_durable.control import classify, policy
from bt_durable.legacy import handoff
from bt_durable.legacy import m3 as legacy_m3
from durable_support import wait_until
from test_durable_e2e import FAST, EngineCase


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


def row(workflow_id: str, status: str, parent: str = "", created: int = 0):
    return SimpleNamespace(workflow_id=workflow_id, status=status, parent_workflow_id=parent or None, created_at=created)


class FakeDBOS:
    """`list_workflows` over a fixed table, with the three filters `scratch.workflow_facts` uses."""

    def __init__(self, rows):
        self.rows = list(rows)
        self.calls = 0

    def list_workflows(self, *, workflow_ids=None, parent_workflow_id=None, load_input=True, load_output=True):
        self.calls += 1
        if workflow_ids is not None:
            return [r for r in self.rows if r.workflow_id in workflow_ids]
        return [r for r in self.rows if r.parent_workflow_id in (parent_workflow_id or ())]


class ScratchCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="bt-scratch-"))
        self.root = self.tmp / "attempts-root"
        self.repo = self.tmp / "app"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        (self.repo / ".gitignore").write_text("node_modules/\n")
        (self.repo / "README.md").write_text("app\n")
        git(self.repo, "add", "-A")
        git(self.repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "initial")
        self.base = git(self.repo, "rev-parse", "HEAD")
        self.addCleanup(subprocess.run, ["rm", "-rf", str(self.tmp)], check=False)

    def attempt(self, key: str, *, capture: bool = True) -> Path:
        """A worktree as GitWorkspaces lays it out, with installed dependencies, and (by default) its real capture."""
        name = legacy_m3.workspace.dirname_of(key)
        tree = self.root / "ws" / "proj" / "worktrees" / name
        branch = f"m3/{name}-scope1"
        tree.parent.mkdir(parents=True, exist_ok=True)
        git(self.repo, "worktree", "add", "-q", "-b", branch, str(tree), self.base)
        (tree / f"{key}.txt").write_text(key)
        (tree / "node_modules" / "pkg").mkdir(parents=True)
        (tree / "node_modules" / "pkg" / "index.js").write_bytes(b"x" * 65536)
        adir = self.root / "attempts" / key
        adir.mkdir(parents=True)
        ws = legacy_m3.model.Workspace(path=str(tree), branch=branch, base_sha=self.base, repo=str(self.repo))
        (adir / "workspace.json").write_text(json.dumps(ws.to_dict()))
        (adir / "output.log").write_text("log")
        if capture:
            handoff.capture(ws, adir, dirname=key, attempt_id=key, when=1_700_000_001.0, patch_max=1 << 20,
                            mode="snapshot")
        return tree

    def snapshot_ref(self, key: str) -> str:
        manifest = json.loads((self.root / "attempts" / key / "handoff" / "manifest.json").read_text())
        return manifest["refs"]["snapshot"]

    def registered(self) -> list[str]:
        return [line.split(" ", 1)[1] for line in git(self.repo, "worktree", "list", "--porcelain").splitlines()
                if line.startswith("worktree ") and str(self.root) in line]


class Collection(ScratchCase):
    def test_a_settled_attempt_loses_only_its_worktree(self):
        tree = self.attempt("a1")
        ref = self.snapshot_ref("a1")
        snapshot = git(self.repo, "rev-parse", ref)
        db = FakeDBOS([row("bt:a1:agent", "SUCCESS", "bt:run:T1:k1", 1), row("bt:run:T1:k1", "SUCCESS")])
        report = scratch.collect(self.root, db.list_workflows, apply=True)
        self.assertEqual([(v.key, v.action, v.reason) for v in report.verdicts], [("a1", "removed", "settled")])
        self.assertFalse(tree.exists())
        self.assertEqual(self.registered(), [])                                   # pruned from the repository
        self.assertEqual(git(self.repo, "rev-parse", ref), snapshot)              # the snapshot ref stays
        self.assertIn("a1.txt", git(self.repo, "ls-tree", "--name-only", snapshot))
        self.assertTrue(git(self.repo, "branch", "--list", "m3/*"))               # and the branch
        adir = self.root / "attempts" / "a1"
        self.assertEqual(sorted(p.name for p in adir.iterdir()), ["handoff", "output.log", "workspace.json"])

    def test_running_held_busy_and_unknown_attempts_are_kept(self):
        for key in ("run", "held", "busy", "unknown"):
            self.attempt(key)
        db = FakeDBOS([row("bt:run:agent", "PENDING", "bt:r:T1:k1", 1), row("bt:held:agent", "SUCCESS", "bt:r:T2:k1", 1),
                       row("bt:busy:agent", "SUCCESS", "bt:r:T3:k1", 1), row("bt:r:T1:k1", "PENDING"),
                       row("bt:r:T2:k1", "SUCCESS"), row("bt:r:T3:k1", "SUCCESS")])
        busy_tree = self.root / "ws" / "proj" / "worktrees" / legacy_m3.workspace.dirname_of("busy")
        sleeper = subprocess.Popen(["sleep", "30"], cwd=busy_tree)
        self.addCleanup(sleeper.wait)
        self.addCleanup(sleeper.kill)
        report = scratch.collect(self.root, db.list_workflows, apply=True, held=["held"])
        self.assertEqual(sorted((v.key, v.action, v.reason) for v in report.verdicts),
                         [("busy", "keep", "in-use"), ("held", "keep", "unit-held"), ("run", "keep", "running"),
                          ("unknown", "keep", "no-workflow")])
        self.assertEqual(len(self.registered()), 4)

    def test_an_attempt_without_its_snapshot_ref_is_kept_and_reported(self):
        self.attempt("nocapture", capture=False)
        self.attempt("moved")
        git(self.repo, "update-ref", "-d", self.snapshot_ref("moved"))
        db = FakeDBOS([row("bt:nocapture:agent", "ERROR", "bt:r:T1:k1", 1), row("bt:moved:agent", "SUCCESS", "bt:r:T2:k1", 1),
                       row("bt:r:T1:k1", "SUCCESS"), row("bt:r:T2:k1", "SUCCESS")])
        report = scratch.collect(self.root, db.list_workflows, apply=True)
        self.assertEqual(sorted((v.key, v.action, v.reason) for v in report.verdicts),
                         [("moved", "keep", "no-snapshot"), ("nocapture", "keep", "no-snapshot")])
        self.assertEqual(report.reasons(), {"no-snapshot": 2})
        self.assertEqual(len(self.registered()), 2)

    def test_in_an_open_round_only_the_latest_attempt_keeps_its_checkout(self):
        old, new = self.attempt("a1"), self.attempt("a2")
        db = FakeDBOS([row("bt:a1:agent", "SUCCESS", "bt:r:T1:k1", 100), row("bt:a2:agent", "SUCCESS", "bt:r:T1:k1", 200),
                       row("bt:a1:verify:standard", "SUCCESS", "bt:r:T1:k1", 150), row("bt:r:T1:k1", "PENDING")])
        report = scratch.collect(self.root, db.list_workflows, apply=True)
        self.assertEqual(sorted((v.key, v.action, v.reason) for v in report.verdicts),
                         [("a1", "removed", "settled"), ("a2", "keep", "latest-of-open-round")])
        self.assertFalse(old.exists())
        self.assertTrue((new / "node_modules" / "pkg" / "index.js").is_file())   # what M6 mounts for a2's reverify

    def test_a_second_pass_finds_nothing_and_removes_nothing(self):
        self.attempt("a1")
        self.attempt("a2")
        db = FakeDBOS([row("bt:a1:agent", "SUCCESS", "bt:r:T1:k1", 1), row("bt:a2:agent", "SUCCESS", "bt:r:T2:k1", 1),
                       row("bt:r:T1:k1", "SUCCESS"), row("bt:r:T2:k1", "PENDING")])
        first = scratch.collect(self.root, db.list_workflows, apply=True)
        self.assertEqual(first.counts(), {"removed": 1, "keep": 1})
        second = scratch.collect(self.root, db.list_workflows, apply=True)
        self.assertEqual([(v.key, v.action, v.reason) for v in second.verdicts], [("a2", "keep", "latest-of-open-round")])
        self.assertEqual(second.counts(), {"keep": 1})

    def test_a_dry_run_measures_and_touches_nothing_and_the_limit_bounds_a_pass(self):
        for key in ("a1", "a2", "a3"):
            self.attempt(key)
        rows = [row(f"bt:{k}:agent", "SUCCESS", f"bt:r:{k}:k1", 1) for k in ("a1", "a2", "a3")]
        db = FakeDBOS(rows + [row(f"bt:r:{k}:k1", "SUCCESS") for k in ("a1", "a2", "a3")])
        dry = scratch.collect(self.root, db.list_workflows, apply=False, sizes=True)
        self.assertEqual(dry.counts(), {"remove": 3})
        self.assertGreaterEqual(dry.summary()["bytes"], 3 * 65536)
        self.assertEqual(len(self.registered()), 3)
        self.assertIn("eligible (dry run): 3 worktrees", scratch.render(dry))
        self.assertIn("nothing was removed", scratch.render(dry))
        bounded = scratch.collect(self.root, db.list_workflows, apply=True, limit=2)
        self.assertEqual(bounded.counts(), {"removed": 2, "remove": 1})
        self.assertIn("left for the next pass (limit): 1", scratch.render(bounded))
        self.assertEqual(len(self.registered()), 1)

    def test_a_removal_cut_short_is_finished_and_orphans_are_only_reported(self):
        tree = self.attempt("a1")
        name = tree.name
        subprocess.run(["rm", "-rf", str(self.repo / ".git" / "worktrees" / name)], check=True)   # git forgot it
        orphan = self.root / "ws" / "proj" / "worktrees" / "stray"
        orphan.mkdir()
        db = FakeDBOS([row("bt:a1:agent", "SUCCESS", "bt:r:T1:k1", 1), row("bt:r:T1:k1", "CANCELLED")])
        report = scratch.collect(self.root, db.list_workflows, apply=True)
        self.assertEqual([(v.key, v.action) for v in report.verdicts], [("a1", "removed")])
        self.assertFalse(tree.exists())
        self.assertEqual(report.orphans, [str(orphan)])
        self.assertTrue(orphan.is_dir())

    def test_a_worktree_outside_the_scratch_is_never_deleted(self):
        tree = self.attempt("a1")
        outside = self.tmp / "elsewhere"
        git(self.repo, "worktree", "move", str(tree), str(outside))
        data = json.loads((self.root / "attempts" / "a1" / "workspace.json").read_text())
        data["path"] = str(outside)
        (self.root / "attempts" / "a1" / "workspace.json").write_text(json.dumps(data))
        manifest_path = self.root / "attempts" / "a1" / "handoff" / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["worktree"] = str(outside)
        manifest_path.write_text(json.dumps(manifest))
        db = FakeDBOS([row("bt:a1:agent", "SUCCESS", "bt:r:T1:k1", 1), row("bt:r:T1:k1", "SUCCESS")])
        report = scratch.collect(self.root, db.list_workflows, apply=True)
        self.assertEqual([(v.action, v.reason) for v in report.verdicts], [("failed", "outside-scratch")])
        self.assertTrue(outside.is_dir())


class Command(ScratchCase):
    """`bt-durable gc-worktrees`: a dry run unless --apply; no supervisor answer, nothing removed."""

    def run_cli(self, *argv, rows, runtime_error=None):
        from bt_durable import cli
        from bt_durable.settings import EngineConfig
        cfg = EngineConfig(system_database_url="sqlite:///unused", state_dir=self.tmp / "state", scratch_dir=self.root)
        db = FakeDBOS(rows)
        client = SimpleNamespace(client=db, close=lambda: None)

        class Runtime:
            def __init__(self, state_dir):
                if runtime_error:
                    raise runtime_error

            def owned(self, prefix):
                return []
        out, err = io.StringIO(), io.StringIO()
        with patch.object(cli, "engine_config", return_value=cfg), patch.object(cli, "_client", return_value=client), \
                patch("bt_durable.adapters.runtime.SupervisorRuntime", Runtime), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(["gc-worktrees", *argv])
        return code, json.loads(out.getvalue()), err.getvalue()

    def test_dry_run_by_default_then_apply(self):
        tree = self.attempt("a1")
        rows = [row("bt:a1:agent", "SUCCESS", "bt:r:T1:k1", 1), row("bt:r:T1:k1", "SUCCESS")]
        code, summary, text = self.run_cli(rows=rows)
        self.assertEqual(code, 0)
        self.assertEqual((summary["applied"], summary["counts"]), (False, {"remove": 1}))
        self.assertGreaterEqual(summary["bytes"], 65536)
        self.assertIn("eligible (dry run): 1 worktrees", text)
        self.assertTrue(tree.exists())
        code, summary, text = self.run_cli("--apply", "--no-size", rows=rows)
        self.assertEqual((code, summary["applied"], summary["counts"], summary["bytes"]), (0, True, {"removed": 1}, None))
        self.assertFalse(tree.exists())

    def test_apply_without_the_supervisor_removes_nothing(self):
        tree = self.attempt("a1")
        rows = [row("bt:a1:agent", "SUCCESS", "bt:r:T1:k1", 1), row("bt:r:T1:k1", "SUCCESS")]
        with self.assertRaises(SystemExit) as refused:
            self.run_cli("--apply", rows=rows, runtime_error=OSError("bus down"))
        self.assertIn("nothing removed", str(refused.exception))
        self.assertTrue(tree.exists())
        code, summary, _ = self.run_cli("--json", rows=rows, runtime_error=OSError("bus down"))   # a dry run still reports
        self.assertEqual((code, summary["counts"], summary["attempts"][0]["key"]), (0, {"remove": 1}, "a1"))


class Usage(SimpleNamespace):
    pass


class DiskGuardCase(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="bt-disk-"))
        for name in ("w1", "w2", "w3"):
            (self.root / "ws" / "pictures" / "worktrees" / name).mkdir(parents=True)
        (self.root / "ws" / "pictures" / "worktrees" / "w1.json").write_text("{}")
        self.legacy = self.root / "executor"
        (self.legacy / "run-1" / "ws" / "worktrees" / "att-1").mkdir(parents=True)
        self.free = 7 * 10 ** 6

    def guard(self, threshold=10 * scratch.GB):
        return scratch.DiskGuard(self.root, state_dir=self.root / "state", extra={"legacy executor worktrees": self.legacy},
                                 threshold=lambda: threshold, usage=lambda path: Usage(free=self.free))

    def test_below_the_floor_it_names_free_bytes_path_and_the_biggest_consumers(self):
        found = self.guard().check(None, None, "T3.91")
        self.assertEqual((found["state"], found["free_bytes"], found["threshold_bytes"]), ("low", self.free, 10 * scratch.GB))
        self.assertEqual(found["consumers"], [
            {"what": "attempt worktrees (pictures)", "count": 3, "path": str(self.root / "ws" / "pictures" / "worktrees")},
            {"what": "legacy executor worktrees", "count": 1, "path": str(self.legacy)}])
        failure = classify.disk_low(found)
        self.assertEqual((failure.failure_class, failure.code), (FailureClass.ENVIRONMENT, "DISK_LOW"))
        self.assertIn("DISK_LOW: 0.01 GB free on", failure.summary)
        self.assertIn("below execution.min_free_gb = 10 GB", failure.summary)
        self.assertIn("attempt worktrees (pictures): 3", failure.summary)
        self.assertIn("gc-worktrees --apply", failure.summary)
        decision = policy.decide(failure, Spent(), Budget(), now=0, other_route=True)
        self.assertEqual(decision.action, RecoveryAction.ESCALATE)                # never an agent attempt
        self.assertIn("DISK_LOW", healing.OWNER_ENV_CODES)                         # healing leaves it to the owner

    def test_enough_room_or_no_floor_is_quiet(self):
        self.free = 11 * scratch.GB
        self.assertEqual(self.guard().check(), {})
        self.free = 1
        self.assertEqual(self.guard(threshold=0).check(), {})

    def test_a_verification_below_the_floor_runs_no_check_and_asks_the_owner(self):
        from bt_durable.adapters.m6 import M6Verifier
        self.free = 1
        verifier = M6Verifier(store_path=self.root / "m6" / "m6.sqlite3")
        self.addCleanup(verifier.close)
        verifier.disk_guard = self.guard()
        verifier._engine = lambda run, profile: self.fail("no check may run")
        run = RunRef(project="proj", req="REQ-001", plan_id="REQ-001", revision=1, plan_sha256="0" * 64,
                     plan_path=self.root / "PLAN.r1.json")
        attempt = AttemptRef(run=run, task_id="T1", number=1, workflow_id="bt:proj:REQ-001:r1:T1:k1")
        prepared = Prepared(worktree=self.root, branch="b", base_sha="1" * 40, repository=self.root,
                            attempt_dir=self.root, prompt_path=self.root / "p", argv=("x",), env_file=self.root / "e",
                            timeout_seconds=1)
        manifest = self.root / "manifest.json"
        manifest.write_text("{}")
        outcome = verifier.verify(attempt, SimpleNamespace(), prepared,
                                  Snapshot(snapshot_sha="2" * 40, base_sha="1" * 40, manifest_path=manifest),
                                  profile="standard")
        self.assertEqual((outcome.status, outcome.reason_code, outcome.issue_codes),
                         (VerifyStatus.NEEDS_REVIEW, "DISK_LOW", ("DISK_LOW",)))
        failure = classify.classify(classify.AttemptFacts(verify=outcome))
        self.assertEqual((failure.failure_class, failure.code), (FailureClass.ENVIRONMENT, "DISK_LOW"))
        self.assertEqual(policy.decide(failure, Spent(), Budget(), now=0, other_route=True).action,
                         RecoveryAction.ESCALATE)


SERIAL = FAST.model_copy(update={"max_parallel": 1})


class InTheEngine(EngineCase):
    """End to end: the real engine, a real floor, real DBOS rows for the collection (parent workflow ids included)."""

    def test_disk_low_starts_no_agent_retry_runs_and_the_settled_worktree_is_collected(self):
        gates = {"audit_ledger_required": False, "audit_read_only": False}
        self.lab.configure(gates=gates, execution={"min_free_gb": 10 ** 9})        # 1 EB: always below the floor
        run = RunRef.model_validate(self.lab.freeze([lab_support.task("T1")]))
        self.start_engine()
        self.client.start(run, SERIAL)
        decision = lab_support.wait_until(lambda: (self.client.status(run)["tasks"].get("T1") or {}).get("decision"),
                                          240, interval=1, what="the disk decision")
        self.assertEqual(decision["failure"]["code"], "DISK_LOW")
        self.assertIn("below execution.min_free_gb", decision["reason"])
        self.assertEqual(self.lab.launches(), [])                                  # no agent ran
        self.lab.configure(gates=gates, execution={"min_free_gb": 0})              # the owner freed space
        from bt_contracts.owner import OwnerAnswer
        self.client.answer(run, "T1", OwnerAnswer(request_id=decision["request_id"], action="retry"))
        status = self.settled(run, timeout=240)
        self.assertEqual(status["summary"]["status"], "completed", status)
        self.assertEqual(status["summary"]["results"]["T1"]["attempts"], 1)       # the refused start used no attempt
        self.assertEqual(len(self.lab.launches()), 1)
        self.assertEqual([row["event"] for row in self.lab.telemetry() if row.get("event") == "disk_low"], ["disk_low"])
        root = self.lab.state / "attempts-root"
        trees = [p for p in root.glob("ws/*/worktrees/*") if p.is_dir()]
        self.assertEqual(len(trees), 1)
        dry = scratch.collect(root, self.client.client.list_workflows, apply=False)
        self.assertEqual(dry.counts(), {"remove": 1})
        done = scratch.collect(root, self.client.client.list_workflows, apply=True)
        self.assertEqual(done.counts(), {"removed": 1})
        self.assertFalse(trees[0].exists())
        manifest = json.loads(next(root.glob("attempts/*/handoff/manifest.json")).read_text())
        self.assertEqual(lab_support.git(self.lab.repo, "rev-parse", manifest["refs"]["snapshot"]), manifest["snapshot_sha"])


PREVIOUS = "89b1a87f1"          # main before D-266 (the live engine code when the disk filled)


class DiskGuardAfterUpgrade(upgrade.EngineUpgrade):
    """A task workflow recorded by the previous engine (two attempts, two owner decisions) replays on the current one:
    `bt-task-disk-guard` returns False where its history already holds the agent child, and only the retry answered
    after the upgrade meets the guard."""
    test_a_run_started_by_the_previous_engine_continues_on_the_new_one = None      # the parent's own scenario

    def decision(self, run, request_id: str) -> dict:
        def found():
            open_one = (self.client.status(run)["tasks"].get("T1") or {}).get("decision") or {}
            return open_one if open_one.get("request_id") == request_id else None
        return wait_until(found, 240, interval=0.5, what=f"decision {request_id}")

    def test_the_previous_engines_history_replays_and_the_next_start_is_guarded(self):
        from bt_contracts.owner import OwnerAnswer
        from bt_durable.client import Client
        gates = {"audit_ledger_required": False, "audit_read_only": False}
        scripts = lab_support.export_engine(PREVIOUS, Path(tempfile.mkdtemp(prefix="bt-previous-", dir=self.lab.root)))
        run = RunRef.model_validate(self.lab.freeze([lab_support.task("T1", scenario="neverfix")]))
        one_attempt = FAST.model_copy(update={"budget": FAST.budget.model_copy(update={"max_attempts": 1})})
        previous = self.spawn_previous(scripts)
        wait_until(lambda: (self.lab.state / "dbos.sqlite3").exists(), 60, what="DBOS database")
        self.client = Client(self.lab.database_url)
        self.addCleanup(self.client.close)

        def started():
            try:                                  # the file exists before the engine finished creating the schema
                return self.client.start(run, one_attempt)
            except Exception:  # noqa: BLE001
                return None
        wait_until(started, 60, interval=0.5, what="the previous engine's schema")
        self.decision(run, "T1:d1")
        self.client.answer(run, "T1", OwnerAnswer(request_id="T1:d1", action="retry_with_note", note="first answer"))
        self.decision(run, "T1:d2")
        os.killpg(previous.pid, signal.SIGKILL)
        previous.wait(10)

        self.lab.configure(gates=gates, execution={"min_free_gb": 10 ** 9})        # the disk is "full" now
        self.start_engine()                                                        # the current code, same database
        self.client.answer(run, "T1", OwnerAnswer(request_id="T1:d2", action="retry"))
        full = self.decision(run, "T1:d3")
        self.assertEqual(full["failure"]["code"], "DISK_LOW")
        self.assertEqual(len(self.lab.launches()), 2)                              # the replay launched nothing again
        self.lab.configure(gates=gates, execution={"min_free_gb": 0})
        self.client.answer(run, "T1", OwnerAnswer(request_id="T1:d3", action="retry"))
        self.decision(run, "T1:d4")
        self.client.answer(run, "T1", OwnerAnswer(request_id="T1:d4", action="stop"))
        status = self.settled(run, timeout=240)
        rows = self.client.workflows(f"bt:{run.run_id}")
        self.assertFalse([r.workflow_id for r in rows if r.status == "ERROR"], [(r.workflow_id, r.status) for r in rows])
        self.assertEqual(status["summary"]["status"], "blocked", status)
        self.assertEqual(len(self.lab.launches()), 3)
        self.assertEqual(len(list(self.lab.state.glob("attempts-root/attempts/*T1-a3-*/handoff/manifest.json"))), 1)


if __name__ == "__main__":
    unittest.main()
