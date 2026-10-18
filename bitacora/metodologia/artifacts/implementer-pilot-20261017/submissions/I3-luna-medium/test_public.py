import unittest
from app import Scheduler
class Public(unittest.TestCase):
    def test_chain(self):
        s=Scheduler({'a':[],'b':['a']})
        self.assertEqual(s.ready(),['a'])
        self.assertIsNone(s.start('a')); self.assertFalse(s.done())
        self.assertIsNone(s.finish('a')); self.assertEqual(s.ready(),['b'])
        s.start('b'); s.finish('b'); self.assertTrue(s.done())
    def test_empty(self):
        self.assertTrue(Scheduler({}).done())
