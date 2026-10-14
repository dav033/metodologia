"""Classification evidence (schema 1.1.0), plan-level coherence and the launch gate `bind_approved`."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bt_planner import contract as pc  # noqa: E402
from bt_planner import evidence as ev  # noqa: E402
from bt_planner import quality  # noqa: E402
from bt_planner import revisions as rev  # noqa: E402
from support import PlanDir, evidence_for  # noqa: E402


def mini(*tasks, version: str = "1.1.0", **every) -> dict:
    def task(tid: str, **over) -> dict:
        base = {"id": tid, "milestone_id": "M1", "title": f"Task {tid}",
                "objective": f"Deliver the change described for task {tid} completely", "repository": "backend",
                "after": [], "complexity": "low", "scope": "small_change", "estimated_minutes": 30, "risk": "medium",
                "coupling": "low", "confidence": "medium", "estimate_rationale": "Known pattern in this module",
                "classification_evidence": evidence_for(tid), "expected_paths": [f"src/{tid.lower()}/**"],
                "shared_resources": [], "acceptance_criteria": [f"Task {tid} behaves as described"],
                "verification": [{"type": "command", "value": "pytest -q", "purpose": "unit tests"}]}
        base.update(over)
        return base
    made = [task(t, **every) if isinstance(t, str) else task(t["id"], **{**every, **{k: v for k, v in t.items()
                                                                                     if k != "id"}}) for t in tasks]
    return {"schema_version": version, "plan_id": "REQ-X", "revision": 1, "spec_ref": "SPEC.md",
            "milestones": [{"id": "M1", "title": "Base", "acceptance_criteria": ["Everything is delivered"]}],
            "tasks": made}


def check(plan: dict, **kw) -> pc.Report:
    return pc.validate(plan, **kw)


class Evidence(unittest.TestCase):
    def test_complete_evidence_passes_and_old_schema_without_it_only_warns(self):
        self.assertTrue(check(mini("T1")).ok)
        old = mini("T1", version="1.0.0")
        del old["tasks"][0]["classification_evidence"]
        report = check(old)
        self.assertTrue(report.ok, report.errors)
        self.assertTrue(any("classification_evidence: absent (schema 1.0.0" in w for w in report.warnings))

    def test_missing_evidence_is_an_error_from_1_1_0(self):
        plan = mini("T1")
        del plan["tasks"][0]["classification_evidence"]
        self.assertIn("T1.classification_evidence: missing", "\n".join(check(plan).errors))

    def test_each_dimension_is_required(self):
        for dim in ev.DIMENSIONS:
            plan = mini("T1")
            del plan["tasks"][0]["classification_evidence"][dim]
            self.assertIn(f"T1.classification_evidence.{dim}: missing", "\n".join(check(plan).errors), dim)

    def test_justifications_that_say_nothing_are_rejected(self):
        for bad in ("TBD", "n/a", "same as above", "because", "it is easy", "  ", "ok", "docs only"):
            plan = mini("T1")
            plan["tasks"][0]["classification_evidence"]["risk"]["justification"] = bad
            out = "\n".join(check(plan).errors)
            self.assertIn("T1.classification_evidence.risk.justification", out, bad)

    def test_one_sentence_pasted_under_several_dimensions(self):
        plan = mini("T1")
        e = plan["tasks"][0]["classification_evidence"]
        e["scope"]["justification"] = e["risk"]["justification"] = "everything about this change is simple here"
        self.assertIn("scope, risk share the same justification text", "\n".join(check(plan).errors))

    def test_evidence_references_are_typed(self):
        for ref in ("src/a.py", "file:", "url:http://x", 12, "FILE: "):
            plan = mini("T1")
            plan["tasks"][0]["classification_evidence"]["scope"]["evidence"] = [ref]
            self.assertIn("evidence[0]", "\n".join(check(plan).errors), ref)
        plan = mini("T1")
        plan["tasks"][0]["classification_evidence"]["scope"]["evidence"] = []
        self.assertIn("needs at least one reference", "\n".join(check(plan).errors))

    def test_unknown_dimension_and_unsafe_paths(self):
        plan = mini("T1")
        plan["tasks"][0]["classification_evidence"]["durations"] = {"justification": "x y z w v", "evidence": ["file:a"]}
        plan["tasks"][0]["classification_evidence"]["scope"]["evidence"] = ["file:../etc/passwd", "file:/abs"]
        out = "\n".join(check(plan).errors)
        self.assertIn("durations: unknown dimension", out)
        self.assertEqual(out.count("must be relative"), 2)

    def test_file_evidence_must_exist_when_the_repository_is_known(self):
        plan = mini("T1")
        plan["tasks"][0]["classification_evidence"]["scope"]["evidence"] = ["file:src/real.py:10-20", "file:src/ghost.py"]
        seen = []

        def exists(repo, path):
            seen.append((repo, path))
            return path == "src/real.py"

        out = "\n".join(check(plan, file_exists=exists).errors)
        self.assertIn("file 'src/ghost.py' does not exist in repository 'backend'", out)
        self.assertNotIn("real.py", out)
        self.assertIn(("backend", "src/real.py"), seen)  # the :10-20 suffix is a position, not part of the path

    def test_file_evidence_must_be_concrete_not_a_pattern_or_the_root(self):
        for ref in ("file:*", "file:.", "file:**", "file:./", "file:src/*"):
            plan = mini("T1")
            plan["tasks"][0]["classification_evidence"]["scope"]["evidence"] = [ref]
            errors_text = "\n".join(check(plan, file_exists=lambda repo, path: True).errors)
            if ref == "file:src/*":
                self.assertNotIn("concrete path", errors_text, ref)  # a directory glob still names a directory
            else:
                self.assertIn("must name a concrete path", errors_text, ref)

    def test_command_and_precedent_evidence_need_a_recognisable_shape(self):
        bad = {"command:x": "command evidence must read", "command:pytest -q": "command evidence must read",
               "precedent:foo": "precedent 'foo' must be", "precedent:it was fine before": "must be a requirement"}
        for ref, needle in bad.items():
            plan = mini("T1")
            plan["tasks"][0]["classification_evidence"]["duration"]["evidence"] = [ref]
            self.assertIn(needle, "\n".join(check(plan).errors), ref)
        plan = mini("T1")
        plan["tasks"][0]["classification_evidence"]["duration"]["evidence"] = [
            "command:pytest -q -> 31 passed in 2s", "precedent:REQ-009/T4", "precedent:D-021", "precedent:a1b2c3d4e5",
            "precedent:https://example.test/pull/12"]
        self.assertTrue(check(plan).ok, check(plan).errors)

    def test_command_and_precedent_references_that_cannot_exist_are_errors_when_a_verifier_is_supplied(self):
        plan = mini("T1")
        plan["tasks"][0]["classification_evidence"]["duration"]["evidence"] = [
            "command:madeup-tool --flag -> it was fast", "precedent:REQ-999/T1", "precedent:REQ-009/T4",
            "command:python3 -m unittest -> 12 passed"]
        known = {("command", "python3 -m unittest"), ("precedent", "REQ-009/T4")}

        def exists(kind, value, repo):
            return (kind, value) in known

        out = "\n".join(check(plan, ref_exists=exists).errors)
        self.assertIn("command 'madeup-tool --flag' is not an executable", out)
        self.assertIn("precedent 'REQ-999/T1' does not exist", out)
        self.assertNotIn("REQ-009/T4", out)
        self.assertNotIn("python3 -m unittest", out)
        self.assertTrue(check(plan).ok)  # no verifier: only the shape is judged
        self.assertTrue(check(plan, ref_exists=lambda *a: None).ok)  # a verifier that cannot tell never blocks

    def test_a_spec_file_without_an_anchor_is_context_not_support(self):
        plan = mini("T1", confidence="high")
        for entry in plan["tasks"][0]["classification_evidence"].values():
            entry["evidence"] = ["spec:SPEC.md", "file:src/a.py"]
        plan["tasks"][0]["classification_evidence"]["duration"]["evidence"] = ["spec:SPEC.md"]
        self.assertIn("duration rest only on assumptions", "\n".join(check(plan).errors))
        plan["tasks"][0]["classification_evidence"]["duration"]["evidence"] = ["spec:SPEC.md#security"]
        self.assertTrue(check(plan).ok)

    def test_a_justification_unrelated_to_the_task_is_flagged(self):
        plan = mini("T1")
        plan["tasks"][0]["classification_evidence"]["risk"]["justification"] = "aaa bbb ccc ddd"
        self.assertTrue(any("risk.justification: shares no term" in w for w in check(plan).warnings))

    def test_task_references_must_exist_and_not_be_self(self):
        plan = mini("T1", "T2")
        plan["tasks"][0]["classification_evidence"]["coupling"]["evidence"] = ["task:T9", "task:T1"]
        out = "\n".join(check(plan).errors)
        self.assertIn("task 'T9' is not in this plan", out)
        self.assertIn("a task cannot be evidence for itself", out)

    def test_high_confidence_cannot_rest_on_assumptions(self):  # AC-09
        plan = mini("T1", confidence="high")
        e = plan["tasks"][0]["classification_evidence"]
        e["duration"]["evidence"] = ["assumption:the endpoint is simple"]
        out = "\n".join(check(plan).errors)
        self.assertIn("confidence: high, but duration rest only on assumptions", out)
        plan["tasks"][0]["confidence"] = "low"
        self.assertTrue(check(plan).ok)  # the honest version of the same plan is publishable

    def test_high_confidence_needs_something_inspected(self):
        plan = mini("T1", confidence="high")
        for entry in plan["tasks"][0]["classification_evidence"].values():
            entry["evidence"] = ["spec:SPEC.md"]
        self.assertIn("high requires evidence that something was inspected", "\n".join(check(plan).errors))

    def test_coupling_must_name_what_it_couples_to(self):
        plan = mini("T1", coupling="medium")
        self.assertIn("names neither a shared resource nor the task", "\n".join(check(plan).errors))
        plan["tasks"][0]["shared_resources"] = ["session-contract"]
        self.assertTrue(check(plan).ok)

    def test_text_that_carries_no_information(self):
        plan = mini("T1")
        t = plan["tasks"][0]
        t["objective"] = "Task T1"
        t["acceptance_criteria"] = ["works", "Task T1 behaves as described", "Task T1 behaves as described"]
        t["verification"][0]["value"] = "echo ok"
        out = "\n".join(check(plan).errors)
        for needle in ("objective: is too short", "acceptance_criteria[0]: is a placeholder",
                       "acceptance_criteria[2]: duplicate criterion", "'echo ok' cannot fail"):
            self.assertIn(needle, out)

    def test_the_same_findings_are_warnings_for_a_1_0_0_plan(self):
        plan = mini("T1", version="1.0.0")
        plan["tasks"][0]["objective"] = "Task T1"
        report = check(plan)
        self.assertTrue(report.ok)
        self.assertTrue(any("objective" in w for w in report.warnings))

    def test_risk_high_with_only_manual_checks_is_flagged(self):
        plan = mini("T1", risk="high", verification=[{"type": "manual", "value": "look at the screen",
                                                      "purpose": "see it", "expected": "the badge shows"}])
        self.assertTrue(any("nothing is machine-checked" in w for w in check(plan).warnings))

    def test_boilerplate_reused_across_tasks_is_a_warning(self):
        plan = mini("T1", "T2", "T3")
        for t in plan["tasks"]:
            t["classification_evidence"] = evidence_for("T0")  # identical text for every task
        self.assertTrue(any("reused by 3 tasks" in w for w in check(plan).warnings))

    def test_low_complexity_high_risk_stays_legal(self):  # AC-04 under the stricter schema
        plan = mini("T1", complexity="low", risk="high", scope="isolated_fix")
        self.assertTrue(check(plan).ok)

    def test_forbidden_scheduling_keys_inside_evidence_are_rejected(self):
        plan = mini("T1")
        plan["tasks"][0]["classification_evidence"]["scope"]["agent"] = "opus"
        self.assertIn("T1.classification_evidence.scope.agent", "\n".join(check(plan).errors))

    def test_text_that_promises_parallel_safety_is_refused(self):  # AC-06
        claims = ["These two are safe to run in parallel", "can be executed concurrently with T2", "parallel-safe change",
                  "Se puede ejecutar en paralelo con T3", "tarea paralelizable", "no conflicts with other tasks",
                  "ready for parallel work: safe for concurrently"]
        for text in claims[:-1]:
            plan = mini("T1")
            plan["tasks"][0]["estimate_rationale"] = text
            self.assertIn("promises parallel safety", "\n".join(check(plan).errors), text)
        plan = mini("T1")
        plan["tasks"][0]["classification_evidence"]["coupling"]["justification"] = "independent so safe to run in parallel"
        self.assertIn("coupling.justification", "\n".join(check(plan).errors))
        plan = mini("T1")
        plan["tasks"][0]["estimate_rationale"] = "Touches parallel arrays in the renderer; nothing about scheduling"
        self.assertTrue(check(plan).ok)  # the word alone is not a promise
        old = mini("T1", version="1.0.0")
        old["tasks"][0]["estimate_rationale"] = "safe to run in parallel"
        report = check(old)
        self.assertTrue(report.ok and any("promises parallel safety" in w for w in report.warnings))

    def test_scheduling_decisions_are_rejected_by_meaning_not_by_exact_spelling(self):  # AC-15
        for key in ("assignee", "executor", "llm", "concurrency", "max_parallel", "num_workers", "model_hint",
                    "recommendedModel", "preferred-agent", "accountId", "Provider"):
            plan = mini("T1")
            plan["tasks"][0][key] = "x"
            self.assertIn(f"T1.{key}", "\n".join(check(plan).errors), key)
        plan = mini("T1")
        plan["tasks"][0].update(notes="open question", owner_review="required", modeling_notes="ok")
        self.assertTrue(check(plan).ok)  # `modeling` is not `model`

    def test_canonical_text_ignores_key_order_inside_evidence(self):
        a = mini("T1")
        b = copy.deepcopy(a)
        e = b["tasks"][0]["classification_evidence"]
        b["tasks"][0]["classification_evidence"] = {k: {"evidence": v["evidence"], "justification": v["justification"]}
                                                    for k, v in reversed(list(e.items()))}
        self.assertEqual(pc.dumps(a), pc.dumps(b))
        self.assertEqual(json.loads(pc.dumps(a)), json.loads(pc.dumps(b)))


class Hardening(PlanDir):
    def test_schema_1_0_0_keeps_the_exact_serialisation_it_was_frozen_with(self):
        plan = mini("T1", version="1.0.0")
        del plan["tasks"][0]["classification_evidence"]
        plan["tasks"][0]["scope"] = "full_system"
        plan["tasks"][0]["scope_exception"] = {"reason": "r", "owner": "o", "approved_by": "a"}
        text = pc.dumps(plan)
        self.assertLess(text.index('"reason"'), text.index('"owner"'))  # nested keys untouched, as the old code left them
        self.assertLess(text.index('"owner"'), text.index('"approved_by"'))
        self.assertEqual(json.loads(text), json.loads(json.dumps(plan)))
        plan["schema_version"] = "1.1.0"
        modern = pc.dumps(plan)
        self.assertLess(modern.index('"approved_by"'), modern.index('"owner"'))  # 1.1.0 sorts nested keys

    def test_malformed_values_never_raise_out_of_check_or_the_gate(self):
        good = self.good()
        self.sync.approve_freeze(self.rdir, "REQ-042")  # a frozen store makes check serialise the plan
        junk = [[1], {"a": 1}, 1, "x", None, True, [[1]], "\x00"]
        paths = [("milestones",), ("tasks",), ("milestones", 0), ("tasks", 0), ("tasks", 0, "verification"),
                 ("tasks", 0, "classification_evidence"), ("tasks", 0, "classification_evidence", "coupling"),
                 ("tasks", 0, "classification_evidence", "coupling", "evidence"),
                 ("tasks", 0, "classification_evidence", "risk", "evidence"), ("tasks", 0, "after"),
                 ("tasks", 0, "expected_paths"), ("spec_ref",), ("tasks", 0, "verification", 0)]
        for path in paths:
            for value in junk:
                import copy as _copy
                plan = _copy.deepcopy(good)
                node = plan
                for part in path[:-1]:
                    node = node[part]
                node[path[-1]] = value
                try:
                    self.sync.check(self.rdir, plan, "REQ-042", verify_files=True)
                except pc.PlanContractError:
                    pass
                except Exception as exc:  # noqa: BLE001
                    self.fail(f"{path}={value!r} raised {type(exc).__name__}: {exc}")

    def test_nul_in_a_path_is_rejected_not_crashed_on(self):
        plan = self.good()
        plan["spec_ref"] = "SPEC.md\x00x"
        plan["tasks"][0]["classification_evidence"]["risk"]["evidence"] = ["spec:SPEC.md\x00#a", "file:a\x00b"]
        self.write(plan)
        self.assertTrue(self.errors())

    def test_an_unclosed_comment_marker_cannot_stall_the_parser(self):
        import time
        from bt_planner import markdown
        start = time.monotonic()
        markdown.parse_document("<!--" * 50000 + "\n- [ ] T1 — x\n")
        self.assertLess(time.monotonic() - start, 2.0)
        tasks = markdown.parse_document("a\n<!-- one\ntwo -->\n- [ ] T1 — kept · repo: r\n<!-- unclosed\n- [ ] T2 — gone\n")["tasks"]
        self.assertEqual([t["id"] for t in tasks], ["T1"])
        self.assertEqual(tasks[0]["line"], 4)

    def test_only_a_command_that_is_nothing_but_a_no_op_is_trivial(self):
        for real in ("echo ok && pytest -q", "sleep 2; curl -f localhost/health", "echo $X | grep -q ok",
                     "printf '%s' a | diff - expected"):
            plan = mini("T1")
            plan["tasks"][0]["verification"][0]["value"] = real
            self.assertTrue(check(plan).ok, real)
        for noop in ("echo ok", "true", "exit 0", "sleep 1", ":"):
            plan = mini("T1")
            plan["tasks"][0]["verification"][0]["value"] = noop
            self.assertFalse(check(plan).ok, noop)

    def test_texts_in_scripts_without_spaces_count_by_length(self):
        self.assertIsNone(ev.weak("接口在过期会话上返回未授权状态", 4))
        self.assertIsNotNone(ev.weak("好", 4))


class Coherence(unittest.TestCase):
    def test_unordered_tasks_sharing_a_path_with_coupling_low_are_an_error(self):
        plan = mini(dict(id="T1", expected_paths=["src/auth/**"]),
                    dict(id="T2", expected_paths=["src/auth/session.py"]))
        out = "\n".join(check(plan).errors)
        self.assertIn("T1 and T2: nothing orders them yet both touch path 'src/auth/**'~'src/auth/session.py'", out)

    def test_ordering_them_or_raising_coupling_resolves_it(self):
        plan = mini(dict(id="T1", expected_paths=["src/a.py"]), dict(id="T2", expected_paths=["src/a.py"], after=["T1"]))
        self.assertTrue(check(plan).ok)
        plan = mini(dict(id="T1", expected_paths=["src/a.py"], coupling="high", shared_resources=["a-module"]),
                    dict(id="T2", expected_paths=["src/a.py"], coupling="high", shared_resources=["a-module"]))
        self.assertTrue(check(plan).ok)

    def test_shared_resource_between_unordered_tasks(self):
        plan = mini(dict(id="T1", shared_resources=["db"], coupling="medium"), dict(id="T2", shared_resources=["db"]))
        self.assertIn("both touch resource 'db'", "\n".join(check(plan).errors))

    def test_transitive_order_counts(self):
        plan = mini(dict(id="T1", expected_paths=["src/a.py"]), dict(id="T2", after=["T1"]),
                    dict(id="T3", after=["T2"], expected_paths=["src/a.py"]))
        self.assertTrue(check(plan).ok)

    def test_a_very_long_chain_does_not_exhaust_the_recursion_limit(self):
        plan = mini(*[dict(id=f"T{i}", after=[f"T{i - 1}"] if i > 1 else [], expected_paths=[f"src/t{i}.py"])
                      for i in range(1, 2501)])
        report = check(plan)
        self.assertEqual(report.errors, [])
        self.assertEqual(quality.analyze(plan)["critical_path"]["minutes"], 2500 * 30)

    def test_cycles_do_not_hang_or_crash_the_lints(self):
        plan = mini(dict(id="T1", after=["T2"]), dict(id="T2", after=["T1"]))
        self.assertTrue(any("cycle" in e for e in check(plan).errors))
        self.assertEqual(quality.analyze(plan)["tasks"], 2)

    def test_redundant_edges_warn(self):
        plan = mini("T1", dict(id="T2", after=["T1"]), dict(id="T3", after=["T1", "T2"]))
        self.assertTrue(any("T3.after: T1 is already implied" in w for w in check(plan).warnings))

    def test_path_overlap_rules(self):
        yes = [("src/**", "src/a.py"), ("src/auth/**", "src/auth/x/y.py"), ("**", "docs/a.md"), ("a/b.py", "a/b.py"),
               ("src/*.py", "src/a.py")]
        no = [("src/auth/**", "src/billing/**"), ("docs/a.md", "docs/b.md"), ("src/auth", "src/authz/x.py")]
        for a, b in yes:
            self.assertTrue(quality.paths_overlap(a, b), (a, b))
        for a, b in no:
            self.assertFalse(quality.paths_overlap(a, b), (a, b))

    def test_analyze_summarises_the_plan(self):
        plan = mini("T1", dict(id="T2", after=["T1"], estimated_minutes=60), dict(id="T3", after=["T1"], confidence="low",
                    estimated_minutes=20))
        a = quality.analyze(plan)
        self.assertEqual((a["tasks"], a["total_minutes"]), (3, 110))
        self.assertEqual(a["critical_path"], {"tasks": ["T1", "T2"], "minutes": 90})
        self.assertEqual(a["widest_level"], 2)
        self.assertEqual(a["low_confidence"], ["T3"])
        self.assertEqual(a["with_evidence"], ["T1", "T2", "T3"])


class PublicationAndEvidenceScope(PlanDir):
    def test_spec_references_must_exist_in_the_plan_folder(self):
        plan = self.good()
        plan["tasks"][0]["classification_evidence"]["risk"]["evidence"] = ["spec:SPEC.md#security", "spec:NOPE.md"]
        self.write(plan)
        out = self.errors()
        self.assertIn("T1.classification_evidence.risk: spec 'NOPE.md' does not exist in the plan folder", out)
        self.assertNotIn("SPEC.md", out)

    def test_file_evidence_is_verified_against_repo_roots_or_reported_as_unverified(self):
        plan = self.good()
        plan["tasks"][0]["classification_evidence"]["scope"]["evidence"] = ["file:src/auth/session.py"]
        self.write(plan)
        repo = self.root / "backend"
        (repo / "src" / "auth").mkdir(parents=True)
        report = self.sync.check(self.rdir)
        self.assertTrue(report.ok)
        self.assertTrue(any("could not be verified against a repository" in w for w in report.warnings))
        self.assertIn("src/auth/session.py' does not exist", self.errors(repo_roots={"backend": repo}))
        (repo / "src" / "auth" / "session.py").write_text("x = 1\n")
        report = self.sync.check(self.rdir, repo_roots={"backend": repo})
        self.assertEqual((report.errors, [w for w in report.warnings if "could not be verified" in w]), ([], []))
        other = self.sync.check(self.rdir, repo_roots={"frontend": repo})
        self.assertTrue(any("repository 'backend' has no checkout here" in w for w in other.warnings))

    def test_spec_anchor_must_match_a_heading(self):
        plan = self.good()
        plan["tasks"][0]["classification_evidence"]["risk"]["evidence"] = ["spec:SPEC.md#security", "spec:SPEC.md#nope"]
        self.write(plan)
        out = self.errors()
        self.assertIn("spec anchor #nope matches no heading of SPEC.md", out)
        self.assertNotIn("#security", out)

    def test_unverifiable_file_evidence_blocks_approval_and_launch_but_not_a_plain_check(self):
        plan = self.good()
        plan["tasks"][0]["classification_evidence"]["scope"]["evidence"] = ["file:src/auth/session.py"]
        self.write(plan)
        self.assertTrue(self.sync.check(self.rdir).ok)  # standalone: reported as a warning
        report = self.sync.check(self.rdir, verify_files=True)
        self.assertTrue(any("could not be verified" in e for e in report.errors))
        with self.assertRaises(pc.PlanContractError) as ctx:
            self.sync.approve_freeze(self.rdir, "REQ-042", verify_files=True)
        self.assertEqual(ctx.exception.code, "PLAN_INVALID")
        repo = self.root / "backend"
        (repo / "src" / "auth").mkdir(parents=True)
        (repo / "src" / "auth" / "session.py").write_text("x = 1\n")
        entry = self.sync.approve_freeze(self.rdir, "REQ-042", repo_roots={"backend": repo}, verify_files=True)
        self.assertEqual(self.sync.bind_approved(self.rdir, "REQ-042", repo_roots={"backend": repo},
                                                 verify_files=True), entry)
        with self.assertRaises(pc.PlanContractError):  # a launch on a machine without the checkout is refused
            self.sync.bind_approved(self.rdir, "REQ-042", verify_files=True)

    def test_new_revisions_must_use_the_evidence_schema_but_a_frozen_one_stays_valid(self):
        plan = self.good()
        old = copy.deepcopy(plan)
        old["schema_version"] = "1.0.0"
        for t in old["tasks"]:
            del t["classification_evidence"]
        self.write(old)
        self.assertIn("predates classification evidence", self.errors())
        # a 1.0.0 revision frozen before the evidence existed (written to the store as it was) keeps passing
        rev.freeze(self.rdir, old)
        self.assertEqual(self.errors(), "")


class LaunchGate(PlanDir):
    def bind(self, **kw):
        return self.sync.bind_approved(self.rdir, "REQ-042", **kw)

    def approve(self, plan: dict | None = None) -> dict:
        """The approval act: it is what creates the record a launch is compared against."""
        if plan is not None:
            self.write(plan)
        return self.sync.approve_freeze(self.rdir, "REQ-042")

    def code(self, **kw) -> str:
        with self.assertRaises(pc.PlanContractError) as ctx:
            self.bind(**kw)
        return ctx.exception.code

    def test_legacy_plan_has_nothing_to_bind(self):
        self.assertIsNone(self.bind())

    def test_not_approved_is_refused_unless_forced(self):
        self.good()
        self.md("review")
        self.assertEqual(self.code(), "PLAN_NOT_APPROVED")
        self.assertEqual(self.bind(forced=True)["source"], "launch-forced")

    def test_invalid_plan_is_never_bound_even_when_forced(self):
        plan = self.good()
        del plan["tasks"][0]["risk"]
        self.write(plan)
        self.assertEqual(self.code(forced=True), "PLAN_INVALID")
        self.assertFalse((self.rdir / "plan-revisions").exists())

    def test_a_launch_never_creates_the_approval_record(self):
        self.good()
        self.assertEqual(self.code(), "PLAN_NOT_FROZEN")  # approved by hand: no record of what was approved
        self.assertEqual(self.code(freeze=False), "PLAN_NOT_FROZEN")
        self.assertFalse((self.rdir / "plan-revisions").exists())

    def test_the_approval_act_freezes_exactly_what_the_launch_then_binds(self):
        plan = self.good()
        entry = self.approve()
        self.assertEqual(entry["source"], "approval")
        self.assertEqual(entry["sha256"], rev.sha256(pc.dumps(plan)))
        self.assertEqual(rev.load_revision(self.rdir, 1), json.loads(pc.dumps(plan)))
        self.assertEqual(self.bind(), entry)  # idempotent, nothing written
        self.assertEqual(self.bind(freeze=False), entry)
        self.assertEqual([r["revision"] for r in rev.list_revisions(self.rdir)], [1])

    def test_edit_after_approval_is_drift_not_a_new_revision(self):
        plan = self.good()
        self.approve()
        plan["tasks"][0]["estimated_minutes"] = 45
        self.write(plan)
        self.assertEqual(self.code(), "PLAN_INVALID")  # same revision number, different bytes
        plan["revision"] = 2
        self.write(plan)
        self.assertEqual(self.code(), "PLAN_DRIFT")  # a new revision is a new approval, never frozen by a launch
        self.assertEqual([r["revision"] for r in rev.list_revisions(self.rdir)], [1])

    def test_approving_the_new_revision_makes_it_launchable(self):
        plan = self.good()
        self.approve()
        plan["revision"] = 2
        plan["tasks"][0]["estimated_minutes"] = 45
        self.assertEqual(self.approve(plan)["revision"], 2)
        self.assertEqual(self.bind()["revision"], 2)

    def test_plan_json_removed_after_freeze_is_refused(self):
        self.good()
        self.approve()
        (self.rdir / "PLAN.json").unlink()
        self.assertEqual(self.code(), "PLAN_MISSING")

    def test_md_contradiction_blocks_the_launch(self):
        plan = self.good()
        self.approve()
        plan["tasks"][0]["title"] = "A different title"
        self.write(plan)
        self.assertEqual(self.code(), "PLAN_INVALID")

    def test_the_manifest_records_how_each_revision_was_frozen(self):
        plan = self.good()
        self.approve()
        plan["revision"] = 2
        plan["tasks"][0]["estimated_minutes"] = 45
        self.approve(plan)
        self.assertEqual([r["source"] for r in rev.list_revisions(self.rdir)], ["approval", "approval"])

    def test_a_forced_launch_of_an_unapproved_plan_is_recorded_as_forced(self):
        self.good()
        self.md("review")
        self.assertEqual(self.bind(forced=True, freeze=False)["frozen_at"], None)
        self.assertFalse((self.rdir / "plan-revisions").exists())
        self.assertEqual(self.bind(forced=True)["source"], "launch-forced")
        self.assertEqual([r["source"] for r in rev.list_revisions(self.rdir)], ["launch-forced"])


if __name__ == "__main__":
    unittest.main()
