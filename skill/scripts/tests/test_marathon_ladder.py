"""Marathon escalation ladder, `task escalate`, early termination after `task done` and live session logs.

Same harness as test_marathon (throwaway BITACORA_ROOT, stub agent through --agent-cmd), with a stub that also
records the model arguments it was launched with ({model_args}) and can linger or hang.
Run: python -m unittest discover -s <skill>/scripts/tests -v
"""
import json
import os
import sys
import time
import unittest

from test_marathon import TMP, MarathonCase, quiet  # noqa: F401  (sets BITACORA_ROOT before bt_* imports)

import bt_core  # noqa: E402
import bt_run  # noqa: E402
import bt_runstate as rs  # noqa: E402
import bt_runtask as rt  # noqa: E402

LADDER_STUB = '''
import json, os, pathlib, subprocess, sys, time
cfg_path = pathlib.Path(os.environ["STUB_CFG"])
cfg = json.loads(cfg_path.read_text())
task, req, project = os.environ["BITACORA_TASK"], os.environ["BITACORA_RUN"], os.environ["BITACORA_PROJECT"]
counter = cfg_path.with_name("count-" + task)
n = int(counter.read_text()) if counter.exists() else 0
counter.write_text(str(n + 1))
seq = cfg.get(task, ["report" if task == "FINAL" else "done"])
action = seq[min(n, len(seq) - 1)]
with open(cfg_path.with_name("argv.log"), "a") as f:
    f.write(task + " " + " ".join(sys.argv[1:]) + "\\n")
cli = [sys.executable, os.environ["STUB_SCRIPT"], "--project", project]
if action == "fail":
    subprocess.run(cli + ["task", "fail", req, task, "--reason", "boom 42 in /tmp/x%d" % n], check=True)
elif action == "fail-linger":
    subprocess.run(cli + ["task", "fail", req, task, "--reason", "no driver for the device"], check=True)
    time.sleep(120)
elif action == "failn":
    subprocess.run(cli + ["task", "fail", req, task, "--reason", "variant " + "abcdefgh"[n]], check=True)
elif action.startswith("escalate-"):
    subprocess.run(cli + ["task", "escalate", req, task, "--to", action.split("-")[1], "--reason", "needs a design"],
                   check=True)
elif action in ("done", "linger"):
    print("working on " + task, flush=True)
    subprocess.run(cli + ["task", "done", req, task, "--evidence", "stub did " + task], check=True)
    if action == "linger":
        time.sleep(120)
elif action == "hang":
    print("halfway through " + task, flush=True)
    time.sleep(120)
elif action == "report":
    pathlib.Path(os.environ["STUB_RDIR"], "REPORT.md").write_text("# report\\n")
'''

HAIKU, SONNET, OPUS = "--model haiku", "--model sonnet --effort xhigh", "--model opus --effort xhigh"


