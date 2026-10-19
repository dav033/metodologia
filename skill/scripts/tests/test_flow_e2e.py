"""SUPERRR cross-module proof (T8.1 + T9.3): one real run, from the plan to the web.

SPEC -> PLAN.md -> `plan-json init/check/freeze` -> M2 route map when the run is created -> M1 reserves/dispatches ->
M3 executes -> M4 observes (tokens) -> M6 verifies (first attempt rejected) -> M5 recommends a retry -> M1 accepts the
second attempt -> a classification amendment (medium -> high) changes the route of the NEXT task's attempt -> revision
N+1 adds a task and the run is rebased onto it keeping the accepted work. What the flow bus read from the real stores
and what the pages show is checked at every step. No provider, network or real repository: the same local doubles as
`test_scheduler_m1_m6_e2e`.
"""
from __future__ import annotations

import http.client
import json
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bt_core
import bt_flow_bus as bus
import bt_live_api as live
import bt_plan_adapter as plan_adapter
import bt_scheduler_adapter as scheduler_adapter
import bt_scheduler_executor_wiring as composition
import bt_scheduler_m4_wiring as m4_runtime
import bt_scheduler_run as runtime
import bt_server
import scheduler_chain_support as chain
import scheduler_executor_support as support
from scheduler_executor_support import core
from test_scheduler_m1_m6_e2e import SnapshotAgent

PROJECT, REQ = "flowproj", "REQ-062"


class RoutedM2Port(chain.M2Port):
    """M2's public API as the chain test uses it, plus the full-DAG route map `plan()` and the classification overlay."""

    def __init__(self, ledger_path, route_of, overlay):
        super().__init__(ledger_path, lambda task_id: route_of(task_id))
        self.overlay = overlay

    def close(self):
        pass

    def plan(self, request):
        routes = []
        for view in request.tasks:
            provider, model, profile, effort, *_ = self.route_table(view.id)[0]
            routes.append(core.PlannedRoute(view.id, {"schema_version": core.ROUTING_CONTRACT_VERSION, "provider": provider,
                                                      "model": model, "profile": profile, "effort": effort or ""}))
        return tuple(routes)

    def propose(self, request):
        import dataclasses
        changed = self.overlay()
        views = tuple(dataclasses.replace(v, meta={**v.meta, **changed.get(v.id, {})}) for v in request.ready)
        return super().propose(dataclasses.replace(request, ready=views))


