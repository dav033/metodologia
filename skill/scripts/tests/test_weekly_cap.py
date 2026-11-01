"""D-279, the owner's weekly cap (2026-10-31): «cuando una cuenta tenga 90% de la cuota semanal no se tenga en cuenta ni
se use más en metodologia sin importar que una tarea tenga dicha cuenta como la propietaria, se debe rutear».

An account at or above `routing.weekly_cap_percent` of its seven-day window is never picked: not by the router, not by a
pinned run, a delegation, a role session's override or the durable engine; work moves to the next eligible account and
says so; with every account capped the existing "all accounts spent" path runs, naming the cap. Unknown usage never
excludes. No provider is contacted: every reading is a fixture."""
from __future__ import annotations

import json
import logging
import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_agents import AgentTests

import bt_agent_terminal as terminal
import bt_agents
import bt_config
import bt_subscriptions
import bt_weekly_cap as cap
from bt_contracts.execution import Route, RunRef

NOW = time.time()


def row(weekly: float, *, reset: float | None = None, status: str = "ok", age: float = 0, short: float = 10,
        provider: str = "claude") -> dict:
    return {"provider": provider, "status": status, "observed_at": NOW - age, "windows": {
        "five_hour": {"used_percent": short, "resets_at": NOW + 3600, "window_minutes": 300},
        "seven_day": {"used_percent": weekly, "resets_at": NOW + 2 * 86400 if reset is None else reset,
                      "window_minutes": 10080}}}


def configured(value):
    real = bt_config.get
    return patch.object(bt_config, "get", side_effect=lambda key, default=None:
                        value if key == "routing.weekly_cap_percent" else real(key, default))


class Predicate(unittest.TestCase):
    def test_at_or_above_the_threshold_is_capped_and_below_is_not(self):
        self.assertTrue(cap.check(row(90), NOW, 90).capped)
        self.assertTrue(cap.check(row(97.5), NOW, 90).capped)
        self.assertEqual(cap.check(row(89.9), NOW, 90).state, "under")
        found = cap.check(row(93), NOW, 90)
        self.assertEqual((found.used_percent, found.resets_at), (93, NOW + 2 * 86400))

    def test_unknown_or_stale_data_is_never_capped(self):
        cases = {"no_sample": None, "no_weekly_window": {"status": "ok", "windows": {}},
                 "invalid_weekly_window": row("x"),                                            # type: ignore[arg-type]
                 "weekly_window_reset_since_reading": row(99, reset=NOW - 1),
                 "stale_reading_without_reset": {**row(99), "observed_at": NOW - 3 * 3600}}
        cases["stale_reading_without_reset"]["windows"]["seven_day"]["resets_at"] = None
        for why, sample in cases.items():
            found = cap.check(sample, NOW, 90)
            self.assertEqual((found.state, found.why), ("unknown", why), why)
            self.assertFalse(found.capped)

    def test_a_reading_of_the_current_week_counts_even_when_the_last_poll_failed(self):
        """Within one seven-day window usage only grows: an older reading of the same window is a lower bound."""
        self.assertTrue(cap.check(row(95, status="http_429", age=20 * 3600), NOW, 90).capped)
        fresh_no_reset = row(95)
        fresh_no_reset["windows"]["seven_day"]["resets_at"] = None
        self.assertTrue(cap.check(fresh_no_reset, NOW, 90).capped)

    def test_the_threshold_comes_from_the_configuration(self):
        self.assertEqual(cap.threshold(), 90.0)
        for value, expected in ((95, 95.0), (75, 75.0), (0, 90.0), (-3, 90.0), (True, 90.0), ("x", 90.0)):
            with configured(value):
                self.assertEqual(cap.threshold(), expected, value)
        with configured(95):
            self.assertFalse(cap.check(row(93), NOW).capped)
        with configured(101):                                                  # never reachable: the cap is off
            self.assertFalse(cap.check(row(100), NOW).capped)

    def test_unknown_usage_is_logged_once_per_account(self):
        cap._noted.clear()
        with self.assertLogs("bt_weekly_cap", level=logging.INFO) as logs:
            cap.for_account({}, "claude:test", NOW)
            cap.for_account({}, "claude:test", NOW)
        self.assertEqual(len(logs.records), 1)
        self.assertIn("not excluded", logs.output[0])

    def test_the_owners_line(self):
        self.assertEqual(cap.line("claude-luis", cap.check(row(93), NOW, 90), "codex-luis"),
                         "claude-luis excluida: 93 % de la cuota semanal; se ruteó a codex-luis")


