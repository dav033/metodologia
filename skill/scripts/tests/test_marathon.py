"""Marathon mode end to end, with a stub agent (--agent-cmd) in a throwaway BITACORA_ROOT.

Run: python -m unittest discover -s <skill>/scripts/tests -v
The stub is a small python script generated in the temp dir; its behavior per task comes from a JSON file
({"T1": ["limit", "done"]} = first session hits a usage limit, the second one finishes the task).
"""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="marathon-test-"))
os.environ["BITACORA_ROOT"] = str(TMP / "bitacora")
os.environ["BITACORA_PORT"] = "8797"
os.environ["BITACORA_RUN_BACKOFF_SEC"] = "1"
SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import bt_core  # noqa: E402
import bt_notify  # noqa: E402
import bt_run  # noqa: E402
import bt_runstate as rs  # noqa: E402
import bt_runtask as rt  # noqa: E402

# Isolation guard: a module that imported bt_core before this one froze ROOT at the real bitácora, and these tests would
# then create projects and runs in it. Fail loudly instead of polluting (never import bt_core at module level elsewhere
# in a file that sorts before test_marathon.py).
if Path(bt_core.ROOT).resolve() != (TMP / "bitacora").resolve():
    raise RuntimeError(f"bt_core.ROOT is {bt_core.ROOT}, not the throwaway root {TMP / 'bitacora'}: some test module "
                       "imported bt_core before test_marathon set BITACORA_ROOT. Refusing to run against the real bitácora.")

STUB = '''
import json, os, pathlib, subprocess, sys
cfg_path = pathlib.Path(os.environ["STUB_CFG"])
cfg = json.loads(cfg_path.read_text())
task, req, project = os.environ["BITACORA_TASK"], os.environ["BITACORA_RUN"], os.environ["BITACORA_PROJECT"]
counter = cfg_path.with_name("count-" + task)
n = int(counter.read_text()) if counter.exists() else 0
counter.write_text(str(n + 1))
seq = cfg.get(task, ["report" if task == "FINAL" else "done"])
action = seq[min(n, len(seq) - 1)]
with open(os.environ["STUB_ORDER"], "a") as f:
    f.write(task + ":" + action + "\\n")
cli = [sys.executable, os.environ["STUB_SCRIPT"], "--project", project]
if action == "limit":
    print("Claude AI usage limit reached, try again later")
    sys.exit(1)
if action in ("done", "pause", "stop"):
    if action != "done":
        subprocess.run(cli + ["run-control", req, action], check=True)
    subprocess.run(cli + ["task", "done", req, task, "--evidence", "stub did " + task], check=True)
elif action == "fail":
    subprocess.run(cli + ["task", "fail", req, task, "--reason", "boom 42 in /tmp/x%d" % n], check=True)
elif action == "report":
    pathlib.Path(os.environ["STUB_RDIR"], "REPORT.md").write_text("# report\\n")
elif action == "nothing":
    pass
'''


def quiet(fn, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args, **kwargs)


class MarathonCase(unittest.TestCase):
    counter = 0

    @classmethod
    def setUpClass(cls):
        cls.stub = TMP / "stub.py"
        cls.stub.write_text(STUB, encoding="utf-8")
        bt_notify.notify = lambda *a, **k: None  # no toasts, no ntfy during tests
        bt_notify.install_autostart = lambda *a, **k: None
        bt_notify.remove_autostart = lambda *a, **k: None
        bt_run.commit_bitacora = lambda *a, **k: None

    def make_req(self, tasks: list[str], behavior: dict | None = None):
        MarathonCase.counter += 1
        self.project = f"proj{MarathonCase.counter}"
        pdir, _ = bt_core.ensure_project(self.project)
        self.rdir = pdir / "requirements" / "REQ-001-demo"
        self.rdir.mkdir(parents=True)
        (self.rdir / "SPEC.md").write_text("---\nstatus: approved\n---\n# Demo\n", encoding="utf-8")
        (self.rdir / "PLAN.md").write_text("---\nstatus: approved\n---\n# Plan\n\n## Tasks\n" + "\n".join(tasks) + "\n",
                                           encoding="utf-8")
        work = TMP / f"work{MarathonCase.counter}"
        work.mkdir()
        self.work = work
        self.order = work / "order.log"
        cfg = work / "cfg.json"
        cfg.write_text(json.dumps(behavior or {}), encoding="utf-8")
        os.environ.update(STUB_CFG=str(cfg), STUB_ORDER=str(self.order), STUB_RDIR=str(self.rdir),
                          STUB_SCRIPT=str(SCRIPTS / "bitacora.py"))
        self.cmd = f'"{sys.executable}" "{self.stub.as_posix()}"'

    def run_sup(self, **opts):
        opts.setdefault("agent_cmd", self.cmd)
        return quiet(bt_run.supervise, self.project, "REQ-001", **opts)

    def state(self) -> dict:
        return rs.load(self.rdir)

    def task(self, tid: str) -> dict:
        return rs.get_task(self.state(), tid)

    def order_log(self) -> list[str]:
        return self.order.read_text().split() if self.order.exists() else []

    def pending_text(self) -> str:
        return (bt_core.ROOT / self.project / "PENDING.md").read_text(encoding="utf-8")


