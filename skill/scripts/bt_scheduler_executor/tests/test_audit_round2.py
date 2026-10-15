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
from support import FakeResolver, World, git, order, wait_for


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
