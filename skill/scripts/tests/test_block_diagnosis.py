"""Why a run stopped: the rules name the origin and the fix, the agent's answer is checked and cached, the panel shows it."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import bt_block_agent as agent
import bt_block_diagnosis as rules
import bt_page_diagnosis as page
import bt_run_stores
import bt_scheduler_decisions as decisions

OPTIONS = [decisions.RETRY, decisions.RETRY_NOTE, decisions.STOP]


def request(**extra):
    base = {"id": "T16:4", "source": "task", "task": "T16", "attempt": "att-4", "title": "T16 bloqueada",
            "what": "No se pudo comprobar qué proceso produjo el resultado.", "reason": "m5:identity_unverified",
            "options": list(OPTIONS), "recommended": "retry", "error": "", "project": "demo", "req": "REQ-001"}
    return {**base, **extra}


class Plan:
    """ancestors() over a fixed graph: T14a → T14b → T16, T9 → T16."""
    graph = {"T16": {"T14b", "T14a", "T9"}, "T14b": {"T14a"}, "T14a": set(), "T9": set()}

    def ancestors(self, task):
        return self.graph[task]

    def task(self, task):
        return SimpleNamespace(id=task, after=tuple(self.graph.get(task, ())), meta={"title": "go-live kit"},
                               acceptance_criteria=("works",), verification=(
                                   {"type": "command", "value": "DB=x npm test"},
                                   {"type": "command", "value": "npm test | tee out"}))


CLASH = "start rejected: INTEGRATION_CONFLICT: T9+T14a vs T14b for T16: remote/gateway/app.py, remote/gateway/x.py"
REDONE = {"tasks": {"T14a": {"attempts": ["a1", "a2"]}, "T14b": {"attempts": ["b1"]}},
          "attempts": {"a1": {"state": "accepted"}, "a2": {"state": "accepted"}, "b1": {"state": "accepted"}}}


class Rules(unittest.TestCase):
    def test_a_clash_names_the_task_built_on_a_replaced_result_and_offers_to_redo_it(self):
        diagnosis, extra = rules.explain(request(), REDONE, plan=Plan(), failures=[CLASH], req="REQ-027")
        self.assertEqual(diagnosis["kind"], "conflict")
        self.assertEqual(diagnosis["option"], "rework_conflict")
        self.assertIn("remote/gateway/app.py", diagnosis["origin"])
        self.assertEqual(extra[0]["target"], "T14b")
        self.assertIn("rework T14b --only", " ".join(diagnosis["steps"]))

    def test_without_evidence_of_a_redo_the_work_merged_last_is_redone(self):
        _, extra = rules.explain(request(), {"tasks": {}, "attempts": {}}, plan=None, failures=[CLASH])
        self.assertEqual(extra[0]["target"], "T14b")

    def test_known_causes_each_get_their_origin_and_option(self):
        cases = [
            ("fatal: not a git repository (or any parent up to mount point /)", "plan", "retry_with_note"),
            ("npm ERR! EROFS: read-only file system, rmdir 'node_modules/.bin'", "environment", "retry_with_note"),
            ("Error [ERR_MODULE_NOT_FOUND]: Cannot find package '@eslint/eslintrc' imported from /w", "dependency", "retry_with_note"),
            ("Error: SUPABASE_DB_URL is not set", "environment", "retry"),
            ("connect ECONNREFUSED 127.0.0.1:5432", "environment", "retry"),
            ("You've hit your usage limit", "quota", "retry"),
        ]
        for text, kind, option in cases:
            with self.subTest(text=text):
                diagnosis, _ = rules.explain(request(reason="m5:attempts_exhausted"), {}, verify=text)
                self.assertEqual((diagnosis["kind"], diagnosis["option"]), (kind, option))
                self.assertTrue(diagnosis["headline"] and diagnosis["origin"] and diagnosis["steps"])

    def test_the_missing_module_and_variable_are_named(self):
        module, _ = rules.explain(request(), {}, verify="Cannot find package '@eslint/eslintrc' imported from x")
        self.assertIn("@eslint/eslintrc", module["headline"])
        self.assertIn("@eslint/eslintrc", module["note"])
        env, _ = rules.explain(request(), {}, verify="Error: SUPABASE_DB_URL is not set")
        self.assertIn("SUPABASE_DB_URL", env["headline"])
        self.assertIn("verifier-demo.env", " ".join(env["steps"]))

    def test_a_plan_revision_is_offered_when_one_exists(self):
        offered = request(options=[*OPTIONS, decisions.REVISE])
        diagnosis, _ = rules.explain(offered, {}, verify="fatal: not a git repository")
        self.assertEqual(diagnosis["option"], "revise")

    def test_the_same_failure_over_and_over_says_retrying_alone_repeats_it(self):
        diagnosis, _ = rules.explain(request(), {}, verify="AssertionError: 3 != 4", failures=["m6://a", "m6://a", "m6://a"])
        self.assertEqual(diagnosis["option"], "retry_with_note")
        self.assertIn("repetirá", diagnosis["origin"])

    def test_an_unknown_stop_falls_back_to_the_reason_and_suggests_the_agent(self):
        diagnosis, _ = rules.explain(request(you_can=["Mira el run."]), {})
        self.assertEqual(diagnosis["kind"], "unknown")
        self.assertEqual(diagnosis["confidence"], "baja")
        self.assertIn("Pide el diagnóstico del agente.", diagnosis["steps"])

    def test_a_review_with_a_refused_command_points_at_it(self):
        review = request(source="review", options=[decisions.FAIL, decisions.PASS, decisions.STOP],
                         evidence=["npm test → unknown (CHECK_UNSUPPORTED)"])
        diagnosis, _ = rules.explain(review, {}, plan=Plan())
        self.assertEqual((diagnosis["kind"], diagnosis["option"]), ("plan", "review_fail"))
        self.assertIn("npm test | tee out", diagnosis["origin"])
        self.assertNotIn("DB=x npm test", diagnosis["origin"])       # a leading assignment is accepted by M6

    def test_a_review_where_every_criterion_passed_and_only_a_check_is_unmapped_is_approved(self):
        evidence = ["CHECK_UNMAPPED: A verification check does not map exactly to an acceptance criterion.",
                    "criterio PASS: Only user/admin seed credentials succeed", "criterio PASS: APIs reject access",
                    "npm run asesor:test → pass", "npx tsx --test auth.test.ts → pass"]
        review = request(source="review", options=[decisions.FAIL, decisions.PASS, decisions.STOP], evidence=evidence)
        diagnosis, _ = rules.explain(review, {})
        self.assertEqual((diagnosis["option"], diagnosis["confidence"]), ("review_pass", "alta"))
        failing = request(source="review", options=review["options"], evidence=[*evidence, "criterio FAIL: x"])
        self.assertNotEqual(rules.explain(failing, {})[0]["option"], "review_pass")

    def test_an_audit_past_its_rework_limit_offers_to_send_the_named_tasks_back(self):
        failure = "audit gate: 2 open blocking finding(s): F1 (high), F2 (high) | M6 evidence: m6://x"
        audit = request(task="T18", reason="m5:rework_limit")
        diagnosis, extra = rules.explain(audit, {}, failures=[failure], req="REQ-027",
                                         refused={"named": ["T16", "T17"], "why": "limit: T17 was already sent back 2 time(s)"})
        self.assertEqual(diagnosis["option"], "rework_findings")
        self.assertIn("F1 (high), F2 (high)", diagnosis["headline"])
        self.assertEqual(extra[0]["target"], "T16,T17")
        self.assertIn("rework T16,T17 --only", " ".join(diagnosis["steps"]))
        diagnosis, extra = rules.explain(audit, {}, failures=[failure])
        self.assertEqual((diagnosis["option"], extra), ("retry_with_note", []))

    def test_the_bundle_carries_the_task_the_failures_and_the_rule(self):
        diagnosis, _ = rules.explain(request(), REDONE, plan=Plan(), failures=[CLASH])
        text = rules.bundle(request(), plan=Plan(), failures=[CLASH], verify="", rule=diagnosis,
                            answered=[{"request": "T16:3", "option": "retry", "reason": "try"}])
        for needle in ("Project: demo", "go-live kit", "INTEGRATION_CONFLICT", "Rule-based guess", "T16:3 retry",
                       "rework_conflict"):
            self.assertIn(needle, text)


class Agent(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.rdir = Path(self.temp.name)
        self.config = {"profile": "claude", "model": "haiku", "effort": "", "timeout_seconds": 5}
        patcher = patch("bt_profiles.session_env", return_value={})
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_with(self, stdout, code=0):
        seen = {}

        def runner(argv, **kwargs):
            seen["argv"], seen["input"] = argv, kwargs["input"]
            return subprocess.CompletedProcess(argv, code, stdout, "boom" if code else "")
        return agent.diagnose("demo", self.rdir, request(), "EVIDENCE", runner=runner, config=self.config), seen

    def test_a_valid_answer_is_stored_for_the_request_and_shown_as_the_agents(self):
        answer = json.dumps({"headline": "Choca T14b", "origin": "app.py", "kind": "conflict", "steps": ["Rehaz T14b"],
                             "option": "retry", "note": "", "confidence": "alta"})
        result, seen = self.run_with("Aquí va:\n" + answer)
        self.assertEqual(result["state"], "done")
        self.assertEqual(result["label"], rules.KINDS["conflict"][0])
        self.assertIn("EVIDENCE", seen["input"])
        self.assertIn("--disallowedTools", seen["argv"])
        self.assertEqual(agent.cached(self.rdir, "T16:4")["headline"], "Choca T14b")
        self.assertIsNone(agent.cached(self.rdir, "T16:5"))                # a new attempt is a new request

    def test_an_option_that_is_not_offered_falls_back_to_the_recommendation(self):
        answer = json.dumps({"headline": "x", "steps": ["y"], "option": "delete_everything", "kind": "nonsense"})
        result, _ = self.run_with(answer)
        self.assertEqual((result["option"], result["kind"]), ("retry", "unknown"))

    def test_a_broken_answer_or_exit_is_stored_as_a_failure(self):
        self.assertEqual(self.run_with("no json here")[0]["state"], "failed")
        failed = self.run_with("{}", code=3)[0]
        self.assertEqual(failed["state"], "failed")
        self.assertIn("3", failed["error"])

    def test_codex_runs_read_only_with_its_last_message_file(self):
        argv = agent.argv("codex", "codex", "gpt-6-luna", "medium", Path("/tmp/out"))
        for needle in ("--sandbox", "read-only", "--output-last-message", "model_reasoning_effort=medium"):
            self.assertIn(needle, argv)

    def test_spawn_does_not_ask_twice_and_a_dead_marker_expires(self):
        with patch("subprocess.Popen") as popen:
            self.assertTrue(agent.spawn("demo", "REQ-001", self.rdir, "T16:4"))
            self.assertFalse(agent.spawn("demo", "REQ-001", self.rdir, "T16:4"))
        self.assertEqual(popen.call_count, 1)
        self.assertIn("diagnose", popen.call_args[0][0])
        marker = json.loads(agent.path(self.rdir, "T16:4").read_text())
        marker["started"] = 0
        agent.path(self.rdir, "T16:4").write_text(json.dumps(marker))
        self.assertEqual(agent.cached(self.rdir, "T16:4")["state"], "failed")


class Cards(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.rdir = Path(self.temp.name) / "demo" / "requirements" / "REQ-001-x"
        self.rdir.mkdir(parents=True)
        self.doc = {"revision": 1, "tasks": {"T16": {"state": "blocked", "reason": "m5:identity_unverified",
                                                     "attempts": ["att-4"]}, **REDONE["tasks"]},
                    "attempts": {"att-4": {"id": "att-4", "state": "failed", "failure": CLASH}, **REDONE["attempts"]}}
        for target, value in (("_state", lambda rdir: self.doc), ("_newer_revision", lambda rdir, current: False),
                              ("_plan", lambda rdir: Plan())):
            patcher = patch.object(decisions, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(bt_run_stores, "paths", return_value={})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_the_card_of_a_clash_recommends_redoing_the_other_task(self):
        [card] = decisions.open_requests(self.rdir)
        self.assertEqual(card["recommended"], "rework_conflict")
        self.assertEqual([o["id"] for o in card["options"]], ["retry", "retry_with_note", "rework_conflict", "stop"])
        self.assertEqual(card["diagnosis"]["kind"], "conflict")
        self.assertIn("REQ-001", decisions.evidence(self.rdir, card))

    def test_answering_rework_conflict_redoes_the_target_only_and_reopens_the_task(self):
        calls = []
        with patch.object(decisions.ops, "apply", side_effect=lambda *a, **k: calls.append((a[3], a[4], k)) or ["ok"]), \
                patch.object(decisions.ops, "status", return_value={"blocked_tasks": ["T16"]}), \
                patch.object(decisions.ops, "resume", return_value="resumed"):
            decisions.answer("demo", "REQ-001", self.rdir, "T16:1", "rework_conflict")
        self.assertEqual(calls[0][:2], ("rework", "T14b"))
        self.assertTrue(calls[0][2]["only"])
        self.assertEqual(calls[1][:2], ("reopen", "T16"))

    def test_the_watchdog_hands_each_new_request_to_the_agent_once(self):
        asked = []
        decisions.announce("demo", "REQ-001", self.rdir, notify=lambda *a: None, diagnose=asked.append)
        decisions.announce("demo", "REQ-001", self.rdir, notify=lambda *a: None, diagnose=asked.append)
        self.assertEqual([r["id"] for r in asked], ["T16:1"])
        with patch("bt_config.get", return_value=False):
            self.assertIsNone(decisions.auto_diagnoser("demo", "REQ-001", self.rdir))

    def test_the_panel_shows_origin_steps_option_and_the_agent_state(self):
        [card] = decisions.open_requests(self.rdir)
        html = page.html(card)
        for needle in ("Conflicto entre tareas", "De dónde viene", "Cómo solucionarlo", "Rehacer T14b",
                       'data-diagnose="T16:1"', "Error técnico y evidencia"):
            self.assertIn(needle, html)
        card["agent"] = {"state": "running", "model": "haiku"}
        self.assertIn("está leyendo la evidencia", page.html(card))
        card["agent"] = {"state": "done", "model": "haiku", "kind": "code", "label": "Código", "tone": "bad",
                         "headline": "<b>otra</b>", "origin": "o", "steps": ["s"], "option": "retry_with_note",
                         "note": "fix it", "confidence": "media"}
        html = page.html(card)
        self.assertIn("Segunda opinión del agente", html)          # the rule was sure: it stays first
        self.assertIn("&lt;b&gt;otra&lt;/b&gt;", html)
        self.assertEqual(page.note_for(card), "fix it")


if __name__ == "__main__":
    unittest.main()
