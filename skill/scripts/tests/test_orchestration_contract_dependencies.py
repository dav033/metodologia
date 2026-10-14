"""The shared validation leaf must not depend on execution or persistence."""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]


def imports(module: str) -> set[str]:
    tree = ast.parse((SCRIPTS / (module + '.py')).read_text())
    result = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name.split('.')[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module.split('.')[0])
    return result


class ContractDependenciesTests(unittest.TestCase):
    def test_validation_leaf_has_no_execution_or_persistence_imports(self):
        self.assertTrue((SCRIPTS / 'bt_orchestration_contract.py').exists(), 'missing shared validation leaf')
        self.assertFalse({name for name in imports('bt_orchestration_contract') if name.startswith('bt_')})

    def test_completion_context_and_actions_subgraph_has_no_cycles_including_local_imports(self):
        modules = {'bt_orchestration_contract', 'bt_orchestration_context',
                   'bt_orchestration_actions', 'bt_orchestration_completion'}
        graph = {module: imports(module) & modules for module in modules if (SCRIPTS / (module + '.py')).exists()}
        def visit(module, path):
            self.assertNotIn(module, path, ' -> '.join([*path, module]))
            for dependency in graph.get(module, set()):
                visit(dependency, [*path, module])
        for module in graph:
            visit(module, [])


if __name__ == '__main__':
    unittest.main()
