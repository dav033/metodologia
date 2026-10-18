import unittest
from app.intervals import merge_intervals
class Public(unittest.TestCase):
    def test_smoke(self):
        self.assertEqual(merge_intervals([(3,5),(1,4)]), [(1,5)])
    def test_empty(self):
        self.assertEqual(merge_intervals([]), [])
