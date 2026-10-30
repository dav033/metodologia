"""«Probar esto» on a decision that waits for manual evidence (owner, 2026-10-30, pictures REQ-021 T10.5)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_durable_panel
import bt_page_manual_check as card
import bt_plans_api as api
import bt_verify_guide as guides
import bt_verify_servers as servers

ATTEMPT = "proj-REQ-021-r25-T10.5-a1-098ef7ce"
CHECK = ("A separate manual local observation using the already configured AI provider confirms an English conversation "
         "receives an English reply and a Spanish conversation a Spanish reply.")
DECISION = {"id": "T10.5:d1@k1", "request_id": "T10.5:d1", "task_id": "T10.5", "attempt": ATTEMPT,
            "failure": {"code": "MANUAL_EVIDENCE_REQUIRED", "failure_class": "product_decision",
                        "summary": "manual evidence is missing for: " + CHECK},
            "options": ["reverify", "retry", "retry_with_note", "retry_other_route", "stop"], "reason": "x", "seq": 1}
PLAN = {"subplans": [{"id": "SP-10"}], "tasks": [{"id": "T10.5", "subplan_id": "SP-10", "verification": [
    {"type": "command", "value": "npm run idioma:test", "purpose": "screens"},
    {"type": "manual", "value": "Owner observes the configured local chat in English and Spanish", "purpose": CHECK,
     "expected": CHECK}]}]}
SPEC = ("## Pruebas\n\n| Subplan | Where | How | Expect |\n|---|---|---|---|\n"
        "| SP-1 | Local | 1) `npm run cuentas:sembrar-prueba` creates designer-plus@prueba.local. | 1) ok |\n"
        "| SP-10 | Local | Select English as Designer Plus and visit home. Ask the chat in English for a decoration, then "
        "repeat in Spanish. Run `npm run idioma:test`; record the configured provider. | English replies. |\n")


class Wiring(unittest.TestCase):
    def test_only_a_manual_evidence_decision_that_can_be_reverified_gets_the_block(self):
        self.assertEqual(bt_durable_panel.manual_check(DECISION),
                         {"task": "T10.5", "request_id": "T10.5:d1", "attempt": ATTEMPT,
                          "check": "manual evidence is missing for: " + CHECK})
        bound = bt_durable_panel.manual_check({**DECISION, "verify_attempt": "proj-REQ-021-r25-T10.5-a0-1111"})
        self.assertEqual(bound["attempt"], "proj-REQ-021-r25-T10.5-a0-1111")      # the receipt's attempt wins
        self.assertEqual(bt_durable_panel.manual_check({**DECISION, "failure": {"code": "CRITERION_MANUAL"}})["task"], "T10.5")
        self.assertIsNone(bt_durable_panel.manual_check({**DECISION, "failure": {"code": "CHECK_FAILED"}}))
        self.assertIsNone(bt_durable_panel.manual_check({**DECISION, "options": ["retry", "stop"]}))

    def test_the_card_starts_the_snapshot_and_answers_with_works_or_does_not_work(self):
        root = Path(tempfile.mkdtemp(prefix="bt-manual-card-"))
        rdir = root / "proj" / "requirements" / "REQ-021-x"
        rdir.mkdir(parents=True)
        (rdir / "PLAN.json").write_text(json.dumps(PLAN))
        (rdir / "SPEC.md").write_text(SPEC)
        target = {"id": "T10.5", "kind": "task", "commit": "b" * 40, "attempt": ATTEMPT, "decision": DECISION["id"],
                  "version": "a1-098ef7ce"}
        decision = {**DECISION, "manual": bt_durable_panel.manual_check(DECISION)}
        with patch.object(servers, "recipe", return_value={"servers": [{"name": "web", "port": 3000, "run": "x"}]}), \
                patch.object(servers, "task_target", return_value=target), \
                patch.object(servers, "status", return_value={"state": "stopped", "url": "", "servers": {}, "log": ""}), \
                patch.object(servers, "planned", return_value={"url": "http://localhost:3004/", "ports": {"web": 3004}}):
            html = card.block(root, "proj", "REQ-021", rdir, decision, "/plans/proj/REQ-021", "tok")
        self.assertIn('<a class="pp-vurl" href="http://localhost:3004/"', html)
        self.assertIn('action="/p/proj/req/REQ-021/verify-run"', html)
        self.assertIn('name="anchor" value="T10.5"', html)
        self.assertIn("Probar esto ↗", html)
        self.assertIn('action="/plans/proj/REQ-021/attest"', html)
        self.assertIn('name="request" value="T10.5:d1"', html)                  # the request attest answers, no round
        self.assertIn(">Funciona</button>", html)
        self.assertIn('name="option" value="retry_with_note"', html)
        self.assertIn('name="request" value="T10.5:d1@k1"', html)              # «No funciona»: the decision itself
        self.assertIn(">No funciona</button>", html)
        self.assertIn("I&#x27;m planning a birthday party", html)                # what to type in English
        self.assertIn("¿Qué decoración con globos", html)                        # and in Spanish
        self.assertIn("designer-plus@prueba.local", html)
        self.assertIn("bbbbbbbbbb", html)
        with patch.object(servers, "recipe", return_value={"servers": [{"name": "web", "port": 3000, "run": "x"}]}), \
                patch.object(servers, "task_target", return_value=None):
            self.assertIn("no está disponible", card.block(root, "proj", "REQ-021", rdir, decision, "/plans/x/y", "t"))
        self.assertEqual(card.block(root, "proj", "REQ-021", rdir, {**DECISION, "manual": None}, "/plans/x/y", "t"), "")


class Guide(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="bt-manual-guide-"))
        self.rdir = self.root / "proj" / "requirements" / "REQ-021-x"
        self.rdir.mkdir(parents=True)
        (self.rdir / "PLAN.json").write_text(json.dumps(PLAN))
        (self.rdir / "SPEC.md").write_text(SPEC)

    def test_a_language_pair_check_becomes_a_message_in_each_language_and_an_evidence_prefill(self):
        env = self.root / "app.env"
        env.write_text("IA_PROVEEDOR=gemini\nGEMINI_CHAT_MODEL=gemini-x\nGEMINI_API_KEY=secret-value-123\n"
                       "DATABASE_URL=postgresql://u:pw@h/db\n")
        g = guides.manual(self.root, "proj", self.rdir, "T10.5", url="http://localhost:3004/",
                          recipe={"env_file": str(env)}, attempt=ATTEMPT, commit="c" * 40)
        texts = [s["do"] for s in g["steps"]]
        self.assertEqual(texts[0], "Abre http://localhost:3004/ e inicia sesión como designer-plus@prueba.local.")
        self.assertEqual(texts[1], "Ask the chat in English for a decoration, then repeat in Spanish.")   # not the command
        self.assertIn(guides.SAY["en"], texts[2])
        self.assertIn(guides.SAY["es"], texts[3])
        self.assertEqual([s["expect"] for s in g["steps"][2:4]], ["La respuesta llega en inglés.", "La respuesta llega en español."])
        self.assertEqual(g["provider"], "GEMINI_CHAT_MODEL=gemini-x, IA_PROVEEDOR=gemini")
        self.assertNotIn("secret-value", json.dumps(g))
        self.assertNotIn("pw@", json.dumps(g))
        self.assertIn(ATTEMPT, g["prefill"])
        self.assertIn("inglés recibió respuesta en inglés", g["prefill"])
        self.assertEqual(guides.manual(self.root, "proj", self.rdir, "T10.5"), guides.manual(self.root, "proj", self.rdir, "T10.5"))


class Answers(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="bt-manual-attest-"))
        (self.root / "proj" / "requirements" / "REQ-021-x").mkdir(parents=True)
        self.decision = {**DECISION, "manual": bt_durable_panel.manual_check(DECISION)}

    def test_works_seals_the_owners_evidence_through_bt_durable_attest(self):
        done = subprocess.CompletedProcess([], 0, '{\n "receipts": []\n}', "")
        with patch.object(bt_durable_panel, "owned", return_value=True), \
                patch.object(bt_durable_panel, "decisions", return_value=[self.decision]), \
                patch.object(bt_durable_panel, "cli", return_value=["bt-durable"]), \
                patch.object(api.subprocess, "run", return_value=done) as run:
            said = api.attest(self.root, "proj", "REQ-021", "T10.5", "T10.5:d1", "Probé el chat: inglés y español bien.")
        args = run.call_args.args[0]
        self.assertEqual(args[:8], ["bt-durable", "attest", "proj", "REQ-021", "T10.5", "--request", "T10.5:d1", "--evidence"])
        self.assertEqual(args[-2:], ["--by", "owner"])
        self.assertIn("se vuelve a verificar", said)

    def test_works_refuses_an_empty_note_or_a_decision_that_is_not_open(self):
        with patch.object(bt_durable_panel, "owned", return_value=True), \
                patch.object(bt_durable_panel, "decisions", return_value=[self.decision]):
            with self.assertRaises(api.PlanError):
                api.attest(self.root, "proj", "REQ-021", "T10.5", "T10.5:d1", "ok")
            with self.assertRaises(api.PlanError):
                api.attest(self.root, "proj", "REQ-021", "T10.5", "T10.5:d9", "Probé el chat: inglés y español bien.")

    def test_does_not_work_answers_retry_with_note_with_what_failed(self):
        with patch.object(bt_durable_panel, "owned", return_value=True), \
                patch.object(bt_durable_panel, "dispatch", return_value={"messages": ["enviado"]}) as sent:
            api.decide(self.root, "proj", "REQ-021", "T10.5:d1@k1", "retry_with_note", "En español respondió en inglés.")
        params = sent.call_args.args[4]
        self.assertEqual((params["option"], params["reason"]), ("retry_with_note", "En español respondió en inglés."))


class TaskSnapshot(unittest.TestCase):
    def test_a_task_target_is_the_snapshot_its_decision_names(self):
        repo = Path(tempfile.mkdtemp(prefix="bt-manual-repo-"))
        git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, check=True).stdout.strip()  # noqa: E731
        git("init", "-q")
        git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", f"m3 snapshot {ATTEMPT}")
        sha = git("rev-parse", "HEAD")
        git("update-ref", "refs/m3/handoff/x-T10-5-a1", sha)
        import bt_workspace
        with patch.object(bt_workspace, "repos", return_value={"app": repo}), \
                patch.object(bt_durable_panel, "decisions", return_value=[{**DECISION, "manual": bt_durable_panel.manual_check(DECISION)}]):
            found = servers.task_target(Path("/r"), "proj", Path("/r/proj/requirements/REQ-021-x"), "T10.5")
        self.assertEqual((found["commit"], found["version"], found["kind"]), (sha, "a1-098ef7ce", "task"))
        self.assertEqual(servers.slug("T10.5", found["version"]), "T10.5-a1-098ef7ce")
        self.assertEqual(servers.slug("SP-8", 1), "SP-8-v1")
        self.assertEqual(servers.session_name("proj", Path("/r/REQ-021-x"), "T10.5", "a1-098ef7ce"), "bv-proj-REQ-021-T10_5-a1-098ef7ce")


if __name__ == "__main__":
    unittest.main()