class Samples(AgentTests):
    """The real router (`bt_agents.candidates` / `route`, plain and role-ranked) over stored samples."""

    def setUp(self):
        super().setUp()
        self.samples: dict = {}
        cap._recorded.clear()
        for target, name, value in ((bt_subscriptions, "load", lambda *a: self.samples),
                                    (bt_subscriptions, "ensure_fresh", lambda *a, **k: None)):
            patcher = patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        which = patch.object(bt_agents.shutil, "which", side_effect=lambda name: "/bin/" + name)
        which.start()
        self.addCleanup(which.stop)

    def use(self, profile: str, weekly: float, **kw):
        self.samples[bt_agents.account_key(profile)] = row(weekly, **kw)


class Router(Samples):
    def test_a_capped_account_is_never_a_candidate(self):
        self.use("claude", 93)
        self.use("codex-named", 40)
        routes, _ = bt_agents.candidates("personal-project", ["claude", "codex-named"], 0)
        self.assertEqual([r["profile"] for r in routes], ["codex-named"])
        self.assertEqual([c["profile"] for c in routes.weekly_capped], ["claude"])
        role_routes, _ = bt_agents.candidates("personal-project", ["claude", "codex-named"], 0, "plan", role="planner")
        self.assertEqual({r["profile"] for r in role_routes}, {"codex-named"})

    def test_the_route_says_where_the_work_went(self):
        self.use("claude", 93)
        self.use("codex-named", 10)
        chosen = bt_agents.route("personal-project", {"pool": ["claude", "codex-named"]}, 0)
        self.assertEqual(chosen["profile"], "codex-named")
        self.assertIn("claude excluida: 93 % de la cuota semanal; se ruteó a codex-named", chosen["why"])
        self.assertEqual(chosen["decision"]["weekly_cap"][0]["profile"], "claude")
        events = (self.state / "events").glob("weekly-cap-*.jsonl")
        lines = [json.loads(line) for path in events for line in path.read_text().splitlines()]
        self.assertEqual([(e["profile"], e["rerouted_to"]) for e in lines], [("claude", "codex-named")])

    def test_a_quota_pressure_that_would_prefer_the_capped_account_does_not_matter(self):
        self.use("claude", 90, short=0)
        self.use("codex-named", 50, short=80)
        chosen = bt_agents.route("personal-project", {"pool": ["claude", "codex-named"]}, 0, role="runner")
        self.assertEqual(chosen["agent"], "codex")

    def test_every_account_capped_is_the_spent_pool_path_naming_the_cap(self):
        self.use("claude", 95, reset=NOW + 5000)
        self.use("codex-named", 91, reset=NOW + 9000)
        with self.assertRaises(bt_agents.NoRoute) as raised:
            bt_agents.route("personal-project", {"pool": ["claude", "codex-named"]}, 0)
        self.assertAlmostEqual(raised.exception.until, NOW + 5000, delta=1)
        self.assertIn("weekly cap", raised.exception.reason)
        self.assertIn("claude 95%", raised.exception.reason)

    def test_unknown_weekly_usage_keeps_the_account(self):
        self.use("claude", 99, reset=NOW - 60)                                 # its week already reset
        self.use("codex-named", 40)
        routes, _ = bt_agents.candidates("personal-project", ["claude", "codex-named"], 0)
        self.assertEqual({r["profile"] for r in routes}, {"claude", "codex-named"})

    def test_a_lagging_stored_sample_is_overruled_by_the_newer_live_reading(self):
        """2026-10-31: codex-luis's hourly poll kept failing at 84 % while globalusage read it live at 90 %."""
        self.use("claude", 40)
        self.use("codex-named", 84, status="app_server_unavailable", age=5 * 3600)
        (self.state / "globalusage-cache.json").write_text(json.dumps(
            {"at": NOW, "rows": [{**row(90, provider="codex"), "profile": "codex-named"}]}))
        routes, _ = bt_agents.candidates("personal-project", ["claude", "codex-named"], 0)
        self.assertEqual([r["profile"] for r in routes], ["claude"])
        self.assertEqual(routes.weekly_capped[0]["used_percent"], 90)

    def test_the_threshold_is_configurable(self):
        self.use("claude", 93)
        self.use("codex-named", 40)
        with configured(95):
            routes, _ = bt_agents.candidates("personal-project", ["claude", "codex-named"], 0)
        self.assertEqual({r["profile"] for r in routes}, {"claude", "codex-named"})
        with configured(80):
            routes, _ = bt_agents.candidates("personal-project", ["claude", "codex-named"], 0)
        self.assertEqual({r["profile"] for r in routes}, {"codex-named"})


