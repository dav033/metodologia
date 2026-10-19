"""`watch`: tells each piece of news of a run once, waits for the next one, ends when the run does."""
from __future__ import annotations

import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bt_runstate as rs  # noqa: E402
import bt_watch  # noqa: E402


def task(tid, status="todo", milestone=None):
    return {"id": tid, "title": tid, "status": status, "after": [], "milestone": milestone, "repo": None,
            "verify": None, "level": None, "kind": "implement", "tier": 0, "attempts": 0}


def entry(session, tid, result, at, **extra):
    return {"at": at, "session": session, "task": tid, "result": result, "summary": f"{tid} {result}", "seconds": 600,
            "profile": "codex-luis", "model": "gpt-6-luna", "effort": "medium", **extra}


class WatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name) / "proj" / "requirements" / "REQ-001-x"
        self.rdir.mkdir(parents=True)
        for target, value in ((bt_watch, "STATE"),):
            p = patch.object(target, value, Path(self.tmp.name) / "state")
            p.start()
            self.addCleanup(p.stop)
        for name, value in (("find_req", lambda pdir, req: self.rdir), ("req_id", lambda rdir: "REQ-001")):
            p = patch.object(bt_watch, name, value)
            p.start()
            self.addCleanup(p.stop)
        self.state = {"req": "REQ-001", "status": "running", "sessions": 0, "waiting_until": None, "log": [],
                      "heartbeat": {"at": rs.now_iso(), "task": "M1"},
                      "tasks": [task("T1", milestone="M1"), task("T2", milestone="M1"), task("T3")]}

    def save(self):
        self.state["heartbeat"]["at"] = rs.now_iso()
        rs.save(self.rdir, self.state)

    def watch(self, timeout_min=0.01):
        return bt_watch.watch("proj", "REQ-001", timeout_min, 0.05)

    def test_first_call_reports_the_start_and_later_calls_only_what_is_new(self):
        self.save()
        first = self.watch()
        self.assertIn("running · 0/3 tasks done", first)
        self.assertIn("the run has started", first)
        self.assertIn("terminal: false", first)
        self.state["tasks"][0]["status"] = self.state["tasks"][1]["status"] = "done"
        self.state["log"] += [entry(1, "T1", "done", "2026-10-13T01:00:00"), entry(1, "T2", "done", "2026-10-13T01:00:00")]
        self.save()
        second = self.watch()
        self.assertIn("S1 [codex-luis gpt-6-luna medium] T1:done T2:done (10 min)", second)
        self.assertIn("2/3 tasks done", second)
        self.assertIn("next: T3", second)
        self.state["tasks"][2]["status"] = "in_progress"
        self.state["heartbeat"]["task"] = "T3"
        self.assertIn("now running: T3", bt_watch.report("proj", "REQ-001", self.state, []))
        self.state["tasks"][2]["status"] = "todo"
        third = self.watch()  # nothing happened in between: waits out its timeout and says so
        self.assertNotIn("S1 [", third)
        self.assertIn("no news in", third)

    def test_it_returns_as_soon_as_something_happens(self):
        self.save()
        self.watch()

        def later():
            time.sleep(0.2)
            self.state["log"].append(entry(1, "T1", "verify_failed", "2026-10-13T02:00:00"))
            self.save()
        threading.Thread(target=later).start()
        started = time.time()
        out = bt_watch.watch("proj", "REQ-001", 1, 0.05)
        self.assertLess(time.time() - started, 5)
        self.assertIn("T1:verify_failed", out)

    def test_blocked_waiting_and_end_are_news_and_the_end_is_terminal(self):
        self.save()
        self.watch()
        self.state.update(status="waiting", waiting_until="2026-10-13T05:00:00")
        self.save()
        out = self.watch()
        self.assertIn("status: waiting", out)
        self.assertIn("waiting for usage limits until: 2026-10-13T05:00:00", out)
        self.state.update(status="blocked", waiting_until=None)
        self.state["tasks"][2]["status"] = "blocked"
        self.save()
        out = self.watch()
        self.assertIn("blocked tasks: T3", out)
        self.assertIn("terminal: true", out)
        self.assertIn("blocked: see PENDING.md", out)
        again = self.watch()  # a finished run answers at once, without repeating itself
        self.assertIn("nothing new since the last report", again)
        self.assertIn("terminal: true", again)

    def test_a_silent_legacy_supervisor_reports_retirement_once(self):
        self.save()
        self.watch()
        with patch.object(rs, "is_stale", return_value=True):
            out = self.watch()
            self.assertIn("may have died", out)
            self.assertIn("there is no resume command", out)
            self.assertNotIn("may have died", self.watch())

    def test_no_run_yet_says_so(self):
        self.assertIn("no RUN.json yet", self.watch())

    def test_handoff_tells_the_session_to_keep_watching(self):
        import bt_handoff
        with patch("bt_launch.launch", return_value={"opened": "x", "handoff": "h"}), \
             patch.object(bt_handoff, "assess", return_value={"ok": True, "problems": [], "reasons": [], "auto": True}), \
             patch.object(bt_handoff, "find_req", return_value=self.rdir), \
             patch.object(bt_handoff.rounds, "plan_decide"), patch.object(bt_handoff, "_front", return_value="draft"):
            (self.rdir / "PLAN.md").write_text("---\nstatus: draft\n---\n")
            out = bt_handoff.handoff("proj", "REQ-001")
        self.assertEqual(out["watch"], "bitacora.py --project proj watch REQ-001")
        self.assertIn("in the background", out["next"])


if __name__ == "__main__":
    unittest.main()
