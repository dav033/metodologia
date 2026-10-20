"""Plans view: pages, JSON API, SSE live updates, CSRF, cancel / delete / restore (temp root, ephemeral port)."""
from __future__ import annotations

import http.client
import json
from urllib.parse import unquote
import sys
import tempfile
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import bt_core  # noqa: E402
import bt_plans_api as api  # noqa: E402
import bt_server  # noqa: E402

PLAN = {"schema_version": "1.0.0", "plan_id": "REQ-001", "revision": 1, "spec_ref": "SPEC.md",
        "milestones": [{"id": "M1", "title": "First", "acceptance_criteria": ["a"]}],
        "tasks": [{"id": "T1", "milestone_id": "M1", "title": "Do <b>one</b>", "after": [], "complexity": "low"},
                  {"id": "T2", "milestone_id": "M1", "title": "Do two", "after": ["T1"], "complexity": "extreme"}]}


def run_json(status="running", t1="in_progress"):
    return {"status": status, "heartbeat": {"at": "2026-10-18T10:00:00"}, "tasks": [
        {"id": "T1", "status": t1, "attempts": 1}, {"id": "T2", "status": "todo", "attempts": 0}],
        "log": [{"task": "T1", "agent": "claude", "model": "sonnet", "profile": "work", "effort": "high",
                 "result": "blocked", "at": "2026-10-18T09:00:00", "seconds": 5}]}


class PlansBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        for target, attr in ((bt_server, "ROOT"), (bt_core, "ROOT")):
            p = patch.object(target, attr, self.root)
            p.start()
            self.addCleanup(p.stop)
        for target in (bt_server, bt_core):
            p = patch.object(target, "STATE", self.root / ".state")
            p.start()
            self.addCleanup(p.stop)
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), bt_server.Handler)
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.addCleanup(self.httpd.server_close)
        self.addCleanup(self.httpd.shutdown)

    def req(self, project="demo", n=1, status="approved", run=None):
        rdir = self.root / project / "requirements" / f"REQ-{n:03d}-demo"
        rdir.mkdir(parents=True, exist_ok=True)
        (rdir / "SPEC.md").write_text(f"---\nstatus: ready\n---\n# Spec — REQ-{n:03d} — Title {n}\n", encoding="utf-8")
        (rdir / "PLAN.md").write_text(f"---\nstatus: {status}\n---\n# Plan\n", encoding="utf-8")
        (rdir / "PLAN.json").write_text(json.dumps({**PLAN, "plan_id": f"REQ-{n:03d}"}), encoding="utf-8")
        if run:
            (rdir / "RUN.json").write_text(json.dumps(run), encoding="utf-8")
        return rdir

    def get(self, path, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        c.request("GET", path, headers=headers or {})
        r = c.getresponse()
        return r.status, r.read().decode(), r

    def post(self, path, form, origin=True):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        h = {"Content-Type": "application/x-www-form-urlencoded"}
        if origin:
            h["Origin"] = f"http://127.0.0.1:{self.port}"
        c.request("POST", path, urlencode(form), h)
        r = c.getresponse()
        r.read()
        return r.status, r.getheader("Location")

    def tok(self):
        return bt_server.token()


class PageTests(PlansBase):
    def test_two_active_plans_listed_together_and_escaped(self):
        self.req(n=1, run=run_json())
        self.req(n=2, run=run_json())
        self.req(n=3)
        status, html, _ = self.get("/plans")
        self.assertEqual(status, 200)
        self.assertEqual(html.count('class="card'), 1)  # one card per project
        self.assertIn("3 planes · 3 abiertos · <span class=\"live\">2 en ejecución</span>", html)
        self.assertIn("/plans/demo/REQ-003", html)
        _, only, _ = self.get("/plans?filter=active")
        self.assertNotIn("/plans/demo/REQ-003", only)
        self.assertIn("/plans/demo/REQ-002", only)

    def test_detail_shows_tasks_models_difficulty_and_no_edit_forms(self):
        self.req(run=run_json())
        status, html, _ = self.get("/plans/demo/REQ-001")
        self.assertEqual(status, 200)
        for needle in ("lvl-extreme", "lvl-low", "sonnet", "work", "tras T1", "Do &lt;b&gt;one&lt;/b&gt;", "EventSource"):
            self.assertIn(needle, html)
        self.assertNotIn("<textarea", html)
        self.assertEqual(html.count("<form"), 2)  # cancel + delete only
        self.assertEqual(self.get("/plans/demo/REQ-009")[0], 404)
        self.assertEqual(self.get("/plans/..%2F/REQ-001")[0], 404)

    def test_dashboard_links_to_plans(self):
        self.assertIn('href="/plans"', self.get("/")[1])

    def test_json_api_shape(self):
        self.req(run=run_json())
        _, body, r = self.get("/api/plans")
        rows = json.loads(body)["plans"]
        self.assertEqual(rows[0]["req_id"], "REQ-001")
        self.assertTrue(rows[0]["active"])
        _, body, _ = self.get("/api/plans/demo/REQ-001?html=1")
        data = json.loads(body)
        self.assertEqual(data["milestones"][0]["tasks"][0]["attempt"]["model_requested"], "sonnet")
        self.assertIn('data-k="t-T1"', data["html"])


class RunButtonTests(PlansBase):
    def test_button_follows_the_plan_state(self):
        rdir = self.req(status="review")
        self.assertIn('name="expected" value="approve"', self.get("/plans/demo/REQ-001")[1])
        self.req(status="approved")
        self.assertIn('name="expected" value="launch"', self.get("/plans/demo/REQ-001")[1])
        (rdir / "RUN.projection.json").write_text(json.dumps({"status": "running"}), encoding="utf-8")
        self.req(status="launched")
        with patch("bt_scheduler_ops.owner_pids", return_value=[]), patch("bt_scheduler_ops.watching", return_value=False):
            self.assertIn('name="expected" value="resume"', self.get("/plans/demo/REQ-001")[1])
        with patch("bt_scheduler_ops.owner_pids", return_value=[123]):
            self.assertNotIn('name="expected"', self.get("/plans/demo/REQ-001")[1])
        (rdir / "RUN.projection.json").write_text(json.dumps({"status": "done"}), encoding="utf-8")
        with patch("bt_scheduler_ops.owner_pids", return_value=[]), patch("bt_scheduler_ops.watching", return_value=False):
            self.assertNotIn('name="expected"', self.get("/plans/demo/REQ-001")[1])

    def test_stale_page_does_not_run_another_action(self):
        self.req(status="review")
        with patch("bt_launch.launch") as launch:
            status, loc = self.post("/plans/demo/REQ-001/run", {"token": self.tok(), "expected": "resume"})
        self.assertEqual(status, 303)
        self.assertIn("cambi", unquote(loc))
        launch.assert_not_called()
        self.assertIn("status: review", (self.root / "demo/requirements/REQ-001-demo/PLAN.md").read_text())

    def test_review_plan_is_approved_and_launched_once(self):
        self.req(status="review")
        with patch("bt_launch.launch", return_value={"workdir": "/w"}) as launch, \
                patch("bt_rounds.plan_decide") as decide, patch("bt_server.commit"):
            status, loc = self.post("/plans/demo/REQ-001/run", {"token": self.tok(), "expected": "approve"})
        self.assertEqual(status, 303)
        decide.assert_called_once()
        launch.assert_called_once_with("demo", "REQ-001", background=True)
        self.assertIn("aprobado y lanzado", unquote(loc))

    def test_run_needs_the_token(self):
        self.req(status="review")
        with patch("bt_launch.launch") as launch:
            status, _ = self.post("/plans/demo/REQ-001/run", {"token": "bad", "expected": "approve"})
        self.assertEqual(status, 403)
        launch.assert_not_called()


REQUEST = {"id": "T3:2", "source": "task", "task": "T3", "attempt": "att-0002", "title": "T3 bloqueada: timeout_repeated",
           "what": "El agente superó dos veces el límite de tiempo.", "reason": "m5:timeout_repeated",
           "evidence": ["intentos: 2"], "recommended": "retry", "unskippable": False,
           "options": [{"id": "retry", "label": "Reintentar", "consequence": "Un intento nuevo."},
                       {"id": "retry_with_note", "label": "Reintentar con una indicación tuya", "consequence": "Con tu nota."}]}


class BlockedRows(unittest.TestCase):
    def test_a_blocked_task_row_says_it_waits_for_the_owner_with_the_error_and_a_link_to_the_card(self):
        import bt_page_plans as pages
        ask = dict(REQUEST, needs="Decidir cómo seguir.", error="check failed\nCannot find module 'x'", you_can=["Reintenta."])
        html = pages._blocked_note({"id": "T3", "state": "blocked"}, {"T3": ask})
        for needle in ("Espera por ti", "Decidir cómo seguir.", "check failed", 'href="#d-T3:2"'):
            self.assertIn(needle, html)
        self.assertNotIn("Cannot find module", html)                      # only the first line of the error is on the row
        self.assertIn("no tiene aún una tarjeta", pages._blocked_note({"id": "T4", "state": "blocked"}, {}))
        self.assertEqual(pages._blocked_note({"id": "T5", "state": "running"}, {"T3": ask}), "")

    def test_the_card_on_the_plan_page_shows_needs_error_and_actions(self):
        import bt_page_plans as pages
        ask = dict(REQUEST, needs="Decidir cómo seguir.", error="boom", you_can=["Reintenta."])
        html = pages._decisions({"project": "demo", "req_id": "REQ-001", "decisions": [ask]}, "/plans/demo/REQ-001", "tok")
        for needle in ("De dónde viene", "Decidir cómo seguir.", "boom", "Cómo solucionarlo", "Reintenta.",
                       "/plans/demo/REQ-001/diagnose", "Pedir diagnóstico al agente"):
            self.assertIn(needle, html)


class DecisionTests(PlansBase):
    def scheduler_req(self, status="launched"):
        rdir = self.req(status=status)
        (rdir / "RUN.projection.json").write_text(json.dumps({"status": "running"}), encoding="utf-8")
        return rdir

    def test_open_requests_and_rounds_are_answerable_on_the_plan_page(self):
        rdir = self.scheduler_req()
        (rdir / "rounds").mkdir()
        (rdir / "rounds" / "round-01.json").write_text(json.dumps({"round": 1, "status": "open", "questions": []}),
                                                        encoding="utf-8")
        with patch("bt_scheduler_decisions.open_requests", return_value=[REQUEST]):
            html = self.get("/plans/demo/REQ-001")[1]
        self.assertIn("Esperando tu decisión", html)
        self.assertIn('name="request" value="T3:2"', html)
        self.assertIn("Reintentar (recomendada)", html)
        self.assertEqual(html.count("<textarea"), 1)          # only the option that needs a reason asks for one
        self.assertIn("/p/demo/req/REQ-001?tab=rounds", html)

    def test_a_decision_posted_from_the_page_goes_through_the_decision_module(self):
        self.scheduler_req()
        with patch("bt_scheduler_decisions.answer", return_value=["T3: reopened"]) as answer:
            status, loc = self.post("/plans/demo/REQ-001/decide",
                                    {"token": self.tok(), "request": "T3:2", "option": "retry", "reason": ""})
        self.assertEqual(status, 303)
        self.assertEqual(answer.call_args.args[3:5], ("T3:2", "retry"))
        self.assertEqual(answer.call_args.kwargs["by"], "web")
        self.assertIn("T3: reopened", unquote(loc))

    def test_a_refused_decision_is_reported_not_applied(self):
        self.scheduler_req()
        with patch("bt_scheduler_decisions.answer", side_effect=ValueError("no open request T3:2")):
            status, loc = self.post("/plans/demo/REQ-001/decide", {"token": self.tok(), "request": "T3:2", "option": "retry"})
        self.assertEqual(status, 303)
        self.assertIn("No se aplicó", unquote(loc))

    def test_a_plan_without_a_scheduler_run_asks_nothing(self):
        self.req(status="approved")
        self.assertNotIn("Esperando tu decisión", self.get("/plans/demo/REQ-001")[1])


class SseTests(PlansBase):
    def read_event(self, resp, name, timeout=4.0):
        end = time.time() + timeout
        event = None
        while time.time() < end:
            line = resp.fp.readline().decode()
            if not line:
                break
            if line.startswith("event: "):
                event = line[7:].strip()
            elif line.startswith("data: ") and event == name:
                return json.loads(line[6:])
        return None

    def test_change_pushes_plan_event_and_disconnect_keeps_server_alive(self):
        rdir = self.req(run=run_json())
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=6)
        c.request("GET", "/events?plan=demo/REQ-001")
        resp = c.getresponse()
        self.assertEqual(resp.getheader("Content-Type").split(";")[0], "text/event-stream")
        time.sleep(0.2)
        (rdir / "RUN.json").write_text(json.dumps(run_json(t1="done")), encoding="utf-8")
        data = self.read_event(resp, "plan")
        self.assertIsNotNone(data)
        self.assertEqual(data["status"]["milestones"][0]["tasks"][0]["state"], "completed")
        self.assertIn("completada", data["html"])
        c.close()
        self.assertEqual(self.get("/plans")[0], 200)

    def test_keepalive_comment(self):
        self.req(run=run_json())
        with patch.object(api, "KEEPALIVE_SEC", 0):
            c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=6)
            c.request("GET", "/events")
            resp = c.getresponse()
            lines = [resp.fp.readline().decode() for _ in range(4)]
            self.assertTrue(any(l.startswith(": keepalive") for l in lines), lines)
            c.close()

    def test_clients_share_one_computation_per_window(self):
        calls = []
        key = ("test-share", id(calls))
        build = lambda: calls.append(1) or len(calls)
        values = [api._shared_value(key, build, 60) for _ in range(5)]
        self.assertEqual((values, len(calls)), ([1] * 5, 1))
        self.assertEqual(api._shared_value(key, build, 0), 2)                                # an expired window rebuilds
        with patch.object(api, "_shared", {}):
            with self.assertRaises(ValueError):
                api._shared_value("boom", lambda: (_ for _ in ()).throw(ValueError("x")), 60)
            self.assertEqual(api._shared_value("boom", lambda: "ok", 60), "ok")             # a failure is not cached

    def test_client_cap_returns_503(self):
        with patch.object(api, "_slots", threading.BoundedSemaphore(0)):
            self.assertEqual(self.get("/events")[0], 503)


