"""Impact selection (bt_regress_select, D-NNN): the suites a branch's changed paths can reach, and when the selection is
not trusted. A small repository in a temporary directory stands for metodologia: skill/scripts with modules, a package,
assets and suites; git only where the base matters (pyproject.toml)."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_regress_select as sel

FILES = {
    "pyproject.toml": '[project]\nname = "x"\ndependencies = ["dbos"]\n[project.scripts]\nbt-tool = "pkg.cli:main"\n'
                      '[tool.setuptools]\npy-modules = ["bt_a", "bt_b"]\n',
    "uv.lock": "lock\n",
    "skill/assets/plans.js": 'import "./plans-core.js";\n',
    "skill/assets/plans-core.js": "export const x = 1;\n",
    "skill/assets/orphan.js": "export const y = 1;\n",
    "skill/agents/kit/real/runtime/motion.tsx": "export const m = 1;\n",
    "skill/references/modules.md": "# docs\n",
    "skill/scripts/bt_core.py": "def index():\n    import bt_index\n    return bt_index\n",
    "skill/scripts/bt_index.py": "import bt_heavy\n",
    "skill/scripts/bt_heavy.py": "X = 1\n",
    "skill/scripts/bt_a.py": "import bt_core\nimport bt_b\n",
    "skill/scripts/bt_b.py": "def later():\n    import bt_lazy\n",
    "skill/scripts/bt_lazy.py": "def deeper():\n    import bt_deep\n",
    "skill/scripts/bt_deep.py": "D = 1\n",
    "skill/scripts/bt_dynamic.py": "import importlib\nmod = importlib.import_module('bt_target')\n",
    "skill/scripts/bt_target.py": "T = 1\n",
    "skill/scripts/bt_page.py": "from pathlib import Path\nASSETS = Path('assets')\nJS = ASSETS / 'plans.js'\n",
    "skill/scripts/bt_kit.py": "from pathlib import Path\nREAL = Path(__file__).parent / 'agents/kit/real'\n",
    "skill/scripts/runner.py": "import bt_target\n",
    "skill/scripts/pkg/__init__.py": "",
    "skill/scripts/pkg/__main__.py": "from .cli import main\nmain()\n",
    "skill/scripts/pkg/cli.py": "from . import helpers\nfrom .sub.leaf import value\n\ndef main():\n    return value\n",
    "skill/scripts/pkg/helpers.py": "H = 1\n",
    "skill/scripts/pkg/sub/__init__.py": "",
    "skill/scripts/pkg/sub/leaf.py": "from ..helpers import H\nvalue = H\n",
    "skill/scripts/tests/support_fixture.py": "import bt_a\n",
    "skill/scripts/tests/test_a.py": "import bt_a\nimport bt_b\n",
    "skill/scripts/tests/test_package_modules.py": "from pathlib import Path\nP = Path('pyproject.toml')\n",
    "skill/scripts/tests/test_core.py": "import bt_core\n",
    "skill/scripts/tests/test_dynamic.py": "import bt_dynamic\n",
    "skill/scripts/tests/test_page.py": "import bt_page\n",
    "skill/scripts/tests/test_kit.py": "import bt_kit\n",
    "skill/scripts/tests/test_patch.py": "from unittest import mock\nP = mock.patch('pkg.helpers.H', 2)\n",
    "skill/scripts/tests/test_module_run.py": "import subprocess, sys\nsubprocess.run([sys.executable, '-m', 'pkg'])\n",
    "skill/scripts/tests/test_tool.py": "import subprocess\nsubprocess.run(['bt-tool'])\n",
    "skill/scripts/tests/test_runs_script.py": "from pathlib import Path\nS = Path('skill/scripts') / 'runner.py'\n",
    "skill/scripts/tests/test_scan.py": "from pathlib import Path\nFILES = list(Path('.').rglob('*.py'))\n",
    "skill/scripts/tests/test_lonely.py": "X = 1\n",
    "skill/scripts/tests/test_x_boundary.py": "X = 1\n",
}


def write(root: Path, files: dict[str, str]) -> None:
    for path, text in files.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(textwrap.dedent(text), encoding="utf-8")


def sh(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True)


class Case(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="bt-select-")
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name)
        write(self.repo, FILES)

    def select(self, *changed: str, limit: int = 100) -> sel.Selection:
        return sel.select(self.repo, list(changed), limit=limit)


class ImportGraph(Case):
    def test_relative_lazy_and_string_imports_resolve(self):
        graph = sel.Graph(self.repo)
        scripts = "skill/scripts/"
        cli = graph.nodes[scripts + "pkg/cli.py"]
        self.assertEqual(cli.imports, {scripts + "pkg/__init__.py", scripts + "pkg/helpers.py",
                                       scripts + "pkg/sub/__init__.py", scripts + "pkg/sub/leaf.py"})
        self.assertIn(scripts + "pkg/helpers.py", graph.nodes[scripts + "pkg/sub/leaf.py"].imports)   # from ..helpers
        self.assertEqual(graph.nodes[scripts + "bt_b.py"].lazy, {scripts + "bt_lazy.py"})              # in a function
        self.assertEqual(graph.nodes[scripts + "bt_b.py"].imports, set())
        self.assertIn(scripts + "bt_target.py", graph.nodes[scripts + "bt_dynamic.py"].lazy)           # importlib
        patch = graph.nodes[scripts + "tests/test_patch.py"].lazy
        self.assertTrue({scripts + "pkg/__init__.py", scripts + "pkg/helpers.py"} <= patch)   # mock.patch
        self.assertIn(scripts + "pkg/__main__.py", graph.nodes[scripts + "tests/test_module_run.py"].lazy)  # -m pkg
        self.assertIn(scripts + "pkg/cli.py", graph.nodes[scripts + "tests/test_tool.py"].lazy)        # console script

    def test_lazy_imports_inside_one_package_are_followed_at_any_depth(self):
        write(self.repo, {"skill/scripts/pkg/engine.py": "def start():\n    from .wiring import W\n",
                          "skill/scripts/pkg/wiring.py": "W = 1\n",
                          "skill/scripts/pkg/helpers.py": "def go():\n    from . import engine\n"})
        reach = sel.Graph(self.repo).reach("skill/scripts/tests/test_patch.py")
        self.assertIn("skill/scripts/pkg/wiring.py", reach)   # helpers (1) -> engine (2) -> wiring (3), all lazy

    def test_lazy_imports_are_followed_only_near_the_suite(self):
        graph = sel.Graph(self.repo)
        reach = graph.reach("skill/scripts/tests/test_a.py")
        self.assertIn("skill/scripts/bt_lazy.py", reach)      # bt_b (depth 1) imports it in a function
        self.assertNotIn("skill/scripts/bt_deep.py", reach)   # bt_lazy (depth 2) imports it in a function
        self.assertNotIn("skill/scripts/bt_index.py", reach)  # bt_a (depth 1) -> bt_core (depth 2): its lazy import
        core = graph.reach("skill/scripts/tests/test_core.py")
        self.assertIn("skill/scripts/bt_heavy.py", core)      # bt_core at depth 1: its lazy bt_index and on
        self.assertIn("skill/scripts/bt_deep.py", graph.reach("skill/scripts/tests/test_a.py", lazy_depth=9))

    def test_a_reason_names_the_path(self):
        found = self.select("skill/scripts/pkg/helpers.py")
        self.assertIn("imports pkg.helpers", found.suites["test_patch"])
        self.assertIn("imports pkg.helpers via pkg.__main__ (+1)", found.suites["test_module_run"])


class Selection(Case):
    def test_known_diffs(self):
        found = self.select("skill/scripts/bt_lazy.py")
        self.assertEqual(found.full, "")
        self.assertEqual(found.suites["test_a"], ["imports bt_lazy via bt_b"])
        self.assertNotIn("test_core", found.suites)
        self.assertEqual(found.suites["test_x_boundary"], ["always"])
        self.assertEqual(found.suites["test_scan"], ["scans bt_lazy"])                 # globs *.py
        self.assertNotIn("test_lonely", found.suites)

        found = self.select("skill/assets/plans-core.js")                             # named by plans.js, by bt_page
        self.assertEqual(found.suites["test_page"], ["reads assets/plans-core.js via bt_page (+1)"])
        found = self.select("skill/agents/kit/real/runtime/motion.tsx")               # a folder bt_kit names
        self.assertEqual(found.suites["test_kit"], ["reads agents/kit/real/runtime/motion.tsx via bt_kit"])
        found = self.select("skill/scripts/bt_target.py")
        self.assertEqual(found.suites["test_runs_script"], ["imports bt_target via runner"])   # a script it runs
        self.assertIn("test_dynamic", found.suites)
        found = self.select("skill/scripts/tests/test_lonely.py", "skill/references/modules.md")   # docs may be unread
        self.assertEqual((found.full, found.suites["test_lonely"]), ("", ["changed"]))

    def test_a_deleted_module_still_finds_who_imports_it(self):
        (self.repo / "skill/scripts/bt_heavy.py").unlink()
        found = self.select("skill/scripts/bt_heavy.py")
        self.assertEqual(found.full, "")
        self.assertIn("test_core", found.suites)


class Fallbacks(Case):
    def test_what_the_graph_cannot_see_runs_everything(self):
        self.assertIn("uv.lock", self.select("uv.lock").full)
        self.assertIn("shared test helper", self.select("skill/scripts/tests/support_fixture.py").full)
        self.assertIn("the regression itself", self.select("skill/scripts/bt_regress.py").full)
        self.assertIn("no suite reaches skill/assets/orphan.js", self.select("skill/assets/orphan.js").full)
        self.assertIn("no suite reaches skill/scripts/bt_deep.py", self.select("skill/scripts/bt_deep.py").full)
        crowded = self.select("skill/scripts/bt_core.py", limit=20)
        self.assertIn("more than 20%", crowded.full)
        self.assertIn("test_core", crowded.first)                                   # direct: it still goes first
        self.assertNotIn("test_a", crowded.first)                                   # via bt_a: with the rest
        self.assertEqual(self.select("skill/scripts/bt_core.py", limit=100).full, "")

    def test_pyproject_is_trusted_only_when_just_py_modules_changed(self):
        sh(self.repo, "init", "-q", "-b", "main")
        sh(self.repo, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "add", "-A")
        sh(self.repo, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "base")
        pyproject = self.repo / "pyproject.toml"
        pyproject.write_text(FILES["pyproject.toml"].replace('"bt_b"]', '"bt_b", "bt_core"]'), encoding="utf-8")
        self.assertEqual(self.select("pyproject.toml").full, "")
        pyproject.write_text(FILES["pyproject.toml"].replace('["dbos"]', '["dbos", "httpx"]'), encoding="utf-8")
        self.assertIn("beyond py-modules", self.select("pyproject.toml").full)

    def test_changed_paths_lists_both_sides_of_a_rename_and_never_the_bitacora(self):
        sh(self.repo, "init", "-q", "-b", "main")
        commit = ["-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m"]
        sh(self.repo, "add", "-A")
        sh(self.repo, *commit, "base")
        sh(self.repo, "checkout", "-q", "-b", "topic")
        sh(self.repo, "mv", "skill/scripts/bt_heavy.py", "skill/scripts/bt_weighty.py")
        (self.repo / "bitacora").mkdir()
        (self.repo / "bitacora" / "log.md").write_text("day\n", encoding="utf-8")
        sh(self.repo, "add", "-A")
        sh(self.repo, *commit, "rename")
        self.assertEqual(sel.changed_paths(self.repo), ["skill/scripts/bt_heavy.py", "skill/scripts/bt_weighty.py"])


if __name__ == "__main__":
    unittest.main()
