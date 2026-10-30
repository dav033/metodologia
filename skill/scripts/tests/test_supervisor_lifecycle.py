"""bt_supervisor lifecycle on real processes, for both backends: launch -> observe -> exit status and output,
the output cap, the exact environment, idempotent launch (the anti-duplication guarantee) and release."""
from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from supervisor_support import (
    BASE_ENV,
    PY,
    SCRIPTS,
    AttemptAlive,
    LaunchSpec,
    PgroupCase,
    SystemdCase,
    derive_outcome,
)


class LifecycleTests:
    def test_launch_observe_exit_code_and_output(self):
        key = self.key("life")
        spec = self.sh(key, "echo out-line; echo err-line >&2; cat; sleep 0.8; exit 3", stdin_text="fed-stdin\n")
        identity = self.sup.launch(spec)
        self.assertEqual(identity.backend, self.BACKEND)
        running = self.sup.observe(key)
        self.assertEqual(running.state, "running")
        self.assertTrue(running.live_pids)
        self.assertEqual(running.identity, identity)
        done = self.wait_state(key)
        self.assertEqual((done.exit_code, done.signal, done.result, done.oom_killed), (3, None, "exit-code", False))
        self.assertEqual(done.identity, identity)
        self.assertEqual(done.live_pids, [])
        self.assertIsNotNone(done.started_at)
        self.assertGreaterEqual(done.ended_at, done.started_at)
        text = done.log_path.read_text()
        for needle in ("out-line", "err-line", "fed-stdin"):
            self.assertIn(needle, text)
        ok = self.sh(self.key("ok"), "exit 0")
        self.sup.launch(ok)
        self.assertEqual(self.wait_state(ok.attempt_key).result, "success")

    def test_environment_is_exactly_the_given_one(self):
        key = self.key("env")
        code = "import json, os; print(json.dumps(dict(os.environ)))"
        self.sup.launch(self.spec(key, [PY, "-I", "-c", code], env={**BASE_ENV, "X_GIVEN": "v a l$HOME\"\n"}))
        done = self.wait_state(key)
        env = json.loads(done.log_path.read_text().strip().splitlines()[-1])
        self.assertEqual(env, {**BASE_ENV, "X_GIVEN": "v a l$HOME\"\n", "BT_ATTEMPT_KEY": key,
                               "BT_SUPERVISOR_ID": self.sup.store.supervisor_id})

    def test_another_supervisors_process_with_the_same_key_is_never_ours(self):
        # two engines (or two test labs) may hand out the same attempt key: terminating ours must not touch theirs,
        # and their process must not make ours look alive (REQ-030 iteration 2: a lab killed another lab's agent)
        import os

        from bt_supervisor.api import make_supervisor
        key = self.key("shared")
        other = make_supervisor(self.tmp / "other-state", self.BACKEND, unit_prefix=self.prefix + "o-")
        self.addCleanup(lambda: other.terminate(key) and None)
        theirs = other.launch(self.sh(key, "sleep 30"))
        mine = self.sup.launch(self.sh(key, "sleep 30"))
        self.assertNotEqual(theirs.unit or theirs.main_pid, mine.unit or mine.main_pid)
        ended = self.sup.terminate(key)
        self.assertEqual(ended.live_pids, [])
        still = other.observe(key)
        self.assertEqual(still.state, "running")
        self.assertTrue(still.live_pids)
        for pid in still.live_pids:
            os.kill(pid, 0)                                      # alive: our terminate never reached it
        other.terminate(key)


    def test_an_inherited_service_identity_never_reaches_the_unit(self):
        # an engine running as a systemd service copies its own INVOCATION_ID into the agent environment: the unit
        # must keep the manager's identity, so the attempt stays observable and terminable (REQ-021 a1, 2026-10-28)
        key = self.key("inherit")
        inherited = {"INVOCATION_ID": "d0083645ab904d76bec6a30ba19dd613", "JOURNAL_STREAM": "8:1", "SYSTEMD_EXEC_PID": "1"}
        identity = self.sup.launch(self.spec(key, [PY, "-I", "-c", "import time; time.sleep(30)"],
                                             env={**BASE_ENV, **inherited}))
        self.assertNotEqual(identity.invocation_id, inherited["INVOCATION_ID"])
        self.assertEqual(self.sup.observe(key).state, "running")
        ended = self.sup.terminate(key)
        self.assertEqual(ended.live_pids, [])

    def test_output_cap_bounds_the_log_and_keeps_the_tail(self):
        key = self.key("cap")
        code = "import sys\nfor i in range(20000): sys.stdout.write(f'line {i:06d} ' + 'x' * 24 + '\\n')"
        cap = 64 * 1024
        self.sup.launch(self.spec(key, [PY, "-I", "-c", code], output_cap_bytes=cap))
        done = self.wait_state(key)
        self.assertEqual(done.result, "success")
        log = done.log_path.read_bytes()
        self.assertLessEqual(len(log), cap + 200)                     # the head plus one marker line
        self.assertTrue(log.startswith(b"line 000000 "))
        self.assertIn(b"[bt_supervisor] output exceeded", log)
        tail = (done.log_path.parent / "output.tail").read_bytes()
        self.assertLessEqual(len(tail), cap)
        self.assertTrue(tail.endswith(b"line 019999 " + b"x" * 24 + b"\n"))

    def test_spawn_error_is_reported(self):
        key = self.key("spawn")
        self.sup.launch(self.spec(key, [str(self.tmp / "no-such-binary")]))
        done = self.wait_state(key)
        self.assertEqual(done.result, "spawn-error")
        self.assertIn("could not start", done.log_path.read_text())

    def test_launch_is_idempotent_per_key(self):
        key = self.key("idem")
        counter = self.tmp / "counter"
        spec = self.sh(key, f"echo started >> '{counter}'; sleep 1.5")
        first = self.sup.launch(spec)
        self.assertEqual(self.sup.launch(spec), first)
        other = self.supervisor()                                    # a restarted orchestrator, same state dir
        self.assertEqual(other.launch(spec), first)
        results, errors = [], []

        def racer():
            try:
                results.append(self.supervisor().launch(spec))
            except Exception as error:  # noqa: BLE001 - surfaced by the assertion below
                errors.append(error)

        threads = [threading.Thread(target=racer) for _ in range(6)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(60)
        self.assertEqual(errors, [])
        self.assertEqual({r.invocation_id for r in results}, {first.invocation_id})
        self.wait_state(key)
        self.assertEqual(self.sup.launch(spec), first)               # exited but not released: still adopted
        time.sleep(0.3)
        self.assertEqual(counter.read_text().splitlines(), ["started"])

    def test_crashed_launch_is_adopted_or_restarted_never_duplicated(self):
        counter = self.tmp / "crash-counter"
        # (a) crashed after the process started but before the record said so: adopt, do not start another
        key = self.key("crash")
        spec = self.sh(key, f"echo started >> '{counter}'; sleep 30")
        first = self.sup.launch(spec)
        record = self.sup.store.read(key, "launch.json")
        self.sup.store.write(key, "launch.json", {**record, "status": "starting", "identity": None})
        self.assertEqual(self.supervisor().launch(spec).invocation_id, first.invocation_id)
        time.sleep(0.3)
        self.assertEqual(counter.read_text().splitlines(), ["started"])
        self.sup.terminate(key, grace=1)
        # (b) crashed after writing the record, before starting anything: absent, releasable, then a clean start
        key2 = self.key("crash2")
        spec2 = self.sh(key2, f"echo second >> '{counter}'; sleep 30")
        store, env_format = self.sup.store, "systemd" if self.BACKEND == "systemd" else "json"
        store.prepare(spec2, store.new_record(spec2, backend=self.BACKEND, unit=None, unenforced=[]),
                      env_format=env_format)
        self.assertEqual(self.sup.observe(key2).state, "absent")
        self.sup.release(key2)
        self.assertFalse(store.dir(key2).exists())
        store.prepare(spec2, store.new_record(spec2, backend=self.BACKEND, unit=None, unenforced=[]),
                      env_format=env_format)
        self.sup.launch(spec2)
        self.assertEqual(self.sup.observe(key2).state, "running")
        time.sleep(0.3)
        self.assertEqual(counter.read_text().splitlines(), ["started", "second"])
        self.sup.terminate(key2, grace=1)

    def test_release_refuses_while_alive_then_frees_the_key(self):
        key = self.key("rel")
        spec = self.sh(key, "sleep 30")
        first = self.sup.launch(spec)
        with self.assertRaises(AttemptAlive):
            self.sup.release(key)
        self.assertIn(key, [i.attempt_key for i in self.sup.list_attempts(key[:4])])
        self.assertEqual(self.sup.terminate(key, grace=2).result, "terminated")
        self.sup.release(key)
        self.sup.release(key)                                        # idempotent
        self.assertEqual(self.sup.observe(key).state, "absent")
        self.assertNotIn(key, [i.attempt_key for i in self.sup.list_attempts("")])
        second = self.sup.launch(spec)                               # the key is free again: a NEW incarnation
        self.assertNotEqual(second.invocation_id, first.invocation_id)
        self.sup.terminate(key, grace=1)

    def test_cli_lists_and_shows(self):
        key = self.key("cli")
        self.sup.launch(self.sh(key, "sleep 30"))
        base = [sys.executable, "-m", "bt_supervisor", "--state-dir", str(self.state_dir), "--backend",
                self.BACKEND, "--unit-prefix", self.prefix]
        listed = subprocess.run(base + ["list"], cwd=SCRIPTS, check=False, capture_output=True, text=True, timeout=60)
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertEqual([i["attempt_key"] for i in json.loads(listed.stdout)["result"]], [key])
        shown = subprocess.run(base + ["show", key], cwd=SCRIPTS, check=False, capture_output=True, text=True, timeout=60)
        self.assertEqual(json.loads(shown.stdout)["result"]["state"], "running")
        stopped = subprocess.run(base + ["stop", key, "--grace", "1"], cwd=SCRIPTS, check=False, capture_output=True, text=True,
                                 timeout=60)
        self.assertEqual(json.loads(stopped.stdout)["result"]["state"], "exited", stopped.stderr)


class SystemdLifecycle(SystemdCase, LifecycleTests):
    def test_a_relaunch_adopts_from_its_files_while_the_manager_does_not_answer(self):
        """A launch run again after the engine stopped (D-181) meets a user manager that does not answer: the attempt's
        files prove it started, so it is adopted, never started again; without that proof the error stands
        (test_durable_shutdown under load, 2026-10-30; the engine-level case is test_durable_launch_hiccup)."""
        from unittest import mock

        from bt_supervisor.errors import ManagerUnavailable
        counter = self.tmp / "silent-counter"
        key = self.key("silent")
        spec = self.sh(key, f"echo started >> '{counter}'; sleep 30")
        first = self.sup.launch(spec)
        again = self.supervisor()
        for status in ("started", "starting"):                     # finalized, or cut between systemd-run and that
            record = self.sup.store.read(key, "launch.json")
            self.sup.store.write(key, "launch.json", {**record, "status": status, "identity": None})
            with mock.patch.object(again, "_show", side_effect=ManagerUnavailable("bus timed out")):
                self.assertEqual(again.launch(spec).invocation_id, first.invocation_id, status)
        time.sleep(0.3)
        self.assertEqual(counter.read_text().splitlines(), ["started"])
        self.sup.terminate(key, grace=1)
        fresh = self.sh(self.key("silent2"), f"echo second >> '{counter}'")
        store = self.sup.store                                     # a record, but nothing says the unit started
        store.prepare(fresh, store.new_record(fresh, backend="systemd", unit=None, unenforced=[]), env_format="systemd")
        with mock.patch.object(again, "_show", side_effect=ManagerUnavailable("bus timed out")), \
                self.assertRaises(ManagerUnavailable):
            again.launch(fresh)
        self.assertEqual(counter.read_text().splitlines(), ["started"])


class PgroupLifecycle(PgroupCase, LifecycleTests):
    pass


class ModelAndOutcome(unittest.TestCase):
    def test_spec_validation(self):
        good = {"attempt_key": "k-1", "argv": ["true"], "cwd": "/tmp", "env": {}, "log_dir": "/tmp/l"}
        LaunchSpec(**good)
        for bad in ({"attempt_key": ".."}, {"attempt_key": "a/b"}, {"attempt_key": "x" * 101}, {"cwd": "rel"},
                    {"env": {"BT_ATTEMPT_KEY": "x"}}, {"env": {"1BAD": "x"}}, {"argv": []}, {"extra": 1},
                    {"output_cap_bytes": 10}):
            with self.assertRaises(ValueError, msg=bad):
                LaunchSpec(**{**good, **bad})

    def test_outcome_precedence(self):
        self.assertEqual(derive_outcome({"service_result": "oom-kill", "exit_kind": "killed", "exit_status": "KILL"},
                                        None, True), (None, "SIGKILL", "oom-kill", True))
        self.assertEqual(derive_outcome({"service_result": "success", "exit_kind": "killed", "exit_status": "TERM"},
                                        None, False)[2], "signal")
        self.assertEqual(derive_outcome({"service_result": "success", "exit_kind": "killed", "exit_status": "TERM"},
                                        None, True)[2], "terminated")
        self.assertEqual(derive_outcome({"service_result": "timeout"}, {"returncode": -15}, False)[:3],
                         (None, "SIGTERM", "timeout"))
        self.assertEqual(derive_outcome(None, None, False, fallback={"Result": "exit-code", "ExecMainCode": "1",
                                                                     "ExecMainStatus": "4"})[:3],
                         (4, None, "exit-code"))
        self.assertEqual(derive_outcome({"reason": "exited", "returncode": 0}, None, False)[2], "success")


if __name__ == "__main__":
    unittest.main()