class HappyPath(MarathonCase):
    def test_three_tasks_respect_dependencies_and_finish(self):
        self.make_req(["- [ ] T3 — third · after: T1, T2", "- [ ] T1 — first · repo: backend",
                       "- [ ] T2 — second · after: T1"])
        self.assertEqual(self.run_sup(), 0)
        self.assertEqual([e.split(":")[0] for e in self.order_log()], ["T1", "T2", "T3", "FINAL"])
        state = self.state()
        self.assertEqual(state["status"], "done")
        self.assertTrue(all(t["status"] == "done" for t in state["tasks"]))
        self.assertTrue((self.rdir / "REPORT.md").exists())
        plan = (self.rdir / "PLAN.md").read_text(encoding="utf-8")
        self.assertIn("status: done", plan)
        self.assertIn("[x] T1", plan)
        self.assertEqual(state["sessions"], 4)
        self.assertEqual(self.task("T1")["repo"], "backend")

    def test_ticked_tasks_start_done_and_examples_in_comments_are_ignored(self):
        self.make_req(["<!-- - [ ] T9 — example only -->", "- [x] T1 — already done", "- [ ] T2 — next · after: T1"])
        self.assertEqual([t["id"] for t in rs.init_state(self.project, self.rdir, "claude", "haiku", True)["tasks"]],
                         ["T1", "T2"])
        self.run_sup()
        self.assertEqual([e.split(":")[0] for e in self.order_log()], ["T2", "FINAL"])


class Failures(MarathonCase):
    def verify_cmd(self, code: int) -> str:
        return f'`"{sys.executable}" -c "import sys; sys.exit({code})"`'

    def test_verify_failure_counts_a_verify_failed_attempt(self):
        self.make_req([f"- [ ] T1 — check me · verify: {self.verify_cmd(1)}"])
        self.run_sup(once=True)
        t = self.task("T1")
        self.assertEqual((t["status"], t["attempts"]), ("todo", 1))
        self.assertTrue(t["last_error"].startswith("verify failed"))
        self.assertEqual(self.state()["log"][-1]["result"], "verify_failed")

    def test_verify_passing_keeps_the_task_done(self):
        self.make_req([f"- [ ] T1 — check me · verify: {self.verify_cmd(0)}"])
        self.run_sup(once=True)
        self.assertEqual(self.task("T1")["status"], "done")
        self.assertEqual(self.state()["log"][-1]["result"], "done")

    def test_same_error_escalates_to_the_top_tier_then_blocks_and_files_a_pending_item(self):
        self.make_req(["- [ ] T1 — flaky thing", "- [ ] T2 — independent"], {"T1": ["fail"]})
        code = self.run_sup()
        t = self.task("T1")
        self.assertEqual((t["status"], t["attempts"], t["tier"]), ("blocked", 3, 2))  # haiku, sonnet, opus
        self.assertEqual(self.task("T2")["status"], "done")  # the run continued with other tasks
        self.assertEqual(code, 2)
        self.assertEqual(self.state()["status"], "blocked")
        self.assertRegex(t["pending_id"], r"^P-\d+")
        self.assertRegex(self.pending_text(), rf"{t['pending_id']} · \[blocked\] REQ-001 T1: flaky thing")

    def test_max_attempts_blocks_when_errors_differ(self):
        self.make_req(["- [ ] T1 — x"], {"T1": ["nothing"]})
        self.run_sup(max_attempts=2, once=True)
        self.run_sup(max_attempts=2, once=True)
        self.assertEqual(self.task("T1")["status"], "blocked")

    def test_usage_limit_waits_without_consuming_an_attempt(self):
        self.make_req(["- [ ] T1 — big"], {"T1": ["limit", "done"]})
        self.run_sup(once=True)
        state = self.state()
        self.assertEqual(state["status"], "waiting")
        self.assertTrue(state["waiting_until"])
        self.assertEqual((self.task("T1")["attempts"], self.task("T1")["status"]), (0, "todo"))
        self.assertEqual(state["log"][-1]["result"], "usage_limit")

    def test_usage_limit_then_the_run_continues_and_finishes(self):
        self.make_req(["- [ ] T1 — big"], {"T1": ["limit", "done"]})
        self.assertEqual(self.run_sup(), 0)
        self.assertEqual(self.state()["status"], "done")
        self.assertEqual(self.task("T1")["attempts"], 0)
        self.assertEqual(self.order_log()[:2], ["T1:limit", "T1:done"])


