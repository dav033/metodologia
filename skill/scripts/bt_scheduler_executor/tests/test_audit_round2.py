"""Round-2 audit regressions: forged agent records, PREPARING re-drive, shared workspaces, replayed single-use routes,
and executor roots that share one repository."""
from __future__ import annotations

import json
import os
import signal
import sys
import time
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]
import bt_scheduler_executor as ex
from bt_scheduler_executor import artifacts, procinfo
from bt_scheduler_executor import model as m
from support import FakeDriver, FakeResolver, World, git, order, wait_for


def shim_record(w, attempt_id):
    adir = Path(w.x.describe(attempt_id)["artifacts"]["dir"])
    assert wait_for(lambda: (adir / "shim.json").exists() and json.loads((adir / "shim.json").read_text()).get("child_ident"))
    return adir, json.loads((adir / "shim.json").read_text())


class ForgedExit(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def read(self, payload):
        (self.dir / "exit.json").write_text(payload)
        return artifacts.read_exit(self.dir / "exit.json")

    def test_a_record_that_is_not_what_the_shim_writes_is_lost_not_trusted(self):
        for payload in ('[1, 2]', '"exited"', '{"reason": "exited", "returncode": "0"}', '{"reason": "exited", "returncode": true}',
                        '{"reason": "success", "returncode": 0}', '{"reason": ["exited"]}'):
            info = self.read(payload)
            self.assertEqual(info["reason"], "lost", payload)
            self.assertTrue(info["adopt_orphan"], payload)

    def test_a_null_or_hostile_counter_is_zero_not_a_crash(self):
        info = self.read('{"reason": "exited", "returncode": 0, "output_bytes": null, "dropped_bytes": "x", "child_pid": -5}')
        self.assertEqual((info["reason"], info["returncode"], info["output_bytes"], info["dropped_bytes"]),
                         ("exited", 0, 0, 0))
        self.assertNotIn("child_pid", info)

    def test_a_record_that_appears_between_the_read_and_the_existence_check_is_not_lost(self):
        from unittest.mock import patch
        (self.dir / "exit.json").write_text('{"reason": "exited", "returncode": 0}')
        real, calls = artifacts.read_json, []

        def late(path, *args, **kwargs):
            calls.append(path)
            return None if len(calls) == 1 else real(path, *args, **kwargs)     # absent at the first read, there afterwards

        with patch.object(artifacts, "read_json", late):
            info = artifacts.read_exit(self.dir / "exit.json")
        self.assertEqual((info["reason"], info["returncode"]), ("exited", 0))

    def test_an_absent_record_is_none_and_a_present_unreadable_one_is_lost(self):
        self.assertIsNone(artifacts.read_exit(self.dir / "exit.json"))
        os.mkfifo(self.dir / "exit.json")
        self.assertEqual(artifacts.read_exit(self.dir / "exit.json")["reason"], "lost")

    def test_a_forged_record_beside_a_dead_agent_ends_the_attempt_lost_never_stuck_running(self):
        w = World(self)
        w.x.start(order(1, "sleep:60"))
        adir, shim = shim_record(w, "att-0001")
        w.x.close()
        os.killpg(shim["child_pid"], signal.SIGKILL)
        os.kill(shim["pid"], signal.SIGKILL)
        self.assertTrue(wait_for(lambda: not procinfo.alive(shim["pid"], shim["ident"])))
        (adir / "exit.json").write_text('{"reason": "exited", "returncode": ["not", "an", "int"], "output_bytes": null}')
        w.x = w.build()
        d = w.finish("att-0001")
        self.assertEqual((d["state"], d["outcome"]["cause"]), ("failed", "lost"))


class ForgedExitWhileAlive(unittest.TestCase):
    def test_a_well_formed_forgery_never_leaves_the_real_agent_running_after_the_attempt_ends(self):
        from unittest.mock import patch
        w = World(self)
        w.x.start(order(1, "sleep:60"))
        adir, shim = shim_record(w, "att-0001")
        self.assertTrue(procinfo.alive(shim["child_pid"], shim["child_ident"]))
        (adir / "exit.json").write_text('{"reason": "exited", "returncode": 0, "output_bytes": 0}')   # the agent forges it
        with patch.object(procinfo, "kill_in_cwd", lambda *a, **k: 0):   # an agent whose cwd is outside the worktree
            d = w.finish("att-0001")
        self.assertIn(d["state"], ("finished", "failed"))
        self.assertTrue(wait_for(lambda: not procinfo.alive(shim["child_pid"], shim["child_ident"]), 10),
                        "the agent kept running after its attempt was settled")


class SettleRetries(unittest.TestCase):
    def test_a_retried_settle_does_not_sweep_the_worktree_again(self):
        from unittest.mock import patch
        cfg = ex.Config(poll_seconds=0.05, heartbeat_seconds=3600, grace_seconds=1.0, timeout_seconds=60,
                        settle_retry_seconds=0.2)
        w = World(self, config=cfg)
        sweeps, real_sweep, real_preserve, failed = [], procinfo.kill_in_cwd, w.x._preserve, []

        def counting(directory, *args, **kwargs):
            sweeps.append(directory)
            return real_sweep(directory, *args, **kwargs)

        def flaky(row, outcome, adir):
            if not failed:
                failed.append(1)
                raise OSError("disk hiccup")                  # the settle fails once after the sweep, then is retried
            return real_preserve(row, outcome, adir)

        w.x._preserve = flaky
        with patch.object(procinfo, "kill_in_cwd", counting):
            w.x.start(order(1, "ok"))
            d = w.finish("att-0001")
        self.assertEqual(d["state"], "finished")
        self.assertEqual(failed, [1], "the settle was never retried")
        self.assertEqual(len(sweeps), 1, sweeps)


class SweepSparesTheOperator(unittest.TestCase):
    """P-032: an interactive shell or editor opened in the worktree is not something the agent left behind."""

    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.children: list[int] = []
        self.addCleanup(self._reap)

    def _reap(self):
        for pid in self.children:
            try:
                os.kill(pid, signal.SIGKILL)
                os.waitpid(pid, 0)
            except OSError:
                pass

    def interactive_in_worktree(self) -> int:
        """A process with a controlling terminal (a pty, like a terminal emulator's shell) whose cwd is the worktree."""
        import pty
        pid, _fd = pty.fork()
        if pid == 0:
            os.chdir(self.dir)
            os.execvp("sleep", ["sleep", "60"])
        self.children.append(pid)
        self.assertTrue(wait_for(lambda: os.path.realpath(f"/proc/{pid}/cwd") == os.path.realpath(self.dir)))
        return pid

    def test_an_interactive_process_that_is_not_the_agents_descendant_is_spared(self):
        pid = self.interactive_in_worktree()
        self.assertEqual(procinfo.kill_in_cwd(str(self.dir), 0, spare_interactive=True), 0)
        self.assertEqual(procinfo.kill_in_cwd(str(self.dir), 0, spare_interactive=False), 1)      # the old rule would hit it
        self.assertTrue(procinfo.start_ident(pid))

    def test_a_terminal_identity_is_rechecked_after_opening_its_pidfd(self):
        from unittest.mock import patch
        pid = self.interactive_in_worktree()
        ident = procinfo.start_ident(pid)
        self.assertTrue(ident)
        real_pidfd_open = os.pidfd_open
        with patch.object(procinfo.os, "pidfd_open", wraps=real_pidfd_open) as open_pidfd, \
                patch.object(procinfo, "start_ident", return_value=f"{ident}:recycled") as read_ident, \
                patch.object(procinfo.signal, "pidfd_send_signal") as send_signal:
            self.assertEqual(procinfo.kill_in_cwd(str(self.dir), spare_interactive=True,
                                                   known_descendants={pid: ident}), 0)
        open_pidfd.assert_called_once_with(pid, 0)
        read_ident.assert_called_once_with(pid)
        send_signal.assert_not_called()
        self.assertTrue(procinfo.alive(pid, ident), "the process must survive a mismatched identity")

    def test_a_terminal_is_preserved_when_pidfds_are_unavailable(self):
        from unittest.mock import patch
        pid = self.interactive_in_worktree()
        with patch.object(procinfo.os, "pidfd_open", None):
            self.assertEqual(procinfo.kill_in_cwd(str(self.dir), spare_interactive=True,
                                                  known_descendants={pid: procinfo.start_ident(pid)}), 0)
        self.assertTrue(procinfo.start_ident(pid), "without pidfd support the sweep must preserve terminal processes")

    def test_the_real_executor_sweeps_an_agent_terminal_child_after_the_agent_exits(self):
        class TerminalDriver(FakeDriver):
            def prepare(inner_self, route, prompt, workspace, timeout_seconds):
                code = (
                    "import os, pty, signal, sys, time\n"
                    "pid, master = pty.fork()\n"
                    "if pid == 0:\n"
                    "    signal.signal(signal.SIGHUP, signal.SIG_IGN)\n"
                    "    os.execlp('sleep', 'sleep', '60')\n"
                    "open(sys.argv[1], 'w').write(str(pid))\n"
                    "time.sleep(0.6)\n"
                    "os.close(master)\n"
                    "print('TERMINAL-EVENT', flush=True)\n"
                )
                return ex.Launch(argv=(sys.executable, "-c", code, str(Path(workspace.path) / "terminal.pid")))

        w = World(self, driver=TerminalDriver())
        w.x.start(order(1, "terminal"))
        self.assertTrue(wait_for(lambda: (w.x.ledger.get("att-0001") or {}).get("workspace")))
        wt = Path(w.x.ledger.get("att-0001")["workspace"]["path"])
        self.assertTrue(wait_for(lambda: (wt / "terminal.pid").exists()
                                 and (wt / "terminal.pid").read_text().strip().isdigit()))
        pid = int((wt / "terminal.pid").read_text())
        ident = procinfo.start_ident(pid)
        self.assertTrue(ident, "the agent's terminal child must outlive its parent until settle")

        result = w.finish("att-0001")

        self.assertEqual(result["state"], m.FINISHED)
        self.assertTrue(wait_for(lambda: not procinfo.alive(pid, ident)), "the orphaned terminal child survived settle")

    def test_an_orphaned_agent_terminal_process_is_swept_from_its_recorded_identity(self):
        from support import World
        pid = self.interactive_in_worktree()
        ident = procinfo.start_ident(pid)
        self.assertTrue(ident)
        w = World(self, autostart=False)
        adir = w.x.attempts_dir / "att-orphan"
        adir.mkdir()
        (adir / "descendants.json").write_text(json.dumps({"version": 1, "truncated": False,
                                                            "processes": [{"pid": pid, "ident": ident}]}))

        w.x._sweep({"workspace": {"path": str(self.dir)}}, adir)

        self.assertTrue(wait_for(lambda: not procinfo.alive(pid, ident)))

    def test_an_unmatched_identity_in_the_descendant_record_does_not_kill_an_operator_terminal(self):
        from support import World
        pid = self.interactive_in_worktree()
        ident = procinfo.start_ident(pid)
        self.assertTrue(ident)
        w = World(self, autostart=False)
        adir = w.x.attempts_dir / "att-recycled"
        adir.mkdir()
        (adir / "descendants.json").write_text(json.dumps({"version": 1, "truncated": False,
                                                            "processes": [{"pid": pid, "ident": f"{ident}:old"}]}))

        w.x._sweep({"workspace": {"path": str(self.dir)}}, adir)

        self.assertTrue(procinfo.alive(pid, ident), "a recycled PID must not identify an agent-owned terminal")

    def test_an_invalid_descendant_record_is_ignored(self):
        from support import World
        pid = self.interactive_in_worktree()
        ident = procinfo.start_ident(pid)
        self.assertTrue(ident)
        w = World(self, autostart=False)
        adir = w.x.attempts_dir / "att-invalid"
        adir.mkdir()
        (adir / "descendants.json").write_text(json.dumps({"version": True, "truncated": False,
                                                            "processes": [{"pid": pid, "ident": ident}]}))

        w.x._sweep({"workspace": {"path": str(self.dir)}}, adir)

        self.assertTrue(procinfo.alive(pid, ident), "unvalidated process evidence must not cause a signal")

    def test_an_oversized_descendant_record_is_ignored(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "descendants.json"
            records = [{"pid": pid, "ident": f"boot:{pid}"} for pid in range(1, 4098)]
            path.write_text(json.dumps({"version": 1, "truncated": False, "processes": records}))
            self.assertEqual(artifacts.read_descendants(path), {})

    def test_the_agents_pty_child_is_swept_only_while_the_agent_is_alive(self):
        self.interactive_in_worktree()
        # the child's parent is this process: pretend this process is the (live) attempt's agent
        self.assertEqual(procinfo.kill_in_cwd(str(self.dir), 0, roots={os.getpid()}, spare_interactive=True), 1)
        # once the agent is gone nothing links the child to it: an orphaned terminal process is spared (documented limit)
        self.assertEqual(procinfo.kill_in_cwd(str(self.dir), 0, roots={1 << 30}, spare_interactive=True), 0)

    def test_the_operator_can_turn_sparing_off_and_everything_in_the_worktree_is_swept(self):
        from unittest.mock import patch
        seen = {}
        with patch.object(procinfo, "kill_in_cwd", lambda d, *a, **k: seen.update(k) or 0):
            w = World(self, config=ex.Config(poll_seconds=0.05, heartbeat_seconds=3600, grace_seconds=1.0,
                                             timeout_seconds=60, spare_interactive=False))
            w.x.start(order(1, "ok"))
            w.finish("att-0001")
        self.assertIs(seen.get("spare_interactive"), False)

    def test_a_recycled_pid_is_never_a_sweep_root(self):
        w = World(self, autostart=False)
        adir = w.x.attempts_dir / "att-x"
        adir.mkdir(parents=True)
        (adir / "shim.json").write_text(json.dumps({"pid": os.getpid(), "ident": "not-this-process",
                                                    "child_pid": 1, "child_ident": "nope"}))
        self.assertEqual(w.x._sweep_roots(adir), {})
        (adir / "shim.json").write_text(json.dumps({"pid": os.getpid(), "ident": procinfo.start_ident(os.getpid())}))
        self.assertEqual(w.x._sweep_roots(adir), {os.getpid(): procinfo.start_ident(os.getpid())})

    def test_a_headless_straggler_is_swept(self):
        import subprocess
        proc = subprocess.Popen(["sleep", "60"], cwd=self.dir, start_new_session=True)
        self.addCleanup(lambda: (proc.kill(), proc.wait()))
        self.assertEqual(procinfo.kill_in_cwd(str(self.dir), 0, spare_interactive=True), 1)

    def test_descends_from_follows_the_parent_links(self):
        import subprocess
        proc = subprocess.Popen(["sleep", "60"])
        self.addCleanup(lambda: (proc.kill(), proc.wait()))
        self.assertTrue(procinfo.descends_from(proc.pid, {os.getpid()}))
        self.assertFalse(procinfo.descends_from(proc.pid, {1 << 30}))


class PreparingRedrive(unittest.TestCase):
    def test_a_preparing_attempt_that_no_job_drives_is_prepared_again_and_finishes_once(self):
        cfg = ex.Config(poll_seconds=0.05, heartbeat_seconds=3600, grace_seconds=1.0, timeout_seconds=60,
                        settle_retry_seconds=0.2)
        w = World(self, config=cfg, autostart=False)
        w.x.start(order(1, "ok"))
        with w.x.ledger._tx() as con:                      # a start job died: the row is PREPARING, nothing runs for it
            con.execute("UPDATE attempts SET state='preparing' WHERE attempt_id='att-0001'")
        w.x.start_loop()
        d = w.finish("att-0001")
        self.assertEqual((d["state"], d["outcome"]["cause"]), ("finished", "clean"))
        self.assertEqual(w.sink.kinds("att-0001").count(m.EV_STARTED), 1)


class SharedWorkspace(unittest.TestCase):
    def test_a_manager_that_hands_out_a_live_attempts_directory_is_refused(self):
        w = World(self)
        w.x.start(order(1, "sleep:60"))
        shim_record(w, "att-0001")
        first = w.x.ledger.get("att-0001")["workspace"]
        real = w.x.workspaces
        w.x.workspaces = _SameWorkspace(real, first)
        w.x.start(order(2, "ok"))
        d = w.finish("att-0002")
        self.assertEqual(d["state"], "failed")
        self.assertIn("another live attempt", json.dumps(d))
        self.assertEqual(w.x.ledger.get("att-0001")["state"], m.RUNNING)       # the neighbour was left alone
        self.assertTrue(procinfo.alive(*_child(w, "att-0001")))

    def test_the_cwd_sweep_is_only_allowed_for_an_exclusive_worktree(self):
        w = World(self, autostart=False)
        rows = {"a": {"attempt_id": "a", "workspace": {"path": "/p"}}, "b": {"attempt_id": "b", "workspace": {"path": "/p"}}}
        w.x.ledger.in_states = lambda states, limit=None: list(rows.values())
        self.assertFalse(w.x._workspace_exclusive(rows["a"]))
        rows["b"]["workspace"]["path"] = "/q"
        self.assertTrue(w.x._workspace_exclusive(rows["a"]))


def _child(w, attempt_id):
    adir = Path(w.x.describe(attempt_id)["artifacts"]["dir"])
    info = json.loads((adir / "shim.json").read_text())
    return info["child_pid"], info["child_ident"]


class _SameWorkspace:
    """A buggy manager: every allocation returns the directory of an attempt that is still live."""

    def __init__(self, real, workspace):
        self._real, self._ws = real, workspace

    def check(self, request):
        return self._real.check(request)

    def allocate(self, request):
        return ex.Workspace(path=self._ws["path"], branch=self._ws["branch"], base_sha=self._ws["base_sha"],
                            repo=self._ws["repo"])

    def __getattr__(self, name):
        return getattr(self._real, name)


class SingleUseRoute(unittest.TestCase):
    def test_a_selector_reference_starts_one_attempt_ever(self):
        class OneShot(FakeResolver):
            def resolve(self, request):
                route = super().resolve(request)
                return ex.Route(route.provider, route.model, route.profile, route.effort, route.reference,
                                single_use=True)

        w = World(self, resolver=OneShot())
        w.x.start(order(1, "ok", executor="fake:ok"))
        w.finish("att-0001")
        try:
            receipt = w.x.start(order(2, "ok", executor="fake:ok"))
            refused = receipt.status == "rejected"
        except ex.ExecutorError as error:
            refused = error.code == "ROUTE_INVALID"
        self.assertTrue(refused, "a replayed single-use route started a second attempt")
        row = w.x.ledger.get("att-0002")
        self.assertTrue(row is None or row["state"] == m.REJECTED)
        self.assertEqual(len(w.sink.of("att-0002", m.EV_STARTED)), 0)


class RootsSharingARepository(unittest.TestCase):
    def test_the_same_attempt_id_in_two_executor_roots_gets_distinct_branches_and_refs(self):
        w = World(self, autostart=False)
        other = ex.GitWorkspaces(w.tmp / "second-root" / "ws", w.repos)
        one = ex.GitWorkspaces(w.root / "ws", w.repos).allocate(order(1))
        two = other.allocate(order(1))
        self.assertNotEqual(one.branch, two.branch)
        self.assertTrue(one.branch.startswith("m3/att-0001-") and two.branch.startswith("m3/att-0001-"))
        self.assertTrue(Path(one.path).exists() and Path(two.path).exists())
        self.assertNotEqual(one.path, two.path)

    def test_the_handoff_refs_of_two_roots_do_not_overwrite_each_other(self):
        w = World(self, autostart=False)
        refs = []
        for root in (w.root / "ws", w.tmp / "second-root" / "ws"):
            ws = ex.GitWorkspaces(root, w.repos).allocate(order(1))
            (Path(ws.path) / f"{len(refs)}.txt").write_text("work\n")
            from bt_scheduler_executor import handoff
            out = w.tmp / f"out{len(refs)}"
            out.mkdir()
            manifest = handoff.capture(ws, out, dirname="att-0001-x", attempt_id="att-0001", when=time.time(), patch_max=10_000)
            refs.append(manifest["refs"]["snapshot"])
        self.assertNotEqual(refs[0], refs[1])
        for ref in refs:
            self.assertTrue(git(w.repo, "rev-parse", "--verify", ref))


class RelativeRoot(unittest.TestCase):
    def test_a_relative_root_is_resolved_so_worktrees_never_land_inside_the_repository(self):
        w = World(self, autostart=False)
        w.x.close()
        previous = os.getcwd()
        os.chdir(w.tmp)
        self.addCleanup(os.chdir, previous)
        x = ex.AgentExecutor("rel-root", resolver=w.resolver, briefs=w.briefs, driver=w.driver,
                             workspaces=ex.GitWorkspaces("rel-root/ws", w.repos), sink=w.sink, config=w.config,
                             autostart=False)
        w.executors.append(x)                                              # torn down by the world
        self.assertTrue(x.root.is_absolute())
        x.start(order(1, "ok"))
        x.ledger.transition("att-0001", m.PREPARING, expect=(m.QUEUED,))
        ws = ex.GitWorkspaces("rel-root/ws", w.repos).allocate(order(1))
        self.assertTrue(Path(ws.path).is_absolute())
        self.assertTrue(str(ws.path).startswith(str((w.tmp / "rel-root").resolve())))
        self.assertEqual(git(w.repo, "status", "--porcelain"), "")        # nothing appeared in the user's checkout


class FindByArgvIsExact(unittest.TestCase):
    def test_extra_arguments_and_a_different_directory_do_not_match(self):
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            script = Path(t) / "s.py"
            script.write_text("import time; time.sleep(30)\n")
            exact = subprocess.Popen([sys.executable, str(script), t])
            extra = subprocess.Popen([sys.executable, str(script), t, "--more"])
            try:
                self.assertTrue(wait_for(lambda: exact.pid in procinfo.find_by_argv(str(script), t)))
                self.assertNotIn(extra.pid, procinfo.find_by_argv(str(script), t))
            finally:
                for proc in (exact, extra):
                    proc.kill()
                    proc.wait()


if __name__ == "__main__":
    unittest.main()
