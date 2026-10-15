"""OPT-IN smoke tests against the real provider CLIs: `BITACORA_M3_REAL=1 python -m unittest tests.test_scheduler_executor_real`.

Spend is bounded: one tiny prompt per provider, the cheapest catalogue model, a short timeout, no tools asked for.
Skipped by default and never part of the default suites. A provider that is missing, not logged in or out of quota is
reported as SKIPPED with the reason (never as passed). Results go to $BITACORA_M3_REAL_OUT (JSON) when set.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bt_agents
import bt_profiles
import bt_scheduler_executor as m3
import bt_scheduler_executor_adapter as adapter

ENABLED = os.environ.get("BITACORA_M3_REAL") == "1"
CAP_SECONDS = 150
PROMPT_TITLE = "Reply with the single word OK. Do not use any tool and do not create or modify any file."
CASES = (("claude", "direct:claude/haiku", "claude"), ("codex", "direct:codex/gpt-6-luna#low", "codex"),
         ("antigravity", "direct:gemini/gemini-3.8-flash-low", bt_profiles.DEFAULT_BIN["antigravity"]))
RESULTS: dict[str, dict] = {}


class OneLine:
    def brief(self, request):
        return m3.Brief(title=PROMPT_TITLE, objective="Smoke test of the executor.", acceptance_criteria=("You said OK",))


class Sink:
    def __init__(self):
        self.events = []

    def deliver(self, event):
        self.events.append(event)


@unittest.skipUnless(ENABLED, "real provider tests are opt-in: BITACORA_M3_REAL=1")
class RealProviders(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        out = os.environ.get("BITACORA_M3_REAL_OUT")
        if out:
            Path(out).write_text(json.dumps(RESULTS, indent=1, sort_keys=True))

    @staticmethod
    def pin_profile(provider, reference):
        """A throwaway repository belongs to no project, so a work-only account (the gate is the point of the profile
        policy) cannot run in it: when the ambient account is work-only, use a personal profile of that provider."""
        ambient = bt_profiles.ambient(provider)
        if ambient and bt_profiles.load().get(ambient, {}).get("work_only"):
            personal = [p for p, spec in sorted(bt_profiles.load().items())
                        if spec.get("provider") == provider and not spec.get("work_only") and p not in ("claude", "codex")]
            personal = personal or [p for p, spec in sorted(bt_profiles.load().items())
                                    if spec.get("provider") == provider and not spec.get("work_only")]
            if personal:
                return f"{reference.split('#')[0]}@{personal[0]}" + (f"#{reference.split('#')[1]}" if "#" in reference else "")
        return reference

    def run_one(self, provider, reference, binary):
        reference = self.pin_profile(provider, reference)
        # The real CLIs run the user's own session hooks (they write to the bitácora and commit). Point them at a throwaway
        # bitácora root so a smoke test never creates projects or commits in the owner's real one.
        isolated = tempfile.mkdtemp(prefix="m3-real-bitacora-")
        self.addCleanup(shutil.rmtree, isolated, True)
        patcher = mock.patch.dict(os.environ, {"BITACORA_ROOT": isolated})
        patcher.start()
        self.addCleanup(patcher.stop)
        if not shutil.which(binary):
            RESULTS[provider] = {"status": "unavailable", "reason": f"{binary} is not installed"}
            self.skipTest(RESULTS[provider]["reason"])
        tmp = Path(tempfile.mkdtemp(prefix="m3-real-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        repo = tmp / "repo"
        repo.mkdir()
        import subprocess
        for cmd in (["git", "init", "-q", "-b", "main"],
                    ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "init"]):
            subprocess.run(cmd, cwd=repo, check=True, capture_output=True)
        sink = Sink()
        x = m3.AgentExecutor(
            tmp / "root", resolver=adapter.RouteResolver("metodologia"), briefs=OneLine(),
            driver=adapter.MethodologyDriver("metodologia"), workspaces=m3.GitWorkspaces(tmp / "root" / "ws", {"main": repo}),
            sink=sink, config=m3.Config(poll_seconds=0.2, timeout_seconds=CAP_SECONDS, max_timeout_seconds=CAP_SECONDS,
                                        output_head_bytes=200_000, output_tail_bytes=50_000, grace_seconds=5))
        self.addCleanup(x.close)
        started = time.monotonic()
        receipt = x.start(m3.StartRequest("real-1", "REAL", 1, "T1", "att-real", 1, reference, "main", "metodologia",
                                          timeout_seconds=CAP_SECONDS))
        self.assertEqual(receipt.status, "accepted", receipt)
        state = x.wait_state("att-real", m3.model.TERMINAL, CAP_SECONDS + 60)
        self.assertIsNotNone(state, "the attempt never ended")
        d = x.describe("att-real")
        outcome = d["outcome"]
        seconds = round(time.monotonic() - started, 1)
        RESULTS[provider] = {"reference": reference, "state": state, "cause": outcome["cause"], "returncode": outcome["returncode"],
                             "seconds": seconds, "usage": outcome.get("usage"), "cost_usd": outcome.get("cost_usd"),
                             "handoff": d["handoff"].get("status"), "terminal_event": outcome.get("terminal_event"),
                             "events": [e.kind for e in sink.events], "output_bytes": outcome["output"]["bytes"]}
        if outcome["cause"] in ("quota_exhausted", "connection_lost"):       # not a defect of the executor: skipped with the reason
            tail = Path(d["artifacts"]["output"]).read_text(errors="replace")[-300:] if Path(d["artifacts"]["output"]).exists() else ""
            RESULTS[provider]["tail"] = tail
            self.skipTest(f"{provider} could not complete a turn here: {outcome['cause']} ({tail.strip()[:120]})")
        self.assertEqual((state, outcome["cause"]), ("finished", "clean"))
        self.assertEqual(d["handoff"]["status"], "captured")
        self.assertEqual([e.kind for e in sink.events][0], "execution_started")
        self.assertEqual([e.kind for e in sink.events if e.kind != "heartbeat"][-1], "execution_finished")
        self.assertTrue(d["handoff"]["empty"], "a one-word reply should not change any file")

    def test_claude_code(self):
        self.run_one(*CASES[0])

    def test_codex(self):
        self.run_one(*CASES[1])

    def test_gemini_through_antigravity(self):
        self.run_one(*CASES[2])


class RealCasesAreWellFormed(unittest.TestCase):
    """Runs always (no spend): the opt-in cases use catalogue models and references the resolver accepts."""

    def test_every_real_case_resolves_without_launching_anything(self):
        for provider, reference, binary in CASES:
            with self.subTest(provider=provider):
                route = adapter.RouteResolver("metodologia").resolve if shutil.which(binary) else None
                if route is None:
                    continue
                resolved = route(m3.StartRequest("k", "P", 1, "T", "a", 1, reference, "main", "metodologia"))
                self.assertEqual(resolved.provider, provider)
                self.assertIn(resolved.model, bt_agents.MODELS)


if __name__ == "__main__":
    unittest.main()
