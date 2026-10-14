"""How the methodology uses the planner module: only through bt_plan_adapter, one direction, nothing duplicated.

The module's own behaviour is tested inside the module (bt_planner/tests). Here: the boundary seen from outside, the
module suite run as an isolated subprocess, the hooks in handoff / launch / run state, the CLI plumbing, and parity of the
module's PLAN.md parser with the supervisor's parser on every real plan in the repository.
"""
from __future__ import annotations

import ast
import contextlib
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))
REPO = SCRIPTS.parent.parent

import bt_cli_plan  # noqa: E402
import bt_config  # noqa: E402
import bt_handoff  # noqa: E402
import bt_launch  # noqa: E402
import bt_plan_adapter as adapter  # noqa: E402
import bt_runstate as rs  # noqa: E402
import bt_planner as planner  # noqa: E402
from bt_planner import markdown as planner_markdown  # noqa: E402
from bt_planner import revisions as planner_revisions  # noqa: E402


def classified(rdir: Path) -> dict:
    plan = planner.skeleton(rdir, plan_id=adapter.plan_id(rdir))
    for milestone in plan["milestones"]:
        milestone["title"] = milestone["title"] or milestone["id"]
        milestone["acceptance_criteria"] = [f"{milestone['id']} delivered"]
    for task in plan["tasks"]:
        why = {"complexity": "the change follows a pattern already present in the module so little reasoning is needed",
               "scope": "one small localized change confined to a single component of the repository",
               "duration": "comparable to similar edits in this module including running its local tests",
               "risk": "a mistake is local reversible and caught by the task verification command",
               "coupling": "no other task edits the same files or depends on a shared contract",
               "confidence": "the affected code was read and a precedent for this exact change exists"}
        task.update({"objective": f"Deliver the behaviour described by {task['title']} and keep tests passing",
                     "repository": task.get("repository", "app"),
                     "complexity": "low", "scope": "small_change", "estimated_minutes": 30, "risk": "medium",
                     "coupling": "low", "confidence": "medium", "estimate_rationale": "Known pattern",
                     "classification_evidence": {d: {"justification": f"{task['id']}: {sentence}",
                                                     "evidence": ["spec:SPEC.md#spec", "command:python3 -m unittest -> the tests of the module ran"]}
                                                 for d, sentence in why.items()},
                     "expected_paths": task.get("expected_paths", [f"src/{task['id'].lower()}/**"]),
                     "shared_resources": [], "acceptance_criteria": [f"{task['title']} works as described"]})
        if not task.get("verification"):
            task["verification"] = [{"type": "manual", "value": "read the diff", "purpose": "review",
                                     "expected": "matches the objective"}]
    return plan


PLAN_MD = """---
status: {status}
---
# Plan

### M1 — Auth fix
- [ ] T1 — Reject expired sessions · repo: app · files: src/auth/** · verify: `python -m unittest`
- [ ] T2 — Document it · repo: app · after: T1
"""


