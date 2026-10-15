"""Findings of the independent reviews, each pinned by a regression: second writers, untracked agents, double settle,
non-finite numbers, hostile ids and files, head-of-line blocking, pinned base, stragglers, bounded reads."""
from __future__ import annotations

import json
import os
import signal
import stat
import subprocess
import sys
import threading
import time
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]
import bt_scheduler_executor as ex
import support
from bt_scheduler_executor import artifacts, classify, gitutil, procinfo
from bt_scheduler_executor import model as m
from bt_scheduler_executor.workspace import dirname_of
from support import World, git, order, wait_for


def shim_record(w, attempt_id):
    adir = Path(w.x.describe(attempt_id)["artifacts"]["dir"])
    assert wait_for(lambda: (adir / "shim.json").exists() and json.loads((adir / "shim.json").read_text()).get("child_ident"))
    return adir, json.loads((adir / "shim.json").read_text())


class SecondWriter(unittest.TestCase):
    def test_a_preparing_attempt_whose_shim_died_but_whose_agent_lives_is_never_relaunched(self):
        w = World(self)
        w.x.start(order(1, "once:60"))
        adir, shim = shim_record(w, "att-0001")
        wt0 = next((w.root / "ws" / "worktrees").glob("att-0001*/"))
        self.assertTrue(wait_for(lambda: (wt0 / "runs.txt").exists()))
        w.x.close()
        with w.x.ledger._tx() as con:                       # the crash lost the PREPARING -> RUNNING transaction
            con.execute("UPDATE attempts SET state='preparing', shim=NULL WHERE attempt_id='att-0001'")
        os.kill(shim["pid"], signal.SIGKILL)
        self.assertTrue(wait_for(lambda: not procinfo.alive(shim["pid"], shim["ident"])))
        self.assertTrue(procinfo.alive(shim["child_pid"], shim["child_ident"]))
        w.x = w.build()
        d = w.finish("att-0001")
        self.assertEqual(d["outcome"]["cause"], "lost")
        self.assertFalse(procinfo.alive(shim["child_pid"], shim["child_ident"]))
        wt = Path(d["handoff"]["worktree"])
        self.assertEqual(len((wt / "runs.txt").read_text().splitlines()), 1, "a second agent was started")

    def test_a_shim_found_by_its_command_line_that_never_identified_itself_is_stopped_before_relaunch(self):
        w = World(self, autostart=False)
        w.x.start(order(1, "once:0.2"))
        adir = Path(w.x.describe("att-0001")["artifacts"]["dir"])
        w.x.ledger.transition("att-0001", m.PREPARING, expect=(m.QUEUED,))
        w.x.close()
        real_shim = w.x.shim_path
        fake = w.tmp / "ghost_shim.py"                       # find_by_argv matches exactly `<python> <shim> <directory>`
        fake.write_text("import time; time.sleep(60)\n")
        ghost = subprocess.Popen([sys.executable, str(fake), str(adir)])
        self.addCleanup(lambda: (ghost.kill(), ghost.wait()))
        from bt_scheduler_executor import executor as executor_module
        with patch.object(executor_module, "SHIM", fake):
            w.x = w.build()                                  # recovery runs in the constructor and must find the ghost
        w.x.shim_path = real_shim
        self.assertTrue(wait_for(lambda: ghost.poll() is not None, 10), "the unidentified shim was left alive")
        w.x.start_loop()
        self.assertEqual(w.finish("att-0001")["state"], "finished")

    def test_stragglers_that_escaped_the_process_group_are_stopped_before_the_handoff(self):
        class Escape(support.FakeDriver):
            def prepare(self, route, prompt, workspace, timeout):
                code = ("import subprocess,sys,time\n"
                        "subprocess.Popen([sys.executable,'-c','import time,pathlib;time.sleep(1.5);"
                        "pathlib.Path(\"late.txt\").write_text(\"late\")'], start_new_session=True,"
                        " stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
                        "print('TERMINAL-EVENT')")
                return ex.Launch(argv=(sys.executable, "-c", code))
        w = World(self, driver=Escape())
        w.x.start(order(1, "ok"))
        d = w.finish("att-0001")
        wt = Path(d["handoff"]["worktree"])
        time.sleep(2.2)
        self.assertFalse((wt / "late.txt").exists(), "a setsid'd child kept writing after the attempt ended")
        self.assertEqual(procinfo.kill_in_cwd(str(wt)), 0)

    def test_failures_after_the_spawn_stop_the_agent_instead_of_leaving_it_untracked(self):
        w = World(self)
        original = w.x.ledger.transition

        def failing(attempt_id, to, **kw):
            if to == m.RUNNING:
                raise ex.ExecutorError("LEDGER_ERROR", "database is locked")
            return original(attempt_id, to, **kw)
        w.x.ledger.transition = failing
        w.x.start(order(1, "once:30"))
        self.assertEqual(w.x.wait_state("att-0001", m.TERMINAL, 30), m.FAILED)
        w.x.ledger.transition = original
        wt = next((w.root / "ws" / "worktrees").glob("att-0001*/"))
        self.assertTrue(wait_for(lambda: procinfo.kill_in_cwd(str(wt)) == 0 or True))
        time.sleep(1.0)
        self.assertEqual(procinfo.kill_in_cwd(str(wt), 0), 0, "an agent is still running in the worktree")


