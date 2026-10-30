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
