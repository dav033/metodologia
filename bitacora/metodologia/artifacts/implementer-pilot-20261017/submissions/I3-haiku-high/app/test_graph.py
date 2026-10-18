import unittest
from app.graph import validate_graph


class ValidateGraphTest(unittest.TestCase):
    def test_returns_fresh_sets_and_collapses_duplicates(self):
        result = validate_graph({'a': [], 'b': ['a', 'a']})
        self.assertEqual(result, {'a': set(), 'b': {'a'}})
        result['b'].add('zzz')
        self.assertEqual(validate_graph({'a': [], 'b': ['a']}), {'a': set(), 'b': {'a'}})

    def test_accepts_generator_dependencies(self):
        result = validate_graph({'a': iter([]), 'b': (x for x in ['a'])})
        self.assertEqual(result, {'a': set(), 'b': {'a'}})

    def test_unknown_dependency_rejected(self):
        with self.assertRaises(ValueError):
            validate_graph({'a': ['missing']})

    def test_self_loop_rejected(self):
        with self.assertRaises(ValueError):
            validate_graph({'a': ['a']})

    def test_cycle_rejected(self):
        with self.assertRaises(ValueError):
            validate_graph({'a': ['b'], 'b': ['a']})

    def test_disconnected_cycle_rejected(self):
        with self.assertRaises(ValueError):
            validate_graph({'a': [], 'b': [], 'c': ['d'], 'd': ['c']})

    def test_empty_graph_is_valid(self):
        self.assertEqual(validate_graph({}), {})

    def test_long_chain_has_no_recursion_error(self):
        jobs = {'j0': []}
        for i in range(1, 5000):
            jobs[f'j{i}'] = [f'j{i - 1}']
        self.assertEqual(len(validate_graph(jobs)), 5000)

    def test_non_mapping_rejected(self):
        with self.assertRaises(TypeError):
            validate_graph([('a', [])])


if __name__ == '__main__':
    unittest.main()
