"""D-270 (2026-10-31, after `/home` reached 100 %): the scratch D-266 left uncollected. The legacy executor's worktrees
(68 GB: its hourly retention skipped all 262 attempts), the «Probar» copies (23 GB, no GC) and the M6 dependency cache
(2.7 GB, never pruned) are reclaimed by one periodic engine pass (`bt_durable.gc_scratch`, `bt-durable gc-scratch`) that
never discards unpreserved work; test labs default to a tmpfs instead of `$TMPDIR` on /home.

    PYTHONPATH=skill/scripts:skill/scripts/tests python -m unittest test_durable_gc_scratch
"""
from __future__ import annotations

import atexit
import contextlib
import datetime as dt
import fcntl
import importlib.util
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
# the stdlib modules read the machine config of BITACORA_ROOT: never the real bitácora in a test
if not os.environ.get("BITACORA_ROOT"):
    os.environ["BITACORA_ROOT"] = tempfile.mkdtemp(prefix="bt-gc-root-")
    atexit.register(shutil.rmtree, os.environ["BITACORA_ROOT"], True)

import durable_support
from bt_durable import gc_deps, gc_scratch, gc_verify
from bt_scheduler_quality import sandbox_provision

NOW = 1_800_000_000.0
DAY = 86400


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                          capture_output=True, text=True, check=True).stdout.strip()


def make_repo(path: Path, files: dict[str, str] | None = None) -> Path:
    path.mkdir(parents=True)
    git(path, "init", "-q", "-b", "main")
    (path / ".gitignore").write_text("node_modules/\n.next/\n")
    for name, text in (files or {"README.md": "app\n"}).items():
        (path / name).parent.mkdir(parents=True, exist_ok=True)
        (path / name).write_text(text)
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", "initial")
    return path


def age(path: Path, seconds_ago: float) -> None:
    os.utime(path, (NOW - seconds_ago, NOW - seconds_ago), follow_symlinks=False)


class FakeProc:
    """A /proc with the processes a test needs: `cwd` links and `environ` files, owned by this user."""

    def __init__(self, base: Path):
        self.base = base
        base.mkdir(parents=True, exist_ok=True)
        self.next = 100

    def process(self, *, cwd: Path | None = None, environ: dict[str, str] | None = None) -> None:
        entry = self.base / str(self.next)
        self.next += 1
        entry.mkdir()
        (entry / "cwd").symlink_to(cwd or "/")
        (entry / "environ").write_bytes(b"\0".join(f"{k}={v}".encode() for k, v in (environ or {}).items()))


