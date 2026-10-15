"""T7: the run loop — queue, allocate, spawn, watch, settle — for the whole happy and unhappy paths."""
from __future__ import annotations

import json
import os
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]
import bt_scheduler_executor as ex
from bt_scheduler_executor import model as m
from support import World, git, order, wait_for


class Run(unittest.TestCase):
    def test_a_clean_run_has_started_then_finished_and_the_worktree_holds_the_work(self):
        w = World(self)
        self.assertEqual(w.x.start(order(1, "commit")).status, "accepted")
        d = w.finish("att-0001")
        self.assertEqual((d["state"], d["outcome"]["cause"]), ("finished", "clean"))
        self.assertEqual(w.sink.kinds("att-0001"), [m.EV_STARTED, m.EV_FINISHED])
        self.assertTrue((Path(d["handoff"]["worktree"]) / "feature.txt").exists())
        self.assertTrue(wait_for(lambda: not w.strays(), 10), w.strays())
        self.assertEqual(w.x.query("att-0001").state, "finished")

    def test_finished_means_the_agent_stopped_never_that_the_task_is_done(self):
        w = World(self)
        w.x.start(order(1, "ok"))
        w.finish("att-0001")
        event = w.sink.of("att-0001", m.EV_FINISHED)[0]
        self.assertIn("independent verifier", event.payload["note"])
        self.assertNotIn("accepted", json.dumps(event.payload).lower().replace("acceptance", ""))

    def test_event_ids_are_deterministic_and_carry_the_order_identity(self):
        w = World(self)
        w.x.start(order(7, "ok", token=42))
        w.finish("att-0007")
        ids = [e.event_id for e in w.sink.events]
        self.assertEqual(ids, ["att-0007:started", "att-0007:finished"])
        for e in w.sink.events:
            self.assertEqual((e.plan_id, e.revision, e.task_id, e.attempt_id, e.token), ("REQ-T", 1, "T7", "att-0007", 42))

    def test_the_started_event_names_the_route_worktree_and_artifacts_but_no_secret(self):
        w = World(self)
        w.x.start(order(1, "ok"))
        w.finish("att-0001")
        p = w.sink.of("att-0001", m.EV_STARTED)[0].payload
        self.assertEqual((p["provider"], p["model"], p["profile"], p["effort"]), ("fake", "ok", "acct-1", "low"))
        self.assertTrue(Path(p["worktree"]).is_dir())
        self.assertNotIn("secret-for", json.dumps(p))

    def test_the_child_gets_the_profile_environment_and_loses_the_other_profiles_secrets(self):
        w = World(self)
        with mock.patch.dict(os.environ, {"OTHER_PROFILE_SECRET": "leak-me", "AMBIENT_KEEP": "kept"}):
            w.x.start(order(1, "env:OTHER_PROFILE_SECRET,PROFILE_TOKEN,AMBIENT_KEEP"))
            d = w.finish("att-0001")
        env = (Path(d["handoff"]["worktree"]) / "env.txt").read_text().splitlines()
        self.assertEqual(env, ["OTHER_PROFILE_SECRET=<unset>", "PROFILE_TOKEN=secret-for-acct-1", "AMBIENT_KEEP=kept"])

    def test_no_secret_reaches_the_ledger_the_artifacts_or_the_events(self):
        w = World(self)
        w.x.start(order(1, "env:PROFILE_TOKEN"))
        w.finish("att-0001")
        found = []
        for path in w.root.rglob("*"):
            if path.is_file() and not path.name.endswith(("-wal", "-shm")):
                if b"secret-for" in path.read_bytes() and path.name not in ("env.txt", "changes.patch"):
                    found.append(path)
        self.assertEqual(found, [], found)

    def test_the_prompt_is_task_text_and_rules_and_is_private(self):
        w = World(self)
        w.x.start(order(1, "ok"))
        d = w.finish("att-0001")
        prompt = Path(d["artifacts"]["prompt"])
        text = prompt.read_text()
        for needle in ("Task T1", "thing is done", "Do not push", "isolated git worktree", "Do not declare the task verified"):
            self.assertIn(needle, text)
        self.assertEqual(prompt.stat().st_mode & 0o777, 0o600)

    def test_the_agents_own_report_is_only_a_claim(self):
        from bt_scheduler_executor import artifacts
        path = Path(self.id().replace(".", "_") + ".json")
        d = World(self)
        f = d.tmp / "report.json"
        f.write_text(json.dumps({"status": "done", "summary": "all good", "x": 1}))
        claim = artifacts.read_claim(f)
        self.assertEqual(claim, {"status": "done", "summary": "all good", "claimed": True})
        f.write_text("not json")
        self.assertIsNone(artifacts.read_claim(f))
        f.write_text("x" * 70_000)
        self.assertIn("unreadable", artifacts.read_claim(f))
        del path

    def test_the_concurrency_ceiling_is_never_exceeded_and_the_rest_wait_in_the_queue(self):
        w = World(self, config=ex.Config(poll_seconds=0.02, max_running=2, grace_seconds=1, timeout_seconds=60))
        for n in range(1, 7):
            w.x.start(order(n, "sleep:0.4"))
        peak = 0
        deadline = time.monotonic() + 40
        while time.monotonic() < deadline and w.x.ledger.count(m.TERMINAL) < 6:
            peak = max(peak, w.x.ledger.count((m.PREPARING, m.RUNNING)))
            time.sleep(0.01)
        self.assertEqual(w.x.ledger.count((m.FINISHED,)), 6,
                         [(r["attempt_id"], r["state"], (r.get("outcome") or {}).get("cause"))
                          for r in w.x.ledger.in_states(m.TERMINAL) if r["state"] != m.FINISHED])
        self.assertEqual(peak, 2)

    def test_tasks_run_in_queue_order(self):
        w = World(self, config=ex.Config(poll_seconds=0.02, max_running=1, grace_seconds=1, timeout_seconds=60))
        for n in range(1, 5):
            w.x.start(order(n, "ok"))
        w.x.wait_idle(40)
        started = [e.attempt_id for e in w.sink.events if e.kind == m.EV_STARTED]
        self.assertEqual(started, [f"att-000{n}" for n in range(1, 5)])

    def test_a_failing_sink_never_blocks_the_attempt_and_events_are_redelivered_in_order(self):
        w = World(self)
        w.sink.fail = True
        w.x.start(order(1, "ok"))
        self.assertEqual(w.x.wait_state("att-0001", m.TERMINAL, 30), m.FINISHED)
        self.assertEqual(w.sink.events, [])
        self.assertEqual(w.x.ledger.undelivered(), 2)
        w.sink.fail = False
        self.assertTrue(w.x.wait_idle(30))
        self.assertEqual([e.event_id for e in w.sink.events], ["att-0001:started", "att-0001:finished"])

    def test_redelivery_after_a_crash_between_delivery_and_marking_is_idempotent_by_id(self):
        w = World(self)
        w.x.start(order(1, "ok"))
        w.finish("att-0001")
        for row in w.x.ledger.events():                       # pretend the "delivered" marks were lost
            with w.x.ledger._tx() as con:
                con.execute("UPDATE events SET delivered=0 WHERE event_id=?", (row["event_id"],))
        w.x.flush_events()
        ids = [e.event_id for e in w.sink.events]
        self.assertEqual(sorted(set(ids)), sorted(["att-0001:started", "att-0001:finished"]))
        self.assertEqual(len(ids), 4)                           # at least once: duplicates are the sink's to dedupe by id

    def test_heartbeats_are_hints_not_stored_and_stop_with_the_process(self):
        w = World(self, config=ex.Config(poll_seconds=0.02, heartbeat_seconds=0.1, grace_seconds=1, timeout_seconds=60))
        w.x.start(order(1, "sleep:1.0"))
        w.finish("att-0001")
        beats = [e for e in w.sink.events if e.kind == m.EV_HEARTBEAT]
        self.assertGreaterEqual(len(beats), 2)
        self.assertEqual(len({e.event_id for e in beats}), len(beats))
        self.assertEqual([r["kind"] for r in w.x.ledger.events()], [m.EV_STARTED, m.EV_FINISHED])
        count = len(beats)
        time.sleep(0.4)
        self.assertEqual(len([e for e in w.sink.events if e.kind == m.EV_HEARTBEAT]), count)

    def test_a_heartbeat_sink_error_is_ignored(self):
        w = World(self, config=ex.Config(poll_seconds=0.02, heartbeat_seconds=0.05, grace_seconds=1, timeout_seconds=60))
        original = w.sink.deliver

        def flaky(event):
            if event.kind == m.EV_HEARTBEAT:
                raise RuntimeError("no")
            original(event)
        w.sink.deliver = flaky
        w.x.start(order(1, "sleep:0.5"))
        self.assertEqual(w.finish("att-0001")["state"], "finished")

    def test_the_orders_timeout_wins_over_the_default_and_both_are_capped(self):
        w = World(self, config=ex.Config(poll_seconds=0.02, grace_seconds=1, timeout_seconds=50, max_timeout_seconds=100))
        w.x.start(order(1, "ok", timeout=7))
        w.x.start(order(2, "ok"))
        w.x.start(order(3, "ok", timeout=10_000))
        w.x.wait_idle(30)
        self.assertEqual(w.driver.timeouts, [7, 50, 100])

    def test_a_timeout_is_a_failure_with_its_own_cause_and_the_work_is_kept(self):
        w = World(self)
        w.x.start(order(1, "sleep:60", timeout=1))
        d = w.finish("att-0001")
        self.assertEqual((d["state"], d["outcome"]["cause"]), ("failed", "timeout"))
        self.assertTrue((Path(d["handoff"]["worktree"]) / "started.txt").exists())
        self.assertTrue(d["handoff"]["dirty"])

    def test_a_missing_provider_binary_is_start_failed_with_an_empty_handoff(self):
        w = World(self)
        w.driver.prepare = lambda route, prompt, workspace, timeout: ex.Launch(argv=("/no/such/provider",))
        w.x.start(order(1, "ok"))
        d = w.finish("att-0001")
        self.assertEqual((d["state"], d["outcome"]["cause"]), ("failed", "start_failed"))
        self.assertTrue(d["handoff"]["empty"])
        self.assertEqual(w.sink.kinds("att-0001"), [m.EV_FAILED] if False else [m.EV_STARTED, m.EV_FAILED])

    def test_a_driver_that_refuses_at_launch_time_fails_the_attempt_before_any_process(self):
        w = World(self)

        def refuse(route, prompt, workspace, timeout):
            raise ex.ExecutorError("POLICY_DENIED", "work-only profile used outside a work project")
        w.driver.prepare = refuse
        w.x.start(order(1, "ok"))
        d = w.finish("att-0001")
        self.assertEqual(d["outcome"]["cause"], "start_failed")
        self.assertIn("POLICY_DENIED", d["outcome"]["detail"])
        self.assertEqual(w.sink.kinds("att-0001"), [m.EV_FAILED])          # it never started

    def test_a_brief_source_that_blows_up_is_a_failed_start_not_a_stuck_attempt(self):
        class Bad:
            def brief(self, request):
                raise KeyError("task missing")
        w = World(self, briefs=Bad())
        w.x.start(order(1, "ok"))
        d = w.finish("att-0001")
        self.assertEqual((d["state"], d["outcome"]["cause"]), ("failed", "start_failed"))
        self.assertIn("PORT_ERROR", d["outcome"]["detail"])

    def test_every_attempt_ends_in_exactly_one_terminal_event(self):
        w = World(self)
        for n, s in enumerate(("ok", "crash", "quota", "partial", "net", "commit"), 1):
            w.x.start(order(n, s))
        w.x.wait_idle(40)
        for n in range(1, 7):
            terminal = [e for e in w.sink.events if e.attempt_id == f"att-000{n}"
                        and e.kind in (m.EV_FINISHED, m.EV_FAILED, m.EV_CANCELLED)]
            self.assertEqual(len(terminal), 1, n)

    def test_query_reports_the_live_state_while_running(self):
        w = World(self)
        w.x.start(order(1, "sleep:30"))
        self.assertTrue(wait_for(lambda: w.x.query("att-0001").state == "running"))
        self.assertTrue(wait_for(lambda: (Path(w.x.describe("att-0001")["artifacts"]["dir"]) / "shim.json").exists()))
        w.x.cancel("att-0001", 1, "k")
        w.finish("att-0001")

    def test_two_attempts_of_one_task_over_time_get_distinct_worktrees(self):
        w = World(self)
        w.x.start(order(1, "ok"))
        a = w.finish("att-0001")
        req = order(2, "ok")
        req = ex.StartRequest(**{**req.__dict__, "task_id": "T1"})
        w.x.start(req)
        b = w.finish("att-0002")
        self.assertNotEqual(a["handoff"]["worktree"], b["handoff"]["worktree"])
        self.assertTrue(Path(a["handoff"]["worktree"]).is_dir())

    def test_artifacts_live_under_attempts_and_nothing_is_written_to_the_main_checkout(self):
        w = World(self)
        before = git(w.repo, "status", "--porcelain")
        w.x.start(order(1, "dirty"))
        w.finish("att-0001")
        self.assertEqual(git(w.repo, "status", "--porcelain"), before)
        self.assertEqual((w.repo / "README.md").read_text(), "original\n")
        adir = next((w.root / "attempts").iterdir())
        for name in ("order.json", "route.json", "prompt.txt", "output.log", "exit.json", "shim.json"):
            self.assertTrue((adir / name).exists(), name)
        self.assertTrue((adir / "handoff" / "manifest.json").exists())

    def test_close_leaves_agents_running_and_a_new_executor_finishes_the_job(self):
        w = World(self)
        w.x.start(order(1, "sleep:1.5"))
        self.assertTrue(wait_for(lambda: w.x.ledger.get("att-0001")["state"] == m.RUNNING))
        x2 = w.restart()
        self.assertIs(w.x, x2)
        self.assertEqual(w.finish("att-0001")["state"], "finished")
        self.assertEqual([e.event_id for e in w.sink.events].count("att-0001:finished"), 1)


if __name__ == "__main__":
    unittest.main()
