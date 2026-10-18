import unittest
from app.intervals import merge_intervals


class MergeIntervals(unittest.TestCase):
    def test_overlap(self):
        self.assertEqual(merge_intervals([(1, 4), (3, 6)]), [(1, 6)])

    def test_touching_boundaries_merge(self):
        self.assertEqual(merge_intervals([(1, 3), (3, 5)]), [(1, 5)])

    def test_gap_is_kept(self):
        self.assertEqual(merge_intervals([(1, 2), (3, 4)]), [(1, 2), (3, 4)])

    def test_nesting(self):
        self.assertEqual(merge_intervals([(0, 10), (2, 3), (4, 5)]), [(0, 10)])

    def test_duplicates(self):
        self.assertEqual(merge_intervals([(1, 2), (1, 2), (1, 2)]), [(1, 2)])

    def test_negative_coordinates(self):
        self.assertEqual(merge_intervals([(-5, -2), (-3, 0), (4, 6)]), [(-5, 0), (4, 6)])

    def test_empty_intervals_dropped(self):
        self.assertEqual(merge_intervals([(2, 2), (1, 1), (3, 4)]), [(3, 4)])

    def test_only_empty_intervals(self):
        self.assertEqual(merge_intervals([(2, 2)]), [])

    def test_reversed_raises_even_with_empty_others(self):
        with self.assertRaises(ValueError):
            merge_intervals([(2, 2), (5, 1)])

    def test_reversed_raises_alone(self):
        with self.assertRaises(ValueError):
            merge_intervals([(3, 1)])

    def test_generator_input(self):
        gen = ((s, e) for s, e in [(4, 6), (1, 2), (2, 3)])
        self.assertEqual(merge_intervals(gen), [(1, 3), (4, 6)])

    def test_input_not_modified(self):
        data = [(3, 5), (1, 4)]
        merge_intervals(data)
        self.assertEqual(data, [(3, 5), (1, 4)])

    def test_empty_input(self):
        self.assertEqual(merge_intervals([]), [])

    def test_result_sorted_by_start(self):
        self.assertEqual(merge_intervals([(9, 10), (1, 2), (5, 6)]), [(1, 2), (5, 6), (9, 10)])


if __name__ == "__main__":
    unittest.main()