# --------------------------------------------------------------------------------------------- «Probar» copies
class VerifyCopies(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="bt-gc-verify-", dir=durable_support.lab_dir()))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = make_repo(self.tmp / "app")
        self.head = git(self.repo, "rev-parse", "HEAD")
        self.base = self.tmp / "verify"
        self.req = self.base / "proj" / "REQ-001"
        self.req.mkdir(parents=True)
        self.proc = FakeProc(self.tmp / "proc")
        self.facts = gc_verify.ReqFacts()
        self.root = self.tmp / "bitacora"
        (self.root / "proj" / "requirements" / "REQ-001-thing").mkdir(parents=True)

    def copy(self, slug: str, *, touched: float = 2 * DAY) -> Path:
        target = self.req / slug
        git(self.repo, "worktree", "add", "-q", "--detach", str(target), self.head)
        (target / "node_modules").mkdir()
        (target / "node_modules" / "dep.js").write_text("x" * 70000)
        for suffix in gc_verify.SIDECARS:
            side = Path(f"{target}{suffix}")
            side.mkdir() if suffix == ".logs" else side.write_text("{}" if suffix == ".servers.json" else "")
            age(side, touched)
        age(target, touched)
        return target

    def collect(self, apply=True, grace=3 * DAY, alive=frozenset(), **kw):
        return {Path(r["path"]).name: r for r in gc_verify.collect(
            self.base, self.root, apply=apply, grace_seconds=grace, now=NOW, proc=self.proc.base,
            session_alive=lambda name: name in alive, facts_for=lambda rdir: self.facts, **kw)}

    def registered(self) -> list[str]:
        return [line for line in git(self.repo, "worktree", "list", "--porcelain").splitlines()
                if line.startswith("worktree ") and str(self.base) in line]

    def test_a_superseded_version_goes_with_its_sidecars_the_latest_undecided_one_stays(self):
        old, new = self.copy("SP-8-v1"), self.copy("SP-8-v2")
        self.facts.latest = {"SP-8": 2}
        dry = self.collect(apply=False)
        self.assertEqual((dry["SP-8-v1"]["action"], dry["SP-8-v1"]["reason"]), ("remove", "superseded"))
        self.assertGreaterEqual(dry["SP-8-v1"]["bytes"], 65536)
        self.assertTrue(old.exists())
        rows = self.collect()
        self.assertEqual((rows["SP-8-v1"]["action"], rows["SP-8-v2"]["action"], rows["SP-8-v2"]["reason"]),
                         ("removed", "keep", "latest"))
        self.assertFalse(old.exists())
        self.assertEqual(sorted(p.name for p in self.req.iterdir() if p.name.startswith("SP-8-v1")), [])
        self.assertEqual(self.registered(), [f"worktree {new}"])                 # git forgot the removed copy
        self.assertTrue(new.exists())

    def test_a_decided_version_goes_after_the_grace_period(self):
        self.copy("SP-3-v3")
        self.facts.latest = {"SP-3": 3}
        decided = dt.datetime.fromtimestamp(NOW - 2 * DAY).astimezone().isoformat()
        self.facts.decisions = {"SP-3": {"decision": "rejected", "version": 3, "at": decided}}
        self.assertEqual(self.collect(apply=False)["SP-3-v3"]["reason"], "latest")         # 2 days < 3
        self.assertEqual(self.collect(grace=DAY)["SP-3-v3"]["action"], "removed")

    def test_a_running_server_or_a_held_lock_keeps_any_copy(self):
        for slug in ("SP-1-v1", "SP-2-v1", "SP-4-v1", "SP-5-v1"):
            self.copy(slug)
        self.facts.latest = {"SP-1": 2, "SP-2": 2, "SP-4": 2, "SP-5": 2}
        self.proc.process(environ={"BITACORA_VERIFY_ID": "proj/REQ-001/SP-1-v1"})
        self.proc.process(cwd=self.req / "SP-2-v1" / "node_modules")
        with open(self.req / "SP-5-v1.lock", "a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            rows = self.collect(alive={"bv-proj-REQ-001-SP-4-v1"})
        self.assertEqual([rows[s]["reason"] for s in ("SP-1-v1", "SP-2-v1", "SP-4-v1")], ["server-running"] * 3)
        self.assertEqual((rows["SP-5-v1"]["action"], rows["SP-5-v1"]["detail"]), ("failed", "locked"))
        self.assertTrue(all((self.req / s).exists() for s in ("SP-1-v1", "SP-2-v1", "SP-4-v1", "SP-5-v1")))

    def test_edits_recent_use_unknown_names_and_unknown_requirements_are_kept(self):
        edited = self.copy("SP-6-v1")
        (edited / "README.md").write_text("owner edit while trying it\n")
        self.copy("SP-7-v1", touched=60)
        (self.req / "SP-1-v1-node_modules.shared-preserved-20261028").mkdir()
        other = self.base / "proj" / "REQ-002"
        other.mkdir()
        (other / "SP-1-v1").mkdir()
        self.facts.latest = {"SP-6": 2, "SP-7": 2}
        rows = self.collect()
        self.assertEqual((rows["SP-6-v1"]["reason"], rows["SP-6-v1"]["detail"]), ("local-edits", "README.md"))
        self.assertEqual(rows["SP-7-v1"]["reason"], "recent")
        self.assertEqual(rows["SP-1-v1-node_modules.shared-preserved-20261028"]["reason"], "unknown")
        self.assertEqual(rows["SP-1-v1"]["reason"], "unknown")              # REQ-002 has no folder in the bitácora
        self.assertTrue(edited.exists() and (other / "SP-1-v1").exists())

    def test_a_task_copy_lives_while_its_manual_decision_is_open(self):
        self.copy("T10.5-a1-098ef7ce")
        self.facts.open_attempts = {"proj:REQ-001:r3:T10.5:k2-a1-098ef7ce"}
        self.assertEqual(self.collect()["T10.5-a1-098ef7ce"]["reason"], "decision-open")
        self.facts.open_attempts = set()
        self.assertEqual(self.collect(grace=3 * DAY)["T10.5-a1-098ef7ce"]["reason"], "grace")
        self.assertEqual(self.collect(grace=DAY)["T10.5-a1-098ef7ce"]["action"], "removed")


# ----------------------------------------------------------------------------------------------- M6 deps cache
class DepsCache(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="bt-gc-deps-", dir=durable_support.lab_dir()))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.cache = self.tmp / "m6-deps"
        self.cache.mkdir()

    def entry(self, key: str, *, used_ago: float, size: int = 100_000) -> Path:
        target = self.cache / key
        (target / "node_modules").mkdir(parents=True)
        (target / "node_modules" / "blob").write_bytes(b"x" * size)
        (target / sandbox_provision.READY).write_text(key + "\n")
        age(target / sandbox_provision.READY, used_ago)
        return target

    def collect(self, apply=True, **kw):
        kw.setdefault("protected", set())
        kw.setdefault("max_bytes", 10 ** 12)
        kw.setdefault("max_age_seconds", 14 * DAY)
        kw.setdefault("min_idle_seconds", 12 * 3600)
        return {r["key"] or Path(r["path"]).name: r for r in gc_deps.collect(self.cache, apply=apply, now=NOW, **kw)}

    def test_least_recently_used_go_first_until_the_cache_fits(self):
        for key, ago in (("a" * 32, 5 * DAY), ("b" * 32, 3 * DAY), ("c" * 32, 1 * DAY)):
            self.entry(key, used_ago=ago)
        rows = self.collect(apply=False, max_bytes=250_000)
        self.assertEqual([rows[k * 32]["action"] for k in "abc"], ["remove", "keep", "keep"])
        self.assertEqual(rows["a" * 32]["reason"], "over-cap")
        rows = self.collect(max_bytes=150_000)
        self.assertEqual([rows[k * 32]["action"] for k in "abc"], ["removed", "removed", "keep"])
        self.assertEqual(sorted(p.name for p in self.cache.iterdir()), ["c" * 32])

    def test_live_tips_recent_use_and_unknown_folders_are_kept_old_entries_and_dead_builds_go(self):
        self.entry("a" * 32, used_ago=30 * DAY)
        self.entry("b" * 32, used_ago=30 * DAY)
        self.entry("c" * 32, used_ago=3600)
        (self.cache / "notes").mkdir()
        dead = self.cache / ("d" * 32 + ".x1y2")
        dead.mkdir()
        age(dead, 2 * DAY)
        building = self.cache / ("e" * 32 + ".k9")
        building.mkdir()
        age(building, 60)
        rows = self.collect(protected={"b" * 32}, max_bytes=0)
        self.assertEqual({k: (r["action"], r["reason"]) for k, r in rows.items()}, {
            "a" * 32: ("removed", "unused"), "b" * 32: ("keep", "live-run"), "c" * 32: ("keep", "recent"),
            "notes": ("keep", "unknown"), "d" * 32: ("removed", "abandoned-build"), "e" * 32: ("keep", "building")})

    def test_the_keys_of_a_live_runs_tips_are_the_keys_provision_uses(self):
        files = {"package.json": '{"name":"app"}', "package-lock.json": '{"lockfileVersion":3}',
                 "web/package.json": '{"name":"web"}', "web/package-lock.json": '{"v":1}',
                 "node_modules/x/package.json": "{}", "node_modules/x/package-lock.json": "{}"}
        repo = make_repo(self.tmp / "app", files)
        tip = git(repo, "rev-parse", "HEAD")
        git(repo, "update-ref", "refs/bt/subplan/proj/REQ-001/r4/app/SP-1", tip)
        git(repo, "update-ref", "refs/bt/line/proj/REQ-001/r4/app-base", tip)
        state = self.tmp / "state"
        (state / "projections" / "proj").mkdir(parents=True)
        for rev, status in ((4, "PENDING"), (3, "CANCELLED")):
            (state / "projections" / "proj" / f"REQ-001-r{rev}.json").write_text(json.dumps(
                {"run_id": f"proj:REQ-001:r{rev}", "workflow_status": status, "status": "running"}))
        self.assertEqual(gc_deps.live_runs(state), [("proj", "REQ-001", 4)])
        keys = gc_deps.protected_keys(state, lambda project: [repo])
        self.assertEqual(keys, {sandbox_provision.key_of(repo), sandbox_provision.key_of(repo / "web")})

    def test_a_reused_entry_records_its_use(self):
        package = self.tmp / "pkg"
        package.mkdir()
        (package / "package.json").write_text("{}")
        (package / "package-lock.json").write_text("{}")
        target = self.entry(sandbox_provision.key_of(package), used_ago=10 * DAY)
        with patch.object(sandbox_provision.shutil, "which", return_value="/usr/bin/true"):
            found = sandbox_provision.provision(package, root=self.cache)
        self.assertEqual(found, (target / "node_modules").resolve())
        self.assertGreater((target / sandbox_provision.READY).stat().st_mtime, time.time() - 60)


