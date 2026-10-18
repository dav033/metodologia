import unittest

from app import Scheduler as PackageScheduler
from app.graph import validate_graph
from app.scheduler import Scheduler


class ValidationTests(unittest.TestCase):
    def test_package_and_module_export_same_class(self):
        self.assertIs(PackageScheduler, Scheduler)

    def test_unknown_dependency_rejected(self):
        with self.assertRaises(ValueError):
            Scheduler({'a': ['missing']})

    def test_self_loop_rejected(self):
        with self.assertRaises(ValueError):
            Scheduler({'a': ['a']})

    def test_cycle_rejected(self):
        with self.assertRaises(ValueError):
            Scheduler({'a': ['b'], 'b': ['a']})

    def test_disconnected_cycle_rejected(self):
        with self.assertRaises(ValueError):
            Scheduler({'x': [], 'a': ['b'], 'b': ['a']})

    def test_max_parallel_validation(self):
        for bad in (0, -1, True, False, 1.0, '2', None):
            with self.subTest(value=bad):
                with self.assertRaises(ValueError):
                    Scheduler({}, max_parallel=bad)
        self.assertEqual(Scheduler({}, max_parallel=5).max_parallel, 5)

    def test_empty_graph_valid(self):
        s = Scheduler({})
        self.assertEqual(s.ready(), [])
        self.assertEqual(s.statuses(), {})
        self.assertTrue(s.done())

    def test_generator_dependencies_and_duplicates(self):
        s = Scheduler({'a': [], 'b': (d for d in ['a', 'a'])})
        self.assertEqual(s.ready(), ['a'])
        self.assertEqual(validate_graph({'a': [], 'b': iter(['a', 'a'])}),
                         {'a': set(), 'b': {'a'}})

    def test_input_snapshot(self):
        deps = {'a': [], 'b': ['a']}
        s = Scheduler(deps)
        deps['c'] = ['zzz']
        deps['b'].append('q')
        self.assertEqual(sorted(s.statuses()), ['a', 'b'])

    def test_validate_graph_returns_fresh_dict(self):
        jobs = {'a': []}
        result = validate_graph(jobs)
        result['a'].add('x')
        self.assertEqual(validate_graph(jobs), {'a': set()})


class LifecycleTests(unittest.TestCase):
    def test_ready_is_sorted_and_capacity_independent(self):
        s = Scheduler({'c': [], 'a': [], 'b': []}, max_parallel=1)
        self.assertEqual(s.ready(), ['a', 'b', 'c'])
        s.start('a')
        self.assertEqual(s.ready(), ['b', 'c'])

    def test_ready_does_not_mutate(self):
        s = Scheduler({'a': []})
        s.ready()
        self.assertEqual(s.statuses(), {'a': 'pending'})

    def test_start_requires_eligibility(self):
        s = Scheduler({'a': [], 'b': ['a']})
        with self.assertRaises(ValueError):
            s.start('b')
        with self.assertRaises(ValueError):
            s.start('unknown')
        self.assertEqual(s.statuses(), {'a': 'pending', 'b': 'pending'})

    def test_start_respects_capacity_without_state_change(self):
        s = Scheduler({'a': [], 'b': []}, max_parallel=1)
        s.start('a')
        with self.assertRaises(ValueError):
            s.start('b')
        self.assertEqual(s.statuses(), {'a': 'running', 'b': 'pending'})

    def test_finish_accepts_only_running(self):
        s = Scheduler({'a': []})
        with self.assertRaises(ValueError):
            s.finish('a')
        with self.assertRaises(ValueError):
            s.finish('nope')
        self.assertEqual(s.statuses(), {'a': 'pending'})

    def test_finish_success_releases_dependents(self):
        s = Scheduler({'a': [], 'b': ['a']})
        s.start('a')
        self.assertIsNone(s.finish('a', True))
        self.assertEqual(s.statuses(), {'a': 'succeeded', 'b': 'pending'})
        self.assertEqual(s.ready(), ['b'])

    def test_failure_blocks_transitive_descendants_only(self):
        s = Scheduler({'a': [], 'b': ['a'], 'c': ['b'], 'd': [], 'e': ['d']},
                      max_parallel=2)
        s.start('a')
        s.finish('a', success=False)
        self.assertEqual(s.statuses(),
                         {'a': 'failed', 'b': 'blocked', 'c': 'blocked',
                          'd': 'pending', 'e': 'pending'})
        self.assertFalse(s.done())
        s.start('d')
        s.finish('d')
        s.start('e')
        s.finish('e')
        self.assertTrue(s.done())

    def test_blocked_immediately_even_with_running_sibling_dependency(self):
        s = Scheduler({'a': [], 'b': [], 'c': ['a', 'b']}, max_parallel=2)
        s.start('a')
        s.start('b')
        s.finish('a', success=False)
        self.assertEqual(s.statuses()['c'], 'blocked')
        s.finish('b')
        self.assertTrue(s.done())

    def test_completed_states_preserved(self):
        s = Scheduler({'a': [], 'b': [], 'c': ['b']}, max_parallel=2)
        s.start('a')
        s.finish('a')
        s.start('b')
        s.finish('b', success=False)
        self.assertEqual(s.statuses(), {'a': 'succeeded', 'b': 'failed',
                                        'c': 'blocked'})

    def test_statuses_returns_fresh_dict(self):
        s = Scheduler({'a': []})
        snap = s.statuses()
        snap['a'] = 'running'
        self.assertEqual(s.statuses(), {'a': 'pending'})

    def test_max_parallel_attribute_preserved(self):
        self.assertEqual(Scheduler({}, max_parallel=3).max_parallel, 3)

    def test_long_chain_no_recursion_error(self):
        n = 1500
        jobs = {f'j{i:05d}': ([f'j{i - 1:05d}'] if i else []) for i in range(n)}
        s = Scheduler(jobs, max_parallel=1)
        for i in range(n):
            job = f'j{i:05d}'
            self.assertEqual(s.ready(), [job])
            s.start(job)
            s.finish(job)
        self.assertTrue(s.done())

    def test_long_chain_failure_blocks_all(self):
        n = 1200
        jobs = {f'j{i:05d}': ([f'j{i - 1:05d}'] if i else []) for i in range(n)}
        s = Scheduler(jobs, max_parallel=1)
        s.start('j00000')
        s.finish('j00000', success=False)
        self.assertTrue(s.done())
        self.assertEqual(set(s.statuses().values()), {'failed', 'blocked'})


if __name__ == '__main__':
    unittest.main()
