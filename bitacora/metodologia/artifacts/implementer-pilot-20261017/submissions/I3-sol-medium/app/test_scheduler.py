import unittest

from app import Scheduler
from app.graph import validate_graph
from app.scheduler import Scheduler as ModuleScheduler


class GraphTests(unittest.TestCase):
    def test_rejects_invalid_graphs(self):
        for jobs in ({'a': ['missing']}, {'a': ['a']},
                     {'a': [], 'b': ['c'], 'c': ['b']}):
            with self.subTest(jobs=jobs):
                with self.assertRaises(ValueError):
                    validate_graph(jobs)
                with self.assertRaises(ValueError):
                    Scheduler(jobs)

    def test_fresh_dependency_sets(self):
        jobs = {'a': set(), 'b': {'a'}}
        result = validate_graph(jobs)
        self.assertEqual(result, jobs)
        self.assertIsNot(result, jobs)
        self.assertIsNot(result['b'], jobs['b'])
        result['b'].clear()
        self.assertEqual(jobs['b'], {'a'})

    def test_long_chain_validation_and_blocking(self):
        jobs = {str(i): [str(i - 1)] if i else [] for i in range(1500)}
        scheduler = Scheduler(jobs)
        scheduler.start('0')
        scheduler.finish('0', False)
        self.assertTrue(scheduler.done())
        self.assertEqual(scheduler.statuses()['1499'], 'blocked')


class SchedulerTests(unittest.TestCase):
    def test_exports_and_empty(self):
        self.assertIs(Scheduler, ModuleScheduler)
        scheduler = Scheduler({})
        self.assertEqual(scheduler.max_parallel, 2)
        self.assertEqual(scheduler.ready(), [])
        self.assertEqual(scheduler.statuses(), {})
        self.assertTrue(scheduler.done())

    def test_capacity_validation(self):
        for capacity in (True, False, 0, -1, 1.0, '2', None):
            with self.subTest(capacity=capacity):
                with self.assertRaises(ValueError):
                    Scheduler({}, capacity)

    def test_snapshot_generators_and_duplicates(self):
        dependencies = ['a', 'a']
        jobs = {'a': [], 'b': iter(dependencies)}
        scheduler = Scheduler(jobs)
        dependencies.append('missing')
        jobs.clear()
        scheduler.start('a')
        scheduler.finish('a')
        self.assertEqual(scheduler.ready(), ['b'])

    def test_snapshot_mutable_input(self):
        deps = ['a']
        jobs = {'a': [], 'b': deps}
        scheduler = Scheduler(jobs)
        deps.clear()
        jobs['c'] = []
        self.assertEqual(scheduler.ready(), ['a'])

    def test_ready_sorted_pure_and_independent_of_capacity(self):
        scheduler = Scheduler({'z': [], 'a': [], 'b': []}, 1)
        before = scheduler.statuses()
        self.assertEqual(scheduler.ready(), ['a', 'b', 'z'])
        self.assertEqual(scheduler.statuses(), before)
        self.assertIsNone(scheduler.start('a'))
        self.assertEqual(scheduler.ready(), ['b', 'z'])
        before = scheduler.statuses()
        with self.assertRaises(ValueError):
            scheduler.start('b')
        self.assertEqual(scheduler.statuses(), before)
        self.assertIsNone(scheduler.finish('a'))
        scheduler.start('b')

    def test_invalid_transitions_do_not_mutate(self):
        scheduler = Scheduler({'a': [], 'b': ['a']})
        for operation, job in ((scheduler.start, 'missing'),
                               (scheduler.start, 'b'),
                               (scheduler.finish, 'missing'),
                               (scheduler.finish, 'a')):
            before = scheduler.statuses()
            with self.assertRaises(ValueError):
                operation(job)
            self.assertEqual(scheduler.statuses(), before)
        scheduler.start('a')
        before = scheduler.statuses()
        with self.assertRaises(ValueError):
            scheduler.start('a')
        self.assertEqual(scheduler.statuses(), before)
        scheduler.finish('a')
        before = scheduler.statuses()
        with self.assertRaises(ValueError):
            scheduler.finish('a', False)
        self.assertEqual(scheduler.statuses(), before)

    def test_failure_blocks_immediately_and_preserves_other_states(self):
        scheduler = Scheduler({'a': [], 'b': [], 'c': ['a', 'b'],
                               'd': ['c'], 'e': [], 'f': ['e']}, 3)
        scheduler.start('e')
        scheduler.finish('e')
        scheduler.start('a')
        scheduler.start('b')
        self.assertIsNone(scheduler.finish('a', False))
        self.assertEqual(scheduler.statuses(), {
            'a': 'failed', 'b': 'running', 'c': 'blocked',
            'd': 'blocked', 'e': 'succeeded', 'f': 'pending'})
        self.assertFalse(scheduler.done())
        self.assertEqual(scheduler.ready(), ['f'])
        for operation in (scheduler.start, scheduler.finish):
            before = scheduler.statuses()
            with self.assertRaises(ValueError):
                operation('c')
            self.assertEqual(scheduler.statuses(), before)
        scheduler.finish('b')
        scheduler.start('f')
        scheduler.finish('f')
        self.assertTrue(scheduler.done())

    def test_statuses_returns_fresh_dict(self):
        scheduler = Scheduler({'a': []})
        statuses = scheduler.statuses()
        statuses['a'] = 'failed'
        self.assertEqual(scheduler.statuses(), {'a': 'pending'})


if __name__ == '__main__':
    unittest.main()