class Ownership(Samples):
    """Work pinned to an account (a run without a pool, a delegation's --profile, a continuing attempt) is rerouted."""

    def test_a_run_pinned_to_a_capped_account_is_rerouted(self):
        self.use("claude", 92)
        self.use("codex-named", 10)
        chosen = bt_agents.route("personal-project", {"agent": "claude", "profile": "claude"}, 0)
        self.assertEqual(chosen["profile"], "codex-named")
        self.assertEqual(chosen["decision"]["kind"], "fallback")
        self.assertIn("claude excluida: 92 %", chosen["why"])

    def test_a_pinned_run_with_no_eligible_account_waits_like_a_spent_pool(self):
        self.use("claude", 92, reset=NOW + 4000)
        self.use("codex-named", 96, reset=NOW + 8000)
        self.use("codex", 99, reset=NOW + 9000)                                # the default Codex account too
        with self.assertRaises(bt_agents.NoRoute) as raised:
            bt_agents.route("personal-project", {"agent": "claude", "profile": "claude"}, 0)
        self.assertIn("weekly cap", raised.exception.reason)
        self.assertAlmostEqual(raised.exception.until, NOW + 4000, delta=1)

    def test_a_pin_under_the_cap_keeps_its_account(self):
        self.use("claude", 70)
        chosen = bt_agents.route("personal-project", {"agent": "claude", "profile": "claude"}, 0)
        self.assertEqual((chosen["agent"], chosen["why"]), ("claude", "fixed (no pool)"))

    def test_a_delegation_continuing_on_a_capped_account_moves_before_its_next_attempt(self):
        self.use("claude", 94)
        self.use("codex-named", 10)
        order = {"id": "D-1", "project": "personal-project", "profile": "claude", "agent": "claude", "model": "sonnet",
                 "effort": "medium", "kind": "implement", "tier": 0, "auto": False, "role": "implementer"}
        self.assertEqual(cap.reroute_order(order), "")
        self.assertEqual((order["profile"], order["agent"], order["auto"]), ("codex-named", "codex", True))
        self.assertIn("claude excluida: 94 %", order["routed"])
        self.use("codex-named", 99)
        self.use("codex", 99)
        order.update(profile="claude", agent="claude")
        self.assertIn("weekly cap", cap.reroute_order(order))                  # nothing left: like a spent pool

    def test_a_session_continuing_its_last_route_is_rerouted_by_session_route(self):
        import bt_runsession
        self.use("claude", 91)
        self.use("codex-named", 20)
        state = {"pool": ["claude", "codex-named"], "req": "R", "sessions": 3}
        task = {"id": "T1", "kind": "implement", "last_route": {"agent": "claude", "profile": "claude", "result": "ok"}}
        chosen = bt_runsession.session_route("personal-project", state, task, [task])
        self.assertEqual(chosen["profile"], "codex-named")

    def test_the_configured_diagnosis_profile_gives_way_to_another_account_of_its_provider(self):
        """`diagnosis.profile` (block diagnosis, attempt analyst, manual reviewer, recovery Planner) is a pin too; its
        model belongs to its provider, so only an account of that provider may take the call."""
        self.use("claude", 70)
        self.assertEqual(cap.reroute_profile("work-project", "claude", "diagnosis"), "claude")
        self.use("claude", 93)
        self.use("claude-work", 20)
        self.use("codex-named", 5)
        self.assertEqual(cap.reroute_profile("work-project", "claude", "diagnosis"), "claude-work")
        with self.assertRaises(bt_agents.bt_profiles.ProfileError) as raised:   # claude-work is work-only; Codex is
            cap.reroute_profile("personal-project", "claude", "diagnosis")      # another provider: nothing left
        self.assertIn("weekly cap", str(raised.exception))

    def test_the_block_diagnosis_runs_on_the_account_the_cap_left(self):
        import tempfile

        import bt_block_agent
        self.use("claude", 93)
        self.use("claude-work", 20)
        seen = {}

        def runner(argv, **kw):
            seen["env"] = kw.get("env") or {}
            raise OSError("stop after the account was chosen")

        config = {"profile": "claude", "model": "haiku", "effort": "", "timeout_seconds": 5}
        with tempfile.TemporaryDirectory() as rdir:
            result = bt_block_agent.diagnose("work-project", Path(rdir), {"id": "Q1", "options": []}, "evidence",
                                             runner=runner, config=config)
        self.assertEqual(result["profile"], "claude-work")
        self.assertEqual(seen["env"].get("CLAUDE_CONFIG_DIR"), str(self.workdir))


