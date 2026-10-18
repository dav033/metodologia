import unittest
from app.intervals import merge_intervals


class MergeTests(unittest.TestCase):
    def test_touching_and_overlap(self):
        self.assertEqual(merge_intervals([(3, 5), (1, 3), (4, 8)]), [(1, 8)])

    def test_empty_dropped(self):
        self.assertEqual(merge_intervals([(2, 2), (5, 6)]), [(5, 6)])

    def test_reversed_with_empty(self):
        with self.assertRaises(ValueError):
            merge_intervals([(2, 2), (5, 1)])

    def test_generator_negative_nested_dupes(self):
        g = ((a, b) for a, b in [(-5, -1), (-4, -2), (-5, -1), (0, 1)])
        self.assertEqual(merge_intervals(g), [(-5, -1), (0, 1)])

    def test_input_preserved(self):
        data = [(3, 5), (1, 4)]
        merge_intervals(data)
        self.assertEqual(data, [(3, 5), (1, 4)])

    def test_empty_input(self):
        self.assertEqual(merge_intervals([]), [])


if __name__ == "__main__":
    unittest.main()
