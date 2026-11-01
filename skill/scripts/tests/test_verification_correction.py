"""A rejected subplan version waiting for its correction (bt_verification_correction + bt_page_correction, D-268).

Owner, 2026-10-31, about pictures REQ-021 SP-14 (v2 rejected at 15:30, its design redone since): «en el panel debe
aparecer como rechazada en espera de iteración o algo así». Each phase of the correction is derived from existing data
(decisions, drafts, approvals, the planning flow, the run projection), shown as the primary label wherever the subplan's
state appears, and gone once vN+1 is ready to try.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_design_drafts as drafts
import bt_page_correction as correction_view
import bt_planning_flow as flow
import bt_verification as v
import bt_verification_correction as c

SPEC = """# REQ-9 — demo

## Pruebas
| Subplan | Dónde | Cómo | Qué debes ver |
|---|---|---|---|
| SP-1 | Local | abre /datos | Los datos |
| SP-2 | Local | abre /planes | Las cartas de planes |
"""
PLAN = {"milestones": [{"id": "M1", "title": "Pilot"}],
        "subplans": [{"id": "SP-1", "milestone_id": "M1", "title": "Data", "outcome": "Stores."},
                     {"id": "SP-2", "milestone_id": "M1", "title": "Plans page", "outcome": "Plans as cards.",
                      "ui": {"contract": "planes", "version": 2}}],
        "tasks": [{"id": "T1", "subplan_id": "SP-1", "title": "Store", "acceptance_criteria": ["ok"]},
                  {"id": "T2", "subplan_id": "SP-2", "title": "Build plans", "acceptance_criteria": ["ok"]}]}
REJECTED_AT = "2026-10-31T15:30:21-05:00"
BEFORE, AFTER = "2026-10-27T18:48:34-05:00", "2026-10-31T19:16:48-05:00"
NOTE = "Quitemos la lógica de la comparación; los planes como cartas de suscripción"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name) / "pictures" / "requirements" / "REQ-021-pilot"
        self.rdir.mkdir(parents=True)
        (self.rdir / "SPEC.md").write_text(SPEC, encoding="utf-8")
        (self.rdir / "PLAN.json").write_text(json.dumps(PLAN), encoding="utf-8")
        self.publish(SP_1=(1, "a" * 40), SP_2=(2, "b" * 40))

    def publish(self, **versions):
        rows = [{"id": sid.replace("_", "-"), "status": "published", "version": ver, "commit": commit}
                for sid, (ver, commit) in versions.items()]
        (self.rdir / v.PROJECTION).write_text(json.dumps({"subplans": rows}), encoding="utf-8")

    def reject(self, sid: str = "SP-2", version: int = 2, commit: str = "b" * 40, pending: str = "P-211") -> None:
        with v._locked(self.rdir) as data:
            data["gated"] = True
            data["subplans"][sid] = {"decision": "rejected", "version": version, "commit": commit, "by": "owner",
                                     "via": "web", "at": REJECTED_AT, "note": NOTE, "pending": pending,
                                     "open_pending": [pending]}

    def draft(self, status: str, **extra) -> None:
        sub = next(s for s in drafts.subplans(self.rdir) if s["id"] == "SP-2")
        folder = self.rdir / drafts.DIR
        folder.mkdir(exist_ok=True)
        entry = {"status": status, "subplan_id": "SP-2", "ui_digest": sub["ui_digest"], "started": AFTER, **extra}
        (folder / drafts.FILE).write_text(json.dumps({"schema_version": 1, "drafts": {"planes@v2": entry}}), encoding="utf-8")

    def confirm(self, at: str | None) -> None:
        """The planning flow's confirmation of SP-2 as the plan is now (`at`), or a stale one (None)."""
        folder = self.rdir / flow.DIR
        folder.mkdir(exist_ok=True)
        plan = drafts._plan(self.rdir)
        digest = flow._digest(self.rdir, plan, flow._row(plan, "SP-2"), flow.inputs(self.rdir)) if at else "0" * 16
        (folder / flow.FILE).write_text(json.dumps({"schema_version": 1, "outline": {"at": BEFORE}, "focus": "SP-2",
                                                    "subplans": {"SP-2": {"at": at or BEFORE, "digest": digest}}}),
                                        encoding="utf-8")

    def phase(self, sid: str = "SP-2", **kw) -> dict | None:
        return c.correction(self.rdir, sid, **kw)