class FlowEndToEnd(support.World):
    tasks = [{"id": "T1", "title": "First", "repo": "app", "after": [], "complexity": "medium"},
             {"id": "T2", "title": "Second", "repo": "app", "after": ["T1"], "complexity": "medium"}]

    def plan(self, tasks):
        repository = self.repos["app"]
        verify = repository / "verify_result.py"
        if not verify.exists():
            verify.write_text("from pathlib import Path\nif Path('result.txt').read_text().strip() != 'PASS':\n"
                              "    raise SystemExit(1)\n", encoding="utf-8")
            support.git(repository, "add", "verify_result.py")
            support.git(repository, "commit", "-q", "-m", "Add verification command")
        pipeline = getattr(self, "pipeline", None) or chain.Pipeline(self, PROJECT, REQ, tasks, ["README.md"])
        self.pipeline = pipeline
        (pipeline.rdir / "SPEC.md").write_text("# Flow proof\n\n## Requirements\n- R1. Show every module talking.\n",
                                               encoding="utf-8")
        text = chain.plan_md(REQ, tasks).replace('python3 -c "raise SystemExit(0)"', "python3 verify_result.py")
        (pipeline.rdir / "PLAN.md").write_text(text, encoding="utf-8")
        with patch.object(bt_core, "ROOT", self.root):
            plan_adapter.run_cli("init", pipeline.rdir, force=True, emit=lambda _line: None)
            chain.classify(pipeline.rdir, tasks, ["README.md"])
            path = pipeline.rdir / "PLAN.json"
            data = json.loads(path.read_text())
            for item in data["tasks"]:
                item["acceptance_criteria"] = ["result.txt contains PASS"]
                item["verification"] = [{"type": "command", "value": "python3 verify_result.py",
                                         "purpose": "result.txt contains PASS", "category": "functional"}]
            path.write_text(json.dumps(data, indent=2))
            pipeline.step("check")
            pipeline.step("freeze")
        self.rdir = pipeline.rdir

    def run_to_completion(self):
        seen = {"live": None, "amended": False}
        self.rdir_holder = {}

        def route_of(task_id):
            high = plan_adapter.effective_overrides(self.rdir).get(task_id, {}).get("complexity") == "high"
            return [("claude", "opus", "claude-personal", "high")] if high else [("claude", "sonnet", "claude-personal", "low")]

        def make_assignment(project, ledger_path, *, laya_root):
            return RoutedM2Port(ledger_path, route_of, lambda: plan_adapter.effective_overrides(self.rdir))

        original_drain = m4_runtime.drain_pending_streams
        original_wire = runtime._wire
        original_composition_wire = composition.wire

        def wire_with_retry_budget(*args, **kwargs):
            kwargs["config"] = core.Config(max_parallel_tasks=1, max_attempts=3)
            return original_composition_wire(*args, **kwargs)

        def drain(wiring, run_id):
            result = original_drain(wiring, run_id)
            attempts = wiring.scheduler.read(lambda ctx: tuple(ctx.state.attempts.values()))
            if attempts and not seen["amended"]:
                seen["amended"] = True                     # discovered while T1 runs: T2 is harder than estimated
                record = plan_adapter.amend(self.rdir, "T2", "complexity", "high", reason="the second task touches "
                                            "more than estimated", evidence=["file:README.md"], by="claude",
                                            proposed_by="agent")
                scheduler_adapter.record_amendment(self.rdir, record)
            if seen["live"] is None and any(a.state in ("running", "verifying") for a in attempts):
                seen["live"] = live.now_items(self.root)    # the "working now" list while an attempt is alive
            return result

        driver = SnapshotAgent()
        with patch.object(runtime.bt_core, "ROOT", self.root), \
                patch("bt_workspace.repos", return_value=self.repos), \
                patch.object(scheduler_adapter, "DecisionAssignmentPort", side_effect=make_assignment), \
                patch.object(composition, "wire", side_effect=wire_with_retry_budget), \
                patch.object(composition.api, "MethodologyDriver", return_value=driver), \
                patch.object(runtime, "_wire", side_effect=original_wire), \
                patch.object(runtime, "_install_autostart"), patch.object(runtime, "_remove_autostart"), \
                patch.object(runtime.bt_notify, "notify"), \
                patch.object(m4_runtime, "drain_pending_streams", side_effect=drain):
            self.assertEqual(runtime.run(PROJECT, REQ, self.rdir, resume=False, no_autostart=True), 0)
        return seen

    def kinds(self, events):
        return [(e["kind"], e["task"], (e.get("data") or {}).get("state")) for e in events]

    def first(self, events, kind, task=None, state=None, after=-1):
        for index, (k, t, s) in enumerate(self.kinds(events)):
            if index > after and k == kind and (task is None or t == task) and (state is None or s == state):
                return index
        self.fail(f"no {kind} {task or ''} {state or ''} after #{after}: {self.kinds(events)}")

    def test_the_whole_chain_from_plan_to_web(self):
        self.plan(self.tasks)
        seen = self.run_to_completion()

        # ---- the bus read every module's own store, in causal order
        with patch.object(bt_core, "ROOT", self.root):
            events = bus.snapshot(self.rdir, PROJECT)
        pos = {}
        pos["run_created"] = self.first(events, "run_created")
        pos["route_map"] = self.first(events, "route_map", after=pos["run_created"] - 1)
        pos["assign"] = self.first(events, "assignment", "T1", after=pos["route_map"])
        pos["start"] = self.first(events, "start_order", "T1", after=pos["assign"])
        pos["stream"] = self.first(events, "stream", "T1", after=pos["start"])
        pos["verifying"] = self.first(events, "state_change", "T1", "verifying", after=pos["stream"])
        pos["verify"] = self.first(events, "verify_order", "T1", after=pos["stream"])
        pos["verdict"] = self.first(events, "verdict", "T1", after=pos["verify"])
        pos["recommend"] = self.first(events, "recommendation", "T1", after=pos["verdict"])
        pos["retry_start"] = self.first(events, "start_order", "T1", after=pos["recommend"])
        pos["accepted"] = self.first(events, "state_change", "T1", "accepted", after=pos["retry_start"])
        pos["amended"] = self.first(events, "amendment")
        ordered = [pos[k] for k in ("run_created", "route_map", "assign", "start", "stream", "verify", "verdict",
                                    "recommend", "retry_start", "accepted")]
        self.assertEqual(ordered, sorted(ordered), pos)
        self.assertNotIn("unknown", [k for k, _, _ in self.kinds(events)])
        tokens = [e for e in events if e["kind"] == "stream" and (e.get("data") or {}).get("tokens")]
        self.assertTrue(tokens, "M4's provider-reported tokens never reached the bus")

        # ---- per-attempt facts: the real route of EACH attempt, tokens as reported (output only for Claude)
        with patch.object(bt_core, "ROOT", self.root):
            from bt_attempt_facts import attempt_facts
            facts = attempt_facts(self.rdir)
        t1 = facts["T1"]
        self.assertEqual([a["state"] for a in t1], ["rejected", "accepted"])
        self.assertEqual({a["route"]["model"] for a in t1}, {"sonnet"})
        self.assertTrue(all(a["route"]["source"] == "m2-ledger" for a in t1))
        self.assertEqual([a["tokens"]["output"] for a in t1], [3, 3])
        self.assertTrue(all(a["tokens"]["total"] is None for a in t1))       # Claude reports output only: no invented total
        self.assertTrue(all(a["duration_s"] is not None and a["duration_s"] >= 0 for a in t1))
        # ---- the classification amendment changed the route of T2's attempt (sonnet before, opus after)
        t2 = facts["T2"]
        self.assertEqual((t2[-1]["state"], t2[-1]["route"]["model"], t2[-1]["route"]["effort"]), ("accepted", "opus", "high"))

        # ---- "working now" was visible while an attempt lived, with its real route
        self.assertTrue(seen["live"], "no live attempt was listed while one was running")
        item = seen["live"][0]
        self.assertEqual((item["project"], item["req_id"], item["task"]), (PROJECT, REQ, "T1"))
        self.assertTrue(item["attempt"]["live"])

        # ---- what the pages show for the finished run (before revision N+1)
        self.serve()
        page = self.get(f"/plans/{PROJECT}/{REQ}")[2]
        self.assertTrue('href="/metrics/model/claude/sonnet/low"' in page, "attempt model chip is not a link")
        self.assertTrue('href="/metrics/model/claude/opus/high"' in page, "amended task's model chip is not a link")
        self.assertTrue("<s>media</s> → <b>alta</b>" in page, "the amendment (old → new) is not shown")
        self.assertTrue("Evolución del plan" in page and 'id="t-T2"' in page)

        # ---- revision N+1: a new task; the run is rebased keeping the accepted work
        tasks3 = self.tasks + [{"id": "T3", "title": "Third", "repo": "app", "after": ["T2"], "complexity": "low"}]
        self.plan(tasks3)
        with patch.object(bt_core, "ROOT", self.root):
            report = scheduler_adapter.rebase_to_latest(self.rdir)
            events2 = bus.snapshot(self.rdir, PROJECT)
        self.assertEqual((report.from_revision, report.to_revision, report.kept, report.added),
                         (1, 2, ("T1", "T2"), ("T3",)))
        self.assertIn("run_rebased", [e["kind"] for e in events2])
        self.assertGreater(len(events2), len(events))

        self.check_web(events2)

    def serve(self):
        for target, attr, value in ((bt_server, "ROOT", self.root), (bt_core, "ROOT", self.root),
                                    (bt_server, "STATE", self.root / ".state"), (bt_core, "STATE", self.root / ".state")):
            patcher = patch.object(target, attr, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), bt_server.Handler)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.addCleanup(self.httpd.server_close)
        self.addCleanup(self.httpd.shutdown)

    def get(self, path):
        conn = http.client.HTTPConnection("127.0.0.1", self.httpd.server_address[1], timeout=10)
        conn.request("GET", path)
        resp = conn.getresponse()
        return resp.status, resp.getheader("Location"), resp.read().decode()

    def check_web(self, events):
        get = self.get
        status, _, page = get(f"/plans/{PROJECT}/{REQ}")
        self.assertEqual(status, 200)
        self.assertTrue("revisión 2" in page and "T2: complejidad" in page and "· r1" in page,
                        "the timeline must keep the amendment of revision 1 after the rebase")

        status, _, body = get(f"/api/flow?scope=run:{PROJECT}/{REQ}")
        served = json.loads(body)["events"]
        self.assertEqual(status, 200)
        self.assertEqual({e["kind"] for e in served} >= {"run_created", "route_map", "assignment", "verdict",
                                                          "recommendation", "run_rebased"}, True)
        self.assertEqual(get(f"/flow?scope=run:{PROJECT}/{REQ}")[0], 200)
        status, location, _ = get(f"/go/{PROJECT}/{REQ}/T2")
        self.assertEqual((status, location), (303, f"/plans/{PROJECT}/{REQ}#t-T2"))
        status, _, stats = get("/metrics/model/claude/sonnet")
        self.assertEqual(status, 200)
        self.assertIn(REQ, stats)                                            # Scheduler attempts feed the model page
        status, _, now = get("/now")
        self.assertEqual(status, 200)
        self.assertIn("Nada se está ejecutando", now)                       # nothing is alive after the rebase


if __name__ == "__main__":
    unittest.main()