class RoleRoute(unittest.TestCase):
    """`role_route` (Planner, Designer, Solucionador): the override pin and the ~/.claude-work fallback give way."""

    def setUp(self):
        cap._recorded.clear()
        self.capped = {"/acc/owner": 93.0, "/acc/luis": 97.0}
        patchers = [patch.object(terminal, "_home_cap", side_effect=self.home_cap),
                    patch.object(terminal, "unattended", return_value=True),
                    patch.object(bt_agents, "pool_for", return_value=["claude-work"]),
                    patch("bt_profiles.load", return_value={
                        "claude-work": {"provider": "claude", "env": {"CLAUDE_CONFIG_DIR": "/acc/work"}},
                        "claude-luis": {"provider": "claude", "env": {"CLAUDE_CONFIG_DIR": "/acc/luis"}}})]
        for patcher in patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

    def home_cap(self, provider, home):
        used = self.capped.get(home)
        return (cap.Cap("capped", used, NOW + 3600) if used is not None else cap.Cap("under", 10.0)), home

    def ranked(self, rows, capped=()):
        routes = cap.Routes(rows)
        routes.weekly_capped = list(capped)
        return patch.object(bt_agents, "candidates", return_value=(routes, None))

    def test_a_capped_override_pin_is_skipped_for_the_ranked_account(self):
        with patch.dict(os.environ, {"BITACORA_PLANNER_CLAUDE_CONFIG_DIR": "/acc/owner"}), \
                self.ranked([{"agent": "claude", "profile": "claude-work", "model": "opus", "effort": "high"}]):
            route = terminal.planner_route("pictures")
        self.assertEqual(route["home"], "/acc/work")
        self.assertIn("/acc/owner excluida: 93 % de la cuota semanal; se ruteó a claude-work", route["weekly_cap"])

    def test_an_override_under_the_cap_still_pins(self):
        self.capped = {}
        with patch.dict(os.environ, {"BITACORA_SOLVER_CLAUDE_CONFIG_DIR": "/acc/owner"}):
            route = terminal.role_route("pictures", "solver", override="BITACORA_SOLVER_CLAUDE_CONFIG_DIR")
        self.assertEqual((route["home"], set(route)), ("/acc/owner", {"provider", "home", "model", "effort"}))

    def test_the_ranking_never_offers_a_capped_account(self):
        luis = {"account": "claude:luis", "profile": "claude-luis", "used_percent": 97.0, "resets_at": NOW + 3600,
                "threshold": 90.0}
        with self.ranked([{"agent": "claude", "profile": "claude-work", "model": "sonnet", "effort": "high"}], [luis]):
            route = terminal.role_route("pictures", "solver")
        self.assertEqual(route["home"], "/acc/work")

    def test_every_account_capped_is_exhausted_with_the_cap_as_reason(self):
        luis = {"account": "claude:luis", "profile": "claude-luis", "used_percent": 97.0, "resets_at": NOW + 3600,
                "threshold": 90.0}
        self.capped["/home/x/.claude-work"] = 95.0
        with patch.dict(os.environ, {"BITACORA_PLANNER_CLAUDE_CONFIG_DIR": "/acc/owner"}), \
                self.ranked([], [luis]), patch.object(terminal.Path, "home", return_value=Path("/home/x")), \
                patch.object(terminal.Path, "is_dir", return_value=True):
            route = terminal.planner_route("pictures")
        self.assertEqual((route["home"], route["exhausted"]), ("", "1"))
        self.assertIn("weekly cap", route["reason"])
        self.assertIn("claude-luis 97%", route["reason"])
        with patch.object(terminal, "agent_state", return_value="absent"), patch.object(terminal, "exists",
                                                                                        return_value=False):
            ok, said = terminal.start_planner(Path("/nonexistent"), "pictures", Path("/nonexistent/REQ-1-x"),
                                              route=route)
        self.assertFalse(ok)
        self.assertIn("weekly cap", said)


