"""The owner's «No funciona» on a subplan version reaches the Solucionador (bt_durable.rejections) and comes back as a
repaired version «por probar» with his note. Owner, 2026-10-31: «pues mete lo que me dijiste de que lo pase al
solucionador y llena los huecos».

No tmux, no agent and no database: the terminal, the route, the notifications and the client are the Solucionador
suite's fakes; the published versions are rows of the durable composer's store, as in production."""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bt_verification as verification
import test_durable_solver as base
from bt_durable import rejections, solver

SPEC = """# REQ-900 — demo

## Pruebas
| Subplan | Dónde | Cómo | Qué debes ver |
|---|---|---|---|
| SP-1 | Local | Abre /proyectos y pulsa «Nuevo» | El formulario se abre |
"""
PLAN = {"subplans": [{"id": "SP-1", "title": "Proyectos"}, {"id": "SP-2", "title": "Otro"}],
        "tasks": [{"id": "T1", "subplan_id": "SP-1"}, {"id": "T2", "subplan_id": "SP-2"}]}
C1, C2 = "a" * 40, "b" * 40
RECIPE = {"servers": [{"name": "web", "port": 3999, "ready": "/", "open": "/", "run": "npm run dev -- --port {port}"}],
          "auto_login": {"cookie": "sid", "mint": "echo x", "default": "test+admin@x.co",
                         "accounts": ["test+admin@x.co", {"email": "ana@x.co", "role": "viewer"}]}}