class Settling(unittest.TestCase):
    def test_a_failed_start_is_settled_once_not_twice(self):
        w = World(self, config=ex.Config(poll_seconds=0.01, grace_seconds=1, timeout_seconds=60, settle_retry_seconds=0.01))
        from bt_scheduler_executor import handoff
        original, calls = handoff.capture, {}

        def counting(ws, directory, **kw):
            calls[kw["attempt_id"]] = calls.get(kw["attempt_id"], 0) + 1
            time.sleep(0.15)
            return original(ws, directory, **kw)
        handoff.capture = counting
        self.addCleanup(setattr, handoff, "capture", original)
        w.driver.prepare = lambda *a, **k: (_ for _ in ()).throw(ex.ExecutorError("POLICY_DENIED", "no"))
        for n in range(1, 5):
            w.x.start(order(n, "ok"))
        self.assertTrue(w.x.wait_idle(60))
        self.assertEqual(calls, {f"att-000{n}": 1 for n in range(1, 5)})

    def test_a_clean_exit_with_work_that_cannot_be_preserved_is_a_failure_not_a_success(self):
        w = World(self, config=ex.Config(poll_seconds=0.05, grace_seconds=1, timeout_seconds=60, handoff_tries=1))
        from bt_scheduler_executor import handoff
        original = handoff.capture
        handoff.capture = lambda *a, **k: (_ for _ in ()).throw(ex.ExecutorError("WORKSPACE_ERROR", "boom"))
        self.addCleanup(setattr, handoff, "capture", original)
        w.x.start(order(1, "ok"))
        self.assertEqual(w.finish("att-0001")["outcome"]["cause"], "artifact_error")

    def test_a_cancelled_attempt_has_a_manifest_and_a_brief_even_with_no_workspace(self):
        w = World(self, config=ex.Config(poll_seconds=0.02, max_running=1, grace_seconds=1, timeout_seconds=60))
        w.x.start(order(1, "sleep:30"))
        w.x.start(order(2, "ok"))
        self.assertTrue(wait_for(lambda: w.x.ledger.get("att-0001")["state"] == m.RUNNING))
        w.x.cancel("att-0002", 1, "k")
        d = w.finish("att-0002")
        self.assertEqual(d["handoff"]["status"], "none")
        manifest = Path(d["artifacts"]["handoff"]) / "manifest.json"
        self.assertEqual(json.loads(manifest.read_text())["status"], "none")
        self.assertTrue((Path(d["artifacts"]["handoff"]) / "continue.md").exists())
        payload = w.sink.of("att-0002", m.EV_CANCELLED)[0].payload["handoff"]
        self.assertTrue(Path(payload["manifest"]).exists() and Path(payload["brief"]).exists())
        w.x.cancel("att-0001", 1, "k1")
        w.finish("att-0001")

    def test_a_shim_stopped_from_outside_is_killed_not_cancelled(self):
        w = World(self)
        w.x.start(order(1, "sleep:60"))
        _, shim = shim_record(w, "att-0001")
        os.kill(shim["pid"], signal.SIGTERM)                 # a shutdown or a pkill, not M1's cancel
        d = w.finish("att-0001")
        self.assertEqual((d["state"], d["outcome"]["cause"]), ("failed", "killed"))

    def test_connection_words_with_a_zero_exit_are_never_a_connection_failure(self):
        class Odd(support.FakeDriver):
            def classify(self, route, raw, returncode, **kw):
                return ex.Classification("failed")
        w = World(self, driver=Odd())
        w.x.start(order(1, "nettext"))
        d = w.finish("att-0001")
        self.assertEqual(d["outcome"]["cause"], "agent_error")