class DurableRouter(unittest.TestCase):
    """The durable engine's capacity (`LiveQuota`): a capped account reads as exhausted until its week resets."""

    def setUp(self):
        cap._recorded.clear()
        self.routes = [Route(provider="claude", model="sonnet", profile="claude-luis"),
                       Route(provider="codex", model="gpt-6.1-sol", profile="codex-luis")]
        self.run = RunRef(project="proj", req="REQ-001", revision=1, plan_id="REQ-001", plan_sha256="0" * 64,
                          plan_path=Path("/nonexistent/PLAN.json"))

    def quota(self, luis: float, codex: float):
        from bt_durable.adapters.routes import LiveQuota
        rows = [{**row(luis), "profile": "claude-luis"}, {**row(codex, provider="codex"), "profile": "codex-luis"}]
        return LiveQuota(reader=lambda: rows)

    def test_a_capped_account_is_exhausted_until_its_weekly_reset(self):
        reading = self.quota(92, 10).reading(self.routes[0], NOW)
        self.assertEqual((reading.state, reading.cap, reading.status), ("exhausted", "weekly_cap", "ok"))
        self.assertAlmostEqual(reading.reset_at, NOW + 2 * 86400, delta=1)
        self.assertEqual(self.quota(80, 10).reading(self.routes[0], NOW).state, "available")

    def test_the_static_router_skips_it_and_waits_naming_the_cap_when_all_are_capped(self):
        from types import SimpleNamespace

        from bt_durable.adapters.routes import StaticRouter
        task = SimpleNamespace(id="T1")
        chosen = StaticRouter(self.routes, self.quota(92, 10)).decide(self.run, task, exclude=(), now=NOW)
        self.assertEqual((chosen.kind, chosen.route.profile), ("run", "codex-luis"))
        waiting = StaticRouter(self.routes, self.quota(92, 99)).decide(self.run, task, exclude=(), now=NOW)
        self.assertEqual(waiting.kind, "wait")
        self.assertIn("weekly cap", waiting.reason)


class LongLivedSolver(unittest.TestCase):
    """A running Solucionador whose account crosses the cap moves at its next safe boundary, never mid-integration."""

    def setUp(self):
        import tempfile

        from test_durable_solver import FLAGS, Client, SolverTests, Terminal
        cap._recorded.clear()
        self.base = Path(tempfile.mkdtemp(prefix="bt-weekly-cap-"))
        self.root = self.base / "root"
        self.clock = [1_000_000.0]
        self.terminal, self.client = Terminal(), Client()
        self.activity, self.routes, self.integrating = [], [], {}
        self.route = {"provider": "claude", "home": "/acc/luis", "model": "sonnet", "effort": "high"}
        self.capped_homes: set[str] = set()
        self.make_run = SolverTests.make_run.__get__(self)
        self.open_decision = SolverTests.open_decision.__get__(self)
        self.rdirs = {"REQ-900": self.make_run("REQ-900")}
        patcher = patch("bt_config.get", side_effect=lambda key, default=None: FLAGS.get(key, default))
        patcher.start()
        self.addCleanup(patcher.stop)

    def route_for(self, project, avoid):
        self.routes.append(avoid)
        return self.route

    def weekly(self, provider, home):
        return (cap.Cap("capped", 92.0, NOW + 3600) if home in self.capped_homes else cap.Cap("under", 10.0)), home

    def solver(self):
        from bt_durable import solver
        return solver.Solver(self.root, self.client, terminal=self.terminal, route_for=self.route_for,
                             notify=lambda title, text: None, record=lambda rdir, text: self.activity.append(text),
                             now=lambda: self.clock[0], work=self.base / "work",
                             integrating=lambda sid: list(self.integrating.get(sid, [])), weekly_cap=self.weekly)

    def session(self):
        from bt_durable import solver
        state = solver.load(self.rdirs["REQ-900"])
        return next(s for s in state["sessions"] if s["id"] == state.get("active", state["sessions"][-1]["id"]))

    def test_a_session_on_a_capped_account_moves_after_its_integration(self):
        self.solver().run_pass([self.open_decision()])
        self.assertEqual(self.terminal.started[0]["env"]["CLAUDE_CONFIG_DIR"], "/acc/luis")
        self.capped_homes = {"/acc/luis"}
        self.integrating = {self.session()["id"]: [4242]}
        self.solver().run_pass([])
        self.assertEqual((self.terminal.killed, len(self.terminal.started)), ([], 1))   # never mid-integration
        self.integrating = {}
        self.route = {"provider": "claude", "home": "/acc/work", "model": "sonnet", "effort": "high"}
        self.solver().run_pass([])
        self.assertEqual(len(self.terminal.started), 2)
        self.assertEqual(self.terminal.started[-1]["env"]["CLAUDE_CONFIG_DIR"], "/acc/work")
        self.assertEqual((self.session()["cap_moves"], self.session()["restarts"]), (1, 0))
        self.assertTrue(any("/acc/luis excluida: 92 % de la cuota semanal; se ruteó a /acc/work" in a
                            for a in self.activity))

    def test_with_every_account_capped_it_stays_and_says_so_once(self):
        self.solver().run_pass([self.open_decision()])
        self.capped_homes = {"/acc/luis"}
        self.route = {"provider": "claude", "home": "", "model": "sonnet", "effort": "high", "exhausted": "1",
                      "reason": "weekly cap: claude-luis 92% at or above 90% of the weekly quota (D-279)"}
        self.solver().run_pass([])
        self.solver().run_pass([])
        self.assertEqual((self.terminal.killed, len(self.terminal.started)), ([], 1))
        self.assertEqual(sum("ninguna otra cuenta disponible" in a for a in self.activity), 1)

    def test_a_new_session_never_starts_on_a_capped_account(self):
        self.route = {"provider": "claude", "home": "", "model": "sonnet", "effort": "high", "exhausted": "1",
                      "reason": "weekly cap: claude-luis 92% at or above 90% of the weekly quota (D-279)"}
        said = self.solver().run_pass([self.open_decision()])
        self.assertEqual(self.terminal.started, [])
        self.assertTrue(any("weekly cap" in line for line in said))


