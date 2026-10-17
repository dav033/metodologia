"""Scheduler authority reads in the CLI watcher and local run views."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import bt_page_req
import bt_page_run
import bt_pages
import bt_scheduler_adapter as adapter
import bt_watch


class SchedulerRunViews(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project_dir = Path(self.temp.name) / "demo-project"
        self.rdir = self.project_dir / "requirements" / "REQ-042-demo"
        self.rdir.mkdir(parents=True)
        self.db = Path(self.temp.name) / "SCHEDULER.db"
        self.db.touch()

    def projection(self, *, status="running", heartbeat="2026-10-16T12:00:00+00:00"):
        return {"authority": "scheduler", "projection": True, "req": "REQ-042", "status": status,
                "scheduler_status": status, "heartbeat_at": heartbeat, "tasks": [
                    {"id": "T1", "title": "Demostrar estado", "status": "in_progress", "attempts": 1,
                     "scheduler_state": "active"},
                    {"id": "T2", "title": "Esperar", "status": "todo", "attempts": 0,
                     "scheduler_state": "pending"}],
                "plan_ref": {"plan_id": "demo", "revision": 1, "sha256": "0" * 64}}

    def test_projection_is_read_only_scheduler_authority_and_never_run_json(self):
        (self.rdir / "RUN.json").write_text("{}", encoding="utf-8")
        self.assertEqual(adapter.authority(self.rdir), "legacy")
        with patch.object(adapter, "run_db_path", return_value=self.db):
            self.assertEqual(adapter.authority(self.rdir), "scheduler")
            (self.rdir / adapter.PROJECTION).write_text(json.dumps(self.projection()), encoding="utf-8")
            self.assertEqual(adapter.read_projection(self.rdir)["authority"], "scheduler")
            self.assertTrue((self.rdir / "RUN.json").exists())

    def test_corrupt_scheduler_projection_never_falls_back_to_run_json(self):
        (self.rdir / "RUN.json").write_text(json.dumps({"status": "running"}), encoding="utf-8")
        (self.rdir / adapter.PROJECTION).write_text("{broken", encoding="utf-8")
        with patch.object(adapter, "run_db_path", return_value=self.db):
            self.assertIsNone(adapter.read_projection(self.rdir))

    def test_scheduler_projection_requires_complete_plan_identity(self):
        (self.rdir / adapter.PROJECTION).write_text(
            json.dumps(self.projection() | {"plan_ref": {}}), encoding="utf-8")
        with patch.object(adapter, "run_db_path", return_value=self.db):
            self.assertIsNone(adapter.read_projection(self.rdir))

    def test_scheduler_watch_reports_stale_with_exact_resume_command(self):
        run = self.projection(heartbeat="2000-01-01T00:00:00+00:00")
        lines, cursor = bt_watch.scheduler_news("metodologia", "REQ-042", run, {})
        self.assertTrue(cursor["stale"])
        report = bt_watch.scheduler_report("metodologia", "REQ-042", run, lines)
        self.assertIn("bitacora.py --project metodologia scheduler-run REQ-042 --resume", report)
        self.assertEqual(bt_watch.scheduler_news("metodologia", "REQ-042", run, cursor)[0], [])

    def test_dashboard_includes_scheduler_run_and_exact_recovery_command(self):
        pdir = self.project_dir
        with patch.object(adapter, "run_db_path", return_value=self.db):
            (self.rdir / adapter.PROJECTION).write_text(
                json.dumps(self.projection(heartbeat="2000-01-01T00:00:00+00:00")), encoding="utf-8")
            runs = bt_page_run.active_runs(pdir)
            self.assertEqual(runs[0]["authority"], "scheduler")
            self.assertTrue(runs[0]["stale"])
            with patch.object(bt_pages, "projects", return_value=[pdir]), \
                    patch.object(bt_pages.ws, "repos", return_value={}), \
                    patch.object(bt_pages, "open_pending", return_value=[]), \
                    patch.object(bt_pages, "artifacts", return_value=[]), \
                    patch.object(bt_pages, "last_day_logs", return_value=[]):
                html = bt_pages.dashboard()
        self.assertIn("bitacora.py --project demo-project scheduler-run REQ-042 --resume", html)

    def test_dashboard_marks_missing_scheduler_projection_and_offers_recovery(self):
        pdir = self.project_dir
        with patch.object(adapter, "run_db_path", return_value=self.db), \
                patch.object(bt_pages, "projects", return_value=[pdir]), \
                patch.object(bt_pages.ws, "repos", return_value={}), \
                patch.object(bt_pages, "open_pending", return_value=[]), \
                patch.object(bt_pages, "artifacts", return_value=[]), \
                patch.object(bt_pages, "last_day_logs", return_value=[]):
            html = bt_pages.dashboard()
        self.assertIn("desconocido", html)
        self.assertIn("bitacora.py --project demo-project scheduler-run REQ-042 --resume", html)

    def test_requirement_page_exposes_run_tab_when_projection_is_missing(self):
        with patch.object(bt_page_req, "find_req", return_value=self.rdir), \
                patch.object(bt_page_req, "req_id", return_value="REQ-042"), \
                patch.object(bt_page_req, "has_run", return_value=True), \
                patch.object(bt_page_req, "load_run", return_value=None), \
                patch.object(bt_page_req, "run_panel", return_value="proyección Scheduler no disponible"), \
                patch.object(bt_page_req, "_front", return_value="launched"), \
                patch.object(bt_page_req, "_first_heading", return_value="Demo"):
            html = bt_page_req.req_page("metodologia", "REQ-042", "", "token")
        self.assertIn('?tab=run">Maratón', html)
        self.assertIn("proyección Scheduler no disponible", html)

    def test_scheduler_run_panel_renders_projection_and_m1_controls(self):
        run = self.projection()
        with patch.object(bt_page_run, "load_run", return_value=run), \
                patch.object(bt_page_run, "scheduler_authority", return_value=True):
            html = bt_page_run.run_panel("metodologia", "REQ-042", self.rdir, "secret-token")
        self.assertIn("Scheduler", html)
        self.assertIn("Demostrar estado", html)
        self.assertIn('name="token" value="secret-token"', html)
        self.assertIn('name="action" value="pause"', html)

    def test_scheduler_run_panel_shows_complexity_and_planned_or_revalidated_routes(self):
        run = self.projection()
        run["tasks"][0].update(milestone="M1", complexity="high", model="sonnet", effort="xhigh",
                               profile="claude-work", route_status="assigned")
        run["tasks"][1].update(milestone="M2", complexity="low", model="haiku", effort="",
                               profile="claude-default", route_status="recommended")
        with patch.object(bt_page_run, "load_run", return_value=run), \
                patch.object(bt_page_run, "scheduler_authority", return_value=True):
            html = bt_page_run.run_panel("metodologia", "REQ-042", self.rdir, "token")

        self.assertIn("Complejidad", html)
        self.assertIn("Modelo M2", html)
        self.assertIn("claude-work · sonnet (xhigh) · revalidado al iniciar", html)
        self.assertIn("claude-default · haiku · planificado", html)

    def test_scheduler_run_panel_displays_route_account_quota_and_stable_unavailable_reason_escaped(self):
        run = self.projection()
        run["tasks"][0].update(
            provider="claude", model="sonnet", profile="claude-work", effort="high", account_ref="acct:opaque-1",
            route_status="recommended", selection_reason="route_policy_preferred", quota_state="fresh",
            quota_reason="quota_fresh", quota_observed_at="1792170000", quota_valid_until="1e999",
            quota_used_percent="12.5",
        )
        run["tasks"][1].update(route_status="unavailable", route_reason="m2_batch_unavailable <script>")
        with patch.object(bt_page_run, "load_run", return_value=run), \
                patch.object(bt_page_run, "scheduler_authority", return_value=True):
            html = bt_page_run.run_panel("metodologia", "REQ-042", self.rdir, "token")

        for expected in ("Cuenta y evidencia de cuota", "claude · claude-work · sonnet (high) · planificado",
                         "acct:opaque-1", "cuota fresh", "observada 2026-10-16 17:00:00 UTC",
                         "válida hasta sin dato", "uso 12.5%", "selección route_policy_preferred",
                         "motivo: m2_batch_unavailable &lt;script&gt;"):
            self.assertIn(expected, html)
        self.assertNotIn("1e999", html)
        self.assertNotIn("<script>", html)

    def test_scheduler_panel_fails_closed_when_projection_is_unavailable(self):
        with patch.object(bt_page_run, "load_run", return_value=None), \
                patch.object(bt_page_run, "scheduler_authority", return_value=True):
            html = bt_page_run.run_panel("metodologia", "REQ-042", self.rdir, "token")
        self.assertIn("proyección Scheduler no disponible", html)
        self.assertNotIn('name="action" value="stop"', html)

    def test_watch_reports_missing_projection_with_scheduler_resume(self):
        with patch.object(bt_watch, "find_req", return_value=self.rdir), \
                patch.object(bt_watch, "req_id", return_value="REQ-042"), \
                patch.object(adapter, "scheduler_authority", return_value=True), \
                patch.object(adapter, "read_projection", return_value=None):
            result = bt_watch.watch("demo-project", "REQ-042", timeout_min=0)
        self.assertIn("Scheduler · proyección no disponible", result)
        self.assertIn("bitacora.py --project demo-project scheduler-run REQ-042 --resume", result)


if __name__ == "__main__":
    unittest.main()
