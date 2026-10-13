"""P-011: a supervised session may only mark its own task in its own run and project."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import bt_runtask  # noqa: E402  (imports bt_core: this file must sort after test_marathon.py)


class OwnershipTests(unittest.TestCase):
    rdir = Path("/x/bitacora/pictures/requirements/REQ-014-marathon")

    def check(self, **env):
        with patch.dict(os.environ, env, clear=False):
            bt_runtask._own_task(env.get("TASK", "T1"), self.rdir)

    def run_env(self, run="REQ-014", project="pictures", task="T1"):
        return {"BITACORA_RUN": run, "BITACORA_PROJECT": project, "BITACORA_TASK": task}

    def test_same_run_project_and_task_is_allowed(self):
        with patch.dict(os.environ, self.run_env()):
            bt_runtask._own_task("T1", self.rdir)

    def test_another_requirement_is_refused_even_with_the_same_task_id(self):
        with patch.dict(os.environ, self.run_env(run="REQ-003")), self.assertRaises(SystemExit) as ctx:
            bt_runtask._own_task("T1", self.rdir)
        self.assertIn("REQ-003", str(ctx.exception))

    def test_another_project_is_refused(self):
        with patch.dict(os.environ, self.run_env(project="maros")), self.assertRaises(SystemExit):
            bt_runtask._own_task("T1", self.rdir)

    def test_another_task_is_refused(self):
        with patch.dict(os.environ, self.run_env()), self.assertRaises(SystemExit):
            bt_runtask._own_task("T2", self.rdir)

    def test_a_human_outside_a_session_is_not_restricted(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("BITACORA_") or k == "BITACORA_ROOT"}
        with patch.dict(os.environ, env, clear=True):
            bt_runtask._own_task("T9", self.rdir)


if __name__ == "__main__":
    unittest.main()