class Controls(MarathonCase):
    def test_stop_is_honored_between_sessions(self):
        self.make_req(["- [ ] T1 — a", "- [ ] T2 — b · after: T1"], {"T1": ["stop"]})
        self.assertEqual(self.run_sup(), 0)
        self.assertEqual(self.state()["status"], "stopped")
        self.assertEqual(self.task("T2")["status"], "todo")
        self.assertEqual(self.order_log(), ["T1:stop"])

    def test_pause_waits_until_resume(self):
        self.make_req(["- [ ] T1 — a", "- [ ] T2 — b · after: T1"], {"T1": ["pause"]})
        thread = threading.Thread(target=self.run_sup, daemon=True)
        thread.start()
        deadline = time.time() + 60
        while time.time() < deadline and (self.state() or {}).get("status") != "paused":
            time.sleep(0.2)
        self.assertEqual(self.state()["status"], "paused")
        time.sleep(2)
        self.assertEqual(self.task("T2")["status"], "todo")
        rt.run_control(self.rdir, "resume")
        thread.join(60)
        self.assertFalse(thread.is_alive())
        self.assertEqual(self.state()["status"], "done")

    def test_resume_sends_in_progress_tasks_back_to_todo(self):
        self.make_req(["- [ ] T1 — a", "- [ ] T2 — b"])
        state = rs.init_state(self.project, self.rdir, "claude", "haiku", True)
        rs.mark(state, "T1", "in_progress")
        state.update(status="stopped", control="stop")
        rs.save(self.rdir, state)
        opened = bt_run._open(self.project, self.rdir, {})
        self.assertEqual(opened["tasks"][0]["status"], "todo")
        self.assertEqual((opened["status"], opened["control"]), ("running", None))

    def test_web_buttons_write_control_without_clobbering_the_state(self):
        import bt_page_run
        self.make_req(["- [ ] T1 — a"])
        rs.save(self.rdir, rs.init_state(self.project, self.rdir, "claude", "haiku", True))
        bt_page_run.apply_control(self.rdir, "pause")
        self.assertEqual(self.state()["control"], "pause")
        self.assertEqual(self.state()["tasks"][0]["id"], "T1")
        bt_page_run.apply_control(self.rdir, "resume")
        self.assertIsNone(self.state()["control"])

    def test_session_cap_stops_the_run(self):
        self.make_req(["- [ ] T1 — a"], {"T1": ["nothing"]})
        state = rs.init_state(self.project, self.rdir, "claude", "haiku", True, {"max_sessions": 1, "max_attempts": 9})
        rs.save(self.rdir, state)
        self.run_sup()
        self.run_sup()
        self.assertEqual(self.state()["status"], "stopped")


class ReinjectAfterCompact(MarathonCase):
    def test_session_start_after_compact_restates_the_current_task(self):
        self.make_req(["- [ ] T1 — wire the thing · verify: `echo ok`"])
        rs.save(self.rdir, rs.init_state(self.project, self.rdir, "claude", "haiku", True))
        rt.task_note(self.rdir, "T1", "try the other API")
        rt.task_fail(self.rdir, "T1", "first attempt exploded")
        env = {**os.environ, "BITACORA_PROJECT": self.project, "BITACORA_RUN": "REQ-001", "BITACORA_TASK": "T1"}
        out = subprocess.run([sys.executable, str(SCRIPTS / "bitacora.py"), "hook", "start"], env=env, cwd=str(self.work),
                             input=json.dumps({"session_id": "abc12345", "source": "compact", "cwd": str(self.work)}),
                             capture_output=True, text=True, encoding="utf-8", timeout=60).stdout
        for needle in ("Current marathon task", "wire the thing", "first attempt exploded", "try the other API",
                       "work ONLY on this task"):
            self.assertIn(needle, out)

    def test_no_block_outside_a_marathon_session(self):
        import bt_runprompt
        for key in ("BITACORA_RUN", "BITACORA_TASK"):
            os.environ.pop(key, None)
        self.assertEqual(bt_runprompt.marathon_block(), "")