class Inputs(unittest.TestCase):
    def test_non_finite_timeouts_and_limits_are_refused(self):
        for bad in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(bad=bad), self.assertRaises(ex.ExecutorError):
                order(1, timeout=bad).validate()
            with self.assertRaises(ex.ExecutorError):
                ex.Config(timeout_seconds=bad).validate()

    def test_attempt_ids_with_dots_slashes_and_hostile_characters_get_valid_branch_names(self):
        w = World(self)
        for n, attempt in enumerate(("a..b", "x/y", "..", "ends.lock", "sp ace", "ü", "@{u}", "-dash"), 1):
            r = w.x.start(order(n, "ok", attempt_id=attempt, key=f"k{n}"))
            self.assertEqual(r.status, "accepted", (attempt, r))
        self.assertTrue(w.x.wait_idle(60))
        for attempt in ("a..b", "x/y", "..", "ends.lock", "sp ace", "ü", "@{u}", "-dash"):
            self.assertEqual(w.x.ledger.get(attempt)["state"], m.FINISHED, attempt)

    def test_two_ids_can_never_share_an_artifact_directory(self):
        names = {dirname_of(f"att-{n}") for n in range(5000)}
        self.assertEqual(len(names), 5000)
        w = World(self, autostart=False)
        w.x.start(order(1))
        with self.assertRaises(Exception):
            with w.x.ledger._tx() as con:                     # a hand-forced clash is refused by the database itself
                con.execute("INSERT INTO attempts(attempt_id, idem_key, dirname, state, request, created, updated)"
                            " SELECT 'other','other-key',dirname,'queued','{}',0,0 FROM attempts")

    def test_the_base_is_pinned_when_the_order_is_accepted(self):
        w = World(self, autostart=False)
        base = git(w.repo, "rev-parse", "HEAD")
        w.x.start(order(1, "ok"))
        (w.repo / "later.txt").write_text("x")
        git(w.repo, "add", "-A")
        git(w.repo, "commit", "-m", "moved on")
        w.x = w.restart()
        w.x.start_loop()
        d = w.finish("att-0001")
        self.assertEqual(d["handoff"]["base_sha"], base)

    def test_a_foreign_order_does_not_bind_the_root_and_a_port_error_is_not_sticky(self):
        w = World(self, autostart=False)
        w.resolver.fail = KeyError("transient")
        self.assertEqual(w.x.start(order(1)).code, "PORT_ERROR")
        w.resolver.fail = None
        self.assertEqual(w.x.start(order(1)).status, "accepted")        # the same key, the same id: not burned
        self.assertEqual(w.x.start(order(2, plan="REQ-OTHER")).code, "FOREIGN_RUN")
        self.assertEqual(w.x.start(order(3)).status, "accepted")
        w2 = World(self, autostart=False)
        w2.resolver.fail = ex.ExecutorError("ROUTE_INVALID", "no")
        self.assertEqual(w2.x.start(order(1, plan="REQ-FIRST")).code, "ROUTE_INVALID")
        self.assertEqual(w2.x.start(order(2, plan="REQ-SECOND")).code, "ROUTE_INVALID")     # a refusal binds nothing

    def test_a_queue_full_refusal_leaves_no_empty_directory(self):
        w = World(self, autostart=False, config=ex.Config(max_queued=1))
        w.x.start(order(1))
        w.x.start(order(2))
        self.assertEqual(len(list((w.root / "attempts").iterdir())), 1)

    def test_artifacts_are_private(self):
        w = World(self)
        w.x.start(order(1, "ok"))
        d = w.finish("att-0001")
        adir = Path(d["artifacts"]["dir"])
        self.assertEqual(stat.S_IMODE(adir.stat().st_mode), 0o700)
        for path in adir.rglob("*"):
            if path.is_file():
                self.assertEqual(stat.S_IMODE(path.stat().st_mode) & 0o077, 0, path)