class Phases(Base):
    def test_a_redesign_walks_the_pipeline_in_order(self):
        self.reject()
        self.confirm(None)                                   # the confirmation predates the new contract
        self.draft("drafting", phase="explore")
        got = self.phase()
        self.assertEqual((got["path"], got["phase"], got["label"]), ("redesign", "redesigning", "Rechazada v2 · rediseñando"))
        self.assertEqual([s["label"] for s in got["steps"]], ["rediseñando", "elige una dirección", "aprueba el contrato",
                                                              "reconfirma el subplan", "por unir a la ejecución",
                                                              "construyendo v3", "v3 lista para probar"])
        self.assertEqual([s["state"] for s in got["steps"]], ["now", "todo", "todo", "todo", "todo", "todo", "todo"])
        self.assertEqual((got["note"], got["pending"], got["next"]), (NOTE, "P-211", 3))

        self.draft("choosing", directions=[{"id": "a", "status": "ready"}])
        self.assertEqual(self.phase()["label"], "Rechazada v2 · elige una dirección")
        self.draft("drafting", phase="finalise", chosen="c")         # the chosen direction becomes the contract
        self.assertEqual(self.phase()["phase"], "redesigning")
        self.draft("ready", chosen="c")
        got = self.phase()
        self.assertEqual(got["label"], "Rechazada v2 · aprueba el contrato")
        self.assertEqual([s["state"] for s in got["steps"]][:3], ["done", "done", "now"])
        self.draft("approved", chosen="c", approved=AFTER)
        self.assertEqual(self.phase()["label"], "Rechazada v2 · reconfirma el subplan")
        self.confirm(AFTER)
        got = self.phase(progress=(2, 5))
        self.assertEqual((got["label"], got["detail"]), ("Rechazada v2 · construyendo v3", "2/5 tareas"))

    def test_the_label_goes_away_once_the_next_version_is_ready_to_try(self):
        self.reject()
        self.draft("approved", chosen="c", approved=AFTER)
        self.confirm(AFTER)
        self.assertEqual(self.phase()["phase"], "building")
        self.publish(SP_1=(1, "a" * 40), SP_2=(3, "c" * 40))
        row = next(r for r in v.state(self.rdir)["subplans"] if r["id"] == "SP-2")
        self.assertEqual((row["state"], row["retest"]), ("outdated", True))      # «por probar» with the note, as before
        self.assertIsNone(self.phase())
        self.assertEqual(c.corrections(self.rdir), {})

    def test_a_contract_approved_in_the_approvals_file_after_the_rejection_is_a_redesign(self):
        self.reject()
        self.draft("approved", chosen="c")                    # no stamp on the draft: the approvals record decides
        (self.rdir / "design-approvals.json").write_text(json.dumps({"schema_version": 1, "approvals": {"planes@v2": {
            "status": "approved", "when": "2026-10-31T22:04:58+00:00"}}}), encoding="utf-8")
        self.confirm(None)
        self.assertEqual(self.phase()["phase"], "reconfirm")

    def test_without_the_planning_flow_an_approved_redesign_is_building(self):
        self.reject()
        self.draft("approved", chosen="c", approved=AFTER)
        self.assertEqual(self.phase()["phase"], "building")

    def test_a_bounded_repair_is_repairing_until_the_next_version(self):
        self.reject()
        self.draft("approved", chosen="b", approved=BEFORE)    # the design stands: the fix is repair tasks
        got = self.phase(row={**next(r for r in v.state(self.rdir)["subplans"] if r["id"] == "SP-2"),
                              "solver": {"text": "el Solucionador confirmó el fallo y pidió la reparación"}},
                         progress=(1, 2))
        self.assertEqual((got["path"], got["label"]), ("repair", "Rechazada v2 · reparando"))
        self.assertEqual([s["label"] for s in got["steps"]], ["reparando", "v3 lista para probar"])
        self.assertEqual(got["detail"], "el Solucionador confirmó el fallo y pidió la reparación · 1/2 tareas")
        self.publish(SP_1=(1, "a" * 40), SP_2=(3, "c" * 40))
        self.assertIsNone(self.phase())

    def test_a_subplan_without_interface_or_designer_is_repaired(self):
        self.reject("SP-1", 1, "a" * 40, "P-213")
        self.assertEqual(self.phase("SP-1")["label"], "Rechazada v1 · reparando")
        self.reject()                                         # SP-2 has a contract but the Designer never ran here
        self.assertEqual(self.phase()["path"], "repair")

    def test_approved_or_untouched_subplans_have_no_correction(self):
        self.assertIsNone(self.phase())
        with v._locked(self.rdir) as data:
            data["subplans"]["SP-2"] = {"decision": "approved", "version": 2, "commit": "b" * 40, "at": AFTER}
        self.assertIsNone(self.phase())

    def test_the_read_model_writes_nothing(self):
        self.reject()
        self.draft("drafting")
        self.confirm(None)
        before = {p: p.read_bytes() for p in self.rdir.rglob("*") if p.is_file()}
        c.correction(self.rdir, "SP-2")
        c.corrections(self.rdir)
        self.assertEqual({p: p.read_bytes() for p in self.rdir.rglob("*") if p.is_file()}, before)


