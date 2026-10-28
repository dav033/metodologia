import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_verification as v

SPEC = """# REQ-9 — demo

## Pruebas
| Subplan | Dónde | Cómo | Qué debes ver |
|---|---|---|---|
| SP-1 | Local | `npm run dev` y abre http://localhost:3000 | La página carga |
| SP-1 | Producción | https://demo.example.com | El mismo catálogo |
| SP-2 | GitHub Packages | `npm view @x/ui` | La versión 1.0.0 |
| SP-3 | none | Es interno | — |

## Otra cosa
texto
"""
PLAN = {"subplans": [{"id": "SP-1", "title": "One", "produces": [{"contract": "kit", "version": 1}]},
                     {"id": "SP-2", "title": "Two", "consumes": [{"contract": "kit", "version": 1}]},
                     {"id": "SP-3", "title": "Three"}],
        "tasks": [{"id": "T1", "subplan_id": "SP-1"}, {"id": "T2", "subplan_id": "SP-2", "after": ["T1"]},
                  {"id": "T3", "subplan_id": "SP-3"}]}
COMMIT = "a" * 40


def git(repo, *args):
    env = {k: val for k, val in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env, check=True).stdout.strip()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name) / "proj" / "requirements" / "REQ-009-demo"
        self.rdir.mkdir(parents=True)
        (self.rdir / "SPEC.md").write_text(SPEC, encoding="utf-8")
        (self.rdir / "PLAN.json").write_text(json.dumps(PLAN), encoding="utf-8")

    def projection(self, **versions):
        rows = [{"id": s["id"], "status": "published" if s["id"] in versions else "pending",
                 "version": versions.get(s["id"], (None, None))[0], "commit": versions.get(s["id"], (None, None))[1]}
                for s in PLAN["subplans"]]
        (self.rdir / v.PROJECTION).write_text(json.dumps({"subplans": rows}), encoding="utf-8")



