"""Shared scaffolding for the executor adapter and integration tests: fake provider binaries on PATH, an isolated
bitácora root with profiles and projects, git repositories, and an approved (frozen) plan in a requirement folder."""
from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))
HERE = Path(__file__).resolve().parent
PROVIDER = HERE / "fake_providers" / "provider.py"

import bt_profiles
import bt_scheduler_adapter as sched
import bt_scheduler_executor_adapter as adapter

core = sched.core


def git(cwd, *args):
    done = subprocess.run(["git", "-c", "user.name=T", "-c", "user.email=t@t", "-c", "core.hooksPath=/dev/null", *args],
                          cwd=str(cwd), capture_output=True, text=True, check=False)
    if done.returncode:
        raise RuntimeError(f"git {args}: {done.stderr}")
    return done.stdout.strip()


def make_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q", "-b", "main")
    (path / "README.md").write_text("original\n")
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", "initial")
    return path


def task(tid, title, after=(), repo="app", **extra):
    return {"id": tid, "milestone_id": "M1", "title": f"{title} SCENARIO:{extra.pop('scenario', 'ok')}",
            "objective": f"do {tid}", "repository": repo, "after": list(after), "expected_paths": [f"{tid}/**"],
            "shared_resources": [], "acceptance_criteria": [f"{tid} works"],
            "verification": [{"type": "command", "value": "true", "purpose": "smoke"}], **extra}


def plan_text(tasks, plan_id="REQ-042", revision=1):
    return json.dumps({"schema_version": "1.0.0", "plan_id": plan_id, "revision": revision, "tasks": tasks}, indent=1) + "\n"


def freeze(rdir: Path, text: str, revision: int = 1) -> str:
    folder = rdir / "plan-revisions"
    folder.mkdir(exist_ok=True)
    (folder / f"PLAN.r{revision}.json").write_text(text, encoding="utf-8")
    manifest = json.loads((folder / "MANIFEST.json").read_text()) if (folder / "MANIFEST.json").exists() \
        else {"schema": 1, "revisions": []}
    digest = hashlib.sha256(text.encode()).hexdigest()
    manifest["revisions"].append({"revision": revision, "sha256": digest, "frozen_at": "2026-10-14T00:00:00+00:00"})
    (folder / "MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
    return digest


class Verifier:
    """An independent verifier stub: accepts every attempt whose executor reported it stopped, with evidence."""

    def __init__(self, accept=True):
        self.accept, self.orders = accept, []
        self.scheduler = None

    def request(self, order):
        self.orders.append(order)
        if self.scheduler is not None:
            self.scheduler.submit_verdict(core.Verdict(
                verdict_id=f"v-{order.attempt_id}", plan_id=order.plan_id, revision=order.revision, task_id=order.task_id,
                attempt_id=order.attempt_id, accepted=self.accept, verifier="independent-test-verifier",
                evidence="stub verification passed" if self.accept else "stub rejected", token=order.token))
        return core.Ack("accepted")


class World(unittest.TestCase):
    """An isolated bitácora root (profiles, projects), fake provider binaries first on PATH, repositories and a plan."""
    maxDiff = None

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="m3-integ-"))
        self.addCleanup(self.cleanup)
        self.root = self.tmp / "bitacora"
        for project, work in (("proj", False), ("workproj", True)):
            (self.root / project).mkdir(parents=True)
            (self.root / project / "project.json").write_text(json.dumps({"work": work}))
        for target, value in (("bt_profiles.ROOT", self.root), ("bt_profiles.STATE", self.root / ".state")):
            patcher = patch(target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        bt_profiles.add("claude-personal", "claude", {"CLAUDE_CONFIG_DIR": str(self.tmp / "claude-a")})
        bt_profiles.add("claude-work", "claude", {"CLAUDE_CONFIG_DIR": str(self.tmp / "claude-w")}, work_only=True)
        bt_profiles.add("codex-1", "codex", {"CODEX_HOME": str(self.tmp / "codex-1")})
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        for exe in ("claude", "codex", "agy"):
            path = self.bin / exe
            path.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{PROVIDER}" {exe} "$@"\n')
            path.chmod(path.stat().st_mode | stat.S_IEXEC)
        self.record = self.tmp / "record.jsonl"
        env = {"PATH": f"{self.bin}:{os.environ['PATH']}", "FAKE_RECORD": str(self.record), "OTHER_SECRET": "leak-me",
               "CLAUDE_CONFIG_DIR": str(self.tmp / "inherited-claude"), "CODEX_HOME": str(self.tmp / "inherited-codex")}
        patcher = patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.repos = {"app": make_repo(self.tmp / "app"), "docs": make_repo(self.tmp / "docs")}
        self.rdir = self.tmp / "REQ-042-demo"
        self.rdir.mkdir()
        self.wirings = []

    def cleanup(self):
        for w in self.wirings:
            try:
                w.close()
            except Exception:
                pass
        for entry in Path("/proc").iterdir():
            if entry.name.isdigit():
                try:
                    if str(self.tmp) in (entry / "cmdline").read_bytes().decode("utf-8", "replace") or \
                            os.readlink(entry / "cwd").startswith(str(self.tmp)):
                        os.kill(int(entry.name), 9)
                except OSError:
                    pass
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def approve(self, tasks, revision=1):
        text = plan_text(tasks, revision=revision)
        self.sha = freeze(self.rdir, text, revision)
        return text

    def wire(self, reference, *, parallel=3, verifier=None, executor_config=None, max_attempts=1, **kw):
        from bt_scheduler_executor import Config
        verifier = verifier or Verifier()
        wiring = adapter.wire(self.rdir, project=kw.pop("project", "proj"), assignment=adapter.PinnedRoute(reference),
                              verification=verifier, repos=self.repos, default_repository="app",
                              config=core.Config(max_parallel_tasks=parallel, max_attempts=max_attempts),
                              executor_config=executor_config or Config(poll_seconds=0.05, grace_seconds=1.0,
                                                                        timeout_seconds=60, heartbeat_seconds=3600),
                              **kw)
        verifier.scheduler = wiring.scheduler
        self.verifier = verifier
        self.wirings.append(wiring)
        return wiring

    def records(self):
        if not self.record.exists():
            return []
        return [json.loads(line) for line in self.record.read_text().splitlines() if line.strip()]

    def run_until(self, wiring, predicate, timeout=60.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            wiring.scheduler.step()
            if predicate(wiring.scheduler.snapshot()):
                return True
            time.sleep(0.05)
        return False