class Views(Base):
    def ctx(self) -> dict:
        return {"project": "pictures", "rid": "REQ-021", "rdir": self.rdir, "token": "tok", "root": None}

    def test_badge_and_strip_carry_the_note_and_the_pending_link(self):
        self.reject()
        self.draft("drafting")
        got = self.phase()
        badge = correction_view.badge(got)
        self.assertIn('class="pp-state rejected"', badge)
        self.assertIn("Rechazada v2 · rediseñando</span>", badge)
        self.assertIn("title=\"Tu nota: «Quitemos la lógica", badge)
        strip = correction_view.strip("pictures", got)
        self.assertIn('<li class="now" aria-current=step>rediseñando', strip)
        self.assertIn("<summary>Tu nota del rechazo · P-211</summary>", strip)
        self.assertIn('href="/go/pictures/P-211"', strip)
        self.assertNotIn("<details", correction_view.strip("pictures", got, note=False))
        self.assertIn('href="/go/pictures/P-211"', correction_view.strip("pictures", got, note=False))

    def test_probar_run_card_and_chip_show_the_correction_instead_of_a_bare_rejection(self):
        import bt_page_verification as page
        self.reject()
        self.draft("ready", chosen="c")
        panel = page.panel(self.ctx(), {"id": "SP-2"})
        self.assertIn('<span class="pp-vstate bad" title="Tu nota: «', panel)
        self.assertIn("Rechazada v2 · aprueba el contrato</span> Versión 2", panel)
        self.assertIn('class="pp-rej"', panel)
        self.assertIn("Tu nota: «Quitemos", panel)                       # the note stays in the actions
        card = page.run_card("pictures", "REQ-021", self.rdir)
        self.assertIn("Rechazada v2 · aprueba el contrato", card)
        chip = page.chip(self.rdir)
        self.assertIn("por probar 1", chip)                               # SP-1 v1 waits for its test
        self.assertIn("1 rechazada en corrección", chip)
        self.assertIn('title="SP-2: Rechazada v2 · aprueba el contrato"', chip)
        self.publish(SP_1=(1, "a" * 40), SP_2=(3, "c" * 40))              # v3 ready to try: back to «por probar»
        panel = page.panel(self.ctx(), {"id": "SP-2"})
        self.assertNotIn("Rechazada v2", panel)
        self.assertIn('<span class="pp-vstate warn">por probar</span>', panel)
        self.assertIn("Rechazaste la versión 2: «Quitemos", panel)
        self.assertNotIn("rechazada", page.chip(self.rdir))

    def test_the_now_page_says_a_rejected_subplan_is_in_correction(self):
        import bt_live_api
        import bt_page_now
        self.reject()
        self.draft("drafting")
        with patch.object(bt_live_api, "runs", return_value=[("pictures", self.rdir)]):
            items = bt_live_api.verify_items(Path(self.tmp.name))
        self.assertEqual(items[0]["rejected"], {"SP-2": "Rechazada v2 · rediseñando"})
        html = bt_page_now.verify_html(items)
        self.assertIn("por probar", html)                                 # SP-1 still waits for its test
        self.assertIn("SP-2 · Rechazada v2 · rediseñando", html)
        only = [{**items[0], "subplans": ["SP-2"]}]
        self.assertIn('<i class="dot bad"></i>en corrección', bt_page_now.verify_html(only))
        self.assertIn("REQ-021 · SP-2 rechazada v2 · rediseñando", bt_page_now.bar_html([], verify=only))


