"""D-273: a check's outcome never depends on which checks ran before it, and a failing prepared check says what ran first.

pictures REQ-021 r32 T3.91 a2-a4: a full `tsc --noEmit` failed in M6 and passed in the attempt's worktree. The cause was
not an earlier check (each check already starts from a fresh copy) but the verifier's own preparation (`next typegen`,
which writes the git-ignored `next-env.d.ts`); the builder could not tell, so these tests pin both halves.
"""

from __future__ import annotations

import dataclasses
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bt_scheduler_quality import sandbox_mounts, sandbox_prepare
from bt_scheduler_quality.engine import QualityEngine
from bt_scheduler_quality.policy import CheckSpec, QualityPolicy
from bt_scheduler_quality.runner import SandboxRunner
from bt_scheduler_quality.store import QualityStore
from test_snapshot import _make_snapshot

WRITE = (
    "import os\n"
    "os.makedirs('.next/types', exist_ok=True)\n"
    "for name in ('next-env.d.ts', '.next/types/routes.d.ts', 'generated.txt', 'tracked.txt', 'node_modules/dep/leak'):\n"
    "    open(name, 'w').write('written by an earlier check')\n"
)
PROBE = (
    "import os, sys\n"
    "leaked = [n for n in ('next-env.d.ts', '.next', 'generated.txt', 'node_modules/dep/leak') if os.path.exists(n)]\n"
    "if leaked or open('tracked.txt').read() != 'dirty tracked data\\n' or not os.path.exists('node_modules/dep/index.js'):\n"
    "    print('leaked', leaked); sys.exit(7)\n"
)


class CheckIsolationTests(unittest.TestCase):
    def test_files_a_check_writes_are_never_seen_by_the_next_check_in_either_order(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo, source, _, _ = _make_snapshot(root, files={
                ".gitignore": "next-env.d.ts\n.next/\ngenerated.txt\nnode_modules/\n",
                "write.py": WRITE, "probe.py": PROBE,
                "node_modules/dep/index.js": "module.exports = 1\n",     # the attempt's install: ignored, overlaid
            })
            source = dataclasses.replace(source, worktree=repo)
            results = {}
            for order_name, commands in (("write-first", ("write.py", "probe.py")), ("probe-first", ("probe.py", "write.py"))):
                store = QualityStore(":memory:")
                order = {
                    "idempotency_key": f"verify:T-001:{order_name}", "plan_id": "PLAN-TEST", "revision": 1,
                    "task_id": "T-001", "attempt_id": source.attempt_id, "token": 1,
                    "acceptance_criteria": list(commands),
                    "verification": [{"type": "command", "value": f"python3 {name}", "purpose": name} for name in commands],
                }
                result = QualityEngine(QualityPolicy(), store).verify(order, source)
                results[order_name] = {check["command"]: (check["status"], check["exit_code"]) for check in result["checks"]}
                tree_digests = {check["tree_digest"] for check in result["checks"]}
                store.close()

            self.assertEqual(results["write-first"], results["probe-first"])
            self.assertEqual(results["write-first"], {"python3 write.py": ("pass", 0), "python3 probe.py": ("pass", 0)})
            self.assertEqual(len(tree_digests), 1)                       # every check is keyed to the same captured tree
            self.assertFalse((repo / "node_modules" / "dep" / "leak").exists())    # the host install is never written
            self.assertFalse((repo / "next-env.d.ts").exists())

    def test_a_failing_prepared_check_ends_by_naming_what_ran_before_it_and_a_passing_one_is_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "package.json").write_text(json.dumps({"dependencies": {"next": "16.3.0"}}), encoding="utf-8")
            (root / "fails.py").write_text(
                "import os, sys\nsys.exit(3 if os.path.exists('next-env.d.ts') else 0)\n", encoding="utf-8")
            (root / "passes.py").write_text("print('ok')\n", encoding="utf-8")
            typegen = ("python3", "-c", "open('next-env.d.ts', 'w').write('/// <reference types=\"next\" />')")
            dep = (sandbox_mounts.Mount(str(root), "/workspace/node_modules"),)
            with patch.object(sandbox_prepare, "NEXT_TYPEGEN", typegen):
                failed = SandboxRunner(QualityPolicy()).run(_check("fails.py"), root, mounts=dep)
                passed = SandboxRunner(QualityPolicy()).run(_check("passes.py"), root, mounts=dep)
            unprepared = SandboxRunner(QualityPolicy()).run(_check("fails.py"), root)

        self.assertEqual((failed.status, failed.exit_code), ("fail", 3))
        self.assertTrue(failed.stdout.endswith(b"Run them in your worktree first to reproduce.\n"), failed.stdout)
        self.assertIn(b"next-env.d.ts and .next/types/**", failed.stdout)
        self.assertIn(b"`python3 -c open('next-env.d.ts'", failed.stdout)
        self.assertEqual((passed.status, passed.stdout), ("pass", b"ok\n"))    # a pass keeps its exact output (pass cache)
        self.assertEqual((unprepared.status, unprepared.stdout), ("pass", b""))

    def test_a_failing_preparation_step_is_named_and_the_check_did_not_run(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "package.json").write_text(json.dumps({"devDependencies": {"next": "16.3.0"}}), encoding="utf-8")
            (root / "probe.py").write_text("print('never')\n", encoding="utf-8")
            broken = ("python3", "-c", "import sys; sys.exit(2)")
            dep = (sandbox_mounts.Mount(str(root), "/workspace/node_modules"),)
            with patch.object(sandbox_prepare, "NEXT_TYPEGEN", broken):
                result = SandboxRunner(QualityPolicy()).run(_check("probe.py"), root, mounts=dep)

        self.assertEqual((result.status, result.exit_code), ("fail", 1))
        self.assertIn(b"preparation step `python3 -c import sys; sys.exit(2)` failed (exit 2)", result.stderr)
        self.assertIn(b"the check itself did not run", result.stderr)
        self.assertNotIn(b"never", result.stdout)

    def test_the_note_names_each_step_and_the_ignored_files_it_leaves(self):
        both = sandbox_prepare.prepare_note((sandbox_prepare.BUILD_WORKSPACES, sandbox_prepare.NEXT_TYPEGEN))

        self.assertEqual(sandbox_prepare.prepare_note(()), "")
        self.assertIn("`npm run build --workspaces --if-present` and `npx --no-install next typegen`", both)
        self.assertIn("(the workspace packages' build output, next-env.d.ts and .next/types/**)", both)
        self.assertLess(len(both), 500)        # it shares the correction note's tail budget with the real output


def _check(script: str) -> CheckSpec:
    return CheckSpec("CHECK-001", "command", f"python3 {script}", ("python3", script), ".", "test behavior")


if __name__ == "__main__":
    unittest.main()
