from textwrap import dedent as D

CASE = dict(
 id='I1', title='Repair interval merging', difficulty=1,
 prompt='''Repair app.intervals.merge_intervals(intervals). Input is an iterable of integer pairs (start,end), representing half-open intervals. Return a new list of tuples sorted by start, merging overlap AND touching boundaries. Drop empty intervals; reversed bounds raise ValueError, even when other intervals are empty. Preserve the caller's input. Empty input returns []. Negative coordinates, duplicates, nesting, and generators must work. Integers are guaranteed; type validation is not required. Use standard library only. Only app/ may be edited; do not change test_public.py. You may add your own tests under app/.''',
 starter={'app/__init__.py':'', 'app/intervals.py':D('''\
 def merge_intervals(intervals):
     result = []
     for start, end in sorted(intervals):
         if result and start < result[-1][1]:
             result[-1] = (result[-1][0], max(result[-1][1], end))
         else:
             result.append((start, end))
     return result
 '''), 'test_public.py':D('''\
 import unittest
 from app.intervals import merge_intervals
 class Public(unittest.TestCase):
     def test_smoke(self):
         self.assertEqual(merge_intervals([(3,5),(1,4)]), [(1,5)])
     def test_empty(self):
         self.assertEqual(merge_intervals([]), [])
 ''')},
 reference={'app/intervals.py':D('''\
 def merge_intervals(intervals):
     items = []
     for start, end in intervals:
         if start > end:
             raise ValueError('reversed interval')
         if start < end:
             items.append((start, end))
     result = []
     for start, end in sorted(items):
         if result and start <= result[-1][1]:
             result[-1] = (result[-1][0], max(result[-1][1], end))
         else:
             result.append((start, end))
     return result
 ''')},
 private_tests={'test_private.py':D('''\
 import random
 import unittest
 from app.intervals import merge_intervals as merge
 class Private(unittest.TestCase):
     def test_touching(self):
         self.assertEqual(merge([(4,8),(1,4),(8,9)]), [(1,9)])
     def test_empty_intervals(self):
         self.assertEqual(merge([(0,0),(5,5)]), [])
     def test_empty_outside(self):
         self.assertEqual(merge([(-10,-10),(1,2),(10,10)]), [(1,2)])
     def test_reverse(self):
         with self.assertRaises(ValueError): merge([(2,1)])
     def test_reverse_after_empty(self):
         with self.assertRaises(ValueError): merge([(0,0),(8,3)])
     def test_nested_duplicate(self):
         self.assertEqual(merge([(1,10),(3,4),(1,10),(2,9)]), [(1,10)])
     def test_negative_and_disjoint(self):
         self.assertEqual(merge([(-2,0),(-5,-2),(3,4)]), [(-5,0),(3,4)])
     def test_preserves_input(self):
         values = [[3,5],[1,4]]
         self.assertEqual(merge(values), [(1,5)])
         self.assertEqual(values, [[3,5],[1,4]])
     def test_generator(self):
         self.assertEqual(merge((p for p in [(2,3),(1,2)])), [(1,3)])
     def test_randomized_coverage_oracle(self):
         rng = random.Random(1701)
         for _ in range(100):
             pairs = [tuple(sorted((rng.randrange(-12,13),rng.randrange(-12,13)))) for _ in range(15)]
             covered = {i for a,b in pairs for i in range(a,b)}
             expected = []
             for point in sorted(covered):
                 if expected and expected[-1][1] == point:
                     expected[-1] = (expected[-1][0],point+1)
                 else: expected.append((point,point+1))
             self.assertEqual(merge(pairs), expected)
 ''')})