class OlderVersionRepublished(Base):
    """Live pictures REQ-021, 2026-10-31 ~19:40: after the rejections a new run revision re-published older trees for
    retest — SP-14 v2 (another commit), SP-2 v1, SP-3 v2 — while the decisions rejected v2, v2 and v3. `state` gave
    `outdated` + `retest`, and the first D-268 filter (`state == "rejected"`) showed nothing."""

    def ctx(self) -> dict:
        return {"project": "pictures", "rid": "REQ-021", "rdir": self.rdir, "token": "tok", "root": None}

    def live_rows(self) -> None:
        self.reject("SP-2", 2, "b" * 40, "P-210")
        self.reject("SP-1", 3, "e" * 40, "P-213")
        self.draft("approved", chosen="c", approved=AFTER)
        self.publish(SP_1=(2, "a" * 40), SP_2=(1, "d" * 40))

    def test_the_live_rows_are_outdated_retests_and_still_in_correction(self):
        self.live_rows()
        rows = {r["id"]: r for r in v.state(self.rdir)["subplans"]}
        self.assertEqual([(rows[s]["state"], rows[s]["retest"], rows[s]["version"]) for s in ("SP-1", "SP-2")],
                         [("outdated", True, 2), ("outdated", True, 1)])
        found = c.corrections(self.rdir)
        self.assertEqual({sid: x["label"] for sid, x in found.items()},
                         {"SP-1": "Rechazada v3 · reparando", "SP-2": "Rechazada v2 · construyendo v3"})
        self.assertEqual((found["SP-2"]["retest"], found["SP-2"]["detail"]),
                         (1, "v1 publicada de nuevo para volver a probarla"))
        self.publish(SP_1=(2, "a" * 40), SP_2=(2, "f" * 40))          # same number, another tree: still not v3
        self.assertEqual(c.correction(self.rdir, "SP-2")["phase"], "building")
        self.publish(SP_1=(4, "a" * 40), SP_2=(3, "f" * 40))          # above N: the corrections are ready to try
        self.assertEqual(c.corrections(self.rdir), {})

    def test_probar_shows_the_retest_without_hiding_the_rejection(self):
        import bt_page_verification as page
        self.live_rows()
        panel = page.panel(self.ctx(), {"id": "SP-2"})
        self.assertIn('Rechazada v2 · construyendo v3</span><span class="pp-vstate warn">por probar</span> Versión 1', panel)
        self.assertIn("La versión 1 se publicó de nuevo y no es la corrección: puedes volver a probarla mientras llega la "
                      "versión 3.", panel)
        self.assertIn('class="pp-rej"', panel)
        self.assertIn("verify-approve", panel)                           # the retest can still be decided
        chip = page.chip(self.rdir)
        self.assertIn("2 rechazadas en corrección", chip)
        self.assertNotIn("por probar", chip)                             # both «por probar» rows are corrections
        self.assertIn("Rechazada v3 · reparando", page.run_card("pictures", "REQ-021", self.rdir))

    def test_the_control_block_and_the_now_page_keep_the_rejection(self):
        import bt_live_api
        import bt_subplan_status as status_model
        self.live_rows()
        ctx = {**self.ctx(), "subplans": drafts.subplans(self.rdir), "flow": None,
               "rows": {row["ref"]: row for row in drafts.rows(self.rdir)},
               "run_status": None, "opts": {"lang": "en", "sp": "SP-2"}}
        with patch.object(status_model, "_stages", return_value={}):
            st = status_model.statuses(ctx)["SP-2"]
        self.assertIn("Puedes volver a probar la versión 1; tu rechazo de la versión 2 sigue en corrección",
                      [i["text"] for i in st["you"]])
        self.assertTrue(any(b["text"].startswith("Rechazaste la versión 2: construyendo v3") for b in st["blockers"]))
        with patch.object(bt_live_api, "runs", return_value=[("pictures", self.rdir)]):
            items = bt_live_api.verify_items(Path(self.tmp.name))
        self.assertEqual(items[0]["rejected"], {"SP-1": "Rechazada v3 · reparando",
                                                "SP-2": "Rechazada v2 · construyendo v3"})


