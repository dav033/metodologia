"""Migration bridge from legacy runs (REQ-030 M8): progress is re-proved from evidence, never copied; ownership
moves once, refuses while the legacy run is alive, repeats as a no-op, and rolls back by handing the run back."""
from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import bt_run_owner
from bt_durable import migrate


def git(cwd, *args):
    return subprocess.run(["git", "-c", "user.name=T", "-c", "user.email=t@t", *args], cwd=cwd, check=True,
                          capture_output=True, text=True).stdout.strip()


class Legacy:
    """A legacy run on disk: Scheduler state doc, an M6 store with content-addressed results, executor manifests."""

    def __init__(self, root: Path):
        self.root = root
        self.state = root / "state"
        (self.state / "scheduler").mkdir(parents=True)
        self.repo = root / "app"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        (self.repo / "a.txt").write_text("a\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "base")
        self.base = git(self.repo, "rev-parse", "HEAD")
        self.rdir = root / "bitacora" / "proj" / "requirements" / "REQ-777-old"
        (self.rdir / "plan-revisions").mkdir(parents=True)
        tasks = [{"id": t, "objective": t, "acceptance_criteria": [f"{t} ok"], "after": [], "repository": "app",
                  "verification": [{"type": "command", "value": "true", "purpose": f"{t} ok"}],
                  "expected_paths": []} for t in ("T1", "T2", "T3", "T4", "T5")]
        self.plan = json.dumps({"schema_version": "1.0.0", "plan_id": "REQ-777", "revision": 2, "tasks": tasks})
        (self.rdir / "plan-revisions" / "PLAN.r2.json").write_text(self.plan)
        self.m6 = self.state / "scheduler" / "proj-REQ-777-abc-modules"
        self.m6.mkdir()
        conn = sqlite3.connect(self.m6 / "m6-quality.sqlite3")
        conn.execute("CREATE TABLE artifacts (digest TEXT PRIMARY KEY, media_type TEXT, content BLOB, created_at TEXT)")
        conn.commit()
        conn.close()
        self.tasks, self.attempts = {}, {}

    def snapshot(self, name: str) -> str:
        git(self.repo, "checkout", "-q", "-b", f"att-{name}", self.base)
        (self.repo / f"{name}.txt").write_text(name)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", name)
        sha = git(self.repo, "rev-parse", "HEAD")
        git(self.repo, "checkout", "-q", "main")
        return sha

    def result(self, task: str, status: str, snapshot: str, revision: int = 2, tamper: bool = False) -> str:
        # the shape M6 really stores behind m6://result/: an evidence manifest, with no top-level status
        mark = "pass" if status == "PASS" else "fail"
        body = json.dumps({"schema_version": "m6.evidence-manifest/1.1", "reason_code": "PASS" if mark == "pass" else
                           "FAIL_CODE", "criteria": [{"status": mark}], "checks": [{"status": mark}],
                           "request": {"task_id": task, "revision": revision},
                           "input": {"snapshot_sha": snapshot, "base_sha": self.base}}).encode()
        digest = hashlib.sha256(body).hexdigest()
        conn = sqlite3.connect(self.m6 / "m6-quality.sqlite3")
        conn.execute("INSERT INTO artifacts VALUES (?,?,?,?)", (digest, "application/json",
                                                                body + (b" " if tamper else b""), "now"))
        conn.commit()
        conn.close()
        return f"m6://result/{digest}"

    def accepted(self, task: str, attempt: str, evidence: str, snapshot: str):
        self.tasks[task] = {"state": "completed", "attempts": [attempt]}
        self.attempts[attempt] = {"state": "accepted", "evidence": evidence, "task_id": task}
        hand = self.state / "executor" / "proj-REQ-777-r2-x" / "attempts" / f"{attempt}-ff" / "handoff"
        hand.mkdir(parents=True)
        (hand / "manifest.json").write_text(json.dumps({"repository": str(self.repo), "snapshot_sha": snapshot,
                                                        "base_sha": self.base}))

    def write(self, live: bool = False):
        attempts = dict(self.attempts)
        if live:
            attempts["att-9"] = {"state": "running", "task_id": "T5"}
            self.tasks["T5"] = {"state": "active", "attempts": ["att-9"]}
        doc = {"plan_id": "REQ-777", "revision": 2, "plan_sha256": hashlib.sha256(self.plan.encode()).hexdigest(),
               "tasks": self.tasks, "attempts": attempts}
        db = self.state / "scheduler" / "proj-REQ-777.db"
        db.unlink(missing_ok=True)
        conn = sqlite3.connect(db)
        conn.execute("CREATE TABLE state (id INTEGER PRIMARY KEY, version INTEGER, doc TEXT)")
        conn.execute("INSERT INTO state VALUES (1, 1, ?)", (json.dumps(doc),))
        conn.commit()
        conn.close()


class Migration(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="bt-migrate-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.legacy = Legacy(self.root)
        lg = self.legacy
        s1, s2, s3 = lg.snapshot("t1"), lg.snapshot("t2"), lg.snapshot("t3")
        lg.accepted("T1", "att-1", lg.result("T1", "PASS", s1), s1)                 # proven: inherit
        lg.accepted("T2", "att-2", lg.result("T2", "FAIL", s2), s2)                 # accepted on weaker evidence
        lg.accepted("T3", "att-3", lg.result("T3", "PASS", s3, tamper=True), s3)    # tampered evidence
        lg.tasks["T4"] = {"state": "blocked", "attempts": [], "reason": "attempts_exhausted: check X fails"}

    def inventory(self, **kw):
        return migrate.inventory(state_dir=self.legacy.state, rdir=self.legacy.rdir, project="proj", req="REQ-777", **kw)

    def test_progress_is_inherited_only_with_valid_evidence(self):
        self.legacy.write()
        inv = self.inventory()
        verdicts = {t.task_id: t.verdict for t in inv.tasks}
        self.assertEqual(verdicts, {"T1": "inherit", "T2": "reconcile", "T3": "redo", "T4": "redo"})
        self.assertEqual(migrate.inherited(inv), {"T1": "legacy att-1 " + inv.tasks[0].evidence})
        self.assertIn("attempts_exhausted", next(t for t in inv.tasks if t.task_id == "T4").diagnosis)

    def test_a_vanished_snapshot_is_redone(self):
        self.legacy.write()
        sha = next(t for t in self.inventory().tasks if t.task_id == "T1").snapshot_sha
        git(self.legacy.repo, "branch", "-D", "att-t1")
        git(self.legacy.repo, "reflog", "expire", "--expire=now", "--all")
        git(self.legacy.repo, "gc", "-q", "--prune=now")
        inv = self.inventory()
        self.assertEqual(next(t for t in inv.tasks if t.task_id == "T1").verdict, "redo", sha)

    def test_claim_refuses_a_live_legacy_run(self):
        self.legacy.write(live=True)
        inv = self.inventory(owner_pids=[4242])
        self.assertEqual(len(inv.blockers), 2)
        with self.assertRaisesRegex(RuntimeError, "MIGRATION_BLOCKED"):
            migrate.claim(self.legacy.rdir, inv, by="test")
        self.assertIsNone(bt_run_owner.read(self.legacy.rdir))

    def test_claim_is_idempotent_and_blocks_the_legacy_owner_then_rolls_back(self):
        self.legacy.write()
        inv = self.inventory()
        first = migrate.claim(self.legacy.rdir, inv, by="test")
        again = migrate.claim(self.legacy.rdir, self.inventory(), by="test")
        self.assertEqual(first, again)
        self.assertIn("OWNED_BY_DBOS", bt_run_owner.refuse_legacy_start(self.legacy.rdir))
        report = migrate.diff(self.inventory(), self.legacy.rdir)
        self.assertEqual(report["current_owner"]["backend"], "dbos")
        migrate.release(self.legacy.rdir, by="test")
        self.assertEqual(bt_run_owner.refuse_legacy_start(self.legacy.rdir), "")

    def test_inventory_and_backup_are_stable_and_never_write_the_legacy_stores(self):
        self.legacy.write()
        db = self.legacy.state / "scheduler" / "proj-REQ-777.db"
        before = hashlib.sha256(db.read_bytes()).hexdigest()
        inv1, inv2 = self.inventory(), self.inventory()
        self.assertEqual(inv1.digest, inv2.digest)
        target = migrate.backup(self.legacy.state, self.legacy.rdir, inv1, self.root / "backups")
        self.assertEqual(migrate.backup(self.legacy.state, self.legacy.rdir, inv2, self.root / "backups"), target)
        self.assertTrue((target / "SHA256SUMS").read_text().strip())
        self.assertEqual(hashlib.sha256(db.read_bytes()).hexdigest(), before)

    def test_concurrent_owner_changes_lose_the_race_cleanly(self):
        self.legacy.write()
        inv = self.inventory()
        stale = bt_run_owner.read(self.legacy.rdir)
        migrate.claim(self.legacy.rdir, inv, by="first")
        with self.assertRaises(bt_run_owner.OwnerConflict):
            bt_run_owner.write(self.legacy.rdir, {"backend": "legacy"}, expect=stale)


if __name__ == "__main__":
    unittest.main()
