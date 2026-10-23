"""A long sandbox check exposes activity before returning its verdict."""
import tempfile
import unittest
from pathlib import Path

from bt_scheduler_quality.policy import CheckSpec, QualityPolicy
from bt_scheduler_quality.runner import SandboxRunner


class RunnerProgressTests(unittest.TestCase):
    def test_progress_arrives_during_execution_and_finishes_without_output_content(self):
        events = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "probe.py").write_text(
                "import time\nprint('private-output', flush=True)\ntime.sleep(0.3)\n",
                encoding="utf-8",
            )
            spec = CheckSpec("CHECK-001", "command", "python3 probe.py", ("python3", "probe.py"), ".", "activity")
            runner = SandboxRunner(QualityPolicy(), progress=lambda *event: events.append(event))
            result = runner.run(spec, root)
        self.assertEqual(result.status, "pass")
        self.assertEqual(events[0], ("CHECK-001", "running", 0))
        self.assertEqual(events[-1][0:2], ("CHECK-001", "finished"))
        self.assertTrue(any(phase == "running" and size > 0 for _, phase, size in events[:-1]))
        self.assertNotIn("private-output", repr(events))