class OwnerRejection(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="bt-reject-"))
        os.environ["BITACORA_VERIFY_DIR"] = str(self.tmp / "verify")
        self.addCleanup(os.environ.pop, "BITACORA_VERIFY_DIR", None)
        self.root = self.tmp / "root"
        self.rdir = self.root / "proj" / "requirements" / "REQ-900-x"
        (self.rdir / "plan-revisions").mkdir(parents=True)
        plan = self.rdir / "plan-revisions" / "PLAN.r1.json"
        plan.write_text(json.dumps(PLAN))
        (self.rdir / "RUN.durable-run.json").write_text(json.dumps(
            {"project": "proj", "req": "REQ-900", "revision": 1, "plan_id": "REQ-900", "plan_path": str(plan),
             "plan_sha256": "0" * 64}))
        (self.rdir / "SPEC.md").write_text(SPEC)
        (self.rdir / "PLAN.json").write_text(json.dumps(PLAN))
        (self.root / "proj" / "PENDING.md").write_text("# proj — Pending\n\n## Open\n_None_\n\n## Blocked\n_None_\n\n"
                                                      "## Recently closed\n_None_\n")
        (self.root / "proj" / "verify-servers.json").write_text(json.dumps(RECIPE))
        (self.rdir / "RUN.owner.json").write_text(json.dumps({"backend": "dbos", "run_id": "proj:REQ-900:r1",
                                                              "workflow_id": "bt:proj:REQ-900:r1"}))
        self.store = self.root / ".state" / "durable" / "composition"
        self.store.mkdir(parents=True)
        self.flags = dict(base.FLAGS)
        self.clock = [1_000_000.0]
        self.terminal, self.client, self.activity, self.notified = base.Terminal(), base.Client(), [], []
        for p in (patch("bt_config.get", side_effect=lambda key, default=None: self.flags.get(key, default)),
                  patch("bt_vcs.pull"), patch("bt_runutil.notify", side_effect=lambda t, b: self.notified.append(b))):
            p.start()
            self.addCleanup(p.stop)

    def publish(self, commit=C1):
        """The composer publishes SP-1 at `commit` (a new commit is a new version) and the engine announces it."""
        self.clock[0] += 60
        with contextlib.closing(sqlite3.connect(self.store / "proj-REQ-900-r1-app.db")) as conn, conn:
            conn.execute("CREATE TABLE IF NOT EXISTS versions(plan_id TEXT, subplan_id TEXT, version INTEGER, body TEXT, "
                         "request_sha256 TEXT)")
            conn.execute("INSERT INTO versions VALUES(?,?,?,?,?)", ("REQ-900.bt-r1", "SP-1", 1, json.dumps(
                {"commit": commit, "published_at": f"2026-10-31T{int(self.clock[0]) % 86400:08d}", "subplan_id": "SP-1"}),
                "x"))
        verification.on_projection(self.rdir)

    def solver(self):
        return solver.Solver(self.root, self.client, terminal=self.terminal,
                             route_for=lambda project, avoid: {"provider": "claude", "home": "/acc/a"},
                             notify=lambda title, text: self.notified.append(text),
                             record=lambda rdir, text: self.activity.append(text), now=lambda: self.clock[0],
                             work=self.tmp / "work", integrating=lambda sid: [])

    def state(self):
        return solver.load(self.rdir)

    def owner_triggers(self):
        return {k: v for k, v in (self.state().get("triggers") or {}).items() if v["kind"] == "owner_rejected"}

    def test_a_rejection_starts_the_solver_once_with_what_the_owner_saw_and_how_to_reproduce_it(self):
        self.publish()
        msg = verification.decide("proj", self.rdir, "SP-1", "rejected", "El botón «Nuevo»\nno hace nada")
        self.assertIn("abrí el pendiente P-001", msg)
        self.assertEqual(verification._load(self.rdir)["subplans"]["SP-1"]["pending"], "P-001")
        self.solver().run_pass([])
        self.solver().run_pass([])                                        # once per rejection: no second session
        self.assertEqual(len(self.terminal.started), 1)
        (key, item), = self.owner_triggers().items()
        self.assertEqual(key, verification.rejection_key("SP-1", verification._load(self.rdir)["subplans"]["SP-1"]))
        self.assertEqual((item["subplan"], item["version"], item["commit"], item["pending"], item["status"]),
                         ("SP-1", 1, C1, "P-001", "running"))
        self.assertEqual(item["pages"], ["/proyectos"])
        self.assertEqual(self.state()["tasks"], {"SP-1": 1})             # max_per_task counts the subplan
        session = self.state()["sessions"][0]
        brief = (Path(session["dir"]) / "BRIEF.md").read_text()
        for text in ("The owner rejected SP-1 version 1", C1, "El botón «Nuevo» no hace nada", "P-001",
                     "Abre /proyectos y pulsa «Nuevo»", "El formulario se abre", "`/proyectos`", "verify open REQ-900 SP-1",
                     "verify serve REQ-900 SP-1", "--login", "verify storage-state REQ-900 SP-1", "ana@x.co (viewer)",
                     "test+admin@x.co", "/home/david/dev/pictures/node_modules/playwright",
                     str(self.rdir / "evidence/owner-rejected/SP-1-v1.md"), "asked_owner", key):
            self.assertIn(text, brief)
        prompt = (Path(session["dir"]) / "PROMPT.md").read_text()
        self.assertIn("Known case: the owner rejected a subplan version", prompt)
        self.assertTrue(any("SP-1: rechazaste la versión 1 (P-001)" in line and "no hace nada" in line
                            for line in self.activity), self.activity)

    def test_a_second_rejection_while_the_session_works_goes_to_its_inbox_with_its_own_brief(self):
        self.publish()
        self.client.runs["proj:REQ-900:r1"] = {"run_id": "proj:REQ-900:r1", "workflow_id": "bt:proj:REQ-900:r1",
                                               "workflow_status": "ERROR", "summary": None, "tasks": {}}
        self.solver().run_pass([])                                        # an ERROR run starts the session
        verification.decide("proj", self.rdir, "SP-1", "rejected", "no carga la lista")
        self.solver().run_pass([])
        self.assertEqual(len(self.terminal.started), 1)
        (key, item), = self.owner_triggers().items()
        self.assertEqual(item["status"], "queued")
        session = self.state()["sessions"][0]
        inbox = (Path(session["dir"]) / "inbox.jsonl").read_text()
        self.assertIn(key, inbox)
        extra = Path(session["dir"]) / "BRIEF.SP-1-v1.md"
        self.assertIn("no carga la lista", extra.read_text())
        self.assertIn(str(extra), self.terminal.sent[-1][1])

    def test_an_approval_a_new_version_or_another_note_makes_it_stale(self):
        self.publish()
        verification.decide("proj", self.rdir, "SP-1", "rejected", "falla")
        rejected = rejections.triggers(type("Run", (), {"run_id": "proj:REQ-900:r1"})(), self.rdir)
        self.assertEqual(len(rejected), 1)
        self.assertTrue(rejections.current(self.rdir, rejected[0]))
        verification.decide("proj", self.rdir, "SP-1", "rejected", "falla otra cosa")   # a new rejection, a new key
        self.assertFalse(rejections.current(self.rdir, rejected[0]))
        again = rejections.triggers(type("Run", (), {"run_id": "proj:REQ-900:r1"})(), self.rdir)
        self.assertNotEqual(again[0]["key"], rejected[0]["key"])
        self.publish(C2)                                                  # the repaired version is published
        self.assertFalse(rejections.current(self.rdir, again[0]))
        self.assertEqual(rejections.triggers(type("Run", (), {"run_id": "proj:REQ-900:r1"})(), self.rdir), [])

    def test_the_resolution_is_one_activity_line_and_the_panel_shows_the_solvers_answer(self):
        import bt_page_verification as page
        self.publish()
        verification.decide("proj", self.rdir, "SP-1", "rejected", "falla el botón")
        self.solver().run_pass([])
        session = self.state()["sessions"][0]
        (Path(session["dir"]) / "result.json").write_text(json.dumps({
            "outcome": "asked_owner", "summary": "no lo reproduje", "handled": [],
            "question": "En v1 el botón abre el formulario con test+admin; ¿con qué cuenta lo probaste?"}))
        self.activity.clear()
        self.solver().run_pass([])
        self.assertEqual(len([line for line in self.activity if "Solucionador · te pregunta algo" in line]), 1)
        row = next(r for r in verification.state(self.rdir)["subplans"] if r["id"] == "SP-1")
        self.assertEqual(row["solver"]["status"], "asked_owner")
        html = page.panel({"project": "proj", "rid": "REQ-900", "rdir": self.rdir, "token": "t"}, {"id": "SP-1"})
        self.assertIn("El Solucionador te pregunta algo: En v1 el botón abre el formulario", html)
        self.assertIn("pendiente P-001", html)

    def test_the_repaired_version_is_por_probar_again_with_the_previous_note_and_its_approval_closes_the_p_item(self):
        import bt_page_verification as page
        self.publish(C1)
        verification.decide("proj", self.rdir, "SP-1", "rejected", "falla el botón")
        self.publish(C2)
        self.assertTrue(any("SP-1 versión 2 está lista para probar de nuevo: rechazaste la versión 1 («falla el botón»)"
                            in line for line in (json.loads(x)["text"] for x in (self.rdir / ".planning" / "activity.jsonl")
                                                 .read_text().splitlines())))
        self.assertIn("rechazaste la versión 1 («falla el botón»)", self.notified[-1])
        row = next(r for r in verification.state(self.rdir)["subplans"] if r["id"] == "SP-1")
        self.assertEqual((row["state"], row["retest"]), ("outdated", True))
        html = page.panel({"project": "proj", "rid": "REQ-900", "rdir": self.rdir, "token": "t"}, {"id": "SP-1"})
        self.assertIn('<span class="pp-vstate warn">por probar</span> Versión 2', html)
        self.assertIn("Rechazaste la versión 1: «falla el botón»; comprueba esto en la versión 2.", html)
        self.assertNotIn("vuelve a probarla", html)
        self.assertIn("por probar", page.run_card("proj", "REQ-900", self.rdir))
        verification.decide("proj", self.rdir, "SP-1", "approved")
        pending = (self.root / "proj" / "PENDING.md").read_text()
        closed = pending.split("## Recently closed", 1)[1]
        self.assertIn("P-001", closed)
        self.assertIn("the owner approved SP-1 v2", closed)
        self.assertNotIn("P-001", pending.split("## Recently closed", 1)[0])

    def test_the_owner_is_told_the_solver_takes_it_only_while_the_solver_is_on(self):
        self.publish()
        msg = verification.decide("proj", self.rdir, "SP-1", "rejected", "falla")
        self.assertIn("se lo paso al Solucionador", msg)
        self.assertIn("«por probar» con tu nota", msg)
        self.flags["solver.enabled"] = False
        msg = verification.decide("proj", self.rdir, "SP-1", "rejected", "falla otra vez")   # nobody takes it: as before
        self.assertIn("el requisito sigue por verificar", msg)
        self.assertEqual(self.solver().run_pass([]), [])

    def test_the_cli_writes_a_signed_in_playwright_storage_state_without_printing_the_token(self):
        import bt_cli_verify
        out = self.tmp / "s" / "state.json"
        minted = {"ok": True, "token": "T" * 30, "cookie": "sid", "account": "ana@x.co", "url": "http://localhost:3999/"}
        args = argparse.Namespace(action="storage-state", subplan="SP-1", account="ana@x.co", out=str(out))
        with patch("bt_verify_servers.mint_session", return_value=minted) as mint, \
                patch("builtins.print") as said:
            self.assertEqual(bt_cli_verify.servers(args, self.root, "proj", self.rdir), 0)
        mint.assert_called_once_with(self.root, "proj", self.rdir, "SP-1", "ana@x.co")
        data = json.loads(out.read_text())
        self.assertEqual({(c["name"], c["value"], c["domain"]) for c in data["cookies"]},
                         {("sid", "T" * 30, "localhost"), ("sid", "T" * 30, "127.0.0.1")})
        self.assertEqual(out.stat().st_mode & 0o777, 0o600)
        self.assertNotIn("T" * 30, " ".join(str(c) for c in said.call_args_list))

    def test_the_cli_serves_the_version_and_waits_until_it_answers(self):
        import bt_cli_verify
        args = argparse.Namespace(action="serve", subplan="SP-1", login=True, timeout=60)
        states = iter([{"state": "preparing"}, {"state": "ready", "url": "http://localhost:3999/"}])
        with patch("bt_verify_servers.start", return_value={"ok": True, "message": "Arrancando", "url": ""}) as start, \
                patch("bt_verify_servers.status", side_effect=lambda *a: next(states)), patch("builtins.print"):
            self.assertEqual(bt_cli_verify.servers(args, self.root, "proj", self.rdir, sleep=lambda s: None), 0)
        start.assert_called_once_with(self.root, "proj", self.rdir, "SP-1", login=True)


if __name__ == "__main__":
    unittest.main()
