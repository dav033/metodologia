import unittest
from app import Scheduler
from app.scheduler import Scheduler as S2
from app.graph import validate_graph


class T(unittest.TestCase):
    def test_invalid(self):
        for g in ({'a': ['b']}, {'a': ['a']}, {'a': ['b'], 'b': ['a']},
                  {'x': [], 'a': ['b'], 'b': ['c'], 'c': ['a']}):
            with self.assertRaises(ValueError):
                Scheduler(g)
        for m in (0, True, 1.5, '2'):
            with self.assertRaises(ValueError):
                Scheduler({}, m)

    def test_generators_and_block(self):
        s = Scheduler({'a': iter([]), 'b': (d for d in []), 'c': (d for d in 'ab'), 'd': ['c']}, 3)
        self.assertIs(S2, Scheduler)
        s.start('a'); s.start('b'); s.finish('a', False)
        self.assertEqual(s.statuses(), {'a': 'failed', 'b': 'running', 'c': 'blocked', 'd': 'blocked'})
        s.finish('b'); self.assertTrue(s.done())

    def test_capacity(self):
        s = Scheduler({'a': [], 'b': [], 'c': []})
        s.start('a'); s.start('b')
        with self.assertRaises(ValueError): s.start('c')
        with self.assertRaises(ValueError): s.start('zz')
        self.assertEqual(s.ready(), ['c'])

    def test_long_chain(self):
        g = {str(i): [str(i - 1)] if i else [] for i in range(5000)}
        s = Scheduler(g); s.start('0'); s.finish('0', False)
        self.assertEqual(s.statuses()['4999'], 'blocked')
        self.assertEqual(len(validate_graph(g)), 5000)
