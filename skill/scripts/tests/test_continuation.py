"""Cross-session recovery through the real hook/context interfaces."""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bt_core
import bt_hooks
import bt_index
import bt_learn
import bt_views


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "logs"
        self.root.mkdir()
        for module in (bt_core, bt_hooks, bt_views, bt_index, bt_learn):
            for name, value in (("ROOT", self.root), ("STATE", self.root / ".state")):
                if not hasattr(module, name):
                    continue
                p = patch.object(module, name, value)
                p.start()
                self.addCleanup(p.stop)
        p = patch("bt_lock._lock_dir", return_value=self.root / ".state" / "locks")
        p.start()
        self.addCleanup(p.stop)
        (self.root / ".state" / "locks").mkdir(parents=True)

    def close_clean_session(self, project="alpha", sid="old-session", active=False):
        pdir, _ = bt_core.ensure_project(project)
        day = bt_core.ensure_session_block(pdir, sid, Path(self.tmp.name))
        text = day.read_text().replace("### Goal\n-", "### Goal\n- Audit the workflow")
        text = text.replace("### Done\n-", "### Done\n- Reproduced the continuity failure")
        text = text.replace("### Next session starts with\n-", "### Next session starts with\n- Run the recovery regression")
        day.write_text(text)
        bt_core._save_bindings({sid: project})
        data = {"session_id": sid, "cwd": self.tmp.name, "stop_hook_active": active}
        with patch("sys.stdin", io.StringIO(json.dumps(data))), contextlib.redirect_stdout(io.StringIO()):
            bt_hooks.hook_stop("codex")
        return day

    def test_clean_close_recovers_with_new_session_and_generic_cwd(self):
        self.close_clean_session()
        context = bt_views.build_context(None, "new-session", Path(self.tmp.name), "startup")
        self.assertIn("Continuation candidate: **alpha**", context)
        self.assertIn("Run the recovery regression", context)
        self.assertIn("unverified", context.lower())
        self.assertNotIn("new-session", bt_core._load_bindings())

    def test_multiple_projects_remain_explicit_without_silent_rebinding(self):
        self.close_clean_session("alpha", "alpha-old")
        self.close_clean_session("beta", "beta-old")
        context = bt_views.build_context(None, "new-session", Path(self.tmp.name), "startup")
        self.assertIn("Continuation candidate: **beta**", context)
        self.assertIn("Other continuation projects: alpha", context)
        self.assertIn("ambiguous", context.lower())
        self.assertNotIn("new-session", bt_core._load_bindings())

    def test_known_project_recovers_previous_session_despite_new_empty_block(self):
        self.close_clean_session()
        context = bt_views.build_context("alpha", "new-session", Path(self.tmp.name), "startup")
        self.assertIn("Run the recovery regression", context)
        self.assertIn("old-sess", context)

    def test_final_stop_after_logging_reminder_still_saves_checkpoint(self):
        self.close_clean_session(active=True)
        context = bt_views.build_context(None, "new-session", Path(self.tmp.name), "startup")
        self.assertIn("Run the recovery regression", context)

    def test_source_changes_are_live_and_never_claim_verified_completion(self):
        day = self.close_clean_session()
        day.write_text(day.read_text().replace("Run the recovery regression", "Inspect the new blocker"))
        context = bt_views.build_context(None, "new-session", Path(self.tmp.name), "startup")
        self.assertIn("Inspect the new blocker", context)
        self.assertIn("Source changed since checkpoint", context)

    def test_checkpoint_has_no_session_prose_or_secrets_and_context_withholds_secret(self):
        day = self.close_clean_session()
        day.write_text(day.read_text().replace("Run the recovery regression", "password=topsecret"))
        from bt_continuation import save_checkpoint
        save_checkpoint(self.root, "alpha", "old-session")
        stored = (self.root / ".state" / "continuation" / "alpha.json").read_text()
        self.assertNotIn("topsecret", stored)
        self.assertNotIn("Audit the workflow", stored)
        context = bt_views.build_context(None, "new-session", Path(self.tmp.name), "startup")
        self.assertNotIn("topsecret", context)
        self.assertIn("withheld", context)
        known = bt_views.build_context("alpha", "new-session", Path(self.tmp.name), "startup")
        self.assertNotIn("topsecret", known)

    def test_old_next_steps_survive_more_than_five_placeholder_days(self):
        pdir = self.root / "alpha" / "2026-01" / "W1"
        pdir.mkdir(parents=True)
        (pdir / "2026-01-01.md").write_text("### Next session starts with\n- Recover the paused investigation\n")
        for n in range(2, 9):
            (pdir / f"2026-01-{n:02}.md").write_text("### Next session starts with\n-\n")
        self.assertIn("Recover the paused investigation", bt_views.last_next_steps(self.root / "alpha"))

    def test_late_close_of_older_session_cannot_replace_newer_work(self):
        day = self.close_clean_session()
        bt_core.ensure_session_block(self.root / "alpha", "later-session", Path(self.tmp.name))
        text = day.read_text()
        start = text.index("session `later-se`")
        text = text[:start] + text[start:].replace("### Goal\n-", "### Goal\n- Finish the new task").replace(
            "### Next session starts with\n-", "### Next session starts with\n- Verify the later work")
        day.write_text(text)
        from bt_continuation import save_checkpoint
        save_checkpoint(self.root, "alpha", "later-session")
        save_checkpoint(self.root, "alpha", "old-session")
        context = bt_views.build_context(None, "fresh-session", Path(self.tmp.name), "startup")
        self.assertIn("Verify the later work", context)
        self.assertNotIn("Run the recovery regression", context)

    def test_empty_session_cannot_disguise_missing_conversational_handoff(self):
        self.close_clean_session()
        bt_core.ensure_session_block(self.root / "alpha", "empty-session", Path(self.tmp.name))
        from bt_continuation import save_checkpoint
        save_checkpoint(self.root, "alpha", "empty-session")
        context = bt_views.build_context(None, "fresh-session", Path(self.tmp.name), "startup")
        self.assertIn("Session `empty-se` has no recorded handoff", context)
        self.assertIn("Prior session context only", context)

    def test_first_empty_session_is_recoverable_as_incomplete(self):
        pdir, _ = bt_core.ensure_project("alpha")
        bt_core.ensure_session_block(pdir, "empty-session", Path(self.tmp.name))
        bt_core._save_bindings({"empty-session": "alpha"})
        data = {"session_id": "empty-session", "cwd": self.tmp.name}
        with patch("sys.stdin", io.StringIO(json.dumps(data))), contextlib.redirect_stdout(io.StringIO()):
            bt_hooks.hook_stop("codex")
        context = bt_views.build_context(None, "fresh-session", Path(self.tmp.name), "startup")
        self.assertIn("Continuation candidate: **alpha**", context)
        self.assertIn("Source missing or empty", context)

    def test_invalid_checkpoint_does_not_select_a_different_project(self):
        self.close_clean_session()
        checkpoint = self.root / ".state" / "continuation" / "alpha.json"
        data = json.loads(checkpoint.read_text())
        data["project"] = "beta"
        checkpoint.write_text(json.dumps(data))
        context = bt_views.build_context("alpha", "fresh-session", Path(self.tmp.name), "startup")
        self.assertIn("checkpoint unreadable/invalid", context)
        self.assertNotIn("Continuation checkpoint — beta", context)

    def test_session_end_persists_handoff_independently_of_stop(self):
        day = self.close_clean_session()
        checkpoint = self.root / ".state" / "continuation" / "alpha.json"
        old = json.loads(checkpoint.read_text())["saved_at"]
        day.write_text(day.read_text().replace("Run the recovery regression", "Continue after SessionEnd"))
        data = {"session_id": "old-session", "cwd": self.tmp.name}
        with patch("sys.stdin", io.StringIO(json.dumps(data))), patch("bt_vcs.commit", return_value=False):
            bt_hooks.hook_end()
        self.assertNotEqual(old, json.loads(checkpoint.read_text())["saved_at"])
        context = bt_views.build_context(None, "fresh-session", Path(self.tmp.name), "startup")
        self.assertIn("Continue after SessionEnd", context)

    def test_new_client_recovers_canonical_log_without_any_previous_hook(self):
        pdir, _ = bt_core.ensure_project("alpha")
        day = bt_core.ensure_session_block(pdir, "old-session", Path(self.tmp.name))
        day.write_text(day.read_text().replace("### Goal\n-", "### Goal\n- Audit continuity").replace(
            "### Next session starts with\n-", "### Next session starts with\n- Resume canonical work"))
        context = bt_views.build_context(None, "fresh-session", Path(self.tmp.name), "startup")
        self.assertIn("Resume canonical work", context)
        self.assertIn("recovered from canonical log", context)
        self.assertFalse((self.root / ".state" / "continuation").exists())

    def test_named_project_symlink_is_a_legitimate_authority(self):
        actual, _ = bt_core.ensure_project("actual")
        external = Path(self.tmp.name) / "external-project-logs"
        actual.rename(external)
        linked = self.root / "alpha"
        linked.symlink_to(external, target_is_directory=True)
        self.close_clean_session("alpha")
        context = bt_views.build_context("alpha", "fresh-session", Path(self.tmp.name), "startup")
        self.assertIn("Run the recovery regression", context)

    def test_corrupt_historical_log_cannot_abort_current_handoff(self):
        pdir, _ = bt_core.ensure_project("alpha")
        old = pdir / "2020-01" / "W1" / "2020-01-01.md"
        old.parent.mkdir(parents=True)
        old.write_bytes(b"\xff\xfe broken historical encoding")
        self.close_clean_session()
        context = bt_views.build_context(None, "fresh-session", Path(self.tmp.name), "startup")
        self.assertIn("Run the recovery regression", context)
        self.assertIn("Some session logs could not be read", context)
        self.assertNotIn("broken historical encoding", context)

    def test_generic_and_hq_context_inject_confirmed_owner_and_skill_learning(self):
        for scope, text in (("owner", "Keep responses in Spanish"), ("skill", "Verify the recorded next action")):
            item = bt_learn.add(None, text, "Confirmed by the owner", source="session-1", scope=scope)
            bt_learn.confirm(None, item["id"], scope=scope)
        for cwd in (Path(self.tmp.name), self.root):
            context = bt_views.build_context(None, "fresh-session", cwd, "startup")
            self.assertIn("Keep responses in Spanish", context)
            self.assertIn("Verify the recorded next action", context)

    def test_crash_with_old_checkpoint_recovers_newer_canonical_session(self):
        day = self.close_clean_session()
        bt_core.ensure_session_block(self.root / "alpha", "crashed-session", Path(self.tmp.name))
        text = day.read_text()
        start = text.index("session `crashed-")
        day.write_text(text[:start] + text[start:].replace("### Goal\n-", "### Goal\n- Resume the new investigation").replace(
            "### Next session starts with\n-", "### Next session starts with\n- Recover work after crash"))
        context = bt_views.build_context(None, "fresh-session", Path(self.tmp.name), "startup")
        self.assertIn("Recover work after crash", context)
        self.assertNotIn("Run the recovery regression", context)


if __name__ == "__main__":
    unittest.main()