class Verification(Base):
    def test_spec_rows_are_read_with_their_place_kind(self):
        rows = v.tests(self.rdir)
        self.assertEqual([(r["subplans"], r["kind"]) for r in rows],
                         [(["SP-1"], "local"), (["SP-1"], "production"), (["SP-2"], "external"), (["SP-3"], "none")])
        self.assertEqual(rows[0]["how"], "`npm run dev` y abre http://localhost:3000")
        self.assertEqual(len(v.tests_for(self.rdir, "SP-1")), 2)
        self.assertTrue(v.missing(self.rdir, "SP-9"))
        self.assertFalse(v.missing(self.rdir, "SP-3"))

    def test_a_plan_wide_row_does_not_stand_in_for_a_subplan_and_none_needs_a_reason(self):
        (self.rdir / "SPEC.md").write_text("## Pruebas\n| Subplan | Where | How | Expect |\n|---|---|---|---|\n"
                                           "| all | Local | run it | ok |\n| SP-2 | none |  |  |\n| SP-3 | none | internal only |  |\n")
        self.assertTrue(v.missing(self.rdir, "SP-1"))          # `all` supplements, it never replaces a subplan's own row
        self.assertTrue(v.missing(self.rdir, "SP-2"))          # `none` without a reason
        self.assertFalse(v.missing(self.rdir, "SP-3"))
        self.assertEqual(len(v.tests_for(self.rdir, "SP-1")), 1)

    def test_runs_without_subplans_in_their_projection_are_not_gated(self):
        (self.rdir / v.PROJECTION).write_text(json.dumps({"tasks": []}))
        self.assertFalse(v.applies(self.rdir))
        self.assertEqual(v.gate(self.rdir), [])

    def test_a_run_planned_before_this_feature_is_never_gated_even_when_it_reports_subplans(self):
        (self.rdir / "SPEC.md").write_text("# REQ-9\n\nno pruebas here\n")
        self.projection(**{"SP-1": (1, COMMIT)})
        self.assertFalse(v.applies(self.rdir))
        self.assertEqual(v.gate(self.rdir), [])

    def test_once_gated_the_gate_cannot_fail_open(self):
        self.projection(**{"SP-1": (1, COMMIT)})
        v.on_projection(self.rdir)
        self.assertTrue(v._load(self.rdir)["gated"])
        (self.rdir / v.PROJECTION).write_text(json.dumps({"tasks": []}))          # a projection written without subplans
        self.assertTrue(v.applies(self.rdir))
        self.assertTrue(v.gate(self.rdir))
        (self.rdir / "PLAN.json").write_text("{ broken")                             # a PLAN.json caught mid-edit
        self.assertEqual(v.gate(self.rdir), ["no puedo leer los subplanes del plan; reintenta en unos segundos"])

    def test_a_malformed_published_version_is_ignored(self):
        self.projection(**{"SP-1": ("../x", COMMIT), "SP-2": (1, "not-a-sha")})
        self.assertEqual(v.published(self.rdir), {})
        self.assertEqual({r["state"] for r in v.state(self.rdir)["subplans"]}, {"waiting"})

    def test_a_failed_notification_is_retried_and_an_unchanged_projection_writes_nothing(self):
        self.projection(**{"SP-1": (1, COMMIT)})
        with patch("bt_runutil.notify", side_effect=OSError("no bus")):
            self.assertEqual(v.on_projection(self.rdir), [])
        self.assertEqual(v._load(self.rdir)["seen"], {})                           # not marked: the next projection retries
        with patch("bt_runutil.notify"):
            self.assertEqual(v.on_projection(self.rdir), ["SP-1"])
            before = (self.rdir / v.DIR / v.FILE).stat().st_mtime_ns
            self.assertEqual(v.on_projection(self.rdir), [])
        self.assertEqual((self.rdir / v.DIR / v.FILE).stat().st_mtime_ns, before)

    def test_a_subplan_goes_waiting_to_test_approved_and_outdated_when_republished(self):
        self.projection()
        self.assertEqual({r["state"] for r in v.state(self.rdir)["subplans"]}, {"waiting"})
        self.assertEqual(len(v.gate(self.rdir)), 3)
        self.projection(**{"SP-1": (1, COMMIT)})
        self.assertEqual(v.state(self.rdir)["subplans"][0]["state"], "to_test")
        self.assertIn("todavía se está construyendo", v.decide("proj", self.rdir, "SP-2", "approved"))
        self.assertIn("aprobado", v.decide("proj", self.rdir, "SP-1", "approved"))
        self.assertEqual(v.state(self.rdir)["subplans"][0]["state"], "approved")
        self.projection(**{"SP-1": (2, "b" * 40)})                     # the engine published a newer version
        self.assertEqual(v.state(self.rdir)["subplans"][0]["state"], "outdated")
        self.assertIn("SP-1: cambió tras tu decisión", v.gate(self.rdir))

    def test_rejecting_needs_a_note_and_is_kept_pinned_to_the_version(self):
        self.projection(**{"SP-1": (1, COMMIT)})
        self.assertIn("escribe qué falló", v.decide("proj", self.rdir, "SP-1", "rejected", "  "))
        v.decide("proj", self.rdir, "SP-1", "rejected", "el botón no responde")
        row = v.state(self.rdir)["subplans"][0]
        self.assertEqual((row["state"], row["decision"]["note"]), ("rejected", "el botón no responde"))
        v.decide("proj", self.rdir, "SP-1", "approved")                     # changing your mind on the same version is allowed
        self.assertEqual(v.state(self.rdir)["subplans"][0]["state"], "approved")

    def test_a_rejection_is_filed_as_a_pending_item_when_the_project_has_one(self):
        pdir = self.rdir.parents[1]
        (pdir / "PENDING.md").write_text("# proj — Pending\n\n## Open\n- P-007 · old · urgency: low · complexity: S · added 2026-10-01 · x\n\n## Closed\n")
        self.projection(**{"SP-1": (1, COMMIT)})
        with patch("bt_vcs.pull"):
            msg = v.decide("proj", self.rdir, "SP-1", "rejected", "el botón\nno responde")
        self.assertIn("abrí el pendiente P-008", msg)
        text = (pdir / "PENDING.md").read_text()
        self.assertIn("P-008 · The owner rejected SP-1 v1 of REQ-009 after trying it: el botón no responde", text)
        self.assertIn("P-007", text)

    def test_the_gate_is_empty_only_when_every_subplan_is_approved(self):
        self.projection(**{"SP-1": (1, COMMIT), "SP-2": (1, COMMIT), "SP-3": (1, COMMIT)})
        for sid in ("SP-1", "SP-2"):
            v.decide("proj", self.rdir, sid, "approved")
        self.assertEqual(v.gate(self.rdir), ["SP-3: por probar"])
        self.assertIn("Todos los subplanes están aprobados", v.decide("proj", self.rdir, "SP-3", "approved"))
        self.assertEqual(v.gate(self.rdir), [])

    def test_dependents_come_from_task_edges_and_consumed_contracts(self):
        self.assertEqual(v.dependents(self.rdir, "SP-1"), ["SP-2"])
        self.assertEqual(v.dependents(self.rdir, "SP-3"), [])

    def test_each_new_published_version_is_announced_once(self):
        self.projection(**{"SP-1": (1, COMMIT)})
        with patch("bt_runutil.notify") as notify:
            self.assertEqual(v.on_projection(self.rdir), ["SP-1"])
            self.assertEqual(v.on_projection(self.rdir), [])
            self.projection(**{"SP-1": (2, "b" * 40)})
            self.assertEqual(v.on_projection(self.rdir), ["SP-1"])
        self.assertEqual(notify.call_count, 2)
        self.assertIn("REQ-009", notify.call_args[0][1])

    def test_open_local_creates_a_detached_worktree_of_the_published_commit_and_closes_it(self):
        repo = Path(self.tmp.name) / "repo"
        repo.mkdir()
        git(repo, "init", "-q")
        (repo / "a.txt").write_text("one")
        git(repo, "add", ".")
        git(repo, "commit", "-qm", "one")
        base = git(repo, "rev-parse", "HEAD")
        (repo / "a.txt").write_text("two")
        git(repo, "commit", "-qam", "two")
        commit = git(repo, "rev-parse", "HEAD")
        git(repo, "update-ref", "refs/m3/line/run/app/SP-1", commit)
        git(repo, "update-ref", "refs/m3/line/run/app/SP-1-base", base)
        git(repo, "checkout", "-q", base)                                   # the main checkout is NOT at the published commit
        self.projection(**{"SP-1": (1, commit)})
        os.environ["BITACORA_VERIFY_DIR"] = str(Path(self.tmp.name) / "verify")
        self.addCleanup(os.environ.pop, "BITACORA_VERIFY_DIR", None)
        with patch("bt_workspace.repos", return_value={"app": repo}):
            target, msg = v.open_local(Path(self.tmp.name), "proj", self.rdir, "SP-1")
            self.assertEqual((target / "a.txt").read_text(), "two")
            self.assertEqual(git(target, "rev-parse", "HEAD"), commit)
            self.assertEqual(v.open_local(Path(self.tmp.name), "proj", self.rdir, "SP-1")[0], target)   # idempotent
            self.assertEqual(v.revert_command(Path(self.tmp.name), "proj", self.rdir, "SP-1"),
                             f"git -C {repo} revert --no-commit {base}..{commit}")
            (target / "scratch.txt").write_text("my edit while trying")
            self.assertIn("cambios sin guardar", v.close_local(Path(self.tmp.name), "proj", self.rdir, "SP-1"))
            self.assertTrue((target / "scratch.txt").exists())                   # nothing was discarded
            (target / "scratch.txt").unlink()
            self.assertEqual(v.close_local(Path(self.tmp.name), "proj", self.rdir, "SP-1"), "Cerrado.")
            target2, _ = v.open_local(Path(self.tmp.name), "proj", self.rdir, "SP-1")
            import shutil
            shutil.rmtree(target2)                                                 # deleted by hand: opening again still works
            self.assertEqual(v.open_local(Path(self.tmp.name), "proj", self.rdir, "SP-1")[0], target2)
            v.close_local(Path(self.tmp.name), "proj", self.rdir, "SP-1")
        self.assertFalse(target.exists())
        self.assertEqual(git(repo, "rev-parse", "HEAD"), base)              # the repo's own checkout never moved

    def test_open_local_refuses_a_subplan_with_no_published_version(self):
        self.projection()
        target, msg = v.open_local(Path(self.tmp.name), "proj", self.rdir, "SP-1")
        self.assertIsNone(target)
        self.assertIn("todavía no tiene una versión publicada", msg)


