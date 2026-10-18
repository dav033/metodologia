import unittest

from app import Scheduler
from app.graph import validate_graph


class Construction(unittest.TestCase):
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
            Scheduler({'x': [], 'y': [], 'a': ['b'], 'b': ['a']})

    def test_cycle_downstream_of_valid_jobs_rejected(self):
        with self.assertRaises(ValueError):
            Scheduler({'root': [], 'a': ['root', 'b'], 'b': ['a']})

    def test_invalid_max_parallel_rejected(self):
        for value in (0, -1, True, False, 1.0, '2', None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    Scheduler({'a': []}, max_parallel=value)

    def test_max_parallel_one_accepted_and_preserved(self):
        s = Scheduler({'a': []}, max_parallel=1)
        self.assertEqual(s.max_parallel, 1)

    def test_empty_graph_is_valid(self):
        s = Scheduler({})
        self.assertTrue(s.done())
        self.assertEqual(s.ready(), [])
        self.assertEqual(s.statuses(), {})

    def test_duplicate_dependencies_are_harmless(self):
        s = Scheduler({'a': [], 'b': ['a', 'a']})
        s.start('a')
        s.finish('a')
        self.assertEqual(s.ready(), ['b'])

    def test_generator_dependencies_supported(self):
        s = Scheduler({'a': (x for x in []), 'b': (x for x in ['a'])})
        self.assertEqual(s.ready(), ['a'])
        s.start('a')
        s.finish('a')
        self.assertEqual(s.ready(), ['b'])

    def test_input_is_snapshotted(self):
        deps = ['a']
        jobs = {'a': [], 'b': deps}
        s = Scheduler(jobs)
        deps.append('c')
        jobs['c'] = []
        self.assertEqual(sorted(s.statuses()), ['a', 'b'])
        s.start('a')
        s.finish('a')
        self.assertEqual(s.ready(), ['b'])

    def test_validate_graph_returns_fresh_sets(self):
        first = validate_graph({'a': [], 'b': ['a']})
        self.assertEqual(first, {'a': set(), 'b': {'a'}})
        first['b'].add('zzz')
        self.assertEqual(validate_graph({'a': [], 'b': ['a']}), {'a': set(), 'b': {'a'}})


class Eligibility(unittest.TestCase):
    def test_ready_is_sorted_and_ignores_capacity(self):
        s = Scheduler({'c': [], 'a': [], 'b': []}, max_parallel=1)
        self.assertEqual(s.ready(), ['a', 'b', 'c'])

    def test_ready_does_not_change_state(self):
        s = Scheduler({'a': [], 'b': ['a']})
        before = s.statuses()
        s.ready()
        s.ready()
        self.assertEqual(s.statuses(), before)

    def test_job_waits_for_all_dependencies(self):
        s = Scheduler({'a': [], 'b': [], 'c': ['a', 'b']}, max_parallel=3)
        s.start('a')
        s.finish('a')
        self.assertEqual(s.ready(), ['b'])
        s.start('b')
        s.finish('b')
        self.assertEqual(s.ready(), ['c'])

    def test_statuses_returns_fresh_dict(self):
        s = Scheduler({'a': []})
        snapshot = s.statuses()
        snapshot['a'] = 'succeeded'
        self.assertEqual(s.statuses(), {'a': 'pending'})


class Transitions(unittest.TestCase):
    def test_start_returns_none_and_marks_running(self):
        s = Scheduler({'a': []})
        self.assertIsNone(s.start('a'))
        self.assertEqual(s.statuses(), {'a': 'running'})

    def test_start_respects_capacity_without_changing_state(self):
        s = Scheduler({'a': [], 'b': []}, max_parallel=1)
        s.start('a')
        before = s.statuses()
        with self.assertRaises(ValueError):
            s.start('b')
        self.assertEqual(s.statuses(), before)
        self.assertEqual(s.ready(), ['b'])

    def test_start_rejects_unknown_and_non_eligible(self):
        s = Scheduler({'a': [], 'b': ['a']})
        for job_id in ('nope', 'b'):
            with self.subTest(job_id=job_id):
                before = s.statuses()
                with self.assertRaises(ValueError):
                    s.start(job_id)
                self.assertEqual(s.statuses(), before)

    def test_start_rejects_already_running_job(self):
        s = Scheduler({'a': []}, max_parallel=2)
        s.start('a')
        with self.assertRaises(ValueError):
            s.start('a')
        self.assertEqual(s.statuses(), {'a': 'running'})

    def test_finish_rejects_unknown_and_non_running(self):
        s = Scheduler({'a': [], 'b': ['a']})
        for job_id in ('nope', 'a', 'b'):
            with self.subTest(job_id=job_id):
                before = s.statuses()
                with self.assertRaises(ValueError):
                    s.finish(job_id)
                self.assertEqual(s.statuses(), before)

    def test_finish_twice_rejected(self):
        s = Scheduler({'a': []})
        s.start('a')
        s.finish('a')
        with self.assertRaises(ValueError):
            s.finish('a', success=False)
        self.assertEqual(s.statuses(), {'a': 'succeeded'})

    def test_finish_returns_none(self):
        s = Scheduler({'a': []})
        s.start('a')
        self.assertIsNone(s.finish('a'))


class Failure(unittest.TestCase):
    def test_failure_blocks_transitive_descendants_only(self):
        s = Scheduler({'a': [], 'b': ['a'], 'c': ['b'], 'd': [], 'e': ['d']})
        s.start('a')
        s.finish('a', success=False)
        self.assertEqual(
            s.statuses(),
            {'a': 'failed', 'b': 'blocked', 'c': 'blocked', 'd': 'pending', 'e': 'pending'},
        )
        self.assertEqual(s.ready(), ['d'])

    def test_blocked_immediately_even_if_other_dependency_running(self):
        s = Scheduler({'a': [], 'b': [], 'c': ['a', 'b']}, max_parallel=2)
        s.start('a')
        s.start('b')
        s.finish('a', success=False)
        self.assertEqual(s.statuses()['c'], 'blocked')
        self.assertEqual(s.ready(), [])
        s.finish('b')
        self.assertEqual(s.statuses(), {'a': 'failed', 'b': 'succeeded', 'c': 'blocked'})

    def test_completed_states_are_preserved(self):
        s = Scheduler({'a': [], 'b': [], 'c': ['a', 'b']}, max_parallel=2)
        s.start('a')
        s.finish('a')
        s.start('b')
        s.finish('b', success=False)
        self.assertEqual(s.statuses(), {'a': 'succeeded', 'b': 'failed', 'c': 'blocked'})

    def test_done_treats_blocked_as_terminal(self):
        s = Scheduler({'a': [], 'b': ['a']})
        s.start('a')
        self.assertFalse(s.done())
        s.finish('a', success=False)
        self.assertTrue(s.done())

    def test_done_false_while_jobs_pending_or_running(self):
        s = Scheduler({'a': [], 'b': []}, max_parallel=1)
        s.start('a')
        self.assertFalse(s.done())
        s.finish('a')
        self.assertFalse(s.done())
        s.start('b')
        s.finish('b')
        self.assertTrue(s.done())

    def test_max_parallel_respected_across_sequence(self):
        s = Scheduler({f'j{i}': [] for i in range(4)}, max_parallel=2)
        s.start('j0')
        s.start('j1')
        with self.assertRaises(ValueError):
            s.start('j2')
        s.finish('j0')
        s.start('j2')
        self.assertEqual(s.statuses()['j2'], 'running')


class LongChain(unittest.TestCase):
    N = 1200

    def _chain(self):
        jobs = {'j0000': []}
        for i in range(1, self.N):
            jobs[f'j{i:04d}'] = [f'j{i - 1:04d}']
        return Scheduler(jobs, max_parallel=1)

    def test_long_chain_completes_without_recursion_error(self):
        s = self._chain()
        for i in range(self.N):
            job = f'j{i:04d}'
            self.assertEqual(s.ready(), [job])
            s.start(job)
            s.finish(job)
        self.assertTrue(s.done())
        self.assertTrue(all(v == 'succeeded' for v in s.statuses().values()))

    def test_long_chain_failure_blocks_all_descendants(self):
        s = self._chain()
        s.start('j0000')
        s.finish('j0000', success=False)
        self.assertTrue(s.done())
        statuses = s.statuses()
        self.assertEqual(statuses['j0000'], 'failed')
        self.assertTrue(all(statuses[f'j{i:04d}'] == 'blocked' for i in range(1, self.N)))


if __name__ == '__main__':
    unittest.main()
