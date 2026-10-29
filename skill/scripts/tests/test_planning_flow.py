from __future__ import annotations

import json
import unittest
from unittest.mock import patch

import test_design_drafts as base

import bt_design_drafts as drafts
import bt_page_planning
import bt_planning_flow as flow
import bt_rounds
from bt_core import _front

PLAN = {"milestones": [{"id": "M1", "title": "Shop"}],
        "subplans": [
            {"id": "SP-1", "milestone_id": "M1", "title": "Data layer", "outcome": "Stores orders."},
            {"id": "SP-2", "milestone_id": "M1", "title": "Checkout screen", "outcome": "The buyer pays.",
             "ui": {"contract": "checkout", "version": 1, "design_task": "T2", "visual_review_task": "T3"}}],
        "tasks": [{"id": "T1", "title": "Store", "subplan_id": "SP-1", "kind": "implement",
                   "acceptance_criteria": ["Orders persist."]},
                  {"id": "T2", "title": "Design checkout", "subplan_id": "SP-2", "kind": "design",
                   "acceptance_criteria": ["Contract approved."]},
                  {"id": "T3", "title": "Build checkout", "subplan_id": "SP-2", "kind": "implement", "ui": True,
                   "acceptance_criteria": ["Pay works."]}]}
SKELETON = {"milestones": PLAN["milestones"], "subplans": PLAN["subplans"], "tasks": []}
SPEC = """---
status: ready
---
# Shop

## Inputs

| Item | Subplan | Where | Who | Status |
|---|---|---|---|---|
| Repository path | all | ~/dev/shop | owner | available |
| Stripe test key | SP-2 | env STRIPE_KEY in ~/.config/shop/.env | owner | {status} |

## Pruebas

| Subplan | Dónde | Cómo | Qué debes ver |
|---|---|---|---|
| SP-1 | Local | `npm run dev` | Los pedidos se guardan |
| SP-2 | Local | abre /checkout | El comprador paga |
"""


