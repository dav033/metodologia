"""Behavior tests for evidence-backed learnings."""
from __future__ import annotations

import argparse
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import bt_learn


class LearnTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="learn-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "bitacora"
        self.state = Path(self.tmp.name) / ".state"
        self.root.mkdir()
        (self.state / "locks").mkdir(parents=True)
        for target, value in (("bt_learn.ROOT", self.root),
                              ("bt_learn.bt_lock._lock_dir", lambda: self.state / "locks")):
            patcher = patch(target, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def add_learning(self, source: str, text: str = "Prefer small focused changes", **kwargs) -> dict:
        return bt_learn.add("alpha", text, f"Observed in {source}", source=source, **kwargs)

    def test_add_creates_candidate_with_evidence(self):
        item = self.add_learning("REQ-006/T3")
        self.assertTrue(item["created"])
        self.assertEqual((item["id"], item["status"], item["sightings"]), ("L-001", "candidate", 1))
        self.assertEqual(item["evidence"][0]["source"], "REQ-006/T3")

    def test_missing_evidence_is_refused(self):
        with self.assertRaises(bt_learn.LearnError):
            bt_learn.add("alpha", "Prefer small focused changes", "  ")
        self.assertFalse((self.root / "alpha" / "learnings.json").exists())

    def test_secret_patterns_are_refused_without_writing(self):
        samples = ("-----BEGIN RSA PRIVATE KEY-----", "AKIA1234567890ABCDEF", "ghp_" + "a" * 20,
                   "sk-" + "a" * 20, "xoxb-123456789", "password=abcdef", "Ab3" * 14, "f" * 41)
        for sample in samples:
            with self.subTest(pattern=sample[:12]), self.assertRaises(bt_learn.LearnError):
                bt_learn.add("alpha", "Preference contains this " + sample, "observed once", source="REQ/T1")
        self.assertFalse((self.root / "alpha" / "learnings.json").exists())

    def test_commit_hashes_and_long_paths_are_legitimate_evidence(self):
        item = bt_learn.add("alpha", "Verify commands run from the repository root",
                            "commit " + "a1b2c3d4e5" * 4 + " in /home/user/dev/project/skill/scripts/tests/test_x.py",
                            source="REQ/T1")
        self.assertTrue(item["created"])

    def test_duplicate_from_another_source_increments_sightings(self):
        self.add_learning("REQ-1/T1")
        item = self.add_learning("REQ-2/T3", text="Prefer small, focused changes!")
        self.assertFalse(item["created"])
        self.assertEqual((item["id"], item["sightings"], len(item["evidence"])), ("L-001", 2, 2))

    def test_duplicate_from_same_source_only_updates_timestamp(self):
        first = self.add_learning("REQ-1/T1")
        second = self.add_learning("REQ-1/T1")
        self.assertFalse(second["created"])
        self.assertEqual(second["sightings"], 1)
        self.assertEqual(len(second["evidence"]), 1)
        self.assertGreater(second["updated"], first["updated"])

    def test_opposite_or_reordered_rules_never_share_evidence(self):
        pairs = (
            ("Use transactions for all customer invoice state changes",
             "Do not use transactions for all customer invoice state changes"),
            ("Copy records from alpha to beta", "Copy records from beta to alpha"),
            ("Require invoice amount > 100", "Require invoice amount < 100"),
        )
        for n, (first, second) in enumerate(pairs):
            project = f"project-{n}"
            original = bt_learn.add(project, first, "Observed", source="session-1")
            bt_learn.reject(project, original["id"])
            different = bt_learn.add(project, second, "Correction", source="session-2")
            self.assertTrue(different["created"])
            self.assertEqual(different["status"], "candidate")
            self.assertEqual(different["sightings"], 1)

    def test_rejection_reason_cannot_persist_secrets(self):
        item = self.add_learning("REQ-1/T1")
        before = (self.root / "alpha" / "learnings.json").read_bytes()
        with self.assertRaises(bt_learn.LearnError):
            bt_learn.reject("alpha", item["id"], reason="password=abcdef")
        self.assertEqual((self.root / "alpha" / "learnings.json").read_bytes(), before)

    def test_malformed_learning_is_a_deliberate_storage_error(self):
        path = self.root / "alpha" / "learnings.json"
        path.parent.mkdir()
        path.write_text('{"schema":1,"items":[null]}', encoding="utf-8")
        with self.assertRaises(bt_learn.LearnError):
            bt_learn.brief("alpha")

    def test_project_learning_never_leaks_to_another_project(self):
        item = self.add_learning("REQ-1/T1")
        bt_learn.confirm("alpha", item["id"])
        self.assertIn(item["text"], bt_learn.brief("alpha"))
        self.assertNotIn(item["text"], bt_learn.brief("beta"))

    def test_context_consumers_respect_configured_limit_and_report_corruption(self):
        import bt_config
        import bt_context
        import bt_runprompt
        first = self.add_learning("REQ-1/T1")
        bt_learn.confirm("alpha", first["id"])
        with patch.object(bt_config, "get", return_value=0):
            self.assertNotIn(first["text"], bt_learn.context_brief("alpha"))
            self.assertNotIn(first["text"], "\n".join(bt_runprompt._team("alpha")))
        (self.root / "alpha" / "learnings.json").write_text("broken", encoding="utf-8")
        self.assertIn("WARNING", bt_learn.context_brief("alpha"))
        self.assertIn("WARNING", "\n".join(bt_runprompt._team("alpha")))
        with patch.object(bt_context.bt_agents, "brief", return_value=""), \
                patch.object(bt_context.bt_events, "read_all", return_value=[]), \
                patch.object(bt_context.bt_events, "read_defects", return_value=[]):
            self.assertIn("confirmed learnings could not be loaded", bt_context.text("alpha"))

    def test_cli_scope_filters_without_hiding_default_global_list(self):
        import bt_cli_learn
        self.add_learning("REQ-1/T1")
        bt_learn.add(None, "Keep skill changes evidence based", "Observed", source="REQ/T2", scope="skill")
        parser = argparse.ArgumentParser()
        bt_cli_learn.register(parser.add_subparsers(dest="cmd"))
        for suffix, expected, absent in ((["--scope", "skill"], "Keep skill", "Prefer small"),
                                         (["--scope", "project"], "Prefer small", "Keep skill"),
                                         ([], "Keep skill", None)):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                bt_cli_learn.dispatch(parser.parse_args(["learn", "list", *suffix]), "alpha")
            self.assertIn(expected, output.getvalue())
            if absent:
                self.assertNotIn(absent, output.getvalue())

    def test_third_independent_sighting_promotes(self):
        self.add_learning("REQ-1/T1")
        self.add_learning("REQ-2/T1")
        item = self.add_learning("REQ-3/T4")
        self.assertEqual((item["status"], item["promoted_by"]), ("confirmed", "sightings"))

    def test_custom_promotion_threshold(self):
        self.add_learning("REQ-1/T1", promote_after=2)
        item = self.add_learning("REQ-2/T1", promote_after=2)
        self.assertEqual(item["status"], "confirmed")

    def test_rejected_duplicate_stays_rejected(self):
        item = self.add_learning("REQ-1/T1")
        rejected = bt_learn.reject("alpha", item["id"], reason="Not a durable rule")
        again = self.add_learning("REQ-2/T1")
        self.assertEqual(rejected["status"], "rejected")
        self.assertTrue(again["ignored"])
        self.assertEqual(again["sightings"], 1)

    def test_confirm_reject_and_unknown_id(self):
        first = self.add_learning("REQ-1/T1")
        self.assertEqual(bt_learn.confirm("alpha", first["id"])["promoted_by"], "owner")
        second = bt_learn.add("alpha", "Run formatting before each commit", "Observed", source="REQ-2/T1")
        self.assertEqual(bt_learn.reject("alpha", second["id"])["status"], "rejected")
        with self.assertRaises(bt_learn.LearnError):
            bt_learn.confirm("alpha", "L-999")

    def test_owner_scope_is_global_and_appears_in_each_project_brief(self):
        item = bt_learn.add(None, "Owner prefers concise Spanish updates", "Owner requested Spanish", scope="owner",
                            kind="preference")
        self.assertTrue((self.root / "learnings.json").exists())
        self.assertFalse((self.root / "alpha" / "learnings.json").exists())
        bt_learn.confirm(None, item["id"], scope="owner")
        self.assertIn(item["text"], bt_learn.brief("alpha"))
        self.assertIn(item["text"], bt_learn.brief("beta"))

    def test_brief_only_lists_confirmed_and_counts_candidates(self):
        candidate = self.add_learning("REQ-1/T1")
        confirmed = bt_learn.add("alpha", "Run formatters before a commit", "Observed", source="REQ-2/T1")
        bt_learn.confirm("alpha", confirmed["id"])
        text = bt_learn.brief("alpha")
        self.assertIn(confirmed["text"], text)
        self.assertNotIn(candidate["text"], text)
        self.assertIn("Candidates awaiting confirmation: 1", text)

    def test_brief_truncates_confirmed_items(self):
        ids = []
        for n, text in enumerate(("Prefer careful concise reviews", "Use explicit typed contracts",
                                  "Record reproduction steps clearly"), 1):
            item = bt_learn.add("alpha", text, "Observed", source=f"REQ-{n}/T1")
            ids.append(item["id"])
            bt_learn.confirm("alpha", item["id"])
        result = bt_learn.brief("alpha", max_items=1)
        self.assertEqual(result.count("- ["), 1)
        self.assertIn("(+2 more: bitacora.py learn list)", result)

    def test_global_volume_cannot_starve_project_learning(self):
        for n in range(4):
            item = bt_learn.add(None, f"Global owner convention number {n}", "Observed", source=f"chat-{n}", scope="owner")
            bt_learn.confirm(None, item["id"], scope="owner")
        project = self.add_learning("REQ-1/T1")
        bt_learn.confirm("alpha", project["id"])
        self.assertIn(project["text"], bt_learn.brief("alpha", max_items=2))

    def test_markdown_is_generated_for_global_and_project(self):
        self.add_learning("REQ-1/T1")
        self.assertIn("## Candidates", (self.root / "alpha" / "LEARNINGS.md").read_text(encoding="utf-8"))
        bt_learn.add(None, "Owner prefers concise Spanish updates", "Requested", scope="owner", kind="preference")
        global_md = (self.root / "LEARNINGS.md").read_text(encoding="utf-8")
        self.assertIn("Owner prefers concise Spanish updates", global_md)
        self.assertIn("Requested", global_md)

    def test_ids_are_never_reused_after_rejection(self):
        item = self.add_learning("REQ-1/T1")
        bt_learn.reject("alpha", item["id"])
        next_item = self.add_learning("REQ-2/T1", text="Apply stable naming to modules")
        self.assertEqual((item["id"], next_item["id"]), ("L-001", "L-002"))

    def test_global_ids_never_collide_with_project_ids_and_are_listed_once(self):
        project = bt_learn.add("alpha", "Invoices are paginated by the server", "seen in the API", source="REQ/T1")
        owner = bt_learn.add(None, "The owner wants interface text in Spanish", "said so", source="chat", scope="owner")
        skill = bt_learn.add(None, "The plan template should name the repo role", "missed twice", source="REQ/T2",
                             scope="skill")
        self.assertEqual((project["id"], owner["id"], skill["id"]), ("L-001", "LG-001", "LG-002"))
        listed = [item["id"] for item in bt_learn.listing("alpha")]
        self.assertEqual(sorted(listed), ["L-001", "LG-001", "LG-002"])  # the root file is not read once per scope
        self.assertIsNone(bt_learn.scope_of_id("LG-001"))
        self.assertEqual(bt_learn.scope_of_id("L-001"), "project")
        self.assertEqual(bt_learn.confirm(None, "LG-002", "owner")["scope"], "skill")  # either global scope finds it
        with self.assertRaises(bt_learn.LearnError):
            bt_learn.confirm("alpha", "LG-001", "project")


if __name__ == "__main__":
    unittest.main()
