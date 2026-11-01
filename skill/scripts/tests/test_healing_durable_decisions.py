"""The engine answers a durable run's open decision the way the legacy Scheduler's self-healing did: a diagnosing model
reads the failure and its validated `retry`/`retry_with_note` goes to that exact round, once per signature; a plan defect
goes to the Planner and stays for the owner (D-167; pictures REQ-021 T4.2, T7.4 and T93 waited for a person)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_block_agent
from bt_durable import healing

FLAGS = {"healing.enabled": True, "healing.model_diagnosis": True, "diagnosis.auto": True,
         "healing.max_per_task": 2, "healing.max_actions": 40}


class Client:
    def __init__(self, decision: dict, round_no: int = 2):
        self.item = {"workflow_id": f"bt:proj:REQ-900:r1:T7.4:k{round_no}", "decision": decision,
                     "state": {"state": "needs_decision"}}
        self.answers = []

    def status(self, run):
        return {"tasks": {"T7.4": self.item}}

    def answer(self, run, task_id, answer, round_no=None):
        self.answers.append((task_id, answer.request_id, answer.action, answer.note, answer.by, round_no))
        return "bt:wf"


def decision(signature: str = "sig-1", request: str = "T7.4:d1") -> dict:
    return {"request_id": request, "task_id": "T7.4", "reason": "the task used its attempts", "limit_hit": "max_attempts",
            "options": ["reverify", "retry", "retry_with_note", "retry_other_route", "stop"],
            "failure": {"failure_class": "implementation", "code": "CHECK_FAILED", "signature": signature,
                        "summary": "checks failed: npm run herramientas:test-checkpoint",
                        "evidence": [{"kind": "output_line", "excerpt": "counter.form: Expected HTTP 200; got 502"}]}}


class DurableHealing(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="bt-healing-"))
        self.rdir = self.root / "proj" / "requirements" / "REQ-900-x"
        (self.rdir / "plan-revisions").mkdir(parents=True)
        plan = self.rdir / "plan-revisions" / "PLAN.r1.json"
        plan.write_text(json.dumps({"tasks": [{"id": "T7.4", "title": "Checkpoint", "subplan_id": "SP-7", "after": ["T7.3"],
                                               "objective": "Counter on a running server", "acceptance_criteria": ["200"],
                                               "verification": [{"value": "npm run herramientas:test-checkpoint",
                                                                 "category": "integration"}]}]}))
        (self.rdir / "RUN.durable-run.json").write_text(json.dumps(
            {"project": "proj", "req": "REQ-900", "revision": 1, "plan_id": "REQ-900", "plan_path": str(plan),
             "plan_sha256": "0" * 64}))
        self.planner, self.escalated = [], []
        self.patches = [patch("bt_config.get", side_effect=lambda key, default=None: FLAGS.get(key, default)),
                        patch("bt_planning_activity.record")]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def diagnosis(self, **answer):
        def diagnose(project, rdir, request, evidence):
            self.request, self.evidence = request, evidence
            bt_block_agent._write(rdir, request["id"], {"state": "done", **answer})
        return diagnose

    def heal(self, client, diagnose):
        return healing.heal(self.root, client, diagnose=diagnose, start=lambda job: job(),
                            notify=lambda *args: self.planner.append(args), escalate=self.escalated.append)

    def test_a_diagnosed_note_goes_to_that_round_once_per_signature(self):
        client = Client(decision())
        diagnose = self.diagnosis(kind="environment", option="retry_with_note", confidence="alta",
                                  headline="El checkpoint no arranca ai-api",
                                  note="Start services/ai-api with a shared INTERNAL_HMAC_SECRET before next dev.")
        self.assertEqual(self.heal(client, diagnose), ["proj:REQ-900:r1:T7.4:T7.4:d1@k2: diagnosing"])
        self.assertIn("npm run herramientas:test-checkpoint", self.evidence)
        self.assertEqual([o["id"] for o in self.request["options"]],
                         ["reverify", "retry", "retry_with_note", "retry_other_route", "stop"])
        self.assertEqual(self.heal(client, diagnose), ["proj:REQ-900:r1:T7.4:T7.4:d1@k2: retry_with_note"])
        self.assertEqual(client.answers, [("T7.4", "T7.4:d1", "retry_with_note",
                                           "Start services/ai-api with a shared INTERNAL_HMAC_SECRET before next dev.",
                                           "healing", 2)])
        self.assertEqual(self.heal(client, diagnose), [])                    # the same request: answered already
        client.item["decision"] = decision(request="T7.4:d2")                # the same failure again: the owner's
        client.item["workflow_id"] = "bt:proj:REQ-900:r1:T7.4:k3"
        self.assertEqual(self.heal(client, diagnose),                        # ...and the Solucionador's (REQ-031)
                         ["proj:REQ-900:r1:T7.4:T7.4:d2@k3: the same failure again, left to the owner"])
        self.assertEqual(self.heal(client, diagnose), [])
        self.assertEqual(len(client.answers), 1)
        self.assertEqual([(e["kind"], e["request_id"], e["round"]) for e in self.escalated], [("repeat", "T7.4:d2", 3)])

    def test_an_attempt_that_changed_nothing_reaches_the_diagnosis_and_is_not_retried_again(self):
        """pictures REQ-021 r32 T2.57 (D-262): every attempt changed nothing and its agent said it stopped at the design
        gate; healing answered d1, d2, d3 with the same note about an npm script, each with a new signature."""
        said = "I stopped at the design gate: design/contracts/cuentas-admin@v2.md is missing, so I changed nothing."
        outputs = {"att-1": {"agent": {"status": "completed", "text": said},
                             "snapshot": {"snapshot_sha": "a" * 40, "base_sha": "a" * 40, "changed_paths": []}}}
        client = Client(dict(decision(signature="sig-a"), verify_attempt="att-1"), round_no=1)
        client.attempt_output = outputs.get
        diagnose = self.diagnosis(kind="code", option="retry_with_note", confidence="media",
                                  headline="Falta el script npm", note="Add the npm script cuentas:test-ui-redesign first.")
        self.heal(client, diagnose)
        self.assertIn("it changed NOTHING", self.evidence)
        self.assertIn(said, self.evidence)
        self.heal(client, diagnose)
        self.assertEqual(len(client.answers), 1)
        outputs["att-2"] = outputs["att-1"]
        client.item["decision"] = dict(decision(signature="sig-b", request="T7.4:d2"), verify_attempt="att-2")
        self.assertEqual(self.heal(client, diagnose),
                         ["proj:REQ-900:r1:T7.4:T7.4:d2@k1: no change again after healing's answer, left to the owner"])
        self.assertEqual(len(client.answers), 1)
        self.assertEqual([(e["kind"], e["request_id"]) for e in self.escalated], [("repeat", "T7.4:d2")])
        self.assertIn("changed nothing", self.escalated[0]["reason"])

    def test_an_agent_that_could_not_run_its_checks_is_left_to_the_owner(self):
        """pictures REQ-021 r32 T3.91 a5..a7 (D-265): the agent said its DB check could not run (refused connection) and
        healing answered with locator and hit-testing guesses until max_attempts."""
        said = ("Cambios hechos. La URL de prueba apunta al puerto 55965, que rechazó la conexión, así que el smoke real "
                "de navegador queda pendiente.")
        outputs = {"att-5": {"agent": {"status": "completed", "text": said},
                             "snapshot": {"snapshot_sha": "b" * 40, "base_sha": "a" * 40, "changed_paths": ["a.ts"]}}}
        client = Client(dict(decision(), verify_attempt="att-5"))
        client.attempt_output = outputs.get
        calls = []
        self.assertEqual(self.heal(client, lambda *args: calls.append(args)),
                         ["proj:REQ-900:r1:T7.4:T7.4:d1@k2: environment, left to the owner"])
        self.assertEqual((calls, client.answers), ([], []))                 # no diagnosis, no answer
        self.assertEqual([e["kind"] for e in self.escalated], ["decision"])
        self.assertIn("could not run its checks", self.escalated[0]["reason"])
        facts = healing.attempt_facts(client, {"verify_attempt": "att-5"})
        self.assertTrue(facts["checks_not_run"])
        run = next(healing.runs(self.root))[1]
        text = healing.evidence(run, self.rdir, "T7.4", decision(), 2, facts)
        self.assertTrue(text.startswith("THE AGENT SAYS IT COULD NOT RUN ITS CHECKS"))

    def test_an_unreachable_test_resource_is_left_to_the_owner(self):
        env = dict(decision(), failure={"failure_class": "environment", "code": "AGENT_ENV_UNREACHABLE",
                                        "signature": "sig-env", "summary": "AGENT_ENV_UNREACHABLE: DB_URL -> ..."})
        client = Client(env)
        calls = []
        self.assertEqual(self.heal(client, lambda *args: calls.append(args)),
                         ["proj:REQ-900:r1:T7.4:T7.4:d1@k2: environment, left to the owner"])
        self.assertEqual((calls, client.answers), ([], []))

    def test_checks_not_run_reads_the_final_message_simply(self):
        for said in ("I could not run the browser check: ECONNREFUSED 127.0.0.1:55965", "no ejecuté el smoke",
                     "The e2e check was not run because the database is down", "el smoke real queda pendiente"):
            self.assertTrue(healing.checks_not_run(said), said)
        for said in ("Implemented the change; all checks pass.", "No quedan tareas pendientes.", "", "Not run: none"):
            self.assertFalse(healing.checks_not_run(said), said)

    # the final messages of pictures REQ-021 r32 T3.91 (2026-10-31), shortened: a7/a8 could not run the browser suite,
    # a10 ran and passed every check of its own and only said the independent verification was still to come (D-269)
    T391_A7 = ("Pasaron la regresión de conjuntos (11 tipos), la regresión piloto existente (11 tipos), el build de "
               "paquetes con heap limitado, TypeScript estricto y ESLint focalizado.\n\nNo ejecuté `--suite "
               "rectangular-mouse`: la URL de prueba apunta al puerto `55965`, que rechazó la conexión. El smoke real de "
               "navegador y la matriz completa quedan pendientes hasta que el endpoint REQ-021 configurado esté disponible.")
    T391_A8 = ("Pasaron la regresión de conjuntos, la prueba existente de mesas, ESLint, el build de workspaces, TypeScript "
               "estricto y `git diff --check`.\n\nLa suite `rectangular-mouse` no llegó a abrir el navegador: la conexión "
               "a la base de pruebas configurada falló con `ECONNREFUSED 127.0.0.1:55965`. Por eso no pude comprobar que el "
               "canvas renderice el piso; la tarea queda sin verificar independientemente. No hice commit.")
    T391_A10 = ("La prueba `rectangular-mouse` pasó en `/3d` con un Master Designer autenticado y una base aislada: creó una "
                "mesa rectangular de `240×90×75 cm` con 8 sillas, abrió el editor, y undo/redo y la comprobación de una "
                "sola creación pasaron.\n\nTambién pasaron el test de conjunto (11 tipos), el piloto (11 tipos), el build "
                "de workspaces, TypeScript estricto, ESLint focalizado y `git diff --check`. Solo queda modificado ese "
                "harness; no hice commit. **La verificación independiente sigue pendiente; no declaro la tarea "
                "verificada.**")

    def test_checks_not_run_needs_an_explicit_cannot_run_statement(self):
        """T3.91 a10 (D-269): «La verificación independiente sigue pendiente» matched the D-265 «sigue … pendiente»
        pattern and healing left d7 to the owner as if the agent could not run its checks, which had all passed."""
        self.assertTrue(healing.checks_not_run(self.T391_A7))
        self.assertTrue(healing.checks_not_run(self.T391_A8))
        self.assertFalse(healing.checks_not_run(self.T391_A10))
        for said in ("La verificación independiente sigue pendiente.", "Independent verification is still pending.",
                     "Queda pendiente la auditoría independiente.", "The independent review was not run by me.",
                     "All checks passed; the e2e smoke remains pending for the reviewer.",
                     "Pasaron el build y el lint; el smoke queda pendiente para el auditor."):
            self.assertFalse(healing.checks_not_run(said), said)
        for said in ("No se pudo ejecutar el smoke: la base no responde.", "I couldn't run the e2e suite.",
                     "La suite no llegó a abrir el navegador.", "Pasaron los unit tests; no pude ejecutar el smoke.",
                     "Lint passed, but the browser check could not run: connection refused."):
            self.assertTrue(healing.checks_not_run(said), said)

    def test_a_retry_after_passing_checks_is_diagnosed_not_left_to_the_owner(self):
        """With a10's message the decision goes on to the diagnosis instead of «el agente no pudo ejecutar sus checks»."""
        outputs = {"att-10": {"agent": {"status": "completed", "text": self.T391_A10},
                              "snapshot": {"snapshot_sha": "b" * 40, "base_sha": "a" * 40, "changed_paths": ["a.ts"]}}}
        client = Client(dict(decision(), verify_attempt="att-10"))
        client.attempt_output = outputs.get
        calls = []
        result = self.heal(client, lambda *args: calls.append(args))
        self.assertNotIn("proj:REQ-900:r1:T7.4:T7.4:d1@k2: environment, left to the owner", result)
        self.assertFalse(healing.attempt_facts(client, {"verify_attempt": "att-10"})["checks_not_run"])
        self.assertEqual(len(calls), 1)                                       # the diagnosis was asked

    def test_attempt_facts_read_the_decided_attempt(self):
        changed = {"agent": {"status": "completed", "text": "done"},
                   "snapshot": {"snapshot_sha": "b" * 40, "base_sha": "a" * 40, "changed_paths": ["src/a.ts"]}}
        reader = type("Reader", (), {"attempt_output": staticmethod(lambda key: changed)})()
        facts = healing.attempt_facts(reader, {"verify_attempt": "att-9"})
        self.assertEqual((facts["unchanged"], facts["changed"], facts["agent_message"]), (False, 1, "done"))
        self.assertEqual(healing.attempt_facts(reader, {}), {})                     # no attempt named
        self.assertEqual(healing.attempt_facts(object(), {"verify_attempt": "att-9"}), {})   # an older client

    def test_a_plan_defect_goes_to_the_planner_and_stays_for_the_owner(self):
        client = Client(decision())
        diagnose = self.diagnosis(kind="plan", option="retry", confidence="alta", headline="T7.4 no depende de SP-6",
                                  origin="The ledger capture is built in SP-6.", steps=["Make T7.4 depend on T96"])
        self.heal(client, diagnose)
        self.assertEqual(self.heal(client, diagnose), ["proj:REQ-900:r1:T7.4:T7.4:d1@k2: sent to the Planner"])
        self.assertEqual(client.answers, [])
        self.assertIn("blames the plan: T7.4 no depende de SP-6", self.planner[0][2])
        self.assertEqual([(e["kind"], e["key"]) for e in self.escalated],
                         [("decision", "proj:REQ-900:r1:T7.4:T7.4:d1@k2")])

    def test_an_unsure_or_unoffered_choice_and_a_disabled_healer_leave_the_decision(self):
        client = Client(decision())
        diagnose = self.diagnosis(kind="code", option="retry", confidence="baja", headline="?")
        self.heal(client, diagnose)
        self.assertEqual(self.heal(client, diagnose), ["proj:REQ-900:r1:T7.4:T7.4:d1@k2: left to the owner"])
        self.assertEqual(client.answers, [])
        only = decision(signature="sig-2", request="T7.4:d3")
        only["options"] = ["reverify", "stop"]
        self.assertEqual(self.heal(Client(only), diagnose),
                         ["proj:REQ-900:r1:T7.4:T7.4:d3@k2: no retry offered, left to the owner"])
        self.assertEqual(self.heal(Client(only), diagnose), [])
        self.assertEqual([e["request_id"] for e in self.escalated], ["T7.4:d1", "T7.4:d3"])
        FLAGS["healing.model_diagnosis"] = False
        try:
            self.assertEqual(self.heal(Client(decision(signature="sig-3")), diagnose), [])
        finally:
            FLAGS["healing.model_diagnosis"] = True


if __name__ == "__main__":
    unittest.main()
