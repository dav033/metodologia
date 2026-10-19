import json
import tempfile
import unittest
from pathlib import Path

import bt_live_api as live
import bt_page_now as now_page
import bt_presence as presence

SID = "abcd1234-0000-0000-0000-000000000001"
SPEC = "/home/x/bitacora/pictures/requirements/REQ-018-category-based/SPEC.md"


def edit(path, **kw):
    return {"session_id": SID, "hook_event_name": "PostToolUse", "tool_name": "Edit", "cwd": "/home/x/dev/pictures",
            "tool_input": {"file_path": path}, **kw}


class Presence(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_a_planning_edit_marks_the_session_as_planning_that_requirement(self):
        presence.record(self.root, {"session_id": SID, "hook_event_name": "UserPromptSubmit"}, "pictures", "claude", 100.0)
        presence.record(self.root, edit(SPEC), "pictures", "claude", 105.0)
        (s,) = presence.sessions(self.root, 110.0)
        self.assertEqual((s["state"], s["activity"], s["req"], s["stage"], s["project"]),
                         ("working", "planning", "REQ-018", "especificación", "pictures"))
        self.assertEqual(s["since"], 100.0)

    def test_stop_is_idle_and_session_end_forgets_it(self):
        presence.record(self.root, edit(SPEC), "pictures", "claude", 100.0)
        presence.record(self.root, {"session_id": SID, "hook_event_name": "Stop"}, "pictures", "claude", 120.0)
        self.assertEqual(presence.sessions(self.root, 121.0)[0]["state"], "idle")
        presence.record(self.root, {"session_id": SID, "hook_event_name": "SessionEnd"}, None)
        self.assertEqual(presence.sessions(self.root, 122.0), [])

    def test_silent_working_session_is_quiet_then_forgotten(self):
        presence.record(self.root, edit(SPEC), "pictures", "claude", 100.0)
        self.assertTrue(presence.sessions(self.root, 100.0 + presence.IDLE_AFTER_S + 1)[0]["quiet"])
        self.assertEqual(presence.sessions(self.root, 100.0 + presence.FORGET_AFTER_S + 1), [])

    def test_a_bad_session_id_is_ignored(self):
        presence.record(self.root, {**edit(SPEC), "session_id": "../x"}, "pictures", "claude", 100.0)
        self.assertEqual(presence.sessions(self.root, 101.0), [])

    def test_planning_edits_become_agent_to_planner_flow_events_with_a_resumable_cursor(self):
        presence.record(self.root, edit(SPEC), "pictures", "claude", 100.0)
        events, cur = live._planning_events(self.root, "global", "", None)
        self.assertEqual([(e["from"], e["to"], e["kind"], e["run"]) for e in events],
                         [("agent", "planner", "planning", "pictures/REQ-018")])
        again, _ = live._planning_events(self.root, "global", "", {"presence/planning": cur})
        self.assertEqual(again, [])
        self.assertEqual(live._planning_events(self.root, "project:other", "", None)[0], [])

    def test_the_now_page_and_bar_show_the_planning_agent(self):
        presence.record(self.root, edit(SPEC), "pictures", "claude", 100.0)
        agents = presence.sessions(self.root, 101.0)
        frag = now_page.fragments([], agents)
        self.assertIn("planificando REQ-018", frag["bar"])
        self.assertIn("/go/pictures/REQ-018", frag["agents"])
        self.assertIn("Agentes en sesión", now_page.now_page([], agents))
        self.assertEqual(now_page.fragments([], [])["bar"], "")


if __name__ == "__main__":
    unittest.main()
