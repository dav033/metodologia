"""End-to-end opt-in worktree runs against throwaway repositories and state."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

TMP = Path(os.environ.setdefault("BITACORA_TEST_ROOT", tempfile.mkdtemp(prefix="isolated-run-test-")))
HOME = TMP / "home"
HOME.mkdir(exist_ok=True)
os.environ.setdefault("BITACORA_ROOT", str(TMP / "bitacora"))
os.environ.setdefault("BITACORA_PORT", "8798")
SCRIPTS = Path(__file__).resolve().parents[2] / "skill" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import bt_core
import bt_run

STUB = '''
import json, os, pathlib, subprocess, sys, time
task = os.environ["BITACORA_TASK"]
head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
run_state = json.loads(pathlib.Path(os.environ["STUB_RDIR"], "RUN.json").read_text())
recorded = run_state.get("worktrees", {}).get(task, {}).get("worktree")
pathlib.Path(os.environ["STUB_STARTS"]).open("a").write(json.dumps({"task": task, "cwd": os.getcwd(), "head": head,
    "recorded": recorded == os.getcwd(), "time": time.time()}) + "\\n")
if task == "FINAL":
    pathlib.Path(os.environ["STUB_RDIR"], "REPORT.md").write_text("# final\\n")
    raise SystemExit(0)
if task.endswith("-audit"):
    action = os.environ.get("STUB_AUDIT_ACTION")
    if action:
        pathlib.Path("README.md").write_text("audit change\\n")
        if action == "commit":
            subprocess.run(["git", "add", "README.md"], check=True)
            subprocess.run(["git", "-c", "user.name=Audit", "-c", "user.email=audit@example.invalid",
                            "commit", "-m", "audit change"], check=True)
        if action == "sleep":
            time.sleep(30)
    cli = [sys.executable, os.environ["STUB_CLI"], "--project", os.environ["BITACORA_PROJECT"]]
    subprocess.run(cli + ["task", "done", os.environ["BITACORA_RUN"], task, "--evidence", "stub audit passed"], check=True)
    raise SystemExit(0)
time.sleep(float(os.environ.get("STUB_SLEEP", "0.25")))
files = json.loads(pathlib.Path(os.environ["STUB_FILES"]).read_text())
spec = files[task]
target = pathlib.Path(spec.get("write", spec["file"]))
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(spec.get("content", task) + "\\n")
cli = [sys.executable, os.environ["STUB_CLI"], "--project", os.environ["BITACORA_PROJECT"]]
subprocess.run(cli + ["task", "done", os.environ["BITACORA_RUN"], task, "--evidence", "stub wrote file"], check=True)
'''


class IsolatedRunFixture(unittest.TestCase):
    serial = 0

    @classmethod
    def setUpClass(cls):
        cls.stub = TMP / "agent.py"
        cls.stub.write_text(STUB, encoding="utf-8")
        bt_run.commit_bitacora = lambda *args, **kwargs: None

    def setUp(self):
        environment = patch.dict(os.environ, {"HOME": str(HOME), "BITACORA_ROOT": str(bt_core.ROOT)})
        environment.start()
        self.addCleanup(environment.stop)
        type(self).serial += 1
        self.project = f"isolated{type(self).serial}"
        self.repo = TMP / f"repo{type(self).serial}"
        self.repo.mkdir()
        self.git(self.repo, "init", "-b", "main")
        self.git(self.repo, "config", "user.name", "Test")
        self.git(self.repo, "config", "user.email", "test@example.invalid")
        (self.repo / "README.md").write_text("base\n")
        self.git(self.repo, "add", "README.md")
        self.git(self.repo, "commit", "-m", "base")
        bt_core.ensure_project(self.project)
        bt_core.register_repo(self.project, self.repo, "app")
        pdir = bt_core.ROOT / self.project
        self.rdir = pdir / "requirements" / "REQ-001-demo"
        self.rdir.mkdir(parents=True)
        (self.rdir / "SPEC.md").write_text("---\nstatus: approved\n---\n# Demo\n")
        self.starts = TMP / f"starts{self.serial}.jsonl"
        self.files_path = TMP / f"files{self.serial}.json"
        os.environ.update(STUB_STARTS=str(self.starts), STUB_FILES=str(self.files_path), STUB_CLI=str(SCRIPTS / "bitacora.py"),
                          STUB_RDIR=str(self.rdir), STUB_SLEEP="0.25")
        self.cmd = f'"{sys.executable}" "{self.stub}"'

    @staticmethod
    def git(repo: Path, *args: str) -> str:
        result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=True)
        return result.stdout.strip()

    def plan(self, rows: list[str]):
        (self.rdir / "PLAN.md").write_text("---\nstatus: approved\n---\n# Plan\n\n" + "\n".join(rows) + "\n")

    def files(self, mapping: dict):
        self.files_path.write_text(json.dumps(mapping))

    def run_supervisor(self, **options):
        options.setdefault("agent_cmd", self.cmd)
        options.setdefault("no_autostart", True)
        return bt_run.supervise(self.project, "REQ-001", **options)

    def records(self):
        return [json.loads(line) for line in self.starts.read_text().splitlines()]

