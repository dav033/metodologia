"""The subplan control block on the Plan tab: flow, what waits for the owner, blockers, work in progress, news and
decisions (bt_subplan_status + bt_page_subplan_control), the subplan list badges and the subplan-scoped feed."""
from __future__ import annotations

import json
import unittest
from unittest.mock import patch

import test_design_drafts as base
import test_planning_flow as fixtures

import bt_design_drafts as drafts
import bt_page_planning
import bt_planning_activity as activity
import bt_planning_flow as flow
import bt_rounds
import bt_subplan_status as status_model
import bt_verification as verification


class ControlTests(unittest.TestCase):
    setUp = base.DraftTests.setUp
    write_plan = base.DraftTests.write_plan
    create = base.DraftTests.create
    finish = base.DraftTests.finish

    def spec(self, status: str) -> None:
        (self.rdir / "SPEC.md").write_text(fixtures.SPEC.format(status=status), encoding="utf-8")

    def page(self, **q) -> str:
        return bt_page_planning.fragment("demo", "REQ-001", self.rdir, "draft", "tok",
                                         bt_page_planning.options(self.rdir, {"lang": "en", **q}))

    def status(self, sid: str) -> dict:
        subplans = drafts.subplans(self.rdir)
        rows = {row["ref"]: row for row in drafts.rows(self.rdir)}
        ctx = {"project": "demo", "rid": "REQ-001", "rdir": self.rdir, "status": "draft", "token": "tok",
               "opts": bt_page_planning.options(self.rdir, {"lang": "en", "sp": sid}), "subplans": subplans,
               "rows": rows, "flow": flow.state(self.rdir, subplans, rows)}
        return status_model.statuses(ctx)[sid]

    def started(self, plan: dict = fixtures.PLAN) -> None:
        self.write_plan(plan)
        flow.start(self.rdir)
        flow.confirm_outline("demo", self.rdir)

    @staticmethod
    def steps(st: dict) -> dict:
        return {s["key"]: s["state"] for s in st["steps"]}

    def test_a_subplan_without_tasks_is_being_defined_and_its_design_waits(self):
        self.spec("available")
        self.started(fixtures.SKELETON)
        st = self.status("SP-2")
        self.assertEqual((st["current"], self.steps(st)["design"]), ("define", "todo"))
        self.assertIn({"who": "Planner", "text": "Todavía no tiene tareas"}, st["blockers"])
        self.assertEqual(st["you"], [])
        self.assertEqual(self.steps(self.status("SP-1"))["design"], "skip")  # no interface, no design step
        self.assertIn('<li class="na"><span class="sc-dot" aria-hidden="true"></span>Diseñar', self.page(sp="SP-1"))

    def test_open_round_questions_reach_the_owner_and_answers_become_decisions(self):
        self.spec("available")
        self.started()
        f = bt_rounds.new_round(self.rdir, {"title": "Checkout", "questions": [
            {"text": "SP-2: ¿Qué pasarela de pago?", "options": [{"key": "a", "label": "Stripe"}, {"key": "b", "label": "Otra"}]},
            {"text": "SP-1: ¿Dónde se guardan los pedidos?"}]})
        you = self.status("SP-2")["you"]
        self.assertIn({"kind": "round", "text": "Responder 1 pregunta de la ronda 1", "action": "Responder", "view": "asks"},
                      you)
        bt_rounds.answer_round(f, {"q1": {"choice": "a", "note": "en pesos"}, "q2": {"text": "Postgres"}}, "web")
        st = self.status("SP-2")
        self.assertFalse(any(i["kind"] == "round" for i in st["you"]))
        self.assertIn("Ronda 1: ¿Qué pasarela de pago? → a) Stripe · nota: en pesos", [d["text"] for d in st["decisions"]])
        self.assertNotIn("Postgres", json.dumps(st["decisions"]))  # SP-1's answer stays in SP-1

    def test_the_designer_at_work_and_a_design_to_choose(self):
        self.spec("available")
        self.started()
        st = self.status("SP-2")                # the outline confirmation started SP-2's Designer (it has tasks)
        self.assertEqual([w["who"] for w in st["working"]], ["Designer"])
        with drafts._locked(self.rdir) as data:
            data["drafts"]["checkout@v1"].update(status="choosing", phase="explore", chosen=None, directions=[
                {"id": "a", "status": "ready", "name": "Calm", "revision": 1},
                {"id": "b", "status": "ready", "name": "Dense", "revision": 1}])
        st = self.status("SP-2")
        self.assertEqual(st["working"], [])
        self.assertIn("Elegir una de las 2 direcciones de diseño", [i["text"] for i in st["you"]])
        self.assertEqual((st["current"], self.steps(st)["design"]), ("design", "now"))
        html = self.page(sp="SP-2")
        self.assertIn('data-k="control-SP-2"', html)
        self.assertIn("Te toca: Elegir una de las 2 direcciones de diseño", html)

    def test_a_ready_subplan_offers_confirmation_then_execution(self):
        self.spec("location given")
        self.started()
        self.finish("D-1")
        st = self.status("SP-2")
        self.assertEqual(st["current"], "confirm")
        self.assertIn("Revisar y confirmar el subplan", [i["text"] for i in st["you"]])
        self.assertIn("planning-confirm", self.page(sp="SP-2"))
        flow.confirm("demo", self.rdir, "SP-2")
        st = self.status("SP-2")
        self.assertEqual((self.steps(st)["confirm"], st["current"]), ("done", "run"))
        self.assertIn("Mandarlo a ejecutar: aprobarlo como etapa", [i["text"] for i in st["you"]])
        self.assertIn("Confirmaste el subplan en la web", [d["text"] for d in st["decisions"]])
        html = self.page(sp="SP-2")
        self.assertIn("stage-run", html)
        self.assertNotIn('class="pp-flow', html)       # the control block replaced the one-line flow bar

    def test_run_decisions_gate_waits_and_versions_to_try_reach_the_owner(self):
        self.spec("location given")
        plan = {**fixtures.PLAN, "composition_gates": [{"id": "CG-1", "task": "T9", "subplans": ["SP-1", "SP-2"]}]}
        self.started(plan)
        self.finish("D-1")
        flow.confirm("demo", self.rdir, "SP-2")
        run = {"milestones": [{"tasks": [
            {"id": "T2", "subplan_id": "SP-2", "state": "completed", "attempts": 1},
            {"id": "T3", "subplan_id": "SP-2", "state": "pending", "after": ["T9"]},
            {"id": "T9", "state": "needs_decision", "title": "Gate"}]}],
            "decisions": [{"task": "T9", "what": "checks failed"}]}
        verified = {"applies": True, "subplans": [{"id": "SP-2", "state": "to_test", "version": 2, "commit": "c0ffee",
                                                   "decision": {}}], "approved": 0, "total": 1,
                    "counts": {k: int(k == "to_test") for k in verification.STATES_ES}}
        with patch("bt_page_planning_run._status", return_value=run), \
                patch("bt_page_planning_flow.stage_info", return_value={"held": ["SP-2"], "revision": 3, "outside": [],
                                                                        "stages": []}), \
                patch("bt_verification.applies", return_value=True), patch("bt_verification.state", return_value=verified):
            st, gate_member = self.status("SP-2"), self.status("SP-1")
            html = self.page(sp="SP-2")
        texts = [i["text"] for i in st["you"]]
        self.assertIn("Decidir cómo sigue T9: checks failed", texts)
        self.assertIn("Probar la versión 2 y aprobarla o rechazarla", texts)
        self.assertIn({"who": "Tú", "text": "T3 espera a T9 (puerta de composición), que necesita tu decisión"}, st["blockers"])
        self.assertIn("Decidir cómo sigue T9: checks failed", [i["text"] for i in gate_member["you"]])  # SP-1 is in the gate
        self.assertEqual(st["tasks"], {"done": 1, "total": 2})
        self.assertIn("?tab=run", html)
        self.assertIn("view=verify", html)

    def test_feed_follows_the_open_subplan_without_translation_noise(self):
        self.spec("available")
        self.started()
        activity.record(self.rdir, "Planner", "Changed the data layer", sp="SP-1")
        activity.record(self.rdir, "Traducción", "Español al día · 3 secciones", kind="translate")
        activity.record(self.rdir, "Planner", "Changed the checkout tasks", sp="SP-2")
        feed = self.page(sp="SP-2").split('data-k="feed"')[1]
        self.assertIn("Lo que cambió en SP-2", feed)
        self.assertIn("Changed the checkout tasks", feed)
        self.assertNotIn("Changed the data layer", feed)
        self.assertNotIn("Español al día", feed)
        whole = self.page(sp="SP-2", feed="all").split('data-k="feed"')[1]
        for text in ("Lo que cambió en la conversación", "Changed the data layer", "Español al día", "Changed the checkout"):
            self.assertIn(text, whole)

    def test_the_list_counts_what_waits_for_the_owner_and_carries_the_newest_change(self):
        self.spec("location given")
        self.started()
        self.finish("D-1")
        activity.record(self.rdir, "Planner", "Changed the checkout tasks", sp="SP-2")
        newest = activity.events(self.rdir, 1)[0]["at"]
        listing = self.page(sp="SP-1").split('data-k="list"')[1].split('class="pp-detail"')[0]
        self.assertIn('class="sc-badge"', listing)
        self.assertIn(f'data-sc-latest="{newest}" data-sc-sp="SP-2"', listing)
        news = self.page(sp="SP-2").split('data-k="control-SP-2"')[1]
        self.assertIn(f'data-at="{newest}"', news)
        self.assertIn("Changed the checkout tasks", news)


if __name__ == "__main__":
    unittest.main()