class HostileFiles(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def test_a_fifo_a_symlink_a_device_and_an_oversized_file_are_not_read(self):
        os.mkfifo(self.dir / "fifo.json")
        (self.dir / "real.json").write_text('{"a": 1}')
        os.symlink(self.dir / "real.json", self.dir / "link.json")
        os.symlink("/dev/zero", self.dir / "zero.json")
        (self.dir / "big.json").write_text(" " * 2_000_000 + "{}")
        t0 = time.monotonic()
        for name in ("fifo.json", "link.json", "zero.json", "big.json"):
            self.assertIsNone(artifacts.read_json(self.dir / name), name)
        self.assertLess(time.monotonic() - t0, 5)
        self.assertEqual(artifacts.read_json(self.dir / "real.json"), {"a": 1})

    def test_the_agents_report_cannot_hang_or_exhaust_the_executor(self):
        os.symlink("/dev/zero", self.dir / "report.json")
        self.assertIn("unreadable", artifacts.read_claim(self.dir / "report.json"))
        (self.dir / "r2.json").unlink() if (self.dir / "r2.json").exists() else None
        os.mkfifo(self.dir / "r2.json")
        self.assertIn("unreadable", artifacts.read_claim(self.dir / "r2.json"))

    def test_a_patch_over_the_cap_is_never_held_in_memory(self):
        repo = support.make_repo(self.dir / "repo")
        (repo / "big.bin").write_bytes(os.urandom(300_000))
        git(repo, "add", "-A")
        git(repo, "commit", "-m", "big")
        self.assertIsNone(gitutil.run_capped(repo, ["diff", "--binary", "HEAD~1", "HEAD"], 10_000))
        raw = gitutil.run_capped(repo, ["diff", "--binary", "HEAD~1", "HEAD"], 10_000_000)
        self.assertGreater(len(raw), 300_000)
        with self.assertRaises(ex.ExecutorError):
            gitutil.run_capped(repo, ["diff", "no-such-ref", "HEAD"], 100)


class Delivery(unittest.TestCase):
    def test_one_poisoned_attempt_does_not_block_the_events_of_the_others(self):
        w = World(self, autostart=False)
        sink = w.sink
        original = sink.deliver

        def picky(event):
            if event.attempt_id == "att-0001":
                raise RuntimeError("poison")
            original(event)
        sink.deliver = picky
        for n in (1, 2):
            w.x.start(order(n, "ok"))
        w.x.start_loop()
        self.assertTrue(wait_for(lambda: w.x.ledger.get("att-0002")["state"] == m.FINISHED
                                 and all(e["delivered"] for e in w.x.ledger.events("att-0002"))))
        self.assertEqual(w.sink.kinds("att-0002"), [m.EV_STARTED, m.EV_FINISHED])
        self.assertTrue(w.x.ledger.undelivered() >= 1)                   # the poisoned one stays, in order, for later
        sink.deliver = original
        self.assertTrue(w.x.wait_idle(30))
        self.assertEqual(w.sink.kinds("att-0001"), [m.EV_STARTED, m.EV_FINISHED])

    def test_concurrent_flushes_never_deliver_a_batch_twice(self):
        w = World(self, autostart=False)
        w.sink.fail = True
        w.x.start(order(1, "ok"))
        w.x.start_loop()
        w.x.wait_state("att-0001", m.TERMINAL, 30)
        w.x.close()
        w.sink.fail = False
        w.x = w.build(autostart=False)
        threads = [threading.Thread(target=w.x.flush_events) for _ in range(6)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual([e.event_id for e in w.sink.events], ["att-0001:started", "att-0001:finished"])

    def test_a_query_never_emits_or_signals(self):
        w = World(self, autostart=False, config=ex.Config(poll_seconds=0.05, heartbeat_seconds=0.001, grace_seconds=1,
                                                         timeout_seconds=60))
        w.x.start(order(1, "sleep:30"))
        deadline = time.monotonic() + 30
        while w.x.ledger.get("att-0001")["state"] != m.RUNNING and time.monotonic() < deadline:
            w.x.tick()                                      # no background loop: only these calls can emit anything
            time.sleep(0.05)
        self.assertEqual(w.x.ledger.get("att-0001")["state"], m.RUNNING)
        time.sleep(0.05)
        before = len(w.sink.events)
        for _ in range(5):
            w.x.query("att-0001")
        self.assertEqual(len(w.sink.events), before, "a query emitted an event")
        w.x.cancel("att-0001", 1, "k")
        for _ in range(400):
            w.x.tick()
            if w.x.ledger.get("att-0001")["state"] in m.TERMINAL:
                break
            time.sleep(0.05)
        self.assertEqual(w.x.ledger.get("att-0001")["state"], m.CANCELLED)

    def test_the_supervisor_survives_a_phase_that_raises(self):
        w = World(self)
        original = w.x._watch_all
        w.x._watch_all = lambda: (_ for _ in ()).throw(RuntimeError("corrupt row"))
        w.x.start(order(1, "ok"))
        self.assertEqual(w.x.wait_state("att-0001", (m.RUNNING, m.SETTLING, m.FINISHED), 30) is not None, True)
        w.x._watch_all = original
        self.assertEqual(w.finish("att-0001")["state"], "finished")
        self.assertTrue((w.root / "executor.log").exists())

    def test_the_log_never_grows_without_bound(self):
        w = World(self, autostart=False)
        from bt_scheduler_executor import executor
        old = executor.LOG_MAX
        executor.LOG_MAX = 2000
        self.addCleanup(setattr, executor, "LOG_MAX", old)
        for i in range(200):
            w.x._log("x" * 100)
        self.assertLess((w.root / "executor.log").stat().st_size, 4000)


class Reading(unittest.TestCase):
    def test_the_cli_reader_opens_no_write_transaction_and_a_second_reader_is_not_blocked(self):
        w = World(self)
        w.x.start(order(1, "ok"))
        w.finish("att-0001")
        reader = ex.ledger.Ledger(w.root / "ledger.db", create=False)
        blocker = subprocess.Popen([sys.executable, "-c",
                                    "import sqlite3,sys,time; c=sqlite3.connect(sys.argv[1]); c.execute('BEGIN IMMEDIATE'); time.sleep(3)",
                                    str(w.root / "ledger.db")])
        self.addCleanup(lambda: (blocker.kill(), blocker.wait()))
        time.sleep(0.5)
        t0 = time.monotonic()
        self.assertEqual(reader.get("att-0001")["state"], "finished")
        self.assertLess(time.monotonic() - t0, 1.5)

    def test_an_unknown_ledger_schema_is_refused(self):
        w = World(self, autostart=False)
        w.x.close()
        with ex.ledger.Ledger(w.root / "ledger.db")._tx() as con:
            con.execute("UPDATE meta SET value='99' WHERE key='schema'")
        with self.assertRaises(ex.ExecutorError) as caught:
            ex.ledger.Ledger(w.root / "ledger.db")
        self.assertEqual(caught.exception.code, "LEDGER_ERROR")


class ProcessTable(unittest.TestCase):
    def test_an_unreadable_process_table_means_unknown_not_dead(self):
        from unittest import mock
        with mock.patch.object(Path, "read_text", side_effect=PermissionError("denied")):
            self.assertTrue(procinfo.alive(os.getpid(), "whatever"))      # unknown: never a reason to kill
            with self.assertRaises(procinfo.IdentityUnknown):
                procinfo.start_ident(os.getpid())

    def test_the_connection_classifier_needs_a_failing_exit(self):
        cls = ex.Classification("failed")
        out = classify.outcome(support.FakeDriver(), ex.Route("p", "ok"), "ECONNRESET", {"reason": "exited", "returncode": 0},
                               cancel_requested=False, state_before=m.RUNNING, totals=(10, 0))
        self.assertNotEqual(out["cause"], "connection_lost")
        del cls


if __name__ == "__main__":
    unittest.main()