class FlowTests(unittest.TestCase):
    setUp = base.DraftTests.setUp
    write_plan = base.DraftTests.write_plan
    create = base.DraftTests.create
    finish = base.DraftTests.finish

    def spec(self, status: str) -> None:
        (self.rdir / "SPEC.md").write_text(SPEC.format(status=status), encoding="utf-8")

    def page(self, **q) -> str:
        return bt_page_planning.fragment("demo", "REQ-001", self.rdir, _front(self.rdir / "PLAN.md", "status"), "tok",
                                         bt_page_planning.options(self.rdir, {"lang": "en", **q}))

    def test_render_reuses_the_same_flow_and_design_snapshot(self):
        flow.start(self.rdir)
        with patch.object(flow, "state", wraps=flow.state) as state, patch.object(drafts, "rows", wraps=drafts.rows) as rows:
            self.page(sp="SP-2", view="design")
        self.assertEqual(state.call_count, 1)
        self.assertEqual(rows.call_count, 1)

    def approve(self):
        with patch("bt_scheduler_adapter.plan_compatibility_report", return_value=None), \
                patch("bt_plan_adapter.publishable_problem", return_value=None), \
                patch("bt_plan_adapter.freeze_approved", return_value=None):
            return bt_rounds.plan_decide(self.rdir, True, "", "web")

    def test_requirements_off_the_flow_are_untouched(self):
        self.assertFalse(flow.active(self.rdir))
        self.assertEqual(flow.approval_problems(self.rdir), [])
        self.assertIsNone(flow.design_scope(self.rdir))
        self.assertNotIn('data-k="steps"', self.page())

    def test_interview_then_skeleton_then_subplans(self):
        (self.rdir / "PLAN.json").unlink()
        self.assertTrue(flow.start(self.rdir))
        self.assertFalse(flow.start(self.rdir))
        self.assertEqual(flow.state(self.rdir)["phase"], "interview")
        self.assertIn('data-k="interview"', self.page())
        self.write_plan(SKELETON)
        self.assertEqual(flow.state(self.rdir)["phase"], "outline")
        html = self.page()
        self.assertIn('data-k="outline"', html)
        self.assertIn("Confirmar esqueleto", html)
        self.assertEqual(flow.approval_problems(self.rdir), ["falta confirmar el esqueleto"])

    def test_designer_waits_for_the_skeleton_then_designs_every_subplan_with_tasks(self):
        flow.start(self.rdir)
        drafts.request("demo", self.rdir, ["nope@v1"])  # turn drafts on without starting anything
        self.assertEqual(drafts.sync("demo", self.rdir), [])  # no Designer before the skeleton is confirmed
        # SP-1 (no UI) is the focus; SP-2 already has tasks, so its Designer starts without waiting for its turn
        self.assertIn("El Designer empezó checkout@v1", flow.confirm_outline("demo", self.rdir))
        self.assertEqual(len(self.orders), 1)
        self.assertEqual(drafts.sync("demo", self.rdir), [])  # already drafting: never a second batch for SP-2
        self.assertIn("Ya se está", flow.focus("demo", self.rdir, "SP-1"))
        self.assertEqual(flow.state(self.rdir)["subplans"]["SP-2"]["state"], "pending")

    def test_a_subplan_without_tasks_waits_for_its_focus(self):
        self.write_plan({**SKELETON, "tasks": [t for t in PLAN["tasks"] if t["subplan_id"] == "SP-1"]})
        flow.start(self.rdir)
        self.assertIn("Ahora se define SP-1", flow.confirm_outline("demo", self.rdir))
        self.assertEqual(self.orders, [])
        drafts.request("demo", self.rdir, ["nope@v1"])
        self.assertEqual(drafts.sync("demo", self.rdir), [])  # SP-2 has no tasks and is not in focus
        self.assertIn("El Designer empezó checkout@v1", flow.focus("demo", self.rdir, "SP-2"))
        self.assertEqual(len(self.orders), 1)
        self.assertEqual(flow.state(self.rdir)["subplans"]["SP-2"]["state"], "defining")

    def test_designers_of_different_subplans_work_in_parallel(self):
        profile = {"id": "SP-3", "milestone_id": "M1", "title": "Profile screen", "outcome": "The buyer edits the profile.",
                   "ui": {"contract": "profile", "version": 1, "design_task": "T4", "visual_review_task": "T5"}}
        self.write_plan({**PLAN, "subplans": PLAN["subplans"] + [profile], "tasks": PLAN["tasks"] + [
            {"id": "T4", "title": "Design profile", "subplan_id": "SP-3", "kind": "design",
             "acceptance_criteria": ["Contract approved."]},
            {"id": "T5", "title": "Build profile", "subplan_id": "SP-3", "kind": "implement", "ui": True,
             "acceptance_criteria": ["Profile saves."]}]})
        flow.start(self.rdir)
        self.assertIn("El Designer empezó checkout@v1, profile@v1", flow.confirm_outline("demo", self.rdir))
        self.assertEqual(len(self.orders), 2)
        self.assertEqual({r["ref"]: r["status"] for r in drafts.rows(self.rdir)},
                         {"checkout@v1": "drafting", "profile@v1": "drafting"})
        self.assertEqual(flow.design_scope(self.rdir), {"checkout@v1", "profile@v1"})
        self.assertEqual(drafts.request("demo", self.rdir, ["checkout@v1"], force=True), [])  # one batch per subplan

    def test_confirmation_needs_tasks_criteria_inputs_and_a_ready_design(self):
        self.spec("pending")
        self.write_plan(SKELETON)
        flow.start(self.rdir)
        flow.confirm_outline("demo", self.rdir)
        self.assertIn("todavía no tiene tareas", flow.confirm("demo", self.rdir, "SP-1"))
        self.write_plan(PLAN)
        self.assertIn("SP-1 confirmado. Ahora se define SP-2", flow.confirm("demo", self.rdir, "SP-1"))
        refused = flow.confirm("demo", self.rdir, "SP-2")
        self.assertIn("faltan entradas: Stripe test key", refused)
        self.assertIn("Designer sigue trabajando", refused)
        self.finish("D-1")
        self.spec("location given")
        self.assertIn("listo para aprobar", flow.confirm("demo", self.rdir, "SP-2"))
        self.assertEqual(_front(self.rdir / "PLAN.md", "status"), "review")
        self.assertEqual(flow.state(self.rdir)["phase"], "ready")
        self.assertEqual(self.approve(), "approved")
        self.assertEqual(flow.state(self.rdir)["subplans"]["SP-2"]["state"], "confirmed")  # pinning keeps it

    def test_a_change_after_confirmation_reopens_the_subplan_and_blocks_approval(self):
        self.spec("location given")
        self.write_plan(PLAN)
        flow.start(self.rdir)
        flow.confirm_outline("demo", self.rdir)
        flow.confirm("demo", self.rdir, "SP-1")
        changed = json.loads(json.dumps(PLAN))
        changed["tasks"][0]["title"] = "Store with retries"
        self.write_plan(changed)
        self.assertEqual(flow.state(self.rdir)["subplans"]["SP-1"]["state"], "changed")
        with self.assertRaises(SystemExit) as raised:
            self.approve()
        self.assertIn("SP-1: cambió después de confirmarlo", str(raised.exception))

    def test_subplan_page_shows_the_flow_actions_and_inputs(self):
        self.spec("pending")
        self.write_plan(PLAN)
        flow.start(self.rdir)
        flow.confirm_outline("demo", self.rdir)
        html = self.page(sp="SP-2")
        self.assertIn('data-k="steps"', html)
        self.assertIn("Subplanes 0/2", html)
        self.assertIn("Definir ahora", html)
        self.assertIn("Entradas · faltan 1", html)
        self.assertIn('value="approve" disabled', html)
        self.assertNotIn("stage-run", html)                      # D-134: only a confirmed subplan can run
        flow.confirm("demo", self.rdir, "SP-1")
        self.assertIn("stage-run", self.page(sp="SP-1"))           # «Ejecutar subplan» sits next to the confirmation
        self.assertIn("Ejecutar subplan", self.page(sp="SP-1"))
        self.assertIn("view=session", html)                       # the hands-on «Sesión» tab is reachable from any subplan
        self.assertIn("session-start", self.page(sp="SP-2", view="session"))
        inputs = self.page(sp="SP-2", view="inputs")
        self.assertIn("Stripe test key", inputs)
        self.assertIn("todo el plan", inputs)

    def test_inputs_table_scopes_and_statuses(self):
        self.spec("deferred: use a mock gateway")
        rows = flow.inputs(self.rdir)
        self.assertEqual([(r["item"], r["subplan"], r["pending"]) for r in rows],
                         [("Repository path", "", False), ("Stripe test key", "SP-2", False)])
        self.spec("deferred")  # a deferral without its fallback is not an answer
        self.assertTrue(flow.inputs(self.rdir)[1]["pending"])
        self.assertEqual([r["item"] for r in flow.inputs_for(self.rdir, "SP-1", rows)], ["Repository path"])

    def test_inputs_parser_handles_real_tables(self):
        (self.rdir / "SPEC.md").write_text("""# Shop

## Inputs

| # | Item | Subplan | Where it lives | Supplier | Status |
|---|---|---|---|---|---|
| 1 | Host a\\|b | sp-1, SP2 | ssh `a\\|b` | Owner | available after Friday |
| 2 | Token | SP-1/SP-9 | env TOKEN | Owner | deferred |
| 3 | Repo | all | ~/dev/shop | Owner | location given |

### Notes

| Subplan | Why |
|---|---|
| SP-1 | context |

## Inputs (extra)

| Item | Where |
|---|---|
| Mail account | 1Password |

## Next
""", encoding="utf-8")
        rows = flow.inputs(self.rdir)
        self.assertEqual([(r["item"], r["subplans"], r["pending"]) for r in rows],
                         [("Host a|b", ["SP-1", "SP-2"], True), ("Token", ["SP-1", "SP-9"], True),
                          ("Repo", [], False), ("Mail account", [], True)])
        self.assertEqual(rows[-1]["status"], "sin columna Status")
        self.assertEqual([r["item"] for r in flow.inputs_for(self.rdir, "SP-2", rows)],
                         ["Host a|b", "Repo", "Mail account"])
        flow.start(self.rdir)
        self.write_plan(PLAN)
        flow.confirm_outline("demo", self.rdir)
        self.assertIn("hay entradas para subplanes que no existen: SP-9", flow.approval_problems(self.rdir))

    def test_a_reopened_subplan_becomes_the_focus_and_its_design_follows(self):
        self.spec("location given")
        self.write_plan(PLAN)
        flow.start(self.rdir)
        flow.confirm_outline("demo", self.rdir)
        flow.confirm("demo", self.rdir, "SP-1")
        self.finish("D-1")
        drafts.rows(self.rdir)
        flow.confirm("demo", self.rdir, "SP-2")
        self.assertEqual(flow.state(self.rdir)["phase"], "ready")
        changed = json.loads(json.dumps(PLAN))
        changed["subplans"][1]["outcome"] = "The buyer pays in two steps."
        self.write_plan(changed)
        st = flow.state(self.rdir)
        self.assertEqual((st["phase"], st["focus"], st["subplans"]["SP-2"]["state"]), ("subplans", "SP-2", "changed"))
        self.assertEqual(flow.design_scope(self.rdir), {"checkout@v1"})
        self.assertIn("desactualizado", " ".join(st["subplans"]["SP-2"]["problems"]))
        self.assertEqual(drafts.sync("demo", self.rdir), ["checkout@v1"])  # redesigned without a click

    def test_actions_are_refused_off_planning_or_while_plan_json_is_written(self):
        self.write_plan(PLAN)
        self.assertIn("no está en la planificación conjunta", flow.confirm_outline("demo", self.rdir))
        flow.start(self.rdir)
        (self.rdir / "PLAN.json").write_text("{", encoding="utf-8")
        self.assertIn("se está editando", flow.confirm_outline("demo", self.rdir))
        self.assertEqual(flow.state(self.rdir)["phase"], "outline")  # not flipped back to the interview
        self.write_plan(PLAN)
        (self.rdir / "PLAN.md").write_text("---\nstatus: approved\n---\n# Plan\n", encoding="utf-8")
        self.assertIn("ya no está en planificación", flow.confirm_outline("demo", self.rdir))
        self.assertIsNone(flow._load(self.rdir)["outline"])


