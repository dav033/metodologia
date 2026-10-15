"""The whole chain, collectively: planner (init → classify → check → freeze) → M1 core → M2 decision ledger → M3 executor →
independent verifier, with the methodology's own drivers against fake provider binaries. Plus randomised soak runs that
check cross-module invariants. Each module's own suite covers it alone; this file covers the seams."""
from __future__ import annotations

import hashlib
import json
import os
import random
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scheduler_chain_support as cs
import scheduler_executor_support as s
from scheduler_executor_support import adapter, core

try:
    import bt_scheduler_decision as m2
except Exception:  # noqa: BLE001
    m2 = None


class Chain(s.World):
    def setUp(self):
        super().setUp()
        if m2 is None:
            self.skipTest("M2 module not importable")
        s.bt_profiles.add("agy-1", "antigravity")                      # M2 requires a named profile for every route
        self.ledger_path = self.tmp / "m2-decisions.db"

    # ---------------------------------------------------------------------------------------------- helpers
    def build(self, tasks, req="REQ-050", route_table=None, **wire_kw):
        pipe = cs.Pipeline(self, "chainproj", req, tasks, ["README.md"])
        self.state_fields = pipe.run()
        self.rdir = pipe.rdir
        self.m2port = cs.M2Port(self.ledger_path, route_table or cs.rotating())
        return self.open(**wire_kw)

    def open(self, verifier=None, **kw):
        verifier = verifier or s.Verifier()
        with patch.object(s.bt_profiles, "ROOT", self.root):
            wiring = adapter.wire(self.rdir, project="chainproj", assignment=self.m2port, verification=verifier,
                                  repos=self.repos, default_repository="app", m2_ledger=self.ledger_path,
                                  config=core.Config(max_parallel_tasks=kw.pop("parallel", 3),
                                                     max_attempts=kw.pop("max_attempts", 1)),
                                  executor_config=adapter.m3.Config(poll_seconds=0.05, grace_seconds=1.0,
                                                                    timeout_seconds=60,
                                                                    heartbeat_seconds=kw.pop("heartbeat_seconds", 3600)),
                                  **kw)
        verifier.scheduler = wiring.scheduler
        self.verifier = verifier
        self.wirings.append(wiring)
        return wiring

    def strays(self):
        found = []
        for entry in Path("/proc").iterdir():
            if entry.name.isdigit() and int(entry.name) != os.getpid():
                try:
                    if os.readlink(entry / "cwd").startswith(str(self.tmp)):
                        found.append((int(entry.name), (entry / "cmdline").read_bytes()[:60]))
                except OSError:
                    pass
        return found

    def attempts(self, w):
        return [w.executor.ledger.get(a) for a in w.executor.ledger.all_ids()]

    @staticmethod
    def dag(n=6):
        tasks = [{"id": "T1", "title": "Foundation piece", "repo": "app", "after": []},
                 {"id": "T2", "title": "Left branch piece", "repo": "app", "after": ["T1"]},
                 {"id": "T3", "title": "Right branch piece", "repo": "docs", "after": ["T1"]},
                 {"id": "T4", "title": "Independent piece", "repo": "docs", "after": []},
                 {"id": "T5", "title": "Join piece", "repo": "app", "after": ["T2", "T3"]},
                 {"id": "T6", "title": "Final piece", "repo": "app", "after": ["T5", "T4"]}]
        return tasks[:n]

    # ---------------------------------------------------------------------------------------------- the happy chain
    def test_a_plan_goes_through_planner_m1_m2_m3_and_only_the_verifier_completes_it(self):
        w = self.build(self.dag())
        self.assertTrue(self.run_until(w, lambda snap: snap.status == "completed", 90), w.scheduler.snapshot())
        snap = w.scheduler.snapshot()
        self.assertEqual({t: v["state"] for t, v in snap.tasks.items()}, {f"T{i}": "completed" for i in range(1, 7)})
        self.assertEqual(sorted(o.task_id for o in self.verifier.orders), [f"T{i}" for i in range(1, 7)])
        self.assertTrue(all(v["verifier"] == "independent-test-verifier" for v in snap.tasks.values()))
        self.assertEqual(len(self.records()), 6)
        self.assertEqual(self.strays(), [])

    def test_the_same_plan_identity_is_seen_by_every_module(self):
        w = self.build(self.dag(4))
        self.assertTrue(self.run_until(w, lambda snap: snap.status == "completed", 90))
        planner_sha = self.state_fields["plan_ref"]["sha256"]
        self.assertEqual(w.scheduler.snapshot().plan_sha256, planner_sha)                      # planner == M1
        manifest = json.loads((self.rdir / "plan-revisions" / "MANIFEST.json").read_text())
        self.assertEqual(manifest["revisions"][-1]["sha256"], planner_sha)
        frozen = (self.rdir / "plan-revisions" / "PLAN.r1.json").read_bytes()
        self.assertEqual(hashlib.sha256(frozen).hexdigest(), planner_sha)                       # bytes on disk == approved hash
        for tid, record in self.m2port.decisions.items():
            self.assertEqual(record.plan_sha256, planner_sha, tid)                              # M2 decided on that plan
        for row in self.attempts(w):
            self.assertEqual(row["request"]["plan_id"], "REQ-050")                              # M3 serves that run only
        ledger = w.executor.ledger
        self.assertEqual(ledger.bound_run(), "REQ-050:r1")                                      # the root is bound to this run
        self.assertTrue(ledger.run_matches("REQ-050", 1))
        self.assertFalse(ledger.run_matches("REQ-050", 2))                                      # and to no other revision
        self.assertFalse(ledger.run_matches("REQ-999", 1))                                      # nor to another plan

    def test_every_hop_names_the_same_route_and_the_provider_ran_exactly_that(self):
        w = self.build(self.dag(5))
        self.assertTrue(self.run_until(w, lambda snap: snap.status == "completed", 90))
        snap = w.scheduler.snapshot()
        by_task = {a["request"]["task_id"]: a for a in self.attempts(w)}
        for tid, record in self.m2port.decisions.items():
            reference = "route:" + self.m2port.m2.executor_reference(record.decision_id, record.selected.route_id)
            self.assertEqual(snap.tasks[tid]["executor"], reference, tid)                       # M1 carries M2's reference
            row = by_task[tid]
            self.assertEqual(row["request"]["executor"], reference)                             # M3 got it verbatim
            self.assertEqual((row["route"]["provider"], row["route"]["model"], row["route"]["profile"]),
                             (record.selected.provider, record.selected.model, record.selected.profile))
        flag = {"claude": "--model", "codex": "-m", "agy": "--model"}
        ran = sorted((r["provider"], r["argv"][r["argv"].index(flag[r["provider"]]) + 1]) for r in self.records())
        want = sorted(({"claude": "claude", "codex": "codex", "antigravity": "agy"}[r.selected.provider],
                       r.selected.model) for r in self.m2port.decisions.values())
        self.assertEqual(ran, want)                                                             # the binaries ran M2's choice

    def test_no_stage_can_complete_a_task_by_itself(self):
        w = self.build(self.dag(3), verifier=s.Verifier(accept=False))
        self.assertTrue(self.run_until(w, lambda snap: snap.status == "blocked", 90))
        self.assertEqual({v["state"] for v in w.scheduler.snapshot().tasks.values()} & {"completed"}, set())
        self.assertTrue(all(a["state"] == "finished" for a in self.attempts(w)))              # M3 says "stopped", M1 says "no"

    # ---------------------------------------------------------------------------------------------- faults across the seams
    def test_a_quota_failure_on_the_route_m2_chose_blocks_only_its_branch(self):
        tasks = self.dag()
        tasks[1] = {**tasks[1], "title": "Left branch piece SCENARIO:quota"}
        w = self.build(tasks)
        self.assertTrue(self.run_until(w, lambda snap: snap.status == "blocked", 90), w.scheduler.snapshot())
        snap = w.scheduler.snapshot()
        self.assertEqual(snap.tasks["T2"]["state"], "blocked")
        self.assertEqual({t for t, v in snap.tasks.items() if v["unreachable"]}, {"T5", "T6"})
        self.assertEqual({t: v["state"] for t, v in snap.tasks.items() if t in ("T1", "T3", "T4")},
                         {"T1": "completed", "T3": "completed", "T4": "completed"})
        failed = next(a for a in self.attempts(w) if a["request"]["task_id"] == "T2")
        self.assertEqual(failed["outcome"]["cause"], "quota_exhausted")
        self.assertTrue(failed["handoff"]["dirty"])                                              # the half-done work survives
        self.assertEqual(len([r for r in self.records() if "T5" in r["cwd"] or "T6" in r["cwd"]]), 0)
        self.assertEqual(self.strays(), [])

    def test_an_unresolvable_m2_reference_never_starts_anything(self):
        w = self.build(self.dag(1))
        w.scheduler.ports.assignment = type("Bad", (), {"propose": lambda self, request: [
            core.Assignment(v.id, "m2:v1:" + "0" * 64 + ":" + "1" * 64) for v in request.ready]})()
        self.assertTrue(self.run_until(w, lambda snap: snap.status == "blocked", 60))
        self.assertEqual(self.records(), [])
        self.assertEqual(w.executor.ledger.get("att-0001")["rejection"]["code"], "ROUTE_UNRESOLVABLE")

    def test_the_planners_frozen_revision_is_what_runs_and_a_later_edit_stops_everything(self):
        self.build(self.dag(2))
        plan_json = self.rdir / "PLAN.json"
        revision = self.rdir / "plan-revisions" / "PLAN.r1.json"
        self.assertEqual(revision.stat().st_mode & 0o222, 0, "the planner freezes the approved revision read-only")
        revision.chmod(0o644)
        revision.write_text(revision.read_text().replace('"title"', '"title" ', 1))              # tamper with the approved file
        with self.assertRaises(core.SchedulerError):
            self.open()
        self.assertEqual(self.records(), [])
        self.assertTrue(plan_json.exists())

    def test_a_restart_of_every_layer_in_the_middle_of_a_run_loses_nothing(self):
        os.environ["FAKE_DELAY"] = "1.2"
        self.addCleanup(os.environ.pop, "FAKE_DELAY", None)
        w = self.build(self.dag(4))
        self.assertTrue(self.run_until(w, lambda snap: any(v["state"] == "active" for v in snap.tasks.values())
                                       and w.executor.ledger.count(("running",)) >= 1, 60))
        w.close()                                                                               # executor + core handle gone
        w2 = self.open()                                                                        # same planner revision, same M2 ledger
        self.assertTrue(self.run_until(w2, lambda snap: snap.status == "completed", 120), w2.scheduler.snapshot())
        self.assertEqual(len(self.records()), 4)                                                # four tasks, four runs, none twice
        self.assertEqual(len({r["cwd"] for r in self.records()}), 4)
        self.assertEqual(self.strays(), [])

    def test_the_users_checkout_is_never_touched_by_any_stage(self):
        before = {n: (s.git(p, "rev-parse", "HEAD"), s.git(p, "status", "--porcelain")) for n, p in self.repos.items()}
        w = self.build(self.dag(), route_table=cs.rotating(1))
        self.assertTrue(self.run_until(w, lambda snap: snap.status == "completed", 90))
        after = {n: (s.git(p, "rev-parse", "HEAD"), s.git(p, "status", "--porcelain")) for n, p in self.repos.items()}
        self.assertEqual(after, before)

    def test_a_heartbeat_travels_executor_to_core_and_proves_nothing(self):
        os.environ["FAKE_DELAY"] = "1.5"
        self.addCleanup(os.environ.pop, "FAKE_DELAY", None)
        w = self.build(self.dag(1), heartbeat_seconds=0.2)
        seen, real = [], w.scheduler.ingest

        def spy(event):
            result = real(event)
            seen.append((event.kind, getattr(result, "reason", None)))
            return result

        w.scheduler.ingest = spy
        self.assertTrue(self.run_until(w, lambda snap: snap.status == "completed", 60), w.scheduler.snapshot())
        beats = [reason for kind, reason in seen if kind == "heartbeat"]
        self.assertTrue(beats, f"no heartbeat reached the core: {seen}")
        self.assertEqual(set(beats), {"liveness_hint"})                                         # M1 took them as hints only
        self.assertEqual(w.scheduler.snapshot().tasks["T1"]["attempts"], 1)                     # and counted no extra attempt

    def test_a_transient_executor_refusal_goes_through_the_real_core_without_burning_the_attempt(self):
        w = self.build(self.dag(2), max_attempts=1)
        real, calls = w.executor.start, []

        def flaky(request):
            calls.append(request.attempt_id)
            if len(calls) == 1:
                return adapter.m3.Receipt("rejected", "LEDGER_ERROR", "disk hiccup", request.attempt_id)
            return real(request)

        w.executor.start = flaky
        self.assertTrue(self.run_until(w, lambda snap: snap.status == "completed", 90), w.scheduler.snapshot())
        self.assertGreater(len(calls), 1)
        snap = w.scheduler.snapshot()
        self.assertEqual({t: v["attempts"] for t, v in snap.tasks.items()}, {"T1": 1, "T2": 1})   # budget of 1 was enough
        self.assertEqual(len(self.records()), 2)

    def test_a_second_core_run_of_the_same_plan_gets_its_own_executor_root_and_runs_again(self):
        w = self.build(self.dag(2))
        self.assertTrue(self.run_until(w, lambda snap: snap.status == "completed", 60))
        first_root = w.executor.root
        w.close()
        db = adapter.sched.run_db_path(self.rdir)                                               # a NEW run of the same revision
        for suffix in ("", "-wal", "-shm"):
            Path(str(db) + suffix).unlink(missing_ok=True)
        w2 = self.open()
        self.assertNotEqual(w2.executor.root, first_root)
        self.assertTrue(self.run_until(w2, lambda snap: snap.status == "completed", 90), w2.scheduler.snapshot())
        self.assertEqual(len(self.records()), 4, "the second run reused the first run's finished attempts")
        self.assertEqual(self.strays(), [])

    # ---------------------------------------------------------------------------------------------- randomised soak
    def soak(self, seed: int):
        rnd = random.Random(seed)
        n = rnd.randint(5, 9)
        scenarios = rnd.choices(["ok", "commit", "dirty", "quota", "net", "crash", "partial"],
                                weights=[5, 2, 2, 1, 1, 1, 1], k=n)
        tasks = []
        for i in range(1, n + 1):
            deps = sorted(rnd.sample([f"T{j}" for j in range(1, i)], rnd.randint(0, min(2, i - 1))), key=lambda t: int(t[1:]))
            tasks.append({"id": f"T{i}", "title": f"Piece number {i} SCENARIO:{scenarios[i - 1]}",
                          "repo": rnd.choice(["app", "docs"]), "after": deps})
        w = self.build(tasks, req=f"REQ-{100 + seed}", route_table=cs.rotating(seed),
                       parallel=rnd.randint(1, 4), max_attempts=rnd.randint(1, 2))
        self.assertTrue(self.run_until(w, lambda snap: snap.status in ("completed", "blocked"), 150),
                        (seed, w.scheduler.snapshot()))
        self.assertTrue(w.executor.wait_idle(60), f"seed {seed}: events not delivered")
        snap = w.scheduler.snapshot()
        def provider_of(tid):
            record = self.m2port.decisions.get(tid)
            return record.selected.provider if record is not None and record.selected is not None else None
        # a clean exit WITHOUT end-of-turn evidence is a failure everywhere except Codex, which has no such marker (documented
        # limit: its clean = exit 0 with output; M1 still needs the independent verdict, which this stub grants)
        failing = {f"T{i}" for i, sc in enumerate(scenarios, 1)
                   if sc in ("quota", "net", "crash") or (sc == "partial" and provider_of(f"T{i}") not in ("codex", None))}
        for t in tasks:
            v = snap.tasks[t["id"]]
            if t["id"] in failing:
                self.assertNotEqual(v["state"], "completed", (seed, t["id"]))                   # a failing agent is never accepted
            if v["state"] == "completed":
                self.assertEqual(v["verifier"], "independent-test-verifier", (seed, t["id"]))
                self.assertTrue(v["evidence"])
                for dep in t["after"]:
                    self.assertEqual(snap.tasks[dep]["state"], "completed", (seed, t["id"], dep))   # no task before its prerequisites
        if snap.status == "completed":
            self.assertFalse(failing, seed)
        else:
            self.assertTrue(failing, f"seed {seed}: blocked with no failing task")
        # M1 <-> M3 agree on every attempt, and each ends with exactly one terminal event
        trail = {e.attempt_id for e in w.scheduler.audit_log() if e.attempt_id}
        self.assertEqual(sorted(w.executor.ledger.all_ids()), sorted(trail), seed)
        for row in self.attempts(w):
            self.assertIn(row["state"], ("finished", "failed", "rejected", "cancelled"), (seed, row["attempt_id"]))
            kinds = [e["kind"] for e in w.executor.ledger.events(row["attempt_id"])
                     if e["kind"] in ("execution_finished", "execution_failed", "execution_cancelled")]
            self.assertEqual(len(kinds), 0 if row["state"] == "rejected" else 1, (seed, row["attempt_id"], kinds))
            self.assertTrue(all(e["delivered"] for e in w.executor.ledger.events(row["attempt_id"])))
        started = [a for a in self.attempts(w) if a["state"] != "rejected"]
        self.assertEqual(len(self.records()), len(started), f"seed {seed}: provider runs != attempts")
        cwds = [r["cwd"] for r in self.records()]
        self.assertEqual(len(cwds), len(set(cwds)), f"seed {seed}: two runs shared a worktree")
        for tid in {t for t, v in snap.tasks.items() if v["unreachable"]}:
            self.assertEqual(snap.tasks[tid]["attempts"], 0, (seed, tid))                       # nothing downstream of a block ran
        for tid, record in self.m2port.decisions.items():
            self.assertEqual(record.plan_sha256, self.state_fields["plan_ref"]["sha256"])
        self.assertEqual(self.strays(), [], f"seed {seed}")
        for p in self.repos.values():
            self.assertEqual(s.git(p, "status", "--porcelain"), "", f"seed {seed}: a checkout was dirtied")

    def test_randomised_plans_keep_every_cross_module_invariant(self):
        for seed in range(1, 1 + int(os.environ.get("BITACORA_CHAIN_SEEDS", "6"))):
            with self.subTest(seed=seed):
                try:
                    self.soak(seed)
                finally:
                    self.cleanup_world()

    def cleanup_world(self):
        """Fresh processes/repos between seeds inside one test."""
        for wiring in self.wirings:
            wiring.close()
        self.wirings.clear()
        if self.record.exists():
            self.record.unlink()
        for key in self.repos:
            self.repos[key] = s.make_repo(self.tmp / f"{key}-{time.monotonic_ns()}")
        import shutil
        shutil.rmtree(self.root / "chainproj", ignore_errors=True)
        if self.ledger_path.exists():
            self.ledger_path.unlink()


if __name__ == "__main__":
    unittest.main()