class LadderCase(MarathonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ladder_stub = TMP / "ladder_stub.py"
        cls.ladder_stub.write_text(LADDER_STUB, encoding="utf-8")

    def make_req(self, tasks, behavior=None):
        super().make_req(tasks, behavior)
        self.cmd = f'"{sys.executable}" "{self.ladder_stub.as_posix()}" {{model_args}}'

    def argv_log(self, task: str) -> list[str]:
        f = self.work / "argv.log"
        lines = f.read_text().splitlines() if f.exists() else []
        return [ln.split(" ", 1)[1] for ln in lines if ln.startswith(task + " ")]

    def session_log(self, n: int) -> str:
        f = bt_core.STATE / "runs" / f"{self.project}-REQ-001" / f"session-{n:04d}.log"
        return f.read_text(encoding="utf-8", errors="replace")


class Ladder(LadderCase):
    def test_each_failure_climbs_haiku_sonnet_opus_with_xhigh(self):
        self.make_req(["- [ ] T1 — tricky"], {"T1": ["failn", "failn", "done"]})
        self.assertEqual(self.run_sup(), 0)
        self.assertEqual(self.argv_log("T1"), [HAIKU, SONNET, OPUS])
        rows = [x for x in self.state()["log"] if x["task"] == "T1"]
        self.assertEqual([(x["model"], x.get("effort")) for x in rows],
                         [("haiku", None), ("sonnet", "xhigh"), ("opus", "xhigh")])
        self.assertEqual((self.task("T1")["status"], self.task("T1")["tier"]), ("done", 2))

    def test_repeated_error_escalates_and_only_blocks_at_opus(self):
        self.make_req(["- [ ] T1 — flaky"], {"T1": ["fail"]})
        self.assertEqual(self.run_sup(), 2)
        self.assertEqual(self.argv_log("T1"), [HAIKU, SONNET, OPUS])
        t = self.task("T1")
        self.assertEqual((t["status"], t["attempts"]), ("blocked", 3))
        self.assertIn("top model tier", self.pending_text())

    def test_differing_errors_get_four_attempts_haiku_sonnet_opus_opus(self):
        self.make_req(["- [ ] T1 — wobbly"], {"T1": ["failn"]})
        self.run_sup()
        self.assertEqual(self.argv_log("T1"), [HAIKU, SONNET, OPUS, OPUS])
        self.assertEqual((self.task("T1")["status"], self.task("T1")["attempts"]), ("blocked", 4))

    def test_architecture_level_starts_at_opus(self):
        self.make_req(["- [ ] T1 — design the sync engine · level: architecture", "- [ ] T2 — small"])
        self.assertEqual(self.run_sup(), 0)
        self.assertEqual(self.argv_log("T1"), [OPUS])
        self.assertEqual(self.argv_log("T2"), [HAIKU])
        self.assertEqual(self.task("T1")["level"], "architecture")

    def test_agent_escalation_is_an_attempt_but_not_a_failure(self):
        self.make_req(["- [ ] T1 — gnarly"], {"T1": ["escalate-opus", "done"]})
        self.assertEqual(self.run_sup(), 0)
        self.assertEqual(self.argv_log("T1"), [HAIKU, OPUS])
        t = self.task("T1")
        self.assertEqual((t["status"], t["attempts"], t["error_hashes"], t["tier"]), ("done", 1, [], 2))
        self.assertNotIn("escalation", t)
        self.assertIn("escalated to opus: needs a design", t["notes"])
        self.assertEqual(self.state()["log"][0]["result"], "escalated")

    def test_an_escalated_session_counts_toward_max_attempts(self):
        self.make_req(["- [ ] T1 — gnarly"], {"T1": ["escalate-sonnet"]})
        self.run_sup(max_attempts=1)
        self.assertEqual(self.argv_log("T1"), [HAIKU])
        self.assertEqual((self.task("T1")["status"], self.task("T1")["attempts"]), ("blocked", 1))

    def test_escalate_by_hand_moves_the_tier_up_only(self):
        self.make_req(["- [ ] T1 — a"])
        rs.save(self.rdir, rs.init_state(self.project, self.rdir, "claude", "haiku", True))
        rt.task_escalate(self.rdir, "T1", "opus", "architecture call")
        for to in ("sonnet", "opus", "gpt"):  # lower, same, unknown: refused
            with self.assertRaises(SystemExit):
                rt.task_escalate(self.rdir, "T1", to, "no")
        t = self.task("T1")
        self.assertEqual((t["tier"], "escalation" in t), (2, False))


class SessionLifecycle(LadderCase):
    def test_lingering_session_is_ended_after_task_done_and_grace(self):
        self.make_req(["- [ ] T1 — a"], {"T1": ["linger"]})
        os.environ["BITACORA_RUN_GRACE_SEC"] = "1"
        try:
            start = time.time()
            self.run_sup(once=True)
        finally:
            del os.environ["BITACORA_RUN_GRACE_SEC"]
        self.assertLess(time.time() - start, 60)
        entry = self.state()["log"][-1]
        self.assertEqual((entry["result"], entry.get("early_exit")), ("done", True))
        self.assertIn("[x] T1", (self.rdir / "PLAN.md").read_text(encoding="utf-8"))

    def test_lingering_session_after_task_fail_is_ended_and_keeps_the_agents_reason(self):
        self.make_req(["- [ ] T1 — a"], {"T1": ["fail-linger"]})
        os.environ["BITACORA_RUN_GRACE_SEC"] = "1"
        try:
            self.run_sup(once=True)
        finally:
            del os.environ["BITACORA_RUN_GRACE_SEC"]
        entry, t = self.state()["log"][-1], self.task("T1")
        self.assertEqual((entry["result"], entry.get("early_exit")), ("failed", True))
        self.assertEqual((t["last_error"], t["tier"]), ("no driver for the device", 1))

    def test_killed_session_keeps_its_live_log(self):
        self.make_req(["- [ ] T1 — a"], {"T1": ["hang"]})
        rs.save(self.rdir, rs.init_state(self.project, self.rdir, "claude", "haiku", True, {"session_timeout_min": 0.05}))
        self.run_sup(once=True)
        self.assertEqual(self.state()["log"][-1]["result"], "timeout")
        self.assertIn("halfway through T1", self.session_log(1))


class StreamJson(unittest.TestCase):
    def test_result_event_is_parsed_and_tool_output_is_not_a_limit(self):
        from bt_runsettle import detect_limit, parse_output
        events = [{"type": "system", "subtype": "init"},
                  {"type": "user", "message": {"content": "tool said: 429 quota exceeded"}},
                  {"type": "result", "subtype": "success", "is_error": False, "result": "all good",
                   "total_cost_usd": 0.42}]
        text = "\n".join(json.dumps(x) for x in events)
        self.assertEqual(parse_output(text), {"text": "all good", "is_error": False, "cost": 0.42, "limit": False})
        self.assertIsNone(detect_limit({"text": text, "rc": 1}))
        limit = text.rsplit("\n", 1)[0] + "\n" + json.dumps(
            {"type": "result", "is_error": True, "result": "Claude AI usage limit reached|1900000000"})
        self.assertEqual(detect_limit({"text": limit, "rc": 1}), 1900000000)
        cut = "\n".join(json.dumps(x) for x in events[:2]) + "\nError: rate limit hit"
        self.assertEqual(parse_output(cut)["text"], "Error: rate limit hit")
        killed = "\n".join(json.dumps(x) for x in events[:2]) + '\n{"type": "user", "message": "got 429 fr'
        self.assertIsNone(detect_limit({"text": killed, "rc": 1}))


if __name__ == "__main__":
    unittest.main()