if __name__ == "__main__":
    unittest.main()


class TasksPanel(unittest.TestCase):
    def test_each_task_shows_its_complexity_and_classification(self):
        import bt_page_planning_views as views
        ctx = {"opts": {"lang": "en"}}
        task = {"id": "T1", "title": "Build it", "kind": "implement", "complexity": "high", "risk": "low",
                "coupling": "medium", "confidence": "low", "scope": "large_change", "estimated_minutes": 30,
                "after": ["T0"], "acceptance_criteria": ["a", "b"], "ui": True}
        html = views.tasks_panel(ctx, {"tasks": [task, {"id": "T2", "title": "Bare", "kind": "docs"}]})
        for expected in ("Complejidad alta", "<dt>Riesgo</dt><dd class=\"lv ok\">bajo", "<dt>Acoplamiento</dt><dd class=\"lv mid\">medio",
                         "<dt>Confianza</dt><dd class=\"lv warn\">baja", "cambio grande", "~30 min", "después de T0",
                         "2 criterios", "implement · UI", "0 criterios"):
            self.assertIn(expected, html)
        self.assertEqual(html.count(">Complejidad "), 1)    # a task without complexity shows none rather than a blank

    def test_each_task_shows_everything_the_executor_receives(self):
        import bt_page_planning_views as views
        ctx = {"opts": {"lang": "en"}}
        task = {"id": "T1", "title": "Build it", "kind": "implement", "objective": "Ship <the> guard",
                "acceptance_criteria": ["first criterion"], "expected_paths": ["src/a.ts"], "repository": "pictures",
                "covers": ["R1", "R2"], "estimate_rationale": "30 + 30",
                "verification": [{"type": "command", "value": "npm test", "purpose": "proves it",
                                  "category": "behavior", "created_by": "T1"},
                                 {"type": "manual", "value": "owner looks", "purpose": "approved",
                                  "expected": "named ids", "environment": "human_attestation"}],
                "classification_evidence": {"risk": {"justification": "exposes tools", "evidence": ["file:src/p.ts"]}}}
        html = views.tasks_panel(ctx, {"tasks": [task]})
        for expected in ("Ship &lt;the&gt; guard", "<li>first criterion</li>", "<code>npm test</code>", "proves it",
                         "la crea T1", "Manual</span> owner looks", "Esperado: named ids", "<code>src/a.ts</code>",
                         "<dd>R1, R2</dd>", "30 + 30", "Por qué esta clasificación", "exposes tools",
                         "<code>file:src/p.ts</code>", 'id="t-T1"'):
            self.assertIn(expected, html)
        self.assertIn('<details class="pp-tdet"><summary>', html)    # folded by default: the cards stay scannable
        bare = views.tasks_panel(ctx, {"tasks": [{"id": "T2", "title": "Bare", "kind": "docs"}]})
        self.assertNotIn("pp-tdet", bare)

    def test_the_complexity_pill_lists_the_policy_models_for_the_task(self):
        import bt_page_planning_views as views
        ctx = {"opts": {"lang": "en"}}
        def panel(kind, cx):
            return views.tasks_panel(ctx, {"tasks": [{"id": "T1", "title": "x", "kind": kind, "complexity": cx}]})
        impl = panel("implement", "high")
        self.assertIn("Modelos recomendados", impl)
        self.assertIn("Implementador", impl)
        self.assertLess(impl.index("Sonnet 5.5"), impl.index("GPT-6 Luna"))        # preferred first, then the alternative
        self.assertIn("no cambia la preferencia", impl)
        self.assertIn("<em>Preferido</em>", impl)
        audit = panel("audit", "high")
        self.assertLess(audit.index("GPT-6.1 Sol"), audit.index("Sonnet 5.5"))
        self.assertIn("esfuerzo alto", audit)                                     # the high-complexity reviewer pair
        self.assertIn("rol fijo", panel("docs", "low"))


