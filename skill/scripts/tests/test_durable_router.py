"""The durable router asks the M2 decision engine over the allowed routes, with LiveQuota as the capacity signal
(REQ-030 item 5). A route M2 refuses for a known reason is never chosen; when nothing can run the answer is a durable
wait for the earliest known reset or `unavailable`; every decision reaches the telemetry.

Profiles, cooldown marks and attempt history are the methodology's local facts: they are patched here, so the suite
never reads or writes the operator's bitácora."""
from __future__ import annotations

import hashlib
import json
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bt_agents
import bt_events
import bt_profiles
import bt_scheduler_decision_adapter as m2_adapter
from bt_contracts.execution import Route, RunRef
from bt_durable.adapters import routes as routing
from bt_durable.adapters.routes import LiveQuota, M2Router, StaticRouter, build_router
from bt_durable.legacy import load_plan

PROFILES = {
    "claude": {"provider": "claude", "bin": "claude", "env": {}, "work_only": False},
    "codex": {"provider": "codex", "bin": "codex", "env": {}, "work_only": False},
    "lab-a": {"provider": "claude", "bin": "claude", "env": {"CLAUDE_CONFIG_DIR": "/nonexistent/lab-a"},
              "work_only": False},
    "lab-b": {"provider": "claude", "bin": "claude", "env": {"CLAUDE_CONFIG_DIR": "/nonexistent/lab-b"},
              "work_only": False},
    "work-c": {"provider": "claude", "bin": "claude", "env": {"CLAUDE_CONFIG_DIR": "/nonexistent/work-c"},
               "work_only": True},
}
A = Route(provider="claude", profile="lab-a", model="sonnet", effort="medium")
B = Route(provider="claude", profile="lab-b", model="sonnet", effort="medium")


def plan(title: str = "T1 build it"):
    tasks = [{"id": "T1", "milestone_id": "M1", "title": title, "objective": "do it",
              "repository": "app", "after": [], "expected_paths": ["T1/**"], "shared_resources": [],
              "acceptance_criteria": ["T1 works"],
              "verification": [{"type": "command", "value": "true", "purpose": "T1 works"}]}]
    text = json.dumps({"schema_version": "1.0.0", "plan_id": "REQ-900", "revision": 1, "tasks": tasks})
    sha = hashlib.sha256(text.encode()).hexdigest()
    run = RunRef(project="proj", req="REQ-900", plan_id="REQ-900", revision=1, plan_sha256=sha,
                 plan_path=Path("/nonexistent/PLAN.r1.json"))
    return run, load_plan(text, approved_sha256=sha).task("T1")


def row(profile, *windows, status="ok", observed=None):
    return {"profile": profile, "provider": "claude", "status": status,
            "observed_at": time.time() - 5 if observed is None else observed,
            "windows": {f"w{i}": {"used_percent": used, "resets_at": reset, "window_minutes": 300}
                        for i, (used, reset) in enumerate(windows)}}


class Recorder:
    def __init__(self):
        self.events = []

    def __call__(self, event, **fields):
        self.events.append({"event": event, **fields})


class Facts(unittest.TestCase):
    """Isolate the methodology facts M2 reads: profiles, cooldown marks, history, binaries on PATH."""

    def setUp(self):
        self.cooling: dict[str, float] = {}
        for patcher in (patch.object(bt_profiles, "load", return_value=PROFILES),
                        patch.object(bt_profiles, "excluded_profiles", return_value=set()),
                        patch.object(bt_profiles, "is_work_project", return_value=False),
                        patch.object(bt_agents, "cooling_until",
                                     side_effect=lambda profile, _agent=None: self.cooling.get(profile)),
                        patch.object(bt_events, "read_all", return_value=[]),
                        patch.object(m2_adapter.shutil, "which", side_effect=lambda name: f"/usr/bin/{name}")):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.telemetry = Recorder()

    def router(self, rows, routes=(A, B), **kw):
        return M2Router(list(routes), LiveQuota(reader=lambda: rows), telemetry=self.telemetry, **kw)

    def decisions(self):
        return [e for e in self.telemetry.events if e["event"] == "route_decision"]