class LongLivedPlanner(unittest.TestCase):
    """A Planner between turns on a capped account moves (conversation and notice) like one whose account ran out."""

    def setUp(self):
        import tempfile

        import bt_planner_notices as notices
        cap._recorded.clear()
        self.notices = notices
        self.rdir = Path(tempfile.mkdtemp(prefix="bt-weekly-planner-")) / "proj" / "requirements" / "REQ-021-x"
        self.rdir.mkdir(parents=True)
        self.started = []
        self.route = {"provider": "claude", "home": "/acc/work", "model": "opus", "effort": "high"}
        for target, name, value in ((notices, "_rdir", lambda project, req: self.rdir),
                                    (terminal, "_record", lambda rdir: {"provider": "claude", "config_dir": "/acc/luis"}),
                                    (terminal, "_home_cap", lambda provider, home: (
                                        cap.Cap("capped", 94.0, NOW + 3600) if home == "/acc/luis" else
                                        cap.Cap("under", 5.0), "claude-luis" if home == "/acc/luis" else home)),
                                    (terminal, "planner_route", lambda project, avoid: self.route),
                                    (terminal, "kill", lambda name: True),
                                    (terminal, "start_planner", self.start)):
            patcher = patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def start(self, root, project, rdir, *, avoid="", route=None, message="", fresh=False):
        self.started.append((avoid, route, message))
        return True, "Planner abierto."

    def test_it_moves_with_the_notice_to_the_next_eligible_account(self):
        state, said = self.notices.leave_capped("proj", "REQ-021", "hola")
        self.assertEqual(state, "moved")
        self.assertEqual(self.started, [("/acc/luis", self.route, "hola")])
        self.assertIn("claude-luis excluida: 94 % de la cuota semanal; se ruteó a /acc/work", said)

    def test_with_no_other_account_it_stays(self):
        self.route = {"provider": "claude", "home": "", "exhausted": "1", "reason": "weekly cap: ..."}
        with patch.object(terminal, "_save_record"):
            self.assertIsNone(self.notices.leave_capped("proj", "REQ-021", "hola"))
        self.assertEqual(self.started, [])


class ScheduledRouter(unittest.TestCase):
    def test_the_m2_usage_facts_call_a_capped_account_exhausted(self):
        import bt_scheduler_decision_adapter as adapter
        usage = {"claude:x": row(93)}
        facts = adapter._usage_facts("claude", "claude:x", "sonnet", usage, NOW)
        self.assertEqual((facts[0], facts[-1]), ("exhausted", "capacity_exhausted"))
        self.assertEqual(adapter._usage_facts("claude", "claude:x", "sonnet", {"claude:x": row(50)}, NOW)[0],
                         "available")


if __name__ == "__main__":
    unittest.main()