class PruebasGate(unittest.TestCase):
    setUp = base.DraftTests.setUp
    write_plan = base.DraftTests.write_plan
    create = base.DraftTests.create
    finish = base.DraftTests.finish

    def test_a_subplan_cannot_be_confirmed_without_how_to_try_it_and_changing_it_reopens_the_subplan(self):
        plan = {"milestones": PLAN["milestones"], "subplans": PLAN["subplans"][:1], "tasks": PLAN["tasks"][:1]}
        self.write_plan(plan)
        flow.start(self.rdir)
        flow.confirm_outline("demo", self.rdir)
        spec = SPEC.split("## Pruebas")[0].format(status="location given")
        (self.rdir / "SPEC.md").write_text(spec, encoding="utf-8")
        self.assertIn("falta cómo probarlo", flow.confirm("demo", self.rdir, "SP-1"))
        (self.rdir / "SPEC.md").write_text(spec + "## Pruebas\n| Subplan | Where | How | Expect |\n|---|---|---|---|\n"
                                           "| SP-1 | Local | run it | it works |\n", encoding="utf-8")
        self.assertIn("SP-1 confirmado", flow.confirm("demo", self.rdir, "SP-1"))
        self.assertEqual(flow.state(self.rdir)["subplans"]["SP-1"]["state"], "confirmed")
        (self.rdir / "SPEC.md").write_text(spec + "## Pruebas\n| Subplan | Where | How | Expect |\n|---|---|---|---|\n"
                                           "| SP-1 | Local | run it twice | it works |\n", encoding="utf-8")
        self.assertEqual(flow.state(self.rdir)["subplans"]["SP-1"]["state"], "changed")

    def test_confirmations_made_before_pruebas_existed_keep_their_digest(self):
        plan = {"milestones": PLAN["milestones"], "subplans": PLAN["subplans"][:1], "tasks": PLAN["tasks"][:1]}
        self.write_plan(plan)
        sp = flow._plan_order(self.rdir)[0]
        no_tests = flow._digest(self.rdir, flow.drafts._plan(self.rdir), sp, [])
        (self.rdir / "SPEC.md").write_text("## Pruebas\n| Subplan | Where | How | Expect |\n|---|---|---|---|\n| SP-1 | Local | go | ok |\n")
        self.assertNotEqual(flow._digest(self.rdir, flow.drafts._plan(self.rdir), sp, []), no_tests)
        (self.rdir / "SPEC.md").write_text("# nothing about tests\n")
        self.assertEqual(flow._digest(self.rdir, flow.drafts._plan(self.rdir), sp, []), no_tests)


