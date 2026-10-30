"""Compositions of pictures REQ-021 r19: a member folds only its own work, package.json merges by key, a resolved conflict
is reused, and a run blocked by rejected gates tells the owner (D-160)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import bt_composition_adapter as adapter


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=T", "-c", "user.email=t@t", *args], cwd=repo, check=True,
                          capture_output=True, text=True).stdout.strip()


def commit(repo: Path, files: dict[str, str], message: str) -> str:
    for name, text in files.items():
        (repo / name).parent.mkdir(parents=True, exist_ok=True)
        (repo / name).write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def manifest(scripts: dict) -> str:
    return json.dumps({"name": "app", "scripts": scripts}, indent=2) + "\n"


class Repo(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="bt-compose-"))
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        self.base = commit(self.repo, {"package.json": manifest({"a": "x"}), "list.ts": "export const T = [\"a\"];\n"}, "base")
        self.port = adapter.GitSubprocessPort(self.repo, self.tmp / "ws")
        self.port.resolutions = self.tmp / "resolutions"

    def branch(self, name: str, files: dict[str, str]) -> str:
        git(self.repo, "checkout", "-q", "-b", name, self.base)
        return commit(self.repo, files, name)


class ManifestMerge(Repo):
    def test_merge_json_unions_added_keys_and_reports_a_real_clash(self):
        merged, clashes = adapter.merge_json({"s": {"a": 1}}, {"s": {"a": 1, "b": 2}}, {"s": {"a": 1, "c": 3}})
        self.assertEqual((merged, clashes), ({"s": {"a": 1, "b": 2, "c": 3}}, []))
        self.assertEqual(adapter.merge_json({"a": 1}, {"a": 2}, {"a": 3})[1], [".a"])
        self.assertEqual(adapter.merge_json({"a": 1, "b": 1}, {"a": 1}, {"a": 1, "b": 1}), ({"a": 1}, []))     # ours deleted
        self.assertEqual(adapter.merge_json({"a": 1, "b": 1}, {"a": 1}, {"a": 1, "b": 2})[1], [".b"])          # deleted vs changed

    def test_two_subplans_appending_npm_scripts_compose_without_a_conflict(self):
        ours = self.branch("ours", {"package.json": manifest({"a": "x", "b": "y"})})
        theirs = self.branch("theirs", {"package.json": manifest({"a": "x", "c": "z"})})
        result = self.port.merge_tree(self.base, ours, theirs)
        self.assertEqual(result.conflicts, ())
        merged = json.loads(git(self.repo, "cat-file", "blob", f"{result.tree}:package.json"))
        self.assertEqual(merged["scripts"], {"a": "x", "b": "y", "c": "z"})

    def test_a_script_both_sides_changed_differently_stays_a_conflict(self):
        ours = self.branch("ours", {"package.json": manifest({"a": "one"})})
        theirs = self.branch("theirs", {"package.json": manifest({"a": "two"})})
        self.port.resolutions = None
        self.assertEqual(self.port.merge_tree(self.base, ours, theirs).conflicts, ("package.json",))


class SubsumedHunks(Repo):
    """pictures REQ-021 r25 (D-172): gate T95 and SP-8's line both changed TABLAS_TRABAJO_CUENTA the same way and SP-8
    also appended a function right after it; git calls that one hunk a conflict, on every retry."""
    BASE = "const T = [\"a\"];\n\nexport function f() {}\n"
    SAME = "const T = [\"a\", \"b\"];\n"

    def test_one_side_is_the_other_plus_additions(self):
        both = adapter.merge_subsumed(self.BASE, self.SAME + "\nexport function g() {}\n\nexport function f() {}\n",
                                      self.SAME + "\nexport function f() {}\n")
        self.assertEqual(both, self.SAME + "\nexport function g() {}\n\nexport function f() {}\n")
        mirrored = adapter.merge_subsumed(self.BASE, self.SAME + "\nexport function f() {}\n",
                                          self.SAME + "\nexport function g() {}\n\nexport function f() {}\n")
        self.assertEqual(mirrored, both)

    def test_a_real_conflict_and_a_resurrection_stay_conflicts(self):
        self.assertIsNone(adapter.merge_subsumed(self.BASE, "const T = [\"a\", \"b\"];\n\nexport function f() {}\n",
                                                 "const T = [\"a\", \"c\"];\n\nexport function f() {}\n"))
        base = "const T = 1;\nconst U = 2;\n"                 # theirs removed U where ours changed T: taking ours would
        self.assertIsNone(adapter.merge_subsumed(base, "const T = 9;\nconst U = 2;\n", "const T = 9;\n"))  # bring U back

    def test_the_port_settles_it_in_the_tree(self):
        self.port.resolutions = None
        start = commit(self.repo, {"list.ts": self.BASE}, "base list")
        git(self.repo, "checkout", "-q", "-b", "line", start)
        ours = commit(self.repo, {"list.ts": self.SAME + "\nexport function g() {}\n\nexport function f() {}\n"}, "line")
        git(self.repo, "checkout", "-q", "-b", "gate", start)
        theirs = commit(self.repo, {"list.ts": self.SAME + "\nexport function f() {}\n"}, "gate")
        result = self.port.merge_tree(start, ours, theirs)
        self.assertEqual(result.conflicts, ())
        self.assertIn("function g", git(self.repo, "cat-file", "blob", f"{result.tree}:list.ts"))


class RecordedResolution(Repo):
    def test_a_conflict_waits_with_its_context_and_a_written_resolution_is_reused(self):
        ours = self.branch("ours", {"list.ts": "export const T = [\"p\", \"a\"];\n"})
        theirs = self.branch("theirs", {"list.ts": "export const T = [\"a\", \"d\"];\n"})
        first = self.port.merge_tree(self.base, ours, theirs)
        self.assertEqual(first.conflicts, ("list.ts",))
        contexts = list(self.port.resolutions.glob("*.json"))
        self.assertEqual(len(contexts), 1)
        self.assertIn("<<<<<<<", contexts[0].with_suffix(".diff3").read_text())
        contexts[0].with_suffix(".resolved").write_text("export const T = [\"p\", \"a\", \"d\"];\n")
        second = self.port.merge_tree(self.base, ours, theirs)
        self.assertEqual(second.conflicts, ())
        self.assertEqual(git(self.repo, "cat-file", "blob", f"{second.tree}:list.ts"), "export const T = [\"p\", \"a\", \"d\"];")


class OwnWork(Repo):
    def test_a_member_folds_from_where_its_own_snapshots_start(self):
        from bt_durable.adapters.composition import _own_work_base
        git(self.repo, "checkout", "-q", "-b", "line", self.base)
        foreign = commit(self.repo, {"other.ts": "1\n"}, "bt: integrate T9 into proj:REQ-001:r1 (SP-2)")
        first = commit(self.repo, {"own.ts": "1\n"}, "m3 snapshot proj-REQ-001-r1-T2.1-a1-0123abcd")
        tip = commit(self.repo, {"own.ts": "2\n"}, "m3 snapshot proj-REQ-001-r2-T2.2-a2-89abcdef")
        items = [{"task_id": "T2.1", "snapshot": first}, {"task_id": "T2.2", "snapshot": tip}]
        self.assertEqual(_own_work_base(self.repo, tip, items), foreign)
        self.assertEqual(_own_work_base(self.repo, tip, [*items, {"task_id": "T2.0", "snapshot": self.base}]), "")
        self.assertEqual(_own_work_base(self.repo, tip, [{"task_id": "T5.1", "snapshot": tip}]), "")


class LineIntegration(Repo):
    """A gate task built on a composed candidate is integrated into the subplan lines that hold it; there, too, npm
    scripts appended by different subplans merge by key (pictures REQ-021 r24: T93 conflicted with SP-11's line, D-164)."""

    def integrate(self, composer):
        from types import SimpleNamespace
        from bt_contracts.execution import RunRef, Snapshot
        from bt_durable.adapters.integration import GitLineIntegrator
        git(self.repo, "checkout", "-q", "main")
        run = RunRef(project="proj", req="REQ-900", revision=1, plan_id="REQ-900", plan_path="/nonexistent",
                     plan_sha256="0" * 64)
        lines = GitLineIntegrator({"app": self.repo}, composer=composer)
        lines.sync(run, "app", {"SP-1": []})
        line = lines.subplan_ref(run, "app", "SP-1")
        git(self.repo, "update-ref", line, self.branch("line", {"package.json": manifest({"a": "x", "b": "y"})}))
        snapshot = self.branch("gate", {"package.json": manifest({"a": "x", "c": "z"})})
        _tip, conflict, _note = lines.integrate(run, SimpleNamespace(id="T93", repository="app"),
                                                Snapshot(snapshot_sha=snapshot, base_sha=self.base,
                                                         manifest_path=self.tmp / "none.json"), lines=("SP-1",))
        return conflict, line

    def test_a_line_merges_package_json_by_key_like_the_composer(self):
        from types import SimpleNamespace
        conflict, line = self.integrate(SimpleNamespace(state_dir=self.tmp / "state"))
        self.assertEqual(conflict, "")
        merged = json.loads(git(self.repo, "cat-file", "blob", f"{line}:package.json"))
        self.assertEqual(merged["scripts"], {"a": "x", "b": "y", "c": "z"})

    def test_without_a_composer_the_conflict_stays_as_git_found_it(self):
        conflict, _line = self.integrate(None)
        self.assertEqual(conflict, "conflicts with accepted work in: package.json (line of SP-1)")

    def test_a_criss_cross_history_settles_against_a_virtual_base(self):
        """pictures REQ-021 r25 (D-169): the gate and SP-7's line had both taken SP-3 and SP-4, so they had several merge
        bases; the line kept the conflict on every retry. A script one side removed is not brought back."""
        from types import SimpleNamespace
        from bt_contracts.execution import RunRef, Snapshot
        from bt_durable.adapters.integration import GitLineIntegrator
        one = self.branch("one", {"package.json": manifest({"a": "x", "b": "y"})})
        two = self.branch("two", {"list.ts": "export const T = [\"a\", \"two\"];\n"})
        git(self.repo, "checkout", "-q", "-b", "line", one)
        git(self.repo, "merge", "-q", "--no-edit", two)
        line_tip = commit(self.repo, {"package.json": manifest({"a": "x", "d": "w"})}, "line drops b, adds d")
        git(self.repo, "checkout", "-q", "-b", "gate", two)
        git(self.repo, "merge", "-q", "--no-edit", one)
        snapshot = commit(self.repo, {"package.json": manifest({"a": "x", "b": "y", "e": "v"})}, "gate adds e")
        self.assertEqual(len(git(self.repo, "merge-base", "--all", line_tip, snapshot).split()), 2)
        git(self.repo, "checkout", "-q", "main")
        run = RunRef(project="proj", req="REQ-900", revision=1, plan_id="REQ-900", plan_path="/nonexistent",
                     plan_sha256="0" * 64)
        lines = GitLineIntegrator({"app": self.repo}, composer=SimpleNamespace(state_dir=self.tmp / "state"))
        lines.sync(run, "app", {"SP-7": []})
        ref = lines.subplan_ref(run, "app", "SP-7")
        git(self.repo, "update-ref", ref, line_tip)
        _tip, conflict, _note = lines.integrate(run, SimpleNamespace(id="T93", repository="app"),
                                                Snapshot(snapshot_sha=snapshot, base_sha=self.base,
                                                         manifest_path=self.tmp / "none.json"), lines=("SP-7",))
        self.assertEqual(conflict, "")
        merged = json.loads(git(self.repo, "cat-file", "blob", f"{ref}:package.json"))
        self.assertEqual(merged["scripts"], {"a": "x", "d": "w", "e": "v"})
        self.assertFalse(list((self.tmp / "state" / "composition" / "resolutions").glob("*.json")))


class BlockedNotice(unittest.TestCase):
    def test_a_run_blocked_by_rejected_gates_tells_the_owner_once(self):
        from types import SimpleNamespace
        from bt_durable import projection
        rdir = Path(tempfile.mkdtemp(prefix="bt-blocked-")) / "REQ-021-x"
        rdir.mkdir()
        run = SimpleNamespace(run_id="p:REQ-021:r19")
        plan = SimpleNamespace(composition_gates=[SimpleNamespace(id="CG-5", task="T95")])
        source = SimpleNamespace()
        with patch.object(projection, "requirement_dir", return_value=rdir), \
                patch.object(projection, "_event", return_value={"gates": {"rejected": {"CG-5": "git_text_conflict"}}}), \
                patch("bt_planning_activity.record") as record, patch("bt_runutil.notify") as notify:
            projection._announce_blocked(source, "wf", run, plan)
            projection._announce_blocked(source, "wf", run, plan)
        record.assert_called_once()
        notify.assert_called_once()
        self.assertIn("CG-5 (T95)", record.call_args.args[2])


if __name__ == "__main__":
    unittest.main()
