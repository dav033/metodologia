"""Marathon robustness: a claimed `task done` is not trusted until verify passed (also after a crash), and usage-limit
streaks never count as an error or block a task. Same harness as test_marathon.
Run: python -m unittest discover -s <skill>/scripts/tests -v
"""
import os
import sys
import time
import unittest

from test_marathon import MarathonCase  # noqa: F401  (sets BITACORA_ROOT before bt_* imports)

import bt_runsession  # noqa: E402
import bt_runsettle  # noqa: E402
import bt_runstate as rs  # noqa: E402
import bt_runtask as rt  # noqa: E402


def verify_cmd(code: int) -> str:
    return f'`"{sys.executable}" -c "import sys; sys.exit({code})"`'


class RobustCase(MarathonCase):
    def seed(self, tasks: list[str], behavior: dict | None = None, **claims):
        """A RUN.json as a crashed supervisor left it: claims = {task_id: fields to merge into that task}."""
        self.make_req(tasks, behavior)
        rs.save(self.rdir, rs.init_state(self.project, self.rdir, "claude", "haiku", True))

        def fn(s):
            for tid, fields in claims.items():
                rs.get_task(s, tid).update(fields)
        rs.update(self.rdir, fn)

    def plan(self) -> str:
        return (self.rdir / "PLAN.md").read_text(encoding="utf-8")

    def settle_info(self, text: str) -> dict:
        return {"rc": 1, "text": text, "stopped": False, "timed_out": False, "seconds": 1, "model": None, "effort": None}


CRASHED = {"status": "in_progress", "claimed_done": True, "evidence": "agent says it works"}


class ClaimedDone(RobustCase):
    def supervised(self, fn, *args):
        os.environ["BITACORA_RUN"] = "REQ-001"
        try:
            return fn(*args)
        finally:
            del os.environ["BITACORA_RUN"]

    def test_under_a_supervisor_task_done_is_only_a_claim(self):
        self.seed(["- [ ] T1 — a"])
        self.supervised(rt.task_done, self.rdir, "T1", "all green")
        t = self.task("T1")
        self.assertEqual((t["status"], t["claimed_done"], t["evidence"]), ("in_progress", True, "all green"))
        self.assertIn("[ ] T1", self.plan())

    def test_by_hand_task_done_is_done_and_ticked_at_once(self):
        self.seed(["- [ ] T1 — a"])
        rt.task_done(self.rdir, "T1", "by hand")
        self.assertEqual(self.task("T1")["status"], "done")
        self.assertNotIn("claimed_done", self.task("T1"))
        self.assertIn("[x] T1", self.plan())

    def test_a_claim_taken_back_with_task_fail_is_no_longer_a_claim(self):
        self.seed(["- [ ] T1 — a"])
        self.supervised(rt.task_done, self.rdir, "T1", "x")
        self.supervised(rt.task_fail, self.rdir, "T1", "changed my mind")
        self.assertEqual((self.task("T1")["status"], "claimed_done" in self.task("T1")), ("todo", False))

    def test_a_late_done_does_not_reopen_a_verified_or_blocked_task(self):
        self.seed(["- [ ] T1 — a", "- [ ] T2 — b"], T1={"status": "done"}, T2={"status": "blocked"})
        self.supervised(rt.task_done, self.rdir, "T1", "again")
        self.supervised(rt.task_done, self.rdir, "T2", "again")
        self.assertEqual([(t["status"], "claimed_done" in t) for t in self.state()["tasks"]],
                         [("done", False), ("blocked", False)])

    def test_a_stop_keeps_the_claim_so_the_next_start_verifies_it(self):
        self.seed([f"- [ ] T1 — a · verify: {verify_cmd(0)}"], T1=CRASHED)
        info = {**self.settle_info(""), "stopped": True}
        bt_runsettle.settle_task(self.project, self.rdir, "T1", 1, info, self.work)
        self.assertEqual((self.task("T1")["status"], self.task("T1").get("claimed_done")), ("todo", True))
        bt_runsettle.recover_claims(self.project, self.rdir, self.work)
        self.assertEqual(self.task("T1")["status"], "done")

    def test_a_claim_ends_the_session_wait_like_any_verdict(self):
        self.seed(["- [ ] T1 — a"], T1=CRASHED)
        self.assertTrue(bt_runsession._reported(self.rdir, self.task("T1"), 1, 0))

    def test_recovery_ticks_a_claim_whose_verify_passes(self):
        self.seed([f"- [ ] T1 — a · verify: {verify_cmd(0)}"], T1=CRASHED)
        bt_runsettle.recover_claims(self.project, self.rdir, self.work)
        t = self.task("T1")
        self.assertEqual((t["status"], "claimed_done" in t), ("done", False))
        self.assertIn("[x] T1", self.plan())
        self.assertEqual(self.state()["log"][-1]["result"], "done")
        self.assertIn("re-verified", self.state()["log"][-1]["summary"])

    def test_recovery_does_not_trust_a_claim_whose_verify_fails(self):
        self.seed([f"- [ ] T1 — a · verify: {verify_cmd(1)}"], T1=CRASHED)
        bt_runsettle.recover_claims(self.project, self.rdir, self.work)
        t = self.task("T1")
        self.assertEqual((t["status"], t["attempts"], t["tier"], "claimed_done" in t), ("todo", 1, 1, False))
        self.assertIn("[ ] T1", self.plan())
        self.assertEqual(self.state()["log"][-1]["result"], "verify_failed")

    def test_resume_verifies_the_claim_before_picking_new_work(self):
        self.seed([f"- [ ] T1 — a · verify: {verify_cmd(0)}", "- [ ] T2 — b · after: T1"], T1=CRASHED)
        self.run_sup(once=True)
        self.assertEqual(self.task("T1")["status"], "done")
        self.assertEqual(self.order_log(), ["T2:done"])  # T1 was not run again, T2 could start because T1 verified

    def test_resume_with_a_failing_claim_reruns_the_task_instead_of_unblocking_dependents(self):
        self.seed([f"- [ ] T1 — a · verify: {verify_cmd(1)}", "- [ ] T2 — b · after: T1"], T1=CRASHED)
        self.run_sup(once=True)
        self.assertEqual(self.order_log(), ["T1:done"])  # the agent had to redo T1; T2 never ran
        self.assertEqual([e["result"] for e in self.state()["log"]], ["verify_failed", "verify_failed"])
        self.assertEqual(self.task("T2")["status"], "todo")

    def test_a_run_json_from_before_claims_with_a_bare_done_is_still_trusted(self):
        self.seed(["- [ ] T1 — a · verify: " + verify_cmd(1), "- [ ] T2 — b · after: T1"], T1={"status": "done"})
        self.run_sup(once=True)
        self.assertEqual(self.order_log(), ["T2:done"])
        self.assertEqual(self.task("T1")["status"], "done")