class ResumeBriefing(unittest.TestCase):
    setUp = base.DraftTests.setUp
    write_plan = base.DraftTests.write_plan
    create = base.DraftTests.create
    finish = base.DraftTests.finish

    def brief(self) -> str:
        import bt_planning_resume as resume
        return resume.briefing("demo", self.rdir)

    def test_a_new_session_is_told_to_start_then_to_wait_for_an_open_round(self):
        self.write_plan(PLAN)
        self.assertIn("NEXT: Collaborative planning is not on", self.brief())
        flow.start(self.rdir)
        self.assertIn("No skeleton yet" if flow.state(self.rdir)["phase"] == "interview" else "skeleton", self.brief())
        f = bt_rounds.new_round(self.rdir, {"title": "Scope", "questions": [{"text": "Who uses it?", "options": [
            {"key": "a", "label": "staff"}], "type": "choice"}]})
        self.assertIn("Round 1 is open", self.brief())
        bt_rounds.answer_round(f, {"q1": {"choice": "a", "note": "only staff"}}, "terminal")
        text = self.brief()
        self.assertIn("only staff", text)
        self.assertNotIn("is open", text)

    def test_it_lists_subplans_without_a_pruebas_row_and_the_focus_work(self):
        self.write_plan(PLAN)
        flow.start(self.rdir)
        flow.confirm_outline("demo", self.rdir)
        (self.rdir / "SPEC.md").write_text("# Shop\n", encoding="utf-8")
        text = self.brief()
        self.assertIn("Without a `## Pruebas` row", text)
        self.assertIn("SP-1", text.split("Without a `## Pruebas` row")[1].splitlines()[0])
        self.assertIn("Define the focus subplan SP-1", text)
