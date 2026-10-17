import ast
import unittest
from pathlib import Path


class BoundaryTests(unittest.TestCase):
    def test_module_has_no_sibling_or_execution_dependencies(self):
        root = Path(__file__).resolve().parents[1]
        forbidden = {"subprocess", "socket", "requests", "urllib.request", "http", "multiprocessing"}
        for path in root.glob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [item.name for item in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    names = [node.module or ""]
                for name in names:
                    self.assertFalse(name.startswith("bt_"), (path, name))
                    self.assertFalse(any(name == item or name.startswith(item + ".") for item in forbidden), (path, name))
            self.assertLessEqual(len(path.read_text().splitlines()), 400, path)

    def test_policy_is_pure(self):
        root = Path(__file__).resolve().parents[1]
        tree = ast.parse((root / "policy.py").read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.assertTrue(all(item.name in {"hashlib", "json"} for item in node.names))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, {"open", "exec", "eval", "__import__"})


if __name__ == "__main__":
    unittest.main()
