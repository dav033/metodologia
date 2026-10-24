"""Runtime ownership checks for Designer snapshots."""
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))
import bt_scheduler_executor_adapter as adapter  # noqa: E402


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, text=True,
                          capture_output=True).stdout.strip()


class DesignerWriteScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "user.email", "test@example.com")
        (self.repo / "design").mkdir()
        (self.repo / "design" / "old.txt").write_text("old\n")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "base")
        self.base = git(self.repo, "rev-parse", "HEAD")

    def snapshot(self, edits):
        for name, value in edits.items():
            path = self.repo / name
            if value is None:
                path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(value)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "snapshot")
        return git(self.repo, "rev-parse", "HEAD")

    def test_violation_returns_stable_cause_and_paths(self):
        snap = self.snapshot({"design/new.txt": "ok\n", "src/app.py": "bad\n"})
        refusal = adapter.designer_scope_refusal(self.repo, self.base, snap, kind="design", role="")
        self.assertEqual(refusal, ("DESIGN_SCOPE_VIOLATION", ("src/app.py",)))

    def test_rename_out_of_design_reports_both_paths(self):
        git(self.repo, "mv", "design/old.txt", "outside.txt")
        git(self.repo, "commit", "-qm", "rename")
        snap = git(self.repo, "rev-parse", "HEAD")
        refusal = adapter.designer_scope_refusal(self.repo, self.base, snap, kind="design", role="")
        self.assertEqual(refusal, ("DESIGN_SCOPE_VIOLATION", ("design/old.txt", "outside.txt")))

    def test_preview_paths_refused_when_disabled_and_allowed_when_enabled(self):
        snap = self.snapshot({"design/preview/mock.html": "preview\n"})
        self.assertEqual(adapter.designer_scope_refusal(self.repo, self.base, snap, kind="design", role="",
                                                        preview_enabled=False),
                         ("DESIGN_PREVIEW_DISABLED", ("design/preview/mock.html",)))
        self.assertIsNone(adapter.designer_scope_refusal(self.repo, self.base, snap, kind="design", role="",
                                                         preview_enabled=True))

    def test_non_design_legacy_and_designer_role_are_handled(self):
        snap = self.snapshot({"src/app.py": "ok\n"})
        self.assertIsNone(adapter.designer_scope_refusal(self.repo, self.base, snap, kind="implementation", role=""))
        self.assertIsNone(adapter.designer_scope_refusal(self.repo, self.base, snap, kind="design", role="",
                                                         plan_version="1.2.0"))
        refusal = adapter.designer_scope_refusal(self.repo, self.base, snap, kind="implementation", role="designer")
        self.assertEqual(refusal[0], "DESIGN_SCOPE_VIOLATION")

    def test_terminal_success_is_converted_to_failed_before_core_verification(self):
        snap = self.snapshot({"outside.txt": "bad\n"})
        class Scheduler:
            def ingest(inner, event):
                inner.event = event
                from scheduler_executor_support import core
                return core.IngestResult("applied")
        scheduler = Scheduler()
        sink = adapter.CoreEventSink(scheduler, scope_check=lambda _event:
                                     adapter.designer_scope_refusal(self.repo, self.base, snap,
                                                                    kind="design", role=""))
        import bt_scheduler_executor as m3
        sink.deliver(m3.TechnicalEvent("terminal", "execution_finished", "P", 1, "T", "att", 1, "now",
                                       {"handoff": {"base_sha": self.base, "snapshot_sha": snap}}))
        self.assertEqual(scheduler.event.kind, "execution_failed")
        self.assertEqual(scheduler.event.payload["cause"], "DESIGN_SCOPE_VIOLATION")
        self.assertIn("outside.txt", scheduler.event.payload["detail"])


if __name__ == "__main__":
    unittest.main()