class Hardening(MarathonCase):
    def verify_cmd(self, code: int) -> str:
        return f'`"{sys.executable}" -c "import sys; sys.exit({code})"`'

    def test_failed_verify_is_never_ticked_so_resume_cannot_turn_it_into_done(self):
        self.make_req([f"- [ ] T1 — check me · verify: {self.verify_cmd(1)}"])
        self.run_sup(once=True)
        self.assertIn("[ ] T1", (self.rdir / "PLAN.md").read_text(encoding="utf-8"))
        reopened = bt_run._open(self.project, self.rdir, {})
        self.assertEqual(reopened["tasks"][0]["status"], "todo")

    def test_ticking_skips_html_comments_and_happens_after_verify(self):
        self.make_req([])
        text = bt_core.render("PLAN.md", id="REQ-001", title="Demo", date="2026-01-01") + "\n- [ ] T1 — real work\n"
        (self.rdir / "PLAN.md").write_text(text, encoding="utf-8")
        self.run_sup(once=True)
        plan = (self.rdir / "PLAN.md").read_text(encoding="utf-8")
        self.assertIn("- [ ] T1 — <what>", plan)
        self.assertIn("- [x] T1 — real work", plan)

    def test_plan_ticks_do_not_override_a_blocked_or_todo_task(self):
        self.make_req(["- [ ] T1 — a", "- [ ] T2 — b"])
        state = rs.init_state(self.project, self.rdir, "claude", "haiku", True)
        rs.mark(state, "T1", "blocked")
        rs.save(self.rdir, state)
        (self.rdir / "PLAN.md").write_text("# Plan\n- [x] T1 — a\n- [x] T2 — b\n", encoding="utf-8")
        opened = bt_run._open(self.project, self.rdir, {})
        self.assertEqual([t["status"] for t in opened["tasks"]], ["blocked", "todo"])

    def test_limit_words_in_a_successful_session_are_not_a_usage_limit(self):
        from bt_runsettle import detect_limit
        ok = json.dumps({"result": "tests got 429 from the mock", "is_error": False})
        self.assertIsNone(detect_limit({"text": ok, "rc": 0}))
        self.assertIsNone(detect_limit({"text": "quota notes, all fine", "rc": 0}))
        self.assertEqual(detect_limit({"text": json.dumps({"result": "usage limit reached", "is_error": True}), "rc": 1}), 0)
        self.assertEqual(detect_limit({"text": "Claude AI usage limit reached|1900000000", "rc": 1}), 1900000000)

    def test_endless_usage_limit_messages_are_logged_as_a_streak_not_a_failure(self):
        import bt_runsettle
        self.make_req(["- [ ] T1 — big"], {"T1": ["limit"]})
        bt_runsettle.LIMIT_STREAK_MAX = 2
        try:
            self.run_sup(once=True)
            self.assertEqual(self.task("T1")["attempts"], 0)
            time.sleep(1.5)
            self.run_sup(once=True)
        finally:
            bt_runsettle.LIMIT_STREAK_MAX = 8
        self.assertEqual(self.task("T1")["attempts"], 0)
        self.assertEqual(self.state()["log"][-1]["result"], "limit_streak")
        self.assertEqual((self.task("T1")["error_hashes"], self.task("T1")["tier"], self.task("T1")["limit_streaks"]),
                         ([], 0, 1))

    def test_restart_keeps_an_explicit_pause_and_a_pending_usage_limit_wait(self):
        self.make_req(["- [ ] T1 — a"])
        state = rs.init_state(self.project, self.rdir, "claude", "haiku", True)
        state.update(status="paused", control="pause")
        rs.save(self.rdir, state)
        opened = bt_run._open(self.project, self.rdir, {})
        self.assertEqual((opened["status"], opened["control"]), ("paused", "pause"))
        until = (time.time() + 3600)
        opened = rs.update(self.rdir, lambda s: s.update(control=None, status="waiting",
                                                         waiting_until=time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(until))))
        opened = bt_run._open(self.project, self.rdir, {})
        self.assertEqual(opened["status"], "waiting")
        self.assertTrue(opened["waiting_until"])

    def test_plan_edits_cannot_rewrite_verify_after_approval(self):
        self.make_req([f"- [ ] T1 — a · verify: {self.verify_cmd(1)}"])
        rs.save(self.rdir, rs.init_state(self.project, self.rdir, "claude", "haiku", True))
        (self.rdir / "PLAN.md").write_text("# Plan\n- [ ] T1 — a · verify: `echo ok`\n", encoding="utf-8")
        opened = bt_run._open(self.project, self.rdir, {})
        self.assertIn("exit(1)", opened["tasks"][0]["verify"])
        self.assertEqual(opened["plan_drift"], ["T1.verify"])

    def test_the_session_cannot_mark_a_task_that_is_not_its_own(self):
        self.make_req(["- [ ] T1 — a", "- [ ] T2 — b"])
        rs.save(self.rdir, rs.init_state(self.project, self.rdir, "claude", "haiku", True))
        os.environ["BITACORA_TASK"] = "T1"
        try:
            with self.assertRaises(SystemExit):
                rt.task_done(self.rdir, "T2", "sneaky")
        finally:
            del os.environ["BITACORA_TASK"]
        self.assertEqual(self.task("T2")["status"], "todo")

    def test_unknown_repo_role_fails_verify_instead_of_running_elsewhere(self):
        self.make_req([f"- [ ] T1 — a · repo: nope · verify: {self.verify_cmd(0)}"])
        self.run_sup(once=True)
        self.assertEqual(self.state()["log"][-1]["result"], "verify_failed")
        self.assertIn("unknown repo role 'nope'", self.task("T1")["last_error"])

    def test_unreadable_run_json_raises_and_the_supervisor_survives_a_failed_iteration(self):
        self.make_req(["- [ ] T1 — a"])
        rs.save(self.rdir, rs.init_state(self.project, self.rdir, "claude", "haiku", True))
        original = bt_run._step
        calls = []

        def flaky(*args):
            calls.append(1)
            if len(calls) == 1:
                raise rs.RunStateError("locked")
            return original(*args)
        bt_run._step = flaky
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(self.run_sup(), 0)
        finally:
            bt_run._step = original
        self.assertEqual(self.state()["status"], "done")
        (self.rdir / "RUN.json").write_text("{half", encoding="utf-8")
        with self.assertRaises(rs.RunStateError):
            rs.load(self.rdir)


