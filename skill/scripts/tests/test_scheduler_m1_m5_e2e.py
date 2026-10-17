"""Frozen Planner → M1 → M2 → M3 processes → M4 → M5 → authorised retry, without provider cost."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import scheduler_chain_support as chain
import scheduler_executor_support as support
from bt_scheduler_executor_adapter import run_identity
from bt_scheduler_monitor.queries import events as query_events
from scheduler_executor_support import adapter, core


class PlannerThroughRecovery(support.World):
    def _run_chain(self, *, monitor=True, restart=False, reject=False, quota_reroute=False,
                   no_alternate_route=False, block_after_wait=False):
        scenario = "ok" if reject else "net" if block_after_wait else "recover"
        tasks = [{"id": "T1", "title": f"SCENARIO:{scenario}", "repo": "app", "after": []}]
        pipeline = chain.Pipeline(self, "chainproj", "REQ-060", tasks, ["README.md"])
        frozen = pipeline.run()
        self.rdir = pipeline.rdir
        original_repo = support.git(self.repos["app"], "rev-parse", "HEAD")
        legacy = self.tmp / "untouched-RUN.json"
        legacy.write_bytes(b'{"schema":0,"opaque":"preserve"}\n')
        ledger = self.tmp / "m2.db"
        route_calls = 0

        def routes(_task):
            nonlocal route_calls
            route_calls += 1
            if quota_reroute or no_alternate_route:
                first_status = "available" if route_calls == 1 else "exhausted"
                second_status = "available" if quota_reroute else "exhausted"
                return [("claude", "sonnet", "claude-personal", "low", first_status),
                        ("codex", "gpt-6-luna", "codex-1", "low", second_status)]
            return [("claude", "sonnet", "claude-personal", "low")]

        assignment = chain.M2Port(ledger, routes)
        verifier = support.Verifier()
        if reject:
            def verify(order):
                verifier.orders.append(order)
                accept = len(verifier.orders) > 1
                verifier.scheduler.submit_verdict(core.Verdict(
                    f"v-{order.attempt_id}", order.plan_id, order.revision, order.task_id, order.attempt_id,
                    accept, "independent-check", "tests passed" if accept else "tests failed: secret-value",
                    order.token))
                return core.Ack("accepted")
            verifier.request = verify
        monitor_path = self.tmp / "m4.db" if monitor else None
        history_path = self.tmp / "m5" / "history.db"
        scheduler_now = [time.time()]

        def wire():
            with patch.object(support.bt_profiles, "ROOT", self.root):
                result = adapter.wire(
                    self.rdir, project="chainproj", assignment=assignment, verification=verifier,
                    repos=self.repos, default_repository="app", m2_ledger=ledger,
                    config=core.Config(max_attempts=3, max_recovery_waits=1 if block_after_wait else 3),
                    executor_config=adapter.m3.Config(poll_seconds=0.05, grace_seconds=1,
                                                      timeout_seconds=15, heartbeat_seconds=3600),
                    monitor_store_path=monitor_path, recovery_store_path=history_path,
                    clock=(lambda: scheduler_now[0]) if block_after_wait or no_alternate_route else None,
                    recovery_policy={"max_same_cause": 1} if block_after_wait else None)
            verifier.scheduler = result.scheduler
            self.wirings.append(result)
            return result

        wiring = wire()
        restarted = False
        deadline = time.monotonic() + 35
        while time.monotonic() < deadline:
            wiring.scheduler.step()
            for aid in wiring.executor.ledger.all_ids():
                info = wiring.executor.describe(aid)
                if info and (Path(info["artifacts"]["dir"]) / info["stream"]["stream_ref"]).exists():
                    wiring.drain_stream(aid, run_identity(wiring.scheduler))
            if block_after_wait or no_alternate_route:
                decision = wiring.recovery.latest()
                if decision and decision["action"] == "wait":
                    scheduler_now[0] = max(scheduler_now[0], decision["cooldown_until"] + 0.01)
            snap = wiring.scheduler.snapshot()
            if restart and not restarted and snap.tasks["T1"]["state"] == "recovering":
                wiring.close()
                self.wirings.remove(wiring)
                wiring = wire()
                restarted = True
            if no_alternate_route and snap.tasks["T1"]["attempts"] == 1 and \
                    assignment.decisions["T1"].selected is None:
                break
            if snap.status in {"completed", "blocked"}:
                break
            time.sleep(0.03)

        if block_after_wait:
            snap = wiring.scheduler.snapshot()
            self.assertEqual(snap.status, "blocked",
                             (snap, wiring.recovery.latest(), wiring.recovery.metrics(), scheduler_now[0]))
            ids = wiring.executor.ledger.all_ids()
            self.assertEqual(len(ids), 2)
            decision = wiring.recovery.latest()
            self.assertEqual((decision["action"], decision["reason_code"]), ("block", "same_cause_limit"))
            self.assertEqual(wiring.recovery.metrics()["actions"], {"retry": 1, "wait": 1, "block": 1})
            self.assertEqual(assignment.proposal_calls, 2)
            self.assertEqual(len(self.records()), 2)
            for _ in range(5):
                wiring.scheduler.step()
            self.assertEqual(wiring.scheduler.snapshot().status, "blocked")
            self.assertEqual(wiring.executor.ledger.all_ids(), ids)
            self.assertEqual(wiring.recovery.latest(), decision)
            self.assertEqual(wiring.recovery.metrics()["actions"], {"retry": 1, "wait": 1, "block": 1})
            self.assertEqual(assignment.proposal_calls, 2)
            self.assertEqual(len(self.records()), 2)
            return

        if no_alternate_route:
            snap = wiring.scheduler.snapshot()
            self.assertEqual((snap.status, snap.tasks["T1"]["state"], snap.tasks["T1"]["attempts"]),
                             ("running", "ready", 1), snap)
            ids = wiring.executor.ledger.all_ids()
            self.assertEqual(len(ids), 1)
            self.assertEqual(wiring.recovery.latest()["action"], "retry")
            self.assertEqual(wiring.recovery.metrics()["actions"], {"retry": 1, "wait": 1, "block": 0})
            no_route = assignment.decisions["T1"]
            self.assertIsNone(no_route.selected)
            self.assertEqual(no_route.status, "no_eligible_candidate")
            self.assertTrue(all("quota_exhausted" in item.reason_codes for item in no_route.exclusions))
            self.assertEqual(assignment.proposal_calls, 2)
            self.assertEqual(len(self.records()), 1)
            recovery_decision = wiring.recovery.latest()
            recovery_metrics = wiring.recovery.metrics()
            for _ in range(5):
                wiring.scheduler.step()
            self.assertEqual(wiring.scheduler.snapshot().tasks["T1"]["attempts"], 1)
            self.assertEqual(wiring.executor.ledger.all_ids(), ids)
            self.assertEqual(wiring.recovery.latest(), recovery_decision)
            self.assertEqual(wiring.recovery.metrics(), recovery_metrics)
            self.assertEqual(len(self.records()), 1)
            return

        self.assertEqual(wiring.scheduler.snapshot().status, "completed",
                         (wiring.scheduler.snapshot(), wiring.recovery.latest()))
        ids = wiring.executor.ledger.all_ids()
        self.assertEqual(len(ids), 2)
        rows = sorted((wiring.executor.ledger.get(aid) for aid in ids), key=lambda row: row["request"]["token"])
        first, second = rows
        self.assertEqual(first["handoff"]["status"], "captured")
        self.assertEqual(second["request"]["base_ref"], first["handoff"]["snapshot_sha"])
        facts = wiring.recovery.describe(first["attempt_id"])
        self.assertEqual(facts["request"]["plan_sha256"], frozen["plan_ref"]["sha256"])
        self.assertTrue(facts["snapshot_verified"])
        self.assertNotEqual(first["workspace"]["path"], second["workspace"]["path"])
        if not reject:
            for row in rows:
                self.assertEqual((Path(row["workspace"]["path"]) / "partial-progress.txt").read_text(),
                                 "preserved partial work\n")
            self.assertTrue((Path(second["workspace"]["path"]) / "recovered.txt").is_file())
        self.assertEqual(wiring.scheduler.snapshot().plan_sha256, frozen["plan_ref"]["sha256"])
        self.assertEqual(support.git(self.repos["app"], "rev-parse", "HEAD"), original_repo)
        self.assertEqual(support.git(self.repos["app"], "status", "--porcelain"), "")
        self.assertEqual(legacy.read_bytes(), b'{"schema":0,"opaque":"preserve"}\n')
        expected_providers = ["claude", "codex"] if quota_reroute else ["claude", "claude"]
        self.assertEqual([row["route"]["provider"] for row in rows], expected_providers)
        self.assertNotEqual(first["route"]["reference"], second["route"]["reference"])
        if quota_reroute:
            decisions = assignment.decision_history["T1"]
            self.assertEqual([record.selected.profile for record in decisions], ["claude-personal", "codex-1"])
            self.assertTrue(any("quota_exhausted" in item.reason_codes for item in decisions[1].exclusions),
                            decisions[1].exclusions)
        prompt = (Path(second["artifacts"]["dir"]) / "prompt.txt").read_text() if "artifacts" in second else \
            (Path(wiring.executor.describe(second["attempt_id"])["artifacts"]["dir"]) / "prompt.txt").read_text()
        self.assertIn("Continue the preserved files", prompt)
        self.assertNotIn("secret-value", json.dumps(wiring.recovery.latest()))
        if monitor:
            all_events = query_events(monitor_path)["items"]
            self.assertTrue(all_events)
            before = wiring.scheduler.snapshot().tasks["T1"].copy()
            wiring.monitor.deliver_incidents("m5-e2e", now=time.time())
            self.assertEqual(wiring.scheduler.snapshot().tasks["T1"], before)
        if restart:
            self.assertTrue(restarted)

    def test_full_chain_continues_partial_snapshot_and_reassigns_through_m2(self):
        self._run_chain()

    def test_restart_after_durable_wait_does_not_duplicate_attempts_or_decisions(self):
        self._run_chain(restart=True)

    def test_quality_rejection_recovers_but_only_new_verdict_can_accept(self):
        self._run_chain(reject=True)

    def test_m4_is_optional(self):
        self._run_chain(monitor=False)

    def test_retry_rechecks_quota_and_moves_from_exhausted_account_a_to_eligible_b(self):
        self._run_chain(quota_reroute=True)

    def test_no_eligible_b_after_retry_does_not_relaunch_an_attempt(self):
        self._run_chain(no_alternate_route=True)

    def test_m5_wait_then_block_does_not_repeat_retry_or_dispatch(self):
        self._run_chain(block_after_wait=True)
