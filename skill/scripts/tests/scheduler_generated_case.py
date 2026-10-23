"""Generated output acceptance through the executor's real integration gate."""
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import bt_scheduler_integrator as integ
import scheduler_executor_support as s
from scheduler_executor_support import core, git


def delete_snapshot(repo: Path, base: str, name: str) -> str:
    with tempfile.TemporaryDirectory() as scratch:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(scratch) / "index")}

        def run(*args):
            return subprocess.run(["git", *args], cwd=repo, env=env, check=True,
                                  capture_output=True, text=True).stdout.strip()

        run("read-tree", base)
        run("update-index", "--force-remove", "--", name)
        tree = run("write-tree")
    return git(repo, "commit-tree", tree, "-p", base, "-m", "delete generated")


class GeneratedGate(unittest.TestCase):
    def test_generated_deletions_do_not_fail_the_foreign_file_gate(self):
        import bt_integration_line
        from test_scheduler_integrator import FakePlan, snapshot

        base = snapshot(self.app, self.head, {"registry.json": "base\n"})
        self.accept("T1", snapshot(self.app, base, {"registry.json": "left\n"}))
        candidate = delete_snapshot(self.app, base, "registry.json")
        plan = FakePlan({"T1": ([], "app"), "T2": ([], "app")})
        plan.spec["T2"].expected_paths = ("b.txt",)
        plan.spec["T1"].expected_paths = ("a.txt",)
        plan.generated_paths = ("registry.json",)
        args = {"plan": plan, "accepted": lambda: dict(self.accepted), "snapshot_of": lambda a: self.snaps.get(a),
                "repo_of": lambda role: self.app, "default_repository": "app", "identity": "gen-delete"}
        integrator = integ.PredecessorIntegrator()
        integrator.bind(**args)
        line = bt_integration_line.Line(**args, base_of=lambda role: base)
        integrator.attach_line(line)
        self.assertEqual(integrator.would_conflict("T2", "att-T2", candidate), "")
        plan.generated_paths = ()
        self.assertIn("INTEGRATION_FILES_LOST", integrator.would_conflict("T2", "att-T2", candidate))

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.app = s.make_repo(Path(self.tmp.name) / "app")
        self.head = git(self.app, "rev-parse", "HEAD")
        self.accepted, self.snaps = {}, {}

    def accept(self, tid, sha):
        self.accepted[tid] = f"att-{tid}"
        self.snaps[f"att-{tid}"] = sha

    def test_generated_outputs_pass_the_line_gate_but_sources_still_reject(self):
        import bt_integration_line
        from test_scheduler_integrator import snapshot

        for declared, mixed in ((False, False), (True, False), (True, True)):
            with self.subTest(declared=declared, mixed=mixed):
                tasks = [{"id": tid, "repository": "app", "after": [], "expected_paths": [f"{tid}.txt"]}
                         for tid in ("T1", "T2")]
                body = {"schema_version": "1.0.0", "plan_id": "REQ-G", "revision": 1, "tasks": tasks}
                if declared:
                    body["generated_paths"] = ["registry.json"]
                    body["generated_command"] = {"app": "npm run registry:build"}
                raw = json.dumps(body)
                plan = core.load_plan(raw, approved_sha256=hashlib.sha256(raw.encode()).hexdigest())
                self.accept("T1", snapshot(self.app, self.head, {"registry.json": "left\n", "T1.txt": "1\n",
                                                              **({"README.md": "left\n"} if mixed else {})}))
                candidate = snapshot(self.app, self.head, {"registry.json": "right\n", "T2.txt": "2\n",
                                                           **({"README.md": "right\n"} if mixed else {})})
                args = {"plan": plan, "accepted": lambda: dict(self.accepted), "snapshot_of": lambda a: self.snaps.get(a),
                        "repo_of": lambda role: self.app, "default_repository": "app", "identity": f"gen-{declared}-{mixed}"}
                integrator = integ.PredecessorIntegrator()
                integrator.bind(**args)
                line = bt_integration_line.Line(**args)
                integrator.attach_line(line)
                clash = integrator.would_conflict("T2", "att-T2", candidate)
                if not declared or mixed:
                    self.assertIn("README.md" if mixed else "registry.json", clash)
                    if mixed:
                        self.assertNotIn("registry.json", clash)
                else:
                    self.assertEqual(clash, "")
                    self.accept("T2", candidate)
                    integrator.recompute_line()
                    self.assertEqual(line.needs_resolution("app"), {})
                    self.assertEqual(git(self.app, "show", f"{line.tip('app')}:registry.json"), "right")
                    self.assertEqual(line.state("app").generated_stale, ("registry.json",))
