"""Throwaway-root fixtures for tests that build a requirement (SPEC/PLAN) and read or write its RUN.json state.

Importing this module points BITACORA_ROOT at the disposable root before any bt_* module freezes it.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# test_00_isolation.py (first in discovery) may already have chosen the throwaway root; reuse it.
TMP = Path(os.environ.get("BITACORA_TEST_ROOT") or tempfile.mkdtemp(prefix="run-case-test-"))
os.environ["BITACORA_TEST_ROOT"] = str(TMP)
os.environ["BITACORA_ROOT"] = str(TMP / "bitacora")
os.environ["BITACORA_PORT"] = "8797"
os.environ["BITACORA_RUN_BACKOFF_SEC"] = "1"
SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import bt_agents  # noqa: E402
import bt_config  # noqa: E402
import bt_core  # noqa: E402
import bt_events  # noqa: E402
import bt_profiles  # noqa: E402
import bt_runprompt as rp  # noqa: E402
import bt_runsettle as settle  # noqa: E402
import bt_runstate as rs  # noqa: E402
import bt_runtask as rt  # noqa: E402

if Path(bt_core.ROOT).resolve() != (TMP / "bitacora").resolve():
    raise RuntimeError(f"bt_core.ROOT is {bt_core.ROOT}, not the throwaway root {TMP / 'bitacora'}: some test module "
                       "imported bt_core before the root was set. Refusing to run against the real bitácora.")

ENV_KEYS = ("BITACORA_TASK", "BITACORA_RUN", "BITACORA_PROJECT", "BITACORA_SESSION", "BITACORA_KIND")


class RunCase(unittest.TestCase):
    counter = 0

    def make_req(self, tasks: list[str]) -> None:
        RunCase.counter += 1
        self.project = f"proj{RunCase.counter}"
        pdir, _ = bt_core.ensure_project(self.project)
        self.rdir = pdir / "requirements" / "REQ-001-demo"
        self.rdir.mkdir(parents=True)
        (self.rdir / "SPEC.md").write_text("---\nstatus: approved\n---\n# Demo\n", encoding="utf-8")
        (self.rdir / "PLAN.md").write_text("---\nstatus: approved\n---\n# Plan\n\n## Tasks\n" + "\n".join(tasks) + "\n",
                                           encoding="utf-8")
        self.work = TMP / f"work{RunCase.counter}"
        self.work.mkdir()

    def state(self) -> dict:
        return rs.load(self.rdir)

    def task(self, tid: str) -> dict:
        return rs.get_task(self.state(), tid)


class MilestoneCase(RunCase):
    """A requirement in a per-test root: modules that froze ROOT/STATE at import are repointed for the test."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="milestones-test-")
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.isolated_root = base / "bitacora"
        self.isolated_state = self.isolated_root / ".state"
        self.isolated_state.mkdir(parents=True)
        old_root = os.environ.get("BITACORA_ROOT")
        os.environ["BITACORA_ROOT"] = str(self.isolated_root)
        self.addCleanup(lambda: os.environ.__setitem__("BITACORA_ROOT", old_root)
                        if old_root is not None else os.environ.pop("BITACORA_ROOT", None))
        replacements = {
            bt_core: {"ROOT": self.isolated_root, "STATE": self.isolated_state},
            rp: {"ROOT": self.isolated_root},
            settle: {"ROOT": self.isolated_root},
            rt: {"ROOT": self.isolated_root},
            rs: {"STATE": self.isolated_state},
            bt_agents: {"STATE": self.isolated_state},
            bt_profiles: {"ROOT": self.isolated_root, "STATE": self.isolated_state},
            bt_events: {"STATE": self.isolated_state},
            bt_config: {"STATE": self.isolated_state},
        }
        for module, attrs in replacements.items():
            for name, value in attrs.items():
                p = patch.object(module, name, value)
                p.start()
                self.addCleanup(p.stop)
        self.addCleanup(self._clear_env)
        self._clear_env()
        for key in ("CODEX_HOME", "CLAUDE_CONFIG_DIR"):
            old = os.environ.pop(key, None)
            self.addCleanup(lambda name=key, value=old: os.environ.__setitem__(name, value)
                            if value is not None else os.environ.pop(name, None))
        p = patch("bt_agents.shutil.which", return_value="/stub-agent")
        p.start()
        self.addCleanup(p.stop)

    @staticmethod
    def _clear_env():
        for key in ENV_KEYS:
            os.environ.pop(key, None)

    def make_milestone_req(self, groups):
        lines = ["---", "status: approved", "---", "# Plan", ""]
        for heading, tasks in groups:
            lines.extend([heading, *tasks, ""])
        self.make_req([])
        (self.rdir / "PLAN.md").write_text("\n".join(lines), encoding="utf-8")

    def create_profiles(self):
        claude_home = self.work / "claude-home"
        codex_home = self.work / "codex-home"
        claude_home.mkdir(exist_ok=True)
        codex_home.mkdir(exist_ok=True)
        bt_profiles.add("claude-test", "claude", {"CLAUDE_CONFIG_DIR": str(claude_home)})
        bt_profiles.add("codex-test", "codex", {"CODEX_HOME": str(codex_home)})
        return ["claude-test", "codex-test"]