class Units(unittest.TestCase):
    def test_error_hash_ignores_numbers_and_paths(self):
        self.assertEqual(rs.error_hash("boom 42 in C:\\x\\y 0xdeadbeef"), rs.error_hash("boom 7 in D:\\z 0xabcdef12"))
        self.assertNotEqual(rs.error_hash("boom"), rs.error_hash("bang"))

    def test_agent_argv(self):
        import bt_runprompt as rp
        argv, stdin = rp.agent_argv({"agent": "claude", "model": "haiku"}, Path("."), "PROMPT")
        self.assertEqual((argv[1:4], argv[-1], stdin), (["-p", "--model", "haiku"], "PROMPT", None))
        self.assertNotIn("--effort", argv)
        self.assertIn("stream-json", argv)
        argv, _ = rp.agent_argv({"agent": "claude", "model": "haiku"}, Path("."), "PROMPT", "opus", "xhigh")
        self.assertEqual(argv[1:6], ["-p", "--model", "opus", "--effort", "xhigh"])
        argv, stdin = rp.agent_argv({"agent": "codex", "model": "haiku"}, Path("."), "PROMPT")
        self.assertEqual((argv[1], argv[-1], stdin, "-m" in argv, "-c" in argv), ("exec", "-", "PROMPT", False, False))
        argv, _ = rp.agent_argv({"agent": "codex", "model": "gpt-5"}, Path("."), "PROMPT", "gpt-5", "xhigh")
        self.assertEqual(argv[-5:], ["-m", "gpt-5", "-c", 'model_reasoning_effort="xhigh"', "-"])


if __name__ == "__main__":
    unittest.main()