# ------------------------------------------------------------------------------------- legacy executor (pass)
def _executor_support():
    spec = importlib.util.spec_from_file_location(
        "executor_test_support", HERE.parent / "bt_scheduler_executor" / "tests" / "support.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ThePass(unittest.TestCase):
    """`gc_scratch.run_pass` / `bt-durable gc-scratch`: every area, per area counts and bytes, dry run first."""

    def setUp(self):
        from bt_scheduler_executor import handoff
        from bt_scheduler_executor.retention import RETENTION_SECONDS
        from bt_scheduler_executor.workspace import GitWorkspaces, dirname_of
        support = _executor_support()
        self.tmp = Path(tempfile.mkdtemp(prefix="bt-gc-pass-", dir=durable_support.lab_dir()))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.state = self.tmp / "state" / "durable"
        self.state.mkdir(parents=True)
        repo = support.make_repo(self.tmp / "repo")
        (repo / ".gitignore").write_text("node_modules/\nreports/\n")
        support.git(repo, "add", ".gitignore")
        support.git(repo, "commit", "-qm", "ignore")
        run = self.tmp / "state" / "executor" / "proj-REQ-001-r1-c1da55c1-1792409909290"
        request = support.order(1)
        workspace = GitWorkspaces(run / "ws", {"main": repo}).allocate(request)
        self.tree = Path(workspace.path)
        (self.tree / "README.md").write_text("agent change\n")
        dirname = dirname_of(request.attempt_id)
        saved = handoff.capture(workspace, run / "attempts" / dirname, dirname=dirname, attempt_id=request.attempt_id,
                                when=time.time() - RETENTION_SECONDS - 60, patch_max=2**20)
        (self.tree / "reports").mkdir()
        (self.tree / "reports" / "results.json").write_text('{"passed": 3}')      # what blocked 49 checkouts
        (self.tree / "node_modules").mkdir()
        (self.tree / "node_modules" / "dep.js").write_text("y" * 70000)
        (run / "executor.lock").touch()
        with sqlite3.connect(run / "ledger.db") as db:
            db.execute("CREATE TABLE attempts(attempt_id, dirname, state, ended_at, workspace, handoff)")
            db.execute("INSERT INTO attempts VALUES (?,?,?,?,?,?)", (
                request.attempt_id, dirname, "finished", time.time() - RETENTION_SECONDS - 1,
                json.dumps(asdict(workspace)), json.dumps(saved)))
        db.close()
        self.run_dir, self.dirname = run, dirname
        self.verify = self.tmp / "verify"
        (self.verify / "proj" / "REQ-001").mkdir(parents=True)
        self.deps = self.tmp / "deps"
        (self.deps / ("f" * 32) / "node_modules").mkdir(parents=True)
        (self.deps / ("f" * 32) / ".m6-ready").write_text("f")
        age(self.deps / ("f" * 32) / ".m6-ready", 400 * DAY)
        patcher = patch.dict(os.environ, {"BITACORA_VERIFY_DIR": str(self.verify), "M6_DEPS_CACHE": str(self.deps)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_dry_run_then_apply_reclaims_the_preserved_checkout_and_the_stale_cache(self):
        events = []
        reports = gc_scratch.run_pass(self.state, self.tmp / "bitacora", apply=False,
                                      emit=lambda event, **f: events.append((event, f)))
        summary = {r.area: r.summary() for r in reports}
        self.assertEqual(summary["legacy_executor"]["counts"], {"eligible": 1})
        self.assertGreaterEqual(summary["legacy_executor"]["bytes"], 65536)
        self.assertEqual(summary["deps_cache"]["counts"], {"remove": 1})
        self.assertEqual(summary["verify_copies"]["counts"], {})
        self.assertTrue(self.tree.exists())
        self.assertEqual([e for e, _ in events], ["disk_gc_area"] * 3)
        text = gc_scratch.render(reports)
        self.assertIn("eligible (dry run): 1", text)
        self.assertIn("nothing was removed", text)
        events.clear()
        reports = gc_scratch.run_pass(self.state, self.tmp / "bitacora", apply=True,
                                      emit=lambda event, **f: events.append((event, f)))
        self.assertEqual({r.area: r.counts() for r in reports},
                         {"legacy_executor": {"removed": 1}, "verify_copies": {}, "deps_cache": {"removed": 1}})
        self.assertFalse(self.tree.exists())
        archive = self.run_dir / "attempts" / self.dirname / "retained-ignored.tar.gz"
        self.assertTrue(archive.is_file())
        removed = [f for e, f in events if e == "disk_gc_removed"]
        self.assertEqual(sorted(f["area"] for f in removed), ["deps_cache", "legacy_executor"])
        self.assertEqual(next(f for f in removed if f["area"] == "legacy_executor")["archive"], str(archive))
        again = gc_scratch.run_pass(self.state, self.tmp / "bitacora", apply=True)
        self.assertEqual(again[0].counts(), {"settled": 1})                     # recorded once in the index
        self.assertEqual(gc_scratch.run_pass(self.state, self.tmp / "bitacora", apply=True)[0].counts(), {})

    def test_switches_and_the_folders_outside_the_bitacora(self):
        reports = gc_scratch.run_pass(self.state, self.tmp / "bitacora", apply=True,
                                      conf={"legacy_executor": False, "deps_cache": False})
        self.assertEqual([r.skipped for r in reports], ["disk_gc.legacy_executor is off", "", "disk_gc.deps_cache is off"])
        self.assertTrue(self.tree.exists())
        with patch.dict(os.environ, {"BITACORA_VERIFY_DIR": "", "M6_DEPS_CACHE": ""}), \
                patch("bt_core.is_live_root", return_value=False):
            reports = gc_scratch.run_pass(self.state, self.tmp / "bitacora", apply=False, areas=("verify_copies",
                                                                                                  "deps_cache"))
        self.assertEqual([r.skipped for r in reports], ["not the live bitácora"] * 2)   # a lab never reaches ~/.cache

    def test_the_command_is_a_dry_run_unless_apply(self):
        from bt_durable import cli
        from bt_durable.settings import EngineConfig
        cfg = EngineConfig(system_database_url="sqlite:///unused", state_dir=self.state)

        def run_cli(*argv):
            out, err = io.StringIO(), io.StringIO()
            with patch.object(cli, "engine_config", return_value=cfg), contextlib.redirect_stdout(out), \
                    contextlib.redirect_stderr(err):
                code = cli.main(["gc-scratch", *argv])
            return code, json.loads(out.getvalue()), err.getvalue()
        code, out, text = run_cli("--area", "legacy_executor", "--json")
        self.assertIn("eligible (dry run): 1", text)
        self.assertEqual((code, [a["area"] for a in out], out[0]["counts"]), (0, ["legacy_executor"], {"eligible": 1}))
        self.assertEqual(out[0]["items"][0]["attempt_id"], "att-0001")
        self.assertTrue(self.tree.exists())
        code, out, _ = run_cli("--apply", "--no-size")
        self.assertEqual((code, out[0]["counts"], out[0]["bytes"]), (0, {"removed": 1}, None))
        self.assertFalse(self.tree.exists())
        telemetry = [json.loads(line) for line in (self.state / "telemetry.jsonl").read_text().splitlines()]
        self.assertIn("disk_gc_removed", [t.get("event") for t in telemetry])

    def test_the_engine_runs_it_in_the_background_when_enabled(self):
        events = []
        with patch.object(gc_scratch, "settings", return_value={**gc_scratch.settings(), "enabled": False}):
            self.assertIsNone(gc_scratch.start_background(self.state, self.tmp, lambda e, **f: events.append(e)))
        thread = gc_scratch.start_background(self.state, self.tmp, lambda e, **f: events.append(e), wait=True)
        self.assertIsNotNone(thread)
        self.assertIn("disk_gc_removed", events)
        self.assertFalse(self.tree.exists())


class EngineLoop(unittest.TestCase):
    """The engine loop runs each periodic pass on its own clock. Until D-270 the reaper's pass (every 30 s) also reset
    the worktree pass's clock, so D-266's collection (every 600 s) never ran in the engine."""

    def test_every_pass_keeps_its_own_cadence(self):
        import threading

        from bt_durable import restarts, service
        from bt_durable.settings import EngineConfig
        calls: dict[str, int] = {}

        def count(name):
            def call(*args, **kwargs):
                calls[name] = calls.get(name, 0) + 1
            return call
        stop = threading.Event()
        cfg = EngineConfig(system_database_url="sqlite:///unused", state_dir=Path(tempfile.mkdtemp(dir=durable_support.lab_dir())))
        self.addCleanup(shutil.rmtree, cfg.state_dir, True)
        projector = type("P", (), {"refresh": lambda self: None})
        with patch.multiple(service, reap_once=count("reap"), _drain_joins=count("joins"), _heal_decisions=count("heal"),
                            _deliver_held_notices=count("notices"), collect_worktrees=count("worktrees"),
                            collect_disk=count("disk"), _disk_interval=lambda: 0.7), \
                patch.object(service.engine, "start"), patch.object(service.engine, "stop"), \
                patch("bt_durable.remote.write_marker"), patch("bt_durable.projection.EngineProjector",
                                                               lambda dbos: projector()), \
                patch.object(restarts, "previous_stop", return_value=None), patch.object(restarts, "begin"), \
                patch.object(restarts, "record_clean_stop"):
            timer = threading.Timer(2.6, stop.set)
            timer.start()
            service._loop(cfg, None, stop, reap_seconds=0.2, project_seconds=0.2, marker=cfg.state_dir / "m.json",
                          gc_seconds=0.5)
        self.assertGreaterEqual(calls.get("reap", 0), 6)
        self.assertGreaterEqual(calls.get("worktrees", 0), 3)          # was 0: reset by every reaper pass
        self.assertGreaterEqual(calls.get("disk", 0), 2)


class Settings(unittest.TestCase):
    def test_defaults(self):
        conf = gc_scratch.settings()
        self.assertEqual((conf["enabled"], conf["interval_min"], conf["legacy_archive_mb"], conf["verify_grace_days"],
                          conf["deps_cache_max_gb"]), (True, 60, 32, 3, 4))
        self.assertEqual(gc_scratch.interval_seconds(), 3600.0)


class LabDir(unittest.TestCase):
    """Labs and test temp folders default to a tmpfs, not `$TMPDIR` (on /home, pinned by snapshots)."""

    def test_bt_lab_dir_wins_then_a_fast_tmp_then_the_inherited_one(self):
        with patch.dict(os.environ, {"BT_LAB_DIR": "/somewhere"}):
            self.assertEqual(durable_support.lab_dir(), "/somewhere")
        with patch.dict(os.environ, {"BT_LAB_DIR": "", "BT_REGRESS_TMPDIR": "/dev/shm"}):
            self.assertEqual(durable_support.lab_dir(), "/dev/shm")
        with patch.dict(os.environ, {"BT_LAB_DIR": "", "BT_REGRESS_TMPDIR": ""}):
            self.assertIsNone(durable_support.lab_dir())
        env = {k: v for k, v in os.environ.items() if k not in ("BT_LAB_DIR", "BT_REGRESS_TMPDIR")}
        with patch.dict(os.environ, env, clear=True), patch("bt_regress.fast_tmp", return_value="/tmp"):
            self.assertEqual(durable_support.lab_dir(), "/tmp")
            lab = durable_support.Lab()
            self.addCleanup(shutil.rmtree, lab.root, True)
            self.assertEqual(lab.root.parent, Path("/tmp"))


if __name__ == "__main__":
    unittest.main()
