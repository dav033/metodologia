"""Provider driver contract v1 against fake CLIs (REQ-007 T7, gate G4).

Every scenario runs in a subprocess with a throwaway BITACORA_ROOT (importing bt_* here would freeze ROOT). The
fake provider binaries print canned streams chosen by a `SCENARIO:<name>` marker in the prompt. Only the driver
contract is checked: a clean turn is "completed", never "verified", and anything partial, malformed, failed,
limited or killed must not look like success. Real-provider runs are separate and opt-in.
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "skill" / "scripts"

FAKE = textwrap.dedent('''\
    #!%(python)s
    import json, os, re, sys, time
    provider = os.environ["FAKE_PROVIDER"]
    text = " ".join(sys.argv[1:]) + " " + (sys.stdin.read() if not sys.stdin.isatty() else "")
    scenario = re.search(r"SCENARIO:(\\w+)", text).group(1)
    def claude(result, error=False, extra=None):
        print(json.dumps({"type": "system", "subtype": "init"}))
        print(json.dumps({"type": "result", "subtype": "error_during_execution" if error else "success",
                          "is_error": error, "result": result, "total_cost_usd": 0.02,
                          "usage": {"input_tokens": 7, "output_tokens": 3}}))
    def agy(response, status="SUCCESS", error=None):
        print(json.dumps({"event": "start"}))
        print(json.dumps({"event": "result", "result": {"status": status, "response": response, "error": error,
                                                         "usage": {"total_tokens": 10}}}))
    out = sys.stdout
    if scenario == "env":
        print("ACCOUNT_VAR=" + os.environ.get("ACCOUNT_VAR", "<unset>"))
        print("SENTINEL=" + os.environ.get("SENTINEL_SECRET", "<unset>"))
        sys.exit(0)
    if scenario == "slow":
        print("working", flush=True)
        time.sleep(30)
    if scenario == "ok":
        if provider == "claude": claude("all done")
        elif provider == "antigravity": agy("all done")
        else: print("all done")
    elif scenario == "iserror":
        if provider == "claude": claude("tool failed hard", error=True)
        elif provider == "antigravity": agy("", status="FAILURE", error="internal failure")
        else: print("internal failure"); sys.exit(1)
    elif scenario == "cut":
        if provider == "claude":
            print(json.dumps({"type": "system", "subtype": "init"})); sys.stdout.write('{"type": "res')
        elif provider == "antigravity":
            print(json.dumps({"event": "start"})); sys.stdout.write('{"event": "resu')
        # codex: nothing at all
    elif scenario == "agyshape":
        print(json.dumps({"event": "start"})); print(json.dumps({"event": "result"}))
    elif scenario == "agystr":
        print(json.dumps({"event": "result", "result": "oops"}))
    elif scenario == "codexerr":
        print("ERROR: 500 internal server error")
    elif scenario == "garbage":
        print("Traceback (most recent call last):\\n  boom\\nnot json at all")
    elif scenario == "nonzero":
        if provider == "claude": claude("looked fine")
        elif provider == "antigravity": agy("looked fine")
        else: print("looked fine")
        sys.exit(3)
    elif scenario == "limit":
        if provider == "claude": claude("Claude usage limit reached|4102444800", error=True); sys.exit(1)
        elif provider == "antigravity": agy("", status="FAILURE", error="RESOURCE_EXHAUSTED: quota"); sys.exit(1)
        else: print("You've hit your usage limit. try again at Oct 13th, 2099 1:08 AM."); sys.exit(1)
    elif scenario == "mentions":
        # a successful run that merely talks about limits must stay a success
        msg = "Documented the 429 and quota handling; no usage limit was hit."
        if provider == "claude": claude(msg)
        elif provider == "antigravity": agy(msg)
        else: print(msg)
''')

RUNNER = textwrap.dedent('''\
    import json, os, sys
    sys.path.insert(0, %(scripts)r)
    import bt_driver, signal
    provider, executable, scenario, timeout = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
    driver = bt_driver.driver_for(provider, executable)
    removal = tuple(os.environ.get("REMOVE_VARS", "").split(",")) if os.environ.get("REMOVE_VARS") else ()
    invocation = driver.invocation("SCENARIO:" + scenario, os.getcwd(), timeout_sec=int(timeout) if timeout >= 60 else None,
                                   env_remove=removal)
    if os.environ.get("INTERRUPT_AFTER"):
        def _interrupt(*_):
            raise KeyboardInterrupt
        signal.signal(signal.SIGALRM, _interrupt)
        signal.alarm(int(os.environ["INTERRUPT_AFTER"]))
    outcome = driver.run(invocation, timeout)
    print(json.dumps({"outcome": outcome.as_dict(), "redacted": invocation.redacted(), "argv": list(invocation.argv)}))
''')


class DriverContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temp = tempfile.TemporaryDirectory(prefix="driver-contract-")
        cls.addClassCleanup(cls._temp.cleanup)
        cls.dir = Path(cls._temp.name)
        cls.fake = cls.dir / "fake-provider"
        cls.fake.write_text(FAKE % {"python": sys.executable}, encoding="utf-8")
        cls.fake.chmod(cls.fake.stat().st_mode | stat.S_IXUSR)
        cls.runner = cls.dir / "runner.py"
        cls.runner.write_text(RUNNER % {"scripts": str(SCRIPTS)}, encoding="utf-8")

    def run_driver(self, provider: str, scenario: str, timeout: float = 20, extra_env: dict | None = None,
                   executable: str | None = None) -> dict:
        env = {"PATH": "/usr/bin:/bin", "HOME": str(self.dir), "BITACORA_ROOT": str(self.dir / "bit"),
               "FAKE_PROVIDER": provider, "PYTHONDONTWRITEBYTECODE": "1", **(extra_env or {})}
        done = subprocess.run([sys.executable, "-I", str(self.runner), provider, executable or str(self.fake),
                               scenario, str(timeout)], capture_output=True, text=True, env=env, cwd=self.dir,
                              timeout=120)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout)

    def test_clean_turn_is_completed_with_reported_fields_and_unknown_stays_null(self) -> None:
        for provider in ("claude", "codex", "antigravity"):
            with self.subTest(provider=provider):
                out = self.run_driver(provider, "ok")["outcome"]
                self.assertEqual((out["version"], out["status"], out["is_error"]), (1, "completed", False))
                self.assertIn("all done", out["text"])
                self.assertIsNone(out["reset_epoch"])
        self.assertEqual(self.run_driver("claude", "ok")["outcome"]["usage"], {"input_tokens": 7, "output_tokens": 3})
        self.assertEqual(self.run_driver("claude", "ok")["outcome"]["cost_usd"], 0.02)
        self.assertEqual(self.run_driver("antigravity", "ok")["outcome"]["usage"], {"total_tokens": 10})
        codex = self.run_driver("codex", "ok")["outcome"]
        self.assertIsNone(codex["usage"])      # not reported -> null, never zero
        self.assertIsNone(codex["cost_usd"])

    def test_provider_reported_error_is_failed(self) -> None:
        for provider in ("claude", "codex", "antigravity"):
            with self.subTest(provider=provider):
                out = self.run_driver(provider, "iserror")["outcome"]
                self.assertEqual((out["status"], out["is_error"]), ("failed", True))

    def test_cut_streams_are_partial_never_completed(self) -> None:
        for provider in ("claude", "codex", "antigravity"):
            with self.subTest(provider=provider):
                out = self.run_driver(provider, "cut")["outcome"]
                self.assertEqual(out["status"], "partial")
                self.assertFalse(out["terminal_event"])

    def test_nonzero_exit_after_a_good_looking_stream_is_failed(self) -> None:
        for provider in ("claude", "codex", "antigravity"):
            with self.subTest(provider=provider):
                self.assertEqual(self.run_driver(provider, "nonzero")["outcome"]["status"], "failed")

    def test_garbage_output_is_not_completed_for_stream_providers(self) -> None:
        for provider in ("claude", "antigravity"):
            with self.subTest(provider=provider):
                self.assertEqual(self.run_driver(provider, "garbage")["outcome"]["status"], "partial")

    def test_usage_limits_are_classified_with_reset_only_when_stated(self) -> None:
        claude = self.run_driver("claude", "limit")["outcome"]
        self.assertEqual((claude["status"], claude["reset_epoch"]), ("limit", 4102444800))
        codex = self.run_driver("codex", "limit")["outcome"]
        self.assertEqual(codex["status"], "limit")
        self.assertGreater(codex["reset_epoch"], 4000000000)   # 2099 absolute announcement
        agy = self.run_driver("antigravity", "limit")["outcome"]
        self.assertEqual(agy["status"], "limit")
        self.assertIsNone(agy["reset_epoch"])                   # none given: unknown, not invented

    def test_a_success_that_only_mentions_limits_stays_completed(self) -> None:
        for provider in ("claude", "codex", "antigravity"):
            with self.subTest(provider=provider):
                self.assertEqual(self.run_driver(provider, "mentions")["outcome"]["status"], "completed")

    def test_timeout_kills_the_process_group_and_reports_timeout(self) -> None:
        out = self.run_driver("claude", "slow", timeout=1.5)["outcome"]
        self.assertEqual(out["status"], "timeout")
        self.assertIn("working", out["text"])

    def test_missing_binary_is_a_failed_outcome_not_an_exception(self) -> None:
        out = self.run_driver("codex", "ok", executable="/nonexistent/provider")["outcome"]
        self.assertEqual((out["status"], out["returncode"]), ("failed", None))

    def test_env_removal_applies_and_secrets_never_reach_logs_or_outcomes(self) -> None:
        result = self.run_driver("claude", "env", extra_env={"ACCOUNT_VAR": "other-account",
                                                              "SENTINEL_SECRET": "s3cret-token-value",
                                                              "REMOVE_VARS": "ACCOUNT_VAR"})
        self.assertIn("ACCOUNT_VAR=<unset>", result["outcome"]["text"])
        # the sentinel reached the child (inherited) but must not appear in what the driver exposes for logging
        exposed = json.dumps({"redacted": result["redacted"], "argv": result["argv"]})
        self.assertNotIn("s3cret-token-value", exposed)
        self.assertEqual(result["redacted"]["env_removed"], ["ACCOUNT_VAR"])
        self.assertNotIn("SCENARIO", json.dumps(result["redacted"]))   # prompt text is not logged

    def test_antigravity_result_event_without_a_result_object_is_not_completed(self) -> None:
        for scenario in ("agyshape", "agystr"):
            with self.subTest(scenario=scenario):
                out = self.run_driver("antigravity", scenario)["outcome"]
                self.assertNotEqual(out["status"], "completed")
                self.assertFalse(out["terminal_event"])

    def test_codex_completed_is_best_effort_and_pinned_as_such(self) -> None:
        # Documented limit: no end-of-turn event, so exit 0 with output reads as completed. Verification decides.
        out = self.run_driver("codex", "codexerr")["outcome"]
        self.assertEqual(out["status"], "completed")

    def test_keyboard_interrupt_kills_the_group_and_reports_cancelled(self) -> None:
        out = self.run_driver("claude", "slow", timeout=20, extra_env={"INTERRUPT_AFTER": "1"})["outcome"]
        self.assertEqual(out["status"], "cancelled")

    def test_invocation_repr_hides_prompt_and_secret_values(self) -> None:
        probe = ("import sys; sys.path.insert(0, %r); import bt_driver;"
                 "i = bt_driver.Invocation('claude', ('claude', '-p', 'PROMPT-BODY'), 'STDIN-BODY', '/tmp',"
                 "('X',), (('TOKEN', 'v4lue'),)); print(repr(i))" % str(SCRIPTS))
        env = {"PATH": "/usr/bin:/bin", "HOME": str(self.dir), "BITACORA_ROOT": str(self.dir / "bit")}
        done = subprocess.run([sys.executable, "-I", "-c", probe], capture_output=True, text=True, env=env)
        self.assertEqual(done.returncode, 0, done.stderr)
        for secret in ("PROMPT-BODY", "STDIN-BODY", "v4lue"):
            self.assertNotIn(secret, done.stdout)

    def test_statuses_are_a_closed_vocabulary(self) -> None:
        seen = {self.run_driver(p, s)["outcome"]["status"] for p in ("claude", "codex", "antigravity")
                for s in ("ok", "iserror", "cut", "limit")}
        self.assertTrue(seen <= {"completed", "failed", "limit", "partial", "timeout", "cancelled"})
        self.assertTrue({"completed", "failed", "limit", "partial"} <= seen)


if __name__ == "__main__":
    unittest.main()