class VerificationWeb(Base):
    """Page pieces, the server action, the merge gate and the CLI, on the same fixture."""

    def ctx(self):
        return {"project": "proj", "rid": "REQ-009", "rdir": self.rdir, "token": "tok", "root": Path(self.tmp.name),
                "opts": {"lang": "en"}}

    def test_local_test_port_is_visible_without_claiming_the_app_is_running(self):
        import bt_page_verification as page
        local = {"kind": "local", "where": "", "how": "Open http://localhost:3000/3d", "expect": ""}
        html = page._where([local])
        self.assertIn("Puerto indicado para la prueba: 3000", html)
        self.assertIn("Abrir la copia no inicia la aplicación", html)
        self.assertIn("ssh -L 3000:127.0.0.1:3000 usuario@servidor", html)
        no_url = {**local, "how": "Run a command"}
        self.assertNotIn("Puerto indicado", page._where([no_url]))
        self.assertNotIn("Puerto indicado", page._where([{**local, "kind": "external"}]))

    def test_the_tab_explains_where_to_try_a_subplan_before_and_after_it_is_built(self):
        import bt_page_verification as page
        plan = page.panel(self.ctx(), {"id": "SP-1"})                        # no run yet: planning phase
        self.assertIn("Cuando este subplan termine de construirse", plan)
        self.assertIn("En local", plan)
        self.assertIn("Fuera de tus servidores", page.panel(self.ctx(), {"id": "SP-2"}))
        self.assertIn('<a href="https://demo.example.com"', page.panel(self.ctx(), {"id": "SP-1"}))
        self.assertIn("Falta «cómo probarlo»", page.panel(self.ctx(), {"id": "SP-9"}))
        self.projection()
        self.assertIn("se está construyendo", page.panel(self.ctx(), {"id": "SP-1"}))

    def test_a_published_version_offers_open_approve_reject_and_the_way_back(self):
        import bt_page_verification as page
        self.projection(**{"SP-1": (3, COMMIT)})
        html = page.panel(self.ctx(), {"id": "SP-1"})
        for expected in ("por probar", "Versión 3", COMMIT[:10], "Abrir esta versión en local", "verify-approve",
                         "verify-reject", "Cómo deshacer este subplan", "SP-2 se construye sobre este subplan"):
            self.assertIn(expected, html)
        v.decide("proj", self.rdir, "SP-1", "rejected", "falla el botón")
        self.assertIn("Tu nota: «falla el botón»", page.panel(self.ctx(), {"id": "SP-1"}))
        self.projection(**{"SP-1": (4, "b" * 40)})
        self.assertIn("vuelve a probarla", page.panel(self.ctx(), {"id": "SP-1"}))

    def test_run_card_chip_and_tab_label_follow_the_states(self):
        import bt_page_verification as page
        self.assertEqual(page.run_card("proj", "REQ-009", self.rdir) + page.chip(self.rdir), "")     # not a reporting run
        self.projection(**{"SP-1": (1, COMMIT)})
        card = page.run_card("proj", "REQ-009", self.rdir)
        self.assertIn("(0/3)", card)
        self.assertIn("view=verify&amp;sp=SP-1", card)
        self.assertIn("por probar 1", page.chip(self.rdir))
        self.assertEqual(page.tab_label(self.rdir), "Probar · 0/3")
        v.decide("proj", self.rdir, "SP-1", "approved")
        self.projection(**{"SP-1": (1, COMMIT), "SP-2": (1, COMMIT), "SP-3": (1, COMMIT)})
        for sid in ("SP-2", "SP-3"):
            v.decide("proj", self.rdir, sid, "approved")
        self.assertIn("ya puedes fusionar", page.run_card("proj", "REQ-009", self.rdir))
        self.assertEqual(page.tab_label(self.rdir), "Probar ✓")

    def test_the_review_merge_refuses_until_every_subplan_is_approved(self):
        import bt_review
        self.projection(**{"SP-1": (1, COMMIT)})
        out = bt_review.merge("proj", self.rdir, False)
        self.assertEqual(len(out), 1)
        self.assertIn("No fusioné nada: faltan subplanes por aprobar", out[0])
        self.assertIn("SP-2: se está construyendo", out[0])

    def test_the_server_action_decides_and_only_accepts_a_valid_subplan(self):
        import bt_server
        self.projection(**{"SP-1": (1, COMMIT)})
        with patch.object(bt_server, "commit") as commit, patch.object(bt_server, "ROOT", Path(self.tmp.name)):
            go = lambda action, **form: bt_server.Handler.verify_post(object(), "proj", "REQ-009", self.rdir, action, form, "/p/proj/req/REQ-009")
            url = go("verify-approve", anchor="SP-1")
            self.assertIn("view=verify&sp=SP-1", url)
            self.assertIn("SP-1%20aprobado", url)
            self.assertEqual(v.state(self.rdir)["subplans"][0]["state"], "approved")
            self.assertIn("Para%20rechazar%20escribe", go("verify-reject", anchor="SP-1", comments=" "))
            self.assertIn("Subplan%20no%20v%C3%A1lido", go("verify-approve", anchor="../x"))
        self.assertEqual(commit.call_count, 2)

    def test_now_page_lists_subplans_waiting_for_the_owner(self):
        import bt_page_now
        items = [{"project": "proj", "req": "REQ-009", "subplans": ["SP-1", "SP-2"], "approved": 1, "total": 3}]
        frag = bt_page_now.fragments([], [], items)
        self.assertIn("SP-1, SP-2", frag["verify"])
        self.assertIn("por probar", frag["bar"])
        self.assertEqual(bt_page_now.fragments([], [], [])["bar"], "")
        self.assertIn("Subplanes por probar", bt_page_now.now_page([], [], items))

    def test_the_cli_needs_the_owner_to_decide_and_prints_the_blocking_list(self):
        import argparse
        import io
        from contextlib import redirect_stdout

        import bt_cli_verify
        root = Path(self.tmp.name)
        self.projection(**{"SP-1": (1, COMMIT)})
        ns = lambda **kw: argparse.Namespace(**{"action": "status", "req": "REQ-009", "subplan": None, "note": "", "by": None, **kw})
        with self.assertRaises(SystemExit):
            bt_cli_verify.dispatch(ns(action="approve", subplan="SP-1"), root, "proj")
        out = io.StringIO()
        with redirect_stdout(out):
            bt_cli_verify.dispatch(ns(), root, "proj")
        self.assertIn("SP-2: se está construyendo", json.loads(out.getvalue())["blocking"])
        with redirect_stdout(io.StringIO()):
            bt_cli_verify.dispatch(ns(action="approve", subplan="SP-1", by="owner"), root, "proj")
        self.assertEqual(v.state(self.rdir)["subplans"][0]["state"], "approved")


if __name__ == "__main__":
    unittest.main()