class ActionTests(PlansBase):
    def form(self, **extra):
        return {"token": self.tok(), **extra}

    def test_csrf_and_origin_rejected(self):
        self.req()
        base = "/plans/demo/REQ-001/cancel"
        self.assertEqual(self.post(base, {"token": "bad", "confirm": "REQ-001"})[0], 403)
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        c.request("POST", base, urlencode(self.form(confirm="REQ-001")),
                  {"Content-Type": "application/x-www-form-urlencoded", "Origin": "http://evil.example"})
        self.assertEqual(c.getresponse().status, 403)
        self.assertIn("status: approved", (self.root / "demo/requirements/REQ-001-demo/PLAN.md").read_text())

    def test_cancel_requires_typed_id_then_sets_status_without_touching_plan_json(self):
        rdir = self.req()
        before = (rdir / "PLAN.json").read_bytes()
        status, loc = self.post("/plans/demo/REQ-001/cancel", self.form(confirm="nope"))
        self.assertEqual(status, 303)
        self.assertIn("approved", (rdir / "PLAN.md").read_text())
        self.post("/plans/demo/REQ-001/cancel", self.form(confirm="req-001"))
        self.assertIn("status: cancelled", (rdir / "PLAN.md").read_text())
        self.assertEqual((rdir / "PLAN.json").read_bytes(), before)

    def test_cancel_scheduler_plan_goes_through_adapter(self):
        rdir = self.req()
        (self.root / ".state" / "scheduler").mkdir(parents=True)
        (self.root / ".state" / "scheduler" / "demo-REQ-001.db").write_bytes(b"")
        with patch("bt_plans_api.scheduler_.apply_control") as ctl:
            self.post("/plans/demo/REQ-001/cancel", self.form(confirm="REQ-001"))
        ctl.assert_called_once_with(rdir, "stop", by="web")
        self.assertIn("status: cancelled", (rdir / "PLAN.md").read_text())

    def test_delete_moves_to_trash_and_restore_is_byte_identical(self):
        rdir = self.req(run=run_json("done", "done"))
        (rdir / "plan-revisions").mkdir()
        (rdir / "plan-revisions" / "PLAN.r1.json").write_text("{}", encoding="utf-8")
        before = {p.name: p.read_bytes() for p in (rdir / "PLAN.md", rdir / "PLAN.json", rdir / "RUN.json")}
        self.assertEqual(self.post("/plans/demo/REQ-001/delete", self.form(confirm="REQ-001"))[0], 303)
        for name in ("PLAN.md", "PLAN.json", "RUN.json", "plan-revisions"):
            self.assertFalse((rdir / name).exists())
        self.assertTrue((rdir / "SPEC.md").exists())
        entry = next((self.root / "demo" / api.TRASH_DIR).iterdir())
        manifest = json.loads((entry / api.MANIFEST).read_text())
        self.assertEqual({f["path"] for f in manifest["files"]},
                         {"PLAN.md", "PLAN.json", "RUN.json", "plan-revisions/PLAN.r1.json"})
        self.assertTrue(all(len(f["sha256"]) == 64 and f["original"] for f in manifest["files"]))
        self.assertEqual((entry / "PLAN.json").read_bytes(), before["PLAN.json"])
        self.assertIn("Restaurar", self.get("/plans")[1])
        self.post("/plans/demo/restore", self.form(entry=entry.name))
        for name, data in before.items():
            self.assertEqual((rdir / name).read_bytes(), data)
        self.assertTrue((rdir / "plan-revisions" / "PLAN.r1.json").exists())

    def test_restore_refuses_to_overwrite_and_rejects_traversal(self):
        rdir = self.req()
        self.post("/plans/demo/REQ-001/delete", self.form(confirm="REQ-001"))
        entry = next((self.root / "demo" / api.TRASH_DIR).iterdir())
        (rdir / "PLAN.md").write_text("new", encoding="utf-8")
        with self.assertRaises(api.PlanError):
            api.restore_plan(self.root, "demo", entry.name)
        self.assertEqual((rdir / "PLAN.md").read_text(), "new")
        self.assertTrue((entry / "PLAN.md").exists())
        with self.assertRaises(api.PlanError):
            api.restore_plan(self.root, "demo", "../demo")

    def test_delete_refused_while_active_unless_cancelled(self):
        rdir = self.req(run=run_json())
        self.post("/plans/demo/REQ-001/delete", self.form(confirm="REQ-001"))
        self.assertTrue((rdir / "PLAN.md").exists())
        with self.assertRaises(api.PlanError):
            api.delete_plan(self.root, "demo", "REQ-001", "REQ-001")
        with self.assertRaises(api.PlanError):
            api.delete_plan(self.root, "demo", "REQ-001", "wrong")
        api.cancel_plan(self.root, "demo", "REQ-001", "REQ-001")
        api.delete_plan(self.root, "demo", "REQ-001", "REQ-001")
        self.assertFalse((rdir / "PLAN.md").exists())

    def test_no_unlink_in_plan_code_path(self):
        for name in ("bt_plans_api.py", "bt_page_plans.py"):
            text = (SCRIPTS / name).read_text(encoding="utf-8")
            for banned in (".unlink(", "os.remove", "rmtree", "os.rmdir"):
                self.assertNotIn(banned, text)



