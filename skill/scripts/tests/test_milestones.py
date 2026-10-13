"""Milestone grouping, independent audits, and pool routing for marathon runs."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

# Reuse the existing disposable-root harness; importing it also configures BITACORA_ROOT
# before any bt_* imports when this file is run by itself.
from test_marathon import MarathonCase  # noqa: E402
import bt_agents  # noqa: E402
import bt_config  # noqa: E402
import bt_core  # noqa: E402
import bt_events  # noqa: E402
import bt_profiles  # noqa: E402
import bt_run  # noqa: E402
import bt_runprompt as rp  # noqa: E402
import bt_runsettle as settle  # noqa: E402
import bt_runstate as rs  # noqa: E402
import bt_runtask as rt  # noqa: E402


STUB = r'''
import json, os, pathlib, subprocess, sys
env = os.environ
task_list = env["BITACORA_TASK"].split(",")
kind = env.get("BITACORA_KIND", "")
provider = "codex" if env.get("CODEX_HOME") else "claude"
cfg_path = pathlib.Path(env["STUB_CFG"])
cfg = json.loads(cfg_path.read_text())
rows_path = pathlib.Path(env["STUB_ORDER"])
rows = json.loads(rows_path.read_text()) if rows_path.exists() else []
rows.append({"tasks": task_list, "kind": kind, "provider": provider})
rows_path.write_text(json.dumps(rows))
if task_list == ["FINAL"]:
    pathlib.Path(env["STUB_RDIR"], "REPORT.md").write_text("# report\n")
    raise SystemExit(0)
if kind == "audit" and cfg.get("break_verify"):
    pathlib.Path(env["STUB_WORK"], cfg["break_verify"]).unlink(missing_ok=True)
action = cfg.get("providers", {}).get(provider, "done")
cli = [sys.executable, env["STUB_SCRIPT"], "--project", env["BITACORA_PROJECT"]]
if action == "limit":
    print("Claude AI usage limit reached, try again later")
    raise SystemExit(1)
for tid in task_list:
    per_task = cfg.get("tasks", {}).get(tid, action)
    if isinstance(per_task, list):
        per_task = per_task.pop(0) if per_task else "untouched"
        cfg["tasks"][tid] = per_task
        cfg_path.write_text(json.dumps(cfg))
    if per_task == "done":
        subprocess.run(cli + ["task", "done", env["BITACORA_RUN"], tid, "--evidence", "stub completed " + tid], check=True)
    elif per_task == "fail":
        subprocess.run(cli + ["task", "fail", env["BITACORA_RUN"], tid, "--reason", "stub failed " + tid], check=True)
    elif per_task == "limit":
        print("Claude AI usage limit reached, try again later")
        raise SystemExit(1)
'''


class MilestoneTests(MarathonCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="milestones-test-")
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.isolated_root = base / "bitacora"
        self.isolated_state = self.isolated_root / ".state"
        self.isolated_state.mkdir(parents=True)
        old_root = os.environ.get("BITACORA_ROOT")
        os.environ["BITACORA_ROOT"] = str(self.isolated_root)
        self.addCleanup(lambda: os.environ.__setitem__("BITACORA_ROOT", old_root)
                        if old_root is not None else os.environ.pop("BITACORA_ROOT", None))
        replacements = {
            bt_core: {"ROOT": self.isolated_root, "STATE": self.isolated_state},
            bt_run: {"ROOT": self.isolated_root},
            rp: {"ROOT": self.isolated_root},
            settle: {"ROOT": self.isolated_root},
            rt: {"ROOT": self.isolated_root},
            rs: {"STATE": self.isolated_state},
            bt_agents: {"STATE": self.isolated_state},
            bt_profiles: {"ROOT": self.isolated_root, "STATE": self.isolated_state},
            bt_events: {"STATE": self.isolated_state},
            bt_config: {"STATE": self.isolated_state},
        }
        for module, attrs in replacements.items():
            for name, value in attrs.items():
                p = patch.object(module, name, value)
                p.start()
                self.addCleanup(p.stop)
        self.stub = base / "stub.py"
        self.stub.write_text(STUB, encoding="utf-8")
        self.addCleanup(self._clear_env)
        for key in ("STUB_CFG", "STUB_ORDER", "STUB_RDIR", "STUB_SCRIPT", "STUB_WORK",
                    "BITACORA_TASK", "BITACORA_RUN", "BITACORA_PROJECT", "BITACORA_SESSION", "BITACORA_KIND"):
            os.environ.pop(key, None)
        for key in ("CODEX_HOME", "CLAUDE_CONFIG_DIR"):
            old = os.environ.pop(key, None)
            self.addCleanup(lambda name=key, value=old: os.environ.__setitem__(name, value)
                            if value is not None else os.environ.pop(name, None))
        p = patch("bt_agents.shutil.which", return_value="/stub-agent")
        p.start()
        self.addCleanup(p.stop)

    @staticmethod
    def _clear_env():
        for key in ("STUB_CFG", "STUB_ORDER", "STUB_RDIR", "STUB_SCRIPT", "STUB_WORK",
                    "BITACORA_TASK", "BITACORA_RUN", "BITACORA_PROJECT", "BITACORA_SESSION", "BITACORA_KIND"):
            os.environ.pop(key, None)

    def make_milestone_req(self, groups, behavior=None):
        lines = ["---", "status: approved", "---", "# Plan", ""]
        for heading, tasks in groups:
            lines.extend([heading, *tasks, ""])
        self.make_req([], behavior)
        (self.rdir / "PLAN.md").write_text("\n".join(lines), encoding="utf-8")
        cfg = self.work / "cfg.json"
        cfg.write_text(json.dumps(behavior or {}), encoding="utf-8")
        os.environ.update(STUB_CFG=str(cfg), STUB_ORDER=str(self.order), STUB_RDIR=str(self.rdir),
                          STUB_SCRIPT=str(SCRIPTS / "bitacora.py"), STUB_WORK=str(self.work))
        self.cmd = f'"{sys.executable}" "{self.stub.as_posix()}"'

    def create_profiles(self):
        claude_home = self.work / "claude-home"
        codex_home = self.work / "codex-home"
        claude_home.mkdir(exist_ok=True)
        codex_home.mkdir(exist_ok=True)
        bt_profiles.add("claude-test", "claude", {"CLAUDE_CONFIG_DIR": str(claude_home)})
        bt_profiles.add("codex-test", "codex", {"CODEX_HOME": str(codex_home)})
        return ["claude-test", "codex-test"]

    def rows(self):
        return json.loads(self.order.read_text(encoding="utf-8"))


class PlanUnits(MilestoneTests):
    def test_plan_parses_milestones_kind_risk_and_heading_boundaries(self):
        self.make_milestone_req([
            ("### M1 — First", ["- [ ] T1 — Write guide · kind: docs · risk: high",
                                  "- [ ] T2 — Add tests · after: T1"]),
            ("## Other section", ["- [ ] T3 — Outside milestone · kind: research"]),
            ("### M2 — Second", ["- [ ] T4 — Review design"]),
        ])
        parsed = rs.parse_plan(self.rdir / "PLAN.md")
        self.assertEqual([t["milestone"] for t in parsed], ["M1", "M1", None, "M2"])
        self.assertEqual((parsed[0]["kind"], parsed[0]["risk"]), ("docs", "high"))
        self.assertEqual(parsed[1]["kind"], "test")
        self.assertEqual(parsed[3]["kind"], "audit")
        self.assertEqual(rs.milestones(self.rdir / "PLAN.md"), [
            {"id": "M1", "title": "First", "tasks": ["T1", "T2"]},
            {"id": "M2", "title": "Second", "tasks": ["T4"]},
        ])

    def test_plan_without_groups_keeps_single_task_units(self):
        self.make_req(["- [ ] T1 — one", "- [ ] T2 — two"])
        state = rs.init_state(self.project, self.rdir, "claude", "haiku", True)
        self.assertEqual([t["milestone"] for t in rs.parse_plan(self.rdir / "PLAN.md")], [None, None])
        self.assertEqual(rs.unit_of(state, state["tasks"][0]), [state["tasks"][0]])
        self.assertEqual(rs.milestones(self.rdir / "PLAN.md"), [])

    def test_sync_inserts_idempotent_audits_after_each_group(self):
        self.make_milestone_req([
            ("### M1 — First", ["- [ ] T1 — one", "- [ ] T2 — two · after: T1"]),
            ("### M2 — Second", ["- [ ] T3 — three"]),
        ])
        state = rs.init_state(self.project, self.rdir, "claude", "haiku", True, audit=True)
        self.assertEqual([t["id"] for t in state["tasks"]], ["T1", "T2", "M1-audit", "T3", "M2-audit"])
        first_audit = state["tasks"][2]
        self.assertEqual((first_audit["after"], first_audit["kind"], first_audit["tier"]),
                         (["T1", "T2"], "audit", 1))
        rs.sync_plan(state, self.rdir)
        self.assertEqual([t["id"] for t in state["tasks"]].count("M1-audit"), 1)
        plain = rs.init_state(self.project, self.rdir, "claude", "haiku", True, audit=False)
        self.assertNotIn("M1-audit", [t["id"] for t in plain["tasks"]])

    def test_unit_contains_ready_pending_members_but_never_audit(self):
        self.make_milestone_req([("### M1 — First", ["- [ ] T1 — one", "- [ ] T2 — two · after: T1",
                                                       "- [ ] T3 — three · after: T2"])])
        state = rs.init_state(self.project, self.rdir, "claude", "haiku", True, audit=True)
        unit = rs.next_unit(state)
        self.assertEqual([t["id"] for t in unit], ["T1", "T2", "T3"])
        self.assertEqual(rs.unit_label(unit), "M1")
        state["tasks"][0]["status"] = "done"
        self.assertEqual([t["id"] for t in rs.unit_of(state, state["tasks"][1])], ["T2", "T3"])
        state["tasks"][0]["status"] = "todo"
        state["tasks"][1]["status"] = "blocked"
        state["tasks"][2]["after"] = ["T1"]
        self.assertEqual([t["id"] for t in rs.unit_of(state, state["tasks"][0])], ["T1", "T3"])
        self.assertEqual(rs.unit_of(state, state["tasks"][3]), [state["tasks"][3]])

    def test_ready_units_require_fully_named_disjoint_repo_sets(self):
        tasks = [
            {"id": "T1", "milestone": "M1", "status": "todo", "after": [], "repo": "api"},
            {"id": "T2", "milestone": "M2", "status": "todo", "after": [], "repo": "web"},
            {"id": "T3", "milestone": "M3", "status": "todo", "after": [], "repo": "api"},
        ]
        self.assertEqual([[t["id"] for t in u] for u in rs.ready_units({"tasks": tasks}, 2)], [["T1"], ["T2"]])
        tasks[1]["repo"] = "api"
        self.assertEqual([[t["id"] for t in u] for u in rs.ready_units({"tasks": tasks}, 2)], [["T1"]])
        tasks[1]["repo"] = None
        self.assertEqual([[t["id"] for t in u] for u in rs.ready_units({"tasks": tasks}, 2)], [["T1"]])


class MilestoneRuns(MilestoneTests):
    def test_two_audited_milestones_run_in_order_then_final_review(self):
        self.make_milestone_req([
            ("### M1 — First", ["- [ ] T1 — one", "- [ ] T2 — two"]),
            ("### M2 — Second", ["- [ ] T3 — three"]),
        ])
        self.assertEqual(self.run_sup(audit=True, no_autostart=True), 0)
        rows = self.rows()
        self.assertEqual([r["tasks"] for r in rows], [["T1", "T2"], ["M1-audit"], ["T3"], ["M2-audit"], ["FINAL"]])
        self.assertEqual(rows[1]["kind"], "audit")
        self.assertEqual(self.state()["sessions"], 5)
        self.assertTrue(all(t["status"] == "done" for t in self.state()["tasks"]))

    def test_failed_member_skips_dependent_without_counting_an_attempt(self):
        self.make_milestone_req([("### M1 — First", ["- [ ] T1 — one", "- [ ] T2 — two",
                                                      "- [ ] T3 — three · after: T2"])],
                                {"tasks": {"T1": "done", "T2": "fail", "T3": "untouched"}})
        self.assertEqual(self.run_sup(audit=False, once=True, no_autostart=True), 0)
        self.assertEqual(self.task("T1")["status"], "done")
        self.assertEqual((self.task("T2")["status"], self.task("T2")["attempts"], self.task("T2")["tier"]),
                         ("todo", 1, 1))
        self.assertEqual((self.task("T3")["status"], self.task("T3")["attempts"]), ("todo", 0))
        self.assertEqual(self.state()["log"][-1]["result"], "skipped")

    def test_claimed_done_with_failed_verify_is_not_done(self):
        verify = f'`"{sys.executable}" -c "import sys; sys.exit(1)"`'
        self.make_milestone_req([("### M1 — First", [f"- [ ] T1 — one · verify: {verify}"])])
        self.run_sup(audit=False, once=True, no_autostart=True)
        self.assertEqual((self.task("T1")["status"], self.task("T1")["attempts"]), ("todo", 1))
        self.assertEqual(self.state()["log"][-1]["result"], "verify_failed")

    def test_audit_repeats_member_verification_after_auditor_changes_file(self):
        verify = f'`"{sys.executable}" -c "import os,pathlib,sys; sys.exit(0 if (pathlib.Path(os.environ[\'STUB_WORK\']) / \'proof.txt\').exists() else 1)"`'
        self.make_milestone_req([("### M1 — First", [f"- [ ] T1 — create proof · verify: {verify}"])],
                                {"break_verify": "proof.txt"})
        # The stub creates the proof as the builder's work; the auditor removes it before its verdict.
        original = self.stub.read_text(encoding="utf-8")
        self.stub.write_text(original.replace('if task_list == ["FINAL"]:',
                                              'if task_list == ["T1"]:\n    pathlib.Path(env["STUB_WORK"], "proof.txt").write_text("ok")\nif task_list == ["FINAL"]:'),
                         encoding="utf-8")
        self.assertEqual(self.run_sup(audit=True, no_autostart=True, once=True), 0)
        self.assertEqual(self.run_sup(no_autostart=True, once=True), 0)
        self.assertEqual(self.task("T1")["status"], "done")
        audit = self.task("M1-audit")
        self.assertEqual((audit["status"], audit["attempts"]), ("todo", 1))
        self.assertEqual(self.state()["log"][-1]["result"], "verify_failed")

    def test_milestone_owner_may_mark_each_named_task_but_not_another(self):
        self.make_milestone_req([("### M1 — First", ["- [ ] T1 — one", "- [ ] T2 — two", "- [ ] T3 — three"])])
        rs.save(self.rdir, rs.init_state(self.project, self.rdir, "claude", "haiku", True, audit=False))
        os.environ.update(BITACORA_RUN="REQ-001", BITACORA_PROJECT=self.project, BITACORA_TASK="T1,T2")
        rt.task_done(self.rdir, "T1", "ok")
        rt.task_done(self.rdir, "T2", "ok")
        with self.assertRaises(SystemExit):
            rt.task_done(self.rdir, "T3", "outside scope")
        self.assertEqual([t["status"] for t in self.state()["tasks"]], ["in_progress", "in_progress", "todo"])

    def test_prompts_include_member_verifies_builders_and_audit_report_path(self):
        self.make_milestone_req([("### M1 — First", ["- [ ] T1 — one · verify: `echo verify-one`",
                                                       "- [ ] T2 — two · verify: `echo verify-two`"])])
        state = rs.init_state(self.project, self.rdir, "claude", "haiku", True, audit=True)
        unit = rs.unit_of(state, state["tasks"][0])
        prompt = rp._milestone_prompt(self.project, self.rdir, state, unit, 1, "branch")
        self.assertIn("T1", prompt)
        self.assertIn("`echo verify-one`", prompt)
        self.assertIn("`echo verify-two`", prompt)
        state["tasks"][0]["last_route"] = {"agent": "claude", "model": "haiku"}
        auditor = state["tasks"][2]
        audit_prompt = rp._audit_prompt(self.project, self.rdir, state, auditor, 2, "branch")
        self.assertIn("claude/haiku", audit_prompt)
        self.assertIn((self.rdir / "AUDIT-M1.md").as_posix(), audit_prompt)
        rs.save(self.rdir, state)
        os.environ.update(BITACORA_RUN="REQ-001", BITACORA_PROJECT=self.project, BITACORA_TASK="T1,T2")
        block = rp.marathon_block()
        self.assertIn("milestone **M1**", block)
        self.assertIn("tasks T1, T2", block)

    def test_pool_cools_limited_account_and_continues_on_other_provider(self):
        self.make_req(["- [ ] T1 — one"], {"providers": {"claude": "limit", "codex": "done"}})
        profiles = self.create_profiles()
        self.assertEqual(self.run_sup(pool=profiles, audit=False, no_autostart=True), 0)
        rows = self.rows()
        self.assertEqual([r["provider"] for r in rows], ["claude", "codex", "codex"])
        self.assertEqual(self.state()["status"], "done")
        self.assertIsNotNone(bt_agents.cooling_until("claude-test", "claude"))
        self.assertIsNone(self.state().get("waiting_until"))

    def test_pool_waits_only_when_every_profile_is_cooling(self):
        self.make_req(["- [ ] T1 — one"], {"providers": {"claude": "limit"}})
        profiles = self.create_profiles()
        bt_agents.quota_mark("codex-test", "codex", 0)
        self.assertEqual(self.run_sup(pool=profiles, audit=False, no_autostart=True, once=True), 0)
        state = self.state()
        self.assertEqual(state["status"], "waiting")
        self.assertTrue(state["waiting_until"])
        self.assertEqual(state["tasks"][0]["attempts"], 0)

    def test_failed_provider_is_avoided_for_next_attempt(self):
        self.make_req(["- [ ] T1 — one"], {"providers": {"claude": "fail", "codex": "done"}})
        profiles = self.create_profiles()
        self.assertEqual(self.run_sup(pool=profiles, audit=False, no_autostart=True, once=True), 0)
        self.assertEqual(self.task("T1")["last_route"]["agent"], "claude")
        self.assertEqual(self.run_sup(no_autostart=True, once=True), 0)
        self.assertEqual(self.task("T1")["status"], "done")
        self.assertEqual(self.task("T1")["last_route"]["agent"], "codex")


if __name__ == "__main__":
    unittest.main()
