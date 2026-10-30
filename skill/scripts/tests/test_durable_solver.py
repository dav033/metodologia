"""The Solucionador (REQ-031): what healing leaves for a person, a repeated failure, a stuck task or a run in ERROR starts
one full-access session per run, with its brief, once per trigger, within the limits; its result.json, its absence, the
watchdog or a spent account close or move it. On 2026-10-29 an operator did all of this by hand for pictures REQ-021.

No tmux, no agent and no database: the terminal, the route, the owner's notification and the client are fakes."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_agent_terminal
from bt_durable import cli, solver
from bt_durable.service import _PassStatus

FLAGS = {"healing.enabled": True, "healing.model_diagnosis": True, "diagnosis.auto": True, "solver.enabled": True,
         "solver.max_concurrent": 1, "solver.max_per_task": 3, "solver.max_minutes": 120, "solver.stuck_minutes": 45,
         "scheduler.attempt_timeout_minutes": 120}


class Terminal:
    name_for = staticmethod(bt_agent_terminal.name_for)

    def __init__(self):
        self.live, self.started, self.sent, self.killed, self.shown = set(), [], [], [], ""

    def exists(self, name):
        return name in self.live

    def start(self, name, cwd, command, env, scope=""):
        if name in self.live:
            raise RuntimeError("taken")
        self.live.add(name)
        self.started.append({"name": name, "cwd": cwd, "command": command, "env": env, "scope": scope})

    def screen(self, name, lines=40):
        return self.shown

    def send(self, name, text):
        self.sent.append((name, text))
        return "Enviado."

    def kill(self, name):
        self.killed.append(name)
        self.live.discard(name)
        return True


class Client:
    def __init__(self):
        self.runs = {}

    def status(self, run):
        return self.runs.get(run.run_id) or {"run_id": run.run_id, "workflow_id": f"bt:{run.run_id}",
                                             "workflow_status": "PENDING", "summary": None, "tasks": {}}


def decision(request="T7.4:d1"):
    return {"request_id": request, "task_id": "T7.4", "reason": "the task used its attempts", "limit_hit": "max_attempts",
            "options": ["retry", "retry_with_note", "stop"],
            "failure": {"failure_class": "integration", "code": "INTEGRATION_CONFLICT", "signature": "sig",
                        "summary": "package.json (line of SP-7)",
                        "evidence": [{"kind": "output_line", "excerpt": "CONFLICT (content): package.json"}]}}


class SolverTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="bt-solver-"))
        self.root = self.base / "root"
        self.clock = [1_000_000.0]
        self.terminal, self.client = Terminal(), Client()
        self.notified, self.activity, self.routes = [], [], []
        self.route = {"provider": "claude", "home": "/acc/luis", "model": "opus", "effort": "high"}
        self.rdirs = {req: self.make_run(req) for req in ("REQ-900", "REQ-901")}
        for p in (patch("bt_config.get", side_effect=lambda key, default=None: FLAGS.get(key, default)),):
            p.start()
            self.addCleanup(p.stop)

    def make_run(self, req):
        rdir = self.root / "proj" / "requirements" / f"{req}-x"
        (rdir / "plan-revisions").mkdir(parents=True)
        plan = rdir / "plan-revisions" / "PLAN.r1.json"
        plan.write_text(json.dumps({"tasks": [{"id": "T7.4", "title": "Checkpoint", "objective": "Gate",
                                               "acceptance_criteria": ["merges"], "verification": []}]}))
        (rdir / "RUN.durable-run.json").write_text(json.dumps(
            {"project": "proj", "req": req, "revision": 1, "plan_id": req, "plan_path": str(plan), "plan_sha256": "0" * 64}))
        return rdir

    def open_decision(self, req="REQ-900", request="T7.4:d1", round_no=2):
        run_id = f"proj:{req}:r1"
        self.client.runs[run_id] = {"run_id": run_id, "workflow_id": f"bt:{run_id}", "workflow_status": "PENDING",
                                    "summary": {"status": "running"}, "tasks": {"T7.4": {
                                        "workflow_id": f"bt:{run_id}:T7.4:k{round_no}", "workflow_status": "PENDING",
                                        "state": {"state": "needs_decision"}, "decision": decision(request)}}}
        return solver.trigger("decision", f"{run_id}:T7.4:{request}@k{round_no}", run_id, task_id="T7.4",
                              request_id=request, round_no=round_no, reason="healing's repair limit is reached")

    def route_for(self, project, avoid):
        self.routes.append(avoid)
        return self.route

    def solver(self):
        return solver.Solver(self.root, self.client, terminal=self.terminal, route_for=self.route_for,
                             notify=lambda title, text: self.notified.append(text),
                             record=lambda rdir, text: self.activity.append(text), now=lambda: self.clock[0],
                             work=self.base / "work")

    def state(self, req="REQ-900"):
        return solver.load(self.rdirs[req])

    def session(self, req="REQ-900"):
        state = self.state(req)
        return next(s for s in state["sessions"] if s["id"] == state.get("active", state["sessions"][-1]["id"]))

    def test_a_decision_healing_left_starts_one_full_access_session_with_its_brief(self):
        said = self.solver().run_pass([self.open_decision()])
        self.assertEqual(len(self.terminal.started), 1, said)
        started = self.terminal.started[0]
        self.assertEqual(started["name"], "bit-proj-REQ-900-solver")
        for flag in ("claude --session-id", "--model opus --effort high", "--dangerously-skip-permissions", "PROMPT.md"):
            self.assertIn(flag, started["command"])
        self.assertEqual(started["env"]["CLAUDE_CONFIG_DIR"], "/acc/luis")
        self.assertTrue(started["scope"].startswith("bt-solver-"))         # outside bt-durable.service's cgroup
        self.assertNotIn(str(Path.home() / "dev" / "metodologia"), str(started["cwd"]))   # never the live checkout
        session = self.session()
        folder = Path(session["dir"])
        brief = (folder / "BRIEF.md").read_text()
        for text in ("CONFLICT (content): package.json", "healing's repair limit is reached", "bt-durable answer proj "
                     "REQ-900", "--by solver", "bt_integrate.py --branch solver/", "tell-planner proj REQ-900",
                     "journalctl --user -u bt-durable.service", "DECISIONS.md", str(self.rdirs["REQ-900"] / "RUN.notes")):
            self.assertIn(text, brief)
        prompt = (folder / "PROMPT.md").read_text()
        self.assertIn("You are the Solucionador", prompt)
        self.assertIn("never built or repaired through metodologia's own scheduler", prompt)
        self.assertIn(str(folder / "BRIEF.md"), prompt)
        self.assertEqual(json.loads((folder / "triggers.json").read_text())[0]["request_id"], "T7.4:d1")
        self.assertEqual(self.state()["tasks"], {"T7.4": 1})

    def test_once_per_key_one_per_run_and_one_on_the_machine(self):
        first = self.open_decision()
        self.solver().run_pass([first])
        self.solver().run_pass([first])                                       # the same key: nothing new
        self.assertEqual(len(self.terminal.started), 1)
        self.client.runs["proj:REQ-900:r1"]["workflow_status"] = "ERROR"
        later = {"key": "proj:REQ-900:r1:error:bt:proj:REQ-900:r1"}
        self.solver().run_pass([])                                           # its run's session is busy: inbox
        self.assertEqual(len(self.terminal.started), 1)
        inbox = (Path(self.session()["dir"]) / "inbox.jsonl").read_text()
        self.assertIn(later["key"], inbox)
        self.assertIn("inbox.jsonl", self.terminal.sent[0][1])
        other = self.open_decision("REQ-901")
        self.solver().run_pass([other])                                      # max_concurrent 1: it waits
        self.assertEqual(len(self.terminal.started), 1)
        self.assertEqual(self.state("REQ-901")["triggers"][other["key"]]["status"], "pending")
        folder = Path(self.session()["dir"])
        (folder / "result.json").write_text(json.dumps({"outcome": "fixed", "summary": "integrador arreglado (D-900)",
                                                        "handled": [first["key"]]}))
        self.solver().run_pass([])
        self.assertIn("bit-proj-REQ-900-solver", self.terminal.killed)
        triggers = self.state()["triggers"]
        self.assertEqual(triggers[first["key"]]["status"], "fixed")
        self.assertEqual([s["status"] for s in self.state()["sessions"]], ["fixed", "running"])   # the inbox's turn
        self.assertEqual(triggers[later["key"]]["status"], "running")
        self.assertEqual(self.state("REQ-901")["triggers"][other["key"]]["status"], "pending")   # the slot was taken
        self.assertTrue(any("arreglado en su origen" in line for line in self.activity))

    def test_the_watchdog_and_a_vanished_session_give_up_and_tell_the_owner(self):
        self.solver().run_pass([self.open_decision()])
        self.clock[0] += 121 * 60
        self.solver().run_pass([])
        session = self.state()["sessions"][0]
        self.assertEqual(session["status"], "gave_up")
        self.assertIn("120 min", session["summary"])
        self.assertIn("bit-proj-REQ-900-solver", self.terminal.killed)
        self.assertTrue(self.notified)
        self.solver().run_pass([self.open_decision(request="T7.4:d2", round_no=3)])
        self.terminal.live.clear()                                           # the agent's shell is gone
        self.solver().run_pass([])
        self.assertEqual(self.state()["sessions"][1]["summary"], "la sesión terminó sin escribir result.json")

    def test_a_spent_account_moves_the_session_and_keeps_its_conversation(self):
        self.solver().run_pass([self.open_decision()])
        sid = self.session()["session_id"]
        self.terminal.shown = "You've hit your weekly limit · resets 3pm"
        self.route = {"provider": "claude", "home": "/acc/work", "model": "opus", "effort": "high"}
        with patch.object(bt_agent_terminal, "transcript", side_effect=lambda home, cwd, s: self.base / home.strip("/") / f"{s}.jsonl"):
            (self.base / "acc" / "luis").mkdir(parents=True)
            (self.base / "acc" / "luis" / f"{sid}.jsonl").write_text("{}\n")
            self.solver().run_pass([])
        self.assertEqual(self.routes, ["", "/acc/luis"])
        self.assertIn(f"claude --resume {sid}", self.terminal.started[-1]["command"])
        self.assertEqual(self.terminal.started[-1]["env"]["CLAUDE_CONFIG_DIR"], "/acc/work")
        self.assertEqual(self.session()["restarts"], 1)
        self.solver().run_pass([])
        self.solver().run_pass([])                                           # MAX_RESTARTS reached
        self.assertEqual(self.state()["sessions"][0]["status"], "gave_up")

    def test_codex_runs_it_when_no_claude_account_can(self):
        self.route = {"provider": "codex", "home": "/acc/codex-luis", "model": "gpt-6.1-sol", "effort": "high"}
        self.solver().run_pass([self.open_decision()])
        started = self.terminal.started[0]
        self.assertIn("codex --dangerously-bypass-approvals-and-sandbox -m gpt-6.1-sol", started["command"])
        self.assertEqual(started["env"]["CODEX_HOME"], "/acc/codex-luis")

    def test_a_stuck_task_and_a_run_in_error_are_triggers(self):
        run_id = "proj:REQ-900:r1"
        task = {"workflow_id": f"bt:{run_id}:T7.4:k1", "workflow_status": "PENDING", "state": {"state": "routing"},
                "decision": None}
        self.client.runs[run_id] = {"run_id": run_id, "workflow_id": f"bt:{run_id}", "workflow_status": "PENDING",
                                    "tasks": {"T7.4": task}}
        self.solver().run_pass([])
        self.clock[0] += 44 * 60
        self.solver().run_pass([])
        self.assertEqual(self.terminal.started, [])
        self.clock[0] += 2 * 60
        self.solver().run_pass([])
        self.assertEqual(self.session()["kind"], "stuck")
        running = {"workflow_id": f"bt:{run_id}:T7.4:k1", "workflow_status": "PENDING",
                   "state": {"state": "running", "attempt": "a1"}}
        watch = {"T7.4": running}
        state = {}
        self.assertEqual(solver.stuck_triggers(type("R", (), {"run_id": run_id})(), {"tasks": watch}, state, 0.0,
                                               solver.settings()), [])
        self.assertEqual(solver.stuck_triggers(type("R", (), {"run_id": run_id})(), {"tasks": watch}, state,
                                               (120 + 46) * 60.0, solver.settings())[0]["kind"], "stuck")
        errored = {"workflow_id": f"bt:{run_id}@2", "workflow_status": "ERROR"}
        self.assertEqual(solver.error_triggers(type("R", (), {"run_id": run_id})(), errored)[0]["key"],
                         f"{run_id}:error:bt:{run_id}@2")

    def test_a_run_with_nothing_live_and_nothing_to_answer_is_stalled(self):
        """pictures REQ-021 r25, 2026-10-29: the run workflow PENDING, every task workflow ended, no decision, while gate
        CG-7's composition failed every turn; no trigger saw it. The brief carries the gate's failed turns."""
        run_id = "proj:REQ-900:r1"
        done = {"workflow_id": f"bt:{run_id}:T7.4:k1", "workflow_status": "SUCCESS", "state": {"state": "completed"},
                "decision": None}
        summary = {"status": "running", "tasks": {"T7.4": "completed"}, "gates": {"composed": {}, "rejected": {}}}
        self.client.runs[run_id] = {"run_id": run_id, "workflow_id": f"bt:{run_id}", "workflow_status": "PENDING",
                                    "summary": summary, "tasks": {"T7.4": done}}
        telemetry = self.root / ".state" / "durable" / "telemetry.jsonl"
        telemetry.parent.mkdir(parents=True)
        telemetry.write_text("".join(json.dumps(row) + "\n" for row in (
            {"event": "gate_compose_failed", "run_id": run_id, "gate": "CG-7", "turn": 1,
             "reason": "StepFailure: GitCommandError: git merge-tree … app/[locale]/page.tsx"},
            {"event": "gate_compose_failed", "run_id": "proj:REQ-901:r1", "gate": "CG-1", "turn": 1, "reason": "other"},
            {"event": "task_settled", "run_id": run_id, "task_id": "T7.4", "status": "completed"})))
        self.solver().run_pass([])                       # first sight (an engine just restarted): the clock starts
        self.clock[0] += 44 * 60
        self.solver().run_pass([])
        self.assertEqual(self.terminal.started, [])
        self.clock[0] += 2 * 60
        self.solver().run_pass([])
        session = self.session()
        self.assertEqual(session["kind"], "stalled")
        brief = (Path(session["dir"]) / "BRIEF.md").read_text()
        self.assertIn("## Composition gates", brief)
        self.assertIn("CG-7", brief)
        self.assertIn("GitCommandError", brief)
        self.assertNotIn("CG-1", brief)                  # another run's gate

    def test_a_run_that_ended_with_a_rejected_gate_starts_a_session_at_once(self):
        """pictures REQ-021 r25, 2026-10-29 23:19: the run workflow ended SUCCESS/blocked with CG-7 rejected after three
        failed compositions; no decision, no ERROR, RUN.solver/state.json stayed empty."""
        run_id = "proj:REQ-900:r1"
        plan = Path(json.loads((self.rdirs["REQ-900"] / "RUN.durable-run.json").read_text())["plan_path"])
        plan.write_text(json.dumps({"tasks": [{"id": "T97", "title": "Gate"}],
                                    "composition_gates": [{"id": "CG-7", "subplans": ["SP-7"], "task": "T97"}]}))
        reason = ("COMPOSE_FAILED 3 turns: DBOSMaxStepRetriesExceeded: DBOS Error 7: Step bt.compose has exceeded its "
                  "maximum of 3 retries (last: StepFailure: GitCommandError: app/[locale]/page.tsx)")
        self.client.runs[run_id] = {"run_id": run_id, "workflow_id": f"bt:{run_id}", "workflow_status": "SUCCESS",
                                    "summary": {"status": "blocked", "tasks": {"T96": "completed"},
                                                "gates": {"composed": {"CG-6": "C3"}, "rejected": {"CG-7": reason}}},
                                    "tasks": {}}
        self.solver().run_pass([])                                       # no wait: nothing will change by itself
        session = self.session()
        self.assertEqual(session["kind"], "ended")
        brief = (Path(session["dir"]) / "BRIEF.md").read_text()
        self.assertIn("GitCommandError", brief)
        self.assertIn("bt-durable retry-task proj REQ-900 T97", brief)
        self.solver().run_pass([])
        self.assertEqual(len(self.state()["sessions"]), 1)                # once per run workflow and gate set
        self.client.runs[run_id] = {**self.client.runs[run_id], "workflow_id": f"bt:{run_id}@2",
                                    "workflow_status": "PENDING"}         # the retry reopened it: the trigger is done
        self.assertFalse(solver.Solver._current(self.state()["triggers"][session["triggers"][0]], {},
                                                self.client.runs[run_id]))

    def test_a_run_the_owner_stopped_is_not_a_block_for_the_solver(self):
        run = type("R", (), {"run_id": "proj:REQ-900:r1"})()
        ended = {"workflow_id": "bt:proj:REQ-900:r1", "workflow_status": "SUCCESS",
                 "summary": {"status": "blocked", "tasks": {"T1": "completed", "T2": "blocked"}}}
        self.assertEqual(solver.ended_triggers(run, ended, {"T2"}), [])            # the owner stopped T2
        self.assertEqual(solver.ended_triggers(run, ended, set())[0]["blocked"], ["T2"])
        done = {**ended, "summary": {"status": "completed", "tasks": {"T1": "completed"}}}
        self.assertEqual(solver.ended_triggers(run, done, set()), [])
        rdir = self.rdirs["REQ-900"]
        telemetry = self.base / "telemetry.jsonl"
        telemetry.write_text(json.dumps({"event": "decision_answered", "run_id": "proj:REQ-900:r1", "task_id": "T2",
                                         "action": "stop", "by": "owner"}) + "\n" +
                             json.dumps({"event": "decision_answered", "run_id": "proj:REQ-900:r1", "task_id": "T3",
                                         "action": "stop", "by": "solver"}) + "\n")
        (rdir / "RUN.decisions.jsonl").write_text(json.dumps({"task": "T4", "option": "stop", "by": "owner"}) + "\n")
        self.assertEqual(solver.owner_stops(rdir, telemetry, "proj:REQ-900:r1"), {"T2", "T4"})

    def test_a_spent_step_reports_its_cause(self):
        """The reason the run records (gate_compose_failed, the rejected gate, a child's internal_error) is what the
        brief shows: r25's said only that bt.compose ran out of retries, not why."""
        import pickle

        from bt_durable.execution import steps, workflows
        from dbos._error import DBOSMaxStepRetriesExceeded
        spent = DBOSMaxStepRetriesExceeded("bt.compose", 3, [steps.StepFailure("GitCommandError: app/[locale]/page.tsx")])
        for error in (spent, pickle.loads(pickle.dumps(spent))):          # as raised, and as DBOS replays it
            self.assertIn("GitCommandError: app/[locale]/page.tsx", workflows._step_error(error))
        self.assertEqual(workflows._step_error(RuntimeError("x")), "RuntimeError: x")

    def test_a_paused_run_a_live_task_or_a_change_is_not_stalled(self):
        run = type("R", (), {"run_id": "proj:REQ-900:r1"})()
        cfg, state = solver.settings(), {}
        quiet = {"workflow_id": "bt:proj:REQ-900:r1", "workflow_status": "PENDING",
                 "summary": {"status": "running", "tasks": {"T1": "completed"}}, "tasks": {}}
        later = 46 * 60.0
        self.assertEqual(solver.stalled_triggers(run, quiet, state, 0.0, cfg), [])
        self.assertEqual(solver.stalled_triggers(run, quiet, state, later, cfg)[0]["kind"], "stalled")
        paused = {**quiet, "summary": {"status": "paused", "tasks": {"T1": "completed"}}}
        self.assertEqual(solver.stalled_triggers(run, paused, {}, later, cfg), [])
        live = {**quiet, "tasks": {"T2": {"workflow_status": "PENDING", "state": {"state": "running"}}}}
        self.assertEqual(solver.stalled_triggers(run, live, {}, later, cfg), [])
        ended = {**quiet, "workflow_status": "SUCCESS"}
        self.assertEqual(solver.stalled_triggers(run, ended, {}, later, cfg), [])
        moved = {**quiet, "summary": {"status": "running", "tasks": {"T1": "completed", "T2": "completed"}}}
        self.assertEqual(solver.stalled_triggers(run, moved, state, later, cfg), [])      # a change restarts the clock

    def test_a_task_that_used_its_sessions_and_a_stale_trigger_stay_with_the_owner(self):
        state = {"tasks": {"T7.4": 3}}
        solver.save(self.rdirs["REQ-900"], state)
        self.solver().run_pass([self.open_decision()])
        self.assertEqual(self.terminal.started, [])
        self.assertEqual(list(self.state()["triggers"].values())[0]["status"], "limit")
        self.assertTrue(self.notified)
        solver.save(self.rdirs["REQ-900"], {})
        moved = self.open_decision()
        self.open_decision(request="T7.4:d2", round_no=3)                     # someone answered; a new round opened
        self.solver().run_pass([moved])
        self.assertEqual(self.terminal.started, [])
        self.assertEqual(self.state()["triggers"][moved["key"]]["status"], "stale")

    def test_an_unattended_composition_resolution_request_goes_to_the_run_whose_task_conflicts(self):
        """2026-10-29 19:55: three requests sat open for up to 3 h while T95 failed INTEGRATION_CONFLICT on every retry."""
        import os
        from bt_durable import resolutions
        folder = self.root / ".state" / "durable" / "composition" / "resolutions"
        folder.mkdir(parents=True)
        request = {"path": "src/lib/cuentas/dependientes.ts", "blobs": {"base": "b0", "ours": "b1", "theirs": "b2"},
                   "commits": {"base": "c" * 40, "ours": "d" * 40, "theirs": "e" * 40}}
        (folder / "k1.json").write_text(json.dumps(request))
        (folder / "k1.diff3").write_text("<<<<<<< ours\nA\n||||||| base\n=======\nA\nB\n>>>>>>> theirs\n")
        self.open_decision("REQ-901")                                        # another run with an unrelated decision
        run_id = "proj:REQ-900:r1"
        self.open_decision()
        failure = self.client.runs[run_id]["tasks"]["T7.4"]["decision"]["failure"]
        failure["summary"] = "INTEGRATION_CONFLICT: src/lib/cuentas/dependientes.ts (line of SP-8)"
        self.client.runs["proj:REQ-901:r1"]["tasks"]["T7.4"]["decision"]["failure"]["summary"] = "checks failed"
        self.solver().run_pass([])
        self.assertEqual(self.terminal.started, [])                          # younger than resolution_after_seconds
        old = self.clock[0] - 300
        os.utime(folder / "k1.json", (old, old))
        self.solver().run_pass([])
        self.assertEqual(self.session()["kind"], "resolution")
        brief = (Path(self.session()["dir"]) / "BRIEF.md").read_text()
        for text in ("src/lib/cuentas/dependientes.ts", "ours `b1`", str(folder / "k1.resolved"), "||||||| base",
                     "never drop either side's change", "`retry`"):
            self.assertIn(text, brief)
        self.assertEqual(self.state("REQ-901").get("triggers", {}), {})
        statuses = {"a": {"tasks": {"T1": {"decision": {"failure": {"code": "INTEGRATION_CONFLICT"}}}}},
                    "b": {"tasks": {"T2": {"decision": {"failure": {"code": "INTEGRATION_CONFLICT"}}}}}}
        self.assertIsNone(resolutions.target({"path": "x.ts", "commits": {}}, statuses))   # ambiguous: it waits
        self.assertEqual(resolutions.target({"path": "x.ts", "commits": {}}, {"a": statuses["a"]}), ("a", "T1"))
        (folder / "k1.resolved").write_text("A\nB\n")
        self.assertEqual(resolutions.open_requests(folder, self.clock[0], 120), [])

    def test_a_rejected_gates_conflict_goes_to_its_run_without_any_decision(self):
        """pictures REQ-021 r25, 2026-10-30 04:38 (D-193): the composer rejected CG-9 on Taller3D.tsx; the request named
        no decision, so the trigger never found its run and the requests sat open."""
        import os
        from bt_durable import resolutions
        state_dir = self.root / ".state" / "durable"
        folder = state_dir / "composition" / "resolutions"
        folder.mkdir(parents=True)
        for key, path in (("k9", "src/components/tres-d/Taller3D.tsx"), ("old", "src/app/3d/page.tsx")):
            (folder / f"{key}.json").write_text(json.dumps({"path": path, "blobs": {}, "commits": {}}))
            (folder / f"{key}.diff3").write_text("<<<<<<< ours\nA\n=======\nB\n>>>>>>> theirs\n")
            old = self.clock[0] - 300
            os.utime(folder / f"{key}.json", (old, old))
        run_id = "proj:REQ-900:r1"
        self.open_decision("REQ-901")                                        # another run, nothing to do with it
        self.client.runs["proj:REQ-901:r1"]["tasks"]["T7.4"]["decision"]["failure"].update(code="CHECKS_FAILED",
                                                                                         summary="checks failed",
                                                                                         evidence=[])
        self.client.runs[run_id] = {"run_id": run_id, "workflow_id": f"bt:{run_id}", "workflow_status": "PENDING",
                                    "summary": {"status": "running", "gates": {"rejected": {"CG-9": "git_text_conflict"}}},
                                    "tasks": {}}
        rows = [{"event": "gate_composed", "run_id": run_id, "gate": "CG-9", "state": "rejected",
                 "conflicts": {"SP-4": ["src/components/tres-d/Taller3D.tsx"]}},
                {"event": "gate_composed", "run_id": "proj:REQ-777:r1", "gate": "CG-9", "state": "rejected",
                 "conflicts": {"SP-1": ["src/app/3d/page.tsx"]}}]                # a run no longer in the statuses
        (state_dir / "telemetry.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        self.assertEqual(resolutions.rejected_paths(state_dir / "telemetry.jsonl", self.client.runs),
                         {run_id: {"src/components/tres-d/Taller3D.tsx": "CG-9"}})
        self.solver().run_pass([])
        self.assertEqual(self.session()["kind"], "resolution")
        self.assertEqual(self.session()["task"], "CG-9")
        triggers = self.state()["triggers"]
        self.assertEqual([t["resolution"]["path"] for t in triggers.values()], ["src/components/tres-d/Taller3D.tsx"])
        self.assertEqual(self.state("REQ-901").get("triggers", {}), {})

    def test_it_is_off_with_its_switch_or_without_the_healing_before_it(self):
        for key in ("solver.enabled", "healing.model_diagnosis"):
            with self.subTest(key=key), patch.dict(FLAGS, {key: False}):
                self.assertEqual(self.solver().run_pass([self.open_decision()]), [])
        self.assertEqual(self.terminal.started, [])

    def test_the_pass_reads_each_status_once_and_the_answer_says_who(self):
        calls = []

        class Counting:
            def status(self, run):
                calls.append(run.run_id)
                return {}

            def answer(self, *args, **kwargs):
                return "wf"
        cached = _PassStatus(Counting())
        run = type("R", (), {"run_id": "r"})()
        cached.status(run)
        cached.status(run)
        self.assertEqual((calls, cached.answer()), (["r"], "wf"))
        sent = []

        class Answering:
            def answer(self, run, task, answer, round_no=None):
                sent.append((task, answer.by, round_no))
                return "wf"

            def close(self):
                pass
        with patch.object(cli, "_client", return_value=Answering()), patch.object(cli, "_run_of", return_value=None):
            cli.main(["answer", "proj", "REQ-900", "T7.4", "T7.4:d1@k2", "retry", "--by", "solver"])
        self.assertEqual(sent, [("T7.4", "solver", 2)])


if __name__ == "__main__":
    unittest.main()