class Boundary(unittest.TestCase):
    """The dependency points one way: methodology -> adapter -> bt_planner, never the reverse, never around it."""

    def top_imports(self, path: Path) -> set[str]:
        names = set()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                names |= {alias.name.split(".")[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and not node.level:
                names.add((node.module or "").split(".")[0])
        return names

    ALLOWED_USERS = {"bt_plan_adapter.py", "test_plan_integration.py", "test_package_install.py"}

    def test_only_the_adapter_imports_the_module(self):
        offenders = []
        for path in sorted(REPO.rglob("*.py")):
            rel = path.relative_to(REPO)
            if (".git" in rel.parts or "bt_planner" in rel.parts or "node_modules" in rel.parts
                    or ".state" in rel.parts or ".venv" in rel.parts or path.name in self.ALLOWED_USERS):
                continue  # `.state` holds throwaway review snapshots (full copies of the tree, venv included)
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeError):
                continue
            for node in ast.walk(tree):
                names = set()
                if isinstance(node, ast.Import):
                    names = {a.name.split(".")[0] for a in node.names}
                elif isinstance(node, ast.ImportFrom) and not node.level:
                    names = {(node.module or "").split(".")[0]}
                elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                    names = {node.value.split(".")[0]}  # importlib.import_module("bt_planner...") and friends
                if "bt_planner" in names:
                    offenders.append(f"{rel}:{getattr(node, 'lineno', '?')}")
        self.assertEqual(offenders, [], "only bt_plan_adapter may reach the planner module")
        self.assertIn("bt_planner", self.top_imports(SCRIPTS / "bt_plan_adapter.py"))

    def test_the_module_imports_nothing_of_the_methodology(self):
        stdlib = set(sys.stdlib_module_names)
        for path in (SCRIPTS / "bt_planner").glob("*.py"):
            outside = {n for n in self.top_imports(path) if n and n not in stdlib and n != "bt_planner"}
            self.assertEqual(outside, set(), path.name)

    def test_the_old_scattered_modules_are_gone(self):
        for name in ("bt_plan_contract", "bt_plan_revisions", "bt_plan_sync"):
            self.assertFalse((SCRIPTS / f"{name}.py").exists(), name)

    def test_module_suite_passes_in_an_isolated_interpreter(self):
        done = subprocess.run([sys.executable, "-I", "-m", "unittest", "discover", "-s",
                               str(SCRIPTS / "bt_planner" / "tests")], capture_output=True, text=True, timeout=300,
                              cwd=tempfile.gettempdir(), env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"})
        self.assertEqual(done.returncode, 0, (done.stderr or done.stdout)[-1500:])
        self.assertRegex(done.stderr, r"Ran \d+ tests")

    def test_module_runs_as_a_command_from_a_lone_copy_with_no_methodology_reachable(self):
        import shutil
        with tempfile.TemporaryDirectory(prefix="planner-cmd-") as tmp:
            shutil.copytree(SCRIPTS / "bt_planner", Path(tmp) / "bt_planner",
                            ignore=shutil.ignore_patterns("__pycache__", "tests"))
            done = subprocess.run([sys.executable, "-I", "-c",
                                   "import sys; sys.path.insert(0, sys.argv[1]); from bt_planner.cli import main; "
                                   "import importlib.util as u; "
                                   "assert all(u.find_spec(m) is None for m in ('bt_core', 'bt_runstate', 'bitacora')); "
                                   "sys.exit(main(['example']))", tmp], capture_output=True, text=True, timeout=60,
                                  cwd=tempfile.gettempdir())
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn('"plan_id"', done.stdout)


class Isolated(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="plan-integration-")
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "bitacora"
        self.rdir = self.root / "sample" / "requirements" / "REQ-001-demo"
        self.rdir.mkdir(parents=True)
        (self.rdir / "SPEC.md").write_text("# Spec\n", encoding="utf-8")
        self.set_status("draft")
        for target, value in (("bt_handoff.ROOT", self.root), ("bt_launch.ROOT", self.root)):
            patcher = patch(target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        repos = patch.object(bt_handoff.ws, "repos", lambda root, project: {"app": Path(self._tmp.name)})
        repos.start()
        self.addCleanup(repos.stop)
        cfg = patch.object(bt_config, "get", side_effect=lambda key, default=None: default)
        cfg.start()
        self.addCleanup(cfg.stop)

    def set_status(self, status: str) -> None:
        (self.rdir / "PLAN.md").write_text(PLAN_MD.format(status=status), encoding="utf-8")

    def good_plan(self) -> dict:
        plan = classified(self.rdir)
        (self.rdir / "PLAN.json").write_text(planner.dumps(plan), encoding="utf-8")
        return plan


class Handoff(Isolated):
    def test_plans_without_the_contract_are_untouched(self):
        self.assertEqual(adapter.handoff_problems(self.rdir), [])
        self.assertFalse(any("PLAN.json" in p for p in bt_handoff.assess("sample", self.rdir)["problems"]))

    def test_an_incomplete_plan_json_blocks_the_handoff(self):
        planner.write_skeleton(self.rdir)
        report = bt_handoff.assess("sample", self.rdir)
        self.assertFalse(report["ok"] or report["auto"])
        self.assertTrue(any(p.startswith("PLAN.json: T1.") for p in report["problems"]), report["problems"])
        self.assertTrue(any("plan-json check REQ-001" in p for p in report["problems"]))

    def test_a_complete_plan_json_passes(self):
        self.good_plan()
        self.assertFalse(any("PLAN.json" in p for p in bt_handoff.assess("sample", self.rdir)["problems"]))


class Launch(Isolated):
    def launch_until_after_freeze(self):
        class Stop(Exception):
            pass
        with patch.object(bt_launch, "find_req", return_value=self.rdir), \
                patch("bt_requirements_gate.require_ready", return_value={"status": "ready"}), \
                patch.object(bt_launch.ws, "clone_missing"), patch.object(bt_launch, "write_handoff", side_effect=Stop):
            with self.assertRaises(Stop):
                bt_launch.launch("sample", "REQ-001", mode="marathon")

    def test_launch_binds_the_revision_frozen_at_approval_and_never_creates_it(self):
        self.good_plan()
        self.set_status("approved")  # approved by hand: no approval record
        with self.assertRaises(SystemExit) as ctx:
            self.launch_until_after_freeze()
        self.assertIn("PLAN_NOT_FROZEN", str(ctx.exception))
        self.assertEqual(planner.list_revisions(self.rdir), [])
        planner.approve_freeze(self.rdir, adapter.plan_id(self.rdir), adapter.APPROVED_STATES)
        self.launch_until_after_freeze()
        self.launch_until_after_freeze()  # idempotent on retry
        self.assertEqual([r["revision"] for r in planner.list_revisions(self.rdir)], [1])

    def test_launch_refuses_an_invalid_approved_plan_json(self):
        planner.write_skeleton(self.rdir)
        self.set_status("approved")
        with patch.object(bt_launch, "find_req", return_value=self.rdir), \
                patch("bt_requirements_gate.require_ready", return_value={"status": "ready"}):
            with self.assertRaises(SystemExit) as ctx:
                bt_launch.launch("sample", "REQ-001", mode="marathon")
        self.assertIn("PLAN_INVALID", str(ctx.exception))
        self.assertEqual(planner.list_revisions(self.rdir), [])

    def test_legacy_plans_launch_as_before(self):
        self.set_status("approved")
        self.launch_until_after_freeze()
        self.assertFalse((self.rdir / "plan-revisions").exists())

    def test_dry_run_never_writes(self):
        self.good_plan()
        self.set_status("approved")
        planner.approve_freeze(self.rdir, adapter.plan_id(self.rdir), adapter.APPROVED_STATES)
        before = sorted(p.name for p in (self.rdir / "plan-revisions").iterdir())
        with patch.object(bt_launch, "find_req", return_value=self.rdir), \
                patch("bt_requirements_gate.require_ready", return_value={"status": "ready"}), \
                patch.object(bt_launch, "write_handoff", side_effect=RuntimeError("stop")), \
                self.assertRaises(RuntimeError):
            bt_launch.launch("sample", "REQ-001", mode="marathon", dry_run=True)
        self.assertEqual(sorted(p.name for p in (self.rdir / "plan-revisions").iterdir()), before)


class RunState(Isolated):
    def test_new_run_records_plan_ref_only_when_a_revision_is_frozen(self):
        self.assertNotIn("plan_ref", rs.init_state("sample", self.rdir, "claude", "haiku", False))
        self.good_plan()
        self.set_status("approved")
        entry = planner.approve_freeze(self.rdir, adapter.plan_id(self.rdir), adapter.APPROVED_STATES)
        state = rs.init_state("sample", self.rdir, "claude", "haiku", False)
        self.assertEqual(state["plan_ref"], {"plan_id": "REQ-001", "revision": 1, "sha256": entry["sha256"]})
        self.assertNotIn("plan", state)  # the run never copies the plan: one source of truth

    def test_an_existing_run_json_is_never_modified_by_planner_operations(self):  # AC-11
        run = self.rdir / "RUN.json"
        run.write_text(json.dumps({"req": "REQ-001", "status": "running", "sessions": 3,
                                   "tasks": [{"id": "T1", "status": "done", "attempts": 2}]}), encoding="utf-8")
        before = run.read_bytes()
        self.set_status("approved")
        planner.write_skeleton(self.rdir)
        self.good_plan()
        adapter.run_cli("check", self.rdir, emit=lambda _: None)
        adapter.run_cli("freeze", self.rdir, emit=lambda _: None)
        adapter.run_cli("compat", self.rdir, emit=lambda _: None)
        adapter.freeze_on_launch(self.rdir)
        adapter.handoff_problems(self.rdir)
        self.assertEqual(run.read_bytes(), before)

    def test_a_damaged_store_leaves_a_trace_and_does_not_stop_the_run(self):
        (self.rdir / "plan-revisions").mkdir()
        (self.rdir / "plan-revisions" / "MANIFEST.json").write_text("{", encoding="utf-8")
        state = rs.init_state("sample", self.rdir, "claude", "haiku", False)
        self.assertEqual(state["plan_ref_error"], "REVISION_STORE_UNREADABLE")
        self.assertNotIn("plan_ref", state)


class Cli(Isolated):
    def invoke(self, action: str, **flags) -> int:
        import argparse
        args = argparse.Namespace(action=action, req="REQ-001", force=False, json=False, **flags)
        with contextlib.redirect_stdout(io.StringIO()):
            return bt_cli_plan.dispatch(args, self.root, "sample")

    def test_command_plumbing_uses_the_requirement_id_and_the_methodology_states(self):
        self.assertEqual(self.invoke("init"), 0)
        self.assertEqual(self.invoke("check"), 2)
        self.good_plan()
        self.assertEqual(self.invoke("check"), 0)
        self.assertEqual(self.invoke("freeze"), 2)  # still `draft`
        self.set_status("approved")
        self.assertEqual(self.invoke("freeze"), 0)
        self.assertEqual(self.invoke("show"), 0)
        self.assertEqual(self.invoke("compat"), 0)
        self.assertEqual(self.invoke("bind"), 0)  # the launch gate, read-only
        self.assertEqual(self.invoke("report"), 0)
        self.assertEqual(adapter.plan_id(self.rdir), "REQ-001")

    def test_parser_registers_the_command(self):
        import argparse
        parser = argparse.ArgumentParser()
        bt_cli_plan.add_parser(parser.add_subparsers(dest="cmd"))
        self.assertEqual(parser.parse_args(["plan-json", "check", "REQ-009"]).action, "check")


class LaunchPaths(Isolated):
    """Every way of starting work passes the same gate: valid, consistent with PLAN.md, exactly the approved revision."""

    def approved(self) -> dict:
        """What `plan approve` does: the plan is approved and exactly that PLAN.json is frozen."""
        plan = self.good_plan()
        self.set_status("approved")
        planner.approve_freeze(self.rdir, adapter.plan_id(self.rdir), adapter.APPROVED_STATES)
        return plan

    def revise(self, plan: dict, minutes: int) -> None:
        plan["revision"] += 1
        plan["tasks"][0]["estimated_minutes"] = minutes
        (self.rdir / "PLAN.json").write_text(planner.dumps(plan), encoding="utf-8")

    def revisions(self) -> list[int]:
        return [r["revision"] for r in planner.list_revisions(self.rdir)]

    def standard_launch(self, **kw):
        class Stop(Exception):
            pass
        with patch.object(bt_launch, "find_req", return_value=self.rdir), \
                patch("bt_requirements_gate.require_ready", return_value={"status": "ready"}), \
                patch.object(bt_launch.ws, "clone_missing"), \
                patch.object(bt_launch, "write_handoff", side_effect=Stop):
            try:
                bt_launch.launch("sample", "REQ-001", mode="marathon", **kw)
            except Stop:
                return "passed the gate"
        return "completed"

    def foreground_launch(self, **kw):
        import bt_orchestration_transition as transition
        with patch.object(transition.core, "find_req", return_value=self.rdir), \
                patch.object(transition.gate, "require_ready", return_value={"status": "ready"}), \
                patch.object(transition.state_, "load", return_value=None), \
                patch.object(transition.core.ws, "workdir", return_value=self.rdir), \
                patch.object(transition.client, "locate", return_value={"wrapper": None, "why": "no parent"}):
            return transition.launch("sample", "REQ-001", **kw)

    def open_run(self):
        import bt_run
        with patch.object(bt_run.rs, "load", return_value=None), patch.object(bt_run.rs, "save"), \
                patch.object(bt_run, "_pool", return_value=None):
            return bt_run._open("sample", self.rdir, {"agent": "claude", "model": "haiku"})

    # -- standard / web / handoff launch (bt_launch.launch) ---------------------------------------------------------
    def test_standard_launch_refuses_content_nobody_approved(self):
        plan = self.approved()
        self.assertEqual(self.standard_launch(), "passed the gate")
        self.assertEqual(self.revisions(), [1])
        self.revise(plan, 55)  # an edit after approval, with a bumped revision number
        with self.assertRaises(SystemExit) as ctx:
            self.standard_launch()
        self.assertIn("PLAN_DRIFT", str(ctx.exception))
        self.assertEqual(self.revisions(), [1])  # the launch did not freeze it on the way in

    def test_launch_after_a_new_approval_runs_the_new_revision(self):
        plan = self.approved()
        self.standard_launch()
        self.revise(plan, 55)
        rounds_module = __import__("bt_rounds")
        self.set_status("review")
        rounds_module.plan_decide(self.rdir, True, "", "test")
        self.assertEqual(self.revisions(), [1, 2])
        self.assertEqual(self.standard_launch(), "passed the gate")

    def test_force_still_validates_and_freezes_what_it_launches(self):
        self.good_plan()
        self.set_status("review")
        self.assertEqual(self.standard_launch(force=True), "passed the gate")
        self.assertEqual(self.revisions(), [1])
        broken = self.rdir.parent / "REQ-002-broken"
        broken.mkdir()
        (broken / "SPEC.md").write_text("# s\n", encoding="utf-8")
        (broken / "PLAN.md").write_text(PLAN_MD.format(status="review"), encoding="utf-8")
        planner.write_skeleton(broken)
        with self.assertRaises(SystemExit) as ctx:
            adapter.freeze_on_launch(broken, forced=True)
        self.assertIn("PLAN_INVALID", str(ctx.exception))
        self.assertFalse((broken / "plan-revisions").exists())

    def test_dry_run_validates_without_writing(self):
        self.approved()
        self.assertEqual(self.standard_launch(dry_run=True), "passed the gate")
        self.assertEqual(self.revisions(), [1])  # only the approval froze anything
        data = json.loads((self.rdir / "PLAN.json").read_text())
        data["tasks"][0]["risk"] = "critical"
        (self.rdir / "PLAN.json").write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(SystemExit) as ctx:
            self.standard_launch(dry_run=True)
        self.assertIn("PLAN_INVALID", str(ctx.exception))

    def test_contradiction_between_plan_md_and_plan_json_blocks_launch(self):
        plan = self.approved()
        plan["tasks"][1]["after"] = []
        (self.rdir / "PLAN.json").write_text(planner.dumps(plan), encoding="utf-8")
        with self.assertRaises(SystemExit) as ctx:
            self.standard_launch()
        self.assertIn("T2.after", str(ctx.exception))

    # -- foreground transition ---------------------------------------------------------------------------------
    def test_foreground_launch_freezes_the_same_revision(self):
        self.approved()
        self.assertEqual(self.foreground_launch()["decision"], "manual")
        self.assertEqual(self.revisions(), [1])

    def test_foreground_dry_run_writes_nothing_and_refuses_drift(self):
        plan = self.approved()
        self.foreground_launch()
        self.revise(plan, 99)
        import bt_orchestration_terminal as terminal
        for kw in ({}, {"dry_run": True}):
            with self.assertRaisesRegex(terminal.TerminalError, "FOREGROUND_PLAN_REFUSED: PLAN_DRIFT"):
                self.foreground_launch(**kw)
        self.assertEqual(self.revisions(), [1])

    def test_foreground_refuses_an_invalid_plan_json(self):
        planner.write_skeleton(self.rdir)
        self.set_status("approved")
        import bt_orchestration_terminal as terminal
        with self.assertRaisesRegex(terminal.TerminalError, "FOREGROUND_PLAN_REFUSED: PLAN_INVALID"):
            self.foreground_launch()
        self.assertFalse((self.rdir / "plan-revisions").exists())

    def test_successor_helper_rechecks_the_revision_before_replacing_the_session(self):
        import bt_orchestration_transition as transition
        self.assertIn("launch_problem(rdir, freeze=False)", Path(transition.__file__).read_text(encoding="utf-8"))

    # -- the run itself ------------------------------------------------------------------------------------------
    def test_a_new_run_binds_the_frozen_revision_and_refuses_drift(self):
        plan = self.approved()
        state = self.open_run()
        self.assertEqual(state["plan_ref"]["revision"], 1)
        self.revise(plan, 70)
        with self.assertRaises(SystemExit) as ctx:
            self.open_run()
        self.assertIn("PLAN_DRIFT", str(ctx.exception))

    def test_a_new_run_of_an_unapproved_contract_plan_is_refused(self):
        self.good_plan()
        self.set_status("draft")
        with self.assertRaises(SystemExit) as ctx:
            self.open_run()
        self.assertIn("PLAN_NOT_APPROVED", str(ctx.exception))

    def test_legacy_plans_start_runs_exactly_as_before(self):
        self.set_status("draft")
        state = self.open_run()
        self.assertNotIn("plan_ref", state)
        self.assertFalse((self.rdir / "plan-revisions").exists())

    def resume(self, existing: dict):
        import bt_run
        with patch.object(bt_run.rs, "load", return_value=existing), \
                patch.object(bt_run.rs, "update", side_effect=lambda rdir, fn: existing), \
                patch.object(bt_run, "_pool", return_value=None), patch.object(bt_run, "reap_orphans", return_value=[]):
            return bt_run._open("sample", self.rdir, {"agent": "claude"})

    def test_a_resumed_run_is_never_rewritten_and_never_runs_unapproved_content(self):
        plan = self.approved()
        self.open_run()  # freezes r1
        existing = {"req": "REQ-001", "status": "paused", "sessions": 1, "tasks": [], "limits": {}, "log": [],
                    "plan_ref": {"plan_id": "REQ-001", "revision": 1, "sha256": "x"}}
        before = json.dumps(existing, sort_keys=True)
        self.assertIs(self.resume(existing), existing)  # still the approved revision: resumes
        self.assertEqual(json.dumps(existing, sort_keys=True), before)
        self.revise(plan, 80)  # an unreviewed new revision appears on disk
        with self.assertRaises(SystemExit) as ctx:
            self.resume(existing)
        self.assertIn("PLAN_DRIFT", str(ctx.exception))
        self.assertEqual(json.dumps(existing, sort_keys=True), before)

    def test_resume_refuses_when_plan_json_was_deleted_after_a_freeze(self):
        self.approved()
        self.open_run()
        (self.rdir / "PLAN.json").unlink()
        existing = {"req": "REQ-001", "status": "paused", "sessions": 1, "tasks": [], "limits": {}, "log": [],
                    "plan_ref": {"plan_id": "REQ-001", "revision": 1, "sha256": "x"}}
        with self.assertRaises(SystemExit) as ctx:
            self.resume(existing)
        self.assertIn("PLAN_MISSING", str(ctx.exception))

    def test_resume_does_not_need_the_checkouts_that_launch_needed(self):
        plan = self.good_plan()
        plan["tasks"][0]["classification_evidence"]["scope"]["evidence"] = ["file:src/auth/session.py"]
        (self.rdir / "PLAN.json").write_text(planner.dumps(plan), encoding="utf-8")
        self.set_status("approved")
        planner.approve_freeze(self.rdir, adapter.plan_id(self.rdir), adapter.APPROVED_STATES)  # verified elsewhere
        existing = {"req": "REQ-001", "status": "paused", "sessions": 1, "tasks": [], "limits": {}, "log": [],
                    "plan_ref": {"plan_id": "REQ-001", "revision": 1, "sha256": "x"}}
        self.assertIsNone(adapter.resume_problem(self.rdir, existing))
        self.assertIsNotNone(adapter.launch_problem(self.rdir, freeze=False))  # a NEW run still demands the evidence

    def test_foreground_freezes_nothing_when_the_workspace_is_unusable(self):
        import bt_orchestration_terminal as terminal
        import bt_orchestration_transition as transition
        self.approved()
        with patch.object(transition.core, "find_req", return_value=self.rdir), \
                patch.object(transition.gate, "require_ready", return_value={"status": "ready"}), \
                patch.object(transition.state_, "load", return_value=None), \
                patch.object(transition.core.ws, "workdir", return_value=None):
            with self.assertRaisesRegex(terminal.TerminalError, "FOREGROUND_WORKSPACE_REQUIRED"):
                transition.launch("sample", "REQ-001")
        self.assertEqual(self.revisions(), [1])  # nothing beyond the approval record

    def test_resuming_a_run_of_a_legacy_plan_is_untouched(self):
        existing = {"req": "REQ-001", "status": "paused", "sessions": 1, "tasks": [], "limits": {}, "log": []}
        self.assertIs(self.resume(existing), existing)

    # -- approval ----------------------------------------------------------------------------------------------------
    def test_approval_refuses_an_invalid_plan_json_and_leaves_the_status(self):
        import bt_rounds
        planner.write_skeleton(self.rdir)
        self.set_status("review")
        with self.assertRaises(SystemExit) as ctx:
            bt_rounds.plan_decide(self.rdir, True, "", "terminal")
        self.assertIn("PLAN_INVALID", str(ctx.exception))
        self.assertEqual(planner.plan_status(self.rdir), "review")
        self.assertEqual(bt_rounds.plan_decide(self.rdir, False, "needs work", "terminal"), "changes-requested")

    def test_approval_freezes_exactly_the_approved_bytes(self):
        import bt_rounds
        plan = self.good_plan()
        self.set_status("review")
        self.assertEqual(bt_rounds.plan_decide(self.rdir, True, "", "terminal"), "approved")
        frozen = planner.load_revision(self.rdir, 1)
        self.assertEqual(planner.dumps(frozen), planner.dumps(plan))

    def test_approving_a_legacy_plan_is_unchanged(self):
        import bt_rounds
        self.set_status("review")
        self.assertEqual(bt_rounds.plan_decide(self.rdir, True, "", "terminal"), "approved")
        self.assertFalse((self.rdir / "plan-revisions").exists())

    # -- nothing can start a run around the gate ------------------------------------------------------------------
    def test_every_entry_that_creates_a_run_or_launches_goes_through_the_gate(self):
        callers = {path.name for path in SCRIPTS.glob("*.py")
                   if "init_state(" in path.read_text(encoding="utf-8") and path.name != "bt_runstate.py"}
        self.assertEqual(callers, {"bt_run.py"}, "a new module creates run state: route it through the launch gate")
        gated = {"bt_run.py": "launch_problem(", "bt_launch.py": "freeze_on_launch(",
                 "bt_orchestration_transition.py": "launch_problem("}
        for name, call in gated.items():
            self.assertIn(call, (SCRIPTS / name).read_text(encoding="utf-8"), name)
        self.assertIn("freeze_approved(", (SCRIPTS / "bt_rounds.py").read_text(encoding="utf-8"))


class RefVerifier(Isolated):
    def test_it_knows_requirements_tasks_decisions_commands_and_commits(self):
        import bt_core
        project = self.rdir.parent.parent
        (project / "DECISIONS.md").write_text("## D-007 — x\n", encoding="utf-8")
        (project / "PENDING.md").write_text("- P-012 · y\n", encoding="utf-8")
        with patch.object(bt_core, "ROOT", self.root):  # never the owner's real bitácora
            verify = adapter.ref_verifier(self.rdir)
        self.assertTrue(verify("precedent", "REQ-001", ""))
        self.assertTrue(verify("precedent", "REQ-001/T1", ""))
        self.assertFalse(verify("precedent", "REQ-001/T9", ""))
        self.assertFalse(verify("precedent", "REQ-777", ""))
        self.assertTrue(verify("precedent", "D-007", ""))
        self.assertFalse(verify("precedent", "D-008", ""))
        self.assertTrue(verify("precedent", "P-012", ""))
        self.assertIsNone(verify("precedent", "https://example.test/x", ""))
        self.assertTrue(verify("command", "python3 -m unittest", ""))
        self.assertTrue(verify("command", "FOO=1 python3 -c 'pass'", ""))
        self.assertFalse(verify("command", "no-such-binary-xyz --help", ""))


class ParserParity(unittest.TestCase):
    """The module keeps its own PLAN.md parser so it can stand alone; this keeps both parsers from drifting apart."""

    FIELDS = ("id", "done", "milestone", "title", "repo", "verify", "after", "files", "resources")
    SIZE_WORDS = {"s": "S", "small": "S", "low": "S", "m": "M", "medium": "M", "med": "M", "l": "L", "large": "L",
                  "high": "L", "xl": "L"}  # the supervisor's own normalisation; the module reports the raw word

    def compare(self, text: str, label: str) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "PLAN.md"
            path.write_text(text, encoding="utf-8")
            theirs, their_stones = rs.parse_plan(path), rs.milestones(path)
        ours, our_stones = planner_markdown.parse(text)
        self.assertEqual([t["id"] for t in ours], [t["id"] for t in theirs], label)
        for mine, other in zip(ours, theirs):
            for field in self.FIELDS:
                self.assertEqual(mine[field], other[field], f"{label} {mine['id']}.{field}")
            self.assertEqual(mine["risk"], other["risk"], f"{label} {mine['id']}.risk")
            self.assertEqual(self.SIZE_WORDS.get(mine["complexity"] or ""), other["complexity"],
                             f"{label} {mine['id']}.complexity")
        self.assertEqual(our_stones, their_stones, label)

    def test_synthetic_document(self):
        self.compare("""---
status: approved
---
<!-- - [ ] T9 — hidden · after: T1 -->
### M1 — First
- [ ] T1 — Do it · repo: backend · files: src/a.py, tests/** · verify: `pytest -k "a · b"` · risk: HIGH
- [x] T2.1: Next · after: T1, T0a, junk · resources: db, queue · complexity: Large
- [ ] T2.2 — Sized · size: m · risk: critical
### M2 - Second
- [ ] T3a -- Other · files: ../secret
## Appendix
- [ ] T4 — Orphan
#### M3 Deep
* [ ] T5 – Star bullet
""", "synthetic")

    def test_every_real_plan_in_the_repository(self):
        plans = sorted((REPO / "bitacora").glob("*/requirements/*/PLAN.md"))
        if not plans:
            self.skipTest("no real plans in this checkout")
        for plan in plans:
            with self.subTest(plan=plan.parent.name):
                self.compare(plan.read_text(encoding="utf-8"), plan.parent.name)


class RealHistoricalPlans(unittest.TestCase):
    """AC-13: compatibility is read-only and honest on REQ-013/015/016 of the pictures project."""

    REQUIREMENTS = REPO / "bitacora" / "pictures" / "requirements"
    CLASSIFICATION = ("complexity", "scope", "estimated_minutes", "risk", "coupling", "confidence", "estimate_rationale")

    @staticmethod
    def digest(folder: Path) -> dict[str, str]:
        return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(folder.rglob("*")) if p.is_file()}

    def folder(self, req: str) -> Path:
        found = sorted(self.REQUIREMENTS.glob(f"{req}-*"))
        if not found:
            self.skipTest(f"{req} not present in this checkout")
        return found[0]

    def test_compat_changes_nothing_and_reports_missing_classification(self):
        for req in ("REQ-013", "REQ-015", "REQ-016"):
            with self.subTest(req=req):
                folder = self.folder(req)
                before = self.digest(folder)
                info = planner.compat(folder, adapter.plan_id(folder))
                planner.skeleton(folder, adapter.plan_id(folder))
                self.assertEqual(self.digest(folder), before)
                self.assertFalse((folder / "PLAN.json").exists() or (folder / "plan-revisions").exists())
                self.assertGreater(info["task_count"], 0)
                for task in info["tasks"]:
                    for key in self.CLASSIFICATION:
                        self.assertIn(key, task["needs_enrichment"])
                        self.assertNotIn(key, task["derived"])

    def test_plans_without_milestone_headings_are_flagged(self):
        info = planner.compat(self.folder("REQ-013"))
        self.assertEqual(info["milestones_in_md"], [])
        self.assertEqual(len(info["tasks_without_milestone"]), info["task_count"])

    def test_a_finished_run_json_keeps_its_bytes_and_has_no_plan_ref(self):
        run = self.folder("REQ-016") / "RUN.json"
        if not run.exists():
            self.skipTest("REQ-016 has no RUN.json here")
        before = run.read_bytes()
        planner.compat(run.parent)
        self.assertEqual(run.read_bytes(), before)
        self.assertNotIn(b"plan_ref", before)


class Wiring(unittest.TestCase):
    def test_skill_routes_to_the_reference_and_the_reference_to_the_module(self):
        skill = (REPO / "skill" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("references/plan-contract.md", skill)
        doc = (REPO / "skill" / "references" / "plan-contract.md").read_text(encoding="utf-8")
        self.assertIn("bt_planner/README.md", doc)
        self.assertTrue(planner_revisions.DIR in doc)

    def test_module_convention_is_documented(self):
        doc = (REPO / "skill" / "references" / "modules.md").read_text(encoding="utf-8")
        for needle in ("bt_planner", "adapter", "test_boundaries"):
            self.assertIn(needle, doc)


if __name__ == "__main__":
    unittest.main()
