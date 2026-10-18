import unittest
from app import Scheduler
from app import scheduler as scheduler_module


class ConstructionTest(unittest.TestCase):
    def test_exports_match(self):
        self.assertIs(scheduler_module.Scheduler, Scheduler)

    def test_invalid_max_parallel_rejected(self):
        for value in (0, -1, True, False, 1.0, '2', None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    Scheduler({}, max_parallel=value)

    def test_max_parallel_attribute_preserved(self):
        self.assertEqual(Scheduler({}, max_parallel=5).max_parallel, 5)
        self.assertEqual(Scheduler({}).max_parallel, 2)

    def test_invalid_graph_rejected_at_construction(self):
        with self.assertRaises(ValueError):
            Scheduler({'a': ['b'], 'b': ['a']})
        with self.assertRaises(ValueError):
            Scheduler({'a': ['x']})

    def test_input_is_snapshotted(self):
        deps = ['a']
        jobs = {'a': [], 'b': deps}
        s = Scheduler(jobs)
        deps.append('c')
        jobs['c'] = []
        self.assertEqual(s.statuses(), {'a': 'pending', 'b': 'pending'})
        self.assertEqual(s.ready(), ['a'])

    def test_generator_dependencies(self):
        s = Scheduler({'a': iter([]), 'b': (x for x in ['a'])})
        self.assertEqual(s.ready(), ['a'])
        s.start('a')
        s.finish('a')
        self.assertEqual(s.ready(), ['b'])


class ReadyTest(unittest.TestCase):
    def test_ready_sorted_and_independent_of_capacity(self):
        s = Scheduler({'c': [], 'a': [], 'b': [], 'd': ['a']}, max_parallel=1)
        self.assertEqual(s.ready(), ['a', 'b', 'c'])
        s.start('a')
        self.assertEqual(s.ready(), ['b', 'c'])

    def test_ready_does_not_change_state(self):
        s = Scheduler({'a': []})
        before = s.statuses()
        s.ready()
        s.ready()
        self.assertEqual(s.statuses(), before)


class StartTest(unittest.TestCase):
    def test_start_respects_capacity_without_mutation(self):
        s = Scheduler({'a': [], 'b': []}, max_parallel=1)
        s.start('a')
        with self.assertRaises(ValueError):
            s.start('b')
        self.assertEqual(s.statuses(), {'a': 'running', 'b': 'pending'})

    def test_start_ineligible_or_unknown_rejected(self):
        s = Scheduler({'a': [], 'b': ['a']})
        with self.assertRaises(ValueError):
            s.start('b')
        with self.assertRaises(ValueError):
            s.start('nope')
        with self.assertRaises(ValueError):
            s.start(['a'])
        self.assertEqual(s.statuses(), {'a': 'pending', 'b': 'pending'})

    def test_start_returns_none(self):
        s = Scheduler({'a': []})
        self.assertIsNone(s.start('a'))


class FinishTest(unittest.TestCase):
    def test_finish_only_running(self):
        s = Scheduler({'a': []})
        with self.assertRaises(ValueError):
            s.finish('a')
        with self.assertRaises(ValueError):
            s.finish('zzz')
        self.assertEqual(s.statuses(), {'a': 'pending'})

    def test_finish_after_finish_rejected(self):
        s = Scheduler({'a': []})
        s.start('a')
        s.finish('a')
        with self.assertRaises(ValueError):
            s.finish('a', success=False)
        self.assertEqual(s.statuses(), {'a': 'succeeded'})

    def test_failure_blocks_descendants_transitively(self):
        s = Scheduler({'a': [], 'b': ['a'], 'c': ['b'], 'd': []})
        s.start('a')
        s.start('d')
        s.finish('a', success=False)
        self.assertEqual(s.statuses(), {'a': 'failed', 'b': 'blocked', 'c': 'blocked', 'd': 'running'})
        self.assertFalse(s.done())
        s.finish('d')
        self.assertTrue(s.done())

    def test_job_blocked_immediately_while_other_dependency_runs(self):
        s = Scheduler({'a': [], 'b': [], 'c': ['a', 'b']}, max_parallel=2)
        s.start('a')
        s.start('b')
        s.finish('a', success=False)
        self.assertEqual(s.statuses()['c'], 'blocked')
        self.assertEqual(s.ready(), [])
        s.finish('b')
        self.assertEqual(s.statuses(), {'a': 'failed', 'b': 'succeeded', 'c': 'blocked'})
        self.assertTrue(s.done())

    def test_blocked_dependency_propagates_while_sibling_running(self):
        s = Scheduler({'a': [], 'b': ['a'], 'c': ['b', 'x'], 'x': []}, max_parallel=2)
        s.start('a')
        s.finish('a', success=False)
        self.assertEqual(s.statuses(), {'a': 'failed', 'b': 'blocked', 'c': 'blocked', 'x': 'pending'})

    def test_unrelated_jobs_continue(self):
        s = Scheduler({'a': [], 'b': ['a'], 'c': []})
        s.start('a')
        s.finish('a', success=False)
        self.assertEqual(s.ready(), ['c'])
        s.start('c')
        s.finish('c')
        self.assertTrue(s.done())

    def test_completed_states_preserved(self):
        s = Scheduler({'a': [], 'b': [], 'c': ['a']})
        s.start('a')
        s.finish('a')
        s.start('b')
        s.finish('b', success=False)
        self.assertEqual(s.statuses(), {'a': 'succeeded', 'b': 'failed', 'c': 'pending'})
        self.assertEqual(s.ready(), ['c'])

    def test_diamond_join_becomes_ready_only_after_all_succeed(self):
        s = Scheduler({'a': [], 'b': ['a'], 'c': ['a'], 'd': ['b', 'c']}, max_parallel=2)
        s.start('a')
        s.finish('a')
        s.start('b')
        s.finish('b')
        self.assertEqual(s.ready(), ['c'])
        s.start('c')
        self.assertEqual(s.ready(), [])
        s.finish('c')
        self.assertEqual(s.ready(), ['d'])


class DoneTest(unittest.TestCase):
    def test_empty_graph_done(self):
        self.assertTrue(Scheduler({}).done())

    def test_done_false_while_pending(self):
        self.assertFalse(Scheduler({'a': []}).done())

    def test_long_chain_without_recursion_error(self):
        n = 1200
        jobs = {'j0': []}
        for i in range(1, n):
            jobs[f'j{i}'] = [f'j{i - 1}']
        s = Scheduler(jobs, max_parallel=1)
        for i in range(n):
            job = f'j{i}'
            self.assertEqual(s.ready(), [job])
            s.start(job)
            s.finish(job)
        self.assertTrue(s.done())
        self.assertTrue(all(v == 'succeeded' for v in s.statuses().values()))

    def test_long_chain_failure_blocks_all(self):
        n = 1200
        jobs = {'j0': []}
        for i in range(1, n):
            jobs[f'j{i}'] = [f'j{i - 1}']
        s = Scheduler(jobs)
        s.start('j0')
        s.finish('j0', success=False)
        self.assertTrue(s.done())
        statuses = s.statuses()
        self.assertEqual(statuses['j0'], 'failed')
        self.assertTrue(all(statuses[f'j{i}'] == 'blocked' for i in range(1, n)))


if __name__ == '__main__':
    unittest.main()