class M2Routing(Facts):
    def test_an_account_without_quota_is_never_chosen_and_the_other_runs(self):
        now = time.time()
        rows = [row("lab-a", (100.0, now + 3600)), row("lab-b", (10.0, now + 7200))]
        run, task = plan()
        decision = self.router(rows).decide(run, task, exclude=(), now=now)
        self.assertEqual((decision.kind, decision.route.profile), ("run", "lab-b"))
        self.assertTrue(decision.route.reference.startswith("m2:"))
        [event] = self.decisions()
        self.assertEqual((event["kind"], event["basis"], event["route"]), ("run", "m2", "claude:lab-b:sonnet"))
        self.assertEqual([r["route"] for r in event["ranked"]], ["claude:lab-b:sonnet"])
        [refused] = event["rejected"]
        self.assertEqual(refused["route"], "claude:lab-a:sonnet")
        self.assertIn("quota_exhausted", refused["reasons"])
        self.assertIn("capacity_exhausted", refused["reasons"])
        self.assertEqual(event["capacity"]["claude:lab-a:sonnet"]["state"], "exhausted")
        self.assertEqual(event["capacity"]["claude:lab-a:sonnet"]["reset_at"], now + 3600)
        self.assertEqual(event["capacity"]["claude:lab-b:sonnet"]["state"], "available")
        self.assertRegex(event["batch_id"], r"^[0-9a-f]{64}$")
        self.assertEqual(event["policy"], m2_adapter.DURABLE_POLICY_VERSION)
        # switching to A would not be worth an attempt: it has no capacity now
        self.assertEqual(self.router(rows).alternatives(run, task, exclude=(routing.key(B),)), 0)
        self.assertEqual(self.router(rows).alternatives(run, task, exclude=(routing.key(A),)), 1)

    def test_with_capacity_everywhere_the_operator_order_leads(self):
        now = time.time()
        rows = [row("lab-a", (60.0, now + 3600)), row("lab-b", (5.0, now + 3600))]
        run, task = plan()
        self.assertEqual(self.router(rows).decide(run, task, exclude=(), now=now).route.profile, "lab-a")
        # excluded after a failure on it: the next allowed route, still ranked by M2
        self.assertEqual(self.router(rows).decide(run, task, exclude=(routing.key(A),), now=now).route.profile, "lab-b")

    def test_m2_route_policy_prefers_headroom_where_the_baseline_is_not_preserved(self):
        now = time.time()
        rows = [row("lab-a", (80.0, now + 3600)), row("lab-b", (10.0, now + 3600))]
        run, task = plan("Document the API in the README")   # a docs task: the dispatch reorders it by policy
        decision = self.router(rows).decide(run, task, exclude=(), now=now)
        self.assertEqual(decision.route.profile, "lab-b")
        self.assertFalse(self.decisions()[0]["preserve_baseline"])

    def test_every_route_full_waits_for_the_earliest_reset(self):
        now = time.time()
        rows = [row("lab-a", (100.0, now + 900)), row("lab-b", (97.0, now + 300), (40.0, now + 9000))]
        run, task = plan()
        decision = self.router(rows).decide(run, task, exclude=(), now=now)
        self.assertEqual((decision.kind, decision.not_before), ("wait", now + 300))
        self.assertEqual(self.decisions()[0]["kind"], "wait")

    def test_full_without_a_known_reset_is_unavailable_never_invented(self):
        now = time.time()
        rows = [row("lab-a", (100.0, None)), row("lab-b", (100.0, None))]
        run, task = plan()
        decision = self.router(rows).decide(run, task, exclude=(), now=now)
        self.assertEqual(decision.kind, "unavailable")
        self.assertIn("quota_exhausted", decision.reason)

    def test_unknown_capacity_runs_only_when_no_route_has_known_capacity(self):
        now = time.time()
        run, task = plan()
        unknown_a = [row("lab-b", (10.0, now + 3600))]                       # no reading for A at all
        self.assertEqual(self.router(unknown_a).decide(run, task, exclude=(), now=now).route.profile, "lab-b")
        a_unknown_b_full = [row("lab-a", status="http_429"), row("lab-b", (100.0, now + 600))]
        decision = self.router(a_unknown_b_full).decide(run, task, exclude=(), now=now)
        self.assertEqual((decision.kind, decision.route.profile), ("run", "lab-a"))
        self.assertTrue(decision.route.reference.startswith("m2-unknown:"))
        self.assertEqual(self.decisions()[-1]["basis"], "unknown_capacity")
        strict = self.router(a_unknown_b_full, allow_unknown=False).decide(run, task, exclude=(), now=now)
        self.assertEqual((strict.kind, strict.not_before), ("wait", now + 600))

    def test_a_signed_out_or_unauthorized_account_is_never_chosen(self):
        now = time.time()
        run, task = plan()
        rows = [row("lab-a", status="invalid_credentials"), row("lab-b", (100.0, None))]
        self.assertEqual(self.router(rows).decide(run, task, exclude=(), now=now).kind, "unavailable")
        work = Route(provider="claude", profile="work-c", model="sonnet")      # work-only profile, personal project
        decision = self.router([row("work-c", (1.0, now + 60))], routes=(work, B)).decide(run, task, exclude=(), now=now)
        self.assertEqual(decision.route.profile, "lab-b")                       # B unknown, C refused for good
        refused = {r["route"]: r["reasons"] for r in self.decisions()[-1]["rejected"]}
        self.assertIn("profile_not_authorized", refused["claude:work-c:sonnet"])

    def test_a_cooldown_mark_blocks_only_while_the_live_reading_cannot_say_otherwise(self):
        now = time.time()
        run, task = plan()
        self.cooling["lab-a"] = now + 1200
        fresh = [row("lab-a", (20.0, now + 3600)), row("lab-b", (100.0, now + 4000))]
        self.assertEqual(self.router(fresh).decide(run, task, exclude=(), now=now).route.profile, "lab-a")
        unread = [row("lab-a", status="network_unavailable"), row("lab-b", (100.0, now + 4000))]
        decision = self.router(unread).decide(run, task, exclude=(), now=now)
        self.assertEqual((decision.kind, decision.not_before), ("wait", now + 1200))

    def test_a_window_that_already_reset_is_unknown_not_full(self):
        now = time.time()
        reading = LiveQuota(reader=lambda: [row("lab-a", (100.0, now - 10))]).reading(A, now)
        self.assertEqual((reading.state, reading.status), ("unknown", "reset_passed"))
        self.assertEqual(LiveQuota(reader=lambda: [row("lab-a", (100.0, now - 10))])(A), (None, None))
        self.assertEqual(LiveQuota(reader=lambda: [row("lab-a", (96.0, now + 50))])(A), (0.0, now + 50))
        self.assertEqual(LiveQuota(reader=lambda: [row("lab-a", (30.0, now + 50))])(A), (70.0, None))
        self.assertEqual(LiveQuota(reader=lambda: 1 / 0)(A), (None, None))

    def test_a_route_listed_twice_is_considered_once(self):
        now = time.time()
        run, task = plan()
        decision = self.router([row("lab-a", (10.0, now + 60))], routes=(A, A)).decide(run, task, exclude=(), now=now)
        self.assertEqual(decision.route.profile, "lab-a")
        self.assertEqual(self.decisions()[-1]["rejected"][0]["reasons"], ["duplicate_route"])


class Wiring(Facts):
    def test_static_on_request_and_m2_by_default(self):
        self.assertIsInstance(build_router("static", [A]), StaticRouter)
        self.assertIsInstance(build_router("m2", [A, B], LiveQuota(reader=list)), M2Router)
        with self.assertRaises(ValueError):
            build_router("fastest", [A])

    def test_m2_that_cannot_be_built_falls_back_to_static_with_the_reason(self):
        bad = Route(provider="claude", profile="lab-a", model="son\x01net")    # M2 refuses this identity
        router = build_router("m2", [bad], telemetry=self.telemetry)
        self.assertIsInstance(router, StaticRouter)
        [event] = [e for e in self.telemetry.events if e["event"] == "router_fallback"]
        self.assertIn("DecisionInputError", event["reason"])

    def test_telemetry_failure_never_changes_the_decision(self):
        now = time.time()
        run, task = plan()

        def broken(*_a, **_k):
            raise OSError("disk full")
        router = M2Router([A, B], LiveQuota(reader=lambda: [row("lab-b", (1.0, now + 60))]), telemetry=broken)
        self.assertEqual(router.decide(run, task, exclude=(), now=now).route.profile, "lab-b")


if __name__ == "__main__":
    unittest.main()