class JoinPending(Base):
    """pictures REQ-021, 2026-10-31: SP-14 reconfirmed at 19:55:55, stage r34 frozen at 19:56:01 with it, the join refused
    (JOIN_MATERIAL_MISSING) and the durable run still in r32 — the panel said «construyendo v3» while nothing built
    (D-272). «construyendo» needs the running revision to hold the stage with the reconfirmed subplan."""

    CONFIRMED = "2026-10-31T19:55:55-05:00"

    def setUp(self):
        super().setUp()
        import bt_run_owner
        self.reject()
        self.draft("approved", chosen="c", approved=AFTER)
        self.confirm(self.CONFIRMED)
        bt_run_owner.write(self.rdir, {"run_id": "pictures:REQ-021:r32", "backend": "dbos", "since": 1.0, "by": "test",
                                       "workflow_id": "bt:pictures:REQ-021:r32"}, expect=None)
        self.running(32)
        self.stages = [{"revision": 31, "frozen_at": "2026-10-31T16:02:56", "subplans": ["SP-1", "SP-2"], "kept": []},
                       {"revision": 32, "frozen_at": "2026-10-31T17:05:00", "subplans": ["SP-1", "SP-2"], "kept": ["SP-2"]},
                       {"revision": 33, "frozen_at": "2026-10-31T18:12:04", "subplans": ["SP-1", "SP-2"], "kept": []}]

    def running(self, revision: int) -> None:
        (self.rdir / "RUN.durable-run.json").write_text(json.dumps({"project": "pictures", "req": "REQ-021",
                                                                    "revision": revision}))

    def phase(self, sid: str = "SP-2", **kw) -> dict | None:
        import bt_plan_adapter
        with patch.object(bt_plan_adapter, "stage_summary", return_value={"stages": self.stages, "complete": False}):
            return c.correction(self.rdir, sid, **kw)

    def test_a_reconfirmed_change_not_frozen_yet_waits_for_ejecutar_cambios(self):
        got = self.phase()
        self.assertEqual((got["phase"], got["label"]), ("joining", "Rechazada v2 · por unir a la ejecución"))
        self.assertEqual(got["detail"], "aprueba la etapa con «Ejecutar cambios»; la ejecución sigue en r32")
        self.assertEqual([s["state"] for s in got["steps"]], ["done", "done", "done", "done", "now", "todo", "todo"])
        self.assertEqual(got["join"], {"stage": None, "running": 32, "waiting": False, "refused": None})

    def test_a_frozen_stage_the_run_has_not_joined_is_por_unir_with_the_refusal(self):
        self.stages.append({"revision": 34, "frozen_at": "2026-10-31T19:56:01", "subplans": ["SP-1", "SP-2"], "kept": []})
        got = self.phase(progress=(0, 3))
        self.assertEqual((got["phase"], got["detail"]), ("joining", "etapa r34 aprobada; la ejecución sigue en r32"))
        (self.rdir / "RUN.join.refused.json").write_text(json.dumps({
            "at": "2026-10-31T19:56:05-05:00", "revision": 34, "code": "JOIN_MATERIAL_MISSING",
            "message": "T2.3 was accepted in pictures:REQ-021:r32 but its snapshot (2d45cd5030b7) has no captured handoff"}))
        got = self.phase()
        self.assertEqual(got["detail"], "etapa r34 aprobada; la ejecución sigue en r32 · la unión se rechazó: "
                                        "JOIN_MATERIAL_MISSING: T2.3 was accepted in pictures:REQ-021:r32 but its snapshot "
                                        "(2d45cd5030b7) has no captured handoff")
        self.assertEqual(got["join"]["refused"]["code"], "JOIN_MATERIAL_MISSING")
        (self.rdir / "RUN.join.json").write_text(json.dumps({"run": {"revision": 34}}))     # the engine's pending join
        self.assertEqual(self.phase()["detail"], "etapa r34 aprobada; la ejecución sigue en r32 · se une en cuanto "
                                                 "terminen los intentos en curso")
        (self.rdir / "RUN.join.json").write_text(json.dumps({"run": {"revision": 34}, "error": "JOIN_LINES_EXIST: x"}))
        self.assertIn("la unión se rechazó: JOIN_LINES_EXIST: x", self.phase()["detail"])

    def test_once_the_run_holds_the_stage_it_is_building(self):
        self.stages.append({"revision": 34, "frozen_at": "2026-10-31T19:56:01", "subplans": ["SP-1", "SP-2"], "kept": []})
        (self.rdir / "RUN.join.refused.json").write_text(json.dumps({"revision": 34, "code": "OLD", "message": "x"}))
        self.running(34)
        got = self.phase(progress=(1, 3))
        self.assertEqual((got["label"], got["detail"], got["join"]), ("Rechazada v2 · construyendo v3", "1/3 tareas", None))

    def test_a_stage_that_kept_the_subplan_as_before_does_not_hold_the_change(self):
        self.stages.append({"revision": 34, "frozen_at": "2026-10-31T19:56:01", "subplans": ["SP-1", "SP-2"],
                            "kept": ["SP-2"]})
        self.running(34)
        self.assertEqual(self.phase()["join"]["stage"], None)

    def test_a_run_outside_the_durable_runtime_keeps_building(self):
        (self.rdir / "RUN.owner.json").unlink()
        self.assertEqual(self.phase()["phase"], "building")

    def test_the_control_block_asks_the_owner_only_when_the_change_is_not_frozen(self):
        import bt_plan_adapter
        import bt_subplan_status as status_model

        def blockers() -> list[dict]:
            ctx = {"project": "pictures", "rid": "REQ-021", "rdir": self.rdir, "token": "tok", "root": None,
                   "subplans": drafts.subplans(self.rdir), "flow": None,
                   "rows": {row["ref"]: row for row in drafts.rows(self.rdir)},
                   "run_status": None, "opts": {"lang": "en", "sp": "SP-2"}}
            with patch.object(status_model, "_stages", return_value={}), \
                    patch.object(bt_plan_adapter, "stage_summary", return_value={"stages": self.stages}):
                return status_model.statuses(ctx)["SP-2"]["blockers"]
        found = blockers()
        self.assertTrue(any(b["who"] == "Tú" and b["text"].startswith("Rechazaste la versión 2: por unir a la ejecución")
                            for b in found), found)
        self.stages.append({"revision": 34, "frozen_at": "2026-10-31T19:56:01", "subplans": ["SP-1", "SP-2"], "kept": []})
        found = blockers()
        self.assertTrue(any(b["who"] == "Ejecución" and "etapa r34 aprobada" in b["text"] for b in found), found)