class TaskDetailTests(unittest.TestCase):
    def test_task_card_shows_what_the_plan_says_and_flags_a_task_without_it(self):
        import bt_page_plans as pp
        import bt_planstatus as ps
        raw = {"id": "T3", "title": "Handle context loss", "objective": "A lost <context> is reported",
               "acceptance_criteria": ["shows a message", "rebuilds the scene"], "expected_paths": ["src/a.ts"],
               "verification": [{"type": "command", "value": "npm test", "purpose": "shows a message", "category": "product"},
                                {"type": "command", "value": "npm test", "purpose": "rebuilds the scene"}],
               "estimated_minutes": 90, "repository": "pictures"}
        task = {**ps._blank_task("T3", raw["title"], "M1"), "detail": ps._detail(raw)}
        html = pp._task(task)
        for needle in ("A lost &lt;context&gt; is reported", "Criterios de aceptación", "<li>rebuilds the scene</li>",
                       "<code>npm test</code>", "<code>src/a.ts</code>", "90 min", "Detalle de la tarea"):
            self.assertIn(needle, html)
        self.assertEqual(html.count("<code>npm test</code>"), 1)            # one command, its purposes under it
        self.assertNotIn("sin detalle", html)
        bare = pp._task({**ps._blank_task("T4", "Only a title", "M1"), "detail": ps._detail({"id": "T4"})})
        self.assertIn("sin detalle", bare)
        self.assertIn("objetivo, criterios de aceptación, verificación", bare)
        legacy = pp._task(ps._blank_task("T5", "From PLAN.md", "M1"))
        self.assertIn("no tiene PLAN.json", legacy)


if __name__ == "__main__":
    unittest.main()