class UsageLimitStreaks(RobustCase):
    def setUp(self):
        self.max = bt_runsettle.LIMIT_STREAK_MAX
        bt_runsettle.LIMIT_STREAK_MAX = 2

    def tearDown(self):
        bt_runsettle.LIMIT_STREAK_MAX = self.max

    def settle(self, n: int, text: str = "usage limit reached") -> str:
        return bt_runsettle.settle_task(self.project, self.rdir, "T1", n, self.settle_info(text), self.work)

    def test_long_streaks_never_add_error_hashes_escalate_or_block(self):
        self.seed(["- [ ] T1 — a"], T1={"tier": 2})
        results = [self.settle(n) for n in range(1, 13)]
        t = self.task("T1")
        self.assertEqual(results.count("limit_streak"), 6)
        self.assertEqual((t["status"], t["error_hashes"], t["tier"]), ("todo", [], 2))
        self.assertEqual((t["attempts"], t["limit_streaks"]), (0, 6))  # limits never use up the attempts
        self.assertIsNone(t.get("pending_id"))

    def test_a_streak_does_not_poison_the_next_real_failure(self):
        self.seed(["- [ ] T1 — a"])
        for n in (1, 2):
            self.settle(n)
        self.assertEqual(self.task("T1")["attempts"], 0)
        for n, reason in ((3, "alpha broke"), (4, "beta broke"), (5, "gamma broke")):
            rs.update(self.rdir, lambda s: rs.mark(s, "T1", "in_progress"))  # a session starts in_progress
            bt_runsettle.settle_task(self.project, self.rdir, "T1", n, {**self.settle_info(reason), "rc": 0}, self.work)
        t = self.task("T1")  # three real failures climb the ladder, they do not block at the first one
        self.assertEqual((t["status"], t["attempts"], t["tier"]), ("todo", 3, 2))

    def test_plain_usage_limits_below_the_streak_leave_the_task_untouched(self):
        self.seed(["- [ ] T1 — a"])
        self.assertEqual(self.settle(1), "usage_limit")
        t = self.task("T1")
        self.assertEqual((t["attempts"], t["error_hashes"], t["tier"], t["limit_streak"]), (0, [], 0, 1))

    def test_a_streak_result_sends_the_supervisor_to_wait_like_a_limit(self):
        self.assertIn("limit_streak", bt_runsettle.LIMIT_RESULTS)
        self.make_req(["- [ ] T1 — a"], {"T1": ["limit"]})
        self.run_sup(once=True)
        time.sleep(1.5)
        self.run_sup(once=True)
        self.assertEqual(self.state()["log"][-1]["result"], "limit_streak")
        self.assertEqual(self.state()["status"], "waiting")


if __name__ == "__main__":
    unittest.main()