class PlanTab(unittest.TestCase):
    """The subplan list, its header and the control block of the Plan tab (fixtures of test_subplan_control)."""

    def setUp(self):
        import test_subplan_control as control
        self.case = control.ControlTests("test_feed_follows_the_open_subplan_without_translation_noise")
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.rdir = self.case.rdir

    def test_the_rejection_is_the_primary_label_in_the_list_header_and_control(self):
        case = self.case
        case.spec("location given")
        case.started()
        case.finish("D-1")                                               # checkout@v1 ready: contract to approve
        rows = [{"id": "SP-1", "status": "published", "version": 1, "commit": "a" * 40},
                {"id": "SP-2", "status": "published", "version": 2, "commit": "b" * 40}]
        (self.rdir / v.PROJECTION).write_text(json.dumps({"subplans": rows}), encoding="utf-8")
        with v._locked(self.rdir) as data:
            data["gated"] = True
            data["subplans"]["SP-2"] = {"decision": "rejected", "version": 2, "commit": "b" * 40, "at": REJECTED_AT,
                                        "note": "el pago falla", "pending": "P-9", "open_pending": ["P-9"]}
        drafts.rows(self.rdir)                                           # settle the finished Designer session
        html = case.page(sp="SP-2")
        listing = html.split('data-k="list"')[1].split('class="pp-detail"')[0]
        self.assertIn('<span class="pp-rejtag" title="Tu nota: «el pago falla» · P-9">Rechazada v2 · aprueba el contrato'
                      '</span>', listing)
        self.assertIn('class="pp-dot rejected" title="Rechazada v2 · aprueba el contrato"', listing)
        self.assertNotIn("· rechazado", listing)
        head = html.split('class="pp-dhead"')[1].split("</header>")[0]
        self.assertLess(head.index("Rechazada v2 · aprueba el contrato"), head.index("diseño listo"))
        self.assertIn('class="pp-rej"', html)
        self.assertIn('href="/go/demo/P-9"', html)
        self.assertIn("Rechazaste la versión 2: aprueba el contrato", html)   # the control block's blocker
        rows[1].update(version=3, commit="c" * 40)                       # v3 published: the label goes away
        (self.rdir / v.PROJECTION).write_text(json.dumps({"subplans": rows}), encoding="utf-8")
        html = case.page(sp="SP-2")
        self.assertNotIn("Rechazada v2", html)
        self.assertNotIn('class="pp-rej"', html)


if __name__ == "__main__":
    unittest.main()
