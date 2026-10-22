from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import bt_recovery_cycle as cycles
import bt_recovery_rollout as rollout

GIT = ["git", "-c", "commit.gpgsign=false"]
GIT_IDENTITY = {"GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.invalid",
                "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.invalid"}


def git(repo, *args):
    return subprocess.run([*GIT, *args], cwd=repo, check=True, capture_output=True, text=True,
                          env={**os.environ, **GIT_IDENTITY}).stdout.strip()


def make_repo(root: Path) -> tuple[Path, str, str]:
    repo = root / "repo"
    (repo / "skill/scripts").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    (repo / "skill/scripts/bitacora.py").write_text("print('staged')\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "base")
    correction = git(repo, "rev-parse", "HEAD")
    (repo / "skill/scripts/extra.py").write_text("X = 1\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "upgrade")
    return repo, git(repo, "rev-parse", "HEAD"), correction


def receipts(snapshot: str, correction: str) -> dict:
    return {"upgrade": {"snapshot": snapshot, "accepted": True},
            "m6": {"accepted": True, "snapshot": snapshot, "receipt": "m6-receipt-1"},
            "audits": [{"id": "T8", "verdict": "accepted", "snapshot": snapshot},
                       {"id": "T9", "verdict": "accepted", "snapshot": snapshot}],
            "correction_commits": [correction]}


def ok_smoke(stage: Path) -> dict:
    return {"ok": True}


class Staging(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.repo, self.snapshot, self.correction = make_repo(self.root)
        self.state = self.root / "state"
        self.addCleanup(self._tmp.cleanup)

    def prepare(self, **kw):
        return rollout.prepare_recovery_runtime(self.repo, self.snapshot, receipts(self.snapshot, self.correction),
                                                self.state, smoke=ok_smoke, **kw)

    def test_stages_exact_snapshot_without_touching_local_tree(self):
        (self.repo / "skill/scripts/bitacora.py").write_text("print('dirty local edit')\n")
        (self.repo / "untracked.txt").write_text("keep\n")
        before = subprocess.run(["git", "status", "--porcelain"], cwd=self.repo, capture_output=True, text=True,
                                check=False).stdout
        manifest = self.prepare()
        self.assertEqual(subprocess.run(["git", "status", "--porcelain"], cwd=self.repo, capture_output=True,
                                        text=True, check=False).stdout, before)
        staged = Path(manifest["bitacora"])
        self.assertEqual(staged.read_text(), "print('staged')\n")
        self.assertFalse((staged.parent.parent.parent / "untracked.txt").exists())
        self.assertTrue(staged.is_absolute())
        self.assertEqual(Path(manifest["root"]), (self.state / "recovery-runtimes" / manifest["source_digest"]).resolve())
        self.assertEqual(sorted(p.name for p in self.state.iterdir()), ["recovery-runtimes"])
        self.assertEqual([p.name for p in (self.state / "recovery-runtimes").iterdir()], [manifest["source_digest"]])
        self.assertEqual(manifest["correction_commits"], [self.correction])

    def test_prepare_is_idempotent_and_detects_tampering(self):
        first = self.prepare()
        self.assertEqual(self.prepare()["source_digest"], first["source_digest"])
        Path(first["bitacora"]).write_text("print('tampered')\n")
        with self.assertRaises(rollout.RolloutError) as ctx:
            self.prepare()
        self.assertEqual(ctx.exception.code, "runtime_tampered")

    def test_refuses_unaccepted_or_mismatched_evidence(self):
        for mutate, code in ((lambda r: r["m6"].update(accepted=False), "m6_not_accepted"),
                             (lambda r: r["audits"][0].update(snapshot="0" * 40), "audit_not_accepted"),
                             (lambda r: r.update(audits=[]), "audit_missing"),
                             (lambda r: r["upgrade"].update(accepted=False), "upgrade_not_accepted"),
                             (lambda r: r.update(correction_commits=["1" * 40]), "correction_commit_not_in_snapshot")):
            data = receipts(self.snapshot, self.correction)
            mutate(data)
            with self.assertRaises(rollout.RolloutError) as ctx:
                rollout.prepare_recovery_runtime(self.repo, self.snapshot, data, self.state, smoke=ok_smoke)
            self.assertEqual(ctx.exception.code, code)
        self.assertFalse((self.state / "recovery-runtimes").exists() and
                         [p for p in (self.state / "recovery-runtimes").iterdir()])

    def test_failed_smoke_leaves_no_stage(self):
        with self.assertRaises(rollout.RolloutError):
            rollout.prepare_recovery_runtime(self.repo, self.snapshot, receipts(self.snapshot, self.correction),
                                             self.state, smoke=lambda stage: {"ok": False})
        self.assertEqual(list((self.state / "recovery-runtimes").iterdir()), [])

    def test_default_smoke_rejects_a_tree_that_cannot_start(self):
        with self.assertRaises(rollout.RolloutError) as ctx:
            rollout.prepare_recovery_runtime(self.repo, self.snapshot, receipts(self.snapshot, self.correction), self.state)
        self.assertEqual(ctx.exception.code, "smoke_failed")

    def test_current_repository_snapshot_passes_isolated_startup_and_import_smoke(self):
        import shutil
        src = self.root / "real"
        shutil.copytree(ROOT, src / "skill/scripts", ignore=shutil.ignore_patterns(
            "tests", "__pycache__", ".git", "node_modules", "*.pyc"))
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=src, check=True)
        git(src, "add", "-A")
        git(src, "commit", "-qm", "real")
        sha = git(src, "rev-parse", "HEAD")
        manifest = rollout.prepare_recovery_runtime(src, sha, receipts(sha, sha), self.state)
        self.assertTrue(manifest["smoke"]["ok"])

    def test_older_runtime_needs_current_schema_evidence(self):
        with self.assertRaises(rollout.RolloutError) as ctx:
            self.prepare(compatibility={"compatible": True, "schemas": ["recovery-cycles/1"], "evidence_ref": "x"})
        self.assertEqual(ctx.exception.code, "incompatible_runtime")
        good = {"compatible": True, "schemas": list(rollout.CURRENT_SCHEMAS), "evidence_ref": "compat-1"}
        self.assertTrue(self.prepare(compatibility=good)["older"])


class FakeHost:
    """Records every machine action; `fail_spawn` simulates a crash between enabling and the new watcher."""

    def __init__(self, root: Path, rdir: Path, ref: str):
        self.calls, self.rdir, self.fail_spawn, self.hold_at, self.held = [], rdir, False, None, False
        self.watch_on, self.stop, self.pids = True, {"stopped": False, "generation": 0}, [4242]
        self.counters = {"counters": "c1", "decisions": "d1"}
        (rdir / "RUN.decisions.jsonl").write_text('{"answer":1}\n')
        (rdir / "RUN.projection.json").write_text("{}\n")
        self.store = root / "m5-recovery.sqlite3"
        self.policy = {"approved": True, "frozen": True, "run_identity": "run-1", "authorization_ref": ref}
        self.live = {"run_identity": "run-1", "plan_id": "REQ-X", "revision": 3, "plan_sha256": "ab" * 32,
                     "identity_current": True, "stop": self.stop, "owner_pending": True, "owner_controls": []}
        self.policy_record = {}

    def sources(self, rdir):
        return {**self.live, "stop": dict(self.stop)}

    def adapter(self, rdir):
        return FakeRecoveryAdapter(self)

    def hold(self, rdir, why):
        self.calls.append("hold")
        self.held, self.hold_at = True, 1000.5
        self.stop = {"stopped": True, "generation": 1000.5}

    def release(self, rdir):
        self.calls.append("release")
        self.held, self.hold_at = False, None
        self.stop = {"stopped": False, "generation": 0}

    def stop_watchers(self):
        self.calls.append("stop_watchers")
        n, self.pids, self.watch_on = len(self.pids), [], False
        return n

    def stop_owner(self):
        self.calls.append("stop_owner")
        return 1

    def spawn(self, bitacora, rdir):
        self.calls.append(f"spawn:{bitacora}")
        if self.fail_spawn:
            raise OSError("crash")
        self.watch_on, self.pids = True, [999]
        return 999

    def store_paths(self, rdir):
        return [rdir / "RUN.decisions.jsonl", rdir / "RUN.projection.json"]

    def host(self) -> rollout.Host:
        return rollout.Host(sources=self.sources, adapter=self.adapter, hold=self.hold, stop_watchers=self.stop_watchers,
                            stop_owner=self.stop_owner, watcher_pids=lambda: list(self.pids),
                            watching=lambda rdir: self.watch_on, spawn_watch=self.spawn, store_paths=self.store_paths,
                            preserved=lambda rdir: dict(self.counters),
                            hold_file=lambda rdir: {"at": self.hold_at} if self.held else {}, release=self.release,
                            wait_watch=1.0)


class FakeRecoveryAdapter:
    """Models the tested M5 lifecycle boundary without opening a production scheduler database."""

    def __init__(self, host):
        self.host = host

    def preview_recovery(self):
        return {"preview_digest": "preview-1"}

    def recovery_status(self):
        marker = rollout._read_json(self.host.rdir / "RUN.recovery-policy.json")
        if marker.get("schema_version") == "recovery-policy-disabled/1":
            return {"mode": "preview", "cycles": []}
        return {"mode": "enabled" if self.host.policy_record else "preview", "cycles": []}

    def enable_diagnostic_recovery(self, run_identity, preview_digest, stop_generation, authorization_ref):
        if (run_identity != self.host.live["run_identity"] or preview_digest != "preview-1"
                or stop_generation != 0 or authorization_ref != "auth-1"):
            return {"enabled": False, "blocker": "stale_authorization"}
        self.host.policy_record = {"run_id": run_identity, "preview_digest": preview_digest,
                                   "authorization_ref": authorization_ref}
        return {"enabled": True}

    def close(self):
        pass


class Activation(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        repo, self.snapshot, correction = make_repo(self.root)
        self.state = self.root / "state"
        self.runtime = rollout.prepare_recovery_runtime(repo, self.snapshot, receipts(self.snapshot, correction),
                                                        self.state, smoke=ok_smoke)
        self.rdir = self.root / "REQ-X"
        self.rdir.mkdir()
        self.fake = FakeHost(self.root, self.rdir, "auth-1")
        self.auth = {"ref": "auth-1", "approved": True, "run_identity": "run-1", "plan_id": "REQ-X", "revision": 3,
                     "plan_sha256": "ab" * 32, "stop_generation": 0, "runtime_digest": self.runtime["source_digest"],
                     "evidence_hashes": self.runtime["evidence_hashes"]}
        self.auth["preview_digest"] = self.fake.adapter(self.rdir).preview_recovery()["preview_digest"]

    def activate(self, auth=None, fake=None):
        fake = fake or self.fake
        return rollout.activate_recovery_runtime("p", "REQ-X", self.rdir, self.runtime, auth or self.auth, self.state,
                                                 host=fake.host())

    def refused(self, code, auth=None):
        with self.assertRaises(rollout.RolloutError) as ctx:
            self.activate(auth)
        self.assertEqual(ctx.exception.code, code)
        self.assertEqual(self.fake.calls, [], "a refused activation must not touch the machine")

    def test_activation_replaces_watcher_with_staged_runtime_and_preserves_state(self):
        journal = self.activate()
        self.assertEqual(self.fake.calls, ["hold", "stop_watchers", "stop_owner", "release", f"spawn:{self.runtime['bitacora']}"])
        self.assertEqual(journal["state"], "active")
        sources = [r["source"] for r in journal["receipts"]]
        self.assertEqual(sources, ["M1", "M3", "M6", "host"])
        self.assertTrue(all(r["schema_version"] == rollout.RECEIPT_SCHEMA for r in journal["receipts"]))
        self.assertEqual(journal["receipts"][1]["correction_commits"], self.runtime["correction_commits"])
        self.assertEqual(journal["receipts"][2]["audit_snapshots"][0]["snapshot"], self.snapshot)
        binding = json.loads((self.rdir / rollout.BINDING).read_text())
        self.assertEqual((binding["runtime_digest"], binding["bitacora"]), (self.runtime["source_digest"], self.runtime["bitacora"]))
        backup = Path(journal["phases"]["backup"]["path"])
        self.assertEqual((backup / "RUN.decisions.jsonl").read_text(), '{"answer":1}\n')
        self.assertNotIn("preserved_drift", journal)
        self.assertEqual((self.rdir / "RUN.decisions.jsonl").read_text(), '{"answer":1}\n')
        self.assertEqual(self.fake.adapter(self.rdir).recovery_status()["mode"], "enabled")
        self.assertEqual(self.activate()["state"], "active")              # replay is a no-op
        self.assertEqual(self.fake.calls.count("hold"), 1)

    def test_refusals_precede_any_machine_action(self):
        self.refused("missing_authorization", {**self.auth, "approved": False})
        self.refused("evidence_mismatch", {**self.auth, "evidence_hashes": {"m6": "x"}})
        self.refused("stale_target", {**self.auth, "plan_sha256": "cd" * 32})
        self.refused("stale_target", {**self.auth, "revision": 4})
        self.refused("stale_stop_generation", {**self.auth, "stop_generation": 5})
        self.refused("stale_preview", {**self.auth, "preview_digest": "0" * 64})
        self.fake.stop = {"stopped": True, "generation": 7}
        self.refused("stop_active")
        self.assertFalse((self.rdir / rollout.JOURNAL).exists())

    def test_unverified_watch_lock_is_refused(self):
        self.fake.pids = []
        self.refused("unverified_watch_lock")

    def test_crash_adoption_reuses_the_same_activation_once(self):
        self.fake.fail_spawn = True
        with self.assertRaises(OSError):
            self.activate()
        journal = json.loads((self.rdir / rollout.JOURNAL).read_text())
        self.assertEqual(journal["state"], "activating")
        self.assertIn("enabled", journal["phases"])
        self.assertNotIn("started", journal["phases"])
        with self.assertRaises(rollout.RolloutError) as ctx:               # one authorization: no other activation
            self.activate({**self.auth, "ref": "auth-2"})
        self.assertEqual(ctx.exception.code, "authorization_consumed")
        self.fake.fail_spawn, self.fake.watch_on = False, False
        self.fake.pids = []
        done = self.activate()
        self.assertEqual(done["state"], "active")
        self.assertTrue(done["receipts"][3]["adopted"])
        self.assertEqual([c for c in self.fake.calls if c in ("hold", "stop_owner", "release")], ["hold", "stop_owner", "release"])
        self.assertEqual(sum(c.startswith("spawn") for c in self.fake.calls), 2)   # failed try + adopted start
        self.assertEqual(self.fake.adapter(self.rdir).recovery_status()["cycles"], [])

    def test_crash_between_hold_and_backup_resumes_without_second_hold(self):
        self.fake.stop_owner = lambda: (_ for _ in ()).throw(RuntimeError("crash"))
        with self.assertRaises(RuntimeError):
            self.activate()
        del self.fake.stop_owner
        self.activate()
        self.assertEqual(self.fake.calls.count("hold"), 1)

    def test_a_stop_during_activation_wins(self):
        self.fake.fail_spawn = True
        with self.assertRaises(OSError):
            self.activate()
        self.fake.stop = {"stopped": True, "generation": 2000.0}           # owner presses stop after the release
        self.fake.fail_spawn = False
        with self.assertRaises(rollout.RolloutError) as ctx:
            self.activate()
        self.assertEqual(ctx.exception.code, "stop_won")
        self.assertEqual(sum(c.startswith("spawn") for c in self.fake.calls), 1)

    def test_overridden_hold_stops_activation(self):
        orig = self.fake.stop_owner
        def steal():
            self.fake.hold_at = 5555.0                                     # someone else rewrote the hold
            return orig()
        self.fake.stop_owner = steal
        with self.assertRaises(rollout.RolloutError) as ctx:
            self.activate()
        self.assertEqual(ctx.exception.code, "stop_won")
        self.assertNotIn("release", self.fake.calls)

    def test_counter_or_decision_drift_is_reported_not_hidden(self):
        orig = self.fake.spawn
        def drift(b, r):
            self.fake.counters = {"counters": "c2", "decisions": "d1"}
            return orig(b, r)
        self.fake.spawn = drift
        self.assertEqual(self.activate()["preserved_drift"]["after"]["counters"], "c2")

    def test_older_runtime_is_refused_without_compatibility(self):
        runtime = {**self.runtime, "older": True, "compatibility": {"compatible": True, "schemas": []}}
        with self.assertRaises(rollout.RolloutError) as ctx:
            rollout._check_authorization(self.auth, runtime, self.fake.sources(self.rdir), False, {})
        self.assertEqual(ctx.exception.code, "incompatible_runtime")

    def test_rollback_holds_and_disables_without_restoring_anything(self):
        self.activate()
        before = cycles.Ledger(self.fake.store.with_suffix(".cycles.json")).read()
        with open(self.rdir / "RUN.decisions.jsonl", "a") as handle:
            handle.write('{"answer":2}\n')                                  # a newer authoritative outcome
        self.fake.calls.clear()
        journal = rollout.rollback_recovery_runtime("p", "REQ-X", self.rdir, "operator choice", self.state,
                                                    host=self.fake.host())
        self.assertEqual(journal["state"], "rolled_back")
        self.assertFalse(journal["rollback"]["backup_restored"])
        self.assertEqual(self.fake.calls[0], "hold")
        self.assertNotIn("release", self.fake.calls)
        self.assertTrue(self.fake.held)
        self.assertEqual((self.rdir / "RUN.decisions.jsonl").read_text(), '{"answer":1}\n{"answer":2}\n')
        self.assertEqual(self.fake.adapter(self.rdir).recovery_status()["mode"], "preview")   # even with a frozen policy
        self.assertEqual(cycles.Ledger(self.fake.store.with_suffix(".cycles.json")).read()["cycles"], before["cycles"])
        self.assertTrue(Path(self.runtime["bitacora"]).exists())
        with self.assertRaises(rollout.RolloutError) as ctx:
            self.activate()
        self.assertEqual(ctx.exception.code, "rolled_back")


if __name__ == "__main__":
    unittest.main()
